import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def plot_left_arm_motion(df, sample_rate, window_size=0.5):
    """
    Plots acceleration and gyroscope magnitude over time in separate subplots
    with vertical lines showing window boundaries.

    Parameters:
        df (pd.DataFrame): Must contain 'accX', 'accY', 'accZ', 'gyroX', 'gyroY', 'gyroZ', and 'timestamp' columns
        sample_rate (float): Samples per second
        window_size (float): Duration of each window in seconds
    """
    # Ensure timestamps are datetime
    if not np.issubdtype(df['timestamp'].dtype, np.datetime64):
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Compute time axis in seconds
    time_seconds = (df['timestamp'] - df['timestamp'].iloc[0]).dt.total_seconds()

    # Compute acceleration magnitude
    acc_data = df[['accX', 'accY', 'accZ']].to_numpy()
    accel_magnitude = np.linalg.norm(acc_data, axis=1)

    # Compute gyroscope magnitude
    if {'gyroX', 'gyroY', 'gyroZ'}.issubset(df.columns):
        gyro_data = df[['gyroX', 'gyroY', 'gyroZ']].to_numpy()
        gyro_magnitude = np.linalg.norm(gyro_data, axis=1)
    else:
        raise ValueError("DataFrame must contain 'gyroX', 'gyroY', 'gyroZ' columns.")

    # Window boundaries
    window_len = int(window_size * sample_rate)
    window_lines = time_seconds[window_len::window_len]

    # Create figure with two subplots
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Plot acceleration
    axes[0].plot(time_seconds, accel_magnitude, label='Acceleration Magnitude', color='blue')
    for x in window_lines:
        axes[0].axvline(x=x, color='gray', linestyle='--', alpha=0.5)
    axes[0].set_ylabel("Acceleration Magnitude")
    axes[0].set_xlabel("Time (seconds)")
    axes[0].grid(True)
    axes[0].legend()

    # Plot gyroscope
    axes[1].plot(time_seconds, gyro_magnitude, label='Gyroscope Magnitude', color='red')
    for x in window_lines:
        axes[1].axvline(x=x, color='gray', linestyle='--', alpha=0.5)
    axes[1].set_xlabel("Time (seconds)")
    axes[1].set_ylabel("Gyroscope Magnitude")
    axes[1].grid(True)
    axes[1].legend()

    # Final layout
    plt.tight_layout()
    plt.show()

def estimate_sample_rate(timestamps): # computes avg sample rate between readings in Hz
    if len(timestamps) < 2: # fewer than 2 timestamps are provied
        return 1
    intervals = [(t2 - t1).total_seconds() for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
    avg_interval = np.mean(intervals)
    return 1 / avg_interval if avg_interval > 0 else 1
    

df = pd.read_csv("data/data9/left_arm.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
timestamps = df['timestamp'].to_list()
sample_rate = estimate_sample_rate(timestamps)
plot_left_arm_motion(df, sample_rate)