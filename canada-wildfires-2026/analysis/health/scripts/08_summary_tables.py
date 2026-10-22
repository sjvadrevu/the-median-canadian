"""Step 8: summary tables for results.md.
Outputs: worst_days.csv (top 10 days per year nationally and the worst day per province-year, total pop),
cma_may_sep.csv (CMA x year, May-Sep), group_comparison.csv (age, low income, on-reserve vs reference),
national_comparable.csv (national totals restricted to provinces with data in every year).
"""
import os, numpy as np, pandas as pd

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
e = pd.read_csv(f"{H}/exposure_by_group.csv")
d = pd.read_csv(f"{H}/daily_popweighted_pm25.csv", parse_dates=["date"])
d["year"] = d.date.dt.year
provpop = e.query("dimension=='province' and weight=='total_pop'").groupby("group").population.first()
provpop["Canada"] = provpop.sum()
d["coverage"] = d.covered_pop / d.group.map(provpop)

nat = d[d.group == "Canada"]
top = nat.sort_values("popw_pm25", ascending=False).groupby("year").head(10).sort_values(["year", "popw_pm25"], ascending=[True, False])
top = top.assign(rank=top.groupby("year").cumcount() + 1, scope="Canada top 10")
pw = d[(d.group != "Canada") & (d.coverage >= 0.5)]
pw = pw.loc[pw.groupby(["group", "year"]).popw_pm25.idxmax()].assign(rank=1, scope="province worst day")
pd.concat([top, pw])[["scope", "group", "year", "rank", "date", "popw_pm25", "popw_increment", "covered_pop", "coverage"]].round(3).to_csv(
    f"{H}/worst_days.csv", index=False)

cma = e[(e.dimension == "cma") & (e.weight == "total_pop") & (e.period == "May-Sep")]
cma[["group", "year", "population", "share_person_days_covered", "person_days_gt27", "person_days_gt60", "person_days_gt100",
     "people_ge1day_gt100", "popw_mean_pm25", "popw_mean_increment", "days_gt27_per_covered_person"]].round(3).to_csv(
    f"{H}/cma_may_sep.csv", index=False)

g = e[(e.dimension == "national") & (e.period == "May-Sep")].copy()
g["covered_person_days"] = g.share_person_days_covered * g.population * g.n_days
g["days_gt27_per_covered_person"] = g.person_days_gt27 / (g.covered_person_days / g.n_days)
g["days_gt100_per_covered_person"] = g.person_days_gt100 / (g.covered_person_days / g.n_days)
g["share_ge1day_gt100_of_covered"] = g.people_ge1day_gt100 / g.pop_with_any_coverage
g["share_with_any_coverage"] = g.pop_with_any_coverage / g.population
r = e[(e.dimension == "reserve") & (e.period == "May-Sep") & (e.weight == "total_pop")].copy()
r["weight"] = r.group; r["covered_person_days"] = r.share_person_days_covered * r.population * r.n_days
r["days_gt27_per_covered_person"] = r.person_days_gt27 / (r.covered_person_days / r.n_days)
r["days_gt100_per_covered_person"] = r.person_days_gt100 / (r.covered_person_days / r.n_days)
r["share_ge1day_gt100_of_covered"] = r.people_ge1day_gt100 / r.pop_with_any_coverage
r["share_with_any_coverage"] = r.pop_with_any_coverage / r.population
cols = ["year", "weight", "population", "share_with_any_coverage", "share_person_days_covered", "days_gt27_per_covered_person",
        "days_gt100_per_covered_person", "share_ge1day_gt100_of_covered", "popw_mean_pm25", "popw_mean_increment",
        "person_days_gt27", "person_days_gt100", "people_ge1day_gt100"]
pd.concat([g[cols], r[cols]]).round(4).to_csv(f"{H}/group_comparison.csv", index=False)

# national comparable: provinces with >= 50% coverage in every year
pv = e[(e.dimension == "province") & (e.weight == "total_pop")]
ok = pv[pv.period == "May-Sep"].groupby("group").share_person_days_covered.min()
keep = ok[ok >= 0.5].index
c = pv[pv.group.isin(keep)].groupby(["year", "period"]).agg(
    population=("population", "sum"), person_days_gt27=("person_days_gt27", "sum"), person_days_gt60=("person_days_gt60", "sum"),
    person_days_gt100=("person_days_gt100", "sum"), people_ge1day_gt100=("people_ge1day_gt100", "sum"),
    person_ug_days_increment=("person_ug_days_increment", "sum")).reset_index()
c["provinces"] = " ".join(sorted(keep))
c.to_csv(f"{H}/national_comparable.csv", index=False)
pd.set_option("display.width", 250)
print(c[c.period == "May-Sep"].to_string())
print(top[top.year >= 2018].groupby("year").head(3)[["year", "date", "popw_pm25", "coverage"]].to_string())
print(pw[pw.year == 2026][["group", "date", "popw_pm25", "coverage"]].to_string())
