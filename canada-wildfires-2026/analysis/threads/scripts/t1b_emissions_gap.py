"""Thread 1b: wildfire CO2 outside Canada's national GHG total, 2016-2026.

Official numbers (ECCC NIR 2026, raw tables in analysis/economy/raw/ghg/):
  - national total excluding LULUCF: A-IPCC-Sector CSV, Region Canada, CategoryID 0 (checked = sum of sectors
    other than LULUCF);
  - LULUCF total and Forest Land: same CSV, CategoryID 700 and 710;
  - managed-forest wildfire direct immediate emissions (CO2, CH4, N2O) and natural-disturbance net line, managed
    forest area: EN_Ch6_Tables Table 6-5 and Table 6-1 (values rounded to 2 significant figures in the source).
Our estimate: per-cell aboveground CO2 from analysis/economy (07b method, low/high, mapped and scaled), split by
the managed / unmanaged forest map georeferenced in t1a (NRCan image of the GHG managed forest, ~9.6 km pixels).
Pixels that are not forest-coloured on the image take the class of the nearest forest-coloured pixel.
Outputs: t1_official_inventory_lines.csv, t1_wildfire_co2_managed_split_by_year.csv,
         t1_managed_forest_area_check.csv
"""
import json
import numpy as np, pandas as pd, openpyxl
from scipy import ndimage
from affine import Affine

BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
T = f"{BASE}/analysis/threads"
E = f"{BASE}/analysis/economy"
FW = f"{BASE}/analysis/forest/work"

# ---------- official lines
d = pd.read_csv(f"{E}/raw/ghg/A-IPCC-Sector_GHG_IPCC_Can_Prov_Terr.csv", encoding="latin1", low_memory=False)
c = d[d.Region == "Canada"].copy()
for col in ["CO2", "CO2eq"]:
    c[col] = pd.to_numeric(c[col], errors="coerce")
tot = c[c.CategoryID == 0].set_index("Year").CO2eq
leaf = c[c.Total.isna() & (c.Source != "Land Use, Land-Use Change and Forestry") & (c.Source != "Total")].groupby("Year").CO2eq.sum()
lulucf = c[c.CategoryID == 700].set_index("Year").CO2eq
forest = c[c.CategoryID == 710].set_index("Year").CO2eq
wb = openpyxl.load_workbook(f"{E}/raw/ghg/E-LULUCF_EN_Ch6_Tables_FullTimeSeries.xlsx", read_only=True, data_only=True)
rows65 = [list(r) for r in wb["Table 6–5 All Years"].iter_rows(values_only=True)]
hdr = rows65[2]; ycol = {int(v): i for i, v in enumerate(hdr) if isinstance(v, str) and v.isdigit()}
def row65(label, gas=None, start=3):
    for i in range(start, len(rows65)):
        r = rows65[i]
        if any(isinstance(x, str) and x.strip().startswith(label) for x in r[:3]):
            if gas is None:
                return r
            for j in range(i, i + 5):
                if rows65[j][3] == gas:
                    return rows65[j]
    raise KeyError(label)
r_area = row65("Total managed forest area")
r_wf = row65("Wildfires – direct immediate")
r_wf_co2 = row65("Wildfires – direct immediate", "CO2")
r_ind = row65("Wildfires – indirect immediate")
r_post = row65("Post-wildfire")
r_nd = row65("Emissions/removals from lands impacted")
rows61 = [list(r) for r in wb["Table 6–1 All Years"].iter_rows(values_only=True)]
hdr61 = [r for r in rows61 if sum(isinstance(v, (int, float)) and 1989 < v < 2030 for v in r) > 10][0]
y61 = {int(v): i for i, v in enumerate(hdr61) if isinstance(v, (int, float)) and 1989 < v < 2030}
r_nd61 = [r for r in rows61 if any(isinstance(x, str) and x.strip().startswith("Natural disturbances") for x in r[:3])][0]
off = []
for y in range(2016, 2025):
    off.append(dict(year=y, national_total_excl_lulucf_kt=tot[y], check_sum_sectors_kt=leaf[y], lulucf_total_kt=lulucf[y],
                    forest_land_kt=forest[y], managed_forest_area_kha=r_area[ycol[y]],
                    nir_wildfire_direct_immediate_kt_co2e=r_wf[ycol[y]], nir_wildfire_direct_immediate_kt_co2=r_wf_co2[ycol[y]],
                    nir_wildfire_indirect_co2_kt=r_ind[ycol[y]], nir_post_wildfire_co2_kt=r_post[ycol[y]],
                    nir_natural_disturbance_net_kt=r_nd[ycol[y]], nir_natural_disturbance_line_table61_kt=r_nd61[y61[y]]))
O = pd.DataFrame(off)
O["wildfire_direct_as_share_of_national"] = O.nir_wildfire_direct_immediate_kt_co2e / O.national_total_excl_lulucf_kt
O.to_csv(f"{T}/t1_official_inventory_lines.csv", index=False)
print(O.to_string(), flush=True)

# ---------- managed map
cls = np.load(f"{T}/work/mf_class_img.npy")
A = json.load(open(f"{T}/work/mf_affine.json"))
forestpx = np.isin(cls, [1, 2])
_, (ir, ic) = ndimage.distance_transform_edt(~forestpx, return_indices=True)
cls_filled = cls[ir, ic]          # 1 managed, 2 unmanaged everywhere
gm = json.load(open(f"{FW}/grid_meta.json")); TR = Affine(*gm["transform"]); W = gm["W"]
def managed_of_idx(idx):
    x, y = TR * ((idx % W) + 0.5, (idx // W) + 0.5)
    col = np.floor((np.asarray(x) - A["tx"]) / A["sx"]).astype(int); row = np.floor((A["ty"] - np.asarray(y)) / A["sy"]).astype(int)
    ok = (row >= 0) & (row < cls.shape[0]) & (col >= 0) & (col < cls.shape[1])
    out = np.full(len(idx), 2, np.int8)
    out[ok] = cls_filled[row[ok], col[ok]]
    direct = np.zeros(len(idx), bool); direct[ok] = forestpx[row[ok], col[ok]]
    return out == 1, direct

# area check: LC2020 forest inside managed class, every 4th cell
fc = np.load(f"{FW}/forest_count.npy", mmap_mode="r")
sub = np.asarray(fc[::4, ::4])
rr, cc2 = np.nonzero((sub > 0) & (sub != 255))
idx = (rr * 4).astype(np.int64) * W + cc2 * 4
fha = sub[rr, cc2].astype(float) * 0.09 * 16          # 30 m pixel = 0.09 ha; 4x4 cells per sample
asc = np.load(f"{FW}/areal_scale_coarse.npy")
def areal(idx):
    r = np.minimum((idx // W) // gm["step"], asc.shape[0] - 1); cl = np.minimum((idx % W) // gm["step"], asc.shape[1] - 1)
    return 1.0 / asc[r, cl].astype("float64")
fha = fha * areal(idx)
man, _ = managed_of_idx(idx)
chk = pd.DataFrame([dict(forest_lc2020_Mha=fha.sum() / 1e6, managed_forest_lc2020_Mha=fha[man].sum() / 1e6,
                         unmanaged_forest_lc2020_Mha=fha[~man].sum() / 1e6, managed_share=fha[man].sum() / fha.sum(),
                         nir_managed_forest_area_Mha_rounded=r_area[ycol[2024]] / 1000)])
chk.to_csv(f"{T}/t1_managed_forest_area_check.csv", index=False)
print(chk.to_string(), flush=True)

# ---------- per-cell CO2 split (07b method)
W_ = f"{E}/work"
c26 = pd.read_pickle(f"{W_}/cells.pkl"); c16 = pd.read_pickle(f"{W_}/cells_1622.pkl")
c26["bio2020"] = np.load(f"{W_}/scanfi_bio2020.npz")["bio_t"]; c26["bio2025"] = np.load(f"{W_}/scanfi_bio2025.npz")["bio_t"]
c16["bio2015"] = np.load(f"{W_}/scanfi_bio2015_1622.npz")["bio_t"]; c16["bio2020"] = np.load(f"{W_}/scanfi_bio2020_1622.npz")["bio_t"]
for df, f in [(c26, "knn2011.npz"), (c16, "knn2011_cells_1622.npz")]:
    k = np.load(f"{W_}/{f}")
    for v in ["agb_live", "bio_foliage", "bio_branch", "bio_stembark"]:
        df[v] = k[v + "_per_ha"].astype("float64") * df.area_ha.values
    df["managed"], df["on_coloured_px"] = managed_of_idx(df.idx.values.astype(np.int64))
sf = pd.read_csv(f"{W_}/scale_factors_2016_2025.csv"); fac = {(r.year, r.prov): r.factor for r in sf.itertuples()}
rows = []
for y in range(2016, 2027):
    src = c16 if y < 2023 else c26
    dd = src[src[f"b{y}"]].copy()
    dd["bio"] = dd.bio2015 if y <= 2020 else (dd.bio2020 if y <= 2025 else dd.bio2025)
    if y == 2026:
        dd["w"] = dd.w26
    else:
        dd["w"] = [1.0 if pk > 0 else fac.get((y, p), np.nan) for p, pk in zip(dd.prov, dd.park_id)]
        dd["w"] = dd.w.fillna(1.0)
    acc = {k: 0.0 for k in ["low", "high", "low_s", "high_s", "low_m", "high_m", "low_s_m", "high_s_m", "area", "area_m", "area_s", "area_s_m"]}
    for p, g in dd.groupby("prov"):
        fol = g.bio_foliage.sum() / g.agb_live.sum(); nst = (g.bio_foliage.sum() + g.bio_branch.sum() + g.bio_stembark.sum()) / g.agb_live.sum()
        k = 0.5 * 44 / 12
        mm = g.managed.values
        for tag, wv in [("", np.ones(len(g))), ("_s", g.w.values)]:
            b = g.bio.values * wv
            acc["low" + tag] += b.sum() * fol * k; acc["high" + tag] += b.sum() * nst * k
            acc["low" + tag + "_m"] += b[mm].sum() * fol * k; acc["high" + tag + "_m"] += b[mm].sum() * nst * k
        acc["area"] += g.area_ha.sum(); acc["area_m"] += g.area_ha[mm].sum()
        acc["area_s"] += (g.area_ha * g.w).sum(); acc["area_s_m"] += (g.area_ha * g.w)[mm].sum()
    ey = min(y, 2024)
    r = dict(year=y, inventory_year_compared=ey, national_total_excl_lulucf_t=tot[ey] * 1000,
             area_mapped_ha=acc["area"], area_mapped_managed_ha=acc["area_m"], area_scaled_ha=acc["area_s"], area_scaled_managed_ha=acc["area_s_m"],
             share_area_managed=acc["area_m"] / acc["area"],
             co2_low_scaled_t=acc["low_s"], co2_high_scaled_t=acc["high_s"],
             co2_low_scaled_managed_t=acc["low_s_m"], co2_high_scaled_managed_t=acc["high_s_m"],
             co2_low_scaled_unmanaged_t=acc["low_s"] - acc["low_s_m"], co2_high_scaled_unmanaged_t=acc["high_s"] - acc["high_s_m"],
             co2_low_mapped_t=acc["low"], co2_high_mapped_t=acc["high"],
             share_co2_managed=acc["low_s_m"] / acc["low_s"] if acc["low_s"] else np.nan)
    if y <= 2024:
        rr_ = O.set_index("year").loc[y]
        r["nir_managed_wildfire_direct_t_co2e"] = rr_.nir_wildfire_direct_immediate_kt_co2e * 1000
        r["nir_managed_wildfire_direct_t_co2"] = rr_.nir_wildfire_direct_immediate_kt_co2 * 1000
    for lvl in ["low", "high"]:
        r[f"all_wildfire_co2_{lvl}_share_of_national"] = r[f"co2_{lvl}_scaled_t"] / r["national_total_excl_lulucf_t"]
        r[f"unmanaged_co2_{lvl}_share_of_national"] = r[f"co2_{lvl}_scaled_unmanaged_t"] / r["national_total_excl_lulucf_t"]
    rows.append(r)
R = pd.DataFrame(rows)
R.to_csv(f"{T}/t1_wildfire_co2_managed_split_by_year.csv", index=False)
pd.set_option("display.width", 250)
print(R.to_string())
