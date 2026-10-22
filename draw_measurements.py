import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import re

DATA_DIR = Path("./measurements_data")

def find_first_measurement_folder(data_dir):
    subfolders = [
        path for path in data_dir.iterdir()
        if path.is_dir()
    ]

    if not subfolders:
        raise FileNotFoundError(
            f"No measurement subfolders found in: {data_dir}"
        )

    return max(subfolders, key=lambda path: path.stat().st_mtime)

def read_measurement_csv(file_path):
    sample_indices = []
    time_intervals_ns = []

    with file_path.open("r", newline="", encoding="utf-8") as csv_file:
        lines = csv_file.readlines()

    header_index = None

    for index, line in enumerate(lines):
        if line.strip() == "sample_index,time_interval_s":
            header_index = index
            break

    if header_index is None:
        print(f"Skipping file without measurement data: {file_path.name}")
        return sample_indices, time_intervals_ns

    reader = csv.DictReader(lines[header_index:])

    for row in reader:
        try:
            sample_index = int(row["sample_index"])
            time_interval_s = float(row["time_interval_s"])

            if not np.isfinite(time_interval_s):
                continue

            # Skip invalid oscilloscope readings.
            if abs(time_interval_s) >= 1e30:
                continue

            sample_indices.append(sample_index)
            time_intervals_ns.append(time_interval_s * 1e9)

        except (ValueError, TypeError, KeyError):
            continue

    return sample_indices, time_intervals_ns

def plot_measurements(ax, file_path, sample_indices, time_intervals_ns):
    values = np.array(time_intervals_ns)

    mean_value = np.mean(values)
    variance = np.var(values, ddof=0)
    standard_deviation = np.std(values, ddof=0)
    minimum = np.min(values)
    maximum = np.max(values)

    line, = ax.plot(
        sample_indices,
        values,
        marker=".",
        linestyle="-",
        label=file_path.stem
    )

    statistics_label = (
        f"{file_path.stem}: "
        f"Mean={mean_value:.4f} ns | "
        f"Variance={variance:.6f} ns² | "
        f"Std={standard_deviation:.4f} ns | "
        f"Min={minimum:.4f} ns | "
        f"Max={maximum:.4f} ns"
    )

    return line, statistics_label

def format_measurement_name(name):
    match = re.search(
        r"(\d{2})\.(\d{2})\.(\d{4})_(\d{2})_(\d{2})_(\d{2})$",
        name
    )

    if match:
        day, month, year, hour, minute, second = match.groups()
        return (
            f"{day}.{month}.{year} "
            f"{hour}:{minute}:{second}"
        )

    return name

def main():
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(
            f"Measurement directory not found: {DATA_DIR.resolve()}"
        )

    measurement_folder = find_first_measurement_folder(DATA_DIR)
    csv_files = sorted(measurement_folder.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in: {measurement_folder}"
        )

    print(f"Reading measurements from: {measurement_folder}")

    fig, ax = plt.subplots(figsize=(18, 9))

    statistics_labels = []
    plotted_count = 0

    for file_path in csv_files:
        sample_indices, time_intervals_ns = read_measurement_csv(file_path)

        if not time_intervals_ns:
            print(f"No valid measurements in: {file_path.name}")
            continue

        line, statistics_label = plot_measurements(
            ax,
            file_path,
            sample_indices,
            time_intervals_ns
        )

        statistics_labels.append((line, statistics_label))
        plotted_count += 1

    if plotted_count == 0:
        raise ValueError( f"No valid measurement data found in: {measurement_folder}")
    
    ax.set_title( f"Time Interval Measurements - {format_measurement_name(measurement_folder.name)}")
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Time interval (ns)")
    ax.grid(True, alpha=0.3)

    # Display the color legend below the plot.
    color_legend = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=min(5, plotted_count),
        title="Amplitude / CSV file",
        fontsize=8,
        framealpha=0.9
    )

    ax.add_artist(color_legend)

    # Display all statistics on one line per measurement file.
    statistics_handles = [
        plt.Line2D([], [], color="none", label=label)
        for _, label in statistics_labels
    ]

    ax.legend(
        handles=statistics_handles,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        title="Measurement Statistics",
        fontsize=7,
        handlelength=0,
        handletextpad=0,
        labelspacing=0.65,
        borderpad=0.5,
        framealpha=0.9
    )

    # Reserve space for the statistics and the color legend.
    fig.subplots_adjust(
        left=0.06,
        right=0.53,
        bottom=0.25,
        top=0.92
    )

    # Maximize the figure window when supported.
    manager = plt.get_current_fig_manager()

    try:
        manager.window.state("zoomed")
    except (AttributeError, NotImplementedError):
        pass

    plt.show()


if __name__ == "__main__":
    main()