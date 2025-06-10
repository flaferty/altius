import asyncio
import csv
from datetime import datetime
from bleak import BleakClient, BleakScanner

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

READ_INTERVAL = 0.5  # seconds
CSV_FILENAME = "ble_sensor_log.csv"

async def read_loop(client):
    fieldnames = ["timestamp", "accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ", "magX", "magY", "magZ"]
    
    # makes new csv file, overwrites it with new data every time
    with open(CSV_FILENAME, mode='w', newline='') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader() # writes first row as fieldnames

        while True:
            row = {"timestamp": datetime.now().isoformat()}
            for name, uuid in CHARACTERISTICS.items():
                try:
                    value = await client.read_gatt_char(uuid) # value from the corresponding uuid
                    int_val = int.from_bytes(value, byteorder='little', signed=True)
                    row[name] = int_val # store the value into dictionary
                except Exception as e:
                    row[name] = None

            print(row)
            writer.writerow(row)
            csvfile.flush()  # ensures data is written to disk every loop
            await asyncio.sleep(READ_INTERVAL)

async def main():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()

    # finds first device woth matching name
    nano = next((d for d in devices if d.name and DEVICE_NAME == d.name), None) 

    if not nano:
        print("Device not found.")
        return

    async with BleakClient(nano.address) as client:
        if not client.is_connected:
            print("Failed to connect.")
            return
        print(f"Connected to {DEVICE_NAME}")
        await read_loop(client)

asyncio.run(main())
