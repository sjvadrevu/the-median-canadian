"""Step 3: smoke days per city and year, 2018-2026.

Input: data/smoke-cost/city_daily_pm25_2018_2026.csv (city-day 24 h mean PM2.5, mean of
reporting stations; NAPS validated preferred, else AirNow real-time; data_status per day).

Rules
- A city-day counts only if a 24 h mean exists for it (NAPS days need >= 18 valid hours,
  AirNow days are AirNow's own PM2.5-24hr value). No infilling.
- Thresholds use the CITY MEAN of stations, strictly greater than 27, 60 and 100 ug/m3.
  27 ug/m3 is the 2020 CAAQS 24 h PM2.5 value; the standard itself is a 3-year average of
  the annual 98th percentile, so a day above 27 is not a formal exceedance of the standard.
- Coverage: a city-year is ADEQUATE when >= 115 of the 153 days May 1 - Sep 30 (75%) have a
  value. Rankings use adequate years only. 2026 data end 2026-10-19.
- Counts are reported for the whole year (to Oct 19 for 2026) and for May-Sep only.
- status: share of counted days that are validated / realtime / mixed.
No attribution of smoke to specific fires (no smoke model).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

d = pd.read_csv(f"{DATA}/smoke-cost/city_daily_pm25_2018_2026.csv")
d["date"] = pd.to_datetime(d["date"])
d = d[d.pm25_mean_of_stations.notna()]
d["year"] = d.date.dt.year
d["mmdd"] = d.date.dt.strftime("%m-%d")
d["mjjas"] = d.date.dt.month.between(5, 9)
d["to_oct19"] = d["mmdd"] <= "10-19"
v = d.pm25_mean_of_stations
for t in (27, 60, 100):
    d[f"gt{t}"] = v > t
smap = pd.read_csv(f"{DATA}/smoke-cost/city_station_map.csv")

rows = []
for (c, y), g in d.groupby(["city", "year"]):
    s = g[g.mjjas]
    w = g.loc[g.pm25_mean_of_stations.idxmax()]
    st = g.data_status.value_counts(normalize=True)
    r = dict(city=c, group=g.group.iloc[0], year=y,
             days_with_data=len(g), days_with_data_may_sep=len(s),
             coverage_may_sep_pct=round(100 * len(s) / 153, 1),
             adequate=len(s) >= 115,
             days_gt27=int(g.gt27.sum()), days_gt60=int(g.gt60.sum()), days_gt100=int(g.gt100.sum()),
             days_gt27_may_sep=int(s.gt27.sum()), days_gt60_may_sep=int(s.gt60.sum()),
             days_gt100_may_sep=int(s.gt100.sum()),
             days_gt27_jan1_oct19=int(g[g.to_oct19].gt27.sum()),
             worst_day=w.date.strftime("%Y-%m-%d"), worst_day_pm25=round(w.pm25_mean_of_stations, 1),
             worst_day_max_station_pm25=round(w.pm25_max_station, 1),
             worst_day_status=w.data_status,
             pct_validated=round(100 * st.get("validated", 0), 1),
             pct_realtime=round(100 * st.get("realtime", 0), 1),
             pct_mixed=round(100 * st.get("mixed", 0), 1),
             median_stations=float(g.n_stations.median()))
    r["data_basis"] = ("validated" if r["pct_validated"] >= 95 else
                       "real-time" if r["pct_realtime"] >= 95 else "mixed")
    r["period"] = "Jan 1 - Oct 19" if y == 2026 else "calendar year"
    rows.append(r)
cy = pd.DataFrame(rows)

# Rank 2026 among adequate years 2018-2026 (1 = most smoke days). Uses Jan 1-Oct 19 counts
# for every year so 2026 is compared like for like.
rk = []
for c, g in cy.groupby("city"):
    a = g[g.adequate]
    out = dict(city=c, n_adequate_years=len(a),
               adequate_years=";".join(map(str, sorted(a.year))))
    if 2026 in set(a.year):
        for col, nm in [("days_gt27_jan1_oct19", "rank2026_days_gt27"),
                        ("days_gt27_may_sep", "rank2026_days_gt27_may_sep"),
                        ("worst_day_pm25", "rank2026_worst_day")]:
            rr = a[col].rank(ascending=False, method="min")
            out[nm] = int(rr[a.year == 2026].iloc[0])
            v26 = a.loc[a.year == 2026, col].iloc[0]
            out[nm.replace("rank2026", "years_tied2026")] = int((a[col] == v26).sum() - 1)
        top = a.sort_values("days_gt27_jan1_oct19", ascending=False).iloc[0]
        out["most_smoke_days_year"] = int(top.year)
        out["most_smoke_days_jan1_oct19"] = int(top.days_gt27_jan1_oct19)
    rk.append(out)
rk = pd.DataFrame(rk)
cy = cy.merge(rk, on="city", how="left")
cy = cy.merge(smap[["city", "pop_rank_2021", "population_2021", "pc_code"]], on="city", how="left")
cy.to_csv(f"{OUT}/city_smoke_days.csv", index=False)

# Days above 27 after Oct 19 in 2018-2025 (to size what 2026's partial year can still add)
late = d[(~d.to_oct19) & d.gt27 & (d.year < 2026)].groupby("year").size()
print("city-days >27 after Oct 19, by year:", late.to_dict())

# 2026 daily file for a smoke calendar
d26 = d[d.year == 2026].copy()
d26["band"] = pd.cut(d26.pm25_mean_of_stations, [-np.inf, 27, 60, 100, np.inf],
                     labels=["0-27", "27-60", "60-100", "100+"], right=True)
d26 = d26.rename(columns={"pm25_mean_of_stations": "pm25_city_mean", "pm25_max_station": "pm25_max_station"})
d26["date"] = d26.date.dt.strftime("%Y-%m-%d")
d26[["city", "group", "date", "pm25_city_mean", "pm25_max_station", "n_stations",
     "data_status", "band"]].round(2).to_csv(f"{OUT}/city_smoke_daily_2026.csv", index=False)

# console summary
c26 = cy[cy.year == 2026].sort_values("days_gt27", ascending=False)
print(c26[["city", "days_with_data", "adequate", "days_gt27", "days_gt60", "days_gt100", "worst_day",
           "worst_day_pm25", "rank2026_days_gt27", "n_adequate_years", "most_smoke_days_year"]].to_string())
print("cities with 2026 data:", c26.city.nunique(), "adequate:", int(c26.adequate.sum()))
print("2026 not adequate / missing:", sorted(set(smap.city) - set(c26[c26.adequate].city)))
