"""Step 9: lowest minimum temperature Aug 15 - Oct 17 each year (years with >= 90% of days) and whether
<= 0 C / <= -2 C / <= -5 C had occurred by Oct 17; 2026 ranked against earlier years (rank 1 = mildest).
Output: weather_freeze_by_oct17.csv"""
import pandas as pd
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
rows = []
for cid in ["301S001", "3012515", "3011887", "3013961"]:
    d = pd.read_csv(f"{O}/raw/eccc/daily/{cid}.csv.gz", low_memory=False, dtype={"CLIMATE_IDENTIFIER": str})
    d["date"] = d.LOCAL_DATE.str[:10]; d = d.set_index("date")
    yrs = []
    for y in range(1950, 2027):
        mm = d.MIN_TEMPERATURE.loc[f"{y}-08-15":f"{y}-10-17"]
        if mm.notna().sum() < 0.9 * 64: continue
        yrs.append(dict(year=y, lowest=mm.min(), n=mm.notna().sum(), le0=(mm <= 0).any(), le2=(mm <= -2).any(), le5=(mm <= -5).any()))
    y = pd.DataFrame(yrs); e = y[y.year < 2026]; t = y[y.year == 2026]
    r = dict(station=d.STATION_NAME.iloc[0], climate_id=cid, years=f"{e.year.min()}-{e.year.max()}", n_earlier_years=len(e))
    if len(t):
        v = float(t.lowest.iloc[0])
        r.update(lowest_min_2026=v, days_with_data_2026=int(t.n.iloc[0]), rank_mildest=int((e.lowest > v).sum() + 1),
                 median_lowest_earlier=e.lowest.median(), share_earlier_years_le0=round(e.le0.mean(), 3),
                 share_earlier_years_le_minus2=round(e.le2.mean(), 3), share_earlier_years_le_minus5=round(e.le5.mean(), 3))
    else:
        r.update(note="2026 window < 90% complete")
    rows.append(r)
R = pd.DataFrame(rows); R.to_csv(f"{O}/weather_freeze_by_oct17.csv", index=False); print(R.T)
