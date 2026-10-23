"""Step 4: wildfire spending per fire season matched to official area burned, for BC, ON, AB, SK.

Each province keeps its own definition (they are NOT comparable with each other):
  BC  BCWS "Total Cost (estimated)" by fire year (Apr 1-Mar 31), 2008-2024; 2025 = BCWS
      estimate to 2025-11-01 ($510M; Budget 2026 fiscal forecast $665M kept as alternative);
      2026 = forecast: Budget 2026 Fire Management vote $235.702M + First Quarterly Report
      overspend $614M = $849.7M (fiscal-year Fire Management, a different line).  Nominal $.
  ON  Public Accounts, MNRF "Emergency Fire Fighting" (statutory), net of recoveries, actuals,
      FY2015-16..2025-26 (fire season = first year).  FY2014-15 excluded (not fire-only).
      Excludes base fire program (Public Safety and Emergency Response line).  Nominal $.
  AB  Voted actuals (Lapse/Encumbrance schedules, unaudited): sum of all wildfire program
      lines in the year (Wildfire Management + Presuppression and Response, operating and
      contingency votes).  FY2015-16..2025-26, FY2022-23 missing.  Nominal $.
  SK  SPSA season wildfire costs, calendar year 2016-2025, restated in 2025 dollars by the
      Provincial Auditor (2026 Report Vol 1 Ch 5).  Real 2025 $.  Appropriations not used.
Area burned: NFD (CCFM) agency-reported final totals 1990-2025; 2026 = CIFFC/NRCan
preliminary year-to-date (2026-10-20).
Population: 2021 Census (table 98-10-0001); no newer StatCan estimate file is in the data
folder, so per-resident figures use 2021 counts for every year.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

sp = pd.read_csv(f"{DATA}/smoke-cost/wildfire_spending_by_jurisdiction.csv")
area = pd.read_csv(f"{DATA}/smoke-cost/fire_area_count_by_agency_year.csv")
pop = pd.read_csv(f"{DATA}/geo/statcan/tables/98100001/98100001.csv", encoding="utf-8-sig")
pop = pop.rename(columns={pop.columns[4]: "pop2021"})
popmap = {k: int(pop.loc[pop.GEO == v, "pop2021"].iloc[0]) for k, v in PR_NAME.items()}

rows = []
def add(prov, season, amount, status, definition, unit="CAD millions (nominal)", note=""):
    rows.append(dict(province=prov, fire_season=int(season), cost_cad_m=round(float(amount), 3),
                     cost_status=status, definition=definition, unit=unit, note=note))

bc = sp[sp.jurisdiction == "BC"]
for _, r in bc[bc.line_item == "BCWS total wildfire cost"].iterrows():
    add("BC", r.fire_season, r.amount, "estimated actual (BCWS total cost, fire year)",
        "BCWS total wildfire cost")
r = bc[(bc.fire_season == 2025) & (bc.line_item == "Estimated cost of wildfire suppression")].iloc[0]
add("BC", 2025, r.amount, "estimate as of 2025-11-01", "BCWS estimated suppression cost",
    note="Budget 2026 fiscal 2025/26 Fire Management forecast = 665.0")
b26 = bc[(bc.fire_season == 2026)]
amt26 = b26.amount.sum()
add("BC", 2026, amt26, "forecast (Budget 2026 vote 235.702 + Q1 2026-09-14 overspend 614.0)",
    "Fire Management fiscal-year forecast (different line from BCWS total cost)")

on = sp[(sp.jurisdiction == "ON") & (sp.line_item.str.contains("Emergency Fire Fighting"))]
for _, r in on.iterrows():
    add("ON", r.fire_season, r.amount, "actual (Public Accounts)", "Emergency Fire Fighting, net of recoveries")

ab = sp[sp.jurisdiction == "AB"].groupby("fire_season").agg(amount=("amount", "sum"),
                                                          lines=("line_item", "; ".join)).reset_index()
for _, r in ab.iterrows():
    add("AB", r.fire_season, r.amount, "actual (voted actuals, unaudited)",
        "All wildfire program lines (management + presuppression/response)", note=r.lines)

sk = sp[(sp.jurisdiction == "SK") & (sp.line_item == "SPSA wildfire costs (season)")]
for _, r in sk.iterrows():
    add("SK", r.fire_season, r.amount, "actual, restated in 2025 dollars",
        "SPSA season wildfire costs (calendar year)", unit="CAD millions (2025 dollars)")

c = pd.DataFrame(rows)
a = area.rename(columns={"ISO": "province", "year": "fire_season"})[
    ["province", "fire_season", "area_burned_ha", "fire_count", "status"]].rename(
    columns={"status": "area_status"})
c = c.merge(a, on=["province", "fire_season"], how="left")
c["population_2021"] = c.province.map(popmap)
c["cost_per_ha_cad"] = (c.cost_cad_m * 1e6 / c.area_burned_ha).round(0)
c["cost_per_resident_cad"] = (c.cost_cad_m * 1e6 / c.population_2021).round(2)
c["cost_per_fire_cad"] = (c.cost_cad_m * 1e6 / c.fire_count).round(0)

# Trend per province over the actual/estimated years (2026 forecast excluded)
tr = []
for p, g in c.groupby("province"):
    h = g[~g.cost_status.str.startswith("forecast")].sort_values("fire_season")
    x = h.fire_season.values.astype(float)
    def slope(y):
        return float(np.polyfit(x, y, 1)[0])
    half = len(h) // 2
    e, l = h.iloc[:half], h.iloc[-half:]
    tr.append(dict(
        province=p, years=f"{int(x.min())}-{int(x.max())}", n_years=len(h),
        slope_cost_cad_m_per_year=round(slope(h.cost_cad_m.values), 2),
        slope_log_cost_pct_per_year=round(100 * (np.exp(slope(np.log(h.cost_cad_m.values))) - 1), 1),
        median_cost_per_ha=round(h.cost_per_ha_cad.median()),
        slope_log_cost_per_ha_pct_per_year=round(100 * (np.exp(slope(np.log(h.cost_per_ha_cad.values))) - 1), 1),
        pearson_r_cost_vs_area=round(float(np.corrcoef(h.cost_cad_m, h.area_burned_ha)[0, 1]), 2),
        mean_cost_first_half=round(e.cost_cad_m.mean(), 1), first_half_years=f"{e.fire_season.min()}-{e.fire_season.max()}",
        mean_cost_second_half=round(l.cost_cad_m.mean(), 1), second_half_years=f"{l.fire_season.min()}-{l.fire_season.max()}",
        max_cost_year=int(h.loc[h.cost_cad_m.idxmax(), "fire_season"]), max_cost_cad_m=h.cost_cad_m.max()))
tr = pd.DataFrame(tr)
c.sort_values(["province", "fire_season"]).to_csv(f"{OUT}/cost_per_hectare.csv", index=False)
tr.to_csv(f"{OUT}/cost_trend_by_province.csv", index=False)
pd.set_option("display.width", 250)
print(c[["province", "fire_season", "cost_cad_m", "area_burned_ha", "cost_per_ha_cad", "cost_per_resident_cad", "cost_status"]].to_string())
print(tr.to_string())
print(popmap)
