"""Rasterize every NBAC year (1972-2025) and the 2026 CWFIS M3 outlines to the 240 m grid.

A cell counts as burned in a year when its centre lies inside a burned polygon of that year.
NBAC and M3 are in Lambert conformal conic with the same parameters as the grid (EPSG:3978 vs
EPSG:3979 differ only by NAD83 vs NAD83(CSRS), sub-2 m), so coordinates are used as is.
Outputs work/burn_YYYY.npy (uint32 flat cell indices) and work/burn_rasterize_log.csv.
"""
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
from shapely import make_valid
from common import NBAC_SHP, M3, WORK, EA
from grid import rasterize_idx, cell_area_m2

years = list(range(1972, 2026))
if len(sys.argv) > 1:
    years = [int(a) for a in sys.argv[1:]]
log = []
for y in years:
    if y == 2026:
        g = gpd.read_file(M3)
        src = "M3"
    else:
        g = pyogrio.read_dataframe(NBAC_SHP, where=f"YEAR = {y}", columns=["YEAR", "POLY_HA", "ADJ_HA", "ADMIN_NAME"])
        src = "NBAC"
    geoms = [make_valid(x) if not x.is_valid else x for x in g.geometry]
    ea_area = gpd.GeoSeries(geoms, crs=g.crs).to_crs(EA).area.sum() / 1e4
    idx = rasterize_idx(geoms)
    np.save(WORK / f"burn_{y}.npy", idx)
    ras_ha = cell_area_m2(idx).sum() / 1e4
    row = dict(year=y, source=src, n_poly=len(g), vector_ea_ha=ea_area, raster_ha=ras_ha,
               attr_poly_ha=g["POLY_HA"].sum() if "POLY_HA" in g else np.nan,
               attr_adj_ha=g["ADJ_HA"].sum() if "ADJ_HA" in g else np.nan)
    print(row, flush=True)
    # write after each year so a crash keeps earlier rows
    lf = WORK / "burn_rasterize_log.csv"
    df = pd.DataFrame([row])
    if lf.exists():
        old = pd.read_csv(lf)
        df = pd.concat([old[old.year != y], df]).sort_values("year")
    df.to_csv(lf, index=False)
