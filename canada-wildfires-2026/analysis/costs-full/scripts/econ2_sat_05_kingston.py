"""econ2_sat_05_kingston.py: a second satellite count for the 2025 Kingston fire (NBAC 2025_684, which also holds the May 2025
Small Point fire), with a summer window on both sides.

Why: in the first run (job atl2025, post window Aug 26 to Oct 15, 2025 against the same weeks of 2024) the drought-browned
vegetation of fall 2025 shifted the main cluster by +154 dNBR, beyond the +-100 limit of the quality screen, so no count was
usable. Here the post window is the next summer (Jun 15 to Aug 15, 2026) and the pre window the summer before both fires
(Jun 5 to Aug 25, 2024), the same next-summer rule econ2_sat_01 uses for fires that burned past mid-September. The count
therefore covers both 2025 fires (official: 248 damaged or destroyed by both, Canadian Press season review; 203 destroyed in
the August fire, premier). Regrowth and rebuilding by summer 2026 can hide some losses, so the count is a lower estimate
(the Long Lake NS fire, imaged the same way, gave 13 flags against 20 homes lost).
Writes work/econ2_sat/aoi_kng2025.gpkg and fp_kng2025.csv.gz (the 2025_684 rows of fp_atl2025.csv.gz); then run
econ2_sat_03_features.py kng2025 0 1 and econ2_sat_04_apply.py kng2025.
usage: python3 -I econ2_sat_05_kingston.py"""
import os
import pandas as pd, geopandas as gpd

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(B, "work", "econ2_sat")
a = gpd.read_file(os.path.join(OUT, "aoi_atl2025.gpkg"))
a["fire_id"] = a.fire_id.astype(str)
k = a[a.fire_id == "2025_684"].copy()
assert len(k) == 1
k["post_start"], k["post_end"] = "2026-06-15", "2026-08-15"
k["pre_start"], k["pre_end"] = "2024-06-05", "2024-08-25"
k["window_rule"] = "next summer against the summer before both fires (fall 2025 drought offset in the first run)"
k.to_file(os.path.join(OUT, "aoi_kng2025.gpkg"), driver="GPKG")
fp = pd.read_csv(os.path.join(OUT, "fp_atl2025.csv.gz"))
f = fp[fp.aoi.astype(str) == "2025_684"]
f.to_csv(os.path.join(OUT, "fp_kng2025.csv.gz"), index=False)
print("kng2025: 1 polygon,", len(f), "footprints within 1 km,", int((f.dist <= 500).sum()), "within 500 m")
