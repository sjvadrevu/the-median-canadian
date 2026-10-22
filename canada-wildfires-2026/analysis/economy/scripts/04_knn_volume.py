"""Sample the NFI MODIS 250 m kNN 2011 forest attribute layers (Beaudoin et al., NRCan) at every burned
240 m cell centre: merchantable volume (m3/ha), total volume (m3/ha), live aboveground biomass (t/ha),
dead biomass (t/ha), and live aboveground biomass components (t/ha): stem wood, stem bark, branches, foliage.

The 250 m and 240 m grids do not nest, so each 240 m cell takes the value of the 250 m pixel containing its
centre (nearest-pixel sampling). Values per cell = value per ha x true cell area (ha). Nodata -> 0 (non-forest
or outside the mapped area); n_nodata is recorded.
Output: work/knn2011.npz (arrays aligned to work/cells.pkl).
"""
import sys
import numpy as np
import pandas as pd
import rasterio
from ecommon import WORK, RAW
from grid import meta

LAYERS = {"vol_merch": "Structure_Volume_Merch", "vol_total": "Structure_Volume_Total",
          "agb_live": "Structure_Biomass_TotalLiveAboveGround", "bio_dead": "Structure_Biomass_TotalDead",
          "bio_stemwood": "Structure_Biomass_StemWood", "bio_stembark": "Structure_Biomass_StemBark",
          "bio_branch": "Structure_Biomass_Branch", "bio_foliage": "Structure_Biomass_Foliage"}
m = meta()
X0, Y0 = m["transform"][2], m["transform"][5]
DX, DY = 0.6, -6585076.93
CELLS = sys.argv[1] if len(sys.argv) > 1 else "cells.pkl"   # optional: other cell table
cells = pd.read_pickle(WORK / CELLS)
xs = X0 + 240 * (cells.col.values + 0.5) - DX
ys = Y0 - 240 * (cells.row.values + 0.5) - DY
out = {}
for k, name in LAYERS.items():
    f = RAW / "knn2011" / f"NFI_MODIS250m_2011_kNN_{name}_v1.tif"
    with rasterio.open(f) as r:
        a = r.read(1)
        t = r.transform
        jj = np.floor((xs - t.c) / t.a).astype(np.int64)
        ii = np.floor((ys - t.f) / t.e).astype(np.int64)
        ok = (ii >= 0) & (ii < r.height) & (jj >= 0) & (jj < r.width)
        v = np.full(len(cells), np.nan, "float32")
        v[ok] = a[ii[ok], jj[ok]]
        nd = ~np.isfinite(v) | (v < 0) | (v > 1e6)
        v[nd] = 0
        out[k + "_per_ha"] = v
        out[k + "_nodata"] = nd
        print(k, "nodata cells", int(nd.sum()), "total", float((v * cells.area_ha.values).sum()), flush=True)
        del a
np.savez(WORK / ("knn2011.npz" if CELLS == "cells.pkl" else f"knn2011_{CELLS[:-4]}.npz"), **out)
