"""Priority 4: distance from each fire's origin to the nearest road (StatCan NRN, all road classes incl. resource and
winter roads; a no-winter-road version is also kept).

Origin = agency fire point (CNFDB 2023-2025, 2026 agency list). Area = agency size, scaled so each province-year sums
to the official total (share of agency hectares x official). 2026 alternative origin = first hotspot inside each M3
outline (escape_speed_2026_fires.csv), area = outline area.
Outputs: access_by_prov_year.csv, access_by_response.csv, access_m3_2026.csv
"""
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

from common import OUT, SEASON, WORK

F = pd.read_pickle(WORK / "fires.pkl")
F = F[F.year.between(2023, 2026)].copy()
n = pd.read_csv(SEASON / "NFD_-_Area_burned_by_month_-_EN_FR.csv")
off = n[n.Year.between(2023, 2025)].groupby(["ISO", "Year"])["Area (hectares)"].sum()
off.index.names = ["prov", "year"]
o26 = F[F.year == 2026].groupby("prov").size_ha.sum()
off = pd.concat([off, pd.concat({2026: o26}, names=["year", "prov"]).swaplevel()]).sort_index()
pt = F.groupby(["prov", "year"]).size_ha.transform("sum")
F["w_ha"] = F.size_ha / pt * pd.Series(list(zip(F.prov, F.year))).map(off).values
BANDS = [0, 10, 25, 50, 1e9]
BL = ["0-10 km", "10-25 km", "25-50 km", ">50 km"]
F["band"] = pd.cut(F.road_km, BANDS, labels=BL, right=False)

rows = []
for col in ["road_km", "road_km_no_winter"]:
    for (y, prov), d in (list(F.groupby(["year", "prov"])) + [((y, "Canada"), d) for y, d in F.groupby("year")]
                         + [(("2023-2026", "Canada"), F)] + [(("2023-2026", p), d) for p, d in F.groupby("prov")]):
        t = d.w_ha.sum()
        if t <= 0:
            continue
        r = dict(distance=col, year=y, prov=prov, fires=len(d), official_ha=t,
                 median_km_fires=float(d[col].median()))
        for k in [10, 25, 50]:
            r[f"share_area_gt_{k}km"] = d.loc[d[col] > k, "w_ha"].sum() / t
            r[f"share_fires_gt_{k}km"] = (d[col] > k).mean()
        rows.append(r)
A = pd.DataFrame(rows)
A.to_csv(OUT / "access_by_prov_year.csv", index=False, float_format="%.4f")
print(A[(A.prov == "Canada") & (A.distance == "road_km")].T.to_string())

R = F.pivot_table(index=["band"], columns="resp", values="w_ha", aggfunc="sum", fill_value=0, observed=False)
R["total"] = R.sum(1)
R.to_csv(OUT / "access_by_response.csv", float_format="%.0f")
print(R)

# 2026 alternative origin: first hotspot of each M3 outline
E = pd.read_csv(OUT / "escape_speed_2026_fires.csv")
E = E[E.first_x_3978.notna()]
tr = Transformer.from_crs("EPSG:3978", "ESRI:102001", always_xy=True)
x, y = tr.transform(E.first_x_3978.values, E.first_y_3978.values)
xs, ys = [], []
for p in ["pe", "ns", "nb", "nl", "yt", "nt", "nu", "mb", "sk", "ab", "qc", "bc", "on"]:
    z = np.load(WORK / f"roadpts_{p}.npz", allow_pickle=True)
    xs.append(z["x"]); ys.append(z["y"])
t = cKDTree(np.c_[np.concatenate(xs).astype(float), np.concatenate(ys).astype(float)])
E["road_km_first_hotspot"] = t.query(np.c_[x, y])[0] / 1000
rows = []
for prov, d in [("Canada", E)] + list(E.groupby("prov")):
    tt = d.area_ha_albers.sum()
    r = dict(prov=prov, outlines=len(d), mapped_ha=tt)
    for k in [10, 25, 50]:
        r[f"share_area_gt_{k}km"] = d.loc[d.road_km_first_hotspot > k, "area_ha_albers"].sum() / tt
    rows.append(r)
M = pd.DataFrame(rows)
M.to_csv(OUT / "access_m3_2026.csv", index=False, float_format="%.4f")
print(M.to_string())
