"""Station anomalies -> area-year panel (climate_panel.csv), one row per area_id x year, 1991-2026.

Station quality control (site-years set to NaN):
  * snow-on-ground variables when the winter maximum is 0 cm but the site's median winter maximum
    (other years) is >= 10 cm (stations that report 0 instead of missing);
  * snowfall when it is 0 cm and either the winter maximum depth is >= 10 cm or the site's median
    snowfall is >= 20 cm.
Consistency rule (per variable, as in analysis/weather): a site is used for a variable when it has a
valid value in at least 24 of the 30 fire years 1991-2020 (column suffix none); the strict 28-of-30 rule
can be applied from n_valid_1991_2020 in work/station_normals.csv (not used in the correlations).
Normals: the site's mean over valid 1991-2020 years.
Station anomalies:
  snowfall_pct, max_snow_depth_pct, swe_apr1_pct, p_*_pct: 100 x value / normal (normal must be
      >= 5 cm, 5 cm, 10 mm, 1 mm)
  snow_cover_days_anom, melt_anom_days, t_amj_anom_c: value - normal
  months_since_wet: months from the last wet month to May of the fire year (0 = May itself was wet);
      wet month = precipitation >= 125% of that calendar month's 1991-2020 site mean; up to 2 missing
      months are skipped; searched back 60 months (60 = none found). Not anomalised.
Composition rule: an area-year value is dropped when fewer than half of its usual stations reported.
Stations to areas: a station serves every area that contains it or lies within 50 km of its boundary.
An area with no such station for a variable takes the nearest 3 stations within 250 km (basis column
'nearest'). Area value = median of its stations' anomalies that year; n_<var> = stations used.
CanSWE 1 April SWE (1991-2025 only) is aggregated the same way (consistency: 20 of 30 years, because
snow courses are sampled less regularly).
Outputs: climate_panel.csv, station_list.csv (stations used, with area assignment), work/station_normals.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
import numpy as np
import pandas as pd

from common import OUT, out_dir, REGION, WORK, YEARS, area_dir, log

D = area_dir()
fh = open(D / "log_06.txt", "w")
SY = pd.read_csv(WORK / "site_year.csv", dtype={"site": str})
SM = pd.read_csv(WORK / "site_month.csv", dtype={"site": str})
META = pd.read_csv(WORK / "site_meta.csv", dtype={"site": str}).set_index("site")
CS = pd.read_csv(WORK / "canswe_station_year.csv")

# ---------------- QC
med_max = SY[SY.max_snow_depth_cm > 0].groupby("site").max_snow_depth_cm.median()
bad = (SY.max_snow_depth_cm == 0) & (SY.site.map(med_max).fillna(0) >= 10)
for c in ["snow_cover_days", "max_snow_depth_cm", "melt_doy"]:
    SY.loc[bad, c] = np.nan
SY.loc[bad, "no_snow_winter"] = np.nan
med_sf = SY[SY.snowfall_cm > 0].groupby("site").snowfall_cm.median()
bad_sf = (SY.snowfall_cm == 0) & ((SY.max_snow_depth_cm >= 10) | (SY.site.map(med_sf).fillna(0) >= 20))
SY.loc[bad_sf, "snowfall_cm"] = np.nan
# melt date outliers: a single spurious snow-on-ground report in summer moves the melt date by months
# (e.g. Yellowknife A 2023: 1 August). Melt dates more than 5 scaled MADs (MAD x 1.4826) or 30 days,
# whichever is larger, from the site's median are set missing.
mmed = SY.groupby("site").melt_doy.transform("median")
mmad = SY.groupby("site").melt_doy.transform(lambda s: (s - s.median()).abs().median() * 1.4826)
bad_m = (SY.melt_doy - mmed).abs() > np.maximum(5 * mmad, 30)
SY.loc[bad_m, "melt_doy"] = np.nan
log(f"QC: {int(bad.sum())} site-years snow-on-ground set missing; {int(bad_sf.sum())} snowfall set missing; "
    f"{int(bad_m.sum())} melt dates set missing as outliers", fh)

# ---------------- months since wet (as of end of May)
SM["m"] = pd.PeriodIndex(SM.month, freq="M")
SM["cal"] = SM.m.dt.month
SM["yr"] = SM.m.dt.year
nm = SM[SM.yr.between(1991, 2020)].groupby(["site", "cal"]).p.agg(["mean", "count"])
SM = SM.join(nm, on=["site", "cal"])
SM["wet"] = np.where(SM.p.notna() & (SM["count"] >= 20), SM.p >= 1.25 * SM["mean"], np.nan)
msw = []
for s, g in SM.groupby("site"):
    w = dict(zip(g.m, g.wet))
    for y in YEARS:
        p0 = pd.Period(f"{y}-05", freq="M")
        miss, val = 0, np.nan
        for k in range(0, 61):
            v = w.get(p0 - k, np.nan)
            if v != v:          # NaN
                miss += 1
                if miss > 2:
                    break
                continue
            if v:
                val = k
                break
        else:
            val = 60
        msw.append((s, y, val))
SY = SY.merge(pd.DataFrame(msw, columns=["site", "fire_year", "months_since_wet"]), on=["site", "fire_year"], how="left")

# ---------------- normals and anomalies
PCT = {"snowfall_cm": ("snowfall_pct", 5), "max_snow_depth_cm": ("max_snow_depth_pct", 5),
       "p_amj": ("p_amj_pct", 1), "p_jja_prev": ("p_jja_prev_pct", 1), "p_son_prev": ("p_son_prev_pct", 1),
       "p_ndjfm": ("p_ndjfm_pct", 1), "p_12m": ("p_12m_pct", 1)}
DIFF = {"snow_cover_days": "snow_cover_days_anom", "melt_doy": "melt_anom_days", "t_amj": "t_amj_anom_c"}
RAWV = {"months_since_wet": "months_since_wet"}
norm_rows = []
inN = SY.fire_year.between(1991, 2020)
for v in list(PCT) + list(DIFF) + list(RAWV):
    cnt = SY[inN].groupby("site")[v].count()
    mu = SY[inN].groupby("site")[v].mean()
    SY[f"cons24_{v}"] = SY.site.map(cnt).fillna(0) >= 24
    SY[f"cons28_{v}"] = SY.site.map(cnt).fillna(0) >= 28
    norm_rows.append(pd.DataFrame({"var": v, "n_valid_1991_2020": cnt, "normal": mu}))
    if v in PCT:
        name, mn = PCT[v]
        nrm = SY.site.map(mu)
        SY[name] = np.where(nrm >= mn, 100 * SY[v] / nrm, np.nan)
    elif v in DIFF:
        SY[DIFF[v]] = SY[v] - SY.site.map(mu)
    else:
        SY[v + "_x"] = SY[v]
NR = pd.concat(norm_rows).reset_index().rename(columns={"index": "site"})
NR.to_csv(WORK / "station_normals.csv", index=False)

# CanSWE normals
cin = CS.fire_year.between(1991, 2020)
cc = CS[cin].groupby("station_id").swe_apr1_mm.agg(["count", "mean"])
CS = CS.join(cc, on="station_id")
CS = CS[(CS["count"] >= 20) & (CS["mean"] >= 10)].copy()
CS["swe_apr1_pct"] = 100 * CS.swe_apr1_mm / CS["mean"]
log(f"CanSWE consistent stations (>=20 of 30 years, normal >=10 mm): {CS.station_id.nunique()}", fh)

# ---------------- stations -> areas
A = gpd.read_file(D / "areas_1km.gpkg")


def assign(pts):
    """pts: GeoDataFrame (ESRI:102001) indexed by station key -> long table station, area_id, dist_km."""
    out = []
    for r in A.itertuples():
        d = pts.distance(r.geometry) / 1000.0
        out.append(pd.DataFrame({"station": pts.index, "area_id": r.fma_id, "dist_km": d.values}))
    return pd.concat(out, ignore_index=True)


SP = gpd.GeoDataFrame(META[["lon", "lat"]], geometry=gpd.points_from_xy(META.lon, META.lat), crs="EPSG:4326").to_crs(A.crs)
DS = assign(SP)
cs_st = CS.drop_duplicates("station_id").set_index("station_id")
CP = gpd.GeoDataFrame(cs_st[["lon", "lat"]], geometry=gpd.points_from_xy(cs_st.lon, cs_st.lat), crs="EPSG:4326").to_crs(A.crs)
DC = assign(CP)

VARS = (["snowfall_pct", "snow_cover_days_anom", "max_snow_depth_pct", "melt_anom_days", "t_amj_anom_c",
         "p_amj_pct", "p_jja_prev_pct", "p_son_prev_pct", "p_ndjfm_pct", "p_12m_pct", "months_since_wet_x"])
SRC = {"snowfall_pct": "snowfall_cm", "snow_cover_days_anom": "snow_cover_days", "max_snow_depth_pct": "max_snow_depth_cm",
       "melt_anom_days": "melt_doy", "t_amj_anom_c": "t_amj", "p_amj_pct": "p_amj", "p_jja_prev_pct": "p_jja_prev",
       "p_son_prev_pct": "p_son_prev", "p_ndjfm_pct": "p_ndjfm", "p_12m_pct": "p_12m", "months_since_wet_x": "months_since_wet"}


def area_stations(dist, eligible):
    d = dist[dist.station.isin(eligible)]
    near = d[d.dist_km <= 50].assign(basis="inside_or_50km")
    have = set(near.area_id)
    far = d[~d.area_id.isin(have) & (d.dist_km <= 250)].sort_values("dist_km").groupby("area_id").head(3).assign(basis="nearest")
    return pd.concat([near, far])


panel = pd.DataFrame([(int(a), y) for a in A.fma_id for y in YEARS], columns=["area_id", "year"])
station_list = []
for v in VARS:
    src = SRC[v]
    elig = SY.loc[SY[f"cons24_{src}"], "site"].unique()
    AS = area_stations(DS, elig)
    station_list.append(AS.assign(variable=v))
    x = SY[["site", "fire_year", v]].dropna()
    j = AS.merge(x, left_on="station", right_on="site")
    agg = j.groupby(["area_id", "fire_year"])[v].agg(["median", "count"])
    agg.columns = [v, f"n_{v}"]
    panel = panel.merge(agg, left_on=["area_id", "year"], right_index=True, how="left")
    basis = AS.groupby("area_id").basis.first()
    panel[f"basis_{v}"] = panel.area_id.map(basis)
    panel[f"n_{v}"] = panel[f"n_{v}"].fillna(0).astype(int)
# CanSWE
AS = area_stations(DC, CS.station_id.unique())
station_list.append(AS.assign(variable="swe_apr1_pct"))
j = AS.merge(CS[["station_id", "fire_year", "swe_apr1_pct"]], left_on="station", right_on="station_id")
agg = j.groupby(["area_id", "fire_year"]).swe_apr1_pct.agg(["median", "count"])
agg.columns = ["swe_apr1_pct", "n_swe_apr1_pct"]
panel = panel.merge(agg, left_on=["area_id", "year"], right_index=True, how="left")
panel["n_swe_apr1_pct"] = panel["n_swe_apr1_pct"].fillna(0).astype(int)
panel["basis_swe_apr1_pct"] = panel.area_id.map(AS.groupby("area_id").basis.first())
panel = panel.rename(columns={"months_since_wet_x": "months_since_wet", "n_months_since_wet_x": "n_months_since_wet",
                              "basis_months_since_wet_x": "basis_months_since_wet"})
# composition rule: an area-year value is dropped when fewer than half of the area's usual number of
# stations reported (usual = median n over 1991-2020 years with data); networks that changed IDs
# (e.g. Hydro-Quebec snow courses) otherwise leave an area represented by a few border stations.
dropped = {}
for v in VARS + ["swe_apr1_pct"]:
    v2 = "months_since_wet" if v == "months_since_wet_x" else v
    nc = f"n_{v2}"
    usual = panel[panel.year.between(1991, 2020) & (panel[nc] > 0)].groupby("area_id")[nc].median()
    thin = panel[nc] < 0.5 * panel.area_id.map(usual).fillna(0)
    dropped[v2] = int((thin & panel[v2].notna()).sum())
    panel.loc[thin, v2] = np.nan
log(f"area-years dropped by the composition rule: {dropped}", fh)
# raw melt date (median day of year of the same stations) for readability
AS = area_stations(DS, SY.loc[SY["cons24_melt_doy"], "site"].unique())
j = AS.merge(SY[["site", "fire_year", "melt_doy"]].dropna(), left_on="station", right_on="site")
panel = panel.merge(j.groupby(["area_id", "fire_year"]).melt_doy.median().rename("melt_doy_median"),
                    left_on=["area_id", "year"], right_index=True, how="left")

# ---------------- indices and outcome
I = pd.read_csv(OUT / "indices_by_fire_year.csv")
icols = ["oni_djf", "enso_winter_phase", "oni_mam", "pdo_djf", "pdo_mam", "ao_djf", "ao_mam", "ao_jfm",
         "nao_djf", "nao_mam", "vortex_jfm", "vortex_source"]
panel = panel.merge(I[["fire_year"] + icols], left_on="year", right_on="fire_year", how="left").drop(columns="fire_year")
O = pd.read_csv(D / "outcome.csv")
panel = panel.merge(O, on=["area_id", "year"], how="left")
panel["log10_burned_ha"] = np.log10(panel.burned_ha + 1)
attrs = A.drop(columns="geometry").rename(columns={"fma_id": "area_id"})[["area_id", "area_name", "province", "agency", "area_level"]]
panel = attrs.merge(panel, on="area_id")
panel.insert(3, "region", panel.province.map(REGION))
panel = panel.sort_values(["area_id", "year"])
panel.to_csv(out_dir() / "climate_panel.csv", index=False, float_format="%.4g")

SL = pd.concat(station_list)
SL = SL.merge(META[["STATION_NAME", "prov", "lon", "lat", "elev", "n_ids", "member_ids"]], left_on="station", right_index=True, how="left")
SL.to_csv(out_dir() / "station_list.csv", index=False, float_format="%.5g")
cov = panel[panel.year.between(1991, 2025)]
log("areas with >=1 station (any year) by variable:", fh)
for v in [c for c in panel.columns if c.startswith("n_")]:
    log(f"  {v}: areas {int((panel.groupby('area_id')[v].max() > 0).sum())} of {panel.area_id.nunique()}; "
        f"area-years with data 1991-2025 {int((cov[v] > 0).sum())}; 2026 areas {int((panel[panel.year == 2026][v] > 0).sum())}", fh)
log(f"stations used (any variable): {SL.station.nunique()}", fh)
