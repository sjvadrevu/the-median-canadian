"""Roads, railways and power lines inside, or within 1 km of, the 2026 CWFIS M3 fire outlines.

Sources (downloaded one province at a time, clipped, then deleted to save disk):
  Roads:  National Road Network (NRN), Statistics Canada GeoBase series, GPKG per province/territory,
          https://geo.statcan.gc.ca/nrn_rrn/<pt>/nrn_rrn_<pt>_GPKG.zip (files dated 2026-06-26), layer ROADSEG.
  Rail:   National Railway Network (NRWN), NRCan GeoBase, https://ftp.maps.canada.ca/pub/nrcan_rncan/vector/
          geobase_nrwn_rfn/<pt>/nrwn_rfn_<pt>_shp_en.zip (2019 release), TRACK layer.
  Power:  CanVec 1:50K Resource management, power_line_1 (national), raw/canvec/canvec_50K_CA_Res_MGT_fgdb.zip.
Fire: CWFIS M3 2026 outlines (718), dissolved in ESRI:102001; "within 1 km" = 1,000 m planar buffer in
Albers equal area. Lengths are geodesic (GRS80) after clipping, so they are true ground lengths.
Lengths are mapped (outline based, not scaled): outlines are about 18% larger than the official area.
Outputs: work/infra_segments_2026.gpkg (clipped lines), infra_2026_by_type.csv, infra_2026_by_province.csv.
"""
import os
import sys
import zipfile
import subprocess
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
from pyproj import Geod
from shapely import make_valid
from shapely.ops import unary_union
from ecommon import M3, EA, RAW, WORK, OUT

geod = Geod(ellps="GRS80")
fires = gpd.read_file(M3).to_crs(EA)
fires["geometry"] = [make_valid(g) for g in fires.geometry]
inside = unary_union(fires.geometry.values)
buf = inside.buffer(1000)
fire_prov = fires.groupby("prov").geometry.apply(lambda s: unary_union(s.values).buffer(1000))
print("fire area ha", inside.area / 1e4, "buffer ha", buf.area / 1e4, flush=True)


def glen(gs):
    g = gpd.GeoSeries(gs, crs=EA).to_crs(4326)
    return np.array([geod.geometry_length(x) if x is not None and not x.is_empty else 0.0 for x in g]) / 1000.0


def clip_lengths(df, kind, prov, cols):
    df = df.to_crs(EA)
    df = df[df.intersects(buf)]
    if df.empty:
        return pd.DataFrame(), None
    g_in = df.geometry.intersection(inside)
    g_buf = df.geometry.intersection(buf)
    df = df.assign(km_inside=glen(g_in.values), km_within_1km=glen(g_buf.values))
    seg = gpd.GeoDataFrame(df[cols + ["km_inside", "km_within_1km"]], geometry=g_buf.values, crs=EA)
    seg["kind"] = kind
    seg["file_prov"] = prov
    return seg, seg


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    for i in range(4):
        r = subprocess.run(["curl", "-sS", "-L", "-m", "1800", "-o", str(dest), url])
        if r.returncode == 0 and dest.exists() and dest.stat().st_size > 1000:
            return True
    return False


tmp = RAW / "tmp_infra"
tmp.mkdir(exist_ok=True)
segs = []
log = []
mask4617 = gpd.GeoSeries([buf], crs=EA).to_crs(4617).iloc[0].simplify(0.001)
provs = ["bc", "ab", "sk", "mb", "on", "qc", "nb", "ns", "nl", "yt", "nt", "nu"]
only = sys.argv[1:] or ["roads", "rail", "power"]

if "roads" in only:
    for p in provs:
        url = f"https://geo.statcan.gc.ca/nrn_rrn/{p}/nrn_rrn_{p}_GPKG.zip"
        z = tmp / f"nrn_vec_{p}.zip"   # distinct from 05b temp names
        cache = WORK / f"road_seg_{p}.pkl"
        if cache.exists():   # province already clipped in an earlier run
            seg, lg = pd.read_pickle(cache)
            if len(seg):
                segs.append(seg)
            log.append(lg)
            continue
        if not fetch(url, z):
            log.append(dict(kind="road", prov=p, url=url, status="download failed"))
            continue
        names = zipfile.ZipFile(z).namelist()
        gp = [n for n in names if n.lower().endswith(".gpkg") and n.upper().startswith("NRN")][0]
        path = f"/vsizip/{z}/{gp}"
        lyr = [l for l, _ in pyogrio.list_layers(path) if l.upper().endswith("ROADSEG")][0]
        info = pyogrio.read_info(path, layer=lyr)
        m = gpd.GeoSeries([buf], crs=EA).to_crs(info["crs"]).iloc[0].simplify(0.001)
        want = {"ROADCLASS", "PAVSTATUS", "RTNUMBER1", "ROADJURIS"}
        cols = [f for f in info["fields"] if f.upper() in want]
        df = pyogrio.read_dataframe(path, layer=lyr, mask=m, columns=cols)
        df.columns = [c.upper() if c != "geometry" else c for c in df.columns]
        seg, _ = clip_lengths(df, "road", p.upper(), sorted(c.upper() for c in cols))
        if len(seg):
            segs.append(seg)
        log.append(dict(kind="road", prov=p, url=url, layer=lyr, crs=str(info["crs"]), n_features_layer=info["features"],
                        n_read=len(df), n_kept=len(seg), status="ok"))
        print(log[-1], flush=True)
        pd.to_pickle((seg, log[-1]), cache)
        os.remove(z)

if "rail" in only:
    for p in provs:
        url = f"https://ftp.maps.canada.ca/pub/nrcan_rncan/vector/geobase_nrwn_rfn/{p}/nrwn_rfn_{p}_shp_en.zip"
        z = tmp / f"nrwn_vec_{p}.zip"
        if not fetch(url, z):
            log.append(dict(kind="rail", prov=p, url=url, status="download failed (no file for this province?)"))
            print(log[-1], flush=True)
            continue
        names = zipfile.ZipFile(z).namelist()
        shp = [n for n in names if n.upper().endswith("TRACK.SHP")]
        if not shp:
            log.append(dict(kind="rail", prov=p, url=url, status="no TRACK layer", files=";".join(names)))
            continue
        path = f"/vsizip/{z}/{shp[0]}"
        info = pyogrio.read_info(path)
        m = gpd.GeoSeries([buf], crs=EA).to_crs(info["crs"]).iloc[0].simplify(0.001)
        cols = [c for c in ["TRACKCLASS", "TRACKNAME", "OPERATOR1", "TRACKSEG"] if c in info["fields"]]
        df = pyogrio.read_dataframe(path, mask=m, columns=cols)
        seg, _ = clip_lengths(df, "rail", p.upper(), cols)
        if len(seg):
            segs.append(seg)
        log.append(dict(kind="rail", prov=p, url=url, layer=shp[0], crs=str(info["crs"]), n_features_layer=info["features"],
                        n_read=len(df), n_kept=len(seg), status="ok"))
        print(log[-1], flush=True)
        os.remove(z)

if "power" in only:
    z = RAW / "canvec" / "canvec_50K_CA_Res_MGT_fgdb.zip"
    path = f"/vsizip/{z}/canvec_50K_CA_Res_MGT.gdb"
    info = pyogrio.read_info(path, layer="power_line_1")
    m = gpd.GeoSeries([buf], crs=EA).to_crs(info["crs"]).iloc[0].simplify(0.001)
    df = pyogrio.read_dataframe(path, layer="power_line_1", mask=m,
                                columns=["feature_id", "line_location", "number_of_lines"])
    seg, _ = clip_lengths(df, "power_line", "CA", ["feature_id", "line_location", "number_of_lines"])
    if len(seg):
        segs.append(seg)
    log.append(dict(kind="power_line", prov="CA", url="canvec_50K_CA_Res_MGT_fgdb.zip", layer="power_line_1",
                    crs=str(info["crs"]), n_features_layer=info["features"], n_read=len(df), n_kept=len(seg), status="ok"))
    print(log[-1], flush=True)

tag = "_".join(only)
pd.DataFrame(log).to_csv(WORK / f"infra_log_{tag}.csv", index=False)
if segs:
    allseg = pd.concat(segs, ignore_index=True)
    # province of the segment: the fire-province buffer it falls in (M3 'prov'), by largest overlap
    allseg = gpd.GeoDataFrame(allseg, geometry="geometry", crs=EA)
    rp = allseg.representative_point()
    fp = gpd.GeoDataFrame({"fire_prov": fire_prov.index}, geometry=fire_prov.values, crs=EA)
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=rp, crs=EA), fp, how="left", predicate="within")
    allseg["fire_prov"] = j.groupby(level=0).fire_prov.first().reindex(allseg.index).values
    allseg.to_file(WORK / f"infra_segments_2026_{tag}.gpkg", driver="GPKG")
    allseg.drop(columns="geometry").to_csv(WORK / f"infra_segments_2026_{tag}.csv", index=False)
print("done")
