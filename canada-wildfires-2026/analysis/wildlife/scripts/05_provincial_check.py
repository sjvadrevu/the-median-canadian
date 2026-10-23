"""Sensitivity check: 2026 share burned of ECCC ranges in BC, ON and MB using each province's own
2026 fire perimeters instead of CWFIS M3 outlines. (QC, SK, NT, NL have no public 2026 perimeters;
AB's layer is a partial dashboard feed and is skipped.)
Usage: python -I 05_provincial_check.py <data_dir> <work_dir>"""
import sys, os
import pandas as pd, geopandas as gpd, shapely

DATA, WORK = sys.argv[1], sys.argv[2]
INP = os.path.join(WORK, "inputs.gpkg")
CRS = "ESRI:102001"
P = f"{DATA}/fire/raw/provincial"
bc = gpd.read_file(f"{P}/bc/bc_PROT_CURRENT_FIRE_POLYS_SP.geojson")
bc = bc[bc.FIRE_YEAR == 2026]
on = gpd.read_file(f"{P}/on/on_in_year_fire_perimeters.geojson")
print("ON FIRETYPE counts:", on.FIRETYPE.value_counts().to_dict() if "FIRETYPE" in on else "n/a")
mb = gpd.read_file(f"zip://{P}/mb/MB_Forest_Fires_Shapefile.zip")
prov = {}
for k, g in (("BC", bc), ("ON", on), ("MB", mb)):
    g = g.to_crs(CRS)
    U = shapely.union_all(shapely.make_valid(g.geometry.values))
    prov[k] = U
    print(k, len(g), "polygons, dissolved", round(U.area / 1e4), "ha")
m3 = gpd.read_file(INP, layer="m3_2026")
M = shapely.union_all(m3.geometry.values)
e = gpd.read_file(INP, layer="eccc_ranges")
rows = []
for _, r in e.iterrows():
    k = r.CODE[:2]
    if k not in prov:
        continue
    a = r.geometry.area
    rows.append(dict(code=r.CODE, herd=r.HERD, perimeter_source=k,
                     share_2026_m3_pct=round(100 * shapely.intersection(r.geometry, M).area / a, 2),
                     share_2026_provincial_pct=round(100 * shapely.intersection(r.geometry, prov[k]).area / a, 2)))
df = pd.DataFrame(rows)
df["diff_pts"] = (df.share_2026_m3_pct - df.share_2026_provincial_pct).round(2)
df.to_csv(os.path.join(WORK, "provincial_perimeter_check.csv"), index=False)
print(df.sort_values("share_2026_m3_pct", ascending=False).to_string())
