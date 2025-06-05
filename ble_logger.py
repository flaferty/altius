import asyncio
import pandas as pd
from bleak import BleakScanner, BleakClient
from datetime import datetime

# BLE Characteristic UUIDs (must match Arduino sketch)
CHAR_UUIDS = {
    "accX": "2a57",
    "accY": "2a58",
    "accZ": "2a59",
    "gyroX": "2a5a",
    "gyroY": "2a5b",
    "gyroZ": "2a5c",
    "magX": "2a5d",
    "magY": "2a5e",
    "magZ": "2a5f"
}

imu_data = {
    "timestamp": [],
    "accX": [], "accY": [], "accZ": [],
    "gyroX": [], "gyroY": [], "gyroZ": [],
    "magX": [], "magY": [], "magZ": []
}

# BLE notification handler
def notification_handler(axis):
    def handler(_, data):
        value = int.from_bytes(data, byteorder='little', signed=True) / 1000.0
        imu_data[axis].append(value)

        if axis == "magZ":
            imu_data["timestamp"].append(datetime.now().isoformat())
            print(f"{imu_data['timestamp'][-1]} | "
                  f"A=({imu_data['accX'][-1]:.2f}, {imu_data['accY'][-1]:.2f}, {imu_data['accZ'][-1]:.2f}) | "
                  f"G=({imu_data['gyroX'][-1]:.2f}, {imu_data['gyroY'][-1]:.2f}, {imu_data['gyroZ'][-1]:.2f}) | "
                  f"M=({imu_data['magX'][-1]:.2f}, {imu_data['magY'][-1]:.2f}, {imu_data['magZ'][-1]:.2f})")
    return handler

async def main():
    print("Scanning for NanoBLE-IMU.")
    device = await BleakScanner.find_device_by_name("NanoBLE-IMU", timeout=10.0)

    if not device:
        print("Device not found.")
        return

    async with BleakClient(device) as client:
        print(f"Connected to {device.address}")

        for axis, uuid in CHAR_UUIDS.items():
            await client.start_notify(uuid, notification_handler(axis))

        print("Receiving 9-axis IMU data. Press Ctrl+C to stop.")

        try:
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("Logging stopped by user.")

        df = pd.DataFrame(imu_data)
        filename = f"imu_9axis_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    asyncio.run(main())
