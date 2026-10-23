"""Step 2: nearest 2026 fire outline (CWFIS M3, 2026-10-20) for all 1,026 StatCan 2021
population centres (PC, dissolved by PCUID).
  d_edge_km   = geodesic distance from the PC boundary to the nearest fire outline
                (0 = a fire outline touches or overlaps the PC polygon)
  d_centre_km = geodesic distance from the PC representative point (inside the polygon)
  nearest_fire_agency_match = an agency-reported 2026 fire lies inside/within 5 km of it
  nearest_agency_matched_fire_edge_km = same distance using only agency-matched outlines
  direction   = 8-point compass bearing from the representative point to the nearest
                point of that fire outline.
Rebuild 2026-10-21: the 13 outlines flagged exclude_from_distance (00c_outline_class.py: agricultural/grass or
military-range burns with no agency-reported fire) are dropped; nearest_fire_outline_class gives the class.
Output: city_nearest_fire.csv (all PCs, rank by 2021 population, top30 flag)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

pc = gpd.read_file(f"{DATA}/geo/statcan/popcentres_2021_pop.gpkg").to_crs(ALBERS)
pc["geometry"] = shapely.make_valid(pc.geometry.values)
pc = pc.sort_values("pop2021", ascending=False).reset_index(drop=True)
pc["pop_rank_2021"] = np.arange(1, len(pc) + 1)
pc["prov"] = pc.PRUID.astype(str).map(lambda s: ",".join(PR_ABBR[p.strip()] for p in s.split(",")))
fires = gpd.read_file(f"{WORK}/fires_2026.gpkg")
fires = fires[~fires.exclude_from_distance.astype(bool)].reset_index(drop=True)
fires["fire_idx"] = np.arange(len(fires))

ne = nearest_fire(pc, fires)
fm = fires[fires.agency_match].reset_index(drop=True)
fm["fire_idx"] = np.arange(len(fm))
nm = nearest_fire(pc, fm)
rp = pc.copy()
rp["geometry"] = pc.geometry.representative_point()
nc = nearest_fire(rp, fires)

# direction from representative point to nearest point of the edge-nearest fire
fi = fires.set_index("fire_uid")
tgt = fi.loc[ne["fire_uid"].values, "geometry"].values
lines = shapely.shortest_line(rp.geometry.values, tgt)
co = shapely.get_coordinates(lines).reshape(-1, 2, 2)
tr = Transformer.from_crs(ALBERS, "EPSG:4326", always_xy=True)
lo1, la1 = tr.transform(co[:, 0, 0], co[:, 0, 1]); lo2, la2 = tr.transform(co[:, 1, 0], co[:, 1, 1])
az, _, _ = GEOD.inv(lo1, la1, lo2, la2)
pts8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
dirn = [pts8[int(((a % 360) + 22.5) // 45) % 8] for a in az]

out = pd.DataFrame({
    "pcuid": pc.PCUID, "name": pc.PCNAME, "prov": pc.prov, "pop2021": pc.pop2021.astype(int),
    "pop_rank_2021": pc.pop_rank_2021, "top30": pc.pop_rank_2021 <= 30,
    "lon": np.round(lo1, 4), "lat": np.round(la1, 4),
    "nearest_fire_edge_km": ne.d_km.round(1).values,
    "nearest_fire_centre_km": nc.d_km.round(1).values,
    "direction_from_centre": dirn,
    "nearest_fire_uid": ne.fire_uid.values, "nearest_fire_prov": ne.fire_prov.values,
    "nearest_fire_first_detected": ne.fire_first.values, "nearest_fire_last_detected": ne.fire_last.values,
    "nearest_fire_outline_ha": fi.loc[ne.fire_uid.values, "area_ha"].round(0).values,
    "nearest_fire_agency_match": fi.loc[ne.fire_uid.values, "agency_match"].values,
    "nearest_fire_outline_class": fi.loc[ne.fire_uid.values, "outline_class"].values,
    "nearest_agency_matched_fire_edge_km": nm.d_km.round(1).values,
    "same_fire_for_centre": (nc.fire_uid.values == ne.fire_uid.values),
})
out.to_csv(f"{OUT}/city_nearest_fire.csv", index=False)
pd.set_option("display.width", 250)
print(out[out.top30][["pop_rank_2021", "name", "prov", "nearest_fire_edge_km", "nearest_fire_centre_km",
                      "direction_from_centre", "nearest_fire_prov", "nearest_fire_first_detected"]].to_string())
for t in (0, 10, 25, 50, 100):
    s = out[out.nearest_fire_edge_km <= t]
    print(f"PCs with fire outline within {t} km of edge: {len(s)} ; pop {s.pop2021.sum():,}")
print("top30 where nearest outline has no agency match:", out[out.top30 & ~out.nearest_fire_agency_match][["name","nearest_fire_edge_km","nearest_agency_matched_fire_edge_km"]].to_string())
print(out.sort_values("nearest_fire_edge_km").head(15)[["name", "prov", "pop2021", "nearest_fire_edge_km", "nearest_fire_centre_km"]].to_string())
