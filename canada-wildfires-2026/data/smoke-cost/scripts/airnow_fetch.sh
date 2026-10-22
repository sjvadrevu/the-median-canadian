#!/bin/bash
# Fetch AirNow daily_data.dat for dates missing from the May-Sep archive, keep PM2.5 lines only.
OUT=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/data/smoke-cost/raw/airnow/daily_extra
mkdir -p $OUT
python3 -c "
import datetime as dt
d=dt.date(2024,1,1)
while d<=dt.date(2026,10,19):
    if not (5<=d.month<=9): print(d.strftime('%Y%m%d'))
    d+=dt.timedelta(1)
" | xargs -P 8 -I{} bash -c 'f='$OUT'/pm25_{}.txt; [ -s $f ] && exit 0; y=$(echo {}|cut -c1-4); curl -sS --retry 3 --max-time 60 "https://files.airnowtech.org/airnow/$y/{}/daily_data.dat" -o '$OUT'/tmp_{}.dat && grep "|PM2.5-24hr|" '$OUT'/tmp_{}.dat > $f; rm -f '$OUT'/tmp_{}.dat'
ls $OUT | wc -l
