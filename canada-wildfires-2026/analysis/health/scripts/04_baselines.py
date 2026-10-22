"""Step 4: baseline death rates and weekly death series by province.

Inputs (Statistics Canada, Open Licence):
  13-10-0810-01 Provisional weekly death counts, by selected grouped causes of death (place of occurrence)
  13-10-0768-01 Provisional weekly death counts, by age group and sex (place of occurrence)
  17-10-0005-01 Population estimates on July 1, by age and gender
Outputs: work/weekly_deaths.csv (province x week: all causes, non-accidental = all - accidents - suicide,
         deaths 65+ from 13-10-0768), baseline_death_rates.csv
"""
import os, numpy as np, pandas as pd

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = f"{H}/raw/deaths"
AB = {"Newfoundland and Labrador": "NL", "Prince Edward Island": "PE", "Nova Scotia": "NS", "New Brunswick": "NB",
      "Quebec": "QC", "Ontario": "ON", "Manitoba": "MB", "Saskatchewan": "SK", "Alberta": "AB",
      "British Columbia": "BC", "Yukon": "YT", "Northwest Territories": "NT", "Nunavut": "NU", "Canada": "Canada"}

c = pd.read_csv(f"{R}/13100810/13100810.csv", dtype=str)
c.columns = [x.strip() for x in c.columns]
c["prov"] = c.GEO.str.replace(", place of occurrence", "", regex=False).map(AB)
c["v"] = pd.to_numeric(c.VALUE, errors="coerce")
cause = c["Cause of death (ICD-10)"].str.strip()
key = {"Total, all causes of death [A00-Y89]": "all_causes",
       "Accidents (unintentional injuries) [V01-X59, Y85-Y86]": "accidents",
       "Intentional self-harm (suicide) [X60-X84, Y87.0]": "suicide",
       "Chronic lower respiratory diseases [J40-J47]": "clrd",
       "Diseases of heart [I00-I09, I11, I13, I20-I51]": "heart",
       "Influenza and pneumonia [J09-J18]": "flu_pneu",
       "Cerebrovascular diseases [I60-I69]": "cerebrovascular"}
c["k"] = cause.map(key)
w = c.dropna(subset=["k"]).pivot_table(index=["REF_DATE", "prov"], columns="k", values="v", aggfunc="first").reset_index()
w["non_accidental"] = w.all_causes - w.accidents.fillna(0) - w.suicide.fillna(0)
a = pd.read_csv(f"{R}/13100768/13100768.csv", dtype=str)
a = a[(a.Sex == "Both sexes")]
a["prov"] = a.GEO.str.replace(", place of occurrence", "", regex=False).map(AB)
a["v"] = pd.to_numeric(a.VALUE, errors="coerce")
ag = a.pivot_table(index=["REF_DATE", "prov"], columns="Age at time of death", values="v", aggfunc="first").reset_index()
ag["deaths_65p"] = ag["Age at time of death, 65 to 84 years"] + ag["Age at time of death, 85 years and over"]
ag = ag.rename(columns={"Age at time of death, all ages": "all_ages_768"})[["REF_DATE", "prov", "all_ages_768", "deaths_65p"]]
w = w.merge(ag, on=["REF_DATE", "prov"], how="outer").rename(columns={"REF_DATE": "week_ending"})
w.to_csv(f"{H}/work/weekly_deaths.csv", index=False)

# baseline: non-accidental deaths in weeks ending May 7 .. Oct 6 (covering May 1 - Sep 30), per day per person
pop = pd.read_csv(f"{R}/17100005/17100005.csv", dtype=str, usecols=["REF_DATE", "GEO", "Gender", "Age group", "VALUE"])
pop = pop[(pop.Gender == "Total - gender") & (pop["Age group"] == "All ages")]
pop["prov"] = pop.GEO.map(AB); pop["year"] = pop.REF_DATE.astype(int); pop["pop"] = pd.to_numeric(pop.VALUE)
pop = pop.dropna(subset=["prov"])[["prov", "year", "pop"]]
w["date"] = pd.to_datetime(w.week_ending); w["year"] = w.date.dt.year
md = w.date.dt.strftime("%m-%d")
s = w[(md >= "05-07") & (md <= "10-06")]
b = s.groupby(["prov", "year"]).agg(weeks=("non_accidental", "count"), non_acc=("non_accidental", "sum"),
                                     all_causes=("all_causes", "sum")).reset_index()
b = b.merge(pop, on=["prov", "year"], how="left")
b["non_acc_per_day"] = b.non_acc / (b.weeks * 7)
b["daily_rate_per_person"] = b.non_acc_per_day / b["pop"]
b["daily_rate_per_100k"] = b.daily_rate_per_person * 1e5
b.to_csv(f"{H}/baseline_death_rates.csv", index=False)
print(b[b.year >= 2018].pivot(index="prov", columns="year", values="daily_rate_per_100k").round(3).to_string())
print(b[b.year >= 2018].pivot(index="prov", columns="year", values="weeks").to_string())
