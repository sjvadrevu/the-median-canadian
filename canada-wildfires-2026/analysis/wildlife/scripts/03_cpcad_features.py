"""Mapped 2026 burned area per protected/conserved area (CPCAD 2025 terrestrial), records dissolved by PARENT_ID.
Usage: python -I 03_cpcad_features.py <work_dir>"""
import sys, os
import pandas as pd, geopandas as gpd, shapely

WORK = sys.argv[1]
INP = os.path.join(WORK, "inputs.gpkg")
LOCNAME = {1: "AB", 2: "BC", 3: "MB", 4: "NB", 5: "NL", 6: "NT", 7: "NS", 8: "NU", 9: "ON", 10: "PE", 11: "QC", 12: "SK", 13: "YT"}
PAD = {1: "PA", 2: "OECM", 3: "Interim PA", 4: "Interim OECM", 5: "n/a"}
STATUS = {1: "Designated", 2: "Established", 3: "Interim", 4: "Inscribed", 5: "Adopted"}

pa = gpd.read_file(INP, layer="cpcad_t")
m3 = gpd.read_file(INP, layer="m3_2026")
M = shapely.union_all(m3.geometry.values)
shapely.prepare(M)
hit = pa[pa.geometry.intersects(M)].PARENT_ID.unique()
sub = pa[pa.PARENT_ID.isin(hit)]
rows = []
for pid, g in sub.groupby("PARENT_ID"):
    geom = shapely.union_all(g.geometry.values)
    a = geom.area
    b = shapely.intersection(geom, M).area
    r = g.sort_values("area_km2", ascending=False).iloc[0]
    rows.append(dict(parent_id=pid, name=r.NAME_E, province=LOCNAME.get(int(r.LOC), r.LOC), type=r.TYPE_E,
                     pa_or_oecm=PAD.get(int(r.PA_OECM_DF), r.PA_OECM_DF), status=STATUS.get(int(r.STATUS), r.STATUS),
                     iucn_cat=r.IUCN_CAT, manager=r.MGMT_E, n_records=len(g),
                     area_km2=round(a / 1e6, 3), burned_2026_mapped_km2=round(b / 1e6, 3),
                     share_burned_2026_mapped_pct=round(100 * b / a, 2)))
df = pd.DataFrame(rows)
df = df[df.burned_2026_mapped_km2 > 0].sort_values("burned_2026_mapped_km2", ascending=False)
df.to_csv(os.path.join(WORK, "cpcad_features_2026.csv"), index=False)
print(len(df), "protected/conserved areas (by PARENT_ID) intersect 2026 outlines")
print(df.head(25).to_string())
