"""Step 7: CIHI NACRS monthly emergency department (ED) visits (all causes) by province vs monthly smoke.
CIHI data tables "NACRS Emergency Department Visits and Lengths of Stay by Province/Territory", Table 2
(ED visits by month, age and sex), fiscal years 2021-22 to 2025-26 (April 2021 to March 2026).
Model: quasi-Poisson GLM, monthly visits ~ province x fiscal-year FE + province x calendar-month FE
+ offset(log days) + monthly mean population-weighted PM2.5 increment (per 10 ug/m3), all months, then also
May-Sep only. Age groups 0-4, 65+ and all ages. Outcome is ALL-CAUSE ED visits (no diagnosis by month is
published), so the test is weak.
Outputs: monthly_ed_vs_smoke.csv, monthly_ed_model.csv
"""
import os, glob, numpy as np, pandas as pd, openpyxl, statsmodels.api as sm

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PMAP = {"N.L.": "NL", "P.E.I.": "PE", "N.S.": "NS", "N.B.": "NB", "Que.": "QC", "Ont.": "ON", "Man.": "MB",
        "Sask.": "SK", "Alta.": "AB", "B.C.": "BC", "Y.T.": "YT", "Yuk.": "YT", "N.W.T.": "NT", "Nun.": "NU", "Total": "Total"}
rows = []
for f in sorted(glob.glob(f"{H}/raw/cihi/ed_*.xlsx")):
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    ws = [s for s in wb.worksheets if s.title.strip().lower().startswith(("table 2", "2 ed visits"))][0]
    prov = month = None; hdr = None
    for r in ws.iter_rows(values_only=True):
        r = list(r)
        if hdr is None:
            if r and isinstance(r[0], str) and r[0].startswith("Province"):
                hdr = [str(c) for c in r]
            continue
        if not any(r) or r[0] is not None and isinstance(r[0], str) and r[0].startswith(("Notes", "Note", "Source", "*")):
            if r and r[0] and str(r[0]).startswith(("Notes", "Note", "Source")):
                break
            continue
        cells = [c for c in r]
        # carry-forward of province and month columns
        if cells[0] is not None:
            nm = str(cells[0]).replace("*", "").replace("\u2020", "").replace("\u2021", "").strip()
            prov = PMAP.get(nm, nm)
        if cells[1] is not None:
            month = str(cells[1]).strip()
        sex = cells[2]
        if sex is None:
            continue
        vals = cells[3:8]
        rows.append([os.path.basename(f), prov, month, str(sex).strip()] + vals)
ed = pd.DataFrame(rows, columns=["file", "prov", "month", "sex", "a0_4", "a5_19", "a20_64", "a65p", "all"])
ed = ed[ed.sex == "All"].copy()
ed["date"] = pd.to_datetime(ed.month, format="%B %Y", errors="coerce")
ed = ed.dropna(subset=["date"])
for c in ["a0_4", "a65p", "all"]:
    ed[c] = pd.to_numeric(ed[c], errors="coerce")
ed = ed.drop_duplicates(["prov", "date"], keep="last")
print(ed.groupby("prov").date.agg(["min", "max", "count"]))

d = pd.read_csv(f"{H}/daily_popweighted_pm25.csv", parse_dates=["date"])
d = d[d.group != "Canada"].rename(columns={"group": "prov"})
d["m"] = d.date.dt.to_period("M").dt.to_timestamp()
mm = d.groupby(["prov", "m"]).agg(inc=("popw_increment", "mean"), pm=("popw_pm25", "mean"), covpop=("covered_pop", "mean")).reset_index()
x = ed.merge(mm, left_on=["prov", "date"], right_on=["prov", "m"], how="inner")
provpop = pd.read_csv(f"{H}/exposure_by_group.csv").query("dimension=='province' and weight=='total_pop'").groupby("group").population.first()
x["coverage"] = x.covpop / x.prov.map(provpop)
x = x[x.coverage >= 0.5]
x["days"] = x.date.dt.days_in_month
x["fy"] = np.where(x.date.dt.month >= 4, x.date.dt.year, x.date.dt.year - 1)
x["cm"] = x.date.dt.month
x.to_csv(f"{H}/monthly_ed_vs_smoke.csv", index=False)

res = []
for subset in ("all_months", "May-Sep"):
    xx = x if subset == "all_months" else x[x.cm.between(5, 9)]
    for outc in ("all", "a0_4", "a65p"):
        df = xx.dropna(subset=[outc])
        df = df[df[outc] > 0]
        X = pd.get_dummies(df.prov + "_" + df.fy.astype(str), drop_first=True, dtype=float)
        X = X.join(pd.get_dummies(df.prov + "_m" + df.cm.astype(str), drop_first=True, dtype=float))
        X["inc10"] = df.inc / 10
        X = sm.add_constant(X, has_constant="add")
        r = sm.GLM(df[outc], X, family=sm.families.Poisson(), offset=np.log(df.days)).fit(scale="X2")
        b, se = r.params["inc10"], r.bse["inc10"]
        res.append(dict(months=subset, outcome={"all": "all ages", "a0_4": "age 0-4", "a65p": "age 65+"}[outc],
                        n_province_months=len(df), provinces=" ".join(sorted(df.prov.unique())),
                        max_monthly_increment=df.inc.max(),
                        pct_per10=100 * (np.exp(b) - 1), lo=100 * (np.exp(b - 1.96 * se) - 1),
                        hi=100 * (np.exp(b + 1.96 * se) - 1), p=float(2 * (1 - __import__("scipy").stats.norm.cdf(abs(b / se)))),
                        dispersion=r.scale))
res = pd.DataFrame(res)
res.round(3).to_csv(f"{H}/monthly_ed_model.csv", index=False)
pd.set_option("display.width", 250)
print(res.round(3).to_string())
