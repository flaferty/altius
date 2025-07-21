import os

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def calculate_movement_smoothness(file_path, stillness_accel_threshold=0.8, stillness_gyro_threshold=8.0,
                                  max_expected_jerk=1000.0):
    """
    Calculates a smoothness score by analyzing jerk during movement periods.

    stillness_accel_threshold, stillness_gyro_thresholdL: these are crucial parameters. They define how much "noise" (small variations) we allow in the sensor readings before we consider a limb to be truly "moving." If the sensor readings change less than these thresholds, we assume the limb is still.

    max_expected_jerk: this parameter helps us normalize our final smoothness score. It represents the maximum jerk we'd expect to see in a very jerky movement.
    """
    try:
        df = pd.read_csv(file_path, index_col='timestamp')
        df.index = pd.to_datetime(df.index, format='mixed')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0.0, None, []

    if df.empty:
        return 0.0, None, []

    # 1: Detect Movement vs. Stillness
    # calculate the magnitude
    df['acc_mag'] = np.sqrt(df['accX'] ** 2 + df['accY'] ** 2 + df['accZ'] ** 2)
    df['gyro_mag'] = np.sqrt(df['gyroX'] ** 2 + df['gyroY'] ** 2 + df['gyroZ'] ** 2)

    window_size = 10
    df['acc_mag_std'] = df['acc_mag'].rolling(window=window_size, min_periods=1).std()
    df['gyro_mag_std'] = df['gyro_mag'].rolling(window=window_size, min_periods=1).std()

    df['is_still'] = (df['acc_mag_std'] < stillness_accel_threshold) & \
                     (df['gyro_mag_std'] < stillness_gyro_threshold)

    # when the limb is MOVING ---
    df['is_moving'] = ~df['is_still']

    # 2: Identify Movement Periods ---
    df['movement_change'] = df['is_moving'].astype(int).diff()
    starts = df.index[df['movement_change'] == 1]
    ends = df.index[df['movement_change'] == -1]

    if df['is_moving'].iloc[0]:
        starts = starts.insert(0, df.index[0])
    if df['is_moving'].iloc[-1]:
        ends = ends.append(pd.Index([df.index[-1]]))

    movements = []
    min_len = min(len(starts), len(ends))
    for i in range(min_len):
        movements.append((starts[i], ends[i]))

    if not movements:
        print("Warning: No movement periods detected!")
        # If there's no movement, the movement is perfectly smooth.
        return 100.0, df, []

    # 3: Calculate Smoothness Score from Jerk ---
    jerk_scores = []
    for start, end in movements:
        move_df = df.loc[start:end].copy()
        if len(move_df) < 2:
            continue

        # Calculate time differences for this specific movement block
        dt = move_df.index.to_series().diff().dt.total_seconds().dropna()
        dt = dt[dt > 0.01]
        if dt.empty:
            continue

        # Calculate jerk for both accelerometer and gyroscope magnitudes
        acc_jerk = move_df['acc_mag'].diff().dropna() / dt
        gyro_jerk = move_df['gyro_mag'].diff().dropna() / dt

        # Combine the absolute jerk values
        total_jerk = (np.abs(acc_jerk).mean() + np.abs(gyro_jerk).mean()) / 2

        if not pd.isna(total_jerk):
            jerk_scores.append(total_jerk)

    if not jerk_scores:
        print("Warning: No valid jerk scores calculated!")
        return 100.0, df, []

    # Lower average jerk is better (smoother)
    average_jerk = np.median(np.clip(jerk_scores, 0, 1000))
    
    # Normalize the score.
    smoothness_score = 1 - (average_jerk / max_expected_jerk)
    final_score = max(0.0, min(1.0, smoothness_score)) * 100

    # Removed the print statement here, as it will be handled by the main loop
    #print(f"\nAnalysis for {file_path}:")
    #print(f"Detected {len(movements)} movement periods.")
    #print(f"Average Jerk: {average_jerk:.3f}, Smoothness Score: {final_score:.1f}/100")

    return final_score, df, movements

def get_smoothness_score(folder="data"):
    limb_files = {
        'Right Arm': os.path.join(folder, 'right_arm.csv'),
        'Left Arm': os.path.join(folder, 'left_arm.csv'),
        'Left Leg': os.path.join(folder, 'left_leg.csv'),
        'Right Leg': os.path.join(folder, 'right_leg.csv')
    }

    limb_scores = {}
    output_directory = "climber_smoothness_results"

    for limb, file in limb_files.items():
        print(f"\n--- Processing {limb} data from {file} ---")
        raw_score, processed_df, detected_movements = calculate_movement_smoothness(file)

        if processed_df is not None:
            final_score = raw_score
            limb_scores[limb] = final_score
            # Uncomment if visualization is needed
            # visualize_movements(limb, processed_df, detected_movements, final_score)
        else:
            print(f"Skipping visualization for {limb} due to data processing error.")

    print("\n-- Overall Smoothness Results --")
    if limb_scores:
        overall_score = sum(limb_scores.values()) / len(limb_scores)
        print(f"Overall Average Smoothness Score (All Limbs): {overall_score:.1f}/100")
        return overall_score
    else:
        print("No valid data found for smoothness score.")
        return 0.0