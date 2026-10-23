"""Add the burn-context feature dnbr_r100_250_share100 to an event feature file written before s2lib gained it, from
that event's saved work/dnbr_<event>.tif (band 1 = offset-corrected dNBR on the same 10 m UTM grid). Same definition
as s2lib.building_features: share of finite pixels whose centres are 100-250 m from the footprint centroid with
dNBR >= 100, NaN if fewer than 50 such pixels. Centroids are rebuilt from the footprint WKT in the footprint file.
usage: 05b_add_context.py <event> <footprints.csv.gz>   (updates work/features_<event>.csv in place)"""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd, rasterio
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ev, fpf = sys.argv[1:3]
ff = os.path.join(P, "work", f"features_{ev}.csv")
d = pd.read_csv(ff)
fp = pd.read_csv(fpf)
assert len(fp) == (d["set"] == "microsoft").sum() and np.allclose(fp.x.values, d.loc[d["set"] == "microsoft", "x"].values)
with rasterio.open(os.path.join(P, "work", f"dnbr_{ev}.tif")) as src:
    a = src.read(1).astype("float32"); a[a == src.nodata] = np.nan
    tr, crs = src.transform, src.crs
x0, y1, RES = tr.c, tr.f, tr.a; H_, W_ = a.shape
cen = gpd.GeoSeries.from_wkt(fp.footprint_wkt, crs=4326).to_crs(3978).to_crs(crs).centroid
out = []
for cx, cy in zip(cen.x.values, cen.y.values):
    c0, r0 = int((cx - x0) // RES), int((y1 - cy) // RES); R = 26
    rs, re_, cs, ce = max(r0 - R, 0), min(r0 + R + 1, H_), max(c0 - R, 0), min(c0 + R + 1, W_)
    if re_ <= rs or ce <= cs: out.append(np.nan); continue
    yy, xx = np.mgrid[rs:re_, cs:ce]; dd = np.hypot(x0 + (xx + 0.5) * RES - cx, y1 - (yy + 0.5) * RES - cy)
    sub = a[rs:re_, cs:ce]; an = sub[(dd >= 100) & (dd <= 250) & np.isfinite(sub)]
    out.append(float((an >= 100).mean()) if an.size >= 50 else np.nan)
d.loc[d["set"] == "microsoft", "dnbr_r100_250_share100"] = out
d.to_csv(ff, index=False)
print(ev, "context added", np.isfinite(out).sum(), "of", len(out), "median", np.nanmedian(out))
