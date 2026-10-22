"""Step 2: per-outline evidence for all 718 CWFIS M3 2026 outlines (processed outline by
outline for the raster part), the matched sample, and the classification (rule.py).

Inputs (all official, raw):
  M3 outlines            data/fire/m3_perimeters_2026_cwfis_20261020.gpkg
  agency match flag      analysis/people/work/fires_2026.gpkg (00b_flag_m3_agency_match.py:
                         NRCan CWFIF 2026 fire-list point inside or within 5 km)
  hotspots               data/fire/cwfis_hotspots_2026_canada.csv.gz
  land cover             data/geo/landcover/landcover-2020-classification.tif (windowed reads)
  DND land               data/geo/dnd/ab_dnd_layer7.geojson, ab_dnd_layer13.geojson (Alberta
                         official polygons); data/geo/dnd/dfrp_dnd_parcels.gpkg (DFRP points)
  agency records         season/nrcan_fire_list.json (CWFIF), BC/ON/MB/AB 2026 perimeters,
                         QC 2026 points, NT 2026 points
Outputs: work/evidence_all_718.csv, outline_evidence.csv (80 unmatched + 80 sample),
         outline_class_2026.geojson
"""
import os, sys, json, gc, math
import numpy as np, pandas as pd, geopandas as gpd, shapely
import rasterio
from rasterio import features
from rasterio.windows import from_bounds
from rasterio.enums import Resampling

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule as R

B = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
OUT = f"{B}/analysis/outline-check"
WORK = f"{OUT}/work"
ALB = "ESRI:102001"
SEED = 20261021
N_SAMPLE = 80
MAX_PIX = 40_000_000   # above this, land cover is read from an overview (decimated)

# ------------------------------------------------------------------ outlines
m3 = gpd.read_file(f"{B}/data/fire/m3_perimeters_2026_cwfis_20261020.gpkg")
pf = gpd.read_file(f"{B}/analysis/people/work/fires_2026.gpkg", ignore_geometry=True)
assert len(m3) == len(pf) == 718 and (m3.UID.values == pf.fire_uid.values).all()
g = m3.to_crs(ALB)
g["geometry"] = shapely.make_valid(g.geometry.values)
g["fire_idx"] = np.arange(len(g))
g["agency_match"] = pf.agency_match.values.astype(bool)
g["n_cwfif_5km"] = pf.n_agency_fires.values
g["area_ha"] = g.geometry.area / 1e4
g["first_date"] = pd.to_datetime(g.FIRSTDATE).dt.strftime("%Y-%m-%d")
g["last_date"] = pd.to_datetime(g.LASTDATE).dt.strftime("%Y-%m-%d")
g["outline_days_span"] = (pd.to_datetime(g.LASTDATE) - pd.to_datetime(g.FIRSTDATE)).dt.total_seconds() / 86400
g["month"] = pd.to_datetime(g.FIRSTDATE).dt.month
print("unmatched", (~g.agency_match).sum(), "area ha", round(g.loc[~g.agency_match, "area_ha"].sum()))

# ------------------------------------------------------------------ matched sample
# random sample of 80 agency-matched outlines, stratified on size: quintile bins of the
# unmatched outlines' areas, 16 per bin (bin edges extended to 0 and infinity).
um = g[~g.agency_match]
edges = np.quantile(um.area_ha, [0, .2, .4, .6, .8, 1.0])
edges[0], edges[-1] = 0, np.inf
rng = np.random.default_rng(SEED)
mt = g[g.agency_match].copy()
mt["bin"] = pd.cut(mt.area_ha, edges, labels=False, include_lowest=True)
pick = []
for b in range(5):
    pool = mt.index[mt.bin == b].values
    k = min(16, len(pool))
    pick += list(rng.choice(pool, size=k, replace=False))
    print("size bin", b, f"{edges[b]:.0f}-{edges[b+1]:.0f} ha", "pool", len(pool), "picked", k)
g["group"] = np.where(~g.agency_match, "unmatched", "matched (not sampled)")
g.loc[pick, "group"] = "matched sample"
print(g.group.value_counts().to_dict())

# ------------------------------------------------------------------ hotspots
# Two hotspot sources from the same publisher (CWFIS):
#  file = cwfis_hotspots_2026_canada.csv.gz (daily CSV downloads, as specified for this task)
#  wfs  = CWFIS WFS public:hotspots archive (03_fetch_wfs_hotspots.py), which holds records
#         missing from the daily files (most VIIRS for 2026-06-29..07-02, Sentinel-3 SLSTR).
# Primary detection evidence = deduplicated UNION; file-only columns kept as sensitivity.
import glob
h = pd.read_csv(f"{B}/data/fire/cwfis_hotspots_2026_canada.csv.gz",
                usecols=["lat", "lon", "rep_date", "source", "sensor", "fuel"])
h["origin"] = "file"
wf = [pd.read_csv(f, usecols=["lat", "lon", "rep_date", "source", "sensor"])
      for f in sorted(glob.glob(f"{B}/data/fire/raw/hotspots_wfs_2026/2026*.csv"))]
w = pd.concat(wf, ignore_index=True)
w["origin"] = "wfs"; w["fuel"] = None
print("hotspot rows: file", len(h), "wfs (Canada bbox)", len(w))
h = pd.concat([h, w], ignore_index=True); del w, wf
hp = gpd.GeoDataFrame(h, geometry=gpd.points_from_xy(h.lon, h.lat), crs="EPSG:4326").to_crs(ALB)
hp["day"] = hp.rep_date.astype(str).str[:10]   # rep_date is UTC in both sources
hp["cx"] = np.floor(hp.geometry.x / 1000).astype(np.int64)
hp["cy"] = np.floor(hp.geometry.y / 1000).astype(np.int64)
j = gpd.sjoin(hp[["day", "sensor", "source", "fuel", "origin", "cx", "cy", "geometry"]],
              g[["fire_idx", "geometry"]], predicate="within")
del hp, h; gc.collect()
KEY = ["fire_idx", "sensor", "cx", "cy", "day"]
raw_n_file = j[j.origin == "file"].groupby("fire_idx").size()
raw_n_wfs = j[j.origin == "wfs"].groupby("fire_idx").size()
jd = j.drop_duplicates(KEY)                                   # union, deduplicated
jf = j[j.origin == "file"].drop_duplicates(KEY)               # file only, deduplicated
print("inside outlines raw", len(j), "dedup union", len(jd), "dedup file-only", len(jf))

def det_agg(d, sfx):
    a = d.groupby("fire_idx").agg(**{f"n_det{sfx}": ("day", "size"), f"det_days{sfx}": ("day", "nunique"),
                                    f"det_first{sfx}": ("day", "min"), f"det_last{sfx}": ("day", "max")})
    return a
g = g.join(det_agg(jd, ""), on="fire_idx").join(det_agg(jf, "_file"), on="fire_idx")
sens = jd.groupby(["fire_idx", "sensor"]).size().unstack(fill_value=0)
for s, c in [("VIIRS-I", "n_viirs"), ("MODIS", "n_modis"), ("SLSTR", "n_slstr")]:
    g[c] = g.fire_idx.map(sens[s] if s in sens else pd.Series(dtype=int)).fillna(0).astype(int)
fuel_grass_farm = jf.assign(gf=jf.fuel.isin(["O1a", "O1b", "farm", "low_veg", "non_fuel"])) \
    .groupby("fire_idx").gf.mean()
fuel_top = jf.groupby("fire_idx").fuel.agg(lambda s: s.value_counts().index[0])
g["n_hotspots_raw_file"] = g.fire_idx.map(raw_n_file).fillna(0).astype(int)
g["n_hotspots_raw_wfs"] = g.fire_idx.map(raw_n_wfs).fillna(0).astype(int)
for sfx in ("", "_file"):
    g[f"n_det{sfx}"] = g[f"n_det{sfx}"].fillna(0).astype(int)
    g[f"det_days{sfx}"] = g[f"det_days{sfx}"].fillna(0).astype(int)
g["det_span_days"] = (pd.to_datetime(g.det_last) - pd.to_datetime(g.det_first)).dt.days + 1
g["cwfis_fuel_top"] = g.fire_idx.map(fuel_top)
g["cwfis_fuel_grass_farm_share"] = g.fire_idx.map(fuel_grass_farm).round(3)
g["season_month"] = pd.to_datetime(g.det_first).dt.month.fillna(g.month).astype(int)
g["season_month_file"] = pd.to_datetime(g.det_first_file).dt.month.fillna(g.month).astype(int)
del j, jd, jf; gc.collect()

# ------------------------------------------------------------------ DND land
abd = pd.concat([gpd.read_file(f"{B}/data/geo/dnd/ab_dnd_layer7.geojson").assign(kind="Air Weapons Range")
                 .rename(columns={"AWR_NAME": "dnd_name"}),
                 gpd.read_file(f"{B}/data/geo/dnd/ab_dnd_layer13.geojson").assign(kind="Military Base")
                 .rename(columns={"MB_NAME": "dnd_name"})])[["dnd_name", "kind", "geometry"]]
abd = abd.to_crs(ALB)
abd["geometry"] = shapely.make_valid(abd.geometry.values)
ab_union = shapely.union_all(abd.geometry.values)
dfrp = gpd.read_file(f"{B}/data/geo/dnd/dfrp_dnd_parcels.gpkg")
dfrp_big = dfrp[dfrp.land_ha >= R.DFRP_MIN_HA].copy()
dfrp_big["geometry"] = dfrp_big.buffer(dfrp_big.eq_radius_m, quad_segs=32)
dfrp_union = shapely.union_all(dfrp_big.geometry.values)
dfrp_pts = dfrp.copy()

ab_share, dfrp_share, dnd_near_name, dnd_near_km, dnd_method = [], [], [], [], []
for geom, prov in zip(g.geometry.values, g.prov.values):
    a = geom.area
    ab_share.append(shapely.intersection(geom, ab_union).area / a)
    dfrp_share.append(shapely.intersection(geom, dfrp_union).area / a)
    if prov == "AB":
        d = abd.distance(geom)
        i = d.idxmin() if hasattr(d, "idxmin") else None
        dnd_near_name.append(f"{abd.dnd_name.iloc[int(np.argmin(d.values))]} (AB {abd.kind.iloc[int(np.argmin(d.values))]})")
        dnd_near_km.append(float(d.min()) / 1000)
        dnd_method.append("Alberta official DND polygons")
    else:
        d = dfrp_pts.distance(geom).values
        k = int(np.argmin(d))
        dnd_near_name.append(f"{dfrp_pts.name.iloc[k]} ({dfrp_pts.municipality.iloc[k]}, {dfrp_pts.land_ha.iloc[k]:.0f} ha)")
        dnd_near_km.append(float(d[k]) / 1000)
        dnd_method.append("DFRP parcel point + equal-area circle (proxy)")
g["dnd_share_ab_polygons"] = np.round(ab_share, 3)
g["dnd_share_dfrp_proxy"] = np.round(dfrp_share, 3)
g["dnd_share"] = np.where(g.prov == "AB", g.dnd_share_ab_polygons, g.dnd_share_dfrp_proxy)
g["dnd_method"] = dnd_method
g["dnd_nearest"] = dnd_near_name
g["dnd_nearest_km"] = np.round(dnd_near_km, 2)

# ------------------------------------------------------------------ agency records
def ms(s):
    return pd.to_datetime(s, unit="ms", errors="coerce")

src = {}
fl = pd.DataFrame(json.load(open(f"{B}/season/nrcan_fire_list.json")))
fl = fl[fl.latitude.notna()]
src["cwfif"] = gpd.GeoDataFrame(
    dict(rec_id=fl.national_fire_id.values, rec_date=pd.to_datetime(fl.situation_report_date).dt.strftime("%Y-%m-%d").values,
         rec_note=(fl.fire_year.astype(str) + " " + fl.national_fire_cause.astype(str) + " prescribed=" + fl.fire_was_prescribed.astype(str) + " " + fl.fire_size.astype(str) + " ha").values),
    geometry=gpd.points_from_xy(fl.longitude, fl.latitude), crs="EPSG:4326")
P = f"{B}/data/fire/raw/provincial"
bc = gpd.read_file(f"{P}/bc/bc_PROT_CURRENT_FIRE_POLYS_SP.geojson")
bc = bc[bc.FIRE_YEAR == 2026]
src["bc"] = gpd.GeoDataFrame(dict(rec_id=bc.FIRE_NUMBER.values, rec_date=pd.to_datetime(bc.TRACK_DATE).dt.strftime("%Y-%m-%d").values,
                                  rec_note=(bc.FIRE_SIZE_HECTARES.astype(str) + " ha; date=TRACK_DATE").values), geometry=bc.geometry.values, crs=bc.crs)
on = gpd.read_file(f"{P}/on/on_in_year_fire_perimeters.geojson")
src["on"] = gpd.GeoDataFrame(dict(rec_id=on.FIRENUMB.values, rec_date=ms(on.DATE_MAPPED).dt.strftime("%Y-%m-%d").values,
                                  rec_note=(on.FIRETYPE.astype(str) + " " + on.CUR_SIZE.round(1).astype(str) + " ha; date=DATE_MAPPED").values), geometry=on.geometry.values, crs=on.crs)
mb = gpd.read_file(f"zip://{P}/mb/MB_Forest_Fires_Shapefile.zip")
src["mb"] = gpd.GeoDataFrame(dict(rec_id=mb.FIRENUM.values, rec_date=pd.to_datetime(mb.DETDATE, format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d").values,
                                  rec_note=(mb.OPSFMSHECT.astype(str) + " ha cause " + mb.CAUSE.astype(str) + "; date=DETDATE").values), geometry=mb.geometry.values, crs=mb.crs)
ab = gpd.read_file(f"{P}/ab/ab_wildfire_perimeter_extinguished_prod.geojson")
src["ab"] = gpd.GeoDataFrame(dict(rec_id=ab.FireNumber.values, rec_date=ms(ab.ASSESSMENT_ASSISTANCE_DATE).dt.strftime("%Y-%m-%d").values,
                                  rec_note=(ab.FIRE_TYPE.astype(str) + " " + ab.SumAreaHa.astype(str) + " ha; date=assessment").values), geometry=ab.geometry.values, crs=ab.crs)
qc = gpd.read_file(f"{B}/season/perimeters/qc_points_feux_historique_2026.geojson")
qc = qc[qc.annee == 2026]
src["qc"] = gpd.GeoDataFrame(dict(rec_id=qc.numero.astype(str).values, rec_date=pd.to_datetime(qc.d_debut).dt.strftime("%Y-%m-%d").values,
                                  rec_note=(qc.cause.astype(str) + " " + qc.sup_ha.astype(str) + " ha; date=d_debut").values), geometry=qc.geometry.values, crs=qc.crs)
nt = pd.DataFrame(json.load(open(f"{P}/nt/nt_fires_points_2026.json")))
src["nt"] = gpd.GeoDataFrame(dict(rec_id=nt.title.values, rec_date=pd.to_datetime(nt.discoverydate, errors="coerce").dt.strftime("%Y-%m-%d").values,
                                  rec_note=(nt.cause.astype(str) + " " + nt.currentsize.astype(str) + " ha; date=discovery").values),
                             geometry=gpd.points_from_xy(nt.longitude, nt.latitude), crs="EPSG:4326")
POINT_SRC = {"cwfif", "qc", "nt"}
first = pd.to_datetime(g.FIRSTDATE).dt.normalize()
last = pd.to_datetime(g.LASTDATE).dt.normalize()
agency_hit = np.zeros(len(g), bool)
hit_src = [[] for _ in range(len(g))]
for name, s in src.items():
    s = s.to_crs(ALB)
    s["geometry"] = shapely.make_valid(s.geometry.values)
    s = s[~s.geometry.is_empty].reset_index(drop=True)
    jn = gpd.sjoin_nearest(g[["fire_idx", "geometry"]], s, how="left", distance_col="d_m")
    jn = jn[~jn.index.duplicated(keep="first")].reindex(g.index)
    g[f"{name}_nearest_id"] = jn.rec_id.values
    g[f"{name}_nearest_km"] = (jn.d_m / 1000).round(2).values
    g[f"{name}_nearest_date"] = jn.rec_date.values
    g[f"{name}_nearest_note"] = jn.rec_note.values
    rd = pd.to_datetime(jn.rec_date, errors="coerce")
    dd = np.where(rd < first, (rd - first).dt.days, np.where(rd > last, (rd - last).dt.days, 0))
    g[f"{name}_date_gap_days"] = pd.Series(dd, index=g.index).where(rd.notna())
    near = (jn.d_m.values <= R.AGENCY_KM * 1000)
    if name in POINT_SRC:
        near &= (np.abs(g[f"{name}_date_gap_days"].fillna(9999).values) <= R.AGENCY_DAYS)
    agency_hit |= near
    for i in np.where(near)[0]:
        hit_src[i].append(name)
    print("agency source", name, len(s), "outlines with record <=5 km (date-checked for points):", int(near.sum()),
          "of which unmatched:", int((near & ~g.agency_match.values).sum()))
g["agency_record_5km_any_source"] = agency_hit
g["agency_sources_5km"] = [",".join(x) for x in hit_src]
g["cnfdb_2026"] = "not available (CNFDB points end 2025, version 20260811)"

# ------------------------------------------------------------------ land cover, outline by outline
LC = f"{B}/data/geo/landcover/landcover-2020-classification.tif"
lc_rows = []
with rasterio.open(LC) as r:
    geoms3979 = g.to_crs(r.crs).geometry.values
    for i, geom in enumerate(geoms3979):
        minx, miny, maxx, maxy = geom.bounds
        win = from_bounds(minx - 30, miny - 30, maxx + 30, maxy + 30, r.transform).round_offsets().round_lengths()
        npx = win.width * win.height
        f = 1
        while npx / (f * f) > MAX_PIX:
            f *= 2
        h_, w_ = max(1, int(math.ceil(win.height / f))), max(1, int(math.ceil(win.width / f)))
        arr = r.read(1, window=win, out_shape=(h_, w_), resampling=Resampling.nearest)
        tr = r.window_transform(win) * rasterio.Affine.scale(win.width / w_, win.height / h_)
        inside = features.geometry_mask([geom], out_shape=arr.shape, transform=tr, invert=True)
        if inside.sum() == 0:   # tiny polygon: take centre pixel
            inside = features.geometry_mask([geom], out_shape=arr.shape, transform=tr, invert=True, all_touched=True)
        cnt = np.bincount(arr[inside], minlength=20)
        lc_rows.append(np.concatenate([cnt, [f]]))
        del arr, inside
        if i % 100 == 0:
            gc.collect(); print("land cover", i, "factor", f)
lc = np.array(lc_rows)
cnt, fac = lc[:, :20].astype(float), lc[:, 20]
land = cnt[:, 1:].sum(1) - cnt[:, R.WATER]
def share(cls):
    return np.round(cnt[:, list(cls)].sum(1) / np.where(land > 0, land, np.nan), 3)
g["lc_forest"] = share(R.FOREST)
g["lc_cropland"] = share(R.CROPLAND)
g["lc_grassland"] = share(R.GRASS)
g["lc_grassland_temperate10"] = share((10,))
g["lc_shrub"] = share(R.SHRUB)
g["lc_wetland"] = share(R.WETLAND)
g["lc_urban"] = share(R.URBAN)
g["lc_barren_snow"] = share(R.BARREN)
g["lc_water_share_of_all"] = np.round(cnt[:, R.WATER] / np.where(cnt[:, 1:].sum(1) > 0, cnt[:, 1:].sum(1), np.nan), 3)
g["lc_natural"] = share(R.NATURAL)
g["lc_agri"] = share(R.AGRI)
g["lc_urban_barren16"] = share(R.URBAN_BARREN)
g["lc_land_pixels"] = land.astype(int)
g["lc_decimation"] = fac

# ------------------------------------------------------------------ classify
for sfx in ("", "_file"):
    cls, det = [], []
    for row in g.itertuples():
        c, d = R.classify(row.dnd_share, np.nan_to_num(row.lc_urban_barren16), np.nan_to_num(row.lc_natural),
                          np.nan_to_num(row.lc_agri), getattr(row, f"det_days{sfx}"), getattr(row, f"season_month{sfx}"))
        if c == "wildfire" and not row.agency_match:
            c = "wildfire (unreported in agency lists)"
        cls.append(c); det.append(d)
    g["class" if not sfx else "class_file_only"] = cls
    g["class_detail" if not sfx else "class_detail_file_only"] = det

cols = ["fire_uid", "group", "agency_match", "n_cwfif_5km", "class", "class_detail", "prov", "month", "area_ha",
        "AREA", "HCOUNT", "CONSIS_ID", "first_date", "last_date", "outline_days_span",
        "n_hotspots_raw_file", "n_hotspots_raw_wfs", "n_det", "det_days", "det_first", "det_last", "det_span_days",
        "n_viirs", "n_modis", "n_slstr", "season_month",
        "n_det_file", "det_days_file", "det_first_file", "det_last_file", "class_file_only", "class_detail_file_only",
        "cwfis_fuel_top", "cwfis_fuel_grass_farm_share",
        "lc_forest", "lc_cropland", "lc_grassland", "lc_grassland_temperate10", "lc_shrub", "lc_wetland", "lc_urban",
        "lc_barren_snow", "lc_water_share_of_all", "lc_natural", "lc_agri", "lc_urban_barren16", "lc_land_pixels", "lc_decimation",
        "dnd_share", "dnd_method", "dnd_share_ab_polygons", "dnd_share_dfrp_proxy", "dnd_nearest", "dnd_nearest_km",
        "agency_record_5km_any_source", "agency_sources_5km"]
for name in src:
    cols += [f"{name}_nearest_id", f"{name}_nearest_km", f"{name}_nearest_date", f"{name}_date_gap_days", f"{name}_nearest_note"]
cols += ["cnfdb_2026"]
g = g.rename(columns={"UID": "fire_uid"})
g["area_ha"] = g.area_ha.round(1)
g["AREA"] = g.AREA.round(1)
g[cols].to_csv(f"{WORK}/evidence_all_718.csv", index=False)
ev = g[g.group != "matched (not sampled)"].sort_values(["group", "class", "prov", "fire_uid"], ascending=[False, True, True, True])
ev[cols].to_csv(f"{OUT}/outline_evidence.csv", index=False)

gj = g[["fire_uid", "group", "agency_match", "class", "class_detail", "prov", "first_date", "last_date", "area_ha",
        "det_days", "lc_natural", "lc_agri", "dnd_share", "geometry"]].copy()
gj["matched"] = np.where(gj.agency_match, "matched", "unmatched")
gj["geometry"] = gj.geometry.simplify(100, preserve_topology=True)
gj = gj.to_crs("EPSG:4326")
gj["geometry"] = shapely.set_precision(gj.geometry.values, 1e-5)
gj.to_file(f"{OUT}/outline_class_2026.geojson", driver="GeoJSON")
print("done", len(g), "evidence rows", len(ev))
print(pd.crosstab(g["class"], g["group"]))
