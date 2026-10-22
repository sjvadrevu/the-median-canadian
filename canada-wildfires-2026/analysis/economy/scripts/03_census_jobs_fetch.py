"""Fetch 2021 Census employed labour force by industry for Canada, provinces/territories and all 293 census
divisions from Statistics Canada table 98-10-0592-01 via the Web Data Service (WDS).

Coordinates: Geography x Statistic=Count(1) x Labour force status=Employed(2) x Age=Total(1) x Gender=Total(1)
x Industry (members below) x Class of worker=Total(1).
Output: raw/statcan/t9810059201_employed_by_industry_cd.csv (one row per geography x industry).
"""
import json
import time
import requests
import pandas as pd
from ecommon import RAW

PID = 98100592
IND = {1: "Total - Industry", 3: "All industries", 4: "11 Agriculture, forestry, fishing and hunting",
       9: "113 Forestry and logging", 18: "1153 Support activities for forestry", 77: "321 Wood product manufacturing",
       81: "322 Paper manufacturing", 389: "72 Accommodation and food services", 390: "721 Accommodation services",
       391: "7211 Traveller accommodation", 392: "7212 RV parks and recreational camps"}
out = RAW / "statcan"
out.mkdir(exist_ok=True)
U = "https://www150.statcan.gc.ca/t1/wds/rest/"
md = requests.post(U + "getCubeMetadata", json=[{"productId": PID}], timeout=120).json()[0]["object"]
json.dump(md, open(out / "t9810059201_metadata.json", "w"))
geos = md["dimension"][0]["member"]
coords = []
for g in geos:
    for i in IND:
        coords.append((g, i, f"{g['memberId']}.1.2.1.1.{i}.1.0.0.0"))
got = {}
todo = [c for _, _, c in coords]
for rnd in range(6):
    fail = []
    for k in range(0, len(todo), 100):
        batch = todo[k:k + 100]
        body = [{"productId": PID, "coordinate": c, "latestN": 1} for c in batch]
        try:
            res = requests.post(U + "getDataFromCubePidCoordAndLatestNPeriods", json=body, timeout=180).json()
        except Exception as e:  # retry transient failures in the next round
            print("error", k, e)
            fail += batch
            continue
        # match on the coordinate echoed in each response object (response order is not guaranteed)
        for x in res:
            o = x.get("object") or {}
            if x.get("status") == "SUCCESS" and isinstance(o, dict) and o.get("coordinate"):
                dp = (o.get("vectorDataPoint") or [{}])[0]
                got[o["coordinate"]] = (dp.get("value"), dp.get("symbolCode"), o.get("vectorId"))
        fail += [c for c in batch if c not in got]
        time.sleep(1)
    print("round", rnd, "got", len(got), "missing", len(fail), flush=True)
    todo = fail
    if not todo:
        break
    time.sleep(10)
rows = []
for g, i, c in coords:
    v = got.get(c, (None, None, None))
    rows.append(dict(geo_member=g["memberId"], geo_code=g["classificationCode"], geo_level=g["geoLevel"],
                     geo_name=g["memberNameEn"], industry_member=i, industry=IND[i], employed=v[0],
                     symbol=v[1], vector_id=v[2], coordinate=c))
df = pd.DataFrame(rows)
df.to_csv(out / "t9810059201_employed_by_industry_cd.csv", index=False)
print("missing values", df.employed.isna().sum())
