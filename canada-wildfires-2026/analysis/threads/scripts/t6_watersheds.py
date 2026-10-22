"""Thread 6: drinking-water source areas and fire, 2023-2026.

National: NRCan National Hydro Network (NHN) work units (1,341 polygons, each tagged with its Water Survey of
Canada sub-sub-drainage area, SSDA). Burned share per work unit and per SSDA = burned 240 m cells (union of NBAC
2023-2025 and CWFIS M3 2026, analysis/forest/work/burn_<y>.npy, all outlines) / unit area on the same grid.
Population centres (StatCan 2021) are assigned the work unit and SSDA containing their representative point.
No upstream routing: NHN work units carry no network topology in the index, so 'downstream' is not modelled.

British Columbia (openly published drinking-water data, DataBC):
  - 466 designated Community Watersheds (WLS_COMMUNITY_WS_PUB_SVW): the drainage area upstream of a community
    water-supply intake. Burned share computed by exact vector overlay with the fire outlines (people/work/fires_<y>.gpkg).
  - Surface-water drinking water source points (DWS_SOURCE_POINT, SOURCE_TYPE surface) linked to their community
    watershed or, failing that, the NHN work unit they fall in.
"""
import numpy as np, pandas as pd, geopandas as gpd
from rasterio import features
import json
from affine import Affine
from shapely import make_valid

BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
T = f"{BASE}/analysis/threads"
FW = f"{BASE}/analysis/forest/work"
PW = f"{BASE}/analysis/people/work"
YEARS = [2023, 2024, 2025, 2026]
m = json.load(open(f"{FW}/grid_meta.json")); TR = Affine(*m["transform"]); H, W = m["H"], m["W"]
asc = np.load(f"{FW}/areal_scale_coarse.npy")
def cell_ha(idx):
    r = np.minimum((idx // W) // m["step"], asc.shape[0] - 1); c = np.minimum((idx % W) // m["step"], asc.shape[1] - 1)
    return 57600.0 / asc[r, c].astype("float64") / 1e4

# ---- NHN work units on the grid
wu = gpd.read_file(f"{T}/raw/nhn/NHN_INDEX_22_INDEX_WORKUNIT_LIMIT_2.shp").to_crs("EPSG:3979")
wu["geometry"] = wu.geometry.simplify(120).map(lambda g: make_valid(g) if not g.is_valid else g)
wu["uid"] = np.arange(1, len(wu) + 1)
# rasterise in strips of 1,000 rows to keep memory low; accumulate unit area and burned area per year and union
burn = {y: np.load(f"{FW}/burn_{y}.npy").astype(np.int64) for y in YEARS}
union = np.unique(np.concatenate(list(burn.values())))
sets = {**{y: burn[y] for y in YEARS}, "union": union}
area = np.zeros(len(wu) + 1)
bsum = {k: np.zeros(len(wu) + 1) for k in sets}
geoms = list(zip(wu.geometry, wu.uid))
STRIP = 1000
for r0 in range(0, H, STRIP):
    h = min(STRIP, H - r0)
    g = features.rasterize(geoms, out_shape=(h, W), transform=TR * Affine.translation(0, r0), fill=0, dtype="uint16").ravel()
    nz = np.flatnonzero(g)
    area += np.bincount(g[nz], weights=cell_ha(nz.astype(np.int64) + r0 * W), minlength=len(wu) + 1)
    lo, hi = r0 * W, (r0 + h) * W
    for k, idx in sets.items():
        sel = idx[(idx >= lo) & (idx < hi)]
        u = g[sel - lo]; kk = u > 0
        bsum[k] += np.bincount(u[kk], weights=cell_ha(sel[kk]), minlength=len(wu) + 1)
    del g, nz
print("rasterised work units", flush=True)
def burned_by_unit(key):
    return bsum[key]
res = pd.DataFrame({"uid": wu.uid, "DATASETNAM": wu.DATASETNAM, "WSCSSDA": wu.WSCSSDA, "WSCSSDANAM": wu.WSCSSDANAM,
                    "WSCSDANAME": wu.WSCSDANAME, "WSCMDANAME": wu.WSCMDANAME, "prov1": wu.PROVCD_1, "area_ha_grid": area[1:]})
for y in YEARS:
    res[f"burned_ha_{y}"] = burned_by_unit(y)[1:]
res["burned_ha_2023_2026_union"] = burned_by_unit("union")[1:]
res["share_2023_2026"] = res.burned_ha_2023_2026_union / res.area_ha_grid
for y in YEARS:
    res[f"share_{y}"] = res[f"burned_ha_{y}"] / res.area_ha_grid
res.to_csv(f"{T}/t6_workunit_burned_share.csv", index=False)
ss = res.groupby(["WSCSSDA", "WSCSSDANAM"]).agg(area_ha=("area_ha_grid", "sum"), burned_union=("burned_ha_2023_2026_union", "sum"),
                                                **{f"b{y}": (f"burned_ha_{y}", "sum") for y in YEARS}).reset_index()
ss["share_2023_2026"] = ss.burned_union / ss.area_ha
ss.to_csv(f"{T}/t6_ssda_burned_share.csv", index=False)

# ---- population centres
pc = gpd.read_file(f"{BASE}/data/geo/statcan/popcentres_2021_pop.gpkg").to_crs("EPSG:3979")
pcp = pc.copy(); pcp["geometry"] = pc.geometry.representative_point()
j = gpd.sjoin(pcp[["PCUID", "PCNAME", "PRUID", "pop2021", "geometry"]], wu[["uid", "WSCSSDA", "geometry"]], how="left", predicate="within")
j = j.drop_duplicates("PCUID")
j = j.merge(res[["uid", "DATASETNAM", "WSCSSDANAM", "share_2023_2026"] + [f"share_{y}" for y in YEARS]], on="uid", how="left")
j = j.merge(ss[["WSCSSDA", "share_2023_2026"]].rename(columns={"share_2023_2026": "ssda_share_2023_2026"}), on="WSCSSDA", how="left")
j.drop(columns="geometry").to_csv(f"{T}/t6_popcentres_watershed.csv", index=False)

out = []
for thr in (0.05, 0.10, 0.20):
    a = res.share_2023_2026 > thr
    out.append(dict(level="NHN work unit", threshold=thr, units_over=int(a.sum()), units_total=len(res),
                    pcs_in_units=int((j.share_2023_2026 > thr).sum()), pc_pop=j.loc[j.share_2023_2026 > thr, "pop2021"].sum()))
    b = ss.share_2023_2026 > thr
    out.append(dict(level="WSC sub-sub-drainage area", threshold=thr, units_over=int(b.sum()), units_total=len(ss),
                    pcs_in_units=int((j.ssda_share_2023_2026 > thr).sum()), pc_pop=j.loc[j.ssda_share_2023_2026 > thr, "pop2021"].sum()))
    for y in YEARS:
        c = res[f"share_{y}"] > thr
        out.append(dict(level=f"NHN work unit, {y} alone", threshold=thr, units_over=int(c.sum()), units_total=len(res),
                        pcs_in_units=int((j[f"share_{y}"] > thr).sum()), pc_pop=j.loc[j[f"share_{y}"] > thr, "pop2021"].sum()))
O = pd.DataFrame(out); O.to_csv(f"{T}/t6_watershed_summary.csv", index=False)
print(O.to_string())
print(res.sort_values("share_2023_2026", ascending=False).head(25)[["DATASETNAM", "WSCSSDANAM", "prov1", "area_ha_grid", "share_2023_2026"]].to_string())
print(j[j.share_2023_2026 > 0.10].sort_values("pop2021", ascending=False).head(30)[["PCNAME", "PRUID", "pop2021", "WSCSSDANAM", "share_2023_2026"]].to_string())

# BC community watersheds and intakes: see t6b_bc_water.py
