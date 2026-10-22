"""Rebuild 2026-10-21: timber_biomass_carbon_by_area.csv recomputed on the fma_v2 area layer.

Same inputs and formulas as 07_timber_carbon.py (work/cells.pkl, SCANFI, kNN 2011, NFD harvest), with two changes:
  * areas: each burned cell takes its fma_v2 id from analysis/forest/work/fma_v2_id.npy (Manitoba 22 MWS restriction
    areas + remainder, Quebec 65 SOPFEU zones + remainder); there is no national_park level any more;
  * 2026 scale weight: the province factor of analysis/forest/scaling_factors_by_province.csv (rebuild basis:
    official agency total + Parks Canada hectares allocated to the province, over all M3 area in the province,
    national parks included) applies to every cell of the province, parks included. 2023-2025 weights unchanged.
National mapped totals are unchanged by construction; national scaled totals change only through the redistribution
of the Parks Canada hectares across provinces.
Output: timber_biomass_carbon_by_area_v2.csv (07_timber_carbon.py and its output are left untouched).
"""
import numpy as np
import pandas as pd
from ecommon import WORK, OUT, RAW, FWORK, DATA, FOREST
from grid import load

cells = pd.read_pickle(WORK / "cells.pkl")
b25 = np.load(WORK / "scanfi_bio2025.npz")
b20 = np.load(WORK / "scanfi_bio2020.npz")
k = np.load(WORK / "knn2011.npz")
ex = pd.read_pickle(WORK / "cells_extra.pkl")             # first_year, bio_prefire_union_t, burned_2011_2022
assert (ex.idx.values == cells.idx.values).all()
A = cells.area_ha.values
cells["bio2025_t"] = b25["bio_t"]
cells["bio2020_t"] = b20["bio_t"]
cells["bio_prefire_union_t"] = ex.bio_prefire_union_t.values
cells["burned_2011_2022"] = ex.burned_2011_2022.values
for v in ["vol_merch", "vol_total", "agb_live", "bio_dead", "bio_stemwood", "bio_stembark", "bio_branch", "bio_foliage"]:
    cells[v] = k[v + "_per_ha"].astype("float64") * A

fid2 = load("fma_v2_id")
cells["fma_v2_id"] = np.asarray(fid2.ravel()[cells.idx.values]).astype("int64")
attr = pd.read_csv(DATA / "geo" / "fma_v2_attributes.csv")
cells["prov_v2"] = cells.fma_v2_id.map(dict(zip(attr.fma_id, attr.province))).fillna("outside")
cells["fma_name"] = cells.fma_v2_id.map(dict(zip(attr.fma_id, attr.area_name)))
chg = (cells.prov_v2 != cells.prov).sum()
print("cells whose province differs from the fma_all grid:", int(chg))
sf = pd.read_csv(FOREST / "scaling_factors_by_province.csv").set_index("province")["scaling_factor"]
assert "PC" not in sf.index
cells["w26"] = cells.prov_v2.map(sf).astype(float).fillna(1.0)
w_last = cells.w_last.values.copy()
s26 = (cells.last_year == 2026).values
w_last[s26] = cells.w26.values[s26]
cells["w_last"] = w_last
cells["prov"] = cells.prov_v2

scopes = {"2026": cells.b2026.values, "2023": cells.b2023.values, "2024": cells.b2024.values,
          "2025": cells.b2025.values, "union_2023_2026": np.ones(len(cells), bool)}


def summarise(df, scope):
    if scope == "2026":
        bio, w = df.bio2025_t, df.w26
    elif scope in ("2023", "2024", "2025"):
        bio = df.bio2020_t
        w = df.w_last.where(df.last_year == int(scope), np.nan)
        w = w.fillna(1.0)
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
    for (fi, f), g in d[d.fma_v2_id > 0].groupby(["fma_v2_id", "fma_name"]):
        rows.append(summarise(g, scope).rename(("fma", f"{g.prov.iloc[0]} | {f} | {fi}", scope)))
res = pd.DataFrame(rows)
res.index = pd.MultiIndex.from_tuples(res.index, names=["level", "unit", "scope"])
res = res.reset_index()
res["foliage_share"] = res.foliage_knn2011_t / res.agb_knn2011_t
res["nonstem_share"] = (res.foliage_knn2011_t + res.branch_knn2011_t + res.stembark_knn2011_t) / res.agb_knn2011_t
CF = 0.5
for sfx, col in [("mapped", "agb_prefire_scanfi_t"), ("scaled", "agb_prefire_scanfi_scaled_t")]:
    res[f"agc_prefire_{sfx}_t"] = res[col] * CF
    res[f"co2_low_{sfx}_t"] = res[col] * CF * res.foliage_share * 44 / 12
    res[f"co2_high_{sfx}_t"] = res[col] * CF * res.nonstem_share * 44 / 12
    res[f"co2_all_agb_{sfx}_t"] = res[col] * CF * 44 / 12
harv = pd.read_csv(OUT / "harvest_nfd_by_province.csv", index_col=0)
key = np.where(res.level == "Canada", "Canada", np.where(res.level == "province", res.unit, None))
res["harvest_2024_m3"] = pd.Series(key).map(harv.harvest_2024_m3).values
res["harvest_mean_2020_2024_m3"] = pd.Series(key).map(harv.harvest_mean_2020_2024_m3).values
for sfx, col in [("mapped", "vol_merch_knn2011_m3"), ("scaled", "vol_merch_knn2011_scaled_m3")]:
    res[f"years_of_harvest_2024_{sfx}"] = res[col] / res.harvest_2024_m3
    res[f"years_of_harvest_mean_{sfx}"] = res[col] / res.harvest_mean_2020_2024_m3
res.to_csv(OUT / "timber_biomass_carbon_by_area_v2.csv", index=False)

old = pd.read_csv(OUT / "timber_biomass_carbon_by_area.csv")
cmp = ["area_mapped_ha", "area_scaled_ha", "agb_prefire_scanfi_t", "agb_prefire_scanfi_scaled_t",
       "vol_merch_knn2011_m3", "vol_merch_knn2011_scaled_m3", "co2_low_scaled_t", "co2_high_scaled_t"]
a = old[old.level == "Canada"].set_index("scope")[cmp]
b = res[res.level == "Canada"].set_index("scope")[cmp]
pd.set_option("display.width", 250)
print("Canada, old (fma_all basis):\n", a.round(0).to_string())
print("Canada, v2:\n", b.round(0).to_string())
print("v2 / old - 1:\n", (b / a - 1).round(5).to_string())
print("fma rows (2026):", int(((res.level == "fma") & (res.scope == "2026")).sum()))
