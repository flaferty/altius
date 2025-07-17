import pandas as pd
import numpy as np
from datetime import datetime

sensor_files = {
    "Left Leg": "left_leg.csv",
    "Right Leg": "right_leg.csv",
    "Left Arm": "left_arm.csv",
    "Right Arm": "right_arm.csv"
}

def estimate_sample_rate(timestamps):
    if len(timestamps) < 2:
        return 1
    intervals = [(t2 - t1).total_seconds() for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
    avg_interval = np.mean(intervals)
    return 1 / avg_interval if avg_interval > 0 else 1

def compute_stability(accel_data, gyro_data, sample_rate, window_size=0.5, accel_thresh=0.02, gyro_thresh=0.05):
    window_len = max(1, int(window_size * sample_rate))
    num_windows = len(accel_data) // window_len
    stable_windows = 0
    stability_segments = []

    for i in range(num_windows):
        start = i * window_len
        end = start + window_len
        accel_window = accel_data[start:end]
        gyro_window = gyro_data[start:end]

        accel_std = np.std(accel_window, axis=0)
        gyro_std = np.std(gyro_window, axis=0)

        if np.all(accel_std < accel_thresh) and np.all(gyro_std < gyro_thresh):
            stable = True
            stable_windows += 1
        else:
            stable = False
        stability_segments.append(stable)

    stability_score = stable_windows / num_windows if num_windows > 0 else 0
    return stability_score, stability_segments

overall_scores = {}
for limb, filename in sensor_files.items():
    try:
        df = pd.read_csv(filename)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        acc_data = df[['accX', 'accY', 'accZ']].to_numpy()
        gyro_data = df[['gyroX', 'gyroY', 'gyroZ']].to_numpy()
        timestamps = df['timestamp'].to_list()

        sample_rate = estimate_sample_rate(timestamps)
        stability_score, segments = compute_stability(acc_data, gyro_data, sample_rate)

        print(f"\n--- {limb} ---")
        print(f"Estimated sample rate: {sample_rate:.2f} Hz")
        print(f"Stability Score: {stability_score * 100:.1f}")
        print(f"Stability Windows: {segments}")

        overall_scores[limb] = stability_score

    except FileNotFoundError:
        print(f"\nFile not found for {limb}: {filename}")
    except Exception as e:
        print(f"\nError processing {limb}: {e}")

if overall_scores:
    avg_score = np.mean(list(overall_scores.values()))
    print(f"\nAverage Stability Score Across All Limbs: {avg_score*100:.1f}")


