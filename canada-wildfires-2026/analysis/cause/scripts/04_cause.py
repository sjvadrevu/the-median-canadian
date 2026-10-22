"""Ignition cause: 2026 by agency and area; history 1990-2025 (NFD official tables and CNFDB points);
trends in the human share; distance to population for human vs lightning fires.

Outputs (analysis/cause/):
  cause_2026_by_agency.csv     official API totals by cause (count, ha) and the fire-list sums, per agency + CA
  cause_2026_by_area.csv       fire list points by area: count and ha by cause, shares, 1991-2020 point averages
  cause_by_year_national.csv   NFD and CNFDB national count/ha by cause and human shares, 1990-2025 (+2026)
  cause_by_year_province.csv   NFD by province-year (+2026 official)
  cause_trends.csv             Theil-Sen slope and Kendall test of human share (fires, area), 1990-2025
  cause_by_area_year.csv       CNFDB/2026 points: count and ha by cause per area-year (model input)
  cnfdb_completeness.csv       CNFDB point sums vs NFD by agency-year
  distance_to_population.csv   median and share-within distances by cause, period, province
"""
import json

import numpy as np
import pandas as pd

from common import (NFD_AREA_CAUSE, NFD_NUM_CAUSE, OFFICIAL_BY_CAUSE_2026, OUT, area_attrs, area_dir, log,
                    theil_sen)

D = area_dir()
fh = open(D / "log_04.txt", "w")
F = pd.read_pickle(D / "fires_all.pkl")
A = area_attrs()
CM = {"Human activity": "human", "Natural cause": "lightning", "Unspecified": "undetermined"}


def shares(df, n="n", ha="ha"):
    for k in ["n", "ha"]:
        cols = [f"{k}_{c}" for c in ["lightning", "human", "undetermined"]]
        tot = df[cols].sum(axis=1)
        known = df[f"{k}_lightning"] + df[f"{k}_human"]
        df[f"{k}_total"] = tot
        df[f"human_share_{k}_known"] = df[f"{k}_human"] / known.replace(0, np.nan)
        df[f"lightning_share_{k}_known"] = df[f"{k}_lightning"] / known.replace(0, np.nan)
        df[f"undetermined_share_{k}"] = df[f"{k}_undetermined"] / tot.replace(0, np.nan)
    return df


def wide(g, keys):
    t = g.groupby(keys + ["cause"]).agg(n=("size_ha", "size"), ha=("size_ha", "sum")).unstack("cause", fill_value=0)
    t.columns = [f"{a}_{b}" for a, b in t.columns]
    for k in ["n", "ha"]:
        for c in ["lightning", "human", "undetermined"]:
            if f"{k}_{c}" not in t:
                t[f"{k}_{c}"] = 0.0
    return shares(t.reset_index())


# ------------------------------------------------------------- 2026 official by agency
off = json.load(open(OFFICIAL_BY_CAUSE_2026))
rows = []
for r in off:
    row = dict(agency=r["agency_code"], date=r["date"], official_n_total=r["fire_count"]["total"],
               official_ha_total=r["area_burned"]["total"])
    for c, k in [("natural", "lightning"), ("human", "human"), ("undetermined", "undetermined")]:
        row[f"n_{k}"] = sum(v["cause"][c] for v in r["fire_count"]["response_type"].values())
        row[f"ha_{k}"] = sum(v["cause"][c] for v in r["area_burned"]["response_type"].values())
    rows.append(row)
O = pd.DataFrame(rows)
tot = O.drop(columns=["agency", "date"]).sum()
O = pd.concat([O, pd.DataFrame([dict(agency="CA", date=O.date.iloc[0], **tot)])], ignore_index=True)
O = shares(O)
f26 = F[F.year == 2026]
lst = wide(f26.assign(agency=f26.agency), ["agency"])
lst = pd.concat([lst, wide(f26.assign(agency="CA"), ["agency"])])
O = O.merge(lst[["agency", "n_total", "ha_total"]].rename(columns={"n_total": "list_n_cal2026", "ha_total": "list_ha_cal2026"}),
            on="agency", how="left")
O.to_csv(OUT / "cause_2026_by_agency.csv", index=False)
log(O[["agency", "n_total", "n_lightning", "n_human", "n_undetermined", "ha_total", "ha_lightning", "ha_human",
       "ha_undetermined", "human_share_n_known", "human_share_ha_known"]].round(3).to_string(), fh)

# ------------------------------------------------------------- area-year from points
ay = wide(F[F.fma_id > 0], ["fma_id", "year"])
ay.to_csv(OUT / "cause_by_area_year.csv", index=False)
a26 = ay[ay.year == 2026].drop(columns="year")
base = ay[(ay.year >= 1991) & (ay.year <= 2020)]
full = pd.MultiIndex.from_product([A.fma_id, range(1991, 2021)], names=["fma_id", "year"])
base = base.set_index(["fma_id", "year"]).reindex(full, fill_value=0).reset_index()
bm = base.groupby("fma_id")[["n_lightning", "n_human", "n_undetermined", "ha_lightning", "ha_human", "ha_undetermined"]].mean()
bm.columns = [f"avg9120_{c}" for c in bm.columns]
ar = A[["fma_id", "province", "area_name"]].merge(a26, on="fma_id", how="left").merge(bm.reset_index(), on="fma_id", how="left")
ar = ar.fillna({c: 0 for c in ar.columns if c.startswith(("n_", "ha_"))})
ar["ratio_n_lightning_vs_9120"] = ar.n_lightning / ar.avg9120_n_lightning.replace(0, np.nan)
ar["ratio_n_human_vs_9120"] = ar.n_human / ar.avg9120_n_human.replace(0, np.nan)
ar.to_csv(OUT / "cause_2026_by_area.csv", index=False)

# ------------------------------------------------------------- NFD official history
na = pd.read_csv(NFD_AREA_CAUSE, encoding="utf-8-sig")
nn = pd.read_csv(NFD_NUM_CAUSE, encoding="utf-8-sig")
na["cause"] = na.Cause.map(CM)
nn["cause"] = nn.Cause.map(CM)
pa = na.pivot_table(index=["Year", "ISO"], columns="cause", values="Area (hectares)", aggfunc="sum", fill_value=0)
pn = nn.pivot_table(index=["Year", "ISO"], columns="cause", values="Number", aggfunc="sum", fill_value=0)
pa.columns = [f"ha_{c}" for c in pa.columns]
pn.columns = [f"n_{c}" for c in pn.columns]
P = pa.join(pn, how="outer").fillna(0).reset_index().rename(columns={"Year": "year", "ISO": "province"})
# 2026 official (provinces, Parks Canada kept separate as PC)
o26 = O[O.agency != "CA"].rename(columns={"agency": "province"})[["province"] + [c for c in P.columns if c.startswith(("n_", "ha_"))]]
o26["year"] = 2026
P = shares(pd.concat([P, o26], ignore_index=True))
P.to_csv(OUT / "cause_by_year_province.csv", index=False)
nat_nfd = shares(P[P.province != "PC"].groupby("year")[[c for c in P.columns if c.startswith(("n_", "ha_")) and not c.endswith("total")]].sum().reset_index())
nat_nfd["series"] = "NFD (12 provinces/territories; 2026 = official API without Parks Canada)"
cn = F[(F.source == "CNFDB")]
nat_pts = wide(cn.assign(k=1), ["year"])
nat_pts["series"] = "CNFDB points (all agencies incl. Parks Canada)"
N = pd.concat([nat_nfd, nat_pts], ignore_index=True)
N.to_csv(OUT / "cause_by_year_national.csv", index=False)

# ------------------------------------------------------------- trends
tr = []
for prov, g in [("CA", nat_nfd)] + [(p, P[P.province == p]) for p in sorted(P.province.unique()) if p != "PC"]:
    g = g[(g.year >= 1990) & (g.year <= 2025)]
    for var in ["human_share_n_known", "human_share_ha_known", "n_human", "n_lightning", "ha_human", "ha_lightning"]:
        t = theil_sen(g.year, g[var])
        g9120 = g[(g.year >= 1991) & (g.year <= 2020)][var]
        v26 = (nat_nfd if prov == "CA" else P[P.province == prov]).set_index("year")[var].get(2026, np.nan)
        tr.append(dict(scope=prov, variable=var, slope_per_decade=t["slope"] * 10, lo95_per_decade=t["lo"] * 10,
                       hi95_per_decade=t["hi"] * 10, kendall_tau=t["tau"], p_value=t["p"], n_years=t["n"],
                       mean_1990s=g[(g.year >= 1990) & (g.year <= 1999)][var].mean(),
                       mean_2016_2025=g[(g.year >= 2016)][var].mean(),
                       mean_1991_2020=g9120.mean(), median_1991_2020=g9120.median(), value_2026=v26,
                       rank_2026_high_of_37=int((pd.concat([g[var], pd.Series([v26])]) > v26).sum() + 1) if pd.notna(v26) else np.nan))
T = pd.DataFrame(tr)
T.to_csv(OUT / "cause_trends.csv", index=False)
log(T[T.scope == "CA"].round(4).to_string(), fh)

# ------------------------------------------------------------- CNFDB completeness vs NFD
cp = cn.groupby(["year", "agency"]).agg(cnfdb_n=("size_ha", "size"), cnfdb_ha=("size_ha", "sum")).reset_index()
cp = cp.merge(P[["year", "province", "n_total", "ha_total"]].rename(columns={"province": "agency", "n_total": "nfd_n", "ha_total": "nfd_ha"}),
              on=["year", "agency"], how="outer")
cp["ratio_n"] = cp.cnfdb_n / cp.nfd_n
cp["ratio_ha"] = cp.cnfdb_ha / cp.nfd_ha
cp.to_csv(OUT / "cnfdb_completeness.csv", index=False)
bad = cp[(cp.year <= 2025) & (cp.agency != "PC") & ((cp.ratio_ha < 0.5) | (cp.ratio_ha > 2)) & (cp.nfd_ha > 10000)]
log("CNFDB agency-years with point ha <50% or >200% of NFD (NFD > 10,000 ha):\n" + bad.round(2).to_string(), fh)

# ------------------------------------------------------------- distance to population
F["period"] = np.where(F.year == 2026, "2026", np.where(F.year >= 2016, "2016-2025", np.where(F.year >= 1991, "1991-2015", "1990")))
F.loc[F.year == 1990, "period"] = "1991-2015"           # 1990 folded in; label kept short
rows = []
for (per, prov), g in list(F.groupby(["period", "province"])) + [((p, "CA"), g) for p, g in F.groupby("period")]:
    for cz, h in g.groupby("cause"):
        dd = h.dist_da_km.dropna()
        if len(dd) == 0:
            continue
        w = h.size_ha.fillna(0)
        rows.append(dict(period=per, province=prov, cause=cz, n=len(dd), median_km_da=dd.median(),
                         p25_km_da=dd.quantile(.25), p75_km_da=dd.quantile(.75),
                         share_within_5km=(dd <= 5).mean(), share_within_10km=(dd <= 10).mean(),
                         share_within_25km=(dd <= 25).mean(), share_beyond_50km=(dd > 50).mean(),
                         ha=w.sum(), ha_share_within_10km=w[h.dist_da_km <= 10].sum() / w.sum() if w.sum() > 0 else np.nan,
                         ha_share_beyond_50km=w[h.dist_da_km > 50].sum() / w.sum() if w.sum() > 0 else np.nan,
                         median_km_popcentre=h.dist_popcentre_km.median()))
DP = pd.DataFrame(rows)
DP.to_csv(OUT / "distance_to_population.csv", index=False)
log(DP[DP.province == "CA"].round(3).to_string(), fh)
