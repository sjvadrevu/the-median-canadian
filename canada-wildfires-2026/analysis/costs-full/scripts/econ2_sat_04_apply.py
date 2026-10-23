"""econ2_sat_04_apply.py: apply the property method's calibrated rule to the econ2 feature files, count likely destroyed
buildings and value them at local 2021 Census home values, as the bill does.

Rule (unchanged from analysis/property/scripts/07_apply_rule.py and 15_apply_2026.py): calibration_rules.csv fold 'all'
(dndvi_bmax >= 180 AND dnbr_r20_60 >= 40) AND burn context (dnbr_r100_250_share100 >= 0.20). Counted within 500 m of the
job's fire polygon (the 500-1000 m band is the false-positive check). Estimate = flagged x P / R with P, R the 5-fold
spatial CV precision and recall (calibration_accuracy.csv) and a band from 95% Wilson intervals (calibration sample only).
Value: each flagged footprint at the 2021 Census average (and median) value of owner-occupied dwellings of its DA, fallback
CD (property/work/da_values_2021.csv, nearest DA within 2 km), exactly as 13_value_destroyed.py est_row.
Bill overlap: a flagged footprint that is also flagged within 500 m in one of the bill's apply files
(analysis/property/work/apply_*.csv, the events summed by the slide builder) is marked in_bill and not counted as new.
Quality screen: qa_pass = cluster dNBR offset within +-100 AND the fire polygon's 500-1000 m flags <= 26% of its 0-500 m
flags AND the fire polygon is at least 10 ha (see the code comments); the econ2 rows count only qa_pass flags.
Labels: Indian reserve name (Aboriginal Lands of Canada, data/geo/indigenous/al_ta) if inside one, else the nearest 2021
population centre within 30 km (data/geo/statcan/lpc_000b21a_popcentres_2021.gpkg), else 'rural'.
usage: python3 -I econ2_sat_04_apply.py <job> [...]  -> work/econ2_sat/apply_<job>.csv, work/econ2_sat/est_<job>.csv"""
import glob, os, re, sys
import numpy as np, pandas as pd, geopandas as gpd

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); AN = os.path.dirname(B); W = os.path.dirname(AN)
P = os.path.join(AN, "property"); OUT = os.path.join(B, "work", "econ2_sat")
rule = pd.read_csv(os.path.join(P, "calibration_rules.csv")).query("fold == 'all'").rule.iloc[0]
conds = [re.match(r"\s*(\w+)\s*>=\s*(-?[\d.]+)", c).groups() for c in rule.split("AND")]
acc = pd.read_csv(os.path.join(P, "calibration_accuracy.csv")).iloc[0]


def wilson(k, n, z=1.96):
    p = k / n; c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


Pp, Rr = acc.tp / acc.predicted, acc.tp / acc.actual
(Plo, Phi), (Rlo, Rhi) = wilson(acc.tp, acc.predicted), wilson(acc.tp, acc.actual)
dv = pd.read_csv(os.path.join(P, "work", "da_values_2021.csv"), dtype={"DAUID": str, "CDUID": str, "PRUID": str})
da = gpd.read_file(os.path.join(W, "data", "geo", "statcan", "da_2021_pop_gen50m.gpkg"), columns=["DAUID"]).merge(dv, on="DAUID")
pc = gpd.read_file(os.path.join(W, "data", "geo", "statcan", "lpc_000b21a_popcentres_2021.gpkg"), columns=["PCNAME"]).to_crs(3978)
al = gpd.read_file(os.path.join(W, "data", "geo", "indigenous", "al_ta")).to_crs(3978)
al = al[["NAME1", "geometry"]].rename(columns={"NAME1": "reserve"})
# bill footprints: flagged within 500 m in the apply files the slide builder sums
bill = []
for ev in ["tantallon2023", "barrington2023", "mcdougall2023", "bushcreek2023", "jasper2024", "denare2025", "lacdubonnet2025"]:
    a = pd.read_csv(os.path.join(P, "work", f"apply_{ev}.csv"))
    bill.append(a[a.likely_destroyed & (a.dist_fire_m.fillna(1e9) <= 500)][["x", "y"]].assign(bill_event=ev))
a26 = pd.read_csv(os.path.join(P, "work", "apply_2026.csv"))
bill.append(a26[a26.likely_destroyed & (a26.dist <= 500)][["x", "y"]].assign(bill_event="2026 all outlines"))
bill = pd.concat(bill); bill["k"] = bill.x.round(0).astype(int).astype(str) + "_" + bill.y.round(0).astype(int).astype(str)
billk = set(bill.k)


def values_at(lon, lat):
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs=4326).to_crs(da.crs)
    j = gpd.sjoin_nearest(pts, da[["DAUID", "avg_value", "median_value", "avg_value_src", "geometry"]], max_distance=2000)
    return j[~j.index.duplicated()].reindex(range(len(pts)))


for job in sys.argv[1:]:
    fs = sorted(glob.glob(os.path.join(OUT, f"features_{job}_part*.csv")))
    d = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True).drop_duplicates(["x", "y"]).reset_index(drop=True)
    m = np.ones(len(d), bool)
    for f, v in conds:
        m &= (d[f] >= float(v)).fillna(False).values
    d["rule_only"] = m
    d["burn_context"] = (d.dnbr_r100_250_share100 >= 0.20).fillna(False).values
    d["likely_destroyed"] = d.rule_only & d.burn_context
    d["no_data"] = d[[f for f, _ in conds]].isna().any(axis=1)
    d["k"] = d.x.round(0).astype(int).astype(str) + "_" + d.y.round(0).astype(int).astype(str)
    d["in_bill"] = d.k.isin(billk)
    g = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.x, d.y), crs=3978)
    r = gpd.sjoin(g[["geometry"]], al, predicate="within", how="left")
    d["reserve"] = r[~r.index.duplicated()].reserve.values
    n = gpd.sjoin_nearest(g[["geometry"]], pc, max_distance=30000, how="left", distance_col="pc_dist")
    n = n[~n.index.duplicated()]
    d["place"] = np.where(d.reserve.notna(), "IR " + d.reserve.fillna("").astype(str), n.PCNAME.fillna("rural").values)
    v = values_at(d.lon.values, d.lat.values)
    d["DAUID"] = v.DAUID.values; d["avg_value"] = v.avg_value.values; d["median_value"] = v.median_value.values; d["value_src"] = v.avg_value_src.values
    # Quality screen (from the property method's own checks): (1) a cluster whose dNBR offset is beyond +-100 has an unstable
    # pre/post match (analysis/property dropped Enterprise 2023 for offsets of +83 to +85 and 0 fallbacks) -> unreliable;
    # (2) a fire polygon fails the false-positive check when its 500-1000 m band has more than 26% as many flags as its
    # 0-500 m band (the worst ratio among the bill's main events: Bradley Creek 2026, 26 per 103 = 0.252 on the M3 outline).
    d["offset_ok"] = d.dnbr_offset.abs() <= 100
    ok = d[d.offset_ok]
    f5 = ok[(ok.dist <= 500) & ok.likely_destroyed].groupby("aoi").size()
    f10 = ok[(ok.dist > 500) & (ok.dist <= 1000) & ok.likely_destroyed].groupby("aoi").size()
    qa = pd.DataFrame({"f500": f5, "f1000": f10}).fillna(0)
    qa["fp_ok"] = qa.f1000 <= 0.26 * qa.f500
    d["fp_ok"] = d.aoi.map(qa.fp_ok).fillna(True).astype(bool)
    # (3) the fire polygon must be at least 10 ha: the rule's burn context needs 20% of the 100-250 m ring (16.5 ha) burned,
    # which a fire of a few hectares cannot supply, so flags next to tiny polygons come from other land changes
    aoi = gpd.read_file(os.path.join(OUT, f"aoi_{job}.gpkg"), columns=["fire_id", "area_ha"])
    d["area_ok"] = d.aoi.astype(str).map(aoi.assign(fire_id=aoi.fire_id.astype(str)).set_index("fire_id").area_ha).fillna(0).values >= 10
    d["qa_pass"] = d.offset_ok & d.fp_ok & d.area_ok
    d.drop(columns=["k"]).to_csv(os.path.join(OUT, f"apply_{job}.csv"), index=False)
    rows = []
    for (fid, place), gg in d.groupby(["aoi", "place"]):
        near = gg[gg.dist <= 500]; fl = near[near.likely_destroyed]; new = fl[~fl.in_bill]
        if len(fl) == 0 and len(gg[(gg.dist > 500) & gg.likely_destroyed]) == 0:
            continue
        rows.append(dict(job=job, fire_id=fid, place=place, qa_pass_share=round(float(fl.qa_pass.mean()), 3) if len(fl) else np.nan,
                         flagged_500m_qa=int(fl.qa_pass.sum()), flagged_500m_new_qa=int((fl.qa_pass & ~fl.in_bill).sum()),
                         footprints_1km=len(gg), footprints_500m=len(near), no_data_500m=int(near.no_data.sum()),
                         flagged_inside=int(gg[(gg.dist <= 0) & gg.likely_destroyed].shape[0]), flagged_500m=len(fl),
                         flagged_500_1000m=int(gg[(gg.dist > 500) & (gg.dist <= 1000) & gg.likely_destroyed].shape[0]),
                         flagged_500m_in_bill=int(fl.in_bill.sum()), flagged_500m_new=len(new),
                         est_new=round(len(new) * Pp / Rr, 1), est_new_lo=round(len(new) * Plo / Rhi, 1), est_new_hi=round(len(new) * Phi / Rlo, 1),
                         value_new_avg_cad=float(new.avg_value.sum()), value_new_median_cad=float(new.median_value.sum()),
                         value_all_avg_cad=float(fl.avg_value.sum()), value_all_median_cad=float(fl.median_value.sum()),
                         mean_avg_value_flagged=float(fl.avg_value.mean()) if len(fl) else np.nan,
                         mean_median_value_flagged=float(fl.median_value.mean()) if len(fl) else np.nan,
                         share_value_from_DA=round(float((fl.value_src == "DA").mean()), 3) if len(fl) else np.nan,
                         dnbr_offset_median=float(gg.dnbr_offset.median()), post_start=str(gg.post_start.iloc[0]), post_end=str(gg.post_end.iloc[0])))
    e = pd.DataFrame(rows).sort_values(["flagged_500m"], ascending=False)
    e.to_csv(os.path.join(OUT, f"est_{job}.csv"), index=False)
    tot = e[["footprints_500m", "flagged_500m", "flagged_500_1000m", "flagged_500m_in_bill", "flagged_500m_new", "value_new_avg_cad"]].sum()
    print(job, "footprints", len(d), "features rows", len(fs), "files;", tot.to_dict())
    pd.set_option("display.width", 250)
    print("qa: flagged_500m passing", int(e.flagged_500m_qa.sum()), "new passing", int(e.flagged_500m_new_qa.sum()))
    print(e[e.flagged_500m > 0].head(40)[["fire_id", "place", "qa_pass_share", "footprints_500m", "flagged_inside", "flagged_500m", "flagged_500_1000m", "flagged_500m_in_bill",
                                           "flagged_500m_new", "value_new_avg_cad", "mean_avg_value_flagged", "dnbr_offset_median"]].to_string())
