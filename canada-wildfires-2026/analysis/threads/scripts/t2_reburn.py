"""Thread 2: short-interval reburns, 1987-2026, on the 240 m grid of analysis/forest.

Burn record: NBAC 1972-2025 (all polygons incl. prescribed; cell-centre rule) + CWFIS M3 2026 outlines
(analysis/forest/work/burn_<y>.npy). For each burn year Y and window k (5, 10, 15, 20 years), a cell burned in Y is a
'reburn within k' when it also burned in any year Y-k..Y-1 (time since its most recent previous burn <= k).
Windows are only computed when Y-k >= 1972.

Conifer restriction (two definitions):
  LC: Land Cover of Canada 2020 needleleaf (classes 1, 2) >= 50% of the 64 30 m pixels of the cell
      (work/lc2020_needleleaf_count_240m.tif). Static 2020 map: post-fire for burns before 2020.
  SCANFI: SCANFI v2 black spruce + jack pine crown closure >= 50% of total crown closure and total closure >= 10%,
      read from the map epoch at or before the start of the window (epoch = max(1985, floor((Y-k)/5)*5)), i.e. the
      stand before the earlier fire in most cases. Source: the 1/16 overview (.ovr, 480 m, decimated sample) of the
      30 m rasters; each 240 m cell takes the overview pixel containing its centre.
Outputs: t2_reburn_national_by_year.csv, t2_reburn_by_period.csv, t2_reburn_2023_2026_by_province.csv,
         t2_reburn_2023_2026_by_fma.csv
"""
import json
import numpy as np, pandas as pd, rasterio, rasterio.windows
from affine import Affine
from pyproj import Transformer

BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
T = f"{BASE}/analysis/threads"
FW = f"{BASE}/analysis/forest/work"
m = json.load(open(f"{FW}/grid_meta.json")); TR = Affine(*m["transform"]); H, W = m["H"], m["W"]
asc = np.load(f"{FW}/areal_scale_coarse.npy")
def cell_ha(idx):
    r = np.minimum((idx // W) // m["step"], asc.shape[0] - 1); c = np.minimum((idx % W) // m["step"], asc.shape[1] - 1)
    return 57600.0 / asc[r, c].astype("float64") / 1e4

YEARS = list(range(1972, 2027))
burn = {y: np.load(f"{FW}/burn_{y}.npy").astype(np.int64) for y in YEARS}
U = np.unique(np.concatenate(list(burn.values())))
print("cells ever burned", len(U), flush=True)
ha = cell_ha(U)
# province and FMA
fma = np.load(f"{FW}/fma_v2_id.npy", mmap_mode="r").ravel()
fma_u = np.asarray(fma[U]).astype(np.int32)
att = pd.read_csv(f"{BASE}/data/geo/fma_v2_attributes.csv")
prov_of = dict(zip(att.fma_id, att.province)); name_of = dict(zip(att.fma_id, att.area_name))
lut = np.array(["NA"] * (max(int(fma_u.max()), int(att.fma_id.max())) + 1), dtype="<U2")
for i, pv in prov_of.items():
    lut[int(i)] = pv
prov_u = lut[fma_u]
# LC needleleaf
with rasterio.open(f"{T}/work/lc2020_needleleaf_count_240m.tif") as s:
    assert s.width == W and s.height == H
    nl_u = np.full(len(U), 255, np.uint8)
    rowsU = U // W
    for r0 in range(0, H, 1000):
        h = min(1000, H - r0)
        blk = s.read(1, window=rasterio.windows.Window(0, r0, W, h)).ravel()
        sel = (rowsU >= r0) & (rowsU < r0 + h)
        nl_u[sel] = blk[U[sel] - r0 * W]
    del blk, rowsU
lc_conifer = (nl_u != 255) & (nl_u >= 32)
# SCANFI epochs
rr, cc = U // W, U % W
xs, ys = TR * (cc + 0.5, rr + 0.5)
t = Transformer.from_crs("EPSG:3979", "+proj=lcc +lat_0=0 +lon_0=-95 +lat_1=49 +lat_2=77 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs", always_xy=True)
sx, sy = t.transform(np.asarray(xs), np.asarray(ys))
orow = np.floor((9436500.0 - sy) / 480.0).astype(np.int64); ocol = np.floor((sx + 2341500.0) / 480.0).astype(np.int64)
del xs, ys, sx, sy
EPOCHS = [1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020]
sc = {}
for e in EPOCHS:
    arr = {}
    for l in ["spsCC_blackSpruce", "spsCC_jackPine", "att_closure"]:
        with rasterio.open(f"{T}/raw/scanfi_ovr/SCANFI_{l}_{e}_v2_20260119.tif.ovr") as s:
            a = s.read(1)
        ok = (orow >= 0) & (orow < a.shape[0]) & (ocol >= 0) & (ocol < a.shape[1])
        v = np.full(len(U), 255, np.uint8); v[ok] = a[orow[ok], ocol[ok]]
        arr[l] = v.astype(np.int16); del a
    bad = (arr["att_closure"] == 255) | (arr["spsCC_blackSpruce"] == 255) | (arr["spsCC_jackPine"] == 255)
    bsjp = arr["spsCC_blackSpruce"] + arr["spsCC_jackPine"]
    sc[e] = (~bad) & (arr["att_closure"] >= 10) & (2 * bsjp >= arr["att_closure"])
    print("epoch", e, "share of ever-burned cells BS/JP-leading", round(sc[e].mean(), 3), flush=True)

pos = {y: np.searchsorted(U, burn[y]) for y in YEARS}
last = np.zeros(len(U), np.int16)
rows = []   # national per year
cellrows = []  # 2023-2026 cell-level detail for province/FMA tables
K = [5, 10, 15, 20]
for y in YEARS:
    p = pos[y]
    tsl = np.where(last[p] > 0, y - last[p], 9999)
    if y >= 1987:
        for k in K:
            if y - k < 1972:
                continue
            e = max(1985, (y - k) // 5 * 5); e = min(e, 2020)
            re = tsl <= k
            for basis, mask in [("all", np.ones(len(p), bool)), ("LC2020 needleleaf", lc_conifer[p]), (f"SCANFI BS/JP (epoch {e})", sc[e][p])]:
                rows.append(dict(year=y, k=k, basis=basis.split(" (")[0], epoch=e if basis.startswith("SCANFI") else None,
                                 burned_ha=ha[p][mask].sum(), reburn_ha=ha[p][mask & re].sum()))
        if y >= 2023:
            d = pd.DataFrame({"u": p, "year": y, "tsl": tsl})
            cellrows.append(d)
    last[p] = y
R = pd.DataFrame(rows)
R["reburn_share"] = R.reburn_ha / R.burned_ha
R.to_csv(f"{T}/t2_reburn_national_by_year.csv", index=False)
# periods
def period(y):
    if y < 1990: return "1987-1989"
    if y < 2000: return "1990-1999"
    if y < 2010: return "2000-2009"
    if y < 2020: return "2010-2019"
    if y < 2023: return "2020-2022"
    return "2023-2026"
R["period"] = R.year.map(period)
P = R.groupby(["period", "k", "basis"]).agg(years=("year", "nunique"), burned_ha=("burned_ha", "sum"), reburn_ha=("reburn_ha", "sum")).reset_index()
P["reburn_share"] = P.reburn_ha / P.burned_ha
P["reburn_ha_per_year"] = P.reburn_ha / P.years
P.to_csv(f"{T}/t2_reburn_by_period.csv", index=False)
print(P[P.k == 15].to_string(), flush=True)
print(P[P.basis == "SCANFI BS/JP"].pivot_table(index="period", columns="k", values="reburn_share").to_string())

# 2023-2026 by province and FMA (SCANFI epoch per k as above, using the epoch of each row's year)
C = pd.concat(cellrows, ignore_index=True)
C["ha"] = ha[C.u.values]; C["prov"] = prov_u[C.u.values]; C["fma"] = fma_u[C.u.values]; C["lc"] = lc_conifer[C.u.values]
out_p, out_f = [], []
for k in K:
    C["re"] = C.tsl <= k
    scm = np.zeros(len(C), bool)
    for yy in (2023, 2024, 2025, 2026):
        e = min(2020, max(1985, (yy - k) // 5 * 5)); sel = C.year.values == yy
        scm[sel] = sc[e][C.u.values[sel]]
    C["sc"] = scm
    for basis, col in [("all", None), ("LC2020 needleleaf", "lc"), ("SCANFI BS/JP", "sc")]:
        sub = C if col is None else C[C[col]]
        for key, grp, out in [("prov", ["prov"], out_p), ("fma", ["prov", "fma"], out_f)]:
            g = sub.groupby(grp + ["year"]).apply(lambda s: pd.Series({"burned_ha": s.ha.sum(), "reburn_ha": s.ha[s.re].sum()}), include_groups=False).reset_index()
            g2 = sub.groupby(grp).apply(lambda s: pd.Series({"burned_ha": s.ha.sum(), "reburn_ha": s.ha[s.re].sum()}), include_groups=False).reset_index()
            g2["year"] = "2023-2026 (sum of years)"
            g = pd.concat([g, g2]); g["k"] = k; g["basis"] = basis
            out.append(g)
PP = pd.concat(out_p); PP["reburn_share"] = PP.reburn_ha / PP.burned_ha
FF = pd.concat(out_f); FF["reburn_share"] = FF.reburn_ha / FF.burned_ha; FF["area_name"] = FF.fma.map(name_of)
PP.to_csv(f"{T}/t2_reburn_2023_2026_by_province.csv", index=False)
FF.to_csv(f"{T}/t2_reburn_2023_2026_by_fma.csv", index=False)
x = PP[(PP.k == 15) & (PP.year == "2023-2026 (sum of years)")].pivot_table(index="prov", columns="basis", values=["reburn_ha", "reburn_share"])
print(x.to_string())
y15 = FF[(FF.k == 15) & (FF.year == "2023-2026 (sum of years)") & (FF.basis == "all")].sort_values("reburn_ha", ascending=False).head(20)
print(y15.to_string())
