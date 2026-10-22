"""Area burned in Canada 1959/1972-2026: share of forest burned and hectares burned, decadal means, trends.

Inputs
  analysis/cause/burn_history_by_area_year.csv   forest share burned per fma_v2 area and year, 1972-2026
        (NBAC 1972-2025 rasterized at 240 m; CWFIS M3 2026 with forest_share_burned_scaled = M3 x province
        official/M3 factor); forest = Land Cover 2020 forest classes.
  analysis/cause/work/areas_fcd292dde04d/area_forest.csv   forest ha per area
  analysis/forest/nbac_totals_by_year_admin.csv  NBAC hectares (all land) by province and year 1972-2025
  analysis/forest/scaling_factors_by_province.csv official 2026 hectares by province (agency + Parks Canada)
  data/fire/raw/nfdb/NFDB_point_txt.zip           CNFDB fire points (version 20260811)
Series
  forest share  = sum of forest ha burned / sum of forest ha (Canada and region); 2026 on the scaled basis.
  hectares      = NBAC all-land ha (1972-2025) and official 2026 ha (provinces + Parks Canada); NBAC's PC and
                  DND columns are added to Canada only.
  1959-1971     = CNFDB fires >= 200 ha (prescribed burns removed) summed by agency/region, multiplied by the
                  region's NBAC / CNFDB(>=200 ha) ratio in 1972-1981. Used only where the overlap test passes:
                  ratio 1972-1981 within 0.5 to 2 and the same ratio in 1982-1991 within a factor 1.5 of it, and
                  log-correlation of yearly totals 1972-1991 >= 0.7.
Trends: OLS of log10(value) on year, slope reported as % change per decade (10**(10 b) - 1), interval from
1,000 bootstrap resamples of years (and the AR1-adjusted OLS interval); Theil-Sen and Mann-Kendall.
Periods 1972-2026, 1972-2022 (without 2023-2026), 1959-2026 (Canada and passing regions with CNFDB extension).
Outputs: area_burned_series.csv, area_burned_decades.csv, area_burned_trends.csv, cnfdb_overlap_check.csv,
         work/log_07.txt
"""
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from scipy import stats

from common import WORK, OUT, CAUSE, CAUSE_AREAS, FOREST, FIRE, REGION, REGIONS, areas, log, trend_stats

fh = open(WORK / "log_07.txt", "w")
rng = np.random.default_rng(7)
A = areas()
B = pd.read_csv(CAUSE / "burn_history_by_area_year.csv")
B = B.merge(A[["fma_id", "forest_ha", "region"]], on="fma_id")
B["fb"] = np.where(B.year == 2026, B.forest_share_burned_scaled, B.forest_share_burned) * B.forest_ha
B["fb_mapped"] = B.forest_share_burned * B.forest_ha
rows = []
for scope in ["Canada"] + REGIONS:
    d = B if scope == "Canada" else B[B.region == scope]
    fh_tot = (A if scope == "Canada" else A[A.region == scope]).forest_ha.sum()
    g = d.groupby("year")[["fb", "fb_mapped"]].sum()
    for y, r in g.iterrows():
        rows.append(dict(scope=scope, year=y, forest_share=r.fb / fh_tot, forest_share_mapped=r.fb_mapped / fh_tot,
                         forest_burned_ha=r.fb, forest_ha=fh_tot))
FS = pd.DataFrame(rows)

N = pd.read_csv(FOREST / "nbac_totals_by_year_admin.csv").set_index("YEAR")
SC = pd.read_csv(FOREST / "scaling_factors_by_province.csv").set_index("province")
hrows = []
for y in range(1972, 2027):
    for scope in ["Canada"] + REGIONS:
        if y <= 2025:
            if scope == "Canada":
                v = N.loc[y, "CANADA"]
            else:
                v = N.loc[y, [p for p, r in REGION.items() if r == scope and p in N.columns]].sum()
        else:
            if scope == "Canada":
                v = SC.official_2026_ha.sum()
            else:
                v = SC.loc[[p for p in SC.index if REGION.get(p) == scope], "official_2026_ha"].sum()
        hrows.append(dict(scope=scope, year=y, hectares=v, ha_source="NBAC" if y <= 2025 else "official 2026 (agency + Parks Canada)"))
HA = pd.DataFrame(hrows)

# CNFDB large fires
c = pd.read_csv(zipfile.ZipFile(FIRE / "raw" / "nfdb" / "NFDB_point_txt.zip").open("NFDB_point_20260811.txt"),
                usecols=["SRC_AGENCY", "YEAR", "SIZE_HA", "LATITUDE", "LONGITUDE", "PRESCRIBED", "CAUSE2"], low_memory=False)
pb = c.PRESCRIBED.astype(str).str.strip().isin(["PB", "1"]) | (c.CAUSE2 == "H-PB")
c = c[~pb & (c.SIZE_HA >= 200) & (c.YEAR >= 1959) & (c.YEAR <= 2025)]
c["region"] = c.SRC_AGENCY.map(REGION)
# Parks Canada points: region from latitude/longitude via the nearest fma_v2 area
pc = c.SRC_AGENCY == "PC"
if pc.any():
    import geopandas as gpd
    from common import CLIMATE_AREAS
    G = gpd.read_file(CLIMATE_AREAS / "areas_1km.gpkg")
    idc = "fma_id" if "fma_id" in G.columns else "area_id"
    pts = gpd.GeoDataFrame(c[pc], geometry=gpd.points_from_xy(c[pc].LONGITUDE, c[pc].LATITUDE), crs="EPSG:4326").to_crs(G.crs)
    j = gpd.sjoin_nearest(pts, G[[idc, "geometry"]], how="left")
    j = j[~j.index.duplicated()]
    c.loc[pc, "region"] = j[idc].map(A.set_index("fma_id").region).values
CN = c.groupby(["region", "YEAR"]).SIZE_HA.sum().unstack(0).reindex(range(1959, 2026)).fillna(0)
CN["Canada"] = CN.sum(axis=1)
chk = []
ext = {}
for scope in ["Canada"] + REGIONS:
    h = HA[HA.scope == scope].set_index("year").hectares
    cn = CN[scope]
    r1 = h.loc[1972:1981].sum() / cn.loc[1972:1981].sum()
    r2 = h.loc[1982:1991].sum() / cn.loc[1982:1991].sum()
    lc = np.corrcoef(np.log10(h.loc[1972:1991] + 1), np.log10(cn.loc[1972:1991] + 1))[0, 1]
    ok = (0.5 <= r1 <= 2) and (max(r1, r2) / min(r1, r2) <= 1.5) and lc >= 0.7
    chk.append(dict(scope=scope, ratio_nbac_to_cnfdb200_1972_1981=r1, ratio_1982_1991=r2, log_corr_1972_1991=lc,
                    cnfdb200_mean_1959_1971_ha=cn.loc[1959:1971].mean(), passes=ok))
    if ok:
        ext[scope] = cn.loc[1959:1971] * r1
CK = pd.DataFrame(chk)
CK.to_csv(OUT / "cnfdb_overlap_check.csv", index=False)
log(CK.round(3).to_string(), fh)
# extend hectares and forest share (forest share 1959-1971 = scaled ha x region forest fraction of burned ha 1972-1981 / forest ha)
er = []
for scope, s in ext.items():
    fs = FS[FS.scope == scope].set_index("year")
    h = HA[HA.scope == scope].set_index("year").hectares
    ff = fs.loc[1972:1981, "forest_burned_ha"].sum() / h.loc[1972:1981].sum()
    for y, v in s.items():
        er.append(dict(scope=scope, year=y, hectares=v, ha_source="CNFDB >=200 ha x NBAC/CNFDB 1972-1981",
                       forest_share=v * ff / fs.forest_ha.iloc[0], forest_share_mapped=np.nan,
                       forest_burned_ha=v * ff, forest_ha=fs.forest_ha.iloc[0]))
S = FS.merge(HA, on=["scope", "year"], how="outer")
S = pd.concat([pd.DataFrame(er), S], ignore_index=True).sort_values(["scope", "year"])
S["forest_ha_per_burned_ha"] = S.forest_burned_ha / S.hectares
S.to_csv(OUT / "area_burned_series.csv", index=False)

# decades
S["decade"] = np.where(S.year >= 2020, "2020-2026", (S.year // 10 * 10).astype(str) + "s")
S.loc[S.year < 1960, "decade"] = "1959"
dec = S.groupby(["scope", "decade"]).agg(n_years=("year", "size"), forest_share_mean=("forest_share", "mean"),
                                         hectares_mean=("hectares", "mean"), forest_per_burned=("forest_ha_per_burned_ha", "mean")).reset_index()
dec.to_csv(OUT / "area_burned_decades.csv", index=False)


def boot_trend(y, v, nb=1000):
    y = np.asarray(y, float)
    lv = np.log10(np.asarray(v, float))
    b = np.polyfit(y, lv, 1)[0]
    bs = []
    n = len(y)
    for _ in range(nb):
        i = rng.integers(0, n, n)
        if np.unique(y[i]).size < 3:
            continue
        bs.append(np.polyfit(y[i], lv[i], 1)[0])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    pct = lambda s: (10 ** (10 * s) - 1) * 100
    p_boot = 2 * min((np.array(bs) <= 0).mean(), (np.array(bs) >= 0).mean())
    return dict(pct_per_decade=pct(b), boot_lo=pct(lo), boot_hi=pct(hi), p_boot=p_boot)


tr = []
for scope in ["Canada"] + REGIONS:
    s = S[S.scope == scope].set_index("year")
    for var in ["forest_share", "hectares"]:
        periods = [(1972, 2026), (1972, 2022), (1990, 2026)]
        if scope in ext:
            periods.append((1959, 2026))
            periods.append((1959, 2022))
        for a, b in periods:
            x = s.loc[a:b, var].dropna()
            x = x[x > 0]
            ts = trend_stats(x.index.values, np.log10(x.values))
            pct = lambda q: (10 ** q - 1) * 100       # per-decade log10 slope -> % per decade
            tr.append(dict(scope=scope, variable=var, period=f"{a}-{b}", n=len(x), **boot_trend(x.index, x.values),
                           ols_ar1_lo=pct(ts["ols_lo"]), ols_ar1_hi=pct(ts["ols_hi"]), ols_p_ar1=ts["ols_p_ar1"],
                           sen_pct=pct(ts["sen_per"]), sen_lo=pct(ts["sen_lo"]), sen_hi=pct(ts["sen_hi"]), mk_p=ts["mk_p"],
                           mean_first_10=x.iloc[:10].mean(), mean_last_10=x.iloc[-10:].mean()))
TR = pd.DataFrame(tr)
TR.to_csv(OUT / "area_burned_trends.csv", index=False)
pd.set_option("display.width", 250)
log(TR.round(3).to_string(), fh)
log(dec[dec.scope == "Canada"].round(5).to_string(), fh)
log(S[S.scope == "Canada"][["year", "forest_share", "hectares", "forest_ha_per_burned_ha"]].round(4).to_string(), fh)
