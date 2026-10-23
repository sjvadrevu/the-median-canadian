"""Step 13: late-season fires in the CNFDB fire points (v20260811), 1990-2025, Canada and Alberta.
Month = MONTH field (start/report month as given by the agency); fires without a month are excluded and counted.
Per year: all fires, fires in September, October, Sep-Oct; share of dated fires in Sep-Oct and in October;
area burned by fires starting in Oct. Trend: Kendall tau and Theil-Sen slope per decade (scipy), 1990-2025.
Output: late_season_cnfdb_by_year.csv, late_season_trends.csv (cnfdb rows)"""
import zipfile, pandas as pd, numpy as np
from scipy.stats import kendalltau, theilslopes
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
R = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/data/fire/raw"
p = pd.read_csv(zipfile.ZipFile(f"{R}/nfdb/NFDB_point_txt.zip").open("NFDB_point_20260811.txt"), low_memory=False, encoding="latin1",
                usecols=["YEAR", "MONTH", "SIZE_HA", "SRC_AGENCY", "CAUSE"])
p = p[(p.YEAR >= 1990) & (p.YEAR <= 2025)]
rows = []
for scope, s in [("Canada", p), ("AB", p[p.SRC_AGENCY == "AB"])]:
    for y, g in s.groupby("YEAR"):
        dated = g[(g.MONTH >= 1) & (g.MONTH <= 12)]
        rows.append(dict(scope=scope, year=int(y), fires=len(g), fires_no_month=len(g) - len(dated), sep=int((dated.MONTH == 9).sum()),
                         oct=int((dated.MONTH == 10).sum()), sep_oct=int(dated.MONTH.isin([9, 10]).sum()),
                         share_sep_oct=round(dated.MONTH.isin([9, 10]).mean(), 4), share_oct=round((dated.MONTH == 10).mean(), 4),
                         oct_ha=round(dated[dated.MONTH == 10].SIZE_HA.sum(), 1), oct_human=int(((dated.MONTH == 10) & (dated.CAUSE == "H")).sum())))
Y = pd.DataFrame(rows); Y.to_csv(f"{O}/late_season_cnfdb_by_year.csv", index=False)
tr = []
for scope, g in Y.groupby("scope"):
    for m in ["oct", "sep_oct", "share_oct", "share_sep_oct", "fires"]:
        t = kendalltau(g.year, g[m]); sl = theilslopes(g[m], g.year)
        tr.append(dict(source="CNFDB points", scope=scope, metric=m, years="1990-2025", n_years=len(g), theil_sen_per_decade=round(sl[0] * 10, 4),
                       lo95=round(sl[2] * 10, 4), hi95=round(sl[3] * 10, 4), kendall_tau=round(t.statistic, 3), p_value=round(t.pvalue, 4),
                       mean_1990_1999=round(g[g.year <= 1999][m].mean(), 4), mean_2016_2025=round(g[g.year >= 2016][m].mean(), 4)))
T = pd.DataFrame(tr); T.to_csv(f"{O}/late_season_trends_cnfdb.csv", index=False)
pd.set_option("display.width", 250); print(T.to_string()); print(Y[Y.scope == "Canada"].to_string())
