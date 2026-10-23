#!/bin/bash
# Download AAFC Canadian Drought Monitor monthly "areas of drought" shapefiles (April to September, 2002 to 2026).
# Source directory listing: https://agriculture.canada.ca/atlas/data_donnees/canadianDroughtMonitor/data_donnees/shp/areasOfDrought/YYYY/
# Files that the listing does not contain are logged as missing. Re-running skips files already downloaded.
C="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$C/raw/cdm"; mkdir -p "$OUT"
B=https://agriculture.canada.ca/atlas/data_donnees/canadianDroughtMonitor/data_donnees/shp/areasOfDrought
LOG="$OUT/download_log.csv"; echo "year,month,file,status,bytes" > "$LOG"
for y in $(seq 2002 2026); do
  lst=$(curl -sS --max-time 90 --retry 5 --retry-all-errors "$B/$y/" | grep -o 'href="cdm_[^"]*_drought_areas_shp.zip"' | sed 's/href="//;s/"//')
  for m in 04 05 06 07 08 09; do
    yy=${y:2:2}; f="cdm_${yy}${m}_drought_areas_shp.zip"
    if ! echo "$lst" | grep -q "$f"; then echo "$y,$m,$f,not_in_listing,0" >> "$LOG"; continue; fi
    if [ ! -s "$OUT/$f" ]; then curl -sS --max-time 300 --retry 5 --retry-all-errors -o "$OUT/$f" "$B/$y/$f"; fi
    if [ -s "$OUT/$f" ] && unzip -tq "$OUT/$f" >/dev/null 2>&1; then echo "$y,$m,$f,ok,$(stat -c %s "$OUT/$f")" >> "$LOG"; else echo "$y,$m,$f,failed,0" >> "$LOG"; rm -f "$OUT/$f"; fi
  done
done
echo done
