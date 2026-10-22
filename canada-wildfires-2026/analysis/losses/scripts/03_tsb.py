"""TSB air occurrence data (ASIS, January 1995 to present; files dated 2026-10-21 on www.bst.gc.ca):
firefighting / fire-management flights and other flights whose TSB summary describes wildfire work.
Coded set: aircraft OperationTypeID = 'FIRE FIGHTING / FIRE MANAGEMENT'.
Text set (not coded): summary matches wildfire-work keywords; listed in tsb_wildfire_text_matches.csv for checking.
Counts: fatalities / serious / minor from the INJURIES table summed per occurrence (all persons on the aircraft
and on the ground as TSB records them). Output written to analysis/losses/."""
import os, re
import pandas as pd

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(L, "raw", "tsb")
rd = lambda f, **k: pd.read_csv(os.path.join(R, f), encoding="utf-8-sig", low_memory=False, **k)

occ = rd("ASISdb_MDOTW_VW_OCCURRENCE_PUBLIC.csv", usecols=lambda c: c in {"OccNo", "OccDate", "CountryID_DisplayEng", "ProvinceID_DisplayEng",
         "OccClassID_DisplayEng", "OccTypeID_DisplayEng", "Location", "Latitude", "Longitude", "Summary", "TotalFatalCount", "TotalSeriousCount", "TotalMinorCount",
         "SeriousIncidentEnum_DisplayEng"})
ac = rd("ASISdb_MDOTW_VW_AIRCRAFT_PUBLIC.csv", usecols=["OccNo", "AcID", "OperationTypeID_DisplayEng", "AircraftTypeID_DisplayEng",
        "AircraftMakeID_DisplayEng", "AircraftModelID_DisplayEng", "OperatorTypeID_DisplayEng", "StateOperatorID_DisplayEng", "DamageLevelID_DisplayEng", "RegCountryID_DisplayEng"])
inj = rd("ASISdb_MDOTW_VW_INJURIES_PUBLIC.csv")
inj = inj.groupby("OccNo")[["FatalCount", "SeriousCount", "MinorCount"]].sum()

print("occurrence rows", len(occ), "unique OccNo", occ.OccNo.nunique(), "(table repeats rows per occurrence; deduplicated)")
occ = occ.drop_duplicates("OccNo")
print(occ.OccTypeID_DisplayEng.value_counts().to_string())
occ["OccDate"] = pd.to_datetime(occ.OccDate, errors="coerce")
occ["year"] = occ.OccDate.dt.year
print("occurrences", len(occ), "date range", occ.OccDate.min(), occ.OccDate.max())
print(occ.OccClassID_DisplayEng.value_counts().to_string())

fire_ac = ac[ac.OperationTypeID_DisplayEng == "FIRE FIGHTING / FIRE MANAGEMENT"]
kw = re.compile(r"wild ?fire|wildland fire|forest fire|bush fire|fire suppression|fire management|forest fire ?fighting|air ?tanker|water ?bomb|skimmer|bird ?dog|"
                r"bambi|monsoon bucket|helibucket|initial attack|fire crew|fire camp|fire base|fire attack|retardant|smoke from (?:forest|wild)", re.I)
occ["kw"] = occ.Summary.fillna("").str.contains(kw)
coded = set(fire_ac.OccNo)
occ["set"] = "none"
occ.loc[occ.kw & ~occ.OccNo.isin(coded), "set"] = "text match only"
occ.loc[occ.OccNo.isin(coded), "set"] = "coded firefighting"
sel = occ[occ.set != "none"].merge(inj, left_on="OccNo", right_index=True, how="left")
acs = ac.groupby("OccNo").agg(aircraft=("AircraftTypeID_DisplayEng", lambda s: "; ".join(sorted(set(map(str, s))))),
                              make_model=("AircraftModelID_DisplayEng", lambda s: "; ".join(sorted(set(map(str, s))))),
                              operation=("OperationTypeID_DisplayEng", lambda s: "; ".join(sorted(set(map(str, s))))),
                              operator_type=("OperatorTypeID_DisplayEng", lambda s: "; ".join(sorted(set(map(str, s))))),
                              damage=("DamageLevelID_DisplayEng", lambda s: "; ".join(sorted(set(map(str, s))))))
sel = sel.merge(acs, left_on="OccNo", right_index=True, how="left")
for c in ["FatalCount", "SeriousCount", "MinorCount"]:
    sel[c] = sel[c].fillna(0).astype(int)
sel = sel[sel.CountryID_DisplayEng.fillna("CANADA").str.upper() == "CANADA"]
cols = ["OccNo", "OccDate", "year", "set", "OccTypeID_DisplayEng", "OccClassID_DisplayEng", "ProvinceID_DisplayEng", "Location", "Latitude", "Longitude",
        "aircraft", "make_model", "operation", "operator_type", "damage", "FatalCount", "SeriousCount", "MinorCount", "TotalFatalCount", "Summary"]
sel.sort_values("OccDate")[cols].to_csv(os.path.join(L, "tsb_firefighting_occurrences.csv"), index=False)
sel[sel.set == "text match only"].sort_values("OccDate")[cols].to_csv(os.path.join(L, "tsb_wildfire_text_matches.csv"), index=False)

def yr(df):
    g = df.groupby("year").agg(occurrences=("OccNo", "count"),
                               accidents=("OccTypeID_DisplayEng", lambda s: int(s.astype(str).str.upper().str.contains("ACCIDENT").sum())),
                               fatal_occurrences=("FatalCount", lambda s: int((s > 0).sum())),
                               fatalities=("FatalCount", "sum"), serious_injuries=("SeriousCount", "sum"), minor_injuries=("MinorCount", "sum"))
    return g.reindex(range(1995, 2027), fill_value=0)
# Text matches with a fatality or serious injury since 1995 were read one by one (TSB summary). These four describe
# wildfire work by aircraft not coded as firefighting; the rest are smoke-affected or unrelated flights.
CONFIRMED = {"A04W0165": "forest fire infra-red scanning (AB)", "A19P0059": "fire surveillance flight for BC Wildfire Service",
             "A23W0082": "helicopter supporting forest fire fighting, bucketing (AB)", "A25A0051": "aerial fire suppression, NS DNRR helicopter"}
sel["wildfire_work"] = (sel.set == "coded firefighting") | sel.OccNo.isin(CONFIRMED)
sel["confirmed_note"] = sel.OccNo.map(CONFIRMED)
sel.sort_values("OccDate")[cols + ["wildfire_work", "confirmed_note"]].to_csv(os.path.join(L, "tsb_firefighting_occurrences.csv"), index=False)
a = yr(sel[sel.set == "coded firefighting"]).add_prefix("coded_")
b = yr(sel[sel.wildfire_work]).add_prefix("wildfire_work_")
out = a.join(b)
for c in ["coded_fatalities", "wildfire_work_fatalities"]:
    out["rank_" + c] = out[c].rank(ascending=False, method="min").astype(int)
out.index.name = "year"
out.to_csv(os.path.join(L, "tsb_firefighting_by_year.csv"))
pd.set_option("display.width", 250)
print(out.to_string())
f = sel[(sel.FatalCount > 0) | (sel.SeriousCount > 0)].sort_values("OccDate")
for _, r in f[f.set == "text match only"].iterrows():
    print("TEXT", r.OccNo, r.OccDate.date(), r.ProvinceID_DisplayEng, r.operation, r.FatalCount, r.SeriousCount, "|", str(r.Summary)[:260].replace("\n", " "))
print(f[f.year >= 2021][["OccNo", "OccDate", "set", "OccTypeID_DisplayEng", "ProvinceID_DisplayEng", "aircraft", "make_model", "operation", "FatalCount", "SeriousCount"]].to_string())
