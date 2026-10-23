"""Step 1: one row per 2021 dissemination area (DA) with population, province, on-reserve flag,
census metropolitan area / agglomeration (CMA/CA), and Census Profile age and low-income counts.

Inputs:
  ../people/work/da_base.csv (DA representative points, 2021 pop, province, on_reserve; built in people/scripts/01_da_base.py)
  raw/profile/da_profile_age_income.csv (StatCan Census Profile 2021 SDMX API, DF_DA, characteristics 1, 8, 10, 24, 321, 326)
  raw/cma/cma_2021.gpkg (StatCan 2021 cartographic boundary file, CMA/CA layer, via geo.statcan.gc.ca MapServer/6)
Output: work/da_attr.csv
"""
import os, pandas as pd, numpy as np, geopandas as gpd

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(H)
da = pd.read_csv(f"{W}/people/work/da_base.csv", dtype={"DAUID": str, "DGUID": str})
da = da[["DAUID", "DGUID", "PRUID", "prov", "pop2021", "on_reserve", "reserve_name", "lon", "lat"]]

# Census Profile
p = pd.read_csv(f"{H}/raw/profile/da_profile_age_income.csv", dtype={"REF_AREA": str, "ALT_GEO_CODE": str},
                usecols=["REF_AREA", "CHARACTERISTIC", "OBS_VALUE"])
p = p.pivot_table(index="REF_AREA", columns="CHARACTERISTIC", values="OBS_VALUE", aggfunc="first")
p = p.rename(columns={1: "prof_pop2021", 8: "age_total", 10: "age_0_4", 24: "age_65p",
                      321: "lim_universe", 326: "lim_low_income"})
p.index.name = "DGUID"
print("profile DAs", len(p), "non-null:", p.notna().sum().to_dict())
da = da.merge(p.reset_index(), on="DGUID", how="left")

# CMA / CA membership by point in polygon
cma = gpd.read_file(f"{H}/raw/cma/cma_2021.gpkg")[["CMAUID", "CMAPUID", "CMANAME", "CMATYPE", "geometry"]]
pts = gpd.GeoDataFrame(da[["DAUID"]], geometry=gpd.points_from_xy(da.lon, da.lat), crs=4326)
j = gpd.sjoin(pts, cma, how="left", predicate="within")
j = j[~j.index.duplicated()]
da["CMAUID"] = j["CMAUID"].values
da["CMANAME"] = j["CMANAME"].values
da["CMATYPE"] = j["CMATYPE"].values  # B = CMA, K = tracted CA, D = non-tracted CA
miss = da.CMAUID.isna() & da.DAUID.notna()
# points on generalised edges: snap to a CMA within 1 km
if miss.any():
    pm = pts[miss.values].to_crs(3347); cm = cma.to_crs(3347)
    jn = gpd.sjoin_nearest(pm, cm, how="left", max_distance=1000, distance_col="d")
    jn = jn[~jn.index.duplicated()]
    ok = jn.CMAUID.notna()
    da.loc[jn.index[ok], "CMAUID"] = jn.loc[ok, "CMAUID"].values
    da.loc[jn.index[ok], "CMANAME"] = jn.loc[ok, "CMANAME"].values
    da.loc[jn.index[ok], "CMATYPE"] = jn.loc[ok, "CMATYPE"].values
    print("snapped to CMA/CA within 1 km:", int(ok.sum()))
da["is_cma"] = da.CMATYPE.eq("B")
print("pop in CMAs", da.loc[da.is_cma, "pop2021"].sum(), "CMAs", da.loc[da.is_cma, "CMANAME"].nunique())
print("age_0_4 total", da.age_0_4.sum(), "65+", da.age_65p.sum(), "LIM low income", da.lim_low_income.sum(),
      "universe", da.lim_universe.sum())
print("pop2021 vs profile pop diff", (da.pop2021 - da.prof_pop2021).abs().sum())
da.to_csv(f"{H}/work/da_attr.csv", index=False)
