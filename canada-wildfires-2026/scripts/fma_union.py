"""Per fire management area (fma_v2): forest burned 2023 to 2026 as a union (overlaps counted once),
plus mapped all-land hectares and mapped forest hectares per year 2023 to 2026.
Reuses the analysis/forest 240 m grid and burn indices; no new data.
Output: <src>/site-build/fma_union_2023_2026.csv
Usage: python scripts/fma_union.py /path/to/wildfire"""
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ.get("WILDFIRE_SRC", "../wildfire"))
FOREST_SCRIPTS = SRC / "analysis" / "forest" / "scripts"
sys.path.insert(0, str(FOREST_SCRIPTS))
from common import WORK, OUT  # noqa: E402
from grid import meta, load, cell_area_m2  # noqa: E402

m = meta()
fc = load("forest_count")
fid = load("fma_v2_id")
T = pd.read_csv(OUT / "fma_2026_table.csv")
nf = int(T.fma_id.max()) + 1


def forest_w(idx):
    rc = np.unravel_index(idx, (m["H"], m["W"]))
    return np.asarray(fc[rc], dtype="float64") * 900.0 * cell_area_m2(idx) / 57600.0


rows = {}
B = {y: np.load(WORK / f"burn_{y}.npy") for y in (2023, 2024, 2025, 2026)}
for y, idx in B.items():
    rc = np.unravel_index(idx, (m["H"], m["W"]))
    f = np.asarray(fid[rc]).astype("int64")
    rows[f"forest_mapped_ha_{y}"] = np.bincount(f, weights=forest_w(idx), minlength=nf) / 1e4
    rows[f"land_mapped_ha_{y}"] = np.bincount(f, weights=cell_area_m2(idx), minlength=nf) / 1e4
u = np.unique(np.concatenate(list(B.values())))
rc = np.unravel_index(u, (m["H"], m["W"]))
f = np.asarray(fid[rc]).astype("int64")
rows["forest_union_ha_2023_2026"] = np.bincount(f, weights=forest_w(u), minlength=nf) / 1e4
rows["land_union_ha_2023_2026"] = np.bincount(f, weights=cell_area_m2(u), minlength=nf) / 1e4
D = pd.DataFrame(rows)
D.index.name = "fma_id"
D = D.loc[T.fma_id.values]
D["forest_ha"] = T.set_index("fma_id").forest_ha
D["forest_share_union_2023_2026"] = D.forest_union_ha_2023_2026 / D.forest_ha.replace(0, np.nan)
out = SRC / "site-build" / "fma_union_2023_2026.csv"
D.to_csv(out)
tot = D.forest_union_ha_2023_2026.sum()
print(f"union forest {tot:,.0f} ha (analysis/forest says 20,784,452 ha); share {tot / D.forest_ha.sum():.4%}")
chk = (D.forest_mapped_ha_2026 / D.forest_ha - T.set_index("fma_id").forest_share_burned_2026).abs().max()
print("max diff vs 2026 share in table:", chk)
