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
        col = "Raw_IFFT" if dev == "Nordic" else "MainMode_Result_m"
        fallback = None if dev == "Nordic" else "Raw_MainMode_m"
        
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

def apply_outlier_filter(df):
    thres = {
        ("Grass", "Nordic"): 1.93,
        ("Grass", "SiLabs 1x1"): 3.24,
        ("Grass", "SiLabs 2x2"): 1.04,
        ("Asphalt", "Nordic"): 1.15,
        ("Asphalt", "SiLabs 1x1"): 3.44,
        ("Asphalt", "SiLabs 2x2"): 1.20,
        ("Indoor", "Nordic"): 1.87,
        ("Indoor", "SiLabs 1x1"): 5.47,
        ("Indoor", "SiLabs 2x2"): 1.85
    }
    parts = []
    for (env, dev), g in df.groupby(["env", "device"]):
        t = thres.get((env, dev))
        parts.append(g[g["err_m"].abs() <= t] if t is not None else g)
    return pd.concat(parts, ignore_index=True) if parts else df

def beta_silabs(sub):
    if sub.empty:
        return np.nan
    per_dist = []
    for _, g_dist in sub.groupby("gt_distance"):
        per_angle = g_dist.groupby("angle_deg")["err_m"].median()
        if not per_angle.empty:
            per_dist.append(per_angle.median())
    return np.mean(per_dist) if per_dist else np.nan

def build_table(df):
    records = []
    POL_ORDER = ["XY-XY", "XY-XZ", "XY-YZ", "YZ-XZ", "YZ-YZ"]
    DEVS = ["Nordic", "SiLabs 1x1", "SiLabs 2x2"]
    
    envs_map = {
        "Grass": df[df["env"] == "Grass"],
        "Asphalt": df[df["env"] == "Asphalt"],
        "Grass+Asphalt": df[df["env"].isin(["Grass", "Asphalt"])],
        "Indoor": df[df["env"] == "Indoor"],
        "All": df
    }
    
    for env_name, df_env in envs_map.items():
        all_means = {d: df_env.loc[df_env["device"] == d, "err_m"].mean() for d in DEVS}
        rows = ["All", "YZ-UL", "XY-SL", "YZ-SL"]
        if env_name != "Grass+Asphalt":
            rows = POL_ORDER + rows
            
        for label in rows:
            rec = {"Env.": env_name, "Orient. pair": label}
            for dev in DEVS:
                sub = df_env[df_env["device"] == dev]
                val = np.nan
                if label in POL_ORDER:
                    val = sub.loc[sub["polpair"] == label, "err_m"].mean()
                elif label == "All":
                    val = all_means[dev]
                elif label == "YZ-UL":
                    val = sub.loc[(sub["polpair"] == "YZ-YZ") & (sub["angle_deg"] == -90), "err_m"].mean()
                elif label in ("XY-SL", "YZ-SL"):
                    val = beta_silabs(sub[sub["polpair"] == ("XY-XY" if label == "XY-SL" else "YZ-YZ")])
                
                if dev == "SiLabs 2x2":
                    rec["SiLabs2 g"] = val
                else:
                    prefix = "Nordic" if dev == "Nordic" else "SiLabs1"
                    rec[f"{prefix} b"] = val
                    rec[f"{prefix} d"] = val - all_means[dev] if label in ("YZ-UL", "XY-SL", "YZ-SL") else np.nan
            records.append(rec)
    return pd.DataFrame(records)

def fmt(v):
    return "" if pd.isna(v) else f"{v:+.2f}"

def print_table(df_table):
    W, SEP = [15, 13, 7, 7, 7, 7, 8], "  "
    TOTAL = sum(W) + len(SEP) * (len(W) - 1)
    
    def row_str(cols):
        return SEP.join(s.rjust(w) if i >= 2 else s.ljust(w) for i, (s, w) in enumerate(zip(cols, W)))
        
    print("=" * TOTAL)
    print(SEP.join(["Env.".ljust(W[0]), "Orient. pair".ljust(W[1]), 
                    "Nordic".center(W[2] + len(SEP) + W[3]), 
                    "SiLabs 1x1".center(W[4] + len(SEP) + W[5]), 
                    "SiLabs 2x2".center(W[6])]))
    print(SEP.join(["".ljust(W[0]), "".ljust(W[1]), 
                    "-" * (W[2] + len(SEP) + W[3]), 
                    "-" * (W[4] + len(SEP) + W[5]), 
                    "-" * W[6]]))
    print(row_str(["", "", "b [m]", "d [m]", "b [m]", "d [m]", "g [m]"]))
    print("-" * TOTAL)
    
    last_env = None
    for i, rec in enumerate(df_table.to_dict("records")):
        env = rec["Env."]
        print(row_str([
            env if env != last_env else "",
            rec["Orient. pair"],
            fmt(rec["Nordic b"]),
            fmt(rec["Nordic d"]),
            fmt(rec["SiLabs1 b"]),
            fmt(rec["SiLabs1 d"]),
            fmt(rec["SiLabs2 g"]),
        ]))
        last_env = env
        next_env = df_table.iloc[i + 1]["Env."] if i + 1 < len(df_table) else None
        if i == len(df_table) - 1:
            print("=" * TOTAL)
        elif next_env != env:
            print("-" * TOTAL)

if __name__ == "__main__":
    print("Loading CS_Dataset ...", file=sys.stderr)
    df_raw = load_data()
    df_filt = apply_outlier_filter(df_raw)
    print_table(build_table(df_filt))
