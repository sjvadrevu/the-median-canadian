"""Timber volume, aboveground biomass and carbon inside 2026 and 2023-2026 burned areas; harvest comparison.

Inputs (aligned to work/cells.pkl):
  work/scanfi_bio2025.npz, work/scanfi_bio2020.npz  SCANFI v2 aboveground biomass (t) per 240 m cell
  work/knn2011.npz   NFI kNN 2011 250 m layers sampled at cell centres (per ha)
Pre-fire biomass: 2026 burns use SCANFI 2025; 2023, 2024 and 2025 burns use SCANFI 2020. For the 2023-2026 union,
each cell uses the layer before its FIRST burn in the period (2020 if first burned 2023-2025, 2025 if only 2026).
Volume: kNN 2011 merchantable and total volume (m3/ha). 2011 is the only open national volume map; volume on
cells that burned again between 2011 and 2022 (NBAC) is reported separately because it is out of date.
Harvest: National Forestry Database, net merchantable volume of roundwood harvested (all categories and tenures),
2024 and mean 2020-2024, by province.
Carbon (OUR ESTIMATE, assumption based):
  carbon = biomass x 0.5 (assumed carbon fraction of dry biomass)
  combusted aboveground carbon = pre-fire live aboveground carbon x combustion share
  LOW combustion share  = foliage share of live aboveground biomass (all foliage burns, nothing else)
  HIGH combustion share = (foliage + branches + stem bark) share (all non-stem biomass burns, stem wood stays)
  Shares come from kNN 2011 biomass components over the same burned cells (area-weighted by biomass).
  CO2 = carbon x 44/12. Excludes dead wood, litter, peat and soil organic layers, CH4, N2O and later decay.
Scales: "mapped" = outline/NBAC footprint as mapped. "scaled" = multiplied per cell by the provincial factor
(official area / mapped area): 2026 factors from analysis/forest/scaling_factors_by_province.csv; for 2023-2025 the
factor is NFD official provincial area / NBAC mapped area outside national parks (work/scale_factors_2023_2025.csv).
"""
import numpy as np
import pandas as pd
from ecommon import WORK, OUT, RAW, FMA_ATTR, FWORK, YEARS
from grid import load

cells = pd.read_pickle(WORK / "cells.pkl")
b25 = np.load(WORK / "scanfi_bio2025.npz")
b20 = np.load(WORK / "scanfi_bio2020.npz")
k = np.load(WORK / "knn2011.npz")
A = cells.area_ha.values
cells["bio2025_t"] = b25["bio_t"]
cells["bio2020_t"] = b20["bio_t"]
first = np.where(cells.b2023, 2023, np.where(cells.b2024, 2024, np.where(cells.b2025, 2025, 2026)))
cells["first_year"] = first
cells["bio_prefire_union_t"] = np.where(first == 2026, cells.bio2025_t, cells.bio2020_t)
for v in ["vol_merch", "vol_total", "agb_live", "bio_dead", "bio_stemwood", "bio_stembark", "bio_branch",
          "bio_foliage"]:
    cells[v] = k[v + "_per_ha"].astype("float64") * A
# cells that burned between 2011 and 2022 (2011 volume map is stale there)
stale = np.zeros(len(cells), bool)
for y in range(2011, 2023):
    stale |= np.isin(cells.idx.values, np.load(FWORK / f"burn_{y}.npy"))
cells["burned_2011_2022"] = stale
fattr = pd.read_csv(FMA_ATTR)
cells["fma_name"] = cells.fma_id.map(dict(zip(fattr.fma_id, fattr.area_name)))
park_name = dict(zip(fattr.fma_id - 99, fattr.area_name))
cells["park_name"] = cells.park_id.map(park_name)

scopes = {"2026": cells.b2026.values, "2023": cells.b2023.values, "2024": cells.b2024.values,
          "2025": cells.b2025.values, "union_2023_2026": np.ones(len(cells), bool)}


def summarise(df, scope):
    if scope == "2026":
        bio, w = df.bio2025_t, df.w26
    elif scope in ("2023", "2024", "2025"):
        bio = df.bio2020_t
        w = df.w_last.where(df.last_year == int(scope), np.nan)
        w = w.fillna(1.0)   # cells re-burned later keep factor 1 for this year (small share)
    else:
        bio, w = df.bio_prefire_union_t, df.w_last
    return pd.Series(dict(
        area_mapped_ha=df.area_ha.sum(), area_scaled_ha=(df.area_ha * w).sum(),
        forest_mapped_ha=df.forest_ha.sum(),
        agb_prefire_scanfi_t=bio.sum(), agb_prefire_scanfi_scaled_t=(bio * w).sum(),
        agb_scanfi_2025_t=df.bio2025_t.sum(), agb_scanfi_2020_t=df.bio2020_t.sum(),
        vol_merch_knn2011_m3=df.vol_merch.sum(), vol_merch_knn2011_scaled_m3=(df.vol_merch * w).sum(),
        vol_total_knn2011_m3=df.vol_total.sum(), vol_total_knn2011_scaled_m3=(df.vol_total * w).sum(),
        vol_merch_on_cells_burned_2011_2022_m3=df.vol_merch[df.burned_2011_2022].sum(),
        agb_knn2011_t=df.agb_live.sum(), dead_knn2011_t=df.bio_dead.sum(),
        stemwood_knn2011_t=df.bio_stemwood.sum(), stembark_knn2011_t=df.bio_stembark.sum(),
        branch_knn2011_t=df.bio_branch.sum(), foliage_knn2011_t=df.bio_foliage.sum()))


rows = []
for scope, sel in scopes.items():
    d = cells[sel]
    rows.append(summarise(d, scope).rename(("Canada", "all", scope)))
    for p, g in d.groupby("prov"):
        rows.append(summarise(g, scope).rename(("province", p, scope)))
    for f, g in d[d.fma_id > 0].groupby("fma_name"):
        rows.append(summarise(g, scope).rename(("fma", f"{g.prov.iloc[0]} | {f}", scope)))
    for f, g in d[d.park_id > 0].groupby("park_name"):
        rows.append(summarise(g, scope).rename(("national_park", f, scope)))
res = pd.DataFrame(rows)
res.index = pd.MultiIndex.from_tuples(res.index, names=["level", "unit", "scope"])
res = res.reset_index()

# combustion shares from kNN components (biomass-weighted over the scope)
res["foliage_share"] = res.foliage_knn2011_t / res.agb_knn2011_t
res["nonstem_share"] = (res.foliage_knn2011_t + res.branch_knn2011_t + res.stembark_knn2011_t) / res.agb_knn2011_t
CF = 0.5
for sfx, col in [("mapped", "agb_prefire_scanfi_t"), ("scaled", "agb_prefire_scanfi_scaled_t")]:
    res[f"agc_prefire_{sfx}_t"] = res[col] * CF
    res[f"co2_low_{sfx}_t"] = res[col] * CF * res.foliage_share * 44 / 12
    res[f"co2_high_{sfx}_t"] = res[col] * CF * res.nonstem_share * 44 / 12
    res[f"co2_all_agb_{sfx}_t"] = res[col] * CF * 44 / 12

# harvest
h = pd.read_csv(RAW / "nfd" / "NFD - Net Merchantable Volume of Roundwood Harvested by Category and Ownership - EN FR.csv",
                encoding="utf-8-sig")
hv = h.groupby(["ISO", "Year"])["Volume (cubic metres)"].sum().unstack()
harv = pd.DataFrame({"harvest_2024_m3": hv[2024], "harvest_mean_2020_2024_m3": hv[list(range(2020, 2025))].mean(axis=1)})
harv.loc["Canada"] = harv.sum()
qual = h[h.Year == 2024].groupby("ISO")["Data qualifier"].agg(lambda s: ";".join(sorted(set(map(str, s)))))
harv["nfd_2024_qualifiers"] = qual
harv.to_csv(OUT / "harvest_nfd_by_province.csv")
key = np.where(res.level == "Canada", "Canada", np.where(res.level == "province", res.unit, None))
res["harvest_2024_m3"] = pd.Series(key).map(harv.harvest_2024_m3).values
res["harvest_mean_2020_2024_m3"] = pd.Series(key).map(harv.harvest_mean_2020_2024_m3).values
for sfx, col in [("mapped", "vol_merch_knn2011_m3"), ("scaled", "vol_merch_knn2011_scaled_m3")]:
    res[f"years_of_harvest_2024_{sfx}"] = res[col] / res.harvest_2024_m3
    res[f"years_of_harvest_mean_{sfx}"] = res[col] / res.harvest_mean_2020_2024_m3
res.to_csv(OUT / "timber_biomass_carbon_by_area.csv", index=False)
cells[["idx", "first_year", "bio_prefire_union_t", "burned_2011_2022"]].to_pickle(WORK / "cells_extra.pkl")

pd.set_option("display.width", 250)
show = ["level", "unit", "scope", "area_mapped_ha", "agb_prefire_scanfi_t", "vol_merch_knn2011_m3",
        "vol_merch_knn2011_scaled_m3", "harvest_2024_m3", "years_of_harvest_2024_mapped", "years_of_harvest_2024_scaled",
        "foliage_share", "nonstem_share", "co2_low_mapped_t", "co2_high_mapped_t"]
print(res[res.level.isin(["Canada", "province"])][show].to_string())
print(harv)
