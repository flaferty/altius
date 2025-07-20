import pandas as pd
import numpy as np
import os

def estimate_sample_rate(timestamps):
    if len(timestamps) < 2:
        return 1
    intervals = [(t2 - t1).total_seconds() for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
    avg_interval = np.mean(intervals)
    return 1 / avg_interval if avg_interval > 0 else 1

def count_grips(
    path,
    sample_rate,
    window_sec=0.25,
    stillness_tol_acc=0.2,
    stillness_tol_gyro=50,
    min_consec_windows=3
):
    df = pd.read_csv(path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    acc_data = df[['accX', 'accY', 'accZ']].to_numpy()
    gyro_data = df[['gyroX', 'gyroY', 'gyroZ']].to_numpy()

    accel_magnitude = np.linalg.norm(acc_data, axis=1)
    gyro_magnitude = np.linalg.norm(gyro_data, axis=1)

    window_len = int(window_sec * sample_rate)
    num_windows = len(df) // window_len

    is_still = []
    for i in range(num_windows):
        start = i * window_len
        end = start + window_len
        acc_mag_window = accel_magnitude[start:end]
        gyro_mag_window = gyro_magnitude[start:end]

        still = np.mean(np.abs(acc_mag_window - 1.0)) < stillness_tol_acc and \
                np.mean(gyro_mag_window) < stillness_tol_gyro
        is_still.append(still)

    grip_count = 0
    i = 0
    while i <= len(is_still) - min_consec_windows:
        if all(is_still[i:i + min_consec_windows]):
            grip_count += 1
            while i < len(is_still) and is_still[i]:
                i += 1
        else:
            i += 1

    return grip_count

def get_grip_count(folder):
    grip_counts = []
    for side in ["left_arm", "right_arm"]:
        file_path = os.path.join(folder, f"{side}.csv")
        if not os.path.exists(file_path):
            print(f"[!] File not found: {file_path}")
            grip_counts.append(0)
            continue

        df = pd.read_csv(file_path)
        if df.empty:
            grip_counts.append(0)
            continue

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        sample_rate = estimate_sample_rate(df['timestamp'].to_list())
        grips = count_grips(
            path=file_path,
            sample_rate=sample_rate
        )
        grip_counts.append(grips)

    return grip_counts

print(get_grip_count("data"))