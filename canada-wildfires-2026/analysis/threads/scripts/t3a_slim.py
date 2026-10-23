"""Stream CSV members of a CWFIS hotspot archive zip, keep lat, lon, rep_date, sensor, source (and satellite/agency
when present) for points in a Canada bounding box (lat 41-84, lon -142 to -52). Writes gzip CSV."""
import sys, zipfile, io
import pandas as pd

zf, out = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(zf)
first = True
n_in = n_out = 0
with open(out, "wb") as fo:
    import gzip
    gz = gzip.GzipFile(fileobj=fo, mode="wb")
    for m in z.namelist():
        if not m.lower().endswith((".csv", ".txt")):
            print("skip member", m)
            continue
        for ch in pd.read_csv(z.open(m), chunksize=500_000, low_memory=False):
            ch.columns = [c.strip().lower() for c in ch.columns]
            n_in += len(ch)
            keep = [c for c in ["lat", "lon", "rep_date", "sensor", "source", "satellite", "agency", "frp"] if c in ch.columns]
            ch = ch[keep]
            ch = ch[ch.lat.between(41, 84) & ch.lon.between(-142, -52)]
            n_out += len(ch)
            gz.write(ch.to_csv(index=False, header=first).encode())
            first = False
        print(m, "cols", keep, flush=True)
    gz.close()
print(zf, "rows in", n_in, "kept", n_out)
