"""Fire-season climate per station, area, region and Canada, fire years 1950-2026; trends and comparisons.

Input: work/temp_monthly_filled.csv, work/prec_monthly_filled.csv (02).
Variables for fire year y (every month in the window must be present):
  t_mjja      mean temperature May-Aug y (C)
  p_amjjas    precipitation Apr-Sep y (mm)
  p_sondjfm   precipitation Sep y-1 to Mar y, the previous fall and winter (mm)
  p_12m       precipitation Oct y-1 to Sep y, the 12 months ending with the fire season (mm)
Station anomaly: temperature minus the station's 1961-1990 mean; precipitation as % of its 1961-1990 mean.
A station needs >= 24 of the 30 normal years for that variable.
Areas: every eligible fma_v2 area (forest >= 100,000 ha and >= 5% of land, not Nunavut; 177 areas) takes the
stations inside it or within 50 km of its boundary; an area with none takes the nearest 3 stations within
300 km of its boundary (basis = nearest). Area anomaly = mean of its station anomalies that year.
Region and Canada: forest-weighted mean of area anomalies over areas with a value (weight = forest ha).
Trends: OLS per decade with a lag-1-autocorrelation-adjusted 95% interval, Theil-Sen per decade with 95%
interval, Mann-Kendall p. Periods 1950-2026 and 1972-2026. Comparisons: mean 2016-2026 minus mean 1961-1990
(Welch 95% interval); rank of 2023, 2024, 2025, 2026 among 1950-2026 (1 = warmest or driest).
Outputs: climate_area_year.csv (panel input for 06), climate_series.csv (region/Canada by year),
         climate_trends.csv, climate_recent_vs_normal.csv, climate_ranks_2023_2026.csv,
         station_trends.csv, work/area_station_map.csv, work/log_03.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import stats

from common import WORK, OUT, CLIMATE_AREAS, NORMAL, RECENT, REGIONS, areas, log, trend_stats

fh = open(WORK / "log_03.txt", "w")
YRS = range(1950, 2027)
ST = pd.read_csv(WORK / "ahccd_stations.csv", dtype={"station": str})


def season(F, months_spec):
    """months_spec: list of (year_offset, month). Returns station x fire-year totals/means (complete only)."""
    F = F.set_index(["station", "year", "mon"]).value
    out = {}
    for y in YRS:
        idx = [(y + dy, m) for dy, m in months_spec]
        out[y] = idx
    st = F.index.get_level_values(0).unique()
    res = []
    W = F.unstack(["year", "mon"])
    for y, idx in out.items():
        cols = [c for c in idx if c in W.columns]
        if len(cols) < len(idx):
            res.append(pd.Series(np.nan, index=W.index, name=y))
            continue
        sub = W[cols]
        ok = sub.notna().all(axis=1)
        res.append(sub.sum(axis=1).where(ok).rename(y))
    return pd.concat(res, axis=1)


T = pd.read_csv(WORK / "temp_monthly_filled.csv", dtype={"station": str})
P = pd.read_csv(WORK / "prec_monthly_filled.csv", dtype={"station": str})
V = {"t_mjja": season(T, [(0, m) for m in (5, 6, 7, 8)]) / 4,
     "p_amjjas": season(P, [(0, m) for m in range(4, 10)]),
     "p_sondjfm": season(P, [(-1, m) for m in (9, 10, 11, 12)] + [(0, m) for m in (1, 2, 3)]),
     "p_12m": season(P, [(-1, m) for m in (10, 11, 12)] + [(0, m) for m in range(1, 10)])}
ANOM = {}
srows = []
for v, X in V.items():
    nrm_cols = [y for y in range(NORMAL[0], NORMAL[1] + 1)]
    nn = X[nrm_cols].notna().sum(axis=1)
    X = X[nn >= 24]
    mu = X[nrm_cols].mean(axis=1)
    A = X.sub(mu, axis=0) if v.startswith("t_") else X.div(mu, axis=0) * 100
    ANOM[v] = A
    log(f"{v}: {len(A)} stations with >= 24 normal years; valid station-years 1950-2026 {int(A.notna().sum().sum())}", fh)
    for s, row in A.iterrows():
        ts = trend_stats(row.index.values, row.values)
        srows.append(dict(variable=v, station=s, **ts))
STR = pd.DataFrame(srows)
STR = STR.merge(ST.drop_duplicates("station")[["station", "name", "prov", "lat", "lon"]], on="station", how="left")
STR.to_csv(OUT / "station_trends.csv", index=False)
for v in V:
    s = STR[(STR.variable == v) & (STR.n >= 60)]
    log(f"  station trends {v} (n>=60 yrs, {len(s)} stations): median Sen {s.sen_per.median():.3f}/decade; "
        f"positive {(s.sen_per > 0).mean():.1%}; significant positive (MK p<0.05) {((s.mk_p < 0.05) & (s.sen_per > 0)).mean():.1%}, "
        f"significant negative {((s.mk_p < 0.05) & (s.sen_per < 0)).mean():.1%}", fh)

# ---------------------------------------------------------------- station -> area map
A0 = areas()
EL = A0[A0.eligible].copy()
G = gpd.read_file(CLIMATE_AREAS / "areas_1km.gpkg")
idc = "fma_id" if "fma_id" in G.columns else "area_id"
G = G[G[idc].isin(EL.fma_id)].to_crs("ESRI:102001").set_index(idc)
maprows = []
for v, A in ANOM.items():
    kind = "temp" if v.startswith("t_") else "prec"
    s = ST[(ST.kind == kind) & ST.station.isin(A.index)].drop_duplicates("station")
    pts = gpd.GeoSeries(gpd.points_from_xy(s.lon, s.lat), crs="EPSG:4326").to_crs("ESRI:102001")
    pts.index = s.station.values
    for fid, geom in G.geometry.items():
        d = pts.distance(geom) / 1000
        near = d[d <= 50]
        basis = "inside_or_50km"
        if near.empty:
            near = d[d <= 300].nsmallest(3)
            basis = "nearest_3_within_300km"
        for sid, dk in near.items():
            maprows.append(dict(variable=v, fma_id=fid, station=sid, dist_km=dk, basis=basis))
MP = pd.DataFrame(maprows)
MP.to_csv(WORK / "area_station_map.csv", index=False)

# ---------------------------------------------------------------- area-year values
rows = []
for v, A in ANOM.items():
    m = MP[MP.variable == v]
    L = A.stack().rename("anom").reset_index()
    L.columns = ["station", "year", "anom"]
    J = m.merge(L, on="station")
    g = J.groupby(["fma_id", "year"]).agg(anom=("anom", "mean"), n=("anom", "size")).reset_index()
    g["variable"] = v
    g["basis"] = g.fma_id.map(m.drop_duplicates("fma_id").set_index("fma_id").basis)
    rows.append(g)
AY = pd.concat(rows)
AYW = AY.pivot_table(index=["fma_id", "year"], columns="variable", values="anom").reset_index()
NW = AY.pivot_table(index=["fma_id", "year"], columns="variable", values="n").add_prefix("n_").reset_index()
BW = AY.drop_duplicates(["fma_id", "variable"]).pivot(index="fma_id", columns="variable", values="basis").add_prefix("basis_").reset_index()
AYW = AYW.merge(NW, on=["fma_id", "year"]).merge(BW, on="fma_id")
AYW = AYW.merge(EL[["fma_id", "province", "region", "area_name", "forest_ha"]], on="fma_id")
AYW.to_csv(OUT / "climate_area_year.csv", index=False)
for v in V:
    b = AYW.drop_duplicates("fma_id")
    fw = b.groupby(f"basis_{v}").forest_ha.sum() / EL.forest_ha.sum()
    log(f"{v}: areas covered {b[f'basis_{v}'].notna().sum()} of {len(EL)}; forest share by basis {fw.round(3).to_dict()}", fh)

# ---------------------------------------------------------------- region / Canada series
ser = []
for scope in ["Canada"] + REGIONS:
    d = AYW if scope == "Canada" else AYW[AYW.region == scope]
    for v in V:
        x = d[d[v].notna()]
        g = x.groupby("year").apply(lambda z: pd.Series({"value": np.average(z[v], weights=z.forest_ha),
                                                         "n_areas": len(z), "forest_cov": z.forest_ha.sum()}), include_groups=False)
        tot = (EL if scope == "Canada" else EL[EL.region == scope]).forest_ha.sum()
        g["forest_share_covered"] = g.forest_cov / tot
        nst = ANOM[v].notna().sum()
        g = g.reset_index()
        g["scope"] = scope
        g["variable"] = v
        ser.append(g)
SER = pd.concat(ser)
SER = SER[(SER.year >= 1950) & (SER.year <= 2026)]
SER.to_csv(OUT / "climate_series.csv", index=False)

tr, rc, rk = [], [], []
for (scope, v), g in SER.groupby(["scope", "variable"]):
    g = g.set_index("year").value
    for y0 in (1950, 1972):
        s = g.loc[y0:2026]
        tr.append(dict(scope=scope, variable=v, period=f"{y0}-2026", **trend_stats(s.index.values, s.values)))
    a = g.loc[NORMAL[0]:NORMAL[1]].dropna()
    b = g.loc[RECENT[0]:RECENT[1]].dropna()
    w = stats.ttest_ind(b, a, equal_var=False)
    se = np.sqrt(a.var() / len(a) + b.var() / len(b))
    dfw = se ** 4 / ((a.var() / len(a)) ** 2 / (len(a) - 1) + (b.var() / len(b)) ** 2 / (len(b) - 1))
    tq = stats.t.ppf(0.975, dfw)
    diff = b.mean() - a.mean()
    rc.append(dict(scope=scope, variable=v, mean_1961_1990=a.mean(), mean_2016_2026=b.mean(), diff=diff,
                   diff_lo=diff - tq * se, diff_hi=diff + tq * se, welch_p=w.pvalue, n_a=len(a), n_b=len(b)))
    full = g.loc[1950:2026].dropna()
    asc = v.startswith("p_")          # precipitation: rank 1 = driest
    for y in (2023, 2024, 2025, 2026):
        if y in full.index:
            r = (full < full[y]).sum() + 1 if asc else (full > full[y]).sum() + 1
            rk.append(dict(scope=scope, variable=v, year=y, value=full[y], rank=int(r), n_years=len(full),
                           percentile=stats.percentileofscore(full, full[y]),
                           z_vs_1961_1990=(full[y] - a.mean()) / a.std()))
    s4 = full.loc[2023:2026]
    if len(s4) == 4:
        roll = full.rolling(4).mean().dropna()
        r = (roll < roll.loc[2026]).sum() + 1 if asc else (roll > roll.loc[2026]).sum() + 1
        rk.append(dict(scope=scope, variable=v, year="2023-2026 mean", value=s4.mean(), rank=int(r), n_years=len(roll),
                       percentile=stats.percentileofscore(roll, roll.loc[2026]), z_vs_1961_1990=np.nan))
TR = pd.DataFrame(tr)
RC = pd.DataFrame(rc)
RK = pd.DataFrame(rk)
TR.to_csv(OUT / "climate_trends.csv", index=False)
RC.to_csv(OUT / "climate_recent_vs_normal.csv", index=False)
RK.to_csv(OUT / "climate_ranks_2023_2026.csv", index=False)
pd.set_option("display.width", 250)
log(TR[TR.period == "1950-2026"][["scope", "variable", "n", "ols_per", "ols_lo", "ols_hi", "ols_p_ar1", "sen_per", "sen_lo", "sen_hi", "mk_p"]].round(3).to_string(), fh)
log(RC.round(3).to_string(), fh)
log(RK[RK.scope == "Canada"].round(2).to_string(), fh)
cov = SER[SER.scope == "Canada"].pivot(index="year", columns="variable", values="n_areas")
log("Canada n_areas by year (every 10th): " + cov.iloc[::10].to_string(), fh)
