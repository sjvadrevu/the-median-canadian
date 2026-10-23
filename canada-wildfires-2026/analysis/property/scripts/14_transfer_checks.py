"""Count-level transfer check of the Jasper-calibrated rule on other events with an official count but no
structure-level layer: flagged Microsoft footprints (inside the fire polygon or within 500 m) vs the official figure.
ratio = flagged / official. -> transfer_checks.csv"""
import os
import pandas as pd
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFF = {"jasper2024": (567, "official destroyed polygons, whole layer (Municipality of Jasper); 374 of them overlap a Microsoft footprint"),
       "tantallon2023": (200, "approx. structures lost (151 homes), HRFE"),
       "barrington2023": (230, "structures destroyed (+59 damaged), HRFE citing Barrington AAR"),
       "mcdougall2023": (200, "approx. structures impacted (destroyed or damaged), CORE/RDCO"),
       "bushcreek2023": (185, "structures lost: CSRD 176 (approx.) + TNRD 9; Little Shuswap Lake Band not published"),
       "denare2025": (400, "approx. permanent residences destroyed in the SHOE fire region (about half in Denare Beach), SK/SPSA"),
       "baldrange2026": (150, "approx. structures damaged or destroyed (preliminary), District of Summerland"),
       "enterprise2023": (None, "no official count found"), "lacdubonnet2025": (None, "no official count found"),
       "bradleycreek2026": (None, "no official count published by OKIB")}
rows = []
for ev, (n, what) in OFF.items():
    f = os.path.join(P, "work", f"apply_{ev}.csv")
    if not os.path.exists(f): continue
    a = pd.read_csv(f); near = a[a.dist_fire_m.fillna(1e9) <= 500]
    r = dict(event=ev, official=n, official_what=what, footprints_inside=int((a.dist_fire_m <= 0).sum()), footprints_within_500m=len(near),
             flagged_inside=int(a[a.dist_fire_m <= 0].likely_destroyed.sum()), flagged_within_500m=int(near.likely_destroyed.sum()),
             flagged_500_1000m=int(a[(a.dist_fire_m > 500) & (a.dist_fire_m <= 1000)].likely_destroyed.sum()),
             old_rule_within_500m=int(near.old_rule.sum()), no_data=int(near.no_data.sum()))
    r["ratio_flagged_to_official"] = round(r["flagged_within_500m"] / n, 2) if n else None
    rows.append(r)
o = pd.DataFrame(rows); o.to_csv(os.path.join(P, "transfer_checks.csv"), index=False); print(o.drop(columns="official_what").to_string())
