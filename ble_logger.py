import asyncio
import csv
from datetime import datetime
from bleak import BleakClient, BleakScanner
import struct  # required for decoding floats

DEVICE_NAME = "IMU_LeftHand"

CHARACTERISTICS = {
    "accX": "00000001-0000-1000-8000-00805f9b34fb",
    "accY": "00000002-0000-1000-8000-00805f9b34fb",
    "accZ": "00000003-0000-1000-8000-00805f9b34fb",
    "gyroX": "00000004-0000-1000-8000-00805f9b34fb",
    "gyroY": "00000005-0000-1000-8000-00805f9b34fb",
    "gyroZ": "00000006-0000-1000-8000-00805f9b34fb",
    "magX": "00000007-0000-1000-8000-00805f9b34fb",
    "magY": "00000008-0000-1000-8000-00805f9b34fb",
    "magZ": "00000009-0000-1000-8000-00805f9b34fb"
}

READ_INTERVAL = 0.5  # seconds, should be changed to a higher value later

DEVICES = {
    "IMU_LeftHand": "left_hand.csv",
    "IMU_RightHand": "right_hand.csv",
    "IMU_LeftLeg": "left_leg.csv",
    "IMU_RightLeg": "right_leg.csv"
}

async def read_loop(client, csv_filename, device_name):
    fieldnames = ["timestamp", "accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ", "magX", "magY", "magZ"]
    
    # makes new csv file, overwrites it with new data every time
    with open(csv_filename, mode='w', newline='') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader() # writes first row as fieldnames

        while True:
            row = {"timestamp": datetime.now().isoformat()}
            for name, uuid in CHARACTERISTICS.items():
                try:
                    value = await client.read_gatt_char(uuid)  # raw bytes from BLE
                    float_val = struct.unpack('<f', value)[0]  # convert to float
                    row[name] = round(float_val, 3) 
                except Exception:
                    row[name] = None

            print(f"[{device_name}] {row}")
            writer.writerow(row)
            csvfile.flush()  # ensures data is written to disk every loop
            await asyncio.sleep(READ_INTERVAL)

async def connect_to_device(device_name, csv_filename):
    print(f"Scanning for {device_name}...")
    devices = await BleakScanner.discover()

    # finds first device woth matching name
    nano = next((d for d in devices if d.name and d.name == device_name), None)

    if not nano:
        print(f"{device_name} not found.")
        return

    async with BleakClient(nano.address) as client:
        if not client.is_connected:
            print(f"Failed to connect to {device_name}.")
            return
        print(f"Connected to {device_name}")
        await read_loop(client, csv_filename, device_name)


async def main():
    tasks = []
    for device_name, csv_filename in DEVICES.items():
        tasks.append(connect_to_device(device_name, csv_filename))
    await asyncio.gather(*tasks) # runs all tasks in parallel

asyncio.run(main())
