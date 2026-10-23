"""All-land hectares burned per fma_v2 area and year, 1972-2026, from the analysis/forest 240 m burn rasters.

Same cell rule and true-area correction as analysis/climate/scripts/05_areas_outcome.py: burn_YYYY.npy holds the
flat indices of 240 m cells burned in year Y (NBAC 1972-2025, CWFIS M3 2026), the area id comes from
analysis/forest/work/fma_v2_id.npy, cell area = 57,600 m2 / areal scale factor. Forest burned ha per cell is
from the Land Cover 2020 forest count. 2026 also gets burned_ha_scaled = burned_ha x the province's official/M3
factor (analysis/forest/scaling_factors_by_province.csv).
Reason: the forest share series uses the 2020 land cover, which misses forest that burned in about 1995-2019 and
had not regrown by 2020 (07 shows forest ha per burned ha falling from 0.52 in the 1970s to 0.19 in the 2010s
and back to 0.66 in 2020-2026). All-land hectares do not depend on the 2020 map, so the model (09) uses them.
Output: work/area_burned_ha_1972_2026.csv, work/log_08.txt
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd

from common import WORK, FOREST, areas, log

fh = open(WORK / "log_08.txt", "w")
FW = FOREST / "work"
A = areas()
m = json.load(open(FW / "grid_meta.json"))
H, W, step = m["H"], m["W"], m["step"]
grid = np.load(FW / "fma_v2_id.npy", mmap_mode="r").reshape(-1)
asc = np.load(FW / "areal_scale_coarse.npy").astype("float64")
fc = np.load(FW / "forest_count.npy", mmap_mode="r").reshape(-1)
nmax = int(A.fma_id.max()) + 1
SC = pd.read_csv(FOREST / "scaling_factors_by_province.csv").set_index("province").scaling_factor
rows = []
for y in range(1972, 2027):
    idx = np.load(FW / f"burn_{y}.npy").astype("int64")
    ids = np.asarray(grid[idx]).astype("int64")
    r = np.minimum((idx // W) // step, asc.shape[0] - 1)
    c = np.minimum((idx % W) // step, asc.shape[1] - 1)
    ca = 57600.0 / asc[r, c]
    fa = np.asarray(fc[idx], "float64") * 900.0 * ca / 57600.0
    b = np.bincount(ids, weights=ca, minlength=nmax)[:nmax] / 1e4
    bf = np.bincount(ids, weights=fa, minlength=nmax)[:nmax] / 1e4
    for i in A.fma_id:
        rows.append((int(i), y, b[i], bf[i]))
    log(f"{y} burned {b[1:].sum():,.0f} ha (outside areas {b[0]:,.0f}), forest {bf[1:].sum():,.0f} ha", fh)
    del idx, ids, ca, fa
O = pd.DataFrame(rows, columns=["fma_id", "year", "burned_ha", "forest_burned_ha"])
O = O.merge(A[["fma_id", "province", "forest_ha", "land_ha_grid"]], on="fma_id")
O["burned_ha_scaled"] = np.where(O.year == 2026, O.burned_ha * O.province.map(SC).fillna(1.0), O.burned_ha)
O["land_share_burned"] = O.burned_ha_scaled / O.land_ha_grid
O.to_csv(WORK / "area_burned_ha_1972_2026.csv", index=False)
