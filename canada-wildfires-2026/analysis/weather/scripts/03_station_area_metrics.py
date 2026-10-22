"""Station 2026 vs own history; province / fire management area summaries;
daily share of stations at extreme FWI; station GeoJSON.

Inputs: work/site_year.pkl, work/site_meta.pkl, work/site_daily.pkl (from 02),
data/geo/fma_v2.gpkg (via work/fma_simple.gpkg from 00_simplify_fma.py).
Outputs (analysis/weather/): station_extreme_days.csv, area_weather_2026.csv,
daily_extreme_share.csv, stations_2026_anomaly.geojson, work/summary_03.json
"""
import json
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

W = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(W, "analysis", "weather")
WK = os.path.join(OUT, "work")
TAG = os.environ.get("TAG", "")  # e.g. _nothread for the unthreaded sensitivity run
if TAG:
    OUT = os.path.join(WK, "sens" + TAG)
    os.makedirs(OUT, exist_ok=True)
EXTREME = 30.0
S = {}

sy = pd.read_pickle(os.path.join(WK, f"site_year{TAG}.pkl"))
sm = pd.read_pickle(os.path.join(WK, f"site_meta{TAG}.pkl"))
daily = pd.read_pickle(os.path.join(WK, f"site_daily{TAG}.pkl"))
d26 = daily[daily["year"] == 2026]
sm["share_2026_days_from_other_id"] = (d26["aes"].astype(str) != d26["site"]).groupby(d26["site"]).mean().reindex(sm.index)

# ---------------- assign province / FMA (non-park rows tile each province)
fma = gpd.read_file(os.path.join(W, "analysis", "weather", "work", "fma_simple.gpkg"))  # built by 00_simplify_fma.py
fma = fma[~fma["agency"].str.contains("Parks Canada")][["fma_id", "area_name", "province", "area_level", "geometry"]]
pts = gpd.GeoDataFrame(sm[["lon", "lat"]].copy(), geometry=gpd.points_from_xy(sm["lon"], sm["lat"]), crs="EPSG:4326").to_crs(fma.crs)
j = gpd.sjoin_nearest(pts, fma, how="left", distance_col="dist_to_fma_m")
j = j[~j.index.duplicated(keep="first")]
sm = sm.join(j[["fma_id", "area_name", "province", "area_level", "dist_to_fma_m"]])
# stations far outside Canada (e.g. USA border stations) are dropped
sm["in_canada"] = sm["dist_to_fma_m"] < 20000
S["sites_dropped_outside_canada"] = int((~sm["in_canada"]).sum())


def station_table(rule_col):
    st = sm[sm[rule_col] & sm["in_canada"]].copy()
    q = sy[sy["qualifies"] & sy["site"].isin(st.index)]
    for lab, a, b in [("9120", 1991, 2020), ("9125", 1991, 2025)]:
        g = q[q["year"].between(a, b)].groupby("site")
        st[f"normal_extreme_{lab}"] = g["extreme_days"].mean()
        st[f"normal_high_plus_{lab}"] = g["high_plus_days"].mean()
        st[f"max_extreme_{lab}"] = g["extreme_days"].max()
    y26 = sy[sy["year"] == 2026].set_index("site")
    st["extreme_2026"] = y26["extreme_days"].reindex(st.index)
    st["high_plus_2026"] = y26["high_plus_days"].reindex(st.index)
    # rank among qualifying years 1991-2026 (1 = most days); ties share the best rank
    qq = q[q["year"].between(1991, 2026)].copy()
    for v in ["extreme_days", "high_plus_days"]:
        qq["r"] = qq.groupby("site")[v].rank(ascending=False, method="min")
        qq["rs"] = qq.groupby("site")[v].rank(ascending=False, method="max")  # strict
        r26 = qq[qq["year"] == 2026].set_index("site")
        short = "extreme" if v == "extreme_days" else "high_plus"
        st[f"rank_{short}_2026"] = r26["r"].reindex(st.index)
        st[f"rank_{short}_2026_strict"] = r26["rs"].reindex(st.index)
    st["n_years_ranked"] = qq.groupby("site").size().reindex(st.index)
    ok = st["qual_2026"]
    for short in ["extreme", "high_plus"]:
        n = st[f"normal_{short}_9120"]
        st[f"ratio_{short}_2026_vs_9120"] = np.where(ok & (n > 0), st[f"{short}_2026"] / n, np.nan)
        st[f"anom_{short}_2026_vs_9120"] = np.where(ok, st[f"{short}_2026"] - n, np.nan)
        st[f"ratio_{short}_2026_vs_9125"] = np.where(ok & (st[f"normal_{short}_9125"] > 0), st[f"{short}_2026"] / st[f"normal_{short}_9125"], np.nan)
        st[f"record_{short}_2026"] = np.where(ok, st[f"rank_{short}_2026"] == 1, np.nan)
        st[f"record_{short}_2026_outright"] = np.where(ok, (st[f"rank_{short}_2026_strict"] == 1) & (st[f"{short}_2026"] > 0), np.nan)
        # tied record at zero days is not counted as a record
        st[f"record_{short}_2026"] = np.where(ok, (st[f"rank_{short}_2026"] == 1) & (st[f"{short}_2026"] > 0), np.nan)
    for c in ["extreme_2026", "high_plus_2026"]:
        st.loc[~ok, c] = np.nan
    return st


st = station_table("consistent")
st_rel = station_table("consistent_relaxed")
S["consistent_sites"] = int(len(st))
S["consistent_sites_2026_qualifying"] = int(st["qual_2026"].sum())
S["relaxed_sites"] = int(len(st_rel))
S["relaxed_sites_2026_qualifying"] = int(st_rel["qual_2026"].sum())

cols = ["name", "province", "area_name", "fma_id", "lon", "lat", "n_ids", "member_ids", "n_qual_1991_2020",
        "n_qual_1991_2025", "share_2026_days_from_other_id", "cov_jja_2026", "cov_mjjas_2026", "qual_2026",
        "extreme_2026", "normal_extreme_9120", "normal_extreme_9125", "max_extreme_9125",
        "ratio_extreme_2026_vs_9120", "ratio_extreme_2026_vs_9125", "anom_extreme_2026_vs_9120",
        "rank_extreme_2026", "rank_extreme_2026_strict", "n_years_ranked", "record_extreme_2026", "record_extreme_2026_outright",
        "high_plus_2026", "normal_high_plus_9120", "normal_high_plus_9125", "ratio_high_plus_2026_vs_9120",
        "anom_high_plus_2026_vs_9120", "rank_high_plus_2026", "record_high_plus_2026"]
out = pd.concat([st[cols].assign(rule="strict_28of30"),
                 st_rel[~st_rel.index.isin(st.index)][cols].assign(rule="relaxed_24of30_only")])
out.index.name = "site_id"
out.round(3).to_csv(os.path.join(OUT, "station_extreme_days.csv"))


# ---------------- area summaries
def summarise(df):
    d = df[df["qual_2026"]]
    r = {"n_stations": len(d)}
    if len(d) == 0:
        return pd.Series(r)
    for s in ["extreme", "high_plus"]:
        r[f"median_ratio_{s}_9120"] = d[f"ratio_{s}_2026_vs_9120"].median()
        r[f"n_zero_normal_{s}"] = int((d[f"normal_{s}_9120"] == 0).sum())
        r[f"pooled_ratio_{s}_9120"] = d[f"{s}_2026"].sum() / d[f"normal_{s}_9120"].sum() if d[f"normal_{s}_9120"].sum() > 0 else np.nan
        r[f"median_anom_days_{s}_9120"] = d[f"anom_{s}_2026_vs_9120"].median()
        r[f"mean_{s}_days_2026"] = d[f"{s}_2026"].mean()
        r[f"mean_{s}_days_normal_9120"] = d[f"normal_{s}_9120"].mean()
        r[f"share_record_{s}"] = d[f"record_{s}_2026"].astype(float).mean()
        r[f"n_record_{s}"] = int(d[f"record_{s}_2026"].astype(float).sum())
    r["median_ratio_extreme_9125"] = d["ratio_extreme_2026_vs_9125"].median()
    return pd.Series(r)


rows = []
for rule, df in [("strict_28of30", st), ("relaxed_24of30", st_rel)]:
    a = summarise(df); a["level"] = "national"; a["area_id"] = "CA"; a["area_name"] = "Canada"; a["province"] = "CA"; a["rule"] = rule; rows.append(a)
    for p, g in df.groupby("province"):
        a = summarise(g); a["level"] = "province"; a["area_id"] = p; a["area_name"] = p; a["province"] = p; a["rule"] = rule; rows.append(a)
    for (fid, nm, p), g in df.groupby(["fma_id", "area_name", "province"]):
        a = summarise(g); a["level"] = "fma"; a["area_id"] = int(fid); a["area_name"] = nm; a["province"] = p; a["rule"] = rule; rows.append(a)
area = pd.DataFrame(rows)
# list every FMA, including those with no consistent station
allf = fma[["fma_id", "area_name", "province", "area_level"]].copy()
for rule in ["strict_28of30", "relaxed_24of30"]:
    have = set(area[(area["rule"] == rule) & (area["level"] == "fma")]["area_id"])
    miss = allf[~allf["fma_id"].isin(have)]
    area = pd.concat([area, pd.DataFrame({"level": "fma", "area_id": miss["fma_id"], "area_name": miss["area_name"],
                                          "province": miss["province"], "rule": rule, "n_stations": 0})])
lvl = dict(zip(allf["fma_id"], allf["area_level"]))
area["fma_level"] = [lvl.get(i) if l == "fma" else None for i, l in zip(area["area_id"], area["level"])]
lead = ["rule", "level", "area_id", "area_name", "province", "fma_level", "n_stations"]
area = area[lead + [c for c in area.columns if c not in lead]]
area["n_stations"] = area["n_stations"].fillna(0).astype(int)
area.round(3).to_csv(os.path.join(OUT, "area_weather_2026.csv"), index=False)

# ---------------- daily share of stations at extreme FWI
qual = sy[sy["qualifies"]][["site", "year"]]
use = st[st["qual_2026"]].index  # same station set each year, comparison is like for like
qual = qual[qual["site"].isin(use)]
dd = daily[daily["site"].isin(use)].merge(qual, on=["site", "year"])
dd = dd.join(st["province"], on="site")
den = qual.join(st["province"], on="site")
recs = []
for scope, sub, dn in [("CA", dd, den)] + [(p, dd[dd["province"] == p], den[den["province"] == p]) for p in sorted(st["province"].dropna().unique())]:
    nsy = dn.groupby("year").size()
    if (st.loc[use, "province"] == scope).sum() < 4 and scope != "CA":
        continue
    ext = sub[sub["fwi"] >= EXTREME].groupby(["year", "md"]).size()
    tab = ext.unstack("md").reindex(index=range(1991, 2027)).fillna(0)
    md_all = sorted(daily["md"].unique())
    tab = tab.reindex(columns=md_all).fillna(0)
    share = tab.div(nsy.reindex(tab.index), axis=0)
    base = share.loc[1991:2020]; base25 = share.loc[1991:2025]
    r = pd.DataFrame({"scope": scope, "md": md_all,
                      "share_2026": share.loc[2026].values,
                      "n_stations_2026": int(nsy.get(2026, 0)),
                      "normal_mean_9120": base.mean().values,
                      "normal_p90_9120": base.quantile(0.9).values,
                      "normal_max_9120": base.max().values,
                      "normal_mean_9125": base25.mean().values,
                      "mean_n_stations_per_year_9120": nsy.loc[1991:2020].mean()})
    recs.append(r)
ds = pd.concat(recs)
ds = ds[ds["md"] <= 1019]
ds["date"] = pd.to_datetime("2026" + ds["md"].astype(str).str.zfill(4), format="%Y%m%d")
ds = ds[ds["date"] >= "2026-04-01"]
for c in ["share_2026", "normal_mean_9120", "normal_mean_9125"]:
    ds[c + "_7d"] = ds.groupby("scope")[c].transform(lambda s: s.rolling(7, center=True, min_periods=4).mean())
ds["ratio_2026_to_normal_9120"] = ds["share_2026"] / ds["normal_mean_9120"].replace(0, np.nan)
ds = ds[["scope", "date", "share_2026", "share_2026_7d", "normal_mean_9120", "normal_mean_9120_7d", "normal_p90_9120",
         "normal_max_9120", "normal_mean_9125", "normal_mean_9125_7d", "ratio_2026_to_normal_9120", "n_stations_2026",
         "mean_n_stations_per_year_9120"]]
ds.round(4).to_csv(os.path.join(OUT, "daily_extreme_share.csv"), index=False)


def runs(mask, dates):
    out, start = [], None
    for m, d in zip(list(mask) + [False], list(dates) + [None]):
        if m and start is None:
            start = d; prev = d
        elif m:
            prev = d
        elif start is not None:
            out.append((start, prev, (prev - start).days + 1)); start = None
    return out


peaks = {}
for scope, g in ds.groupby("scope"):
    g = g.sort_values("date").reset_index(drop=True)
    i = g["share_2026"].idxmax(); i7 = g["share_2026_7d"].idxmax()
    above = runs(g["share_2026"] > g["normal_p90_9120"], g["date"])
    pk = g.loc[i, "date"]
    inrun = [r for r in above if r[0] <= pk <= r[1]]
    longest = max(above, key=lambda r: r[2]) if above else None
    peaks[scope] = {
        "n_stations": int(g["n_stations_2026"].iloc[0]),
        "peak_day": str(pk.date()), "peak_share": round(float(g.loc[i, "share_2026"]), 4),
        "normal_mean_on_peak_day": round(float(g.loc[i, "normal_mean_9120"]), 4),
        "peak_7d_centre": str(g.loc[i7, "date"].date()), "peak_7d_share": round(float(g.loc[i7, "share_2026_7d"]), 4),
        "normal_7d_on_that_centre": round(float(g.loc[i7, "normal_mean_9120_7d"]), 4),
        "run_above_p90_containing_peak": [str(inrun[0][0].date()), str(inrun[0][1].date()), inrun[0][2]] if inrun else None,
        "longest_run_above_p90": [str(longest[0].date()), str(longest[1].date()), longest[2]] if longest else None,
        "days_above_p90": int((g["share_2026"] > g["normal_p90_9120"]).sum()),
        "days_above_normal_max": int((g["share_2026"] > g["normal_max_9120"]).sum()),
        "station_days_share_2026": round(float(g["share_2026"].mean()), 4),
        "station_days_share_normal": round(float(g["normal_mean_9120"].mean()), 4),
        "max_normal_mean_day": str(g.loc[g["normal_mean_9120"].idxmax(), "date"].date()),
    }
S["daily_peaks"] = peaks

# ---------------- GeoJSON for the site
gj = st[st["qual_2026"]].copy()
g = gpd.GeoDataFrame(pd.DataFrame({
    "id": gj.index, "name": gj["name"].str.replace("+", " ", regex=False).str.title(), "prov": gj["province"], "fma": gj["area_name"],
    "ext26": gj["extreme_2026"].astype(int), "ext_norm": gj["normal_extreme_9120"].round(1),
    "ratio": gj["ratio_extreme_2026_vs_9120"].round(2), "anom": gj["anom_extreme_2026_vs_9120"].round(1),
    "rank": gj["rank_extreme_2026"].astype(int), "nyrs": gj["n_years_ranked"].astype(int),
    "record": gj["record_extreme_2026"].astype(bool),
    "hi26": gj["high_plus_2026"].astype(int), "hi_norm": gj["normal_high_plus_9120"].round(1)}),
    geometry=gpd.points_from_xy(gj["lon"].round(3), gj["lat"].round(3)), crs="EPSG:4326")
g.to_file(os.path.join(OUT, "stations_2026_anomaly.geojson"), driver="GeoJSON", COORDINATE_PRECISION=3)

# ---------------- summary numbers
q = st[st["qual_2026"]]
S["national"] = summarise(st).to_dict()
S["national_relaxed"] = summarise(st_rel).to_dict()
S["n_stations_2026_above_normal_extreme"] = int((q["anom_extreme_2026_vs_9120"] > 0).sum())
S["n_stations_2026_below_normal_extreme"] = int((q["anom_extreme_2026_vs_9120"] < 0).sum())
S["n_stations_2026_rank_top3_extreme"] = int((q["rank_extreme_2026"] <= 3).sum())
S["n_stations_2026_above_9120_max"] = int((q["extreme_2026"] > q["max_extreme_9125"]).sum())
S["top_ratio_stations"] = q.sort_values("anom_extreme_2026_vs_9120", ascending=False).head(10)[
    ["name", "province", "extreme_2026", "normal_extreme_9120", "rank_extreme_2026", "n_years_ranked"]].round(1).reset_index().to_dict("records")
S["coverage_2026_consistent"] = {"qualifying": int(q.shape[0]), "of": int(len(st)),
                                 "median_cov_jja": float(st["cov_jja_2026"].median())}
S["sites_by_province"] = st.groupby("province").size().to_dict()
# context: the same national statistics for every year 1991-2026 (same site set, own-year qualifying)
qq = sy[sy["qualifies"] & sy["site"].isin(st.index)].join(st["normal_extreme_9120"], on="site")
yr = qq.groupby("year").agg(n=("site", "size"), sum_ext=("extreme_days", "sum"), sum_norm=("normal_extreme_9120", "sum"))
yr["median_ratio"] = qq.assign(r=qq["extreme_days"] / qq["normal_extreme_9120"]).groupby("year")["r"].median()
yr["pooled_ratio"] = yr["sum_ext"] / yr["sum_norm"]
yr["mean_ext_days"] = yr["sum_ext"] / yr["n"]
yr = yr.loc[1991:2026]
yr.round(3).to_csv(os.path.join(OUT if TAG else WK, "national_by_year.csv"))
S["median_ratio_1991_2020_typical"] = float(yr.loc[1991:2020, "median_ratio"].median())
S["median_ratio_rank_2026_of_36"] = int(yr["median_ratio"].rank(ascending=False).loc[2026])
S["pooled_ratio_rank_2026_of_36"] = int(yr["pooled_ratio"].rank(ascending=False).loc[2026])
S["mean_ext_days_rank_2026_of_36"] = int(yr["mean_ext_days"].rank(ascending=False).loc[2026])
S["top5_pooled_years"] = yr["pooled_ratio"].sort_values(ascending=False).head(5).round(2).to_dict()
with open(os.path.join(OUT if TAG else WK, "summary_03.json"), "w") as f:
    json.dump(S, f, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
print(json.dumps(S, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))[:6000])
