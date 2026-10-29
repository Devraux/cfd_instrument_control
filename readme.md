# PMT Timing Measurement

Python script for automated PMT timing measurements using a Tektronix AFG3000 series function generator, an Agilent Infiniium 90000 oscilloscope, and a DAC8554 interface.

## Hardware Configuration

- **Communication interface:** GPIF
- **Function generator:** Tektronix AFG3000 series
- **Generator address:** `TCPIP0::131.29.71.191::inst0::INSTR`
- **Oscilloscope:** Agilent Infiniium 90000 series
- **Oscilloscope address:** `TCPIP0::131.29.71.191::inst0::INSTR`
- **DAC interface:** DAC8554 via USB serial (Raspberry Pi Pico CLI)

## Measurement Configuration

Measurement parameters are configured using the constants at the beginning of the Python script:

```python
PMT_PULSES_COUNT = 100
PMT_AMPLITUDE_MIN = 1
PMT_AMPLITUDE_MAX = 2
PMT_AMPLITUDE_RESOLUTION = 0.2
PMT_AMPLITUDE_SAMPLE_NUMBER = 100
PMT_OUTPUT_DIR = "./measurements_data"
PMT_PERIOD = 1E-3
PMT_WIDTH = 1E-6
PMT_RISE_TIME = 10E-9
PMT_FALL_TIME = 10E-9
PMT_MEASURE_DELAY = 0
```

- `PMT_PULSES_COUNT` — number of timing measurements per amplitude.
- `PMT_AMPLITUDE_MIN`, `PMT_AMPLITUDE_MAX` — minimum and maximum generator amplitudes.
- `PMT_AMPLITUDE_RESOLUTION` — amplitude step between consecutive measurement series.
- `PMT_AMPLITUDE_SAMPLE_NUMBER` — configured number of samples per amplitude.
- `PMT_OUTPUT_DIR` — output directory for measurement data.
- `PMT_PERIOD` — pulse period in seconds.
- `PMT_WIDTH` — pulse width in seconds.
- `PMT_RISE_TIME`, `PMT_FALL_TIME` — pulse rise and fall times in seconds.
- `PMT_MEASURE_DELAY` — delay between consecutive measurements in seconds.

## Output

Each run creates a timestamped directory inside `PMT_OUTPUT_DIR`, containing one CSV file per amplitude. Each file includes the measurement date and time, DAC configuration, and measured time intervals.

## Requirements
Install the required Python packages:

```bash
pip install pyvisa pyserial
```
Ensure that the required VISA backend and instrument connections are configured before running the script.


CFD calibrate, amplitude: -0.2
CFD characterize, dac code: 0x45000
Measured too high time counter. Step: 2, measured time:9.99999e+37
Measured too high time counter. Step: 24, measured time:9.99999e+37
Measured too high time counter. Step: 36, measured time:9.99999e+37
Measured too high time counter. Step: 56, measured time:9.99999e+37
Measured too high time counter. Step: 60, measured time:9.99999e+37
CFD characterize, dac code: 0x46000
Measured too high time counter. Step: 20, measured time:9.99999e+37
Measured too high time counter. Step: 27, measured time:9.99999e+37
Measured too high time counter. Step: 43, measured time:9.99999e+37
Measured too high time counter. Step: 52, measured time:9.99999e+37
Measured too high time counter. Step: 92, measured time:9.99999e+37
Measured too high time counter. Step: 95, measured time:9.99999e+37
CFD characterize, dac code: 0x47000
Measured too high time counter. Step: 28, measured time:9.99999e+37
Measured too high time counter. Step: 45, measured time:9.99999e+37
Measured too high time counter. Step: 69, measured time:9.99999e+37
CFD characterize, dac code: 0x48000
Measured too high time counter. Step: 38, measured time:9.99999e+37
Measured too high time counter. Step: 53, measured time:9.99999e+37
Measured too high time counter. Step: 87, measured time:9.99999e+37
CFD characterize, dac code: 0x49000
Measured too high time counter. Step: 11, measured time:9.99999e+37
Measured too high time counter. Step: 99, measured time:9.99999e+37
CFD characterize, dac code: 0x50000
CFD characterize, dac code: 0x51000
CFD characterize, dac code: 0x52000
CFD characterize, dac code: 0x53000
CFD characterize, dac code: 0x54000
CFD characterize, dac code: 0x55000
CFD characterize, dac code: 0x56000
CFD characterize, dac code: 0x57000
CFD characterize, dac code: 0x58000
CFD characterize, dac code: 0x59000
CFD characterize, dac code: 0x60000
CFD calibrate, amplitude: -0.4
CFD characterize, dac code: 0x45000
CFD characterize, dac code: 0x46000
CFD characterize, dac code: 0x47000
CFD characterize, dac code: 0x48000
CFD characterize, dac code: 0x49000
CFD characterize, dac code: 0x50000
CFD characterize, dac code: 0x51000
CFD characterize, dac code: 0x52000
CFD characterize, dac code: 0x53000
CFD characterize, dac code: 0x54000
CFD characterize, dac code: 0x55000
CFD characterize, dac code: 0x56000
CFD characterize, dac code: 0x57000
CFD characterize, dac code: 0x58000
CFD characterize, dac code: 0x59000
CFD characterize, dac code: 0x60000
CFD calibrate, amplitude: -2.0
CFD characterize, dac code: 0x45000
CFD characterize, dac code: 0x46000
CFD characterize, dac code: 0x47000
CFD characterize, dac code: 0x48000
CFD characterize, dac code: 0x49000
CFD characterize, dac code: 0x50000
CFD characterize, dac code: 0x51000
CFD characterize, dac code: 0x52000
CFD characterize, dac code: 0x53000
CFD characterize, dac code: 0x54000
CFD characterize, dac code: 0x55000
CFD characterize, dac code: 0x56000
CFD characterize, dac code: 0x57000
CFD characterize, dac code: 0x58000
CFD characterize, dac code: 0x59000
CFD characterize, dac code: 0x60000
########################
# Calibration finished #
########################




python -m venv .venv_build
.\.venv_build\Scripts\python.exe -m pip install --upgrade pip
.\.venv_build\Scripts\python.exe -m pip install pyinstaller numpy matplotlib
.\.venv_build\Scripts\python.exe -m PyInstaller --clean --noconfirm --onedir --name cfd_instrument_control main.py