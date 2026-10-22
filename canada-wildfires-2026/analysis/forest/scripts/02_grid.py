"""Build the 240 m analysis grid (the Land Cover 2020 forest-count grid, EPSG:3979).

Saved in work/:
  forest_count.npy  uint8  number of 30 m forest pixels (classes 1,2,5,6) in each 240 m cell (0..64)
  fma_v2_id.npy     uint16 fire management area id of fma_v2 (1..2066), 0 = outside Canada polygons
                    (rebuild 2026-10-21; the fma_all grids fma_id.npy / park_id.npy are kept for other analyses
                    and are no longer used here: there is no separate Parks Canada layer)
  areal_scale_coarse.npy  float32  Lambert conformal areal scale factor (k*h) at every 25th cell centre
  grid_meta.json
True ground area of a cell = 240*240 / areal_scale (m2); forest area = count*900 / areal_scale (m2).
The grid projection is conformal (not equal-area), so counts are converted to equal-area hectares with
the projection's areal scale factor; the correction is checked against ESRI:102001 polygon areas.
Rasterisation rule: a 240 m cell belongs to a polygon when its centre is inside it.
"""
import json
import numpy as np
import geopandas as gpd
import rasterio
from rasterio import features
from pyproj import Proj, Transformer
from common import FOREST, FMA, FMA_SIMP, FMA_GRID, WORK, EA

import os
with rasterio.open(FOREST) as r:
    fc = r.read(1) if not (WORK / "forest_count.npy").exists() else None
    prof = r.profile
    T = r.transform
    H, W = r.height, r.width
    crs = r.crs
if fc is not None:
    fc[fc == 255] = 0
    np.save(WORK / "forest_count.npy", fc)
    print("grid", H, W, "forest cells", int((fc > 0).sum()))
del fc

# areal scale factor on a coarse lattice (every 25 cells); area-independent, built once
STEP = 25
if not (WORK / "areal_scale_coarse.npy").exists():
    rr = np.arange(STEP // 2, H, STEP)
    cc = np.arange(STEP // 2, W, STEP)
    C, R = np.meshgrid(cc, rr)
    x = T.c + (C + 0.5) * T.a
    y = T.f + (R + 0.5) * T.e
    tr = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    lon, lat = tr.transform(x, y)
    pj = Proj(crs)
    fac = pj.get_factors(lon.ravel(), lat.ravel())
    asc = np.asarray(fac.areal_scale, dtype="float32").reshape(lon.shape)
    np.save(WORK / "areal_scale_coarse.npy", asc)
    print("areal scale range", float(np.nanmin(asc)), float(np.nanmax(asc)))

# Uses the 20 m simplified copy of the area layer written by 02b_fma_simplified.py (run 02b first).
fma = gpd.read_file(FMA_SIMP).to_crs(crs)
assert (fma.agency != "Parks Canada").all() and fma.fma_id.max() < 65535
fid = np.zeros((H, W), dtype="uint16")
for i, geom in zip(fma.fma_id, fma.geometry):
    features.rasterize([(geom, int(i))], out=fid, transform=T)
np.save(WORK / f"{FMA_GRID}.npy", fid)
print("fma cells", int((fid > 0).sum()))
del fid

meta = dict(H=H, W=W, transform=list(T)[:6], crs=crs.to_wkt(), step=STEP)
if not (WORK / "grid_meta.json").exists():          # shared with other analyses; identical content
    json.dump(meta, open(WORK / "grid_meta.json", "w"))
