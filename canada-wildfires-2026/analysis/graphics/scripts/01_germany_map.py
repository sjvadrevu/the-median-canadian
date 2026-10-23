"""Slide graphic: land burned in Canada, 2023 to 2026, with Germany drawn at the same scale.

Inputs: NBAC 2023 to 2025 outlines, CWFIS M3 2026 outlines (wildfire class from outline-check),
fire management areas (Canada outline), Natural Earth 1:50m countries (Germany).
All shapes in equal-area projections (Canada: EPSG:3978; Germany: Lambert azimuthal equal area
centred on Germany), so areas compare directly. Output: canada_burned_germany.svg and _stats.csv."""
import os
import geopandas as gpd
import pandas as pd
import pyogrio
from shapely import affinity
from shapely.ops import unary_union

W = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(W, "analysis", "graphics")
nb = pyogrio.read_dataframe(os.path.join(W, "data/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp"),
                            where="YEAR >= 2023", columns=["YEAR", "POLY_HA"])
nb = nb.to_crs(3978)
m3 = gpd.read_file(os.path.join(W, "data/fire/m3_perimeters_2026_cwfis_20261020.gpkg")).to_crs(3978)
fma = gpd.read_file(os.path.join(W, "data/geo/fma_v2.gpkg")).to_crs(3978)
canada = unary_union([g.simplify(5000) for g in fma.geometry.buffer(0)]).simplify(4000)
print("canada done", flush=True)
geoms = [g.simplify(1500) for g in list(nb.geometry) + list(m3.geometry) if g is not None]
geoms = [g for g in geoms if not g.is_empty]
burn = unary_union([g.buffer(0) for g in geoms])
burn_ha = burn.area / 1e4
print("burn done", flush=True)
ne = gpd.read_file(os.path.join(W, "data/geo/ne/ne_50m_admin_0_countries.geojson"))
de = ne[ne.ADMIN == "Germany"].to_crs("+proj=laea +lat_0=51 +lon_0=10.5 +datum=WGS84 +units=m")
de_geom = de.geometry.iloc[0]
de_ha = de_geom.area / 1e4
pd.DataFrame([{"burned_union_ha_mapped": burn_ha, "germany_ha": de_ha}]).to_csv(os.path.join(OUT, "canada_burned_germany_stats.csv"), index=False)
print(f"mapped burned union {burn_ha/1e6:.2f} M ha; Germany {de_ha/1e6:.2f} M ha")
burn_s = burn
# place Germany over the Atlantic, east of Labrador, same scale
minx, miny, maxx, maxy = canada.bounds
dminx, dminy, dmaxx, dmaxy = de_geom.bounds
tx = maxx - (dmaxx - dminx) * 1.15 - dminx
ty = miny + (maxy - miny) * 0.08 - dminy
de_t = affinity.translate(de_geom.simplify(1500), tx, ty)

def path(g):
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    out = []
    for p in polys:
        for ring in [p.exterior] + list(p.interiors):
            xs = list(ring.coords)
            out.append("M" + "L".join(f"{(x - minx) * sc:.1f},{(maxy - y) * sc:.1f}" for x, y in xs) + "Z")
    return "".join(out)

Wpx = 928
sc = Wpx / (maxx - minx)
Hpx = (maxy - miny) * sc
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wpx}" height="{Hpx:.0f}" viewBox="0 0 {Wpx} {Hpx:.0f}">',
       f'<path d="{path(canada)}" fill="#3a4250" stroke="#5b6575" stroke-width="1"/>',
       f'<path d="{path(burn_s)}" fill="#ff6b4f"/>',
       f'<path d="{path(de_t)}" fill="none" stroke="#ffffff" stroke-width="3" stroke-dasharray="6 5"/>',
       '</svg>']
open(os.path.join(OUT, "canada_burned_germany.svg"), "w").write("".join(svg))
c = de_t.centroid
print("germany label at", (c.x - minx) * sc, (maxy - c.y) * sc, "svg height", Hpx)
open(os.path.join(OUT, "germany_label_xy.txt"), "w").write(f"{(c.x - minx) * sc:.1f},{(maxy - c.y) * sc:.1f},{Hpx:.0f}")
