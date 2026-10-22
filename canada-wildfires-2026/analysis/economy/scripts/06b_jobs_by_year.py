"""Per-year (2016-2026) count of census divisions (CD) touched by fire and the forestry / accommodation jobs in them.

Burned area per CD and year from the 240 m burned cells (NBAC 2016-2025, CWFIS M3 2026), cell-centre rule.
CD polygons and 2021 Census jobs as in 06_livelihoods.py (work/cd_2021_from_da.gpkg,
census_divisions_jobs_and_fire.csv). Jobs are 2021 Census counts for every year (no annual CD series exists),
so year-to-year differences come only from which CDs burned.
Scopes per year: touched (>= 100 ha mapped burned in the CD) and burned >= 1% of CD land.
Outputs: jobs_by_year.csv (Canada and province x year x scope), work/cd_burned_ha_by_year.csv
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from affine import Affine
from rasterio import features
from ecommon import WORK, OUT, FWORK
from grid import meta, cell_area_m2

m = meta()
T = Affine(*m["transform"])
cd = gpd.read_file(WORK / "cd_2021_from_da.gpkg").to_crs(m["crs"])
cdid = np.zeros((m["H"], m["W"]), dtype="uint16")
for i, g in enumerate(cd.geometry, start=1):
    features.rasterize([(g, i)], out=cdid, transform=T)
flat = cdid.ravel()
code = np.array(["none"] + list(cd.CDUID))
rows = {}
for y in range(2016, 2027):
    idx = np.load(FWORK / f"burn_{y}.npy")
    a = cell_area_m2(idx) / 1e4
    rows[y] = pd.Series(np.bincount(flat[idx], weights=a, minlength=len(code)), index=code)
del cdid, flat
bh = pd.DataFrame(rows).drop(index="none")
bh.index.name = "CDUID"
bh.to_csv(WORK / "cd_burned_ha_by_year.csv")

j = pd.read_csv(OUT / "census_divisions_jobs_and_fire.csv", dtype={"CDUID": str}).set_index("CDUID")
bh = bh.reindex(j.index).fillna(0)
out = []
for y in bh.columns:
    for scope, sel in [("touched", bh[y] >= 100), ("burned_ge1pct", bh[y] / j.land_ha >= 0.01)]:
        g = j[sel]
        for p, gg in list(g.groupby("prov")) + [("Canada", g)]:
            hf, ha = gg[gg.high_forestry], gg[gg.high_accommodation]
            out.append(dict(year=y, scope=scope, prov=p, n_cd=len(gg), employed_all=gg.employed_all.sum(),
                            forestry_jobs=gg.forestry_jobs.sum(), accommodation_jobs=gg.accommodation_jobs.sum(),
                            n_cd_high_forestry=len(hf), forestry_jobs_in_high_forestry_cd=hf.forestry_jobs.sum(),
                            n_cd_high_accommodation=len(ha),
                            accommodation_jobs_in_high_accommodation_cd=ha.accommodation_jobs.sum(),
                            mapped_burned_ha_in_these_cd=bh.loc[gg.index, y].sum()))
o = pd.DataFrame(out)
o.to_csv(OUT / "jobs_by_year.csv", index=False)
print(o[o.prov == "Canada"].to_string())
