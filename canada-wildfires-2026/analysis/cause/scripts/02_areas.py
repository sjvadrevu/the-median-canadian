"""Prepare the area layer used by every later step.

For the default area file (data/geo/fma_all.gpkg) the 20 m simplified copy and the 240 m area-id grid made
by analysis/forest (02b_fma_simplified.py, 02_grid.py) are reused. For any other AREA_FILE they are rebuilt
here with the same rules (part-by-part 20 m Douglas-Peucker; a cell belongs to the polygon containing its
centre) and stored as uint16 so more than 255 areas fit.

Outputs (work/areas_<hash>/): areas.csv, areas_simplified_1km.gpkg, grid_path.json, [area_grid.npy],
area_forest.csv (forest ha and land ha per area, equal-area).
"""
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from rasterio import features

from common import (AREA_FILE, DEFAULT_AREA_FILE, FOREST_WORK, area_dir, grid_meta, log)

D = area_dir()
fh = open(D / "log_02.txt", "w")
log(f"area file {AREA_FILE} -> {D}", fh)

default = AREA_FILE == DEFAULT_AREA_FILE.resolve()
if default and (FOREST_WORK / "fma_simplified.gpkg").exists() and (FOREST_WORK / "fma_id.npy").exists():
    simp = gpd.read_file(FOREST_WORK / "fma_simplified.gpkg")
    json.dump({"path": str(FOREST_WORK / "fma_id.npy"), "source": "analysis/forest/work"}, open(D / "grid_path.json", "w"))
    log("reusing analysis/forest simplified areas and grid", fh)
elif (FOREST_WORK / f"{AREA_FILE.stem}_simplified.gpkg").exists() and (FOREST_WORK / f"{AREA_FILE.stem}_id.npy").exists():
    # analysis/forest built the same products for this area file (e.g. fma_v2, rebuild 2026-10-21) with the same
    # rules (part-by-part 20 m simplification, cell-centre rasterisation, uint16): reuse instead of a second copy
    simp = gpd.read_file(FOREST_WORK / f"{AREA_FILE.stem}_simplified.gpkg")
    json.dump({"path": str(FOREST_WORK / f"{AREA_FILE.stem}_id.npy"), "source": "analysis/forest/work"},
              open(D / "grid_path.json", "w"))
    log(f"reusing analysis/forest {AREA_FILE.stem} simplified areas and grid", fh)
else:
    ids = pyogrio.read_dataframe(AREA_FILE, columns=["fma_id"], read_geometry=False)
    rows = []
    for i in ids.fma_id:
        g = pyogrio.read_dataframe(AREA_FILE, where=f"fma_id = {int(i)}").to_crs("ESRI:102001")
        parts = shapely.get_parts(g.geometry.iloc[0])
        parts = np.concatenate([shapely.get_parts(p) for p in parts])
        parts = parts[shapely.get_type_id(parts) == 3]
        s = shapely.simplify(parts, 20, preserve_topology=True)
        s = s[~shapely.is_empty(s) & (shapely.area(s) > 0)]
        s = shapely.make_valid(s)
        s = np.concatenate([shapely.get_parts(x) for x in s])
        s = s[shapely.get_type_id(s) == 3]
        g["geometry"] = [shapely.multipolygons(s)]
        rows.append(g)
    simp = gpd.GeoDataFrame(pd.concat(rows, ignore_index=True), crs="ESRI:102001")
    simp.to_file(D / "areas_simplified_20m.gpkg", driver="GPKG")
    m = grid_meta()
    np_ = simp[simp.agency != "Parks Canada"].to_crs("EPSG:3979")
    grid = np.zeros((m["H"], m["W"]), dtype="uint16")
    for i, geom in zip(np_.fma_id, np_.geometry):
        features.rasterize([(geom, int(i))], out=grid, transform=m["T"])
    np.save(D / "area_grid.npy", grid)
    del grid
    json.dump({"path": str(D / "area_grid.npy"), "source": "rebuilt"}, open(D / "grid_path.json", "w"))
    log("rebuilt simplified areas and grid", fh)

nonpark = simp[simp.agency != "Parks Canada"].copy()
attrs = nonpark.drop(columns=[c for c in ["geometry", "simplify_area_change"] if c in nonpark]).copy()
attrs.to_csv(D / "areas.csv", index=False)
# light copy for snapping points: drop polygon parts under 1 km2, simplify each part to 1 km
light = nonpark[["fma_id", "province", "area_name", "geometry"]].explode(index_parts=False)
light = light[light.area > 1e6].copy()
light["geometry"] = shapely.make_valid(shapely.simplify(light.geometry.values, 1000, preserve_topology=True))
light = light[~light.geometry.is_empty].dissolve(by=["fma_id", "province", "area_name"]).reset_index()
light.to_file(D / "areas_simplified_1km.gpkg", driver="GPKG")
log(f"{len(attrs)} non-park areas", fh)

# forest and land area per area, row blocks
from common import area_grid
m = grid_meta()
g = area_grid()
fc = np.load(FOREST_WORK / "forest_count.npy", mmap_mode="r")
asc = np.load(FOREST_WORK / "areal_scale_coarse.npy").astype("float64")
nmax = int(attrs.fma_id.max()) + 1
tf = np.zeros(nmax)
tl = np.zeros(nmax)
colc = np.minimum(np.arange(m["W"]) // m["step"], asc.shape[1] - 1)
for r0 in range(0, m["H"], 1000):
    r1 = min(r0 + 1000, m["H"])
    sc = asc[np.minimum(np.arange(r0, r1) // m["step"], asc.shape[0] - 1)][:, colc]
    a = np.asarray(g[r0:r1]).ravel().astype("int64")
    tf += np.bincount(a, weights=(np.asarray(fc[r0:r1], "float64") * 900.0 / sc).ravel() / 1e4, minlength=nmax)[:nmax]
    tl += np.bincount(a, weights=(57600.0 / sc).ravel() / 1e4, minlength=nmax)[:nmax]
af = attrs[["fma_id", "province", "area_name"]].copy()
af["forest_ha"] = tf[af.fma_id.values]
af["land_ha_grid"] = tl[af.fma_id.values]
af.to_csv(D / "area_forest.csv", index=False)
log(f"Canada forest {af.forest_ha.sum():,.0f} ha; areas with < 1% forest: {(af.forest_ha < 0.01 * af.land_ha_grid).sum()}", fh)
