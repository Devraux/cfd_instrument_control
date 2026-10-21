import pyvisa

def scan_gpib():
    rm = pyvisa.ResourceManager()
    found_devices = []

    try:
        print("Scanning GPIB bus ...")

        for address in range(31):
            resource = f"GPIB0::{address}::INSTR"
            instrument = None

            try:
                instrument = rm.open_resource(resource)
                instrument.timeout = 1000
                instrument.read_termination = "\n"
                instrument.write_termination = "\n"

                try:
                    identification = instrument.query("*IDN?").strip()
                except Exception:
                    identification = "No response to *IDN?"

                found_devices.append(
                    {
                        "address": address,
                        "resource": resource,
                        "identification": identification,
                    })

                print(f"[FOUND] Address {address}: {identification}")

            except Exception:
                pass

            finally:
                if instrument is not None:
                    instrument.close()

        print("--- Scan summary ---")

        if found_devices:
            print(f"Found {len(found_devices)} responding GPIB addresses.")
        else:
            print("No responding devices found.")
            
        return found_devices

    finally:
        rm.close()


if __name__ == "__main__":
    scan_gpib()