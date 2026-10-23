"""Step 4: ESTIMATED burn scar of the 2026-10-17 CFB Wainwright fire from Sentinel-2 dNBR.
pre = 2026-10-04 (S2C, 2.5% cloud), post = 2026-10-19 (S2B, 40% tile cloud; scar area mostly
clear, thin cloud east of the base boundary). NBR = (B8A - B12)/(B8A + B12), 20 m.
Masked: SCL 0,1,3,8,9,10,11 in either date, water (SCL 6) in either date.
Burn = 8-connected component(s) of dNBR >= T that contain or touch (within 300 m) the 2026-10-17
or 2026-10-18 VIIRS detections or the Alberta Wildfire RMD-001-2026 point, after a 1-pixel
morphological opening (removes single-pixel noise). T = 0.10, 0.20, 0.27 (main), 0.44.
Also reported: the 2026-10-14 scene (pre-fire, partly cloudy) dNBR vs 10-04 inside the mapped
burn, to check for burning before 10-14 18:39 UTC.
Outputs: work/burn_T*.gpkg, burn_estimate.csv, burn_map.png
"""
import numpy as np, geopandas as gpd, pandas as pd, rasterio.features as rf, matplotlib
from scipy import ndimage as ndi
from affine import Affine
from shapely.geometry import shape, Point
matplotlib.use("Agg"); import matplotlib.pyplot as plt
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
B = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
def load(s):
    d = np.load(f"{O}/work/s2/{s}.npz"); return {k: d[k] for k in d.files}
BAD = [0, 1, 3, 8, 9, 10, 11]
def nbr(d):
    a = d["B8A"].astype(float); b = d["B12"].astype(float)
    with np.errstate(all="ignore"): n = (a - b) / (a + b)
    n[np.isin(d["SCL"], BAD + [6]) | (a + b == 0)] = np.nan; return n
pre = load("S2C_12UWD_20261004_0_L2A"); post = load("S2B_12UWD_20261019_0_L2A"); mid = load("S2C_12UWD_20261014_0_L2A")
xa, yb, px = pre["transform"]; tr = Affine(px, 0, xa, 0, -px, yb)
dn = nbr(pre) - nbr(post); dmid = nbr(pre) - nbr(mid)
dnd = gpd.read_file(f"{B}/data/geo/dnd/ab_dnd_layer13.geojson"); dnd = dnd[dnd.MB_NAME.str.contains("Wainwright")].to_crs(32612)
base = dnd.union_all()
hs = pd.read_csv(f"{O}/raw/wfs_hotspots_wainwright_20261010_on.csv")
hs = hs[hs.rep_day.isin(["2026-10-17", "2026-10-18"])]
seeds = gpd.GeoSeries(list(gpd.points_from_xy(hs.lon, hs.lat)) + [Point(-110.934717, 52.772633)], crs=4326).to_crs(32612)
seedmask = rf.rasterize([(g.buffer(300), 1) for g in seeds], out_shape=dn.shape, transform=tr) == 1
basemask = rf.rasterize([(base, 1)], out_shape=dn.shape, transform=tr) == 1
rows = []; polys = {}
valid = ~np.isnan(dn)
for T in [0.10, 0.20, 0.27, 0.44]:
    m = np.nan_to_num(dn, nan=-9) >= T
    m = ndi.binary_opening(m, structure=np.ones((2, 2)))
    lab, n = ndi.label(m, structure=np.ones((3, 3)))
    ids = np.unique(lab[seedmask & m]); ids = ids[ids > 0]
    burn = np.isin(lab, ids)
    burn = ndi.binary_fill_holes(burn) & ~np.isnan(dn) | burn  # fill interior holes (lake islands kept out by nan)
    shp = [shape(g) for g, v in rf.shapes(burn.astype("uint8"), mask=burn, transform=tr) if v == 1]
    g = gpd.GeoDataFrame(geometry=[gpd.GeoSeries(shp).union_all()], crs=32612)
    g.to_file(f"{O}/work/burn_T{int(T*100):02d}.gpkg"); polys[T] = g
    a_tot = burn.sum() * px * px / 1e4; a_in = (burn & basemask).sum() * px * px / 1e4
    outside = g.geometry.iloc[0].difference(base)
    maxd = max((Point(c).distance(base) for geom in getattr(outside, "geoms", [outside]) if not geom.is_empty
                for c in geom.exterior.coords), default=0.0)
    # cloud check in a 500 m ring around the burn in the post scene
    ring = ndi.binary_dilation(burn, iterations=25) & ~burn
    cl = np.isin(post["SCL"], BAD)[ring].mean()
    mid_ok = ~np.isnan(dmid) & burn
    rows.append(dict(threshold=T, components=len(ids), area_ha=round(a_tot, 1), inside_base_ha=round(a_in, 1),
                     outside_base_ha=round(a_tot - a_in, 1), max_dist_beyond_base_m=round(maxd),
                     post_masked_share_500m_ring=round(cl, 3),
                     share_burn_clear_on_1014=round(mid_ok.sum() / burn.sum(), 3),
                     share_of_clear_1014_already_dNBR_ge_T=round((dmid[mid_ok] >= T).mean(), 3) if mid_ok.any() else None,
                     median_dNBR=round(float(np.nanmedian(dn[burn])), 3)))
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(f"{O}/burn_estimate.csv", index=False)
# map
X0, X1, Y0, Y1 = 501000, 512000, 5840000, 5852000
fig, ax = plt.subplots(figsize=(9, 10))
c0 = int((X0 - xa) / px); c1 = int((X1 - xa) / px); r0 = int((yb - Y1) / px); r1 = int((yb - Y0) / px)
rgb = np.dstack([post["B04"], post["B03"], post["B02"]])[r0:r1, c0:c1].astype(float) / 2000
ax.imshow(np.clip(rgb, 0, 1), extent=[xa + c0 * px, xa + c1 * px, yb - r1 * px, yb - r0 * px])
dnd.boundary.plot(ax=ax, color="cyan", lw=1.2)
for T, c in [(0.10, "yellow"), (0.27, "red"), (0.44, "magenta")]:
    polys[T].boundary.plot(ax=ax, color=c, lw=1)
hs2 = gpd.GeoDataFrame(hs, geometry=gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(32612)
ax.scatter(hs2.geometry.x, hs2.geometry.y, s=18, c="white", edgecolor="k")
ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.set_title("Estimated burn (dNBR 10-04 vs 10-19): yellow 0.10, red 0.27, magenta 0.44; cyan AB DND polygon")
fig.savefig(f"{O}/burn_map.png", dpi=100)
