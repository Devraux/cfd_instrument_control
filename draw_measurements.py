import csv
import re
import tkinter as tk
from tkinter import ttk
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk



DATA_DIR = Path("./measurements_data")


def find_latest_measurement_folder(data_dir):
    folders = [
        path for path in data_dir.iterdir()
        if path.is_dir() and (
            (path / "cfd_out").is_dir()
            or (path / "calibration").is_dir()
        )
    ]

    if not folders:
        raise FileNotFoundError(f"No measurement session folders found in: {data_dir.resolve()}")

    return max(folders, key=lambda path: path.stat().st_mtime)

def format_measurement_name(name):
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})_(\d{2})_(\d{2})_(\d{2})$", name )

    if match:
        day, month, year, hour, minute, second = match.groups()
        return f"{day}.{month}.{year} {hour}:{minute}:{second}"

    return name

def read_measurement_csv(file_path):
    sample_indices = []
    time_intervals_ns = []

    with file_path.open("r", newline="", encoding="utf-8-sig") as f:
        lines = f.readlines()

    header_index = None

    for index, line in enumerate(lines):
        if line.strip() == "sample_index,time_interval_s":
            header_index = index
            break

    if header_index is None:
        return sample_indices, time_intervals_ns

    reader = csv.DictReader(lines[header_index:])

    for row in reader:
        try:
            sample_index = int(row["sample_index"])
            value = float(row["time_interval_s"])

            if not np.isfinite(value) or abs(value) >= 1e30:
                continue

            sample_indices.append(sample_index)
            time_intervals_ns.append(value * 1e9)

        except (ValueError, TypeError, KeyError):
            continue

    return sample_indices, time_intervals_ns

def read_summary_csv(file_path, value_column):
    amplitudes = []
    values = []

    if not file_path.is_file():
        return amplitudes, values

    with file_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                amplitude = float(row["amplitude_v"])
                value = float(row[value_column])

                if not np.isfinite(amplitude) or not np.isfinite(value):
                    continue

                amplitudes.append(amplitude)
                values.append(value)

            except (ValueError, TypeError, KeyError):
                continue

    order = np.argsort(amplitudes)

    return (
        np.array(amplitudes)[order],
        np.array(values)[order]
    )

def read_generic_csv(file_path):

    with file_path.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if not rows:
        return None, None, None

    for header_index, row in enumerate(rows):
        headers = [cell.strip() for cell in row]

        if len(headers) < 2 or not any(headers):
            continue

        data_rows = rows[header_index + 1:]
        numeric_columns = []

        for column_index, header in enumerate(headers):
            if not header:
                continue

            count = 0
            for data_row in data_rows:
                if column_index >= len(data_row):
                    continue
                try:
                    value = float(data_row[column_index])
                    if np.isfinite(value) and abs(value) < 1e30:
                        count += 1
                except (ValueError, TypeError):
                    pass

            if count > 0:
                numeric_columns.append((column_index, header))

        if len(numeric_columns) >= 2:
            columns = []

            for column_index, header in numeric_columns:
                x_values = []
                for data_row in data_rows:
                    if column_index >= len(data_row):
                        continue
                    try:
                        value = float(data_row[column_index])
                        if np.isfinite(value) and abs(value) < 1e30:
                            x_values.append(value)
                    except (ValueError, TypeError):
                        pass
                columns.append((header, x_values))

            return headers, data_rows, columns

    return None, None, None

def add_cfd_out_tab(notebook, session_folder):
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="CFD_OUT(Sample number)")

    fig = Figure(figsize=(12, 7))
    ax = fig.add_subplot(111)

    cfd_dir = session_folder / "cfd_out"
    csv_files = sorted(cfd_dir.glob("cfd_*V.csv"))

    plotted_count = 0
    statistics = []

    for file_path in csv_files:
        samples, times_ns = read_measurement_csv(file_path)

        if not times_ns:
            print(f"No valid measurements in: {file_path.name}")
            continue

        values = np.array(times_ns)

        line, = ax.plot(
            samples,
            values,
            marker=".",
            markersize=3,
            linewidth=0.8,
            label=file_path.stem
        )

        statistics.append(
            f"{file_path.stem}: "
            f"mean={np.mean(values):.4f} ns, "
            f"std={np.std(values):.4f} ns, "
            f"min={np.min(values):.4f} ns, "
            f"max={np.max(values):.4f} ns"
        )
        plotted_count += 1

    ax.set_title("Time Interval Measurements")
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Time interval (ns)")
    ax.grid(True, alpha=0.3)

    if plotted_count:
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.12),
            ncol=min(5, plotted_count),
            fontsize=8
        )
        fig.subplots_adjust(bottom=0.25)
    else:
        ax.text(
            0.5, 0.5, "No valid CFD Out data found",
            ha="center", va="center", transform=ax.transAxes
        )

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    toolbar = NavigationToolbar2Tk(canvas, frame)
    toolbar.update()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    

    if statistics:
        stats_frame = ttk.LabelFrame(
            frame,
            text="Measurement Statistics",
            padding=5
        )
        stats_frame.pack(
            side=tk.BOTTOM,
            fill=tk.X,
            padx=8,
            pady=5
        )

        table_frame = ttk.Frame(stats_frame)
        table_frame.pack(fill=tk.X, expand=True)

        columns = ("amplitude", "mean", "std", "min", "max")

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=4
        )

        tree.heading("amplitude", text="Amplitude [V]")
        tree.heading("mean", text="Mean [ns]")
        tree.heading("std", text="Std [ns]")
        tree.heading("min", text="Min [ns]")
        tree.heading("max", text="Max [ns]")

        for column in columns:
            tree.column(column, width=105, anchor="center")

        scrollbar_y = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=tree.yview
        )
        scrollbar_x = ttk.Scrollbar(
            stats_frame,
            orient=tk.HORIZONTAL,
            command=tree.xview
        )

        tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.pack(fill=tk.X)

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cfd_files = sorted((session_folder / "cfd_out").glob("cfd_*V.csv"),
                            key=lambda p: float(p.stem.replace("cfd_", "").replace("V", "").replace("_", ".")),
                            reverse=True)

        for file_path in cfd_files:
            _, times_ns = read_measurement_csv(file_path)

            if not times_ns:
                continue

            values = np.asarray(times_ns, dtype=float)
            amplitude = (
                file_path.stem
                .replace("cfd_", "")
                .replace("V", "")
                .replace("_", ".")
            )

            tree.insert(
                "",
                tk.END,
                values=(
                    amplitude,
                    f"{np.mean(values):.4f}",
                    f"{np.std(values):.4f}",
                    f"{np.min(values):.4f}",
                    f"{np.max(values):.4f}"
                )
            )

def add_summary_tab(notebook, session_folder, title, subfolder, filename, value_column, y_label):
    frame = ttk.Frame(notebook)
    notebook.add(frame, text=title)

    fig = Figure(figsize=(10, 7))
    ax = fig.add_subplot(111)

    file_path = session_folder / subfolder / filename
    amplitudes, values = read_summary_csv(file_path, value_column)

    if len(amplitudes):
        ax.plot(
            amplitudes,
            values,
            marker="o",
            linestyle="-")
    else:
        ax.text(
            0.5, 0.5,
            f"No valid data found\n{file_path}",
            ha="center", va="center",
            transform=ax.transAxes)

    ax.set_title(title)
    ax.set_xlabel("Amplitude (V)")
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.3)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    toolbar = NavigationToolbar2Tk(canvas, frame)
    toolbar.update()
    canvas.get_tk_widget().pack( side=tk.TOP, fill=tk.BOTH, expand=True)

def add_calibration_tab(notebook, session_folder):
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="Calibration")

    fig = Figure(figsize=(10, 7))
    ax = fig.add_subplot(111)

    calibration_dir = session_folder / "calibration"
    csv_files = sorted(calibration_dir.glob("*.csv"))
    plotted = 0

    for file_path in csv_files:
        _, _, columns = read_generic_csv(file_path)

        if not columns or len(columns) < 2:
            print(f"Could not find numeric calibration data in {file_path.name}")
            continue

        x_name, x_values = columns[0]

        for y_name, y_values in columns[1:]:
            length = min(len(x_values), len(y_values))

            if length == 0:
                continue

            ax.plot(
                x_values[:length],
                y_values[:length],
                marker=".",
                linestyle="-",
                label=f"{file_path.stem}: {y_name}")
            plotted += 1

    ax.set_title("Calibration")
    ax.set_xlabel(" / ".join(columns[0][0:1]) if plotted and columns else "X")
    ax.set_ylabel("Measured value")
    ax.grid(True, alpha=0.3)

    if plotted:
        ax.legend(fontsize=8)
    else:
        ax.text(
            0.5, 0.5,
            "No plottable calibration CSV data found",
            ha="center", va="center",
            transform=ax.transAxes
        )

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    toolbar = NavigationToolbar2Tk(canvas, frame)
    toolbar.update()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def add_setup_tab(notebook, ):
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="Measurement setup")

def main():
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(
            f"Measurement directory not found: {DATA_DIR.resolve()}"
        )

    session_folder = find_latest_measurement_folder(DATA_DIR)

    print(f"Reading measurements from: {session_folder.resolve()}")

    root = tk.Tk()
    root.title(f"Measurement Results - {format_measurement_name(session_folder.name)}")

    try:
        root.state("zoomed")
    except tk.TclError:
        pass

    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    add_setup_tab(notebook,)
    add_calibration_tab(notebook, session_folder)
    add_cfd_out_tab(notebook, session_folder)

    add_summary_tab(
        notebook,
        session_folder,
        title="Mean(Amplitude)",
        subfolder="mean",
        filename="mean_vs_amplitude.csv",
        value_column="mean_time_interval_s",
        y_label="Mean time interval [s]")

    add_summary_tab(
        notebook,
        session_folder,
        title="Deviation(Amplitude)",
        subfolder="deviation",
        filename="deviation_vs_amplitude.csv",
        value_column="standard_deviation_s",
        y_label="Standard deviation [s]"
    )

    for tab_index in (2, 3):
        tab = notebook.nametowidget(notebook.tabs()[tab_index])
        for child in tab.winfo_children():
            if isinstance(child, FigureCanvasTkAgg):
                fig = child.figure
                ax = fig.axes[0]
                for line in ax.lines:
                    line.set_ydata(line.get_ydata() * 1e9)
                fig.canvas.draw_idle()

    root.mainloop()

if __name__ == "__main__":
    main()