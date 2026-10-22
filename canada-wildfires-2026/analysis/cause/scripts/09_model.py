"""Expected vs actual: area x year panel, leave-one-year-out (LOYO) skill, 2026 held out.

Outcome   y = log10(forest share burned + 1e-4)   (1e-4 = 0.01% of the area's forest; zeros become -4)
          plus a two-part check: P(share >= 0.1%) by logistic regression.
Blocks in chain order (each a set of within-area anomalies; area fixed effects always included):
  climate   (optional) every numeric column of analysis/climate/climate_panel.csv joined on fma_id, year
  drought   CDM D1+ share mean Apr-Jun, D1+ and D2+ share max Apr-Sep
  weather   station extreme-day anomaly (median over stations; strict-rule areas only)
  ignition  log(1 + lightning-caused fires), log(1 + human-caused fires), start date of the ignition season
            (10th percentile of fire start dates, NaN when fewer than 5 fires -> area mean)
  fuel      forest share burned in the previous 10 and 20 years
Panels: P_all  = all eligible areas, 2003-2025 (drought available), no weather block
        P_stn  = areas with a strict-rule station, 2003-2025, all blocks
        P_long = all eligible areas 1991-2025, no drought, no weather (longer record)
Models: FE  = area mean only (climatology); ridge on within-area anomalies, blocks added one at a time in chain
        order and each block alone; gradient boosting (HistGradientBoosting, all blocks + area mean of y)
        with permutation importance on LOYO predictions.
Skill:  R2 of y (pooled), within-area R2 (skill beyond each area's own average), Spearman across areas
        within each year (median over years), Spearman of national yearly totals.
Chain links: LOYO within-area R2 of each block's summary variable predicted from the preceding blocks.
2026: models refit on all training years, predict each area; residual = actual - expected (log10), with the
standardized contribution of each predictor (coefficient x anomaly) for the linear model.
Outputs: model_skill.csv, model_chain_links.csv, model_importance.csv, model_2026_by_area.csv,
         model_panel.csv, model_rank_correlations.csv, log_09.txt
"""
import os
import time
import warnings

os.environ.setdefault("OMP_NUM_THREADS", "1")       # shared machine: avoid thread thrashing
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score

from common import AREA_FILE, BASE, DEFAULT_AREA_FILE, OUT, area_attrs, area_dir, log

warnings.filterwarnings("ignore")
D = area_dir()
fh = open(D / "log_09.txt", "w")
OFF = 1e-4
A = area_attrs()
AF = pd.read_csv(D / "area_forest.csv")

# ------------------------------------------------------------- panel
B = pd.read_csv(OUT / "burn_history_by_area_year.csv")
C = pd.read_csv(OUT / "cause_by_area_year.csv")
T = pd.read_csv(OUT / "timing_by_area_year.csv")
Dr = pd.read_csv(OUT / "drought_by_area_year.csv")
Wx = pd.read_csv(OUT / "weather_by_area_year.csv")
Wx = Wx[Wx.rule == "strict"]
P = B[["fma_id", "year", "province", "area_name", "forest_share_burned", "forest_share_burned_scaled",
       "prior10_share", "prior20_share", "prior40_share"]].copy()
P = P.merge(C[["fma_id", "year", "n_lightning", "n_human", "n_undetermined"]], on=["fma_id", "year"], how="left")
P[["n_lightning", "n_human", "n_undetermined"]] = P[["n_lightning", "n_human", "n_undetermined"]].fillna(0)
P = P.merge(T[["fma_id", "year", "start_p10_doy", "n_fires"]], on=["fma_id", "year"], how="left")
P.loc[P.n_fires.fillna(0) < 5, "start_p10_doy"] = np.nan
P = P.merge(Dr[["fma_id", "year", "d1_area_mean_apr_jun", "d1_area_max_apr_sep", "d2_area_max_apr_sep"]], on=["fma_id", "year"], how="left")
# The CDM shows no dryness anywhere in Yukon or NWT in 2003-2014 and frequent dryness from 2015
# (drought_coverage_check.csv): treated as not assessed there before 2015 (missing, not zero).
dcols = ["d1_area_mean_apr_jun", "d1_area_max_apr_sep", "d2_area_max_apr_sep"]
P.loc[P.province.isin(["YT", "NT"]) & (P.year < 2015), dcols] = np.nan
P = P.merge(Wx[["fma_id", "year", "ext_anom_median", "n_stations"]], on=["fma_id", "year"], how="left")
P["log_n_lightning"] = np.log1p(P.n_lightning)
P["log_n_human"] = np.log1p(P.n_human)
P["y_unscaled"] = np.log10(P.forest_share_burned + OFF)
P["y"] = np.log10(P.forest_share_burned_scaled + OFF)        # 2026 scaled to official totals; = unscaled before 2026

BLOCKS = {"drought": ["d1_area_mean_apr_jun", "d1_area_max_apr_sep", "d2_area_max_apr_sep"],
          "weather": ["ext_anom_median"],
          "ignition": ["log_n_lightning", "log_n_human", "start_p10_doy"],
          "fuel": ["prior10_share", "prior20_share"]}
CHAIN = ["drought", "weather", "ignition", "fuel"]
clim_file = BASE / "analysis" / "climate" / "climate_panel.csv"
if AREA_FILE != DEFAULT_AREA_FILE.resolve():
    # non-default area file: analysis/climate writes its panel to work/areas_<hash>/ with the same file hash
    clim_file = BASE / "analysis" / "climate" / "work" / D.name / "climate_panel.csv"
log(f"climate panel: {clim_file}", fh)
if clim_file.exists():
    CP = pd.read_csv(clim_file)
    if "fma_id" not in CP.columns and "area_id" in CP.columns:
        CP = CP.rename(columns={"area_id": "fma_id"})
    # predictors only: drop outcome columns (leakage), station counts, and the vortex stand-in duplicate of ao_jfm
    drop = {"burned_ha", "forest_burned_ha", "forest_ha", "forest_share_burned", "log10_burned_ha",
            "melt_doy_median", "vortex_jfm"}
    CP = CP[[c for c in CP.columns if c not in drop and not c.startswith("n_")]]
    idc = [c for c in CP.columns if c in ("fma_id", "year")]
    num = [c for c in CP.columns if c not in idc and pd.api.types.is_numeric_dtype(CP[c])]
    num = [c for c in num if CP[c].notna().mean() > 0.5]
    P = P.merge(CP[idc + num], on=["fma_id", "year"], how="left")
    BLOCKS = {"climate": num, **BLOCKS}
    CHAIN = ["climate"] + CHAIN
    log(f"climate_panel.csv joined: {len(num)} numeric columns", fh)
else:
    log("climate_panel.csv not found: climate block skipped (rerun this script when it exists)", fh)

# eligible areas: at least 100,000 ha of forest and forest on >= 5% of land; Nunavut excluded (no official
# totals, not assessed by the CDM)
AF["forest_frac"] = AF.forest_ha / AF.land_ha_grid
elig = AF[(AF.forest_ha >= 1e5) & (AF.forest_frac >= 0.05) & (AF.province != "NU")].fma_id
P = P[P.fma_id.isin(elig)].copy()
stn_areas = Wx[(Wx.year >= 2003) & (Wx.year <= 2025)].groupby("fma_id").year.nunique()
stn_areas = stn_areas[stn_areas >= 15].index
P.to_csv(OUT / "model_panel.csv", index=False)
log(f"eligible areas {P.fma_id.nunique()} of {len(A)}; areas with a strict station in >= 15 of 23 years: "
    f"{P[P.fma_id.isin(stn_areas)].fma_id.nunique()}", fh)


# ------------------------------------------------------------- helpers
def within(train, test, cols):
    """Within-area anomalies using training-year means; missing -> 0 (area mean)."""
    mu = train.groupby("fma_id")[cols].mean()
    Xtr = (train[cols] - mu.reindex(train.fma_id).values).fillna(0).values
    Xte = (test[cols] - mu.reindex(test.fma_id).values).fillna(0).values
    sd = Xtr.std(0)
    sd[sd == 0] = 1
    return Xtr / sd, Xte / sd, sd


def fit_predict(train, test, cols, target="y", alpha=10.0):
    ym = train.groupby("fma_id")[target].mean()
    base_te = ym.reindex(test.fma_id).values
    if not cols:
        return base_te, None
    Xtr, Xte, _ = within(train, test, cols)
    ytr = train[target].values - ym.reindex(train.fma_id).values
    r = Ridge(alpha=alpha).fit(Xtr, ytr)
    return base_te + r.predict(Xte), r


def skill(df, pred, target="y"):
    y = df[target].values
    ok = np.isfinite(pred) & np.isfinite(y)
    df = df[ok]
    y, pred = y[ok], pred[ok]
    am = df.groupby("fma_id")[target].transform("mean").values
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    r2w = 1 - ((y - pred) ** 2).sum() / ((y - am) ** 2).sum()
    sp = [stats.spearmanr(g[target], pred[df.year.values == yy])[0] for yy, g in df.groupby("year") if len(g) > 5]
    # national totals: forest-weighted share
    fw = df.fma_id.map(AF.set_index("fma_id").forest_ha).values
    tot = pd.DataFrame(dict(year=df.year.values, a=fw * (10 ** y - OFF), p=fw * (10 ** pred - OFF))).groupby("year").sum()
    return dict(r2=r2, r2_within=r2w, spearman_within_year_median=np.nanmedian(sp),
                spearman_pooled=stats.spearmanr(y, pred)[0], spearman_national_years=stats.spearmanr(tot.a, tot.p)[0],
                n=len(y))


def loyo(df, cols, target="y", years=None):
    pred = np.full(len(df), np.nan)
    yrs = sorted(df.year.unique()) if years is None else years
    for yy in yrs:
        tr = df[df.year != yy]
        te_m = (df.year == yy).values
        pred[te_m], _ = fit_predict(tr, df[te_m], cols, target)
    return pred


# ------------------------------------------------------------- skill tables
panels = {"P_all": (P[(P.year >= 2003) & (P.year <= 2025)], [b for b in CHAIN if b != "weather"]),
          "P_stn": (P[(P.year >= 2003) & (P.year <= 2025) & P.fma_id.isin(stn_areas)], CHAIN),
          "P_long": (P[(P.year >= 1991) & (P.year <= 2025)], [b for b in CHAIN if b in ("ignition", "fuel", "climate")])}
rows = []
t0 = time.time()
for pn, (df, chain) in panels.items():
    df = df.reset_index(drop=True)
    log(f"skill {pn} start {time.time() - t0:.0f}s", fh)
    rows.append(dict(panel=pn, model="FE only (area average)", blocks="", n_areas=df.fma_id.nunique(),
                     years=f"{df.year.min()}-{df.year.max()}", **skill(df, loyo(df, []))))
    cum = []
    for b in chain:
        cum = cum + BLOCKS[b]
        rows.append(dict(panel=pn, model="FE + chain to " + b, blocks="+".join(chain[:chain.index(b) + 1]),
                         n_areas=df.fma_id.nunique(), years=f"{df.year.min()}-{df.year.max()}", **skill(df, loyo(df, cum))))
    for b in chain:
        rows.append(dict(panel=pn, model="FE + " + b + " only", blocks=b, n_areas=df.fma_id.nunique(),
                         years=f"{df.year.min()}-{df.year.max()}", **skill(df, loyo(df, BLOCKS[b]))))
    # without ignition counts (conditions only: what could be known without counting fires)
    cond = sum([BLOCKS[b] for b in chain if b != "ignition"], [])
    rows.append(dict(panel=pn, model="FE + all except ignition", blocks="no ignition", n_areas=df.fma_id.nunique(),
                     years=f"{df.year.min()}-{df.year.max()}", **skill(df, loyo(df, cond))))
    # gradient boosting, all blocks + area mean of y (training years) as a feature
    cols = sum([BLOCKS[b] for b in chain], [])
    pred = np.full(len(df), np.nan)
    for yy in sorted(df.year.unique()):
        tr, te = df[df.year != yy], df[df.year == yy]
        am = tr.groupby("fma_id").y.mean()
        Xtr = np.c_[am.reindex(tr.fma_id).values, tr[cols].values]
        Xte = np.c_[am.reindex(te.fma_id).values, te[cols].values]
        gb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=20,
                                           random_state=0).fit(Xtr, tr.y.values)
        pred[(df.year == yy).values] = gb.predict(Xte)
    rows.append(dict(panel=pn, model="Gradient boosting (all blocks + area mean)", blocks="all",
                     n_areas=df.fma_id.nunique(), years=f"{df.year.min()}-{df.year.max()}", **skill(df, pred)))
    # two-part check: any noticeable burn (>= 0.1% of forest)
    cols_all = sum([BLOCKS[b] for b in chain], [])
    pz = np.full(len(df), np.nan)
    for yy in sorted(df.year.unique()):
        tr, te = df[df.year != yy], df[df.year == yy]
        lab = (tr.forest_share_burned >= 1e-3).astype(int)
        rate = lab.groupby(tr.fma_id).mean().clip(0.02, 0.98)
        Xtr, Xte, _ = within(tr, te, cols_all)
        Xtr = np.c_[np.log(rate / (1 - rate)).reindex(tr.fma_id).values, Xtr]
        Xte = np.c_[np.log(rate / (1 - rate)).reindex(te.fma_id).fillna(0).values, Xte]
        pz[(df.year == yy).values] = LogisticRegression(C=0.5, max_iter=2000).fit(Xtr, lab).predict_proba(Xte)[:, 1]
    lab = (df.forest_share_burned >= 1e-3).astype(int)
    rows.append(dict(panel=pn, model="Two-part check: logistic P(burn >= 0.1% of forest)", blocks="all",
                     n_areas=df.fma_id.nunique(), years=f"{df.year.min()}-{df.year.max()}",
                     auc=roc_auc_score(lab, pz), base_rate=lab.mean(), n=len(df)))
SK = pd.DataFrame(rows)
SK.to_csv(OUT / "model_skill.csv", index=False)
log(SK.round(3).to_string(), fh)

# ------------------------------------------------------------- chain links (P_stn: every block present)
df = panels["P_stn"][0].reset_index(drop=True)
links = []
targets = {"drought": "d1_area_max_apr_sep", "weather": "ext_anom_median", "ignition": "log_n_lightning", "outcome": "y"}
order = CHAIN + ["outcome"]
for i, b in enumerate(order[1:], start=1):
    tgt = targets.get(b)
    if tgt is None:
        continue
    d = df[df[tgt].notna()].reset_index(drop=True)
    prev = order[i - 1]
    for label, cols in [("previous block only", BLOCKS[prev]), ("all earlier blocks", sum([BLOCKS[x] for x in order[:i]], []))]:
        if b == "outcome" and label == "previous block only":
            cols = BLOCKS[prev]
        s = skill(d, loyo(d, cols, target=tgt), target=tgt)
        links.append(dict(link=f"{'+'.join(order[:i]) if label != 'previous block only' else prev} -> {b} ({tgt})",
                          predictors=label, r2_within=s["r2_within"], spearman_within_year_median=s["spearman_within_year_median"], n=s["n"]))
# also the light-weight pairwise links on P_all (more areas)
da = panels["P_all"][0].reset_index(drop=True)
for src, tgt in [("drought", "log_n_lightning"), ("drought", "y"), ("fuel", "y")]:
    s = skill(da, loyo(da, BLOCKS[src], target=tgt), target=tgt)
    links.append(dict(link=f"{src} -> {tgt} (P_all, {da.fma_id.nunique()} areas)", predictors="that block only",
                      r2_within=s["r2_within"], spearman_within_year_median=s["spearman_within_year_median"], n=s["n"]))
LK = pd.DataFrame(links)
LK.to_csv(OUT / "model_chain_links.csv", index=False)
log(LK.round(3).to_string(), fh)

# ------------------------------------------------------------- rank correlations (within-area anomalies)
rc = []
for pn in ["P_all", "P_stn"]:
    df = panels[pn][0]
    yd = df.y - df.groupby("fma_id").y.transform("mean")
    for b in panels[pn][1]:
        for c in BLOCKS[b]:
            xd = df[c] - df.groupby("fma_id")[c].transform("mean")
            ok = xd.notna()
            rc.append(dict(panel=pn, block=b, predictor=c, spearman_within_area=stats.spearmanr(xd[ok], yd[ok])[0], n=int(ok.sum())))
# 2026 cross-section
p26 = P[P.year == 2026]
for b in CHAIN:
    for c in BLOCKS[b]:
        ok = p26[c].notna()
        if ok.sum() > 5:
            rc.append(dict(panel="2026 across areas (levels)", block=b, predictor=c,
                           spearman_within_area=stats.spearmanr(p26.loc[ok, c], p26.loc[ok, "y"])[0], n=int(ok.sum())))
RC = pd.DataFrame(rc)
RC.to_csv(OUT / "model_rank_correlations.csv", index=False)
log(RC.round(3).to_string(), fh)

# ------------------------------------------------------------- importance (gradient boosting, P_all and P_stn)
imp = []
for pn in ["P_all", "P_stn"]:
    df, chain = panels[pn]
    cols = sum([BLOCKS[b] for b in chain], [])
    tr = df
    am = tr.groupby("fma_id").y.mean()
    X = pd.DataFrame(np.c_[am.reindex(tr.fma_id).values, tr[cols].values], columns=["area_mean_y"] + cols)
    # LOYO permutation importance: average over held-out years
    acc = {c: [] for c in X.columns}
    for yy in sorted(df.year.unique()):
        m = (df.year == yy).values
        tr_ = df[~m]
        am_ = tr_.groupby("fma_id").y.mean()
        Xtr = np.c_[am_.reindex(tr_.fma_id).values, tr_[cols].values]
        Xte = pd.DataFrame(np.c_[am_.reindex(df[m].fma_id).values, df[m][cols].values], columns=X.columns)
        gb = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=20,
                                           random_state=0).fit(Xtr, tr_.y.values)
        pi = permutation_importance(gb, Xte, df[m].y.values, n_repeats=5, random_state=0, scoring="neg_mean_squared_error")
        for c, v in zip(X.columns, pi.importances_mean):
            acc[c].append(v)
    for c in X.columns:
        imp.append(dict(panel=pn, predictor=c, block=next((b for b in chain if c in BLOCKS[b]), "area"),
                        perm_importance_mse=np.mean(acc[c])))
IM = pd.DataFrame(imp)
IM.to_csv(OUT / "model_importance.csv", index=False)
log(IM.sort_values(["panel", "perm_importance_mse"], ascending=[True, False]).round(4).to_string(), fh)

# ------------------------------------------------------------- 2026 expected vs actual
out26 = []
for pn in ["P_all", "P_stn"]:
    df, chain = panels[pn]
    cols = sum([BLOCKS[b] for b in chain], [])
    cond = sum([BLOCKS[b] for b in chain if b != "ignition"], [])
    te = P[(P.year == 2026) & P.fma_id.isin(df.fma_id.unique())].copy()
    for mname, cc in [("full", cols), ("no_ignition", cond), ("fe_only", [])]:
        pred, r = fit_predict(df, te, cc)
        te[f"expected_{mname}"] = pred
        if mname == "full":
            Xtr, Xte, sd = within(df, te, cc)
            contrib = Xte * r.coef_
            for j, c in enumerate(cc):
                te[f"contrib_{c}"] = contrib[:, j]
            te["top_contributors"] = [", ".join(f"{cc[k]} {contrib[i, k]:+.2f}" for k in np.argsort(-np.abs(contrib[i]))[:3])
                                      for i in range(len(te))]
            log(f"{pn} ridge coefficients (log10 units per training SD of anomaly): " +
                ", ".join(f"{c} {v:+.3f}" for c, v in zip(cc, r.coef_)), fh)
    te["panel"] = pn
    te["actual_y"] = te.y
    te["resid_full"] = te.y - te.expected_full
    te["resid_no_ignition"] = te.y - te.expected_no_ignition
    te["actual_share"] = te.forest_share_burned_scaled
    te["expected_share_full"] = 10 ** te.expected_full - OFF
    te["expected_share_no_ignition"] = 10 ** te.expected_no_ignition - OFF
    te["expected_share_fe_only"] = 10 ** te.expected_fe_only - OFF
    te["ratio_actual_to_expected_full"] = (te.actual_share + OFF) / (te.expected_share_full + OFF)
    out26.append(te)
O26 = pd.concat(out26, ignore_index=True)
keep = ["panel", "fma_id", "province", "area_name", "actual_share", "forest_share_burned", "expected_share_fe_only",
        "expected_share_no_ignition", "expected_share_full", "ratio_actual_to_expected_full", "resid_full",
        "resid_no_ignition", "top_contributors"] + sum(BLOCKS.values(), []) + [c for c in O26.columns if c.startswith("contrib_")]
O26[[c for c in keep if c in O26.columns]].to_csv(OUT / "model_2026_by_area.csv", index=False)
for pn in ["P_all", "P_stn"]:
    o = O26[O26.panel == pn]
    s = skill(o.assign(y=o.actual_y), o.expected_full.values)
    s2 = skill(o.assign(y=o.actual_y), o.expected_no_ignition.values)
    s0 = skill(o.assign(y=o.actual_y), o.expected_fe_only.values)
    log(f"2026 held out {pn}: full Spearman {s['spearman_pooled']:.3f} R2 {s['r2']:.3f}; no-ignition Spearman {s2['spearman_pooled']:.3f} "
        f"R2 {s2['r2']:.3f}; FE-only Spearman {s0['spearman_pooled']:.3f} R2 {s0['r2']:.3f}; n={s['n']}", fh)
    log(o.sort_values("resid_full", ascending=False)[["area_name", "province", "actual_share", "expected_share_full",
        "expected_share_no_ignition", "ratio_actual_to_expected_full", "top_contributors"]].round(4).to_string(), fh)
