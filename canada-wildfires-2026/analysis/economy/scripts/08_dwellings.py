"""Private dwellings (2021 Census) in dissemination areas (DA) that intersect 2026 CWFIS M3 fire outlines.

Dissemination-block counts (the finer unit) are published only in the Geographic Attribute File on
www12.statcan.gc.ca, which refused automated download (HTTP 403 bot check), so the DA is the finest unit used.
Two counts, both "dwellings in areas intersecting fires", NOT losses:
  A. DA polygon intersects an outline (upper bound; rural DAs are large)
  B. DA representative point (inside the DA polygon) lies inside an outline (tighter)
Dwellings: table 98-10-0015-01 "Total private dwellings, 2021" and "Private dwellings occupied by usual residents".
DA polygons: StatCan 2021 cartographic DA (generalised 50 m), EPSG:3347, overlay in ESRI:102001.
Outputs: dwellings_2026_by_province.csv, work/dwellings_da_2026.csv
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import make_valid
from ecommon import DATA, WORK, OUT, M3, EA

G = DATA / "geo" / "statcan"
t = pd.read_csv(G / "tables" / "98100015" / "98100015.csv", encoding="utf-8-sig", dtype=str)
cols = list(t.columns)
pdw = [c for c in cols if "Total private dwellings" in c][0]
odw = [c for c in cols if "occupied by usual residents" in c][0]
popc = [c for c in cols if "Population, 2021" in c][0]
t = t[t.DGUID.str.contains("S0512", na=False)].copy()     # DA rows
t["DAUID"] = t.DGUID.str[-8:]
for c, n in [(pdw, "dw_total"), (odw, "dw_occupied"), (popc, "pop2021_t")]:
    t[n] = pd.to_numeric(t[c], errors="coerce")
t = t[["DAUID", "dw_total", "dw_occupied", "pop2021_t"]]
print("DA rows", len(t), "dwellings", t.dw_total.sum())

da = gpd.read_file(G / "da_2021_pop_gen50m.gpkg").to_crs(EA)
pts = gpd.read_file(G / "da_2021_pop_points.gpkg").to_crs(EA)
fires = gpd.read_file(M3).to_crs(EA)
fires["geometry"] = [make_valid(g) for g in fires.geometry]
fires = fires[["UID", "prov", "geometry"]]
hitA = gpd.sjoin(da[["DAUID", "PRUID", "geometry"]], fires, predicate="intersects").DAUID.unique()
hitB = gpd.sjoin(pts[["DAUID", "geometry"]], fires, predicate="within").DAUID.unique()
d = da[["DAUID", "PRUID"]].merge(t, on="DAUID", how="left")
d["A_intersects"] = d.DAUID.isin(hitA)
d["B_point_inside"] = d.DAUID.isin(hitB)
PR = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON", "46": "MB", "47": "SK", "48": "AB",
      "59": "BC", "60": "YT", "61": "NT", "62": "NU"}
d["prov"] = d.PRUID.astype(str).map(PR)
d[d.A_intersects].to_csv(WORK / "dwellings_da_2026.csv", index=False)
rows = []
for p, g in list(d.groupby("prov")) + [("Canada", d)]:
    a, b = g[g.A_intersects], g[g.B_point_inside]
    rows.append(dict(prov=p, n_da_intersecting=len(a), dwellings_total_da_intersecting=a.dw_total.sum(),
                     dwellings_occupied_da_intersecting=a.dw_occupied.sum(), pop2021_da_intersecting=a.pop2021_t.sum(),
                     n_da_point_inside=len(b), dwellings_total_da_point_inside=b.dw_total.sum(),
                     dwellings_occupied_da_point_inside=b.dw_occupied.sum(), pop2021_da_point_inside=b.pop2021_t.sum(),
                     n_da_no_count_intersecting=int(a.dw_total.isna().sum())))
r = pd.DataFrame(rows)
r.to_csv(OUT / "dwellings_2026_by_province.csv", index=False)
print(r.to_string())
