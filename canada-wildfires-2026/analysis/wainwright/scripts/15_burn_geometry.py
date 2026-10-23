"""Step 15: geometry of the main estimated burn (dNBR >= 0.27): length (longest vertex-to-vertex span),
orientation, extent in lat/lon, part outside the Alberta DND polygon, distance from the Oct 17 hotspot cluster
centroid; export WGS84 GeoJSON of the estimate and of the outside part.
Outputs: burn_estimate_T27.geojson, burn_outside_base_T27.geojson, burn_geometry.csv"""
import geopandas as gpd, numpy as np, pandas as pd
from shapely.geometry import MultiPoint
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
B = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
g = gpd.read_file(f"{O}/work/burn_T27.gpkg").to_crs(32612); geom = g.geometry.iloc[0]
dnd = gpd.read_file(f"{B}/data/geo/dnd/ab_dnd_layer13.geojson"); base = dnd[dnd.MB_NAME.str.contains("Wainwright")].to_crs(32612).union_all()
hull = geom.convex_hull; pts = np.array(hull.exterior.coords)
d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1)); i, j = np.unravel_index(d.argmax(), d.shape)
dx, dy = pts[j] - pts[i]; bearing = (np.degrees(np.arctan2(dx, dy)) + 360) % 180
out = geom.difference(base)
hs = pd.read_csv(f"{O}/raw/wfs_hotspots_wainwright_20261010_on.csv"); hs = hs[hs.rep_day == "2026-10-17"]
c = gpd.GeoSeries(gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(32612)
cen = MultiPoint(list(c)).centroid
far = max(cen.distance(gpd.GeoSeries([gpd.points_from_xy([x], [y])[0] for x, y in geom.convex_hull.exterior.coords]).iloc[k]) for k in range(len(geom.convex_hull.exterior.coords)))
ll = gpd.GeoSeries([geom], crs=32612).to_crs(4326).total_bounds
r = dict(area_ha=round(geom.area / 1e4, 1), outside_ha=round(out.area / 1e4, 1), length_km=round(d.max() / 1000, 2),
         long_axis_bearing_deg=round(bearing), lon_min=round(ll[0], 4), lat_min=round(ll[1], 4), lon_max=round(ll[2], 4), lat_max=round(ll[3], 4),
         hotspot_cluster_extent_km=round(MultiPoint(list(c)).convex_hull.length / 2 / 1000, 2),
         max_dist_from_oct17_cluster_centroid_km=round(far / 1000, 2))
pd.DataFrame([r]).to_csv(f"{O}/burn_geometry.csv", index=False); print(r)
gpd.GeoDataFrame(dict(label=["ESTIMATE: Sentinel-2 dNBR>=0.27, 2026-10-04 vs 2026-10-19"]), geometry=[geom], crs=32612).to_crs(4326).to_file(f"{O}/burn_estimate_T27.geojson")
gpd.GeoDataFrame(dict(label=["ESTIMATE: part outside Alberta DND polygon"]), geometry=[out], crs=32612).to_crs(4326).to_file(f"{O}/burn_outside_base_T27.geojson")
