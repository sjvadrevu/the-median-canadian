"""Shared paths and constants for the 2026 wildfire forest analysis."""
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]          # .../wildfire
DATA = BASE / "data"
OUT = BASE / "analysis" / "forest"
WORK = OUT / "work"
WORK.mkdir(parents=True, exist_ok=True)

M3 = DATA / "fire" / "m3_perimeters_2026_cwfis_20261020.gpkg"
HOTSPOTS = DATA / "fire" / "cwfis_hotspots_2026_canada.csv.gz"     # superseded (gaps 2026-06-29..07-02), not used
HOTSPOTS_WFS = DATA / "fire" / "raw" / "hotspots_wfs_2026"            # CWFIS WFS public:hotspots archive, one CSV per UTC day
NBAC_SHP = WORK / "nbac_shp" / "NBAC_merged_1972_to_2025_20260513.shp"
NBAC_XLSX = DATA / "fire" / "raw" / "nbac" / "NBAC_summarystats_1972_to_2025_20260513.xlsx"
# Area layer (rebuild 2026-10-21): fma_v2 = fma_all with Manitoba split into 22 MWS restriction areas + remainder,
# Quebec into 65 SOPFEU fire danger zones + remainder, and the Parks Canada layer removed (parks are folded into
# the province rows that contain them). Grid and simplified copy carry the v2 names so the fma_all versions used
# by other analyses (economy, cause/climate default runs) are left in place.
FMA = DATA / "geo" / "fma_v2.gpkg"
FMA_SIMP = WORK / "fma_v2_simplified.gpkg"
FMA_GRID = "fma_v2_id"                                  # work/fma_v2_id.npy, uint16 area id per 240 m cell
PARKS = DATA / "geo" / "parks" / "clab" / "CLAB_CA_2026-10-05.shp"   # national park boundaries (PC allocation only)
OUTLINE_CLASS = BASE / "analysis" / "outline-check" / "outline_class_2026.geojson"
FOREST = DATA / "geo" / "landcover" / "lc2020_forest_count_240m.tif"
PROV = DATA / "geo" / "statcan" / "lpr_000b21a_e_provinces_2021.gpkg"
OFFICIAL = DATA / "smoke-cost" / "fire_area_count_by_agency_year.csv"

EA = "ESRI:102001"          # Canada Albers Equal Area, used for every vector area
PROVS = ["BC", "AB", "SK", "MB", "ON", "QC", "NB", "NS", "PE", "NL", "YT", "NT", "NU"]
