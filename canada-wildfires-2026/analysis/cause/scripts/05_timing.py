"""Season timing, 1990-2026, from fire start (report) dates.

Per year and scope (Canada, each province by geographic location of the ignition point, each area):
  first_fire_doy           first fire of the year (any size)
  start_p10_doy / p90       10th and 90th percentile of fire start dates (count based): ignition season
  first_large200_doy       first fire that reached 200 ha or more; first_large1000_doy for 1,000 ha
  area_p10/p50/p90_doy     date by which 10/50/90% of the year's area had started, each fire's final size
                           credited to its start date (not to the days it actually burned)
Cross-check of when area actually burned: CWFIS FireM3 estimated cumulative area by day (2012-2026, satellite
hotspot based), date reaching 10/50/90% of the year total.
Trends: Theil-Sen slope and Kendall test, 1990-2025; 2026 compared with the trend line value for 2026 and with
the residual spread (2026 residual / SD of 1990-2025 residuals).
Outputs: timing_by_year_scope.csv, timing_trends.csv, timing_m3_by_year.csv, timing_by_area_year.csv
"""
import numpy as np
import pandas as pd

from common import BASE, OUT, area_dir, log, theil_sen

D = area_dir()
fh = open(D / "log_05.txt", "w")
F = pd.read_pickle(D / "fires_all.pkl")
F = F[F.doy.notna()].copy()
F = F[F.start.dt.year == F.year]


def wq(doy, w, q):
    o = np.argsort(doy)
    d, ww = doy[o], w[o]
    cw = np.cumsum(ww)
    if cw[-1] <= 0:
        return np.nan
    return float(d[np.searchsorted(cw, q * cw[-1])])


def metrics(g):
    doy = g.doy.values.astype(float)
    w = g.size_ha.fillna(0).values
    r = dict(n_fires=len(g), ha=w.sum(), first_fire_doy=doy.min() if len(doy) else np.nan)
    r["start_p10_doy"] = np.percentile(doy, 10) if len(doy) >= 5 else np.nan
    r["start_p50_doy"] = np.percentile(doy, 50) if len(doy) >= 5 else np.nan
    r["start_p90_doy"] = np.percentile(doy, 90) if len(doy) >= 5 else np.nan
    for thr in [200, 1000]:
        big = doy[w >= thr]
        r[f"first_large{thr}_doy"] = big.min() if len(big) else np.nan
        r[f"last_large{thr}_doy"] = big.max() if len(big) else np.nan
        r[f"n_large{thr}"] = len(big)
    for q in [0.1, 0.5, 0.9]:
        r[f"area_p{int(q * 100)}_doy"] = wq(doy, w, q) if w.sum() > 0 else np.nan
    return pd.Series(r)


rows = []
for y, g in F.groupby("year"):
    rows.append(metrics(g).rename(None).to_frame().T.assign(year=y, scope="CA"))
    for p, h in g.groupby("province"):
        rows.append(metrics(h).to_frame().T.assign(year=y, scope=p))
TY = pd.concat(rows, ignore_index=True)
TY.to_csv(OUT / "timing_by_year_scope.csv", index=False)

# area-level, for the model
ra = []
for (a, y), g in F[F.fma_id > 0].groupby(["fma_id", "year"]):
    ra.append(metrics(g).to_frame().T.assign(fma_id=a, year=y))
TA = pd.concat(ra, ignore_index=True)
TA.to_csv(OUT / "timing_by_area_year.csv", index=False)

# trends
MET = ["first_fire_doy", "start_p10_doy", "start_p50_doy", "start_p90_doy", "first_large200_doy",
       "first_large1000_doy", "last_large200_doy", "area_p10_doy", "area_p50_doy", "area_p90_doy"]
tr = []
for s, g in TY.groupby("scope"):
    h = g[(g.year >= 1990) & (g.year <= 2025)]
    for m in MET:
        t = theil_sen(h.year, h[m].astype(float))
        v26 = g.loc[g.year == 2026, m]
        v26 = float(v26.iloc[0]) if len(v26) and pd.notna(v26.iloc[0]) else np.nan
        pred = t.get("intercept", np.nan) + t["slope"] * 2026 if np.isfinite(t["slope"]) else np.nan
        res = h[m].astype(float) - (t.get("intercept", np.nan) + t["slope"] * h.year)
        base = h[(h.year >= 1991) & (h.year <= 2020)][m].astype(float)
        tr.append(dict(scope=s, metric=m, slope_days_per_decade=t["slope"] * 10, lo95=t["lo"] * 10, hi95=t["hi"] * 10,
                       kendall_tau=t["tau"], p_value=t["p"], n_years=t["n"], mean_1991_2020=base.mean(),
                       median_1991_2020=base.median(), trend_value_2026=pred, value_2026=v26,
                       resid_2026_days=v26 - pred, resid_2026_z=(v26 - pred) / res.std() if res.std() > 0 else np.nan,
                       rank_2026_earliest=int((pd.concat([h[m].astype(float), pd.Series([v26])]) < v26).sum() + 1) if pd.notna(v26) else np.nan,
                       n_ranked=int(h[m].notna().sum() + 1)))
TT = pd.DataFrame(tr)
TT.to_csv(OUT / "timing_trends.csv", index=False)
log(TT[TT.scope == "CA"].round(2).to_string(), fh)

# satellite (M3) cumulative-by-day
m3a = pd.read_csv(BASE / "data/fire/raw/m3_2026/cwfis_firem3_estimated_cumulative_area_burned_by_day_archive.csv")
m3c = pd.read_csv(BASE / "data/fire/raw/m3_2026/cwfis_firem3_estimated_cumulative_area_burned_by_day_canada.csv", skipinitialspace=True)
m3p = pd.read_csv(BASE / "data/fire/raw/m3_2026/cwfis_firem3_estimated_cumulative_area_burned_by_day_by_province.csv", skipinitialspace=True)
m3a["date"] = pd.to_datetime(m3a.date)
m3a["area"] = pd.to_numeric(m3a.area, errors="coerce")
nat = m3a.groupby("date").area.sum(min_count=1).reset_index()
m3c["date"] = pd.to_datetime(m3c.date)
nat = pd.concat([nat.rename(columns={"area": "ha"}), m3c.rename(columns={"hectares": "ha"})])
mrows = []
for y, g in nat.groupby(nat.date.dt.year):
    g = g.sort_values("date").dropna()
    tot = g.ha.max()
    r = dict(year=y, scope="CA", total_ha=tot, first_date=g.date.min().date(), last_date=g.date.max().date())
    for q in [0.1, 0.5, 0.9]:
        r[f"m3_p{int(q * 100)}_doy"] = g.loc[g.ha >= q * tot, "date"].min().dayofyear
    mrows.append(r)
M = pd.DataFrame(mrows)
M.to_csv(OUT / "timing_m3_by_year.csv", index=False)
log(M.to_string(), fh)
for q in ["m3_p10_doy", "m3_p50_doy", "m3_p90_doy"]:
    h = M[M.year <= 2025]
    t = theil_sen(h.year, h[q])
    log(f"M3 {q}: 2012-2025 mean {h[q].mean():.1f}, 2026 {M.loc[M.year == 2026, q].iloc[0]}, Theil-Sen {t['slope'] * 10:.1f} d/decade p={t['p']:.2f}", fh)
