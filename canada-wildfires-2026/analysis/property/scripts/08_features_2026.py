"""Sentinel-2 burn features for every Microsoft footprint within 1 km of a 2026 CWFIS M3 outline (outlines classed
agricultural/grass burn or military range excluded; work/fp_2026_all_1km.csv.gz from 04_footprints.py).
Footprints are processed in clusters (fire x 20 km cell). Post window per fire: day after the outline's last hotspot
detection to 2026-10-20, or the last 30 days to 2026-10-20 if that is later (as analysis/losses/08_dnbr.py); pre window:
same calendar dates in 2025 (+-10 days). Offset from pixels > 1 km outside all 2026 outlines.
Resumable and shardable: '08_features_2026.py k n' processes clusters i with i % n == k, appends to
work/features_2026_part<k>.csv and skips clusters already present in any work/features_2026*.csv."""
import glob
import os, sys, time
import numpy as np, pandas as pd, geopandas as gpd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s2lib
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.dirname(os.path.dirname(P))
END = pd.Timestamp("2026-10-20")
fp = pd.read_csv(os.path.join(P, "work", "fp_2026_all_1km.csv.gz"))
fp["cluster"] = fp.aoi.astype(str) + "_" + (fp.x // 20000).astype(int).astype(str) + "_" + (fp.y // 20000).astype(int).astype(str)
outl = gpd.read_file(os.path.join(W, "analysis", "outline-check", "outline_class_2026.geojson"))
info = outl.set_index("fire_uid")
K, N = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
outf = os.path.join(P, "work", f"features_2026_part{K}.csv")
done = set().union(*[set(pd.read_csv(f).cluster) for f in glob.glob(os.path.join(P, "work", "features_2026*.csv"))])
sc_rows = []
for i, (cl, g) in enumerate(fp.groupby("cluster")):
    if cl in done or i % N != K: continue
    t0 = time.time()
    fid = int(g.aoi.iloc[0]); last = pd.Timestamp(info.loc[fid, "last_date"])
    ps = min(last + pd.Timedelta(days=1), END - pd.Timedelta(days=30))
    gg = gpd.GeoDataFrame(g, geometry=gpd.GeoSeries.from_wkt(g.footprint_wkt), crs=4326).to_crs(3978)
    utm, tr, shape, bbox, ext = s2lib.grid_for(gg.geometry.values)
    res = s2lib.dnbr_pair(bbox, utm, tr, shape, ps.date(), END.date())
    if res is None:
        print(cl, "no imagery"); f = pd.DataFrame(index=range(len(g))); offs = {"dnbr": np.nan, "dndvi": np.nan}
    else:
        offs = s2lib.offset_and_apply(res, outl.to_crs(utm).geometry.values, tr, shape, ext)
        f = s2lib.building_features(gg.to_crs(utm).geometry.values, res, tr, shape, ext)
        sc_rows += [dict(cluster=cl, fire_uid=fid, **s) for s in res["scenes"]]
    o = pd.concat([g.drop(columns=["footprint_wkt"]).reset_index(drop=True), f], axis=1)
    o["dnbr_offset"] = offs["dnbr"]; o["post_start"] = ps.date()
    c = gg.to_crs(4326).geometry.centroid; o["lon"] = c.x.values; o["lat"] = c.y.values
    o.to_csv(outf, mode="a", header=not os.path.exists(outf), index=False)
    pd.DataFrame(sc_rows).to_csv(os.path.join(P, "work", f"scenes_2026_part{K}.csv"), index=False)
    print(cl, len(g), "bldgs", shape, f"{time.time()-t0:.0f}s", flush=True)
