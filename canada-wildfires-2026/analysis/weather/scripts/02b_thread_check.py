"""Homogeneity check for threaded sites: in years where two member IDs of a site
both have full core-season coverage (>= 90% of Jun-Aug days), compare their
extreme-day (FWI >= 30) counts. Output: work/thread_check.csv (one row per
site with overlap) and per-site share of 2026 days taken from a non-lead ID.
"""
import os
import sys

import numpy as np
import pandas as pd

W = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WK = os.path.join(W, "analysis", "weather", "work")
sm = pd.read_pickle(os.path.join(WK, "site_meta.pkl"))
sm = sm[sm["consistent_relaxed"]]
members = {a: s for s, ids in sm["member_ids"].items() for a in ids.split(";")}
obs = pd.read_pickle(os.path.join(WK, "obs.pkl"))
obs = obs[obs["aes"].isin(list(members)) & obs["fwi"].notna()]
obs["aes"] = obs["aes"].astype(str)
obs["year"] = obs["date"].dt.year
md = obs["date"].dt.month * 100 + obs["date"].dt.day
jja = obs[(md >= 601) & (md <= 831)].groupby(["aes", "year"]).size() / 92
ext = obs.assign(e=obs["fwi"] >= 30).groupby(["aes", "year"])["e"].sum()
ay = pd.DataFrame({"jja": jja, "ext": ext}).fillna(0).reset_index()
ay = ay[ay["jja"] >= 0.9]
ay["site"] = ay["aes"].map(members)
ay["lead"] = ay["aes"] == ay["site"]
rows = []
for s, g in ay.groupby("site"):
    L = g[g["lead"]].set_index("year")["ext"]
    for a, h in g[~g["lead"]].groupby("aes"):
        o = h.set_index("year")["ext"]
        yrs = L.index.intersection(o.index)
        if len(yrs) == 0:
            continue
        rows.append({"site": s, "other_id": a, "overlap_years": len(yrs),
                     "lead_mean_ext": L[yrs].mean(), "other_mean_ext": o[yrs].mean(),
                     "mean_diff_other_minus_lead": (o[yrs] - L[yrs]).mean(),
                     "mean_abs_diff": (o[yrs] - L[yrs]).abs().mean()})
tc = pd.DataFrame(rows)
tc.round(2).to_csv(os.path.join(WK, "thread_check.csv"), index=False)
print("pairs with overlap", len(tc), "sites", tc["site"].nunique() if len(tc) else 0)
if len(tc):
    print(tc[["overlap_years", "lead_mean_ext", "other_mean_ext", "mean_diff_other_minus_lead", "mean_abs_diff"]].describe().round(2))
