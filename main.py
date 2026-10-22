import gen_cmd
import scope_cmd
import dac8554_api
import time
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Measurement parameters
PMT_AMPLITUDE_MIN = -2 # Min pmt amplitude
PMT_AMPLITUDE_MAX = -0.5 # Max pmt amplitude
PMT_AMPLITUDE_RESOLUTION = 0.1 # Amplitude increase value resolution
PMT_AMPLITUDE_SAMPLE_NUMBER = 1000 # Number of samples measured for picked amplitude
PMT_OUTPUT_DIR = "./measurements_data"
PMT_PERIOD = 1E-6
PMT_WIDTH = 200E-9
PMT_RISE_TIME = 10E-9
PMT_FALL_TIME = 10E-9
PMT_MEASURE_DELAY = 20e-9
PMT_DELAY = 20e-9

DAC_A = 0x7FFF
DAC_B = 0x7FFF
DAC_C = 0x7FFF
DAC_D = 0x7FFF


def prepare_measurement_files(  dac,
                                amplitude_min,
                                amplitude_max,
                                amplitude_resolution,
                                sample_number,
                                output_dir="./measurements_data"):
    
    timestamp = datetime.now().strftime("%d.%m.%Y_%H_%M_%S")
    output_path = Path(output_dir) / f"cfd_out_data_{timestamp}"
    output_path.mkdir(parents=True, exist_ok=False)

    config = dac.read_config()

    amplitude_min = Decimal(str(amplitude_min))
    amplitude_max = Decimal(str(amplitude_max))
    amplitude_resolution = Decimal(str(amplitude_resolution))

    if amplitude_resolution <= 0:
        raise ValueError("amplitude_resolution must be greater than 0")

    if amplitude_max < amplitude_min:
        raise ValueError("amplitude_max must be greater than or equal to amplitude_min")

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
        if not amplitude_str:
            amplitude_str = "0"

        file_path = output_path / f"cfd_{amplitude_str}V.csv"

        with file_path.open("w", newline="", encoding="utf-8") as csv_file:
            now = datetime.now()

            csv_file.write(f"Measurement date: {now.strftime('%d.%m.%Y')}\n")
            csv_file.write(f"Measurement time: {now.strftime('%H:%M:%S')}\n")
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


def main():
    generator = gen_cmd.Generator() 
    oscilloscope = scope_cmd.Oscilloscope()
    dac = dac8554_api.dac8554_api()

    # Create output folder structure
    output_path, files = prepare_measurement_files(dac, 
                                                   PMT_AMPLITUDE_MIN, 
                                                   PMT_AMPLITUDE_MAX, 
                                                   PMT_AMPLITUDE_RESOLUTION,
                                                   PMT_AMPLITUDE_SAMPLE_NUMBER, 
                                                   PMT_OUTPUT_DIR)  

    # Set dac output voltages:
    dac.write_all(0, DAC_A, DAC_B, DAC_C, DAC_D)

    # Configure Oscilloscope
    oscilloscope.enable_channel(1, True) 
    oscilloscope.enable_channel(2, True) 
    oscilloscope.enable_channel(3, True) 
    oscilloscope.enable_channel(4, True)   
    
    oscilloscope.set_amplitude_scale(1, 0.200) # 200mV / div
    oscilloscope.set_amplitude_scale(2, 0.200) # 50 mV / div
    oscilloscope.set_amplitude_scale(3, 0.200) # 200mV / div
    oscilloscope.set_amplitude_scale(4, 0.050) # 50 mV / div
    
    oscilloscope.set_time_scale(5E-9) # 5ns / div

    oscilloscope.set_trigger(4, edge="RISing", level="MIDDle")
    
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



if __name__ == "__main__":
    main()