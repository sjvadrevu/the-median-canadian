"""The 2023-2026 run: which drivers were unusual in all four years, and does the model predict the run?

National drivers per year (1991-2026 where available): forest share burned (NBAC/M3, Canada), lightning- and
human-caused fire counts (NFD; 2026 official), station extreme fire weather days (analysis/weather national
mean over consistent stations), forest-weighted CDM D1+/D2+ share (Apr-Sep max and Apr-Jun mean, areas in the
model panel; 2015+ only for YT/NT), forest share burned in the previous 10 years, ignition season start.
For each driver: value in each of 2023-2026, rank among all years, z-score against the reference period
(1991-2022, or 2003-2022 for drought), and whether all four years sit above the reference 75th percentile.
By area: mean within-area anomaly of each driver in 2023-2026 vs the area's reference mean, with the outcome.
Model test: ridge with area fixed effects (same features as 09_model.py) trained on 2003-2022 only, predicting
2023-2026 as a block; national forest-weighted share predicted vs actual each year, against the same
ratio for 2003-2022 leave-one-year-out predictions (calibration baseline, since back-transforming log
predictions understates totals).
Outputs: run_national_drivers.csv, run_driver_summary.csv, run_by_area.csv, run_model_check.csv, log_10.txt
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from common import FOREST_DIR, OUT, WEATHER_DIR, area_dir, log

D = area_dir()
fh = open(D / "log_10.txt", "w")
OFF = 1e-4
RUN = [2023, 2024, 2025, 2026]
P = pd.read_csv(OUT / "model_panel.csv")
AF = pd.read_csv(D / "area_forest.csv").set_index("fma_id")
P["fw"] = P.fma_id.map(AF.forest_ha)

# ------------------------------------------------------------- national drivers
nat = pd.DataFrame(index=pd.Index(range(1991, 2027), name="year"))
cs = pd.read_csv(FOREST_DIR / "canada_forest_share_by_year.csv", index_col=0).share_forest_burned
nat["canada_forest_share_burned"] = cs
nb = pd.read_csv(OUT / "cause_by_year_national.csv")
nb = nb[nb.series.str.startswith("NFD")].set_index("year")
nat["n_lightning_fires"] = nb.n_lightning
nat["n_human_fires"] = nb.n_human
nat["ha_lightning_fires"] = nb.ha_lightning
nat["ha_human_fires"] = nb.ha_human
wn = pd.read_csv(WEATHER_DIR / "work" / "national_by_year.csv").set_index("year")
nat["station_mean_extreme_days"] = wn.mean_ext_days
nat["station_pooled_ratio"] = wn.pooled_ratio


def fwmean(col, d=P):
    g = d[d[col].notna()]
    return (g[col] * g.fw).groupby(g.year).sum() / g.fw.groupby(g.year).sum()


for c in ["d1_area_max_apr_sep", "d2_area_max_apr_sep", "d1_area_mean_apr_jun"]:
    nat[f"drought_{c}_forest_weighted"] = fwmean(c)
    # robustness: provinces where the CDM shows dryness in most years from 2003 (excludes QC, NL, YT, NT,
    # whose northern assessment looks thinner or absent in early years; drought_coverage_check.csv)
    nat[f"drought_{c}_forest_weighted_south"] = fwmean(c, P[P.province.isin(["BC", "AB", "SK", "MB", "ON", "NB", "NS", "PE"])])
nat["prior10_share_forest_weighted"] = fwmean("prior10_share")
tm = pd.read_csv(OUT / "timing_by_year_scope.csv")
nat["ignition_start_p10_doy"] = tm[tm.scope == "CA"].set_index("year").start_p10_doy
nat["area_p50_doy"] = tm[tm.scope == "CA"].set_index("year").area_p50_doy
nat = nat.reset_index()
nat.to_csv(OUT / "run_national_drivers.csv", index=False)

rows = []
for c in nat.columns[1:]:
    s = nat.set_index("year")[c]
    ref = s[(s.index <= 2022) & (s.index >= (2003 if c.startswith("drought") else 1991))].dropna()
    if len(ref) < 5:
        continue
    r = dict(driver=c, ref_period=f"{ref.index.min()}-{ref.index.max()}", ref_mean=ref.mean(), ref_p75=ref.quantile(.75),
             ref_max=ref.max())
    allyrs = pd.concat([ref, s[RUN]]).dropna()
    for y in RUN:
        v = s.get(y, np.nan)
        r[f"v{y}"] = v
        r[f"z{y}"] = (v - ref.mean()) / ref.std()
        r[f"rank{y}_of_{len(allyrs)}"] = int((allyrs > v).sum() + 1) if pd.notna(v) else np.nan
    r["run_mean"] = s[RUN].mean()
    r["run_mean_z"] = (r["run_mean"] - ref.mean()) / ref.std()
    r["all_four_above_ref_p75"] = bool((s[RUN] > r["ref_p75"]).all())
    r["all_four_above_ref_mean"] = bool((s[RUN] > ref.mean()).all())
    rows.append(r)
S = pd.DataFrame(rows)
S.to_csv(OUT / "run_driver_summary.csv", index=False)
log(S.round(3).to_string(), fh)

# ------------------------------------------------------------- by area
feats = ["d1_area_max_apr_sep", "d2_area_max_apr_sep", "d1_area_mean_apr_jun", "ext_anom_median", "log_n_lightning",
         "log_n_human", "start_p10_doy", "prior10_share"]
ref = P[(P.year >= 2003) & (P.year <= 2022)]
mu = ref.groupby("fma_id")[feats + ["y"]].mean()
sd = ref.groupby("fma_id")[feats + ["y"]].std()
run = P[P.year.isin(RUN)].groupby("fma_id")[feats + ["y"]].mean()
Z = ((run - mu) / sd.replace(0, np.nan)).add_suffix("_run_z")
share_run = P[P.year.isin(RUN)].groupby("fma_id").forest_share_burned_scaled.sum()
share_ref4 = ref.groupby("fma_id").forest_share_burned.mean() * 4
BA = pd.DataFrame(dict(forest_share_burned_2023_2026=share_run, expected_4yr_at_2003_2022_rate=share_ref4))
BA["ratio_run_vs_ref"] = BA.forest_share_burned_2023_2026 / BA.expected_4yr_at_2003_2022_rate.replace(0, np.nan)
BA = BA.join(Z).join(P.drop_duplicates("fma_id").set_index("fma_id")[["province", "area_name"]])
BA["forest_ha"] = AF.forest_ha.reindex(BA.index)
BA = BA.sort_values("forest_share_burned_2023_2026", ascending=False)
BA.reset_index().to_csv(OUT / "run_by_area.csv", index=False)
log(BA.head(20).round(2).to_string(), fh)
# forest-weighted share of run burned area by sign of driver anomaly
burned_fw = (BA.forest_share_burned_2023_2026 * BA.forest_ha)
for f in feats:
    z = BA[f + "_run_z"]
    ok = z.notna()
    log(f"{f}: share of 2023-2026 burned forest in areas with run-mean anomaly > 0: "
        f"{burned_fw[ok & (z > 0)].sum() / burned_fw[ok].sum():.3f} (areas with data {ok.sum()})", fh)

# ------------------------------------------------------------- model check
FEATS = {"P_all": ["d1_area_mean_apr_jun", "d1_area_max_apr_sep", "d2_area_max_apr_sep", "log_n_lightning",
                   "log_n_human", "start_p10_doy", "prior10_share", "prior20_share"]}
FEATS["P_all_no_ignition"] = ["d1_area_mean_apr_jun", "d1_area_max_apr_sep", "d2_area_max_apr_sep", "prior10_share", "prior20_share"]
FEATS["FE_only"] = []


def fit_pred(tr, te, cols):
    ym = tr.groupby("fma_id").y.mean()
    base = ym.reindex(te.fma_id).values
    if not cols:
        return base
    m = tr.groupby("fma_id")[cols].mean()
    Xtr = (tr[cols] - m.reindex(tr.fma_id).values).fillna(0).values
    Xte = (te[cols] - m.reindex(te.fma_id).values).fillna(0).values
    s = Xtr.std(0)
    s[s == 0] = 1
    r = Ridge(alpha=10).fit(Xtr / s, tr.y.values - ym.reindex(tr.fma_id).values)
    return base + r.predict(Xte / s)


d = P[(P.year >= 2003)].copy()
out = []
for mname, cols in FEATS.items():
    # baseline: LOYO within 2003-2022
    for y in range(2003, 2023):
        tr, te = d[(d.year != y) & (d.year <= 2022)], d[d.year == y]
        p = fit_pred(tr, te, cols)
        out.append(dict(model=mname, scheme="LOYO 2003-2022", year=y,
                        actual=(te.forest_share_burned * te.fw).sum() / te.fw.sum(),
                        predicted=((10 ** p - OFF).clip(0) * te.fw).sum() / te.fw.sum()))
    tr = d[d.year <= 2022]
    for y in RUN:
        te = d[d.year == y]
        p = fit_pred(tr, te, cols)
        out.append(dict(model=mname, scheme="train 2003-2022, predict run", year=y,
                        actual=(te.forest_share_burned_scaled * te.fw).sum() / te.fw.sum(),
                        predicted=((10 ** p - OFF).clip(0) * te.fw).sum() / te.fw.sum()))
MC = pd.DataFrame(out)
MC["ratio_actual_to_predicted"] = MC.actual / MC.predicted
MC.to_csv(OUT / "run_model_check.csv", index=False)
for mname in FEATS:
    m = MC[MC.model == mname]
    base = m[m.scheme.str.startswith("LOYO")]
    rn = m[~m.scheme.str.startswith("LOYO")]
    cal = base.actual.sum() / base.predicted.sum()
    log(f"{mname}: 2003-2022 LOYO total actual/predicted {cal:.2f} (median yearly ratio {base.ratio_actual_to_predicted.median():.2f}); "
        f"run 2023-2026 actual {rn.actual.sum():.4f} vs predicted {rn.predicted.sum():.4f} (ratio {rn.actual.sum() / rn.predicted.sum():.2f}, "
        f"{rn.actual.sum() / rn.predicted.sum() / cal:.2f} x the calibration ratio); by year: " +
        ", ".join(f"{int(r.year)} {r.actual:.4f}/{r.predicted:.4f}" for r in rn.itertuples()), fh)
