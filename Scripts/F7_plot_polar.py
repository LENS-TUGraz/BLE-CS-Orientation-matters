import os
import sys
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl

sns.set_theme(style="whitegrid", context="paper")

# Configs matching the legacy script
ANGLES = [0, -45, -90, -135, -180, -225, -270, -315]
GT_LEVELS = [2.0, 4.0, 6.0, 8.0, 10.0]
POL_ORDER = ["XY-XY", "XY-XZ", "XY-YZ", "YZ-XZ", "YZ-YZ"]
DEV_ORDER = ["Nordic", "SiLabs 1x1", "SiLabs 2x2"]
OFFSETS_M = {"Nordic": 0.5862, "SiLabs 1x1": 1.3111, "SiLabs 2x2": 0.0}

IQR_CAP_Q = 0.95
DOT_S_MIN = 18
DOT_S_MAX = 140
CMAP_NAME = "RdYlGn_r"
MAE_VMAX = 20.0

def load_data():
    rows = []
    for root, _, files in os.walk("CS_Dataset/Indoor"):
        parts = os.path.relpath(root, "CS_Dataset/Indoor").split(os.sep)
        if len(parts) < 3:
            continue
        dev = {"Nordic": "Nordic", "Silabs1x1": "SiLabs 1x1", "Silabs2x2": "SiLabs 2x2"}.get(parts[0])
        pol = parts[1].upper().replace("_", "-")
        if not dev or pol not in POL_ORDER:
            continue
            
        try:
            dist_raw = float(parts[-1].lower().replace("m", "").replace("_", "."))
        except ValueError:
            continue
        dist_gt = min(GT_LEVELS, key=lambda x: abs(x - dist_raw))
        if abs(dist_gt - dist_raw) > 0.25:
            continue
            
        suffix = "_distance.csv" if dev == "Nordic" else "_app.csv"
        col = "Smoothed_IFFT" if dev == "Nordic" else "Raw_MainMode_m"
        
        for f in files:
            if not f.endswith(suffix):
                continue
            df = pd.read_csv(os.path.join(root, f))
            if col not in df.columns or df.empty:
                continue
                
            raw_angle = str(df["Degrees"].iloc[0]).replace("_deg", "")
            try:
                ang = int(round(float(raw_angle) % 360))
                angle = -ang if ang else 0
            except:
                continue
            if angle not in ANGLES:
                continue
                
            vals = pd.to_numeric(df[col], errors="coerce").dropna().values
            rows.extend((dev, pol, dist_gt, angle, float(v)) for v in vals)
            
    df = pd.DataFrame(rows, columns=["device", "polpair", "gt_m", "angle_deg", "meas_m"])
    df["meas_corr"] = df["meas_m"] - df["device"].map(OFFSETS_M)
    
    pts = []
    for (dev, pol, gt, ang), sub in df.groupby(["device", "polpair", "gt_m", "angle_deg"]):
        x = sub["meas_corr"].values
        mae = np.mean(np.abs(x - gt))
        iqr = np.percentile(x, 75) - np.percentile(x, 25)
        pts.append({"device": dev, "polpair": pol, "gt_m": gt, "angle_deg": ang, "mae_m": mae, "iqr_m": iqr})
        
    pts = pd.DataFrame(pts)
    pts["device"] = pd.Categorical(pts["device"], categories=DEV_ORDER, ordered=True)
    pts["polpair"] = pd.Categorical(pts["polpair"], categories=POL_ORDER, ordered=True)
    pts["angle_cat"] = pd.Categorical(pts["angle_deg"], categories=ANGLES, ordered=True)
    pts["gt_cat"] = pd.Categorical(pts["gt_m"], categories=GT_LEVELS, ordered=True)
    return pts.sort_values(["device", "polpair", "gt_cat", "angle_cat"]).reset_index(drop=True)

def make_radius_mapper(gt_levels):
    gt_levels = np.asarray(gt_levels, dtype=float)
    rings = np.arange(1, len(gt_levels) + 1, dtype=float)
    return lambda d: np.interp(np.asarray(d, dtype=float), gt_levels, rings), rings

def robust_cap(values: np.ndarray, q: float, fallback: float = 1.0) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return fallback
    cap = float(np.nanquantile(values, q))
    return cap if (np.isfinite(cap) and cap > 0) else fallback

def size_from_metric(v: np.ndarray, cap: float) -> np.ndarray:
    return DOT_S_MIN + (DOT_S_MAX - DOT_S_MIN) * np.clip(np.asarray(v, dtype=float) / (cap if cap > 0 else 1.0), 0.0, 1.0)

def polar_points_layer(data: pd.DataFrame, dist_to_ring, rings, iqr_cap, mae_cap, cmap_name, norm, **kws):
    ax = plt.gca()
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_thetagrids([0, 90, 180, 270], labels=["0", "270", "180", "90"])
    ax.tick_params(axis="x", pad=-4)
    ax.set_rticks(rings)
    ax.set_yticklabels([f"{d:g} m" for d in GT_LEVELS])
    ax.set_rlim(0.5, rings[-1] + 0.6)
    
    theta = np.deg2rad(data["angle_deg"].to_numpy(float))
    r_gt = dist_to_ring(data["gt_m"].to_numpy(float))
    s = size_from_metric(data["iqr_m"].to_numpy(float), cap=iqr_cap)
    c = mpl.cm.get_cmap(cmap_name)(norm(np.clip(data["mae_m"].to_numpy(float), 0.0, mae_cap)))
    ax.scatter(theta, r_gt, s=s, c=c, edgecolors="black", linewidths=0.45, zorder=3)

def add_iqr_size_legend(fig, iqr_cap, anchor=(0.48, 0.04), fontsize=13, title_fontsize=13):
    levels = np.array([0.0, 0.5, 1.0, 1.5], dtype=float)
    handles = [plt.scatter([], [], s=float(size_from_metric(np.array([v]), cap=iqr_cap)[0]), 
                          facecolors="none", edgecolors="black", linewidths=0.8) for v in levels]
    fig.legend(handles, [f"{v:.1f} m" for v in levels], title="Marker size: IQR",
               loc="lower center", bbox_to_anchor=anchor, ncol=len(levels), frameon=False,
               fontsize=fontsize, title_fontsize=title_fontsize, handletextpad=0.8, columnspacing=1.4)

def main():
    print("Loading CS_Dataset/Indoor ...", file=sys.stderr)
    pts = load_data()
    
    dist_to_ring, rings = make_radius_mapper(np.array(GT_LEVELS, float))
    iqr_cap = robust_cap(pts["iqr_m"].to_numpy(float), IQR_CAP_Q, fallback=0.5)
    norm = mpl.colors.Normalize(vmin=0.0, vmax=float(MAE_VMAX))
    
    g = sns.FacetGrid(pts, row="device", col="polpair", subplot_kws=dict(projection="polar"),
                      height=2.95, aspect=1.20, sharex=False, sharey=False, despine=False, margin_titles=True)
    g.map_dataframe(polar_points_layer, dist_to_ring=dist_to_ring, rings=rings, 
                    iqr_cap=iqr_cap, mae_cap=MAE_VMAX, cmap_name=CMAP_NAME, norm=norm)
    
    for ax in g.axes.flat:
        ax.tick_params(axis="x", labelsize=12)
        ax.tick_params(axis="y", labelsize=12)
        ax.title.set_fontsize(14)
        ax.title.set_fontweight("bold")
        
    g.set_titles(col_template=r"$\bf{{{col_name}}}$", row_template="")
    
    row_texts = []
    for row_idx, name in enumerate(g.row_names):
        row_axes = g.axes[row_idx, :]
        y_center = 0.5 * (min(ax.get_position().y0 for ax in row_axes) + max(ax.get_position().y1 for ax in row_axes))
        txt = g.fig.text(row_axes[0].get_position().x0 - 0.02, y_center, str(name),
                         rotation=90, va="center", ha="center", fontsize=14, fontweight="bold")
        row_texts.append(txt)
        
    # Offset labels matching the original script
    for idx, dy in [(1, 0.045), (2, 0.085)]:
        x, y = row_texts[idx].get_position()
        row_texts[idx].set_position((x, y + dy))
        
    for ax in g.axes.flat:
        ax.set_title(ax.get_title(), pad=10, y=1.05)
        
    g.fig.subplots_adjust(left=0.06, right=0.88, top=0.95, bottom=0.14, wspace=0.10, hspace=0.30)
    
    # Colorbar
    sm = mpl.cm.ScalarMappable(cmap=mpl.cm.get_cmap(CMAP_NAME), norm=norm)
    sm.set_array([])
    cbar_ax = g.fig.add_axes([0.895, 0.18, 0.010, 0.70])
    cbar = g.fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label("MAE [m]", fontsize=13)
    cbar.ax.tick_params(labelsize=12)
    cbar.set_ticks([0, 10, 20])
    
    add_iqr_size_legend(g.fig, iqr_cap=iqr_cap, anchor=(0.48, 0.04), fontsize=13, title_fontsize=13)
    
    plt.show()

if __name__ == "__main__":
    main()
