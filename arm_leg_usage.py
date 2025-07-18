import os
import csv
from datetime import datetime
import numpy as np

PARTS = ["left_arm", "right_arm", "left_leg", "right_leg"]

def read_csv_file(filename):
    data = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                ts = row['timestamp']
                accX = float(row['accX'])
                accY = float(row['accY'])
                accZ = float(row['accZ'])
                data.append((ts, accX, accY, accZ))
            except:
                continue
    return data

def compute_magnitude(ax, ay, az):
    return np.sqrt(ax**2 + ay**2 + az**2)

def analyze_arm_leg_usage(all_data, movement_threshold=0.8):
    movement_counts = {}

    for part, readings in all_data.items():
        prev_mag = None
        count = 0
        for ts, ax, ay, az in readings:
            mag = compute_magnitude(ax, ay, az)
            if prev_mag is not None and abs(mag - prev_mag) > movement_threshold:
                count += 1
            prev_mag = mag
        movement_counts[part] = count

    return movement_counts

def usage_summary(movement_counts):
    arm_total = movement_counts.get("left_hand", 0) + movement_counts.get("right_hand", 0)
    leg_total = movement_counts.get("left_leg", 0) + movement_counts.get("right_leg", 0)
    total = arm_total + leg_total

    if total == 0:
        return {
            "arm_usage_ratio": 0.0,
            "leg_usage_ratio": 0.0,
            "comment": "No significant movement detected"
        }

    arm_ratio = arm_total / total
    leg_ratio = leg_total / total

    if leg_ratio < 0.3:
        comment = "Climber overuses arms and underuses legs"
    elif 0.3 <= leg_ratio <= 0.6:
        comment = "Balanced use of arms and legs"
    else:
        comment = "Climber uses legs more actively than arms — good technique"

    return {
        "arm_usage_ratio": round(arm_ratio, 2),
        "leg_usage_ratio": round(leg_ratio, 2),
        "comment": comment
    }

def analyze_usage_from_csv(folder):
    all_data = {}
    for part in PARTS:
        file_match = [f for f in os.listdir(folder) if f.startswith(part)]
        if not file_match:
            print(f"No csv file found for {part}")
            continue
        data = read_csv_file(os.path.join(folder, file_match[0]))
        all_data[part] = data

    movement_counts = analyze_arm_leg_usage(all_data)
    summary = usage_summary(movement_counts)

    print("\nArm / Leg Usage Analysis:\n")

    for part in PARTS:
        count = movement_counts.get(part, 0)
        print(f"  {part}: {count} movements")

    print(f"\nArm usage ratio: {summary['arm_usage_ratio']}")
    print(f"Leg usage ratio: {summary['leg_usage_ratio']}\n")
    print(f"Comment: {summary['comment']}\n")

    return summary
