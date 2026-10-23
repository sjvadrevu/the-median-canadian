"""Value of standing merchantable timber burned, by province and year 2016-2026 and the 2023-2026 union.

Volume: scaled merchantable volume burned (NFI kNN 2011 on NBAC 2016-2025 / M3 2026 footprints, scaled to official
provincial area), from analysis/economy/timber_carbon_by_year.csv (identical to burned_cells()).
Prices (timber_prices_by_province_year.csv):
  stumpage   = Crown stumpage per m3 (what government would have collected had the wood been harvested and sold)
  roundwood  = industry value per m3 (StatCan output of forestry and logging / NFD harvest), if available
Value = volume x price of that province and year (the 2023-2026 union uses the price of each cell's last burn year,
approximated by the volume-weighted mix of 2023-2026 prices; see code). Real values in 2025 dollars use the CPI
all-items annual average (StatCan v41690973 via Bank of Canada Valet; 2026 = January-September mean).
This is the value of standing timber burned, not a loss: most burned forest is outside current harvest plans, much
can be salvaged, and harvest levels are capped by allowable cuts, not by the standing stock.
Outputs: timber_value_by_province_year.csv, timber_value_canada_year.csv, timber_value_in_tenure.csv
"""
import json
import numpy as np
import pandas as pd
from vcommon import OUT, ECON, BASE

tc = pd.read_csv(ECON / "timber_carbon_by_year.csv")
pr = pd.read_csv(OUT / "timber_prices_by_province_year.csv")
cpi = json.load(open(BASE / "analysis" / "losses" / "raw" / "cpi" / "boc_V41690973.json"))["observations"]
c = pd.DataFrame([(o["d"][:4], float(o["V41690973"]["v"])) for o in cpi], columns=["y", "v"]).groupby("y").v.mean()
c.index = c.index.astype(int)
defl = c[2025] / c  # multiply nominal by this to get 2025 dollars

has_rw = "price_roundwood" in pr.columns
yr = tc[tc.year != "2023_2026"].copy()
yr["year"] = yr.year.astype(int)
yr = yr[yr.prov != "Canada"].merge(pr, on=["prov", "year"], how="left")
yr["value_stump_nominal"] = yr.vol_merch_scaled_m3 * yr.price_stump
yr["value_stump_2025d"] = yr.value_stump_nominal * yr.year.map(defl)
if has_rw:
    yr["value_roundwood_nominal"] = yr.vol_merch_scaled_m3 * yr.price_roundwood
    yr["value_roundwood_2025d"] = yr.value_roundwood_nominal * yr.year.map(defl)
yr["harvest_value_stump_nominal"] = yr.total_harvest_m3 * yr.price_stump
keep = ["prov", "year", "vol_merch_scaled_m3", "harvest_m3", "price_stump", "price_stump_basis", "value_stump_nominal",
        "value_stump_2025d"] + (["price_roundwood", "price_roundwood_basis", "value_roundwood_nominal", "value_roundwood_2025d"] if has_rw else [])
yr[keep].to_csv(OUT / "timber_value_by_province_year.csv", index=False)

agg = {"vol_merch_scaled_m3": "sum", "value_stump_nominal": "sum", "value_stump_2025d": "sum"}
if has_rw:
    agg.update({"value_roundwood_nominal": "sum", "value_roundwood_2025d": "sum"})
can = yr.groupby("year").agg(agg)
can["missing_price_volume_m3"] = yr[yr.price_stump.isna()].groupby("year").vol_merch_scaled_m3.sum()
can = can.fillna({"missing_price_volume_m3": 0})
# union 2023-2026 (each hectare once): use per-year sums restricted to first burn is not available at province level,
# so report the sum of the four seasons and the union volume valued at the 2023-2026 volume-weighted mean price.
u = tc[(tc.year == "2023_2026") & (tc.prov != "Canada")][["prov", "vol_merch_scaled_m3"]]
w = yr[yr.year >= 2023].groupby("prov").apply(lambda g: np.average(g.price_stump, weights=g.vol_merch_scaled_m3) if g.vol_merch_scaled_m3.sum() > 0 else np.nan, include_groups=False)
u["price_stump_vw_2023_2026"] = u.prov.map(w)
u["value_stump_union_nominal"] = u.vol_merch_scaled_m3 * u.price_stump_vw_2023_2026
if has_rw:
    w2 = yr[yr.year >= 2023].groupby("prov").apply(lambda g: np.average(g.price_roundwood.fillna(0), weights=g.vol_merch_scaled_m3) if g.vol_merch_scaled_m3.sum() > 0 else np.nan, include_groups=False)
    u["price_roundwood_vw_2023_2026"] = u.prov.map(w2)
    u["value_roundwood_union_nominal"] = u.vol_merch_scaled_m3 * u.price_roundwood_vw_2023_2026
u.to_csv(OUT / "timber_value_union_2023_2026.csv", index=False)
can.to_csv(OUT / "timber_value_canada_year.csv")

# inside tenure
t = pd.read_csv(OUT / "tenure_volume_by_year.csv")
t = t[t.year != "2023_2026"].copy(); t["year"] = t.year.astype(int)
t = t.merge(pr[["prov", "year", "price_stump"] + (["price_roundwood"] if has_rw else [])], on=["prov", "year"], how="left")
t["value_stump_in_tenure_nominal"] = t.vol_merch_in_tenure_scaled_m3 * t.price_stump
if has_rw:
    t["value_roundwood_in_tenure_nominal"] = t.vol_merch_in_tenure_scaled_m3 * t.price_roundwood
t.to_csv(OUT / "timber_value_in_tenure.csv", index=False)

pd.set_option("display.width", 220)
print((can / 1e6).round(1).to_string())
print(yr[yr.year == 2026][keep].sort_values("value_stump_nominal", ascending=False).head(10).to_string())
print(u.assign(v=u.value_stump_union_nominal / 1e6).round(2).to_string())
print(t[t.year.isin([2023, 2024, 2025, 2026])][["layer", "year", "vol_merch_in_tenure_scaled_m3", "share_vol_in_tenure", "value_stump_in_tenure_nominal"]].round(2).to_string())
