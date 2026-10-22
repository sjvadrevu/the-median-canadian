"""Infrastructure inside burned areas per year 2016-2026 and 2023-2026 (union), summarised from
analysis/economy/infra_by_year.csv (grid method, NBAC 2016-2025, CWFIS M3 2026; NRN roads, NRWN rail, CanVec power
lines). No recomputation. Provinces summed (rows labelled 'outside' kept: cells outside any province polygon).
Road and rail totals = sum over all classes (only power lines carry an 'all' row). Highway = NRN classes Freeway + Expressway / Highway; main rail = NRWN 'Main'. -> infrastructure_by_year.csv"""
import os
import pandas as pd
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.dirname(os.path.dirname(P))
d = pd.read_csv(os.path.join(W, "analysis", "economy", "infra_by_year.csv"))
ROADC = sorted(set(d[d.kind == "road"].cls) - {"all"}); RAILC = sorted(set(d[d.kind == "rail"].cls) - {"all"})
sel = {"roads_all_km": ("road", ROADC), "highways_km": ("road", ["Freeway", "Expressway / Highway"]),
       "rail_all_km": ("rail", RAILC), "rail_main_km": ("rail", ["Main"]), "power_lines_km": ("power_line", ["all"])}
rows = []
for (yr, band), g in d.groupby(["year", "band"]):
    r = dict(year=yr, band=band)
    for k, (kind, cls) in sel.items():
        r[k] = round(g[(g.kind == kind) & g.cls.isin(cls)].km.sum(), 1)
    rows.append(r)
o = pd.DataFrame(rows).sort_values(["band", "year"])
o.to_csv(os.path.join(P, "infrastructure_by_year.csv"), index=False)
d2 = d[(d.cls != "all") | (d.kind == "power_line")]
pv = d2[(d2.year.isin(["2026", "2023_2026"])) & (d.band == "inside")].pivot_table(index="prov", columns=["year", "kind"], values="km", aggfunc="sum").round(0)
pv.to_csv(os.path.join(P, "infrastructure_by_province_2026_and_2023_2026.csv"))
print(o.to_string()); print(pv)
