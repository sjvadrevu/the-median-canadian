"""econ2_sat_02_footprints.py: Microsoft Global ML Building Footprints (release 2026-02-03, Canada quadkey tiles; the same
source and logic as analysis/property/scripts/04_footprints.py) within BUFFER m of a job's fire polygons.
Writes footprints with WKT (EPSG:4326), centroid x/y in EPSG:3978, nearest fire_id ('aoi') and distance in m (0 = inside).
usage: python3 -I econ2_sat_02_footprints.py <job> [buffer_m=1000]  -> work/econ2_sat/fp_<job>.csv.gz"""
import gzip, json, math, os, sys, time
import numpy as np, pandas as pd, geopandas as gpd, requests, shapely
from shapely import STRtree
from pyproj import Transformer

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); AN = os.path.dirname(B)
OUT = os.path.join(B, "work", "econ2_sat")
job = sys.argv[1]; BUF = float(sys.argv[2]) if len(sys.argv) > 2 else 1000.0
links = pd.read_csv(os.path.join(AN, "losses", "raw", "buildings", "dataset-links.csv"))
links = links[links.Location == "Canada"].copy(); links["QuadKey"] = links.QuadKey.astype(str).str.zfill(9)
tr = Transformer.from_crs(4326, 3978, always_xy=True)


def tile_xy(lon, lat, z=9):
    n = 2 ** z
    return min(int((lon + 180) / 360 * n), n - 1), min(int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n), n - 1)


def quadkey(x, y, z=9):
    return "".join(str((1 if x & (1 << (i - 1)) else 0) + (2 if y & (1 << (i - 1)) else 0)) for i in range(z, 0, -1))


a = gpd.read_file(os.path.join(OUT, f"aoi_{job}.gpkg")).to_crs(3978)
a = a[~a.geometry.is_empty].reset_index(drop=True)
tree = STRtree(a.geometry.values)
qks = set()
for g in gpd.GeoSeries(a.geometry.buffer(BUF + 200).envelope, crs=3978).to_crs(4326):
    x0, y0, x1, y1 = g.bounds; tx0, ty0 = tile_xy(x0, y1); tx1, ty1 = tile_xy(x1, y0)
    qks |= {quadkey(tx, ty) for tx in range(tx0, tx1 + 1) for ty in range(ty0, ty1 + 1)}
todo = links[links.QuadKey.isin(qks)]
print(job, len(a), "polygons;", len(todo), "tile parts", flush=True)
sess, kept, n, t0 = requests.Session(), [], 0, time.time()
for r in todo.itertuples():
    for k in range(4):
        try:
            resp = sess.get(r.Url, timeout=300); resp.raise_for_status(); break
        except Exception:
            time.sleep(10 * (k + 1))
    else:
        print("FAILED", r.Url, flush=True); continue
    rings = [json.loads(l)["geometry"]["coordinates"][0] for l in gzip.decompress(resp.content).decode().splitlines() if l.strip()]
    n += len(rings)
    if not rings: continue
    c = np.array([np.asarray(rg)[:-1].mean(axis=0) for rg in rings])
    x, y = tr.transform(c[:, 0], c[:, 1]); pts = shapely.points(x, y)
    pi, oi = tree.query(pts, predicate="dwithin", distance=BUF)
    if not len(pi): continue
    df = pd.DataFrame({"pi": pi, "oi": oi})
    df["dist"] = shapely.distance(pts[df.pi.values], a.geometry.values[df.oi.values])
    df = df.sort_values(["pi", "dist"]).drop_duplicates("pi")
    kept.append(pd.DataFrame({"aoi": a.fire_id.values[df.oi], "x": x[df.pi], "y": y[df.pi], "dist": df.dist.round(1).values,
                              "footprint_wkt": [shapely.Polygon(rings[i]).wkt for i in df.pi], "tile": r.QuadKey}))
k = pd.concat(kept).drop_duplicates(["x", "y"]) if kept else pd.DataFrame(columns=["aoi", "x", "y", "dist", "footprint_wkt", "tile"])
k.to_csv(os.path.join(OUT, f"fp_{job}.csv.gz"), index=False)
print(job, "scanned", n, "kept", len(k), "within 500 m", int((k.dist <= 500).sum()), "inside", int((k.dist <= 0).sum()), f"{time.time()-t0:.0f}s", flush=True)
