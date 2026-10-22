"""Analyses 2, 3, 4 and 6: official-scaled hectares and forest share burned by fire management area,
Canada totals, cumulative 2023-2026, reburns, and validation of mapped outlines vs official totals.

Area layer: data/geo/fma_v2.gpkg (rebuild 2026-10-21): 186 rows that tile Canada; Manitoba as 22 MWS fire and
travel restriction areas + agricultural-south remainder, Quebec as 65 SOPFEU fire danger zones + far-north
remainder; no separate Parks Canada layer (national parks are part of the province rows they lie in).

Allocation rule (rebuild 2026-10-21, agreed with the user):
  * Official total per province P = provincial agency official 2026 total (CWFIF/CIFFC as of 2026-10-20)
    + the Parks Canada official 2026 total (124,872.1 ha) allocated to provinces in proportion to the CWFIS M3
    outline area (ESRI:102001) inside national parks (CLSS CLAB 2026-10-05 boundaries) in each province.
  * factor_P = official total P / M3 outline area in P (all of it, national parks included).
  * Area official-scaled ha = M3 outline area in the area x factor_P; a province with a single row takes its
    official total. Nunavut has no official agency total and no M3 area inside national parks, so it is not scaled.
  * Province totals therefore include national parks inside them.
  * Forest share burned = forest area (Land Cover 2020, classes 1,2,5,6) inside the 2026 outlines in the area /
    total forest area in the area (whole area polygon). A ratio of mapped quantities, not scaled; the scaled
    version (share x factor_P) is reported next to it and is the basis for the headline record claim.
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import make_valid
from common import M3, FMA_SIMP, FMA_GRID, PARKS, OFFICIAL, OUTLINE_CLASS, OUT, WORK, EA
from grid import load, cell_area_m2, meta

pd.set_option("display.width", 250)
YEARS_HIST = list(range(1972, 2026))

# ---------------------------------------------------------------- official totals
off = pd.read_csv(OFFICIAL)
off26 = off[off.year == 2026].set_index("ISO").area_burned_ha
PC_OFFICIAL = off26["PC"]

# ---------------------------------------------------------------- vector overlay (hectares)
fma = gpd.read_file(FMA_SIMP)                          # 20 m simplified copy of fma_v2 (02b)
attrs = fma.drop(columns=["geometry", "simplify_area_change"]).copy()
parks = gpd.read_file(PARKS).to_crs(EA)
park_union = make_valid(parks.geometry.make_valid().union_all())

m3 = gpd.read_file(M3).to_crs(EA)
m3["geometry"] = [make_valid(g) if not g.is_valid else g for g in m3.geometry]
m3["mapped_ha"] = m3.area / 1e4

cache = WORK / "m3_fma_v2_overlay.gpkg"
if cache.exists():
    ov = gpd.read_file(cache, layer="ov")
else:
    ov = gpd.overlay(m3[["UID", "geometry"]], fma[["fma_id", "province", "geometry"]], how="intersection",
                     keep_geom_type=True)
    ov["ha_all"] = ov.area / 1e4
    ov["ha_in_parks"] = ov.geometry.intersection(park_union).area / 1e4
    ov.to_file(cache, layer="ov", driver="GPKG")

mapped = attrs[["fma_id"]].copy()
mapped["mapped_ha"] = mapped.fma_id.map(ov.groupby("fma_id").ha_all.sum()).fillna(0)
mapped["mapped_ha_in_national_parks"] = mapped.fma_id.map(ov.groupby("fma_id").ha_in_parks.sum()).fillna(0)

total_mapped = m3.mapped_ha.sum()
in_canada = ov.ha_all.sum()
print(f"M3 total {total_mapped:,.0f} ha; inside province polygons {in_canada:,.0f}; outside {total_mapped - in_canada:,.0f}")

# province assignment of each fire (largest overlap) for the simplified fire layer
dom = ov.sort_values("ha_all", ascending=False).drop_duplicates("UID").set_index("UID").province
m3["province"] = m3.UID.map(dom).fillna("outside")

# ---------------------------------------------------------------- scaling factors
A = attrs.merge(mapped, on="fma_id")
pk_by_prov = A.groupby("province").mapped_ha_in_national_parks.sum()
pk_total = pk_by_prov.sum()
pc_alloc = PC_OFFICIAL * pk_by_prov / pk_total
prov_rows = []
for p, grp in A.groupby("province"):
    m_all = grp.mapped_ha.sum()
    m_pk = grp.mapped_ha_in_national_parks.sum()
    o_ag = off26.get(p, np.nan)
    o_pc = pc_alloc.get(p, 0.0)
    o = o_ag + o_pc if pd.notna(o_ag) else (o_pc if o_pc > 0 else np.nan)
    f = o / m_all if (m_all > 0 and pd.notna(o)) else np.nan
    prov_rows.append(dict(province=p, official_agency_2026_ha=o_ag, parks_canada_allocated_ha=o_pc,
                          official_2026_ha=o, m3_mapped_ha=m_all, m3_mapped_ha_in_national_parks=m_pk,
                          parks_canada_share_of_mapped_park_area=m_pk / pk_total if pk_total else np.nan,
                          scaling_factor=f,
                          factor_old_basis_agency_over_outside_parks=(o_ag / (m_all - m_pk)) if (m_all - m_pk) > 0 else np.nan,
                          n_areas=len(grp)))
F = pd.DataFrame(prov_rows)
fac = F.set_index("province").scaling_factor
off_tot = F.set_index("province").official_2026_ha
assert abs(F.parks_canada_allocated_ha.sum() - PC_OFFICIAL) < 0.01
n_rows = A.groupby("province").size()


def official_ha(r):
    o = off_tot.get(r.province, np.nan)
    if pd.isna(o):
        return np.nan                                  # NU: no official total
    if n_rows[r.province] == 1:
        return o                                       # whole-province row takes the official total
    return r.mapped_ha * fac[r.province]


A["official_scaled_ha_2026"] = A.apply(official_ha, axis=1)

# ---------------------------------------------------------------- raster: forest
m = meta()
fc = load("forest_count")
fid = load(FMA_GRID)
nf = int(A.fma_id.max()) + 1
tot_f = np.zeros(nf)
tot_land = np.zeros(nf)
asc = load("areal_scale_coarse", mmap=False).astype("float64")
for r0 in range(0, m["H"], 1000):
    r1 = min(r0 + 1000, m["H"])
    rows = np.arange(r0, r1)
    sc = asc[np.minimum(rows // m["step"], asc.shape[0] - 1)][:, np.minimum(np.arange(m["W"]) // m["step"], asc.shape[1] - 1)]
    fa = np.asarray(fc[r0:r1], dtype="float64") * 900.0 / sc
    ca = 57600.0 / sc
    f_ = np.asarray(fid[r0:r1]).ravel().astype("int64")
    tot_f += np.bincount(f_, weights=fa.ravel(), minlength=nf)
    tot_land += np.bincount(f_, weights=ca.ravel(), minlength=nf)
CAN_FOREST_HA = tot_f[1:].sum() / 1e4
print(f"Canada forest (inside StatCan provinces) {CAN_FOREST_HA:,.0f} ha")


def forest_w(idx):
    rc = np.unravel_index(idx, (m["H"], m["W"]))
    return np.asarray(fc[rc], dtype="float64") * 900.0 * cell_area_m2(idx) / 57600.0


B = {y: np.load(WORK / f"burn_{y}.npy") for y in YEARS_HIST + [2026]}
share = {}
for y, idx in B.items():
    rc = np.unravel_index(idx, (m["H"], m["W"]))
    share[y] = np.bincount(np.asarray(fid[rc]).astype("int64"), weights=forest_w(idx), minlength=nf)

ids = A.fma_id.values


def col(y, kind):
    bf = share[y][ids]
    if kind == "ha":
        return bf / 1e4
    with np.errstate(all="ignore"):
        return np.where(tot_f[ids] > 0, bf / tot_f[ids], np.nan)


A["forest_ha"] = tot_f[ids] / 1e4
A["forest_burned_mapped_ha_2026"] = col(2026, "ha")
A["forest_share_burned_2026"] = col(2026, "share")
hist = pd.DataFrame({y: col(y, "share") for y in YEARS_HIST}, index=A.fma_id)
hist.to_csv(OUT / "fma_forest_share_by_year_1972_2025.csv")
A["avg_share_1991_2020"] = hist.loc[:, 1991:2020].mean(axis=1).values
A["ratio_2026_vs_1991_2020"] = A.forest_share_burned_2026 / A.avg_share_1991_2020.replace(0, np.nan)
A["max_share_1972_2025"] = hist.max(axis=1).values
A["max_share_year_1972_2025"] = hist.fillna(-1).idxmax(axis=1).where(hist.max(axis=1) > 0).values
A["record_2026"] = (A.forest_share_burned_2026 > A.max_share_1972_2025) & (A.forest_share_burned_2026 > 0)
# scaled basis: 2026 share x province factor (M3 outlines are buffered hotspot outlines). Headline record basis.
A["scaling_factor"] = A.province.map(fac)
A["forest_share_2026_scaled_sensitivity"] = A.forest_share_burned_2026 * A.scaling_factor
A["record_2026_if_scaled"] = (A.forest_share_2026_scaled_sensitivity > A.max_share_1972_2025) & (A.forest_share_2026_scaled_sensitivity > 0)

# ---------------------------------------------------------------- reburns (analysis 4)
idx26 = B[2026]
last = np.zeros(len(idx26), dtype="int16")
for y in YEARS_HIST:
    hit = np.isin(idx26, B[y], assume_unique=True)
    last[hit] = y
since = np.where(last > 0, 2026 - last, -1)
cat = np.select([since < 0, since < 10, since <= 30], [0, 1, 2], 3).astype("uint8")
CATS = {0: "no burn 1972-2025", 1: "under 10 years (2017-2025)", 2: "10 to 30 years (1996-2016)", 3: "over 30 years (1972-1995)"}
ca26 = cell_area_m2(idx26)
rc26 = np.unravel_index(idx26, (m["H"], m["W"]))
f26 = np.asarray(fid[rc26]).astype("int64")
np.save(WORK / "reburn_cat_2026.npy", cat)

rb_rows = []
for r in A.itertuples():
    sel = f26 == r.fma_id
    tot = ca26[sel].sum()
    d = dict(fma_id=r.fma_id, province=r.province, area_name=r.area_name, footprint_cells_ha=tot / 1e4)
    for k, v in CATS.items():
        fr = ca26[sel & (cat == k)].sum() / tot if tot > 0 else np.nan
        d[f"share_{k}"] = fr
        d[f"official_scaled_ha_{k}"] = fr * r.official_scaled_ha_2026 if pd.notna(r.official_scaled_ha_2026) else np.nan
    rb_rows.append(d)
RB = pd.DataFrame(rb_rows)
RB.to_csv(OUT / "reburn_2026_by_fma.csv", index=False)
prv = []
pmap = attrs.set_index("fma_id").province
f26prov = pd.Series(f26).map(pmap).fillna("outside").values
groups = {p: (f26prov == p) for p in sorted(set(f26prov) - {"outside"})}
groups["Canada (all mapped, in provinces)"] = f26 > 0
for g, sel in groups.items():
    tot = ca26[sel].sum()
    d = dict(group=g, footprint_cells_ha=tot / 1e4)
    o = off26.sum() if g.startswith("Canada") else off_tot.get(g, np.nan)
    for k, v in CATS.items():
        fr = ca26[sel & (cat == k)].sum() / tot if tot > 0 else np.nan
        d[f"share_{k}"] = fr
        d[f"official_scaled_ha_{k}"] = fr * o if pd.notna(o) else np.nan
    d["official_2026_ha"] = o
    prv.append(d)
RBP = pd.DataFrame(prv)
RBP.to_csv(OUT / "reburn_2026_by_province.csv", index=False)
print(RBP.round(3).to_string())

# ---------------------------------------------------------------- Canada totals and cumulative (analysis 3)
can = {}
bf26 = share[2026][1:].sum()
can["canada_forest_ha"] = CAN_FOREST_HA
can["forest_burned_2026_mapped_ha"] = bf26 / 1e4
can["share_canada_forest_burned_2026"] = bf26 / 1e4 / CAN_FOREST_HA
yrs4 = [2023, 2024, 2025, 2026]
allidx = np.concatenate([B[y] for y in yrs4])
u, cnt = np.unique(allidx, return_counts=True)
rcu = np.unravel_index(u, (m["H"], m["W"]))
fu = np.asarray(fid[rcu]).astype("int64")
inprov = fu > 0
u, cnt, fu = u[inprov], cnt[inprov], fu[inprov]
wu = forest_w(u)
au = cell_area_m2(u)
can["union_2023_2026_forest_burned_ha"] = wu.sum() / 1e4
can["share_canada_forest_burned_2023_2026_union"] = wu.sum() / 1e4 / CAN_FOREST_HA
can["sum_of_annual_forest_burned_2023_2026_ha"] = sum(share[y][1:].sum() for y in yrs4) / 1e4
can["union_2023_2026_all_land_mapped_ha"] = au.sum() / 1e4
can["sum_annual_mapped_cells_ha_2023_2026"] = sum(cell_area_m2(B[y])[np.asarray(fid[np.unravel_index(B[y], (m['H'], m['W']))]) > 0].sum() for y in yrs4) / 1e4
can["twice_or_more_2023_2026_mapped_ha"] = au[cnt >= 2].sum() / 1e4
can["twice_or_more_share_of_union"] = au[cnt >= 2].sum() / au.sum()
can["twice_or_more_forest_ha"] = wu[cnt >= 2].sum() / 1e4
nfd = off[(off.year >= 2023) & (off.year <= 2025)].groupby("year").area_burned_ha.sum()
can["official_sum_2023_2026_ha"] = nfd.sum() + off26.sum()
can["official_scaled_union_2023_2026_ha"] = can["official_sum_2023_2026_ha"] * can["union_2023_2026_all_land_mapped_ha"] / can["sum_annual_mapped_cells_ha_2023_2026"]
for y in yrs4:
    can[f"forest_burned_{y}_mapped_ha"] = share[y][1:].sum() / 1e4
    can[f"share_canada_forest_burned_{y}"] = share[y][1:].sum() / 1e4 / CAN_FOREST_HA
nat = pd.Series({y: share[y][1:].sum() / 1e4 / CAN_FOREST_HA for y in YEARS_HIST + [2026]})
nat.to_csv(OUT / "canada_forest_share_by_year.csv", header=["share_forest_burned"])
can["rank_2026_share_1972_2026"] = int((nat > nat[2026]).sum() + 1)
can["avg_share_1991_2020"] = nat.loc[1991:2020].mean()
nat_factor = off26.sum() / in_canada
can["national_official_to_mapped_ratio_2026"] = nat_factor
can["share_canada_forest_burned_2026_scaled"] = nat[2026] * nat_factor
can["rank_2026_share_scaled_1972_2026"] = int((nat.drop(2026) > nat[2026] * nat_factor).sum() + 1)
pu = pd.Series(fu).map(pmap).values
tw = pd.DataFrame({"prov": pu, "a": au, "two": cnt >= 2})
twp = tw.groupby("prov").apply(lambda d: pd.Series({"union_mapped_ha": d.a.sum() / 1e4,
                                                    "twice_or_more_mapped_ha": d.a[d.two].sum() / 1e4,
                                                    "share": d.a[d.two].sum() / d.a.sum()}))
twp.to_csv(OUT / "burned_twice_2023_2026_by_province.csv")
print(twp.round(3).to_string())
pd.Series(can).to_csv(OUT / "canada_totals.csv", header=["value"])
print(pd.Series(can).to_string())

# per-province forest share 2026 (whole province, national parks included)
pf = []
for p, grp in A.groupby("province"):
    pid = grp.fma_id.values
    tf = tot_f[pid].sum()
    s26 = share[2026][pid].sum() / tf if tf > 0 else np.nan
    pf.append(dict(province=p, forest_ha=tf / 1e4, forest_burned_mapped_ha_2026=share[2026][pid].sum() / 1e4,
                   share_2026=s26, share_2026_scaled=s26 * fac.get(p, np.nan),
                   avg_share_1991_2020=np.mean([share[y][pid].sum() / tf for y in range(1991, 2021)]) if tf > 0 else np.nan,
                   max_share_1972_2025=max(share[y][pid].sum() / tf for y in YEARS_HIST) if tf > 0 else np.nan))
PF = pd.DataFrame(pf)
PF["record_2026"] = PF.share_2026 > PF.max_share_1972_2025
PF["record_2026_if_scaled"] = PF.share_2026_scaled > PF.max_share_1972_2025
PF.to_csv(OUT / "province_forest_share_2026.csv", index=False)
print(PF.round(4).to_string())

# ---------------------------------------------------------------- save main table
keep = ["fma_id", "province", "agency", "area_name", "area_level", "boundary_status", "area_km2_equal_area",
        "mapped_ha", "mapped_ha_in_national_parks", "scaling_factor", "official_scaled_ha_2026", "forest_ha",
        "forest_burned_mapped_ha_2026", "forest_share_burned_2026", "avg_share_1991_2020", "ratio_2026_vs_1991_2020",
        "max_share_1972_2025", "max_share_year_1972_2025", "record_2026", "forest_share_2026_scaled_sensitivity",
        "record_2026_if_scaled"]
A[keep].to_csv(OUT / "fma_2026_table.csv", index=False)
F.to_csv(OUT / "scaling_factors_by_province.csv", index=False)
print(F.round(4).to_string())
chk = A.official_scaled_ha_2026.sum()
print(f"sum official-scaled ha {chk:,.1f} vs official {off26.sum():,.1f}")
rec = A[A.record_2026 | A.record_2026_if_scaled][["fma_id", "province", "area_name", "forest_share_burned_2026",
                                                  "forest_share_2026_scaled_sensitivity", "max_share_1972_2025",
                                                  "max_share_year_1972_2025", "record_2026", "record_2026_if_scaled"]]
print(rec.sort_values("forest_share_burned_2026", ascending=False).round(4).to_string())

# geometry outputs for the site
cls = gpd.read_file(OUTLINE_CLASS, columns=["fire_uid", "class"], ignore_geometry=True)
m3_out = m3[["UID", "CONSIS_ID", "FIRSTDATE", "LASTDATE", "HCOUNT", "AREA", "province", "mapped_ha", "geometry"]].copy()
m3_out["official_scaled_ha"] = m3_out.mapped_ha * m3_out.province.map(fac)
m3_out["outline_class"] = m3_out.UID.map(dict(zip(cls.fire_uid, cls["class"])))
assert m3_out.outline_class.notna().all()
m3_out["geometry"] = m3_out.geometry.simplify(100, preserve_topology=True)
m3_out.to_crs("EPSG:4326").to_file(OUT / "fires_2026_simplified.geojson", driver="GeoJSON", COORDINATE_PRECISION=5)
# fma_2026.geojson is written by 08_fma_geojson.py (part-by-part simplification is much faster)
