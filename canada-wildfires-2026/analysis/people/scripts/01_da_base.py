"""Step 1: attributes of every 2021 dissemination area (DA) representative point: province,
fire management area (data/geo/fma_v2.gpkg since the 2026-10-21 rebuild: MB and QC sub-areas; no separate
Parks Canada layer, so national parks are part of the province's areas) and reserve membership (point inside an Aboriginal
Lands of Canada Indian Reserve polygon). Distances are computed in 02y_year_distances.py.

Outputs (work/): da_base.csv, reserves_albers.gpkg.
"""
import sys, os, time, gc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

t0 = time.time()
pts = gpd.read_file(f"{DATA}/geo/statcan/da_2021_pop_points.gpkg").to_crs(ALBERS)
pts = pts[["DAUID", "DGUID", "PRUID", "pop2021", "geometry"]].reset_index(drop=True)
pts["prov"] = pts["PRUID"].astype(str).map(PR_ABBR)
print("DA points", len(pts), "pop sum", pts.pop2021.sum(), "missing pop", pts.pop2021.isna().sum())

# Fire management areas: fma_v2 rows partition each province (no overlapping Parks Canada layer).
fma = gpd.read_file(f"{DATA}/geo/fma_v2.gpkg").to_crs(ALBERS)
ag = fma[["fma_id", "agency", "area_name", "province", "geometry"]]
j = gpd.sjoin(pts[["geometry"]], ag, how="left", predicate="within")
j = j[~j.index.duplicated()]
pts["fma_id"] = j["fma_id"]
pts["fma_name"] = j["area_name"]
pts["fma_agency"] = j["agency"]
# points that fall in no polygon (generalisation slivers) -> nearest polygon
miss = pts["fma_id"].isna()
if miss.any():
    jn = gpd.sjoin_nearest(pts.loc[miss, ["geometry"]], ag, how="left")
    jn = jn[~jn.index.duplicated()]
    pts.loc[miss, "fma_id"] = jn["fma_id"]
    pts.loc[miss, "fma_name"] = jn["area_name"]
    pts.loc[miss, "fma_agency"] = jn["agency"]
print("DA points assigned to FMA by nearest (outside polygons):", int(miss.sum()))
del fma, ag, j; gc.collect()

# Reserves (Aboriginal Lands of Canada, ALTYPE = Indian Reserve)
al = gpd.read_file(f"{DATA}/geo/indigenous/al_ta/AL_TA_CA_2_189_eng.shp")
print("AL_TA", len(al), al.ALTYPE.value_counts().to_dict())
ir = al[al.ALTYPE == "Indian Reserve"].copy().to_crs(ALBERS)
ir["geometry"] = shapely.make_valid(ir.geometry.values)
ir = ir[["NID", "ALCODE", "NAME1", "JUR1", "geometry"]].reset_index(drop=True)
ir.to_file(f"{WORK}/reserves_albers.gpkg", driver="GPKG")
jr = gpd.sjoin(pts[["geometry"]], ir, how="left", predicate="within")
jr = jr[~jr.index.duplicated()]
pts["reserve_nid"] = jr["NID"]
pts["reserve_name"] = jr["NAME1"]
pts["on_reserve"] = pts["reserve_nid"].notna()
print("DA points on reserve:", int(pts.on_reserve.sum()), "pop", pts.loc[pts.on_reserve, "pop2021"].sum())
# DAs with no population that are not inside a reserve polygon: nearest reserve within 2 km
nopop = pts.pop2021.isna() & ~pts.on_reserve
if nopop.any():
    jn = gpd.sjoin_nearest(pts.loc[nopop, ["geometry"]], ir, how="left", distance_col="dres")
    jn = jn[~jn.index.duplicated()]
    pts.loc[nopop, "nearest_reserve_name"] = jn["NAME1"]
    pts.loc[nopop, "nearest_reserve_km"] = (jn["dres"] / 1000).round(2)

x, y = pts.geometry.x, pts.geometry.y
lon, lat = Transformer.from_crs(ALBERS, "EPSG:4326", always_xy=True).transform(x.values, y.values)
pts["lon"] = np.round(lon, 5); pts["lat"] = np.round(lat, 5)
pts.drop(columns="geometry").to_csv(f"{WORK}/da_base.csv", index=False)
print("total", round(time.time() - t0), "s")
