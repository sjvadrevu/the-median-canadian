"""Trend in extreme fire-weather days at fixed CWFIS stations, 1990-2026.

Input (reused from analysis/weather): work/site_year.pkl (extreme_days = days with FWI >= 30 from Apr 1 to
Oct 19; high_plus_days = FWI >= 19; qualifies = FWI computed on >= 90% of Jun-Aug and >= 75% of May-Sep days),
station_extreme_days.csv (the 116 strict sites: qualifying in >= 28 of 30 years 1991-2020, in Canada).
Fixed station set: those 116 sites; a site-year enters only if it qualifies.
National and regional series: mean over qualifying sites of the site's extreme days minus its own 1991-2020 mean
(anomaly keeps the series fixed-composition when a site misses a year), plus the raw mean.
Trend: OLS per decade (AR1-adjusted 95% interval), Theil-Sen, Mann-Kendall, 1990-2026 and 1990-2022
(without the 2023-2026 run). Per site: Theil-Sen slope and Mann-Kendall p on qualifying years.
Outputs: cwfis_extreme_days_series.csv, cwfis_extreme_days_trends.csv, cwfis_site_trends.csv, work/log_06.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from scipy import stats

from common import WORK, OUT, WEATHER, REGION, log, trend_stats

fh = open(WORK / "log_06.txt", "w")
sy = pd.read_pickle(WEATHER / "work" / "site_year.pkl")
st = pd.read_csv(WEATHER / "station_extreme_days.csv", dtype={"site_id": str})
st = st[st.rule == "strict_28of30"] if "rule" in st.columns else st
st["region"] = st.province.map(REGION)
sy["site"] = sy.site.astype(str)
q = sy[sy.qualifies & sy.site.isin(st.site_id) & (sy.year <= 2026)].copy()
q = q.merge(st[["site_id", "name", "province", "region", "fma_id"]], left_on="site", right_on="site_id")
for v in ["extreme_days", "high_plus_days"]:
    q[v + "_anom"] = q[v] - q.groupby("site")[v].transform(lambda s: s[q.loc[s.index, "year"].between(1991, 2020)].mean())
log(f"sites {q.site.nunique()}, qualifying site-years {len(q)}, years {q.year.min()}-{q.year.max()}", fh)

ser = []
for scope in ["Canada", "BC", "Prairies", "Ontario", "Quebec", "Atlantic", "North"]:
    d = q if scope == "Canada" else q[q.region == scope]
    g = d.groupby("year").agg(n_sites=("site", "nunique"), extreme_days_mean=("extreme_days", "mean"),
                              extreme_anom_mean=("extreme_days_anom", "mean"), high_plus_mean=("high_plus_days", "mean"),
                              high_plus_anom_mean=("high_plus_days_anom", "mean")).reset_index()
    g["scope"] = scope
    ser.append(g)
SER = pd.concat(ser)
SER.to_csv(OUT / "cwfis_extreme_days_series.csv", index=False)
tr = []
for scope, g in SER.groupby("scope"):
    for v in ["extreme_anom_mean", "high_plus_anom_mean"]:
        for y1 in (2026, 2022):
            s = g[g.year <= y1]
            base = g[g.year.between(1991, 2020)][v.replace("anom", "days") if v.startswith("extreme") else "high_plus_mean"].mean()
            tr.append(dict(scope=scope, variable=v, period=f"1990-{y1}", n_sites_median=g.n_sites.median(),
                           normal_days_1991_2020=base, **trend_stats(s.year, s[v])))
TR = pd.DataFrame(tr)
TR.to_csv(OUT / "cwfis_extreme_days_trends.csv", index=False)
rows = []
for s, g in q.groupby("site"):
    if len(g) < 25:
        continue
    t = stats.theilslopes(g.extreme_days, g.year)
    tau, p = stats.kendalltau(g.year, g.extreme_days)
    rows.append(dict(site=s, name=g.name.iloc[0], province=g.province.iloc[0], region=g.region.iloc[0], n_years=len(g),
                     mean_9120=g[g.year.between(1991, 2020)].extreme_days.mean(), sen_per_decade=t[0] * 10, mk_tau=tau, mk_p=p))
SI = pd.DataFrame(rows)
SI.to_csv(OUT / "cwfis_site_trends.csv", index=False)
pd.set_option("display.width", 250)
log(TR.round(3).to_string(), fh)
log(f"sites with >= 25 qualifying years: {len(SI)}; Sen slope > 0: {(SI.sen_per_decade > 0).sum()}, < 0: {(SI.sen_per_decade < 0).sum()}, "
    f"= 0: {(SI.sen_per_decade == 0).sum()}; MK p < 0.05 increasing {((SI.mk_p < 0.05) & (SI.mk_tau > 0)).sum()}, "
    f"decreasing {((SI.mk_p < 0.05) & (SI.mk_tau < 0)).sum()}", fh)
log(SI.groupby("region").agg(n=("site", "size"), median_sen=("sen_per_decade", "median"),
                             n_sen_positive=("sen_per_decade", lambda s: (s > 0).sum())).to_string(), fh)
for reg, g in SI.groupby("region"):
    log(f"  {reg}: sig increasing {((g.mk_p < 0.05) & (g.mk_tau > 0)).sum()}, sig decreasing {((g.mk_p < 0.05) & (g.mk_tau < 0)).sum()}", fh)
