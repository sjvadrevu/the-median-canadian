"""The largest and closest fires of 2023 to 2026, carry-over fires and human-caused area.

One record per fire:
  2023 to 2025: NBAC 1972-2025 (20260513) polygons of that YEAR, prescribed burns removed, grouped by YEAR and NFIREID
                (NBAC splits a fire that crosses a provincial or park boundary into several polygons with the same ID).
  2026:         CWFIS FireM3 outlines of 2026-10-20 (analysis/outline-check/outline_class_2026.geojson), classes
                "wildfire" and "wildfire (unreported in agency lists)" only.
Mapped hectares: NBAC POLY_HA summed over the fire's polygons; 2026 outline area_ha (equal-area, as mapped, not
scaled to official totals).

Agency record for each fire:
  2023 to 2025: CNFDB fire points (v20260811) of the same YEAR, prescribed removed, inside the fire or within 1 km of it;
                the point with the largest SIZE_HA labels the fire (FIRE_ID, FIRENAME).
  2026:         CWFIF 2026 fire list (season/nrcan_fire_list.json) points inside or within 5 km of the outline (same rule
                as property/scripts/15_apply_2026.py); the largest fire_size with fire_year 2026 labels the outline. An
                outline with no 2026 point but a point from an earlier fire_year takes that record (a carry-over).
                NT start dates come from the GNWT fire list (discoverydate), as in cause/scripts/03_fires.py, because
                the CWFIF list gives January 1 for every NT fire.
Name: the agency name field (CNFDB FIRENAME) when it holds one; for 2026, the names used in official event documents
(property/events_official.csv). Otherwise the fire is labelled by its fire management area (data/geo/fma_v2.gpkg, area
containing the outline's representative point) and nearest 2021 Census population centre (edge distance).
Cause: NBAC FIRECAUS (agency cause carried by NBAC) for 2023 to 2025; CWFIF national_fire_cause for 2026.
Start date: NBAC AG_SDATE (agency start date) for 2023 to 2025, else hotspot start HS_SDATE (flagged); 2026 agency
report date (NT: GNWT discovery date), else first M3 detection (flagged).
Carry-over: agency start date in an earlier calendar year than the burn year.
Buildings: Microsoft footprints (release 2026-02-03) with centroid inside or within 100 m of the fire.
  2023 to 2025: losses/work/bldg_nbac_YYYY.csv.gz (losses/scripts/05b_buildings_nbac.py) assigned to the nearest NBAC
                polygon of that year within 100 m (the same rule 05b used), then to its fire.
  2026:         losses/buildings_2026_near_outlines.gpkg (losses/scripts/05_buildings.py), wildfire classes only.
  The footprint layer post-dates 2023 to 2025, so buildings already destroyed and cleared may be missing.

Outputs (analysis/largest/):
  fires_2023_2026.csv            every fire with the fields above
  largest_top10.csv, closest_top10.csv
  carryover_by_year.csv, carryover_fires.csv
  cause_area_by_year.csv          mapped hectares by cause and year, and human share
  wainwright_official.csv         the Alberta Wildfire point record for the Oct 17, 2026 CFB Wainwright fire
  largest_outlines.geojson        outlines of the ranked fires and the Wainwright estimate (EPSG:4326, 100 m simplified)
"""
import json, os, zipfile
import numpy as np, pandas as pd, geopandas as gpd, pyogrio, shapely

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(L))
A = os.path.join(W, "analysis")
NBAC = os.path.join(W, "data", "fire", "raw", "nbac", "shp", "NBAC_merged_1972_to_2025_20260513.shp")
CNFDB_ZIP = os.path.join(W, "data", "fire", "raw", "nfdb", "NFDB_point_txt.zip")
FIRE_LIST = os.path.join(W, "data", "fire", "reference", "nrcan_fire_list.json")
NT_POINTS = os.path.join(W, "data", "fire", "raw", "provincial", "nt", "nt_fires_points_2026.json")
CRS = 3978
WILD = {"wildfire", "wildfire (unreported in agency lists)"}
CAUSE = {"Natural": "lightning", "Human": "human", "Undetermined": "undetermined",
         "natural": "lightning", "human": "human", "undetermined": "undetermined"}
# names from official event documents (property/events_official.csv, with their publishers); keyed by agency fire ID
NAMES_2026 = {"BC 2026-K51490": ("Bald Range", "summerland"), "BC 2026-K41351": ("Bradley Creek", "")}

os.makedirs(L, exist_ok=True)


T0 = __import__("time").time()


def log(*a):
    print(f"[{__import__('time').time() - T0:5.0f}s]", *a, flush=True)


# ---------------------------------------------------------------- reference layers
prov = gpd.read_file(os.path.join(W, "data", "geo", "statcan", "lpr_000b21a_e_provinces_2021.gpkg"))[["PREABBR", "geometry"]].to_crs(CRS)
ABBR = {"B.C.": "BC", "Alta.": "AB", "Sask.": "SK", "Man.": "MB", "Ont.": "ON", "Que.": "QC", "N.B.": "NB", "N.S.": "NS",
        "P.E.I.": "PE", "N.L.": "NL", "Y.T.": "YT", "N.W.T.": "NT", "Nvt.": "NU"}
prov["p"] = prov.PREABBR.map(ABBR)
prov["geometry"] = shapely.make_valid(shapely.simplify(np.asarray(prov.geometry.values, dtype=object), 200, preserve_topology=False))
fma = gpd.read_file(os.path.join(W, "data", "geo", "fma_v2.gpkg"))[["fma_id", "area_name", "province", "geometry"]].to_crs(CRS)
fma["geometry"] = shapely.make_valid(shapely.simplify(np.asarray(fma.geometry.values, dtype=object), 200, preserve_topology=False))
pc = gpd.read_file(os.path.join(W, "data", "geo", "statcan", "popcentres_2021_pop.gpkg"))[["PCNAME", "pop2021", "geometry"]].to_crs(CRS)
pc_pts = pc.copy(); pc_pts["geometry"] = pc.geometry.representative_point()
PC_TREE = shapely.STRtree(np.asarray(pc.geometry.values, dtype=object))
log("reference layers read")


def place(g):
    """province list, fire area and nearest population centre for a fire geometry (EPSG:3978)."""
    rp = g.representative_point()
    p_hit = prov[prov.intersects(g)]
    if len(p_hit) > 1:  # order by share of the fire's area
        shares = p_hit.geometry.intersection(g).area
        p_list = list(p_hit.assign(s=shares.values).sort_values("s", ascending=False).p)
    else:
        p_list = list(p_hit.p) or list(prov[prov.distance(rp) == prov.distance(rp).min()].p)
    f_hit = fma[fma.contains(rp)]
    f_name = f_hit.area_name.iloc[0] if len(f_hit) else ""
    # nearest population centre by exact edge distance, through the spatial index (same result as pc.distance(g).idxmin())
    idx, dist = PC_TREE.query_nearest(g, return_distance=True)
    i = pc.index[int(idx[0])]
    return p_list, f_name, pc.loc[i, "PCNAME"], round(float(dist[0]) / 1000)


# ---------------------------------------------------------------- NBAC 2023 to 2025
# NBAC is already in Canada Lambert (EPSG:3978 parameters). Polygons are simplified at 15 m as they are read, to fit in
# memory; areas come from POLY_HA, and building distances from the exact distances 05b stored, so the simplified shapes
# are used only to say which fire a building or agency point belongs to and to draw the map.
parts = []
for y in (2023, 2024, 2025):
    p = pyogrio.read_dataframe(NBAC, where=f"YEAR={y}",
                               columns=["YEAR", "NFIREID", "FIRECAUS", "AG_SDATE", "HS_SDATE", "POLY_HA", "ADMIN_NAME", "PRESCRIBED"])
    p = p[p.PRESCRIBED.fillna("").str.lower() != "true"].set_crs(CRS, allow_override=True)
    geo = shapely.simplify(np.asarray(p.geometry.values, dtype=object), 15, preserve_topology=False)
    inv = ~shapely.is_valid(geo)
    if inv.any():
        geo[inv] = shapely.make_valid(geo[inv])
    p["geometry"] = geo
    parts.append(p)
    log("NBAC", y, len(p), "polygons read")
nb = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=CRS)
del parts
bad = pd.Series(False, index=nb.index)
nb["YEAR"] = nb.YEAR.astype(int); nb["NFIREID"] = nb.NFIREID.astype(int)
nb["key"] = nb.YEAR.astype(str) + "_" + nb.NFIREID.astype(str)
log("NBAC 2023-2025 polygons (prescribed removed):", len(nb), "invalid repaired:", int(bad.sum()))

rows, geoms = [], {}
for key, g in nb.groupby("key", sort=False):
    big = g.loc[g.POLY_HA.idxmax()]
    geom = shapely.union_all(g.geometry.values)
    causes = set(g.FIRECAUS.dropna())
    ag = big.AG_SDATE if pd.notna(big.AG_SDATE) else (g.AG_SDATE.dropna().min() if g.AG_SDATE.notna().any() else pd.NaT)
    rows.append(dict(key=key, year=int(big.YEAR), source="NBAC", nbac_id=int(big.NFIREID), ha=float(g.POLY_HA.sum()),
                     cause=CAUSE.get(big.FIRECAUS, "undetermined"), cause_mixed=len(causes) > 1,
                     start=(pd.Timestamp(ag).date().isoformat() if pd.notna(ag) else
                            (pd.Timestamp(g.HS_SDATE.min()).date().isoformat() if g.HS_SDATE.notna().any() else "")),
                     start_basis="agency" if pd.notna(ag) else "hotspot",
                     nbac_admin=",".join(sorted(set(g.ADMIN_NAME)))))
    geoms[key] = geom
F = pd.DataFrame(rows)
log("NBAC fires:", len(F), F.groupby("year").ha.sum().round().to_dict())

# CNFDB points, same YEAR, within 1 km
zf = zipfile.ZipFile(CNFDB_ZIP)
mem = [n for n in zf.namelist() if n.startswith("NFDB_point_") and n.endswith(".txt")][0]
c = pd.read_csv(zf.open(mem), low_memory=False, encoding="utf-8-sig",
                usecols=["SRC_AGENCY", "FIRE_ID", "FIRENAME", "LATITUDE", "LONGITUDE", "YEAR", "SIZE_HA", "CAUSE", "REP_DATE", "PRESCRIBED", "CAUSE2"])
c = c[(c.YEAR >= 2023) & (c.YEAR <= 2025)]
c = c[~(c.PRESCRIBED.astype(str).str.strip().isin(["PB", "1"]) | (c.CAUSE2 == "H-PB"))]
cp = gpd.GeoDataFrame(c, geometry=gpd.points_from_xy(c.LONGITUDE, c.LATITUDE), crs=4269).to_crs(CRS)
fg = gpd.GeoDataFrame(F[["key", "year"]], geometry=[geoms[k] for k in F.key], crs=CRS)
j = gpd.sjoin(cp, fg, predicate="dwithin", distance=1000)
j = j[j.YEAR == j.year]
j["SIZE_HA"] = j.SIZE_HA.fillna(0)
n_ag = j.groupby("key").size()
n_ag1000 = j[j.SIZE_HA >= 1000].groupby("key").size()
lab = j.sort_values("SIZE_HA", ascending=False).drop_duplicates("key").set_index("key")
F["agency_id"] = F.key.map(lambda k: f"{lab.loc[k, 'SRC_AGENCY']} {str(lab.loc[k, 'FIRE_ID']).strip()}" if k in lab.index else "")
F["agency_name"] = F.key.map(lambda k: str(lab.loc[k, "FIRENAME"]).strip() if k in lab.index and pd.notna(lab.loc[k, "FIRENAME"]) else "")
F["agency_size_ha"] = F.key.map(lambda k: float(lab.loc[k, "SIZE_HA"]) if k in lab.index else np.nan)
F["agency_points"] = F.key.map(n_ag).fillna(0).astype(int)
F["agency_points_1000ha"] = F.key.map(n_ag1000).fillna(0).astype(int)
F["name_source"] = np.where(F.agency_name != "", "CNFDB FIRENAME", "")

# ---------------------------------------------------------------- 2026 outlines
o = gpd.read_file(os.path.join(A, "outline-check", "outline_class_2026.geojson"))
o = o[o["class"].isin(WILD)].to_crs(CRS).reset_index(drop=True)
o["geometry"] = o.geometry.make_valid()
fl = pd.DataFrame(json.load(open(FIRE_LIST)))
fl = fl[fl.latitude.notna()].copy()
nt = pd.DataFrame(json.load(open(NT_POINTS)))
nt_d = pd.to_datetime(nt.set_index("title").discoverydate, errors="coerce")
fl["start"] = pd.to_datetime(fl.situation_report_date, errors="coerce")
isnt = fl.agency_code == "NT"
fl.loc[isnt, "start"] = fl.loc[isnt, "agency_fire_id"].map(nt_d)
pts = gpd.GeoDataFrame(fl, geometry=gpd.points_from_xy(fl.longitude, fl.latitude), crs=4326).to_crs(CRS)
j6 = gpd.sjoin(pts, o[["fire_uid", "geometry"]], predicate="dwithin", distance=5000)
j6["cur"] = j6.fire_year == 2026
lab6 = j6.sort_values(["cur", "fire_size"], ascending=[False, False]).drop_duplicates("fire_uid").set_index("fire_uid")
r6 = []
for _, x in o.iterrows():
    u = x.fire_uid
    has = u in lab6.index
    rec = lab6.loc[u] if has else None
    aid = f"{rec.agency_code} {rec.agency_fire_id}" if has else ""
    st = rec.start if has else pd.NaT
    nm, nm_src = NAMES_2026.get(aid, ("", ""))
    r6.append(dict(key=f"2026_{u}", year=2026, source="CWFIS M3", m3_uid=int(u), ha=float(x.area_ha),
                   cause=CAUSE.get(rec.national_fire_cause, "undetermined") if has else "no agency record", cause_mixed=False,
                   start=(pd.Timestamp(st).date().isoformat() if has and pd.notna(st) else str(x.first_date)[:10]),
                   start_basis="agency" if has and pd.notna(st) else "first detection",
                   agency_fire_year=int(rec.fire_year) if has else np.nan,
                   agency_id=aid, agency_name=nm, agency_size_ha=float(rec.fire_size) if has else np.nan,
                   agency_points=int((j6.fire_uid == u).sum()), agency_points_1000ha=int(((j6.fire_uid == u) & (j6.fire_size >= 1000)).sum()),
                   name_source=("official event document" if nm else ""), outline_class=x["class"]))
    geoms[f"2026_{u}"] = x.geometry
F = pd.concat([F, pd.DataFrame(r6)], ignore_index=True)
log("2026 wildfire outlines:", len(r6), "with agency record:", sum(1 for r in r6 if r["agency_id"]))

# carry-over flag
F["start_year"] = pd.to_datetime(F.start, errors="coerce").dt.year
F["carryover"] = (F.start_basis == "agency") & (F.start_year < F.year)

# ---------------------------------------------------------------- buildings inside or within 100 m
B = {}
for y in (2023, 2024, 2025):
    b = pd.read_csv(os.path.join(A, "losses", "work", f"bldg_nbac_{y}.csv.gz"))
    sub = nb[nb.YEAR == y].reset_index(drop=True)
    tree = shapely.STRtree(sub.geometry.values)
    p = shapely.points(b.x.values, b.y.values)
    pi, oi = tree.query(p, predicate="dwithin", distance=130)  # 100 m plus slack for the 15 m simplification
    d = pd.DataFrame({"pi": pi, "oi": oi})
    d["ds"] = shapely.distance(p[d.pi.values], sub.geometry.values[d.oi.values])
    d = d.sort_values(["pi", "ds"]).drop_duplicates("pi")
    d["key"] = sub.key.values[d.oi.values]
    d["dist"] = b.dist.values[d.pi.values]  # exact distance to the nearest NBAC polygon, from 05b
    unassigned = len(b) - len(d)
    log(y, "buildings", len(b), "assigned", len(d), "unassigned", unassigned)
    for k, g in d.groupby("key"):
        B[k] = (int((g.dist <= 0).sum()), int((g.dist > 0).sum()))
b26 = pyogrio.read_dataframe(os.path.join(A, "losses", "buildings_2026_near_outlines.gpkg"), read_geometry=False,
                             columns=["fire_uid", "zone", "class"])
b26 = b26[b26["class"].isin(WILD)]
for u, g in b26.groupby("fire_uid"):
    B[f"2026_{int(u)}"] = (int((g.zone == "inside").sum()), int((g.zone != "inside").sum()))
F["bldg_inside"] = F.key.map(lambda k: B.get(k, (0, 0))[0])
F["bldg_within_100m"] = F.key.map(lambda k: B.get(k, (0, 0))[1])
F["bldg_inside_or_100m"] = F.bldg_inside + F.bldg_within_100m

# ---------------------------------------------------------------- rankings and places
F = F.sort_values("ha", ascending=False).reset_index(drop=True)
F["rank_area"] = np.arange(1, len(F) + 1)
F["rank_area_in_year"] = F.groupby("year").ha.rank(ascending=False, method="first").astype(int)
F = F.sort_values(["bldg_inside_or_100m", "ha"], ascending=False).reset_index(drop=True)
F["rank_buildings"] = np.where(F.bldg_inside_or_100m > 0, np.arange(1, len(F) + 1), 0)
sel = set(F.nsmallest(10, "rank_area").key) | set(F[F.rank_buildings.between(1, 10)].key)
largest_26 = F[F.year == 2026].nsmallest(1, "rank_area").key.iloc[0]
sel.add(largest_26)
for col in ("provinces", "fire_area", "nearest_pc", "nearest_pc_km"):
    F[col] = None
for i in F.index[F.key.isin(sel)]:
    pl, fa, nm, km = place(geoms[F.at[i, "key"]])
    F.at[i, "provinces"] = "/".join(pl); F.at[i, "fire_area"] = fa; F.at[i, "nearest_pc"] = nm; F.at[i, "nearest_pc_km"] = km
F = F.sort_values("rank_area").reset_index(drop=True)
cols = ["key", "year", "source", "nbac_id", "m3_uid", "outline_class", "ha", "rank_area", "rank_area_in_year", "rank_buildings",
        "agency_id", "agency_name", "name_source", "agency_size_ha", "agency_points", "agency_points_1000ha",
        "cause", "cause_mixed", "start", "start_basis", "agency_fire_year", "carryover",
        "bldg_inside", "bldg_within_100m", "bldg_inside_or_100m", "provinces", "fire_area", "nearest_pc", "nearest_pc_km", "nbac_admin"]
F[cols].to_csv(os.path.join(L, "fires_2023_2026.csv"), index=False, float_format="%.1f")
F[cols].nsmallest(10, "rank_area").to_csv(os.path.join(L, "largest_top10.csv"), index=False, float_format="%.1f")
F[F.rank_buildings.between(1, 10)].sort_values("rank_buildings")[cols].to_csv(os.path.join(L, "closest_top10.csv"), index=False, float_format="%.1f")

# ---------------------------------------------------------------- carry-over and cause by year
co = F.groupby("year").apply(lambda g: pd.Series(dict(fires=len(g), carryover_fires=int(g.carryover.sum()),
                                                      carryover_ha=float(g.loc[g.carryover, "ha"].sum()), total_ha=float(g.ha.sum()))),
                             include_groups=False).reset_index()
co["carryover_share"] = co.carryover_ha / co.total_ha
co.to_csv(os.path.join(L, "carryover_by_year.csv"), index=False, float_format="%.4f")
F[F.carryover][cols].sort_values(["year", "ha"], ascending=[True, False]).to_csv(os.path.join(L, "carryover_fires.csv"), index=False, float_format="%.1f")
ca = F.pivot_table(index="year", columns="cause", values="ha", aggfunc="sum", fill_value=0).reset_index()
ca["total_ha"] = ca.drop(columns="year").sum(axis=1)
ca["human_share"] = ca.human / ca.total_ha
ca.to_csv(os.path.join(L, "cause_area_by_year.csv"), index=False, float_format="%.4f")
log(co.to_string()); log(ca.to_string())

# ---------------------------------------------------------------- CFB Wainwright, Oct 17, 2026 (no official outline)
ab = json.load(open(os.path.join(A, "wainwright", "raw", "ab_feed", "Active_Mutual_Aid_Wildfires_0.geojson")))
wr = [f["properties"] for f in ab["features"] if f["properties"].get("LABEL") == "RMD-001-2026"]
pd.DataFrame(wr)[["LABEL", "FIRE_TYPE", "FIRE_STATUS", "FIRE_STATUS_DATE", "AREA_ESTIMATE", "SIZE_CLASS", "ASSESSMENT_ASSISTANCE_DATE",
                  "RESP_AREA", "LATITUDE", "LONGITUDE"]].assign(
    assessment_assistance_utc=lambda d: pd.to_datetime(d.ASSESSMENT_ASSISTANCE_DATE, unit="ms").dt.strftime("%Y-%m-%d %H:%M"),
    source="Alberta Wildfire ArcGIS feed Active_Mutual_Aid_Wildfires, read 2026-10-22").to_csv(os.path.join(L, "wainwright_official.csv"), index=False)

# ---------------------------------------------------------------- outlines for the page map
out = F[F.key.isin(sel)][["key", "year", "ha"]].copy()
gs = gpd.GeoSeries([geoms[k] for k in out.key], crs=CRS).simplify(100)
og = gpd.GeoDataFrame(out.reset_index(drop=True), geometry=gs.values, crs=CRS)
wa = gpd.read_file(os.path.join(A, "wainwright", "burn_estimate_T27.geojson")).to_crs(CRS)
wg = gpd.GeoDataFrame({"key": ["2026_wainwright_estimate"], "year": [2026], "ha": [float(wa.geometry.area.sum() / 1e4)]},
                      geometry=[shapely.union_all(wa.geometry.values)], crs=CRS)
og = pd.concat([og, wg], ignore_index=True)
og.to_crs(4326).to_file(os.path.join(L, "largest_outlines.geojson"), driver="GeoJSON", COORDINATE_PRECISION=5)
log("outlines written:", len(og))
