"""Step 0c (rebuild 2026-10-21): attach the outline class from analysis/outline-check/outline_class_2026.geojson
(all 718 CWFIS M3 2026 outlines, pre-registered evidence rule) to work/fires_2026.gpkg.

New columns: outline_class, exclude_from_distance.
exclude_from_distance = class is "likely agricultural or grass burn" or "military range" AND the outline has no
agency-reported fire within 5 km (agency_match False). That is the 13 non-wildfire outlines among the 80
unmatched ones. The 3 agency-matched outlines that the rule also places in those classes (two CFB Gagetown
fires listed by New Brunswick, one Saskatchewan fire on cropland) are agency-reported fires and stay in.
Excluded outlines are dropped only from distance-to-people analyses (02y for 2026, 02, 07); burned-area and
forest statistics keep all 718 outlines.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

EXCL = ["likely agricultural or grass burn", "military range"]
f = gpd.read_file(f"{WORK}/fires_2026.gpkg")
c = gpd.read_file(f"{BASE}/analysis/outline-check/outline_class_2026.geojson", columns=["fire_uid", "class"],
                  ignore_geometry=True)
f["outline_class"] = f.fire_uid.map(dict(zip(c.fire_uid, c["class"])))
assert f.outline_class.notna().all(), "outline without class"
f["exclude_from_distance"] = f.outline_class.isin(EXCL) & ~f.agency_match
f.to_file(f"{WORK}/fires_2026.gpkg", driver="GPKG")
print("outlines", len(f), "classes", f.outline_class.value_counts().to_dict())
print("excluded from distance analyses:", int(f.exclude_from_distance.sum()), "outlines,",
      round(f.loc[f.exclude_from_distance, "area_ha"].sum()), "ha;",
      "same classes but agency-matched (kept):", int((f.outline_class.isin(EXCL) & f.agency_match).sum()))
print(f[f.exclude_from_distance][["fire_uid", "fire_prov", "outline_class", "area_ha"]].to_string())
