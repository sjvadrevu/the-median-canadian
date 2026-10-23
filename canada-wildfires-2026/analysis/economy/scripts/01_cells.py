"""Table of every burned 240 m cell in 2023-2026 (union) with year flags, area, forest, province, FMA.

Inputs: analysis/forest/work/burn_{2023..2026}.npy (flat cell indices; NBAC 2023-2025, CWFIS M3 2026),
fma_id.npy, park_id.npy, forest_count.npy, areal_scale_coarse.npy.
Output: work/cells.pkl with columns
  idx (uint32 flat index), row, col, yrmask (bit0=2023 .. bit3=2026), b2023..b2026 flags, last_year,
  area_ha (true ground area), forest_ha (Land Cover 2020 forest classes), fma_id, park_id, prov,
  w26 (scale weight to official 2026 total: provincial factor, Parks Canada factor in national parks),
  w_last (scale weight to the official total of the cell's most recent burn year; see 02 notes).
"""
import numpy as np
import pandas as pd
from ecommon import FWORK, WORK, FMA_ATTR, SCALING, OFFICIAL, YEARS
from grid import load, cell_area_m2, meta

m = meta()
idx_by_year = {y: np.load(FWORK / f"burn_{y}.npy") for y in YEARS}
allidx = np.unique(np.concatenate(list(idx_by_year.values())))
mask = np.zeros(allidx.size, dtype="uint8")
for b, y in enumerate(YEARS):
    mask[np.isin(allidx, idx_by_year[y])] |= (1 << b)
last = np.zeros(allidx.size, dtype="int16")
for b, y in enumerate(YEARS):
    last[(mask >> b) & 1 == 1] = y

fid = load("fma_id")
pid = load("park_id")
fc = load("forest_count")
row = (allidx // m["W"]).astype("int32")
col = (allidx % m["W"]).astype("int32")
area = cell_area_m2(allidx) / 1e4
df = pd.DataFrame(dict(idx=allidx, row=row, col=col, yrmask=mask, last_year=last,
                       **{f"b{y}": ((mask >> b) & 1).astype(bool) for b, y in enumerate(YEARS)},
                       area_ha=area, forest_ha=area * fc.ravel()[allidx] / 64.0,
                       fma_id=fid.ravel()[allidx], park_id=pid.ravel()[allidx]))
attr = pd.read_csv(FMA_ATTR)
df["prov"] = df.fma_id.map(dict(zip(attr.fma_id, attr.province))).fillna("outside")

# 2026 scale weight (official / mapped), as in analysis/forest
sf = pd.read_csv(SCALING).set_index("province")["scaling_factor"]
df["w26"] = df.prov.map(sf).astype(float)
df.loc[df.park_id > 0, "w26"] = sf["PC"]
df["w26"] = df["w26"].fillna(1.0)   # NU (no official total), outside: unscaled

# 2023-2025: official NFD provincial totals (no Parks Canada series) / mapped NBAC area outside parks.
off = pd.read_csv(OFFICIAL)
wl = np.ones(len(df))
rows = []
for y in YEARS[:3]:
    inyr = df[f"b{y}"]
    for p, g in df[inyr & (df.park_id == 0)].groupby("prov"):
        o = off[(off.year == y) & (off.ISO == p)].area_burned_ha.sum()
        mapped = g.area_ha.sum()
        f = o / mapped if (o > 0 and mapped > 0) else np.nan
        rows.append(dict(year=y, prov=p, official_ha=o, mapped_ha_outside_parks=mapped, factor=f))
fac = pd.DataFrame(rows)
fac.to_csv(WORK / "scale_factors_2023_2025.csv", index=False)
for y in YEARS[:3]:
    fy = fac[fac.year == y].set_index("prov").factor
    sel = (df.last_year == y) & (df.park_id == 0)
    wl[sel.values] = df.loc[sel, "prov"].map(fy).fillna(1.0).values
sel = df.last_year == 2026
wl[sel.values] = df.loc[sel, "w26"].values
df["w_last"] = wl
df.to_pickle(WORK / "cells.pkl")
print(len(df), "cells; union ha", df.area_ha.sum(), "forest ha", df.forest_ha.sum())
for y in YEARS:
    s = df[f"b{y}"]
    print(y, "mapped ha", df.area_ha[s].sum(), "forest", df.forest_ha[s].sum())
print("2026 scaled ha", (df.area_ha * df.w26)[df.b2026].sum())
print(fac.to_string())
