"""Burn severity at buildings from Sentinel-2 L2A (AWS Earth Search STAC v1, collection sentinel-2-l2a, keyless COGs).
For each fire with >= 10 buildings inside (from buildings_exposure_by_fire.csv), or a fire given on the command line:
  * window = bounding box of the fire's buildings (inside or within 100 m) + 1.5 km, on a 20 m UTM grid.
  * POST period: 2026 scenes dated after the fire's last hotspot detection if any exist before 2026-10-20, otherwise the
    latest 30 days available; PRE period: the same calendar window one year earlier (2025), so phenology matches
    (anniversary pairing). Up to 6 lowest-cloud scenes per period intersecting the window are read.
  * Per-pixel median composite of NBR = (B8A - B12) / (B8A + B12) over pixels valid in the SCL layer
    (classes 4 vegetation, 5 not-vegetated, 6 water, 7 unclassified kept; 0,1,2,3,8,9,10,11 masked). Reflectance =
    DN * 0.0001 (the listed -0.1 offset is not present in the pixel values, see composite()), floored at 0.0001; pixels with B8A + B12 < 0.02 masked.
  * dNBR = (NBR_pre - NBR_post) * 1000, minus an offset = median dNBR of window pixels > 1 km outside every 2026 outline
    (MTBS practice, removes inter-year differences unrelated to fire).
Severity classes (Key and Benson 2006, FIREMON / USGS, dNBR x1000): < -100 enhanced regrowth; -100 to 99 unburned;
100-269 low; 270-439 moderate-low; 440-659 moderate-high; >= 660 high.
Building classes (our estimate, not an official count):
  likely destroyed      : dNBR at the building (max of the 20 m pixels its footprint touches) >= 440 AND median dNBR
                          of the 20-60 m ring around it >= 270
  damaged surroundings  : not 'likely destroyed' and ring median >= 100 (vegetation around the building burned)
  unburned              : ring median < 100 and building dNBR < 270
  no clear data         : no valid pre or post composite at the building
Scene ids and dates for every fire go to dnbr_scenes.csv."""
import os, sys, json, math, time
import numpy as np, pandas as pd, geopandas as gpd, requests, rasterio, shapely
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling
from rasterio.transform import from_origin
from rasterio.features import rasterize
from pyproj import CRS

os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
                  GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="3", VSI_CACHE="TRUE", GDAL_CACHEMAX="256")
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(L))
STAC = "https://earth-search.aws.element84.com/v1/search"
VALID_SCL = np.array([4, 5, 6, 7])
END = pd.Timestamp("2026-10-20")

b = gpd.read_file(os.path.join(L, "buildings_2026_near_outlines.gpkg"))
fp = pd.read_csv(os.path.join(L, "work", "building_footprints_wkt.csv.gz"))
for d_ in (b, fp):
    d_["xk"] = d_.x.round(1); d_["yk"] = d_.y.round(1)
b = b.merge(fp.drop(columns=["x", "y"]), on=["fire_uid", "xk", "yk"], how="left")
print("footprints matched", b.footprint_wkt.notna().mean())
fx = pd.read_csv(os.path.join(L, "buildings_exposure_by_fire.csv"))
outl = gpd.read_file(os.path.join(W, "analysis", "outline-check", "outline_class_2026.geojson"))
fires = [int(a) for a in sys.argv[1:]] or fx[fx.inside >= 10].sort_values("inside", ascending=False).fire_uid.tolist()
print("fires", fires)

def search(bbox, start, end):
    feats, body = [], {"collections": ["sentinel-2-l2a"], "bbox": bbox, "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z",
                       "limit": 100, "query": {"eo:cloud_cover": {"lt": 60}}}
    url = STAC
    while url:
        r = requests.post(url, json=body, timeout=120); r.raise_for_status(); d = r.json()
        feats += d["features"]
        nxt = [l for l in d.get("links", []) if l.get("rel") == "next"]
        if nxt and len(feats) < 400:
            url = nxt[0]["href"]; body = nxt[0].get("body", body)
        else:
            url = None
    return feats

def composite(items, dst_crs, transform, shape):
    stack, used = [], []
    for it in items:
        try:
            arrs = {}
            for k in ["nir08", "swir22", "scl"]:
                a = it["assets"][k]
                with rasterio.open(a["href"]) as src, WarpedVRT(src, crs=dst_crs, transform=transform, width=shape[1], height=shape[0],
                                                                 resampling=Resampling.nearest, nodata=0) as v:
                    arrs[k] = v.read(1)
            rb = it["assets"]["nir08"].get("raster:bands", [{}])[0]
            # The STAC metadata lists offset -0.1, but the COG pixel values do not carry it: with the offset, 5-25% of
            # B12 pixels over vegetation become negative (checked on S2B_10UGV_20250923 and S2B_10UGV_20260928).
            # NBR is a ratio, so only scale 0.0001 is applied and the offset is ignored.
            sc, off = rb.get("scale", 1e-4), 0.0
            nir = np.clip(arrs["nir08"] * sc + off, 1e-4, None); sw = np.clip(arrs["swir22"] * sc + off, 1e-4, None)
            # mask SCL clouds/shadow/snow, nodata, and very dark pixels (nir + swir < 0.02) where the ratio is unstable
            ok = np.isin(arrs["scl"], VALID_SCL) & (arrs["nir08"] > 0) & (arrs["swir22"] > 0) & ((nir + sw) >= 0.02)
            nbr = np.where(ok, np.clip((nir - sw) / (nir + sw), -1, 1), np.nan)
            if np.isfinite(nbr).mean() < 0.05:
                continue
            stack.append(nbr.astype("float32")); used.append(it)
        except Exception as e:
            print("   skip", it["id"], str(e)[:120])
    if not stack:
        return None, []
    with np.errstate(all="ignore"):
        return np.nanmedian(np.stack(stack), axis=0), used

def classify(v):
    return np.select([v < -100, v < 100, v < 270, v < 440, v < 660], ["enhanced regrowth", "unburned", "low", "moderate-low", "moderate-high"], "high")

scene_rows, bres = [], []
for fid in fires:
    t0 = time.time()
    fb = b[b.fire_uid == fid].copy()
    o = outl[outl.fire_uid == fid].iloc[0]
    g4326 = fb.to_crs(4326)
    lon0, lat0 = g4326.geometry.x.mean(), g4326.geometry.y.mean()
    utm = CRS.from_epsg(32600 + int((lon0 + 180) // 6) + 1)
    fu = fb.to_crs(utm)
    x0, y0, x1, y1 = fu.total_bounds; pad = 1500
    x0, y0 = math.floor((x0 - pad) / 20) * 20, math.floor((y0 - pad) / 20) * 20
    x1, y1 = math.ceil((x1 + pad) / 20) * 20, math.ceil((y1 + pad) / 20) * 20
    W_, H_ = int((x1 - x0) / 20), int((y1 - y0) / 20)
    tr = from_origin(x0, y1, 20, 20)
    bbox = list(gpd.GeoSeries([shapely.box(x0, y0, x1, y1)], crs=utm).to_crs(4326).total_bounds)
    last = pd.Timestamp(o.last_date)
    post_start = min(last + pd.Timedelta(days=1), END - pd.Timedelta(days=30))
    post = search(bbox, post_start.date(), END.date())
    post = sorted(post, key=lambda f: f["properties"]["eo:cloud_cover"])[:6]
    p_dates = sorted(pd.Timestamp(f["properties"]["datetime"][:10]) for f in post)
    if not p_dates:
        print("no post scenes", fid); continue
    pre_s, pre_e = p_dates[0] - pd.DateOffset(years=1) - pd.Timedelta(days=10), p_dates[-1] - pd.DateOffset(years=1) + pd.Timedelta(days=10)
    pre = search(bbox, pre_s.date(), pre_e.date())
    pre = sorted(pre, key=lambda f: f["properties"]["eo:cloud_cover"])[:6]
    nbr_post, used_post = composite(post, utm, tr, (H_, W_))
    nbr_pre, used_pre = composite(pre, utm, tr, (H_, W_))
    for per, used in [("pre", used_pre), ("post", used_post)]:
        for it in used:
            scene_rows.append(dict(fire_uid=fid, period=per, scene_id=it["id"], date=it["properties"]["datetime"][:10],
                                   scene_cloud_cover_pct=round(it["properties"]["eo:cloud_cover"], 2), mgrs=it["properties"].get("grid:code")))
    if nbr_post is None or nbr_pre is None:
        print("missing composite", fid); continue
    dnbr = (nbr_pre - nbr_post) * 1000
    # offset from pixels > 1 km outside all 2026 outlines
    ol = outl.to_crs(utm)
    far = rasterize([(g.buffer(1000), 1) for g in ol.geometry if g.intersects(shapely.box(x0, y0, x1, y1).buffer(2000))],
                    out_shape=(H_, W_), transform=tr, fill=0, dtype="uint8")
    ref = dnbr[(far == 0) & np.isfinite(dnbr)]
    offset = float(np.median(ref)) if ref.size > 200 else 0.0
    dn = dnbr - offset
    # per building: footprint pixels (all touched) and 20-60 m ring
    fu = fu.reset_index(drop=True)
    foot = gpd.GeoSeries.from_wkt(fu.footprint_wkt.where(fu.footprint_wkt.notna(), None), crs=4326, on_invalid="ignore").to_crs(utm)
    foot = foot.where(foot.notna() & ~foot.is_empty, fu.geometry.buffer(5))
    rows, cols = np.indices((H_, W_)); px = x0 + (cols + 0.5) * 20; py = y1 - (rows + 0.5) * 20
    for i, r in fu.iterrows():
        fpoly = foot.iloc[i]
        m = rasterize([(fpoly, 1)], out_shape=(H_, W_), transform=tr, all_touched=True, fill=0, dtype="uint8").astype(bool)
        bx = dn[m]; bx = bx[np.isfinite(bx)]
        cx, cy = fpoly.centroid.x, fpoly.centroid.y
        c0, r0 = int((cx - x0) // 20), int((y1 - cy) // 20)
        rs, re_ = max(r0 - 4, 0), min(r0 + 5, H_); cs, ce = max(c0 - 4, 0), min(c0 + 5, W_)
        sub = dn[rs:re_, cs:ce]; d = np.hypot(px[rs:re_, cs:ce] - cx, py[rs:re_, cs:ce] - cy)
        ring = sub[(d >= 20) & (d <= 60) & np.isfinite(sub)]
        bmax = float(bx.max()) if bx.size else np.nan
        rmed = float(np.median(ring)) if ring.size >= 4 else np.nan
        if np.isnan(bmax) or np.isnan(rmed): cls = "no clear data"
        elif bmax >= 440 and rmed >= 270: cls = "likely destroyed"
        elif rmed >= 100: cls = "damaged surroundings"
        elif bmax < 270: cls = "unburned"
        else: cls = "damaged surroundings"
        bres.append(dict(fire_uid=fid, x=r.x, y=r.y, lon=g4326.geometry.x.iloc[i], lat=g4326.geometry.y.iloc[i], zone=r.zone,
                         community=r.community, community_group=r.community_group, prov=r.prov,
                         dnbr_building_max=round(bmax, 1) if bmax == bmax else None, dnbr_ring_median=round(rmed, 1) if rmed == rmed else None,
                         severity_building=str(classify(np.array([bmax]))[0]) if bmax == bmax else None,
                         severity_ring=str(classify(np.array([rmed]))[0]) if rmed == rmed else None, building_class=cls, dnbr_offset=round(offset, 1)))
    # save a small dNBR raster per fire for checking
    with rasterio.open(os.path.join(L, "work", f"dnbr_{fid}.tif"), "w", driver="GTiff", height=H_, width=W_, count=1, dtype="int16",
                       crs=utm, transform=tr, nodata=-32768, compress="deflate") as dst:
        dst.write(np.where(np.isfinite(dn), np.round(dn), -32768).astype("int16"), 1)
    bb = pd.DataFrame([x for x in bres if x["fire_uid"] == fid])
    print(fid, f"{len(fb)} bldgs, grid {W_}x{H_}, post {len(used_post)} pre {len(used_pre)}, offset {offset:.0f}, {time.time()-t0:.0f}s",
          bb.building_class.value_counts().to_dict(), flush=True)

new = pd.DataFrame(bres); sc = pd.DataFrame(scene_rows)
pb, ps = os.path.join(L, "dnbr_buildings.csv"), os.path.join(L, "dnbr_scenes.csv")
if sys.argv[1:] and os.path.exists(pb):
    new = pd.concat([pd.read_csv(pb).query("fire_uid not in @fires"), new]); sc = pd.concat([pd.read_csv(ps).query("fire_uid not in @fires"), sc])
new.to_csv(pb, index=False); sc.to_csv(ps, index=False)
