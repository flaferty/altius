import asyncio
import struct
import csv
from datetime import datetime
from bleak import BleakClient, BleakScanner

DEVICES = {
    "IMU_LeftArm": "data/left_arm.csv",
    "IMU_RightArm": "data/right_arm.csv",
    "IMU_LeftLeg": "data/left_leg.csv",
    "IMU_RightLeg": "data/right_leg.csv"
}

CHAR_UUID = "abcdef01-1234-5678-1234-56789abcdef0"
found_devices = {}

def detection_callback(device, advertisement_data):
    if advertisement_data.local_name:
        found_devices[device.address] = (device, advertisement_data.local_name)

async def scan_for_devices(print_callback):
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(5)
    await scanner.stop()
    print_callback("[*] Scan complete")

def get_matching_devices(print_callback):
    matches = {}
    requested = set(DEVICES.keys())
    found_names = set(name for _, name in found_devices.values())

    for dev, name in found_devices.values():
        if name in DEVICES:
            matches[name] = dev

    missing = requested - found_names
    for name in missing:
        print_callback(f"[!] Device '{name}' not found.")

    return matches

async def record_imu(device_name, filename, device, print_callback, stop_event):
    client = BleakClient(device)
    csv_file = None

    try:
        await client.connect(timeout=10.0)
        print_callback(f"[+] Connected to {device_name}")

        csv_file = open(filename, mode='w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "timestamp",
            "accX", "accY", "accZ",
            "gyroX", "gyroY", "gyroZ",
            "magX", "magY", "magZ"
        ])

        def handle_notification(sender, data):
            if len(data) == 36:
                try:
                    values = struct.unpack('<9f', data)
                    timestamp = datetime.now().isoformat()
                    csv_writer.writerow([timestamp] + list(values))
                except Exception as e:
                    print_callback(f"[!] Error writing data for {device_name}: {e}")

        await client.start_notify(CHAR_UUID, handle_notification)
        await stop_event.wait()

    except Exception as e:
        print_callback(f"[!] Failed during {device_name} session: {e}")

    finally:
        try:
            if client.is_connected:
                await client.stop_notify(CHAR_UUID)
                await client.disconnect()
        except Exception as e:
            print_callback(f"[!] Error disconnecting {device_name}: {e}")
        
        if csv_file:
            try:
                csv_file.close()
            except Exception as e:
                print_callback(f"[!] Error closing file for {device_name}: {e}")
        
        print_callback(f"[{device_name}] Stopped and cleaned up.")


# main entry point, accepts a print callback
async def main(print_callback=print, stop_event=None):
    if stop_event is None:
        stop_event = asyncio.Event()

    print_callback("[*] Scanning for devices...")
    await scan_for_devices(print_callback)
    matching = get_matching_devices(print_callback)

    if not matching:
        print_callback("[!] No target devices found.")
        return

    device_list = "\n".join(matching.keys())
    print_callback(f"[+] Found devices:\n{device_list}")


    tasks = [
        record_imu(name, DEVICES[name], dev, print_callback, stop_event)
        for name, dev in matching.items()
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        stop_event.set()  # make all record_imu() exit
        print_callback("[!] Logging cancelled.")
