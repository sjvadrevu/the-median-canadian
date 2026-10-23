"""Download ECCC climate-hourly (12:00 LST only) and climate-daily records for the long-record sites (04).

Source: MSC GeoMet OGC API, https://api.weather.gc.ca/collections/climate-hourly/items and
.../climate-daily/items (CSV). Per site, member IDs are anchored on one primary ID (longest record): only IDs within 3 km and 100 m of
it are used, nearest first, each kept only if it adds at least one year not covered by earlier members
(inventory date ranges). FWI sites take daily rain from the hourly IDs first. Daily records 1990-06-01 onward that analysis/climate already downloaded
(analysis/climate/raw/eccc/daily/<id>.csv.gz) are reused; only the earlier part is fetched for those IDs.
Hourly: LOCAL_HOUR=12 (local standard time), 1953-01-01 to 2026-10-20, properties TEMP, RELATIVE_HUMIDITY,
WIND_SPEED, PRECIP_AMOUNT. Daily: 1950-01-01 to 2026-10-20, MAX/MIN_TEMPERATURE, TOTAL_PRECIPITATION,
TOTAL_RAIN, TOTAL_SNOW, SNOW_ON_GROUND.
One request at a time (shared machine). Resumable: existing files are kept.
Outputs: raw/eccc_hourly_noon/<id>.csv.gz, raw/eccc_daily/<id>.csv.gz, work/download_plan.csv, work/log_05.txt
"""
import gzip
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
import requests

from common import RAW, WORK, CLIMATE, log

fh = open(WORK / "log_05.txt", "a")
L = pd.read_csv(WORK / "long_ids.csv", dtype={"CLIMATE_IDENTIFIER": str, "site": str},
                parse_dates=["HLY_FIRST_DATE", "HLY_LAST_DATE", "DLY_FIRST_DATE", "DLY_LAST_DATE"])


ANCHOR_KM = 3.0


def chain(m, f, l, S0, S1, primary=None, seed=()):
    """Anchored member selection. The 5 km union-find of 04 can chain a whole city's stations into one group,
    so members are chosen relative to one primary ID (the longest record unless given): only IDs within
    ANCHOR_KM of the primary and 100 m of its elevation qualify, taken nearest first (then longest), each kept
    only if it adds >= 365 days not covered by IDs already kept. `seed` IDs are kept first."""
    m = m[m[f].notna()].copy()
    if m.empty:
        return []
    m["span"] = (m[l].clip(upper=S1) - m[f].clip(lower=S0)).dt.days
    p = m.loc[m.span.idxmax()] if primary is None else m[m.CLIMATE_IDENTIFIER == primary].iloc[0] if (m.CLIMATE_IDENTIFIER == primary).any() else None
    if p is None:
        p = L[L.CLIMATE_IDENTIFIER == primary].iloc[0]
    la, lo = np.radians(p.lat), np.radians(p.lon)
    dd = 6371 * 2 * np.arcsin(np.sqrt(np.sin((np.radians(m.lat) - la) / 2) ** 2 +
                                      np.cos(la) * np.cos(np.radians(m.lat)) * np.sin((np.radians(m.lon) - lo) / 2) ** 2))
    m["dist"] = dd
    m = m[(m.dist <= ANCHOR_KM) & ((m.elev - p.elev).abs().fillna(0) <= 100)]
    m["seed"] = m.CLIMATE_IDENTIFIER.isin(seed)
    m = m.sort_values(["seed", "dist", "span"], ascending=[False, True, False])
    tot = (S1 - S0).days + 1
    mask = np.zeros(tot, bool)
    keep = []
    for r in m.itertuples():
        a = max((getattr(r, f) - S0).days, 0)
        b = min((getattr(r, l) - S0).days, tot - 1)
        if b < a:
            continue
        if (~mask[a:b + 1]).sum() >= 365:
            keep.append(r.CLIMATE_IDENTIFIER)
            mask[a:b + 1] = True
    return keep


plan = []
H0, H1 = pd.Timestamp("1953-01-01"), pd.Timestamp("2026-09-30")
D0 = pd.Timestamp("1950-01-01")
for site, m in L.groupby("site"):
    if m.fwi_site.any():
        hk = chain(m, "HLY_FIRST_DATE", "HLY_LAST_DATE", H0, H1)
        for cid in hk:
            plan.append(dict(site=site, cid=cid, kind="hourly", role="fwi"))
        # FWI rain: daily records of the same IDs first, then other IDs within 3 km of the hourly primary
        for cid in chain(m, "DLY_FIRST_DATE", "DLY_LAST_DATE", D0, H1, primary=hk[0] if hk else None, seed=hk):
            plan.append(dict(site=site, cid=cid, kind="daily", role="fwi"))
    if m.snow_site.any():
        for cid in chain(m, "DLY_FIRST_DATE", "DLY_LAST_DATE", D0, H1):
            plan.append(dict(site=site, cid=cid, kind="daily", role="snow"))
PL = pd.DataFrame(plan)
PL.to_csv(WORK / "download_plan.csv", index=False)
log(f"plan: hourly IDs {(PL.kind == 'hourly').sum()} for {PL[PL.kind == 'hourly'].site.nunique()} sites; "
    f"daily IDs {(PL.kind == 'daily').sum()} for {PL[PL.kind == 'daily'].site.nunique()} sites", fh)

API = "https://api.weather.gc.ca/collections/{}/items"
sess = requests.Session()
END = "2026-10-20"


def fetch(coll, params, out):
    parts, off, lim = [], 0, 10000
    while True:
        q = dict(params, f="csv", limit=lim, offset=off)
        for attempt in range(6):
            try:
                r = sess.get(API.format(coll), params=q, timeout=240)
                if r.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(5 * (attempt + 1))
        else:
            return "failed", off
        txt = r.text
        n = txt.count("\n") - 1
        parts.append(txt if off == 0 else txt.split("\n", 1)[1] if "\n" in txt else "")
        if n < lim:
            break
        off += lim
    with gzip.open(out, "wt") as f:
        f.write("".join(parts))
    return "ok", sum(p.count("\n") for p in parts) - 1


HD = RAW / "eccc_hourly_noon"
DD = RAW / "eccc_daily"
HD.mkdir(parents=True, exist_ok=True)
DD.mkdir(parents=True, exist_ok=True)
OLD = CLIMATE / "raw" / "eccc" / "daily"
t0 = time.time()
PLd = PL.drop_duplicates(["cid", "kind"])
for k, r in enumerate(PLd.itertuples()):
    if r.kind == "hourly":
        out = HD / f"{r.cid}.csv.gz"
        if out.exists():
            continue
        st, n = fetch("climate-hourly", dict(CLIMATE_IDENTIFIER=r.cid, LOCAL_HOUR=12, sortby="LOCAL_DATE",
                                             datetime=f"1953-01-01/{END}",
                                             properties="CLIMATE_IDENTIFIER,LOCAL_DATE,TEMP,RELATIVE_HUMIDITY,WIND_SPEED,PRECIP_AMOUNT"), out)
    else:
        out = DD / f"{r.cid}.csv.gz"
        if out.exists():
            continue
        end = "1990-05-31" if (OLD / f"{r.cid}.csv.gz").exists() else END
        st, n = fetch("climate-daily", dict(CLIMATE_IDENTIFIER=r.cid, sortby="LOCAL_DATE", datetime=f"1950-01-01/{end}",
                                            properties="CLIMATE_IDENTIFIER,LOCAL_DATE,MAX_TEMPERATURE,MIN_TEMPERATURE,"
                                                       "TOTAL_PRECIPITATION,TOTAL_RAIN,TOTAL_SNOW,SNOW_ON_GROUND"), out)
    log(f"{k}/{len(PLd)} {r.kind} {r.cid} {st} {n} {time.time() - t0:.0f}s", fh)
log("done", fh)
