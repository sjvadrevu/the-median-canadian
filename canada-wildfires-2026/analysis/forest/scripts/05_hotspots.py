"""Analysis 5: timing of the 2026 season from CWFIS satellite hotspots.

Deduplication rule (primary): one detection per sensor (VIIRS-I or MODIS) per 1 km x 1 km cell of a
grid in ESRI:102001 (Canada Albers equal-area, origin 0,0) per UTC calendar day of rep_date.
This removes the same pixel reported by several feeds (NASA, NASA_w, NASA_z, HMS) and repeat overpasses
on the same day. Detections from VIIRS-I and MODIS in the same cell-day are kept as separate detections
(one per sensor). Sensitivity versions: VIIRS-I only, and one per cell-day across sensors.
Province: point-in-polygon against StatCan 2021 provinces (not the file's prov column; agreement reported).
Weeks: ISO weeks, Monday to Sunday (UTC dates).
Input (rebuild 2026-10-21): the complete CWFIS WFS public:hotspots archive for 2026, one CSV per UTC day
(data/fire/raw/hotspots_wfs_2026/, fetched by analysis/outline-check/scripts/03_fetch_wfs_hotspots.py). It replaces
cwfis_hotspots_2026_canada.csv.gz, which lacks most VIIRS records for 2026-06-29..07-02. The archive also carries a
third sensor, Sentinel-3 SLSTR; under the same rule (one per sensor) SLSTR detections count as their own sensor.
A sensitivity without SLSTR (VIIRS-I and MODIS, the two sensors of the old file) is reported. Days after
2026-10-20 (the partial 10-21 file) are dropped so the season ends on the same date as before.
Outputs: weekly_hotspots.csv, hotspot_peak5.csv, hotspot_dedup_summary.csv
"""
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
from common import HOTSPOTS_WFS, PROV, OUT, EA

files = sorted(glob.glob(str(HOTSPOTS_WFS / "2026*.csv")))
h = pd.concat([pd.read_csv(f, usecols=["lat", "lon", "rep_date", "source", "sensor", "agency"]) for f in files],
              ignore_index=True)
n_files, n_all = len(files), len(h)
h = h[h.rep_date.astype(str).str[:10] <= "2026-10-20"].reset_index(drop=True)
h["prov"] = h["agency"]                                   # WFS 'agency' = province/state code of the detection
n_raw = len(h)
g = gpd.GeoDataFrame(h, geometry=gpd.points_from_xy(h.lon, h.lat), crs="EPSG:4326").to_crs(EA)
h["x"] = g.geometry.x.values
h["y"] = g.geometry.y.values
h["cx"] = np.floor(h.x / 1000).astype("int64")
h["cy"] = np.floor(h.y / 1000).astype("int64")
h["day"] = pd.to_datetime(h.rep_date).dt.normalize()

pv = gpd.read_file(PROV).to_crs(EA)
pcol = [c for c in pv.columns if c.upper() in ("PREABBR", "PRABBR", "PRUID", "PRENAME")]
print("province columns", pv.columns.tolist())
ABBR = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON", "46": "MB",
        "47": "SK", "48": "AB", "59": "BC", "60": "YT", "61": "NT", "62": "NU"}
pv["P"] = pv["PRUID"].astype(str).map(ABBR)
j = gpd.sjoin(g[["geometry"]], pv[["P", "geometry"]], how="left", predicate="within")
j = j[~j.index.duplicated()]
h["P"] = j["P"].reindex(h.index).values
agree = (h.P == h.prov).mean()
h["P"] = h["P"].fillna("outside")

d_sensor = h.drop_duplicates(["sensor", "cx", "cy", "day"])
d_viirs = h[h.sensor == "VIIRS-I"].drop_duplicates(["cx", "cy", "day"])
d_any = h.drop_duplicates(["cx", "cy", "day"])
d_nosl = d_sensor[d_sensor.sensor != "SLSTR"]

summ = pd.DataFrame([
    dict(version=f"raw rows, WFS archive ({n_files} daily files, {n_all} rows; to 2026-10-20 UTC)", n=n_raw),
    dict(version="primary: one per sensor per 1 km cell per UTC day", n=len(d_sensor)),
    dict(version="VIIRS-I only, one per 1 km cell per UTC day", n=len(d_viirs)),
    dict(version="any sensor, one per 1 km cell per UTC day", n=len(d_any)),
    dict(version="primary rule without SLSTR (VIIRS-I + MODIS only, the old file's sensors)", n=len(d_nosl)),
    dict(version="primary rule, inside province polygons", n=int((d_sensor.P != "outside").sum())),
    dict(version="share of raw rows where StatCan province = file prov column", n=round(agree, 4)),
])
summ.to_csv(OUT / "hotspot_dedup_summary.csv", index=False)
print(summ.to_string())


def weekly(d):
    wk = d.day - pd.to_timedelta(d.day.dt.weekday, unit="D")
    t = pd.crosstab(wk, d.P)
    t["CAN"] = t.drop(columns=[c for c in t.columns if c == "outside"]).sum(axis=1)
    full = pd.date_range(t.index.min(), t.index.max(), freq="7D")
    return t.reindex(full, fill_value=0)


w = weekly(d_sensor)
w.index.name = "week_start"
cols = ["CAN"] + [p for p in ["BC", "AB", "SK", "MB", "ON", "QC", "NB", "NS", "PE", "NL", "YT", "NT", "NU"] if p in w.columns]
w = w[cols + [c for c in w.columns if c == "outside"]]
out = w.reset_index()
out.insert(1, "week_end", out.week_start + pd.Timedelta(days=6))
out.insert(2, "iso_week", out.week_start.dt.isocalendar().week.values)
wv = weekly(d_viirs)
wa = weekly(d_any)
wn = weekly(d_nosl)
out["CAN_viirs_only"] = wv["CAN"].reindex(w.index, fill_value=0).values
out["CAN_any_sensor"] = wa["CAN"].reindex(w.index, fill_value=0).values
out["CAN_no_slstr"] = wn["CAN"].reindex(w.index, fill_value=0).values
out["week_start"] = out.week_start.dt.date
out["week_end"] = out.week_end.dt.date
out.to_csv(OUT / "weekly_hotspots.csv", index=False)


def peak5(series):
    s = series.astype(float)
    roll = s.rolling(5).sum()
    end = roll.idxmax()
    i = list(s.index).index(end)
    start = s.index[i - 4]
    return start, end + pd.Timedelta(days=6), roll.max(), s.sum()


rows = []
alt = {"CAN_viirs_only": wv, "CAN_any_sensor": wa, "CAN_no_slstr": wn}
for c in cols + list(alt):
    s = w[c] if c in w.columns else alt[c]["CAN"]
    s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="7D"), fill_value=0)
    if s.sum() == 0:
        continue
    a, b, top, tot = peak5(s)
    pk = s.idxmax()
    rows.append(dict(series=c, total_detections=int(tot), peak5_start=a.date(), peak5_end=b.date(),
                     peak5_detections=int(top), peak5_share=top / tot,
                     busiest_week_start=pk.date(), busiest_week_detections=int(s.max())))
pk = pd.DataFrame(rows)
pk.to_csv(OUT / "hotspot_peak5.csv", index=False)
pd.set_option("display.width", 250)
print(pk.round(3).to_string())
first = d_sensor.day.min().date(), d_sensor.day.max().date()
print("dates", first)
print("monthly CAN", d_sensor[d_sensor.P != "outside"].groupby(d_sensor.day.dt.month).size().to_dict())
print("by sensor (primary, in provinces)", d_sensor[d_sensor.P != "outside"].sensor.value_counts().to_dict())
