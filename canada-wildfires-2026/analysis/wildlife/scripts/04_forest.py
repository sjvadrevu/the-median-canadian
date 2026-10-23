"""Forest area (Land Cover of Canada 2020, classes 1,2,5,6; 240 m count raster) inside targets and
inside targets AND 2026 M3 outlines. Cell-centre rasterization on the 240 m grid (EPSG:3979).
Area per 30 m pixel corrected from nominal 900 m2 to true ground area by dividing by the EPSG:3979
areal scale factor at each cell centre (the Lambert conformal grid is not equal-area).
Usage: python -I 04_forest.py <data_dir> <work_dir> [caribou|pa|all]"""
import sys, os, time
import numpy as np, pandas as pd, geopandas as gpd, rasterio, pyproj
from rasterio import features
from rasterio.windows import Window
from shapely import box

DATA, WORK = sys.argv[1], sys.argv[2]
INP = os.path.join(WORK, "inputs.gpkg")
RAS = f"{DATA}/geo/landcover/lc2020_forest_count_240m.tif"
LOCNAME = {1: "AB", 2: "BC", 3: "MB", 4: "NB", 5: "NL", 6: "NT", 7: "NS", 8: "NU", 9: "ON", 10: "PE", 11: "QC", 12: "SK", 13: "YT"}
t0 = time.time()
src = rasterio.open(RAS)
crs = src.crs
proj = pyproj.Proj(crs)
inv = pyproj.Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

m3 = gpd.read_file(INP, layer="m3_2026").to_crs(crs)
MS = m3.sindex
B = 2048  # block size in cells; processing block by block keeps memory bounded


def stats(geoms):
    geoms = [g for g in geoms if g is not None and not g.is_empty]
    gs = gpd.GeoSeries(geoms, crs=crs)
    GS = gs.sindex
    xmin, ymin, xmax, ymax = gs.total_bounds
    T = src.transform
    c0 = max(0, int(np.floor((xmin - T.c) / T.a))); c1 = min(src.width, int(np.ceil((xmax - T.c) / T.a)))
    r0 = max(0, int(np.floor((ymax - T.f) / T.e))); r1 = min(src.height, int(np.ceil((ymin - T.f) / T.e)))
    acc = dict(cells_km2=0.0, forest_km2=0.0, burned_cells_km2=0.0, forest_burned_km2=0.0)
    for r in range(r0, r1, B):
        for c in range(c0, c1, B):
            w = Window(c, r, min(B, c1 - c), min(B, r1 - r))
            tr = src.window_transform(w)
            bb = box(*rasterio.windows.bounds(w, T))
            gi = GS.query(bb, predicate="intersects")
            if len(gi) == 0:
                continue
            inside = features.rasterize(((gs.iloc[i], 1) for i in gi), out_shape=(w.height, w.width), transform=tr, dtype="uint8")
            rr, cc = np.nonzero(inside)
            if len(rr) == 0:
                continue
            mi = MS.query(bb, predicate="intersects")
            if len(mi):
                bm = features.rasterize(((m3.geometry.iloc[i], 1) for i in mi), out_shape=(w.height, w.width), transform=tr, dtype="uint8")[rr, cc].astype(bool)
            else:
                bm = np.zeros(len(rr), bool)
            fv = src.read(1, window=w)[rr, cc].astype(np.float64)
            fv[fv == 255] = 0
            lon, lat = inv.transform(tr.c + (cc + 0.5) * tr.a, tr.f + (rr + 0.5) * tr.e)
            pix_km2 = 900 / proj.get_factors(lon, lat).areal_scale / 1e6  # true km2 of one 30 m pixel
            cell = 64 * pix_km2
            acc["cells_km2"] += cell.sum(); acc["forest_km2"] += (fv * pix_km2).sum()
            acc["burned_cells_km2"] += cell[bm].sum(); acc["forest_burned_km2"] += (fv[bm] * pix_km2[bm]).sum()
    return acc


def block_metrics(acc, inside, w, tr, bm_full=None):
    rr, cc = np.nonzero(inside)
    if len(rr) == 0:
        return
    fv = FBLK[rr, cc].astype(np.float64)
    fv[fv == 255] = 0
    lon, lat = inv.transform(tr.c + (cc + 0.5) * tr.a, tr.f + (rr + 0.5) * tr.e)
    pix_km2 = 900 / proj.get_factors(lon, lat).areal_scale / 1e6
    bm = bm_full[rr, cc].astype(bool)
    cell = 64 * pix_km2
    acc["cells_km2"] += cell.sum(); acc["forest_km2"] += (fv * pix_km2).sum()
    acc["burned_cells_km2"] += cell[bm].sum(); acc["forest_burned_km2"] += (fv[bm] * pix_km2[bm]).sum()


STAGE = sys.argv[3] if len(sys.argv) > 3 else "all"
if STAGE in ("all", "caribou"):
    rows = []
    e = gpd.read_file(INP, layer="eccc_ranges").to_crs(crs)
    for _, r in e.iterrows():
        rows.append(dict(set="eccc", tid=r.CODE, name=r.HERD, **stats([r.geometry])))
    rows.append(dict(set="eccc_union", tid="ALL", name="All 51 ECCC ranges (union)", **stats(list(e.geometry))))
    print("eccc done", round(time.time() - t0), flush=True)
    q = gpd.read_file(INP, layer="qc_caribou").to_crs(crs)
    for _, r in q.iterrows():
        rows.append(dict(set="qc", tid=str(r.EO_ID), name=r.NOM_POP, **stats([r.geometry])))
    rows.append(dict(set="qc_union", tid="ALL", name="Quebec populations (union)", **stats(list(q.geometry))))
    s = gpd.read_file(INP, layer="sk_caribou").to_crs(crs)
    for _, r in s.iterrows():
        rows.append(dict(set="sk", tid=f"{r.RNGEUNIT}|{r.CONUNIT}|{r.SUBUNIT}", name=r.RNGEUNIT, **stats([r.geometry])))
    rows.append(dict(set="sk_union", tid="ALL", name="Saskatchewan units (union)", **stats(list(s.geometry))))
    p = gpd.read_file(INP, layer="parks").to_crs(crs)
    for _, r in p.iterrows():
        rows.append(dict(set="park", tid=r.CLAB_ID, name=r.NAME_E, **stats([r.geometry])))
    pd.DataFrame(rows).to_csv(os.path.join(WORK, "forest_results_caribou_parks.csv"), index=False)
    print("caribou/parks done", round(time.time() - t0), flush=True)

if STAGE in ("all", "pa"):
    # CPCAD terrestrial: block by block, reading only the PA polygons in each block (memory bounded).
    # Overlapping PA records are rasterized onto one mask per province (LOC) and one national mask,
    # so overlaps are counted once.
    from rasterio.warp import transform_bounds
    acc = {}
    T = src.transform
    for r in range(0, src.height, B):
        for c in range(0, src.width, B):
            w = Window(c, r, min(B, src.width - c), min(B, src.height - r))
            tr = src.window_transform(w)
            wb = rasterio.windows.bounds(w, T)
            bb_aea = transform_bounds(crs, "ESRI:102001", *wb, densify_pts=21)
            pa = gpd.read_file(INP, layer="cpcad_t", columns=["LOC"], bbox=bb_aea)
            if len(pa) == 0:
                continue
            pa = pa.to_crs(crs)
            pa = pa[pa.intersects(box(*wb))]
            if len(pa) == 0:
                continue
            FBLK = src.read(1, window=w)
            mi = MS.query(box(*wb), predicate="intersects")
            bm = (features.rasterize(((m3.geometry.iloc[i], 1) for i in mi), out_shape=(w.height, w.width), transform=tr, dtype="uint8")
                  if len(mi) else np.zeros((w.height, w.width), np.uint8))
            nat = np.zeros((w.height, w.width), np.uint8)
            for loc, g in pa.groupby("LOC"):
                ins = features.rasterize(((x, 1) for x in g.geometry), out_shape=(w.height, w.width), transform=tr, dtype="uint8")
                nat |= ins
                k = ("pa_prov", LOCNAME[int(loc)])
                acc.setdefault(k, dict(cells_km2=0.0, forest_km2=0.0, burned_cells_km2=0.0, forest_burned_km2=0.0))
                block_metrics(acc[k], ins, w, tr, bm)
            k = ("pa_nat", "CA")
            acc.setdefault(k, dict(cells_km2=0.0, forest_km2=0.0, burned_cells_km2=0.0, forest_burned_km2=0.0))
            block_metrics(acc[k], nat, w, tr, bm)
        print("row block", r, round(time.time() - t0), flush=True)
    rows = [dict(set=k[0], tid=k[1], name="CPCAD terrestrial", **v) for k, v in acc.items()]
    pd.DataFrame(rows).to_csv(os.path.join(WORK, "forest_results_pa.csv"), index=False)

if STAGE == "all" or os.path.exists(os.path.join(WORK, "forest_results_pa.csv")) and os.path.exists(os.path.join(WORK, "forest_results_caribou_parks.csv")):
    df = pd.concat([pd.read_csv(os.path.join(WORK, f)) for f in ("forest_results_caribou_parks.csv", "forest_results_pa.csv")])
    df.to_csv(os.path.join(WORK, "forest_results.csv"), index=False)
    print(df.to_string())
print("done", round(time.time() - t0))
