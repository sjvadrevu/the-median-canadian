"""Flag burned 240 m cells that fall inside open forest-tenure / management-unit layers and sum merchantable volume
(kNN 2011) burned inside them, by province and year 2016-2026 plus the 2023-2026 union.

Layers (raw/tenure/):
  AB  Forest Management Agreement areas (geospatial.alberta.ca forest_management_agreement_public/MapServer/0), 21 FMAs
  ON  Forest Management Units (LIO_Open07/MapServer/20), 39 FMUs (the managed Crown forest under FMPs)
  QC  Unités d'aménagement (MRNF STF_UA.gpkg, published 2026-09-26)
  BC  Tree Farm Licences (WHSE_ADMIN_BOUNDARIES.FADM_TFL, not retired) and Timber Supply Areas (FADM_TSA_SV)
  SK  Timber supply areas layer (Forestry/MapServer/2): LAND_USE = 'Commercial Forest'; and the subset with an
      area-based licence (FMA or TSL)
Rule: cell centre inside polygon (same as every other grid step). Output: tenure_volume_by_year.csv
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from vcommon import RAW, WORK, OUT, burned_cells, rasterize_idx_window as rasterize_idx
from grid import meta

T = RAW / "tenure"
m = meta()
crs = m["crs"]


def load(path, **kw):
    g = gpd.read_file(path, **kw)
    return g.to_crs(crs)


layers = {}
ab = load(T / "ab_fma.geojson"); layers["AB_FMA"] = ("AB", ab.geometry)
on = load(T / "on_fmu.geojson"); layers["ON_FMU"] = ("ON", on.geometry)
qc = load(T / "qc_ua" / "UA_GPKG" / "STF_UA.gpkg"); layers["QC_UA"] = ("QC", qc.geometry)
tfl = load(T / "bc_WHSE_ADMIN_BOUNDARIES.FADM_TFL.json")
tfl = tfl[tfl.RETIREMENT_DATE.isna()]
tsa = load(T / "bc_tsa.json")
layers["BC_TFL"] = ("BC", tfl.geometry)
layers["BC_TSA_or_TFL"] = ("BC", pd.concat([tfl.geometry, tsa.geometry]))
sk = load(T / "sk_tsa.geojson")
layers["SK_commercial_forest"] = ("SK", sk[sk.LAND_USE == "Commercial Forest"].geometry)
layers["SK_area_licence"] = ("SK", sk[sk.AREA_BASED_LICENCE_NAME.notna() & (sk.AREA_BASED_LICENCE_NAME.str.strip() != "")].geometry)

cells = burned_cells()
rows = []
for name, (prov, geoms) in layers.items():
    idx = rasterize_idx(list(geoms.explode(index_parts=False)))
    inside = np.isin(cells.idx.values, idx)
    sub = cells[cells.prov == prov]
    ins = inside[cells.prov.values == prov]
    for y, g in sub.groupby("year"):
        gi = g[ins[sub.year.values == y]]
        rows.append(dict(layer=name, prov=prov, year=("2023_2026" if y == 0 else y),
                         area_scaled_ha=(g.area_ha * g.w).sum(), area_in_tenure_scaled_ha=(gi.area_ha * gi.w).sum(),
                         vol_merch_scaled_m3=(g.vol_merch * g.w).sum(), vol_merch_in_tenure_scaled_m3=(gi.vol_merch * gi.w).sum(),
                         vol_merch_mapped_m3=g.vol_merch.sum(), vol_merch_in_tenure_mapped_m3=gi.vol_merch.sum(),
                         tenure_cells_total=len(idx)))
    print(name, len(idx), "grid cells in layer", flush=True)
df = pd.DataFrame(rows)
df["share_vol_in_tenure"] = df.vol_merch_in_tenure_scaled_m3 / df.vol_merch_scaled_m3
df.to_csv(OUT / "tenure_volume_by_year.csv", index=False)
print(df[df.year.isin([2023, 2024, 2025, 2026, "2023_2026"])].round(3).to_string())
