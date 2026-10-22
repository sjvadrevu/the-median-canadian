"""Write a lighter copy of the fire management areas (non-park rows only),
simplified at 500 m (ample for 2 km grid cells and station lookups), reading
features in small batches to keep memory low. Output: work/fma_simple.gpkg
Area layer: data/geo/fma_v2.gpkg since the 2026-10-21 rebuild (MB and QC sub-areas, no Parks Canada rows);
override with AREA_FILE=/path/to/areas.gpkg.
"""
import os
import sys

import geopandas as gpd
import pandas as pd
import pyogrio
import shapely

W = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.environ.get("AREA_FILE", os.path.join(W, "data", "geo", "fma_v2.gpkg"))
n = pyogrio.read_info(SRC)["features"]
parts = []
for start in range(0, n, 5):
    g = pyogrio.read_dataframe(SRC, skip_features=start, max_features=5)
    g = g[~g["agency"].str.contains("Parks Canada")]
    if len(g):
        g["geometry"] = shapely.make_valid(shapely.simplify(g.geometry.values, 500, preserve_topology=False))
        parts.append(g[["fma_id", "agency", "area_name", "province", "area_level", "geometry"]])
    print(start, flush=True)
out = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=parts[0].crs)
out.to_file(os.path.join(W, "analysis", "weather", "work", "fma_simple.gpkg"), driver="GPKG")
print(len(out))
