"""Step 3: population-weighted smoke exposure, 2018-2026.

Groups: national, province, CMA (StatCan 2021 census metropolitan areas, CMATYPE B), on-reserve vs off-reserve,
and population sub-groups by weight: total population, children 0-4, people 65+, people in low income (LIM-AT),
population in the low-income universe (comparison base for low income).
Periods: May-Sep (fire season), Jan 1-Oct 19 (comparable across all years incl. 2026), calendar year (2018-2025),
Oct-Apr of each year (non-fire-season: Jan-Apr + Oct-Dec of the same year; 2026 Jan-Apr + Oct 1-19).
Thresholds: strictly greater than 27, 60, 100 ug/m3 (24 h mean).

Outputs: exposure_by_group.csv, daily_popweighted_pm.csv (national and province, total pop),
worst_days.csv, R25 sensitivity in exposure_by_group_R25.csv, work/prov_day_*.npy for the health model.
"""
import os, sys, numpy as np, pandas as pd
from scipy import sparse

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WK = f"{H}/work"
dates = pd.to_datetime(pd.read_csv(f"{WK}/dates.csv").date)
yr, mo, md = dates.dt.year.values, dates.dt.month.values, dates.dt.strftime("%m-%d").values
da = pd.read_csv(f"{WK}/da_attr.csv", dtype={"DAUID": str, "CMAUID": str})
for c in ["pop2021", "age_0_4", "age_65p", "lim_low_income", "lim_universe"]:
    da[c] = da[c].fillna(0.0)
da["pop_with_age"] = np.where(da.age_total.notna(), da.pop2021, 0.0)  # base for age comparisons

PROVS = ["NL", "PE", "NS", "NB", "QC", "ON", "MB", "SK", "AB", "BC", "YT", "NT", "NU"]

def periods(y):
    P = {"May-Sep": (yr == y) & (mo >= 5) & (mo <= 9),
         "Jan1-Oct19": (yr == y) & (md <= "10-19"),
         "Oct-Apr_same_year": (yr == y) & ((mo <= 4) | (mo >= 10))}
    if y <= 2025:
        P["calendar_year"] = yr == y
    return P

def run(R, full=True):
    m = pd.read_csv(f"{WK}/R{R}_da_combo.csv", dtype={"DAUID": str})
    d = da.merge(m, on="DAUID")
    nC = d.combo.max() + 1
    pm = np.load(f"{WK}/R{R}_combo_pm.npy")
    inc = np.load(f"{WK}/R{R}_combo_inc.npy")
    src = np.load(f"{WK}/R{R}_combo_src.npy")
    has = np.isfinite(pm)
    pm0 = np.where(has, pm, 0).astype(np.float64)
    inc0 = np.where(np.isfinite(inc), inc, 0).astype(np.float64)

    # group definitions: (dimension, name, mask over d)
    groups = [("national", "Canada", np.ones(len(d), bool))]
    groups += [("province", p, (d.prov == p).values) for p in PROVS]
    if full:
        for cu, g in d[d.CMATYPE == "B"].groupby("CMAUID"):
            groups.append(("cma", g.CMANAME.iloc[0], (d.CMAUID == cu).values & (d.CMATYPE == "B").values))
        groups += [("reserve", "on_reserve", d.on_reserve.values.astype(bool)),
                   ("reserve", "off_reserve", ~d.on_reserve.values.astype(bool))]
    weights = {"total_pop": d.pop2021.values}
    if full:
        weights.update({"pop_with_age_data": d.pop_with_age.values, "age_0_4": d.age_0_4.values,
                        "age_65p": d.age_65p.values, "lim_universe": d.lim_universe.values,
                        "lim_low_income": d.lim_low_income.values})
    rows = []
    for y in range(2018, 2027):
        for pname, sel in periods(y).items():
            nd = int(sel.sum())
            P, I = pm0[:, sel], inc0[:, sel]
            hv = has[:, sel]
            v = {"covered_days": hv.sum(1), "sum_pm": P.sum(1), "sum_inc": I.sum(1),
                 "d27": (P > 27).sum(1), "d60": (P > 60).sum(1), "d100": (P > 100).sum(1),
                 "d27_rt": ((P > 27) & (src[:, sel] == 0)).sum(1),
                 "any27": (P > 27).any(1), "any60": (P > 60).any(1), "any100": (P > 100).any(1)}
            # combo vectors -> DA vectors
            V = {k: np.asarray(x, dtype=np.float64)[d.combo.values] for k, x in v.items()}
            for dim, gname, gm in groups:
                for wname, w in weights.items():
                    ww = w * gm
                    tot = ww.sum()
                    if tot <= 0:
                        continue
                    cov_pd = (ww * V["covered_days"]).sum()
                    r = dict(radius_km=R, year=y, period=pname, n_days=nd, dimension=dim, group=gname, weight=wname,
                             population=round(tot), pop_with_any_coverage=round((ww * (V["covered_days"] > 0)).sum()),
                             share_person_days_covered=cov_pd / (tot * nd) if nd else np.nan,
                             person_days_gt27=(ww * V["d27"]).sum(), person_days_gt60=(ww * V["d60"]).sum(),
                             person_days_gt100=(ww * V["d100"]).sum(),
                             person_days_gt27_realtime=(ww * V["d27_rt"]).sum(),
                             people_ge1day_gt27=(ww * V["any27"]).sum(), people_ge1day_gt60=(ww * V["any60"]).sum(),
                             people_ge1day_gt100=(ww * V["any100"]).sum(),
                             popw_mean_pm25=(ww * V["sum_pm"]).sum() / cov_pd if cov_pd else np.nan,
                             popw_mean_increment=(ww * V["sum_inc"]).sum() / cov_pd if cov_pd else np.nan,
                             person_ug_days_increment=(ww * V["sum_inc"]).sum())
                    r["days_gt27_per_covered_person"] = r["person_days_gt27"] / (cov_pd / nd) if cov_pd else np.nan
                    rows.append(r)
        print("year", y, "done", file=sys.stderr)
    out = pd.DataFrame(rows)
    for c in out.columns:
        if c.startswith(("person_days", "people_", "person_ug")):
            out[c] = out[c].round(0)
    if not full:
        return out, None
    # daily pop-weighted series, national + province, total pop
    W = sparse.csr_matrix(np.c_[[np.bincount(d.combo.values, weights=d.pop2021.values * gm, minlength=nC)
                                 for _, _, gm in groups[:14]]].T)  # nC x 14
    hasf = has.astype(np.float64)
    covpop = W.T @ hasf
    spm = W.T @ pm0
    sinc = W.T @ inc0
    names = [g[1] for g in groups[:14]]
    dl = []
    for gi, gname in enumerate(names):
        dl.append(pd.DataFrame({"date": dates.dt.strftime("%Y-%m-%d"), "group": gname,
                                "covered_pop": covpop[gi].round(0),
                                "popw_pm25": np.where(covpop[gi] > 0, spm[gi] / np.maximum(covpop[gi], 1), np.nan).round(2),
                                "popw_increment": np.where(covpop[gi] > 0, sinc[gi] / np.maximum(covpop[gi], 1), np.nan).round(2)}))
    daily = pd.concat(dl)
    # province x day arrays for the health model: sum over DAs of pop * f(inc) for given betas
    np.save(f"{WK}/R{R}_prov_day_covpop.npy", covpop)
    np.save(f"{WK}/R{R}_prov_day_sumpm.npy", spm)
    np.save(f"{WK}/R{R}_prov_day_suminc.npy", sinc)
    betas = {"aqbat_mort_c": 0.7, "aqbat_mort_lo": 0.0, "aqbat_mort_hi": 1.04,
             "chen_allcause_c": 1.9, "chen_allcause_lo": 1.6, "chen_allcause_hi": 2.2,
             "aqbat_card_c": 0.71, "aqbat_card_lo": 0.38, "aqbat_card_hi": 1.04,
             "aqbat_resp_c": 0.75, "aqbat_resp_lo": 0.5, "aqbat_resp_hi": 1.01}
    for k, pct in betas.items():
        b = np.log(1 + pct / 100) / 10.0
        f = 1 - np.exp(-b * inc0)
        np.save(f"{WK}/R{R}_prov_day_af_{k}.npy", W.T @ f)
    pd.Series(names).to_csv(f"{WK}/prov_day_names.csv", index=False, header=["group"])
    return out, daily

out50, daily = run(50, full=True)
out50.to_csv(f"{H}/exposure_by_group.csv", index=False)
daily.to_csv(f"{H}/daily_popweighted_pm25.csv", index=False)
out25, _ = run(25, full=False)
out25.to_csv(f"{H}/exposure_by_group_R25.csv", index=False)
print("done")
