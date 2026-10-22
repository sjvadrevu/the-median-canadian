"""Forestry and tourism jobs in census divisions (CD) touched by, or near, the 2026 and 2023-2026 fires; mills.

Jobs: 2021 Census, table 98-10-0592-01, employed labour force (place of residence), industry groups NAICS 2017:
  forestry jobs = 113 Forestry and logging + 1153 Support activities for forestry + 321 Wood product manufacturing
                  + 322 Paper manufacturing
  tourism (accommodation) jobs = 721 Accommodation services (includes 7212 RV parks and recreational camps)
  Series that StatCan does not publish for a CD (no respondents or suppressed) are treated as 0.
CD polygons: StatCan 2021 DA cartographic polygons (generalised 50 m) dissolved by CDUID (first 4 digits of DAUID).
Burned area per CD: the 240 m burned cells (work/cells.pkl) assigned to the CD containing the cell centre.
"Touched": CD contains mapped 2026 burned area of at least 100 ha (to drop slivers). "Burned >= 1%": at least 1% of
the CD's land area inside mapped burned area. "Near": CD edge within 25 km of a 2026 outline (planar distance in
ESRI:102001, under 1.4% error); "near large": same, only fires whose outlines total 1,000 ha or more per CWFIS fire
ID (removes small unmatched spring and farm burns near cities). Same touched / 1% scopes for the 2023-2026 union.
"High dependence" thresholds: forestry share of employed residents at least 3 times the national share; accommodation
share at least 3 times the national share. Both are stated in results.
Mills: NRCan "Importance of the forest industry to the regional economy" mill layer (mills_en.kml, 664 mills,
published 2016, compiled 2001-2011 from several sources); counted inside / within 1, 10, 25 km of 2026 outlines.
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio import features
from shapely import make_valid
from shapely.ops import unary_union
from ecommon import DATA, WORK, OUT, RAW, M3, EA
from grid import meta

m = meta()
from affine import Affine
T = Affine(*m["transform"])
cells = pd.read_pickle(WORK / "cells.pkl")

# --- CD polygons
da = gpd.read_file(DATA / "geo" / "statcan" / "da_2021_pop_gen50m.gpkg")
da["CDUID"] = da.DAUID.str[:4]
cd = da.dissolve(by="CDUID", aggfunc={"pop2021": "sum", "LANDAREA": "sum", "PRUID": "first"}).reset_index()
cd.to_file(WORK / "cd_2021_from_da.gpkg", driver="GPKG")
cdg = cd.to_crs(m["crs"])
cdid = np.zeros((m["H"], m["W"]), dtype="uint16")
for i, g in enumerate(cdg.geometry, start=1):
    features.rasterize([(g, i)], out=cdid, transform=T)
cells["cd_i"] = cdid.ravel()[cells.idx.values]
del cdid
cells["CDUID"] = cells.cd_i.map(dict(zip(range(1, len(cd) + 1), cd.CDUID))).fillna("none")
agg = {}
for col, sel in [("burn2026_mapped_ha", cells.b2026), ("union_2023_2026_mapped_ha", np.ones(len(cells), bool))]:
    agg[col] = cells[sel].groupby("CDUID").area_ha.sum()
agg["burn2026_scaled_ha"] = cells[cells.b2026].assign(s=lambda d: d.area_ha * d.w26).groupby("CDUID").s.sum()
agg["forest_burn2026_mapped_ha"] = cells[cells.b2026].groupby("CDUID").forest_ha.sum()
agg["forest_union_mapped_ha"] = cells.groupby("CDUID").forest_ha.sum()
b = pd.DataFrame(agg).fillna(0)
cd = cd.merge(b, left_on="CDUID", right_index=True, how="left").fillna({c: 0 for c in b.columns})
cd["land_ha"] = cd.LANDAREA * 100
cd["share_land_burned_2026"] = cd.burn2026_mapped_ha / cd.land_ha
cd["share_land_burned_2023_2026"] = cd.union_2023_2026_mapped_ha / cd.land_ha

# distance to fires
fires = gpd.read_file(M3).to_crs(EA)
f26 = unary_union([make_valid(g) for g in fires.geometry])
cde = cd.to_crs(EA)
cd["dist_2026_km"] = cde.geometry.distance(f26).values / 1000
# large fires only: CWFIS fire ID (CONSIS_ID) with total outline area of 1,000 ha or more (equal-area)
fsz = fires.groupby("CONSIS_ID").area_ha_albers.transform("sum")
f26L = unary_union([make_valid(g) for g in fires[fsz >= 1000].geometry])
cd["dist_2026_large_km"] = cde.geometry.distance(f26L).values / 1000

# --- jobs
j = pd.read_csv(RAW / "statcan" / "t9810059201_employed_by_industry_cd.csv", dtype={"geo_code": str})
j["employed"] = j.employed.fillna(0)
jw = j.pivot_table(index=["geo_code", "geo_level", "geo_name"], columns="industry_member", values="employed",
                   aggfunc="first").fillna(0).reset_index()
jw["employed_all"] = jw[3]
jw["forestry_jobs"] = jw[9] + jw[18] + jw[77] + jw[81]
jw["j113"], jw["j1153"], jw["j321"], jw["j322"] = jw[9], jw[18], jw[77], jw[81]
jw["accommodation_jobs"] = jw[390]
jw["j7212"] = jw[392]
keep = ["geo_code", "geo_level", "geo_name", "employed_all", "forestry_jobs", "j113", "j1153", "j321", "j322",
        "accommodation_jobs", "j7212"]
jw = jw[keep]
nat = jw[jw.geo_level == 0].iloc[0]
nat_f = nat.forestry_jobs / nat.employed_all
nat_a = nat.accommodation_jobs / nat.employed_all
jcd = jw[jw.geo_level == 3].rename(columns={"geo_code": "CDUID", "geo_name": "cd_name"})
cd = cd.merge(jcd.drop(columns="geo_level"), on="CDUID", how="left")
cd["forestry_share"] = cd.forestry_jobs / cd.employed_all
cd["accommodation_share"] = cd.accommodation_jobs / cd.employed_all
cd["forestry_x_national"] = cd.forestry_share / nat_f
cd["accommodation_x_national"] = cd.accommodation_share / nat_a
cd["high_forestry"] = cd.forestry_x_national >= 3
cd["high_accommodation"] = cd.accommodation_x_national >= 3
cd["touched_2026"] = cd.burn2026_mapped_ha >= 100
cd["near_2026_25km"] = cd.dist_2026_km <= 25
cd["near_2026_large_25km"] = cd.dist_2026_large_km <= 25
cd["burned_ge1pct_2026"] = cd.share_land_burned_2026 >= 0.01
cd["burned_ge1pct_2023_2026"] = cd.share_land_burned_2023_2026 >= 0.01
cd["touched_2023_2026"] = cd.union_2023_2026_mapped_ha >= 100
PR = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON", "46": "MB", "47": "SK", "48": "AB",
      "59": "BC", "60": "YT", "61": "NT", "62": "NU"}
cd["prov"] = cd.CDUID.str[:2].map(PR)
cols = ["CDUID", "cd_name", "prov", "pop2021", "land_ha", "employed_all", "forestry_jobs", "j113", "j1153", "j321",
        "j322", "accommodation_jobs", "j7212", "forestry_share", "accommodation_share", "forestry_x_national",
        "accommodation_x_national", "high_forestry", "high_accommodation", "burn2026_mapped_ha", "burn2026_scaled_ha",
        "forest_burn2026_mapped_ha", "share_land_burned_2026", "union_2023_2026_mapped_ha", "forest_union_mapped_ha",
        "share_land_burned_2023_2026", "dist_2026_km", "dist_2026_large_km", "touched_2026", "near_2026_25km",
        "near_2026_large_25km", "burned_ge1pct_2026", "touched_2023_2026", "burned_ge1pct_2023_2026"]
cdt = cd[cols].sort_values("burn2026_mapped_ha", ascending=False)
cdt.to_csv(OUT / "census_divisions_jobs_and_fire.csv", index=False)

# province summary
rows = []
for scope, sel in [("touched_2026", cdt.touched_2026), ("burned_ge1pct_2026", cdt.burned_ge1pct_2026),
                   ("near_2026_25km", cdt.near_2026_25km), ("near_2026_large_25km", cdt.near_2026_large_25km),
                   ("touched_2023_2026", cdt.touched_2023_2026), ("burned_ge1pct_2023_2026", cdt.burned_ge1pct_2023_2026)]:
    for p, g in list(cdt[sel].groupby("prov")) + [("Canada", cdt[sel])]:
        hf = g[g.high_forestry]
        ha = g[g.high_accommodation]
        rows.append(dict(scope=scope, prov=p, n_cd=len(g), employed_all=g.employed_all.sum(),
                         forestry_jobs=g.forestry_jobs.sum(), accommodation_jobs=g.accommodation_jobs.sum(),
                         n_cd_high_forestry=len(hf), forestry_jobs_in_high_forestry_cd=hf.forestry_jobs.sum(),
                         employed_in_high_forestry_cd=hf.employed_all.sum(),
                         n_cd_high_accommodation=len(ha), accommodation_jobs_in_high_accommodation_cd=ha.accommodation_jobs.sum(),
                         employed_in_high_accommodation_cd=ha.employed_all.sum(),
                         cd_high_forestry=";".join(hf.sort_values("forestry_share", ascending=False).cd_name.astype(str)),
                         cd_high_accommodation=";".join(ha.sort_values("accommodation_share", ascending=False).cd_name.astype(str))))
ps = pd.DataFrame(rows)
nat_row = dict(national_employed=nat.employed_all, national_forestry_jobs=nat.forestry_jobs,
               national_forestry_share=nat_f, national_accommodation_jobs=nat.accommodation_jobs,
               national_accommodation_share=nat_a, threshold_forestry_share=3 * nat_f,
               threshold_accommodation_share=3 * nat_a)
ps.to_csv(OUT / "jobs_by_province_fire_scope.csv", index=False)
pd.Series(nat_row).to_csv(WORK / "jobs_national_reference.csv")
jw[jw.geo_level <= 2].to_csv(OUT / "jobs_canada_provinces_2021.csv", index=False)
print(pd.Series(nat_row))
print(ps.drop(columns=["cd_high_forestry", "cd_high_accommodation"]).to_string())

# --- mills
mills = gpd.read_file(RAW / "mills" / "mills_en.kml")
mills = mills.set_geometry(gpd.points_from_xy(mills.geometry.x, mills.geometry.y), crs=4326).to_crs(EA)
mills["dist_2026_km"] = mills.geometry.distance(f26) / 1000
mills["band"] = pd.cut(mills.dist_2026_km, [-0.001, 0, 1, 10, 25, 1e9],
                       labels=["inside", "0-1 km", "1-10 km", "10-25 km", ">25 km"])
mo = mills.drop(columns="geometry")[["OBJECTID", "Mill Type", "Mill Ownership", "Mill Location", "Province", "Source",
                                     "dist_2026_km", "band"]].sort_values("dist_2026_km")
mo.to_csv(OUT / "mills_distance_to_2026_fires.csv", index=False)
print(mo[mo.dist_2026_km <= 25].to_string())
print(pd.crosstab(mo.Province, mo.band))
