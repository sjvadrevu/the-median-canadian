"""Step 12: satellite hotspots inside the main DND training areas, from the CWFIS WFS hotspot archive
(public:hotspots, all years in the archive, fetched per base bounding box; raw/base_hotspots/<base>.csv).
Inside-base test against work/bases.gpkg. Metrics per base, year and season (by UTC date of detection):
  detection days  = distinct UTC dates with >= 1 hotspot inside the base
  episodes        = runs of detection days separated by <= 5 days
Two sensor sets: 'MODIS' (Terra + Aqua; consistent 2003-2026) and 'all' (every sensor in the archive).
Outputs: base_hotspots_by_year.csv, base_hotspots_summary.csv"""
import os, time, requests, pandas as pd, geopandas as gpd, numpy as np
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
U = "https://cwfis.cfs.nrcan.gc.ca/geoserver/public/wfs"
os.makedirs(f"{O}/raw/base_hotspots", exist_ok=True)
bases = gpd.read_file(f"{O}/work/bases.gpkg")
def season(m): return {3: "spring", 4: "spring", 5: "spring", 6: "summer", 7: "summer", 8: "summer", 9: "fall", 10: "fall", 11: "fall"}.get(m, "winter")
allrows = []
for _, b in bases.iterrows():
    f = f"{O}/raw/base_hotspots/{b.base}.csv"
    x0, y0, x1, y1 = gpd.GeoSeries([b.geometry], crs=3978).to_crs(4326).total_bounds
    if not os.path.exists(f):
        parts = []
        for y in range(1994, 2027):
            p = dict(service="WFS", version="2.0.0", request="GetFeature", typeNames="public:hotspots", outputFormat="csv",
                     count=100000, propertyName="lat,lon,rep_date,sensor,satellite,source",
                     CQL_FILTER=f"rep_date >= '{y}-01-01T00:00:00Z' AND rep_date < '{y+1}-01-01T00:00:00Z' AND BBOX(geometry,{x0:.4f},{y0:.4f},{x1:.4f},{y1:.4f},'EPSG:4326')")
            for a in range(5):
                try:
                    r = requests.get(U, params=p, timeout=600)
                    if r.status_code == 200 and r.text.startswith("FID"): break
                except requests.RequestException: pass
                time.sleep(10 * (a + 1))
            else:
                raise SystemExit(f"failed {b.base} {y}")
            d = pd.read_csv(pd.io.common.StringIO(r.text)); parts.append(d)
        pd.concat(parts).to_csv(f, index=False)
    d = pd.read_csv(f)
    g = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(3978)
    g = g[g.within(b.geometry)].copy()
    g["date"] = g.rep_date.str[:10]; g["base"] = b.base
    allrows.append(g.drop(columns="geometry"))
    print(b.base, len(d), "in bbox", len(g), "inside", g.date.str[:4].min(), flush=True)
H = pd.concat(allrows)
H.to_csv(f"{O}/work/base_hotspots_inside.csv", index=False)
H["year"] = H.date.str[:4].astype(int); H["season"] = H.date.str[5:7].astype(int).map(season)
H["sensor_set"] = np.where(H.sensor.str.upper().str.contains("MODIS"), "MODIS", "other")
out = []; summ = []
for sset, sub in [("MODIS", H[(H.sensor_set == "MODIS") & (H.year >= 2003)]), ("all", H)]:
    for base, g in sub.groupby("base"):
        days = pd.to_datetime(pd.Series(sorted(g.date.unique())))
        ep = (days.diff().dt.days > 5).cumsum()
        epi = pd.DataFrame(dict(start=days.groupby(ep).min(), n_days=days.groupby(ep).size()))
        epi["season"] = epi.start.dt.month.map(season); epi["year"] = epi.start.dt.year
        dd = pd.DataFrame(dict(date=days)); dd["season"] = dd.date.dt.month.map(season); dd["year"] = dd.date.dt.year
        for (y, s), x in dd.groupby(["year", "season"]):
            out.append(dict(sensor_set=sset, base=base, year=y, season=s, detection_days=len(x),
                            episodes=int(((epi.year == y) & (epi.season == s)).sum()),
                            hotspots=int(((g.year == y) & (g.season == s)).sum())))
        yrs = f"{2003 if sset == 'MODIS' else g.year.min()}-2026"
        r = dict(sensor_set=sset, base=base, years=yrs, n_years_in_period=2026 - (2003 if sset == "MODIS" else int(g.year.min())) + 1,
                 years_with_detection=dd.year.nunique(), detection_days=len(dd), episodes=len(epi), hotspots=len(g))
        for s in ["spring", "summer", "fall", "winter"]:
            r[f"days_{s}"] = int((dd.season == s).sum()); r[f"episodes_{s}"] = int((epi.season == s).sum())
        r["fall_share_days"] = round(r["days_fall"] / len(dd), 3); r["fall_share_episodes"] = round(r["episodes_fall"] / len(epi), 3)
        r["oct_days"] = int((dd.date.dt.month == 10).sum())
        r["years_with_oct_detection"] = sorted(dd[dd.date.dt.month == 10].year.unique().tolist())
        summ.append(r)
pd.DataFrame(out).to_csv(f"{O}/base_hotspots_by_year.csv", index=False)
S = pd.DataFrame(summ); S.to_csv(f"{O}/base_hotspots_summary.csv", index=False)
pd.set_option("display.width", 300); print(S.to_string())
