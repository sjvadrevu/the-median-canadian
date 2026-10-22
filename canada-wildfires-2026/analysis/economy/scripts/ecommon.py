"""Shared paths for the economy analysis. Reuses the 240 m grid built in analysis/forest."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]          # .../wildfire
DATA = BASE / "data"
FOREST = BASE / "analysis" / "forest"
FWORK = FOREST / "work"
OUT = BASE / "analysis" / "economy"
RAW = OUT / "raw"
WORK = OUT / "work"
WORK.mkdir(parents=True, exist_ok=True)
sys.path.append(str(FOREST / "scripts"))  # forest grid.py/common.py (name "common" belongs to forest)

M3 = DATA / "fire" / "m3_perimeters_2026_cwfis_20261020.gpkg"
FMA_ATTR = DATA / "geo" / "fma_all_attributes.csv"
PROV = DATA / "geo" / "statcan" / "lpr_000b21a_e_provinces_2021.gpkg"
SCALING = FOREST / "scaling_factors_by_province.csv"
OFFICIAL = DATA / "smoke-cost" / "fire_area_count_by_agency_year.csv"
EA = "ESRI:102001"
YEARS = [2023, 2024, 2025, 2026]
# SCANFI / kNN grids use NAD83 Canada Lambert with lat_0 = 0; the 240 m grid (EPSG:3979) uses lat_0 = 49.
# Same cone, so the two differ by a constant northing offset (and a sub-metre datum shift).
LCC0 = "+proj=lcc +lat_0=0 +lon_0=-95 +lat_1=49 +lat_2=77 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
