"""Station extreme fire weather days per area and year, 1991-2026 (from analysis/weather work files).

Stations: the consistent sites of analysis/weather (strict rule: 28 of 30 qualifying years 1991-2020; relaxed
rule 24 of 30 kept as a sensitivity), re-assigned to areas of the current area file by location.
Per site-year that qualifies (coverage rule of analysis/weather): extreme days (FWI >= 30) and high-or-above days
(FWI >= 19), April 1 to October 19. Anomaly = days minus the site's 1991-2020 mean over qualifying years.
Area-year value = median anomaly over qualifying stations in the area (and mean, pooled ratio, n).
Output: weather_by_area_year.csv (strict and relaxed), weather_coverage.csv
"""
import numpy as np
import pandas as pd

from common import OUT, WEATHER_DIR, area_attrs, area_dir, assign_area, log

D = area_dir()
fh = open(D / "log_08.txt", "w")
S = pd.read_csv(WEATHER_DIR / "station_extreme_days.csv", dtype={"site_id": str})
SY = pd.read_pickle(WEATHER_DIR / "work" / "site_year.pkl")
S["fma_id_new"] = assign_area(S.lon.values, S.lat.values)
log(f"stations {len(S)}; area changed vs analysis/weather assignment: {(S.fma_id_new != S.fma_id).sum()}", fh)
out = []
for rule, keep in [("strict", S.rule == "strict_28of30"), ("relaxed", S.rule.notna())]:
    s = S[keep & (S.fma_id_new > 0)][["site_id", "fma_id_new"]]
    y = SY[SY.site.isin(s.site_id) & SY.qualifies & (SY.year >= 1991)].merge(s, left_on="site", right_on="site_id")
    base = y[(y.year >= 1991) & (y.year <= 2020)].groupby("site")[["extreme_days", "high_plus_days"]].mean()
    y = y.join(base, on="site", rsuffix="_norm")
    y["ext_anom"] = y.extreme_days - y.extreme_days_norm
    y["hi_anom"] = y.high_plus_days - y.high_plus_days_norm
    a = y.groupby(["fma_id_new", "year"]).agg(n_stations=("site", "nunique"), ext_days_mean=("extreme_days", "mean"),
                                              ext_anom_median=("ext_anom", "median"), ext_anom_mean=("ext_anom", "mean"),
                                              ext_sum=("extreme_days", "sum"), ext_norm_sum=("extreme_days_norm", "sum"),
                                              hi_anom_median=("hi_anom", "median")).reset_index()
    a["ext_pooled_ratio"] = a.ext_sum / a.ext_norm_sum.replace(0, np.nan)
    a = a.rename(columns={"fma_id_new": "fma_id"}).drop(columns=["ext_sum", "ext_norm_sum"])
    a["rule"] = rule
    out.append(a)
Wp = pd.concat(out, ignore_index=True)
Wp.to_csv(OUT / "weather_by_area_year.csv", index=False)
A = area_attrs()
cov = Wp.groupby(["rule", "year"]).fma_id.nunique().unstack("rule")
cov.to_csv(OUT / "weather_coverage.csv")
log(f"areas with >=1 qualifying station (strict) per year: min {cov.strict.min()}, max {cov.strict.max()}, 2026 {cov.strict.get(2026)}", fh)
log(f"areas with >=1 qualifying station (relaxed) per year: min {cov.relaxed.min()}, max {cov.relaxed.max()}, 2026 {cov.relaxed.get(2026)}", fh)
