"""Replacement-value proxy of EXPOSED dwellings: 2021 Census private dwellings in dissemination areas (DAs) touched by
fire, each DA valued at its 2021 Census average (and median) value of owner-occupied dwellings (Census Profile 2021,
characteristics 1475 / 1474, via api.statcan.gc.ca SDMX, raw/census/). DA sets are rebuilt exactly as
analysis/economy/scripts/08b_dwellings_by_year.py (A = DA polygon intersects a burned polygon; B = DA representative
point inside one; NBAC 2016-2025 prescribed removed; CWFIS M3 2026; all fires and fires >= 1,000 ha).
Missing DA values (suppressed, e.g. most reserves, or no owner households) fall back to the census division, then the
province. This is NOT a loss: it is the value of the dwelling stock in areas the fires touched, and owner-occupied
averages are applied to all private dwellings. -> exposed_dwelling_value_by_year.csv, work/da_values_2021.csv"""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd, pyogrio
from shapely import make_valid
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.dirname(os.path.dirname(P))
G = os.path.join(W, "data", "geo", "statcan")
def cen(f):
    d = pd.read_csv(os.path.join(P, "raw", "census", f), usecols=["CHARACTERISTIC", "OBS_VALUE", "ALT_GEO_CODE"], dtype={"ALT_GEO_CODE": str})
    return d.pivot_table(index="ALT_GEO_CODE", columns="CHARACTERISTIC", values="OBS_VALUE").rename(columns={1474: "median_value", 1475: "avg_value"})
vda, vcd, vpr = cen("da_dwelling_value_2021.csv"), cen("cd_dwelling_value_2021.csv"), cen("pr_dwelling_value_2021.csv")
t = pd.read_csv(os.path.join(G, "tables", "98100015", "98100015.csv"), encoding="utf-8-sig", dtype=str)
pdw = [c for c in t.columns if "Total private dwellings" in c][0]
t = t[t.DGUID.str.contains("S0512", na=False)].copy(); t["DAUID"] = t.DGUID.str[-8:]; t["dw_total"] = pd.to_numeric(t[pdw], errors="coerce")
da = gpd.read_file(os.path.join(G, "da_2021_pop_gen50m.gpkg"), columns=["DAUID", "PRUID"]).to_crs("ESRI:102001")
pts = gpd.read_file(os.path.join(G, "da_2021_pop_points.gpkg"), columns=["DAUID"]).to_crs("ESRI:102001")
da = da.merge(t[["DAUID", "dw_total"]], on="DAUID", how="left")
da["CDUID"] = da.DAUID.str[:4]; da["PRUID"] = da.PRUID.astype(str)
for c in ["avg_value", "median_value"]:
    v = da.DAUID.map(vda[c]); src = np.where(v.notna(), "DA", None)
    v2 = da.CDUID.map(vcd[c]); src = np.where(pd.isna(src) & v2.notna(), "CD", src); v = v.fillna(v2)
    v3 = da.PRUID.map(vpr[c]); src = np.where(pd.isna(src) & v3.notna(), "PR", src); v = v.fillna(v3)
    da[c] = v; da[c + "_src"] = src
da.drop(columns="geometry").to_csv(os.path.join(P, "work", "da_values_2021.csv"), index=False)
PR = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON", "46": "MB", "47": "SK", "48": "AB", "59": "BC", "60": "YT", "61": "NT", "62": "NU"}
da["prov"] = da.PRUID.map(PR)
NB = os.path.join(W, "data", "fire", "raw", "nbac", "shp", "NBAC_merged_1972_to_2025_20260513.shp")
M3 = os.path.join(W, "data", "fire", "m3_perimeters_2026_cwfis_20261020.gpkg")
def fires_for(y):
    if y == 2026:
        f = gpd.read_file(M3); f["size"] = f.groupby("CONSIS_ID").area_ha_albers.transform("sum")
    else:
        f = pyogrio.read_dataframe(NB, where=f"YEAR = {y}", columns=["YEAR", "NFIREID", "POLY_HA", "PRESCRIBED"])
        f = f[f.PRESCRIBED.fillna("").astype(str).str.lower() != "true"]; f["size"] = f.groupby("NFIREID").POLY_HA.transform("sum")
    f = f.to_crs("ESRI:102001"); f["geometry"] = [make_valid(g) for g in f.geometry]
    return f[["size", "geometry"]]
hA, hB = {}, {}
years = [int(a) for a in sys.argv[1:]] or list(range(2016, 2027))
for y in years:
    f = fires_for(y)
    for lab, ff in [("all", f), ("ge1000ha", f[f["size"] >= 1000])]:
        hA[(y, lab)] = set(gpd.sjoin(da[["DAUID", "geometry"]], ff, predicate="intersects").DAUID)
        hB[(y, lab)] = set(gpd.sjoin(pts, ff, predicate="within").DAUID)
    print(y, flush=True)
if all(y in years for y in range(2023, 2027)):
    for lab in ["all", "ge1000ha"]:
        hA[("2023_2026", lab)] = set().union(*[hA[(y, lab)] for y in range(2023, 2027)]); hB[("2023_2026", lab)] = set().union(*[hB[(y, lab)] for y in range(2023, 2027)])
rows = []
for (y, lab), A in hA.items():
    for scope, S in [("DA intersects fire", A), ("DA point inside fire", hB[(y, lab)])]:
        s = da[da.DAUID.isin(S)]
        for p in ["Canada"] + sorted(s.prov.dropna().unique()):
            q = s if p == "Canada" else s[s.prov == p]
            rows.append(dict(year=y, fires=lab, scope=scope, prov=p, n_da=len(q), dwellings=q.dw_total.sum(),
                             value_avg_cad=(q.dw_total * q.avg_value).sum(), value_median_cad=(q.dw_total * q.median_value).sum(),
                             dwellings_value_from_DA=q.loc[q.avg_value_src == "DA", "dw_total"].sum(),
                             dwellings_value_fallback=q.loc[q.avg_value_src != "DA", "dw_total"].sum()))
o = pd.DataFrame(rows); o.to_csv(os.path.join(P, "exposed_dwelling_value_by_year.csv"), index=False)
c = o[(o.prov == "Canada")].copy(); c["value_avg_bn"] = (c.value_avg_cad / 1e9).round(2); c["value_median_bn"] = (c.value_median_cad / 1e9).round(2)
print(c[["year", "fires", "scope", "n_da", "dwellings", "value_avg_bn", "value_median_bn", "dwellings_value_fallback"]].to_string())
