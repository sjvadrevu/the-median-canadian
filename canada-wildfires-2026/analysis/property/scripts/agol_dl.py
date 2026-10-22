"""Download all features of an ArcGIS FeatureServer layer to GeoJSON (EPSG:4326), paging by objectIds.
usage: python agol_dl.py <layer_url> <out.geojson>"""
import requests, json, sys, os
url, out = sys.argv[1].rstrip("/"), sys.argv[2]
meta = requests.get(url, params={"f": "json"}, timeout=120).json()
ids = requests.get(url + "/query", params={"where": "1=1", "returnIdsOnly": "true", "f": "json"}, timeout=120).json()
oid, ids = ids["objectIdFieldName"], sorted(ids["objectIds"] or [])
step = min(int(meta.get("maxRecordCount", 1000) or 1000), 1000)
feats = []
for i in range(0, len(ids), step):
    chunk = ids[i:i + step]
    r = requests.post(url + "/query", data={"objectIds": ",".join(map(str, chunk)), "outFields": "*", "outSR": 4326,
                                             "f": "geojson", "returnGeometry": "true"}, timeout=300).json()
    feats += r["features"]
json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w"))
json.dump(meta, open(out.replace(".geojson", "_layer_meta.json"), "w"))
print(out, len(feats), "of", len(ids))
