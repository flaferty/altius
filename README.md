# Altius

Altius is a Python-based system for analysis of climbing performance using 4 Arduino Nano 33 BLE sensors. It collects sensor data via Bluetooth, saves it to CSV files, and provides feedback to the user on climbing technique through a Graphical User Interface.

## Features

- **4 limb IMU logging:** Collects data from four Arduinos (left arm, right arm, left leg, right leg), each running its own firmware.
- **GUI:** Tkinter-based user interface for starting/stopping data collection and viewing performance scores.
- **Scoring:** Calculates and displays scores for:
  - Arm/leg usage ratio
  - Stability
  - Movement smoothness
  - Rhythm/flow
  - Grip count
  - Fall detection
- **CSV-based storage:** Each Arduino writes to a separate CSV file.

## Setup

1. **Clone this repository** 
```sh
    git clone https://github.com/flaferty/altius.git
    cd altius
```

2. **Set up the 4 Arduinos using the `.ino` file from the appropriate `arduino_setup/` subfolder**

3. **Power the Arduinos and secure each device to its respective limb using the custom-designed enclosures**
4. **Run the GUI:**
   ```sh
   python code/gui.py
   ```

## Usage

- **Start the logger** - The GUI will scan for the available IMU devices and connect to them.
- **Data is streamed** from each Arduino and saved to `data/` as a CSV file.
- **Stop the logger** using the **X** button in the GUI to end the session.
- **Scores and feedback** are calculated and displayed automatically.

## Code Structure
```bash
altius/
├── data/                       # Directory for CSV files
├── setup/                      # Arduino setup files
├── code/
    ├── gui.py                  # GUI and application logic
    ├── logger.py               # Handles Bluetooth scanning, connection, and CSV logging
    ├── arm_leg_usage.py        # Calculates arm/leg usage ratios
    ├── stability.py            # Computes stability score
    ├── smoothness.py           # Analyzes movement smoothness
    ├── fall_rhythm.py          # Detects falls and analyzes climbing rhythm/flow
    ├── grip_count.py           # Counts grip events from stillness periods
```
