"""Per-year (2016-2026) and 2023-2026 road, rail and power-line length inside and within about 1 km of burned area,
on the 240 m grid, so every year is measured the same way.

Lines (NRN roads by ROADCLASS, NRWN rail tracks, CanVec power lines; same sources as 05_infra.py) are cut into
pieces of at most 30 m in the grid projection (EPSG:3979); each piece is assigned to the 240 m cell holding its
midpoint, with length divided by the projection's linear scale factor (sqrt of areal scale) to give ground length.
Only cells within 5 cells of any 2016-2026 burned cell are kept.
"Inside": cell burned that year (cell-centre rule, NBAC 2016-2025, M3 2026).
"Within ~1 km": burned cells dilated by a disc of radius 1,000 m (cells whose centre lies within 1,000 m of a burned
cell centre). This raster method is checked against the exact 2026 vector clip from 05_infra.py.
Outputs: infra_by_year.csv (kind x class x year x province: km inside, km within ~1 km), work/infra_cellkm_*.npz
"""
import os
import sys
import subprocess
import zipfile
import numpy as np
import pandas as pd
import pyogrio
import shapely
from pyproj import CRS
from ecommon import WORK, OUT, RAW, FWORK, FMA_ATTR
from grid import meta, load

m = meta()
H, W = m["H"], m["W"]
X0, Y0 = m["transform"][2], m["transform"][5]
GRID_CRS = CRS.from_wkt(m["crs"])
asc = load("areal_scale_coarse", mmap=False)
YEARS = list(range(2016, 2027))
burn = {y: np.load(FWORK / f"burn_{y}.npy").astype(np.int64) for y in YEARS}

# disc offsets for ~1 km dilation and the 5-cell zone
def offsets(rad):
    r = int(np.ceil(rad))
    return [(dr, dc) for dr in range(-r, r + 1) for dc in range(-r, r + 1) if dr * dr + dc * dc <= rad * rad]


def dilate(idx, offs):
    """Cells whose centre is within the disc (given as offsets) of any cell in idx; boolean grid dilation
    on the bounding box of idx (scipy.ndimage)."""
    from scipy import ndimage
    r = int(max(abs(dr) for dr, _ in offs))
    rr, cc = idx // W, idx % W
    r0, r1 = max(rr.min() - r, 0), min(rr.max() + r + 1, H)
    c0, c1 = max(cc.min() - r, 0), min(cc.max() + r + 1, W)
    a = np.zeros((r1 - r0, c1 - c0), bool)
    a[rr - r0, cc - c0] = True
    st = np.zeros((2 * r + 1, 2 * r + 1), bool)
    for dr, dc in offs:
        st[dr + r, dc + r] = True
    a = ndimage.binary_dilation(a, structure=st)
    ii, jj = np.nonzero(a)
    return ((ii + r0).astype(np.int64) * W + (jj + c0)).astype(np.int64)


OFF1K = offsets(1000 / 240)
zone_f = WORK / "infra_zone.npy"
if zone_f.exists():
    zone = np.load(zone_f)
else:
    allb = np.unique(np.concatenate(list(burn.values())))
    zone = dilate(allb, offsets(5))
    np.save(zone_f, zone)
print("zone cells", zone.size, flush=True)


def lines_to_cells(geoms):
    """geoms in grid CRS -> (cell idx, ground km) for pieces whose midpoint is in the zone."""
    geoms = shapely.segmentize(np.asarray(geoms), 30.0)
    parts = shapely.get_parts(shapely.get_parts(geoms))
    coords, li = shapely.get_coordinates(parts, return_index=True)
    same = li[1:] == li[:-1]
    a, b = coords[:-1][same], coords[1:][same]
    mid = (a + b) / 2
    seg = np.hypot(*(b - a).T)
    col = np.floor((mid[:, 0] - X0) / 240).astype(np.int64)
    row = np.floor((Y0 - mid[:, 1]) / 240).astype(np.int64)
    ok = (row >= 0) & (row < H) & (col >= 0) & (col < W)
    idx = row[ok] * W + col[ok]
    seg = seg[ok]
    k = np.sqrt(asc[np.minimum(row[ok] // m["step"], asc.shape[0] - 1), np.minimum(col[ok] // m["step"], asc.shape[1] - 1)])
    pos = np.searchsorted(zone, idx)
    inz = (pos < zone.size) & (zone[np.minimum(pos, zone.size - 1)] == idx)
    return idx[inz], seg[inz] / k[inz] / 1000.0


def accumulate(path, layer, classcol, kind, prov, chunk=200000):
    info = pyogrio.read_info(path, layer=layer)
    n = info["features"]
    acc = {}
    cols = [c for c in info["fields"] if c.upper() == (classcol or "").upper()]
    for s in range(0, n, chunk):
        df = pyogrio.read_dataframe(path, layer=layer, columns=cols, skip_features=s, max_features=chunk)
        df = df.to_crs(GRID_CRS)
        cls = df[cols[0]].astype(str).values if cols else np.array(["all"] * len(df))
        for c in np.unique(cls):
            ii, km = lines_to_cells(df.geometry.values[cls == c])
            if ii.size:
                acc.setdefault(c, []).append((ii, km))
    out = {}
    for c, lst in acc.items():
        ii = np.concatenate([x[0] for x in lst]); km = np.concatenate([x[1] for x in lst])
        u, inv = np.unique(ii, return_inverse=True)
        out[c] = (u, np.bincount(inv, weights=km))
    np.savez(WORK / f"infra_cellkm_{kind}_{prov}.npz",
             **{f"{c}__idx": v[0] for c, v in out.items()}, **{f"{c}__km": v[1] for c, v in out.items()})
    print(kind, prov, n, "features", {c: round(v[1].sum(), 1) for c, v in out.items()}, flush=True)


def fetch(url, dest):
    for i in range(4):
        r = subprocess.run(["curl", "-sS", "-L", "-m", "1800", "-o", str(dest), url])
        if r.returncode == 0 and dest.exists() and dest.stat().st_size > 1000:
            return True
    return False


tmp = RAW / "tmp_infra"
tmp.mkdir(exist_ok=True)
provs = ["bc", "ab", "sk", "mb", "on", "qc", "nb", "ns", "nl", "yt", "nt", "nu"]
todo = sys.argv[1:] or ["power", "rail", "roads", "summarise"]
if "power" in todo and not (WORK / "infra_cellkm_power_line_CA.npz").exists():
    z = RAW / "canvec" / "canvec_50K_CA_Res_MGT_fgdb.zip"
    accumulate(f"/vsizip/{z}/canvec_50K_CA_Res_MGT.gdb", "power_line_1", None, "power_line", "CA")
if "rail" in todo:
    for p in provs:
        if (WORK / f"infra_cellkm_rail_{p.upper()}.npz").exists():
            continue
        z = tmp / f"nrwn_{p}.zip"
        if not fetch(f"https://ftp.maps.canada.ca/pub/nrcan_rncan/vector/geobase_nrwn_rfn/{p}/nrwn_rfn_{p}_shp_en.zip", z):
            continue
        shp = [n for n in zipfile.ZipFile(z).namelist() if n.upper().endswith("TRACK.SHP")]
        if shp:
            path = f"/vsizip/{z}/{shp[0]}"
            accumulate(path, pyogrio.list_layers(path)[0][0], "TRACKCLASS", "rail", p.upper())
        os.remove(z)
if "roads" in todo:
    for p in provs:
        if (WORK / f"infra_cellkm_road_{p.upper()}.npz").exists():
            continue
        z = tmp / f"nrn_{p}.zip"
        if not fetch(f"https://geo.statcan.gc.ca/nrn_rrn/{p}/nrn_rrn_{p}_GPKG.zip", z):
            print("download failed", p)
            continue
        gp = [n for n in zipfile.ZipFile(z).namelist() if n.lower().endswith(".gpkg") and n.upper().startswith("NRN")][0]
        path = f"/vsizip/{z}/{gp}"
        lyr = [l for l, _ in pyogrio.list_layers(path) if l.upper().endswith("ROADSEG")][0]
        accumulate(path, lyr, "ROADCLASS", "road", p.upper())
        os.remove(z)

if "summarise" in todo:
    fid = load("fma_id")
    attr = pd.read_csv(FMA_ATTR)
    provmap = dict(zip(attr.fma_id, attr.province))
    sets = {}
    for y in YEARS:
        sets[(y, "inside")] = burn[y]
        sets[(y, "within_1km")] = dilate(burn[y], OFF1K)
    u = np.unique(np.concatenate([burn[y] for y in range(2023, 2027)]))
    sets[("2023_2026", "inside")] = u
    sets[("2023_2026", "within_1km")] = dilate(u, OFF1K)
    # membership of each set as a boolean over the zone cells (every line piece lies in the zone)
    inset = {k: np.isin(zone, v) for k, v in sets.items()}
    zpr = pd.Series(fid.ravel()[zone]).map(provmap).fillna("outside").values
    rows = []
    for f in sorted(WORK.glob("infra_cellkm_*.npz")):
        kind = "power_line" if "power_line" in f.stem else f.stem.split("_")[2]
        z = np.load(f)
        for key in [k for k in z.files if k.endswith("__idx")]:
            c = key[:-5]
            ii, km = z[key], z[c + "__km"]
            zp = np.searchsorted(zone, ii)
            pr = zpr[zp]
            for (y, band), msk in inset.items():
                hit = msk[zp]
                if not hit.any():
                    continue
                s_ = pd.Series(km[hit]).groupby(pr[hit]).sum()
                for p, v in s_.items():
                    rows.append(dict(kind=kind, source_file=f.stem, cls=c, year=y, band=band, prov=p, km=v))
    r = pd.DataFrame(rows)
    r = r.groupby(["kind", "cls", "year", "band", "prov"], as_index=False).km.sum()
    r.to_csv(OUT / "infra_by_year.csv", index=False)
    t = r.groupby(["kind", "year", "band"]).km.sum().unstack("band")
    print(t.to_string())
