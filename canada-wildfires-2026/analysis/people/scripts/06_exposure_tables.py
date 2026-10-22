"""Step 6: aggregate DA, reserve and First Nation distances into the exposure tables.

Exposure definition: people in 2021 dissemination areas (DA) whose representative point is
inside or within 10 / 25 / 50 km (cumulative bands) of a fire outline of that year.
Sensitivity columns: (a) DA polygon edge instead of point (upper bound: any part of the DA
within the band); (b) 2026 only: only M3 outlines with an agency-reported fire within 5 km.
DAs without a 2021 population (174, table symbol '..') are counted separately (n_da_nopop_*).
Rebuild 2026-10-21: fire management areas from fma_v2 (no Parks Canada unit rows); 2026 distances exclude the
13 outlines flagged exclude_from_distance (00c_outline_class.py).
Outputs: exposure_by_area.csv (2026), exposure_years.csv (2023-2026),
first_nations_exposure.csv, da_no_population.csv
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

YEARS = [2023, 2024, 2025, 2026]
da = pd.read_csv(f"{WORK}/da_base.csv", dtype={"DGUID": str, "DAUID": str, "PRUID": str})
MINHA = [200, 1000]
for y in YEARS:
    da = da.merge(pd.read_csv(f"{WORK}/dist_{y}_da.csv", dtype={"DGUID": str}), on="DGUID", how="left")
    for m in MINHA:
        t = pd.read_csv(f"{WORK}/dist_{y}_da_min{m}.csv", dtype={"DGUID": str}, usecols=["DGUID", f"d{y}_km"])
        da = da.merge(t.rename(columns={f"d{y}_km": f"d{y}_ge{m}_km"}), on="DGUID", how="left")
da["pop"] = da.pop2021.fillna(0)
da["nopop"] = da.pop2021.isna()
CAN = da["pop"].sum()


def summarize(g, yr, matched=False):
    d = g[f"d{yr}_km"]
    r = {"pop_2021": g["pop"].sum(), "n_da": len(g)}
    r["pop_inside_outline"] = g.loc[d <= 0, "pop"].sum()
    for b in BANDS:
        r[f"pop_within_{b}km"] = g.loc[d <= b, "pop"].sum()
    for b in BANDS:
        r[f"pct_within_{b}km"] = round(100 * r[f"pop_within_{b}km"] / r["pop_2021"], 3) if r["pop_2021"] else np.nan
    for b in BANDS:
        r[f"pop_within_{b}km_da_polygon"] = g.loc[g[f"dpoly{yr}_km"] <= b, "pop"].sum()
    for m in MINHA:
        for b in BANDS:
            r[f"pop_within_{b}km_fires_ge{m}ha"] = g.loc[g[f"d{yr}_ge{m}_km"] <= b, "pop"].sum()
    if yr == 2026:
        for b in BANDS:
            r[f"pop_within_{b}km_agency_matched_only"] = g.loc[g["d2026_matched_km"] <= b, "pop"].sum()
    for b in BANDS:
        r[f"n_da_nopop_within_{b}km"] = int((g.nopop & (d <= b)).sum())
    for b in BANDS:
        r[f"pop_on_reserve_within_{b}km"] = g.loc[g.on_reserve & (d <= b), "pop"].sum()
    return r


def table(yr):
    rows = []
    rows.append(dict(year=yr, level="national", area_id="CA", area_name="Canada", prov="CA", **summarize(da, yr)))
    for p, g in da.groupby("prov"):
        rows.append(dict(year=yr, level="province", area_id=p, area_name=PR_NAME[p], prov=p, **summarize(g, yr)))
    for (fid, nm, ag), g in da.groupby(["fma_id", "fma_name", "fma_agency"]):
        rows.append(dict(year=yr, level="fire_management_area", area_id=int(fid), area_name=nm, agency=ag,
                         prov=g.prov.mode().iloc[0], **summarize(g, yr)))
    return pd.DataFrame(rows)


allyrs = pd.concat([table(y) for y in YEARS], ignore_index=True)
num = [c for c in allyrs.columns if c.startswith("pop")]
allyrs[num] = allyrs[num].round(0)
allyrs[allyrs.year == 2026].drop(columns="year").to_csv(f"{OUT}/exposure_by_area.csv", index=False)
allyrs[allyrs.level.isin(["national", "province", "fire_management_area"])].to_csv(
    f"{OUT}/exposure_years.csv", index=False)

# DAs with no 2021 population
np_ = da[da.nopop][["DGUID", "DAUID", "prov", "reserve_name", "nearest_reserve_name", "nearest_reserve_km",
                    "fma_name", "lon", "lat"] + [f"d{y}_km" for y in YEARS]].copy()
np_["inside_reserve_polygon"] = np_.reserve_name.notna()
np_.sort_values(["prov", "DAUID"]).to_csv(f"{OUT}/da_no_population.csv", index=False)

# First Nations
ir = gpd.read_file(f"{WORK}/reserves_albers.gpkg").drop(columns="geometry").rename(
    columns={"JUR1": "prov", "NAME1": "reserve_name"})
fng = gpd.read_file(f"{DATA}/geo/indigenous/fn/Premiere_Nation_First_Nation_GPKG.gpkg").to_crs(ALBERS)
prv = gpd.read_file(f"{DATA}/geo/statcan/lpr_000b21a_e_provinces_2021.gpkg").to_crs(ALBERS)
prv["prov"] = prv.PRUID.astype(str).map(PR_ABBR)
jj = gpd.sjoin_nearest(fng[["geometry"]], prv[["prov", "geometry"]], how="left")
fng["prov"] = jj[~jj.index.duplicated()]["prov"]
ll = fng.to_crs("EPSG:4326"); fng["lon"] = ll.geometry.x.round(4); fng["lat"] = ll.geometry.y.round(4)
fn = pd.DataFrame(fng.drop(columns="geometry"))
for y in YEARS:
    ir = ir.merge(pd.read_csv(f"{WORK}/dist_{y}_reserves.csv"), on="NID", how="left")
    fn = fn.merge(pd.read_csv(f"{WORK}/dist_{y}_fn.csv"), on="band_number", how="left")
    for m in MINHA:
        ir = ir.merge(pd.read_csv(f"{WORK}/dist_{y}_reserves_min{m}.csv", usecols=["NID", f"d{y}_km"]).rename(
            columns={f"d{y}_km": f"d{y}_ge{m}_km"}), on="NID", how="left")
        fn = fn.merge(pd.read_csv(f"{WORK}/dist_{y}_fn_min{m}.csv", usecols=["band_number", f"d{y}_km"]).rename(
            columns={f"d{y}_km": f"d{y}_ge{m}_km"}), on="band_number", how="left")
res_pop = da.loc[da.on_reserve, "pop"].sum()
res_share = res_pop / CAN
fr = []
for yr in YEARS:
    for lvl, key in [("national", None), ("province", "prov")]:
        groups = [("CA", ir, fn, da)] if key is None else [
            (p, ir[ir.prov == p], fn[fn.prov == p], da[da.prov == p]) for p in sorted(da.prov.unique())]
        for p, gi, gf, gd in groups:
            for b in [0] + BANDS:
                col = f"d{yr}_km"
                tot = gd.loc[gd[col] <= b, "pop"].sum()
                onr = gd.loc[gd.on_reserve & (gd[col] <= b), "pop"].sum()
                r = dict(year=yr, level=lvl, prov=p, band_km=b,
                         reserves_total=len(gi), reserves_within=int((gi[col] <= b).sum()),
                         fn_communities_total=len(gf), fn_communities_within=int((gf[col] <= b).sum()),
                         pop_exposed_total=round(tot), pop_exposed_on_reserve=round(onr),
                         pct_exposed_on_reserve=round(100 * onr / tot, 2) if tot else np.nan,
                         reserve_share_of_population_pct=round(100 * gd.loc[gd.on_reserve, "pop"].sum() / gd["pop"].sum(), 2),
                         da_nopop_within=int((gd.nopop & (gd[col] <= b)).sum()))
                r["overrepresentation_ratio"] = (round(r["pct_exposed_on_reserve"] / r["reserve_share_of_population_pct"], 2)
                                                 if tot and r["reserve_share_of_population_pct"] else np.nan)
                for m in MINHA:
                    c2 = f"d{yr}_ge{m}_km"
                    r[f"reserves_within_fires_ge{m}ha"] = int((gi[c2] <= b).sum())
                    r[f"fn_communities_within_fires_ge{m}ha"] = int((gf[c2] <= b).sum())
                    r[f"pop_exposed_total_fires_ge{m}ha"] = round(gd.loc[gd[c2] <= b, "pop"].sum())
                    r[f"pop_exposed_on_reserve_fires_ge{m}ha"] = round(gd.loc[gd.on_reserve & (gd[c2] <= b), "pop"].sum())
                if yr == 2026:
                    r["reserves_within_agency_matched_only"] = int((gi["d2026_matched_km"] <= b).sum())
                    r["fn_communities_within_agency_matched_only"] = int((gf["d2026_matched_km"] <= b).sum())
                fr.append(r)
fr = pd.DataFrame(fr)
fr.to_csv(f"{OUT}/first_nations_exposure.csv", index=False)

# detail lists for 2026
ir[ir.d2026_km <= 50].sort_values("d2026_km").to_csv(f"{OUT}/reserves_within_50km_2026.csv", index=False)
fn[fn.d2026_km <= 50].sort_values("d2026_km").to_csv(f"{OUT}/fn_communities_within_50km_2026.csv", index=False)

pd.set_option("display.width", 250)
nat = allyrs[allyrs.level == "national"]
print(nat[["year", "pop_inside_outline", "pop_within_10km", "pop_within_25km", "pop_within_50km",
           "pct_within_50km", "pop_within_50km_da_polygon", "n_da_nopop_within_50km"]].to_string())
print(nat[["year"] + [c for c in allyrs.columns if "_fires_ge" in c or "agency_matched" in c]].T.to_string())
pv = allyrs[(allyrs.year == 2026) & (allyrs.level == "province")].sort_values("pop_within_50km", ascending=False)
print(pv[["prov", "pop_within_10km", "pop_within_25km", "pop_within_50km", "pct_within_50km"]].to_string())
fm = allyrs[(allyrs.year == 2026) & (allyrs.level == "fire_management_area")].sort_values("pop_within_50km", ascending=False).head(15)
print(fm[["area_name", "prov", "pop_within_10km", "pop_within_25km", "pop_within_50km", "pct_within_50km"]].to_string())
print("reserve pop", res_pop, "share", round(100 * res_share, 3))
print(fr[fr.level == "national"].drop(columns=["level", "prov"]).to_string())
print("no-pop DAs:", len(np_), "inside reserve polygon:", int(np_.inside_reserve_polygon.sum()),
      "within 2 km of reserve:", int((np_.nearest_reserve_km <= 2).sum()), np_.prov.value_counts().to_dict())
