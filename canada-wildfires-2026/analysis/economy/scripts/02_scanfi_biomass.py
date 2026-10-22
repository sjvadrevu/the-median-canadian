"""Sum SCANFI v2 30 m aboveground biomass inside every burned 240 m cell.

Usage: python3 02_scanfi_biomass.py <SCANFI tif or /vsicurl/ URL> <tag> [cells pickle, default cells.pkl]
Output: work/scanfi_<tag>.npz with arrays aligned to work/cells.pkl rows:
  bio_t   aboveground biomass in tonnes (sum over 30 m pixels of t/ha x true pixel area)
  n_valid number of 30 m pixels with a value (>= 0)
  n_nd    number of 30 m pixels that are nodata
A 30 m pixel belongs to the 240 m cell that contains its centre. SCANFI uses NAD83 Canada Lambert with
lat_0 = 0; the grid uses EPSG:3979 (lat_0 = 49). x_3979 = x_scanfi + 0.6 m, y_3979 = y_scanfi - 6,585,076.93 m
(pyproj, varies by under 0.1 m across Canada). Pixel true area = 0.09 ha / areal scale of its 240 m cell.
Nodata pixels (water, outside mapped area) count as 0 biomass and are reported in n_nd.
The raster is read window by window (2048 x 2048 px); only windows containing burned cells are read.
"""
import sys
import time
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from ecommon import WORK
from grid import meta, cell_area_m2

src, tag = sys.argv[1], sys.argv[2]
m = meta()
X0, Y0 = m["transform"][2], m["transform"][5]
DX, DY = 0.6, -6585076.93
cells = pd.read_pickle(WORK / (sys.argv[3] if len(sys.argv) > 3 else "cells.pkl"))
N = len(cells)
crow = cells.row.values
ccol = cells.col.values
ha_px = 0.09 * (cell_area_m2(cells.idx.values) / 57600.0)   # 0.09 ha / areal scale

bio = np.zeros(N, "float64")
nv = np.zeros(N, "int32")
nnd = np.zeros(N, "int32")
B = 2048
with rasterio.open(src) as r:
    t = r.transform
    sx0, sy0 = t.c, t.f
    nd = r.nodata
    # SCANFI pixel row/col range of each burned cell
    cx0 = X0 + 240 * ccol - DX            # cell left edge in SCANFI x
    cy0 = Y0 - 240 * crow - DY            # cell top edge in SCANFI y
    pj = ((cx0 - sx0) // 30).astype(np.int64)
    pi = ((sy0 - cy0) // 30).astype(np.int64)
    wi, wj = pi // B, pj // B
    key = wi * 100000 + wj
    order = np.argsort(key, kind="stable")
    ukeys, starts = np.unique(key[order], return_index=True)
    ends = np.r_[starts[1:], order.size]
    print(len(ukeys), "windows to read", flush=True)
    t0 = time.time()
    for n, (k, s, e) in enumerate(zip(ukeys, starts, ends)):
        sel = order[s:e]
        bi, bj = int(k // 100000), int(k % 100000)
        # pad by one cell (9 px) so cells straddling the window edge are complete
        i0, j0 = bi * B - 9, bj * B - 9
        h = w = B + 18
        i0c, j0c = max(i0, 0), max(j0, 0)
        i1c, j1c = min(i0 + h, r.height), min(j0 + w, r.width)
        a = r.read(1, window=Window(j0c, i0c, j1c - j0c, i1c - i0c))
        ii = np.arange(i0c, i1c)
        jj = np.arange(j0c, j1c)
        # pixel centre -> grid row/col
        ys = sy0 - 30 * (ii + 0.5) + DY
        xs = sx0 + 30 * (jj + 0.5) + DX
        prow = np.floor((Y0 - ys) / 240).astype(np.int64)
        pcol = np.floor((xs - X0) / 240).astype(np.int64)
        r0, c0 = crow[sel].min(), ccol[sel].min()
        r1, c1 = crow[sel].max(), ccol[sel].max()
        lut = np.full((r1 - r0 + 1, c1 - c0 + 1), -1, np.int64)
        lut[crow[sel] - r0, ccol[sel] - c0] = np.arange(sel.size)
        okr = (prow >= r0) & (prow <= r1)
        okc = (pcol >= c0) & (pcol <= c1)
        sub = a[np.ix_(okr, okc)]
        L = lut[np.ix_(prow[okr] - r0, pcol[okc] - c0)]
        hit = L >= 0
        Lh = L[hit]
        v = sub[hit]
        valid = (v != nd) & (v >= 0)
        m_ = sel.size
        bio[sel] += np.bincount(Lh[valid], weights=v[valid].astype("float64"), minlength=m_)
        nv[sel] += np.bincount(Lh[valid], minlength=m_).astype("int32")
        nnd[sel] += np.bincount(Lh[~valid], minlength=m_).astype("int32")
        if n % 100 == 0:
            print(n, round(time.time() - t0), "s", flush=True)
bio_t = bio * ha_px
np.savez(WORK / f"scanfi_{tag}.npz", bio_t=bio_t, n_valid=nv, n_nd=nnd)
tot = nv + nnd
print("pixels per cell: min", tot.min(), "max", tot.max(), "mean", tot.mean())
print("total biomass Mt", bio_t.sum() / 1e6, "mean t/ha", bio_t.sum() / cells.area_ha.sum())
