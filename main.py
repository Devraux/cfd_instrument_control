import gen_cmd
import scope_cmd
import cfd_calib
import dac8554_api
import time
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import math

# Measurement parameters
PMT_AMPLITUDE_MIN = -2 # Min pmt amplitude
PMT_AMPLITUDE_MAX = -0.5 # Max pmt amplitude
PMT_AMPLITUDE_RESOLUTION = 0.5 # Amplitude increase value resolution
PMT_AMPLITUDE_SAMPLE_NUMBER = 100 # Number of samples measured for picked amplitude
PMT_OUTPUT_DIR = "./measurements_data"
PMT_PERIOD = 1E-5
PMT_WIDTH = 8.2E-9
PMT_RISE_TIME = 3.5E-9
PMT_FALL_TIME = 8.4E-9
PMT_MEASURE_DELAY = 20e-9
PMT_DELAY = 3.5e-9
CALIBRATION_ENABLE = False

DAC_A = 0x7FFF
DAC_B = 0x7FFF
DAC_C = 0xD034
DAC_D = 0xF100


def prepare_measurement_files(dac, amplitude_min, amplitude_max, amplitude_resolution, sample_number, output_dir="./measurements_data"):
    timestamp = datetime.now().strftime("%d.%m.%Y_%H_%M_%S")
    output_path = Path(output_dir) / f"cfd_out_data_{timestamp}"

    # Create folders for the four future plot tabs.
    calibration_dir = output_path / "calibration"
    cfd_out_dir = output_path / "cfd_out"
    mean_dir = output_path / "mean"
    deviation_dir = output_path / "deviation"

    for directory in (
        calibration_dir,
        cfd_out_dir,
        mean_dir,
        deviation_dir
    ):
        directory.mkdir(parents=True, exist_ok=False)

    config = dac.read_config()

    amplitude_min = Decimal(str(amplitude_min))
    amplitude_max = Decimal(str(amplitude_max))
    amplitude_resolution = Decimal(str(amplitude_resolution))

    if amplitude_resolution <= 0:
        raise ValueError("amplitude_resolution must be greater than 0")

    if amplitude_max < amplitude_min:
        raise ValueError(
            "amplitude_max must be greater than or equal to amplitude_min"
        )

    if sample_number <= 0:
        raise ValueError("sample_number must be greater than 0")

    amplitudes = []
    amplitude = amplitude_min

    while amplitude <= amplitude_max:
        amplitudes.append(amplitude)
        amplitude += amplitude_resolution

    files = {}

    for amplitude in amplitudes:
        amplitude_str = format(amplitude, ".1f").replace(".", "_")
        file_path = cfd_out_dir / f"cfd_{amplitude_str}V.csv"

        with file_path.open(
            "w", newline="", encoding="utf-8"
        ) as csv_file:
            now = datetime.now()

            csv_file.write(
                f"Measurement date: {now.strftime('%d.%m.%Y')}\n"
            )
            csv_file.write(
                f"Measurement time: {now.strftime('%H:%M:%S')}\n"
            )
            csv_file.write("\n")

            csv_file.write("DAC configuration:\n")
            csv_file.write(config)

            if not config.endswith("\n"):
                csv_file.write("\n")

            csv_file.write("\n")

            writer = csv.writer(csv_file)
            writer.writerow(["sample_index", "time_interval_s"])

        files[amplitude] = file_path

    return output_path, files

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
        mean_rows.append([ float(amplitude), mean_value, sample_count ])

        deviation_rows.append([ float(amplitude), standard_deviation, sample_count ])

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




def main():
    generator = gen_cmd.Generator() 
    oscilloscope = scope_cmd.Oscilloscope()
    dac = dac8554_api.dac8554_api()

    # Set dac output voltages:
    dac.write_all(0, DAC_A, DAC_B, DAC_C, DAC_D)
    
    # Create output folder structure
    output_path, files = prepare_measurement_files(dac, 
                                                   PMT_AMPLITUDE_MIN, 
                                                   PMT_AMPLITUDE_MAX, 
                                                   PMT_AMPLITUDE_RESOLUTION,
                                                   PMT_AMPLITUDE_SAMPLE_NUMBER, 
                                                   PMT_OUTPUT_DIR)  

    # Configure Oscilloscope
    oscilloscope.enable_channel(1, True) 
    oscilloscope.enable_channel(2, True) 
    oscilloscope.enable_channel(3, True) 
    oscilloscope.enable_channel(4, True)   
    
    oscilloscope.set_amplitude_scale(1, 0.200) # 200mV / div
    oscilloscope.set_amplitude_scale(2, 0.200) # 200 mV / div
    oscilloscope.set_amplitude_scale(3, 0.200) # 200mV / div
    oscilloscope.set_amplitude_scale(4, 0.050) # 50 mV / div
    
    oscilloscope.set_time_scale(5E-9) # 5ns / div

    oscilloscope.set_trigger(4, edge="RISing", level=0.8)
    
    oscilloscope.add_time_interval_measurement( 4,
                                                3,
                                                start_edge="RISing",
                                                stop_edge="RISing", 
                                                start_edge_number=1,
                                                stop_edge_number=1,
                                                start_position="MIDDle",
                                                stop_position="MIDDle")
    
    # Configure generator
    generator.enable_trigger()
    generator.set_polarization(channel=1, polarization="INVERTED")

    # Calibrate setup
    cfd_calib.calibrate(dac_obj=dac,
                        generator_obj=generator,
                        oscilloscope_obj=oscilloscope,
                        output_path=output_path,
                        dac_start_code=50_000,
                        dac_stop_code=54_000)

    # Measurement loop
    for amplitude in files:
        amplitude_value = float(amplitude)
        
        generator.generate_continuous_pulse(channel=1,
                                            amplitude=abs(amplitude_value),
                                            period=PMT_PERIOD,
                                            width=PMT_WIDTH,
                                            low=amplitude_value,
                                            rise_time=PMT_RISE_TIME,
                                            fall_time=PMT_FALL_TIME,
                                            delay=PMT_DELAY)

        for j in range(PMT_AMPLITUDE_SAMPLE_NUMBER):
            time_interval = oscilloscope.get_time_interval_measurement()

            with files[amplitude].open("a", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow([j + 1, time_interval])

            time.sleep(PMT_MEASURE_DELAY)

    # Process results after all amplitudes have been measured.
    process_measurement_results(files, output_path)

if __name__ == "__main__":
    main()