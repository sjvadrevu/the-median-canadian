"""Building exposure for 2023, 2024, 2025 burned areas, same method as 05_buildings.py, using NBAC 1972-2025 (20260513)
polygons of the given YEAR (PRESCRIBED burns excluded) instead of 2026 M3 outlines. Footprints: Microsoft Global ML
Building Footprints release 2026-02-03; footprints were detected on imagery of various dates, so buildings destroyed by
a 2023-2025 fire may already be missing, and the counts are exposure of the current footprint layer, not of the
pre-fire building stock. Usage: 05b_buildings_nbac.py 2023 [2024 2025]. Output: buildings_exposure_by_year_nbac.csv"""
import gzip, json, math, os, sys, time
import numpy as np, pandas as pd, geopandas as gpd, requests, shapely, pyogrio
from shapely import STRtree
from pyproj import Transformer

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(L))
NB = os.path.join(W, "data", "fire", "raw", "nbac", "shp", "NBAC_merged_1972_to_2025_20260513.shp")
links = pd.read_csv(os.path.join(L, "raw", "buildings", "dataset-links.csv"))
links = links[links.Location == "Canada"].copy(); links["QuadKey"] = links.QuadKey.astype(str).str.zfill(9)
tr = Transformer.from_crs(4326, 3978, always_xy=True)
def tile_xy(lon, lat, z=9):
    n = 2 ** z; lat = max(min(lat, 85.0511), -85.0511)
    return min(int((lon + 180) / 360 * n), n - 1), min(int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n), n - 1)
def quadkey(x, y, z=9):
    return "".join(str((1 if x & (1 << (i - 1)) else 0) + (2 if y & (1 << (i - 1)) else 0)) for i in range(z, 0, -1))
outp = os.path.join(L, "buildings_exposure_by_year_nbac.csv")
res = pd.read_csv(outp).to_dict("records") if os.path.exists(outp) else []
sess = requests.Session()
for year in [int(a) for a in sys.argv[1:]]:
    t0 = time.time()
    p = pyogrio.read_dataframe(NB, where=f"YEAR={year}", columns=["YEAR", "NFIREID", "ADMIN_NAME", "PRESCRIBED", "ADJ_HA"])
    p = p[p.PRESCRIBED.fillna("").str.lower() != "true"].to_crs(3978)
    inv = ~p.geometry.is_valid
    p.loc[inv, "geometry"] = p.loc[inv, "geometry"].buffer(0); p = p.reset_index(drop=True)
    print(year, "invalid repaired", int(inv.sum()), flush=True)
    tree = STRtree(p.geometry.values)  # queried with predicate dwithin 100 m (no polygon buffering: NBAC polygons are very large)
    qks = set()
    bnd = p.geometry.bounds.values + np.array([-200, -200, 200, 200])
    for g in gpd.GeoSeries([shapely.box(*r) for r in bnd], crs=3978).to_crs(4326):
        x0, y0, x1, y1 = g.bounds; tx0, ty0 = tile_xy(x0, y1); tx1, ty1 = tile_xy(x1, y0)
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                qks.add(quadkey(tx, ty))
    todo = links[links.QuadKey.isin(qks)]
    print(year, len(p), "polygons;", len(todo), "tiles", flush=True)
    kept = []
    for r in todo.itertuples():
        for a in range(4):
            try:
                resp = sess.get(r.Url, timeout=300); resp.raise_for_status(); break
            except Exception as e:
                time.sleep(10 * (a + 1))
        else:
            print("FAILED", r.Url); continue
        lons, lats = [], []
        for line in gzip.decompress(resp.content).decode("utf-8").splitlines():
            if line.strip():
                ring = np.asarray(json.loads(line)["geometry"]["coordinates"][0])
                lons.append(ring[:-1, 0].mean()); lats.append(ring[:-1, 1].mean())
        if not lons: continue
        x, y = tr.transform(np.array(lons), np.array(lats)); pts = shapely.points(x, y)
        pi, oi = tree.query(pts, predicate="dwithin", distance=100)
        if len(pi):
            df = pd.DataFrame({"pi": pi, "oi": oi})
            df["dist"] = shapely.distance(pts[df.pi.values], p.geometry.values[df.oi.values])
            df = df.sort_values(["pi", "dist"]).drop_duplicates("pi")
            kept.append(pd.DataFrame({"x": x[df.pi], "y": y[df.pi], "prov": p.ADMIN_NAME.values[df.oi], "dist": df.dist.values}))
    k = pd.concat(kept).drop_duplicates(["x", "y"]) if kept else pd.DataFrame(columns=["x", "y", "prov", "dist"])
    k.to_csv(os.path.join(L, "work", f"bldg_nbac_{year}.csv.gz"), index=False)
    for prov, g in list(k.groupby("prov")) + [("Canada", k)]:
        res.append(dict(year=year, prov=prov, inside=int((g.dist <= 0).sum()), within_100m=int((g.dist > 0).sum()),
                        source="NBAC 1972-2025 (20260513), YEAR polygons, prescribed excluded"))
    print(year, "inside", int((k.dist <= 0).sum()), "within 100 m", int((k.dist > 0).sum()), f"{time.time()-t0:.0f}s", flush=True)
    pd.DataFrame(res).drop_duplicates(["year", "prov"], keep="last").to_csv(outp, index=False)
