#!/bin/bash
# Thread 2: fetch the 1/16 overview (.ovr, 480 m, decimated) of SCANFI v2 black spruce, jack pine and total crown
# closure for 1985-2020. Full 30 m rasters are 3-6 GB each and do not fit on disk.
T=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/threads
mkdir -p $T/raw/scanfi_ovr; cd $T/raw/scanfi_ovr
U=https://ftp.maps.canada.ca/pub/nrcan_rncan/Forests_Foret/SCANFI/v2
for y in 1985 1990 1995 2000 2005 2010 2015 2020; do
  for l in spsCC_blackSpruce spsCC_jackPine att_closure; do
    f=SCANFI_${l}_${y}_v2_20260119.tif.ovr
    [ -s $f ] || curl -s -m 600 --retry 3 -o $f $U/$f
  done
done
curl -s -m 60 -o SCANFI_v2_blackSpruce_2020.tif.aux.xml $U/SCANFI_spsCC_blackSpruce_2020_v2_20260119.tif.aux.xml
ls -la | head -40; du -sh .
