#!/usr/bin/env bash
# econ_fetch.sh SUBDIR NAME URL
# Downloads URL into raw/econ/SUBDIR/NAME and appends a log line to work/econ_downloads.tsv
# (local_path, url, accessed_utc, http_code, bytes, sha256). Used for every econ_ download.
set -u
BASE=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/costs-full
SUB="$1"; NAME="$2"; URL="$3"
DIR="$BASE/raw/econ/$SUB"
mkdir -p "$DIR"
OUT="$DIR/$NAME"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
CODE=$(curl -sS -L --max-time 180 --retry 2 --retry-delay 3 \
  -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" \
  -o "$OUT" -w "%{http_code}" "$URL" 2>>"$BASE/work/econ_fetch_errors.log")
BYTES=$( [ -f "$OUT" ] && stat -c %s "$OUT" || echo 0 )
SHA=$( [ -f "$OUT" ] && sha256sum "$OUT" | cut -c1-16 || echo none )
printf "%s\t%s\t%s\t%s\t%s\t%s\n" "raw/econ/$SUB/$NAME" "$URL" "$TS" "$CODE" "$BYTES" "$SHA" >> "$BASE/work/econ_downloads.tsv"
echo "$CODE $BYTES raw/econ/$SUB/$NAME"
