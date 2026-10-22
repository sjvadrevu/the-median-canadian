"""Helpers to load the 240 m grid layers and rasterize burn footprints to flat cell indices."""
import json
import numpy as np
from affine import Affine
from rasterio import features
from common import WORK

_meta = None


def meta():
    global _meta
    if _meta is None:
        m = json.load(open(WORK / "grid_meta.json"))
        m["T"] = Affine(*m["transform"])
        _meta = m
    return _meta


def load(name, mmap=True):
    return np.load(WORK / f"{name}.npy", mmap_mode="r" if mmap else None)


def cell_area_m2(idx):
    """True (equal-area) ground area in m2 of 240 m cells given flat indices."""
    m = meta()
    asc = load("areal_scale_coarse", mmap=False)
    r = (idx // m["W"]) // m["step"]
    c = (idx % m["W"]) // m["step"]
    r = np.minimum(r, asc.shape[0] - 1)
    c = np.minimum(c, asc.shape[1] - 1)
    return 57600.0 / asc[r, c].astype("float64")


def rasterize_idx(geoms):
    """Flat indices (uint32) of cells whose centre falls inside any geometry (grid CRS)."""
    m = meta()
    geoms = [g for g in geoms if g is not None and not g.is_empty]
    if not geoms:
        return np.zeros(0, dtype="uint32")
    a = features.rasterize(((g, 1) for g in geoms), out_shape=(m["H"], m["W"]),
                           transform=m["T"], fill=0, dtype="uint8")
    return np.flatnonzero(a).astype("uint32")
