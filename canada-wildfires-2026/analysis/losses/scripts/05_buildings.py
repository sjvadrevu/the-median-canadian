"""Building exposure to 2026 fire outlines.
Footprints: Microsoft Global ML Building Footprints, release 2026-02-03 (ODbL), Canada quadkey (zoom 9) files listed in
https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv. Each tile touching a buffered outline
is streamed (gz in memory), filtered, and discarded; only buildings within 100 m of an outline are kept.
Outlines: analysis/outline-check/outline_class_2026.geojson (CWFIS M3 2026, 718 outlines). Excluded: classes
'likely agricultural or grass burn' and 'military range' (16). 'possible industrial or urban heat' (2) kept in the file but
reported separately and left out of headline totals.
A building is 'inside' if its footprint centroid falls inside an outline, 'within 100 m' if the centroid is outside every
outline but within 100 m of one (distances in EPSG:3978). Exposure, not loss.
Community label: AL_TA reserve/settlement polygon name if inside one; else StatCan 2021 population centre name if inside;
else nearest population centre or ISC First Nation point within 25 km ('near ...'); else 'no named community within 25 km'.
Fire area: data/geo/fma_v2.gpkg area containing the building."""
import gzip, io, json, math, os, sys, time
import numpy as np, pandas as pd, geopandas as gpd, requests, shapely
from shapely import STRtree

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(L))  # .../wildfire
G = os.path.join(W, "data", "geo")
WORK = os.path.join(L, "work"); os.makedirs(WORK, exist_ok=True)
EXCL = {"likely agricultural or grass burn", "military range"}

o = gpd.read_file(os.path.join(W, "analysis", "outline-check", "outline_class_2026.geojson"))
o = o[~o["class"].isin(EXCL)].copy()
o["headline"] = o["class"] != "possible industrial or urban heat"
o = o.to_crs(3978); o["geometry"] = o.geometry.make_valid()
o = o.reset_index(drop=True)
print("outlines kept", len(o), "headline", int(o.headline.sum()))
buf = o.geometry.buffer(100)
tree = STRtree(buf.values)

# quadkeys (zoom 9) touching each buffered outline (bounds in lon/lat)
def tile_xy(lon, lat, z):
    n = 2 ** z; lat = max(min(lat, 85.0511), -85.0511)
    x = int((lon + 180) / 360 * n); y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return min(x, n - 1), min(y, n - 1)
def quadkey(x, y, z):
    q = ""
    for i in range(z, 0, -1):
        d = 0; m = 1 << (i - 1)
        if x & m: d += 1
        if y & m: d += 2
        q += str(d)
    return q
b4326 = gpd.GeoSeries(buf, crs=3978).to_crs(4326)
qks = set()
for g in b4326:
    x0, y0, x1, y1 = g.bounds
    tx0, ty0 = tile_xy(x0, y1, 9); tx1, ty1 = tile_xy(x1, y0, 9)
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            qks.add(quadkey(tx, ty, 9))
links = pd.read_csv(os.path.join(L, "raw", "buildings", "dataset-links.csv"))
links = links[links.Location == "Canada"]
links["QuadKey"] = links.QuadKey.astype(str).str.zfill(9)
todo = links[links.QuadKey.isin(qks)]
print("tiles touching outlines", len(qks), "with Canada data", len(todo), "listed size", todo.Size.tolist()[:5])

done_path = os.path.join(WORK, "bldg_tiles_done.txt")
done = set(open(done_path).read().split()) if os.path.exists(done_path) else set()
parts_dir = os.path.join(WORK, "bldg_parts"); os.makedirs(parts_dir, exist_ok=True)
sess = requests.Session()
from pyproj import Transformer
tr = Transformer.from_crs(4326, 3978, always_xy=True)
t0 = time.time(); ntot = 0
for k, r in enumerate(todo.itertuples()):
    key = f"{r.QuadKey}_{r.Url.split('/')[-1][:10]}"
    if key in done: continue
    for attempt in range(4):
        try:
            resp = sess.get(r.Url, timeout=300); resp.raise_for_status(); break
        except Exception as e:
            print("retry", r.QuadKey, e); time.sleep(10 * (attempt + 1))
    else:
        print("FAILED", r.Url); continue
    raw = gzip.decompress(resp.content).decode("utf-8")
    lons, lats, areas, heights = [], [], [], []
    for line in raw.splitlines():
        if not line.strip(): continue
        f = json.loads(line)
        ring = f["geometry"]["coordinates"][0]
        a = np.asarray(ring)
        lons.append(a[:-1, 0].mean()); lats.append(a[:-1, 1].mean())
        # planar area via shoelace after projection (computed later for kept ones only)
        areas.append(ring); heights.append(f.get("properties", {}).get("height", -1))
    ntot += len(lons)
    if not lons:
        open(done_path, "a").write(key + "\n"); continue
    x, y = tr.transform(np.array(lons), np.array(lats))
    pts = shapely.points(x, y)
    pi, oi = tree.query(pts, predicate="intersects")
    if len(pi):
        df = pd.DataFrame({"pi": pi, "oi": oi})
        df["dist"] = shapely.distance(pts[df.pi.values], o.geometry.values[df.oi.values])
        df = df.sort_values(["pi", "dist"]).drop_duplicates("pi")
        keep = df.pi.values
        ar = []
        for i in keep:
            rx, ry = tr.transform(*np.asarray(areas[i]).T)
            ar.append(0.5 * abs(np.dot(rx, np.roll(ry, 1)) - np.dot(ry, np.roll(rx, 1))))
        out = pd.DataFrame({"x": x[keep], "y": y[keep], "lon": np.array(lons)[keep], "lat": np.array(lats)[keep],
                            "footprint_m2": np.round(ar, 1), "height_m": np.array(heights, dtype=float)[keep],
                            "fire_uid": o.fire_uid.values[df.oi.values], "dist_m": np.round(df.dist.values, 1),
                            "quadkey": r.QuadKey,
                            "footprint_wkt": [shapely.to_wkt(shapely.polygons(np.asarray(areas[i])), rounding_precision=6) for i in keep]})
        out.to_csv(os.path.join(parts_dir, f"{key}.csv.gz"), index=False)
    open(done_path, "a").write(key + "\n")
    if k % 10 == 0:
        print(f"{k+1}/{len(todo)} tiles, {ntot:,} buildings scanned, {time.time()-t0:.0f}s", flush=True)
print("scanned", ntot)
