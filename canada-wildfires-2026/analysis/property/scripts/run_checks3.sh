#!/bin/bash
# re-run (2026-10-21, after container restart) of the check events killed for memory; sequential, single process
S=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/property/scripts; Wk=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/property/work
cd /tmp; ulimit -v 4800000
python3 -I $S/05_event_features.py bushcreek2023 $Wk/fp_bushcreek2023.csv.gz 2023-08-28 2023-10-15 2023; echo "END bushcreek2023 $?"
python3 -I $S/05_event_features.py denare2025 $Wk/fp_denare2025.csv.gz 2025-06-15 2025-08-31 2025; echo "END denare2025 $?"
python3 -I $S/05_event_features.py enterprise2023 $Wk/fp_enterprise2023.csv.gz 2023-08-20 2023-09-30 2023; echo "END enterprise2023 $?"
