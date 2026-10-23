"""Snow season at long-record ECCC stations, winters 1955-56 to 2025-26: snow-cover days and spring melt date.

Data: climate-daily SNOW_ON_GROUND (cm) per site (04 snow sites, 05 downloads; member IDs longest first, other
IDs fill gaps; analysis/climate daily files reused from 1990-06).
Winter y = Aug 1 of y-1 to Jul 31 of y.
  snow_cover_days  days with snow on ground >= 1 cm, Oct 1 to Jun 30; <= 20% of days missing (count scaled to
                   the full window)
  melt_doy         end of continuous spring snow cover: the first day after Jan 31 that starts a run of 14
                   consecutive reported snow-free days (< 1 cm) with no snow-covered day in it; day of year.
                   Needs <= 20% missing Feb 1 to Jun 30. Winters with no snow cover after Jan 31 get melt_doy
                   missing (counted).
  last_snow_doy    day after the last day with snow on ground >= 1 cm between Jan 1 and Jul 31 (alternative).
Quality control: a winter with 0 snow-cover days at a site whose median is >= 60 days is set missing (zeros
recorded for missing reports); melt dates more than 45 days from the site median are set missing.
Per site and day the first reported value among its anchored IDs is used (the snow-role IDs, then the IDs of the
FWI site, all within 3 km of the primary). Many airports stopped reporting snow on ground after 2003-2013, which
limits the long-record set.
Fixed station set: sites with a usual (median 1961-1990) snow cover of >= 30 days, valid winters in >= 45 of
71 (1956-2026), >= 18 of 30 in 1961-1990 and >= 6 of 11 in 2016-2026, for each variable separately.
Series: mean over fixed sites of the anomaly vs the site's 1961-1990 mean (Canada and regions); trends OLS
(AR1-adjusted) and Theil-Sen per decade; 2016-2026 minus 1961-1990 (Welch); ranks of winters 2023-2026.
Outputs: work/snow_site_year.csv, snow_sites.csv, snow_series.csv, snow_trends.csv, snow_site_trends.csv,
         snow_ranks_2023_2026.csv, snow_trends_split_periods.csv, work/log_11.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from scipy import stats

from common import WORK, OUT, RAW, CLIMATE, REGION, REGIONS, log, trend_stats

def safe_csv(f, **kw):
    """Read a gzip CSV; empty downloads (no rows for that ID and period) return an empty frame."""
    try:
        return pd.read_csv(f, **kw)
    except (pd.errors.EmptyDataError, ValueError):
        return pd.DataFrame()


fh = open(WORK / "log_11.txt", "w")
MISS = 0.20     # maximum share of missing days in a window
PL = pd.read_csv(WORK / "download_plan.csv", dtype={"site": str, "cid": str})
L = pd.read_csv(WORK / "long_ids.csv", dtype={"CLIMATE_IDENTIFIER": str, "site": str})
DD, OLD = RAW / "eccc_daily", CLIMATE / "raw" / "eccc" / "daily"
ssites = sorted(L[L.snow_site].site.unique())
import os
if os.environ.get("TEST_SITES"):
    ssites = ssites[:int(os.environ["TEST_SITES"])]   # quick test only
# site name and coordinates = the primary (first planned) ID, not the 5 km group
prim = PL[(PL.kind == "daily") & (PL.role == "snow")].drop_duplicates("site").set_index("site").cid
LL = L.drop_duplicates("CLIMATE_IDENTIFIER").set_index("CLIMATE_IDENTIFIER")
meta = pd.DataFrame({"site": prim.index, "primary_id": prim.values})
for c_, k_ in [("name", "STATION_NAME"), ("prov", "prov"), ("lat", "lat"), ("lon", "lon"), ("elev", "elev")]:
    meta[c_] = LL.loc[meta.primary_id, k_].values
rows = []
for s in ssites:
    g_ = PL[(PL.site == s) & (PL.kind == "daily")].sort_values("role", ascending=False)   # snow-role IDs first, then FWI-site IDs
    cids = list(dict.fromkeys(g_.cid))
    fr = []
    for k, c in enumerate(cids):
        for f in (DD / f"{c}.csv.gz", OLD / f"{c}.csv.gz"):
            if f.exists():
                d = safe_csv(f, usecols=lambda x: x in ("LOCAL_DATE", "SNOW_ON_GROUND"))
                if not d.empty and "SNOW_ON_GROUND" in d:
                    d["pri"] = k
                    fr.append(d)
    if not fr:
        continue
    d = pd.concat(fr)
    d["date"] = pd.to_datetime(d.LOCAL_DATE.str[:10])
    sog = d.sort_values(["date", "pri"]).groupby("date").SNOW_ON_GROUND.first().reindex(pd.date_range("1955-08-01", "2026-07-31"))
    for y in range(1956, 2027):
        w = sog.loc[f"{y}-10-01":f"{y}-06-30".replace(str(y), str(y), 1)] if False else sog.loc[f"{y - 1}-10-01":f"{y}-06-30"]
        nmiss = w.isna().mean()
        scd = (w >= 1).sum() / max(w.notna().sum(), 1) * len(w) if nmiss <= MISS else np.nan
        sp = sog.loc[f"{y}-02-01":f"{y}-07-31"]
        miss_sp = sp.loc[:f"{y}-06-30"].isna().mean()
        melt = np.nan
        nosnow = False
        if miss_sp <= MISS:
            cov = (sp >= 1).astype(float).where(sp.notna())
            free = (sp < 1) & sp.notna()
            if not (cov == 1).any():
                nosnow = True
            else:
                # first day starting 14 consecutive reported snow-free days
                fv = free.values.astype(int)
                run = np.convolve(fv, np.ones(14, int), "valid")
                cand = np.where(run == 14)[0]
                if len(cand):
                    first = sp.index[cand[0]]
                    if first > sp.index[0] or (cov.iloc[0] == 1):
                        melt = first.dayofyear
        ls = sog.loc[f"{y}-01-01":f"{y}-07-31"]
        last = np.nan
        if ls.loc[:f"{y}-06-30"].isna().mean() <= MISS and (ls >= 1).any():
            last = (ls[ls >= 1].index.max() + pd.Timedelta(days=1)).dayofyear
        rows.append(dict(site=s, year=y, snow_cover_days=scd, melt_doy=melt, last_snow_doy=last, no_snow_after_jan=nosnow,
                         miss_oct_jun=nmiss, miss_feb_jun=miss_sp))
SY = pd.DataFrame(rows)
med = SY[SY.year.between(1961, 1990)].groupby("site").snow_cover_days.median()
SY["usual_scd"] = SY.site.map(med)
bad0 = (SY.snow_cover_days == 0) & (SY.usual_scd >= 60)
SY.loc[bad0, ["snow_cover_days", "melt_doy", "last_snow_doy"]] = np.nan
for v in ["melt_doy", "last_snow_doy"]:
    m = SY.groupby("site")[v].transform("median")
    out = (SY[v] - m).abs() > 45
    log(f"QC {v}: {int(out.sum())} melt dates > 45 days from site median set missing", fh)
    SY.loc[out, v] = np.nan
log(f"QC: {int(bad0.sum())} zero-snow winters at snowy sites set missing", fh)
SY.to_csv(WORK / "snow_site_year.csv", index=False)

M = meta[meta.site.isin(SY.site.unique())].copy()
M["region"] = M.prov.map(REGION)
M["usual_scd"] = M.site.map(med)
fixed = {}
for v in ["snow_cover_days", "melt_doy", "last_snow_doy"]:
    ok = SY[SY[v].notna()]
    n_all = ok.groupby("site").year.count()
    n_n = ok[ok.year.between(1961, 1990)].groupby("site").year.count()
    n_r = ok[ok.year.between(2016, 2026)].groupby("site").year.count()
    fixed[v] = [s for s in n_all.index if n_all[s] >= 45 and n_n.get(s, 0) >= 18 and n_r.get(s, 0) >= 6 and med.get(s, 0) >= 30]
    M[f"fixed_{v}"] = M.site.isin(fixed[v])
M.to_csv(OUT / "snow_sites.csv", index=False)
log("fixed sets: " + str({v: len(f) for v, f in fixed.items()}) + "; snow-cover sites by region " +
    str(M[M.fixed_snow_cover_days].groupby("region").size().to_dict()), fh)

ser = []
for v in ["snow_cover_days", "melt_doy", "last_snow_doy"]:
    Q = SY[SY.site.isin(fixed[v]) & SY[v].notna()].merge(M[["site", "region"]], on="site")
    nrm = Q[Q.year.between(1961, 1990)].groupby("site")[v].mean()
    Q["anom"] = Q[v] - Q.site.map(nrm)
    for scope in ["Canada"] + REGIONS:
        d = Q if scope == "Canada" else Q[Q.region == scope]
        if d.site.nunique() < 2:
            continue
        g = d.groupby("year").agg(value=("anom", "mean"), n_sites=("site", "nunique"), raw_mean=(v, "mean")).reset_index()
        g["scope"] = scope
        g["variable"] = v
        ser.append(g)
SER = pd.concat(ser)
SER.to_csv(OUT / "snow_series.csv", index=False)
tr, rk = [], []
for (scope, v), g in SER.groupby(["scope", "variable"]):
    g = g.set_index("year")
    for a, b in [(1956, 2026), (1972, 2026), (1990, 2026)]:
        s = g.loc[a:b]
        A_ = g.loc[1961:1990].value
        B_ = g.loc[2016:2026].value
        tr.append(dict(scope=scope, variable=v, period=f"{a}-{b}", n_sites_median=g.n_sites.median(),
                       normal_raw_mean=g.loc[1961:1990].raw_mean.mean(), diff_2016_2026_vs_1961_1990=B_.mean() - A_.mean(),
                       diff_welch_p=stats.ttest_ind(B_, A_, equal_var=False).pvalue, **trend_stats(s.index, s.value)))
    full = g.value
    for y in (2023, 2024, 2025, 2026):
        if y in full.index:
            rk.append(dict(scope=scope, variable=v, year=y, anomaly=full[y], rank_lowest_or_earliest=int((full < full[y]).sum() + 1), n_years=len(full)))
TR = pd.DataFrame(tr)
TR.to_csv(OUT / "snow_trends.csv", index=False)
pd.DataFrame(rk).to_csv(OUT / "snow_ranks_2023_2026.csv", index=False)
srows = []
for v in ["snow_cover_days", "melt_doy"]:
    for s, g in SY[SY.site.isin(fixed[v]) & SY[v].notna()].groupby("site"):
        t = stats.theilslopes(g[v], g.year)
        tau, p = stats.kendalltau(g.year, g[v])
        srows.append(dict(variable=v, site=s, n_years=len(g), sen_per_decade=t[0] * 10, mk_tau=tau, mk_p=p))
ST = pd.DataFrame(srows).merge(M[["site", "name", "prov", "region"]], on="site")
ST.to_csv(OUT / "snow_site_trends.csv", index=False)
pd.set_option("display.width", 250)
log(TR[TR.period == "1956-2026"][["scope", "variable", "n_sites_median", "normal_raw_mean", "diff_2016_2026_vs_1961_1990", "diff_welch_p",
                                  "ols_per", "ols_lo", "ols_hi", "ols_p_ar1", "sen_per", "sen_lo", "sen_hi", "mk_p"]].round(3).to_string(), fh)
for v in ["snow_cover_days", "melt_doy"]:
    s = ST[ST.variable == v]
    log(f"site trends {v}: n {len(s)}, median Sen {s.sen_per_decade.median():.2f}/decade, negative {(s.sen_per_decade < 0).sum()}, "
        f"MK p<0.05 down {((s.mk_p < 0.05) & (s.mk_tau < 0)).sum()}, up {((s.mk_p < 0.05) & (s.mk_tau > 0)).sum()}", fh)
log(pd.DataFrame(rk).query("scope == 'Canada'").to_string(), fh)

# ---------------------------------------------------------------- split-period sets (the full-period set is small)
# Early: 1956-2005, before most airports stopped reporting snow on ground; sites valid in >= 40 of 50 winters and
# >= 24 of 30 in 1961-1990. Recent: 1991-2026 from analysis/climate/work/site_year.csv (same ECCC daily data,
# window Nov 1-Apr 30 for snow-cover days; melt = day after the last snow day), sites valid in >= 29 of 36 years.
from common import CLIMATE as _CL
split = []
for v in ["snow_cover_days", "melt_doy"]:
    e = SY[SY.year.between(1956, 2005) & SY[v].notna()]
    n_e = e.groupby("site").year.count()
    n_n = e[e.year.between(1961, 1990)].groupby("site").year.count()
    es = [s for s in n_e.index if n_e[s] >= 40 and n_n.get(s, 0) >= 24 and med.get(s, 0) >= 30]
    Q = e[e.site.isin(es)].merge(M[["site", "region"]], on="site")
    Q["anom"] = Q[v] - Q.site.map(Q[Q.year.between(1961, 1990)].groupby("site")[v].mean())
    for scope in ["Canada"] + REGIONS:
        d = Q if scope == "Canada" else Q[Q.region == scope]
        if d.site.nunique() < 3:
            continue
        g = d.groupby("year").anom.mean()
        split.append(dict(set="early 1956-2005", scope=scope, variable=v, n_sites=d.site.nunique(), **trend_stats(g.index, g.values)))
    st = pd.DataFrame([dict(site=s, sen=stats.theilslopes(g[v], g.year)[0] * 10, tau=stats.kendalltau(g.year, g[v])[0],
                            p=stats.kendalltau(g.year, g[v])[1]) for s, g in Q.groupby("site")])
    log(f"early set {v}: {len(es)} sites; median site Sen {st.sen.median():.2f}/decade; negative {(st.sen < 0).sum()}; "
        f"MK p<0.05 down {((st.p < 0.05) & (st.tau < 0)).sum()}, up {((st.p < 0.05) & (st.tau > 0)).sum()}", fh)
CS = pd.read_csv(_CL / "work" / "site_year.csv", dtype={"site": str})
CM = pd.read_csv(_CL / "work" / "site_meta.csv", dtype={"site": str})
CM["region"] = CM.prov.map(REGION)
for v in ["snow_cover_days", "melt_doy"]:
    r = CS[CS[v].notna() & CS.fire_year.between(1991, 2026)]
    n_r = r.groupby("site").fire_year.count()
    md = r.groupby("site").snow_cover_days.median() if v == "snow_cover_days" else None
    rs = [s for s in n_r.index if n_r[s] >= 29 and (md is None or md.get(s, 0) >= 30)]
    Q = r[r.site.isin(rs)].merge(CM[["site", "region"]], on="site")
    Q["anom"] = Q[v] - Q.site.map(Q[Q.fire_year.between(1991, 2020)].groupby("site")[v].mean())
    for scope in ["Canada"] + REGIONS:
        d = Q if scope == "Canada" else Q[Q.region == scope]
        if d.site.nunique() < 3:
            continue
        g = d.groupby("fire_year").anom.mean()
        split.append(dict(set="recent 1991-2026 (analysis/climate sites)", scope=scope, variable=v, n_sites=d.site.nunique(),
                          **trend_stats(g.index, g.values)))
    st = pd.DataFrame([dict(site=s, sen=stats.theilslopes(g[v], g.fire_year)[0] * 10, tau=stats.kendalltau(g.fire_year, g[v])[0],
                            p=stats.kendalltau(g.fire_year, g[v])[1]) for s, g in Q.groupby("site")])
    log(f"recent set {v}: {len(rs)} sites; median site Sen {st.sen.median():.2f}/decade; negative {(st.sen < 0).sum()}; "
        f"MK p<0.05 down {((st.p < 0.05) & (st.tau < 0)).sum()}, up {((st.p < 0.05) & (st.tau > 0)).sum()}", fh)
SP = pd.DataFrame(split)
SP.to_csv(OUT / "snow_trends_split_periods.csv", index=False)
log(SP[["set", "scope", "variable", "n_sites", "ols_per", "ols_lo", "ols_hi", "ols_p_ar1", "sen_per", "mk_p"]].round(3).to_string(), fh)
