"""Thread station IDs into sites, apply the consistency rule, count extreme days.

Threading: CWFIS station IDs (aes) change when a station is replaced (e.g. an
airport station replaced by a new automatic station nearby). IDs whose latest
coordinates are within THREAD_KM (default 5 km) of each other form one site.
For each site-day the FWI is taken from the member ID with the most FWI values
overall that has a computed FWI that day (other IDs only fill gaps).

Coverage rule (a site-year qualifies): FWI computed on >= 90% of days
Jun 1 - Aug 31 AND >= 75% of days May 1 - Sep 30. April and October FWI is
often not computed because the CWFIS start-up waits for snow melt, so an
April 1 - September 30 completeness test fails for nearly every station
(0 stations pass 90% in 28 of 30 years; tested).
Consistent site: qualifying in >= 28 of the 30 years 1991-2020 (strict);
>= 24 of 30 (relaxed, sensitivity only).

Season for counting: Apr 1 - Oct 19 every year. Days with no computed FWI count
as not extreme (pre start-up days are low-danger by construction).

Outputs: work/site_year.pkl, work/site_meta.pkl, work/site_daily.pkl
"""
import os
import sys

import numpy as np
import pandas as pd

W = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WK = os.path.join(W, "analysis", "weather", "work")
THREAD_KM = float(os.environ.get("THREAD_KM", 5))
TAG = os.environ.get("TAG", "")
EXTREME, HIGH = 30.0, 19.0

obs = pd.read_pickle(os.path.join(WK, "obs.pkl"))
ids = pd.read_pickle(os.path.join(WK, "ids.pkl"))
obs = obs[obs["fwi"].notna()]
cnt = obs.groupby("aes", observed=True).size()
ids["nfwi"] = cnt.reindex(ids.index).fillna(0)
ids["y0"] = obs.groupby("aes", observed=True)["date"].min().dt.year.reindex(ids.index)
ids["y1"] = obs.groupby("aes", observed=True)["date"].max().dt.year.reindex(ids.index)
ids = ids[ids["lon"].notna() & (ids["nfwi"] > 0)]

# ---- threading (union-find on pairs closer than THREAD_KM)
lat = np.radians(ids["lat"].to_numpy(float)); lon = np.radians(ids["lon"].to_numpy(float))
parent = np.arange(len(ids))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


for i in range(len(ids)):
    a = np.sin((lat - lat[i]) / 2) ** 2 + np.cos(lat[i]) * np.cos(lat) * np.sin((lon - lon[i]) / 2) ** 2
    d = 6371 * 2 * np.arcsin(np.sqrt(a))
    for j in np.where((d < THREAD_KM) & (np.arange(len(ids)) > i))[0]:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri
ids["grp"] = [find(i) for i in range(len(ids))]
lead = ids.sort_values("nfwi", ascending=False).groupby("grp").head(1)
ids["site"] = ids["grp"].map(dict(zip(lead["grp"], lead.index)))
ids["priority"] = ids.groupby("site")["nfwi"].rank(ascending=False, method="first").astype(np.int16)
print("ids", len(ids), "sites", ids["site"].nunique(), "multi-id sites", int((ids.groupby("site").size() > 1).sum()), flush=True)

obs = obs[obs["aes"].isin(ids.index)]
aes = obs["aes"].astype(str)
site_cat = pd.CategoricalDtype(sorted(ids["site"].unique()))
obs["site"] = aes.map(ids["site"]).astype(site_cat)
obs["priority"] = aes.map(ids["priority"]).astype(np.int16)
del aes
obs = obs.sort_values(["site", "date", "priority"])
daily = obs.drop_duplicates(["site", "date"], keep="first")[["site", "date", "fwi", "aes"]].reset_index(drop=True)
del obs
daily["year"] = daily["date"].dt.year.astype(np.int16)
daily["md"] = (daily["date"].dt.month * 100 + daily["date"].dt.day).astype(np.int16)
print("site-days with FWI", len(daily), flush=True)

# ---- coverage per site-year
md = daily["md"]
core = daily[(md >= 601) & (md <= 831)].groupby(["site", "year"], observed=True).size() / 92
wide = daily[(md >= 501) & (md <= 930)].groupby(["site", "year"], observed=True).size() / 153
ext = daily.assign(e=daily["fwi"] >= EXTREME, h=daily["fwi"] >= HIGH).groupby(["site", "year"], observed=True)[["e", "h"]].sum()
full = pd.MultiIndex.from_product([list(site_cat.categories), range(1990, 2027)], names=["site", "year"])
sy = pd.DataFrame(index=full)
sy["cov_jja"] = core.set_axis(core.index.set_levels(core.index.levels[0].astype(str), level=0)).reindex(full).fillna(0).values
sy["cov_mjjas"] = wide.set_axis(wide.index.set_levels(wide.index.levels[0].astype(str), level=0)).reindex(full).fillna(0).values
e2 = ext.set_axis(ext.index.set_levels(ext.index.levels[0].astype(str), level=0))
sy["extreme_days"] = e2["e"].reindex(full).fillna(0).values
sy["high_plus_days"] = e2["h"].reindex(full).fillna(0).values
sy["qualifies"] = (sy["cov_jja"] >= 0.90) & (sy["cov_mjjas"] >= 0.75)
sy = sy.reset_index()

q = sy[sy["qualifies"]]
sm = ids.loc[sorted(ids["site"].unique()), ["name", "wmo", "lon", "lat", "prov_fwi", "agency_oct2026"]].copy()
sm["n_ids"] = ids.groupby("site").size()
sm["member_ids"] = ids.reset_index().groupby("site")["aes"].apply(lambda s: ";".join(sorted(s)))
sm["n_qual_1991_2020"] = q[q["year"].between(1991, 2020)].groupby("site").size().reindex(sm.index).fillna(0).astype(int)
sm["n_qual_1991_2025"] = q[q["year"].between(1991, 2025)].groupby("site").size().reindex(sm.index).fillna(0).astype(int)
c26 = sy[sy["year"] == 2026].set_index("site")
sm["cov_jja_2026"] = c26["cov_jja"].reindex(sm.index)
sm["cov_mjjas_2026"] = c26["cov_mjjas"].reindex(sm.index)
sm["qual_2026"] = c26["qualifies"].reindex(sm.index).fillna(False).astype(bool)
sm["consistent"] = sm["n_qual_1991_2020"] >= 28
sm["consistent_relaxed"] = sm["n_qual_1991_2020"] >= 24
for col in ["consistent", "consistent_relaxed"]:
    print(col, int(sm[col].sum()), "with 2026 qualifying", int((sm[col] & sm["qual_2026"]).sum()), flush=True)
print("years qualifying among strict sites", q[q["site"].isin(sm.index[sm["consistent"]])].groupby("year").size().to_dict())

sy.to_pickle(os.path.join(WK, f"site_year{TAG}.pkl"))
sm.to_pickle(os.path.join(WK, f"site_meta{TAG}.pkl"))
keep = sm.index[sm["consistent_relaxed"]]
dd = daily[daily["site"].isin(keep)].copy()
dd["site"] = dd["site"].astype(str)
dd.to_pickle(os.path.join(WK, f"site_daily{TAG}.pkl"))
