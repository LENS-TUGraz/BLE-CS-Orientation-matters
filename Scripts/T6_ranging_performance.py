import os
import sys
import numpy as np
import pandas as pd

def load_data():
    allowed = {
        "Grass": [3.0, 7.25, 11.5, 15.75, 20.0],
        "Asphalt": [2.0, 9.0, 16.0, 23.0, 30.0, 37.0],
        "Indoor": [2.0, 4.0, 6.0, 8.0, 10.0]
    }
    rows = []
    for root, _, files in os.walk("CS_Dataset"):
        parts = os.path.relpath(root, "CS_Dataset").split(os.sep)
        if len(parts) < 4:
            continue
        env = "Indoor" if parts[0] == "Indoor" else parts[1]
        if env not in allowed:
            continue
        
        dev = {"Nordic": "Nordic", "Silabs1x1": "SiLabs 1x1", "Silabs2x2": "SiLabs 2x2"}.get(parts[1] if env == "Indoor" else parts[2])
        if not dev:
            continue
        
        pol = (parts[2] if env == "Indoor" else parts[3]).upper().replace("_", "-")
        if pol not in ["XY-XY", "XY-XZ", "XY-YZ", "YZ-XZ", "YZ-YZ"]:
            continue
            
        try:
            dist_raw = float(parts[-1].lower().replace("m", "").replace("_", "."))
        except ValueError:
            continue
        dist_gt = min(allowed[env], key=lambda x: abs(x - dist_raw))
        if abs(dist_gt - dist_raw) > 0.25:
            continue
            
        suffix = "_distance.csv" if dev == "Nordic" else "_app.csv"
        col = "Raw_IFFT" if dev == "Nordic" else "Raw_MainMode_m"
        fallback = None if dev == "Nordic" else "MainMode_Result_m"
        
        for f in files:
            if not f.endswith(suffix):
                continue
            df = pd.read_csv(os.path.join(root, f))
            c = col if col in df.columns else fallback
            if not c or df.empty:
                continue
            
            raw_angle = str(df["Degrees"].iloc[0]).replace("_deg", "")
            try:
                ang = int(round(float(raw_angle) % 360))
                angle = -ang if ang else 0
            except:
                continue
            if angle not in [0, -45, -90, -135, -180, -225, -270, -315]:
                continue
                
            vals = pd.to_numeric(df[c], errors="coerce").dropna().values
            rows.extend((env, dev, pol, angle, dist_gt, float(v - dist_gt)) for v in vals)
            
    return pd.DataFrame(rows, columns=["env", "device", "polpair", "angle_deg", "gt_distance", "err_m"])

def build_table(df):
    df_indoor = df[df["env"] == "Indoor"].copy()
    
    offsets = {"Nordic": 0.59, "SiLabs 1x1": 1.31, "SiLabs 2x2": 0.0}
    custom_offsets = {("Nordic", "XY-SL"): 0.41, ("SiLabs 1x1", "YZ-UL"): 1.08}
    thres = {"Nordic": 1.87, "SiLabs 1x1": 5.47, "SiLabs 2x2": 1.85}
    
    POL_ORDER = ["XY-XY", "XY-XZ", "XY-YZ", "YZ-XZ", "YZ-YZ", "All"]
    records = []
    
    for dev in ["Nordic", "SiLabs 1x1", "SiLabs 2x2"]:
        sub_dev = df_indoor[df_indoor["device"] == dev]
        t = thres[dev]
        rows = POL_ORDER + (["XY-SL"] if dev == "Nordic" else (["YZ-UL"] if dev == "SiLabs 1x1" else []))
        
        for pol in rows:
            if pol == "All":
                g = sub_dev.copy()
                beta = offsets[dev]
            elif (dev, pol) in custom_offsets:
                g = sub_dev.copy()
                beta = custom_offsets[(dev, pol)]
            else:
                g = sub_dev[sub_dev["polpair"] == pol].copy()
                beta = offsets[dev]
                
            if g.empty:
                continue
            
            g["err_corr"] = g["err_m"] - beta
            errs = g["err_corr"].values
            
            mae_val = np.mean(np.abs(errs))
            rmse_val = np.sqrt(np.mean(errs**2))
            p50, p75, p90, p95 = np.percentile(errs, [50, 75, 90, 95])
            
            errs_in = g.loc[g["err_corr"].abs() <= t, "err_corr"].values
            mae_in = np.mean(np.abs(errs_in)) if errs_in.size else np.nan
            rmse_in = np.sqrt(np.mean(errs_in**2)) if errs_in.size else np.nan
            
            records.append({
                "Device": dev,
                "Orient. pair": pol,
                "MAE": mae_val,
                "MAE*": mae_in,
                "RMSE": rmse_val,
                "RMSE*": rmse_in,
                "P50": p50,
                "P75": p75,
                "P90": p90,
                "P95": p95
            })
            
    return pd.DataFrame(records)

def print_table(df_table):
    W, SEP = [12, 13, 6, 6, 6, 6, 6, 6, 6, 6], "  "
    TOTAL = sum(W) + len(SEP) * (len(W) - 1)
    
    def row_str(cols):
        return SEP.join(s.rjust(w) if i >= 2 else s.ljust(w) for i, (s, w) in enumerate(zip(cols, W)))
        
    print("=" * TOTAL)
    print(row_str(["Device", "Orient. pair", "MAE", "MAE*", "RMSE", "RMSE*", "P50", "P75", "P90", "P95"]))
    print("-" * TOTAL)
    
    last_dev = None
    for i, rec in enumerate(df_table.to_dict("records")):
        dev = rec["Device"]
        print(row_str([
            dev if dev != last_dev else "",
            rec["Orient. pair"],
            f"{rec['MAE']:.2f}",
            f"{rec['MAE*']:.2f}",
            f"{rec['RMSE']:.2f}",
            f"{rec['RMSE*']:.2f}",
            f"{rec['P50']:.2f}",
            f"{rec['P75']:.2f}",
            f"{rec['P90']:.2f}",
            f"{rec['P95']:.2f}",
        ]))
        last_dev = dev
        next_dev = df_table.iloc[i + 1]["Device"] if i + 1 < len(df_table) else None
        if i == len(df_table) - 1:
            print("=" * TOTAL)
        elif next_dev != dev:
            print("-" * TOTAL)

if __name__ == "__main__":
    print("Loading CS_Dataset ...", file=sys.stderr)
    df_raw = load_data()
    print_table(build_table(df_raw))
