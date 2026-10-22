import pyvisa

GENERATOR_ADDRESS = "GPIB0::11::INSTR"


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

    def enable_trigger(self):
        self.generator.write("OUTPut:TRIGger:MODE TRIGger")

    def disable_trigger(self):
        pass
        #TODO self.generator.write("OUTPut:TRIGger:MODE SYNC")

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

    def set_polarization(self, channel, polarization):
        polarization = polarization.upper()

        if polarization not in ("NORMAL", "INVERTED"):
            raise ValueError("polarization must be 'NORMAL' or 'INVERTED'")

        polarity = "NORMal" if polarization == "NORMAL" else "INVerted"
        self.generator.write(f"OUTPut{channel}:POLarity {polarity}")  

    def disable_channel(self, channel):
        self.generator.write(f"OUTP{channel} OFF")        

    def close(self):
        if self.generator:
            self.generator.close()
        self.rm.close()