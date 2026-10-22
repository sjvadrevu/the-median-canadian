"""Build data/geo/fma_v2.gpkg (layer fma_v2) and fma_v2_crosswalk.csv.

Start from fma_all.gpkg (146 rows) and:
  * drop the single Manitoba row (fma_id 94) and replace it with mb_qc_subareas/mb_fire_restriction_areas.gpkg
    (22 MWS fire and travel restriction areas + agricultural-south remainder, fma_id 1001-1023);
  * drop the single Quebec row (fma_id 92) and replace it with mb_qc_subareas/qc_sopfeu_fire_danger_zones.gpkg
    (65 SOPFEU fire danger zones + far-north remainder, fma_id 2001-2066);
  * drop the 47 Parks Canada rows (fma_id 100-146). National parks are folded into the provincial rows that
    already contain them (agency rows tile each province, parks included), so nothing else changes.
All other rows keep their fma_id (1-99 except 92 and 94). New ids come from the sub-area files, are unique and
never reuse an old id. Same schema as fma_all: fma_id, agency, area_name, province, area_level, boundary_status,
source, area_km2_equal_area. CRS ESRI:102001.
Crosswalk: one row per old id -> new id with the share of the old row's area in the new row (km2 from
area_km2_equal_area; for parks, overlap measured on the 20 m simplified copies in analysis/forest/work).
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
from pathlib import Path

G = Path(__file__).resolve().parents[1]                  # data/geo
SRC = G / "fma_all.gpkg"
MB = G / "mb_qc_subareas" / "mb_fire_restriction_areas.gpkg"
QC = G / "mb_qc_subareas" / "qc_sopfeu_fire_danger_zones.gpkg"
OUT = G / "fma_v2.gpkg"
COLS = ["fma_id", "agency", "area_name", "province", "area_level", "boundary_status", "source", "area_km2_equal_area"]

old_attr = pyogrio.read_dataframe(SRC, read_geometry=False)
keep_ids = old_attr[(old_attr.agency != "Parks Canada") & ~old_attr.fma_id.isin([92, 94])].fma_id.tolist()
parts = []
for i in keep_ids:                                        # one row at a time (some rows are very large)
    parts.append(pyogrio.read_dataframe(SRC, where=f"fma_id = {int(i)}"))
base = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=parts[0].crs)
mb = gpd.read_file(MB)
qc = gpd.read_file(QC)
assert mb.crs.equals(base.crs) and qc.crs.equals(base.crs)
v2 = gpd.GeoDataFrame(pd.concat([base[COLS + ["geometry"]], mb[COLS + ["geometry"]], qc[COLS + ["geometry"]]],
                                ignore_index=True), crs=base.crs)
v2 = v2.sort_values("fma_id").reset_index(drop=True)
assert v2.fma_id.is_unique and set(v2.fma_id).isdisjoint(set(old_attr.fma_id) - set(keep_ids))
assert v2.geometry.is_valid.all()
v2.to_file(OUT, layer="fma_v2", driver="GPKG")
v2.drop(columns="geometry").to_csv(G / "fma_v2_attributes.csv", index=False)

# province area check (agency rows of fma_all vs v2)
a_old = old_attr[old_attr.agency != "Parks Canada"].groupby("province").area_km2_equal_area.sum()
a_new = v2.groupby("province").area_km2_equal_area.sum()
chk = pd.DataFrame({"fma_all_km2": a_old, "fma_v2_km2": a_new})
chk["diff_pct"] = 100 * (chk.fma_v2_km2 / chk.fma_all_km2 - 1)
print(chk.round(4).to_string())
print("rows", len(v2), "by province", v2.province.value_counts().sort_index().to_dict())

# ---------------------------------------------------------------- crosswalk
cw = []
for r in old_attr.itertuples():
    if r.fma_id in keep_ids:
        cw.append(dict(old_fma_id=r.fma_id, old_area_name=r.area_name, old_agency=r.agency, province=r.province,
                       new_fma_id=r.fma_id, new_area_name=r.area_name, relation="unchanged",
                       share_of_old_area=1.0, overlap_km2=r.area_km2_equal_area))
    elif r.fma_id in (92, 94):
        sub = qc if r.fma_id == 92 else mb
        for s in sub.itertuples():
            cw.append(dict(old_fma_id=r.fma_id, old_area_name=r.area_name, old_agency=r.agency, province=r.province,
                           new_fma_id=s.fma_id, new_area_name=s.area_name, relation="split",
                           share_of_old_area=s.area_km2_equal_area / r.area_km2_equal_area,
                           overlap_km2=s.area_km2_equal_area))
# parks: overlap with v2 rows, on 20 m simplified copies
FW = G.parents[1] / "analysis" / "forest" / "work"
simp_old = gpd.read_file(FW / "fma_simplified.gpkg")
parks = simp_old[simp_old.agency == "Parks Canada"][["fma_id", "area_name", "province", "geometry"]]
v2s = pd.concat([simp_old[simp_old.fma_id.isin(keep_ids)][["fma_id", "area_name", "geometry"]],
                 mb[["fma_id", "area_name", "geometry"]], qc[["fma_id", "area_name", "geometry"]]], ignore_index=True)
v2s = gpd.GeoDataFrame(v2s, crs=simp_old.crs)
ov = gpd.overlay(parks.rename(columns={"fma_id": "old_fma_id", "area_name": "old_area_name"}),
                 v2s.rename(columns={"fma_id": "new_fma_id", "area_name": "new_area_name"}),
                 how="intersection", keep_geom_type=True)
ov["overlap_km2"] = ov.area / 1e6
pa = parks.set_index("fma_id").area / 1e6
ov = ov[ov.overlap_km2 > 0.01]
for r in ov.itertuples():
    cw.append(dict(old_fma_id=r.old_fma_id, old_area_name=r.old_area_name, old_agency="Parks Canada",
                   province=r.province, new_fma_id=r.new_fma_id, new_area_name=r.new_area_name,
                   relation="park removed; area lies inside this row", share_of_old_area=r.overlap_km2 / pa[r.old_fma_id],
                   overlap_km2=r.overlap_km2))
CW = pd.DataFrame(cw).sort_values(["old_fma_id", "new_fma_id"])
CW.to_csv(G / "fma_v2_crosswalk.csv", index=False)
print("crosswalk rows", len(CW), CW.relation.value_counts().to_dict())
print("parks covered", CW[CW.old_agency == "Parks Canada"].old_fma_id.nunique(), "of", len(parks),
      "; share sums min", round(CW[CW.old_agency == "Parks Canada"].groupby("old_fma_id").share_of_old_area.sum().min(), 4))
