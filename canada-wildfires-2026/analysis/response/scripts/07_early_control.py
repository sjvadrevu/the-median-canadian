"""Priority 5: early control over time, CNFDB 1990-2025 plus the 2026 agency list.

Per year (and province): share of fires whose final size is under 1 ha and under 10 ha (a proxy for initial-attack
success: these fires never grew), and share of area from fires of 10,000 ha or more. Fires with no size are dropped.
A "full response only" version uses agencies and years where the record carries a response category.
Trends: Theil-Sen slope with Kendall tau p-value, 1990-2025 (2026 shown, not in the trend).
Also: concentration of area in the largest 1% and 5% of fires (agency records 2023-2026; M3 outlines 2026).
Outputs: early_control_by_year.csv, early_control_trends.csv, size_concentration.csv
"""
import numpy as np
import pandas as pd

from common import OUT, WORK, theil_sen

F = pd.read_pickle(WORK / "fires.pkl")
F = F[F.size_ha.notna()]
rows = []


def summ(d, **k):
    t = d.size_ha.sum()
    return dict(**k, fires=len(d), area_ha=t, lt1ha=(d.size_ha < 1).mean(), lt10ha=(d.size_ha < 10).mean(),
                fires_ge_10000=int((d.size_ha >= 10000).sum()),
                area_share_ge_10000=d.loc[d.size_ha >= 10000, "size_ha"].sum() / t if t > 0 else np.nan)


for y, d in F.groupby("year"):
    rows.append(summ(d, scope="all fires", prov="Canada", year=y))
    rows.append(summ(d[d.cause == "lightning"], scope="lightning", prov="Canada", year=y))
    rows.append(summ(d[d.cause == "human"], scope="human", prov="Canada", year=y))
    ff = d[d.resp == "full"]
    if len(ff) > 50:
        rows.append(summ(ff, scope="full response only", prov="Canada (agencies with response field)", year=y))
    for p, e in d.groupby("prov"):
        if len(e) >= 10:
            rows.append(summ(e, scope="all fires", prov=p, year=y))
Y = pd.DataFrame(rows)
Y.to_csv(OUT / "early_control_by_year.csv", index=False, float_format="%.4f")

tr = []
for (scope, prov), d in Y[Y.year <= 2025].groupby(["scope", "prov"]):
    for v in ["lt1ha", "lt10ha", "area_share_ge_10000", "fires", "fires_ge_10000"]:
        r = theil_sen(d.year, d[v])
        e = d.set_index("year")[v]
        tr.append(dict(scope=scope, prov=prov, var=v, n_years=r["n"], slope_per_decade=r["slope"] * 10,
                       lo_per_decade=r["lo"] * 10, hi_per_decade=r["hi"] * 10, kendall_tau=r["tau"], p=r["p"],
                       mean_1990s=e.loc[1990:1999].mean(), mean_2016_2025=e.loc[2016:2025].mean(),
                       v2023=e.get(2023, np.nan), v2024=e.get(2024, np.nan), v2025=e.get(2025, np.nan),
                       v2026=Y[(Y.scope == scope) & (Y.prov == prov) & (Y.year == 2026)][v].squeeze()
                       if ((Y.scope == scope) & (Y.prov == prov) & (Y.year == 2026)).any() else np.nan))
T = pd.DataFrame(tr)
T.to_csv(OUT / "early_control_trends.csv", index=False, float_format="%.4f")
print(T[T.prov == "Canada"].to_string())
print(T[(T.scope == "all fires") & (T.p <= 0.05)].to_string())


# --- concentration in the largest fires (agency records, all years 2023-2026; M3 2026)
F = pd.read_pickle(WORK / "fires.pkl")
P = pd.read_csv(OUT / "escape_speed_2026_fires.csv")
rows = []


def conc(sizes, label, year, prov="Canada"):
    s = np.sort(np.asarray(sizes, float))[::-1]
    s = s[s > 0]
    n = len(s)
    if n == 0:
        return
    t = s.sum()
    r = dict(source=label, year=year, prov=prov, fires=n, total_ha=t)
    for q in [0.01, 0.05]:
        k = max(int(np.ceil(n * q)), 1)
        r[f"top{int(q*100)}pct_fires"] = k
        r[f"top{int(q*100)}pct_share"] = s[:k].sum() / t
    r["share_from_fires_ge_10000ha"] = s[s >= 10000].sum() / t
    r["share_from_fires_ge_1000ha"] = s[s >= 1000].sum() / t
    rows.append(r)


for y in [2023, 2024, 2025, 2026]:
    d = F[F.year == y]
    conc(d.size_ha, "agency records (CNFDB / 2026 list)", y)
d = F[F.year.between(2023, 2026)]
conc(d.size_ha, "agency records (CNFDB / 2026 list)", "2023-2026")
conc(P.area_ha_albers, "CWFIS M3 outlines", 2026)
C = pd.DataFrame(rows)
C.to_csv(OUT / "size_concentration.csv", index=False, float_format="%.4f")
print(C.to_string())
