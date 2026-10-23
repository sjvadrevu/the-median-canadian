#!/bin/bash
# Thread 3: fetch CWFIS annual hotspot archives 2023-2025, keep slim Canada-bbox columns, delete the zip.
set -e
T=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/threads
mkdir -p $T/raw/hotspots_archive
cd $T/raw/hotspots_archive
for y in 2023 2024 2025; do
  if [ -f hotspots_${y}_slim.csv.gz ]; then continue; fi
  curl -s -m 1800 --retry 3 -o ${y}_hotspots.zip https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/archive/${y}_hotspots.zip
  unzip -l ${y}_hotspots.zip > ${y}_listing.txt
  python3 -I $T/scripts/t3a_slim.py ${y}_hotspots.zip hotspots_${y}_slim.csv.gz
  rm -f ${y}_hotspots.zip
done
ls -la
