"""Step 5: download ECCC climate observations (MSC GeoMet api.weather.gc.ca) for stations near
CFB Wainwright. Daily: full record. Hourly: full record for WAINWRIGHT CFB AIRFIELD 21 (301S001),
Oct 2026 for the others with hourly data. Output raw/eccc/{daily,hourly}/<ID>.csv.gz.
Single-threaded, resumable.
"""
import gzip, time, requests, os
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
S = requests.Session()
DAILY = ["301S001", "3012515", "3013959", "3013961", "3013958", "3011887", "3014600", "3016GF0", "3015401"]
HOURLY = {"301S001": "1995-08-01/2026-10-22", "3013959": "2026-10-01/2026-10-22", "3013958": "2026-10-01/2026-10-22",
          "3011887": "2026-10-01/2026-10-22", "3016GF0": "2026-10-01/2026-10-22", "3015401": "2026-10-01/2026-10-22"}
def pull(coll, cid, dt, out):
    if os.path.exists(out):
        return "kept"
    parts, off, lim = [], 0, 10000
    while True:
        p = dict(f="csv", limit=lim, offset=off, CLIMATE_IDENTIFIER=cid, sortby="UTC_DATE" if coll == "climate-hourly" else "LOCAL_DATE", datetime=dt)
        for a in range(6):
            try:
                r = S.get(f"https://api.weather.gc.ca/collections/{coll}/items", params=p, timeout=300)
                if r.status_code == 200: break
            except requests.RequestException: pass
            time.sleep(5 * (a + 1))
        else:
            return f"failed at {off}"
        t = r.text; n = t.count("\n") - 1
        parts.append(t if off == 0 else t.split("\n", 1)[1])
        if n < lim: break
        off += lim
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with gzip.open(out, "wt") as f: f.write("".join(parts))
    return sum(x.count("\n") for x in parts) - 1
for cid in DAILY:
    print("daily", cid, pull("climate-daily", cid, "1950-01-01/2026-10-22", f"{O}/raw/eccc/daily/{cid}.csv.gz"), flush=True)
for cid, dt in HOURLY.items():
    print("hourly", cid, pull("climate-hourly", cid, dt, f"{O}/raw/eccc/hourly/{cid}.csv.gz"), flush=True)
