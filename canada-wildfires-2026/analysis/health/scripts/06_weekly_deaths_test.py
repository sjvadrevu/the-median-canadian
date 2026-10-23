"""Step 6: did deaths rise in smoky weeks? Observed StatCan provisional weekly deaths (13-10-0810, place of
occurrence) against our population-weighted weekly smoke exposure, by province. No coefficients from the
literature are used here; this is a test on observed counts.

Outcome: weekly non-accidental deaths excluding COVID-19 (all causes - accidents - suicide - COVID-19).
Exposure: mean over the 7 days of the StatCan week (Sunday-Saturday, REF_DATE = Saturday) of the province's
population-weighted daily PM2.5 increment (above station same-month background), 50 km assignment.
Weeks are kept only if stations within 50 km covered at least 50% of the province population on average that week.
Window: weeks ending May 7 - Oct 6 (fire season) of 2018-2025; for each province weeks in the last 10 weeks
before its latest published week are dropped (provisional counts still filling in).
Model A (per province and pooled): quasi-Poisson GLM, deaths ~ year fixed effects + week-of-year (2 Fourier
pairs) + increment at lag 0 + increment at lag 1 (per 10 ug/m3); pooled model has province x year fixed
effects and province-specific seasonality. Reported: percent change per 10 ug/m3 for lag 0, lag 1 and the sum,
with 95% CI (quasi-Poisson scale; HAC is not used, see caveats).
Model B (event check): for each province's 3 smokiest weeks (highest weekly increment), observed vs expected,
where expected = same model fitted with the smoke terms but predicting with increment set to 0.
Outputs: weekly_deaths_vs_smoke.csv, weekly_deaths_model.csv, weekly_deaths_top_smoke_weeks.csv
"""
import os, numpy as np, pandas as pd, statsmodels.api as sm

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WK = f"{H}/work"
w = pd.read_csv(f"{WK}/weekly_deaths.csv", parse_dates=["week_ending"])
cov = pd.read_csv(f"{H}/raw/deaths/13100810/13100810.csv", dtype=str)
cov.columns = [c.strip() for c in cov.columns]
cv = cov[cov["Cause of death (ICD-10)"].str.strip() == "COVID-19 [U07.1, U07.2, U10.9]"].copy()
AB = {"Newfoundland and Labrador": "NL", "Prince Edward Island": "PE", "Nova Scotia": "NS", "New Brunswick": "NB",
      "Quebec": "QC", "Ontario": "ON", "Manitoba": "MB", "Saskatchewan": "SK", "Alberta": "AB",
      "British Columbia": "BC", "Yukon": "YT", "Northwest Territories": "NT", "Nunavut": "NU", "Canada": "Canada"}
cv["prov"] = cv.GEO.str.replace(", place of occurrence", "", regex=False).map(AB)
cv["covid"] = pd.to_numeric(cv.VALUE, errors="coerce")
cv["week_ending"] = pd.to_datetime(cv.REF_DATE)
w = w.merge(cv[["week_ending", "prov", "covid"]], on=["week_ending", "prov"], how="left")
w["covid"] = w.covid.fillna(0)
w["y"] = w.non_accidental - w.covid
last = w.dropna(subset=["all_causes"]).groupby("prov").week_ending.max()

d = pd.read_csv(f"{H}/daily_popweighted_pm25.csv", parse_dates=["date"])
d = d[d.group != "Canada"].rename(columns={"group": "prov"})
d["week_ending"] = d.date + pd.to_timedelta((5 - d.date.dt.weekday) % 7, unit="D")  # Saturday
wk = d.groupby(["prov", "week_ending"]).agg(inc=("popw_increment", "mean"), pm=("popw_pm25", "mean"),
                                             days=("popw_increment", "count"), covpop=("covered_pop", "mean")).reset_index()
x = w.merge(wk, on=["prov", "week_ending"], how="inner")
x = x.sort_values(["prov", "week_ending"])
x["inc_lag1"] = x.groupby("prov").inc.shift(1)
x["year"] = x.week_ending.dt.year
md = x.week_ending.dt.strftime("%m-%d")
x = x[(md >= "05-07") & (md <= "10-06") & (x.year <= 2025)]
x = x[x.week_ending <= x.prov.map(last) - pd.Timedelta(weeks=10)]
x = x.dropna(subset=["y", "inc", "inc_lag1"])
x = x[x.days == 7]
provpop = pd.read_csv(f"{H}/exposure_by_group.csv").query("dimension=='province' and weight=='total_pop'").groupby("group").population.first()
x["coverage"] = x.covpop / x.prov.map(provpop)
x = x[x.coverage >= 0.5]  # weeks where the exposure series represents at least half the province
doy = x.week_ending.dt.dayofyear.values
for k in (1, 2):
    x[f"s{k}"] = np.sin(2 * np.pi * k * doy / 365.25); x[f"c{k}"] = np.cos(2 * np.pi * k * doy / 365.25)
x["inc10"] = x.inc / 10; x["inc10_l1"] = x.inc_lag1 / 10
x.to_csv(f"{H}/weekly_deaths_vs_smoke.csv", index=False)

def fit(df, pooled=False):
    if pooled:
        X = pd.get_dummies(df.prov + "_" + df.year.astype(str), drop_first=True, dtype=float)
        for p in df.prov.unique():
            m = (df.prov == p).astype(float)
            for c in ("s1", "c1", "s2", "c2"):
                X[f"{p}_{c}"] = m * df[c]
    else:
        X = pd.get_dummies(df.year.astype(str), drop_first=True, dtype=float)
        for c in ("s1", "c1", "s2", "c2"):
            X[c] = df[c].values
    X["inc10"] = df.inc10.values; X["inc10_l1"] = df.inc10_l1.values
    X = sm.add_constant(X, has_constant="add")
    X.index = df.index
    r = sm.GLM(df.y, X, family=sm.families.Poisson()).fit(scale="X2")
    return r, X

rows, ev = [], []
provs = [p for p in ["BC", "AB", "SK", "MB", "ON", "QC", "NB", "NS", "PE", "NL", "YT", "NT"] if p in x.prov.unique()]
for p in provs + ["pooled"]:
    df = x if p == "pooled" else x[x.prov == p]
    df = df[df.y > 0]
    if len(df) < 60:
        continue
    r, X = fit(df, pooled=(p == "pooled"))
    b, V = r.params, r.cov_params()
    def pc(v): return 100 * (np.exp(v) - 1)
    out = dict(province=p, n_weeks=len(df), years=f"{df.year.min()}-{df.year.max()}",
               mean_weekly_deaths=df.y.mean(), max_weekly_increment=df.inc.max(), dispersion=r.scale)
    for name, coef in (("lag0", ["inc10"]), ("lag1", ["inc10_l1"]), ("lag0+1", ["inc10", "inc10_l1"])):
        est = sum(b[c] for c in coef); se = np.sqrt(V.loc[coef, coef].values.sum())
        out[f"pct_per10_{name}"] = pc(est); out[f"lo_{name}"] = pc(est - 1.96 * se); out[f"hi_{name}"] = pc(est + 1.96 * se)
        out[f"p_{name}"] = float(2 * (1 - __import__("scipy").stats.norm.cdf(abs(est / se))))
    rows.append(out)
    if p != "pooled":
        X0 = X.copy(); X0["inc10"] = 0; X0["inc10_l1"] = 0
        df = df.assign(expected_no_smoke=r.predict(X0), fitted=r.predict(X))
        top = df.nlargest(3, "inc")
        for _, t in top.iterrows():
            ev.append(dict(province=p, week_ending=t.week_ending.date(), weekly_mean_increment=round(t.inc, 1),
                           weekly_mean_pm25=round(t.pm, 1), observed=t.y, expected_no_smoke=round(t.expected_no_smoke, 1),
                           observed_minus_expected=round(t.y - t.expected_no_smoke, 1),
                           ratio=round(t.y / t.expected_no_smoke, 3)))
res = pd.DataFrame(rows)
res.round(3).to_csv(f"{H}/weekly_deaths_model.csv", index=False)
pd.DataFrame(ev).to_csv(f"{H}/weekly_deaths_top_smoke_weeks.csv", index=False)
pd.set_option("display.width", 250)
print(res.round(2).to_string())
print(pd.DataFrame(ev).to_string())
print("latest published week by province:", last.dt.date.to_dict())
