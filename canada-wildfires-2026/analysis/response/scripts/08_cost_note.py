"""Priority 6 (note only): provincial firefighting spending per hectare burned, from the existing
analysis/economic-value/cost_tally_by_year.csv (2025 dollars) and the NFD official area for the same provinces.
Only provinces with a spending figure in a year are counted (AB, BC, ON, SK). No new cost data.
Output: cost_per_ha_note.csv
"""
import pandas as pd

from common import BASE, OUT, SEASON

c = pd.read_csv(BASE / "analysis/economic-value/cost_tally_by_year.csv")
n = pd.read_csv(SEASON / "NFD_-_Area_burned_by_month_-_EN_FR.csv")
a = n.groupby(["Year", "ISO"])["Area (hectares)"].sum()
F = pd.read_pickle(OUT / "work/fires.pkl")
a26 = F[F.year == 2026].groupby("prov").size_ha.sum()
rows = []
for _, r in c.iterrows():
    y = int(r.year)
    for p in ["AB", "BC", "ON", "SK"]:
        v = r.get(f"A_{p}")
        if pd.notna(v):
            ha = a26.get(p) if y == 2026 else a.get((y, p))
            rows.append(dict(year=y, prov=p, spend_2025_dollars=v, official_ha=ha,
                             dollars_per_ha=v / ha if ha else None))
D = pd.DataFrame(rows)
tot = D.groupby("year")[["spend_2025_dollars", "official_ha"]].sum()
tot["dollars_per_ha"] = tot.spend_2025_dollars / tot.official_ha
tot["provinces"] = D.groupby("year").prov.apply(lambda s: "+".join(s))
D = pd.concat([D, tot.reset_index().assign(prov="sum of provinces with data")], ignore_index=True)
D.to_csv(OUT / "cost_per_ha_note.csv", index=False, float_format="%.1f")
print(D[D.prov == "sum of provinces with data"].to_string())
