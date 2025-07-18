import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

sensor_files = {
    "Left Leg": "data/data10/left_leg.csv",
    "Right Leg": "data/data10/right_leg.csv",
    "Left Arm": "data/data10/left_arm.csv",
    "Right Arm": "data/data10/right_arm.csv"
}


def estimate_sample_rate(timestamps): # computes avg sample rate between readings in Hz
    if len(timestamps) < 2: # fewer than 2 timestamps are provied
        return 1
    intervals = [(t2 - t1).total_seconds() for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
    avg_interval = np.mean(intervals)
    return 1 / avg_interval if avg_interval > 0 else 1

def compute_hold_stability(accel_data, gyro_data,sample_rate):
    
    window_size = 0.5
    accel_thresh=0.12
    gyro_thresh=30
    stillness_tol_acc=1
    stillness_tol_gyro=50
    min_consec_windows=4

    """
    Compute stability score only during periods where the climber is holding a position,
    defined as N or more consecutive 'still' windows
    """
    window_len = max(1, int(window_size * sample_rate)) # no. of sample lines to analyze
    num_windows = len(accel_data) // window_len # no. of windows in the file
    accel_magnitude = np.linalg.norm(accel_data, axis=1) # total acceleration of each row
    gyro_magnitude = np.linalg.norm(gyro_data, axis=1) #total ang. velocity

    is_still = [] # array that shows whether the window was relatively still
    for i in range(num_windows):
        start = i * window_len
        end = start + window_len
        acc_mag_window = accel_magnitude[start:end] # average acceleration in the window
        gyro_mag_window = gyro_magnitude[start:end] # average acceleration in the window
        still = np.mean(np.abs(acc_mag_window - 1.0)) < stillness_tol_acc and \
                np.mean(np.abs(gyro_mag_window - 1.0)) < stillness_tol_gyro
        is_still.append(still) 

    # Identify stable hold segments: N or more consecutive 'still' windows
    hold_indices = []
    i = 0
    while i <= len(is_still) - min_consec_windows:
        if all(is_still[i:i + min_consec_windows]):
            hold_indices.extend(range(i, i + min_consec_windows)) # windows at which the hand is holding the grip
            i += 1
        else:
            i += 1
    hold_indices = sorted(set(hold_indices))

    # Evaluate stability only during those hold windows
    stable_windows = 0
    analyzed_windows = 0
    stability_segments = []

    for i in hold_indices:
        start = i * window_len
        end = start + window_len
        accel_window = accel_data[start:end]
        gyro_window = gyro_data[start:end]

        accel_std = np.std(accel_window, axis=0) # deviation over x, y, z separately
        gyro_std = np.std(gyro_window, axis=0) # deviation over x, y, z separately

        if np.all(accel_std < accel_thresh) and np.all(gyro_std < gyro_thresh):
            stable_windows += 1
            stability_segments.append(True)
        else:
            stability_segments.append(False)

        analyzed_windows += 1


    stability_score = stable_windows / analyzed_windows if analyzed_windows > 0 else 0
    return stability_score, stability_segments


# Main analysis loop
def get_average_stability_score():
    overall_scores = {}

    for limb, filename in sensor_files.items():
        try:
            df = pd.read_csv(filename)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            acc_data = df[['accX', 'accY', 'accZ']].to_numpy()
            gyro_data = df[['gyroX', 'gyroY', 'gyroZ']].to_numpy()
            timestamps = df['timestamp'].to_list()

            sample_rate = estimate_sample_rate(timestamps)
            stability_score, segments = compute_hold_stability(acc_data, gyro_data, sample_rate)

            print(f"\n--- {limb} ---")
            print(f"Estimated sample rate: {sample_rate:.2f} Hz")
            print(f"Stability Score (Still Segments): {stability_score * 100:.1f}%")
            print(f"Stable Windows: {segments}")

            overall_scores[limb] = stability_score

        except FileNotFoundError:
            print(f"\nFile not found for {limb}: {filename}")
        except Exception as e:
            print(f"\nError processing {limb}: {e}")

    if overall_scores:
        avg_score = np.mean(list(overall_scores.values()))
        print(f"\nAverage Stability Score Across All Limbs: {avg_score * 100:.1f}%")
        return avg_score
    return 0.0