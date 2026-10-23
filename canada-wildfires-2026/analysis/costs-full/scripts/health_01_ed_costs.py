"""Cost of the extra emergency department (ED) visits linked to wildfire smoke, 2023 to 2025.

Visits: our own estimate (analysis/health/scripts/09_ed_extra_visits.py), recomputed here by
province and year with the same model: CIHI NACRS all-cause ED visits, May to September,
+1.707% per 10 ug/m3 of monthly smoke increment (95% CI 0.16 to 3.278).

Unit cost: CIHI, Spending Trends in Health Service Delivery, 2014-2015 to 2023-2024, Data Tables
(2025), Table 4.1 'Avg cost data' sheet, Emergency, 'Cost per Patient Day/visit' = direct cost per
ED visit, fiscal year 2023-2024, excluding physician compensation. Quebec is not in the table, so
Quebec uses the 'Canada (excluding Quebec and Nunavut)' value.
Full hospital cost: CIHI (2020) Hospital Spending: Focus on the Emergency Department says the
direct cost per ED visit was $158 in 2018-2019 and the full hospital cost $304 (adds imaging,
housekeeping, administration and other areas). Ratio 304 / 157.6 (the 2018-2019 direct cost in
the 2025 table) is applied to 2023-2024 direct costs.

low = low visits x direct cost; central = central visits x full cost; high = high visits x full cost.
All amounts converted from 2023-2024 dollars to 2025 dollars with CPI all-items
(Bank of Canada Valet V41690973): annual 2025 mean / mean of April 2023 to March 2024.
Output: ../health_ed_by_province_year.csv
"""
import json
import os
import sys
import warnings

import numpy as np
import openpyxl
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
CF = os.path.dirname(HERE)                      # costs-full
AN = os.path.dirname(CF)                        # analysis
RAW = os.path.join(CF, "raw", "health")

# 1. extra visits by province and year (same model as 09_ed_extra_visits.py)
d = pd.read_csv(os.path.join(AN, "health", "monthly_ed_vs_smoke.csv"))
m = pd.read_csv(os.path.join(AN, "health", "monthly_ed_model.csv"))
m = m[(m.months == "May-Sep") & (m.outcome == "all ages")].iloc[0]
d = d[(d.sex == "All") & d.cm.between(5, 9)].copy()
d["year"] = pd.to_datetime(d.m).dt.year
for col, pct in [("extra_c", m.pct_per10), ("extra_lo", m.lo), ("extra_hi", m.hi)]:
    beta = np.log(1 + pct / 100) / 10
    d[col] = d["all"] * (1 - np.exp(-beta * d["inc"]))
d = d[d.year.between(2023, 2025)]
g = (d.groupby(["year", "prov"]).agg(visits_may_sep=("all", "sum"), extra_lo=("extra_lo", "sum"),
                                     extra_c=("extra_c", "sum"), extra_hi=("extra_hi", "sum"))
     .reset_index())
g = g[g.visits_may_sep > 0]          # NS 2025 has no CIHI visits; MB 2025 has no smoke data

# check against the published year totals
chk = pd.read_csv(os.path.join(AN, "health", "ed_extra_visits_by_year.csv")).set_index("year")
for y, s in g.groupby("year").extra_c.sum().items():
    assert abs(s - chk.loc[y, "extra_visits"]) < 2, (y, s)

# 2. CIHI direct cost per ED visit, FY2023-2024, by province
wb = openpyxl.load_workbook(os.path.join(RAW, "spending_trends_2014_2023.xlsx"), read_only=True)
rows = list(wb["Avg cost data"].iter_rows(values_only=True))
hdr = rows[0]
ic, iy, ip, ie = hdr.index("indicator"), hdr.index("fiscal_yr"), hdr.index("prov_cd"), hdr.index("ed")
cost = {r[ip]: float(r[ie]) for r in rows[1:]
        if r[ic] == "Cost per Patient Day/visit" and r[iy] == 2023 and isinstance(r[ie], (int, float))}
direct_2018 = [float(r[ie]) for r in rows[1:] if r[ic] == "Cost per Patient Day/visit" and r[iy] == 2018
               and r[ip] == "Canada (excluding Quebec and Nunavut)"][0]
FULL_2018, DIRECT_2018_REPORT = 304.0, 158.0          # CIHI 2020 highlights, 2018-2019
assert abs(direct_2018 - DIRECT_2018_REPORT) < 0.5, direct_2018
ratio = FULL_2018 / direct_2018
names = {"AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NS": "Nova Scotia",
         "ON": "Ontario", "PE": "Prince Edward Island", "SK": "Saskatchewan", "YT": "Yukon",
         "QC": "Canada (excluding Quebec and Nunavut)"}
g["cihi_geo"] = g.prov.map(names)
g["direct_cost_fy2023_24"] = g.cihi_geo.map(cost)
assert g.direct_cost_fy2023_24.notna().all()
g["full_cost_fy2023_24"] = g.direct_cost_fy2023_24 * ratio

# 3. CPI to 2025 dollars
obs = json.load(open(os.path.join(AN, "losses", "raw", "cpi", "boc_V41690973.json")))["observations"]
c = pd.DataFrame([(o["d"], float(o["V41690973"]["v"])) for o in obs], columns=["d", "v"])
c["d"] = pd.to_datetime(c.d)
cpi_fy2324 = c[(c.d >= "2023-04-01") & (c.d <= "2024-03-01")].v.mean()
cpi_2025 = c[c.d.dt.year == 2025].v.mean()
f = cpi_2025 / cpi_fy2324
g["cpi_factor_to_2025"] = f
g["amount_low_2025d"] = g.extra_lo * g.direct_cost_fy2023_24 * f
g["amount_central_2025d"] = g.extra_c * g.full_cost_fy2023_24 * f
g["amount_high_2025d"] = g.extra_hi * g.full_cost_fy2023_24 * f
g["amount_central_direct_only_2025d"] = g.extra_c * g.direct_cost_fy2023_24 * f
out = g.round({"extra_lo": 1, "extra_c": 1, "extra_hi": 1, "full_cost_fy2023_24": 2,
               "cpi_factor_to_2025": 5, "amount_low_2025d": 0, "amount_central_2025d": 0,
               "amount_high_2025d": 0, "amount_central_direct_only_2025d": 0})
out.to_csv(os.path.join(CF, "health_ed_by_province_year.csv"), index=False)

pd.set_option("display.width", 200)
print(f"full/direct ratio {ratio:.4f}; CPI factor FY2023-24 -> 2025 {f:.5f}")
print(out.to_string(index=False))
tot = out.groupby("year")[["extra_lo", "extra_c", "extra_hi", "amount_low_2025d", "amount_central_2025d",
                           "amount_high_2025d", "amount_central_direct_only_2025d"]].sum()
print(tot.round(0).to_string())
print(tot.sum().round(0).to_string())
sys.exit(0)
