"""Thread 4: repeat exposure, 2023-2026. A place is 'exposed' in a year when it is within 10 km of a fire outline
of that year (NBAC 2023-2025 without prescribed burns; CWFIS M3 2026 without the 13 agricultural/grass and
military-range outlines). Count years exposed (0-4) for:
  - reserves (AL_TA Indian Reserve polygons, edge distance), with on-reserve 2021 population (DAs whose
    representative point lies in the reserve);
  - First Nation communities (ISC band locations, point distance);
  - population centres (StatCan 2021, polygon edge distance, computed here for every year);
  - dissemination areas (representative point), split on-reserve / off-reserve: people.
Distances for reserves, FN points and DAs reuse analysis/people/work/dist_<year>_*.csv (geodesic, from
02y_year_distances.py). Sensitivity: fires of 1,000 ha or more only (*_min1000 files) for the like-for-like basis.
"""
import numpy as np, pandas as pd, geopandas as gpd
from shapely import STRtree
BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
PW = f"{BASE}/analysis/people/work"
OUT = f"{BASE}/analysis/threads"
YEARS = [2023, 2024, 2025, 2026]
BAND = 10.0

def years_table(kind, key, suffix=""):
    out = None
    for y in YEARS:
        d = pd.read_csv(f"{PW}/dist_{y}_{kind}{suffix}.csv", dtype={key: str})
        d = d[[key, f"d{y}_km"]]
        out = d if out is None else out.merge(d, on=key, how="outer")
    out["n_years"] = sum((out[f"d{y}_km"] <= BAND).astype(int) for y in YEARS)
    return out

da = pd.read_csv(f"{PW}/da_base.csv", dtype={"DGUID": str, "reserve_nid": str})
res = gpd.read_file(f"{PW}/reserves_albers.gpkg")
fn = gpd.read_file(f"{BASE}/data/geo/indigenous/fn/Premiere_Nation_First_Nation_GPKG.gpkg")
pop_res = da[da.on_reserve].groupby("reserve_nid").pop2021.sum()
nda_res = da[da.on_reserve].groupby("reserve_nid").size()

rows = []
summ = []
for suffix, label in [("", "all outlines"), ("_min200", "fires >= 200 ha"), ("_min1000", "fires >= 1000 ha")]:
    # reserves
    r = years_table("reserves", "NID", suffix).merge(res[["NID", "NAME1", "JUR1"]], on="NID", how="right")
    r["n_years"] = r["n_years"].fillna(0).astype(int)
    r["pop2021"] = r.NID.map(pop_res).fillna(0)
    r["populated"] = r.NID.isin(pop_res[pop_res > 0].index)
    # FN communities
    f = years_table("fn", "band_number", suffix)
    f["band_number"] = f.band_number.astype(str)
    fn["band_number"] = fn["band_number"].astype(str)
    f = f.merge(fn.drop(columns="geometry"), on="band_number", how="right")
    f["n_years"] = f["n_years"].fillna(0).astype(int)
    # DAs
    dd = years_table("da", "DGUID", suffix).merge(da[["DGUID", "pop2021", "prov", "on_reserve"]], on="DGUID", how="right")
    dd["n_years"] = dd["n_years"].fillna(0).astype(int)
    if suffix == "":
        r.to_csv(f"{OUT}/t4_reserves_years_exposed.csv", index=False)
        f.to_csv(f"{OUT}/t4_fn_communities_years_exposed.csv", index=False)
    for k in [1, 2, 3, 4]:
        summ.append(dict(basis=label, unit="reserves (all 3,322)", years_ge=k, count=int((r.n_years >= k).sum()),
                         exactly=int((r.n_years == k).sum()), total=len(r), share=(r.n_years >= k).mean(),
                         people=r.loc[r.n_years >= k, "pop2021"].sum()))
        rp = r[r.populated]
        summ.append(dict(basis=label, unit="populated reserves (2021 count > 0)", years_ge=k, count=int((rp.n_years >= k).sum()),
                         exactly=int((rp.n_years == k).sum()), total=len(rp), share=(rp.n_years >= k).mean(),
                         people=rp.loc[rp.n_years >= k, "pop2021"].sum()))
        summ.append(dict(basis=label, unit="First Nation communities (638 ISC points)", years_ge=k, count=int((f.n_years >= k).sum()),
                         exactly=int((f.n_years == k).sum()), total=len(f), share=(f.n_years >= k).mean(), people=np.nan))
        for onr, nm in [(True, "people on reserve (DA points)"), (False, "people off reserve (DA points)")]:
            s = dd[dd.on_reserve == onr]
            summ.append(dict(basis=label, unit=nm, years_ge=k, count=int((s.n_years >= k).sum()), exactly=int((s.n_years == k).sum()),
                             total=len(s), share=s.loc[s.n_years >= k, "pop2021"].sum() / s.pop2021.sum(),
                             people=s.loc[s.n_years >= k, "pop2021"].sum()))
    # by province, all outlines, >=2 years
    for p, s in r.groupby("JUR1"):
        rows.append(dict(basis=label, unit="reserves", prov=p, total=len(s), ge2=int((s.n_years >= 2).sum()),
                         ge3=int((s.n_years >= 3).sum()), eq4=int((s.n_years == 4).sum()), people_ge2=s.loc[s.n_years >= 2, "pop2021"].sum()))
    for onr, nm in [(True, "on-reserve people"), (False, "off-reserve people")]:
        for p, s in dd[dd.on_reserve == onr].groupby("prov"):
            rows.append(dict(basis=label, unit=nm, prov=p, total=s.pop2021.sum(), ge2=s.loc[s.n_years >= 2, "pop2021"].sum(),
                             ge3=s.loc[s.n_years >= 3, "pop2021"].sum(), eq4=s.loc[s.n_years == 4, "pop2021"].sum(), people_ge2=np.nan))

# population centres: polygon edge distance to each year's outlines (planar Albers; geodesic differs by <1.4%)
pc = gpd.read_file(f"{BASE}/data/geo/statcan/popcentres_2021_pop.gpkg").to_crs("ESRI:102001")
pcr = pd.DataFrame({"PCUID": pc.PCUID, "name": pc.PCNAME, "PRUID": pc.PRUID, "pop": pc.pop2021})
for suffix, minha in [("", 0), ("_min200", 200), ("_min1000", 1000)]:
    nyrs = np.zeros(len(pc), int)
    for y in YEARS:
        fi = gpd.read_file(f"{PW}/fires_{y}.gpkg")
        if "exclude_from_distance" in fi.columns:
            fi = fi[~fi.exclude_from_distance.astype(bool)]
        if minha:
            tot = fi.groupby("fire_uid").area_ha.transform("sum")
            fi = fi[tot >= minha]
        tree = STRtree(fi.geometry.values)
        hit = np.zeros(len(pc), bool)
        idx = tree.query(pc.geometry.values, predicate="dwithin", distance=BAND * 1000)
        hit[np.unique(idx[0])] = True
        pcr[f"within10_{y}{suffix}"] = hit
        nyrs += hit
        del fi, tree
    pcr[f"n_years{suffix}"] = nyrs
pcr.to_csv(f"{OUT}/t4_popcentres_years_exposed.csv", index=False)
for suffix, label in [("", "all outlines"), ("_min200", "fires >= 200 ha"), ("_min1000", "fires >= 1000 ha")]:
    for k in [1, 2, 3, 4]:
        m = pcr[f"n_years{suffix}"] >= k
        summ.append(dict(basis=label, unit="population centres (1,026)", years_ge=k, count=int(m.sum()),
                         exactly=int((pcr[f"n_years{suffix}"] == k).sum()), total=len(pcr), share=m.mean(), people=pcr.loc[m, "pop"].sum()))
S = pd.DataFrame(summ)
S.to_csv(f"{OUT}/t4_repeat_exposure_summary.csv", index=False)
pd.DataFrame(rows).to_csv(f"{OUT}/t4_repeat_exposure_by_province.csv", index=False)
print(S.to_string())
print(pcr.sort_values("n_years", ascending=False).head(25).to_string())
