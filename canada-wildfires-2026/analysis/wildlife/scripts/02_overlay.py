"""Tiled exact vector overlay in ESRI:102001.
For each target polygon T computes, summed over 100 km tiles:
  A    = area(T)
  m    = area(T & M3_2026)                (M3 outlines, no overlaps)
  u    = area(T & U)   U = union of NBAC 1987-2025 footprints (reburns counted once)
  um   = area(T & U & M3_2026)
Targets: ECCC 51 ranges, Quebec and Saskatchewan caribou layers, set unions, national parks (CLAB),
CPCAD terrestrial union by LOC province and national.
Memory-lean: targets, NBAC and CPCAD are read per tile with a bbox (GeoPackage R-tree); results are
checkpointed per tile so the run can be resumed.
Usage: python -I 02_overlay.py <work_dir> [n_workers] [tile_limit]"""
import sys, os, time
import numpy as np, pandas as pd, geopandas as gpd, pyogrio, shapely
from shapely import box
from multiprocessing import Pool

WORK = sys.argv[1]
NPROC = int(sys.argv[2]) if len(sys.argv) > 2 else 2
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else None
INP = os.path.join(WORK, "inputs.gpkg")
NB = os.path.join(WORK, "nbac_1987_2025.gpkg")
TG = os.path.join(WORK, "targets.gpkg")
TILE = 100_000
LOCNAME = {1: "AB", 2: "BC", 3: "MB", 4: "NB", 5: "NL", 6: "NT", 7: "NS", 8: "NU", 9: "ON", 10: "PE", 11: "QC", 12: "SK", 13: "YT"}


def area(g):
    return 0.0 if g is None or g.is_empty else g.area


def fixclip(geoms, b):
    out = shapely.intersection(geoms, b)
    bad = ~shapely.is_valid(out)
    if bad.any():
        out[bad] = shapely.make_valid(out[bad])
    keep = []
    for g in out:
        if g is None or g.is_empty:
            continue
        if g.geom_type not in ("Polygon", "MultiPolygon"):
            parts = [p for p in shapely.get_parts(g) if p.geom_type in ("Polygon", "MultiPolygon")]
            if not parts:
                continue
            g = shapely.union_all(parts)
        keep.append(g)
    return keep


def build_targets():
    rows = []
    e = gpd.read_file(INP, layer="eccc_ranges")
    for _, r in e.iterrows():
        rows.append(("eccc", r["CODE"], r["HERD"], r.geometry))
    rows.append(("eccc_union", "ALL", "All 51 ECCC boreal caribou ranges (union)", shapely.union_all(e.geometry.values)))
    q = gpd.read_file(INP, layer="qc_caribou")
    for _, r in q.iterrows():
        rows.append(("qc", str(r["EO_ID"]), r["NOM_POP"], r.geometry))
    rows.append(("qc_union", "ALL", "All Quebec forest-ecotype caribou populations (union)", shapely.union_all(q.geometry.values)))
    s = gpd.read_file(INP, layer="sk_caribou")
    for _, r in s.iterrows():
        rows.append(("sk", f"{r['RNGEUNIT']}|{r['CONUNIT']}|{r['SUBUNIT']}", f"{r['RNGEUNIT']} {r['CONUNIT'] or ''} {r['SUBUNIT'] or ''}".strip(), r.geometry))
    rows.append(("sk_union", "ALL", "All Saskatchewan caribou units (union)", shapely.union_all(s.geometry.values)))
    p = gpd.read_file(INP, layer="parks")
    for _, r in p.iterrows():
        rows.append(("park", r["CLAB_ID"], r["NAME_E"], r.geometry))
    g = gpd.GeoDataFrame(rows, columns=["set", "tid", "name", "geometry"], crs="ESRI:102001")
    g.to_file(TG, layer="targets", driver="GPKG")


def init():
    global M3, MS
    M3 = gpd.read_file(INP, layer="m3_2026", columns=[]); MS = M3.sindex


def do_tile(bounds):
    b = box(*bounds)
    res = []
    nb = pyogrio.read_dataframe(NB, bbox=bounds, columns=[])
    U = shapely.union_all(fixclip(nb.geometry.values, b)) if len(nb) else None
    del nb
    mi = MS.query(b, predicate="intersects")
    Mt = shapely.union_all(fixclip(M3.geometry.values[mi], b)) if len(mi) else None
    UM = shapely.intersection(U, Mt) if (U is not None and Mt is not None) else None
    if U is not None: shapely.prepare(U)
    if Mt is not None: shapely.prepare(Mt)

    def metrics(g):
        a = g.area
        am = area(shapely.intersection(g, Mt)) if Mt is not None else 0.0
        au = area(shapely.intersection(g, U)) if U is not None else 0.0
        aum = area(shapely.intersection(g, UM)) if (UM is not None and am > 0) else 0.0
        return a, am, au, aum

    T = pyogrio.read_dataframe(TG, layer="targets", bbox=bounds, columns=["set", "tid"])
    for st, tid, geom in zip(T.set.values, T.tid.values, T.geometry.values):
        pieces = fixclip(np.array([geom]), b)
        if pieces:
            res.append((st, tid, *metrics(pieces[0])))
    del T
    PA = pyogrio.read_dataframe(INP, layer="cpcad_t", bbox=bounds, columns=["LOC"])
    if len(PA):
        allp = []
        for loc, grp in PA.groupby("LOC"):
            pieces = fixclip(grp.geometry.values, b)
            if not pieces:
                continue
            g = shapely.union_all(pieces)
            allp.append(g)
            res.append(("pa_prov", LOCNAME.get(int(loc), str(loc)), *metrics(g)))
        if allp:
            res.append(("pa_nat", "CA", *metrics(shapely.union_all(allp))))
    res.append(("tiles_processed", "CA", b.area, area(Mt), area(U), area(UM)))
    return bounds, res


if __name__ == "__main__":
    t0 = time.time()
    if not os.path.exists(TG):
        build_targets()
    boxes = []
    for f, lyr in ((TG, "targets"), (INP, "m3_2026"), (INP, "cpcad_t")):
        _, bnds = pyogrio.read_bounds(f, layer=lyr)
        boxes.append(shapely.box(*bnds))
    allb = np.concatenate(boxes)
    tree = shapely.STRtree(allb)
    x0, y0, x1, y1 = shapely.total_bounds(allb)
    tiles = []
    for x in np.arange(np.floor(x0 / TILE) * TILE, x1, TILE):
        for y in np.arange(np.floor(y0 / TILE) * TILE, y1, TILE):
            bb = (float(x), float(y), float(x + TILE), float(y + TILE))
            if len(tree.query(box(*bb))):
                tiles.append(bb)
    print("tiles", len(tiles), flush=True)
    if LIMIT:
        tiles = tiles[:LIMIT]
    ck = os.path.join(WORK, "overlay_tiles_checkpoint.csv")
    need_header = not os.path.exists(ck) or os.path.getsize(ck) == 0
    done = set() if need_header else set(pd.read_csv(ck, usecols=["tile"]).tile.unique())
    todo = [bb for bb in tiles if f"{int(bb[0])}_{int(bb[1])}" not in done]
    print("todo", len(todo), "already done", len(done), flush=True)
    with open(ck, "a") as fh:
        if need_header:
            fh.write("tile,set,tid,A,m,u,um\n")
        with Pool(NPROC, initializer=init, maxtasksperchild=25) as pool:
            for k, (bb, r) in enumerate(pool.imap_unordered(do_tile, todo, chunksize=1)):
                key = f"{int(bb[0])}_{int(bb[1])}"
                fh.write("".join(key + "," + ",".join(str(x) for x in row) + "\n" for row in r))
                fh.flush()
                if k % 50 == 0:
                    print(k, len(todo), round(time.time() - t0), "s", flush=True)
    df = pd.read_csv(ck, dtype={"tid": str})
    tilekeys = {f"{int(bb[0])}_{int(bb[1])}" for bb in tiles}
    missing = tilekeys - set(df.tile.unique())
    print("tiles missing from checkpoint:", len(missing), flush=True)
    df = df[df.tile.isin(tilekeys)].drop_duplicates()
    agg = df.groupby(["set", "tid"], as_index=False)[["A", "m", "u", "um"]].sum()
    names = pyogrio.read_dataframe(TG, layer="targets", read_geometry=False, columns=["set", "tid", "name"])
    agg = agg.merge(names, on=["set", "tid"], how="left")
    if not missing:
        agg.to_csv(os.path.join(WORK, "overlay_results.csv"), index=False)
    print("done", round(time.time() - t0), "s")
