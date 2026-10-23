
import csv
import time

PMT_PERIOD = 1E-5
PMT_WIDTH = 8.2E-9
PMT_RISE_TIME = 3.5E-9
PMT_FALL_TIME = 8.4E-9
PMT_MEASURE_DELAY = 20e-9
PMT_DELAY = 3.5e-9

PMT_AMPLITUDE_1 = -0.100
PMT_AMPLITUDE_2 = -0.200
PMT_AMPLITUDE_3 = -1.000
PMT_AMPLITUDES = [PMT_AMPLITUDE_1, PMT_AMPLITUDE_2, PMT_AMPLITUDE_3]



def calibrate( dac_obj, generator_obj, oscilloscope_obj, output_path, dac_start_code=45_000, dac_stop_code=60_000):
    # Get the calibration folder.
    calibration_path = output_path / "calibration"
    calibration_path.mkdir(parents=True, exist_ok=True)

    # Create the calibration CSV file.
    calibration_file = calibration_path / "calibration.csv"

    with calibration_file.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        # Write the CSV header.
        header = ["dac_code"]

        for amplitude in PMT_AMPLITUDES:
            header.append(f"time_interval_{amplitude:.3f}V_s")

        writer.writerow(header)

        # Store measurements for each DAC code.
        results = {}

        for amplitude_value in PMT_AMPLITUDES:
            print(f"PMT amplitude {amplitude_value}")
            # Configure the generator for the selected PMT amplitude.
            generator_obj.generate_continuous_pulse(channel=1,
                                                    amplitude=abs(amplitude_value),
                                                    period=PMT_PERIOD,
                                                    width=PMT_WIDTH,
                                                    low=amplitude_value,
                                                    rise_time=PMT_RISE_TIME,
                                                    fall_time=PMT_FALL_TIME,
                                                    delay=PMT_DELAY)
            time.sleep(0.04)
            # Iterate through all DAC codes.
            for dac_code in range(dac_start_code, dac_stop_code + 1, 100):
                print(f"DAC value: {dac_code}")
                # Set the DAC value.
                dac_obj.write_single(
                    inst=0,
                    channel="CFD_ZERO",
                    value=dac_code
                )

                # Measure the time interval.
                time_interval = oscilloscope_obj.get_time_interval_measurement()

                # Store the measurement.
                if dac_code not in results:
                    results[dac_code] = []

                results[dac_code].append(time_interval)
                time.sleep(0.04)

        # Write all results to the CSV file.
        for dac_code in range(dac_start_code, dac_stop_code + 1, 100):
            writer.writerow([dac_code] + results[dac_code])

