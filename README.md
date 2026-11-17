# BLE Channel Sounding: Orientation Matters

This repository contains the dataset and analysis scripts accompanying the study **"Orientation Matters: An Empirical Study on Ranging Performance of Bluetooth 6.0 Channel Sounding"**. The goal of the study is to characterize how the relative orientation between two Bluetooth Low Energy (BLE) devices - and the antenna polarization plane they expose to each other - affects the accuracy of Channel Sounding (CS)-based ranging.

BLE Channel Sounding is a Bluetooth 6.0 feature that enables accurate distance estimation by measuring the phase of received tones across multiple radio channels. While promising for proximity-sensing and indoor positioning, its practical performance can degrade significantly depending on the physical orientation of the communicating devices. This dataset enables a systematic, reproducible investigation of this effect.

---

## Table of Contents

- [Repository Structure](#repository-structure)
- [Dataset Details](#dataset-details)
  - [Environments](#environments)
  - [Hardware Platforms](#hardware-platforms)
  - [Orientation & Polarization Pairs](#orientation--polarization-pairs)
  - [Measurement Angles](#measurement-angles)
  - [File Naming Convention](#file-naming-convention)
  - [CSV Column Reference](#csv-column-reference)
- [Scripts](#scripts)
- [Getting Started](#getting-started)
- [Citation](#citation)

---

## Repository Structure

```
BLE-CS-Orientation-matters/
├── README.md
├── CS_Dataset/
│   ├── Indoor/
│   │   ├── Nordic/
│   │   │   ├── xy_xy/
│   │   │   │   ├── 2m/   ← *_distance.csv + *_iq.csv per angle
│   │   │   │   ├── 4m/
│   │   │   │   ├── 6m/
│   │   │   │   ├── 8m/
│   │   │   │   └── 10m/
│   │   │   ├── xy_xz/
│   │   │   ├── xy_yz/
│   │   │   ├── yz_xz/
│   │   │   └── yz_yz/
│   │   ├── Silabs1x1/   ← same sub-structure as Nordic
│   │   └── Silabs2x2/   ← same sub-structure as Nordic
│   └── Outdoor/
│       ├── Grass/
│       │   ├── Nordic/   ← same polarization-pair structure
│       │   ├── Silabs1x1/
│       │   └── Silabs2x2/
│       └── Asphalt/
│           ├── Nordic/
│           ├── Silabs1x1/
│           └── Silabs2x2/
└── Scripts/
    ├── T1_summary_best_worst.py
    ├── T3_outlier_thresholds.py
    ├── T4_model_selection.py
    ├── T5_calibration_offsets.py
    ├── T6_ranging_performance.py
    ├── F5_plot_cdf.py
    ├── F6_plot_thresholds.py
    └── F7_plot_polar.py
```

---

## Dataset Details

The dataset captures BLE CS ranging measurements across three **environments**, three **hardware platforms**, five **antenna polarization pair configurations**, eight **relative azimuth angles**, and multiple **ground-truth distances**. Each unique combination of these factors constitutes one measurement file.

### Environments

| Environment | Label in code | Ground-truth distances (m) |
|---|---|---|
| Indoor (office corridor) | `Indoor` | 2, 4, 6, 8, 10 |
| Outdoor — grass field | `Grass` | 3, 7.25, 11.5, 15.75, 20 |
| Outdoor — asphalt parking lot | `Asphalt` | 2, 9, 16, 23, 30, 37 |

The indoor environment is a typical office corridor with reflective walls and floors. The outdoor environments were chosen to minimize multipath: an open grass field and a flat asphalt area. Together these three environments span the range from rich-multipath to near-line-of-sight conditions.

### Hardware Platforms

| Folder name | Display name | Antenna configuration | File suffix |
|---|---|---|---|
| `Nordic` | Nordic | Single antenna (1×1) | `_distance.csv`, `_iq.csv` |
| `Silabs1x1` | SiLabs 1×1 | Single antenna (1×1) | `_app.csv` |
| `Silabs2x2` | SiLabs 2×2 | Dual-antenna (2×2) | `_app.csv` |

The Nordic device exports raw IQ samples and intermediate ranging estimates in separate files. The Silicon Labs devices export a combined application-level log (`_app.csv`) that includes both raw and filtered distance estimates as well as RSSI-based ranging for comparison.

### Orientation & Polarization Pairs

Each device was placed in one of two physical orientations relative to the ground plane, defining which polarization plane the antenna faces toward the peer device. The two orientations used are:

- **XY** — the device lies flat, with its antenna polarization in the horizontal plane.
- **YZ** — the device stands upright on its edge, with its antenna polarization in the vertical plane.

Five polarization pair combinations were measured (initiator orientation _ responder orientation):

| Folder | Pair | Description |
|---|---|---|
| `xy_xy` | XY–XY | Both devices flat (horizontal) |
| `xy_xz` | XY–XZ | One flat, one tilted 90° around the X-axis |
| `xy_yz` | XY–YZ | One flat, one standing upright |
| `yz_xz` | YZ–XZ | One standing upright, one tilted |
| `yz_yz` | YZ–YZ | Both devices standing upright (vertical) |

Matched polarization pairs (XY–XY, YZ–YZ) generally yield better performance. Cross-polarization pairs (e.g., XY–XZ, YZ–XZ) introduce a polarization mismatch that can significantly increase ranging error.

### Measurement Angles

Within each distance and polarization-pair configuration, measurements were taken at **8 relative azimuth angles** of the responder device around the initiator, spaced 45° apart:

`0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°`

These angles are encoded in the filename and in the `Degrees` column of each CSV. In the scripts, angles are internally represented as negative integers (e.g., 45° → `-45`) following the clockwise convention used during data collection.

### File Naming Convention

Files follow a consistent naming pattern that encodes all experimental parameters:

```
<environment>_<distance>_<pol_initiator>_<pol_responder>_<antenna_paths>_<angle>_deg[_<suffix>].csv
```

**Example — Nordic indoor:**
```
indoor_2m0_xy_xy_1_1_45_deg_distance.csv
indoor_2m0_xy_xy_1_1_45_deg_iq.csv
```

**Example — SiLabs outdoor (asphalt):**
```
outdoor_2m0_xy_xy_1_1_45_deg_app.csv
```

| Token | Meaning |
|---|---|
| `indoor` / `outdoor` | Environment category |
| `2m0` | Ground-truth distance (2.0 m; underscore replaces decimal point) |
| `xy_xy` | Polarization pair (initiator_responder) |
| `1_1` | Antenna path count for initiator and responder |
| `45_deg` | Relative azimuth angle of the responder |
| `_distance` | Nordic: per-measurement ranging estimates |
| `_iq` | Nordic: raw per-channel IQ sample data |
| `_app` | SiLabs: combined application-level log |

### CSV Column Reference

#### Nordic — `_distance.csv`

Each row represents one ranging measurement (one CS procedure result):

| Column | Description |
|---|---|
| `Timestamp` | ISO 8601 timestamp of the measurement |
| `Measurement_ID` | Sequential measurement index |
| `Environment` | `indoor` or `outdoor` |
| `True_Range_m` | Ground-truth distance in metres |
| `Orientation` | Polarization pair (e.g., `xy_xy`) |
| `Antenna_Paths` | Antenna path configuration (e.g., `1_1`) |
| `Degrees` | Relative azimuth angle (e.g., `45_deg`) |
| `Antenna` | Antenna index used |
| `Raw_IFFT` | Raw range estimate from IFFT processing (m) |
| `Raw_Slope` | Raw range estimate from phase-slope method (m) |
| `Raw_RTT` | Raw range estimate from Round-Trip-Time method (m) |
| `Smoothed_IFFT` | Smoothed (filtered) IFFT range estimate (m) |
| `Smoothed_Slope` | Smoothed phase-slope estimate (m) |
| `Smoothed_RTT` | Smoothed RTT estimate (m) |
| `Tone_Quality` | Overall tone quality flag (`OK` / `BAD`) |
| `TX_Power_dBm` | Transmit power level (dBm) |
| `Tone` | Per-tone quality flag (`OK` / `BAD`) |

> **Note:** Not every method produces an estimate in every measurement. Empty cells indicate that the method did not return a valid result for that procedure (e.g., RTT not available). The scripts use `Raw_IFFT` as the primary ranging column for Nordic.

---

#### Nordic — `_iq.csv`

Each row represents one IQ sample for a single CS tone (channel):

| Column | Description |
|---|---|
| `Timestamp` | ISO 8601 timestamp |
| `Measurement_ID` | Links back to the corresponding `_distance.csv` row |
| `Environment` | `indoor` or `outdoor` |
| `True_Range_m` | Ground-truth distance (m) |
| `Orientation` | Polarization pair |
| `Antenna_Paths` | Antenna path configuration |
| `Degrees` | Relative azimuth angle |
| `Channel` | BLE channel index (48–72 for CS channels) |
| `Local_I` | In-phase component measured locally |
| `Local_Q` | Quadrature component measured locally |
| `Remote_I` | In-phase component measured by the remote device |
| `Remote_Q` | Quadrature component measured by the remote device |
| `TX_Power_dBm` | Transmit power (dBm) |
| `Tone_Quality` | Tone quality at measurement level (`OK` / `BAD`) |
| `TQI` | Tone Quality Indicator flag (`OK` / `BAD`) |

---

#### SiLabs — `_app.csv`

Applies to both `Silabs1x1` and `Silabs2x2`. Each row is one application-level ranging result:

| Column | Description |
|---|---|
| `Timestamp` | ISO 8601 timestamp |
| `APP_ID` | Application-level session/measurement ID |
| `Environment` | `indoor` or `outdoor` |
| `True_Range_m` | Ground-truth distance (m) |
| `Orientation` | Polarization pair (e.g., `xy_xy`) |
| `Antenna_Paths` | Antenna path configuration (e.g., `1_1`) |
| `Degrees` | Relative azimuth angle (e.g., `0_deg`) |
| `Log_Index` | Internal log sequence number |
| `RangingCounter` | Rolling counter for ranging procedures |
| `BT_Address` | Bluetooth address of the remote device |
| `MainMode_Result_mm` | Filtered distance estimate in millimetres |
| `MainMode_Result_m` | Filtered distance estimate in metres |
| `Raw_MainMode_mm` | Raw (unfiltered) distance estimate in millimetres |
| `Raw_MainMode_m` | Raw (unfiltered) distance estimate in metres |
| `MainMode_Likeliness` | Confidence score for the main-mode estimate (0–1) |
| `RSSI_Distance_mm` | RSSI-based distance estimate in millimetres |
| `RSSI_Distance_m` | RSSI-based distance estimate in metres |

> **Note:** The scripts use `Raw_MainMode_m` as the primary ranging column for SiLabs devices (with `MainMode_Result_m` as a fallback).

---

#### Nordic — Outdoor raw IQ (alternative format)

For outdoor Nordic measurements, a slightly different raw format was used:

| Column | Description |
|---|---|
| `Measurement` | Measurement index |
| `Channel_INDEX` | BLE channel index |
| `ANT_PA_0_I_L` | Local I component, antenna 0 |
| `ANT_PA_0_Q_L` | Local Q component, antenna 0 |
| `ANT_PA_0_I_R` | Remote I component, antenna 0 |
| `ANT_PA_0_Q_R` | Remote Q component, antenna 0 |
| `ANT_PA_0_IFFT` | IFFT range estimate for this tone (m) |
| `ANT_PA_0_SLOPE` | Slope-based range estimate for this tone (m) |
| `ANT_PA_0_RTT` | RTT range estimate for this tone (m) |
| `ANT_PA_0_Tone_Status` | Tone quality (`OK` / `BAD`) |
| `Tone` | Overall tone quality flag |

---

## Scripts

All scripts are located in the `Scripts/` directory and should be run from the **repository root** so that relative paths to `CS_Dataset/` resolve correctly.

### Analysis / Table Scripts

| Script | Output | Description |
|---|---|---|
| `T1_summary_best_worst.py` | Table | For each environment × device combination, reports MAE, RMSE, and IQR of ranging error for the empirically best and worst polarization-pair groups. |
| `T3_outlier_thresholds.py` | Table | Computes and compares two outlier rejection thresholds per device/environment: a robust 3σ threshold derived from the data, and a manually tuned threshold. Reports the resulting outlier rates and their difference. |
| `T4_model_selection.py` | Table | Uses leave-one-distance-out cross-validation to compare two calibration models: a **fixed-slope** (additive bias only) and a **free-linear** (gain + bias) correction. Reports RMSE and MAE for each. |
| `T5_calibration_offsets.py` | Table | Estimates per-device systematic bias (calibration offset β) across all environments and polarization pairs. Also reports orientation-specific offsets for selected special cases (e.g., the upright YZ-YZ configuration). |
| `T6_ranging_performance.py` | Table | Main performance table for the indoor environment. Reports MAE, MAE\* (after outlier rejection), RMSE, RMSE\*, and percentile errors (P50, P75, P90, P95) per device and polarization pair, with and without calibration. |

### Plotting Scripts

| Script | Output | Description |
|---|---|---|
| `F5_plot_cdf.py` | Figure | 3×3 grid of Cumulative Distribution Function (CDF) plots of absolute ranging error — one panel per environment × device combination — with separate curves per polarization pair. |
| `F6_plot_thresholds.py` | Figure | Visualizes the outlier threshold values (τ) overlaid on the error distributions for each environment and device. |
| `F7_plot_polar.py` | Figure | 3×5 polar-plot grid (device × polarization pair) for indoor data. Each point encodes the ground-truth distance as its radial position, the relative angle as its angular position, MAE as colour (RdYlGn scale), and IQR as marker size. |

---

## Getting Started

### Prerequisites

Python 3.8+ is required. Install the necessary packages:

```bash
pip install numpy pandas matplotlib seaborn
```

> `seaborn` is required by `F7_plot_polar.py` only. The table scripts (`T*.py`) and `F5_plot_cdf.py` / `F6_plot_thresholds.py` only need `numpy`, `pandas`, and `matplotlib`.

### Running the Scripts

Run all scripts from the **repository root directory** (not from inside `Scripts/`), as they use relative paths to locate `CS_Dataset/`:

```bash
# Generate the main ranging performance table (Table 6 in the paper)
python Scripts/T6_ranging_performance.py

# Generate calibration offset table
python Scripts/T5_calibration_offsets.py

# Generate outlier threshold comparison table
python Scripts/T3_outlier_thresholds.py

# Compare fixed-slope vs. free-linear calibration models
python Scripts/T4_model_selection.py

# Summarize best and worst orientation-pair performance
python Scripts/T1_summary_best_worst.py

# Plot CDF of absolute ranging error per environment and device
python Scripts/F5_plot_cdf.py

# Plot outlier threshold distributions
python Scripts/F6_plot_thresholds.py

# Plot polar orientation-performance map (indoor only)
python Scripts/F7_plot_polar.py
```

---

## Citation

If you use this dataset or scripts in your research, please cite:

```bibtex
@inproceedings{dzafic2026orientation,
  title     = {{Orientation Matters: An Empirical Study on Ranging Performance of Bluetooth 6.0 Channel Sounding}},
  author    = {Dzafic, Dzenita and Pestana, Jes{\'u}s and Schu{\ss}, Markus and Boano, Carlo Alberto and R{\"o}mer, Kay},
  booktitle = {Proceedings of the International Conference on Embedded Wireless Systems and Networks (EWSN)},
  year      = {2026},
  doi       = {10.3217/wr14-7m60},
  url       = {https://github.com/LENS-TUGraz/BLE-CS-Orientation-matters}
}
```

## License

- **Dataset** (`CS_Dataset/`): [CC BY 4.0](LICENSE)
- **Code** (`Scripts/`): [MIT](Scripts/LICENSE)
