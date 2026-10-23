"""Write fma_2026.geojson for the site: fire management areas of fma_v2 (186 rows tiling Canada; no separate
Parks Canada layer since the 2026-10-21 rebuild) with the attributes of fma_2026_table.csv. Geometry simplified part by part with a
1,000 m tolerance (display only; all areas were computed from the full-detail data), parts under 1 km2
after simplification dropped, WGS84.
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from common import WORK, OUT, FMA_SIMP

fma = gpd.read_file(FMA_SIMP)[["fma_id", "geometry"]]
T = pd.read_csv(OUT / "fma_2026_table.csv")
geoms = []
for g in fma.geometry:
    parts = shapely.get_parts(g)
    s = shapely.simplify(parts, 1000, preserve_topology=True)
    s = s[shapely.area(s) >= 1e6]
    if len(s) == 0:                       # tiny areas: keep the largest original part, lightly simplified
        s = [shapely.simplify(parts[np.argmax(shapely.area(parts))], 100, preserve_topology=True)]
    geoms.append(shapely.make_valid(shapely.multipolygons(list(s))))
fma["geometry"] = geoms
out = fma.merge(T, on="fma_id")
out.to_crs("EPSG:4326").to_file(OUT / "fma_2026.geojson", driver="GeoJSON", COORDINATE_PRECISION=4)
print(len(out), "rows written")
