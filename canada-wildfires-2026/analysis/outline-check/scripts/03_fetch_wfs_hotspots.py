"""Step 3: download the CWFIS WFS hotspot archive (public:hotspots) for 2026, one request per
UTC day, Canada bounding box only, selected fields, CSV. Reason: the daily CSV files used in
cwfis_hotspots_2026_canada.csv.gz lack most VIIRS records for 2026-06-29..07-02 and some other
detections (e.g. 2026-05-07 in southern MB); the WFS archive is the same publisher's complete
record and includes a third sensor (Sentinel-3 SLSTR, source Eumetsat).
Output: data/fire/raw/hotspots_wfs_2026/YYYYMMDD.csv (one per day) + fetch.log
"""
import requests, time, os, datetime as dt, sys
B = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
D = f"{B}/data/fire/raw/hotspots_wfs_2026"
U = "https://cwfis.cfs.nrcan.gc.ca/geoserver/public/wfs"
log = open(f"{D}/fetch.log", "a")
day = dt.date(2026, 1, 1)
end = dt.date(2026, 10, 21)
while day <= end:
    f = f"{D}/{day:%Y%m%d}.csv"
    if os.path.exists(f) and os.path.getsize(f) > 0:
        day += dt.timedelta(days=1); continue
    nxt = day + dt.timedelta(days=1)
    p = dict(service="WFS", version="2.0.0", request="GetFeature", typeNames="public:hotspots",
             outputFormat="csv", count=200000,
             propertyName="lat,lon,rep_date,source,sensor,satellite,agency,uid",
             CQL_FILTER=(f"rep_date >= '{day}T00:00:00Z' AND rep_date < '{nxt}T00:00:00Z' "
                         "AND lat > 41.5 AND lat < 84 AND lon > -141.1 AND lon < -52"))
    for attempt in range(5):
        try:
            r = requests.get(U, params=p, timeout=600)
            if r.status_code == 200 and r.text.startswith("FID"):
                break
            msg = f"{day} attempt {attempt} status {r.status_code} {r.text[:120]!r}"
        except Exception as e:
            msg = f"{day} attempt {attempt} error {e}"
        print(msg, file=log, flush=True); time.sleep(10 * (attempt + 1))
    else:
        print(f"{day} FAILED", file=log, flush=True); day = nxt; continue
    open(f, "w").write(r.text)
    n = r.text.count("\n") - 1
    print(f"{day} rows {n}", file=log, flush=True)
    if n >= 199999:
        print(f"{day} WARNING page limit reached", file=log, flush=True)
    day = nxt
print("done", file=log, flush=True)
