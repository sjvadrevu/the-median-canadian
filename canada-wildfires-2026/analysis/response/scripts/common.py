"""Shared paths for analysis/response (did the 2023-2026 area burned come from fires that escaped early control?)."""
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE.parent                       # analysis/response
BASE = OUT.parents[1]                   # .../wildfire
DATA = BASE / "data"
RAW = OUT / "raw"
WORK = OUT / "work"
WORK.mkdir(exist_ok=True)
SEASON = BASE / "season"
EA = "ESRI:102001"                      # Canada Albers equal area

NBAC_SHP = DATA / "fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp"
CNFDB_ZIP = DATA / "fire/raw/nfdb/NFDB_point_txt.zip"
CNFDB_MEMBER = "NFDB_point_20260811.txt"
M3_2026 = DATA / "fire/m3_perimeters_2026_cwfis_20261020.gpkg"
HOTSPOT_DIR = DATA / "fire/raw/hotspots_wfs_2026"
FIRE_LIST_2026 = SEASON / "nrcan_fire_list.json"
NT_POINTS_2026 = DATA / "fire/raw/provincial/nt/nt_fires_points_2026.json"
OUTLINE_CLASS = BASE / "analysis/outline-check/outline_class_2026.geojson"
PROV_POLY = DATA / "geo/statcan/lpr_000b21a_e_provinces_2021.gpkg"
SCALING = BASE / "analysis/forest/scaling_factors_by_province.csv"
PROVS = ["BC", "AB", "SK", "MB", "ON", "QC", "NB", "NS", "PE", "NL", "YT", "NT", "NU"]


def theil_sen(years, values):
    from scipy import stats
    y = np.asarray(values, float); x = np.asarray(years, float)
    ok = np.isfinite(y) & np.isfinite(x)
    if ok.sum() < 5:
        return dict(slope=np.nan, lo=np.nan, hi=np.nan, tau=np.nan, p=np.nan, n=int(ok.sum()))
    s, icpt, lo, hi = stats.theilslopes(y[ok], x[ok])
    t, p = stats.kendalltau(x[ok], y[ok])
    return dict(slope=s, lo=lo, hi=hi, tau=t, p=p, n=int(ok.sum()))
