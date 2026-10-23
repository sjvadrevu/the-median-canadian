"""Priority 2: how fast 2026 fires grew after first satellite detection, and how concentrated area is in the largest fires.

Fires: the 718 CWFIS M3 2026 outlines (final, 2026-10-20). The 13 farm/grass/military outlines with no agency fire
(analysis/outline-check) are dropped, as in the other distance analyses.
Hotspots: CWFIS WFS hotspot archive 2026 (data/fire/raw/hotspots_wfs_2026, all sensors: VIIRS, MODIS, SLSTR).
First detection = M3 FIRSTDATE (earliest hotspot of the cluster); checked against the earliest hotspot inside the outline.
Growth: every hotspot inside the outline from FIRSTDATE on is snapped to a 400 m cell (EPSG:3978). Estimated area at
time t = final outline area x (distinct cells detected by t / distinct cells over the season). This is the hotspot
footprint growth curve rescaled to the final outline, which is itself a buffer of the same hotspots.
Second start definition ("main run"): the outline's hotspot record is split wherever no new 400 m cell is detected
for more than 7 days, and growth is timed from the start of the run that adds the most cells. This removes early
unrelated or holdover detections that the outline later swallowed; the first definition is the conservative one.
Cross-check: the CWFIS M3 WFS archive keeps earlier daily versions of each outline (area by version date);
first version >= 1,000 ha gives an independent "hours to 1,000 ha".
Outputs: escape_speed_2026_fires.csv, escape_speed_2026_summary.csv (size concentration is in 07)
"""
import glob

import geopandas as gpd
import numpy as np
import pandas as pd

from common import DATA, HOTSPOT_DIR, M3_2026, OUTLINE_CLASS, OUT, WORK

per = gpd.read_file(M3_2026)
cls = gpd.read_file(OUTLINE_CLASS)[["fire_uid", "class", "agency_match"]]
per = per.merge(cls, left_on="UID", right_on="fire_uid", how="left")
per["exclude"] = per["class"].isin(["likely agricultural or grass burn", "military range"]) & ~per.agency_match.fillna(False).astype(bool)
print("classes:", per["class"].value_counts().to_dict(), "excluded:", int(per.exclude.sum()), round(per.loc[per.exclude, "area_ha_albers"].sum()))
per = per[~per.exclude].copy()
per["first"] = pd.to_datetime(per.FIRSTDATE)
per = per.to_crs("EPSG:3978")

# --- hotspots
fs = sorted(glob.glob(str(HOTSPOT_DIR / "2026*.csv")))
hs = pd.concat([pd.read_csv(f, usecols=["lat", "lon", "rep_date", "sensor"]) for f in fs], ignore_index=True)
hs["t"] = pd.to_datetime(hs.rep_date, errors="coerce")
hs = hs[(hs.t <= "2026-10-20 23:59") & hs.lat.between(41, 84) & hs.lon.between(-142, -52)]
print("hotspots read", len(hs), flush=True)
g = gpd.GeoDataFrame(hs[["t", "sensor"]], geometry=gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs("EPSG:3978")
j = gpd.sjoin(g, per[["UID", "first", "geometry"]], predicate="within", how="inner")
j["cx"] = (j.geometry.x // 400).astype(np.int64)
j["cy"] = (j.geometry.y // 400).astype(np.int64)
j = j[j.t >= j["first"] - pd.Timedelta(hours=1)]
j["h"] = (j.t - j["first"]).dt.total_seconds() / 3600
print("hotspots in outlines after first date", len(j), flush=True)

GAP_H = 168


def main_run(hh):
    """Start of the main detection run: the cell first-detection times are split wherever no new cell appears for
    more than GAP_H hours; the run adding the most cells is the main run. Returns its start (hours after FIRSTDATE)
    and the share of all cells detected by start + 24/48/72/168 h."""
    hh = np.sort(hh)
    cut = np.flatnonzero(np.diff(hh) > GAP_H) + 1
    seg = np.split(np.arange(len(hh)), cut)
    big = max(seg, key=len)
    s0 = hh[big[0]]
    out = dict(main_start_h=float(s0), main_run_cells_share=len(big) / len(hh))
    for k in [24, 48, 72, 168]:
        out[f"frac_main_{k}"] = np.mean(hh <= s0 + k)
    return out


rows = []
for uid, d in j.groupby("UID"):
    d = d.sort_values("h")
    first_cell = ~d.duplicated(["cx", "cy"])
    hh = d.h.values[first_cell.values]
    ncell = len(hh)
    rows.append(dict(UID=uid, n_hotspots=len(d), n_cells=ncell, first_hotspot_in_outline_h=float(d.h.min()),
                     first_x_3978=float(d.geometry.x.iloc[0]), first_y_3978=float(d.geometry.y.iloc[0]),
                     frac_24=np.mean(hh <= 24), frac_48=np.mean(hh <= 48), frac_72=np.mean(hh <= 72),
                     frac_168=np.mean(hh <= 168), **main_run(hh)))
R = pd.DataFrame(rows)
P = per[["UID", "prov", "first", "LASTDATE", "area_ha_albers", "HCOUNT"]].merge(R, on="UID", how="left")
for k in [24, 48, 72, 168]:
    P[f"est_ha_{k}h"] = P.area_ha_albers * P[f"frac_{k}"].fillna(0)
    P[f"est_ha_main_{k}h"] = P.area_ha_albers * P[f"frac_main_{k}"].fillna(0)

# --- cross-check with archived M3 versions
v = gpd.read_file(DATA / "fire/raw/m3_2026/wfs_m3polygons_2026.gpkg", ignore_geometry=True)
v["firstdate"] = pd.to_datetime(v.firstdate).dt.tz_localize(None)
v["lastdate"] = pd.to_datetime(v.lastdate).dt.tz_localize(None)
perc = gpd.read_file(M3_2026, ignore_geometry=True)[["UID", "CONSIS_ID"]]
P = P.merge(perc, on="UID", how="left")
first_big = v[v.area >= 1000].sort_values("lastdate").groupby("consis_id").first()
P["m3_version_h_to_1000"] = P.CONSIS_ID.map(
    (first_big.lastdate - first_big.firstdate).dt.total_seconds() / 3600)
P.to_csv(OUT / "escape_speed_2026_fires.csv", index=False, float_format="%.3f")

# --- summary
tot = P.area_ha_albers.sum()
out = []
for prov, d in [("Canada", P)] + list(P.groupby("prov")):
    t = d.area_ha_albers.sum()
    r = dict(prov=prov, fires=len(d), mapped_ha=t,
             share_from_fires_ge_1000ha=d.loc[d.area_ha_albers >= 1000, "area_ha_albers"].sum() / t)
    for k in [24, 48, 72, 168]:
        hit = d[f"est_ha_{k}h"] >= 1000
        r[f"share_area_fires_1000ha_within_{k}h"] = d.loc[hit, "area_ha_albers"].sum() / t
        r[f"fires_1000ha_within_{k}h"] = int(hit.sum())
        r[f"share_area_burned_within_{k}h_of_detection"] = d[f"est_ha_{k}h"].sum() / t
        hit = d[f"est_ha_main_{k}h"] >= 1000
        r[f"main_run_share_area_fires_1000ha_within_{k}h"] = d.loc[hit, "area_ha_albers"].sum() / t
        r[f"main_run_fires_1000ha_within_{k}h"] = int(hit.sum())
    hit = d.m3_version_h_to_1000 <= 72
    r["m3_versions_share_area_1000ha_within_72h"] = d.loc[hit, "area_ha_albers"].sum() / t
    out.append(r)
S = pd.DataFrame(out)
S.to_csv(OUT / "escape_speed_2026_summary.csv", index=False, float_format="%.4f")
print(S.T.to_string())

