"""Choose ECCC climate stations to download (MSC GeoMet climate-stations inventory).

Same approach as analysis/weather: station IDs that replace each other are joined into one site when
they are within THREAD_KM (5 km) of each other; here also within 100 m of elevation (snow depends on
elevation). A site is a download candidate when the union of its members' daily-record date ranges
covers at least 85% of 1990-06-01 to 2026-06-30 and some member reports to at least 2026-06-30.
The real consistency rule (per variable, per year) is applied after download in 02/04.

Input: raw/eccc/climate_stations.json (downloaded with
  https://api.weather.gc.ca/collections/climate-stations/items?f=json&limit=10000)
Output: work/station_ids.csv (one row per climate ID with its site), work/log_01.txt
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd

from common import RAW, WORK, THREAD_KM, THREAD_DZ, log

fh = open(WORK / "log_01.txt", "w")
d = json.load(open(RAW / "eccc" / "climate_stations.json"))
p = pd.DataFrame([f["properties"] for f in d["features"]])
p["lon"] = [f["geometry"]["coordinates"][0] if f["geometry"] else np.nan for f in d["features"]]
p["lat"] = [f["geometry"]["coordinates"][1] if f["geometry"] else np.nan for f in d["features"]]
p["f"] = pd.to_datetime(p.DLY_FIRST_DATE)
p["l"] = pd.to_datetime(p.DLY_LAST_DATE)
p["elev"] = pd.to_numeric(p.ELEVATION, errors="coerce")
log(f"inventory {len(p)} stations, with daily data {p.f.notna().sum()}", fh)
S0, S1 = pd.Timestamp("1990-06-01"), pd.Timestamp("2026-06-30")
c = p[p.f.notna() & (p.l >= S0) & (p.f <= S1) & p.lon.notna()].reset_index(drop=True)
log(f"daily range overlapping {S0.date()}..{S1.date()}: {len(c)}", fh)

# join IDs: union-find on pairs within THREAD_KM and THREAD_DZ
lat = np.radians(c.lat.to_numpy(float))
lon = np.radians(c.lon.to_numpy(float))
el = c.elev.to_numpy(float)
parent = np.arange(len(c))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


for i in range(len(c)):
    a = np.sin((lat - lat[i]) / 2) ** 2 + np.cos(lat[i]) * np.cos(lat) * np.sin((lon - lon[i]) / 2) ** 2
    dist = 6371 * 2 * np.arcsin(np.sqrt(a))
    dz = np.abs(el - el[i])
    ok = (dist < THREAD_KM) & ((dz <= THREAD_DZ) | np.isnan(dz)) & (np.arange(len(c)) > i)
    for j in np.where(ok)[0]:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri
c["grp"] = [find(i) for i in range(len(c))]
c["span_days"] = (c[["l"]].clip(upper=S1).l - c[["f"]].clip(lower=S0).f).dt.days + 1

# union coverage of the target window per group
tot = (S1 - S0).days + 1
cov = {}
for g, m in c.groupby("grp"):
    mask = np.zeros(tot, bool)
    for r in m.itertuples():
        a = max((r.f - S0).days, 0)
        b = min((r.l - S0).days, tot - 1)
        mask[a:b + 1] = True
    cov[g] = mask.mean()
c["site_span_cov"] = c.grp.map(cov)
c["site_last"] = c.groupby("grp").l.transform("max")
# lead ID: longest daily record inside the window; site key = its climate ID
lead = c.sort_values("span_days", ascending=False).groupby("grp").head(1).set_index("grp")["CLIMATE_IDENTIFIER"]
c["site"] = c.grp.map(lead)
sel = c[(c.site_span_cov >= 0.85) & (c.site_last >= S1)].copy()
log(f"sites {c.site.nunique()}; candidate sites {sel.site.nunique()} with {len(sel)} IDs", fh)
log("candidate sites by province: " + str(sel.groupby("PROV_STATE_TERR_CODE").site.nunique().to_dict()), fh)
cols = ["CLIMATE_IDENTIFIER", "STN_ID", "STATION_NAME", "PROV_STATE_TERR_CODE", "lon", "lat", "elev",
        "DLY_FIRST_DATE", "DLY_LAST_DATE", "site", "site_span_cov", "span_days"]
sel[cols].rename(columns={"PROV_STATE_TERR_CODE": "prov"}).to_csv(WORK / "station_ids.csv", index=False)
