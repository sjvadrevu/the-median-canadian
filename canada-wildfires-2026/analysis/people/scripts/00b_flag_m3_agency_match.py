"""Step 0b: flag each 2026 CWFIS M3 outline that has an agency-reported 2026 fire (NRCan
CWFIF fire list, fire_year 2026, 5,451 points with lat/lon) inside it or within 5 km.
Unmatched outlines are hotspot clusters with no agency record: prescribed, agricultural or
military-range burns, fires in jurisdictions that report no list (e.g. DND land), or
industrial heat sources. Used for a sensitivity version of the 2026 exposure numbers.
Output: work/fires_2026.gpkg gains column agency_match (bool) and n_agency_fires.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

f = gpd.read_file(f"{WORK}/fires_2026.gpkg")
fl = pd.DataFrame(json.load(open(f"{DATA}/fire/reference/nrcan_fire_list.json")))
fl = fl[(fl.fire_year == 2026) & fl.latitude.notna()]
pts = gpd.GeoDataFrame(fl, geometry=gpd.points_from_xy(fl.longitude, fl.latitude), crs="EPSG:4326").to_crs(ALBERS)
buf = f[["fire_idx", "geometry"]].copy()
buf["geometry"] = buf.buffer(5000)
j = gpd.sjoin(pts[["national_fire_id", "geometry"]], buf, predicate="within")
n = j.groupby("fire_idx").size()
f["n_agency_fires"] = f.fire_idx.map(n).fillna(0).astype(int)
f["agency_match"] = f.n_agency_fires > 0
f.to_file(f"{WORK}/fires_2026.gpkg", driver="GPKG")
print("outlines", len(f), "matched", int(f.agency_match.sum()),
      "area matched ha", round(f.loc[f.agency_match, "area_ha"].sum()),
      "area unmatched ha", round(f.loc[~f.agency_match, "area_ha"].sum()))
print("unmatched by prov:", f[~f.agency_match].fire_prov.value_counts().to_dict())
print("agency fire points matched to an outline:", j.national_fire_id.nunique(), "of", len(pts))
