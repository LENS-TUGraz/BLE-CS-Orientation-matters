import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, MaxNLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

# Style config
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8})

ENV_ORDER = ["Outdoor (grass)", "Outdoor (asphalt)", "Indoor"]
DEV_ORDER = ["Nordic", "SiLabs 1x1", "SiLabs 2x2"]
ENV_SHORT = {"Outdoor (grass)": "Grass", "Outdoor (asphalt)": "Asphalt", "Indoor": "Indoor"}

THRESHOLDS = {
    ("Outdoor (grass)", "Nordic"): {"tau_3sigma": 1.934, "tau_manual": 2.694},
    ("Outdoor (grass)", "SiLabs 1x1"): {"tau_3sigma": 3.242, "tau_manual": 3.288},
    ("Outdoor (grass)", "SiLabs 2x2"): {"tau_3sigma": 1.04,  "tau_manual": 2.20},
    ("Outdoor (asphalt)", "Nordic"): {"tau_3sigma": 1.151, "tau_manual": 1.564},
    ("Outdoor (asphalt)", "SiLabs 1x1"): {"tau_3sigma": 3.436, "tau_manual": 4.462},
    ("Outdoor (asphalt)", "SiLabs 2x2"): {"tau_3sigma": 1.20,  "tau_manual": 2.50},
    ("Indoor", "Nordic"): {"tau_3sigma": 1.867, "tau_manual": 1.762},
    ("Indoor", "SiLabs 1x1"): {"tau_3sigma": 5.470, "tau_manual": 4.312},
    ("Indoor", "SiLabs 2x2"): {"tau_3sigma": 1.85,  "tau_manual": 2.00},
}

ZOOM_RATIO = {
    ("Outdoor (grass)", "Nordic"): 0.40, ("Outdoor (grass)", "SiLabs 1x1"): 0.30, ("Outdoor (grass)", "SiLabs 2x2"): 0.30,
    ("Outdoor (asphalt)", "Nordic"): 1.00, ("Outdoor (asphalt)", "SiLabs 1x1"): 0.30, ("Outdoor (asphalt)", "SiLabs 2x2"): 0.30,
    ("Indoor", "Nordic"): 0.40, ("Indoor", "SiLabs 1x1"): 0.40, ("Indoor", "SiLabs 2x2"): 0.40,
}

BINS, XMAX_PLOT = 100, 30.0
BIN_EDGES = np.linspace(0.0, XMAX_PLOT, BINS + 1)

def load_data(root_dir="CS_Dataset"):
    ALLOWED_D = {
        "Outdoor (grass)": [3.0, 7.25, 11.5, 15.75, 20.0],
        "Outdoor (asphalt)": [2.0, 9.0, 16.0, 23.0, 30.0, 37.0],
        "Indoor": [2.0, 4.0, 6.0, 8.0, 10.0]
    }
    rows = []
    for root, _, files in os.walk(root_dir):
        parts = os.path.relpath(root, root_dir).split(os.sep)
        if not parts or parts[0] == ".": continue
        
        env = "Indoor" if parts[0] == "Indoor" else f"Outdoor ({parts[1].lower()})" if len(parts) >= 2 and parts[0] == "Outdoor" else None
        if not env: continue
        
        dev = next((d for d in ["Nordic", "Silabs1x1", "Silabs2x2"] if d in parts), None)
        if not dev: continue
        device_label = "Nordic" if dev == "Nordic" else f"SiLabs {'1x1' if '1x1' in dev else '2x2'}"
        
        suffix, col = ("_distance.csv", "Raw_IFFT") if dev == "Nordic" else ("_app.csv", "Raw_MainMode_m")
        
        for f in files:
            if not f.endswith(suffix): continue
            try:
                df = pd.read_csv(os.path.join(root, f))
                if col not in df.columns or df.empty: continue
                
                # Snap distance
                dist_val = float(parts[-1].lower().replace("m", "").replace("_", "."))
                allowed = ALLOWED_D[env]
                dist_gt = allowed[np.argmin(np.abs(np.array(allowed) - dist_val))]
                if abs(dist_gt - dist_val) > 0.25: continue
                
                # Check angle
                deg = float(str(df["Degrees"].iloc[0]).replace("_deg", "")) % 360.0
                angle = 0 if np.isclose(deg, 0.0) or np.isclose(deg, 360.0) else int(-round(deg))
                if angle not in [0, -45, -90, -135, -180, -225, -270, -315]: continue
                
                vals = pd.to_numeric(df[col], errors="coerce").dropna().to_numpy()
                rows.extend([(env, device_label, float(x - dist_gt)) for x in vals])
            except Exception:
                pass
    return pd.DataFrame(rows, columns=["environment", "device", "err_m"])

def plot_hist_on_ax(ax, df, t_3s, t_man, z_ratio):
    x = df["abs_err_m"].dropna().to_numpy()
    counts, edges = np.histogram(x, bins=BIN_EDGES)
    y = counts / (counts.max() if counts.size and counts.max() > 0 else 1)

    ax.bar(edges[:-1], y, width=np.diff(edges), align="edge", linewidth=0)
    for t, c in [(t_3s, "red"), (t_man, "green")]:
        ax.axvline(t, linewidth=1.5, color=c, linestyle="--")

    ax.set_xlim(0.0, XMAX_PLOT)
    ax.set_ylim(0.0, 1.0)
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.45)
    ax.yaxis.set_major_locator(MultipleLocator(0.5))
    ax.xaxis.set_major_locator(MultipleLocator(10))

    ax.text(0.97, 0.93, rf"$\tau_{{3\sigma}}={t_3s:.2f}\,\mathrm{{m}}$", transform=ax.transAxes, color="red", ha="right", va="center", fontsize=7.5)
    ax.text(0.97, 0.79, rf"$\tau_{{\mathrm{{man}}}}={t_man:.2f}\,\mathrm{{m}}$", transform=ax.transAxes, color="green", ha="right", va="center", fontsize=7.5)

    axins = inset_axes(ax, width="100%", height="100%", loc="lower left", bbox_to_anchor=(0.56, 0.16, 0.42, 0.42), bbox_transform=ax.transAxes)
    axins.bar(edges[:-1], y, width=np.diff(edges), align="edge", linewidth=0)
    axins.axvline(t_3s, linewidth=1.2, color="red", linestyle="--")
    axins.axvline(t_man, linewidth=1.2, color="green", linestyle="--")
    axins.set_xlim(0.0, max(t_3s, t_man) * (1.0 + z_ratio))
    axins.set_ylim(0.0, 1.0)
    axins.grid(True, linestyle="--", linewidth=0.3, alpha=0.4)
    axins.yaxis.set_major_locator(MultipleLocator(0.5))
    axins.xaxis.set_major_locator(MaxNLocator(nbins=2))
    axins.tick_params(labelsize=6.5, pad=1)
    mark_inset(ax, axins, loc1=2, loc2=3, fc="none", ec="0.35", lw=0.8)

def main():
    OUT_DIR = "env_device_gauss3sigma_hist_3x3_onecol"
    os.makedirs(OUT_DIR, exist_ok=True)
    
    df = load_data()
    df["abs_err_m"] = df["err_m"].abs()
    
    fig, axes = plt.subplots(3, 3, figsize=(4.9, 3.6), sharex=True, sharey=True)
    fig.supylabel("Norm. count", x=0.02)
    
    summary = []
    for r, env in enumerate(ENV_ORDER):
        for c, dev in enumerate(DEV_ORDER):
            ax = axes[r, c]
            if r == 0: ax.set_title(dev, pad=3)
            
            d = df[(df["environment"] == env) & (df["device"] == dev)]
            if d.empty:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center", va="center", fontsize=7)
                continue
                
            t_3s, t_man = THRESHOLDS[(env, dev)]["tau_3sigma"], THRESHOLDS[(env, dev)]["tau_manual"]
            plot_hist_on_ax(ax, d, t_3s, t_man, ZOOM_RATIO[(env, dev)])
            
            ax.set_ylabel(ENV_SHORT[env] if c == 0 else "", labelpad=1)
            if c > 0: ax.tick_params(axis="y", labelleft=False)
            ax.set_xlabel(r"$|e|$ [m]" if r == 2 else "", labelpad=1)
            
            n_total = len(d)
            n_3s = (d["abs_err_m"] > t_3s).sum()
            n_man = (d["abs_err_m"] > t_man).sum()
            p_3s = 100.0 * n_3s / n_total
            p_man = 100.0 * n_man / n_total
            
            summary.append({
                "environment": env, "device": dev, "tau_3sigma": t_3s, "tau_manual": t_man,
                "n_total": n_total, "n_outliers_3sigma": n_3s, "p_outliers_3sigma": p_3s,
                "n_outliers_manual": n_man, "p_outliers_manual": p_man,
                "delta_pp": p_3s - p_man, "zoom_ratio": ZOOM_RATIO[(env, dev)]
            })
            
    fig.subplots_adjust(left=0.10, right=0.995, top=0.92, bottom=0.12, wspace=0.12, hspace=0.16)
    plt.show()

if __name__ == "__main__":
    main()
