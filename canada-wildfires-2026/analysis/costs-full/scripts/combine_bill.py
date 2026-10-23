"""Combine the cost files into one wildfire bill, counting each dollar once.

Inputs: economic-value/cost_tally_by_year.csv (trees, firefighting in BC, AB, SK, ON), property/destroyed_value_estimates.csv
(buildings, via the slide builder's value), costs-full/gov_costs.csv, econ_costs.csv, health_costs.csv.
Rules:
- Floor ("at least"): official spending in full; estimates at their low end; ISC on-reserve response (an estimate) and
  2026 forecasts and budgets are left out; lost wages and lost output overlap, so the floor takes the larger of the two.
- Central and high: estimates at their central and high values; ISC estimate included; lost wages and output added
  (they may partly overlap, flagged).
Outputs: costs-full/combined_bill.csv (one row per line) and costs-full/bill_summary.json (category totals).
"""
import glob
import json
import os
import re

import pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
AN = os.path.join(D, "..")
M = 1e6


def read_costs(kind):
    """All cost files of one kind: gov_costs.csv plus later research rounds (gov2_costs.csv, gov3_costs.csv, ...),
    in round order, each row tagged with its file so the page can cite it."""
    fs = sorted((f for f in glob.glob(os.path.join(D, f"{kind}*_costs.csv"))
                 if re.fullmatch(rf"{kind}\d*_costs\.csv", os.path.basename(f))),
                key=lambda f: int(re.sub(r"\D", "", os.path.basename(f)) or 1))
    return pd.concat([pd.read_csv(f).assign(_file=os.path.basename(f)) for f in fs], ignore_index=True)


rows = []
tally = pd.read_csv(os.path.join(AN, "economic-value", "cost_tally_by_year.csv")).set_index("year")
trees = tally.loc[2023:2026, "E_timber_value_stumpage"].sum()
fight4 = tally.loc[2023:2025, "A_provincial_firefighting"].sum()
rows.append(dict(cat="trees", item="Timber burned at Crown stumpage, 2023 to 2026", low=trees, central=trees, high=trees, src="economic-value/cost_tally_by_year.csv"))
rows.append(dict(cat="fight", item="Firefighting, BC, AB, SK and ON, 2023 to 2025", low=fight4, central=fight4, high=fight4, src="economic-value/cost_tally_by_year.csv"))

g = read_costs("gov")
for _, r in g.iterrows():
    if r["additive"] == "yes" and "2026-27" not in str(r["period"]) and "2026 season" not in str(r["period"]):
        rows.append(dict(cat="fight", item=f'{r["item"]} ({r["period"]})', low=r["additive_amount_cad"], central=r["additive_amount_cad"], high=r["additive_amount_cad"], src=r["_file"]))
    elif r["additive"] == "yes":
        rows.append(dict(cat="fight_2026", item=f'{r["item"]} ({r["period"]})', low=0, central=0, high=0, ref=r["additive_amount_cad"], src=r["_file"]))
    elif r["additive"] == "partial" and "ISC" in str(r["jurisdiction"]):
        rows.append(dict(cat="fight", item=f'{r["item"]} ({r["period"]}), estimate', low=0, central=r["additive_amount_cad"], high=r["additive_amount_cad"], src=r["_file"]))

e = read_costs("econ")
for _, r in e.iterrows():
    a = str(r["additive"])
    if not (a.startswith("yes") or a.startswith("partial")):
        continue
    sec = str(r["sector"])
    cat = "build" if sec.startswith(("property", "infrastructure")) else "output"
    rows.append(dict(cat=cat, item=r["item"], low=r["amount_low_cad"], central=r["amount_central_cad"], high=r["amount_high_cad"], src=r["_file"]))

h = read_costs("health")
for _, r in h.iterrows():
    if str(r["additive"]) != "yes":
        continue
    it = str(r["item"])
    cat = "health" if it.startswith("Health care") else "wages" if it.startswith("Lost work") else "evac"
    rows.append(dict(cat=cat, item=f'{it} ({r["period"]})', low=r["amount_low_cad"], central=r["amount_central_cad"], high=r["amount_high_cad"], src=r["_file"]))

df = pd.DataFrame(rows).fillna({"low": 0, "central": 0, "high": 0})
df.to_csv(os.path.join(D, "combined_bill.csv"), index=False)


def tot(cat, k):
    return float(df.loc[df.cat == cat, k].sum())


S = {}
for k in ("low", "central", "high"):
    S[k] = {c: tot(c, k) for c in ("trees", "fight", "build", "evac", "health", "wages", "output")}
# lost wages and lost output overlap: floor takes the larger
S["low"]["work"] = max(S["low"]["wages"], S["low"]["output"])
for k in ("central", "high"):
    S[k]["work"] = S[k]["wages"] + S[k]["output"]
out = {"note": "CAD; trees and firefighting in 2025 dollars; buildings at census home values (add the bill's building value separately)",
       "fight_2026_forecast_not_counted": float(df.loc[df.cat == "fight_2026", "ref"].sum()) if "ref" in df else None}
for k in ("low", "central", "high"):
    s = S[k]
    out[k] = {"trees": s["trees"], "firefighting_and_response": s["fight"], "buildings_infrastructure_extra": s["build"],
              "evacuations_and_health": s["evac"] + s["health"], "lost_work_and_output": s["work"],
              "health_care_only": s["health"]}
# lines shown on the slide: floor values, plus the 2026 government forecasts and budgets and the ISC on-reserve estimate,
# each labelled; costs with no public record are named on the website instead of shown as blanks
isc = float(df.loc[df.item.str.contains("Indigenous Services Canada") & df.item.str.contains("estimate"), "central"].sum())
L = out["low"]
out["slide"] = {
    "trees_2023_2026": L["trees"],
    "firefighting_response_2023_2025": L["firefighting_and_response"],
    "firefighting_2026_forecasts": out["fight_2026_forecast_not_counted"],
    "buildings_infrastructure_extra": L["buildings_infrastructure_extra"],
    "evacuations_health_incl_isc": L["evacuations_and_health"] + isc,
    "isc_estimate": isc,
    "lost_work_and_output": L["lost_work_and_output"],
}
json.dump(out, open(os.path.join(D, "bill_summary.json"), "w"), indent=1)
for k in ("low", "central", "high"):
    print(k, {a: round(b / 1e9, 3) for a, b in out[k].items()})
print("2026 forecasts not counted:", round(out["fight_2026_forecast_not_counted"] / 1e9, 3))
