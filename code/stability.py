import pandas as pd
import numpy as np
import os

def estimate_sample_rate(timestamps):
    if len(timestamps) < 2:
        return 1
    intervals = [(t2 - t1).total_seconds() for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
    avg_interval = np.mean(intervals)
    return 1 / avg_interval if avg_interval > 0 else 1

def compute_hold_stability(accel_data, gyro_data, sample_rate):
    window_size = 0.25
    accel_thresh = 0.12
    gyro_thresh = 30
    stillness_tol_acc = 1
    stillness_tol_gyro = 50
    min_consec_windows = 3

    window_len = max(1, int(window_size * sample_rate))
    num_windows = len(accel_data) // window_len
    accel_magnitude = np.linalg.norm(accel_data, axis=1)
    gyro_magnitude = np.linalg.norm(gyro_data, axis=1)

    is_still = []
    for i in range(num_windows):
        start = i * window_len
        end = start + window_len
        acc_mag_window = accel_magnitude[start:end]
        gyro_mag_window = gyro_magnitude[start:end]
        still = np.mean(np.abs(acc_mag_window - 1.0)) < stillness_tol_acc and \
                np.mean(np.abs(gyro_mag_window - 1.0)) < stillness_tol_gyro
        is_still.append(still)

    hold_indices = []
    i = 0
    while i <= len(is_still) - min_consec_windows:
        if all(is_still[i:i + min_consec_windows]):
            hold_indices.extend(range(i, i + min_consec_windows))
            i += 1
        else:
            i += 1
    hold_indices = sorted(set(hold_indices))

    stable_windows = 0
    analyzed_windows = 0
    stability_segments = []

    for i in hold_indices:
        start = i * window_len
        end = start + window_len
        accel_window = accel_data[start:end]
        gyro_window = gyro_data[start:end]

        accel_std = np.std(accel_window, axis=0)
        gyro_std = np.std(gyro_window, axis=0)

        if np.all(accel_std < accel_thresh) and np.all(gyro_std < gyro_thresh):
            stable_windows += 1
            stability_segments.append(True)
        else:
            stability_segments.append(False)

        analyzed_windows += 1

    stability_score = stable_windows / analyzed_windows if analyzed_windows > 0 else 0
    return stability_score, stability_segments

def get_stability(folder):
    overall_scores = {}
    limb_map = {
        "left_leg": "Left Leg",
        "right_leg": "Right Leg",
        "left_arm": "Left Arm",
        "right_arm": "Right Arm"
    }

    for limb_file, limb_name in limb_map.items():
        path = os.path.join(folder, f"{limb_file}.csv")
        try:
            df = pd.read_csv(path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            acc_data = df[['accX', 'accY', 'accZ']].to_numpy()
            gyro_data = df[['gyroX', 'gyroY', 'gyroZ']].to_numpy()
            timestamps = df['timestamp'].to_list()

            sample_rate = estimate_sample_rate(timestamps)
            stability_score, segments = compute_hold_stability(acc_data, gyro_data, sample_rate)

            # print(f"\n--- {limb_name} ---")
            # print(f"Estimated sample rate: {sample_rate:.2f} Hz")
            # print(f"Stability Score (Still Segments): {stability_score * 100:.1f}%")
            # print(f"Stable Windows: {segments}")

            overall_scores[limb_name] = stability_score

        except FileNotFoundError:
            print(f"\nFile not found for {limb_name}: {path}")
        except Exception as e:
            print(f"\nError processing {limb_name}: {e}")

    if overall_scores:
        avg_score = np.mean(list(overall_scores.values()))
        # print(f"\nAverage Stability Score Across All Limbs: {avg_score * 100:.1f}%")
        return avg_score

    return 0.0

