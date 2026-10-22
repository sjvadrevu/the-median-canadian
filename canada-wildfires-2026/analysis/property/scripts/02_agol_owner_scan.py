"""List every public item of Canadian local-government / agency ArcGIS Online owners and orgs linked to 2023-2026 wildfire
events, flagging titles that suggest damage / structure status layers. Output: work/agol_owner_items.csv"""
import requests, pandas as pd, os, re, sys
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://www.arcgis.com/sharing/rest/search"
owners = sys.argv[1:]
rows = []
for o in owners:
    q = f"owner:{o}" if not o.startswith("orgid:") else o
    start = 1
    while start > 0:
        r = requests.get(URL, params=dict(q=q, f="json", num=100, start=start, sortField="modified", sortOrder="desc"), timeout=60).json()
        for it in r.get("results", []):
            rows.append(dict(query=o, id=it["id"], type=it["type"], title=it["title"], owner=it["owner"], url=it.get("url"),
                             modified=pd.to_datetime(it["modified"], unit="ms").date(), snippet=(it.get("snippet") or "")[:150]))
        start = r.get("nextStart", -1)
        if start > 1000: break
df = pd.DataFrame(rows)
f = os.path.join(P, "work", "agol_owner_items.csv")
if os.path.exists(f): df = pd.concat([pd.read_csv(f), df]).drop_duplicates("id")
df.to_csv(f, index=False)
pat = re.compile(r"damag|destroy|structure|status|loss|recover|debris|rebuild|impact|fire|burn|propert", re.I)
s = df[df["query"].isin(owners) & df.title.str.contains(pat)]
for _, r in s.iterrows(): print(r.query[:22], "|", r.type[:10], "|", r.title[:70], "|", r.modified, "|", r.id)
print({o: int((df["query"] == o).sum()) for o in owners})
