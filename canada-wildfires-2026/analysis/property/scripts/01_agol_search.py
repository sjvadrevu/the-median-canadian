"""Search ArcGIS Online (arcgis.com/sharing/rest/search) for Canadian wildfire damage-assessment / structure-status items.
Queries restricted to a Canada bounding box; results deduplicated; written to work/agol_search_hits.csv."""
import requests, pandas as pd, os, time, json
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://www.arcgis.com/sharing/rest/search"
terms = ["damage assessment", "structure damage", "structure status", "structures destroyed", "destroyed structures",
         "wildfire damage", "fire damage", "building damage", "damaged structures", "properties destroyed", "property status",
         "structure loss", "wildfire structures", "evacuation alert", "evacuation order", "rapid damage assessment",
         "Bald Range", "Summerland wildfire", "Bradley Creek", "McDougall Creek", "Bush Creek East", "Tantallon",
         "Jasper wildfire", "Upper Tantallon", "Grouse Complex", "Enterprise wildfire", "Hay River wildfire", "Yellowknife wildfire",
         "Flin Flon wildfire", "Lac du Bonnet wildfire", "Lytton", "Denare Beach", "La Ronge wildfire", "Kelowna wildfire",
         "West Kelowna wildfire", "Shuswap wildfire", "Okanagan Indian Band wildfire", "Kenora wildfire", "wildfire recovery",
         "fire recovery parcels", "debris removal wildfire", "wildfire 2023", "wildfire 2024", "wildfire 2025", "wildfire 2026",
         "Thompson-Nicola wildfire", "Cariboo wildfire", "RDOS", "Sturgeon Lake wildfire", "Drayton Valley wildfire", "Edson wildfire",
         "Fort Nelson wildfire", "Parker Lake", "Barrington Lake", "Shelburne wildfire", "Long Lake wildfire", "Kiskatinaw", "Donnie Creek"]
seen, rows = set(), []
for t in terms:
    for start in (1, 101):
        try:
            r = requests.get(URL, params=dict(q=t, f="json", num=100, start=start, bbox="-141,41.5,-52,72"), timeout=60).json()
        except Exception as e:
            print("fail", t, e); continue
        for it in r.get("results", []):
            if it["id"] in seen: continue
            seen.add(it["id"])
            ext = it.get("extent") or [[None, None], [None, None]]
            rows.append(dict(term=t, id=it["id"], type=it["type"], title=it["title"], owner=it["owner"], url=it.get("url"),
                             created=pd.to_datetime(it["created"], unit="ms").date(), modified=pd.to_datetime(it["modified"], unit="ms").date(),
                             access=it.get("access"), licenseInfo=(it.get("licenseInfo") or "")[:200], tags=";".join(it.get("tags", []))[:200],
                             xmin=ext[0][0], ymin=ext[0][1], xmax=ext[1][0], ymax=ext[1][1], snippet=(it.get("snippet") or "")[:200]))
        if r.get("nextStart", -1) == -1 or r.get("total", 0) <= 100: break
        time.sleep(0.3)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(P, "work", "agol_search_hits.csv"), index=False)
print(len(df))
