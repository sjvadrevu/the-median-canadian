"""Cost tally per fire season 2016-2026, in 2025 dollars (CPI all-items annual average; 2026 = Jan-Sep mean).

Components (each kept separate; 'documented spending and losses' and 'valuations' are never mixed in one number
without saying so):
 A. Provincial firefighting spending, four provinces with consistent series (analysis/people/cost_per_hectare.csv):
    BC = BCWS total wildfire cost (2025 = BCWS estimated suppression cost as of 2025-11-01; 2026 = Fire Management
    fiscal-year forecast, Budget vote + Q1 forecast overrun, a different and broader line: flagged);
    ON = Emergency Fire Fighting, net of recoveries (Public Accounts; 2026 not yet published);
    AB = all wildfire program lines, voted actuals (2022 missing in the source file; 2026 not yet published);
    SK = SPSA season wildfire costs, published already in 2025 dollars (not deflated again; 2026 not published).
 B. Federal NRCan wildland-fire contribution agreements, straight-line over agreement term (06), fiscal year = season.
 C. Federal DFAA payments for wildfires: CDD FED_DFAA_PAYMENTS for 2016-2021 (0 in the CDD means 'not recorded');
    Provincial Emergency Financial Assistance Orders (grants disclosure) for 2022-2025 (analysis/losses).
 D. Insured losses (industry CatIQ, labelled; CDD insurance payments where the CDD has them).
 E. Value of standing merchantable timber burned at Crown stumpage (05) [valuation]; at roundwood value if present.
 F. Modelled acute smoke deaths (analysis/health, net, central) x Health Canada AQBAT value of a statistical life
    $9,158,296 (2023 CAD; low $4,931,390, high $13,385,201), Matz et al. 2026 (Health Canada), Table S2 [valuation].
Outputs: cost_tally_by_year.csv (wide), cost_tally_long.csv, cost_tally_coverage.csv
"""
import json
import numpy as np
import pandas as pd
from vcommon import OUT, BASE

Y = list(range(2016, 2027))
cpi = json.load(open(BASE / "analysis" / "losses" / "raw" / "cpi" / "boc_V41690973.json"))["observations"]
c = pd.DataFrame([(int(o["d"][:4]), float(o["V41690973"]["v"])) for o in cpi], columns=["y", "v"]).groupby("y").v.mean()
to25 = lambda y: c[2025] / c[y]

rows = []
def add(comp, prov, y, nominal=None, real=None, status="", source="", kind="spending"):
    if real is None and nominal is not None:
        real = nominal * to25(y)
    rows.append(dict(component=comp, prov=prov, year=y, value_nominal=nominal, value_2025d=real, status=status, source=source, kind=kind))

# A. provincial firefighting
cp = pd.read_csv(BASE / "analysis" / "people" / "cost_per_hectare.csv")
for r in cp.itertuples():
    if r.fire_season < 2016:
        continue
    v = r.cost_cad_m * 1e6
    if r.province == "SK":
        add("A_provincial_firefighting", "SK", r.fire_season, None, v, r.cost_status, r.definition)
    else:
        add("A_provincial_firefighting", r.province, r.fire_season, v, None, r.cost_status, r.definition)

# B. federal NRCan programs
fp = pd.read_csv(OUT / "federal_wildfire_programs_by_year.csv", index_col=0)
for y in Y:
    if y in fp.index:
        add("B_federal_nrcan_wildfire_programs", "Canada", y, fp.loc[y, "straight_line"], None,
            "agreement values spread evenly over agreement term (allocation)", "Grants and Contributions disclosure, NRCan")

# C. DFAA
cdd = pd.read_csv(BASE / "analysis" / "losses" / "cdd_wildfire_by_year.csv").set_index("year")
dfaa = pd.read_csv(BASE / "analysis" / "losses" / "dfaa_wildfire_payments.csv")
for y in range(2016, 2022):
    v = cdd.loc[y, "FED_DFAA_PAYMENTS"]
    if v and v > 0:
        add("C_federal_DFAA_wildfire", "Canada", y, v, None, "CDD federal DFAA payments", "Canadian Disaster Database")
for y in range(2022, 2026):
    s = dfaa[dfaa.event_year == y].agreement_value.sum()
    if s > 0:
        add("C_federal_DFAA_wildfire", "Canada", y, s, None, "DFAA order values at agreement date (interim; 2025 incomplete)",
            "Grants disclosure, Provincial Emergency Financial Assistance Orders")

# D. insured
ins = {2016: (3.6e9, "CDD insurance payments, Fort McMurray"), 2017: (1.3e8, "CDD insurance payments, BC 2017"),
       2021: (1.79e8, "CDD insurance payments, Lytton 102 M + Central Okanagan 77 M"),
       2024: (1.304e9, "CatIQ final estimate, Jasper wildfire complex (industry)"),
       2026: (2.93e8, "CatIQ 45-day estimate, Bald Range fire, Summerland (industry, early)")}
for y, (v, s) in ins.items():
    add("D_insured_losses", "Canada", y, v, None, s, "CDD / CatIQ", kind="loss")

# E. timber
tv = pd.read_csv(OUT / "timber_value_canada_year.csv", index_col=0)
for y in Y:
    add("E_timber_value_stumpage", "Canada", y, tv.loc[y, "value_stump_nominal"], tv.loc[y, "value_stump_2025d"],
        "value of standing merchantable timber burned at Crown stumpage", "NFD / BC Budget; kNN 2011 volume", kind="valuation")
    if "value_roundwood_nominal" in tv.columns and pd.notna(tv.loc[y, "value_roundwood_nominal"]):
        add("E2_timber_value_roundwood", "Canada", y, tv.loc[y, "value_roundwood_nominal"], tv.loc[y, "value_roundwood_2025d"],
            "value of standing merchantable timber burned at roundwood (forestry and logging output) value", "StatCan / NFD", kind="valuation")

# F. health valuation
VSL = {"central": 9158296.0, "low": 4931390.0, "high": 13385201.0}
hd = pd.read_csv(BASE / "analysis" / "health" / "modelled_acute_deaths_national.csv")
for r in hd.itertuples():
    tag = "Chen" if r.coefficient.startswith("Chen") else "AQBAT"
    for k in ["central"]:
        add(f"F_health_valuation_{tag}", "Canada", int(r.year), None, r.net_c * VSL[k] * to25(2023),
            f"{r.net_c:.0f} modelled acute deaths (net) x VSL {VSL[k]:,.0f} (2023 CAD); provinces reported {r.provinces_reported}",
            "analysis/health; Health Canada AQBAT VSL (Matz et al. 2026 Table S2)", kind="valuation")
    rows[-1]["low_2025d"] = r.net_lo * VSL["low"] * to25(2023)
    rows[-1]["high_2025d"] = r.net_hi * VSL["high"] * to25(2023)

L = pd.DataFrame(rows)
L.to_csv(OUT / "cost_tally_long.csv", index=False)
W = L.pivot_table(index="year", columns="component", values="value_2025d", aggfunc="sum").reindex(Y)
A = L[L.component == "A_provincial_firefighting"].pivot_table(index="year", columns="prov", values="value_2025d", aggfunc="sum").reindex(Y)
A.columns = [f"A_{p}" for p in A.columns]
W = pd.concat([A, W], axis=1)
W["documented_spending_and_losses"] = W[[c for c in ["A_provincial_firefighting", "B_federal_nrcan_wildfire_programs", "C_federal_DFAA_wildfire", "D_insured_losses"] if c in W]].sum(axis=1, min_count=1)
W["valuation_timber_stumpage_plus_health_Chen"] = W[["E_timber_value_stumpage", "F_health_valuation_Chen"]].sum(axis=1, min_count=1)
W["all_components_Chen"] = W[["documented_spending_and_losses", "valuation_timber_stumpage_plus_health_Chen"]].sum(axis=1, min_count=1)
W.to_csv(OUT / "cost_tally_by_year.csv")

# coverage
cov = []
comps = ["A_BC", "A_ON", "A_AB", "A_SK", "B_federal_nrcan_wildfire_programs", "C_federal_DFAA_wildfire", "D_insured_losses",
         "E_timber_value_stumpage", "E2_timber_value_roundwood", "F_health_valuation_Chen", "F_health_valuation_AQBAT"]
for y in Y:
    d = {"year": y}
    for cc in comps:
        v = W.loc[y, cc] if cc in W.columns else np.nan
        d[cc] = "yes" if pd.notna(v) and v != 0 else "missing"
    cov.append(d)
cov = pd.DataFrame(cov)
cov.to_csv(OUT / "cost_tally_coverage.csv", index=False)
pd.set_option("display.width", 250)
print((W / 1e6).round(0).to_string())
print(cov.to_string())
