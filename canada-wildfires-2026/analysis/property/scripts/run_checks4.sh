#!/bin/bash
# Denare Beach 2025 and Enterprise 2023 check events, split into 20 km footprint cells (as 08_features_2026.py) because
# the single-grid runs exceed memory; sequential, one process. Cells merged by 05c_merge_cells.py.
S=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/property/scripts; Wk=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/property/work
cd /tmp; ulimit -v 4800000
for f in $Wk/fp_denare2025c*.csv.gz; do e=$(basename $f .csv.gz); e=${e#fp_}; python3 -I $S/05_event_features.py $e $f 2025-06-15 2025-08-31 2025; echo "END $e $?"; done
for f in $Wk/fp_enterprise2023c*.csv.gz; do e=$(basename $f .csv.gz); e=${e#fp_}; python3 -I $S/05_event_features.py $e $f 2023-08-20 2023-09-30 2023; echo "END $e $?"; done
echo ALLDONE
