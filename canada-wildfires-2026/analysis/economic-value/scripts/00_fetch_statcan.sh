#!/bin/bash
# Poll StatCan full-table CSV downloads until each arrives as a real ZIP (site serves a maintenance HTML page when down).
OUT="$1"; shift
for i in $(seq 1 60); do
  left=0
  for p in "$@"; do
    f="$OUT/${p}-eng.zip"
    if [ -s "$f" ] && unzip -tq "$f" >/dev/null 2>&1; then continue; fi
    curl -sS -m 600 "https://www150.statcan.gc.ca/n1/tbl/csv/${p}-eng.zip" -o "$f.part" 2>>"$OUT/fetch.log"
    if unzip -tq "$f.part" >/dev/null 2>&1; then mv "$f.part" "$f"; echo "$(date -Is) got $p" >> "$OUT/fetch.log"; else rm -f "$f.part"; left=1; fi
  done
  [ $left -eq 0 ] && { echo "$(date -Is) all done" >> "$OUT/fetch.log"; exit 0; }
  echo "$(date -Is) attempt $i: some missing" >> "$OUT/fetch.log"
  sleep 120
done
