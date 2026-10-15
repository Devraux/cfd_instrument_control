import gen_cmd
import scope_cmd
import dac8554_api

# Measurement parameters
PMT_PULSES_COUNT = 100 # Number of pulses to be measured
PMT_AMPLITUDE_MIN = 1 # Min pmt amplitude
PMT_AMPLITUDE_MAX = 2 # Max pmt amplitude
PMT_AMPLITUDE_RESOLUTION = 0.1 # Amplitude increase value resolution
PMT_AMPLITUDE_SAMPLE_NUMBER = 100 # Number of samples measured for picked amplitude
PMT_OUTPUT_DIR = "./measurements_data"
PMT_PERIOD = 1E-3
PMT_WIDTH = 1E-6
PMT_RISE_TIME = 10E-9
PMT_FALL_TIME = 10E-9

def main():
    generator = gen_cmd.Generator() 
    oscilloscope = scope_cmd.Oscilloscope()
    dac = dac8554_api.dac8554_api()

    # Set dac output voltages:
    dac.write_all(A = 0x7FFF, B=0x7FFF, C=0x7FFF, D=0x7FFF)

    # Configure Oscilloscope
    oscilloscope.enable_channel(scope_cmd.OSCILLOSCOPE_CFD_OUT_CHANNEL) 
    oscilloscope.enable_channel(scope_cmd.OSCILLOSCOPE_TRIGGER_CHANNEL)   
    
    oscilloscope.set_amplitude_scale(scope_cmd.OSCILLOSCOPE_CFD_OUT_CHANNEL, 0.200) # 200mV / div
    oscilloscope.set_amplitude_scale(scope_cmd.OSCILLOSCOPE_TRIGGER_CHANNEL, 0.050) # 50 mV / div
    
    oscilloscope.set_time_scale(5E-9) # 5ns / div
    
    oscilloscope.set_trigger(scope_cmd.OSCILLOSCOPE_CFD_OUT_CHANNEL,
                             edge="RISing",
                             level="MIDDle")
    
    oscilloscope.add_time_interval_measurement( scope_cmd.OSCILLOSCOPE_TRIGGER_CHANNEL,
                                                scope_cmd.OSCILLOSCOPE_CFD_OUT_CHANNEL,
                                                start_edge="RISing",
                                                stop_edge="RISing",
                                                start_edge_number=1,
                                                stop_edge_number=1,
                                                start_position="MIDDle",
                                                stop_position="MIDDle")
    
    # Configure generator
    generator.enable_trigger(channel=1)
    generator.set_channel_impedance_50(channel=1)


    # Measurement loop
    for i in range(PMT_AMPLITUDE_MIN, PMT_AMPLITUDE_MAX):
        amplitude = PMT_AMPLITUDE_MIN + i * PMT_AMPLITUDE_RESOLUTION
        generator.generate_continuous_pulse(    channel=1,
                                                amplitude=amplitude,
                                                period=PMT_PERIOD,
                                                width=PMT_WIDTH,
                                                low=PMT_AMPLITUDE_MIN,
                                                rise_time=PMT_RISE_TIME,
                                                fall_time=PMT_FALL_TIME,
                                                delay=0)
        for j in range(PMT_PULSES_COUNT):
            pass


if __name__ == "__main__":
    main()