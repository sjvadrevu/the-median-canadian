"""Sensitivity of area burned to fire-season climate (area x year panel) and a 2023-2026 statistical counterfactual.

Panel: eligible fma_v2 areas (forest >= 100,000 ha and >= 5% of land, not Nunavut; same rule as the cause model)
with AHCCD-based climate for every year (climate_area_year.csv from 03), years 1972-2026.
Outcome: all-land hectares burned (work/area_burned_ha_1972_2026.csv; NBAC 1972-2025, 2026 M3 scaled to official).
Climate predictors (within-area through the area fixed effects):
  t_mjja    May-Aug temperature anomaly vs 1961-1990 (C)
  lp_amjjas ln(Apr-Sep precipitation / 1961-1990 normal)
  lp_sondjfm ln(previous Sep-Mar precipitation / normal)
Models (fit on 1972-2025; 2026 is predicted, not fitted, as in the cause model):
  M1 PPML  E[ha] = exp(area FE + linear year trend + b.x)                     main
  M0 PPML  E[ha] = exp(area FE + b.x)            (no year control)
  M2 PPML  E[ha] = exp(area FE + year FE + b.x)   (b identified only from differences between areas within a year)
  M3 OLS   log10(share of land burned + 1e-4) = area FE + linear trend + b.x  (cause-model structure; expectation
           back-transformed with a smearing factor)
  M1_pre23 = M1 fit on 1972-2022 only.
PPML = Poisson pseudo-maximum likelihood (IRLS with fixed effects removed by weighted alternating demeaning), which handles zero years and gives
expectations in hectares directly. Areas with no burning in the fitting years are dropped (their FE is -inf).
Counterfactual for 2023-2026 (each area-year keeps its own fixed effect and trend):
  warming dT = regional mean May-Aug temperature 2016-2026 minus 1961-1990 (climate_recent_vs_normal.csv)
  S_T     temperature - dT, precipitation as observed
  S_P     precipitation set to the 1961-1990 normal (ln ratio 0), temperature as observed
  S_TP    both (the requested counterfactual)
  S_TPtrend temperature - dT and precipitation shifted by the regional 2016-2026 vs 1961-1990 change only
Ratio = expected ha under observed climate / expected ha under the counterfactual, summed over 2023-2026 (and per
year). Model-weighted: expectations from the model. Actual-weighted: the actual hectares of each area-year are
multiplied by exp(b.(x_cf - x_obs)) (keeps the actual spatial pattern; avoids the model's underprediction).
Uncertainty: 500 bootstrap resamples of fitting years (all areas of a drawn year together), refit, recompute.
Outputs: model_coefficients.csv, counterfactual_2023_2026.csv, counterfactual_by_year.csv,
         counterfactual_by_region.csv, model_fit_check.csv, work/panel_climate_burn.csv, work/log_09.txt
"""
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd

from common import WORK, OUT, areas, log

warnings.filterwarnings("ignore")
fh = open(WORK / "log_09.txt", "w")
NB = int(__import__("os").environ.get("NB", 500))
rng = np.random.default_rng(2026)
A = areas()
C = pd.read_csv(OUT / "climate_area_year.csv")
O = pd.read_csv(WORK / "area_burned_ha_1972_2026.csv")
P = O.merge(C[["fma_id", "year", "region", "t_mjja", "p_amjjas", "p_sondjfm"]], on=["fma_id", "year"], how="inner")
P = P[P.fma_id.isin(A[A.eligible].fma_id) & (P.year >= 1972)].copy()
P["lp_amjjas"] = np.log(P.p_amjjas / 100)
P["lp_sondjfm"] = np.log(P.p_sondjfm / 100)
P["y"] = P.burned_ha_scaled
X = ["t_mjja", "lp_amjjas", "lp_sondjfm"]
P = P.dropna(subset=X)
cnt = P.groupby("fma_id").year.count()
keep = cnt[cnt >= 45].index                   # areas with climate in >= 45 of 55 years
P = P[P.fma_id.isin(keep)].reset_index(drop=True)
P.to_csv(WORK / "panel_climate_burn.csv", index=False)
log(f"panel: {P.fma_id.nunique()} areas, {len(P)} area-years, {P.year.min()}-{P.year.max()}; "
    f"share of eligible forest {A[A.fma_id.isin(keep)].forest_ha.sum() / A[A.eligible].forest_ha.sum():.3f}; "
    f"share of 2023-2026 burned ha in eligible areas covered {P[P.year >= 2023].y.sum() / O[O.fma_id.isin(A[A.eligible].fma_id) & (O.year >= 2023)].burned_ha_scaled.sum():.3f}", fh)

RC = pd.read_csv(OUT / "climate_recent_vs_normal.csv")
dT = RC[RC.variable == "t_mjja"].set_index("scope")["diff"]
dPa = np.log(RC[RC.variable == "p_amjjas"].set_index("scope").eval("mean_2016_2026 / mean_1961_1990"))
dPs = np.log(RC[RC.variable == "p_sondjfm"].set_index("scope").eval("mean_2016_2026 / mean_1961_1990"))
log(f"warming used (C): {dT.round(3).to_dict()}", fh)
T = P[P.year >= 2023].copy()
T["dT"] = T.region.map(dT)


def scen(df, s):
    x = df[X].copy()
    if s in ("S_T", "S_TP", "S_TPtrend"):
        x["t_mjja"] = x.t_mjja - df.dT
    if s in ("S_P", "S_TP"):
        x["lp_amjjas"] = 0.0
        x["lp_sondjfm"] = 0.0
    if s == "S_TPtrend":
        x["lp_amjjas"] = x.lp_amjjas - df.region.map(dPa)
        x["lp_sondjfm"] = x.lp_sondjfm - df.region.map(dPs)
    return x


SCEN = ["S_T", "S_P", "S_TP", "S_TPtrend"]


TRENDED = ("M1", "M3", "M1_pre23")


def demean(V, w, groups, tol=1e-10, maxit=500):
    """Weighted within-transformation of the columns of V over one or two sets of group codes
    (alternating projections)."""
    V = V.copy()
    for _ in range(maxit):
        delta = 0.0
        for g, ng in groups:
            sw = np.bincount(g, weights=w, minlength=ng)
            for j in range(V.shape[1]):
                mu = np.bincount(g, weights=w * V[:, j], minlength=ng) / np.where(sw > 0, sw, 1)
                V[:, j] -= mu[g]
                delta = max(delta, np.abs(mu).max())
        if len(groups) == 1 or delta < tol:
            break
    return V


def fit(df, model):
    """PPML (Poisson pseudo-ML by IRLS, fixed effects removed by weighted demeaning) for M1, M2, M1_pre23;
    OLS within-area for M3. Returns area effects, year effects (M2), trend and climate coefficients."""
    df = df.copy()
    if model == "M1_pre23":
        df = df[df.year <= 2022]
    pos = df.groupby("fma_id").y.sum()
    df = df[df.fma_id.isin(pos[pos > 0].index)]
    areas_ = np.array(sorted(df.fma_id.unique()))
    ai = np.searchsorted(areas_, df.fma_id.values)
    cols = X + (["trend"] if model in TRENDED else [])
    Z = np.c_[df[X].values, ((df.year.values - 2000) / 10.0)[:, None]] if model in TRENDED else df[X].values.astype(float)
    groups = [(ai, len(areas_))]
    years_ = None
    if model == "M2":
        years_ = np.array(sorted(df.year_lab.astype(str).unique()))
        ti = np.searchsorted(years_, df.year_lab.astype(str).values)
        groups.append((ti, len(years_)))
    y = df.y.values.astype(float)
    if model == "M3":
        yy = np.log10(y / df.land_ha_grid.values + 1e-4)
        w = np.ones(len(y))
        V = demean(np.c_[yy, Z], w, groups)
        beta = np.linalg.lstsq(V[:, 1:], V[:, 0], rcond=None)[0]
        resid = V[:, 0] - V[:, 1:] @ beta
        fe = yy - Z @ beta
        alpha = pd.Series(np.bincount(ai, weights=fe) / np.bincount(ai), index=areas_)
        return dict(beta=beta, cols=cols, alpha=alpha, gamma=None, model=model, smear=np.mean(10 ** resid))
    mu = (y + y.mean()) / 2
    eta = np.log(mu)
    dev_old = np.inf
    for it in range(200):
        w = mu
        z = eta + (y - mu) / mu
        V = demean(np.c_[z, Z], w, groups)
        sw = np.sqrt(w)
        beta = np.linalg.lstsq(V[:, 1:] * sw[:, None], V[:, 0] * sw, rcond=None)[0]
        resid = V[:, 0] - V[:, 1:] @ beta
        eta = z - resid
        eta = np.clip(eta, -50, 50)
        mu = np.exp(eta)
        dev = 2 * np.sum(np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / mu), 0) - (y - mu))
        if abs(dev - dev_old) / max(abs(dev), 1) < 1e-10:
            break
        dev_old = dev
    fe = eta - Z @ beta                      # additive fixed-effect component
    if model == "M2":
        al = np.zeros(len(areas_)); ga = np.zeros(len(years_))
        for _ in range(500):
            al_new = np.bincount(ai, weights=fe - ga[ti]) / np.bincount(ai)
            ga_new = np.bincount(ti, weights=fe - al_new[ai]) / np.bincount(ti)
            if max(np.abs(al_new - al).max(), np.abs(ga_new - ga).max()) < 1e-10:
                al, ga = al_new, ga_new
                break
            al, ga = al_new, ga_new
        alpha, gamma = pd.Series(al, index=areas_), pd.Series(ga, index=years_)
    else:
        alpha, gamma = pd.Series(np.bincount(ai, weights=fe) / np.bincount(ai), index=areas_), None
    return dict(beta=beta, cols=cols, alpha=alpha, gamma=gamma, model=model, smear=None, n_iter=it)


def predict(f, df, x):
    m = f["model"]
    df = df[df.fma_id.isin(f["alpha"].index)]
    x = x.loc[df.index]
    b = f["beta"]
    lin = f["alpha"].reindex(df.fma_id).values + x[X].values @ b[:len(X)]
    if m in TRENDED:
        lin = lin + b[len(X)] * (df.year.values - 2000) / 10.0
    if m == "M3":
        return df.index, np.maximum(10 ** lin * f["smear"] - 1e-4, 0) * df.land_ha_grid.values
    if m == "M2":
        g = f["gamma"]
        yv = df.year.astype(str).map(g).values.astype(float)
        fill = g[[str(t) for t in range(2016, 2026) if str(t) in g.index]].mean()
        yv = np.where(np.isnan(yv), fill, yv)      # 2026 is not in the fit: mean of the 2016-2025 year effects
        lin = lin + yv
    return df.index, np.exp(lin)


def ratios(f, T):
    out = {}
    idx, mu_obs = predict(f, T, T[X])
    b = f["beta"][:len(X)]
    Ti = T.loc[idx]
    out["pred_obs_total"] = mu_obs.sum()
    out["actual_total"] = Ti.y.sum()
    for s in SCEN:
        xc = scen(Ti, s)
        _, mu_cf = predict(f, Ti, xc)
        out[f"{s}_model"] = mu_obs.sum() / mu_cf.sum()
        dlin = (xc.values - Ti[X].values) @ b
        mult = 10 ** dlin if f["model"] == "M3" else np.exp(dlin)     # M3 is in log10 units
        out[f"{s}_actual"] = Ti.y.sum() / (Ti.y.values * mult).sum()
        for yv in (2023, 2024, 2025, 2026):
            m_ = (Ti.year == yv).values
            out[f"{s}_model_{yv}"] = mu_obs[m_].sum() / mu_cf[m_].sum()
            out[f"{s}_actual_{yv}"] = Ti.y.values[m_].sum() / (Ti.y.values[m_] * mult[m_]).sum()
        for reg in Ti.region.unique():
            m_ = (Ti.region == reg).values
            out[f"{s}_actual_reg_{reg}"] = Ti.y.values[m_].sum() / max((Ti.y.values[m_] * mult[m_]).sum(), 1e-9)
            out[f"{s}_model_reg_{reg}"] = mu_obs[m_].sum() / mu_cf[m_].sum()
    return out


TRAIN = P[P.year <= 2025].copy()
TRAIN["year_lab"] = TRAIN.year
MODELS = ["M1", "M0", "M2", "M3", "M1_pre23"]
coef_rows, point, boots = [], {}, {m: [] for m in MODELS}
t0 = time.time()
for m in MODELS:
    f = fit(TRAIN, m)
    b = f["beta"]
    point[m] = ratios(f, T)
    for k, v in enumerate(f["cols"]):
        coef_rows.append(dict(model=m, variable=v, coef=b[k]))
    log(f"{m}: coef {dict(zip(X, np.round(b, 3)))}; pred/actual 2023-2026 {point[m]['pred_obs_total'] / point[m]['actual_total']:.3f}; "
        f"S_TP model {point[m]['S_TP_model']:.3f}, S_T model {point[m]['S_T_model']:.3f} ({time.time() - t0:.0f}s)", fh)
# bootstrap by year
M2FULL = fit(TRAIN, "M2")
yrs = np.array(sorted(TRAIN.year.unique()))
for k in range(NB):
    draw = rng.choice(yrs, len(yrs), replace=True)
    parts = []
    for j, yv in enumerate(draw):
        g = TRAIN[TRAIN.year == yv].copy()
        g["year_lab"] = f"{yv}_{j}"
        parts.append(g)
    BT = pd.concat(parts, ignore_index=True)
    for m in MODELS:
        if m == "M1_pre23" and (draw <= 2022).sum() < 30:
            continue
        try:
            fb = fit(BT, m)
        except Exception as e:
            continue
        if m == "M2":
            # the drawn year copies have their own year effects, which are not the 2023-2026 effects: keep the
            # full-sample M2 fixed effects for the expectations and take only b from the bootstrap fit
            fb = dict(M2FULL, beta=fb["beta"])
        r = ratios(fb, T)
        r.update({f"coef_{v}": fb["beta"][i] for i, v in enumerate(fb["cols"])})
        boots[m].append(r)
    if k % 50 == 0:
        log(f"bootstrap {k}/{NB} {time.time() - t0:.0f}s", fh)

rows, yrows, rrows = [], [], []
for m in MODELS:
    Bm = pd.DataFrame(boots[m])
    for v in [c["variable"] for c in coef_rows if c["model"] == m]:
        cr = next(c for c in coef_rows if c["model"] == m and c["variable"] == v)
        cr["boot_lo"], cr["boot_hi"] = np.percentile(Bm[f"coef_{v}"], [2.5, 97.5])
        cr["boot_se"] = Bm[f"coef_{v}"].std()
        cr["n_boot"] = len(Bm)
    for s in SCEN:
        for w in ("model", "actual"):
            k_ = f"{s}_{w}"
            lo, hi = np.percentile(Bm[k_], [2.5, 97.5])
            rows.append(dict(model=m, scenario=s, weighting=w, ratio=point[m][k_], boot_lo=lo, boot_hi=hi,
                             boot_median=np.median(Bm[k_]), share_attributable=1 - 1 / point[m][k_], n_boot=len(Bm)))
            for yv in (2023, 2024, 2025, 2026):
                kk = f"{k_}_{yv}"
                lo, hi = np.percentile(Bm[kk], [2.5, 97.5])
                yrows.append(dict(model=m, scenario=s, weighting=w, year=yv, ratio=point[m][kk], boot_lo=lo, boot_hi=hi))
            for kk in [c for c in point[m] if c.startswith(f"{k_}_reg_")]:
                lo, hi = np.percentile(Bm[kk].dropna(), [2.5, 97.5])
                rrows.append(dict(model=m, scenario=s, weighting=w, region=kk.split("_reg_")[1], ratio=point[m][kk], boot_lo=lo, boot_hi=hi))
CO = pd.DataFrame(coef_rows)
CO["pct_per_unit"] = (np.exp(CO.coef) - 1) * 100
CO.loc[CO.model == "M3", "pct_per_unit"] = (10 ** CO.loc[CO.model == "M3", "coef"] - 1) * 100
CO.to_csv(OUT / "model_coefficients.csv", index=False)
R = pd.DataFrame(rows)
R.to_csv(OUT / "counterfactual_2023_2026.csv", index=False)
pd.DataFrame(yrows).to_csv(OUT / "counterfactual_by_year.csv", index=False)
pd.DataFrame(rrows).to_csv(OUT / "counterfactual_by_region.csv", index=False)
fit_rows = [dict(model=m, actual_2023_2026_ha=point[m]["actual_total"], predicted_obs_climate_ha=point[m]["pred_obs_total"],
                 actual_over_predicted=point[m]["actual_total"] / point[m]["pred_obs_total"]) for m in MODELS]
# per-year fit for M1
f1 = fit(TRAIN, "M1")
idx, mu = predict(f1, P, P[X])
PP = P.loc[idx].assign(pred=mu)
yfit = PP.groupby("year")[["y", "pred"]].sum()
for yv, r in yfit.iterrows():
    fit_rows.append(dict(model="M1 by year", year=yv, actual_ha=r.y, predicted_ha=r.pred, actual_over_predicted=r.y / r.pred))
from scipy import stats as _st
FC = pd.DataFrame(fit_rows)
FC.to_csv(OUT / "model_fit_check.csv", index=False)
lc = _st.spearmanr(yfit.y.loc[:2025], yfit.pred.loc[:2025])[0]
log(f"M1 national yearly totals 1972-2025: Spearman actual vs fitted {lc:.3f}; 2023-2026 actual/predicted by year "
    f"{(yfit.y / yfit.pred).loc[2023:].round(2).to_dict()}", fh)
pd.set_option("display.width", 250)
log(CO.round(4).to_string(), fh)
log(R.round(3).to_string(), fh)
log(pd.DataFrame(yrows).query("model == 'M1'").round(3).to_string(), fh)
log(pd.DataFrame(rrows).query("model == 'M1' and scenario in ['S_T', 'S_TP']").round(3).to_string(), fh)
