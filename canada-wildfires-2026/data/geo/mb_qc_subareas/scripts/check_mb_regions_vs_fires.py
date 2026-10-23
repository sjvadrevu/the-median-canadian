"""Cross-check MWS restriction-area region attribute against 2026 FireView fire numbers (EA/WE/NO prefix).
usage: python3 -I check_mb_regions_vs_fires.py OUT_DIR"""
import sys, re, json, zipfile, tempfile
import pandas as pd, geopandas as gpd
O = sys.argv[1]
s = open(f"{O}/raw/mb/MB_TravelRestrictionAreas_2025.js", encoding="utf-8").read()
g = gpd.GeoDataFrame.from_features(json.loads(s[s.index("{"):].rstrip().rstrip(";"))["features"], crs=4326)
g["geometry"] = g.make_valid()
r = open(f"{O}/raw/mb/restrictions_2025.js", encoding="utf-8").read()
reg = {int(a): x for a, x in re.findall(r'"area":"(\d+)",\s*"restrict":"[^"]*",\s*"region":"([A-Z/]+)"', r)}
g["region"] = g.AREA_NUMBE.astype(int).map(reg)
with tempfile.TemporaryDirectory() as t:
    zipfile.ZipFile(f"{O}/raw/mb/MB_Forest_Fires_Shapefile_2026-10-21.zip").extractall(t)
    f = gpd.read_file(f"{t}/MB_Forest_Fires.shp").to_crs(4326)
f["geometry"] = f.geometry.representative_point()
f["fire_prefix"] = f.FIRENUM.str[:2]
j = gpd.sjoin(f, g[["AREA_NUMBE", "region", "geometry"]], how="left")
print(pd.crosstab(j.fire_prefix, j.region.fillna("outside areas (south)")))
