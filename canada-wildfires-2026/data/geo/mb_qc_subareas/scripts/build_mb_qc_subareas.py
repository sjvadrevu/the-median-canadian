"""Build Manitoba and Quebec fire sub-area layers in the fma_all schema.
usage: python3 -I build_mb_qc_subareas.py GEO_DIR [LAYER ...]   (optional LAYER names: rebuild only those)
GEO_DIR = .../wildfire/data/geo (reads statcan/ and mb_qc_subareas/raw/, writes mb_qc_subareas/*.gpkg)

Method for every layer:
  1. read source polygons, make_valid, project to ESRI:102001 (Canada Albers Equal Area)
  2. dissolve to one row per unit
  3. resolve overlaps (a later unit loses overlap to an earlier unit; order = unit number)
  4. clip to the StatCan 2021 province polygon
  5. gaps (province minus union): pieces >= REMAINDER_MIN_KM2 become a labelled remainder row
     (only where the source genuinely does not cover that area); smaller gap pieces (digitising
     slivers along shared edges / coast) are merged into the adjacent unit (remainder included) with the longest
     shared boundary
  6. write fma_all schema: fma_id, agency, area_name, province, area_level, boundary_status,
     source, area_km2_equal_area (fma_id: 1001+ for MB layers, 2001+ for QC layers; not shared
     with fma_all ids)
"""
import sys, json, re, warnings
import pandas as pd, geopandas as gpd, shapely
from shapely.geometry import shape
from shapely import make_valid
warnings.filterwarnings("ignore")
G = sys.argv[1]
ONLY = sys.argv[2:]
OUT = f"{G}/mb_qc_subareas"
RAW = f"{OUT}/raw"
EA = "ESRI:102001"
COLS = ["fma_id", "agency", "area_name", "province", "area_level", "boundary_status", "source",
        "area_km2_equal_area", "geometry"]
REMAINDER_MIN_KM2 = 2000

prov = gpd.read_file(f"{G}/statcan/lpr_000b21a_e_provinces_2021.gpkg").to_crs(EA)
PROV = {"MB": make_valid(prov.loc[prov.PRUID == "46", "geometry"].union_all()),
        "QC": make_valid(prov.loc[prov.PRUID == "24", "geometry"].union_all())}
log = []
log_extra = []


def polys(geom):
    g = gpd.GeoSeries([geom], crs=EA).explode(index_parts=False)
    return g[g.geom_type == "Polygon"]


def finish(units, pcode, remainder_name, remainder_status, remainder_level, id0, name):
    """units: GeoDataFrame with area_name, area_level, boundary_status, source, agency (ordered)."""
    if ONLY and name not in ONLY:
        return None
    P = PROV[pcode]
    units = units.reset_index(drop=True).copy()
    units["geometry"] = units.geometry.make_valid()
    # 3. overlaps: earlier unit keeps overlap
    taken = None
    ov = 0.0
    geoms = []
    for geom in units.geometry:
        if taken is not None:
            ov += geom.intersection(taken).area
            geom = make_valid(geom.difference(taken))
        geoms.append(geom)
        taken = geom if taken is None else make_valid(taken.union(geom))
    units["geometry"] = geoms
    # 4. clip
    outside = make_valid(units.union_all()).difference(P).area
    units["geometry"] = [make_valid(g.intersection(P)) for g in units.geometry]
    # 5. gaps
    gap = make_valid(P.difference(units.union_all()))
    pieces = polys(gap)
    big = pieces[pieces.area >= REMAINDER_MIN_KM2 * 1e6]
    small = pieces[pieces.area < REMAINDER_MIN_KM2 * 1e6]
    if len(big):
        rem = make_valid(big.union_all())
        units = pd.concat([units, gpd.GeoDataFrame([{
            "agency": units.agency.iloc[0], "area_name": remainder_name, "area_level": remainder_level,
            "boundary_status": remainder_status, "source": "derived (province minus source units)",
            "geometry": rem}], crs=EA)], ignore_index=True)
        units = gpd.GeoDataFrame(units, geometry="geometry", crs=EA)
    merged_small = float(small.area.sum())
    if len(small):
        sp = gpd.GeoDataFrame({"pid": range(len(small))}, geometry=small.values, crs=EA)
        ub = gpd.GeoDataFrame({"k": units.index}, geometry=units.geometry.boundary, crs=EA)
        cand = gpd.sjoin(gpd.GeoDataFrame(sp[["pid"]], geometry=sp.buffer(1), crs=EA), ub,
                         predicate="intersects")[["pid", "k"]]
        if len(cand):
            # shared boundary length between each sliver and each touching unit
            cand["len"] = shapely.length(shapely.intersection(
                shapely.buffer(sp.geometry.values.to_numpy()[cand.pid.values], 1),
                ub.geometry.values.to_numpy()[cand.k.values]))
            best = cand.sort_values("len").groupby("pid").tail(1).set_index("pid").k
        else:
            best = pd.Series(dtype=int)
        rest = sp[~sp.pid.isin(best.index)]
        if len(rest):
            nn = gpd.sjoin_nearest(rest, gpd.GeoDataFrame({"k": units.index}, geometry=units.geometry, crs=EA))
            nn = nn.drop_duplicates("pid").set_index("pid").k
            best = pd.concat([best, nn])
        sp["k"] = sp.pid.map(best)
        for k, grp in sp.groupby("k"):
            units.at[k, "geometry"] = make_valid(shapely.union_all([units.at[k, "geometry"], *grp.geometry.values]))
    units = gpd.GeoDataFrame(units, geometry="geometry", crs=EA)
    units["province"] = pcode
    units["area_km2_equal_area"] = units.area / 1e6
    units["fma_id"] = range(id0, id0 + len(units))
    tot = units.area_km2_equal_area.sum()
    u = make_valid(units.union_all())
    chk = dict(layer=name, rows=len(units), province_km2=round(P.area / 1e6, 1), rows_sum_km2=round(tot, 1),
               diff_pct=round(100 * (tot - P.area / 1e6) / (P.area / 1e6), 4),
               residual_gap_km2=round(P.difference(u).area / 1e6, 2),
               residual_overlap_km2=round((tot * 1e6 - u.area) / 1e6, 2),
               source_overlap_resolved_km2=round(ov / 1e6, 1),
               source_outside_province_clipped_km2=round(outside / 1e6, 1),
               slivers_merged_km2=round(merged_small / 1e6, 1), slivers_merged_n=len(small),
               remainder_km2=round(big.area.sum() / 1e6, 1), all_valid=bool(units.is_valid.all()))
    log.append(chk)
    print(chk)
    units = units[COLS]
    units.to_file(f"{OUT}/{name}.gpkg", layer=name, driver="GPKG")
    units.drop(columns="geometry").to_csv(f"{OUT}/{name}_attributes.csv", index=False)
    return units


# ---------------- Manitoba ----------------
MWS = "Manitoba Wildfire Service"
s = open(f"{RAW}/mb/MB_TravelRestrictionAreas_2025.js", encoding="utf-8").read()
j = json.loads(s[s.index("{"):].rstrip().rstrip(";"))
tr = gpd.GeoDataFrame.from_features(j["features"], crs=4326).to_crs(EA)
tr["geometry"] = tr.make_valid()
r = open(f"{RAW}/mb/restrictions_2025.js", encoding="utf-8").read()
region = {int(a): reg for a, reg in re.findall(r'"area":"(\d+)",\s*"restrict":"[^"]*",\s*"region":"([A-Z/]+)"', r)}
assert len(region) == 22, region
tr["num"] = tr["AREA_NUMBE"].astype(int)
tr["region"] = tr.num.map(region)
tr = tr.dissolve("num", as_index=False, aggfunc="first").sort_values("num")
SRC_TR = ("Manitoba Wildfire Service Fire and Travel Restriction Areas, "
          "https://www.gov.mb.ca/conservation_fire/Restrictions/MB_TravelRestrictionAreas_2025.js "
          "(+ region attribute from restrictions_2025.js), retrieved 2026-10-21")
REM_MB = "Southern Manitoba outside fire and travel restriction areas"
REM_MB_STATUS = ("remainder: agricultural south not covered by MWS restriction areas "
                 "(municipal burning restrictions apply; MWS still reports fires here)")

a = tr.copy()
a["agency"] = MWS
a["area_name"] = a.apply(lambda x: f"Area {x.num} ({x.region.title()})", axis=1)
a["area_level"] = "fire and travel restriction area"
a["boundary_status"] = "official agency boundary (MWS web map GeoJSON; generalised)"
a["source"] = SRC_TR
finish(a, "MB", REM_MB, REM_MB_STATUS, "remainder", 1001, "mb_fire_restriction_areas")

NAMES = {"EAST": "Eastern Region", "WEST": "Western Region", "NORTH": "Northern Region",
         "EAST/WEST": "Eastern/Western shared (Area 8)", "WEST/NORTH": "Western/Northern shared (Area 14)"}
ORDER = ["EAST", "WEST", "NORTH", "EAST/WEST", "WEST/NORTH"]
rg = tr.dissolve("region", as_index=False)
rg["o"] = rg.region.map(ORDER.index)
rg = rg.sort_values("o")
rg["agency"] = MWS
rg["area_name"] = rg.region.map(NAMES)
rg["area_level"] = rg.region.map(lambda x: "fire region" if "/" not in x else "fire region (shared restriction area)")
rg["boundary_status"] = ("official agency boundary, derived: MWS restriction areas dissolved on their "
                         "official region attribute; region limits in the south are not published")
rg["source"] = SRC_TR
finish(rg, "MB", REM_MB, REM_MB_STATUS, "remainder", 1101, "mb_fire_regions")

fs = gpd.read_file(f"{RAW}/mb/mb_forest_sections_v5.geojson").to_crs(EA)
fs["geometry"] = fs.make_valid()
fs["name"] = fs.SEC_NAME.str.replace(r"^HIGHROCK .*", "HIGHROCK", regex=True).str.title()
fs = fs.dissolve("name", as_index=False, aggfunc={"SECTION": "min"}).sort_values(["SECTION", "name"])
fs["agency"] = "Manitoba Natural Resources and Indigenous Futures (Forestry)"
fs["area_name"] = fs["name"] + " Forest Section"
fs["area_level"] = "forest section"
fs["boundary_status"] = "official forestry administrative boundary (not a fire boundary)"
fs["source"] = ("Manitoba_Forest_Sections_Version_5, https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/"
                "services/Manitoba_Forest_Sections_Version_5/FeatureServer/1, retrieved 2026-10-21")
finish(fs, "MB", "Unassigned", "remainder", "remainder", 1201, "mb_forest_sections")

# ---------------- Quebec ----------------
SOP = "SOPFEU"


def sop(name):
    rows = json.load(open(f"{RAW}/qc/{name}.json", encoding="utf-8"))
    return gpd.GeoDataFrame([{**{k: v for k, v in r.items() if k != "geojson"},
                              "geometry": make_valid(shape(json.loads(r["geojson"])))} for r in rows],
                            crs=4326).to_crs(EA)


z = sop("zdi")
z["num"] = z.Numero.astype(int)
z = z.dissolve("num", as_index=False, aggfunc="first").sort_values("num")
z["agency"] = SOP
z["area_name"] = z.apply(lambda x: f"{x.num:02d} {x.Nom}", axis=1)
z["area_level"] = "fire danger zone (ZDI)"
z["boundary_status"] = "official agency boundary (SOPFEU web map GeoJSON; generalised)"
z["source"] = "SOPFEU zones de danger d'incendie, https://www.sopfeu.qc.ca/layers/zdi.json, retrieved 2026-10-21"
finish(z, "QC", "Far north outside SOPFEU fire danger zones (northern zone, no ZDI)",
       "remainder: north of SOPFEU fire danger zones (inside SOPFEU northern zone)", "remainder", 2001,
       "qc_sopfeu_fire_danger_zones")

I = sop("limite-intensive")
N = sop("limite-nordique")
# The SOPFEU northern-zone polygon is the province north of the intensive zone (disjoint from it).
# To avoid merging ~21,000 coastal-island slivers against two 150k-400k vertex polygons, the
# northern zone is built as province minus intensive zone; agreement with SOPFEU's own polygon is logged.
PQ = PROV["QC"]
Ig = make_valid(I.union_all())
Ng = make_valid(N.union_all())
zpi = make_valid(Ig.intersection(PQ))
nord = make_valid(PQ.difference(zpi))
if not ONLY or "qc_sopfeu_protection_zones" in ONLY:
    sym = make_valid(Ng.intersection(PQ)).symmetric_difference(nord).area / 1e6
    print({"check": "SOPFEU limite-nordique vs (province minus intensive zone)", "sym_diff_km2": round(sym, 1),
           "northern_zone_km2": round(nord.area / 1e6, 1)})
    log_extra.append(("qc_sopfeu_protection_zones", round(sym, 1)))
pz = gpd.GeoDataFrame([
    {"area_name": "Intensive protection zone (zone de protection intensive)", "geometry": zpi,
     "source": "SOPFEU https://www.sopfeu.qc.ca/layers/limite-intensive.json, retrieved 2026-10-21"},
    {"area_name": "Northern zone (zone nordique)", "geometry": nord,
     "source": "SOPFEU https://www.sopfeu.qc.ca/layers/limite-nordique.json (built as province minus intensive zone), retrieved 2026-10-21"}], crs=EA)
pz["agency"] = SOP
pz["area_level"] = "protection zone"
pz["boundary_status"] = "official agency boundary (SOPFEU web map GeoJSON)"
finish(pz, "QC", "Outside SOPFEU zones", "remainder", "remainder", 2101, "qc_sopfeu_protection_zones")

ra = sop("ra")
ra["num"] = ra.Numero.astype(int)
ra = ra.dissolve("num", as_index=False, aggfunc="first").sort_values("num")
ra["agency"] = SOP
ra["area_name"] = ra.apply(lambda x: f"{x.num:02d} {x.Nom}", axis=1)
ra["area_level"] = "administrative region"
ra["boundary_status"] = "official administrative boundary as served by SOPFEU (generalised)"
ra["source"] = "SOPFEU https://www.sopfeu.qc.ca/layers/ra.json (17 regions administratives), retrieved 2026-10-21"
finish(ra, "QC", "Unassigned", "remainder", "remainder", 2201, "qc_admin_regions")

import os
new = pd.DataFrame(log)
vp = f"{OUT}/validation.csv"
if ONLY and os.path.exists(vp):
    old = pd.read_csv(vp)
    new = pd.concat([old[~old.layer.isin(new.layer)], new], ignore_index=True)
for layer, sym in log_extra:
    new.loc[new.layer == layer, "note"] = f"SOPFEU northern-zone polygon vs built northern zone: symmetric difference {sym} km2"
new.to_csv(vp, index=False)
