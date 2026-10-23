#!/bin/bash
# Rerun the response analysis end to end. 01 downloads NRN roads (skips provinces already in work/).
# 02 caches work/fires_noroad.pkl; delete it to rebuild the fire table from scratch.
set -e
cd "$(dirname "$0")"
for s in 01_roads 02_fire_table 03_zones 03b_combine 04_escape_speed 05_detection_lag 06_access 07_early_control 08_cost_note 09_province_table; do
  echo "== $s"; python3 -u $s.py > ../work/run_$s.out 2>&1
done
