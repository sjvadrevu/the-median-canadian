"""Build output tables and the simplified range GeoJSON from work/ results.
Usage: python -I 06_tables.py <work_dir> <out_dir>"""
import sys, os, json
import numpy as np, pandas as pd, geopandas as gpd, shapely

WORK, OUT = sys.argv[1], sys.argv[2]
ov = pd.read_csv(os.path.join(WORK, "overlay_results.csv"), dtype={"tid": str})
fo = pd.read_csv(os.path.join(WORK, "forest_results.csv"), dtype={"tid": str})
pc = pd.read_csv(os.path.join(WORK, "provincial_perimeter_check.csv"))


def derive(d):
    d = d.copy()
    d["area_km2"] = d.A / 1e6
    d["burned_2026_mapped_km2"] = d.m / 1e6
    d["share_burned_2026_pct"] = 100 * d.m / d.A
    d["fire_share_1987_2025_pct"] = 100 * d.u / d.A
    d["fire_share_1987_2026_pct"] = 100 * (d.u + d.m - d.um) / d.A
    d["change_from_2026_pts"] = d.fire_share_1987_2026_pct - d.fire_share_1987_2025_pct
    d["pct_of_2026_burn_not_burned_since_1987"] = np.where(d.m > 0, 100 * (d.m - d.um) / d.m.where(d.m > 0, 1), np.nan)
    return d


def add_forest(d, sets):
    f = fo[fo.set.isin(sets)][["set", "tid", "forest_km2", "forest_burned_km2"]].rename(
        columns={"forest_km2": "forest_2020_km2", "forest_burned_km2": "forest_burned_2026_mapped_km2"})
    d = d.merge(f, on=["set", "tid"], how="left")
    d["forest_share_burned_2026_pct"] = 100 * d.forest_burned_2026_mapped_km2 / d.forest_2020_km2
    return d


R = 2
pct_cols = ["share_burned_2026_pct", "fire_share_1987_2025_pct", "fire_share_1987_2026_pct", "change_from_2026_pts",
            "pct_of_2026_burn_not_burned_since_1987", "forest_share_burned_2026_pct"]

# 1. ECCC ranges
e = add_forest(derive(ov[ov.set.isin(["eccc", "eccc_union"])]), ["eccc", "eccc_union"])
e["province"] = np.where(e.set == "eccc", e.tid.str[:2], "ALL")
e = e.merge(pc[["code", "share_2026_provincial_pct"]].rename(columns={"code": "tid", "share_2026_provincial_pct": "check_share_2026_provincial_perimeters_pct"}), on="tid", how="left")
e["fire_alone_over_35pct"] = e.fire_share_1987_2026_pct > 35
e["fire_alone_over_35pct_before_2026"] = e.fire_share_1987_2025_pct > 35
rk = e[e.set == "eccc"].share_burned_2026_pct.rank(ascending=False, method="min")
e.loc[e.set == "eccc", "rank_2026_share"] = rk
e = e.sort_values(["set", "share_burned_2026_pct"], ascending=[True, False])
cols = ["rank_2026_share", "tid", "name", "province", "area_km2", "share_burned_2026_pct", "burned_2026_mapped_km2",
        "fire_share_1987_2025_pct", "fire_share_1987_2026_pct", "change_from_2026_pts",
        "pct_of_2026_burn_not_burned_since_1987", "fire_alone_over_35pct", "fire_alone_over_35pct_before_2026",
        "forest_2020_km2", "forest_burned_2026_mapped_km2", "forest_share_burned_2026_pct",
        "check_share_2026_provincial_perimeters_pct"]
ecsv = e[cols].rename(columns={"tid": "code", "name": "herd_range"}).round(R)
ecsv.to_csv(os.path.join(OUT, "caribou_ranges_2026.csv"), index=False)

# GeoJSON for the site
g = gpd.read_file(os.path.join(WORK, "inputs.gpkg"), layer="eccc_ranges")[["CODE", "geometry"]]
g["geometry"] = shapely.make_valid(g.geometry.simplify(500, preserve_topology=True).values)
g = g.merge(ecsv[ecsv.code != "ALL"], left_on="CODE", right_on="code").drop(columns=["CODE"])
g = g.to_crs("EPSG:4326")
g["geometry"] = shapely.set_precision(shapely.make_valid(g.geometry.values), 1e-5)
gj = os.path.join(OUT, "caribou_ranges_2026.geojson")
if os.path.exists(gj):
    os.remove(gj)
g.to_file(gj, driver="GeoJSON", COORDINATE_PRECISION=5)
chk = gpd.read_file(gj)
print("geojson features", len(chk), "all valid:", bool(chk.is_valid.all()))

# 2. Provincial caribou layers
q = add_forest(derive(ov[ov.set.isin(["qc", "qc_union", "sk", "sk_union"])]), ["qc", "qc_union", "sk", "sk_union"])
q["layer"] = q.set.map({"qc": "Quebec forest-ecotype populations (2022)", "qc_union": "Quebec union",
                        "sk": "Saskatchewan caribou units", "sk_union": "Saskatchewan union"})
q["fire_alone_over_35pct"] = q.fire_share_1987_2026_pct > 35
q = q.sort_values(["set", "share_burned_2026_pct"], ascending=[True, False])
qcols = ["layer", "tid", "name", "area_km2", "share_burned_2026_pct", "burned_2026_mapped_km2", "fire_share_1987_2025_pct",
         "fire_share_1987_2026_pct", "change_from_2026_pts", "pct_of_2026_burn_not_burned_since_1987", "fire_alone_over_35pct",
         "forest_2020_km2", "forest_burned_2026_mapped_km2", "forest_share_burned_2026_pct"]
q[qcols].rename(columns={"tid": "id"}).round(R).to_csv(os.path.join(OUT, "caribou_provincial_layers_2026.csv"), index=False)

# 3. Protected areas
stats = pd.read_csv(os.path.join(WORK, "ProtectedConservedArea_Statistics_2025.csv"), nrows=15, encoding="latin-1")
abbr = {"Alberta": "AB", "British Columbia": "BC", "Manitoba": "MB", "New Brunswick": "NB", "Newfoundland and Labrador": "NL",
        "Northwest Territories": "NT", "Nova Scotia": "NS", "Nunavut": "NU", "Ontario": "ON", "Prince Edward Island": "PE",
        "Quebec": "QC", "Saskatchewan": "SK", "Yukon": "YT", "National Terrestrial": "CA"}
stats["tid"] = stats.Region.map(abbr)
p = add_forest(derive(ov[ov.set.isin(["pa_prov", "pa_nat"])]), ["pa_prov", "pa_nat"])
p = p.merge(stats[["tid", "Total (km2)"]].rename(columns={"Total (km2)": "official_pa_oecm_km2"}), on="tid", how="left")
p = p.sort_values("share_burned_2026_pct", ascending=False)
pcols = ["tid", "area_km2", "official_pa_oecm_km2", "share_burned_2026_pct", "burned_2026_mapped_km2",
         "forest_2020_km2", "forest_burned_2026_mapped_km2", "forest_share_burned_2026_pct"]
p[pcols].rename(columns={"tid": "province", "area_km2": "pa_oecm_union_km2"}).round(R).to_csv(
    os.path.join(OUT, "protected_by_province_2026.csv"), index=False)

n = add_forest(derive(ov[ov.set == "park"]), ["park"]).sort_values("share_burned_2026_pct", ascending=False)
n[["name", "tid", "area_km2", "share_burned_2026_pct", "burned_2026_mapped_km2", "forest_2020_km2",
   "forest_burned_2026_mapped_km2", "forest_share_burned_2026_pct"]].rename(columns={"tid": "clab_id"}).round(R).to_csv(
    os.path.join(OUT, "national_parks_2026.csv"), index=False)

cp = pd.read_csv(os.path.join(WORK, "cpcad_features_2026.csv"))
cp.to_csv(os.path.join(OUT, "protected_areas_2026.csv"), index=False)

# 5. Fire management areas
pd.read_csv(os.path.join(WORK, "fma_results.csv")).to_csv(os.path.join(OUT, "fma_2026.csv"), index=False)
print("tables written")
