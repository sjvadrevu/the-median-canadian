"""Road vertices for distance-to-road: StatCan National Road Network (NRN), all ROADSEG classes, one province at a time.
Each zip is downloaded to raw/nrn/, lines are densified to <=200 m in Canada Albers (ESRI:102001), vertices saved
as work/roadpts_<pt>.npz (x, y, class code), and the zip is deleted (disk is short).
Source: https://geo.statcan.gc.ca/nrn_rrn/<pt>/nrn_rrn_<pt>_GPKG.zip  (Open Government Licence - Canada)
"""
import subprocess, sys, zipfile, os
import numpy as np, pyogrio, shapely
from pyproj import Transformer
from common import RAW, WORK, EA

provs = sys.argv[1:] or ["pe", "ns", "nb", "nl", "yt", "nt", "nu", "mb", "sk", "ab", "qc", "bc", "on"]
for p in provs:
    out = WORK / f"roadpts_{p}.npz"
    if out.exists():
        continue
    url = f"https://geo.statcan.gc.ca/nrn_rrn/{p}/nrn_rrn_{p}_GPKG.zip"
    z = RAW / "nrn" / f"nrn_{p}.zip"
    ok = False
    for _ in range(0 if (z.exists() and zipfile.is_zipfile(z)) else 4):
        r = subprocess.run(["curl", "-sS", "-L", "-m", "3600", "-o", str(z), url])
        if r.returncode == 0 and z.exists() and zipfile.is_zipfile(z):
            ok = True
            break
    if not ok and not (z.exists() and zipfile.is_zipfile(z)):
        print(p, "download failed", flush=True)
        continue
    names = zipfile.ZipFile(z).namelist()
    gp = [n for n in names if n.lower().endswith(".gpkg") and n.upper().startswith("NRN")][0]
    path = f"/vsizip/{z}/{gp}"
    lyr = [l for l, _ in pyogrio.list_layers(path) if l.upper().endswith("ROADSEG")][0]
    info = pyogrio.read_info(path, layer=lyr)
    fld = [f for f in info["fields"] if f.upper() == "ROADCLASS"]
    df = pyogrio.read_dataframe(path, layer=lyr, columns=fld)
    df = df.to_crs(EA)
    cls = df[fld[0]].astype(str).values if fld else np.array(["?"] * len(df))
    g = shapely.segmentize(df.geometry.values, 200.0)
    coords, idx = shapely.get_coordinates(g, return_index=True)
    classes, code = np.unique(cls, return_inverse=True)
    np.savez_compressed(out, x=coords[:, 0].astype("float32"), y=coords[:, 1].astype("float32"),
                        c=code[idx].astype("int16"), classes=classes, n_seg=len(df), url=url, layer=lyr)
    print(p, lyr, len(df), "segments", len(coords), "vertices", flush=True)
    os.remove(z)
print("done")
