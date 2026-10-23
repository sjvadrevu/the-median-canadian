"""One row per province: the headline measure from each of 03b, 04, 05, 06, 07. Output: province_summary.csv"""
import pandas as pd

from common import OUT

z = pd.read_csv(OUT / "zone_share_province_2023_2026.csv").set_index("prov")
e = pd.read_csv(OUT / "escape_speed_2026_summary.csv").set_index("prov")
lag = pd.read_csv(OUT / "detection_lag_summary.csv")
lag = lag[(lag.source == "all") & (lag.year == "2023-2026")].set_index("prov")
a = pd.read_csv(OUT / "access_by_prov_year.csv")
a = a[(a.year == "2023-2026") & (a.distance == "road_km")].set_index("prov")
t = pd.read_csv(OUT / "early_control_trends.csv")
t = t[(t.scope == "all fires") & (t["var"] == "lt10ha")].set_index("prov")
P = pd.DataFrame({
    "official_ha_2023_2026": a.official_ha,
    "not_suppression_share": z.not_suppression_share,
    "unclassified_share": z.unclassified_share,
    "share_area_origin_gt_25km_road": a.share_area_gt_25km,
    "share_area_origin_gt_50km_road": a.share_area_gt_50km,
    "share_area_agency_date_3d_after_first_hotspot": lag.area_agency_3d_or_more_after,
    "m3_2026_share_area_fires_1000ha_within_72h_main_run": e.main_run_share_area_fires_1000ha_within_72h,
    "m3_2026_share_area_fires_1000ha_within_72h_first_detection": e.share_area_fires_1000ha_within_72h,
    "fires_lt10ha_1990s": t.mean_1990s, "fires_lt10ha_2016_2025": t.mean_2016_2025,
    "fires_lt10ha_trend_per_decade": t.slope_per_decade, "fires_lt10ha_trend_p": t.p,
})
P = P.sort_values("official_ha_2023_2026", ascending=False)
P.to_csv(OUT / "province_summary.csv", float_format="%.4f")
print(P.round(3).to_string())
