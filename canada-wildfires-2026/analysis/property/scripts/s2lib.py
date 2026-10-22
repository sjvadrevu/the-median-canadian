"""Sentinel-2 L2A (AWS Earth Search STAC v1, keyless COGs) composites and per-building burn features.
Same compositing as analysis/losses/scripts/08_dnbr.py (per-pixel median of up to N lowest-cloud scenes, SCL mask
4,5,6,7 kept, reflectance = DN*1e-4 with the listed -0.1 offset not applied, see that script), but on a 10 m grid and
with NDVI (B08/B04, native 10 m) added to NBR (B8A/B12, 20 m, read by nearest neighbour onto the 10 m grid).
dNBR and dNDVI = (pre - post) * 1000, minus the median of pixels > 1 km outside the fire polygons (offset)."""
import os, math, time
import numpy as np, pandas as pd, geopandas as gpd, requests, rasterio, shapely
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling
from rasterio.transform import from_origin
from rasterio.features import rasterize
from pyproj import CRS
os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", GDAL_HTTP_MAX_RETRY="4",
                  GDAL_HTTP_RETRY_DELAY="3", VSI_CACHE="TRUE", GDAL_CACHEMAX="256")
STAC = "https://earth-search.aws.element84.com/v1/search"
VALID = np.array([4, 5, 6, 7]); RES = 10

def search(bbox, start, end, maxcc=60):
    feats, body, url = [], {"collections": ["sentinel-2-l2a"], "bbox": bbox, "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z",
                            "limit": 100, "query": {"eo:cloud_cover": {"lt": maxcc}}}, STAC
    while url:
        for k in range(4):
            try:
                r = requests.post(url, json=body, timeout=120); r.raise_for_status(); d = r.json(); break
            except Exception:
                time.sleep(5 * (k + 1))
        feats += d["features"]
        nxt = [l for l in d.get("links", []) if l.get("rel") == "next"]
        url, body = (nxt[0]["href"], nxt[0].get("body", body)) if nxt and len(feats) < 400 else (None, body)
    return feats

def _read(href, crs, tr, shape):
    with rasterio.open(href) as src, WarpedVRT(src, crs=crs, transform=tr, width=shape[1], height=shape[0], resampling=Resampling.nearest, nodata=0) as v:
        return v.read(1)

def composite(items, crs, tr, shape, nmax=6):
    """Up to nmax lowest-cloud scenes PER MGRS tile (so a window spanning several tiles is covered by each)."""
    nbrs, ndvis, used, per = [], [], [], {}
    for it in sorted(items, key=lambda f: f["properties"]["eo:cloud_cover"]):
        g = it["properties"].get("grid:code", it["id"].split("_")[1])
        if per.get(g, 0) >= nmax: continue
        try:
            a = {k: _read(it["assets"][k]["href"], crs, tr, shape) for k in ["nir08", "swir22", "scl", "red", "nir"]}
        except Exception as e:
            print("   skip", it["id"], str(e)[:100]); continue
        ok = np.isin(a["scl"], VALID) & (a["nir08"] > 0) & (a["swir22"] > 0)
        n8, s2 = np.clip(a["nir08"] * 1e-4, 1e-4, None), np.clip(a["swir22"] * 1e-4, 1e-4, None)
        ok1 = ok & ((n8 + s2) >= 0.02)
        nbr = np.where(ok1, np.clip((n8 - s2) / (n8 + s2), -1, 1), np.nan)
        if np.isfinite(nbr).mean() < 0.05: continue
        rd, ni = np.clip(a["red"] * 1e-4, 1e-4, None), np.clip(a["nir"] * 1e-4, 1e-4, None)
        ok2 = ok & (a["red"] > 0) & (a["nir"] > 0) & ((rd + ni) >= 0.02)
        nbrs.append(nbr.astype("float32")); ndvis.append(np.where(ok2, np.clip((ni - rd) / (ni + rd), -1, 1), np.nan).astype("float32"))
        used.append(it); per[g] = per.get(g, 0) + 1
    if not used: return None, None, []
    with np.errstate(all="ignore"):
        return np.nanmedian(np.stack(nbrs), 0), np.nanmedian(np.stack(ndvis), 0), used

def grid_for(geoms_3978, pad=1500):
    g4326 = gpd.GeoSeries(geoms_3978, crs=3978).to_crs(4326)
    lon0 = g4326.centroid.x.mean() if len(g4326) else 0
    utm = CRS.from_epsg(32600 + int((lon0 + 180) // 6) + 1)
    gu = gpd.GeoSeries(geoms_3978, crs=3978).to_crs(utm)
    x0, y0, x1, y1 = gu.total_bounds
    x0, y0 = math.floor((x0 - pad) / RES) * RES, math.floor((y0 - pad) / RES) * RES
    x1, y1 = math.ceil((x1 + pad) / RES) * RES, math.ceil((y1 + pad) / RES) * RES
    W_, H_ = int((x1 - x0) / RES), int((y1 - y0) / RES)
    bbox = list(gpd.GeoSeries([shapely.box(x0, y0, x1, y1)], crs=utm).to_crs(4326).total_bounds)
    return utm, from_origin(x0, y1, RES, RES), (H_, W_), bbox, (x0, y0, x1, y1)

def dnbr_pair(bbox, utm, tr, shape, post_start, post_end, pre_start=None, pre_end=None, nmax=6):
    """Post composite from [post_start, post_end]; pre composite from the same calendar window one year earlier,
    widened by 10 days each side, unless pre_start/pre_end are given. Up to nmax lowest-cloud scenes per MGRS tile."""
    post = search(bbox, post_start, post_end)
    if not post: return None
    if pre_start is None:  # the whole post window shifted back one year, widened by 10 days each side
        pre_start = (pd.Timestamp(post_start) - pd.DateOffset(years=1) - pd.Timedelta(days=10)).date()
        pre_end = (pd.Timestamp(post_end) - pd.DateOffset(years=1) + pd.Timedelta(days=10)).date()
    pre = search(bbox, pre_start, pre_end)
    nb1, nd1, u1 = composite(post, utm, tr, shape, nmax)
    nb0, nd0, u0 = composite(pre, utm, tr, shape, nmax)
    if nb1 is None or nb0 is None: return None
    scenes = [dict(period=p, scene_id=it["id"], date=it["properties"]["datetime"][:10], cloud=round(it["properties"]["eo:cloud_cover"], 2))
              for p, us in [("pre", u0), ("post", u1)] for it in us]
    return dict(dnbr=(nb0 - nb1) * 1000, dndvi=(nd0 - nd1) * 1000, nbr_post=nb1, scenes=scenes)

def offset_and_apply(res, fire_geoms_utm, tr, shape, extent):
    box = shapely.box(*extent).buffer(2000)
    # clip to the box (extent + 2 km) before buffering: identical mask inside the grid, avoids buffering huge polygons
    shapes = [(g.intersection(box).buffer(1000), 1) for g in fire_geoms_utm if g.intersects(box)]
    far = rasterize(shapes, out_shape=shape, transform=tr, fill=0, dtype="uint8") if shapes else np.zeros(shape, "uint8")
    offs = {}
    for k in ["dnbr", "dndvi"]:
        ref = res[k][(far == 0) & np.isfinite(res[k])]
        offs[k] = float(np.median(ref)) if ref.size > 500 else 0.0
        res[k] = res[k] - offs[k]
    return offs

def building_features(foot_utm, res, tr, shape, extent):
    """Per footprint: max / median of dNBR and dNDVI over 10 m pixels touched by the footprint; median of each in rings
    10-30 m and 20-60 m from the footprint centroid; share of 20-60 m ring pixels with dNBR >= 270; burn context =
    share of pixels 100-250 m from the centroid with dNBR >= 100 (USGS 'low' severity or worse)."""
    x0, y0, x1, y1 = extent; H_, W_ = shape
    out = []
    for fpoly in foot_utm:
        cx, cy = fpoly.centroid.x, fpoly.centroid.y
        c0, r0 = int((cx - x0) // RES), int((y1 - cy) // RES)
        R = 26
        rs, re_, cs, ce = max(r0 - R, 0), min(r0 + R + 1, H_), max(c0 - R, 0), min(c0 + R + 1, W_)
        f = {}
        if re_ <= rs or ce <= cs:
            out.append(f); continue
        wtr = rasterio.transform.from_origin(x0 + cs * RES, y1 - rs * RES, RES, RES)
        m = rasterize([(fpoly, 1)], out_shape=(re_ - rs, ce - cs), transform=wtr, all_touched=True, fill=0, dtype="uint8").astype(bool)
        yy, xx = np.mgrid[rs:re_, cs:ce]; d = np.hypot(x0 + (xx + 0.5) * RES - cx, y1 - (yy + 0.5) * RES - cy)
        for k in ["dnbr", "dndvi"]:
            sub = res[k][rs:re_, cs:ce]; b = sub[m]; b = b[np.isfinite(b)]
            f[k + "_bmax"] = float(b.max()) if b.size else np.nan
            f[k + "_bmed"] = float(np.median(b)) if b.size else np.nan
            for lo, hi in [(10, 30), (20, 60)]:
                rg = sub[(d >= lo) & (d <= hi) & np.isfinite(sub)]
                f[f"{k}_r{lo}_{hi}"] = float(np.median(rg)) if rg.size >= 4 else np.nan
                if k == "dnbr" and lo == 20:
                    f["dnbr_r20_60_share270"] = float((rg >= 270).mean()) if rg.size >= 4 else np.nan
            if k == "dnbr":
                an = sub[(d >= 100) & (d <= 250) & np.isfinite(sub)]
                f["dnbr_r100_250_share100"] = float((an >= 100).mean()) if an.size >= 50 else np.nan
        b = res["nbr_post"][rs:re_, cs:ce][m]; b = b[np.isfinite(b)]
        f["nbr_post_bmin"] = float(b.min()) if b.size else np.nan
        out.append(f)
    return pd.DataFrame(out)
