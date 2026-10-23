"""Spot check of the building classes against an official list: District of Summerland Prohibit Entry Order of
2026-09-29 (raw/calib/summerland_20260929_prohibit_entry_order.pdf, 29 property entries where post-wildfire hazards
kept entry prohibited). Addresses geocoded with the Province of BC Address Geocoder (geocoder.api.gov.bc.ca, keyless,
official). For each address, the nearest classified building within 60 m is taken. The list is not a count of
destroyed buildings (entry is prohibited for hazard reasons), so this is a plausibility check, not a calibration."""
import os, re, subprocess
import pandas as pd, geopandas as gpd, requests

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(L, "raw", "calib")
txt = os.path.join(R, "peo.txt")
if not os.path.exists(txt):
    subprocess.run(["pdftotext", "-layout", os.path.join(R, "summerland_20260929_prohibit_entry_order.pdf"), txt], check=True)
addr = re.findall(r"•\s+([\d/]+ [A-Z][A-Za-z ]+?(?:Street|Avenue|Road))", open(txt).read())
print(len(addr), "addresses")
rows = []
for a in addr:
    first = a.split("/")[0] + a[a.index(" "):] if "/" in a else a
    q = f"{first}, Summerland, BC"
    r = requests.get("https://geocoder.api.gov.bc.ca/addresses.json", params={"addressString": q, "maxResults": 1, "outputSRS": 4326}, timeout=60).json()
    f = r["features"][0]
    rows.append(dict(address=a, query=q, lon=f["geometry"]["coordinates"][0], lat=f["geometry"]["coordinates"][1],
                     score=f["properties"].get("score"), precision=f["properties"].get("matchPrecision")))
g = gpd.GeoDataFrame(rows, geometry=gpd.points_from_xy([r["lon"] for r in rows], [r["lat"] for r in rows]), crs=4326).to_crs(3978)
d = pd.read_csv(os.path.join(L, "dnbr_buildings.csv")).query("fire_uid == 36076584")
bg = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.x, d.y), crs=3978)
j = gpd.sjoin_nearest(g, bg[["building_class", "dnbr_building_max", "dnbr_ring_median", "geometry"]], how="left", max_distance=60, distance_col="dist_m")
j = j[~j.index.duplicated()]
j.drop(columns="geometry").to_csv(os.path.join(L, "summerland_prohibit_entry_check.csv"), index=False)
print(j[["address", "score", "precision", "building_class", "dnbr_building_max", "dnbr_ring_median", "dist_m"]].to_string())
print(j.building_class.fillna("no building within 60 m").value_counts().to_string())
