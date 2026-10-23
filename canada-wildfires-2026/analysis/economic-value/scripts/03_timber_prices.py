"""Official timber prices by province and year (CAD per m3, nominal), 2016-2026.

stump_nfd    NFD 'Statement of Revenues from the Sale of Timber from Provincial Crown Land', line 'Stumpage charges',
             divided by NFD net merchantable roundwood harvested on Provincial land (all categories and species).
             = average Crown stumpage (government revenue per m3 harvested). 1990-2024.
stump_bc_fp  BC Budget and Fiscal Plan, Table "Material Assumptions - Revenue", 'Total stumpage rates ($Cdn/cubic metre)',
             updated forecast for the fiscal year that contains the fire season (published the following February);
             2026/27 = Budget 2026 estimate.
qc_bmmb      Quebec BMMB average winning auction price, all desired species (Bilan quinquennal 2018-2023, Table 3),
             fiscal years 2017-18 to 2022-23. Context only (auction lots, not all Crown wood).
Chosen stumpage price (price_stump): BC = stump_bc_fp (all years 2016-2026); other provinces = stump_nfd; years after the
last NFD year carry the last available value (flagged); Ontario 2020-2022 (NFD qualifier n, not available) = mean of
2019 and 2023 (flagged); NB after 2021 carries 2021. Territories report no stumpage revenue (price 0).
Industry value (price_roundwood): see 03b (StatCan output of forestry and logging / NFD harvest), merged if present.
Output: timber_prices_by_province_year.csv
"""
import numpy as np
import pandas as pd
from vcommon import RAW, OUT, YEARS

nfd = RAW / "nfd"
r = pd.read_csv(nfd / "NFD - Statement of Revenues from the Sale of Timber from Provincial Crown Land - EN FR.csv", encoding="utf-8-sig")
r.columns = ["year", "an", "iso", "jur", "jfr", "rev", "revfr", "val", "q", "v2", "q2"]
st = r[r.rev == "Stumpage charges"].set_index(["iso", "year"])
v = pd.read_csv(nfd / "NFD - Net Merchantable Volume of Roundwood Harvested by Category and Ownership - EN FR.csv", encoding="utf-8-sig")
v.columns = ["year", "an", "iso", "jur", "jfr", "cat", "catfr", "sp", "spfr", "ten", "tenfr", "vol", "q", "v2", "q2"]
crown = v[v.ten == "Provincial land"].groupby(["iso", "year"]).vol.sum()
total = v.groupby(["iso", "year"]).vol.sum()

bc_fp = {2016: (12.88, "Budget 2017 updated forecast 2016/17"), 2017: (15.56, "Budget 2018 updated forecast 2017/18"),
         2018: (20.84, "Budget 2019 updated forecast 2018/19"), 2019: (20.51, "Budget 2020 updated forecast 2019/20"),
         2020: (23.32, "Budget 2021 updated forecast 2020/21"), 2021: (37.14, "Budget 2022 updated forecast 2021/22"),
         2022: (36.20, "Budget 2023 updated forecast 2022/23"), 2023: (18.70, "Budget 2024 updated forecast 2023/24"),
         2024: (15.03, "Budget 2025 updated forecast 2024/25"), 2025: (14.94, "Budget 2026 updated forecast 2025/26"),
         2026: (15.24, "Budget 2026 estimate 2026/27")}
qc_bmmb = {2017: 16.72, 2018: 16.97, 2019: 14.79, 2020: 15.23, 2021: 27.12, 2022: 17.43}

provs = ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "ON", "PE", "QC", "SK", "YT", "NU"]
rows = []
for p in provs:
    for y in YEARS:
        s = st.val.get((p, y), np.nan) if (p, y) in st.index else np.nan
        q = st.q.get((p, y), "") if (p, y) in st.index else ""
        cv = crown.get((p, y), np.nan)
        snfd = s / cv if (pd.notna(s) and cv and cv > 0 and q not in ("n", "u")) else np.nan
        rows.append(dict(prov=p, year=y, stumpage_charges_cad=s, stumpage_qualifier=q, crown_harvest_m3=cv,
                         total_harvest_m3=total.get((p, y), np.nan), stump_nfd=snfd,
                         stump_bc_fp=bc_fp.get(y, (np.nan, ""))[0] if p == "BC" else np.nan,
                         qc_bmmb_auction=qc_bmmb.get(y, np.nan) if p == "QC" else np.nan))
df = pd.DataFrame(rows)
df.loc[(df.stumpage_charges_cad == 0) & df.prov.isin(["NT", "YT", "NU"]), "stump_nfd"] = 0.0

def choose(g):
    g = g.sort_values("year").copy()
    p = g.prov.iloc[0]
    if p == "BC":
        g["price_stump"] = g.stump_bc_fp
        g["price_stump_basis"] = [bc_fp[y][1] for y in g.year]
        return g
    s = g.set_index("year").stump_nfd
    basis = {}
    out = {}
    for y in g.year:
        if pd.notna(s.get(y)) and not (p == "ON" and y in (2020, 2021, 2022)):
            out[y] = s[y]; basis[y] = "NFD stumpage charges / Crown harvest"
    if p == "ON":
        m = np.nanmean([s.get(2019), s.get(2023)])
        for y in (2020, 2021, 2022):
            out[y] = m; basis[y] = "NFD n/a; mean of 2019 and 2023"
    if p in ("NT", "NU"):
        for y in g.year:
            out[y] = 0.0; basis[y] = "no Crown stumpage revenue reported in NFD"
    for y in g.year:  # single-year gaps inside the series (e.g. NB 2019, qualifier u): mean of neighbours
        if y not in out and (y - 1) in out and pd.notna(s.get(y + 1)):
            out[y] = (out[y - 1] + s[y + 1]) / 2; basis[y] = "NFD gap; mean of neighbouring years"
    last = max([y for y in out if not basis[y].startswith("carried")], default=None)
    for y in g.year:
        if y not in out and last is not None and y > last:
            out[y] = out[last]; basis[y] = f"carried forward from NFD {last}"
    g["price_stump"] = [out.get(y, np.nan) for y in g.year]
    g["price_stump_basis"] = [basis.get(y, "missing") for y in g.year]
    return g

df = pd.concat([choose(g) for _, g in df.groupby("prov")], ignore_index=True)
rw = OUT / "work" / "roundwood_value_per_m3.csv"
if rw.exists():
    x = pd.read_csv(rw)
    df = df.merge(x, on=["prov", "year"], how="left")
df.to_csv(OUT / "timber_prices_by_province_year.csv", index=False)
pd.set_option("display.width", 220)
print(df.pivot(index="year", columns="prov", values="price_stump").round(2))
print(df.pivot(index="year", columns="prov", values="stump_nfd").round(2))
