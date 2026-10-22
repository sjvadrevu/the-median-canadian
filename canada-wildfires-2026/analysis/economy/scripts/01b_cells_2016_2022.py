"""Cell table for every 240 m cell burned in any year 2016-2022 (NBAC), for the per-year series.

Same columns as 01_cells.py (idx, row, col, area_ha, forest_ha, fma_id, park_id, prov) plus flags b2016..b2022.
Scale factor per province-year (NFD official area / NBAC mapped area outside national parks) is written to
work/scale_factors_2016_2025.csv (2023-2025 repeated from 01 for one consistent table).
Output: work/cells_1622.pkl
"""
import numpy as np
import pandas as pd
from ecommon import FWORK, WORK, FMA_ATTR, OFFICIAL
from grid import load, cell_area_m2, meta

m = meta()
Y = list(range(2016, 2023))
idx_by_year = {y: np.load(FWORK / f"burn_{y}.npy") for y in Y}
allidx = np.unique(np.concatenate(list(idx_by_year.values())))
fid, pid, fc = load("fma_id"), load("park_id"), load("forest_count")
area = cell_area_m2(allidx) / 1e4
df = pd.DataFrame(dict(idx=allidx, row=(allidx // m["W"]).astype("int32"), col=(allidx % m["W"]).astype("int32"),
                       area_ha=area, forest_ha=area * fc.ravel()[allidx] / 64.0,
                       fma_id=fid.ravel()[allidx], park_id=pid.ravel()[allidx]))
for y in Y:
    df[f"b{y}"] = np.isin(allidx, idx_by_year[y])
attr = pd.read_csv(FMA_ATTR)
df["prov"] = df.fma_id.map(dict(zip(attr.fma_id, attr.province))).fillna("outside")
df.to_pickle(WORK / "cells_1622.pkl")
print(len(df), "cells", df.area_ha.sum())

# scale factors 2016-2025 (2023-2025 from the 2023-2026 table)
c26 = pd.read_pickle(WORK / "cells.pkl")
off = pd.read_csv(OFFICIAL)
rows = []
for y in range(2016, 2026):
    d = df if y < 2023 else c26
    sel = d[f"b{y}"] & (d.park_id == 0)
    for p, g in d[sel].groupby("prov"):
        o = off[(off.year == y) & (off.ISO == p)].area_burned_ha.sum()
        mp = g.area_ha.sum()
        rows.append(dict(year=y, prov=p, official_ha=o, mapped_ha_outside_parks=mp,
                         factor=o / mp if (o > 0 and mp > 0) else np.nan))
pd.DataFrame(rows).to_csv(WORK / "scale_factors_2016_2025.csv", index=False)
