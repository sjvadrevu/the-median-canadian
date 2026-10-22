"""Step 5: MODELLED short-term (acute) premature deaths from the wildfire-season PM2.5 increment, by province, 2018-2026.
These are modelled estimates, not counts.

Coefficients (percent increase in daily mortality per 10 ug/m3 PM2.5, 95% CI):
 - AQBAT (Health Canada Air Quality Benefits Assessment Tool), acute all internal-cause mortality, all ages:
   0.7 (0 to 1.04); source study Huang et al. 2023; as tabulated in Matz et al. 2026, GeoHealth 10:e2025GH001565,
   Supporting Information Table S1. Health Canada's own wildfire-smoke assessment uses it.
 - Wildfire-specific: Chen G. et al. 2021, Lancet Planetary Health 5(9):e579-e587, all-cause mortality,
   RR 1.019 (1.016 to 1.022) per 10 ug/m3 of wildfire-related PM2.5, 3-day moving average (lag 0-2), 749 locations
   in 43 countries incl. Canada (abstract). Applied to all-cause deaths; here to non-accidental deaths
   (a conservative choice; noted in results).
Attributable deaths for DA i, day d: baseline daily rate(province, year) x pop_i x (1 - exp(-beta x increment_i,d)),
beta = ln(1 + pct/100) / 10, summed over May 1 - Sep 30 and over DAs with a station within 50 km that day.
Baseline: StatCan weekly non-accidental deaths (all causes minus accidents and suicide) in weeks ending
May 7 - Oct 6 of the same year / days / July 1 population; 2026 uses the 2025 rate (2026 weekly data end before May).
Gross = using the full increment (PM2.5 above each station's 2018-2024 same-month median).
Net = gross minus the province's lowest gross value in 2018-2024 (removes the ordinary day-to-day variation that
the increment also captures in a year with little smoke). Net is the central wildfire-attributable figure.
Province-years with < 50% of person-days covered are not reported.
"""
import os, numpy as np, pandas as pd

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WK = f"{H}/work"
dates = pd.to_datetime(pd.read_csv(f"{WK}/dates.csv").date)
yr, mo = dates.dt.year.values, dates.dt.month.values
names = pd.read_csv(f"{WK}/prov_day_names.csv").group.tolist()
rates = pd.read_csv(f"{H}/baseline_death_rates.csv")
exp = pd.read_csv(f"{H}/exposure_by_group.csv")
cov = exp[(exp.weight == "total_pop") & (exp.period == "May-Sep") & (exp.dimension.isin(["province"]))][
    ["group", "year", "share_person_days_covered", "population", "popw_mean_increment", "person_ug_days_increment"]]
covpop = np.load(f"{WK}/R50_prov_day_covpop.npy")

sets = {"AQBAT acute all internal-cause mortality (Huang 2023 via Matz 2026 Table S1)": "aqbat_mort",
        "Chen 2021 wildfire-specific all-cause mortality (Lancet Planet Health)": "chen_allcause"}
rows = []
for label, k in sets.items():
    A = {b: np.load(f"{WK}/R50_prov_day_af_{k}_{b}.npy") for b in ("c", "lo", "hi")}
    for gi, g in enumerate(names):
        if g == "Canada":
            continue
        for y in range(2018, 2027):
            sel = (yr == y) & (mo >= 5) & (mo <= 9)
            ry = rates[(rates.prov == g) & (rates.year == min(y, 2025))]
            rate = float(ry.daily_rate_per_person.iloc[0])
            r = dict(coefficient=label, province=g, year=y, baseline_rate_year=min(y, 2025),
                     daily_nonacc_death_rate_per_100k=rate * 1e5)
            for b in ("c", "lo", "hi"):
                r[f"afsum_{b}"] = A[b][gi, sel].sum()
                r[f"gross_{b}"] = rate * r[f"afsum_{b}"]
            r["covered_person_days"] = covpop[gi, sel].sum()
            rows.append(r)
out = pd.DataFrame(rows).merge(cov.rename(columns={"group": "province"}), on=["province", "year"], how="left")
for b in ("c", "lo", "hi"):
    ref = out[out.year <= 2024].groupby(["coefficient", "province"])[f"afsum_{b}"].min().rename(f"afmin_{b}")
    out = out.merge(ref.reset_index(), on=["coefficient", "province"])
    out[f"net_{b}"] = out.daily_nonacc_death_rate_per_100k / 1e5 * (out[f"afsum_{b}"] - out[f"afmin_{b}"])
out["reported"] = out.share_person_days_covered >= 0.5
for c in [c for c in out.columns if c.startswith(("gross_", "net_"))]:
    out.loc[~out.reported, c] = np.nan
out = out.drop(columns=[c for c in out.columns if c.startswith(("afsum", "afmin"))])
out.to_csv(f"{H}/modelled_acute_deaths_by_province.csv", index=False)

nat = out.groupby(["coefficient", "year"]).agg(**{f"{m}_{b}": (f"{m}_{b}", "sum") for m in ("gross", "net") for b in ("c", "lo", "hi")},
                                               provinces_reported=("reported", "sum")).reset_index()
nat["provinces_not_reported"] = out[~out.reported].groupby(["coefficient", "year"]).province.apply(lambda s: " ".join(sorted(s))).reindex(
    pd.MultiIndex.from_frame(nat[["coefficient", "year"]])).values
# like-for-like across all years: provinces reported in every year
always = out.groupby(["coefficient", "province"]).reported.all()
keep = always[always].reset_index().province.unique()
lf = out[out.province.isin(keep)].groupby(["coefficient", "year"])[["net_c", "net_lo", "net_hi", "gross_c"]].sum().reset_index()
lf.columns = ["coefficient", "year"] + [f"{c}_common_provinces" for c in ["net_c", "net_lo", "net_hi", "gross_c"]]
nat = nat.merge(lf, on=["coefficient", "year"])
nat["common_provinces"] = " ".join(sorted(keep))
for c in nat.columns:
    if c.startswith(("gross", "net")):
        nat[c] = nat[c].round(1)
nat.to_csv(f"{H}/modelled_acute_deaths_national.csv", index=False)
pd.set_option("display.width", 250)
print(nat.to_string())
print(out[(out.year == 2026)][["coefficient", "province", "share_person_days_covered", "net_c", "net_lo", "net_hi", "gross_c"]].round(1).to_string())
