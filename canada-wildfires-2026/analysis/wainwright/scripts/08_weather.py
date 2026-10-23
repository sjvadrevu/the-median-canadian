"""Step 8: conditions on 2026-10-17 at CFB Wainwright and how unusual they were.
Inputs: raw/eccc/hourly/*.csv.gz, raw/eccc/daily/*.csv.gz (ECCC climate-hourly / climate-daily),
work/cwfis_fwi_near.csv (CWFIS station FWI, noon LST), CWFIS daily FWI grids (data/fire/raw/fwi_grids_daily).
ECCC LOCAL_DATE is local standard time (LST = UTC-7 = MDT-1). Afternoon = 10:00-17:00 LST (11:00-18:00 MDT),
day kept if >= 6 of 8 hours have the variable.
Comparison sets: 'mid-October' = every Oct 10-24 day of earlier years in the station record (2026 excluded);
'summer' = every Jun 1-Aug 31 day of all years incl. 2026.
Rank 1 = most extreme. Percentile = share of comparison days with a value strictly below (above for RH) Oct 17.
Outputs: weather_oct17_hourly.csv, weather_oct17_ranks.csv, weather_rain_freeze.csv, weather_precip_jun_oct.csv
"""
import glob, sys, numpy as np, pandas as pd, rasterio
from pyproj import Transformer
sys.path.insert(0, __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/climate-change/scripts")
from fwi import isi as ISI, fwi as FWI
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
G = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/data/fire/raw/fwi_grids_daily"
F = "2026-10-17"
def midoct(dates):
    md = dates.str[5:10]; return (md >= "10-10") & (md <= "10-24") & (dates.str[:4] < "2026")
def summer(dates):
    m = dates.str[5:7]; return m.isin(["06", "07", "08"])
ranks = []
def rank(name, station, ser, high=True, unit=""):
    """ser: index date string -> value."""
    ser = ser.dropna(); v = ser.get(F, np.nan)
    if np.isnan(v): return
    for label, mask in [("mid-October (Oct 10-24, earlier years)", midoct(ser.index.to_series())),
                        ("summer (Jun-Aug, all years)", summer(ser.index.to_series()))]:
        c = ser[mask.values]
        if c.empty: continue
        r = int((c > v).sum() + 1) if high else int((c < v).sum() + 1)
        pct = (c < v).mean() * 100 if high else (c > v).mean() * 100
        yrs = c.index.str[:4]
        ranks.append(dict(station=station, metric=name, oct17_value=v, unit=unit, comparison=label, n_days=len(c),
                          years=f"{yrs.min()}-{yrs.max()}", n_years=yrs.nunique(), rank_of_oct17=r,
                          pct_days_less_extreme=round(pct, 1), max_in_set=c.max() if high else c.min(),
                          date_of_max=c.idxmax() if high else c.idxmin(), median_in_set=c.median()))
# ---- hourly Wainwright and neighbours
hourly = {}
for f in glob.glob(f"{O}/raw/eccc/hourly/*.csv.gz"):
    d = pd.read_csv(f, low_memory=False, dtype={"CLIMATE_IDENTIFIER": str}); hourly[d.CLIMATE_IDENTIFIER.iloc[0]] = d
hrows = []
for cid, d in hourly.items():
    s = d[(d.LOCAL_DATE >= "2026-10-17 06") & (d.LOCAL_DATE <= "2026-10-18 00")]
    for _, r in s.iterrows():
        hrows.append(dict(station=r.STATION_NAME, climate_id=cid, local_standard_time=r.LOCAL_DATE, utc=r.UTC_DATE,
                          temp_c=r.TEMP, rh_pct=r.RELATIVE_HUMIDITY, wind_dir_10deg=r.WIND_DIRECTION, wind_kmh=r.WIND_SPEED,
                          precip_mm=r.PRECIP_AMOUNT))
pd.DataFrame(hrows).to_csv(f"{O}/weather_oct17_hourly.csv", index=False)
w = hourly["301S001"].copy(); w["date"] = w.LOCAL_DATE.str[:10]; w["hr"] = w.LOCAL_HOUR
aft = w[(w.hr >= 10) & (w.hr <= 17)]
def agg(col, fn):
    g = aft.groupby("date")[col]; n = g.count(); v = g.agg(fn); return v[n >= 6]
rank("afternoon max hourly wind speed (2-min mean at the hour)", "WAINWRIGHT CFB AIRFIELD 21", agg("WIND_SPEED", "max"), True, "km/h")
rank("afternoon min relative humidity", "WAINWRIGHT CFB AIRFIELD 21", agg("RELATIVE_HUMIDITY", "min"), False, "%")
rank("afternoon max hourly temperature", "WAINWRIGHT CFB AIRFIELD 21", agg("TEMP", "max"), True, "C")
# hour-to-hour change (front passage)
w = w.sort_values("UTC_DATE"); w["dT"] = w.TEMP.diff(); w["dWS"] = w.WIND_SPEED.diff()
ok = w.UTC_DATE.str[:13].pipe(pd.to_datetime).diff() == pd.Timedelta("1h")
w.loc[~ok, ["dT", "dWS"]] = np.nan
rank("largest one-hour temperature drop (afternoon)", "WAINWRIGHT CFB AIRFIELD 21",
     -w[(w.hr >= 10) & (w.hr <= 18)].groupby("date").dT.min(), True, "C (drop)")
# ---- daily stations
daily = {}
for f in glob.glob(f"{O}/raw/eccc/daily/*.csv.gz"):
    d = pd.read_csv(f, low_memory=False, dtype={"CLIMATE_IDENTIFIER": str}); d["date"] = d.LOCAL_DATE.str[:10]; daily[d.CLIMATE_IDENTIFIER.iloc[0]] = d.set_index("date")
for cid in ["301S001", "3013959", "3011887", "3016GF0", "3015401"]:
    d = daily[cid]; nm = d.STATION_NAME.iloc[0]
    # ECCC reports max gust only when >= 31 km/h; days with a max temperature but no gust are set to 30 (below threshold)
    g = d.SPEED_MAX_GUST.copy(); g[g.isna() & d.MAX_TEMPERATURE.notna() & (d.index >= d[d.SPEED_MAX_GUST.notna()].index.min())] = 30
    rank("daily max wind gust", nm, g, True, "km/h")
    rank("daily max temperature", nm, d.MAX_TEMPERATURE, True, "C")
    rank("daily min relative humidity", nm, d.MIN_REL_HUMIDITY, False, "%")
# ---- CWFIS station FWI
c = pd.read_csv(f"{O}/work/cwfis_fwi_near.csv", dtype={"aes": str})
for aes in ["301S001", "3013362", "3012192"]:
    s = c[c.aes == aes].set_index("date"); nm = s.name.iloc[0].replace("+", " ")
    for col in ["ffmc", "isi", "fwi", "bui", "dc"]:
        rank(f"CWFIS station {col.upper()} (noon LST obs)", nm, pd.to_numeric(s[col], errors="coerce"), True, "")
# ---- illustrative afternoon ISI / FWI at Wainwright with the 15:00 LST wind (estimate)
s = c[(c.aes == "301S001") & (c.date == F)].iloc[0]
ff, bu = float(s.ffmc), float(s.bui)
illus = []
for hr in [12, 13, 14, 15, 16]:
    hw = hourly["301S001"]; ws = float(hw[hw.LOCAL_DATE == f"{F} {hr:02d}:00:00"].WIND_SPEED.iloc[0])
    i = float(ISI(ff, ws)); illus.append(dict(hour_lst=hr, wind_kmh=ws, ffmc_noon=ff, isi_est=round(i, 1), fwi_est=round(float(FWI(i, bu)), 1)))
pd.DataFrame(illus).to_csv(f"{O}/work/isi_afternoon_illustrative.csv", index=False)
# ---- FWI grid at the fire point
t = Transformer.from_crs(4326, 3978, always_xy=True); x, y = t.transform(-110.934717, 52.772633)
vals = {}
for f in sorted(glob.glob(f"{G}/fwi_*.tif")):
    dt = f[-12:-4]; dt = f"{dt[:4]}-{dt[4:6]}-{dt[6:]}"
    with rasterio.open(f) as r:
        v = next(r.sample([(x, y)]))[0]; vals[dt] = np.nan if v == r.nodata else float(v)
gs = pd.Series(vals); gs.to_csv(f"{O}/work/fwi_grid_at_fire.csv", header=["fwi"])
rank("CWFIS interpolated FWI grid (2 km) at fire point", "grid", gs, True, "")
R = pd.DataFrame(ranks); R.to_csv(f"{O}/weather_oct17_ranks.csv", index=False)
print(R.to_string()); print(pd.DataFrame(illus))
# ---- days since rain, freeze, snow
rows = []
for cid in ["301S001", "3012515", "3013959", "3011887", "3014600"]:
    d = daily[cid]; nm = d.STATION_NAME.iloc[0]; p = d.TOTAL_PRECIPITATION.loc[:"2026-10-16"]
    out = dict(station=nm, climate_id=cid)
    for th in [0.2, 1, 5, 10]:
        last = p[p >= th].index.max(); out[f"last_day_ge_{th}mm"] = last
        out[f"days_since_ge_{th}mm"] = (pd.Timestamp(F) - pd.Timestamp(last)).days
    win = p.loc["2026-08-01":"2026-10-16"]; out["missing_precip_days_aug1_oct16"] = int(win.isna().sum()) + (77 - len(win))
    mn = d.MIN_TEMPERATURE.loc["2026-08-15":"2026-10-17"]
    for th in [0, -2, -5]:
        out[f"first_fall_min_le_{th}C_2026"] = mn[mn <= th].index.min()
    sn = d.loc["2026-09-01":"2026-10-17"]
    out["snow_cm_sep1_oct17"] = sn.TOTAL_SNOW.sum(min_count=1); out["max_snow_on_ground_sep1_oct17"] = sn.SNOW_ON_GROUND.max()
    # median first fall frost dates earlier years (years with >= 90% min-temp coverage Aug15-Nov30)
    ff = {}
    for yr in range(1966, 2026):
        m = d.MIN_TEMPERATURE.loc[f"{yr}-08-15":f"{yr}-11-30"]
        if m.notna().sum() < 0.9 * 108: continue
        for th in [0, -2, -5]:
            hit = m[m <= th].index.min()
            ff.setdefault(th, []).append(pd.Timestamp(hit).dayofyear if isinstance(hit, str) else np.nan)
    for th, lst in ff.items():
        a = np.array(lst, float); out[f"median_first_le_{th}C_doy_earlier_years"] = np.nanmedian(a); out[f"n_years_{th}"] = len(a)
    rows.append(out)
pd.DataFrame(rows).to_csv(f"{O}/weather_rain_freeze.csv", index=False); print(pd.DataFrame(rows).T)
# ---- precipitation Jun 1 - Oct 16 vs station's own 1991-2020 (or available) baseline
prow = []
for cid in ["3012515", "3013961", "3014600", "301S001", "3011887"]:
    d = daily[cid]; nm = d.STATION_NAME.iloc[0]
    tot = {}
    for yr in range(1966, 2027):
        win = d.TOTAL_PRECIPITATION.loc[f"{yr}-06-01":f"{yr}-10-16"]
        if win.notna().sum() >= 0.95 * 138: tot[yr] = win.sum()
    s = pd.Series(tot)
    if 2026 not in s.index:
        prow.append(dict(station=nm, climate_id=cid, note="2026 window incomplete (<95% of days)",
                         days_2026=int(d.TOTAL_PRECIPITATION.loc["2026-06-01":"2026-10-16"].notna().sum()))); continue
    base = s[(s.index >= 1991) & (s.index <= 2020)]
    prow.append(dict(station=nm, climate_id=cid, precip_2026_jun1_oct16_mm=round(s[2026], 1),
                     baseline_years=f"{base.index.min()}-{base.index.max()}", n_baseline_years=len(base),
                     baseline_mean_mm=round(base.mean(), 1), pct_of_baseline=round(100 * s[2026] / base.mean()),
                     rank_driest_of_all_years=int((s < s[2026]).sum() + 1), n_all_years=len(s),
                     all_years=f"{s.index.min()}-{s.index.max()}"))
    for mo, (a, b) in {"jun": ("06-01", "06-30"), "jul": ("07-01", "07-31"), "aug": ("08-01", "08-31"), "sep": ("09-01", "09-30"), "oct1_16": ("10-01", "10-16")}.items():
        prow[-1][f"{mo}_2026_mm"] = d.TOTAL_PRECIPITATION.loc[f"2026-{a}":f"2026-{b}"].sum()
        mb = [d.TOTAL_PRECIPITATION.loc[f"{y}-{a}":f"{y}-{b}"].sum() for y in base.index]
        prow[-1][f"{mo}_baseline_mm"] = round(float(np.mean(mb)), 1)
P = pd.DataFrame(prow); P.to_csv(f"{O}/weather_precip_jun_oct.csv", index=False); print(P.T)
