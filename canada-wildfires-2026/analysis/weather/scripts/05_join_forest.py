"""Join the 2026 fire-weather anomaly per fire management area with the share of
forest burned from the forest analyst (analysis/forest/), when available.

Always writes fma_weather_for_join.csv (key fma_id): station anomaly (strict and
relaxed rule) and grid anomaly per FMA. If a CSV in analysis/forest/ has an
fma_id column and a forest-burned share column, writes
weather_vs_forest_by_fma.csv and Spearman rank correlations to
work/summary_05.json.
"""
import glob
import json
import os
import re
import sys

import pandas as pd
from scipy.stats import spearmanr

W = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(W, "analysis", "weather")
aw = pd.read_csv(os.path.join(OUT, "area_weather_2026.csv"))
aw = aw[aw["level"] == "fma"].copy()
aw["fma_id"] = aw["area_id"].astype(int)
keep = ["n_stations", "median_ratio_extreme_9120", "median_anom_days_extreme_9120", "pooled_ratio_extreme_9120",
        "mean_extreme_days_2026", "mean_extreme_days_normal_9120", "share_record_extreme", "median_ratio_high_plus_9120"]
s = aw[aw["rule"] == "strict_28of30"].set_index("fma_id")[["area_name", "province", "fma_level"] + keep]
r = aw[aw["rule"] == "relaxed_24of30"].set_index("fma_id")[keep].add_suffix("_relaxed")
t = s.join(r)
g = pd.read_csv(os.path.join(OUT, "area_grid_check.csv"))
g = g[g["level"] == "fma"].assign(fma_id=lambda x: x["area_id"].astype(int)).set_index("fma_id")
t = t.join(g[["n_cells", "grid_mean_extreme_2026", "grid_mean_extreme_2018_2025", "grid_ratio_of_means", "grid_mean_anom_days",
              "grid_share_cells_2026_highest_2018_2026"]])
t.round(3).to_csv(os.path.join(OUT, "fma_weather_for_join.csv"))

S = {"forest_file": None}
cands = []
for f in glob.glob(os.path.join(W, "analysis", "forest", "**", "*.csv"), recursive=True):
    try:
        h = pd.read_csv(f, nrows=5)
    except Exception:
        continue
    if "fma_id" in h.columns:
        cols = [c for c in h.columns if re.search(r"forest", c, re.I) and re.search(r"share|pct|frac|percent", c, re.I)]
        if cols:
            cands.append((f, cols))
# deterministic choice: the forest analysis main table if present (glob order is arbitrary)
cands.sort(key=lambda c: (os.path.basename(c[0]) != "fma_2026_table.csv", c[0]))
if cands:
    f, cols = cands[0]
    fo = pd.read_csv(f)
    col = cols[0]
    S["forest_file"] = f; S["forest_column"] = col; S["all_candidates"] = cands
    j = t.join(fo.groupby("fma_id")[col].first(), how="inner")
    j.round(4).to_csv(os.path.join(OUT, "weather_vs_forest_by_fma.csv"))
    res = {}
    for xc, mincond in [("median_anom_days_extreme_9120", "n_stations"), ("median_ratio_extreme_9120", "n_stations"),
                        ("median_anom_days_extreme_9120_relaxed", "n_stations_relaxed"),
                        ("grid_mean_anom_days", "n_cells"), ("grid_ratio_of_means", "n_cells")]:
        d = j[(j[mincond] > 0)][[xc, col]].dropna()
        if len(d) >= 5:
            rr = spearmanr(d[xc], d[col])
            res[xc] = {"n_fma": len(d), "spearman_rho": round(float(rr.statistic), 3), "p": round(float(rr.pvalue), 4)}
    S["spearman"] = res
else:
    S["note"] = "No forest-burned share by fma_id found in analysis/forest/ at run time; join fma_weather_for_join.csv on fma_id later."
with open(os.path.join(OUT, "work", "summary_05.json"), "w") as fh:
    json.dump(S, fh, indent=1, default=str)
print(json.dumps(S, indent=1, default=str))
