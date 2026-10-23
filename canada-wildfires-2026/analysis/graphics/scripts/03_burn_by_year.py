"""Site graphic: land burned in each year, 2023 to 2026 (NBAC 2023 to 2025, CWFIS M3 2026 outlines), as pixel paths
for the same 928 px Canada map as 02_germany_map_fast.py (same simplification, no union), so the site can show one
year at a time. Output: analysis/graphics/canada_burned_by_year_paths.json"""
import json
import os
import sys
import time

import geopandas as gpd
import pyogrio

W = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(W, "slides"))
from canmap import CanMap  # noqa: E402

t0 = time.time()
m = CanMap(928)
nb = pyogrio.read_dataframe(os.path.join(W, "data/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp"),
                            where="YEAR >= 2023 AND POLY_HA >= 20", columns=["YEAR", "POLY_HA"]).to_crs(3978)
m3 = gpd.read_file(os.path.join(W, "data/fire/m3_perimeters_2026_cwfis_20261020.gpkg")).to_crs(3978)
print("read", len(nb), len(m3), round(time.time() - t0), flush=True)


def to_path(g):
    g = g.simplify(1500)
    if g.is_empty:
        return ""
    polys = [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]
    out = []
    for p in polys:
        c = list(p.exterior.coords)
        if len(c) < 4:
            continue
        out.append("M" + "L".join(f"{(x - m.minx) * m.sc:.1f},{(m.maxy - y) * m.sc:.1f}" for x, y in c) + "Z")
    return "".join(out)


paths = {str(y): "".join(to_path(g) for g in nb[nb.YEAR == y].geometry if g is not None) for y in (2023, 2024, 2025)}
paths["2026"] = "".join(to_path(g) for g in m3.geometry if g is not None)
json.dump({"W": m.W, "H": m.H, "burn": paths},
          open(os.path.join(W, "analysis/graphics/canada_burned_by_year_paths.json"), "w"))
print({k: len(v) for k, v in paths.items()}, round(time.time() - t0), flush=True)
