"""Canadian Disaster Database (Public Safety Canada) wildfire events: per-event table,
by-year totals, CPI-normalised costs, ranks. Raw: raw/cdd/cdd-extract-1.xlsx (open.canada.ca
dataset 1c3d15f9-9cfa-4010-8462-0d67e493d9b9, resource modified 2026-02-10).
CPI: StatCan 18-10-0005-01 annual all-items if raw/cpi/18100005.csv exists, otherwise
StatCan vector v41690973 (monthly all-items, 2002=100) as served by Bank of Canada Valet,
averaged to calendar years (1995+ only)."""
import json, os, sys
import pandas as pd

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = os.path.join(L, "raw")
d = pd.read_excel(os.path.join(raw, "cdd", "cdd-extract-1.xlsx"))
latest_start = d.EVENT_START_DATE.max(); latest_end = d.EVENT_END_DATE.max()
w = d[d.EVENT_TYPE == "WF"].copy()
w["year"] = w.EVENT_START_DATE.dt.year
money = ["TOTAL_COST", "OGD_COSTS", "MUNICIPAL_COSTS", "FED_DFAA_PAYMENTS", "PROV_DFAA_PAYMENTS",
         "PROV_DEPT_PAYMENTS", "INSURANCE_PAYMENTS", "NGO_PAYMENTS"]

# CPI
cpi = None; cpi_src = None
p = os.path.join(raw, "cpi", "18100005.csv")
if os.path.exists(p):
    c = pd.read_csv(p)
    c = c[(c.GEO == "Canada") & (c["Products and product groups"] == "All-items")]
    cpi = c.set_index(c.REF_DATE.astype(int))["VALUE"]; cpi_src = "StatCan 18-10-0005-01"
else:
    j = json.load(open(os.path.join(raw, "cpi", "boc_V41690973.json")))
    m = pd.DataFrame([(o["d"], float(o["V41690973"]["v"])) for o in j["observations"]], columns=["d", "v"])
    m["y"] = m.d.str[:4].astype(int)
    g = m.groupby("y").v.agg(["mean", "count"])
    cpi = g[g["count"] == 12]["mean"]; cpi_src = "StatCan v41690973 via Bank of Canada Valet (annual mean of 12 months)"
base_year = 2025
w["cpi_factor_to_2025"] = w.year.map(lambda y: cpi[base_year] / cpi[y] if y in cpi.index else float("nan"))
# TOTAL_COST is blank for some events whose component fields are filled (e.g. Lytton 2021 insurance only):
# COST_BEST = TOTAL_COST when > 0, else the sum of the component fields.
w["COMPONENTS_SUM"] = w[money[1:]].fillna(0).sum(axis=1)
w["COST_BEST"] = w.TOTAL_COST.where(w.TOTAL_COST.fillna(0) > 0, w.COMPONENTS_SUM)
w["TOTAL_COST_2025CAD"] = w.TOTAL_COST * w.cpi_factor_to_2025
w["COST_BEST_2025CAD"] = w.COST_BEST * w.cpi_factor_to_2025
for col in ["FED_DFAA_PAYMENTS", "PROV_DFAA_PAYMENTS", "PROV_DEPT_PAYMENTS", "INSURANCE_PAYMENTS"]:
    w[col + "_2025CAD"] = w[col] * w.cpi_factor_to_2025

keep = ["EVENT_ID", "year", "EVENT_START_DATE", "EVENT_END_DATE", "PLACE", "PROVINCES_AFFECTED / PROVINCES AFFECTÉES",
        "DEAD", "INJURED", "EVACUATED"] + money + ["COMPONENTS_SUM", "COST_BEST", "cpi_factor_to_2025", "TOTAL_COST_2025CAD", "COST_BEST_2025CAD",
        "FED_DFAA_PAYMENTS_2025CAD", "PROV_DFAA_PAYMENTS_2025CAD", "PROV_DEPT_PAYMENTS_2025CAD", "INSURANCE_PAYMENTS_2025CAD", "COMMENT"]
w.sort_values("EVENT_START_DATE")[keep].rename(columns={"PROVINCES_AFFECTED / PROVINCES AFFECTÉES": "PROVINCES"}).to_csv(
    os.path.join(L, "cdd_wildfire_events.csv"), index=False)

agg = {"EVENT_ID": "count", "DEAD": "sum", "INJURED": "sum", "EVACUATED": "sum"}
for c in money + ["COST_BEST", "COST_BEST_2025CAD", "TOTAL_COST_2025CAD", "FED_DFAA_PAYMENTS_2025CAD", "PROV_DFAA_PAYMENTS_2025CAD",
                  "PROV_DEPT_PAYMENTS_2025CAD", "INSURANCE_PAYMENTS_2025CAD"]:
    agg[c] = "sum"
y = w.groupby("year").agg(agg).rename(columns={"EVENT_ID": "events"})
y["events_with_any_cost"] = w.groupby("year").apply(lambda g: int((g.TOTAL_COST.fillna(0) > 0).sum()), include_groups=False)
y["cost_best_not_normalised_no_cpi"] = w[w.cpi_factor_to_2025.isna()].groupby("year").COST_BEST.sum()
full = pd.DataFrame(index=pd.RangeIndex(w.year.min(), 2027, name="year")).join(y)
full["in_cdd"] = full.index <= latest_start.year
full.loc[full.in_cdd, "events"] = full.loc[full.in_cdd, "events"].fillna(0)  # years after CDD end stay blank (not zero)
for c in ["events", "DEAD", "EVACUATED", "COST_BEST_2025CAD", "TOTAL_COST_2025CAD", "INSURANCE_PAYMENTS_2025CAD", "FED_DFAA_PAYMENTS_2025CAD"]:
    s = full.loc[full.in_cdd, c].fillna(0)
    full.loc[full.in_cdd, "rank_" + c] = s.rank(ascending=False, method="min")
full.to_csv(os.path.join(L, "cdd_wildfire_by_year.csv"))

# decade summary and period comparison
w["decade"] = (w.year // 10) * 10
dec = w.groupby("decade").agg(events=("EVENT_ID", "count"), dead=("DEAD", "sum"), evacuated=("EVACUATED", "sum"),
                              cost_best_2025cad=("COST_BEST_2025CAD", "sum"), cost_best_nominal=("COST_BEST", "sum"), insurance_2025cad=("INSURANCE_PAYMENTS_2025CAD", "sum"),
                              fed_dfaa_2025cad=("FED_DFAA_PAYMENTS_2025CAD", "sum"))
dec.to_csv(os.path.join(L, "cdd_wildfire_by_decade.csv"))

with open(os.path.join(L, "work", "cdd_meta.txt"), "w") as f:
    f.write(f"rows {len(d)}; wildfire rows {len(w)}; years {w.year.min()}-{w.year.max()}\n")
    f.write(f"latest event start in whole CDD {latest_start.date()}, latest end {latest_end.date()}\n")
    lw = w.sort_values('EVENT_START_DATE').iloc[-1]
    f.write(f"latest wildfire event {int(lw.EVENT_ID)} {lw.EVENT_START_DATE.date()} to {lw.EVENT_END_DATE.date()} {lw.PLACE}\n")
    f.write(f"CPI source {cpi_src}; CPI years {cpi.index.min()}-{cpi.index.max()}\n")
print(open(os.path.join(L, "work", "cdd_meta.txt")).read())
pd.set_option("display.width", 250)
print(full[full.in_cdd & (full.events > 0)][["events", "DEAD", "INJURED", "EVACUATED", "COST_BEST", "COST_BEST_2025CAD", "INSURANCE_PAYMENTS_2025CAD",
      "FED_DFAA_PAYMENTS_2025CAD", "rank_EVACUATED", "rank_COST_BEST_2025CAD"]].tail(30).to_string())
print(dec.to_string())
