"""Priority 3: agency report date vs first satellite hotspot.

2023-2025: NBAC polygons carry both HS_SDATE (first hotspot date, CWFIS) and AG_SDATE (agency start/report date
from the agency fire record). Lag = AG_SDATE - HS_SDATE in whole days. Positive = the agency date is later than the
first hotspot.
2026: each CWFIS M3 outline (farm/grass/military without agency fire dropped) is matched to the agency fire-list points
inside it; agency date = earliest report date (NT: GNWT discovery date) among them. Lag = agency date - M3 FIRSTDATE,
in hours, rounded down to days for the bins.
Outputs: detection_lag_fires.csv, detection_lag_summary.csv
"""
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

from common import NBAC_SHP, M3_2026, OUTLINE_CLASS, OUT, WORK

BINS = [-1e9, -2, -1, 0, 1, 2, 3, 7, 1e9]
LAB = ["<=-2 d", "-1 d", "same day", "+1 d", "+2 d", "+3 to +6 d", ">=+7 d"]


def binlag(d):
    d = np.floor(d)
    out = pd.Series(pd.NA, index=d.index, dtype=object)
    out[d <= -2] = "<=-2 d"; out[d == -1] = "-1 d"; out[d == 0] = "same day"; out[d == 1] = "+1 d"
    out[d == 2] = "+2 d"; out[(d >= 3) & (d <= 6)] = "+3 to +6 d"; out[d >= 7] = ">=+7 d"
    return out


nb = pyogrio.read_dataframe(NBAC_SHP, read_geometry=False, where="YEAR >= 2023",
                            columns=["YEAR", "NFIREID", "HS_SDATE", "AG_SDATE", "ADJ_HA", "ADMIN_NAME", "PRESCRIBED"])
nb = nb[nb.PRESCRIBED.isna()]
nb["lag_d"] = (pd.to_datetime(nb.AG_SDATE) - pd.to_datetime(nb.HS_SDATE)).dt.days
A = pd.DataFrame(dict(source="NBAC", year=nb.YEAR.astype(int), prov=nb.ADMIN_NAME, area_ha=nb.ADJ_HA,
                      lag_d=nb.lag_d.astype(float), has_both=nb.lag_d.notna()))

per = gpd.read_file(M3_2026)
cls = gpd.read_file(OUTLINE_CLASS)[["fire_uid", "class", "agency_match"]]
per = per.merge(cls, left_on="UID", right_on="fire_uid", how="left")
per = per[~(per["class"].isin(["likely agricultural or grass burn", "military range"]) & ~per.agency_match.astype(bool))]
F = pd.read_pickle(WORK / "fires.pkl")
f26 = F[(F.year == 2026) & F.rep_date.notna()]
pts = gpd.GeoDataFrame(f26[["fire_id", "rep_date"]], geometry=gpd.points_from_xy(f26.lon, f26.lat), crs=4326).to_crs(per.crs)
j = gpd.sjoin(pts, per[["UID", "geometry"]], predicate="within")
ag = j.groupby("UID").rep_date.min()
per["agency_date"] = per.UID.map(ag)
per["lag_h"] = (per.agency_date - pd.to_datetime(per.FIRSTDATE)).dt.total_seconds() / 3600
B = pd.DataFrame(dict(source="M3+agency list", year=2026, prov=per.prov, area_ha=per.area_ha_albers,
                      lag_d=per.lag_h / 24, has_both=per.lag_h.notna()))
X = pd.concat([A, B], ignore_index=True)
X["bin"] = binlag(X.lag_d)
X.to_csv(OUT / "detection_lag_fires.csv", index=False, float_format="%.3f")

rows = []
for (src, y), d in list(X.groupby(["source", "year"])) + [(("all", "2023-2026"), X)]:
    for prov, e in [("Canada", d)] + list(d.groupby("prov")):
        k = e[e.has_both]
        if len(k) == 0:
            continue
        r = dict(source=src, year=y, prov=prov, polygons=len(e), with_both_dates=len(k),
                 area_with_both_share=k.area_ha.sum() / e.area_ha.sum(),
                 median_lag_d=float(np.median(np.floor(k.lag_d))),
                 area_weighted_median_lag_d=float(np.floor(k.sort_values("lag_d").lag_d.values[
                     np.searchsorted(k.sort_values("lag_d").area_ha.cumsum().values, k.area_ha.sum() / 2)])))
        for b in LAB:
            r[f"fires_{b}"] = (k.bin == b).mean()
            r[f"area_{b}"] = k.loc[k.bin == b, "area_ha"].sum() / k.area_ha.sum()
        r["area_agency_1d_or_more_after"] = k.loc[np.floor(k.lag_d) >= 1, "area_ha"].sum() / k.area_ha.sum()
        r["area_agency_3d_or_more_after"] = k.loc[np.floor(k.lag_d) >= 3, "area_ha"].sum() / k.area_ha.sum()
        rows.append(r)
S = pd.DataFrame(rows)
S.to_csv(OUT / "detection_lag_summary.csv", index=False, float_format="%.4f")
print(S[S.prov == "Canada"].T.to_string())
