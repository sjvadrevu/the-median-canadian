"""Thread 6b: BC community watersheds and surface-water intakes (second half of t6, run separately for memory).
Reads t6_workunit_burned_share.csv for the work-unit fallback."""
import numpy as np, pandas as pd, geopandas as gpd
from shapely import make_valid
BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
T = f"{BASE}/analysis/threads"
PW = f"{BASE}/analysis/people/work"
YEARS = [2023, 2024, 2025, 2026]
res = pd.read_csv(f"{T}/t6_workunit_burned_share.csv")
wu = gpd.read_file(f"{T}/raw/nhn/NHN_INDEX_22_INDEX_WORKUNIT_LIMIT_2.shp", where="PROVCD_1 = 'BC' OR PROVCD_2 = 'BC' OR PROVCD_3 = 'BC' OR PROVCD_4 = 'BC'")
wu["uid"] = None
allwu = gpd.read_file(f"{T}/raw/nhn/NHN_INDEX_22_INDEX_WORKUNIT_LIMIT_2.shp", columns=["DATASETNAM"], ignore_geometry=True)
uidmap = dict(zip(allwu.DATASETNAM, range(1, len(allwu) + 1)))
wu["uid"] = wu.DATASETNAM.map(uidmap)
wu = wu.to_crs("EPSG:3979"); wu["geometry"] = wu.geometry.simplify(120)
# ---- BC community watersheds (exact vector overlay)
cw = gpd.read_file(f"{T}/raw/bc_water/WLS_COMMUNITY_WS_PUB_SVW.geojson").to_crs("ESRI:102001")
cw["geometry"] = cw.geometry.map(lambda g: make_valid(g) if not g.is_valid else g)
cw["area_ha"] = cw.area / 1e4
bbox = cw.total_bounds
burned_geoms = {}
cw_all = cw.union_all()
for y in YEARS:
    f = gpd.read_file(f"{PW}/fires_{y}.gpkg", bbox=tuple(bbox))
    f["geometry"] = f.geometry.map(lambda g: make_valid(g) if not g.is_valid else g)
    f = f[f.intersects(cw_all)]
    burned_geoms[y] = f.union_all()
    del f
    inter = cw.geometry.intersection(burned_geoms[y])
    cw[f"burned_ha_{y}"] = inter.area / 1e4
uni = burned_geoms[2023].union(burned_geoms[2024]).union(burned_geoms[2025]).union(burned_geoms[2026])
cw["burned_ha_union"] = cw.geometry.intersection(uni).area / 1e4
cw["share_2023_2026"] = cw.burned_ha_union / cw.area_ha
keep = ["CW_CODE", "CW_NAME", "CW_SOURCE_NAME", "POD_NUMBER", "ORGANIZATION", "ORGANIZATION_TYPE", "WATER_SYSTEM_NAME", "CW_USE",
        "SOURCE_CATEGORY", "WATER_TREATMENT_TYPE", "CONNECTIONS_COUNT", "HEALTH_AUTHORITY", "area_ha"] + \
       [f"burned_ha_{y}" for y in YEARS] + ["burned_ha_union", "share_2023_2026"]
keep = [k for k in keep if k in cw.columns]
cw[keep].sort_values("share_2023_2026", ascending=False).to_csv(f"{T}/t6_bc_community_watersheds_burned.csv", index=False)
bc = []
for thr in (0.0, 0.05, 0.10, 0.20, 0.50):
    s = cw[cw.share_2023_2026 > thr]
    bc.append(dict(threshold=thr, community_watersheds=len(s), of_total=len(cw), water_systems=s.WATER_SYSTEM_NAME.nunique(),
                   connections=pd.to_numeric(s.get("CONNECTIONS_COUNT"), errors="coerce").sum()))
B = pd.DataFrame(bc); B.to_csv(f"{T}/t6_bc_community_watersheds_summary.csv", index=False)
print(B.to_string())
print(cw.sort_values("share_2023_2026", ascending=False).head(25)[["CW_NAME", "WATER_SYSTEM_NAME", "area_ha", "share_2023_2026", "WATER_TREATMENT_TYPE"]].to_string())

# ---- BC surface-water intakes
sp = gpd.read_file(f"{T}/raw/bc_water/DWS_SOURCE_POINT.geojson").to_crs("ESRI:102001")
print(sp.SOURCE_TYPE.value_counts())
sw = sp[sp.SOURCE_TYPE.str.contains("Surface", case=False, na=False)].copy()
sj = gpd.sjoin(sw, cw[["CW_CODE", "share_2023_2026", "geometry"]].rename(columns={"share_2023_2026": "cw_share"}), how="left", predicate="within").drop_duplicates("OBJECTID")
sj2 = gpd.sjoin(sj.drop(columns="index_right").to_crs("EPSG:3979"), wu[["uid", "geometry"]], how="left", predicate="within").drop_duplicates("OBJECTID")
sj2 = sj2.merge(res[["uid", "DATASETNAM", "share_2023_2026"]].rename(columns={"share_2023_2026": "wu_share"}), on="uid", how="left")
sj2["share_used"] = sj2.cw_share.fillna(sj2.wu_share)
sj2["share_basis"] = np.where(sj2.cw_share.notna(), "community watershed", "NHN work unit")
sj2.drop(columns="geometry").to_csv(f"{T}/t6_bc_surface_intakes.csv", index=False)
I = []
for thr in (0.05, 0.10, 0.20):
    s = sj2[sj2.share_used > thr]
    I.append(dict(threshold=thr, intakes=len(s), of_total=len(sj2), systems=s.SYSTEM_NAME.nunique(),
                  pop_served_reported=pd.to_numeric(s.POPULATION_SERVED, errors="coerce").sum(),
                  via_community_watershed=int((s.share_basis == "community watershed").sum())))
I = pd.DataFrame(I); I.to_csv(f"{T}/t6_bc_surface_intakes_summary.csv", index=False)
print(I.to_string())
print(sj2[sj2.share_used > 0.10].sort_values("share_used", ascending=False).head(30)[["SYSTEM_NAME", "INTAKE_WELLHEAD_NAME", "POPULATION_SERVED", "share_basis", "share_used"]].to_string())
