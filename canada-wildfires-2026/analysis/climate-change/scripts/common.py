"""Shared paths and settings for analysis/climate-change/.

Area layer: data/geo/fma_v2.gpkg (186 rows). Area attributes, forest hectares and burn history are reused
from analysis/cause/work/areas_fcd292dde04d/ (the fma_v2 cache, hash of fma_v2.gpkg) and
analysis/cause/burn_history_by_area_year.csv (NBAC 1972-2025, CWFIS M3 2026; fma_v2 ids).
Single-threaded on purpose (shared machine).
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE.parent                         # analysis/climate-change
BASE = OUT.parents[1]                     # .../wildfire
RAW = OUT / "raw"
WORK = OUT / "work"
WORK.mkdir(exist_ok=True)
AREA_FILE = BASE / "data" / "geo" / "fma_v2.gpkg"
AREA_HASH = "fcd292dde04d"
CAUSE = BASE / "analysis" / "cause"
CAUSE_AREAS = CAUSE / "work" / f"areas_{AREA_HASH}"
CLIMATE = BASE / "analysis" / "climate"
CLIMATE_AREAS = CLIMATE / "work" / f"areas_{AREA_HASH}"
WEATHER = BASE / "analysis" / "weather"
FOREST = BASE / "analysis" / "forest"
FIRE = BASE / "data" / "fire"

NORMAL = (1961, 1990)
RECENT = (2016, 2026)
REGION = {"BC": "BC", "AB": "Prairies", "SK": "Prairies", "MB": "Prairies", "ON": "Ontario",
          "QC": "Quebec", "YT": "North", "NT": "North", "NU": "North",
          "NB": "Atlantic", "NS": "Atlantic", "PE": "Atlantic", "NL": "Atlantic"}
REGIONS = ["BC", "Prairies", "Ontario", "Quebec", "Atlantic", "North"]


def log(msg, fh=None):
    print(msg, flush=True)
    if fh is not None:
        fh.write(str(msg) + "\n")
        fh.flush()


def areas():
    """fma_v2 areas with forest hectares, region and the cause model's eligibility rule
    (forest >= 100,000 ha, forest >= 5% of land, not Nunavut)."""
    a = pd.read_csv(CAUSE_AREAS / "areas.csv")
    f = pd.read_csv(CAUSE_AREAS / "area_forest.csv")[["fma_id", "forest_ha", "land_ha_grid"]]
    a = a.merge(f, on="fma_id", how="left")
    a["region"] = a.province.map(REGION)
    a["eligible"] = (a.forest_ha >= 1e5) & (a.forest_ha / a.land_ha_grid >= 0.05) & (a.province != "NU")
    return a


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------- trend statistics
def trend_stats(years, values, per=10.0):
    """OLS slope with a lag-1 autocorrelation-adjusted 95% interval (effective sample size,
    n_eff = n (1 - r1) / (1 + r1)), Theil-Sen slope with its 95% interval, Mann-Kendall p (Kendall tau
    of value on year). Slopes are per `per` years."""
    from scipy import stats
    x = np.asarray(years, float)
    y = np.asarray(values, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = len(x)
    if n < 10:
        return dict(n=n)
    b, a = np.polyfit(x, y, 1)
    res = y - (a + b * x)
    r1 = np.corrcoef(res[:-1], res[1:])[0, 1]
    r1c = max(r1, 0)
    neff = n * (1 - r1c) / (1 + r1c)
    se = np.sqrt((res ** 2).sum() / (n - 2) / ((x - x.mean()) ** 2).sum()) * np.sqrt((n - 2) / max(neff - 2, 1))
    t = stats.t.ppf(0.975, max(neff - 2, 1))
    pv = 2 * (1 - stats.t.cdf(abs(b / se), max(neff - 2, 1)))
    ts = stats.theilslopes(y, x, 0.95)
    tau, mkp = stats.kendalltau(x, y)
    return dict(n=n, ols_per=b * per, ols_lo=(b - t * se) * per, ols_hi=(b + t * se) * per, ols_p_ar1=pv,
                r1=r1, n_eff=neff, sen_per=ts[0] * per, sen_lo=ts[2] * per, sen_hi=ts[3] * per,
                mk_tau=tau, mk_p=mkp)
