"""Step 11: mapped burns inside the main DND training areas.
(a) NBAC 1972-2025 (NRCan, v20260513) polygons intersected with each base (work/bases.gpkg);
    area inside base (equal-area ESRI:102001), start date = AG_SDATE, else HS_SDATE; season by start month
    (spring Mar-May, summer Jun-Aug, fall Sep-Nov, winter Dec-Feb, 'unknown' if no start date).
(b) CWFIS M3 2026 outlines (file of 2026-10-22) intersected with each base; season by FIRSTDATE.
(c) CNFDB fire points 1972-2025 (v20260811) inside each base: count by year and season (REP_DATE, else START date).
Outputs: base_burns_fires.csv (one row per fire x base), base_burns_by_year.csv, base_burns_summary.csv
"""
import zipfile, io, geopandas as gpd, pandas as pd, numpy as np, pyogrio
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
R = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/data/fire/raw"
EA = "ESRI:102001"
bases = gpd.read_file(f"{O}/work/bases.gpkg")
def season(m):
    if pd.isna(m): return "unknown"
    m = int(m); return {3: "spring", 4: "spring", 5: "spring", 6: "summer", 7: "summer", 8: "summer",
                        9: "fall", 10: "fall", 11: "fall"}.get(m, "winter")
rows = []
nb_path = f"{R}/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp"
crs = pyogrio.read_info(nb_path)["crs"]
for _, b in bases.iterrows():
    bb = gpd.GeoSeries([b.geometry], crs=3978).to_crs(crs)
    x0, y0, x1, y1 = bb.total_bounds
    n = pyogrio.read_dataframe(nb_path, bbox=(x0, y0, x1, y1))
    if n.empty: continue
    n = n.set_crs(crs, allow_override=True).to_crs(EA); be = bb.to_crs(EA).iloc[0]
    n["geometry"] = n.geometry.make_valid()
    n = n[n.intersects(be)]
    for _, f in n.iterrows():
        a_in = f.geometry.intersection(be).area / 1e4
        if a_in < 0.01: continue
        sd = f.AG_SDATE if pd.notna(f.AG_SDATE) else f.HS_SDATE
        rows.append(dict(source="NBAC", base=b.base, boundary_source=b.boundary_source, year=int(f.YEAR), fire_id=f.GID,
                         start_date=str(sd)[:10] if pd.notna(sd) else None, start_from="AG_SDATE" if pd.notna(f.AG_SDATE) else ("HS_SDATE" if pd.notna(f.HS_SDATE) else None),
                         season=season(pd.Timestamp(sd).month if pd.notna(sd) else np.nan),
                         fire_ha_total=round(f.POLY_HA, 1), ha_inside_base=round(a_in, 1), cause=f.FIRECAUS, prescribed=f.PRESCRIBED,
                         mapping_source=f.BASRC))
    print(b.base, "NBAC", sum(r["base"] == b.base and r["source"] == "NBAC" for r in rows), flush=True)
# M3 2026
m3 = gpd.read_file(f"{O}/raw/m3_20261022/perimeters.shp").to_crs(EA)
for _, b in bases.iterrows():
    be = gpd.GeoSeries([b.geometry], crs=3978).to_crs(EA).iloc[0]
    s = m3[m3.intersects(be)]
    for _, f in s.iterrows():
        a_in = f.geometry.intersection(be).area / 1e4
        rows.append(dict(source="CWFIS M3 2026 (2026-10-22 file)", base=b.base, boundary_source=b.boundary_source, year=2026,
                         fire_id=str(f.UID), start_date=str(f.FIRSTDATE)[:10], start_from="FIRSTDATE",
                         season=season(pd.Timestamp(f.FIRSTDATE).month), fire_ha_total=round(f.geometry.area / 1e4, 1),
                         ha_inside_base=round(a_in, 1), cause=None, prescribed=None, mapping_source="M3 hotspot outline"))
F = pd.DataFrame(rows)
# CNFDB points
z = zipfile.ZipFile(f"{R}/nfdb/NFDB_point_txt.zip")
p = pd.read_csv(z.open("NFDB_point_20260811.txt"), low_memory=False, encoding="latin1")
p = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.LONGITUDE, p.LATITUDE), crs=4269).to_crs(3978)
prow = []
for _, b in bases.iterrows():
    s = p[p.within(b.geometry)]
    for _, f in s.iterrows():
        d = f.REP_DATE if isinstance(f.REP_DATE, str) and f.REP_DATE[:4].isdigit() else None
        mo = int(f.MONTH) if pd.notna(f.MONTH) and f.MONTH > 0 else (int(d[5:7]) if d else np.nan)
        prow.append(dict(source="CNFDB points", base=b.base, year=int(f.YEAR), fire_id=f.FIRE_ID, start_date=d, season=season(mo),
                         fire_ha_total=f.SIZE_HA, agency=f.SRC_AGENCY, cause=f.CAUSE))
P = pd.DataFrame(prow)
A = pd.concat([F, P], ignore_index=True); A.to_csv(f"{O}/base_burns_fires.csv", index=False)
# per year and summary
by = A.groupby(["source", "base", "year", "season"]).agg(n_fires=("fire_id", "count"), ha_inside_base=("ha_inside_base", "sum")).reset_index()
by.to_csv(f"{O}/base_burns_by_year.csv", index=False)
summ = []
for (src, base), g in A.groupby(["source", "base"]):
    r = dict(source=src, base=base, boundary_source=bases.set_index("base").boundary_source[base],
             base_area_ha=round(bases.set_index("base").area_ha[base]), years_covered="1972-2025" if src != "CWFIS M3 2026 (2026-10-22 file)" else "2026",
             n_fires=len(g), n_years_with_fire=g.year.nunique(),
             ha_inside_total=round(g.ha_inside_base.sum(), 0) if "ha_inside_base" in g else None)
    for s in ["spring", "summer", "fall", "winter", "unknown"]:
        r[f"n_{s}"] = int((g.season == s).sum())
        if src != "CNFDB points": r[f"ha_{s}"] = round(g[g.season == s].ha_inside_base.sum(), 0)
    known = g[g.season != "unknown"]
    r["fall_share_of_dated_fires"] = round((known.season == "fall").mean(), 3) if len(known) else None
    if src != "CNFDB points" and len(known): r["fall_share_of_dated_area"] = round(known[known.season == "fall"].ha_inside_base.sum() / known.ha_inside_base.sum(), 3)
    summ.append(r)
S = pd.DataFrame(summ); S.to_csv(f"{O}/base_burns_summary.csv", index=False)
pd.set_option("display.width", 250); print(S.to_string())
