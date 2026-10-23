"""Extra emergency department visits linked to wildfire-season smoke, by year.

Uses our own estimate from 06 (monthly ED visits vs monthly smoke increment, May to September,
CIHI NACRS all-cause visits, 9 provinces/territories): +1.707% per 10 ug/m3 (95% CI 0.16 to 3.278).
Extra visits in a province-month = visits x (1 - exp(-beta x increment)), beta = ln(1 + pct/100) / 10.
CIHI monthly data run April 2021 to March 2026, so the seasons covered are 2021 to 2025.
Output: ed_extra_visits_by_year.csv"""
import os
import numpy as np
import pandas as pd

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_csv(os.path.join(H, "monthly_ed_vs_smoke.csv"))
m = pd.read_csv(os.path.join(H, "monthly_ed_model.csv"))
m = m[(m.months == "May-Sep") & (m.outcome == "all ages")].iloc[0]
d = d[(d.sex == "All") & d.cm.between(5, 9)].copy()
d["year"] = pd.to_datetime(d.m).dt.year
for col, pct in [("extra_visits", m.pct_per10), ("extra_visits_lo", m.lo), ("extra_visits_hi", m.hi)]:
    beta = np.log(1 + pct / 100) / 10
    d[col] = d["all"] * (1 - np.exp(-beta * d["inc"]))
g = d.groupby("year").agg(provinces=("prov", "nunique"), visits_may_sep=("all", "sum"),
                          extra_visits=("extra_visits", "sum"), extra_visits_lo=("extra_visits_lo", "sum"),
                          extra_visits_hi=("extra_visits_hi", "sum")).round(0)
g.to_csv(os.path.join(H, "ed_extra_visits_by_year.csv"))
print(g.to_string())
