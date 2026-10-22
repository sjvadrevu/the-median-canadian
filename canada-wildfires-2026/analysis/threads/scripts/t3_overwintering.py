"""Thread 3: overwintering ("zombie") fire candidates, winters 2023-24, 2024-25, 2025-26.

Inputs
  - CWFIS hotspot archives 2023, 2024, 2025 (raw/hotspots_archive/*_slim.csv.gz, slimmed by t3a) and the 2026
    CWFIS WFS daily archive (data/fire/raw/hotspots_wfs_2026/2026*.csv, to 2026-10-21).
  - Previous-season perimeters: NBAC 2023, 2024, 2025 (analysis/people/work/fires_<y>.gpkg; prescribed removed).
  - NPRI facility locations (ECCC, 1993-present geolocations).
  - 2026 agency fire list (NRCan CWFIF, data/fire/reference/nrcan_fire_list.json).
Rules (set before results were seen)
  1. Dedupe: one detection per sensor per 1 km Albers cell per UTC day.
  2. Winter W = 1 Nov of year Y to 30 Apr of Y+1; candidates = winter detections inside or within 1 km of a
     year-Y NBAC perimeter.
  3. Industrial / persistent exclusion (any of):
     a. persistent cell: the 1 km cell or one of its 8 neighbours has detections in 3 or more of the calendar
        years 2023-2026, or has winter detections in 2 or more of the three winters;
     b. within 2 km of an NPRI facility location reported 2010 or later.
  4. Remaining candidates are linked into clusters (single linkage, 3 km) per winter = "likely holdover fires".
     Class: 'deep winter' = any detection Dec-Mar; 'November only'; 'April only'; 'Nov and Apr'.
  5. 2026 spring check: 2026 agency fires reported 1 Mar-30 Jun 2026 within 2 km of a 2025-26 cluster detection
     dated on or before the fire's report date.
"""
import glob, json
import numpy as np, pandas as pd, geopandas as gpd
from pyproj import Transformer
from shapely import STRtree, points
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
T = f"{BASE}/analysis/threads"
PW = f"{BASE}/analysis/people/work"
tr = Transformer.from_crs("EPSG:4326", "ESRI:102001", always_xy=True)

parts = []
for y in (2023, 2024, 2025):
    d = pd.read_csv(f"{T}/raw/hotspots_archive/hotspots_{y}_slim.csv.gz", usecols=["lat", "lon", "rep_date", "sensor"])
    parts.append(d)
for f in sorted(glob.glob(f"{BASE}/data/fire/raw/hotspots_wfs_2026/2026*.csv")):
    d = pd.read_csv(f, usecols=["lat", "lon", "rep_date", "sensor"])
    parts.append(d[d.lat.between(41, 84) & d.lon.between(-142, -52)])
h = pd.concat(parts, ignore_index=True); del parts
h["t"] = pd.to_datetime(h.rep_date.str[:19], errors="coerce")
h = h.dropna(subset=["t"])
x, y = tr.transform(h.lon.values, h.lat.values)
h["x"], h["y"] = x, y
h["cx"] = np.floor(x / 1000).astype(np.int32); h["cy"] = np.floor(y / 1000).astype(np.int32)
h["day"] = h.t.dt.floor("D")
n_raw = len(h)
h = h.drop_duplicates(["sensor", "cx", "cy", "day"]).reset_index(drop=True)
print("hotspots raw", n_raw, "deduped", len(h), flush=True)
h["yr"] = h.t.dt.year; h["mo"] = h.t.dt.month
h["winter"] = np.where(h.mo >= 11, h.yr, np.where(h.mo <= 4, h.yr - 1, -1))   # winter labelled by its Nov year
h.loc[~h.winter.isin([2023, 2024, 2025]), "winter"] = -1
h = h[h.t < "2026-10-21"]

# province (StatCan 2021 polygons, simplified 500 m)
prov = gpd.read_file(f"{BASE}/data/geo/statcan/lpr_000b21a_e_provinces_2021.gpkg").to_crs("ESRI:102001")
abbr = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON", "46": "MB", "47": "SK", "48": "AB",
        "59": "BC", "60": "YT", "61": "NT", "62": "NU"}
prov["prov"] = prov.PRUID.astype(str).map(abbr)
prov["geometry"] = prov.geometry.simplify(500)
# province by 1 km raster lookup (cell of the dedup grid; all_touched so coastal cells are kept)
from rasterio import features
from affine import Affine
X0, Y0 = -2600, 5000            # km
GW, GH = 5800, 4800
pid = {p: i + 1 for i, p in enumerate(prov.prov)}
pg = features.rasterize(((g, pid[p]) for g, p in zip(prov.geometry, prov.prov)), out_shape=(GH, GW),
                        transform=Affine(1000, 0, X0 * 1000, 0, -1000, Y0 * 1000), fill=0, dtype="uint8", all_touched=True)
inv = {i: p for p, i in pid.items()}
ci = h.cx.values - X0; ri = Y0 - 1 - h.cy.values
ok = (ci >= 0) & (ci < GW) & (ri >= 0) & (ri < GH)
code = np.zeros(len(h), np.uint8); code[ok] = pg[ri[ok], ci[ok]]
h["prov"] = pd.Series(code).map(inv).values
h = h[h.prov.notna()].reset_index(drop=True)
print("in Canada", len(h), flush=True)

# persistence flags per cell
cell = h.cx.astype(np.int64) * 100000 + h.cy
years_per_cell = h.groupby(cell).yr.nunique()
wint_per_cell = h[h.winter >= 0].groupby(cell[h.winter >= 0]).winter.nunique()
def neigh_max(s):
    """max of s over the 3x3 cell neighbourhood, for every cell key in s's index."""
    keys = s.index.values; cx = keys // 100000; cy = keys % 100000
    best = s.values.astype(float)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            nk = (cx + dx) * 100000 + (cy + dy)
            best = np.fmax(best, np.nan_to_num(s.reindex(nk).values.astype(float), nan=0))
    return pd.Series(best, index=keys)
yrs_n = neigh_max(years_per_cell)
win_n = neigh_max(wint_per_cell)
h["persist_years"] = cell.map(yrs_n).values
h["persist_winters"] = cell.map(win_n).fillna(0).values

# NPRI facilities
npri = pd.read_csv(f"{T}/raw/facilities/NPRI_geolocations_1993-present.csv", encoding="latin1", low_memory=False)
npri.columns = [c.split(" / ")[0].strip() for c in npri.columns]
npri["Latitude"] = pd.to_numeric(npri.Latitude, errors="coerce"); npri["Longitude"] = pd.to_numeric(npri.Longitude, errors="coerce")
npri = npri[(npri["Year of last filed report"] >= 2010) & npri.Latitude.between(41, 84) & npri.Longitude.between(-142, -52)]
fx, fy = tr.transform(npri.Longitude.values, npri.Latitude.values)
ftree = cKDTree(np.c_[fx, fy])
print("NPRI facilities used", len(npri), flush=True)

# winter candidates
w = h[h.winter >= 0].copy()
summary = []
cl_rows = []
det_rows = []
for W in (2023, 2024, 2025):
    ww = w[w.winter == W].copy()
    n_all = len(ww)
    per = gpd.read_file(f"{PW}/fires_{W}.gpkg")[["fire_uid", "fire_prov", "fire_last", "area_ha", "geometry"]]
    stree = STRtree(per.geometry.values)
    p = points(ww.x.values, ww.y.values)
    qi, gi = stree.query(p, predicate="dwithin", distance=1000)
    first = pd.Series(gi, index=qi); first = first[~first.index.duplicated()]
    ww["fire_idx"] = first.reindex(range(len(ww))).values
    ww = ww[ww.fire_idx.notna()].copy()
    n_inper = len(ww)
    dist_fac, _ = ftree.query(np.c_[ww.x.values, ww.y.values])
    ww["near_facility"] = dist_fac <= 2000
    ww["persistent"] = (ww.persist_years >= 3) | (ww.persist_winters >= 2)
    keep = ww[~ww.near_facility & ~ww.persistent].copy()
    summary.append(dict(winter=f"{W}-{str(W + 1)[2:]}", winter_detections_canada=n_all, inside_or_1km_prev_perimeter=n_inper,
                        removed_facility_2km=int(ww.near_facility.sum()), removed_persistent=int((ww.persistent & ~ww.near_facility).sum()),
                        kept_detections=len(keep)))
    if len(keep) == 0:
        continue
    # cluster 3 km single linkage
    xy = np.c_[keep.x.values, keep.y.values]
    pairs = cKDTree(xy).query_pairs(3000, output_type="ndarray")
    n = len(keep)
    g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n)) if len(pairs) else coo_matrix((n, n))
    _, lab = connected_components(g, directed=False)
    keep["cluster"] = lab
    keep["fire_uid"] = per.fire_uid.values[keep.fire_idx.astype(int).values]
    keep["fire_last"] = per.fire_last.values[keep.fire_idx.astype(int).values]
    keep["fire_area_ha"] = per.area_ha.values[keep.fire_idx.astype(int).values]
    keep["W"] = W
    det_rows.append(keep[["W", "cluster", "lat", "lon", "t", "sensor", "prov", "fire_uid", "x", "y"]])
    for c, s in keep.groupby("cluster"):
        months = set(s.mo)
        deep = bool(months & {12, 1, 2, 3})
        if deep:
            cls = "deep winter (Dec-Mar detection)"
        elif months == {11}:
            cls = "November only"
        elif months == {4}:
            cls = "April only"
        else:
            cls = "November and April only"
        cl_rows.append(dict(winter=f"{W}-{str(W + 1)[2:]}", W=W, cluster=c, prov=s.prov.mode().iloc[0], n_det=len(s), n_days=s.day.nunique(),
                            first=s.t.min(), last=s.t.max(), months=",".join(str(m) for m in sorted(months)), cls=cls,
                            lat=s.lat.mean(), lon=s.lon.mean(), x=s.x.mean(), y=s.y.mean(), prev_fire_uid=s.fire_uid.mode().iloc[0],
                            prev_fire_last=s.fire_last.iloc[0], prev_fire_ha=s.fire_area_ha.max()))
S = pd.DataFrame(summary)
C = pd.DataFrame(cl_rows)
D = pd.concat(det_rows, ignore_index=True)
S.to_csv(f"{T}/t3_winter_filter_summary.csv", index=False)
print(S.to_string(), flush=True)

# 2026 spring fires near 2025-26 clusters
fl = pd.DataFrame(json.load(open(f"{BASE}/data/fire/reference/nrcan_fire_list.json")))
fl["rep"] = pd.to_datetime(fl.situation_report_date)
fx2, fy2 = tr.transform(fl.longitude.values, fl.latitude.values)
fl["x"], fl["y"] = fx2, fy2
d25 = D[D.W == 2025].reset_index(drop=True)
dtree = cKDTree(np.c_[d25.x.values, d25.y.values]) if len(d25) else None
spring = fl[(fl.fire_year == 2026) & (fl.rep >= "2026-03-01") & (fl.rep < "2026-07-01")].copy()
matches = []
if dtree is not None:
    for i, r in spring.iterrows():
        idx = dtree.query_ball_point([r.x, r.y], 2000)
        if not idx:
            continue
        s = d25.iloc[idx]
        s = s[s.t <= r.rep + pd.Timedelta(days=1)]
        if len(s):
            matches.append(dict(national_fire_id=r.national_fire_id, agency=r.agency_code, report=r.rep, size_ha=r.fire_size,
                                cause=r.national_fire_cause, cluster=int(s.cluster.mode().iloc[0]),
                                min_dist_m=float(np.min(np.hypot(s.x - r.x, s.y - r.y))), last_winter_det=s.t.max()))
M = pd.DataFrame(matches)
M.to_csv(f"{T}/t3_spring2026_fires_near_holdovers.csv", index=False)
# agency-recognised carry-overs: fire_year 2025 records still in the 2026 list
co = fl[fl.fire_year < 2026].copy()
if len(d25):
    dd, ii = dtree.query(np.c_[co.x.values, co.y.values])
    co["nearest_2025_26_cluster_det_km"] = dd / 1000
    co["nearest_cluster"] = d25.cluster.values[ii]
co[["national_fire_id", "fire_year", "agency_code", "situation_report_date", "status_date", "stage_of_control", "national_fire_cause",
    "fire_size", "latitude", "longitude"] + (["nearest_2025_26_cluster_det_km", "nearest_cluster"] if len(d25) else [])].to_csv(
    f"{T}/t3_agency_carryover_fires_in_2026_list.csv", index=False)
if len(M):
    C["spring2026_fire_match"] = C.apply(lambda r: r.W == 2025 and r.cluster in set(M.cluster), axis=1)
C.to_csv(f"{T}/t3_holdover_clusters.csv", index=False)
D.drop(columns=["x", "y"]).to_csv(f"{T}/t3_holdover_detections.csv", index=False)
by = C.groupby(["winter", "prov", "cls"]).size().unstack(fill_value=0)
by["total"] = by.sum(axis=1)
by.to_csv(f"{T}/t3_holdover_by_winter_province.csv")
print(by.to_string())
print(C.groupby(["winter", "cls"]).agg(n=("cluster", "size"), det=("n_det", "sum")).to_string())
print("spring 2026 fires near 2025-26 clusters:", len(M)); print(M.to_string())
print("agency carry-over records:", len(co)); print(co.groupby(["fire_year", "agency_code"]).size())
if len(d25):
    print("carry-overs within 2 km of a 2025-26 cluster:", int((co.nearest_2025_26_cluster_det_km <= 2).sum()))
