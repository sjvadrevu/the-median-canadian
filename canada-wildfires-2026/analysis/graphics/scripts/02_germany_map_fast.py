"""Slide graphic: land burned in Canada 2023 to 2026 (NBAC 2023 to 2025 + CWFIS M3 2026 outlines),
drawn on the site's Canada base map (EPSG:3978), with Germany drawn at the same scale.
Each outline is simplified to 1.5 km and drawn directly (no union), which is enough at slide size.
Output: analysis/graphics/canada_burned_germany_paths.json (pixel paths for a 928 px wide map)."""
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
                            where="YEAR >= 2023 AND POLY_HA >= 20", columns=["YEAR", "POLY_HA"])
print("nbac read", len(nb), round(time.time() - t0), flush=True)
nb = nb.to_crs(3978)
m3 = gpd.read_file(os.path.join(W, "data/fire/m3_perimeters_2026_cwfis_20261020.gpkg")).to_crs(3978)
print("m3 read", len(m3), round(time.time() - t0), flush=True)


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


burn = "".join(to_path(g) for g in list(nb.geometry) + list(m3.geometry) if g is not None)
print("paths", len(burn), round(time.time() - t0), flush=True)
ne = gpd.read_file(os.path.join(W, "data/geo/ne/ne_50m_admin_0_countries.geojson"))
de = ne[ne.ADMIN == "Germany"].to_crs("+proj=laea +lat_0=51 +lon_0=10.5 +datum=WGS84 +units=m").geometry.iloc[0]
de = max(de.geoms, key=lambda p: p.area) if de.geom_type == "MultiPolygon" else de
cx, cy = de.centroid.x, de.centroid.y
de_px = "M" + "L".join(f"{(x - cx) * m.sc:.1f},{-(y - cy) * m.sc:.1f}" for x, y in de.simplify(1500).exterior.coords) + "Z"
json.dump({"W": m.W, "H": m.H, "base": m.base_path(), "burn": burn, "germany_centred": de_px,
           "germany_ha": de.area / 1e4}, open(os.path.join(W, "analysis/graphics/canada_burned_germany_paths.json"), "w"))
print("done", round(time.time() - t0), flush=True)
