#!/bin/bash
# Run the cause analysis end to end. Optional: AREA_FILE=/path/to/areas.gpkg bash run_all.sh
# (same columns as data/geo/fma_all.gpkg; a new file gets its own work/areas_<hash>/ cache).
# Needs analysis/forest/work (grid, forest counts, burn rasters) and analysis/weather/work (site_year.pkl).
# Step 01 skips files already downloaded. Step 09 joins analysis/climate/climate_panel.csv when it exists.
set -e
cd "$(dirname "$0")"
bash 01_download_cdm.sh
for s in 02_areas 03_fires 04_cause 05_timing 06_drought 07_burn_history 08_weather_panel 09_model 10_run_2023_2026; do
  echo "== $s"; python3 $s.py
done
