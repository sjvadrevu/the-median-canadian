#!/bin/bash
# Download SCANFI v2 biomass 2015 and 2020 one at a time, sum over cells burned 2016-2022, delete the raster.
set -e
cd "$(dirname "$0")"
B=https://ftp.maps.canada.ca/pub/nrcan_rncan/Forests_Foret/SCANFI/v2
for y in 2015 2020; do
  f=../raw/scanfi/SCANFI_att_biomass_${y}_v2_20260119.tif
  curl -sS -o $f $B/SCANFI_att_biomass_${y}_v2_20260119.tif
  python3 02_scanfi_biomass.py $f bio${y}_1622 cells_1622.pkl > ../work/log_02_bio${y}_1622.txt 2>&1
  rm -f $f
done
