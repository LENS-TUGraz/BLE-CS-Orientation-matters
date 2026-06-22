import os
import numpy as np
import pandas as pd

ENV_DISPLAY = {"Outdoor (grass)": "Grass", "Outdoor (asphalt)": "Asphalt"}
THRESHOLDS = {
    ("Outdoor (grass)", "Nordic"): 1.934,
    ("Outdoor (grass)", "SiLabs 1x1"): 3.242,
    ("Outdoor (asphalt)", "Nordic"): 1.151,
    ("Outdoor (asphalt)", "SiLabs 1x1"): 3.436,
}
ordered_angles = [0, -45, -90, -135, -180, -225, -270, -315]

def normalize_angle(a):
    try:
        a = float(a) % 360.0
        return 0 if np.isclose(a, 0.0) or np.isclose(a, 360.0) else int(-round(a))
    except Exception:
        return None

def load_data(root_dir="CS_Dataset"):
    ALLOWED_D = {
        "Outdoor (grass)": [3.0, 7.25, 11.5, 15.75, 20.0],
        "Outdoor (asphalt)": [2.0, 9.0, 16.0, 23.0, 30.0, 37.0]
    }
    rows = []
    for root, _, files in os.walk(root_dir):
        parts = os.path.relpath(root, root_dir).split(os.sep)
        if not parts or parts[0] == ".": continue
        
        env = "Outdoor (grass)" if len(parts) >= 2 and parts[1] == "Grass" else "Outdoor (asphalt)" if len(parts) >= 2 and parts[1] == "Asphalt" else None
        if not env: continue
        
        dev = next((d for d in ["Nordic", "Silabs1x1"] if d in parts), None)
        if not dev: continue
        device_label = "Nordic" if dev == "Nordic" else "SiLabs 1x1"
        
        suffix, col = ("_distance.csv", "Raw_IFFT") if dev == "Nordic" else ("_app.csv", "Raw_MainMode_m")
        for f in files:
            if not f.endswith(suffix): continue
            try:
                df = pd.read_csv(os.path.join(root, f))
                if col not in df.columns or df.empty: continue
                
                dist_val = float(parts[-1].lower().replace("m", "").replace("_", "."))
                dist_gt = min(ALLOWED_D[env], key=lambda x: abs(x - dist_val))
                if abs(dist_gt - dist_val) > 0.25: continue
                
                angle = normalize_angle(str(df["Degrees"].iloc[0]).replace("_deg", ""))
                if angle not in ordered_angles: continue
                
                vals = pd.to_numeric(df[col], errors="coerce").dropna().to_numpy()
                rows.extend([(env, device_label, float(dist_gt), float(x)) for x in vals])
            except Exception:
                pass
    return pd.DataFrame(rows, columns=["environment", "device", "gt_m", "meas_m"])

def lodo_cv(d, model):
    g_unique = np.sort(d["gt_m"].unique())
    preds, trues = [], []
    for g0 in g_unique:
        test, train = d[d["gt_m"] == g0], d[d["gt_m"] != g0]
        if train.empty or test.empty: continue
        
        if model == "fixed_slope":
            beta = (train["meas_m"] - train["gt_m"]).mean()
            g_hat = test["meas_m"] - beta
        else:
            g, m = train["gt_m"].to_numpy(), train["meas_m"].to_numpy()
            A = np.column_stack([g, np.ones_like(g)])
            (a, b), *_ = np.linalg.lstsq(A, m, rcond=None)
            g_hat = (test["meas_m"] - b) / a
            
        preds.append(g_hat)
        trues.append(test["gt_m"])
        
    yhat, y = np.concatenate(preds), np.concatenate(trues)
    err = yhat - y
    return float(np.sqrt(np.mean(err**2))), float(np.mean(np.abs(err)))

def main():
    df = load_data()
    df["abs_err"] = (df["meas_m"] - df["gt_m"]).abs()
    
    rows = []
    for env in ["Outdoor (grass)", "Outdoor (asphalt)"]:
        for dev in ["Nordic", "SiLabs 1x1"]:
            tau = THRESHOLDS[(env, dev)]
            d_filtered = df[(df["environment"] == env) & (df["device"] == dev) & (df["abs_err"] <= tau)]
            rmse_fix, mae_fix = lodo_cv(d_filtered, "fixed_slope")
            rmse_lin, mae_lin = lodo_cv(d_filtered, "free_linear")
            
            rows.append({
                "Env.": ENV_DISPLAY[env], "Device": dev,
                "RMSE_fix": rmse_fix, "RMSE_lin": rmse_lin,
                "MAE_fix": mae_fix, "MAE_lin": mae_lin
            })
            
    res_df = pd.DataFrame(rows).round(3)
    print(res_df.to_string(index=False))

if __name__ == "__main__":
    main()
