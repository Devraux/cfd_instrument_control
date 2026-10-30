from pathlib import Path
import sys

PMT_AMPLITUDE_MIN = 0.5
PMT_AMPLITUDE_MAX = 2.0
PMT_AMPLITUDE_RESOLUTION = 0.1
PMT_POSITIVE_POLARITY = False
PMT_AMPLITUDE_SAMPLE_NUMBER = 100

PMT_AMPLITUDE_1 = 0.2
PMT_AMPLITUDE_2 = 0.4
PMT_AMPLITUDE_3 = 2.0
PMT_AMPLITUDES = [PMT_AMPLITUDE_1, PMT_AMPLITUDE_2, PMT_AMPLITUDE_3]

PMT_PERIOD = 1E-5
PMT_DELAY = 3.5E-9
PMT_MEASURE_DELAY = 1E-3 # Time gap between two timing parameter readings
PMT_RISE_TIME = 3.5E-9
PMT_WIDTH = 8.2E-9
PMT_FALL_TIME = 8.4E-9
PMT_SETTLING_TIME = 250E-3 # Time between setting generator value and reading first timing value

DAC_START_CODE = 45000
DAC_STOP_CODE = 60000
DAC_INCREMENT_STEP = 1000
DAC_SAMPLES_PER_POINT = 100
DAC_INSTANCE = 0
DAC_SETTLING_DELAY = 10E-3 # Time between setting DAC value and reading first timing value

DAC_A = 0x7FFF # Test point
DAC_B = 0x7FFF
DAC_C = 0xD3B8 # CFD_ZERO
DAC_D = 0xF4D8 # CFD_THRESHOLD

LOG_MEASURE_ENABLE = False
POINTS_PER_DECADE = 10

HEX_FORMAT = True  # True = HEX, False = DEC

PMT_OUTPUT_DIR = "./measurements_data"
# .EXE final version important change
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

PMT_OUTPUT_DIR = str(APP_DIR / "measurements_data")