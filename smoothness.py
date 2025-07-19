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


def visualize_movements(limb_name, df, movements, score, output_dir="output_figures"):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8), sharex=True)

    # Raw signal and highlighted movement periods
    ax1.plot(df.index, df['acc_mag'], label='Acceleration Magnitude', color='grey', alpha=0.5)
    for start, end in movements:
        ax1.plot(df.loc[start:end].index, df.loc[start:end, 'acc_mag'], color='darkorange')
        ax1.axvspan(start, end, color='cornflowerblue', alpha=0.2)
    ax1.set_title(f'Smoothness Analysis for {limb_name} (Score: {score:.1f}/100)')
    ax1.set_ylabel('Acceleration (m/s²)')
    ax1.grid(True)

    # Plot jerk for visualization
    df['acc_jerk'] = df['acc_mag'].diff().abs() / df.index.to_series().diff().dt.total_seconds()
    ax2.plot(df.index, df['acc_jerk'], label='Acceleration Jerk', color='firebrick', alpha=0.7)
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Jerk (m/s³)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()

    # --- Save the figure instead of showing it ---
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a clean filename
    file_name = f"{limb_name.replace(' ', '_').lower()}_smoothness_analysis.png"
    save_path = os.path.join(output_dir, file_name)

    plt.savefig(save_path, dpi=300)  # dpi for higher quality
    plt.close(fig)  # Close the figure to free up memory
    print(f"Figure saved to: {save_path}")



def get_smoothness_score():

    # Example setup for 4 limbs:
    limb_files = {
        'Right Arm': 'data/right_arm.csv',
        'Left Arm': 'data/left_arm.csv',
        'Left Leg': 'data/left_leg.csv',
        'Right Leg': 'data/right_leg.csv'
    }
    '''
    limb_files = {
        'Smooth Mover': 'smooth_mover.csv',
        'Jerky Mover': 'jerky_mover.csv'
    }
    '''
    # --- Analysis & Visualization ---
    limb_scores = {}
    output_directory = "climber_smoothness_results"
    for limb, file in limb_files.items():
        print(f"\n--- Processing {limb} data from {file} ---")
        raw_score, processed_df, detected_movements = calculate_movement_smoothness(file)

        if processed_df is not None:
            final_score = raw_score
            limb_scores[limb] = final_score

            visualize_movements(limb, processed_df, detected_movements, final_score)
        else:
            print(f"Skipping visualization for {limb} due to data processing error.")

    # --- Combine 4 Limbs into One Overall Score ---
    print("\n-- Overall Smoothness Results --")
    if limb_scores:
        total_score_sum = sum(limb_scores.values())
        overall_smoothness_score = total_score_sum / len(limb_scores)
        print(f"Overall Average Smoothness Score (All Limbs): {overall_smoothness_score:.1f}/100")
        return overall_smoothness_score
    else:
        print("No limb scores were calculated. Cannot compute overall average.")

    # --- Display Individual Limb Scores to the User ---
    print("\n--- Individual Limb Smoothness Scores ---")
    if limb_scores:
        for limb_name, score in limb_scores.items():
            print(f"{limb_name}: {score:.1f}/100")
    else:
        print("No individual limb scores to display.")

    print(f"\nAll figures have been saved to the '{output_directory}' directory.")