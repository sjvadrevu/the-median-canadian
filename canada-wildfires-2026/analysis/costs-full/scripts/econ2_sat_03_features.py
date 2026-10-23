"""econ2_sat_03_features.py: Sentinel-2 burn features for every footprint of a job (work/econ2_sat/fp_<job>.csv.gz from
econ2_sat_02), exactly as analysis/property/scripts/08_features_2026.py does for 2026: footprints are processed in clusters
(fire x 20 km cell); per cluster a 10 m UTM grid around the footprints (1.5 km pad), per-pixel median composites of up to 6
lowest-cloud Sentinel-2 L2A scenes per MGRS tile for the post window and for the pre window (s2lib.dnbr_pair), dNBR and
dNDVI offset by the median of pixels more than 1 km from any fire polygon of the same year (s2lib.offset_and_apply), and the
per-building features of s2lib.building_features. The windows come from the AOI file (econ2_sat_01_aoi.py).
Fire polygons for the offset mask: NBAC polygons of the same year from every province within 30 km of the job's footprints
(2026: the job's BCWS perimeters plus analysis/outline-check/outline_class_2026.geojson).
Clusters wider than 12 km are processed in 10 km sub-cells (memory), each with its own grid and offset. Clusters with no
footprint within 500 m and clusters on fire polygons under 10 ha are skipped (they cannot pass the econ2_sat_04 screen).
Resumable and shardable: 'econ2_sat_03_features.py <job> k n' processes clusters i with i % n == k, appends to
work/econ2_sat/features_<job>_part<k>.csv and skips clusters already present in any features_<job>_part*.csv (re-read
before each cluster, so several workers can run at once; an optional 4th argument 'rev' walks the clusters from the end).
s2lib is imported read-only from analysis/property/scripts (no bytecode written there)."""
import glob, os, sys, time
sys.dont_write_bytecode = True
import numpy as np, pandas as pd, geopandas as gpd, pyogrio, shapely

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); AN = os.path.dirname(B); W = os.path.dirname(AN)
sys.path.insert(0, os.path.join(AN, "property", "scripts"))
import s2lib  # noqa: E402

OUT = os.path.join(B, "work", "econ2_sat")
job = sys.argv[1]
K, N = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
fp = pd.read_csv(os.path.join(OUT, f"fp_{job}.csv.gz"))
fp["aoi"] = fp.aoi.astype(str)
fp["cluster"] = fp.aoi + "_" + (fp.x // 20000).astype(int).astype(str) + "_" + (fp.y // 20000).astype(int).astype(str)
aoi = gpd.read_file(os.path.join(OUT, f"aoi_{job}.gpkg")).to_crs(3978)
aoi["fire_id"] = aoi.fire_id.astype(str)
info = aoi.set_index("fire_id")
year = int(aoi.year.iloc[0])
box = shapely.box(fp.x.min(), fp.y.min(), fp.x.max(), fp.y.max()).buffer(30000)
if year == 2026:
    m3 = gpd.read_file(os.path.join(AN, "outline-check", "outline_class_2026.geojson")).to_crs(3978)
    fire = pd.concat([aoi[["geometry"]], m3[["geometry"]]], ignore_index=True)
else:
    nb = os.path.join(W, "data/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp")
    b4 = gpd.GeoSeries([box], crs=3978).to_crs(pyogrio.read_info(nb)["crs"]).total_bounds
    fire = pyogrio.read_dataframe(nb, where=f"YEAR={year}", bbox=tuple(b4), columns=["YEAR"]).to_crs(3978)
fire = gpd.GeoDataFrame(fire, geometry="geometry", crs=3978)
fire["geometry"] = fire.geometry.simplify(15, preserve_topology=True)
REV = len(sys.argv) > 4 and sys.argv[4] == "rev"   # optional extra worker that walks the clusters from the end
TAG = f"{K}" if not REV else f"{K}r"
outf = os.path.join(OUT, f"features_{job}_part{TAG}.csv")


def done_now():
    """Clusters already written by any worker (re-read before each cluster so parallel workers do not repeat work)."""
    s = set()
    for f in glob.glob(os.path.join(OUT, f"features_{job}_part*.csv")):
        try:
            s |= set(pd.read_csv(f, usecols=["cluster"]).cluster)
        except Exception:
            pass
    return s


sc_rows = []
groups = list(fp.groupby("cluster"))
order = list(enumerate(groups))[::-1] if REV else list(enumerate(groups))
print(job, "clusters", len(groups), "footprints", len(fp), "done", len(done_now()), flush=True)
for i, (cl, g) in order:
    if (not REV and i % N != K) or cl in done_now():
        continue
    if g.dist.min() > 500:  # no footprint within 500 m: these clusters feed only the 500-1000 m false-positive check
        continue
    if float(info.loc[g.aoi.iloc[0]].area_ha or 0) < 10:  # fire polygons under 10 ha fail the quality screen in econ2_sat_04
        continue
    t0 = time.time()
    fi = info.loc[g.aoi.iloc[0]]
    ps, pe = fi.post_start, fi.post_end
    qs = fi.pre_start if isinstance(fi.pre_start, str) and fi.pre_start else None
    qe = fi.pre_end if isinstance(fi.pre_end, str) and fi.pre_end else None
    # clusters wider than 12 km are processed in 10 km sub-cells to fit in memory (analysis/property split Denare Beach and
    # Enterprise into 20 km cells for the same reason); results are written together under the cluster name
    big = (g.x.max() - g.x.min() > 12000) or (g.y.max() - g.y.min() > 12000)
    subs = [g] if not big else [sg for _, sg in g.groupby([(g.x // 10000).astype(int), (g.y // 10000).astype(int)])]
    outs, sc_rows = [], []
    for sg in subs:
        gg = gpd.GeoDataFrame(sg, geometry=gpd.GeoSeries.from_wkt(sg.footprint_wkt), crs=4326).to_crs(3978)
        utm, tr, shape, bbox, ext = s2lib.grid_for(gg.geometry.values)
        try:
            res = s2lib.dnbr_pair(bbox, utm, tr, shape, ps, pe, qs, qe)
        except Exception as e:
            print(cl, "imagery error", str(e)[:120], flush=True); res = None
        if res is None:
            f = pd.DataFrame(index=range(len(sg))); offs = {"dnbr": np.nan, "dndvi": np.nan}
        else:
            offs = s2lib.offset_and_apply(res, fire.to_crs(utm).geometry.values, tr, shape, ext)
            f = s2lib.building_features(gg.to_crs(utm).geometry.values, res, tr, shape, ext)
            sc_rows += [dict(cluster=cl, fire_id=sg.aoi.iloc[0], **s) for s in res["scenes"]]
            del res
        o = pd.concat([sg.drop(columns=["footprint_wkt"]).reset_index(drop=True), f], axis=1)
        o["dnbr_offset"] = offs["dnbr"]; o["dndvi_offset"] = offs["dndvi"]
        o["post_start"] = ps; o["post_end"] = pe; o["pre_start"] = qs or ""; o["pre_end"] = qe or ""
        c = gg.to_crs(3978).geometry.centroid.to_crs(4326); o["lon"] = c.x.values; o["lat"] = c.y.values
        o["subcell"] = len(outs) if big else -1
        outs.append(o)
    o = pd.concat(outs, ignore_index=True)
    if os.path.exists(outf):
        cols = pd.read_csv(outf, nrows=0).columns.tolist()
        o = o.reindex(columns=cols)  # keep the part file's column order (subcell column only in new files)
    o.to_csv(outf, mode="a", header=not os.path.exists(outf), index=False)
    scf = os.path.join(OUT, f"scenes_{job}_part{TAG}.csv")   # appended per cluster, so restarts keep earlier scene lists
    if sc_rows:
        pd.DataFrame(sc_rows).to_csv(scf, mode="a", header=not os.path.exists(scf), index=False)
    print(cl, len(g), "bldgs", len(subs), "cells", f"{time.time()-t0:.0f}s", flush=True)
print("END", job, K, N, flush=True)
