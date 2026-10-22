
import pyvisa

GENERATOR_ADDRESS = "GPIB0::7::INSTR"
OSCILLOSCOPE_ADDRESS = "GPIB0::11::INSTR"


def check_device(rm, name, address):
    print(f"\nChecking {name}: {address}")

    try:
        instrument = rm.open_resource(address)

        try:
            instrument.timeout = 3000
            instrument.read_termination = "\n"
            instrument.write_termination = "\n"

            print("[OK] Resource opened successfully.")

            try:
                identification = instrument.query("*IDN?").strip()
                print(f"[OK] Identification: {identification}")
            except Exception as error:
                print(f"[WARNING] Resource opened, but *IDN? failed: {error}")

        finally:
            instrument.close()

    except Exception as error:
        print(f"[ERROR] Cannot open resource: {error}")


def main():
    try:
        rm = pyvisa.ResourceManager()

        try:
            print("VISA backend:")
            print(rm.visalib)

            print("\nVISA resources detected:")
            resources = rm.list_resources()
            print(resources if resources else "No resources listed.")

            check_device(rm, "Generator", GENERATOR_ADDRESS)
            check_device(rm, "Oscilloscope", OSCILLOSCOPE_ADDRESS)

        finally:
            rm.close()

    except Exception as error:
        print(f"[FATAL] Cannot initialize VISA: {error}")


if __name__ == "__main__":
    main()
