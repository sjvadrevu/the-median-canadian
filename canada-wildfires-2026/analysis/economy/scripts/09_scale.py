"""Scale translations, each computed from official numbers, with inputs listed per row.

Outputs: scale_comparisons.csv (one row per comparison: metric, value, comparator, comparator value, ratio, inputs)
         country_area_ratios.csv (2026 and 2023-2026 area against every country in UN DYB 2023 Table 3)
"""
import numpy as np
import pandas as pd
from ecommon import OUT, RAW, FOREST, WORK

R = []


def add(group, metric, value, unit, comparator, comp_value, comp_unit, ratio, phrase, inputs):
    R.append(dict(group=group, metric=metric, value=value, unit=unit, comparator=comparator,
                  comparator_value=comp_value, comparator_unit=comp_unit, ratio=ratio, plain=phrase, inputs=inputs))


ft = pd.read_csv(FOREST / "canada_totals.csv", index_col=0).iloc[:, 0]
A26_OFF = 4500984.6
A26_MAP = 5302938.158
AU_OFF = float(ft["official_scaled_union_2023_2026_ha"])
AU_MAP = float(ft["union_2023_2026_all_land_mapped_ha"])
CF = float(ft["canada_forest_ha"])
F26 = float(ft["forest_burned_2026_mapped_ha"])
FU = float(ft["union_2023_2026_forest_burned_ha"])
NAT_RATIO = A26_OFF / A26_MAP
areas = {"2026 official": A26_OFF, "2023-2026 distinct land, official-scaled": AU_OFF}
src_area = ("2026: NRCan CWFIF reported-fire-stats 2026-10-20 (4,500,984.6 ha); 2023-2026: union of NBAC 2023-2025 "
            "and M3 2026 footprints, ratio applied to NFD 2023-2025 + 2026 official (analysis/forest/canada_totals.csv)")

# --- forest share as "one hectare in every N"
for lab, f, note in [("2026 forest burned, mapped", F26, "M3 outlines on Land Cover 2020 forest"),
                     ("2026 forest burned, scaled to official area", F26 * NAT_RATIO,
                      f"mapped x national official/mapped ratio {NAT_RATIO:.4f}"),
                     ("2023-2026 forest burned (union), mapped", FU, "NBAC 2023-2025 + M3 2026 union")]:
    s = f / CF
    add("forest share", lab, f, "ha", "Canada's forest (Land Cover 2020 classes 1,2,5,6)", CF, "ha", s,
        f"{s*100:.2f}% of Canada's forest: one hectare in every {1/s:.0f}",
        f"{note}; forest denominator analysis/forest/canada_totals.csv")

# --- provinces (land area, 2021 Census table 98-10-0001)
p = pd.read_csv(RAW.parent.parent.parent / "data" / "geo" / "statcan" / "tables" / "98100001" / "98100001.csv",
                encoding="utf-8-sig", dtype=str)
la = [c for c in p.columns if "Land area" in c][0]
p["land_km2"] = pd.to_numeric(p[la], errors="coerce")
p = p[p.GEO != "Canada"][["GEO", "land_km2"]]
for lab, a in areas.items():
    km2 = a / 100
    for _, r in p.sort_values("land_km2").iterrows():
        ratio = km2 / r.land_km2
        add("provinces", lab, km2, "km2", r.GEO + " (land area)", r.land_km2, "km2", ratio,
            f"{ratio:.2f} times the land area of {r.GEO}", f"{src_area}; land area 2021 Census table 98-10-0001-01")

# --- cities (CSD land area, table 98-10-0002)
c = pd.read_csv(RAW / "areas" / "t98100002" / "98100002.csv", encoding="utf-8-sig", dtype=str)
lac = [x for x in c.columns if "Land area" in x][0]
c["land_km2"] = pd.to_numeric(c[lac], errors="coerce")
cities = {"Toronto": "2021A00053520005", "Montréal": "2021A00052466023", "Calgary": "2021A00054806016",
          "Ottawa": "2021A00053506008", "Edmonton": "2021A00054811061", "Winnipeg": "2021A00054611040",
          "Vancouver": "2021A00055915022", "Québec": "2021A00052423027", "Halifax": "2021A00051209034"}
for lab, a in areas.items():
    km2 = a / 100
    for name, dg in cities.items():
        v = float(c.loc[c.DGUID == dg, "land_km2"].iloc[0])
        add("cities", lab, km2, "km2", f"City of {name} (census subdivision land area)", v, "km2", km2 / v,
            f"{km2 / v:,.0f} times the land area of the City of {name}",
            f"{src_area}; CSD land area 2021 Census table 98-10-0002-01 (DGUID {dg})")

# --- countries (UN Demographic Yearbook 2023, Table 3, surface area km2, 2023)
x = pd.read_excel(RAW / "areas" / "table03.xls", header=None)
rows = []
for i in range(6, len(x) - 1):
    name = x.iloc[i, 0]
    if isinstance(name, str) and x.iloc[i, 1:17].isna().all():
        v = pd.to_numeric(x.iloc[i + 1, 14], errors="coerce")
        if pd.notna(v) and v > 0 and name.upper() != name:
            rows.append(dict(country=name.split(" - ")[0].strip(), surface_km2=float(v)))
co = pd.DataFrame(rows).drop_duplicates("country")
for lab, a in areas.items():
    co[f"ratio_{lab}"] = (a / 100) / co.surface_km2
co.sort_values("surface_km2").to_csv(OUT / "country_area_ratios.csv", index=False)
pick = ["Netherlands (Kingdom of the)", "Switzerland", "Denmark", "Belgium", "Ireland", "Austria", "Portugal",
        "Czechia", "Greece", "United Kingdom of Great Britain and Northern Ireland", "New Zealand", "Italy",
        "Germany", "Japan", "Norway", "Finland", "Poland", "Sweden", "France", "Spain"]
for lab, a in areas.items():
    km2 = a / 100
    for n in pick:
        r = co[co.country.str.startswith(n.split(" (")[0])]
        if r.empty:
            continue
        r = r.iloc[0]
        add("countries", lab, km2, "km2", f"{r.country} (surface area)", r.surface_km2, "km2", km2 / r.surface_km2,
            f"{km2 / r.surface_km2:.2f} times the area of {r.country}",
            f"{src_area}; UN Demographic Yearbook 2023 Table 3 surface area (km2, includes inland water)")
    # closest countries in size
    co["d"] = (np.log(co.surface_km2) - np.log(km2)).abs()
    for _, r in co.nsmallest(3, "d").iterrows():
        add("countries (closest in size)", lab, km2, "km2", f"{r.country} (surface area)", r.surface_km2, "km2",
            km2 / r.surface_km2, f"about the size of {r.country} ({km2 / r.surface_km2:.2f} times)",
            "UN Demographic Yearbook 2023 Table 3")

# --- wood as years of harvest, biomass/volume as share of national stock
t = pd.read_csv(OUT / "timber_biomass_carbon_by_area.csv")
cn = t[t.level == "Canada"].set_index("scope")
h = pd.read_csv(OUT / "harvest_nfd_by_province.csv", index_col=0)
H24 = h.loc["Canada", "harvest_2024_m3"]
HM = h.loc["Canada", "harvest_mean_2020_2024_m3"]
for sc, lab in [("2026", "2026"), ("union_2023_2026", "2023-2026")]:
    for sfx in ["mapped", "scaled"]:
        col = "vol_merch_knn2011_m3" if sfx == "mapped" else "vol_merch_knn2011_scaled_m3"
        v = cn.loc[sc, col]
        add("wood", f"{lab} merchantable volume in burned area ({sfx})", v, "m3",
            "Canada roundwood harvest 2024 (NFD, all provinces)", H24, "m3/yr", v / H24,
            f"{v / H24:.1f} years of Canada's 2024 harvest",
            "kNN 2011 merchantable volume (NRCan 250 m) summed over burned cells; NFD net merchantable roundwood harvest")
        add("wood", f"{lab} merchantable volume in burned area ({sfx})", v, "m3",
            "Canada roundwood harvest, mean 2020-2024", HM, "m3/yr", v / HM,
            f"{v / HM:.1f} years of Canada's average 2020-2024 harvest", "as above")
nfi = {"vol": 48189.348e6, "agb": 30063.951e6}
for sc, lab in [("2026", "2026"), ("union_2023_2026", "2023-2026")]:
    v = cn.loc[sc, "vol_total_knn2011_m3"]
    add("wood", f"{lab} total tree volume in burned area (mapped)", v, "m3", "NFI total tree volume on forest land",
        nfi["vol"], "m3", v / nfi["vol"], f"{v / nfi['vol'] * 100:.1f}% of Canada's total tree volume (NFI)",
        "kNN 2011 total volume; NFI Table 15.0 (ca_t15_forage20_vol_en.csv)")
    b = cn.loc[sc, "agb_prefire_scanfi_t"]
    add("wood", f"{lab} aboveground biomass in burned area (mapped, SCANFI pre-fire)", b, "t",
        "NFI total aboveground biomass on forest land", nfi["agb"], "t", b / nfi["agb"],
        f"{b / nfi['agb'] * 100:.1f}% of Canada's aboveground tree biomass (NFI)",
        "SCANFI v2 2020/2025; NFI Table 17.0 (ca_t17_forage20_biom_en.csv)")

# --- carbon (our estimate) against the national inventory
g = pd.read_csv(RAW / "ghg" / "B-Economic-Sector_GHG_Econ_Can_Prov_Terr.csv", encoding="latin-1")
g = g[(g.Year == 2024) & (g.Region == "Canada")]
NAT = float(g[g.Index == 0]["Total (kt CO2e)"].iloc[0]) * 1000
CARS = float(g[g.Index == 19]["Total (kt CO2e)"].iloc[0]) * 1000
gi = pd.read_csv(RAW / "ghg" / "A-IPCC-Sector_GHG_IPCC_Can_Prov_Terr.csv", encoding="latin-1")
gi = gi[(gi.Year == 2024) & (gi.Region == "Canada")]
LDGV = float(gi[gi.CategoryID == 221].CO2eq.iloc[0]) * 1000
ELEC = float(g[g.Index == 16]["Total (kt CO2e)"].iloc[0]) * 1000
comps = [("Canada national inventory total 2024 (NIR 2026)", NAT, "of national emissions"),
         ("Passenger cars, light trucks and motorcycles 2024 (economic sector)", CARS,
          "of emissions from all passenger cars, light trucks and motorcycles"),
         ("Light-duty gasoline vehicles (cars) 2024 (IPCC 1.A.3.b)", LDGV, "of emissions from gasoline cars"),
         ("Electricity sector 2024", ELEC, "of electricity-sector emissions")]
for sc, lab in [("2026", "2026"), ("union_2023_2026", "2023-2026")]:
    for sfx in ["scaled", "mapped"]:
        lo, hi = cn.loc[sc, f"co2_low_{sfx}_t"], cn.loc[sc, f"co2_high_{sfx}_t"]
        for cname, cv, ph in comps:
            add("carbon (our estimate)", f"{lab} CO2 from burned aboveground biomass ({sfx}), low-high", f"{lo:.4g}-{hi:.4g}",
                "t CO2", cname, cv, "t CO2e/yr", f"{lo / cv:.3f}-{hi / cv:.3f}",
                f"{lo / cv:.2f} to {hi / cv:.2f} years {ph} ({lo / cv * 365:.0f} to {hi / cv * 365:.0f} days)",
                "SCANFI pre-fire AGB x 0.5 C x combustion share (low = foliage share, high = foliage+branch+bark "
                "share, kNN 2011) x 44/12; GHG_Econ/GHG_IPCC_Can_Prov_Terr.csv 2024")
sc = pd.DataFrame(R)
sc.to_csv(OUT / "scale_comparisons.csv", index=False)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 120)
print(sc[["group", "metric", "comparator", "plain"]].to_string())
print(co.sort_values("surface_km2").to_string()[:100])

# --- per-year lens (2016-2026 and 2023-2026): area, forest share, wood, carbon, each against that year's comparator
fs = pd.read_csv(FOREST / "canada_forest_share_by_year.csv", index_col=0).iloc[:, 0]
off = pd.read_csv(RAW.parent.parent.parent / "data" / "smoke-cost" / "fire_area_count_by_agency_year.csv")
tby = pd.read_csv(OUT / "timber_carbon_by_year.csv")
tby = tby[tby.prov == "Canada"].set_index("year")
co_sorted = co.sort_values("surface_km2")
yr_rows = []
for y in list(range(2016, 2027)) + ["2023_2026"]:
    if y == "2023_2026":
        a_off, share = AU_OFF, FU / CF
        a_src = "union official-scaled (analysis/forest)"
    elif y == 2026:
        a_off, share = A26_OFF, fs[2026]
        a_src = "CWFIF 2026-10-20, 13 agencies incl. Parks Canada"
    else:
        a_off, share = off[off.year == y].area_burned_ha.sum(), fs[y]
        a_src = "NFD final, 12 provinces/territories (no Parks Canada series)"
    km2 = a_off / 100
    near = co_sorted.iloc[(np.log(co_sorted.surface_km2) - np.log(km2)).abs().argsort()[:1]].iloc[0]
    pr = p.iloc[(np.log(p.land_km2) - np.log(km2)).abs().argsort()[:1]].iloc[0]
    t = tby.loc[str(y)] if str(y) in tby.index.astype(str) else tby.loc[y]
    yr_rows.append(dict(year=y, area_official_ha=a_off, area_source=a_src, forest_share_mapped=share,
                        one_hectare_in_every=1 / share, toronto_multiples=km2 / 631.10,
                        closest_country=near.country, closest_country_ratio=km2 / near.surface_km2,
                        closest_province=pr.GEO, closest_province_ratio=km2 / pr.land_km2,
                        merch_volume_scaled_m3=t.vol_merch_scaled_m3, harvest_m3=t.harvest_m3,
                        harvest_year=t.harvest_year, years_of_harvest_scaled=t.years_of_harvest_scaled,
                        co2_low_scaled_t=t.co2_low_scaled_t, co2_high_scaled_t=t.co2_high_scaled_t,
                        emissions_year=t.emissions_year, national_total_t=t.national_total_t,
                        share_national_low=t.co2_low_scaled_share_national,
                        share_national_high=t.co2_high_scaled_share_national,
                        days_national_low=t.co2_low_scaled_share_national * 365,
                        days_national_high=t.co2_high_scaled_share_national * 365,
                        years_cars_low=t.co2_low_scaled_t / t.cars_lighttrucks_moto_t,
                        years_cars_high=t.co2_high_scaled_t / t.cars_lighttrucks_moto_t,
                        nir_managed_forest_wildfire_t_co2e=t.get("nir_managed_forest_wildfire_direct_immediate_t_co2e")))
yb = pd.DataFrame(yr_rows)
yb.to_csv(OUT / "scale_by_year.csv", index=False)
print(yb.drop(columns=["area_source"]).to_string())
