import pyvisa

GENERATOR_ADDRESS = "GPIB0::10::INSTR"


class Generator:

    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.generator = None

        try:
            self.generator = self.rm.open_resource(GENERATOR_ADDRESS)
            self.generator.timeout = 10000
            self.generator.write_termination = "\n"
            self.generator.read_termination = "\n"

        except Exception:
            self.rm.close()
            raise

    def enable_trigger(self, channel):
        self.generator.write(f"SOUR{channel}:FUNC SQUare")
        self.generator.write(f"SOUR{channel}:FREQ 1000")
        self.generator.write(f"SOUR{channel}:VOLT:HIGH 5")
        self.generator.write(f"SOUR{channel}:VOLT:LOW 0")
        self.generator.write(f"OUTP{channel} ON")

    def disable_trigger(self, channel):
        self.generator.write(f"OUTP{channel} OFF")

    def set_channel_impedance_50(self, channel):
        self.generator.write(f"OUTP{channel}:IMP 50")
         
    def generate_pulse( self, channel, amplitude, pulse_count, period, width, low, rise_time, fall_time, delay=0.0):
        high = low + amplitude

        self.generator.write(f"SOUR{channel}:FUNC:SHAP PULS")
        self.generator.write(f"SOUR{channel}:PULSe:PERiod {period}")
        self.generator.write(f"SOUR{channel}:PULSe:WIDTh {width}")
        self.generator.write(f"SOUR{channel}:PULSe:TRAN:LEAD {rise_time}")
        self.generator.write(f"SOUR{channel}:PULSe:TRAN:TRA {fall_time}")
        self.generator.write(f"SOUR{channel}:PULSe:DELay {delay}")

        self.generator.write(f"SOUR{channel}:VOLT:LEV:IMM:HIGH {high}")
        self.generator.write(f"SOUR{channel}:VOLT:LEV:IMM:LOW {low}")

        self.generator.write(f"SOUR{channel}:BURSt:STAT ON")
        self.generator.write(f"SOUR{channel}:BURSt:MODE TRIG")
        self.generator.write(f"SOUR{channel}:BURSt:NCYC {pulse_count}")

        self.generator.write(f"TRIG{channel}:SOURce BUS")
        self.generator.write(f"OUTP{channel} ON")
        self.generator.write("*TRG")

    def generate_single_pulse(self, channel):
        self.generate_pulse(channel, 1)

    def generate_continuous_pulse( self, channel, amplitude, period, width, low, rise_time, fall_time, delay=0.0):
        high = low + amplitude
        self.generator.write(f"SOUR{channel}:BURSt:STAT OFF")

        self.generator.write(f"SOUR{channel}:FUNC:SHAP PULS")

        self.generator.write(f"SOUR{channel}:PULSe:PERiod {period}")
        self.generator.write(f"SOUR{channel}:PULSe:WIDTh {width}")
        self.generator.write(f"SOUR{channel}:PULSe:TRAN:LEAD {rise_time}")
        self.generator.write(f"SOUR{channel}:PULSe:TRAN:TRAiling {fall_time}")
        self.generator.write(f"SOUR{channel}:PULSe:DELay {delay}")

        self.generator.write(f"SOUR{channel}:VOLTage:LEVel:IMMediate:HIGH {high}")
        self.generator.write(f"SOUR{channel}:VOLTage:LEVel:IMMediate:LOW {low}")

        self.generator.write(f"OUTPut{channel} ON")

    def disable_channel(self, channel):
        self.generator.write(f"OUTP{channel} OFF")

    def close(self):
        if self.generator:
            self.generator.close()
        self.rm.close()