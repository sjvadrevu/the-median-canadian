"""Step 10: boundaries of the main DND training areas, one (multi)polygon per base, EPSG:3978.
Official polygons:
  Wainwright, Suffield  - Government of Alberta DND Military Base layer (data/geo/dnd/ab_dnd_layer13.geojson)
  Gagetown              - GeoNB Military Bases (data/geo/dnd/nb_military_bases_geonb.geojson, from PWGSC)
  Petawawa, Meaford     - Ontario MNR LIO Federal Land Other, type 'Military Base' (data/geo/dnd/on_federal_land_military_base.geojson)
Proxy (no official polygon found): Directory of Federal Real Property DND parcels drawn as circles of the
parcel's land area around the parcel point (data/geo/dnd/dfrp_dnd_parcels.gpkg):
  Shilo (12439-01, 12439-02, 12448-01), Dundurn (14121-01), Valcartier (05906-01, 05906-02)
Output: work/bases.gpkg"""
import geopandas as gpd, pandas as pd
B = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/data/geo/dnd"
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
rows = []
ab = gpd.read_file(f"{B}/ab_dnd_layer13.geojson").to_crs(3978)
for nm, key in [("Wainwright", "Wainwright"), ("Suffield", "Suffield")]:
    rows.append((nm, "official: Government of Alberta DND Military Base layer", ab[ab.MB_NAME.str.contains(key)].union_all()))
nb = gpd.read_file(f"{B}/nb_military_bases_geonb.geojson").to_crs(3978)
rows.append(("Gagetown", "official: GeoNB Military Bases (PWGSC source)", nb.union_all()))
on = gpd.read_file(f"{B}/on_federal_land_military_base.geojson").to_crs(3978)
rows.append(("Petawawa", "official: Ontario LIO Federal Land Other (Military Base)", on[on.OFFICIAL_NAME == "CFB Petawawa"].union_all()))
rows.append(("Meaford", "official: Ontario LIO Federal Land Other (Military Base)", on[on.OFFICIAL_NAME.str.contains("Meaford")].union_all()))
df = gpd.read_file(f"{B}/dfrp_dnd_parcels.gpkg").to_crs(3978)
for nm, keys in [("Shilo", [("12439", "01"), ("12439", "02"), ("12448", "01")]), ("Dundurn", [("14121", "01")]),
                 ("Valcartier", [("05906", "01"), ("05906", "02")])]:
    s = df[[ (p, q) in keys for p, q in zip(df.property_number, df.parcel)]]
    rows.append((nm, "PROXY: DFRP parcel point + equal-area circle", s.geometry.buffer(1).union_all() if False else
                 gpd.GeoSeries([g.buffer(r) for g, r in zip(s.geometry, s.eq_radius_m)], crs=3978).union_all()))
g = gpd.GeoDataFrame([dict(base=a, boundary_source=b) for a, b, _ in rows], geometry=[c for *_, c in rows], crs=3978)
g["area_ha"] = g.to_crs(3979).area / 1e4  # NAD83 / Canada Atlas Lambert is conformal; area in EPSG:3979? recompute equal-area below
g["area_ha"] = g.to_crs("ESRI:102001").area / 1e4
g.to_file(f"{O}/work/bases.gpkg"); print(g.drop(columns="geometry"))
