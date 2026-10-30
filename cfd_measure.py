import time
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import math
import numpy as np
import measurement_config as config


def generate_amplitudes(amplitude_min, amplitude_max, amplitude_resolution):
    if not config.LOG_MEASURE_ENABLE:
        amplitudes = []
        amplitude = Decimal(str(amplitude_min))
        amplitude_max = Decimal(str(amplitude_max))
        amplitude_resolution = Decimal(str(amplitude_resolution))

        while amplitude <= amplitude_max:
            amplitudes.append(amplitude)
            amplitude += amplitude_resolution

        return amplitudes

    minimum = abs(float(amplitude_min))
    maximum = abs(float(amplitude_max))

    if minimum <= 0 or maximum <= 0:
        raise ValueError("Logarithmic characterization requires non-zero amplitude limits.")

    lower = min(minimum, maximum)
    upper = max(minimum, maximum)

    points_per_decade = int(config.POINTS_PER_DECADE)

    if points_per_decade < 2:
        raise ValueError("POINTS_PER_DECADE must be at least 2.")

    amplitudes = set()
    decade = 10 ** math.floor(math.log10(lower))

    while decade <= upper:
        step = decade * 10 / points_per_decade

        for i in range(points_per_decade):
            value = decade + i * step

            if lower <= value <= upper:
                amplitudes.add(round(value, 12))

        decade *= 10

    amplitudes.add(round(lower, 12))
    amplitudes.add(round(upper, 12))

    return sorted(Decimal(str(value)) for value in amplitudes)

def prepare_measurement_files(dac):
    timestamp = datetime.now().strftime("%d.%m.%Y_%H_%M_%S")
    output_path = Path(config.PMT_OUTPUT_DIR) / f"cfd_out_data_{timestamp}"

    # Create folders for the four future plot tabs.
    calibration_dir = output_path / "calibration"
    cfd_out_dir = output_path / "cfd_out"
    mean_dir = output_path / "mean"
    deviation_dir = output_path / "deviation"

    for directory in ( calibration_dir, cfd_out_dir, mean_dir, deviation_dir):
        directory.mkdir(parents=True, exist_ok=False)

    # dac_config = dac.read_config()

    amplitude_min = Decimal(str(config.PMT_AMPLITUDE_MIN))
    amplitude_max = Decimal(str(config.PMT_AMPLITUDE_MAX))
    amplitude_resolution = Decimal(str(config.PMT_AMPLITUDE_RESOLUTION))

    if amplitude_resolution <= 0:
        raise ValueError("amplitude_resolution must be greater than 0")

    if amplitude_max < amplitude_min:
        raise ValueError("amplitude_max must be greater than or equal to amplitude_min")

    amplitudes = generate_amplitudes(amplitude_min, amplitude_max, amplitude_resolution)

    files = {}

    for amplitude in amplitudes:
        amplitude_positive = abs(amplitude)
        amplitude_str = format(amplitude_positive.quantize(Decimal("0.1")), "f").replace(".", "_")
        file_path = cfd_out_dir / f"cfd_{amplitude_str}V.csv"

        with file_path.open("w", newline="", encoding="utf-8") as csv_file:
            now = datetime.now()

            csv_file.write(f"Measurement date: {now.strftime('%d.%m.%Y')}\n")
            csv_file.write(f"Measurement time: {now.strftime('%H:%M:%S')}\n")
            csv_file.write("\n")

            # csv_file.write("DAC configuration:\n")
            # csv_file.write(dac_config)

            # if not dac_config.endswith("\n"):
            #     csv_file.write("\n")

            csv_file.write("\n")

            writer = csv.writer(csv_file)
            writer.writerow(["sample_index", "time_interval_s"])

        files[amplitude] = file_path

    return output_path, files

def cfd_calibrate(dac_obj, generator_obj, oscilloscope_obj, output_path, refresh_console=None):

    # Get the calibration folder
    calibration_path = output_path / "calibration"
    calibration_path.mkdir(parents=True, exist_ok=True)

    # Create the calibration CSV file
    calibration_file = calibration_path / "calibration.csv"

    with calibration_file.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        # Write the CSV header.
        header = ["dac_code"]

        for amplitude in config.PMT_AMPLITUDES:
            header.append(f"time_interval_{amplitude:.3f}V_s")

        writer.writerow(header)

        # Store measurements for each DAC code.
        results = {}
        increment_counter = 0
        for amplitude_value in config.PMT_AMPLITUDES:

            # Configure the generator for the selected PMT amplitude.
            amplitude_abs = abs(amplitude_value)

            if config.PMT_POSITIVE_POLARITY:
                generator_low = 0.0
                generator_polarity = "NORMAL"
            else:
                generator_low = -amplitude_abs
                generator_polarity = "INVERTED"

            generator_obj.generate_continuous_pulse(channel=1,
                                                    amplitude=amplitude_abs,
                                                    period=config.PMT_PERIOD,
                                                    width=config.PMT_WIDTH,
                                                    low=generator_low,
                                                    rise_time=config.PMT_RISE_TIME,
                                                    fall_time=config.PMT_FALL_TIME,
                                                    delay=config.PMT_DELAY)

            generator_obj.set_polarization( channel=1, polarization=generator_polarity)
            
            print(f"CFD calibrate, amplitude: {amplitude_value}")
            time.sleep(config.PMT_SETTLING_TIME)

            # Iterate through selected DAC codes.
            for dac_code in range( config.DAC_START_CODE, config.DAC_STOP_CODE + 1, config.DAC_INCREMENT_STEP):
                # Set the DAC value.
                dac_obj.write_single( inst=config.DAC_INSTANCE,
                                      channel="CFD_ZERO",
                                      value=dac_code )

                print(f"CFD characterize, dac code: 0x{dac_code}")
                time.sleep(config.DAC_SETTLING_DELAY)
                
                total_time_interval = 0.0

                for j in range(config.DAC_SAMPLES_PER_POINT):
                    while True:
                        time_interval = oscilloscope_obj.get_time_interval_measurement()

                        if time_interval > 1e30:
                            print( f"Measured too high time counter. Step: {increment_counter}, " f"measured time: {time_interval}.")

                        if time_interval < 0:
                            print( f"Negative time interval measured. Step: {increment_counter}, " f"measured time: {time_interval}. Repeating measurement.")
                            time.sleep(config.PMT_MEASURE_DELAY)
                            continue

                        total_time_interval += time_interval
                        increment_counter += 1
                        time.sleep(config.PMT_MEASURE_DELAY)
                        break

                mean_time_interval = (total_time_interval / config.DAC_SAMPLES_PER_POINT)
                increment_counter = 0

                # Store the mean measurement.
                if dac_code not in results:
                    results[dac_code] = []

                results[dac_code].append(mean_time_interval)

        # Write all results to the CSV file.
        for dac_code in range( config.DAC_START_CODE, config.DAC_STOP_CODE + 1, config.DAC_INCREMENT_STEP):
            writer.writerow([dac_code] + results[dac_code])

    dac_codes = sorted(results.keys())
    measurements = [[results[dac_code][i] for dac_code in dac_codes] for i in range(3)]
    centroid_x, centroid_y = calculate_triangle_centroid( dac_codes, measurements)

    print("########################")
    print("# Calibration finished #")
    print("########################")

    return centroid_x, centroid_y

def cfd_characterize(dac_obj, generator_obj, oscilloscope_obj,  files,  output_path, refresh_console=None):
    
    #Set dac output voltages:
    dac_obj.write_all(config.DAC_INSTANCE, config.DAC_A, config.DAC_B, config.DAC_C, config.DAC_D)

    #Update headers
    dac_config = dac_obj.read_config()

    for file_path in files.values():
        with file_path.open("r", encoding="utf-8") as csv_file:
            lines = csv_file.readlines()

        with file_path.open("w", newline="", encoding="utf-8") as csv_file:
            csv_file.write("DAC configuration:\n")
            csv_file.write(dac_config)

            if not dac_config.endswith("\n"):
                csv_file.write("\n")

            csv_file.write("\n")
            csv_file.writelines(lines)


    time.sleep(config.DAC_SETTLING_DELAY)
    increment_counter = 0
    # Measurement loop
    for amplitude in files:
        amplitude_value = float(amplitude)

        # Configure the generator for the selected PMT amplitude.
        amplitude_abs = abs(amplitude_value)

        if config.PMT_POSITIVE_POLARITY:
            generator_low = 0.0
            generator_polarity = "NORMAL"
        else:
            generator_low = -amplitude_abs
            generator_polarity = "INVERTED"

        generator_obj.generate_continuous_pulse(channel=1,
                                                amplitude=amplitude_abs,
                                                period=config.PMT_PERIOD,
                                                width=config.PMT_WIDTH,
                                                low=generator_low,
                                                rise_time=config.PMT_RISE_TIME,
                                                fall_time=config.PMT_FALL_TIME,
                                                delay=config.PMT_DELAY)

        generator_obj.set_polarization( channel=1, polarization=generator_polarity)
        
        print(f"CFD characterize, amplitude: {amplitude_value}")

        time.sleep(config.PMT_SETTLING_TIME)

        
        for j in range(config.PMT_AMPLITUDE_SAMPLE_NUMBER):
            while True:
                time_interval = oscilloscope_obj.get_time_interval_measurement()

                if time_interval > 1e30:
                    print( f"Measured too high time counter. Step: {increment_counter}, measured time: {time_interval}")

                if time_interval < 0:
                    print( f"Negative time interval measured. Step: {increment_counter}, measured time: {time_interval}. Repeating measurement")
                    time.sleep(config.PMT_MEASURE_DELAY)
                    continue

                with files[amplitude].open("a", newline="", encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow([j + 1, time_interval])

                increment_counter += 1
                time.sleep(config.PMT_MEASURE_DELAY)

                break

        increment_counter = 0

    print("#############################")
    print("# Characterization finished #")
    print("#############################")

def calculate_triangle_centroid(dac_codes, measurements):
    if len(measurements) != 3:
        return 0.0, 0.0

    x = np.asarray(dac_codes, dtype=float)

    if x.ndim != 1 or len(x) < 3:
        return 0.0, 0.0

    if not np.all(np.isfinite(x)):
        return 0.0, 0.0

    if len(np.unique(x)) != len(x):
        return 0.0, 0.0

    if not np.all(np.diff(x) > 0):
        print("error detected")
        order = np.argsort(x)
        x = x[order]
    else:
        order = None

    curves = []

    for curve in measurements:
        y = np.asarray(curve, dtype=float)

        if y.ndim != 1 or len(y) != len(dac_codes):
            return 0.0, 0.0

        if order is not None:
            y = y[order]

        valid = np.isfinite(x) & np.isfinite(y)

        if np.count_nonzero(valid) < 3:
            return 0.0, 0.0

        curves.append((x[valid], y[valid]))

    x_min = float(np.min(x))
    x_max = float(np.max(x))
    x_center = (x_min + x_max) / 2.0
    x_scale = (x_max - x_min) / 2.0

    if x_scale <= 0:
        return 0.0, 0.0

    fitted_lines = []

    for curve_x, curve_y in curves:
        z = (curve_x - x_center) / x_scale

        slope, intercept = np.polyfit(z, curve_y, 1)

        if not np.isfinite(slope) or not np.isfinite(intercept):
            return 0.0, 0.0

        fitted_lines.append((slope, intercept))

    vertices = []

    for i, j in ((0, 1), (0, 2), (1, 2)):
        slope1, intercept1 = fitted_lines[i]
        slope2, intercept2 = fitted_lines[j]

        denominator = slope1 - slope2
        slope_scale = max(abs(slope1), abs(slope2))

        if slope_scale == 0 or abs(denominator) <= (100 * np.finfo(float).eps * slope_scale):
            return 0.0, 0.0

        z_intersection = (intercept2 - intercept1) / denominator
        x_intersection = x_center + z_intersection * x_scale
        y_intersection = slope1 * z_intersection + intercept1

        if not np.isfinite(x_intersection) or not np.isfinite(y_intersection):
            return 0.0, 0.0

        tolerance_x = 1e-9 * max(1.0, x_max - x_min)

        if x_intersection < x_min - tolerance_x:
            return 0.0, 0.0

        if x_intersection > x_max + tolerance_x:
            return 0.0, 0.0

        vertices.append((x_intersection, y_intersection))

    vertices = np.asarray(vertices, dtype=float)

    y_values = np.concatenate([curve_y for _, curve_y in curves])
    y_scale = float(np.max(y_values) - np.min(y_values))

    if not np.isfinite(y_scale) or y_scale <= 0:
        return 0.0, 0.0

    normalized = np.column_stack(((vertices[:, 0] - x_center) / x_scale,(vertices[:, 1] - np.mean(y_values)) / y_scale))

    for i in range(3):
        for j in range(i + 1, 3):
            distance = np.linalg.norm(normalized[i] - normalized[j])

            if distance < 1e-6:
                return 0.0, 0.0

    # Check the triangle area in normalized coordinates.
    area = abs((normalized[1, 0] - normalized[0, 0])
                * (normalized[2, 1] - normalized[0, 1])
                - (normalized[2, 0] - normalized[0, 0])
                * (normalized[1, 1] - normalized[0, 1])
                ) / 2.0

    if not np.isfinite(area) or area < 1e-10:
        return 0.0, 0.0

    centroid_x = float(np.mean(vertices[:, 0]))
    centroid_y = float(np.mean(vertices[:, 1]))

    return centroid_x, centroid_y

def process_measurement_results(files, output_path):
    mean_path = output_path / "mean" / "mean_vs_amplitude.csv"
    deviation_path = output_path / "deviation" / "deviation_vs_amplitude.csv"

    mean_rows = []
    deviation_rows = []

    for amplitude, file_path in files.items():
        time_intervals = []

        with file_path.open("r", newline="", encoding="utf-8") as csv_file:
            lines = csv_file.readlines()

        header_index = None

        for index, line in enumerate(lines):
            if line.strip() == "sample_index,time_interval_s":
                header_index = index
                break

        if header_index is not None:
            reader = csv.DictReader(lines[header_index:])

            for row in reader:
                try:
                    value = float(row["time_interval_s"])
                except (ValueError, TypeError, KeyError):
                    continue

                if not math.isfinite(value):
                    continue

                if abs(value) >= 1e30:
                    continue

                time_intervals.append(value)

        # Count valid measurements.
        sample_count = len(time_intervals)

        # Calculate mean and standard deviation.
        if sample_count == 0:
            mean_value = None
            standard_deviation = None

        else:
            # Calculate mean.
            total = 0
            for value in time_intervals:
                total = total + value
            mean_value = total / sample_count

            # Calculate variance 
            variance_sum = 0

            for value in time_intervals:
                difference = value - mean_value
                squared_difference = difference * difference
                variance_sum = variance_sum + squared_difference

            variance = variance_sum / sample_count

            # Calculate standard deviation.
            standard_deviation = math.sqrt(variance)

        # Store results for this amplitude.
        mean_rows.append([abs(float(amplitude)), mean_value, sample_count])
        deviation_rows.append([abs(float(amplitude)), standard_deviation, sample_count])

    # Save mean results to CSV.
    with mean_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow([ "amplitude_v", "mean_time_interval_s", "valid_sample_count" ])
        writer.writerows(mean_rows)

    # Save standard deviation results to CSV.
    with deviation_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([ "amplitude_v", "standard_deviation_s", "valid_sample_count"])
        writer.writerows(deviation_rows)

def configure_instruments(dac_obj, generator_obj, oscilloscope_obj):
    
    # Configure Oscilloscope
    oscilloscope_obj.enable_channel(1, True) 
    oscilloscope_obj.enable_channel(2, True) 
    oscilloscope_obj.enable_channel(3, True) 
    oscilloscope_obj.enable_channel(4, True)   
    
    oscilloscope_obj.set_amplitude_scale(1, 0.200) # 200mV / div
    oscilloscope_obj.set_amplitude_scale(2, 0.200) # 200 mV / div
    oscilloscope_obj.set_amplitude_scale(3, 0.200) # 200mV / div
    oscilloscope_obj.set_amplitude_scale(4, 0.050) # 50 mV / div
    
    oscilloscope_obj.set_time_scale(5E-9) # 5ns / div

    oscilloscope_obj.set_trigger(4, edge="RISing", level=0.8) # 800 mV
    
    oscilloscope_obj.add_time_interval_measurement( 4,
                                                    3,
                                                    start_edge="RISing",
                                                    stop_edge="RISing", 
                                                    start_edge_number=1,
                                                    stop_edge_number=1,
                                                    start_position="MIDDle",
                                                    stop_position="MIDDle")
    
    # Configure generator
    generator_obj.enable_trigger()