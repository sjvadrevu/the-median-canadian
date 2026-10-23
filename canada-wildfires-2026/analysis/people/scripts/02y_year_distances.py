"""Step 2y: distances to fire outlines for ONE year (run once per year, separate processes to
keep memory low). Usage: python3 -I 02y_year_distances.py 2023 [min_ha]
With min_ha: only fires whose total outline area (all polygons sharing fire_uid, equal-area)
is >= min_ha; DA points, reserves and FN only; files get suffix _min<min_ha>.
Fire outlines: work/fires_<yr>.gpkg (00_extract_fires.py), original vertices.
Computes, for DA representative points, DA polygons (50 m generalised, sensitivity),
reserve polygons (3,322) and First Nation community points (638):
  inside test on the original polygons, then nearest boundary vertex (common.VertexTree).
2026 only: the same again using only M3 outlines with an agency-reported fire within 5 km.
2026 (rebuild 2026-10-21): outlines flagged exclude_from_distance by 00c_outline_class.py (13 agricultural/grass or
military-range burns with no agency-reported fire) are dropped before any distance is computed.
Output: work/dist_<yr>_da.csv, work/dist_<yr>_reserves.csv, work/dist_<yr>_fn.csv
"""
import sys, os, time, gc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

yr = int(sys.argv[1]); t0 = time.time()
minha = int(sys.argv[2]) if len(sys.argv) > 2 else None
sfx = f"_min{minha}" if minha else ""
da = pd.read_csv(f"{WORK}/da_base.csv", dtype={"DGUID": str}, usecols=["DGUID", "lon", "lat"])
pts = gpd.GeoDataFrame(da[["DGUID"]], geometry=gpd.points_from_xy(da.lon, da.lat), crs="EPSG:4326").to_crs(ALBERS)
# lon/lat were rounded to 5 decimals (~1 m); re-read exact points instead
p0 = gpd.read_file(f"{DATA}/geo/statcan/da_2021_pop_points.gpkg", columns=["DGUID"]).to_crs(ALBERS)
pts = p0.set_index("DGUID").reindex(da.DGUID).reset_index()
polys = gpd.read_file(f"{DATA}/geo/statcan/da_2021_pop_gen50m.gpkg", columns=["DGUID"]).to_crs(ALBERS)
polys = polys.set_index("DGUID").reindex(da.DGUID).reset_index()
polys["geometry"] = shapely.make_valid(polys.geometry.values)
ir = gpd.read_file(f"{WORK}/reserves_albers.gpkg")
fn = gpd.read_file(f"{DATA}/geo/indigenous/fn/Premiere_Nation_First_Nation_GPKG.gpkg").to_crs(ALBERS)

fires = gpd.read_file(f"{WORK}/fires_{yr}.gpkg")
if "exclude_from_distance" in fires.columns:
    print("excluded outlines (00c):", int(fires.exclude_from_distance.sum()), flush=True)
    fires = fires[~fires.exclude_from_distance.astype(bool)].reset_index(drop=True)
if minha:
    tot = fires.groupby("fire_uid")["area_ha"].transform("sum")
    fires = fires[tot >= minha].reset_index(drop=True)
fires["fire_idx"] = np.arange(len(fires))
nfires = len(fires)
meta = fires.drop(columns="geometry")
targets = {"da": pts, "dapoly": polys, "res": ir, "fn": fn}
if minha:
    del targets["dapoly"]
ins = {k: inside_index(g, fires) for k, g in targets.items()}
xy, own = boundary_vertices(fires.geometry.values)
if yr == 2026 and not minha:
    fm = fires[fires.agency_match].reset_index(drop=True); fm["fire_idx"] = np.arange(len(fm))
    ins_m = {k: inside_index(g, fm) for k, g in targets.items()}
    xym, ownm = boundary_vertices(fm.geometry.values)
    del fm
del fires; gc.collect()
print(yr, minha, nfires, "fires; inside tests + vertices", len(xy), "in", round(time.time() - t0), "s", flush=True)


def run(xy, own, ins):
    vt = VertexTree(xy, own)
    res = {}
    for k, g in targets.items():
        d, fi = vt.nearest(g.geometry.values)
        s = pd.Series(d, index=g.index); f = pd.Series(np.asarray(fi, dtype=np.int64), index=g.index)
        s.loc[ins[k].index] = 0.0; f.loc[ins[k].index] = ins[k].values.astype(np.int64)
        res[k] = (s.round(3), f.astype(int))
    return res


r = run(xy, own, ins); del xy, own; gc.collect()
uid = meta["fire_uid"].values
out_da = pd.DataFrame({"DGUID": da.DGUID, f"d{yr}_km": r["da"][0].values,
                       f"fire{yr}_uid": uid[r["da"][1].values]})
if not minha:
    out_da[f"dpoly{yr}_km"] = r["dapoly"][0].values
out_res = pd.DataFrame({"NID": ir.NID, f"d{yr}_km": r["res"][0].values, f"fire{yr}_uid": uid[r["res"][1].values]})
out_fn = pd.DataFrame({"band_number": fn.band_number, f"d{yr}_km": r["fn"][0].values, f"fire{yr}_uid": uid[r["fn"][1].values]})
if yr == 2026 and not minha:
    out_da["fire2026_agency_match"] = meta["agency_match"].values[r["da"][1].values]
    rm = run(xym, ownm, ins_m)
    out_da["d2026_matched_km"] = rm["da"][0].values
    out_da["dpoly2026_matched_km"] = rm["dapoly"][0].values
    out_res["d2026_matched_km"] = rm["res"][0].values
    out_fn["d2026_matched_km"] = rm["fn"][0].values
out_da.to_csv(f"{WORK}/dist_{yr}_da{sfx}.csv", index=False)
out_res.to_csv(f"{WORK}/dist_{yr}_reserves{sfx}.csv", index=False)
out_fn.to_csv(f"{WORK}/dist_{yr}_fn{sfx}.csv", index=False)
print(yr, "done in", round(time.time() - t0), "s; DAs <=50 km:", int((out_da[f"d{yr}_km"] <= 50).sum()), flush=True)
