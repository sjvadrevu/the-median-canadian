"""Step 0: extract fire outlines for one year to work/fires_<year>.gpkg in ESRI:102001.
Usage: python3 -I 00_extract_fires.py 2023
2026 = CWFIS M3 perimeters (file stamped 2026-10-20); 2023-2025 = NBAC 1972-2025 v20260513,
prescribed burns (PRESCRIBED = 'true') excluded."""
import sys, os, gc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

yr = int(sys.argv[1])
g = load_fires(yr)
g["area_ha"] = g.geometry.area / 1e4
print(yr, "polygons", len(g), "area ha (equal-area)", round(g.area_ha.sum()),
      "vertices", int(shapely.get_num_coordinates(g.geometry.values).sum()))
g.to_file(f"{WORK}/fires_{yr}.gpkg", driver="GPKG")
