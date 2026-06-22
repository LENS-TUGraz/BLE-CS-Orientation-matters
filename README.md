# BLE Channel Sounding: Orientation Matters

This repository contains the analysis scripts and dataset for evaluating the performance of Bluetooth Low Energy (BLE) Channel Sounding (CS) across different device orientations, environments, and hardware platforms.

## Repository Structure

- `CS_Dataset/`: Contains the collected raw data from various BLE devices in different settings.
  - Environments: Indoor, Outdoor (Grass), Outdoor (Asphalt).
  - Devices: Nordic, SiLabs 1x1, SiLabs 2x2.
  - Ranging distances and orientations are included.
- `Scripts/`: Python scripts for processing data, performing model selection, and plotting results.
  - `T1_summary_best_worst.py`: Summarizes the best and worst performance cases.
  - `T3_outlier_thresholds.py`: Calculates and applies outlier thresholds for the ranging data.
  - `T4_model_selection.py`: Performs model selection on the ranging data.
  - `T5_calibration_offsets.py`: Calculates calibration offsets for the devices.
  - `T6_ranging_performance.py`: Evaluates the overall ranging performance.
  - `F5_plot_cdf.py`: Generates Cumulative Distribution Function (CDF) plots for ranging errors.
  - `F6_plot_thresholds.py`: Plots outlier thresholds.
  - `F7_plot_polar.py`: Generates polar plots to visualize orientation-dependent performance.

## Getting Started

### Prerequisites

You need Python 3 installed along with the following packages:
- `numpy`
- `pandas`
- `matplotlib` (for plotting scripts)

You can install the dependencies using pip:
```bash
pip install numpy pandas matplotlib
```

### Running the Scripts

Navigate to the `Scripts/` directory and run any of the analysis scripts. They will automatically load data from the `CS_Dataset/` directory in the repository root.

Example:
```bash
python Scripts/T5_calibration_offsets.py
```

## Dataset Details

The `CS_Dataset` is structured by environment, device, and polarization pair. It includes ranging estimates collected over various ground-truth distances and relative angles between the devices. The scripts process this data to evaluate how hardware, environment, and relative orientation impact BLE Channel Sounding accuracy.
