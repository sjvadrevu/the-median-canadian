"""Prepare inputs in ESRI:102001 (Canada Albers Equal Area).
Writes work/inputs.gpkg (layers: m3_2026, eccc_ranges, qc_caribou, sk_caribou, parks, cpcad_t, fma)
and work/nbac_1987_2025.gpkg (NBAC polygons 1987-2025, valid, polygonal).
Usage: python -I 01_prep.py <data_dir> <work_dir>"""
import sys, os, time
import geopandas as gpd, pyogrio, shapely
import pandas as pd

DATA, WORK = sys.argv[1], sys.argv[2]
CRS = "ESRI:102001"
OUT = os.path.join(WORK, "inputs.gpkg")


def poly(gs):
    """make_valid and keep polygonal parts only"""
    g = shapely.make_valid(gs.values)
    g = shapely.get_parts(g) if False else g
    out = []
    for x in g:
        if x is None or x.is_empty:
            out.append(None); continue
        if x.geom_type in ("Polygon", "MultiPolygon"):
            out.append(x); continue
        parts = [p for p in shapely.get_parts(x) if p.geom_type in ("Polygon", "MultiPolygon")]
        out.append(shapely.union_all(parts) if parts else None)
    return gpd.GeoSeries(out, crs=gs.crs, index=gs.index)


def save(gdf, layer):
    gdf = gdf.copy()
    gdf["geometry"] = poly(gdf.geometry)
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
    gdf["area_km2"] = gdf.geometry.area / 1e6
    gdf.to_file(OUT, layer=layer, driver="GPKG")
    print(layer, len(gdf), round(gdf.area_km2.sum(), 1), "km2", flush=True)


t = time.time()
STEPS = sys.argv[3].split(",") if len(sys.argv) > 3 else ["small", "cpcad", "nbac"]
if "small" in STEPS:
    save(gpd.read_file(f"{DATA}/fire/m3_perimeters_2026_cwfis_20261020.gpkg").to_crs(CRS), "m3_2026")
    save(gpd.read_file(f"{DATA}/geo/caribou/eccc_boreal_caribou_ranges_2012.geojson").to_crs(CRS), "eccc_ranges")
    save(gpd.read_file(f"{DATA}/geo/caribou/qc_caribou_forestier_aires_repartition.gpkg").to_crs(CRS), "qc_caribou")
    save(gpd.read_file(f"{DATA}/geo/caribou/sk_woodland_caribou_ranges.geojson").to_crs(CRS), "sk_caribou")
    save(gpd.read_file(f"{DATA}/geo/parks/clab/CLAB_CA_2026-10-05.shp").to_crs(CRS), "parks")
    save(gpd.read_file(f"{DATA}/geo/fma_all.gpkg").to_crs(CRS), "fma")
if "fma_v2" in STEPS:                                   # rebuild 2026-10-21 area layer (python 01_prep.py DATA WORK fma_v2)
    save(gpd.read_file(f"{DATA}/geo/fma_v2.gpkg").to_crs(CRS), "fma_v2")
if "cpcad" in STEPS:
    pa = pyogrio.read_dataframe(f"{DATA}/geo/cpcad/extracted/ProtectedConservedArea_2025.gdb",
                                layer="ProtectedConservedArea_2025",
                                columns=["PARENT_ID", "NAME_E", "ZONE_ID", "ZONEDESC_E", "LOC", "BIOME", "PA_OECM_DF",
                                         "STATUS", "TYPE_E", "MGMT_E", "IUCN_CAT", "O_AREA_HA"])
    # an OGR where-filter on BIOME returned 0 rows with geometry for this GDB, so filter in pandas
    pa = pa[pa.BIOME == "T"].copy().to_crs(CRS)
    save(pa, "cpcad_t")
print("layers done", round(time.time() - t), "s", flush=True)
if "nbac" not in STEPS:
    sys.exit(0)

NB = os.path.join(WORK, "nbac_1987_2025.gpkg")
if os.path.exists(NB):
    os.remove(NB)
src = f"{DATA}/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp"
n = pyogrio.read_info(src)["features"]
CH = 2000
tot = 0; byyear = {}
# one sequential pass in chunks (an OGR where-filter per year re-scans the 3 GB file each time)
for k in range(0, n, CH):
    g = pyogrio.read_dataframe(src, skip_features=k, max_features=CH,
                               columns=["YEAR", "NFIREID", "POLY_HA", "ADJ_HA", "PRESCRIBED", "ADMIN_NAME"])
    g = g[g.YEAR >= 1987]
    if len(g) == 0:
        continue
    g = g.to_crs(CRS)
    g["geometry"] = poly(g.geometry)
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    g["area_ha_ea"] = g.geometry.area / 1e4
    for y, v in g.groupby("YEAR").area_ha_ea.sum().items():
        byyear[int(y)] = byyear.get(int(y), 0) + v
    tot += g.area_ha_ea.sum()
    pyogrio.write_dataframe(g, NB, layer="nbac", append=os.path.exists(NB))
    print(k, n, round(time.time() - t), "s", flush=True)
for y in sorted(byyear):
    print("year", y, round(byyear[y]), "ha equal-area")
print("NBAC 1987-2025 summed (with reburn overlap)", round(tot), "ha")
