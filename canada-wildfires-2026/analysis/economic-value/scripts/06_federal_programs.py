"""Federal wildland-fire program contributions (NRCan) from the Proactive Disclosure of Grants and Contributions.

Programs kept (all NRCan): Fighting and Managing Wildfires in a Changing Climate (FMWCC, equipment and training for
provinces/territories, Budget 2022 measure), Contribution in Support of National Aerial Wildfire Capacity (CIFFC,
signed 2026-02-19), Resilient Communities Through FireSmart, Building and Mobilizing Foundational Wildland Fire
Knowledge, Wildland Fire Resilience, Centre of Excellence for Wildland Fire Innovation and Resilience, Supporting and
Mobilizing Indigenous Fire Knowledge. Not kept: 2 Billion Trees, DMAF, Red Cross COVID readiness, DFAA (counted
separately).
Amendments are separate rows with new reference numbers; one agreement = recipient + program + agreement number (or
start date when blank); the row with the highest amendment number (latest disclosure date on ties) is kept.
Agreement value is a multi-year commitment, not annual spending. Two views:
  signed_by_fy : full value in the fiscal year of the original agreement start date
  straight_line: value spread evenly over the fiscal years from start to end date (an allocation assumption)
Outputs: federal_wildfire_programs_agreements.csv, federal_wildfire_programs_by_year.csv
"""
import numpy as np
import pandas as pd
from vcommon import RAW, OUT

g = pd.read_csv(RAW / "grants" / "grants_wildfire_all.csv", low_memory=False)
P = ["Fighting and Managing Wildfires in a Changing Climate", "Contribution in Support of National Aerial Wildfire Capacity",
     "Contributions in Support of the Resilient Communities Through FireSmart program",
     "Contributions in Support of Building and Mobilizing Foundational Wildland Fire Knowledge", "Wildland Fire Resilience",
     "Contributions in support of a Centre of Excellence for Wildland Fire Innovation and Resilience",
     "Grants for Supporting and Mobilizing Indigenous Fire Knowledge"]
x = g[g.prog_name_en.isin(P) & (g.owner_org == "nrcan-rncan")].copy()
x["value"] = pd.to_numeric(x.agreement_value, errors="coerce")
x["amend"] = pd.to_numeric(x.amendment_number, errors="coerce").fillna(0)
x["key_no"] = x.agreement_number.fillna("").astype(str).str.strip()
x["key"] = x.recipient_legal_name.str.upper().str.replace(r"[^A-Z]", "", regex=True).str[:30] + "|" + x.prog_name_en + "|" + \
    np.where(x.key_no != "", x.key_no, x.agreement_start_date.astype(str))
x = x.sort_values(["key", "amend", "ref_number"]).groupby("key").tail(1)
x["start"] = pd.to_datetime(x.agreement_start_date, errors="coerce")
x["end"] = pd.to_datetime(x.agreement_end_date, errors="coerce")
fy = lambda d: d.year if d.month >= 4 else d.year - 1
x["fy_start"] = x.start.map(fy)
x["fy_end"] = x.end.map(fy)
x[["ref_number", "amend", "recipient_legal_name", "recipient_province", "prog_name_en", "value", "agreement_start_date",
   "agreement_end_date", "fy_start", "fy_end", "agreement_title_en"]].to_csv(OUT / "federal_wildfire_programs_agreements.csv", index=False)
rows = []
for r in x.itertuples():
    rows.append(dict(view="signed_by_fy", fy=r.fy_start, prog=r.prog_name_en, value=r.value))
    n = max(int(r.fy_end - r.fy_start + 1), 1)
    for k in range(n):
        rows.append(dict(view="straight_line", fy=r.fy_start + k, prog=r.prog_name_en, value=r.value / n))
d = pd.DataFrame(rows).groupby(["view", "fy"]).value.sum().unstack(0).fillna(0)
d.to_csv(OUT / "federal_wildfire_programs_by_year.csv")
print(len(x), "agreements; total value", x.value.sum() / 1e6)
print((d / 1e6).round(1))
print((x.groupby("prog_name_en").value.agg(["count", "sum"]).assign(sum=lambda t: t["sum"] / 1e6)).round(1))
