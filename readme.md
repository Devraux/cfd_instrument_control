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


BUILD SCRIPT

mkdir -p release/build_env

if [ ! -f release/build_env/.venv_build/Scripts/python.exe ]; then
    python -m venv release/build_env/.venv_build || exit 1
fi

PY="release/build_env/.venv_build/Scripts/python.exe"

"$PY" -m pip install --upgrade pip || exit 1
"$PY" -m pip install --upgrade pyinstaller numpy matplotlib pyserial pyvisa || exit 1

"$PY" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --hidden-import=serial \
  --name cfd_instrument_control \
  --distpath release/build_env/dist \
  --workpath release/build_env/build \
  --specpath release/build_env \
  main.py || exit 1

echo "release/build_env/dist/cfd_instrument_control.exe"
