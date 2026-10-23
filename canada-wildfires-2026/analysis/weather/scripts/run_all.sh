#!/bin/sh
# Reproduce the weather analysis. Usage: sh run_all.sh /path/to/wildfire
set -e
W=${1:-$(cd "$(dirname "$0")/../../.." && pwd)}
S="$W/analysis/weather/scripts"
mkdir -p "$W/analysis/weather/work"
python3 -I "$S/00_simplify_fma.py" "$W"
python3 -I "$S/01_load_stations.py" "$W"
python3 -I "$S/02_station_sites.py" "$W"                                # threaded sites (5 km)
THREAD_KM=0.01 TAG=_nothread python3 -I "$S/02_station_sites.py" "$W"   # sensitivity: no threading
python3 -I "$S/02b_thread_check.py" "$W"
python3 -I "$S/03_station_area_metrics.py" "$W"
TAG=_nothread python3 -I "$S/03_station_area_metrics.py" "$W"
python3 -I "$S/04_grid_check.py" "$W"
python3 -I "$S/05_join_forest.py" "$W"
