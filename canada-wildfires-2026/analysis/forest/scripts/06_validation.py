"""Analysis 6: validation of the split of official totals.

1. Per province: official total vs CWFIS M3 mapped outline area, scaling factor (from 04 output).
2. Where a province publishes its own 2026 perimeters (BC, ON, AB, MB), compare its total with official and
   compare the split across fire management areas from provincial perimeters vs from M3.
3. NWT (points only): split of agency-reported fire sizes by region vs M3 split.
4. Quebec (points only): total of reported sizes vs official, and (rebuild 2026-10-21) split of SOPFEU point
   sizes across the 65 SOPFEU fire danger zones + remainder vs the M3 split.
Rebuild 2026-10-21: area layer fma_v2 (Manitoba now has 23 rows, so its perimeters test the split too); no
separate Parks Canada layer, so outline area inside national parks is no longer removed. Provincial perimeters
and points are compared with the provincial AGENCY official total (official_agency_2026_ha); the area split
shares are applied to the province official total including allocated Parks Canada hectares.
Outputs: validation_province.csv, validation_split_by_area.csv
"""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import make_valid
from common import DATA, WORK, OUT, EA, BASE, FMA_SIMP
FMA = FMA_SIMP

pd.set_option("display.width", 250)
P = DATA / "fire" / "raw" / "provincial"
F = pd.read_csv(OUT / "scaling_factors_by_province.csv")
T = pd.read_csv(OUT / "fma_2026_table.csv")
fma = gpd.read_file(FMA)


def load(p):
    if p == "BC":
        g = gpd.read_file(P / "bc" / "bc_PROT_CURRENT_FIRE_POLYS_SP.geojson")
        return g[g.FIRE_YEAR == 2026]
    if p == "ON":
        return gpd.read_file(P / "on" / "on_in_year_fire_perimeters.geojson")
    if p == "AB":
        return gpd.read_file(P / "ab" / "ab_wildfire_perimeter_extinguished_prod.geojson")
    if p == "MB":
        return gpd.read_file("/vsizip/" + str(P / "mb" / "MB_Forest_Fires_Shapefile.zip"))


vrows, srows = [], []
for p in ["BC", "ON", "AB", "MB"]:
    g = load(p).to_crs(EA)
    g["geometry"] = [make_valid(x) for x in g.geometry]
    dis = make_valid(g.geometry.union_all())
    tot = dis.area / 1e4
    sub = fma[fma.province == p]
    off = F.set_index("province").loc[p, "official_agency_2026_ha"]
    off_tot = F.set_index("province").loc[p, "official_2026_ha"]
    m3 = F.set_index("province").loc[p, "m3_mapped_ha"]
    vrows.append(dict(province=p, source="provincial perimeters (dissolved, ESRI:102001)", mapped_ha=tot,
                      official_ha=off, ratio_mapped_to_official=tot / off, m3_mapped_ha=m3))
    if len(sub) > 1:
        ins = [make_valid(dis.intersection(make_valid(geom))).area / 1e4 for geom in sub.geometry]
        s_prov = np.array(ins) / sum(ins)
        t = T.set_index("fma_id").loc[sub.fma_id]
        s_m3 = (t.mapped_ha / t.mapped_ha.sum()).values
        for fid, name, a, b in zip(sub.fma_id, sub.area_name, s_prov, s_m3):
            srows.append(dict(province=p, fma_id=fid, area_name=name, method="provincial perimeters",
                              share_provincial=a, share_m3=b,
                              ha_official_via_provincial=a * off_tot, ha_official_via_m3=b * off_tot,
                              diff_ha=(b - a) * off_tot))

# NWT points
nt = json.load(open(P / "nt" / "nt_fires_points_2026.json"))
nt = pd.DataFrame(nt)
rmap = {"Dehcho": "Deh Cho", "Beaufort Delta": "Inuvik"}
nt["region2"] = nt.region.replace(rmap)
off_nt = F.set_index("province").loc["NT", "official_agency_2026_ha"]
off_nt_tot = F.set_index("province").loc["NT", "official_2026_ha"]
vrows.append(dict(province="NT", source="NWT fire list points, sum of currentsize", mapped_ha=nt.currentsize.sum(),
                  official_ha=off_nt, ratio_mapped_to_official=nt.currentsize.sum() / off_nt,
                  m3_mapped_ha=F.set_index("province").loc["NT", "m3_mapped_ha"]))
sub = fma[fma.province == "NT"]
t = T.set_index("fma_id").loc[sub.fma_id]
s_m3 = t.mapped_ha / t.mapped_ha.sum()
byreg = nt.groupby("region2").currentsize.sum()
for fid, name, b in zip(sub.fma_id, sub.area_name, s_m3.values):
    a = byreg.get(name, 0.0) / nt.currentsize.sum()
    srows.append(dict(province="NT", fma_id=fid, area_name=name, method="agency fire points (region field)",
                      share_provincial=a, share_m3=b,
                      ha_official_via_provincial=a * off_nt_tot, ha_official_via_m3=b * off_nt_tot,
                      diff_ha=(b - a) * off_nt_tot))

# Quebec points
qf = BASE / "season" / "perimeters" / "qc_points_feux_historique_2026.geojson"
if qf.exists():
    q = gpd.read_file(qf)
    ycol = [c for c in q.columns if "an" == c.lower() or "annee" in c.lower() or "year" in c.lower()]
    print("QC columns", q.columns.tolist(), ycol)
    if ycol:
        q = q[pd.to_numeric(q[ycol[0]], errors="coerce") == 2026]
    s = q["sup_ha"].sum() if "sup_ha" in q.columns else np.nan
    off_qc = F.set_index("province").loc["QC", "official_agency_2026_ha"]
    vrows.append(dict(province="QC", source="SOPFEU points, sum of sup_ha (2026)", mapped_ha=s, official_ha=off_qc,
                      ratio_mapped_to_official=s / off_qc, m3_mapped_ha=F.set_index("province").loc["QC", "m3_mapped_ha"]))
    # split by SOPFEU fire danger zone: point of origin in zone (spatial join), whole fire size to that zone
    qz = fma[fma.province == "QC"]
    qp = q[q.sup_ha.notna()].to_crs(EA)
    jq = gpd.sjoin(qp[["sup_ha", "geometry"]], qz[["fma_id", "geometry"]], how="left", predicate="within")
    jq = jq[~jq.index.duplicated()]
    miss = jq.fma_id.isna()
    if miss.any():                                       # points on water/edges: nearest zone
        jn = gpd.sjoin_nearest(qp.loc[miss[miss].index, ["geometry"]], qz[["fma_id", "geometry"]], how="left")
        jq.loc[miss, "fma_id"] = jn[~jn.index.duplicated()].fma_id
    byz = jq.groupby("fma_id").sup_ha.sum()
    off_qc_tot = F.set_index("province").loc["QC", "official_2026_ha"]
    t = T.set_index("fma_id").loc[qz.fma_id]
    s_m3 = t.mapped_ha / t.mapped_ha.sum()
    for fid, name, b in zip(qz.fma_id, qz.area_name, s_m3.values):
        a = byz.get(fid, 0.0) / s
        srows.append(dict(province="QC", fma_id=fid, area_name=name, method="SOPFEU fire points (zone by location)",
                          share_provincial=a, share_m3=b, ha_official_via_provincial=a * off_qc_tot,
                          ha_official_via_m3=b * off_qc_tot, diff_ha=(b - a) * off_qc_tot))

V = pd.DataFrame(vrows)
S = pd.DataFrame(srows)
V.to_csv(OUT / "validation_province.csv", index=False)
S.to_csv(OUT / "validation_split_by_area.csv", index=False)
print(V.round(3).to_string())
print(S.round(3).to_string())
print(S.groupby("province").diff_ha.apply(lambda d: d.abs().sum() / 2).round(0))
