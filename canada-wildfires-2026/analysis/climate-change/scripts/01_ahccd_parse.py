"""Parse ECCC AHCCD monthly files into long tables and select stations near forested fire management areas.

Inputs (raw/ahccd/, downloaded from https://eccc-opendata-01.collab.science.gc.ca/CDAS/products/AHCCD/):
  Homog_monthly_mean_temp_Gen3.zip  third-generation homogenized monthly mean temperature, updated to 2023
  Adj_monthly_total_prec.zip        second-generation adjusted monthly total precipitation, updated to Dec 2017
  Temperature_Stations_Gen3.xls, Precipitation_Stations.xls  station lists (coordinates)
Missing values are -9999.9 (flag M); every other flag (E estimated, a adjusted, etc.) is kept as valid.
Station selection: inside or within 50 km of an eligible forested fma_v2 area (forest >= 100,000 ha and
>= 5% of land, not Nunavut), and with a usable record (see thresholds below).
Outputs: work/ahccd_temp_monthly.csv, work/ahccd_prec_monthly.csv, work/ahccd_stations.csv, work/log_01.txt
"""
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geopandas as gpd
import numpy as np
import pandas as pd

from common import RAW, WORK, CLIMATE_AREAS, areas, log

fh = open(WORK / "log_01.txt", "w")
R = RAW / "ahccd"


def parse_zip(zp, kind):
    rows = []
    with zipfile.ZipFile(zp) as z:
        for name in z.namelist():
            txt = z.read(name).decode("latin-1").splitlines()
            sid = txt[0].split(",")[0].strip()
            for line in txt[4:]:
                p = [s.strip() for s in line.split(",")]
                if not p or not p[0].isdigit():
                    continue
                yr = int(p[0])
                for m in range(12):
                    v = float(p[1 + 2 * m]) if p[1 + 2 * m] else np.nan
                    fl = p[2 + 2 * m] if len(p) > 2 + 2 * m else ""
                    if v <= -9999 or fl == "M":
                        v = np.nan
                    rows.append((sid, yr, m + 1, v, fl))
    d = pd.DataFrame(rows, columns=["station", "year", "month", kind, "flag"])
    return d


T = parse_zip(R / "Homog_monthly_mean_temp_Gen3.zip", "tmean")
P = parse_zip(R / "Adj_monthly_total_prec.zip", "prec")
log(f"temperature: {T.station.nunique()} stations, {T.tmean.notna().sum()} valid months, years {T.year.min()}-{T.year.max()}", fh)
log(f"precipitation: {P.station.nunique()} stations, {P.prec.notna().sum()} valid months, years {P.year.min()}-{P.year.max()}", fh)

# station lists
ts = pd.read_excel(R / "Temperature_Stations_Gen3.xls", header=None, skiprows=4)
ts = ts.iloc[:, [1, 2, 3, 4, 6, 9, 10, 11, 12]]
ts.columns = ["station", "name", "prov", "from", "to", "lat", "lon", "elev", "joined"]
ts["kind"] = "temp"
ps = pd.read_excel(R / "Precipitation_Stations.xls", header=None, skiprows=4)
ps = ps.iloc[:, [0, 1, 2, 3, 5, 7, 8, 9, 10]]
ps.columns = ["prov", "name", "station", "from", "to", "lat", "lon", "elev", "joined"]
ps["kind"] = "prec"
S = pd.concat([ts, ps], ignore_index=True)
S = S[S.station.notna()].copy()
S["station"] = S.station.astype(str).str.strip()
S["name"] = S.name.astype(str).str.strip()
S["prov"] = S.prov.astype(str).str.strip()
S = S[pd.to_numeric(S.lat, errors="coerce").notna()]
S[["lat", "lon", "elev"]] = S[["lat", "lon", "elev"]].apply(pd.to_numeric, errors="coerce")
log(f"station list rows: temp {(S.kind == 'temp').sum()}, prec {(S.kind == 'prec').sum()}", fh)

# record quality per station
def quality(d, var, months, y0, y1):
    q = d[d.month.isin(months)].groupby(["station", "year"])[var].count().unstack()
    full = (q == len(months))
    yrs = [y for y in range(y0, y1 + 1)]
    full = full.reindex(columns=yrs, fill_value=False).fillna(False)
    out = pd.DataFrame({"n_full_years": full.sum(axis=1),
                        "n_normal_years": full[[y for y in yrs if 1961 <= y <= 1990]].sum(axis=1),
                        "n_post2000": full[[y for y in yrs if y >= 2000]].sum(axis=1)})
    lasty = d[d[var].notna()].groupby("station").year.max()
    out["last_year"] = lasty.reindex(out.index)
    return out


qt = quality(T, "tmean", [5, 6, 7, 8], 1950, 2023)
qp = quality(P, "prec", [4, 5, 6, 7, 8, 9], 1950, 2017)
# Thresholds: temperature May-Aug complete in >= 59 of 74 years 1950-2023 (80%), >= 24 of 30 normal years,
# last value 2020 or later; precipitation Apr-Sep complete in >= 54 of 68 years 1950-2017 (80%),
# >= 24 of 30 normal years, last value 2010 or later (many AHCCD precipitation records end 2010-2014;
# later months come from offset-corrected climate-daily, see 03).
qt["ok"] = (qt.n_full_years >= 59) & (qt.n_normal_years >= 24) & (qt.last_year >= 2020)
qp["ok"] = (qp.n_full_years >= 54) & (qp.n_normal_years >= 24) & (qp.last_year >= 2010)
log(f"long-record temperature stations (Canada): {qt.ok.sum()} of {len(qt)}; precipitation: {qp.ok.sum()} of {len(qp)}", fh)

# distance to eligible forested areas
A = areas()
el = A[A.eligible]
G = gpd.read_file(CLIMATE_AREAS / "areas_1km.gpkg")
idcol = "fma_id" if "fma_id" in G.columns else "area_id"
G = G[G[idcol].isin(el.fma_id)].to_crs("ESRI:102001")
rows = []
for kind, q in [("temp", qt), ("prec", qp)]:
    s = S[(S.kind == kind) & S.station.isin(q.index[q.ok])].drop_duplicates("station")
    pts = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.lon, s.lat), crs="EPSG:4326").to_crs("ESRI:102001")
    for r in pts.itertuples():
        d = G.geometry.distance(r.geometry) / 1000
        near = G.loc[d <= 50, idcol].tolist()
        inside = G.loc[d == 0, idcol].tolist()
        rows.append(dict(station=r.station, kind=kind, name=r.name, prov=r.prov, lat=r.lat, lon=r.lon, elev=r.elev,
                         joined=r.joined, n_full_years=q.loc[r.station, "n_full_years"],
                         n_normal_years=q.loc[r.station, "n_normal_years"], last_year=q.loc[r.station, "last_year"],
                         min_dist_km=float(d.min()), area_inside=inside[0] if inside else np.nan,
                         areas_within_50km=";".join(map(str, near))))
ST = pd.DataFrame(rows)
ST["near_forest_area"] = ST.min_dist_km <= 50
ST.to_csv(WORK / "ahccd_stations.csv", index=False)
for kind in ["temp", "prec"]:
    s = ST[(ST.kind == kind) & ST.near_forest_area]
    log(f"{kind}: {len(s)} long-record stations within 50 km of an eligible forested area; by province "
        f"{s.groupby('prov').size().to_dict()}", fh)
keep_t = ST[(ST.kind == "temp") & ST.near_forest_area].station
keep_p = ST[(ST.kind == "prec") & ST.near_forest_area].station
T[T.station.isin(keep_t) & (T.year >= 1940)].to_csv(WORK / "ahccd_temp_monthly.csv", index=False)
P[P.station.isin(keep_p) & (P.year >= 1940)].to_csv(WORK / "ahccd_prec_monthly.csv", index=False)
