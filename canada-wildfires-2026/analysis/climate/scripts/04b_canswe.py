"""CanSWE v8 (Canadian historical Snow Water Equivalent dataset, 1928-2025; ECCC, Vionnet et al.;
Zenodo record 19075529, file CanSWE-CanEEN_1928-2025_v8.nc) -> 1 April snow water equivalent per
station and fire year 1991-2025 (no 2026 data in the dataset).

1 April SWE = the measurement closest to 1 April within +/- 10 days (snow courses are sampled around
the 1st of the month; automatic stations report daily). Values with agency flag 'E' (estimate) are kept;
CanSWE QC has already set failed values to NaN.
Output: work/canswe_station_year.csv (station_id, lon, lat, elevation, source, fire_year, swe_apr1_mm)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h5py
import numpy as np
import pandas as pd

from common import RAW, WORK, log

fh = open(WORK / "log_04b.txt", "w")
f = h5py.File(RAW / "canswe" / "CanSWE-CanEEN_1928-2025_v8.nc", "r")
t0 = pd.Timestamp("1928-01-01")
days = f["time"][:]
dates = t0 + pd.to_timedelta(days, unit="D")
st = pd.DataFrame({"station_id": [x.decode() for x in f["station_id"][:]],
                   "lon": f["lon"][:], "lat": f["lat"][:], "elevation": f["elevation"][:],
                   "source": [x.decode() for x in f["source"][:]], "type_mes": f["type_mes"][:]})
years = range(1991, 2026)
cols = {}
for y in years:
    tgt = pd.Timestamp(f"{y}-04-01")
    idx = np.where((dates >= tgt - pd.Timedelta(days=10)) & (dates <= tgt + pd.Timedelta(days=10)))[0]
    cols[y] = (idx, np.abs((dates[idx] - tgt).days.values))
lo = min(c[0].min() for c in cols.values())
hi = max(c[0].max() for c in cols.values()) + 1
fill = 9.96921e36
out = []
B = 200
for s0 in range(0, len(st), B):
    a = f["snw"][s0:s0 + B, lo:hi].astype("float64")
    a[a >= fill * 0.9] = np.nan
    for y, (idx, dd) in cols.items():
        sub = a[:, idx - lo]
        order = np.argsort(dd, kind="stable")
        sub = sub[:, order]
        ok = ~np.isnan(sub)
        first = np.where(ok.any(1), ok.argmax(1), -1)
        val = np.where(first >= 0, sub[np.arange(len(sub)), np.maximum(first, 0)], np.nan)
        out.append(pd.DataFrame({"row": np.arange(s0, s0 + len(sub)), "fire_year": y, "swe_apr1_mm": val}))
O = pd.concat(out)
O = O[O.swe_apr1_mm.notna()]
O = O.join(st, on="row").drop(columns="row")
O.to_csv(WORK / "canswe_station_year.csv", index=False)
log(f"CanSWE stations {len(st)}; station-years with 1 Apr SWE 1991-2025: {len(O)}; stations: {O.station_id.nunique()}", fh)
log(O.groupby("fire_year").size().to_string(), fh)
