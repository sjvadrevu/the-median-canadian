"""Build one fire-point table: CNFDB points 1990-2025 plus the 2026 agency fire list (CWFIS/CWFIF API).

Rules
  * CNFDB (NFDB_point_20260811): years 1990-2025; prescribed burns removed (PRESCRIBED in PB/1 or CAUSE2 H-PB).
    CAUSE N -> lightning, H -> human, U -> undetermined. Start date = REP_DATE, else YEAR/MONTH/DAY.
  * 2026 list: fires whose situation_report_date is in calendar 2026 (drops 42 holdovers from earlier years).
    national_fire_cause natural -> lightning. Start date = situation_report_date, except NT, where every
    record carries the placeholder 2026-01-01 and the GNWT fire list discovery date is used (290 of 290 match).
  * Each point gets an area id (240 m raster lookup, snap to nearest area within 10 km) and the distance to
    the nearest populated 2021 dissemination-area representative point and to the nearest population centre
    (centroid), in km, Canada Albers equal-area.
Output: work/areas_<hash>/fires_all.pkl, log_03.txt
"""
import json
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from common import (CNFDB_MEMBER, CNFDB_ZIP, DA_POINTS, FIRE_LIST_2026, NT_POINTS_2026, POPCENTRES,
                    area_attrs, area_dir, assign_area, log)

D = area_dir()
fh = open(D / "log_03.txt", "w")

# ------------------------------------------------------------- CNFDB
cols = ["NFDBFIREID", "SRC_AGENCY", "NAT_PARK", "LATITUDE", "LONGITUDE", "YEAR", "MONTH", "DAY", "REP_DATE",
        "SIZE_HA", "CAUSE", "CAUSE2", "PRESCRIBED"]
c = pd.read_csv(zipfile.ZipFile(CNFDB_ZIP).open(CNFDB_MEMBER), usecols=cols, low_memory=False)
c = c[(c.YEAR >= 1990) & (c.YEAR <= 2025)].copy()
n0 = len(c)
pb = c.PRESCRIBED.astype(str).str.strip().isin(["PB", "1"]) | (c.CAUSE2 == "H-PB")
c = c[~pb]
log(f"CNFDB 1990-2025: {n0} points, {int(pb.sum())} prescribed removed, {len(c)} kept", fh)
d1 = pd.to_datetime(c.REP_DATE, errors="coerce")
d2 = pd.to_datetime(dict(year=c.YEAR, month=c.MONTH.clip(1, 12), day=c.DAY.clip(1, 31)), errors="coerce")
d2[(c.MONTH < 1) | (c.DAY < 1)] = pd.NaT
date = d1.where(d1.notna() & (d1.dt.year == c.YEAR), d2)
cn = pd.DataFrame(dict(
    fire_id=c.NFDBFIREID.astype(str), source="CNFDB", agency=c.SRC_AGENCY, year=c.YEAR.astype(int),
    start=date, size_ha=c.SIZE_HA.clip(lower=0), lat=c.LATITUDE, lon=c.LONGITUDE,
    cause=c.CAUSE.map({"N": "lightning", "H": "human", "U": "undetermined"}).fillna("undetermined"),
    in_nat_park=c.NAT_PARK.astype(str).str.strip().ne("") & c.NAT_PARK.notna()))
log(f"CNFDB start date missing: {cn.start.isna().sum()} ({cn.start.isna().mean():.2%})", fh)

# ------------------------------------------------------------- 2026 fire list
L = pd.DataFrame(json.load(open(FIRE_LIST_2026)))
L["srd"] = pd.to_datetime(L.situation_report_date)
L = L[L.srd.dt.year == 2026].copy()
nt = pd.DataFrame(json.load(open(NT_POINTS_2026)))
nt_d = pd.to_datetime(nt.set_index("title").discoverydate, errors="coerce")
isnt = L.agency_code == "NT"
L.loc[isnt, "srd"] = L.loc[isnt, "agency_fire_id"].map(nt_d)
log(f"2026 list: {len(L)} fires in calendar 2026, {L.fire_size.sum():,.1f} ha; NT dates replaced: "
    f"{L.loc[isnt, 'srd'].notna().sum()} of {isnt.sum()}", fh)
l26 = pd.DataFrame(dict(
    fire_id=L.national_fire_id, source="CWFIS2026", agency=L.agency_code, year=2026, start=L.srd.dt.tz_localize(None),
    size_ha=L.fire_size.clip(lower=0), lat=L.latitude, lon=L.longitude,
    cause=L.national_fire_cause.map({"natural": "lightning", "human": "human", "undetermined": "undetermined"}),
    in_nat_park=L.agency_code == "PC"))
F = pd.concat([cn, l26], ignore_index=True)
F["doy"] = F.start.dt.dayofyear

# ------------------------------------------------------------- area
F["fma_id"] = assign_area(F.lon.values, F.lat.values)
A = area_attrs().set_index("fma_id")
F["province"] = F.fma_id.map(A.province)
log(f"points without an area: {(F.fma_id == 0).sum()} ({F.loc[F.fma_id == 0, 'size_ha'].sum():,.0f} ha)", fh)
# agency vs geographic province agreement (non-Parks)
ok = (F.agency != "PC") & (F.fma_id > 0)
log(f"agency equals geographic province for {(F.agency[ok] == F.province[ok]).mean():.4f} of non-Parks points", fh)

# ------------------------------------------------------------- distance to population
pts = gpd.GeoSeries(gpd.points_from_xy(F.lon, F.lat), crs="EPSG:4326").to_crs("ESRI:102001")
XY = np.c_[pts.x.values, pts.y.values]
good = np.isfinite(XY).all(1)
da = gpd.read_file(DA_POINTS)
da = da[da.pop2021 > 0].to_crs("ESRI:102001")
t = cKDTree(np.c_[da.geometry.x, da.geometry.y])
dist = np.full(len(F), np.nan)
dist[good] = t.query(XY[good])[0] / 1000
F["dist_da_km"] = dist
pc = gpd.read_file(POPCENTRES).to_crs("ESRI:102001")
cen = pc.geometry.representative_point()
t2 = cKDTree(np.c_[cen.x, cen.y])
dist2 = np.full(len(F), np.nan)
dist2[good] = t2.query(XY[good])[0] / 1000
F["dist_popcentre_km"] = dist2
log(f"populated DA points {len(da)}, population centres {len(pc)}", fh)

F.to_pickle(D / "fires_all.pkl")
log(F.groupby(["source", "cause"]).agg(n=("size_ha", "size"), ha=("size_ha", "sum")).to_string(), fh)
