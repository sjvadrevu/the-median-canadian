"""Merge the 2026 feature shards (work/features_2026_part*.csv from 08_features_2026.py) into work/features_2026.csv and
apply the calibrated rule exactly as 07_apply_rule.py ('likely destroyed' = calibrated rule AND burn context
dnbr_r100_250_share100 >= 0.20). Distance band uses 'dist' from 04_footprints.py (m from the footprint centroid to the
nearest 2026 outline; 0 = inside).
Per fire (CWFIS M3 outline): flagged footprints inside / within 500 m / 500-1000 m (false-positive check).
Estimated true count and band: est = flagged x P / R, with P, R the 5-fold spatial CV precision and recall
(calibration_accuracy.csv), band from 95% Wilson intervals of P and R: [flagged x P_lo / R_hi, flagged x P_hi / R_lo].
This band covers sampling error of the Jasper calibration only, NOT transfer error to other places and seasons
(see transfer_checks.csv). Agency label: NRCan CWFIF 2026 fire list point(s) inside or within 5 km, largest fire_size.
-> work/features_2026.csv, work/apply_2026.csv, estimates_2026_by_fire.csv"""
import glob, json, os, re
import numpy as np, pandas as pd, geopandas as gpd
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.dirname(os.path.dirname(P))
parts = sorted(glob.glob(os.path.join(P, "work", "features_2026_part*.csv")))
d = pd.concat([pd.read_csv(f).assign(part=os.path.basename(f)) for f in parts], ignore_index=True)
fp = pd.read_csv(os.path.join(P, "work", "fp_2026_all_1km.csv.gz"), usecols=["aoi", "x", "y"])
dup = d.duplicated(["x", "y"]).sum()
print("parts", len(parts), "rows", len(d), "duplicates", dup, "footprints expected", len(fp))
d = d.drop_duplicates(["x", "y"])
d["set"] = "microsoft"; d["dist_fire_m"] = d["dist"]
d.to_csv(os.path.join(P, "work", "features_2026.csv"), index=False)
# Bald Range check-event file for 07/14 (the 05_event_features.py run was killed for memory; 08 uses the same post
# window 2026-09-19..10-20, the same pre window and the same 2026 outlines for the offset, on 20 km cluster grids)
d[d.aoi == 36076584].assign(event="baldrange2026").to_csv(os.path.join(P, "work", "features_baldrange2026.csv"), index=False)
rule = pd.read_csv(os.path.join(P, "calibration_rules.csv")).query("fold == 'all'").rule.iloc[0]
conds = [re.match(r"\s*(\w+)\s*>=\s*(-?[\d.]+)", c).groups() for c in rule.split("AND")]
m = np.ones(len(d), bool)
for f, v in conds: m &= (d[f] >= float(v)).fillna(False).values
d["rule_only"] = m
d["burn_context"] = (d.dnbr_r100_250_share100 >= 0.20).fillna(False).values
d["likely_destroyed"] = d.rule_only & d.burn_context
d["no_data"] = d[[f for f, _ in conds]].isna().any(axis=1)
d.to_csv(os.path.join(P, "work", "apply_2026.csv"), index=False)
acc = pd.read_csv(os.path.join(P, "calibration_accuracy.csv")).iloc[0]
def wilson(k, n, z=1.96):
    p = k / n; c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h
Pp, Rr = acc.tp / acc.predicted, acc.tp / acc.actual
(Plo, Phi), (Rlo, Rhi) = wilson(acc.tp, acc.predicted), wilson(acc.tp, acc.actual)
outl = gpd.read_file(os.path.join(W, "analysis", "outline-check", "outline_class_2026.geojson")).set_index("fire_uid")
fl = pd.DataFrame(json.load(open(os.path.join(W, "data", "fire", "reference", "nrcan_fire_list.json"))))
fl = fl[(fl.fire_year == 2026) & fl.latitude.notna()]
pts = gpd.GeoDataFrame(fl, geometry=gpd.points_from_xy(fl.longitude, fl.latitude), crs=4326).to_crs(3978)
buf = outl[["geometry"]].to_crs(3978).copy(); buf["geometry"] = buf.buffer(5000)
j = gpd.sjoin(pts[["agency_fire_id", "agency_code", "fire_size", "geometry"]], buf.reset_index(), predicate="within")
lab = j.sort_values("fire_size", ascending=False).drop_duplicates("fire_uid").set_index("fire_uid")
NAMES = {36076584: "Bald Range (Summerland / RDOS Area F)", 36076592: "Bradley Creek (Okanagan Indian Band IR #1)"}
rows = []
for fid, g in d.groupby("aoi"):
    near = g[g.dist <= 500]; k = int(near.likely_destroyed.sum())
    o = outl.loc[fid]
    rows.append(dict(fire_uid=fid, name=NAMES.get(fid, ""), prov=o.prov,
                     agency_fire_id=(f"{lab.loc[fid, 'agency_code']} {lab.loc[fid, 'agency_fire_id']}" if fid in lab.index else ""),
                     outline_class=o["class"], area_ha=o.area_ha, first_det=str(o.first_date)[:10], last_det=str(o.last_date)[:10],
                     footprints_1km=len(g), footprints_inside=int((g.dist <= 0).sum()), footprints_500m=len(near),
                     no_data_500m=int(near.no_data.sum()), flagged_inside=int(g[g.dist <= 0].likely_destroyed.sum()), flagged_500m=k,
                     flagged_500_1000m=int(g[(g.dist > 500) & (g.dist <= 1000)].likely_destroyed.sum()),
                     rule_only_500m=int(near.rule_only.sum()),
                     est_destroyed=round(k * Pp / Rr, 1), est_lo=round(k * Plo / Rhi, 1), est_hi=round(k * Phi / Rlo, 1),
                     post_start=g.post_start.iloc[0]))
o = pd.DataFrame(rows).sort_values("flagged_500m", ascending=False)
tot = o[["footprints_1km", "footprints_inside", "footprints_500m", "no_data_500m", "flagged_inside", "flagged_500m", "flagged_500_1000m", "rule_only_500m", "est_destroyed", "est_lo", "est_hi"]].sum()
o = pd.concat([o, pd.DataFrame([dict(fire_uid="ALL", name="all 2026 outlines with footprints", **tot.round(1).to_dict())])], ignore_index=True)
o.to_csv(os.path.join(P, "estimates_2026_by_fire.csv"), index=False)
print(f"P={Pp:.3f} [{Plo:.3f},{Phi:.3f}] R={Rr:.3f} [{Rlo:.3f},{Rhi:.3f}]")
pd.set_option("display.width", 250)
print(o[o.flagged_500m > 0].drop(columns=["outline_class", "post_start"]).to_string())
print(o.tail(1).to_string())
