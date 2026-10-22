"""Area layer and burn outcome per area and year (1991-2026).

1. Areas: non-park rows of AREA_FILE, read 5 features at a time (default file: reuse analysis/weather 500 m copy), simplified at 1 km (ESRI:102001) for
   station lookups -> work/areas_<hash>/areas_1km.gpkg, areas.csv.
2. Outcome: the 240 m burn rasters made by analysis/forest (work/burn_YYYY.npy: NBAC 1972-2025,
   CWFIS M3 outlines 2026) are summed by area: burned_ha (all land, true area) and forest_burned_ha
   (Land Cover 2020 forest classes 1,2,5,6), forest_share = forest_burned_ha / forest_ha.
   For the default area file the area-id grid of analysis/forest (work/fma_id.npy) is reused; for any
   other AREA_FILE it is rasterised here with the same rule (cell centre inside polygon, 20 m simplified
   parts). These are mapped hectares, not the official agency totals.
Output: work/areas_<hash>/outcome.csv
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from affine import Affine

from common import AREA_FILE, DEFAULT_AREA_FILE, FOREST_WORK, YEARS, area_dir, log

D = area_dir()
fh = open(D / "log_05.txt", "w")
log(f"area file {AREA_FILE} -> {D}", fh)

# ---------------- 1. simplified areas
# default file: reuse the 500 m non-park copy made by analysis/weather (00_simplify_fma.py)
REUSE = FOREST_WORK.parent.parent / "weather" / "work" / "fma_simple.gpkg"
if not (D / "areas_1km.gpkg").exists() and AREA_FILE == DEFAULT_AREA_FILE.resolve() and REUSE.exists():
    g = gpd.read_file(REUSE).to_crs("ESRI:102001")
    g["geometry"] = shapely.make_valid(shapely.simplify(g.geometry.values, 1000, preserve_topology=True))
    g.to_file(D / "areas_1km.gpkg", driver="GPKG")
    log("reused analysis/weather/work/fma_simple.gpkg", fh)
WSIMP = REUSE                                            # analysis/weather/work/fma_simple.gpkg (500 m)
if not (D / "areas_1km.gpkg").exists() and AREA_FILE != DEFAULT_AREA_FILE.resolve() and WSIMP.exists():
    # rebuild 2026-10-21: analysis/weather now builds its 500 m copy from data/geo/fma_v2.gpkg; reuse it when it
    # holds exactly the ids of this area file (same path as the default file takes), since simplifying the
    # full-detail rows (some with ~100,000 parts) takes hours
    g = gpd.read_file(WSIMP).to_crs("ESRI:102001")
    ids = set(pyogrio.read_dataframe(AREA_FILE, columns=["fma_id"], read_geometry=False).fma_id)
    if set(g.fma_id) == ids:
        g["geometry"] = shapely.make_valid(shapely.simplify(g.geometry.values, 1000, preserve_topology=True))
        g.to_file(D / "areas_1km.gpkg", driver="GPKG")
        log("reused analysis/weather/work/fma_simple.gpkg (same ids as AREA_FILE)", fh)
if not (D / "areas_1km.gpkg").exists():
    n = pyogrio.read_info(AREA_FILE)["features"]
    rows, rows20 = [], []
    for start in range(0, n, 5):                       # small batches keep memory low
        g = pyogrio.read_dataframe(AREA_FILE, skip_features=start, max_features=5)
        g = g[~g.agency.astype(str).str.contains("Parks Canada")]
        if not len(g):
            continue
        g = g.to_crs("ESRI:102001")
        g1 = g.copy()
        g1["geometry"] = shapely.make_valid(shapely.simplify(g.geometry.values, 1000, preserve_topology=True))
        rows.append(g1)
        if AREA_FILE != DEFAULT_AREA_FILE.resolve():
            g2 = g.copy()
            g2["geometry"] = shapely.make_valid(shapely.simplify(g.geometry.values, 20, preserve_topology=True))
            rows20.append(g2)
        log(f"areas read {start + 5}", fh)
    A = gpd.GeoDataFrame(pd.concat(rows, ignore_index=True), crs="ESRI:102001")
    A.to_file(D / "areas_1km.gpkg", driver="GPKG")
    if rows20:
        gpd.GeoDataFrame(pd.concat(rows20, ignore_index=True), crs="ESRI:102001").to_file(D / "areas_20m.gpkg", driver="GPKG")
A = gpd.read_file(D / "areas_1km.gpkg")
A.drop(columns="geometry").to_csv(D / "areas.csv", index=False)
log(f"{len(A)} non-park areas", fh)

# ---------------- 2. outcome
m = json.load(open(FOREST_WORK / "grid_meta.json"))
H, W, step = m["H"], m["W"], m["step"]
if AREA_FILE == DEFAULT_AREA_FILE.resolve():
    grid = np.load(FOREST_WORK / "fma_id.npy", mmap_mode="r")
elif (FOREST_WORK / f"{AREA_FILE.stem}_id.npy").exists():
    # analysis/forest grid for this area file (e.g. fma_v2_id.npy, rebuild 2026-10-21): same cell-centre rule on
    # the 20 m part-by-part simplified layer, saves building a second 950 MB copy
    grid = np.load(FOREST_WORK / f"{AREA_FILE.stem}_id.npy", mmap_mode="r")
    log(f"reusing analysis/forest/work/{AREA_FILE.stem}_id.npy", fh)
else:
    from rasterio import features
    gp = D / "area_grid.npy"
    if not gp.exists():
        A20 = gpd.read_file(D / "areas_20m.gpkg").to_crs("EPSG:3979")
        g = np.zeros((H, W), dtype="uint16")
        for i, geom in zip(A20.fma_id, A20.geometry):
            features.rasterize([(geom, int(i))], out=g, transform=Affine(*m["transform"]))
        np.save(gp, g)
        del g
    grid = np.load(gp, mmap_mode="r")
asc = np.load(FOREST_WORK / "areal_scale_coarse.npy").astype("float64")
fc = np.load(FOREST_WORK / "forest_count.npy", mmap_mode="r")
nmax = int(A.fma_id.max()) + 1
flat_grid = grid.reshape(-1)
flat_fc = fc.reshape(-1)


def cell_area(idx):
    r = np.minimum((idx // W) // step, asc.shape[0] - 1)
    c = np.minimum((idx % W) // step, asc.shape[1] - 1)
    return 57600.0 / asc[r, c]


# forest per area (row blocks)
tf = np.zeros(nmax)
colc = np.minimum(np.arange(W) // step, asc.shape[1] - 1)
for r0 in range(0, H, 250):
    r1 = min(r0 + 250, H)
    sc = asc[np.minimum(np.arange(r0, r1) // step, asc.shape[0] - 1)][:, colc]
    a = np.asarray(grid[r0:r1]).ravel().astype("int64")
    tf += np.bincount(a, weights=(np.asarray(fc[r0:r1], "float64") * 900.0 / sc).ravel() / 1e4, minlength=nmax)[:nmax]
rows = []
for y in YEARS:
    idx = np.load(FOREST_WORK / f"burn_{y}.npy").astype("int64")
    ids = np.asarray(flat_grid[idx]).astype("int64")
    ca = cell_area(idx)
    fa = np.asarray(flat_fc[idx], "float64") * 900.0 * ca / 57600.0
    b = np.bincount(ids, weights=ca, minlength=nmax)[:nmax] / 1e4
    bf = np.bincount(ids, weights=fa, minlength=nmax)[:nmax] / 1e4
    for i in A.fma_id:
        rows.append((int(i), y, b[i], bf[i]))
    log(f"{y} burned {b[1:].sum():,.0f} ha forest {bf[1:].sum():,.0f} ha", fh)
O = pd.DataFrame(rows, columns=["area_id", "year", "burned_ha", "forest_burned_ha"])
O["forest_ha"] = O.area_id.map(lambda i: tf[i])
O["forest_share_burned"] = O.forest_burned_ha / O.forest_ha.replace(0, np.nan)
O["burn_source"] = np.where(O.year == 2026, "CWFIS M3 2026 outlines (mapped)", "NBAC (mapped)")
O.to_csv(D / "outcome.csv", index=False)
