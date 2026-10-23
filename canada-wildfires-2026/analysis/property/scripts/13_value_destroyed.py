"""Replacement-value proxy of DESTROYED dwellings = official count x local 2021 Census average (and median) value of
owner-occupied dwellings. 'Local' = mean DA value over the Microsoft footprints our calibrated rule flags as likely
destroyed in that event (footprints inside the fire if none are flagged); for Jasper the official 'Destroyed'
townsite polygons are valued one by one at their own DA. DA values with fallback to CD, then province
(work/da_values_2021.csv from 12_value_exposed.py). Not insured loss, not market loss: a 2021 owner-occupied average
applied to structures, many of which are not owner-occupied homes. -> destroyed_value_official.csv"""
import os
import numpy as np, pandas as pd, geopandas as gpd
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.dirname(os.path.dirname(P))
G = os.path.join(W, "data", "geo", "statcan")
dv = pd.read_csv(os.path.join(P, "work", "da_values_2021.csv"), dtype={"DAUID": str, "CDUID": str, "PRUID": str})
da = gpd.read_file(os.path.join(G, "da_2021_pop_gen50m.gpkg"), columns=["DAUID"]).merge(dv, on="DAUID")
def values_at(lon, lat):
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs=4326).to_crs(da.crs)
    j = gpd.sjoin_nearest(pts, da[["DAUID", "avg_value", "median_value", "avg_value_src", "geometry"]], max_distance=2000)
    return j[~j.index.duplicated()]
# event: (apply file, official count, what is counted, publisher)
EV = [("jasper2024", None, None, "townsite buildings destroyed (Municipality of Jasper layer, Value_Type 'Jasper')", "Municipality of Jasper"),
      ("tantallon2023", 151, "homes", "homes lost (of ~200 structures)", "HRFE / HRM"),
      ("barrington2023", 230, "structures", "structures destroyed (+59 damaged)", "HRFE citing Barrington AAR"),
      ("mcdougall2023", 200, "structures", "structures impacted (destroyed or damaged, approx.)", "CORE / RDCO"),
      ("bushcreek2023", 185, "structures", "structures lost: CSRD 176 + TNRD 9 (approx.)", "CSRD, TNRD"),
      ("denare2025", 400, "homes", "permanent residences destroyed in the SHOE fire region (approx.)", "Gov. of Saskatchewan / SPSA"),
      ("baldrange2026", 150, "structures", "structures damaged or destroyed (approx., preliminary)", "District of Summerland")]
rows = []
for ev, n, kind, what, pub in EV:
    if ev == "jasper2024":
        j = gpd.read_file(os.path.join(P, "raw", "jasper", "jasper_damage_assessment_structures.geojson"))
        j = j[(j.Status.fillna("").str.strip() == "Destroyed") & (j.Value_Type.fillna("").str.strip() == "Jasper")]
        c = j.to_crs(3978).centroid.to_crs(4326); v = values_at(c.x.values, c.y.values); n = len(j); basis = "each destroyed polygon at its own DA"
        rows.append(dict(event=ev, official_count=n, counted=kind or "buildings", what=what, publisher=pub, value_basis=basis, n_da=v.DAUID.nunique(),
                         local_avg_value=v.avg_value.mean(), local_median_value=v.median_value.mean(), value_src=";".join(sorted(v.avg_value_src.dropna().unique())),
                         proxy_value_avg_cad=v.avg_value.sum(), proxy_value_median_cad=v.median_value.sum()))
        continue
    f = os.path.join(P, "work", f"apply_{ev}.csv")
    if not os.path.exists(f): print("missing", ev); continue
    a = pd.read_csv(f)
    s = a[a.likely_destroyed]; basis = "mean DA value over flagged footprints"
    if s.empty: s = a[a.dist_fire_m <= 0]; basis = "mean DA value over footprints inside the fire"
    v = values_at(s.lon.values, s.lat.values)
    rows.append(dict(event=ev, official_count=n, counted=kind, what=what, publisher=pub, value_basis=basis, n_da=v.DAUID.nunique(),
                     local_avg_value=v.avg_value.mean(), local_median_value=v.median_value.mean(), value_src=";".join(sorted(v.avg_value_src.dropna().unique())),
                     proxy_value_avg_cad=n * v.avg_value.mean(), proxy_value_median_cad=n * v.median_value.mean()))
o = pd.DataFrame(rows).round(0)
o.to_csv(os.path.join(P, "destroyed_value_official.csv"), index=False)
print(o.drop(columns=["what", "publisher"]).to_string())
# Our satellite ESTIMATE (not official): footprints flagged likely destroyed within 500 m of the fire polygon, each valued
# at its own DA. Check events from work/apply_<event>.csv; 2026 per CWFIS outline from work/apply_2026.csv.
# -> destroyed_value_estimates.csv
er = []
def est_row(ev, year, s):
    v = values_at(s.lon.values, s.lat.values) if len(s) else pd.DataFrame(columns=["avg_value", "median_value", "avg_value_src"])
    return dict(event=ev, year=year, flagged_500m=len(s), valued=len(v), proxy_value_avg_cad=v.avg_value.sum(), proxy_value_median_cad=v.median_value.sum(),
                share_value_from_DA=round((v.avg_value_src == "DA").mean(), 3) if len(v) else None)
for ev in ["jasper2024", "tantallon2023", "barrington2023", "mcdougall2023", "bushcreek2023", "enterprise2023", "denare2025", "lacdubonnet2025", "bradleycreek2026", "baldrange2026"]:
    f = os.path.join(P, "work", f"apply_{ev}.csv")
    if not os.path.exists(f): print("missing", ev); continue
    a = pd.read_csv(f); er.append(est_row(ev, int(ev[-4:]), a[a.likely_destroyed & (a.dist_fire_m.fillna(1e9) <= 500)]))
a26 = pd.read_csv(os.path.join(P, "work", "apply_2026.csv"))
# Quality screen for the 2026 outlines (the same screen the second cost round applies to its new satellite counts,
# costs-full/scripts/econ2_sat_04_apply.py): (1) a cluster with a dNBR scene offset beyond +-100 has an unstable pre/post
# match; (2) a fire whose 500-1000 m band has more than 26% as many flags as its 0-500 m band fails the false-positive
# check; (3) fires under 10 ha cannot supply the burn context. The check events above all pass (offsets within 100,
# band ratios 0 to 0.03). The flags that fail are listed in work/screen_fail_2026.csv.
outl26 = gpd.read_file(os.path.join(W, "analysis", "outline-check", "outline_class_2026.geojson"))[["fire_uid", "area_ha"]]
a26["offset_ok"] = a26.dnbr_offset.abs() <= 100
ok26 = a26[a26.offset_ok & a26.likely_destroyed]
qa26 = pd.DataFrame({"f500": ok26[ok26.dist <= 500].groupby("aoi").size(),
                     "f1000": ok26[(ok26.dist > 500) & (ok26.dist <= 1000)].groupby("aoi").size()}).fillna(0)
a26["fp_ok"] = a26.aoi.map(qa26.f1000 <= 0.26 * qa26.f500).fillna(True).astype(bool)
a26["area_ok"] = a26.aoi.map(outl26.set_index("fire_uid").area_ha).fillna(0) >= 10
a26["qa_pass"] = a26.offset_ok & a26.fp_ok & a26.area_ok
s26_all = a26[a26.likely_destroyed & (a26.dist <= 500)]
s26_all[~s26_all.qa_pass][["aoi", "x", "y", "lon", "lat", "dnbr_offset", "offset_ok", "fp_ok", "area_ok"]].to_csv(
    os.path.join(P, "work", "screen_fail_2026.csv"), index=False)
s26 = s26_all[s26_all.qa_pass]
print("2026 flags within 500 m:", len(s26_all), "passing the quality screen:", len(s26))
for fid, g in s26.groupby("aoi"): er.append(est_row(f"2026 outline {fid}", 2026, g))
er.append(est_row("2026 all outlines", 2026, s26))
e = pd.DataFrame(er).round({"proxy_value_avg_cad": 0, "proxy_value_median_cad": 0}); e.to_csv(os.path.join(P, "destroyed_value_estimates.csv"), index=False)
print(e.to_string())
