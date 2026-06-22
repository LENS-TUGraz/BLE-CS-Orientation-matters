import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Style config
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8})

POL_ORDER = ["XY-XY", "XY-XZ", "XY-YZ", "YZ-XZ", "YZ-YZ"]
ENV_DISPLAY = {"Outdoor": "Grass", "Outdoor2": "Asphalt", "Indoor": "Indoor"}
ordered_angles = [0, -45, -90, -135, -180, -225, -270, -315]

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
        
        pol = next((p for p in POL_ORDER if p.replace("-", "_").lower() in parts), None)
        if not pol: continue
        
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
                rows.extend([(env, device_label, pol, float(x - dist_gt)) for x in vals])
            except Exception:
                pass
    return pd.DataFrame(rows, columns=["environment", "device", "polpair", "err_m"])

def plot_cdf(df, env_order=("Outdoor", "Outdoor2", "Indoor"), x_max=10.0, save_prefix="cdf_abs_err"):
    df["abs_err"] = df["err_m"].abs()
    devices = [x for x in ["Nordic", "SiLabs 1x1", "SiLabs 2x2"] if x in set(df["device"])]
    
    fig, axes = plt.subplots(len(env_order), len(devices), figsize=(4.9, 3.6), sharey=True, sharex=True)
    
    for r, env in enumerate(env_order):
        for c, dev in enumerate(devices):
            ax = axes[r, c]
            dd = df[(df["environment"] == env) & (df["device"] == dev)]
            if dd.empty:
                ax.grid(True, alpha=0.25)
                continue
                
            for pol in POL_ORDER:
                ee = dd[dd["polpair"] == pol]["abs_err"].dropna().to_numpy()
                if ee.size == 0: continue
                xs = np.sort(ee)
                ys = np.arange(1, xs.size + 1) / xs.size
                ax.plot(xs, ys, linewidth=1.4, label=pol)
                
            ax.grid(True, alpha=0.25)
            ax.set_xlim(0, x_max)
            ax.set_xticks([0, 2.5, 5.0, 7.5, 10.0])
            ax.set_xticklabels(["0", "2.5", "5.0", "7.5", "10"])
            ax.tick_params(axis="both", which="major", labelsize=8)
            
            if r == len(env_order) - 1:
                ax.set_xlabel(r"$|e|$ [m]")
            if c == 0:
                ax.set_ylabel("CDF")
                ax.annotate(ENV_DISPLAY[env], xy=(0, 0.5), xycoords="axes fraction",
                            xytext=(-ax.yaxis.labelpad - 45, 0), textcoords="offset points",
                            ha="right", va="center", rotation=90, fontsize=11)
            if r == 0:
                ax.set_title(dev)
                
    # Shared Legend at bottom
    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=len(POL_ORDER), frameon=False,
                   fontsize=7, handlelength=2.8, columnspacing=1.1)
                   
    fig.tight_layout(rect=[0, 0.07, 1, 1.0])
    plt.show()

if __name__ == "__main__":
    df = load_data()
    plot_cdf(df)
