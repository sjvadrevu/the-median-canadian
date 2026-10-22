"""Compute daily FWI at long-record ECCC stations, 1953-2026, and the trend in extreme fire-weather days.

Weather: 12:00 LST temperature, relative humidity and wind speed from climate-hourly (raw/eccc_hourly_noon), per
site from its member IDs (longest record first, other IDs fill gaps). A gap of 1 or 2 days in any of the three is
filled by linear interpolation; longer gaps stay missing (codes carried forward, FWI missing that day).
Rain: noon-to-noon 24-h rain approximated as 0.5 x daily total precipitation of the previous climate day +
0.5 x that of the current day (climate-daily TOTAL_PRECIPITATION; the climate day runs about midnight to
midnight, so noon-to-noon straddles two of them). Missing daily precipitation counts as 0 and is counted.
Season: every year starts on April 1 with the standard start-up codes (FFMC 85, DMC 6, DC 15; no overwintering)
and runs to October 31. Counting window: April 1 to October 19, as in analysis/weather (CWFIS station counts).
Extreme day: FWI >= 30; high or above: FWI >= 19.
Season qualifies (same rule as analysis/weather): FWI computed on >= 90% of Jun 1-Aug 31 days and >= 75% of
May 1-Sep 30 days, and daily precipitation present on >= 90% of Apr 1-Oct 19 days.
Fixed station set: sites qualifying in >= 80% of the seasons 1953-2026 (>= 60 of 74), >= 24 of 30 in 1961-1990
and >= 9 of 11 in 2016-2026.
Wind-fixed variant: the same calculation with noon wind replaced by the site's 1991-2020 calendar-month mean.
Validation: daily FWI and yearly extreme-day counts against the CWFIS station FWI archive (analysis/weather
site_daily.pkl) for the same climate IDs, 1990-2026.
Outputs: work/fwi_site_year.csv, fwi_sites.csv, fwi_extreme_days_series.csv, fwi_extreme_days_trends.csv,
         fwi_site_trends.csv, fwi_validation.csv, work/log_10.txt
"""
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from scipy import stats

from common import WORK, OUT, RAW, CLIMATE, WEATHER, REGION, REGIONS, log, trend_stats
from fwi import run_season

def safe_csv(f, **kw):
    """Read a gzip CSV; empty downloads (no rows for that ID and period) return an empty frame."""
    try:
        return pd.read_csv(f, **kw)
    except (pd.errors.EmptyDataError, ValueError):
        return pd.DataFrame()


fh = open(WORK / "log_10.txt", "w")
PL = pd.read_csv(WORK / "download_plan.csv", dtype={"site": str, "cid": str})
L = pd.read_csv(WORK / "long_ids.csv", dtype={"CLIMATE_IDENTIFIER": str, "site": str})
fsites = sorted(L[L.fwi_site].site.unique())
import os
if os.environ.get("TEST_SITES"):
    fsites = fsites[:int(os.environ["TEST_SITES"])]   # quick test only
HD, DD, OLD = RAW / "eccc_hourly_noon", RAW / "eccc_daily", CLIMATE / "raw" / "eccc" / "daily"


def read_hourly(cids):
    fr = []
    for k, c in enumerate(cids):
        f = HD / f"{c}.csv.gz"
        if not f.exists():
            continue
        d = safe_csv(f, usecols=["LOCAL_DATE", "TEMP", "RELATIVE_HUMIDITY", "WIND_SPEED"])
        if d.empty:
            continue
        d["pri"] = k
        fr.append(d)
    if not fr:
        return None
    d = pd.concat(fr)
    d["date"] = pd.to_datetime(d.LOCAL_DATE.str[:10])
    d = d.sort_values(["date", "pri"])
    return d.groupby("date")[["TEMP", "RELATIVE_HUMIDITY", "WIND_SPEED"]].first()


def read_daily(cids):
    fr = []
    for k, c in enumerate(cids):
        for f in (DD / f"{c}.csv.gz", OLD / f"{c}.csv.gz"):
            if f.exists():
                d = safe_csv(f, usecols=lambda x: x in ("LOCAL_DATE", "TOTAL_PRECIPITATION", "SNOW_ON_GROUND",
                                                            "MAX_TEMPERATURE", "MIN_TEMPERATURE"))
                if d.empty:
                    continue
                d["pri"] = k
                fr.append(d)
    if not fr:
        return None
    d = pd.concat(fr)
    d["date"] = pd.to_datetime(d.LOCAL_DATE.str[:10])
    d = d.sort_values(["date", "pri"])
    return d.groupby("date").first()


# site name and coordinates = the primary (first planned) ID, not the 5 km group
prim = PL[(PL.kind == "hourly") & (PL.role == "fwi")].drop_duplicates("site").set_index("site").cid
LL = L.drop_duplicates("CLIMATE_IDENTIFIER").set_index("CLIMATE_IDENTIFIER")
meta = pd.DataFrame({"site": prim.index, "primary_id": prim.values})
for c_, k_ in [("name", "STATION_NAME"), ("prov", "prov"), ("lat", "lat"), ("lon", "lon"), ("elev", "elev")]:
    meta[c_] = LL.loc[meta.primary_id, k_].values
SEAS = pd.date_range("2001-04-01", "2001-10-31")
MD = SEAS.strftime("%m-%d")
MON = SEAS.month.values
rows_sy, daily_keep = [], []
YEARS = range(1953, 2027)
for s in fsites:
    hc = PL[(PL.site == s) & (PL.kind == "hourly")].cid.tolist()
    dc_ = PL[(PL.site == s) & (PL.kind == "daily") & (PL.role == "fwi")].cid.tolist()
    h = read_hourly(hc)
    dly = read_daily(dc_)
    if h is None or dly is None:
        continue
    full = pd.date_range("1953-01-01", "2026-10-20")
    h = h.reindex(full)
    h = h.interpolate(limit=2, limit_area="inside")
    p = dly.TOTAL_PRECIPITATION.reindex(full)
    r24 = 0.5 * p.shift(1) + 0.5 * p
    r_ok = p.notna() & p.shift(1).notna()
    Tm = np.full((len(YEARS), len(SEAS)), np.nan); Hm = Tm.copy(); Wm = Tm.copy(); Rm = Tm.copy(); Rok = np.zeros_like(Tm, bool)
    for i, y in enumerate(YEARS):
        idx = pd.to_datetime([f"{y}-{m}" for m in MD])
        sel = idx[idx <= full[-1]]
        n = len(sel)
        Tm[i, :n] = h.TEMP.reindex(sel).values
        Hm[i, :n] = h.RELATIVE_HUMIDITY.reindex(sel).values
        Wm[i, :n] = h.WIND_SPEED.reindex(sel).values
        Rm[i, :n] = r24.reindex(sel).values
        Rok[i, :n] = r_ok.reindex(sel).values
    o = run_season(Tm, Hm, Wm, Rm, MON)
    F = o["fwi"]
    # wind-fixed variant: noon wind replaced by the site's 1991-2020 mean noon wind for that calendar month (removes
    # any wind trend, including anemometer and exposure changes; temperature, humidity and rain as observed)
    yrs_ = np.array(list(YEARS))
    nrm_ = (yrs_ >= 1991) & (yrs_ <= 2020)
    Wc = np.array([np.nanmean(Wm[nrm_][:, MON == mm]) if np.isfinite(Wm[nrm_][:, MON == mm]).any() else np.nan for mm in MON])
    Wfix = np.where(np.isfinite(Wm), np.broadcast_to(Wc, Wm.shape), np.nan)
    Ffw = run_season(Tm, Hm, Wfix, Rm, MON)["fwi"]
    cnt = (SEAS.month >= 4) & ~((SEAS.month == 10) & (SEAS.day > 19))
    jja = SEAS.month.isin([6, 7, 8])
    mjjas = SEAS.month.isin([5, 6, 7, 8, 9])
    for i, y in enumerate(YEARS):
        f = F[i]
        rows_sy.append(dict(site=s, year=y, cov_jja=np.isfinite(f[jja]).mean(), cov_mjjas=np.isfinite(f[mjjas]).mean(),
                            cov_rain=Rok[i][cnt].mean(), extreme_days=int((f[cnt] >= 30).sum()), high_plus_days=int((f[cnt] >= 19).sum()),
                            mean_fwi_mjjas=np.nanmean(f[mjjas]) if np.isfinite(f[mjjas]).any() else np.nan,
                            p95_fwi_mjjas=np.nanpercentile(f[mjjas], 95) if np.isfinite(f[mjjas]).sum() > 20 else np.nan,
                            mean_t_noon_mjjas=np.nanmean(Tm[i][mjjas]) if np.isfinite(Tm[i][mjjas]).any() else np.nan,
                            mean_rh_noon_mjjas=np.nanmean(Hm[i][mjjas]) if np.isfinite(Hm[i][mjjas]).any() else np.nan,
                            mean_ws_noon_mjjas=np.nanmean(Wm[i][mjjas]) if np.isfinite(Wm[i][mjjas]).any() else np.nan,
                            rain_mjjas=np.nansum(Rm[i][mjjas]),
                            extreme_days_fixwind=int((Ffw[i][cnt] >= 30).sum()), high_plus_days_fixwind=int((Ffw[i][cnt] >= 19).sum()),
                            mean_fwi_fixwind=np.nanmean(Ffw[i][mjjas]) if np.isfinite(Ffw[i][mjjas]).any() else np.nan))
    # keep daily FWI 1990-2026 for validation
    for i, y in enumerate(YEARS):
        if y >= 1990:
            daily_keep.append(pd.DataFrame({"site": s, "date": pd.to_datetime([f"{y}-{m}" for m in MD]), "fwi_calc": F[i]}))
    log(f"{s} done ({len(hc)} hourly IDs, {len(dc_)} daily IDs)", fh)
SY = pd.DataFrame(rows_sy)
SY["qualifies"] = (SY.cov_jja >= 0.9) & (SY.cov_mjjas >= 0.75) & (SY.cov_rain >= 0.9)
SY.to_csv(WORK / "fwi_site_year.csv", index=False)
q = SY[SY.qualifies]
n_all = q.groupby("site").year.count()
n_nrm = q[q.year.between(1961, 1990)].groupby("site").year.count()
n_rec = q[q.year.between(2016, 2026)].groupby("site").year.count()
fixed = [s for s in n_all.index if n_all[s] >= 60 and n_nrm.get(s, 0) >= 24 and n_rec.get(s, 0) >= 9]
M = meta[meta.site.isin(SY.site.unique())].copy()
M["n_qual"] = M.site.map(n_all).fillna(0).astype(int)
M["n_qual_1961_1990"] = M.site.map(n_nrm).fillna(0).astype(int)
M["n_qual_2016_2026"] = M.site.map(n_rec).fillna(0).astype(int)
M["fixed_set"] = M.site.isin(fixed)
M["region"] = M.prov.map(REGION)
M.to_csv(OUT / "fwi_sites.csv", index=False)
log(f"computed {SY.site.nunique()} sites; qualifying site-years {len(q)}; fixed set {len(fixed)} sites; by region "
    f"{M[M.fixed_set].groupby('region').size().to_dict()}", fh)
log("qualifying seasons per decade (all sites): " + str(q.groupby(q.year // 10 * 10).size().to_dict()), fh)

# ---------------------------------------------------------------- validation against CWFIS
try:
    wd = pd.read_pickle(WEATHER / "work" / "site_daily.pkl")
    wm = pd.read_pickle(WEATHER / "work" / "site_meta.pkl")
    cw_ids = {}
    for site_w, r in wm.iterrows():
        for c in str(r.member_ids).split(";"):
            cw_ids[c] = str(site_w)
    DK = pd.concat(daily_keep, ignore_index=True)
    vrows = []
    for s in sorted(SY.site.unique()):
        members = PL[(PL.site == s) & (PL.kind == "hourly")].cid.tolist()
        wsites = {cw_ids[c] for c in members if c in cw_ids}
        if not wsites:
            continue
        w = wd[wd.site.astype(str).isin(wsites)].groupby("date").fwi.mean()
        c = DK[DK.site == s].set_index("date").fwi_calc
        j = pd.concat([c, w.rename("fwi_cwfis")], axis=1, join="inner").dropna()
        j = j[(j.index.month >= 5) & (j.index.month <= 9)]
        if len(j) < 500:
            continue
        ex = j.assign(y=j.index.year).groupby("y").agg(calc=("fwi_calc", lambda v: (v >= 30).sum()), cw=("fwi_cwfis", lambda v: (v >= 30).sum()), n=("fwi_calc", "size"))
        ex = ex[ex.n >= 120]
        vrows.append(dict(site=s, cwfis_sites=";".join(sorted(wsites)), n_days=len(j), r_daily=j.fwi_calc.corr(j.fwi_cwfis),
                          mean_calc=j.fwi_calc.mean(), mean_cwfis=j.fwi_cwfis.mean(), bias=(j.fwi_calc - j.fwi_cwfis).mean(),
                          mae=(j.fwi_calc - j.fwi_cwfis).abs().median(),
                          ext_calc_per_yr=ex.calc.mean(), ext_cwfis_per_yr=ex.cw.mean(),
                          r_yearly_extreme=ex.calc.corr(ex.cw) if len(ex) > 5 else np.nan, n_years=len(ex),
                          trend_calc=stats.theilslopes(ex.calc, ex.index)[0] * 10 if len(ex) > 10 else np.nan,
                          trend_cwfis=stats.theilslopes(ex.cw, ex.index)[0] * 10 if len(ex) > 10 else np.nan))
    V = pd.DataFrame(vrows)
    V.to_csv(OUT / "fwi_validation.csv", index=False)
    log(f"validation: {len(V)} sites; median daily r {V.r_daily.median():.3f}; median bias {V.bias.median():.2f}; "
        f"extreme days/yr (May-Sep) calc {V.ext_calc_per_yr.median():.2f} vs CWFIS {V.ext_cwfis_per_yr.median():.2f}; "
        f"median yearly-count r {V.r_yearly_extreme.median():.3f}", fh)
except Exception as e:
    log(f"validation failed: {e}", fh)

# ---------------------------------------------------------------- series and trends (fixed set)
Q = q[q.site.isin(fixed)].merge(M[["site", "region", "name", "prov"]], on="site")
for v in ["extreme_days", "high_plus_days", "extreme_days_fixwind", "high_plus_days_fixwind", "mean_fwi_fixwind", "mean_fwi_mjjas", "p95_fwi_mjjas", "mean_t_noon_mjjas", "mean_rh_noon_mjjas", "mean_ws_noon_mjjas", "rain_mjjas"]:
    nrm = Q[Q.year.between(1961, 1990)].groupby("site")[v].mean()
    Q[v + "_anom"] = Q[v] - Q.site.map(nrm)
ser = []
for scope in ["Canada"] + REGIONS:
    d = Q if scope == "Canada" else Q[Q.region == scope]
    if d.empty:
        continue
    g = d.groupby("year").agg(n_sites=("site", "nunique"), extreme_days_mean=("extreme_days", "mean"),
                              extreme_anom=("extreme_days_anom", "mean"), high_plus_anom=("high_plus_days_anom", "mean"),
                              extreme_fixwind_anom=("extreme_days_fixwind_anom", "mean"), high_plus_fixwind_anom=("high_plus_days_fixwind_anom", "mean"),
                              mean_fwi_fixwind_anom=("mean_fwi_fixwind_anom", "mean"),
                              mean_fwi_anom=("mean_fwi_mjjas_anom", "mean"), p95_fwi_anom=("p95_fwi_mjjas_anom", "mean"),
                              t_noon_anom=("mean_t_noon_mjjas_anom", "mean"), rh_noon_anom=("mean_rh_noon_mjjas_anom", "mean"),
                              ws_noon_anom=("mean_ws_noon_mjjas_anom", "mean"), rain_anom=("rain_mjjas_anom", "mean")).reset_index()
    g["scope"] = scope
    ser.append(g)
SER = pd.concat(ser)
SER.to_csv(OUT / "fwi_extreme_days_series.csv", index=False)
tr = []
for scope, g in SER.groupby("scope"):
    for v in ["extreme_anom", "high_plus_anom", "extreme_fixwind_anom", "high_plus_fixwind_anom", "mean_fwi_fixwind_anom", "mean_fwi_anom", "p95_fwi_anom", "t_noon_anom", "rh_noon_anom", "ws_noon_anom", "rain_anom"]:
        for a, b in [(1953, 2026), (1953, 2022), (1972, 2026), (1990, 2026)]:
            s = g[g.year.between(a, b)]
            a1 = g[g.year.between(1961, 1990)][v]
            b1 = g[g.year.between(2016, 2026)][v]
            tr.append(dict(scope=scope, variable=v, period=f"{a}-{b}", n_sites_median=g.n_sites.median(),
                           normal_extreme_days=g[g.year.between(1961, 1990)].extreme_days_mean.mean(),
                           diff_2016_2026_vs_1961_1990=b1.mean() - a1.mean(),
                           diff_welch_p=stats.ttest_ind(b1, a1, equal_var=False).pvalue if len(b1) > 2 else np.nan,
                           **trend_stats(s.year, s[v])))
TR = pd.DataFrame(tr)
TR.to_csv(OUT / "fwi_extreme_days_trends.csv", index=False)
srows = []
for s, g in Q.groupby("site"):
    t = stats.theilslopes(g.extreme_days, g.year)
    tau, p = stats.kendalltau(g.year, g.extreme_days)
    srows.append(dict(site=s, name=g.name.iloc[0], prov=g.prov.iloc[0], region=g.region.iloc[0], n_years=len(g),
                      mean_1961_1990=g[g.year.between(1961, 1990)].extreme_days.mean(),
                      mean_2016_2026=g[g.year.between(2016, 2026)].extreme_days.mean(),
                      sen_per_decade=t[0] * 10, mk_tau=tau, mk_p=p))
SI = pd.DataFrame(srows)
SI.to_csv(OUT / "fwi_site_trends.csv", index=False)
pd.set_option("display.width", 250)
log(TR[TR.period.isin(["1953-2026", "1953-2022"]) & TR.variable.isin(["extreme_anom", "extreme_fixwind_anom", "high_plus_anom", "mean_fwi_anom", "t_noon_anom", "rh_noon_anom", "ws_noon_anom", "rain_anom"])]
    [["scope", "variable", "period", "n_sites_median", "normal_extreme_days", "diff_2016_2026_vs_1961_1990", "diff_welch_p", "ols_per", "ols_lo", "ols_hi", "ols_p_ar1", "sen_per", "mk_p"]].round(3).to_string(), fh)
log(f"site trends (fixed set {len(SI)}): Sen > 0 {(SI.sen_per_decade > 0).sum()}, < 0 {(SI.sen_per_decade < 0).sum()}, = 0 {(SI.sen_per_decade == 0).sum()}; "
    f"MK p<0.05 up {((SI.mk_p < 0.05) & (SI.mk_tau > 0)).sum()}, down {((SI.mk_p < 0.05) & (SI.mk_tau < 0)).sum()}", fh)
for reg, g in SI.groupby("region"):
    log(f"  {reg}: n {len(g)}, normal {g.mean_1961_1990.mean():.1f} d, 2016-2026 {g.mean_2016_2026.mean():.1f} d, up {((g.mk_p < 0.05) & (g.mk_tau > 0)).sum()}, "
        f"down {((g.mk_p < 0.05) & (g.mk_tau < 0)).sum()}", fh)
