"""Choose long-record ECCC stations for computed FWI (hourly noon weather) and snow season (daily snow on ground).

Inventory: analysis/climate/raw/eccc/climate_stations.json (MSC GeoMet climate-stations, 8,435 stations,
downloaded 2026-10-21). Climate IDs within 5 km and 100 m elevation are joined into one site (union-find, as in
analysis/climate and analysis/weather). Only sites inside or within 50 km of an eligible forested fma_v2 area
(forest >= 100,000 ha and >= 5% of land, not Nunavut) are kept.
  FWI sites: the union of members' hourly date ranges covers >= 85% of 1953-01-01 to 2026-09-30 and reaches
             2026-06-30 (real per-season completeness is tested after download, in 06).
  Snow sites: the union of daily ranges covers >= 85% of 1955-07-01 to 2026-06-30 and reaches 2026-06-30.
Outputs: work/long_ids.csv (one row per climate ID with site, roles), work/log_04.txt
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
import numpy as np
import pandas as pd

from common import WORK, CLIMATE, CLIMATE_AREAS, areas, log

fh = open(WORK / "log_04.txt", "w")
d = json.load(open(CLIMATE / "raw" / "eccc" / "climate_stations.json"))
p = pd.DataFrame([f["properties"] for f in d["features"]])
p["lon"] = [f["geometry"]["coordinates"][0] if f["geometry"] else np.nan for f in d["features"]]
p["lat"] = [f["geometry"]["coordinates"][1] if f["geometry"] else np.nan for f in d["features"]]
for c in ["HLY_FIRST_DATE", "HLY_LAST_DATE", "DLY_FIRST_DATE", "DLY_LAST_DATE"]:
    p[c] = pd.to_datetime(p[c], errors="coerce")
p["elev"] = pd.to_numeric(p.ELEVATION, errors="coerce")
c = p[(p.HLY_FIRST_DATE.notna() | p.DLY_FIRST_DATE.notna()) & p.lon.notna()].reset_index(drop=True)
lat, lon, el = np.radians(c.lat.values), np.radians(c.lon.values), c.elev.values
parent = np.arange(len(c))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


for i in range(len(c)):
    a = np.sin((lat - lat[i]) / 2) ** 2 + np.cos(lat[i]) * np.cos(lat) * np.sin((lon - lon[i]) / 2) ** 2
    dist = 6371 * 2 * np.arcsin(np.sqrt(a))
    ok = (dist < 5) & ((np.abs(el - el[i]) <= 100) | np.isnan(el)) & (np.arange(len(c)) > i)
    for j in np.where(ok)[0]:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri
c["grp"] = [find(i) for i in range(len(c))]


def cover(m, f, l, S0, S1):
    tot = (S1 - S0).days + 1
    mask = np.zeros(tot, bool)
    for a_, b_ in zip(m[f], m[l]):
        if pd.isna(a_):
            continue
        a = max((a_ - S0).days, 0)
        b = min((b_ - S0).days, tot - 1)
        if b >= a:
            mask[a:b + 1] = True
    return mask.mean()


rows = []
for g, m in c.groupby("grp"):
    rows.append(dict(grp=g, hly_cov=cover(m, "HLY_FIRST_DATE", "HLY_LAST_DATE", pd.Timestamp("1953-01-01"), pd.Timestamp("2026-09-30")),
                     hly_last=m.HLY_LAST_DATE.max(),
                     dly_cov=cover(m, "DLY_FIRST_DATE", "DLY_LAST_DATE", pd.Timestamp("1955-07-01"), pd.Timestamp("2026-06-30")),
                     dly_last=m.DLY_LAST_DATE.max()))
G = pd.DataFrame(rows).set_index("grp")
c = c.join(G, on="grp")
c["fwi_site"] = (c.hly_cov >= 0.85) & (c.hly_last >= "2026-06-30")
c["snow_site"] = (c.dly_cov >= 0.85) & (c.dly_last >= "2026-06-30")
# lead id = longest hourly (FWI) or daily record; site key = lead climate ID
c["hspan"] = (c.HLY_LAST_DATE - c.HLY_FIRST_DATE).dt.days.fillna(0)
c["dspan"] = (c.DLY_LAST_DATE - c.DLY_FIRST_DATE).dt.days.fillna(0)
lead = c.sort_values(["hspan", "dspan"], ascending=False).groupby("grp").head(1).set_index("grp").CLIMATE_IDENTIFIER
c["site"] = c.grp.map(lead)
sel = c[c.fwi_site | c.snow_site].copy()

# near eligible forested areas
A = areas()
Gm = gpd.read_file(CLIMATE_AREAS / "areas_1km.gpkg")
idc = "fma_id" if "fma_id" in Gm.columns else "area_id"
Gm = Gm[Gm[idc].isin(A[A.eligible].fma_id)].to_crs("ESRI:102001")
sites = sel.groupby("site").agg(lat=("lat", "mean"), lon=("lon", "mean")).reset_index()
pts = gpd.GeoSeries(gpd.points_from_xy(sites.lon, sites.lat), crs="EPSG:4326").to_crs("ESRI:102001")
dmin = np.array([Gm.geometry.distance(pt).min() / 1000 for pt in pts])
sites["dist_forest_area_km"] = dmin
sel = sel.merge(sites[["site", "dist_forest_area_km"]], on="site")
sel = sel[sel.dist_forest_area_km <= 50]
cols = ["CLIMATE_IDENTIFIER", "STN_ID", "STATION_NAME", "PROV_STATE_TERR_CODE", "lon", "lat", "elev", "TIMEZONE",
        "HLY_FIRST_DATE", "HLY_LAST_DATE", "DLY_FIRST_DATE", "DLY_LAST_DATE", "site", "hly_cov", "dly_cov",
        "fwi_site", "snow_site", "hspan", "dspan", "dist_forest_area_km"]
sel[cols].rename(columns={"PROV_STATE_TERR_CODE": "prov"}).to_csv(WORK / "long_ids.csv", index=False)
log(f"FWI sites {sel[sel.fwi_site].site.nunique()} ({sel.fwi_site.sum()} IDs); snow sites {sel[sel.snow_site].site.nunique()} "
    f"({sel.snow_site.sum()} IDs)", fh)
log("FWI sites by province " + str(sel[sel.fwi_site].groupby("PROV_STATE_TERR_CODE").site.nunique().to_dict()), fh)
log("snow sites by province " + str(sel[sel.snow_site].groupby("PROV_STATE_TERR_CODE").site.nunique().to_dict()), fh)
