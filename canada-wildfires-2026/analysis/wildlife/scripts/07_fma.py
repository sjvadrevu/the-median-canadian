"""Mapped 2026 share burned per fire management area, from M3 outlines.
Usage: python 07_fma.py <work_dir> [layer]
Layer in work/inputs.gpkg: 'fma_v2' (default since the 2026-10-21 rebuild: data/geo/fma_v2.gpkg, MB and QC
sub-areas, no Parks Canada rows; written by 01_prep.py step 'fma_v2') or 'fma' (old fma_all, 146 rows).
06_tables.py copies work/fma_results.csv to fma_2026.csv."""
import sys, os
import pandas as pd, geopandas as gpd, shapely

WORK = sys.argv[1]
INP = os.path.join(WORK, "inputs.gpkg")
m3 = gpd.read_file(INP, layer="m3_2026")
MS = m3.sindex
LAYER = sys.argv[2] if len(sys.argv) > 2 else "fma_v2"
fma = gpd.read_file(INP, layer=LAYER)
rows = []
for _, r in fma.iterrows():
    idx = MS.query(r.geometry, predicate="intersects")
    b = sum(shapely.intersection(r.geometry, g).area for g in m3.geometry.values[idx]) if len(idx) else 0.0
    rows.append(dict(fma_id=r.fma_id, province=r.province, agency=r.agency, area_name=r.area_name, area_level=r.area_level,
                     area_km2=round(r.geometry.area / 1e6, 1), burned_2026_mapped_km2=round(b / 1e6, 2),
                     share_burned_2026_pct=round(100 * b / r.geometry.area, 2)))
df = pd.DataFrame(rows).sort_values("share_burned_2026_pct", ascending=False)
df.to_csv(os.path.join(WORK, "fma_results.csv"), index=False)
print(df.head(30).to_string())
