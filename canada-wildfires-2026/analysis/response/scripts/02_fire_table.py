"""One agency fire-point table, 1990-2026, with the agency's own response label, zone label, geographic province
and distance from the fire's reported origin to the nearest NRN road.

Sources
  * CNFDB points (NFDB_point_20260811), years 1990-2025, prescribed burns removed (PRESCRIBED PB/1, CAUSE2 H-PB,
    ON FIRE_TYPE PB, PC "Prescribed Fire"/"Prescribed Burn").
    RESPONSE field (agency response category): BC, MB, NT, ON, PC, NS, PE and a few QC 2025 records.
    PROTZONE field (agency protection zone of the fire): QC (Intensive / Nordique), YT (fire management zone), MB.
  * 2026 agency fire list (CWFIS/CWFIF national fire list, 13 agencies, as of 2026-10-20), response_type field.
    Same rules as analysis/cause/03_fires.py: calendar-2026 report date; NT dates = GNWT discovery date.
Response class (resp):
  full      agency response full / suppression (FUL, SUP, Actioned, full_response)
  modified  MOD, MDP, Limited Action, modified_response
  monitored MON, MNP, No Action, monitored_response
  zone_full / zone_obs   no fire-level response, classified by the agency's protection zone on the record:
            QC Intensive -> zone_full, QC Nordique -> zone_obs; YT Critical/Full -> zone_full,
            YT Strategic/Transitional/Wilderness -> zone_obs
  unclassified  nothing on the record (AB, SK, NL, NB 1990-2025; most agencies before the 2000s)
Output: work/fires.pkl, work/log_02.txt
"""
import json
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from common import CNFDB_ZIP, CNFDB_MEMBER, FIRE_LIST_2026, NT_POINTS_2026, PROV_POLY, WORK, EA

fh = open(WORK / "log_02.txt", "w")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    fh.write(s + "\n"); fh.flush()


CK = WORK / "fires_noroad.pkl"
if CK.exists():
    F = pd.read_pickle(CK)
    pts = gpd.GeoDataFrame(F[["fire_id"]], geometry=gpd.points_from_xy(F.lon, F.lat), crs=4326).to_crs(EA)
else:
    # ---------------------------------------------------------------- CNFDB
    c = pd.read_csv(zipfile.ZipFile(CNFDB_ZIP).open(CNFDB_MEMBER), low_memory=False)
    c = c[(c.YEAR >= 1990) & (c.YEAR <= 2025)].copy()
    for k in ["RESPONSE", "PROTZONE", "FIRE_TYPE", "PRESCRIBED", "CAUSE2"]:
        c[k] = c[k].astype(str).str.strip().replace({"nan": ""})
    pb = (c.PRESCRIBED.isin(["PB", "1"]) | (c.CAUSE2 == "H-PB") | ((c.SRC_AGENCY == "ON") & (c.FIRE_TYPE == "PB"))
          | c.PROTZONE.str.startswith("Prescribed") | c.FIRE_TYPE.str.startswith("Prescribed"))
    log(f"CNFDB 1990-2025 points {len(c)}, prescribed removed {int(pb.sum())}")
    c = c[~pb].copy()
    RMAP = {"FUL": "full", "SUP": "full", "Actioned": "full", "MOD": "modified", "MDP": "modified",
            "Limited Action": "modified", "MON": "monitored", "MNP": "monitored", "No Action": "monitored"}
    resp = c.RESPONSE.map(RMAP)
    pz = c.PROTZONE.str.lower()
    zone = pd.Series(np.nan, index=c.index, dtype=object)
    qc = c.SRC_AGENCY == "QC"
    zone[qc & pz.eq("intensive")] = "zone_full"
    zone[qc & pz.eq("nordique")] = "zone_obs"
    yt = c.SRC_AGENCY == "YT"
    zone[yt & pz.str.contains("critical|full")] = "zone_full"
    zone[yt & pz.str.contains("strat|transi|wilder")] = "zone_obs"
    c["resp"] = resp.fillna(zone).fillna("unclassified")
    d1 = pd.to_datetime(c.REP_DATE, errors="coerce")
    d2 = pd.to_datetime(dict(year=c.YEAR, month=c.MONTH.clip(1, 12), day=c.DAY.clip(1, 31)), errors="coerce")
    d2[(c.MONTH < 1) | (c.DAY < 1)] = pd.NaT
    rep = d1.where(d1.notna() & (d1.dt.year == c.YEAR), d2)
    cn = pd.DataFrame(dict(
        fire_id=c.NFDBFIREID.astype(str), source="CNFDB", agency=c.SRC_AGENCY, year=c.YEAR.astype(int),
        rep_date=rep, attk_date=pd.to_datetime(c.ATTK_DATE, errors="coerce"), size_ha=c.SIZE_HA.clip(lower=0),
        lat=c.LATITUDE, lon=c.LONGITUDE, cause=c.CAUSE.map({"N": "lightning", "H": "human"}).fillna("undetermined"),
        resp=c.resp, resp_raw=c.RESPONSE, protzone_raw=c.PROTZONE))

    # ---------------------------------------------------------------- 2026 list
    L = pd.DataFrame(json.load(open(FIRE_LIST_2026)))
    L["srd"] = pd.to_datetime(L.situation_report_date)
    L = L[L.srd.dt.year == 2026].copy()
    nt = pd.DataFrame(json.load(open(NT_POINTS_2026)))
    nt_d = pd.to_datetime(nt.set_index("title").discoverydate, errors="coerce")
    isnt = L.agency_code == "NT"
    L.loc[isnt, "srd"] = L.loc[isnt, "agency_fire_id"].map(nt_d)
    log(f"2026 list: {len(L)} fires, {L.fire_size.sum():,.1f} ha; prescribed flagged {int(L.fire_was_prescribed.sum())}")
    l26 = pd.DataFrame(dict(
        fire_id=L.national_fire_id, source="LIST2026", agency=L.agency_code, year=2026,
        rep_date=L.srd.dt.tz_localize(None), attk_date=pd.NaT, size_ha=L.fire_size.clip(lower=0),
        lat=L.latitude, lon=L.longitude,
        cause=L.national_fire_cause.map({"natural": "lightning", "human": "human"}).fillna("undetermined"),
        resp=L.response_type.map({"full_response": "full", "modified_response": "modified",
                                  "monitored_response": "monitored"}).fillna("unclassified"),
        resp_raw=L.response_type, protzone_raw=""))
    F = pd.concat([cn, l26], ignore_index=True)
    F = F[np.isfinite(F.lat) & np.isfinite(F.lon)].reset_index(drop=True)

    # ---------------------------------------------------------------- geographic province
    pts = gpd.GeoDataFrame(F[["fire_id"]], geometry=gpd.points_from_xy(F.lon, F.lat), crs=4326).to_crs(EA)
    pr = gpd.read_file(PROV_POLY)[["PREABBR", "geometry"]].to_crs(EA)
    ab = {"N.L.": "NL", "P.E.I.": "PE", "N.S.": "NS", "N.B.": "NB", "Que.": "QC", "Ont.": "ON", "Man.": "MB",
          "Sask.": "SK", "Alta.": "AB", "B.C.": "BC", "Y.T.": "YT", "N.W.T.": "NT", "Nvt.": "NU"}
    pr["prov"] = pr.PREABBR.map(ab)
    pr["geometry"] = pr.geometry.simplify(500)
    j = gpd.sjoin(pts, pr[["prov", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    F["prov"] = j.prov.reindex(F.index).values
    miss = F.prov.isna()
    if miss.any():   # coast / border points: nearest province within 50 km
        jn = gpd.sjoin_nearest(pts[miss.values], pr[["prov", "geometry"]], how="left", max_distance=50000)
        jn = jn[~jn.index.duplicated()]
        F.loc[miss, "prov"] = jn.prov.reindex(F.index[miss]).values
    log("province polygons: within", int((~miss).sum()), "nearest", int(miss.sum()))
    F["prov"] = F.prov.fillna(F.agency.where(F.agency != "PC"))
    log("province from geography; agency==prov for non-PC:",
        round(float((F.agency[F.agency != "PC"] == F.prov[F.agency != "PC"]).mean()), 4))

    F.to_pickle(CK)

# ---------------------------------------------------------------- distance to nearest NRN road
xs, ys, cls = [], [], []
classes_all = []
for p in ["pe", "ns", "nb", "nl", "yt", "nt", "nu", "mb", "sk", "ab", "qc", "bc", "on"]:
    z = np.load(WORK / f"roadpts_{p}.npz", allow_pickle=True)
    xs.append(z["x"]); ys.append(z["y"])
    names = z["classes"][z["c"]]
    cls.append(names)
X = np.concatenate(xs).astype("float64"); Y = np.concatenate(ys).astype("float64"); C = np.concatenate(cls)
ok = np.isfinite(X) & np.isfinite(Y)
X, Y, C = X[ok], Y[ok], C[ok]
log(f"road vertices: {len(X):,}; classes: {sorted(set(C))}")
P = np.c_[pts.geometry.x.values, pts.geometry.y.values]
t = cKDTree(np.c_[X, Y])
good = np.isfinite(P).all(1)
F["road_km"] = np.nan
F.loc[good, "road_km"] = t.query(P[good])[0] / 1000
nw = C != "Winter"
t2 = cKDTree(np.c_[X[nw], Y[nw]])
F["road_km_no_winter"] = np.nan
F.loc[good, "road_km_no_winter"] = t2.query(P[good])[0] / 1000
log("points without finite projected coordinates:", int((~good).sum()))
F.to_pickle(WORK / "fires.pkl")
log(F.groupby(["source", "resp"]).size_ha.agg(["size", "sum"]).round(0).to_string())
log(F[F.year >= 2023].groupby(["year", "prov"]).size_ha.sum().unstack(0).round(0).to_string())
