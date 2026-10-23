"""Write work/fma_v2_simplified.gpkg (common.FMA_SIMP): the area layer (common.FMA, fma_v2) simplified to 20 m
(ESRI:102001), part by part. (Before the 2026-10-21 rebuild this wrote work/fma_simplified.gpkg from fma_all.)
The source file holds very detailed coastlines and sliver remainders (one row has 98,619 parts and
2.0 M vertices), which cannot be overlaid in memory as is. Each polygon part is simplified on its own
(Douglas-Peucker, topology preserving, 20 m tolerance, far below the 240 m grid); parts that collapse are
dropped. The area change per row is recorded in simplify_area_change (max is reported).
Run this before 02_grid.py.
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
import shapely
from common import FMA, FMA_SIMP, WORK

ids = pyogrio.read_dataframe(FMA, columns=["fma_id"], read_geometry=False)
parts_out = []
for i in ids.fma_id:
    g = pyogrio.read_dataframe(FMA, where=f"fma_id = {int(i)}")
    geom = g.geometry.iloc[0]
    parts = shapely.get_parts(geom)
    parts = np.concatenate([shapely.get_parts(p) for p in parts])
    parts = parts[shapely.get_type_id(parts) == 3]            # polygons only
    a0 = shapely.area(parts).sum()
    s = shapely.simplify(parts, 20, preserve_topology=True)
    s = s[~shapely.is_empty(s) & (shapely.area(s) > 0)]
    s = shapely.make_valid(s)
    s = np.concatenate([shapely.get_parts(x) for x in s])
    s = s[shapely.get_type_id(s) == 3]
    new = shapely.multipolygons(s)
    g["geometry"] = [new]
    g["simplify_area_change"] = shapely.area(new) / a0 - 1
    print(int(i), len(parts), int(shapely.get_num_coordinates(new)), round(float(g.simplify_area_change.iloc[0]), 6), flush=True)
    parts_out.append(g)
out = gpd.GeoDataFrame(pd.concat(parts_out, ignore_index=True), crs=parts_out[0].crs)
out.to_file(FMA_SIMP, driver="GPKG")
print("max abs area change", out.simplify_area_change.abs().max())
