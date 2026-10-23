"""Private dwellings (2021 Census) in dissemination areas intersecting burned areas, per year 2016-2026 and 2023-2026.

Same method as 08_dwellings.py: A = DA polygon intersects a burned polygon; B = DA representative point inside.
Fire polygons: NBAC 2016-2025 (version 20260513, prescribed burns removed, as in analysis/people), CWFIS M3 2026.
NBAC includes many small agency-mapped fires near towns that M3 hotspot outlines miss, so 2026 counts are on a
different (coarser) footprint; the 2026 row is repeated with M3 fires of 1,000 ha or more for reference, and every
year is also given for fires of 1,000 ha or more (NBAC: per NFIREID polygon area; M3: per CONSIS_ID).
The 2021 dwelling stock is used for every year (no annual DA series).
Output: dwellings_by_year.csv
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
from shapely import make_valid
from ecommon import DATA, WORK, OUT, M3, EA, FWORK

G = DATA / "geo" / "statcan"
t = pd.read_csv(G / "tables" / "98100015" / "98100015.csv", encoding="utf-8-sig", dtype=str)
pdw = [c for c in t.columns if "Total private dwellings" in c][0]
popc = [c for c in t.columns if "Population, 2021" in c][0]
t = t[t.DGUID.str.contains("S0512", na=False)].copy()
t["DAUID"] = t.DGUID.str[-8:]
t["dw_total"] = pd.to_numeric(t[pdw], errors="coerce")
t["pop2021"] = pd.to_numeric(t[popc], errors="coerce")
da = gpd.read_file(G / "da_2021_pop_gen50m.gpkg", columns=["DAUID", "PRUID"]).to_crs(EA)
pts = gpd.read_file(G / "da_2021_pop_points.gpkg", columns=["DAUID"]).to_crs(EA)
da = da.merge(t[["DAUID", "dw_total", "pop2021"]], on="DAUID", how="left")
PR = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON", "46": "MB", "47": "SK", "48": "AB",
      "59": "BC", "60": "YT", "61": "NT", "62": "NU"}
da["prov"] = da.PRUID.astype(str).map(PR)
NB = FWORK / "nbac_shp" / "NBAC_merged_1972_to_2025_20260513.shp"


def fires_for(y):
    if y == 2026:
        f = gpd.read_file(M3)
        f["size"] = f.groupby("CONSIS_ID").area_ha_albers.transform("sum")
    else:
        f = pyogrio.read_dataframe(NB, where=f"YEAR = {y}", columns=["YEAR", "NFIREID", "POLY_HA", "PRESCRIBED"])
        f = f[f.PRESCRIBED.fillna("").astype(str).str.lower() != "true"]
        f["size"] = f.groupby("NFIREID").POLY_HA.transform("sum")
    f = f.to_crs(EA)
    f["geometry"] = [make_valid(g) for g in f.geometry]
    return f[["size", "geometry"]]


rows = []
hitsA, hitsB = {}, {}
for y in range(2016, 2027):
    f = fires_for(y)
    for lab, ff in [("all", f), ("ge1000ha", f[f["size"] >= 1000])]:
        A = set(gpd.sjoin(da[["DAUID", "geometry"]], ff, predicate="intersects").DAUID)
        B = set(gpd.sjoin(pts, ff, predicate="within").DAUID)
        hitsA[(y, lab)], hitsB[(y, lab)] = A, B
    print(y, len(f), flush=True)
for lab in ["all", "ge1000ha"]:
    hitsA[("2023_2026", lab)] = set().union(*[hitsA[(y, lab)] for y in range(2023, 2027)])
    hitsB[("2023_2026", lab)] = set().union(*[hitsB[(y, lab)] for y in range(2023, 2027)])
for (y, lab), A in hitsA.items():
    B = hitsB[(y, lab)]
    a, b = da[da.DAUID.isin(A)], da[da.DAUID.isin(B)]
    for p in list(da.prov.dropna().unique()) + ["Canada"]:
        aa = a if p == "Canada" else a[a.prov == p]
        bb = b if p == "Canada" else b[b.prov == p]
        rows.append(dict(year=y, fires=lab, prov=p, n_da_intersecting=len(aa), dwellings_da_intersecting=aa.dw_total.sum(),
                         pop2021_da_intersecting=aa.pop2021.sum(), n_da_point_inside=len(bb),
                         dwellings_da_point_inside=bb.dw_total.sum(), pop2021_da_point_inside=bb.pop2021.sum()))
o = pd.DataFrame(rows)
o.to_csv(OUT / "dwellings_by_year.csv", index=False)
print(o[o.prov == "Canada"].sort_values(["fires", "year"]).to_string())
