import pyvisa

OSCILLOSCOPE_ADDRESS = "GPIB0::7::INSTR"


class Oscilloscope:

    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.scope = None

        try:
            self.scope = self.rm.open_resource(OSCILLOSCOPE_ADDRESS)
            self.scope.timeout = 10000
            self.scope.write_termination = "\n"
            self.scope.read_termination = "\n"
        except Exception:
            self.rm.close()
            raise

    def enable_channel(self, channel, enable):
        state = "ON" if enable else "OFF"
        self.scope.write(f":CHANnel{channel}:DISPlay {state}")

    def add_time_interval_measurement( self, first_channel, second_channel, start_edge="RISing", stop_edge="RISing", start_edge_number=1, stop_edge_number=1, start_position="MIDDle", stop_position="MIDDle"):
        self.scope.write(f":MEASure:SOURce CHANnel{first_channel},CHANnel{second_channel}")
        self.scope.write( f":MEASure:DELTatime:DEFine {start_edge},{start_edge_number},{start_position},{stop_edge},{stop_edge_number},{stop_position}")

    def get_time_interval_measurement(self):
        return float(self.scope.query(":MEASure:DELTatime?"))

    def set_amplitude_scale(self, channel, scale):
        self.scope.write(f":CHANnel{channel}:SCALe {scale}")

    def set_time_scale(self, scale):
        self.scope.write(f":TIMebase:SCALe {scale}")

    def set_trigger(self, channel, edge, level):
        edge = edge.lower()

        if edge not in ("rising", "falling"):
            raise ValueError("edge must be 'rising' or 'falling'")

        slope = "POS" if edge == "rising" else "NEG"

        self.scope.write(f":TRIGger:EDGE:SOURce CHANnel{channel}")
        self.scope.write(f":TRIGger:EDGE:SLOPe {slope}")
        self.scope.write(f":TRIGger:LEVel CHANnel{channel},{level}")

    def set_vertical_offset(self, channel, value):
        self.scope.write(f":CHANnel{channel}:OFFSet {value}")

    def set_horizontal_offset(self, value):
        self.scope.write(f":TIMebase:POSition {value}")

    def close(self):
        if self.scope is not None:
            self.scope.close()
            self.scope = None

        if self.rm is not None:
            self.rm.close()
            self.rm = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass