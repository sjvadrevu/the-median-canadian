"""Pull Ontario Newsroom releases (API) from 2023 onward and keep forest/wildland fire items.
Usage: python3 -I east_01_on_newsroom.py OUTDIR"""
import json, sys, subprocess, re, html, os
out = sys.argv[1]
keep = []
for page in range(1, 60):
    url = f"https://api.news.ontario.ca/api/v1/releases?language=en&limit=100&page={page}"
    raw = subprocess.run(["curl", "-sS", "-m", "60", url], capture_output=True, text=True).stdout
    try:
        d = json.loads(raw)
    except Exception:
        print("fail page", page); continue
    rows = d.get("data", [])
    if not rows:
        break
    for r in rows:
        blob = " ".join(str(r.get(k) or "") for k in ["content_title", "content_lead", "content_body", "quickfacts"])
        if re.search(r"wildland fire|forest fire|firefight|fireranger|waterbomber|wildfire", blob, re.I):
            txt = html.unescape(re.sub(r"<[^>]+>", " ", blob))
            keep.append({"date": r["release_date_time"], "ministry": r.get("ministry_acronym"), "title": r["content_title"],
                         "url": "https://news.ontario.ca/en/" + ("release" if r.get("release_type_label") == "release" else (r.get("release_type_label") or "release")) + "/" + str(r["id"]) + "/" + r["slug"],
                         "text": re.sub(r"\s+", " ", txt)})
    if rows[-1]["release_date_time"] < "2023-01-01":
        break
json.dump(keep, open(os.path.join(out, "on_newsroom_fire_2023_2026.json"), "w"), indent=1)
for k in keep:
    print(k["date"][:10], k["ministry"], k["title"], k["url"])
