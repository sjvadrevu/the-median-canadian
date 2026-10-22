#!/bin/sh
# Reproduce the climate-chain analysis. Usage: sh run_all.sh
# A different area layer: AREA_FILE=/path/to/areas.gpkg sh run_all.sh --areas-only
# (same columns as data/geo/fma_all.gpkg; steps 05-07 are area-dependent and cache in work/areas_<hash>/).
set -e
S=$(cd "$(dirname "$0")" && pwd)
R="$S/../raw"
if [ "$1" != "--areas-only" ]; then
  mkdir -p "$R/indices" "$R/eccc" "$R/canswe"
  # climate indices (NOAA CPC / PSL)
  curl -sS -o "$R/indices/oni.ascii.txt" https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
  curl -sS -o "$R/indices/pdo.timeseries.ersstv5.csv" https://psl.noaa.gov/pdo/data/pdo.timeseries.ersstv5.csv
  curl -sS -o "$R/indices/monthly.ao.index.b50.current.ascii" https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_ao_index/monthly.ao.index.b50.current.ascii
  curl -sS -o "$R/indices/norm.nao.monthly.b5001.current.ascii" https://www.cpc.ncep.noaa.gov/products/precip/CWlink/pna/norm.nao.monthly.b5001.current.ascii
  # polar vortex (NCEP/NCAR R1 U 10 hPa 60N); kept only if the server returns CSV (it returned 503 on 2026-10-21)
  curl -sS -f -o "$R/indices/u10_60n_r1.csv" "https://psl.noaa.gov/thredds/ncss/grid/Datasets/ncep.reanalysis/Monthlies/pressure/uwnd.mon.mean.nc?var=uwnd&north=60&south=60&west=0&east=357.5&vertCoord=10&time_start=1950-01-01&time_end=2026-12-01&accept=csv" || rm -f "$R/indices/u10_60n_r1.csv"
  # ECCC station inventory and CanSWE
  curl -sS -o "$R/eccc/climate_stations.json" "https://api.weather.gc.ca/collections/climate-stations/items?f=json&limit=10000"
  curl -sS -L -o "$R/canswe/CanSWE-CanEEN_1928-2025_v8.nc" "https://zenodo.org/records/19075529/files/CanSWE-CanEEN_1928-2025_v8.nc?download=1"
  python3 -I "$S/01_station_inventory.py"
  python3 -I "$S/02_download_daily.py"
  python3 -I "$S/03_indices.py"
  python3 -I "$S/04_station_metrics.py"
  python3 -I "$S/04b_canswe.py"
fi
python3 -I "$S/05_areas_outcome.py"
python3 -I "$S/06_panel.py"
python3 -I "$S/07_analysis.py"
python3 -I "$S/08_run_windows.py"
