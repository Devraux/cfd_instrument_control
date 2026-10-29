import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import csv
from pathlib import Path
import re
import cfd_measure
from instrument_control import dac8554_api
from instrument_control import gen_cmd
from instrument_control import scope_cmd
import measurement_config as config
from tkinter import messagebox
import sys
import queue

# .EXE final version important change
#DATA_DIR = Path(config.PMT_OUTPUT_DIR).resolve()
#DATA_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = (Path(__file__).resolve().parent / "measurements_data")
current_session_folder = None
results_notebook = None
cfd_zero_calibration_value = (0, 0)

console_queue = queue.Queue()
original_stdout = sys.stdout
original_stderr = sys.stderr

def calibrate_only(parameters, dac_entries, refresh_console):
    global cfd_zero_calibration_value
    update_parameters(parameters, dac_entries)

    dac = dac8554_api.dac8554_api()
    generator = gen_cmd.Generator()
    oscilloscope = scope_cmd.Oscilloscope()

    session_folder, files = cfd_measure.prepare_measurement_files(dac=dac)
    cfd_measure.configure_instruments(dac_obj=dac, generator_obj=generator, oscilloscope_obj=oscilloscope)    
    cfd_zero_calibration_value = cfd_measure.cfd_calibrate(dac_obj=dac, generator_obj=generator, oscilloscope_obj=oscilloscope, output_path=session_folder, refresh_console=refresh_console)
    
    cfd_zero_calibration_x = cfd_zero_calibration_value[0]
    config.DAC_C = round(cfd_zero_calibration_x)
    update_dac_entry(dac_entries, "DAC_C", config.DAC_C)

    refresh_result_tabs(session_folder)

def characterize_only(parameters, dac_entries, refresh_console):
    update_parameters(parameters, dac_entries)

    dac = dac8554_api.dac8554_api()
    generator = gen_cmd.Generator()
    oscilloscope = scope_cmd.Oscilloscope()

    session_folder, files = cfd_measure.prepare_measurement_files(dac=dac)
    
    cfd_measure.configure_instruments(dac, generator, oscilloscope)
    cfd_measure.cfd_characterize(dac_obj=dac, generator_obj=generator, oscilloscope_obj=oscilloscope, output_path=session_folder, files=files, refresh_console=refresh_console)
    cfd_measure.process_measurement_results( files=files, output_path=session_folder)
    
    refresh_result_tabs(session_folder)

def calibrate_and_characterize(parameters, dac_entries, refresh_console):
    global cfd_zero_calibration_value
    update_parameters(parameters, dac_entries)

    dac = dac8554_api.dac8554_api()
    generator = gen_cmd.Generator()
    oscilloscope = scope_cmd.Oscilloscope()

    session_folder, files = cfd_measure.prepare_measurement_files(dac=dac)

    cfd_measure.configure_instruments(dac_obj=dac, generator_obj=generator, oscilloscope_obj=oscilloscope)
    
    cfd_zero_calibration_value = cfd_measure.cfd_calibrate(dac_obj=dac, generator_obj=generator, oscilloscope_obj=oscilloscope, output_path=session_folder, refresh_console=refresh_console)
    cfd_zero_calibration_x = cfd_zero_calibration_value[0]
    config.DAC_C = round(cfd_zero_calibration_x)
    update_dac_entry(dac_entries, "DAC_C", config.DAC_C)

    cfd_measure.cfd_characterize(dac_obj=dac, generator_obj=generator, oscilloscope_obj=oscilloscope, output_path=session_folder, files=files, refresh_console=refresh_console)
    cfd_measure.process_measurement_results(files=files, output_path=session_folder)
    
    refresh_result_tabs(session_folder)

def update_log_measure(log_measure_var):
        config.LOG_MEASURE_ENABLE = log_measure_var.get()

def update_parameters(parameters, dac_entries):
    config.PMT_AMPLITUDE_MIN = float(parameters["PMT_AMPLITUDE_MIN"].get())
    config.PMT_AMPLITUDE_MAX = float(parameters["PMT_AMPLITUDE_MAX"].get())
    config.PMT_AMPLITUDE_RESOLUTION = float(parameters["PMT_AMPLITUDE_RESOLUTION"].get())
    config.PMT_AMPLITUDE_SAMPLE_NUMBER = int(parameters["PMT_AMPLITUDE_SAMPLE_NUMBER"].get())

    config.PMT_PERIOD = float(parameters["PMT_PERIOD"].get()) * 1e-9
    config.PMT_DELAY = float(parameters["PMT_DELAY"].get()) * 1e-9
    config.PMT_RISE_TIME = float(parameters["PMT_RISE_TIME"].get()) * 1e-9
    config.PMT_WIDTH = float(parameters["PMT_WIDTH"].get()) * 1e-9
    config.PMT_FALL_TIME = float(parameters["PMT_FALL_TIME"].get()) * 1e-9

    config.DAC_START_CODE = int(parameters["dac_start_code"].get())
    config.DAC_STOP_CODE = int(parameters["dac_stop_code"].get())
    config.DAC_INCREMENT_STEP = int(parameters["dac_increment_step"].get())
    config.DAC_SAMPLES_PER_POINT = int(parameters["dac_samples_per_point"].get())
    
    config.PMT_AMPLITUDE_1 = float(parameters["pmt_amplitude_1"].get())
    config.PMT_AMPLITUDE_2 = float(parameters["pmt_amplitude_2"].get())
    config.PMT_AMPLITUDE_3 = float(parameters["pmt_amplitude_3"].get())

    dac_base = 16 if config.HEX_FORMAT else 10
    config.DAC_A = int(dac_entries["DAC_A"].get().strip(), dac_base)
    config.DAC_B = int(dac_entries["DAC_B"].get().strip(), dac_base)
    config.DAC_C = int(dac_entries["DAC_C"].get().strip(), dac_base)
    config.DAC_D = int(dac_entries["DAC_D"].get().strip(), dac_base)

    config.PMT_AMPLITUDES = [config.PMT_AMPLITUDE_1, config.PMT_AMPLITUDE_2, config.PMT_AMPLITUDE_3]

    config.DAC_INSTANCE = int(parameters["DAC_INSTANCE"].get())

def update_dac_entry(dac_entries, name, value):
    entry = dac_entries[name]
    entry.delete(0, tk.END)

    if config.HEX_FORMAT:
        entry.insert(0, f"0x{value:04X}")
    else:
        entry.insert(0, str(value))

def add_parameter(parent, name, default, unit, row, column):
    frame = ttk.Frame(parent, padding=5)
    frame.grid(row=row, column=column, sticky="ew", padx=3, pady=3)

    ttk.Label(frame, text=f"{name} [{unit}]").pack(anchor="w")

    entry = ttk.Entry(frame, width=22, font=("TkDefaultFont", 11))
    try:
        entry.insert(0, f"{float(default):.10g}")
    except (ValueError, TypeError):
        entry.insert(0, str(default))
    
    entry.pack(fill=tk.X, pady=(4, 0))
    return entry

def console_write(text):
    if text:
        console_queue.put(text)

def update_console(text_widget):
    messages = []

    while True:
        try:
            messages.append(console_queue.get_nowait())
        except queue.Empty:
            break

    if messages:
        text_widget.configure(state="normal")
        text_widget.insert("end", "".join(messages))
        text_widget.see("end")
        text_widget.configure(state="disabled")

def setup_console(text_widget, root):
    def refresh():
        update_console(text_widget)
        root.after(50, refresh)

    class RedirectOutput:
        def write(self, text):
            console_write(text)
            update_console(text_widget)
            root.update()
            return len(text)

        def flush(self):
            pass

        def isatty(self):
            return False

    sys.stdout = RedirectOutput()
    sys.stderr = RedirectOutput()

    refresh()

def add_setup_tab(notebook):
    frame = ttk.Frame(notebook, padding=10)
    notebook.add(frame, text="Setup")

    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    left = ttk.Frame(frame)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    left.columnconfigure(0, weight=1)

    pmt_frame = ttk.LabelFrame(left, text="PMT signal parameters", padding=8)
    pmt_frame.grid(row=1, column=0, sticky="ew")

    for column in range(3):
        pmt_frame.columnconfigure(column, weight=1)

    parameters = {}

    pmt_parameters = [  ("PMT_AMPLITUDE_MIN", str(config.PMT_AMPLITUDE_MIN), "V", 0, 0),
                        ("PMT_AMPLITUDE_MAX", str(config.PMT_AMPLITUDE_MAX), "V", 0, 1),
                        ("PMT_AMPLITUDE_RESOLUTION", str(config.PMT_AMPLITUDE_RESOLUTION), "V", 0, 2),
                        ("PMT_PERIOD", str(config.PMT_PERIOD / 1e-9), "ns", 1, 0),
                        ("PMT_DELAY", str(config.PMT_DELAY / 1e-9), "ns", 1, 1),
                        ("PMT_RISE_TIME", str(config.PMT_RISE_TIME / 1e-9), "ns", 2, 0, "PMT_LEADING_EDGE"),
                        ("PMT_WIDTH", str(config.PMT_WIDTH / 1e-9), "ns", 2, 1),
                        ("PMT_FALL_TIME", str(config.PMT_FALL_TIME / 1e-9), "ns", 2, 2, "PMT_TRAILING_EDGE"),
                        ("PMT_AMPLITUDE_SAMPLE_NUMBER", str(config.PMT_AMPLITUDE_SAMPLE_NUMBER), "samples", 3, 0)]

    for item in pmt_parameters:
        name, default, unit, row, column = item[:5]
        label = item[5] if len(item) > 5 else name
        parameters[name] = add_parameter(pmt_frame, label, default, unit, row, column)

    additional_frame = ttk.LabelFrame(left, text="CFD calibration additional parameters", padding=8)
    additional_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))

    for column in range(3):
        additional_frame.columnconfigure(column, weight=1)

    additional_parameters = [("dac_start_code", str(config.DAC_START_CODE), "16-bit DAC code", 0, 0),
                            ("dac_stop_code", str(config.DAC_STOP_CODE), "16-bit DAC code", 0, 1),
                            ("dac_increment_step", str(config.DAC_INCREMENT_STEP), "step", 0, 2),
                            ("dac_samples_per_point", str(config.DAC_SAMPLES_PER_POINT), "points", 0, 3),

                            ("pmt_amplitude_1", str(config.PMT_AMPLITUDE_1), "V", 1, 0),
                            ("pmt_amplitude_2", str(config.PMT_AMPLITUDE_2), "V", 1, 1),
                            ("pmt_amplitude_3", str(config.PMT_AMPLITUDE_3), "V", 1, 2)]

    for name, default, unit, row, column in additional_parameters:
        parameters[name] = add_parameter(additional_frame, name, default, unit, row, column)

    right = ttk.Frame(frame)
    right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
    right.columnconfigure(0, weight=1)

    dac_frame = ttk.LabelFrame(right, text="DAC values", padding=8)
    dac_frame.grid(row=0, column=0, sticky="ew")

    for column in range(4):
        dac_frame.columnconfigure(column, weight=1)

    dac_channels = [
        ("DAC_A", "TEST_POINT", config.DAC_A),
        ("DAC_B", "DRV_OFFSET", config.DAC_B),
        ("DAC_C", "CFD_ZERO", config.DAC_C),
        ("DAC_D", "CFD_TH", config.DAC_D)]

    dac_entries = {}

    for column, (name, alias, value) in enumerate(dac_channels):
        cell = ttk.Frame(dac_frame, padding=5)
        cell.grid(row=0, column=column, sticky="ew", padx=3)

        ttk.Label( cell,text=f"{name}\n{alias}",justify=tk.CENTER,font=("TkDefaultFont", 10, "bold")).pack(fill=tk.X, pady=(0, 5))
        entry = ttk.Entry(cell, width=12, justify=tk.CENTER, font=("TkDefaultFont", 11))

        if config.HEX_FORMAT:
            entry.insert(0, f"0x{value:04X}")
        else:
            entry.insert(0, str(value))

        entry.pack(fill=tk.X)

        dac_entries[name] = entry


    # DAC value format selector
    dac_format_var = tk.StringVar( value="HEX" if config.HEX_FORMAT else "DEC")
    previous_format = {"value": dac_format_var.get()}

    def change_dac_format(*args):
        old_format = previous_format["value"]
        new_format = dac_format_var.get()

        if old_format == new_format:
            return

        try:
            values = { name: int( entry.get().strip(), 16 if old_format == "HEX" else 10) for name, entry in dac_entries.items()}
            
        except ValueError:
            messagebox.showerror("Invalid DAC value",f"Please enter valid {old_format} values in all DAC fields.")
            dac_format_var.set(old_format)
            return

        for name, entry in dac_entries.items():
            value = values[name]
            formatted_value = ( f"0x{value:04X}" if new_format == "HEX" else str(value))

            entry.delete(0, tk.END)
            entry.insert(0, formatted_value)

        config.HEX_FORMAT = (new_format == "HEX")
        previous_format["value"] = new_format

    format_frame = ttk.Frame(dac_frame)
    format_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10, 2))

    format_frame.columnconfigure(0, weight=1)
    format_frame.columnconfigure(1, weight=1)
    format_frame.columnconfigure(2, weight=1)

    instance_frame = ttk.Frame(format_frame)
    instance_frame.grid(row=0, column=0, sticky="w")

    ttk.Label(instance_frame, text="DAC set instance:").pack(side=tk.LEFT, padx=(0, 6))

    dac_instance_var = tk.StringVar(value=str(config.DAC_INSTANCE))
    parameters["DAC_INSTANCE"] = dac_instance_var

    dac_instance_selector = ttk.Combobox( instance_frame, textvariable=dac_instance_var, values=("0", "1", "2"), state="readonly", width=4, justify=tk.CENTER)
    dac_instance_selector.pack(side=tk.LEFT)

    def on_dac_set():
        dac = dac8554_api.dac8554_api()
        config.DAC_INSTANCE = int(dac_instance_var.get())

        for name, entry in dac_entries.items():
            value = entry.get().strip()
            config_value = int(value, 16 if config.HEX_FORMAT else 10)
            setattr(config, name, config_value)

        dac.write_all( config.DAC_INSTANCE, config.DAC_A, config.DAC_B, config.DAC_C, config.DAC_D)


    dac_set_button = ttk.Button( format_frame, text="DAC set", command=on_dac_set, padding=(4, 0)) 
    dac_set_button.grid(row=0, column=1, sticky="n")
    format_right_frame = ttk.Frame(format_frame)
    format_right_frame.grid(row=0, column=2, sticky="e")

    ttk.Label(format_right_frame, text="Value format:").pack( side=tk.LEFT, padx=(0, 6))

    format_selector = ttk.Combobox(format_right_frame,textvariable=dac_format_var,values=("HEX", "DEC"),state="readonly",width=6,justify=tk.CENTER)
    format_selector.pack(side=tk.LEFT)
    format_selector.bind("<<ComboboxSelected>>", change_dac_format)

    options_frame = ttk.LabelFrame(right, text="Test options", padding=10)
    options_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    options_frame.columnconfigure(0, weight=1)

    log_measure_var = tk.BooleanVar(value=config.LOG_MEASURE_ENABLE)

    ttk.Checkbutton( options_frame, text="Logarithmic characterization enable", variable=log_measure_var, command=lambda: update_log_measure(log_measure_var), style="TCheckbutton").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Button(options_frame, text="CFD calibrate only", command=lambda: calibrate_only(parameters, dac_entries, refresh_measurement_console)).grid(row=1, column=0, sticky="ew", pady=4)
    ttk.Button(options_frame, text="CFD characterize only", command=lambda: characterize_only(parameters, dac_entries, refresh_measurement_console)).grid(row=2, column=0, sticky="ew", pady=4)
    ttk.Button(options_frame, text="CFD calibrate and characterize", command=lambda: calibrate_and_characterize(parameters, dac_entries, refresh_measurement_console)).grid(row=3, column=0, sticky="ew", pady=4)
    
    console_frame = ttk.LabelFrame(right, text="Console", padding=5)
    console_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))

    right.rowconfigure(2, weight=1)

    console_text = tk.Text(console_frame, height=30, wrap="word", state="disabled", font=("Consolas", 9))
    console_scrollbar = ttk.Scrollbar( console_frame, orient="vertical", command=console_text.yview)
    console_text.configure(yscrollcommand=console_scrollbar.set)
    console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    setup_console(console_text, notebook.winfo_toplevel())

    def refresh_measurement_console():
        update_console(console_text)
        notebook.winfo_toplevel().update()

    return parameters, dac_entries

def find_latest_measurement_folder(data_dir=DATA_DIR):
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Measurement directory not found: {data_dir.resolve()}")

    folders = [ path for path in data_dir.iterdir() if path.is_dir() and ( (path / "cfd_out").is_dir() or (path / "calibration").is_dir())]

    if not folders:
        raise FileNotFoundError(f"No measurement session folders found in: {data_dir.resolve()}")

    return max(folders, key=lambda path: path.stat().st_mtime)

def format_measurement_name(name):
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})_(\d{2})_(\d{2})_(\d{2})$", name)

    if match:
        day, month, year, hour, minute, second = match.groups()
        return f"{day}.{month}.{year} {hour}:{minute}:{second}"

    return name

def read_measurement_csv(file_path):
    sample_indices = []
    time_intervals_ns = []

    with file_path.open("r", newline="", encoding="utf-8-sig") as file:
        lines = file.readlines()

    header_index = next( (index for index, line in enumerate(lines)  if line.strip() == "sample_index,time_interval_s"), None)

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
        return np.array([]), np.array([])

    with file_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

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
    return np.asarray(amplitudes)[order], np.asarray(values)[order]

def read_generic_csv(file_path):
    with file_path.open("r", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.reader(file))

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

                    if np.isfinite(value):
                        count += 1
                except (ValueError, TypeError):
                    continue

            if count > 0:
                numeric_columns.append((column_index, header))

        if len(numeric_columns) >= 2:
            columns = []

            for column_index, header in numeric_columns:
                values = []

                for data_row in data_rows:
                    if column_index >= len(data_row):
                        continue

                    try:
                        value = float(data_row[column_index])

                        if np.isfinite(value):
                            values.append(value)
                    except (ValueError, TypeError):
                        continue

                columns.append((header, values))

            return headers, data_rows, columns

    return None, None, None

def add_interactive_chart(parent, series, title, x_label, y_label):
    frame = ttk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True)

    chart_frame = ttk.LabelFrame(frame, text=" Interactive chart ")
    chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    sidebar = ttk.LabelFrame(frame, text=" Manage series ", padding=10)
    sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
    
    headers_frame = ttk.Frame(sidebar)
    headers_frame.pack(fill=tk.X, pady=(0, 5))

    list_container = ttk.Frame(sidebar)
    list_container.pack(fill=tk.BOTH, expand=True)

    fig = Figure(figsize=(10, 7))
    ax = fig.add_subplot(111)

    log_x_var = tk.BooleanVar(value=False)

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    toolbar = NavigationToolbar2Tk(canvas, chart_frame)
    toolbar.update()

    def toggle_log_x():
        if log_x_var.get():
            has_positive_x = any(
                np.any(np.asarray(line.get_xdata(), dtype=float) > 0)
                for line in lines.values())

            if not has_positive_x:
                log_x_var.set(False)
                return

            ax.set_xscale("log")
        else:
            ax.set_xscale("linear")

        ax.relim()
        ax.autoscale_view()
        canvas.draw_idle()


    ttk.Label( headers_frame, text="Enable", font=("TkDefaultFont", 8, "bold")).pack(side=tk.LEFT, padx=2)
    ttk.Label( headers_frame, text="Highlight", font=("TkDefaultFont", 8, "bold")).pack(side=tk.LEFT, padx=12)
    ttk.Label( headers_frame, text="Series name", font=("TkDefaultFont", 8, "bold")).pack(side=tk.LEFT, padx=5)

    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(x_label, fontsize=11, labelpad=8)
    ax.set_ylabel(y_label, fontsize=11, labelpad=8)
    ax.grid(True, which="major", color="#B0B0B0", linewidth=0.6, alpha=0.45)
    ax.tick_params(axis="both", which="major", labelsize=10, direction="in")
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    chart_colors = [
        (0.0000, 0.4470, 0.7410),
        (0.8500, 0.3250, 0.0980),
        (0.9290, 0.6940, 0.1250),
        (0.4940, 0.1840, 0.5560),
        (0.4660, 0.6740, 0.1880),
        (0.3010, 0.7450, 0.9330),
        (0.6350, 0.0780, 0.1840)]

    colors = [ chart_colors[i % len(chart_colors)] for i in range(len(series))]
    
    lines = {}
    controls = {}
    current_hover = {"name": None}


    for index, (name, x_values, y_values) in enumerate(series):
        color = colors[index]
        if name == "CFD zero calibration point":
            line, = ax.plot(x_values, y_values, color=color, marker="D", markersize=7, markerfacecolor=color, markeredgecolor=color, markeredgewidth=1.0, linestyle="None", label=name, zorder=10)
        else:
            line, = ax.plot(x_values, y_values, color=color, alpha=1.0, linewidth=1.2, linestyle="-", marker="o", markersize=3, markerfacecolor=color, markeredgecolor=color, label=name)
                        
        lines[name] = line


        row = tk.Frame(list_container)
        row.pack(fill=tk.X, anchor=tk.W, pady=2)

        visible_var = tk.BooleanVar(value=True)
        highlight_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(row, variable=visible_var, command=lambda: refresh_styles()).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Checkbutton(row, variable=highlight_var, command=lambda: refresh_styles()).pack(side=tk.LEFT, padx=(0, 15))

        label_color = matplotlib.colors.to_hex(color) if name != "CFD zero calibration point" else "#000000"
        label = tk.Label( row, text=name, fg=label_color, font=("TkDefaultFont", 9, "bold"), cursor="hand2", anchor="w")
        label.pack(side=tk.LEFT, padx=5)

        controls[name] = {"visible": visible_var, "highlight": highlight_var, "label": label, "row": row}

        row.bind("<Enter>", lambda event, n=name: set_hover(n))
        row.bind("<Leave>", lambda event: clear_hover())
        label.bind("<Enter>", lambda event, n=name: set_hover(n))

    log_x_frame = ttk.Frame(sidebar)
    log_x_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

    ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
    ttk.Checkbutton( log_x_frame, text="Logarithmic X-axis", variable=log_x_var, command=toggle_log_x).pack(anchor=tk.W, padx=5, pady=5)

    def set_hover(name):
        current_hover["name"] = name
        refresh_styles()

    def clear_hover():
        current_hover["name"] = None
        refresh_styles()

    def refresh_styles():
        any_active = any(item["highlight"].get() for item in controls.values()) or current_hover["name"] is not None
        default_bg = list_container.winfo_toplevel().cget("bg")

        for name, line in lines.items():
            item = controls[name]
            visible = item["visible"].get()
            highlighted = item["highlight"].get()
            hovered = name == current_hover["name"]

            line.set_visible(visible)

            if not visible:
                item["label"].config(font=("TkDefaultFont", 9, "bold"))
                item["row"].config(bg=default_bg)
                continue

            if highlighted or hovered:
                line.set_alpha(1.0)
                line.set_linewidth(2.0)
                item["label"].config(font=("TkDefaultFont", 9, "bold", "underline"))
                item["row"].config(bg="#e0e0e0")
            elif any_active:
                line.set_alpha(0.40)
                line.set_linewidth(1.2)
                item["label"].config(font=("TkDefaultFont", 9, "bold"))
                item["row"].config(bg=default_bg)
            else:
                line.set_alpha(1.0)
                line.set_linewidth(1.4)
                item["label"].config(font=("TkDefaultFont", 9, "bold"))
                item["row"].config(bg=default_bg)

        canvas.draw_idle()

    def on_canvas_hover(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            if current_hover["name"] is not None:
                clear_hover()
            return

        closest_name = None
        min_dist = float("inf")

        for name, line in lines.items():
            if not controls[name]["visible"].get():
                continue

            contained, _ = line.contains(event)

            if contained:
                x_data, y_data = line.get_data()

                if len(x_data) == 0:
                    continue

                index = np.argmin(np.abs(np.asarray(x_data) - event.xdata))
                distance = abs(y_data[index] - event.ydata)

                if distance < min_dist:
                    min_dist = distance
                    closest_name = name

        if closest_name != current_hover["name"]:
            current_hover["name"] = closest_name
            refresh_styles()

    canvas.mpl_connect("motion_notify_event", on_canvas_hover)
    canvas.draw()
    refresh_styles()

    return fig, ax, canvas

def add_cfd_out_tab(notebook, session_folder):
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="CFD characterization")

    series = []
    statistics = []

    csv_files = sorted((session_folder / "cfd_out").glob("cfd_*V.csv"))

    for file_path in csv_files:
        samples, times_ns = read_measurement_csv(file_path)

        if not times_ns:
            continue

        values = np.asarray(times_ns, dtype=float)
        series.append((file_path.stem, np.asarray(samples), values))
        statistics.append((file_path.stem, np.mean(values), np.std(values), np.min(values), np.max(values)))

    if series:
        chart_container = ttk.Frame(frame)
        chart_container.pack(fill=tk.BOTH, expand=True)
        add_interactive_chart(chart_container, series, "Time Interval Measurements", "Sample index", "Time interval [ns]")
    else:
        ttk.Label(frame, text="No valid CFD Out data found").pack(padx=10, pady=10)

    if statistics:
        stats_frame = ttk.LabelFrame(frame, text="Measurement Statistics", padding=5)
        stats_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=5)

        columns = ("amplitude", "mean", "std", "min", "max")
        tree = ttk.Treeview(stats_frame, columns=columns, show="headings", height=4)

        for column, heading in zip(columns, ("Amplitude [V]", "Mean [ns]", "Std [ns]", "Min [ns]", "Max [ns]")):
            tree.heading(column, text=heading)
            tree.column(column, width=110, anchor="center")

        scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for name, mean, std, minimum, maximum in statistics:
            amplitude = name.replace("cfd_", "").replace("V", "").replace("_", ".")
            tree.insert("", tk.END, values=(amplitude, f"{mean:.4f}", f"{std:.4f}", f"{minimum:.4f}", f"{maximum:.4f}"))

def add_calibration_tab(notebook, session_folder):
    frame = ttk.Frame(notebook)
    notebook.add(frame, text="Calibration")

    series = []
    x_label = "X"

    for file_path in sorted((session_folder / "calibration").glob("*.csv")):
        _, _, columns = read_generic_csv(file_path)

        if not columns or len(columns) < 2:
            continue

        x_name, x_values = columns[0]
        x_label = x_name

        for y_name, y_values in columns[1:]:
            length = min(len(x_values), len(y_values))

            if length:
                series.append(( f"{file_path.stem}: {y_name}", np.asarray(x_values[:length]), np.asarray(y_values[:length]) * 1e9))

    centroid_x, centroid_y = cfd_zero_calibration_value

    if centroid_x != 0 or centroid_y != 0:
        series.append(( "CFD zero calibration point", np.asarray([centroid_x]), np.asarray([centroid_y * 1e9])))

    if series:
        add_interactive_chart(
            frame, series, "Calibration", x_label, "Measured value [ns]")
    else:
        ttk.Label(frame, text="No plottable calibration CSV data found").pack(padx=10, pady=10)

def add_summary_tab( notebook, session_folder, title, subfolder, filename, value_column, y_label, scale_factor):
    frame = ttk.Frame(notebook)
    notebook.add(frame, text=title)

    file_path = session_folder / subfolder / filename
    amplitudes, values = read_summary_csv(file_path, value_column)
    values = values * scale_factor

    if len(values):
        add_interactive_chart( frame, [(title, amplitudes, values)], title, "|Amplitude [V]|", y_label)

        table = ttk.Treeview( frame, columns=("min", "max"), show="headings", height=1)

        table.heading("min", text="Min")
        table.heading("max", text="Max")

        table.column("min", anchor="center", width=150)
        table.column("max", anchor="center", width=150)

        table.insert( "", "end", values=( f"{min(values):.6g}", f"{max(values):.6g}" ))
        table.pack(fill="x", padx=10, pady=5)

    else:
        ttk.Label( frame, text=f"No valid data found: {file_path}").pack(padx=10, pady=10)

def refresh_result_tabs(session_folder):
    global current_session_folder
    current_session_folder = session_folder
    for tab_id in results_notebook.tabs():
        if results_notebook.tab(tab_id, "text") != "Setup":
            results_notebook.forget(tab_id)

    add_calibration_tab(results_notebook, session_folder)
    add_cfd_out_tab(results_notebook, session_folder)
    add_summary_tab( results_notebook, session_folder, "Mean(Amplitude)", "mean", "mean_vs_amplitude.csv", "mean_time_interval_s", "Mean time interval [ns]", scale_factor=1e9)
    add_summary_tab( results_notebook, session_folder, "Deviation(Amplitude)", "deviation", "deviation_vs_amplitude.csv", "standard_deviation_s", "Standard deviation [ps]", scale_factor=1e12)


def main():
    global current_session_folder, results_notebook
    current_session_folder = find_latest_measurement_folder()

    root = tk.Tk()

    if current_session_folder is not None:
        root.title( f"Measurement Results - " f"{format_measurement_name(current_session_folder.name)}")
    else:
        root.title("Measurement automatization")

    root.state('zoomed')
    
    root.geometry("1250x780") 
    root.minsize(1000, 650)

    style = ttk.Style()
    style.configure("TNotebook.Tab", padding=(12, 7),font=("TkDefaultFont", 10))
    style.configure("TLabelframe.Label", font=("TkDefaultFont", 11, "bold"))
    style.configure("TLabel", font=("TkDefaultFont", 10))
    style.configure("TButton", font=("TkDefaultFont", 10), padding=6)

    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    results_notebook = notebook

    add_setup_tab(notebook)

    if current_session_folder is not None:
        add_calibration_tab(notebook, current_session_folder)
        add_cfd_out_tab(notebook, current_session_folder)

        add_summary_tab( notebook, current_session_folder, "Mean(Amplitude)", "mean", "mean_vs_amplitude.csv", "mean_time_interval_s", "Mean time interval [ns]", scale_factor=1e9)
        add_summary_tab( notebook, current_session_folder, "Deviation(Amplitude)", "deviation", "deviation_vs_amplitude.csv", "standard_deviation_s", "Standard deviation [ps]", scale_factor=1e12)
        

    root.mainloop()

if __name__ == "__main__":
    main()
