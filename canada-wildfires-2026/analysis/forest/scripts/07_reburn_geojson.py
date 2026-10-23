"""Write reburn_2026.geojson: the 2026 M3 footprint on the 240 m grid, classed by time since the most recent
NBAC burn (1972-2025). Run after 04_fma_forest.py (uses work/reburn_cat_2026.npy).
Classes: 0 no burn 1972-2025; 1 under 10 years (last burn 2017-2025); 2 10 to 30 years (1996-2016);
3 over 30 years (1972-1995). Geometry: grid cells polygonised, dissolved by class, simplified 120 m, WGS84.
mapped_ha is the equal-area area of the cells (not scaled); official_scaled_ha_national_split applies the
national class shares to the official 2026 total.
"""
import numpy as np
import geopandas as gpd
import rasterio.features as rf
from shapely.geometry import shape
from common import WORK, OUT, EA
from grid import meta, cell_area_m2

m = meta()
idx = np.load(WORK / "burn_2026.npy")
cat = np.load(WORK / "reburn_cat_2026.npy")
LAB = {0: "no burn 1972-2025", 1: "under 10 years (2017-2025)", 2: "10 to 30 years (1996-2016)", 3: "over 30 years (1972-1995)"}
a = np.zeros(m["H"] * m["W"], dtype="uint8")
a[idx] = cat + 1
a = a.reshape(m["H"], m["W"])
recs = [(shape(g), int(v) - 1) for g, v in rf.shapes(a, mask=a > 0, transform=m["T"], connectivity=4)]
del a
gdf = gpd.GeoDataFrame({"cls": [r[1] for r in recs]}, geometry=[r[0] for r in recs], crs=m["crs"])
area = {k: cell_area_m2(idx[cat == k]).sum() / 1e4 for k in LAB}
gdf = gdf.dissolve("cls").reset_index()
gdf["label"] = gdf.cls.map(LAB)
gdf["mapped_ha"] = gdf.cls.map(area)
gdf["share_of_2026_footprint"] = gdf.mapped_ha / sum(area.values())
# national official total (4,500,985 ha) split by the national class shares; provincial splits are in
# reburn_2026_by_province.csv (those apply provincial factors, so their sum differs slightly)
import pandas as pd
from common import OFFICIAL
off = pd.read_csv(OFFICIAL)
gdf["official_scaled_ha_national_split"] = gdf.share_of_2026_footprint * off[off.year == 2026].area_burned_ha.sum()
gdf["geometry"] = gdf.geometry.simplify(120, preserve_topology=True)
gdf.to_crs("EPSG:4326").to_file(OUT / "reburn_2026.geojson", driver="GeoJSON", COORDINATE_PRECISION=4)
print(gdf.drop(columns="geometry"))
