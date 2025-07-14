import asyncio
import struct
import csv
from datetime import datetime
from bleak import BleakClient, BleakScanner

# List of devices to connect to
DEVICES = {
    "IMU_LeftArm": "left_arm.csv",
    "IMU_RightArm": "right_arm.csv",
    "IMU_LeftLeg": "left_leg.csv",
    "IMU_RightLeg": "right_leg.csv"
}

CHAR_UUID = "abcdef01-1234-5678-1234-56789abcdef0"

found_devices = {}

def detection_callback(device, advertisement_data):
    if advertisement_data.local_name:
        found_devices[device.address] = (device, advertisement_data.local_name)
        # print(f"{device.address}, {advertisement_data.local_name}")

async def record_imu(device_name, filename):
    print(f"Scanning for {device_name}...")

    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(5)  # scan duration
    await scanner.stop()

    match = next((dev for dev, name in found_devices.values() if name == device_name),  None)
    
    if not match:
        print(f"[!] Device '{device_name}' not found.")
        return

    async with BleakClient(match.address) as client: # asynchronously connect to arduino as client
        print(f"Connected to {device_name}")

        with open(filename, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                "timestamp",
                "accX", "accY", "accZ",
                "gyroX", "gyroY", "gyroZ",
                "magX", "magY", "magZ"
            ]) #first row

            def handle_notification(sender, data): # has to have 2 parameters
                if len(data) == 36:
                    values = struct.unpack('<9f', data) # 9 float values in little endian
                    timestamp = datetime.now().isoformat()
                    csv_writer.writerow([timestamp] + list(values))
                    #print(f"[{device_name}] {timestamp} "f"acc=({values[0]:.3f}, {values[1]:.3f}, {values[2]:.3f})  "f"gyro=({values[3]:.3f}, {values[4]:.3f}, {values[5]:.3f})  "f"mag=({values[6]:.1f}, {values[7]:.1f}, {values[8]:.1f})")
                else:
                    print(f"[{device_name}] [!] Unexpected data length: {len(data)}")

            await client.start_notify(CHAR_UUID, handle_notification) # subscribe to data from arduino

            try:
                while True:
                    await asyncio.sleep(1) # allows the program to run until manually interrupted
            except asyncio.CancelledError:
                await client.stop_notify(CHAR_UUID)
                print(f"[{device_name}] Stopped.")
            except Exception as e:
                print(f"[{device_name}] Error: {e}")

async def main():
    tasks = [record_imu(name, file) for name, file in DEVICES.items()]
    try:
        await asyncio.gather(*tasks) # runs all coroutine objects concurrently
    except KeyboardInterrupt:
        print("\nInterrupted by user.")

asyncio.run(main())
