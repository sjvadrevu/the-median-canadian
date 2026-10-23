"""Per site and fire year: snow, spring heat and rain, earlier dryness (ECCC daily climate data).

Sites: work/station_ids.csv (01). For each day and each variable the value comes from the member ID
with the longest daily record that reported that variable that day (other IDs fill gaps), as in
analysis/weather. Fire year y uses data from 1 Jun y-1 to 31 Jul y.

Variables per site-year (NaN when the coverage test fails):
  snowfall_cm         total snowfall (TOTAL_SNOW) 1 Nov y-1 - 30 Apr y; <= 10% of days missing
  snow_cover_days     days with snow on ground >= 1 cm, 1 Nov - 30 Apr; <= 10% missing (count scaled
                      to the full window)
  max_snow_depth_cm   maximum snow on ground 1 Nov - 30 Apr; <= 20% missing
  melt_doy            date snow cover ended: the day after the last day (1 Nov y-1 - 31 Jul y) with snow
                      on ground >= 1 cm, as day of year y (1 = 1 Jan; earlier dates are <= 0). Needs
                      <= 15% missing 1 Feb - 30 Jun and >= 5 reports in the 14 days after the last snow
                      day. NaN when there was no snow cover all winter (no_snow_winter = 1).
  t_amj               mean of daily (max+min)/2, Apr-Jun y (each month <= 5 days missing)
  p_amj, p_jja_prev, p_son_prev, p_ndjfm, p_12m       precipitation totals (mm): Apr-Jun y, Jun-Aug y-1,
                      Sep-Nov y-1, Nov y-1 - Mar y, Jul y-1 - Jun y; every month needs <= 3 missing days
Monthly precipitation and temperature per site go to work/site_month.csv for the normals and the
months-since-wet count (05).
Outputs: work/site_year.csv, work/site_month.csv, work/site_meta.csv
"""
import gzip
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd

from common import RAW, WORK, YEARS, log

D = RAW / "eccc" / "daily"
ids = pd.read_csv(WORK / "station_ids.csv", dtype={"CLIMATE_IDENTIFIER": str, "site": str})
ids = ids.sort_values(["site", "span_days"], ascending=[True, False])
USE = ["LOCAL_DATE", "MAX_TEMPERATURE", "MIN_TEMPERATURE", "TOTAL_PRECIPITATION", "TOTAL_SNOW", "SNOW_ON_GROUND"]


def load_site(members):
    fr = []
    for k, cid in enumerate(members):
        f = D / f"{cid}.csv.gz"
        if not f.exists():
            continue
        d = pd.read_csv(f, usecols=USE)
        if d.empty:
            continue
        d["pri"] = k
        d["src"] = cid
        fr.append(d)
    if not fr:
        return None
    d = pd.concat(fr).sort_values(["LOCAL_DATE", "pri"])
    d["date"] = pd.to_datetime(d.LOCAL_DATE.str[:10])
    g = d.groupby("date")[USE[1:]].first()          # first non-null per column = per-variable fallback
    lead_share = (d.drop_duplicates("date").src == members[0]).mean()
    full = pd.date_range("1990-06-01", g.index.max())
    g = g.reindex(full)
    g.columns = ["tx", "tn", "p", "sf", "sog"]
    g["tm"] = (g.tx + g.tn) / 2
    return g, lead_share


def monthly(g):
    mo = g.index.to_period("M")
    nd = g.groupby(mo).size()
    p = g.p.groupby(mo).sum(min_count=1)
    pmiss = nd - g.p.groupby(mo).count()
    t = g.tm.groupby(mo).mean()
    tmiss = nd - g.tm.groupby(mo).count()
    M = pd.DataFrame({"p": p.where(pmiss <= 3), "t": t.where(tmiss <= 5), "ndays": nd})
    # current month is partial: drop it
    last = g.index.max()
    if last != last + pd.offsets.MonthEnd(0):
        M = M.iloc[:-1]
    return M


def win(g, a, b):
    return g.loc[a:b]


def site_years(g, M):
    out = []
    Mi = M.copy()
    Mi.index = Mi.index.to_timestamp()
    for y in YEARS:
        r = {"fire_year": y}
        w = win(g, f"{y-1}-11-01", f"{y}-04-30")
        n = len(w)
        if n < 181:
            out.append(r)
            continue
        sf, sog = w.sf, w.sog
        if sf.isna().mean() <= 0.10:
            r["snowfall_cm"] = sf.sum()
        if sog.isna().mean() <= 0.10:
            r["snow_cover_days"] = (sog >= 1).sum() / sog.notna().sum() * n
        if sog.isna().mean() <= 0.20:
            r["max_snow_depth_cm"] = sog.max()
        # melt date
        ww = win(g, f"{y-1}-11-01", f"{y}-07-31").sog
        fj = win(g, f"{y}-02-01", f"{y}-06-30").sog
        if len(ww) >= 273 and fj.isna().mean() <= 0.15:
            snow = ww[ww >= 1]
            if len(snow) == 0:
                r["no_snow_winter"] = 1
            else:
                last = snow.index.max()
                after = ww.loc[last + pd.Timedelta(days=1): last + pd.Timedelta(days=14)]
                if after.notna().sum() >= 5 or last >= pd.Timestamp(f"{y}-07-31"):
                    r["melt_doy"] = (last + pd.Timedelta(days=1) - pd.Timestamp(f"{y}-01-01")).days + 1
                    r["no_snow_winter"] = 0
        # temperature and precipitation from valid months

        def msum(col, months, fn):
            v = [Mi[col].get(pd.Timestamp(year=yy, month=mm, day=1), np.nan) for yy, mm in months]
            return np.nan if np.any(np.isnan(v)) else fn(v)

        r["t_amj"] = msum("t", [(y, 4), (y, 5), (y, 6)], np.mean)
        r["p_amj"] = msum("p", [(y, 4), (y, 5), (y, 6)], np.sum)
        r["p_jja_prev"] = msum("p", [(y - 1, 6), (y - 1, 7), (y - 1, 8)], np.sum)
        r["p_son_prev"] = msum("p", [(y - 1, 9), (y - 1, 10), (y - 1, 11)], np.sum)
        r["p_ndjfm"] = msum("p", [(y - 1, 11), (y - 1, 12), (y, 1), (y, 2), (y, 3)], np.sum)
        r["p_12m"] = msum("p", [(y - 1, mm) for mm in range(7, 13)] + [(y, mm) for mm in range(1, 7)], np.sum)
        out.append(r)
    return pd.DataFrame(out)


def run(site):
    members = list(ids[ids.site == site].CLIMATE_IDENTIFIER)
    res = load_site(members)
    if res is None:
        return site, None, None, None
    g, lead_share = res
    M = monthly(g)
    Y = site_years(g, M)
    Y.insert(0, "site", site)
    M = M.reset_index().rename(columns={"index": "month"})
    M["month"] = M["month"].astype(str)
    M.insert(0, "site", site)
    return site, Y, M, lead_share


if __name__ == "__main__":
    fh = open(WORK / "log_04.txt", "w")
    sites = ids.site.unique()
    Ys, Ms, meta = [], [], []
    with ProcessPoolExecutor(4) as ex:
        for k, (s, Y, M, ls) in enumerate(ex.map(run, sites, chunksize=4)):
            if Y is not None:
                Ys.append(Y)
                Ms.append(M)
                meta.append((s, ls))
            if k % 100 == 0:
                log(f"{k} sites", fh)
    Y = pd.concat(Ys, ignore_index=True)
    M = pd.concat(Ms, ignore_index=True)
    Y.to_csv(WORK / "site_year.csv", index=False)
    M.to_csv(WORK / "site_month.csv", index=False)
    first = ids.groupby("site").first()
    sm = pd.DataFrame(meta, columns=["site", "share_days_from_lead_id"]).set_index("site")
    sm = sm.join(first[["STATION_NAME", "prov", "lon", "lat", "elev"]])
    sm["n_ids"] = ids.groupby("site").size()
    sm["member_ids"] = ids.groupby("site").CLIMATE_IDENTIFIER.apply(lambda s: ";".join(s))
    sm.to_csv(WORK / "site_meta.csv")
    log(f"site-years {len(Y)}; non-missing counts:\n{Y.notna().sum().to_string()}", fh)
