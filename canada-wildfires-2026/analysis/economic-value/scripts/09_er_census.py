"""Map 2021 census divisions to 2021 economic regions (CD representative point inside ER polygon) and sum 2021
Census employment by industry (analysis/economy/census_divisions_jobs_and_fire.csv, table 98-10-0592-01) to ERs.
Output: er_census_jobs_2021.csv (ER, employed, forestry jobs NAICS 113+1153+321+322, forestry share, accommodation)."""
import pandas as pd
import geopandas as gpd
from vcommon import RAW, OUT, ECON, EWORK

er = gpd.read_file(RAW / "geo" / "er_2021.geojson")
cd = gpd.read_file(EWORK / "cd_2021_from_da.gpkg").to_crs(er.crs)
pts = cd.copy(); pts["geometry"] = cd.representative_point()
j = gpd.sjoin(pts[["CDUID", "geometry"]], er[["ERUID", "ERNAME", "geometry"]], predicate="within", how="left")
jobs = pd.read_csv(ECON / "census_divisions_jobs_and_fire.csv", dtype={"CDUID": str})
jobs = jobs.merge(j[["CDUID", "ERUID", "ERNAME"]], on="CDUID", how="left")
print("CDs without ER:", jobs.ERUID.isna().sum())
cols = ["employed_all", "forestry_jobs", "j113", "j1153", "j321", "j322", "accommodation_jobs", "pop2021"]
e = jobs.groupby(["ERUID", "ERNAME"])[cols].sum().reset_index()
e["forestry_share"] = e.forestry_jobs / e.employed_all
e["accommodation_share"] = e.accommodation_jobs / e.employed_all
e.to_csv(OUT / "er_census_jobs_2021.csv", index=False)
jobs[["CDUID", "cd_name", "prov", "ERUID", "ERNAME"]].to_csv(OUT / "work" / "cd_to_er_2021.csv", index=False)
print(e.sort_values("forestry_share", ascending=False).head(20).round(3).to_string())
