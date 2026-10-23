#!/bin/sh
# Reproduce analysis/climate-change. Single-threaded. Usage: sh run_all.sh
set -e
S=$(cd "$(dirname "$0")" && pwd)
R="$S/../raw/ahccd"
mkdir -p "$R"
B=https://eccc-opendata-01.collab.science.gc.ca/CDAS/products/AHCCD
for f in Homog_monthly_mean_temp_Gen3.zip Adj_monthly_total_prec.zip Adj_monthly_rain.zip Adj_monthly_snow.zip \
         Temperature_Stations_Gen3.xls Precipitation_Stations.xls Temperature_Documentation_Gen3.doc Precipitation_Documentation.doc; do
  [ -f "$R/$f" ] || curl -sS -o "$R/$f" "$B/$f"
done
[ -f "$R/ahccd_stations.json" ] || curl -sS -o "$R/ahccd_stations.json" "https://api.weather.gc.ca/collections/ahccd-stations/items?f=json&limit=2000"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python3 -I "$S/01_ahccd_parse.py"          # AHCCD stations near forested areas
python3 -I "$S/02_fill_monthly.py"         # extend with offset-corrected climate-daily, hold-out check
python3 -I "$S/03_season_climate.py"       # fire-season climate series, trends, ranks
python3 -I "$S/04_select_long_stations.py" # long-record hourly/daily sites
python3 -I "$S/05_download_long.py"        # noon hourly + daily downloads (resumable)
python3 -I "$S/06_cwfis_fwi_trend.py"      # CWFIS fixed-station extreme days 1990-2026
python3 -I "$S/07_area_burned_trend.py"    # area burned series and trends
python3 -I "$S/08_area_outcome.py"         # all-land ha per area 1972-2026
python3 -I "$S/09_sensitivity_counterfactual.py"   # panel sensitivity and 2023-2026 counterfactual
python3 -I "$S/10_compute_fwi.py"          # FWI from station weather 1953-2026
python3 -I "$S/11_snow_season.py"          # snow-cover days and melt date
python3 -I "$S/12_manifest.py"
