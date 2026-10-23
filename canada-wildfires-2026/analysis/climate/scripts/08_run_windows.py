"""How unusual was the 2023-2026 run? Rank of the 4-year mean 2023-2026 among all 4-year windows.

Station variables (climate_panel.csv): for each region and year, the median across areas of the area
value; then the 4-year running mean of that series; rank of the window 2023-2026 among the 33 windows
starting 1991..2023 (1 = most fire-favouring: least snow, earliest melt, warmest, driest).
CanSWE has no 2026, so its window is 2022-2025 vs 1991-2025 windows (flagged).
Indices (indices_by_fire_year.csv): rank of the 2023-2026 mean among the 73 windows 1951-2026,
1 = highest value.
Also, per region, the number of years in 2023-2026 that were on the fire-favouring side of the
1991-2020 median of the regional series.
Outputs: run_windows_2023_2026.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd

from common import OUT, log, out_dir, area_dir

D = area_dir()
fh = open(D / "log_08.txt", "w")
P = pd.read_csv(out_dir() / "climate_panel.csv")
FIRE_DIR = {"snowfall_pct": -1, "snow_cover_days_anom": -1, "max_snow_depth_pct": -1, "melt_anom_days": -1,
            "swe_apr1_pct": -1, "t_amj_anom_c": 1, "p_amj_pct": -1, "p_jja_prev_pct": -1, "p_son_prev_pct": -1,
            "p_ndjfm_pct": -1, "p_12m_pct": -1, "months_since_wet": 1}
rows = []
for rname in ["Canada", "BC", "Prairies", "Ontario", "Quebec", "North", "Atlantic"]:
    sub = P if rname == "Canada" else P[P.region == rname]
    for v, sgn in FIRE_DIR.items():
        s = sub.groupby("year")[v].median()
        last = 2025 if v == "swe_apr1_pct" else 2026
        s = s.loc[1991:last]
        w = s.rolling(4).mean().dropna()           # labelled by end year
        if last not in w.index:
            continue
        x = w * sgn
        base = s.loc[1991:2020]
        yrs = s.loc[last - 3:last]
        rows.append(dict(kind="station", region=rname, variable=v, window=f"{last-3}-{last}",
                         value=w[last], rank_fire_favouring=int((x > x[last]).sum() + 1), n_windows=len(w),
                         median_1991_2020=base.median(),
                         years_on_fire_side=int(((yrs - base.median()) * sgn > 0).sum()),
                         years_available=int(yrs.notna().sum())))
I = pd.read_csv(OUT / "indices_by_fire_year.csv").set_index("fire_year")
for v in ["oni_djf", "pdo_djf", "ao_djf", "ao_jfm", "nao_djf", "oni_mam", "pdo_mam", "ao_mam", "nao_mam"]:
    s = I[v].dropna()
    w = s.rolling(4).mean().dropna()
    base = s.loc[1991:2020]
    rows.append(dict(kind="index", region="global", variable=v, window="2023-2026", value=w[2026],
                     rank_high=int((w > w[2026]).sum() + 1), n_windows=len(w), median_1991_2020=base.median(),
                     years_above_median=int((s.loc[2023:2026] > base.median()).sum()), years_available=4))
R = pd.DataFrame(rows)
R.to_csv(out_dir() / "run_windows_2023_2026.csv", index=False, float_format="%.4g")
log(R.to_string(), fh)
