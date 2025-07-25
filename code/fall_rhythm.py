import csv
from datetime import datetime
import os
import numpy as np
from collections import defaultdict

PARTS = ["left_arm","left_leg","right_arm","right_leg"]

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
                data.append((ts,accX,accY,accZ))
            except:
                continue
    return data

def load_all_sensor_data(folder):
    all_data = {}
    for part in PARTS:
        file_path = os.path.join(folder, f"{part}.csv")
        if os.path.exists(file_path):
            all_data[part] = read_csv_file(file_path)
        else:
            print(f"No csv file found for {part}")
    return all_data


# fall detection start
def compute_magnitude(ax,ay,az):
    return np.sqrt(ax**2 + ay**2 + az**2)

def detect_falls(all_data, partial_threshold = 10.0, sync_window = 0.5):
    partial_falls = []
    full_falls = []

    partial_events = defaultdict(list)
    for part, readings in all_data.items():
        for ts, ax, ay, az in readings:
            mag = compute_magnitude(ax, ay, az)
            if mag > partial_threshold:
                partial_falls.append((ts, part))
                partial_events[part].append(ts)

    def parse_time(ts):
        return datetime.fromisoformat(ts).timestamp()

    all_events = sorted([
        (parse_time(ts), part) for part, ts_list in partial_events.items() for ts in ts_list
    ])

    i = 0
    while i < len(all_events):
        t0, _ = all_events[i]
        parts_triggered = set()
        j=1
        while j < len(all_events) and (all_events[j][0] - t0) <= sync_window:
            parts_triggered.add(all_events[j][1])
            j += 1
        if len(parts_triggered) == len(PARTS):
            full_falls.append(datetime.fromtimestamp(t0).isoformat())
            i = j
        else:
            i += 1

    return {
        "partial_falls": partial_falls,
        "full_falls": full_falls
    }

def get_falls(folder):
    all_data = load_all_sensor_data(folder)
    return detect_falls(all_data)

# rhythm-flow analysis start
def detect_movement_times(data, movement_threshold = 2.5, min_pause = 0.5):
    movement_times = []
    last_time = None

    for ts, ax, ay, az in data:
        mag = compute_magnitude(ax, ay, az)
        if mag > movement_threshold:
            t = datetime.fromisoformat(ts).timestamp()
            if last_time is None or (t - last_time) > min_pause:
                movement_times.append(t)
                last_time = t
    return movement_times

def analyze_rhythm(movement_times):
    if len(movement_times) < 2:
        return None
    intervals = np.diff(movement_times)
    mean_interval = np.mean(intervals)
    std_interval = np.std(intervals)
    rhythm_score = std_interval / mean_interval if mean_interval else float('inf')
    return {
        "mean_interval" : round(mean_interval, 3),
        "std_interval" : round(std_interval, 3),
        "rhythm_score" : round(rhythm_score, 3)
    }

def get_rhythm(folder):
    all_data = load_all_sensor_data(folder)
    all_movement_times = []

    for readings in all_data.values():
        times = detect_movement_times(readings)
        all_movement_times.extend(times)

    all_movement_times.sort()
    return analyze_rhythm(all_movement_times)
