"""Step 2: quicklook PNGs (true colour per scene, dNBR pre 10-04 minus post 10-21) with the
Alberta DND polygon outline and the Oct 14/17/18 VIIRS hotspots, for visual checking."""
import numpy as np, geopandas as gpd, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
B = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
def load(s):
    d = np.load(f"{O}/work/s2/{s}.npz"); return {k: d[k] for k in d.files}
def nbr(d):
    a = d["B8A"].astype(float); b = d["B12"].astype(float)
    n = (a - b) / (a + b); bad = np.isin(d["SCL"], [0, 1, 3, 8, 9, 10, 11]) | (a + b == 0)
    n[bad] = np.nan; return n
pre = load("S2C_12UWD_20261004_0_L2A"); post = load("S2C_12UWD_20261021_0_L2A")
xa, yb, px = pre["transform"]; h, w = pre["SCL"].shape
ext = [xa, xa + w * px, yb - h * px, yb]
dnd = gpd.read_file(f"{B}/data/geo/dnd/ab_dnd_layer13.geojson")
dnd = dnd[dnd.MB_NAME.str.contains("Wainwright")].to_crs(32612)
hs = pd.read_csv(f"{O}/raw/wfs_hotspots_wainwright_20261010_on.csv")
hs = gpd.GeoDataFrame(hs, geometry=gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(32612)
def deco(ax):
    dnd.boundary.plot(ax=ax, color="cyan", lw=0.8)
    for day, c in [("2026-10-14", "yellow"), ("2026-10-17", "red"), ("2026-10-18", "magenta")]:
        s = hs[hs.rep_day == day]; ax.scatter(s.geometry.x, s.geometry.y, s=12, c=c, label=day)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
for s in ["S2C_12UWD_20261004_0_L2A", "S2C_12UWD_20261014_0_L2A", "S2B_12UWD_20261019_0_L2A", "S2C_12UWD_20261021_0_L2A"]:
    d = load(s); rgb = np.dstack([d["B04"], d["B03"], d["B02"]]).astype(float) / 2500
    fig, ax = plt.subplots(figsize=(10, 11)); ax.imshow(np.clip(rgb, 0, 1), extent=ext); deco(ax)
    ax.legend(); ax.set_title(s); fig.savefig(f"{O}/work/ql_{s[11:19]}.png", dpi=110); plt.close(fig)
dn = nbr(pre) - nbr(post)
fig, ax = plt.subplots(figsize=(10, 11)); im = ax.imshow(dn, extent=ext, vmin=-0.3, vmax=0.6, cmap="RdYlGn_r")
deco(ax); plt.colorbar(im, shrink=0.6); ax.set_title("dNBR 2026-10-04 minus 2026-10-21")
fig.savefig(f"{O}/work/ql_dnbr_1004_1021.png", dpi=110); plt.close(fig)
