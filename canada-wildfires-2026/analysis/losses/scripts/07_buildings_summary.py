"""Combine building parts from 05_buildings.py; label community, fire area, province; summarise exposure.
Outputs: buildings_2026_near_outlines.gpkg (points, EPSG:3978) and buildings_exposure_by_{fire,community,province,area}.csv"""
import glob, os
import numpy as np, pandas as pd, geopandas as gpd

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(L)); G = os.path.join(W, "data", "geo")
parts = sorted(glob.glob(os.path.join(L, "work", "bldg_parts", "*.csv.gz")))
b = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
n0 = len(b); b = b.drop_duplicates(subset=["x", "y"]).reset_index(drop=True)
print("buildings near outlines", n0, "after dedupe", len(b))
b = gpd.GeoDataFrame(b, geometry=gpd.points_from_xy(b.x, b.y), crs=3978)
b["zone"] = np.where(b.dist_m <= 0, "inside", "within_100m")

o = gpd.read_file(os.path.join(W, "analysis", "outline-check", "outline_class_2026.geojson"))[["fire_uid", "class", "prov", "first_date", "last_date", "area_ha", "agency_match"]]
b = b.merge(o, on="fire_uid", how="left")
b["headline"] = b["class"] != "possible industrial or urban heat"

# community labels
al = gpd.read_file(os.path.join(G, "indigenous", "al_ta", "AL_TA_CA_2_189_eng.shp"), columns=["NAME1", "ALTYPE"]).to_crs(3978)
pc = gpd.read_file(os.path.join(G, "statcan", "popcentres_2021_pop.gpkg"), columns=["PCNAME", "PRUID", "pop2021"]).to_crs(3978)
fn = gpd.read_file(os.path.join(G, "indigenous", "fn", "Premiere_Nation_First_Nation_GPKG.gpkg")).to_crs(3978)
j = gpd.sjoin(b[["geometry"]], al, how="left", predicate="within")
j = j[~j.index.duplicated()]
b["reserve_or_settlement"] = j["NAME1"]
j = gpd.sjoin(b[["geometry"]], pc, how="left", predicate="within"); j = j[~j.index.duplicated()]
b["population_centre"] = j["PCNAME"]
pcc = pc.copy(); pcc["geometry"] = pcc.geometry.representative_point()
nn = gpd.sjoin_nearest(b[["geometry"]], pc[["PCNAME", "geometry"]], how="left", max_distance=25000, distance_col="d_pc")
nn = nn[~nn.index.duplicated()]
nf = gpd.sjoin_nearest(b[["geometry"]], fn[["band_name", "geometry"]], how="left", max_distance=25000, distance_col="d_fn")
nf = nf[~nf.index.duplicated()]
def label(i):
    if isinstance(b.at[i, "reserve_or_settlement"], str): return b.at[i, "reserve_or_settlement"] + " (reserve/settlement)"
    if isinstance(b.at[i, "population_centre"], str): return b.at[i, "population_centre"]
    cand = []
    if isinstance(nn.at[i, "PCNAME"], str): cand.append((nn.at[i, "d_pc"], f"near {nn.at[i, 'PCNAME']}"))
    if isinstance(nf.at[i, "band_name"], str): cand.append((nf.at[i, "d_fn"], f"near {nf.at[i, 'band_name']} (First Nation)"))
    if cand:
        d, s = min(cand); return f"{s} ({d/1000:.0f} km)"
    return "no named community within 25 km"
b["community"] = [label(i) for i in b.index]
b["community_group"] = b.community.str.replace(r" \(\d+ km\)$", "", regex=True)
fma = gpd.read_file(os.path.join(G, "fma_v2.gpkg"), columns=["area_name", "agency", "province"]).to_crs(3978)
j = gpd.sjoin(b[["geometry"]], fma, how="left", predicate="within"); j = j[~j.index.duplicated()]
b["fire_area"] = j["agency"].fillna("") + " " + j["area_name"].fillna("(outside mapped areas)")
b["prov"] = b["prov"].fillna(j["province"])
b.drop(columns=["footprint_wkt"]).to_file(os.path.join(L, "buildings_2026_near_outlines.gpkg"), layer="buildings", driver="GPKG")
b[["fire_uid", "x", "y", "footprint_wkt"]].to_csv(os.path.join(L, "work", "building_footprints_wkt.csv.gz"), index=False)

h = b[b.headline]
def summ(df, keys):
    g = df.groupby(keys + ["zone"]).size().unstack("zone", fill_value=0)
    for c in ["inside", "within_100m"]:
        if c not in g: g[c] = 0
    g["inside_or_100m"] = g.inside + g.within_100m
    return g.sort_values("inside_or_100m", ascending=False)
f = summ(h, ["fire_uid"]).join(o.set_index("fire_uid")[["prov", "class", "first_date", "last_date", "area_ha", "agency_match"]])
top_comm = h.groupby("fire_uid").community_group.agg(lambda s: "; ".join(f"{k} {v}" for k, v in s.value_counts().head(3).items()))
f = f.join(top_comm.rename("main_communities"))
fa = h.groupby("fire_uid").fire_area.agg(lambda s: s.value_counts().index[0])
f = f.join(fa.rename("fire_area"))
f.to_csv(os.path.join(L, "buildings_exposure_by_fire.csv"))
summ(h, ["prov", "community_group"]).to_csv(os.path.join(L, "buildings_exposure_by_community.csv"))
pv = summ(h, ["prov"]); pv.loc["Canada"] = pv.sum(); pv.to_csv(os.path.join(L, "buildings_exposure_by_province.csv"))
summ(h, ["fire_area"]).to_csv(os.path.join(L, "buildings_exposure_by_fire_area.csv"))
ex = summ(b[~b.headline], ["fire_uid"]).join(o.set_index("fire_uid")[["prov", "class", "area_ha"]])
ex.to_csv(os.path.join(L, "buildings_exposure_excluded_urban_heat.csv"))
pd.set_option("display.width", 250)
print(pv.to_string()); print(f.head(30).to_string()); print("urban-heat outlines:"); print(ex.to_string())
print("fires with >=10 inside:", int((f.inside >= 10).sum()), "buildings inside them:", int(f[f.inside >= 10].inside.sum()))
