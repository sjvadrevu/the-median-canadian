"""Large-scale climate indices: monthly series 1950-2026 and winter/spring values per fire year.

Sources (raw files in raw/indices/):
  ONI   https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt  (3-month running ERSSTv5 Nino3.4
        anomaly; the 'DJF' row of year y = Dec y-1, Jan y, Feb y)
  PDO   https://psl.noaa.gov/pdo/data/pdo.timeseries.ersstv5.csv  (NOAA PSL, ERSSTv5 PDO; the NCEI
        ersst.v5.pdo.dat file returned HTTP 503 on 2026-10-21; PSL's Mantua pdo.data stops in 2025-07)
  AO    https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_ao_index/monthly.ao.index.b50.current.ascii
  NAO   https://www.cpc.ncep.noaa.gov/products/precip/CWlink/pna/norm.nao.monthly.b5001.current.ascii
  Polar vortex: zonal-mean zonal wind at 10 hPa, 60N, NCEP/NCAR Reanalysis 1 monthly means (NOAA PSL),
        file raw/indices/u10_60n_r1.csv if it could be downloaded (THREDDS NCSS); otherwise the
        January-March mean AO is used as the documented proxy (column vortex_source says which).

Fire year y: DJF = Dec y-1 + Jan y + Feb y; MAM = Mar-May y; JFM = Jan-Mar y; NDJFMA = Nov y-1 .. Apr y.
ENSO winter phase: DJF ONI >= 0.5 El Nino, <= -0.5 La Nina, else neutral (CPC threshold).
Outputs: work/indices_monthly.csv, indices_by_fire_year.csv (in analysis/climate/).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd

from common import OUT, RAW, WORK, log

R = RAW / "indices"
fh = open(WORK / "log_03.txt", "w")

# ---- monthly series, index = first of month
oni = pd.read_csv(R / "oni.ascii.txt", sep=r"\s+")
cen = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6, "JJA": 7, "JAS": 8, "ASO": 9,
       "SON": 10, "OND": 11, "NDJ": 12}
oni["date"] = pd.to_datetime(dict(year=oni.YR, month=oni.SEAS.map(cen), day=1))
oni_seas = oni.set_index(["YR", "SEAS"])["ANOM"]
m = pd.DataFrame({"oni_center": oni.set_index("date")["ANOM"]})

pdo = pd.read_csv(R / "pdo.timeseries.ersstv5.csv", skiprows=1, header=None, names=["date", "v"])
pdo["date"] = pd.to_datetime(pdo.date.str.strip())
pdo.loc[pdo.v < -99, "v"] = np.nan
m = m.join(pdo.set_index("date")["v"].rename("pdo"), how="outer")


def cpc(fn, name):
    d = pd.read_csv(R / fn, sep=r"\s+", header=None, names=["y", "mo", "v"])
    d["date"] = pd.to_datetime(dict(year=d.y, month=d.mo, day=1))
    return d.set_index("date")["v"].rename(name)


m = m.join(cpc("monthly.ao.index.b50.current.ascii", "ao"), how="outer")
m = m.join(cpc("norm.nao.monthly.b5001.current.ascii", "nao"), how="outer")

vortex_source = "AO Jan-Mar mean (proxy)"
uf = R / "u10_60n_r1.csv"
if uf.exists():
    u = pd.read_csv(uf)
    tcol = [c for c in u.columns if c.startswith("time")][0]
    vcol = [c for c in u.columns if c.startswith("uwnd")][0]
    u["date"] = pd.to_datetime(u[tcol].str[:10])
    zm = u.groupby("date")[vcol].mean()        # zonal mean over the 144 longitudes
    m = m.join(zm.rename("u10_60n"), how="outer")
    vortex_source = "NCEP/NCAR R1 zonal-mean U 10 hPa 60N, Jan-Mar mean (m/s)"
m = m.loc["1950-01-01":"2026-12-01"]
m.index.name = "date"
m.to_csv(WORK / "indices_monthly.csv")
log(f"monthly rows {len(m)}; last non-missing: " + str({c: str(m[c].dropna().index.max().date()) for c in m}), fh)


def mean_months(s, y, months):
    """months as (year_offset, month) relative to fire year y; NaN if any month missing."""
    v = [s.get(pd.Timestamp(year=y + o, month=mo, day=1), np.nan) for o, mo in months]
    return np.nan if np.any(np.isnan(v)) else float(np.mean(v))


DJF = [(-1, 12), (0, 1), (0, 2)]
MAM = [(0, 3), (0, 4), (0, 5)]
JFM = [(0, 1), (0, 2), (0, 3)]
SON = [(-1, 9), (-1, 10), (-1, 11)]
rows = []
for y in range(1951, 2027):
    r = dict(fire_year=y)
    r["oni_djf"] = oni_seas.get((y, "DJF"), np.nan)
    r["oni_mam"] = oni_seas.get((y, "MAM"), np.nan)
    r["oni_son_prev"] = oni_seas.get((y - 1, "SON"), np.nan)
    for k in ["pdo", "ao", "nao"]:
        r[f"{k}_djf"] = mean_months(m[k], y, DJF)
        r[f"{k}_mam"] = mean_months(m[k], y, MAM)
    r["ao_jfm"] = mean_months(m["ao"], y, JFM)
    if "u10_60n" in m:
        r["u10_60n_djf"] = mean_months(m["u10_60n"], y, DJF)
        r["u10_60n_jfm"] = mean_months(m["u10_60n"], y, JFM)
        r["vortex_jfm"] = r["u10_60n_jfm"]
    else:
        r["vortex_jfm"] = r["ao_jfm"]
    r["vortex_source"] = vortex_source
    o = r["oni_djf"]
    r["enso_winter_phase"] = "El Nino" if o >= 0.5 else ("La Nina" if o <= -0.5 else "neutral")
    rows.append(r)
I = pd.DataFrame(rows)
I.to_csv(OUT / "indices_by_fire_year.csv", index=False)
log(I[I.fire_year >= 2020].to_string(), fh)
