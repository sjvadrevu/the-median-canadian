"""Analysis of climate_panel.csv: 2026 ranks, within-area rank correlations with burn, the chain
index -> snow/spring -> burn, by region, with year-permutation tests and FDR control.

Statistic ("within-area rank correlation", r_w): in every area, each variable is converted to its
percentile rank among that area's years ((rank - 0.5)/n - 0.5, ties averaged), which removes area
fixed effects and makes it robust to skew; the ranks of all area-years are pooled and a Pearson
correlation is taken. Fitting years 1991-2025 (NBAC); 2026 (M3 outlines, a different product) is
only ranked, not fitted.
Inference: areas are not independent within a year (one ENSO value for all areas; shared weather), so
p-values come from permuting the YEAR labels of the predictor jointly across all areas (999 permutations),
and 95% intervals from resampling years with replacement (1000 bootstrap draws). Benjamini-Hochberg
false discovery rate is applied within each family of tests (burn tests; chain tests).
Burn sample: areas with forest >= 100,000 ha and burned area > 0 in at least 5 of the 35 years
1991-2025. Areas need >= 15 years with the predictor.
Outputs: ranks_2026.csv, area_2026_summary.csv, region_2026_summary.csv, correlations_burn.csv,
correlations_chain.csv, chain_summary.csv, work/summary_07.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from scipy.stats import rankdata

from common import OUT, out_dir, WORK, area_dir, log

D = area_dir()
fh = open(D / "log_07.txt", "w")
P = pd.read_csv(out_dir() / "climate_panel.csv")
RNG = np.random.default_rng(20261021)
NPERM, NBOOT = 999, 1000
REGIONS = ["Canada", "BC", "Prairies", "Ontario", "Quebec", "North", "Atlantic"]

INDICES = ["oni_djf", "pdo_djf", "ao_djf", "nao_djf", "vortex_jfm", "oni_mam", "pdo_mam", "ao_mam", "nao_mam"]
SNOW = ["snowfall_pct", "snow_cover_days_anom", "max_snow_depth_pct", "melt_anom_days", "swe_apr1_pct"]
SPRING = ["t_amj_anom_c", "p_amj_pct"]
PRIOR = ["p_jja_prev_pct", "p_son_prev_pct", "p_ndjfm_pct", "p_12m_pct", "months_since_wet"]
STATION = SNOW + SPRING + PRIOR
# +1: a high value should favour fire; -1: a low value should favour fire
FIRE_DIR = {"snowfall_pct": -1, "snow_cover_days_anom": -1, "max_snow_depth_pct": -1, "melt_anom_days": -1,
            "swe_apr1_pct": -1, "t_amj_anom_c": 1, "p_amj_pct": -1, "p_jja_prev_pct": -1, "p_son_prev_pct": -1,
            "p_ndjfm_pct": -1, "p_12m_pct": -1, "months_since_wet": 1}
OUTCOMES = ["forest_share_burned", "log10_burned_ha"]
S = {}

# ---------------------------------------------------------------- 2026 ranks
rk = []
for v in STATION:
    for a, g in P[P.year.between(1991, 2026)].groupby("area_id"):
        g = g[g[v].notna()]
        if 2026 not in set(g.year) or len(g) < 15:
            continue
        x = g.set_index("year")[v] * FIRE_DIR[v]
        r = int((x > x[2026]).sum() + 1)
        rk.append(dict(area_id=a, variable=v, value_2026=g.set_index("year")[v][2026], rank_2026=r, n_years=len(g),
                       n_stations_2026=int(g.set_index("year")[f"n_{v}"][2026]),
                       median_1991_2020=g[g.year.between(1991, 2020)][v].median()))
RK = pd.DataFrame(rk)
attrs = P.drop_duplicates("area_id").set_index("area_id")[["area_name", "province", "region"]]
RK = RK.join(attrs, on="area_id")
RK["rank_note"] = "1 = most fire-favouring year (least snow, earliest melt, warmest, driest, longest since wet)"
RK.to_csv(out_dir() / "ranks_2026.csv", index=False, float_format="%.4g")
W26 = RK.pivot(index="area_id", columns="variable", values=["value_2026", "rank_2026", "n_stations_2026"])
W26.columns = [f"{b}_{a.replace('_2026', '')}" for a, b in W26.columns]
W26 = attrs.join(W26, how="right")
W26.to_csv(out_dir() / "area_2026_summary.csv", float_format="%.4g")

# region summary for 2026: median of area values, share of areas with 2026 in their 5 most fire-favouring years
reg = []
for rname in REGIONS:
    sub = RK if rname == "Canada" else RK[RK.region == rname]
    for v, g in sub.groupby("variable"):
        reg.append(dict(region=rname, variable=v, n_areas=len(g), median_value_2026=g.value_2026.median(),
                        median_rank_2026=g.rank_2026.median(), areas_top5=int((g.rank_2026 <= 5).sum()),
                        areas_rank1=int((g.rank_2026 == 1).sum())))
REG = pd.DataFrame(reg)
REG.to_csv(out_dir() / "region_2026_summary.csv", index=False, float_format="%.4g")


# ---------------------------------------------------------------- correlation machinery
def pct_rank(M):
    """Within-row percentile ranks of an area x year matrix (NaN kept), centred at 0."""
    r = rankdata(M, axis=1, nan_policy="omit")
    n = (~np.isnan(M)).sum(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(np.isnan(M), np.nan, (r - 0.5) / n - 0.5)


def corr(Rx, Ry):
    ok = ~np.isnan(Rx) & ~np.isnan(Ry)
    if ok.sum() < 10:
        return np.nan, int(ok.sum())
    x, y = Rx[ok], Ry[ok]
    return float(np.corrcoef(x, y)[0, 1]), int(ok.sum())


def test(df, xv, yv, min_years=15):
    """df: rows of the chosen areas, years 1991-2025."""
    X = df.pivot(index="area_id", columns="year", values=xv)
    Y = df.pivot(index="area_id", columns="year", values=yv).reindex(index=X.index, columns=X.columns)
    both = X.notna() & Y.notna()
    keep = both.sum(axis=1) >= min_years
    X, Y = X[keep], Y[keep]
    if len(X) == 0:
        return None
    Xm = X.where(Y.notna()).to_numpy(float)
    Ym = Y.where(X.notna()).to_numpy(float)
    Rx, Ry = pct_rank(Xm), pct_rank(Ym)
    r, n = corr(Rx, Ry)
    if np.isnan(r):
        return None
    T = Rx.shape[1]
    # permutation of year labels of the predictor (ranks recomputed on the overlapping years)
    Xraw = X.to_numpy(float)
    Yraw = Y.to_numpy(float)
    cnt = 0
    perm_r = []
    for _ in range(NPERM):
        p = RNG.permutation(T)
        Xp = Xraw[:, p]
        okp = ~np.isnan(Xp) & ~np.isnan(Yraw)
        rp, _ = corr(pct_rank(np.where(okp, Xp, np.nan)), pct_rank(np.where(okp, Yraw, np.nan)))
        perm_r.append(rp)
    perm_r = np.array(perm_r)
    pval = (1 + np.sum(np.abs(perm_r) >= abs(r) - 1e-12)) / (NPERM + 1)
    boots = []
    for _ in range(NBOOT):
        b = RNG.integers(0, T, T)
        rb, _ = corr(Rx[:, b], Ry[:, b])
        boots.append(rb)
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    # per-area Spearman: how many areas agree in sign
    per = []
    for i in range(len(Rx)):
        ok = ~np.isnan(Rx[i]) & ~np.isnan(Ry[i])
        if ok.sum() >= min_years:
            per.append(np.corrcoef(Rx[i, ok], Ry[i, ok])[0, 1])
    per = np.array(per)
    return dict(r_within=r, ci_lo=lo, ci_hi=hi, p_perm=pval, n_area_years=n, n_areas=len(X),
                n_years=int((~np.isnan(Rx)).any(axis=0).sum()), areas_pos=int((per > 0).sum()),
                areas_neg=int((per < 0).sum()), median_area_r=float(np.median(per)) if len(per) else np.nan)


def bh(p):
    p = np.asarray(p, float)
    n = np.sum(~np.isnan(p))
    order = np.argsort(np.where(np.isnan(p), np.inf, p))
    q = np.full(len(p), np.nan)
    prev = 1.0
    for k in range(n - 1, -1, -1):
        i = order[k]
        prev = min(prev, p[i] * n / (k + 1))
        q[i] = prev
    return q


H = P[P.year.between(1991, 2025)].copy()
burnyrs = H.groupby("area_id").burned_ha.apply(lambda s: (s > 0).sum())
forest = H.groupby("area_id").forest_ha.first()
BURN_AREAS = burnyrs[(burnyrs >= 5) & (forest.reindex(burnyrs.index) >= 1e5)].index
S["burn_sample_areas"] = int(len(BURN_AREAS))
S["burn_sample_by_region"] = H[H.area_id.isin(BURN_AREAS)].drop_duplicates("area_id").region.value_counts().to_dict()
log(f"burn sample: {len(BURN_AREAS)} areas {S['burn_sample_by_region']}", fh)

# ---------------------------------------------------------------- burn tests
rows = []
for rname in REGIONS:
    sub = H[H.area_id.isin(BURN_AREAS)]
    if rname != "Canada":
        sub = sub[sub.region == rname]
    for xv in INDICES + STATION:
        for yv in OUTCOMES:
            res = test(sub, xv, yv)
            if res:
                rows.append(dict(region=rname, predictor=xv, outcome=yv, **res))
    log(f"burn tests done: {rname}", fh)
B = pd.DataFrame(rows)
B["q_bh"] = bh(B.p_perm)
B["expected_sign"] = B.predictor.map(lambda v: FIRE_DIR.get(v, np.nan))
B.to_csv(out_dir() / "correlations_burn.csv", index=False, float_format="%.4g")

# ---------------------------------------------------------------- chain tests (all areas with data)
rows = []
LINKS = ([(i, v) for i in INDICES[:5] for v in SNOW + SPRING + ["p_ndjfm_pct"]] +
         [(i, v) for i in INDICES[5:] for v in SPRING] +
         [("melt_anom_days", "t_amj_anom_c"), ("melt_anom_days", "p_amj_pct"), ("snowfall_pct", "melt_anom_days"),
          ("max_snow_depth_pct", "melt_anom_days"), ("swe_apr1_pct", "melt_anom_days"), ("p_ndjfm_pct", "snowfall_pct"),
          ("p_ndjfm_pct", "max_snow_depth_pct"), ("t_amj_anom_c", "p_amj_pct"), ("p_son_prev_pct", "p_amj_pct")])
for rname in REGIONS:
    sub = H if rname == "Canada" else H[H.region == rname]
    for xv, yv in LINKS:
        res = test(sub, xv, yv)
        if res:
            rows.append(dict(region=rname, predictor=xv, outcome=yv, **res))
    log(f"chain tests done: {rname}", fh)
C = pd.DataFrame(rows)
C["q_bh"] = bh(C.p_perm)
C.to_csv(out_dir() / "correlations_chain.csv", index=False, float_format="%.4g")

S["n_burn_tests"] = int(len(B))
S["burn_p05"] = int((B.p_perm < 0.05).sum())
S["burn_q10"] = int((B.q_bh < 0.10).sum())
S["n_chain_tests"] = int(len(C))
S["chain_p05"] = int((C.p_perm < 0.05).sum())
S["chain_q10"] = int((C.q_bh < 0.10).sum())
json.dump(S, open(D / "summary_07.json", "w"), indent=1, default=str)
log(json.dumps(S, default=str), fh)

# ---------------------------------------------------------------- 2023-2026 run vs earlier periods
# Per region and variable: median across areas of the area anomaly for each year 2023-2026, the
# four-year mean (area mean of the 4 years, then median across areas), and the same for the decades
# 1991-2000, 2001-2010, 2011-2020 and 2013-2022; plus the share of areas on the fire-favouring side
# of their own 1991-2020 median. Indices: value per year with rank among fire years 1951-2026.
PERIODS = {"1991-2000": range(1991, 2001), "2001-2010": range(2001, 2011), "2011-2020": range(2011, 2021),
           "2013-2022": range(2013, 2023), "2023-2026": range(2023, 2027)}
run = []
for rname in REGIONS:
    sub = P if rname == "Canada" else P[P.region == rname]
    for v in STATION:
        med = sub[sub.year.between(1991, 2020)].groupby("area_id")[v].median()
        for lab, yrs in list({str(y): [y] for y in range(2023, 2027)}.items()) + list(PERIODS.items()):
            g = sub[sub.year.isin(list(yrs))].groupby("area_id")[v].mean().dropna()
            if len(g) == 0:
                continue
            fav = ((g - med.reindex(g.index)) * FIRE_DIR[v] > 0).mean()
            run.append(dict(region=rname, variable=v, period=lab, n_areas=len(g), median_area_value=g.median(),
                            share_areas_fire_side=fav))
RUN = pd.DataFrame(run)
RUN.to_csv(out_dir() / "run_2023_2026_by_region.csv", index=False, float_format="%.4g")
I = pd.read_csv(OUT / "indices_by_fire_year.csv")
I = I[I.fire_year >= 1951]
irows = []
for v in INDICES:
    s = I.set_index("fire_year")[v].dropna()
    base = s.loc[1991:2020]
    for y in range(2023, 2027):
        if y in s:
            irows.append(dict(index=v, period=str(y), value=s[y], rank_high_1951_2026=int((s > s[y]).sum() + 1),
                              n_years=len(s), z_vs_1991_2020=(s[y] - base.mean()) / base.std()))
    for lab, yrs in PERIODS.items():
        x = s.reindex(list(yrs)).dropna()
        irows.append(dict(index=v, period=lab, value=x.mean(), n_years=len(x),
                          z_vs_1991_2020=(x.mean() - base.mean()) / base.std()))
IR = pd.DataFrame(irows)
IR.to_csv(out_dir() / "indices_2023_2026.csv", index=False, float_format="%.4g")
# national burn context: forest share burned by year from the panel (all areas)
nat = P.groupby("year")[["forest_burned_ha", "forest_ha"]].sum()
nat["share"] = nat.forest_burned_ha / nat.forest_ha
S["national_share_top6"] = nat.share.sort_values(ascending=False).head(6).round(5).to_dict()
json.dump(S, open(D / "summary_07.json", "w"), indent=1, default=str)
log(json.dumps(S["national_share_top6"], default=str), fh)
