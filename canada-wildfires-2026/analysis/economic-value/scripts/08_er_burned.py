"""Area burned (scaled to official provincial totals) and merchantable volume burned per 2021 economic region (ER) and
year 2016-2026, plus the 2023-2026 union and the share of ER land burned.
ER polygons: StatCan 2021 cartographic boundary file, layer ER (geo.statcan.gc.ca geo_wa 2021 MapServer/2).
Output: er_burned_by_year.csv"""
import numpy as np
import pandas as pd
import geopandas as gpd
from vcommon import RAW, OUT, burned_cells, rasterize_idx_window
from grid import meta

m = meta()
er = gpd.read_file(RAW / "geo" / "er_2021.geojson")
if er.crs is None or er.crs.to_epsg() != 3979:
    print("ER CRS", er.crs)
er = er.to_crs(m["crs"])
cells = burned_cells()
rows = []
for _, r in er.iterrows():
    idx = rasterize_idx_window(list(gpd.GeoSeries([r.geometry]).explode(index_parts=False)))
    ins = cells[np.isin(cells.idx.values, idx)]
    g = ins.groupby("year").agg(area_mapped_ha=("area_ha", "sum"), vol_merch_m3=("vol_merch", "sum"))
    ins = ins.assign(a_s=ins.area_ha * ins.w, v_s=ins.vol_merch * ins.w)
    g2 = ins.groupby("year").agg(area_scaled_ha=("a_s", "sum"), vol_merch_scaled_m3=("v_s", "sum"))
    for y in list(range(2016, 2027)) + [0]:
        rows.append(dict(ERUID=r.ERUID, ERNAME=r.ERNAME, PRUID=r.PRUID, land_km2=r.LANDAREA, year=("2023_2026" if y == 0 else y),
                         area_mapped_ha=float(g.area_mapped_ha.get(y, 0.0)), area_scaled_ha=float(g2.area_scaled_ha.get(y, 0.0)),
                         vol_merch_scaled_m3=float(g2.vol_merch_scaled_m3.get(y, 0.0))))
d = pd.DataFrame(rows)
d["share_land_burned"] = d.area_scaled_ha / (d.land_km2 * 100)
d.to_csv(OUT / "er_burned_by_year.csv", index=False)
u = d[d.year == "2023_2026"].sort_values("share_land_burned", ascending=False)
print(u.head(25)[["ERUID", "ERNAME", "area_scaled_ha", "share_land_burned", "vol_merch_scaled_m3"]].round(3).to_string())
