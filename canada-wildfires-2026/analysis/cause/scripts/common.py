"""Shared paths and helpers for the 2026 wildfire cause analysis (analysis/cause/).

Area file: set the environment variable AREA_FILE to a GeoPackage with the same columns as
data/geo/fma_all.gpkg (fma_id integer, agency, area_name, province, area_level). Rows whose agency is
"Parks Canada" are treated as an overlapping layer and ignored; the remaining rows must tile Canada.
Everything that depends on the areas is cached under work/areas_<hash>/ so a new file triggers a rebuild.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE.parent                                   # analysis/cause
BASE = OUT.parents[1]                               # .../wildfire
DATA = BASE / "data"
WORK = OUT / "work"
WORK.mkdir(exist_ok=True)
FOREST_DIR = BASE / "analysis" / "forest"
FOREST_WORK = FOREST_DIR / "work"
WEATHER_DIR = BASE / "analysis" / "weather"
SEASON = BASE / "season"

DEFAULT_AREA_FILE = DATA / "geo" / "fma_all.gpkg"
AREA_FILE = Path(os.environ.get("AREA_FILE", str(DEFAULT_AREA_FILE))).resolve()

FIRE_LIST_2026 = SEASON / "nrcan_fire_list.json"
OFFICIAL_BY_CAUSE_2026 = SEASON / "nrcan_ytd_by-agency_by-response-type_group_by_stage_of_control_true_group_by_status_true_group_by_cause_true.json"
NT_POINTS_2026 = DATA / "fire" / "raw" / "provincial" / "nt" / "nt_fires_points_2026.json"
CNFDB_ZIP = DATA / "fire" / "raw" / "nfdb" / "NFDB_point_txt.zip"
CNFDB_MEMBER = "NFDB_point_20260811.txt"
NFD_AREA_CAUSE = SEASON / "NFD_-_Area_burned_by_cause_class_-_EN_FR.csv"
NFD_NUM_CAUSE = SEASON / "NFD_-_Number_of_fires_by_cause_class_-_EN_FR.csv"
DA_POINTS = DATA / "geo" / "statcan" / "da_2021_pop_points.gpkg"
POPCENTRES = DATA / "geo" / "statcan" / "popcentres_2021_pop.gpkg"
SCALING = FOREST_DIR / "scaling_factors_by_province.csv"

EA = "ESRI:102001"
GRID_CRS = "EPSG:3979"
PROVS = ["BC", "AB", "SK", "MB", "ON", "QC", "NB", "NS", "PE", "NL", "YT", "NT", "NU"]
CAUSES = ["lightning", "human", "undetermined"]


def area_hash():
    h = hashlib.sha1()
    with open(AREA_FILE, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def area_dir():
    d = WORK / f"areas_{area_hash()}"
    d.mkdir(exist_ok=True)
    return d


def area_attrs():
    """Non-park areas (the tiling layer) as a DataFrame."""
    a = pd.read_csv(area_dir() / "areas.csv")
    return a


def grid_meta():
    from affine import Affine
    m = json.load(open(FOREST_WORK / "grid_meta.json"))
    m["T"] = Affine(*m["transform"])
    return m


def area_grid():
    """uint8/uint16 array (H, W): area id of each 240 m cell, 0 outside. Memory-mapped."""
    p = json.load(open(area_dir() / "grid_path.json"))["path"]
    return np.load(p, mmap_mode="r")


def lonlat_to_cell(lon, lat):
    """Row, col on the 240 m grid (EPSG:3979) for lon/lat arrays; -1 when off grid."""
    from pyproj import Transformer
    m = grid_meta()
    tr = Transformer.from_crs("EPSG:4326", GRID_CRS, always_xy=True)
    x, y = tr.transform(np.asarray(lon, float), np.asarray(lat, float))
    T = m["T"]
    c = np.floor((x - T.c) / T.a).astype("int64")
    r = np.floor((y - T.f) / T.e).astype("int64")
    ok = (r >= 0) & (r < m["H"]) & (c >= 0) & (c < m["W"]) & np.isfinite(x) & np.isfinite(y)
    r[~ok] = -1
    c[~ok] = -1
    return r, c


def assign_area(lon, lat, max_snap_m=10000):
    """Area id for points: the 240 m raster cell first; points on cells outside every area
    (coast, border) snap to the nearest area polygon within max_snap_m; otherwise 0."""
    import geopandas as gpd
    lon = np.asarray(lon, float)
    lat = np.asarray(lat, float)
    g = area_grid()
    r, c = lonlat_to_cell(lon, lat)
    out = np.zeros(len(lon), dtype="int64")
    ok = r >= 0
    out[ok] = np.asarray(g[r[ok], c[ok]])
    miss = np.flatnonzero((out == 0) & np.isfinite(lon) & np.isfinite(lat))
    if len(miss):
        polys = gpd.read_file(area_dir() / "areas_simplified_1km.gpkg")
        pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon[miss], lat[miss]), crs="EPSG:4326").to_crs(polys.crs)
        pts["k"] = miss
        j = gpd.sjoin_nearest(pts, polys[["fma_id", "geometry"]], how="left", max_distance=max_snap_m)
        j = j[~j.index.duplicated()]
        v = j.fma_id.fillna(0).astype("int64").values
        out[j.k.values] = v
    return out


_ASC = None


def areal_scale(idx):
    """Lambert conformal areal scale factor for flat 240 m cell indices (coarse lattice from forest/02_grid.py)."""
    global _ASC
    if _ASC is None:
        _ASC = np.load(FOREST_WORK / "areal_scale_coarse.npy").astype("float64")
    m = grid_meta()
    r = (idx // m["W"]) // m["step"]
    c = (idx % m["W"]) // m["step"]
    return _ASC[np.minimum(r, _ASC.shape[0] - 1), np.minimum(c, _ASC.shape[1] - 1)]


def forest_ha(idx):
    """Equal-area forest hectares (Land Cover 2020 classes 1,2,5,6) in flat 240 m cells."""
    fc = np.load(FOREST_WORK / "forest_count.npy", mmap_mode="r")
    m = grid_meta()
    rr, cc = np.unravel_index(idx, (m["H"], m["W"]))
    return np.asarray(fc[rr, cc], dtype="float64") * 900.0 / areal_scale(idx) / 1e4


def burn_idx(year):
    """Flat cell indices burned in a year: NBAC 1972-2025, CWFIS M3 2026 (forest/03_rasterize_burns.py)."""
    return np.load(FOREST_WORK / f"burn_{year}.npy")


def theil_sen(years, values):
    """Theil-Sen slope per year, Kendall tau and p-value (scipy)."""
    from scipy import stats
    y = np.asarray(values, float)
    x = np.asarray(years, float)
    ok = np.isfinite(y) & np.isfinite(x)
    if ok.sum() < 5:
        return dict(slope=np.nan, lo=np.nan, hi=np.nan, tau=np.nan, p=np.nan, n=int(ok.sum()))
    s, icpt, lo, hi = stats.theilslopes(y[ok], x[ok])
    t, p = stats.kendalltau(x[ok], y[ok])
    return dict(slope=s, intercept=icpt, lo=lo, hi=hi, tau=t, p=p, n=int(ok.sum()))


def log(msg, fh=None):
    print(msg, flush=True)
    if fh is not None:
        fh.write(str(msg) + "\n")
        fh.flush()
