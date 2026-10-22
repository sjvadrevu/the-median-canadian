"""Page through an ArcGIS REST layer and write GeoJSON/GPKG.
usage: arcgis_dl.py LAYER_URL OUT_PATH [--where W] [--fields F] [--outsr 4326] [--chunk N] [--nogeom] [--offset-tol T]
Pages by OBJECTID ranges (robust to servers without pagination)."""
import sys, json, time, argparse, requests, geopandas as gpd, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("url"); ap.add_argument("out")
ap.add_argument("--where", default="1=1"); ap.add_argument("--fields", default="*")
ap.add_argument("--outsr", default="4326"); ap.add_argument("--chunk", type=int, default=1000)
ap.add_argument("--nogeom", action="store_true"); ap.add_argument("--tol", default=None)
ap.add_argument("--layer", default=None)
a = ap.parse_args()
import os
H = {"User-Agent": os.environ["UA"]} if os.environ.get("UA") else {}
S = requests.Session()

def get(url, params, tries=6):
    for i in range(tries):
        try:
            r = S.get(url, params=params, headers=H, timeout=300)
            if r.status_code == 200:
                j = r.json()
                if "error" not in j:
                    return j
                print("err", j["error"], file=sys.stderr)
            else:
                print("http", r.status_code, file=sys.stderr)
        except Exception as e:
            print("exc", repr(e)[:200], file=sys.stderr)
        time.sleep(3 * (i + 1))
    raise SystemExit("failed " + url)

meta = get(a.url, {"f": "json"})
oidf = meta.get("objectIdField") or next(f["name"] for f in meta["fields"] if f["type"] == "esriFieldTypeOID")
ids = get(a.url + "/query", {"where": a.where, "returnIdsOnly": "true", "f": "json"})["objectIds"] or []
ids.sort(); print("records", len(ids), file=sys.stderr)
frames = []
for k in range(0, len(ids), a.chunk):
    lo, hi = ids[k], ids[min(k + a.chunk, len(ids)) - 1]
    p = {"where": f"({a.where}) AND {oidf}>={lo} AND {oidf}<={hi}", "outFields": a.fields,
         "returnGeometry": "false" if a.nogeom else "true", "outSR": a.outsr, "f": "geojson"}
    if a.tol: p["maxAllowableOffset"] = a.tol
    j = get(a.url + "/query", p)
    if a.nogeom:
        frames.append(pd.DataFrame([f["properties"] for f in j["features"]]))
    else:
        frames.append(gpd.GeoDataFrame.from_features(j["features"], crs=f"EPSG:{a.outsr}"))
    print(f"{k + len(j['features'])}/{len(ids)}", file=sys.stderr)
df = pd.concat(frames, ignore_index=True)
if a.nogeom:
    df.to_csv(a.out, index=False)
else:
    df = gpd.GeoDataFrame(df, crs=f"EPSG:{a.outsr}")
    if a.out.endswith(".gpkg"):
        df.to_file(a.out, layer=a.layer or "data", driver="GPKG")
    else:
        df.to_file(a.out, driver="GeoJSON")
print("wrote", a.out, len(df), file=sys.stderr)
