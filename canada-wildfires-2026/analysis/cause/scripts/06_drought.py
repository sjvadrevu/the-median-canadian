"""Canadian Drought Monitor (AAFC) monthly areas of drought -> share of each area in D0+, D1+, D2+, D3+,
April to September 2003-2026 (2002 has no April-September maps; August 2003 is not published).

Method: each monthly zip holds one shapefile per class (D0..D4). Classes are burned onto a 1.2 km grid
(every 5th cell of the 240 m analysis grid, EPSG:3979, cell centre rule) in increasing order, so a cell keeps
the worst class that covers it (works whether the layers are nested or exclusive). The area id of a 1.2 km cell
is the area id of its central 240 m cell. Shares use true cell area (Lambert areal scale correction) and are
also given as forest-weighted shares (Land Cover 2020 forest in the central 240 m cell).
The CDM is a map at end of month. The CDM does not assess Nunavut and the Arctic Archipelago.
Outputs: drought_by_area_month.csv, drought_by_area_year.csv, drought_coverage_check.csv
"""
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio import features

from common import FOREST_WORK, OUT, area_attrs, area_dir, area_grid, grid_meta, log

D = area_dir()
fh = open(D / "log_06.txt", "w")
RAW = OUT / "raw" / "cdm"
dl = pd.read_csv(RAW / "download_log.csv", dtype={"month": str})
dl = dl[dl.status == "ok"]
m = grid_meta()
K = 5
T = m["T"]
from affine import Affine
TC = Affine(T.a * K, 0, T.c, 0, T.e * K, T.f)
H, W = m["H"] // K, m["W"] // K
g = area_grid()
aid = np.asarray(g[K // 2::K, K // 2::K][:H, :W]).astype("int64")
fc = np.load(FOREST_WORK / "forest_count.npy", mmap_mode="r")
fw = np.asarray(fc[K // 2::K, K // 2::K][:H, :W]).astype("float64") / 64.0     # forest fraction of central cell
asc = np.load(FOREST_WORK / "areal_scale_coarse.npy").astype("float64")
rr = np.minimum((np.arange(H) * K + K // 2) // m["step"], asc.shape[0] - 1)
cc = np.minimum((np.arange(W) * K + K // 2) // m["step"], asc.shape[1] - 1)
carea = (240.0 * K) ** 2 / asc[rr][:, cc] / 1e4                                  # ha
nmax = int(aid.max()) + 1
flat = aid.ravel()
tot_a = np.bincount(flat, weights=carea.ravel(), minlength=nmax)
tot_f = np.bincount(flat, weights=(carea * fw).ravel(), minlength=nmax)

rows = []
for _, r in dl.iterrows():
    z = RAW / r.file
    names = [n for n in zipfile.ZipFile(z).namelist() if n.lower().endswith(".shp")]
    lvl = np.zeros((H, W), dtype="uint8")
    for cls in range(5):
        nm = [n for n in names if n.upper().endswith(f"_D{cls}_LR.SHP")]
        if not nm:
            continue
        gd = gpd.read_file(f"/vsizip/{z}/{nm[0]}")
        if gd.empty:
            continue
        gd = gd.to_crs("EPSG:3979")
        geoms = [x for x in gd.geometry.make_valid() if x is not None and not x.is_empty]
        if geoms:
            features.rasterize(((x, cls + 1) for x in geoms), out=lvl, transform=TC, merge_alg=features.MergeAlg.replace)
    for k, thr in [("d0", 1), ("d1", 2), ("d2", 3), ("d3", 4)]:
        msk = (lvl >= thr).ravel()
        a = np.bincount(flat[msk], weights=carea.ravel()[msk], minlength=nmax)
        f = np.bincount(flat[msk], weights=(carea * fw).ravel()[msk], minlength=nmax)
        for i in range(1, nmax):
            pass
        rows.append(pd.DataFrame(dict(fma_id=np.arange(nmax), year=int(r.year), month=int(r.month), level=k,
                                      share_area=a / np.where(tot_a > 0, tot_a, np.nan),
                                      share_forest=f / np.where(tot_f > 0, tot_f, np.nan))))
    log(f"{r.year}-{r.month}: D1+ share of Canada grid {((lvl >= 2) & (aid > 0)).sum() / (aid > 0).sum():.3f}", fh)
M = pd.concat(rows, ignore_index=True)
A = area_attrs()
M = M[M.fma_id.isin(A.fma_id)]
M = M.pivot_table(index=["fma_id", "year", "month"], columns="level", values=["share_area", "share_forest"]).reset_index()
M.columns = ["fma_id", "year", "month"] + [f"{lv}_{v.replace('share_', '')}" for v, lv in M.columns[3:]]
M.to_csv(OUT / "drought_by_area_month.csv", index=False)

# per area-year: monthly columns for D1+/D2+ area share, season max/mean, early-season mean (Apr-Jun)
Y = []
for (a, y), h in M.groupby(["fma_id", "year"]):
    r = dict(fma_id=a, year=y, n_months=len(h))
    for lv in ["d1", "d2"]:
        for _, q in h.iterrows():
            r[f"{lv}_area_m{int(q.month):02d}"] = q[f"{lv}_area"]
        r[f"{lv}_area_max_apr_sep"] = h[f"{lv}_area"].max()
        r[f"{lv}_area_mean_apr_sep"] = h[f"{lv}_area"].mean()
        r[f"{lv}_area_mean_apr_jun"] = h.loc[h.month <= 6, f"{lv}_area"].mean()
        r[f"{lv}_forest_mean_apr_jun"] = h.loc[h.month <= 6, f"{lv}_forest"].mean()
        r[f"{lv}_forest_max_apr_sep"] = h[f"{lv}_forest"].max()
    r["d0_area_max_apr_sep"] = h["d0_area"].max()
    r["d3_area_max_apr_sep"] = h["d3_area"].max()
    Y.append(r)
Y = pd.DataFrame(Y).merge(A[["fma_id", "province", "area_name"]], on="fma_id")
Y.to_csv(OUT / "drought_by_area_year.csv", index=False)

# coverage check: does any part of each province ever show D0+ by year (early years assessed less of the north?)
cv = Y.groupby(["province", "year"]).d0_area_max_apr_sep.max().unstack("year")
cv.to_csv(OUT / "drought_coverage_check.csv")
log("max D0+ area share in any area of province, by year:\n" + cv.round(2).to_string(), fh)
