"""Spatial check with CWFIS interpolated daily FWI grids (2 km, 2018-2026).

Per cell and year: days with FWI >= 30 between Apr 1 and Oct 19. A cell-year is
used if the cell has a value on >= 90% of the Jun 1 - Aug 31 grids available
that year. Baseline = mean of 2018-2025 (needs >= 6 of 8 usable years). This is
a short 8-year baseline and is only a check on the station result.

Outputs: grid_extreme_days_2026.tif (band1 2026 days, band2 2018-2025 mean x10,
band3 anomaly days x10, band4 1 if 2026 is the highest of 2018-2026),
area_grid_check.csv, work/summary_04.json
"""
import glob
import json
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio import features
from scipy.stats import spearmanr

W = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(W, "analysis", "weather")
G = os.path.join(W, "data", "fire", "raw", "fwi_grids_daily")
files = sorted(glob.glob(os.path.join(G, "fwi_*.tif")))
with rasterio.open(files[0]) as r:
    prof = r.profile; shape = r.shape; transform = r.transform; crs = r.crs

years = list(range(2018, 2027))
ext = {}; usable = {}; S = {"grid_days": {}}
CACHE = os.path.join(OUT, "work", "grid_years.npz")
if os.path.exists(CACHE):
    z = np.load(CACHE, allow_pickle=True)
    ext = {y: z[f"e{y}"] for y in years}; usable = {y: z[f"u{y}"] for y in years}; S["grid_days"] = z["days"].item()
for y in ([] if ext else years):
    fy = [f for f in files if os.path.basename(f)[4:8] == str(y) and "0401" <= os.path.basename(f)[8:12] <= "1019"]
    e = np.zeros(shape, np.int16); vj = np.zeros(shape, np.int16); nj = 0
    for f in fy:
        md = os.path.basename(f)[8:12]
        with rasterio.open(f) as r:
            a = r.read(1)
        valid = a != 255
        e += (valid & (a >= 30)).astype(np.int16)
        if "0601" <= md <= "0831":
            vj += valid; nj += 1
    ext[y] = e; usable[y] = vj >= 0.9 * nj
    S["grid_days"][y] = {"files": len(fy), "jja_files": nj}
    print(y, len(fy), nj, flush=True)

if not os.path.exists(CACHE):
    np.savez_compressed(CACHE, days=np.array(S["grid_days"], dtype=object),
                        **{f"e{y}": ext[y] for y in years}, **{f"u{y}": usable[y] for y in years})
tot = np.zeros(shape, np.float32); nb = np.zeros(shape, np.int16); bmax = np.full(shape, -1, np.int16)
for y in years[:-1]:
    u = usable[y]
    tot += np.where(u, ext[y], 0); nb += u
    bmax = np.where(u, np.maximum(bmax, ext[y]), bmax)
with np.errstate(all="ignore"):
    base = np.where(nb > 0, tot / nb, np.nan).astype(np.float32)
del tot
ok = usable[2026] & (nb >= 6)
e26 = ext[2026].astype(np.float32)
anom = np.where(ok, e26 - base, np.nan)
is_max = ok & (e26 > bmax) & (e26 > 0)

prof.update(dtype="int16", count=4, nodata=-32768)
with rasterio.open(os.path.join(OUT, "grid_extreme_days_2026.tif"), "w", **prof) as d:
    d.write(np.where(ok, ext[2026], -32768).astype(np.int16), 1)
    d.write(np.where(ok, np.round(base * 10), -32768).astype(np.int16), 2)
    d.write(np.where(ok, np.round(anom * 10), -32768).astype(np.int16), 3)
    d.write(np.where(ok, is_max, -32768).astype(np.int16), 4)

fma = gpd.read_file(os.path.join(W, "analysis", "weather", "work", "fma_simple.gpkg"))  # built by 00_simplify_fma.py
fma = fma[~fma["agency"].str.contains("Parks Canada")].to_crs(crs)
lab = features.rasterize(((g, int(i)) for g, i in zip(fma.geometry, fma["fma_id"])), out_shape=shape,
                         transform=transform, fill=0, dtype="int32")
prov_of = dict(zip(fma["fma_id"], fma["province"]))
for y in years[:-1]:
    del ext[y]
m = ok & (lab > 0)
df = pd.DataFrame({"fma_id": lab[m], "e26": e26[m], "base": base[m], "is_max": is_max[m]})
df["province"] = df["fma_id"].map(prov_of)


def agg(g):
    return pd.Series({"n_cells": len(g), "grid_mean_extreme_2026": g["e26"].mean(), "grid_mean_extreme_2018_2025": g["base"].mean(),
                      "grid_ratio_of_means": g["e26"].mean() / g["base"].mean() if g["base"].mean() > 0 else np.nan,
                      "grid_mean_anom_days": (g["e26"] - g["base"]).mean(),
                      "grid_share_cells_2026_highest_2018_2026": g["is_max"].mean()})


rows = [agg(df).to_frame().T.assign(level="national", area_id="CA", province="CA")]
rows.append(df.groupby("province").apply(agg, include_groups=False).reset_index().assign(level="province", area_id=lambda x: x["province"]))
f2 = df.groupby("fma_id").apply(agg, include_groups=False).reset_index().rename(columns={"fma_id": "area_id"}).assign(level="fma")
f2["province"] = f2["area_id"].map(prov_of)
f2["area_name"] = f2["area_id"].map(dict(zip(fma["fma_id"], fma["area_name"])))
rows.append(f2)
ga = pd.concat(rows, ignore_index=True)
ga["area_name"] = ga["area_name"].fillna(ga["area_id"].astype(str))
ga = ga[["level", "area_id", "area_name", "province", "n_cells", "grid_mean_extreme_2026", "grid_mean_extreme_2018_2025",
         "grid_ratio_of_means", "grid_mean_anom_days", "grid_share_cells_2026_highest_2018_2026"]]
ga.round(3).to_csv(os.path.join(OUT, "area_grid_check.csv"), index=False)
S["national"] = ga[ga["level"] == "national"].iloc[0].to_dict()
S["province"] = ga[ga["level"] == "province"].set_index("area_id")[["grid_mean_extreme_2026", "grid_mean_extreme_2018_2025", "grid_ratio_of_means", "grid_share_cells_2026_highest_2018_2026"]].round(3).to_dict("index")
S["cells_used"] = int(ok.sum())

# station cross-check: sample the grid at stations and compare with the area table
st = pd.read_csv(os.path.join(OUT, "station_extreme_days.csv"))
st = st[(st["rule"] == "strict_28of30") & st["qual_2026"]]
pts = gpd.GeoSeries(gpd.points_from_xy(st["lon"], st["lat"]), crs="EPSG:4326").to_crs(crs)
rr, cc = rasterio.transform.rowcol(transform, pts.x.values, pts.y.values)
rr = np.clip(rr, 0, shape[0] - 1); cc = np.clip(cc, 0, shape[1] - 1)
gs = e26[rr, cc]; okp = ok[rr, cc]
S["station_vs_grid_2026_extreme_days_spearman"] = float(spearmanr(st["extreme_2026"].values[okp], gs[okp]).statistic)
S["station_vs_grid_n"] = int(okp.sum())
S["station_vs_grid_median_station_minus_grid"] = float(np.median(st["extreme_2026"].values[okp] - gs[okp]))
aw = pd.read_csv(os.path.join(OUT, "area_weather_2026.csv"))
aw = aw[(aw["rule"] == "strict_28of30") & (aw["level"] == "fma") & (aw["n_stations"] > 0)]
aw["area_id"] = aw["area_id"].astype(int)
f3 = f2.merge(aw[["area_id", "median_ratio_extreme_9120", "median_anom_days_extreme_9120"]], on="area_id")
S["fma_station_anom_vs_grid_anom_spearman"] = float(spearmanr(f3["median_anom_days_extreme_9120"], f3["grid_mean_anom_days"], nan_policy="omit").statistic)
S["fma_station_vs_grid_n"] = int(len(f3))
with open(os.path.join(OUT, "work", "summary_04.json"), "w") as f:
    json.dump(S, f, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
print(json.dumps(S, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)))
