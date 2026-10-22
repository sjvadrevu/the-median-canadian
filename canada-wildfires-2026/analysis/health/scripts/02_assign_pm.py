"""Step 2: daily PM2.5 for every dissemination area (DA), 2018-01-01 to 2026-10-19.

Method
- Station-day values from ../../data/smoke-cost/station_daily_pm25_2018_2026.csv. Where a station-day has both a
  NAPS validated value and an AirNow real-time value, the NAPS value is used.
- Each DA representative point gets, on each day, the value of the NEAREST station REPORTING THAT DAY within
  R km (great-circle distance). R = 50 km (main) and 25 km (sensitivity). No station within R that day -> no value.
- Background per station: median of the station's daily values for the same calendar month over 2018-2024
  (needs >= 60 values; otherwise all available years 2018-2026 are used and the station is flagged).
- Wildfire-season increment (smoke above background) per DA-day = max(0, PM2.5 - background of the assigned station).

DAs sharing the same ordered candidate-station list are grouped ("combos") so arrays are combo x day.
Outputs (work/): R{50,25}_combo_pm.npy, _combo_inc.npy, _combo_src.npy (1 = validated, 0 = real-time),
R{50,25}_da_combo.csv, dates.csv, stations.csv, station_background.csv
"""
import os, numpy as np, pandas as pd
from scipy.spatial import cKDTree

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(H)
D = os.path.dirname(W) + "/data/smoke-cost"
WK = f"{H}/work"
EARTH = 6371.0088

s = pd.read_csv(f"{D}/station_daily_pm25_2018_2026.csv", dtype={"naps_id": str},
                usecols=["naps_id", "date", "pm25", "source", "Latitude", "Longitude", "Station_Name", "Province"])
s["pri"] = (s.source == "NAPS_validated").astype(int)
s = s.sort_values(["naps_id", "date", "pri"]).drop_duplicates(["naps_id", "date"], keep="last")
st = s.groupby("naps_id").agg(lat=("Latitude", "last"), lon=("Longitude", "last"),
                              name=("Station_Name", "last"), prov=("Province", "last"),
                              n_days=("date", "size"), first=("date", "min"), last=("date", "max")).reset_index()
st["idx"] = np.arange(len(st))
dates = pd.date_range("2018-01-01", s.date.max(), freq="D")
di = pd.Series(np.arange(len(dates)), index=dates.strftime("%Y-%m-%d"))
si = st.set_index("naps_id")["idx"]
PM = np.full((len(st), len(dates)), np.nan, dtype=np.float32)
VAL = np.zeros((len(st), len(dates)), dtype=np.int8)
r, c = si[s.naps_id].values, di[s.date].values
PM[r, c] = s.pm25.values
VAL[r, c] = s.pri.values
print("stations", len(st), "days", len(dates), "station-days", int(np.isfinite(PM).sum()))

# background: monthly median 2018-2024
month = dates.month.values
yr = dates.year.values
BG = np.full((len(st), 13), np.nan, dtype=np.float32)
bg_rows = []
for m in range(1, 13):
    ref = (month == m) & (yr <= 2024)
    alt = (month == m)
    x = PM[:, ref]
    n = np.isfinite(x).sum(1)
    med = np.nanmedian(np.where(np.isfinite(x), x, np.nan), axis=1) if True else None
    xa = PM[:, alt]
    meda = np.nanmedian(xa, axis=1)
    use_alt = n < 60
    BG[:, m] = np.where(use_alt, meda, med)
    for k in range(len(st)):
        bg_rows.append((st.naps_id[k], m, float(BG[k, m]), int(n[k]), bool(use_alt[k])))
bg = pd.DataFrame(bg_rows, columns=["naps_id", "month", "background_median", "n_ref_days_2018_2024", "used_all_years"])
bg.to_csv(f"{WK}/station_background.csv", index=False)
print("stations-months using fallback background:", int(bg.used_all_years.sum()))

def unit(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]

da = pd.read_csv(f"{WK}/da_attr.csv", dtype={"DAUID": str}, usecols=["DAUID", "lat", "lon"])
U = unit(da.lat.values, da.lon.values)
tree = cKDTree(unit(st.lat.values, st.lon.values))
K = 12
dd, ii = tree.query(U, k=K)
dkm = 2 * EARTH * np.arcsin(np.clip(dd / 2, 0, 1))
mi = np.nanmonth = None
mon_idx = month  # for background lookup

for R in (50, 25):
    cand = np.where(dkm <= R, ii, -1)
    keys = pd.Series([",".join(map(str, row[row >= 0])) for row in cand])
    codes, uniq = pd.factorize(keys)
    nC = len(uniq)
    C = np.full((nC, K), -1, dtype=np.int32)
    first = pd.Series(np.arange(len(codes))).groupby(codes).first().values
    C[:] = cand[first]
    out_pm = np.full((nC, len(dates)), np.nan, dtype=np.float32)
    out_st = np.full((nC, len(dates)), -1, dtype=np.int32)
    for k in range(K):
        col = C[:, k]
        ok = col >= 0
        v = np.where(ok[:, None], PM[np.where(ok, col, 0)], np.nan)
        fill = np.isnan(out_pm) & np.isfinite(v)
        out_pm[fill] = v[fill]
        out_st[fill] = np.broadcast_to(col[:, None], fill.shape)[fill]
    has = out_st >= 0
    bgv = np.where(has, BG[np.where(has, out_st, 0), mon_idx[None, :]], np.nan)
    inc = np.where(has, np.maximum(0, out_pm - bgv), np.nan).astype(np.float32)
    src = np.where(has, VAL[np.where(has, out_st, 0), np.arange(len(dates))[None, :]], -1).astype(np.int8)
    np.save(f"{WK}/R{R}_combo_pm.npy", out_pm)
    np.save(f"{WK}/R{R}_combo_inc.npy", inc)
    np.save(f"{WK}/R{R}_combo_src.npy", src)
    np.save(f"{WK}/R{R}_combo_station.npy", out_st)
    pd.DataFrame({"DAUID": da.DAUID, "combo": codes, "nearest_station_km": np.round(dkm[:, 0], 2),
                  "n_stations_within_R": (cand >= 0).sum(1)}).to_csv(f"{WK}/R{R}_da_combo.csv", index=False)
    print(f"R={R} km: combos {nC}; DAs with no station ever within R: {int((cand[:, 0] < 0).sum())}")

pd.DataFrame({"date": dates.strftime("%Y-%m-%d")}).to_csv(f"{WK}/dates.csv", index=False)
st.to_csv(f"{WK}/stations.csv", index=False)
