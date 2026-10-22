"""Federal DFAA agreements for wildfire events, from the Proactive Disclosure - Grants and Contributions subset
(raw/grants/grants_dfaa_wildfire_subset.csv, made by 12_grants_filter.py). Rows of program '(DFAA) Disaster Financial
Assistance Arrangements' whose description mentions fire; event year parsed from 'costs associated with the YYYY ...'.
agreement_value is the value disclosed for the Provincial Emergency Financial Assistance Order (an interim or advance
federal contribution at the agreement date, not the final DFAA settlement). Rows with value 0 (2018-2022 disclosures)
carry no amount. Output dfaa_wildfire_payments.csv and dfaa_all_events_by_year.csv."""
import os, re
import pandas as pd

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_csv(os.path.join(L, "raw", "grants", "grants_dfaa_wildfire_subset.csv"), low_memory=False)
p = d[d.prog_name_en.str.contains("DFAA", na=False)].copy()
p["txt"] = p.agreement_title_en.fillna("") + " | " + p.description_en.fillna("")
p["event_year"] = p.txt.str.extract(r"\b(20\d\d)\b")[0].astype(float)
p["event"] = p.description_en.str.extract(r"costs associated with (?:the )?(\d{4} [^.]*?) under")[0]
p["is_fire"] = p.txt.str.contains(r"fire", case=False)
p = p.sort_values(["ref_number", "amendment_number"]).drop_duplicates("ref_number", keep="last")
cols = ["ref_number", "amendment_number", "agreement_start_date", "recipient_province", "agreement_title_en", "event", "event_year", "agreement_value", "description_en"]
f = p[p.is_fire][cols].sort_values("event_year")
f.to_csv(os.path.join(L, "dfaa_wildfire_payments.csv"), index=False)
a = p.groupby(["event_year", "is_fire"]).agreement_value.agg(["sum", "count"]).unstack("is_fire", fill_value=0)
a.columns = [f"{s}_{'fire' if fire else 'other'}" for s, fire in a.columns]
a.to_csv(os.path.join(L, "dfaa_all_events_by_year.csv"))
pd.set_option("display.width", 250)
print(f[["agreement_start_date", "recipient_province", "event", "agreement_value"]].to_string())
print(f.groupby("event_year").agreement_value.agg(["sum", "count"]))
print(a)
