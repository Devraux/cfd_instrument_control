# from gen_cmd import Generator

# generator = Generator()

# try:
#     print("Configuring continuous pulse signal on channel 1...")

#     generator.enable_trigger()
    
#     generator.generate_continuous_pulse(
#         channel=1,
#         amplitude=2.0,
#         period=1e-6,       # 1 us = 1 MHz
#         width=200e-9,      # 200 ns
#         low=-1.0,
#         rise_time=10e-9,   # 10 ns
#         fall_time=10e-9,   # 10 ns
#         delay=20e-9
#     )

# except Exception as error:
#     print(f"Generator error: {error}")
#     raise



import time
from scope_cmd import Oscilloscope

scope = Oscilloscope()

try:
    scope.enable_channel(4, True)
    scope.enable_channel(1, True)

    scope.add_time_interval_measurement(
        first_channel=4,
        second_channel=1,
        start_edge="RISing",
        stop_edge="RISing",
        start_edge_number=1,
        stop_edge_number=1,
        start_position="MIDDle",
        stop_position="MIDDle"
    )

    print("Reading time interval measurements...")

    for i in range(10):
        time_interval = scope.get_time_interval_measurement()
        print(f"Measurement {i + 1}: {time_interval:.9g} s")
        time.sleep(0.1)

finally:
    scope.close()