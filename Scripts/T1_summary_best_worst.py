import os
import numpy as np
import pandas as pd

CS_DATASET_ROOT = r"CS_Dataset"
POL_ORDER = ["XY-XY", "XY-XZ", "XY-YZ", "YZ-XZ", "YZ-YZ"]
ORDERED_ANGLES = [0, -45, -90, -135, -180, -225, -270, -315]

ENV_MAPPING = {"Indoor": "Indoor", "Outdoor\\Grass": "Grass", "Outdoor\\Asphalt": "Asphalt"}
DEVICE_MAPPING = {"Nordic": "Nordic", "Silabs1x1": "SiLabs 1x1", "Silabs2x2": "SiLabs 2x2"}

ALLOWED_D = {
    "Indoor": [2.0, 4.0, 6.0, 8.0, 10.0],
    "Grass": [3.0, 7.25, 11.5, 15.75, 20.0],
    "Asphalt": [2.0, 9.0, 16.0, 23.0, 30.0, 37.0]
}

ENV_ORDER = ("Grass", "Asphalt", "Indoor")
DEVICE_ORDER = ("Nordic", "SiLabs 1x1", "SiLabs 2x2")

RULES_WORST = {
    ("Grass", "Nordic"): ["XY-XZ", "YZ-XZ"],
    ("Grass", "SiLabs 1x1"): ["XY-XY", "YZ-XZ", "XY-XZ"],
    ("Grass", "SiLabs 2x2"): [],
    ("Asphalt", "Nordic"): ["XY-XZ"],
    ("Asphalt", "SiLabs 1x1"): ["XY-XY", "XY-XZ", "YZ-XZ"],
    ("Asphalt", "SiLabs 2x2"): [],
    ("Indoor", "Nordic"): ["XY-XZ"],
    ("Indoor", "SiLabs 1x1"): ["XY-XY", "XY-XZ", "YZ-XZ", "XY-YZ"],
    ("Indoor", "SiLabs 2x2"): [],
}

def normalize_angle(a):
    try:
        a = float(a) % 360.0
        return 0 if np.isclose(a, 0.0) or np.isclose(a, 360.0) else int(-round(a))
    except ValueError:
        return None

def snap_distance(dist_gt, allowed, tol=0.25):
    if pd.isna(dist_gt): return None
    idx = int(np.argmin(np.abs(np.array(allowed) - float(dist_gt))))
    return allowed[idx] if abs(allowed[idx] - float(dist_gt)) <= tol else None

def collect_errors(root_dir):
    rows = []
    for root, dirs, files in os.walk(root_dir):
        parts = os.path.relpath(root, root_dir).split(os.sep)
        env_label = ENV_MAPPING.get("Outdoor\\" + parts[1] if len(parts) >= 2 and parts[0] == "Outdoor" else parts[0] if parts else None)
        device_label = next((v for k, v in DEVICE_MAPPING.items() if k in parts), None)
        
        if not env_label or not device_label: continue
        
        is_nordic = (device_label == "Nordic")
        suffix, col = ("_distance.csv", "Raw_IFFT") if is_nordic else ("_app.csv", "Raw_MainMode_m")
        
        for f in [x for x in files if x.endswith(suffix)]:
            try:
                df = pd.read_csv(os.path.join(root, f))
                if col not in df.columns or df.empty: continue
                
                dist_str = parts[-1].lower().replace("m", "").replace("_", ".")
                raw_dist = float(dist_str)
                degrees_str = str(df["Degrees"].iloc[0]).replace("_deg", "")
                
                orientation_raw = str(df["Orientation"].iloc[0]).strip().upper().replace("_", "-")
                orientation = next((p for p in POL_ORDER if p in orientation_raw), "")
                if not orientation or orientation in ("NAN", "NONE"):
                    orientation = next((p.replace("_", "-").upper() for p in parts if p.replace("_", "-").upper() in POL_ORDER), "")
                
                dist_gt = snap_distance(raw_dist, ALLOWED_D[env_label])
                angle = normalize_angle(degrees_str)
                
                if dist_gt is None or angle not in ORDERED_ANGLES or orientation not in POL_ORDER: continue
                
                vals = pd.to_numeric(df[col], errors="coerce").to_numpy()
                vals = vals[np.isfinite(vals)]
                rows.extend([(env_label, device_label, orientation, float(x - dist_gt)) for x in vals])
            except Exception:
                pass
    return pd.DataFrame(rows, columns=["environment", "device", "polpair", "err_m"])

if __name__ == "__main__":
    df = collect_errors(CS_DATASET_ROOT)
    df["abs_err"] = np.abs(df["err_m"])
    
    out_rows = []
    for env in ENV_ORDER:
        for dev in DEVICE_ORDER:
            g = df[(df["environment"] == env) & (df["device"] == dev)]
            worst = RULES_WORST.get((env, dev), [])
            best = [p for p in POL_ORDER if p in set(g["polpair"]) and p not in worst]
            
            for group, pols in [("BEST", best), ("WORST", worst)]:
                sub = g[g["polpair"].isin(pols)]
                e, ae = sub["err_m"].to_numpy(), sub["abs_err"].to_numpy()
                
                out_rows.append({
                    "Environment": env, "Device": dev, "Group": group,
                    "Polpairs": ", ".join(pols) if pols else "—",
                    "MAE [m]": np.nanmean(ae) if e.size else np.nan,
                    "RMSE [m]": np.sqrt(np.nanmean(e**2)) if e.size else np.nan,
                    "IQR(|e|) [m]": np.subtract(*np.nanpercentile(ae, [75, 25])) if e.size else np.nan
                })
                
    table = pd.DataFrame(out_rows)
    print(table.to_string(index=False))
