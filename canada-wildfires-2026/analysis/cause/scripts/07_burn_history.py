"""Share of forest burned per area and year (outcome) and share of forest burned in the previous 10, 20 and
40 years (fuel / recent-burn proxy), from the 240 m burn rasters of analysis/forest (NBAC 1972-2025, CWFIS M3 2026).

forest_share_burned(Y)  = forest ha in cells burned in Y / forest ha in the area
prior_k(Y)              = forest ha in cells burned at least once in [Y-k, Y-1] / forest ha in the area
                          (complete only when Y-k >= 1972; flags given)
Forest is Land Cover 2020 (classes 1,2,5,6), so land burned shortly before 2020 and not yet regrown is not
counted as forest; prior shares measured on 2020 forest are therefore biased low for burns in about 2005-2019.
2026 uses M3 outlines (hotspot based, larger than agency totals); forest_share_burned_scaled multiplies the
2026 value by the province factor official ha / M3 ha (analysis/forest/scaling_factors_by_province.csv).
Output: burn_history_by_area_year.csv; check against analysis/forest/fma_forest_share_by_year_1972_2025.csv
"""
import numpy as np
import pandas as pd

from common import FOREST_DIR, OUT, SCALING, area_attrs, area_dir, area_grid, burn_idx, forest_ha, grid_meta, log

D = area_dir()
fh = open(D / "log_07.txt", "w")
A = area_attrs()
AF = pd.read_csv(D / "area_forest.csv").set_index("fma_id")
YEARS = list(range(1972, 2027))
idx_l, yr_l = [], []
for y in YEARS:
    b = burn_idx(y)
    idx_l.append(b)
    yr_l.append(np.full(len(b), y, dtype="int16"))
idx = np.concatenate(idx_l)
yr = np.concatenate(yr_l)
del idx_l, yr_l
u, inv = np.unique(idx, return_inverse=True)
del idx
log(f"{len(inv):,} cell-years, {len(u):,} distinct burned cells", fh)
g = area_grid()
m = grid_meta()
rr, cc = np.unravel_index(u, (m["H"], m["W"]))
cell_area = np.asarray(g[rr, cc]).astype("int64")
cell_forest = forest_ha(u)
del rr, cc
nmax = int(A.fma_id.max()) + 1
fa = AF.forest_ha.reindex(range(nmax)).values
last = np.zeros(len(u), dtype="int16")
rows = []
order_start = np.searchsorted(yr, YEARS)          # yr is sorted by construction
for i, y in enumerate(YEARS):
    r = dict(year=y)
    out = {}
    for k in [10, 20, 40]:
        sel = (last >= y - k) & (last > 0)
        out[f"prior{k}"] = np.bincount(cell_area[sel], weights=cell_forest[sel], minlength=nmax) / fa
    s0 = order_start[i]
    s1 = order_start[i + 1] if i + 1 < len(YEARS) else len(yr)
    cells = inv[s0:s1]
    out["burned"] = np.bincount(cell_area[cells], weights=cell_forest[cells], minlength=nmax) / fa
    last[cells] = y
    rows.append(pd.DataFrame(dict(fma_id=np.arange(nmax), year=y, forest_share_burned=out["burned"],
                                  prior10_share=out["prior10"], prior20_share=out["prior20"], prior40_share=out["prior40"])))
B = pd.concat(rows, ignore_index=True)
B = B[B.fma_id.isin(A.fma_id)].merge(A[["fma_id", "province", "area_name"]], on="fma_id")
for k in [10, 20, 40]:
    B[f"prior{k}_complete"] = B.year - k >= 1972
B["source"] = np.where(B.year == 2026, "CWFIS M3 2026", "NBAC")
sf = pd.read_csv(SCALING).set_index("province").scaling_factor
B["forest_share_burned_scaled"] = B.forest_share_burned
is26 = B.year == 2026
B.loc[is26, "forest_share_burned_scaled"] = B.loc[is26, "forest_share_burned"] * B.loc[is26, "province"].map(sf).fillna(1.0)
B.to_csv(OUT / "burn_history_by_area_year.csv", index=False)

# check against analysis/forest
chk = FOREST_DIR / "fma_forest_share_by_year_1972_2025.csv"
if chk.exists():
    ref = pd.read_csv(chk).melt(id_vars="fma_id", var_name="year", value_name="ref")
    ref["year"] = ref.year.astype(int)
    j = B.merge(ref, on=["fma_id", "year"])
    if len(j):
        d = (j.forest_share_burned - j.ref).abs()
        log(f"check vs analysis/forest: {len(j)} area-years, max abs diff {d.max():.2e}", fh)
log(B[B.year == 2026].sort_values("forest_share_burned", ascending=False).head(12)[
    ["area_name", "province", "forest_share_burned", "prior10_share", "prior20_share", "prior40_share"]].round(4).to_string(), fh)
