"""Priority 1, combined: one national split of 2023-2026 official area burned by response class.

Rule per fire (work/fires.pkl), then share x official provincial total (as in 03 view A):
  suppression      = agency response "full" or protection-zone "full" (QC intensive zone, YT Critical/Full)
                     + Alberta Wildfire fires (AB agency records): Alberta Wildfire's records cover only the Forest
                     Protection Area, and its 2026 list labels 798 of 798 fires (100%) full response; CNFDB carries no
                     response field for AB, so 2023-2025 AB agency fires are counted as suppression on that basis.
  not suppression  = modified, monitored, QC northern zone, YT Strategic/Transitional/Wilderness
  unclassified     = no label (SK 2023-2025, NL 2023-2025, NB)
Also: for suppression-class fires, the share of their area from fires of 10,000 ha or more (fires that escaped
despite a full response), and the same for not-suppression fires.
Outputs: zone_share_national.csv, zone_share_province_2023_2026.csv, escaped_despite_full.csv
"""
import pandas as pd

from common import OUT, SEASON, WORK

F = pd.read_pickle(WORK / "fires.pkl")
F = F[F.year.between(2023, 2026)].copy()
F.loc[(F.agency == "AB") & (F.resp == "unclassified"), "resp"] = "ab_fpa_full"
grp = {"full": "suppression", "zone_full": "suppression", "ab_fpa_full": "suppression",
       "modified": "not_suppression", "monitored": "not_suppression", "zone_obs": "not_suppression",
       "unclassified": "unclassified"}
F["grp"] = F.resp.map(grp)
n = pd.read_csv(SEASON / "NFD_-_Area_burned_by_month_-_EN_FR.csv")
off = n[n.Year.between(2023, 2025)].groupby(["ISO", "Year"])["Area (hectares)"].sum()
off.index.names = ["prov", "year"]
o26 = F[F.year == 2026].groupby("prov").size_ha.sum()
off = pd.concat([off, pd.concat({2026: o26}, names=["year", "prov"]).swaplevel()]).sort_index()
pt = F.groupby(["prov", "year"]).size_ha.transform("sum")
F["w_ha"] = F.size_ha / pt * pd.Series(list(zip(F.prov, F.year))).map(off).values

cols = ["suppression", "not_suppression", "unclassified"]
detail = ["full", "zone_full", "ab_fpa_full", "modified", "monitored", "zone_obs", "unclassified"]
rows = []
for y, d in list(F.groupby("year")) + [("2023-2026", F)]:
    t = d.w_ha.sum()
    r = dict(year=y, official_ha=t)
    for c in cols:
        r[c + "_ha"] = d.loc[d.grp == c, "w_ha"].sum()
        r[c + "_share"] = r[c + "_ha"] / t
    for c in detail:
        r[c + "_share"] = d.loc[d.resp == c, "w_ha"].sum() / t
    cl = r["suppression_ha"] + r["not_suppression_ha"]
    r["not_suppression_share_of_classified"] = r["not_suppression_ha"] / cl
    r["not_suppression_share_low"] = r["not_suppression_ha"] / t                       # unclassified all suppression
    r["not_suppression_share_high"] = (r["not_suppression_ha"] + r["unclassified_ha"]) / t  # all not suppression
    rows.append(r)
N = pd.DataFrame(rows)
N.to_csv(OUT / "zone_share_national.csv", index=False, float_format="%.4f")
print(N.T.to_string())

P = F.pivot_table(index="prov", columns="grp", values="w_ha", aggfunc="sum", fill_value=0)
P["official_2023_2026_ha"] = P.sum(axis=1)
for c in cols:
    if c in P:
        P[c + "_share"] = P[c] / P.official_2023_2026_ha
P = P.sort_values("official_2023_2026_ha", ascending=False)
P.to_csv(OUT / "zone_share_province_2023_2026.csv", float_format="%.4f")
print(P.round(3).to_string())

rows = []
for g, d in F[F.grp != "unclassified"].groupby("grp"):
    t = d.w_ha.sum()
    rows.append(dict(group=g, fires=len(d), official_ha=t,
                     fires_ge_10000=int((d.size_ha >= 10000).sum()),
                     share_area_from_fires_ge_10000=d.loc[d.size_ha >= 10000, "w_ha"].sum() / t,
                     share_area_from_fires_ge_1000=d.loc[d.size_ha >= 1000, "w_ha"].sum() / t,
                     share_fires_lt_10ha=(d.size_ha < 10).mean()))
E = pd.DataFrame(rows)
E.to_csv(OUT / "escaped_despite_full.csv", index=False, float_format="%.4f")
print(E.to_string())
