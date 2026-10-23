"""Step 3: zoomed views (pre 10-04, mid 10-14, post 10-19 true colour; dNBR 10-04 minus 10-19)
over the burn scar. Exploratory figure for visual checking of the mapped burn."""
import numpy as np, geopandas as gpd, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
B = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
def load(s):
    d = np.load(f"{O}/work/s2/{s}.npz"); return {k: d[k] for k in d.files}
def nbr(d):
    a = d["B8A"].astype(float); b = d["B12"].astype(float)
    with np.errstate(all="ignore"): n = (a - b) / (a + b)
    n[np.isin(d["SCL"], [0, 1, 3, 8, 9, 10, 11]) | (a + b == 0)] = np.nan; return n
S = {"pre": "S2C_12UWD_20261004_0_L2A", "mid": "S2C_12UWD_20261014_0_L2A", "post": "S2B_12UWD_20261019_0_L2A"}
D = {k: load(v) for k, v in S.items()}
xa, yb, px = D["pre"]["transform"]; h, w = D["pre"]["SCL"].shape
X0, X1, Y0, Y1 = 499000, 514000, 5837000, 5853000
c0 = int((X0 - xa) / px) if X0 > xa else 0; c1 = int((X1 - xa) / px); r0 = int((yb - Y1) / px); r1 = int((yb - Y0) / px)
ext = [xa + c0 * px, xa + c1 * px, yb - r1 * px, yb - r0 * px]
dnd = gpd.read_file(f"{B}/data/geo/dnd/ab_dnd_layer13.geojson"); dnd = dnd[dnd.MB_NAME.str.contains("Wainwright")].to_crs(32612)
hs = pd.read_csv(f"{O}/raw/wfs_hotspots_wainwright_20261010_on.csv")
hs = gpd.GeoDataFrame(hs, geometry=gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(32612)
fig, axs = plt.subplots(2, 2, figsize=(14, 15))
for ax, k in zip(axs.flat[:3], ["pre", "mid", "post"]):
    d = D[k]; rgb = np.dstack([d["B04"], d["B03"], d["B02"]])[r0:r1, c0:c1].astype(float) / 2000
    ax.imshow(np.clip(rgb, 0, 1), extent=ext); ax.set_title(S[k])
dn = (nbr(D["pre"]) - nbr(D["post"]))[r0:r1, c0:c1]
im = axs[1, 1].imshow(dn, extent=ext, vmin=-0.2, vmax=0.5, cmap="RdYlGn_r"); axs[1, 1].set_title("dNBR 10-04 minus 10-19")
for ax in axs.flat:
    dnd.boundary.plot(ax=ax, color="cyan", lw=1)
    for day, c in [("2026-10-14", "yellow"), ("2026-10-17", "red"), ("2026-10-18", "magenta")]:
        s = hs[hs.rep_day == day]; ax.scatter(s.geometry.x, s.geometry.y, s=14, c=c, edgecolor="k", lw=0.3)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
fig.tight_layout(); fig.savefig(f"{O}/work/ql_zoom.png", dpi=90)
