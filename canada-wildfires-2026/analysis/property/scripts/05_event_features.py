"""Per-building Sentinel-2 burn features for a calibration / check event.
usage: 05_event_features.py <event> <footprints.csv.gz> <post_start> <post_end> <nbac_year> [official.geojson status_col]
 * footprints: output of 04_footprints.py (Microsoft footprints).
 * fire polygons for the offset: NBAC 1972-2025 polygons of nbac_year within 30 km (or 2026 M3 outlines if nbac_year=2026).
 * if an official damage layer is given, each Microsoft footprint gets the status of the official polygon/point it
   overlaps most (polygons) or the nearest official point within 15 m (points); the official polygons are also scored
   directly as footprints (set=official).
Writes work/features_<event>.csv, work/dnbr_<event>.tif and work/scenes_<event>.csv."""
import os, sys
import numpy as np, pandas as pd, geopandas as gpd, shapely, rasterio, pyogrio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s2lib
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.dirname(os.path.dirname(P))
ev, fpf, ps, pe, ny = sys.argv[1:6]
fp = pd.read_csv(fpf)
fp = gpd.GeoDataFrame(fp, geometry=gpd.GeoSeries.from_wkt(fp.footprint_wkt), crs=4326).to_crs(3978)
fp["set"] = "microsoft"
sets = [fp]
if len(sys.argv) > 6:
    off = gpd.read_file(sys.argv[6]).to_crs(3978); sc = sys.argv[7]
    off = off[off[sc].fillna("").str.strip() != ""].reset_index(drop=True)
    off["status"] = off[sc].str.strip()
    if off.geom_type.iloc[0].endswith("Polygon"):
        j = gpd.overlay(fp[["geometry"]].reset_index(names="fid"), off[["status", "geometry"]].reset_index(names="oid"), how="intersection", keep_geom_type=True)
        j["a"] = j.area; j = j.sort_values("a", ascending=False).drop_duplicates("fid")
        fp["status"] = fp.index.map(j.set_index("fid").status); fp["official_id"] = fp.index.map(j.set_index("fid").oid)
        o2 = off[["status", "geometry"]].copy(); o2["set"] = "official"; o2["official_id"] = o2.index
        o2["x"] = o2.centroid.x; o2["y"] = o2.centroid.y
        sets.append(o2)
    else:
        nn = gpd.sjoin_nearest(fp[["geometry"]].assign(geometry=fp.centroid), off[["status", "geometry"]], max_distance=15, distance_col="d")
        nn = nn[~nn.index.duplicated()]
        fp["status"] = nn.status; fp["official_id"] = nn.index_right
allb = pd.concat(sets, ignore_index=True)
allb = gpd.GeoDataFrame(allb, geometry="geometry", crs=3978)
if ny == "2026":
    fire = gpd.read_file(os.path.join(W, "analysis", "outline-check", "outline_class_2026.geojson")).to_crs(3978)
else:
    box = shapely.box(*allb.total_bounds).buffer(30000)
    b4 = gpd.GeoSeries([box], crs=3978).to_crs(pyogrio.read_info(os.path.join(W, "data/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp"))["crs"]).total_bounds
    fire = pyogrio.read_dataframe(os.path.join(W, "data/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp"), where=f"YEAR={ny}", bbox=tuple(b4)).to_crs(3978)
print(ev, len(fp), "microsoft footprints;", len(allb) - len(fp), "official;", len(fire), "fire polygons", flush=True)
utm, tr, shape, bbox, ext = s2lib.grid_for(allb.geometry.values)
res = s2lib.dnbr_pair(bbox, utm, tr, shape, ps, pe)
offs = s2lib.offset_and_apply(res, fire.to_crs(utm).geometry.values, tr, shape, ext)
print("offsets", offs, "scenes", len(res["scenes"]), flush=True)
feat = s2lib.building_features(allb.to_crs(utm).geometry.values, res, tr, shape, ext)
dist = allb.geometry.distance(fire.union_all()) if len(fire) else np.nan
outdf = pd.concat([allb.drop(columns=["geometry", "footprint_wkt"], errors="ignore").reset_index(drop=True), feat], axis=1)
outdf["dist_fire_m"] = np.round(dist.values, 1); outdf["event"] = ev
outdf["dnbr_offset"] = round(offs["dnbr"], 1); outdf["dndvi_offset"] = round(offs["dndvi"], 1)
c = allb.to_crs(4326).centroid; outdf["lon"] = c.x.values; outdf["lat"] = c.y.values
outdf.to_csv(os.path.join(P, "work", f"features_{ev}.csv"), index=False)
pd.DataFrame(res["scenes"]).assign(event=ev).to_csv(os.path.join(P, "work", f"scenes_{ev}.csv"), index=False)
with rasterio.open(os.path.join(P, "work", f"dnbr_{ev}.tif"), "w", driver="GTiff", height=shape[0], width=shape[1], count=2, dtype="int16",
                   crs=utm, transform=tr, nodata=-32768, compress="deflate") as dst:
    for i, k in enumerate(["dnbr", "dndvi"], 1):
        dst.write(np.where(np.isfinite(res[k]), np.round(res[k]), -32768).astype("int16"), i)
if "status" not in outdf: outdf["status"] = None
print(outdf.groupby(["set", "status"], dropna=False).agg(n=("dnbr_bmax", "size"), dnbr_bmax=("dnbr_bmax", "median"), ring=("dnbr_r20_60", "median"), dndvi=("dndvi_bmax", "median")))
