"""Analysis 1: rank the 2026 official area burned against NFD 1990-2025 and NBAC 1972-2025.

Inputs : data/smoke-cost/fire_area_count_by_agency_year.csv (NFD 1990-2025 final + 2026 CIFFC/CWFIF YTD)
         data/fire/raw/nbac/NBAC_summarystats_1972_to_2025_20260513.xlsx (sheet sumstats_admin_name, ADJ_HA)
Outputs: ranking_canada.csv, ranking_province.csv, nbac_totals_by_year_admin.csv
"""
import pandas as pd
from common import OFFICIAL, NBAC_XLSX, OUT

off = pd.read_csv(OFFICIAL)
nfd = off[off.year <= 2025].pivot(index="year", columns="ISO", values="area_burned_ha")
y26 = off[off.year == 2026].set_index("ISO").area_burned_ha
tot26_all = y26.sum()                       # 13 agencies incl. Parks Canada
tot26_noPC = y26.drop("PC").sum()           # 12 provinces/territories, like-for-like with NFD 1990-2025

# NBAC summary by administrative name (provinces, territories, PC, DND), adjusted hectares
x = pd.read_excel(NBAC_XLSX, sheet_name="sumstats_admin_name", header=None)
hdr_row = x.index[x.iloc[:, 0].astype(str).str.strip() == "YEAR"][0]
nb = x.iloc[hdr_row + 1:].copy()
nb.columns = [str(c).strip() for c in x.iloc[hdr_row]]
nb = nb[pd.to_numeric(nb["YEAR"], errors="coerce").notna()]
nb["YEAR"] = nb["YEAR"].astype(int)
nb = nb.set_index("YEAR").apply(pd.to_numeric, errors="coerce").fillna(0.0).sort_index()
nb = nb[[c for c in nb.columns if c.lower() not in ("total", "grand total", "nan")]]
nb.to_csv(OUT / "nbac_totals_by_year_admin.csv")
nbac_tot = nb["CANADA"]
chk = (nb.drop(columns="CANADA").sum(axis=1) - nbac_tot).abs().max()
print("NBAC CANADA column vs sum of admin units, max abs diff (ha):", round(chk, 3))
nb = nb.drop(columns="CANADA")


def rank_block(series_hist, v26, label):
    s = series_hist.copy()
    s.loc[2026] = v26
    rank = int((s > v26).sum() + 1)
    a9120 = series_hist.loc[1991:2020].mean()
    a1625 = series_hist.loc[2016:2025].mean()
    top = s.sort_values(ascending=False)
    return dict(series=label, years=f"{s.index.min()}-{s.index.max()}", n_years=len(s),
                value_2026_ha=v26, rank_2026=rank,
                larger_years=";".join(str(y) for y in top.index[:rank - 1]),
                avg_1991_2020_ha=a9120, ratio_vs_1991_2020=(v26 / a9120) if a9120 > 0 else float('nan'),
                avg_2016_2025_ha=a1625, ratio_vs_2016_2025=v26 / a1625,
                max_year=int(top.index[0]), max_ha=top.iloc[0])


rows = [
    rank_block(nfd.sum(axis=1), tot26_noPC, "NFD 12 provinces/territories (excl. Parks Canada) vs 2026 official excl. PC"),
    rank_block(nfd.sum(axis=1), tot26_all, "NFD 12 provinces/territories vs 2026 official incl. PC (not like-for-like)"),
    rank_block(nbac_tot, tot26_all, "NBAC all admin units (incl. PC, DND) vs 2026 official incl. PC"),
]
can = pd.DataFrame(rows)
can.to_csv(OUT / "ranking_canada.csv", index=False)

prow = []
for p in sorted(y26.index):
    if p == "PC":
        if "PC" in nb.columns:
            r = rank_block(nb["PC"], y26[p], "NBAC PC")
            r["province"] = p
            prow.append(r)
        continue
    r = rank_block(nfd[p], y26[p], "NFD")
    r["province"] = p
    prow.append(r)
    if p in nb.columns:
        r = rank_block(nb[p], y26[p], "NBAC")
        r["province"] = p
        prow.append(r)
prov = pd.DataFrame(prow)[["province"] + list(rows[0].keys())]
prov.to_csv(OUT / "ranking_province.csv", index=False)

pd.set_option("display.width", 250)
print(can.drop(columns=["larger_years"]).to_string())
print(prov.drop(columns=["larger_years"]).round(2).to_string())
print("NBAC columns:", list(nb.columns))
