"""Shared paths for the economic-value analysis. Reuses the 240 m burned-cell tables and kNN volumes from
analysis/economy (cells.pkl = 2023-2026 union cells, cells_1622.pkl = 2016-2022 cells)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[3]          # .../wildfire
DATA = BASE / "data"
ECON = BASE / "analysis" / "economy"
EWORK = ECON / "work"
OUT = BASE / "analysis" / "economic-value"
RAW = OUT / "raw"
WORK = OUT / "work"
WORK.mkdir(parents=True, exist_ok=True)
sys.path.append(str(BASE / "analysis" / "forest" / "scripts"))
YEARS = list(range(2016, 2027))


def burned_cells():
    """Long table: one row per (cell, fire year) 2016-2026 with merchantable volume (kNN 2011) and the scale
    weight to official provincial totals used in analysis/economy (07b)."""
    c26 = pd.read_pickle(EWORK / "cells.pkl")
    c16 = pd.read_pickle(EWORK / "cells_1622.pkl")
    k26 = np.load(EWORK / "knn2011.npz")
    k16 = np.load(EWORK / "knn2011_cells_1622.npz")
    c26["vol_merch"] = k26["vol_merch_per_ha"].astype("float64") * c26.area_ha.values
    c16["vol_merch"] = k16["vol_merch_per_ha"].astype("float64") * c16.area_ha.values
    sf = pd.read_csv(EWORK / "scale_factors_2016_2025.csv")
    fac = {(r.year, r.prov): r.factor for r in sf.itertuples()}
    parts = []
    for y in YEARS:
        src = c16 if y < 2023 else c26
        d = src.loc[src[f"b{y}"], ["idx", "prov", "park_id", "fma_id", "area_ha", "forest_ha", "vol_merch"] +
                    (["w26"] if y == 2026 else [])].copy()
        if y == 2026:
            d["w"] = d.pop("w26")
        else:
            d["w"] = [1.0 if pk > 0 else fac.get((y, p), 1.0) for p, pk in zip(d.prov, d.park_id)]
        d["year"] = y
        parts.append(d)
    out = pd.concat(parts, ignore_index=True)
    out["prov"] = out.prov.astype("category")
    # 2023-2026 union (each cell once), weight = w_last as in economy/07
    u = c26[["idx", "prov", "park_id", "fma_id", "area_ha", "forest_ha", "vol_merch", "w_last"]].rename(columns={"w_last": "w"})
    u["year"] = 0  # 0 = 2023-2026 union
    del c26, c16
    out = pd.concat([out, u], ignore_index=True)
    out["prov"] = out.prov.astype("category")
    out["year"] = out.year.astype("int16")
    return out.drop(columns=["fma_id", "forest_ha"])


def rasterize_idx_window(geoms):
    """Flat grid indices (cell centre inside) computed on the geometries' bounding window only (saves memory)."""
    from rasterio import features
    from affine import Affine
    from grid import meta
    m = meta()
    T = m["T"]
    geoms = [g for g in geoms if g is not None and not g.is_empty]
    xs0, ys0, xs1, ys1 = np.array([g.bounds for g in geoms]).T
    c0 = max(int((xs0.min() - T.c) // 240) - 1, 0); c1 = min(int((xs1.max() - T.c) // 240) + 2, m["W"])
    r0 = max(int((T.f - ys1.max()) // 240) - 1, 0); r1 = min(int((T.f - ys0.min()) // 240) + 2, m["H"])
    Tw = T * Affine.translation(c0, r0)
    a = features.rasterize(((g, 1) for g in geoms), out_shape=(r1 - r0, c1 - c0), transform=Tw, fill=0, dtype="uint8")
    rr, cc = np.nonzero(a)
    return ((rr + r0).astype("int64") * m["W"] + (cc + c0)).astype("uint32")
