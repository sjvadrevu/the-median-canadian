"""econ2_sat_01_aoi.py: fire polygons (AOIs) and Sentinel-2 windows for the econ2 satellite counts of destroyed buildings.

Same method as analysis/property (scripts 04, 05, 07, 08, 15): Microsoft footprints within 1 km of a fire polygon, Sentinel-2
L2A pre/post composites, the Jasper-calibrated rule. This script only defines the polygons and the image windows.

Jobs (polygon source, official data only):
  ab2023    NBAC 2023 polygons, ADMIN_NAME AB (Fox Lake, East Prairie, Sturgeon Lake, Yellowhead County and every other AB fire)
  qc2023    NBAC 2023 polygons, ADMIN_NAME QC
  mb2025    NBAC 2025 polygons, ADMIN_NAME MB (Lac du Bonnet buildings already in the bill are removed later, by footprint)
  atl2025   NBAC 2025 polygons, ADMIN_NAME NS, NB, NL (Kingston NL and the May 2025 Small Point fire included)
  kfn2023   NBAC 2023 NT polygons within 15 km of the Katl'odeeche First Nation reserve (Hay River Dene 1); window
            June-July 2023, after the May 2023 fire that entered the reserve and before the August fire near Hay River
  bc2026    BC Wildfire Service official perimeters (BC Data Catalogue, PROT_CURRENT_FIRE_POLYS_SP, read 2026-10-22) for
            K41351 (Bradley Creek) and C40983 (Pear Lake / Big Bar complex); window as analysis/property/08 for 2026
NBAC = NRCan National Burned Area Composite 1972-2025 (version 20260513), data/fire/raw/nbac.

Post window (2023 and 2025 fires): from the day after the last hotspot (HS_EDATE; else AG_EDATE; else Aug 31) for 60 days,
capped at Oct 15; if that leaves fewer than 30 days, Sep 15 to Oct 15; if the last hotspot is after Sep 15, the next year's
Jun 15 to Aug 15, with the pre window set to the year before the fire (Jun 5 to Aug 25). Otherwise the pre window is the
post window one year earlier widened by 10 days each side (s2lib default).
usage: python3 -I econ2_sat_01_aoi.py   -> work/econ2_sat/aoi_<job>.gpkg"""
import json, os
import pandas as pd, geopandas as gpd, pyogrio, shapely

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # costs-full
AN = os.path.dirname(B)                                                  # analysis
W = os.path.dirname(AN)                                                  # wildfire
OUT = os.path.join(B, "work", "econ2_sat"); os.makedirs(OUT, exist_ok=True)
NBAC = os.path.join(W, "data/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp")


def windows(year, hs_end, ag_end):
    e = pd.Timestamp(hs_end) if pd.notna(hs_end) else (pd.Timestamp(ag_end) if pd.notna(ag_end) else pd.Timestamp(f"{year}-08-31"))
    cap = pd.Timestamp(f"{year}-10-15")
    if e > pd.Timestamp(f"{year}-09-15"):
        return (f"{year+1}-06-15", f"{year+1}-08-15", f"{year-1}-06-05", f"{year-1}-08-25", "next summer")
    ps = e + pd.Timedelta(days=1); pe = min(ps + pd.Timedelta(days=60), cap)
    if (pe - ps).days < 30:
        ps, pe = pd.Timestamp(f"{year}-09-15"), cap
    return (str(ps.date()), str(pe.date()), "", "", "after last hotspot")


def nbac(year, provs):
    q = f"YEAR={year} AND ADMIN_NAME IN ({','.join(repr(p) for p in provs)})"
    g = pyogrio.read_dataframe(NBAC, where=q).to_crs(3978)
    g = g[g.PRESCRIBED.fillna("").astype(str).str.lower().ne("true")].copy()
    bad = ~g.geometry.is_valid
    g.loc[bad, "geometry"] = shapely.make_valid(g.geometry[bad].values)
    # NBAC polygons follow 20 to 30 m pixel edges (up to 1 million vertices); a 15 m simplification removes the staircase
    # and changes distances by at most 15 m against the 250 m and 500 m bands used for counting
    g["geometry"] = g.geometry.simplify(15, preserve_topology=True)
    w = [windows(year, a, b) for a, b in zip(g.HS_EDATE, g.AG_EDATE)]
    g["post_start"], g["post_end"], g["pre_start"], g["pre_end"], g["window_rule"] = zip(*w)
    g["fire_id"] = g.GID.astype(str); g["prov"] = g.ADMIN_NAME; g["year"] = year; g["area_ha"] = g.ADJ_HA.round(1)
    g["hs_sdate"] = g.HS_SDATE.astype(str).str[:10]; g["hs_edate"] = g.HS_EDATE.astype(str).str[:10]
    return g[["fire_id", "prov", "year", "area_ha", "hs_sdate", "hs_edate", "post_start", "post_end", "pre_start", "pre_end", "window_rule", "geometry"]]


jobs = {}
jobs["ab2023"] = nbac(2023, ["AB"])
jobs["qc2023"] = nbac(2023, ["QC"])
jobs["mb2025"] = nbac(2025, ["MB"])
jobs["atl2025"] = nbac(2025, ["NS", "NB", "NL"])
# KFN reserve (Hay River Dene 1, east bank of the Hay River opposite the town): NBAC 2023 NT polygons within 15 km of
# 60.84N 115.73W
nt = nbac(2023, ["NT"])
k = gpd.GeoSeries([shapely.Point(-115.73, 60.84)], crs=4326).to_crs(3978).buffer(15000).iloc[0]
kfn = nt[nt.intersects(k)].copy()
kfn["post_start"], kfn["post_end"], kfn["pre_start"], kfn["pre_end"], kfn["window_rule"] = "2023-06-01", "2023-07-31", "2022-05-22", "2022-08-10", "after the May 2023 fire, before August"
jobs["kfn2023"] = kfn
# BC 2026: BCWS official perimeters
bc = gpd.read_file(os.path.join(B, "raw/econ2/bcws/bcws_current_fire_polys_2026.json")).to_crs(3978)
bc = bc[bc.FIRE_NUMBER.isin(["K41351", "C40983"])].copy()
bc["geometry"] = bc.geometry.buffer(0)
bc["fire_id"] = bc.FIRE_NUMBER; bc["prov"] = "BC"; bc["year"] = 2026; bc["area_ha"] = bc.FIRE_SIZE_HECTARES
bc["hs_sdate"] = ""; bc["hs_edate"] = bc.TRACK_DATE.astype(str).str[:10]
bc["post_start"], bc["post_end"], bc["pre_start"], bc["pre_end"], bc["window_rule"] = "2026-09-19", "2026-10-20", "", "", "as analysis/property 2026 run"
jobs["bc2026"] = bc[["fire_id", "prov", "year", "area_ha", "hs_sdate", "hs_edate", "post_start", "post_end", "pre_start", "pre_end", "window_rule", "geometry"]]
summ = []
for j, g in jobs.items():
    g = gpd.GeoDataFrame(g, geometry="geometry", crs=3978)
    g.to_file(os.path.join(OUT, f"aoi_{j}.gpkg"), driver="GPKG")
    summ.append(dict(job=j, polygons=len(g), area_ha=round(g.area_ha.sum()), next_summer=int((g.window_rule == "next summer").sum())))
print(pd.DataFrame(summ).to_string())
