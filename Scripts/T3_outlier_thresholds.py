import os
import numpy as np
import pandas as pd

ENV_LABEL = {"Outdoor": "Grass", "Outdoor2": "Asphalt", "Indoor": "Indoor"}
ENV_ORDER = ["Outdoor", "Outdoor2", "Indoor"]
DEVICE_ORDER = ["Nordic", "SiLabs 1x1", "SiLabs 2x2"]
ordered_angles = [0, -45, -90, -135, -180, -225, -270, -315]

TAU_MANUAL = {
    ("Outdoor",  "Nordic"):      2.69, ("Outdoor",  "SiLabs 1x1"):  3.29, ("Outdoor",  "SiLabs 2x2"):  2.20,
    ("Outdoor2", "Nordic"):      1.56, ("Outdoor2", "SiLabs 1x1"):  4.46, ("Outdoor2", "SiLabs 2x2"):  2.50,
    ("Indoor",   "Nordic"):      1.76, ("Indoor",   "SiLabs 1x1"):  4.31, ("Indoor",   "SiLabs 2x2"):  2.00,
}

def normalize_angle(a):
    try:
        a = float(a) % 360.0
        return 0 if np.isclose(a, 0.0) or np.isclose(a, 360.0) else int(-round(a))
    except Exception:
        return None

def load_data(root_dir="CS_Dataset"):
    ALLOWED_D = {
        "Outdoor": [3.0, 7.25, 11.5, 15.75, 20.0],
        "Outdoor2": [2.0, 9.0, 16.0, 23.0, 30.0, 37.0],
        "Indoor": [2.0, 4.0, 6.0, 8.0, 10.0]
    }
    rows = []
    for root, _, files in os.walk(root_dir):
        parts = os.path.relpath(root, root_dir).split(os.sep)
        if not parts or parts[0] == ".": continue
        
        env = "Indoor" if parts[0] == "Indoor" else "Outdoor" if len(parts) >= 2 and parts[1] == "Grass" else "Outdoor2" if len(parts) >= 2 and parts[1] == "Asphalt" else None
        if not env: continue
        
        dev = next((d for d in ["Nordic", "Silabs1x1", "Silabs2x2"] if d in parts), None)
        if not dev: continue
        device_label = {"Nordic": "Nordic", "Silabs1x1": "SiLabs 1x1", "Silabs2x2": "SiLabs 2x2"}[dev]
        
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
                rows.extend([(env, device_label, float(x - dist_gt)) for x in vals])
            except Exception:
                pass
    return pd.DataFrame(rows, columns=["environment", "device", "err_m"])

def robust_tau_3sigma(abs_err):
    abs_err = abs_err[np.isfinite(abs_err)]
    med = np.median(abs_err)
    mad = np.median(np.abs(abs_err - med))
    return med + 3.0 * (1.4826 * mad)

def main():
    df = load_data()
    df["abs_err"] = df["err_m"].abs()
    
    rows = []
    for env in ENV_ORDER:
        for dev in DEVICE_ORDER:
            g = df[(df["environment"] == env) & (df["device"] == dev)]
            if g.empty: continue
            
            abs_err = g["abs_err"].to_numpy(dtype=float)
            tau_3s = robust_tau_3sigma(abs_err)
            tau_man = TAU_MANUAL[(env, dev)]
            
            outl_3s = 100.0 * np.mean(abs_err > tau_3s)
            outl_man = 100.0 * np.mean(abs_err > tau_man)
            
            rows.append({
                "Env.": ENV_LABEL[env], "Device": dev,
                r"$\tau_{3\sigma}$ [m]": tau_3s, r"$\tau_{\mathrm{man}}$ [m]": tau_man,
                r"Outl. ($3\sigma$) [\%]": outl_3s, r"Outl. (man.) [\%]": outl_man,
                r"$\Delta$ [\%]": outl_3s - outl_man,
            })
            
    threshold_table = pd.DataFrame(rows).round(2)
    print(threshold_table.to_string(index=False))

if __name__ == "__main__":
    main()
