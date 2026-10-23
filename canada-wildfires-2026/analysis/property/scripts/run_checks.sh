#!/bin/bash
# Sentinel-2 features for the transfer-check events (post-fire windows chosen from NBAC / agency fire dates)
S=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/property/scripts; Wk=${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/property/work
cd /tmp
python3 -I $S/05_event_features.py jasper2024 $Wk/fp_jasper.csv.gz 2024-08-01 2024-09-30 2024 ${WILDFIRE_ROOT:-$(cd "$(dirname "$0")/../../.." && pwd)}/analysis/property/raw/jasper/jasper_damage_assessment_structures.geojson Status
python3 -I $S/05_event_features.py tantallon2023 $Wk/fp_tantallon2023.csv.gz 2023-06-05 2023-07-20 2023
python3 -I $S/05_event_features.py barrington2023 $Wk/fp_barrington2023.csv.gz 2023-06-15 2023-08-15 2023
python3 -I $S/05_event_features.py mcdougall2023 $Wk/fp_mcdougall2023.csv.gz 2023-08-25 2023-10-15 2023
python3 -I $S/05_event_features.py bushcreek2023 $Wk/fp_bushcreek2023.csv.gz 2023-08-28 2023-10-15 2023
python3 -I $S/05_event_features.py enterprise2023 $Wk/fp_enterprise2023.csv.gz 2023-08-20 2023-09-30 2023
python3 -I $S/05_event_features.py denare2025 $Wk/fp_denare2025.csv.gz 2025-06-15 2025-08-31 2025
python3 -I $S/05_event_features.py lacdubonnet2025 $Wk/fp_lacdubonnet2025.csv.gz 2025-05-25 2025-07-15 2025
python3 -I $S/05_event_features.py baldrange2026 $Wk/fp_baldrange2026.csv.gz 2026-09-19 2026-10-20 2026
python3 -I $S/05_event_features.py bradleycreek2026 $Wk/fp_bradleycreek2026.csv.gz 2026-09-19 2026-10-20 2026
