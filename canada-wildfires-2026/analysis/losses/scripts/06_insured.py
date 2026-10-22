"""Insured losses from wildfire: industry data (CatIQ, a PERILS AG subsidiary, and IBC releases that cite CatIQ),
not government data. Only figures the organizations publish themselves on their own sites are used; the full CatIQ
event database is subscription-only. Each value is located by regex in the saved page or WordPress API JSON and the
matching sentence is stored next to it, so every number traces to its text.
Also: CDD (Public Safety Canada) INSURANCE_PAYMENTS per wildfire event for history (from cdd_wildfire_events.csv)."""
import glob, html, json, os, re
import pandas as pd

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(L, "raw", "insured")
posts = {}
for f in glob.glob(os.path.join(R, "catiq_posts_*.json")):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    if isinstance(d, list):
        for p in d:
            posts[p["id"]] = p
def text(p):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p["content"]["rendered"])))
rows = []
def add(event, season, value_cad, kind, date, url, sentence):
    rows.append(dict(event=event, season=season, insured_loss_cad=value_cad, estimate_kind=kind, published=date, source_url=url, quoted_sentence=sentence))
for p in posts.values():
    t = text(p); date = p["date"][:10]; url = p["link"]
    for m in re.finditer(r"[^.]*final estimate for the Jasper fire[^.]*is CAD ([\d.]+) billion[^.]*\.", t):
        add("Jasper wildfire complex (AB)", 2024, float(m.group(1)) * 1e9, "final (2 years post-event)", date, url, m.group(0).strip())
    for m in re.finditer(r"[^.]*Fort McMurray wildfire which, at the time, generated insured losses of CAD ([\d.]+) billion[^.]*\.", t):
        add("Fort McMurray wildfire (AB)", 2016, float(m.group(1)) * 1e9, "as quoted by CatIQ (2016 dollars)", date, url, m.group(0).strip())
    if "Bald Range" in t:
        for m in re.finditer(r"[^.]*(first|second) estimate[^.]*?is CAD ([\d.]+) million\.", t):
            s = m.group(0)
            if m.group(1) == "first" and "Bald Range" not in p["title"]["rendered"]:
                continue
            add("Bald Range fire, Summerland (BC)", 2026, float(m.group(2)) * 1e6, f"{m.group(1)} estimate", date, url, s.strip())
    for m in re.finditer(r"[^.]*insured loss total for the (?:region|country) to CA[DN] \$?([\d.]+) billion[^.]*\.", t):
        yr = int(re.search(r"in (20\d\d)", p["title"]["rendered"]).group(1)) if re.search(r"in (20\d\d)", p["title"]["rendered"]) else None
        add("ALL catastrophe perils, Canada (not wildfire-specific)", yr, float(m.group(1)) * 1e9, "annual total at publication", date, url, m.group(0).strip())
    for m in re.finditer(r"[^.]*record-breaking 2024 total, which currently sits at \$([\d.]+) billion[^.]*\.", t):
        add("ALL catastrophe perils, Canada (not wildfire-specific)", 2024, float(m.group(1)) * 1e9, "2024 total as revised by Jan 2026", date, url, m.group(0).strip())
    for m in re.finditer(r"[^.]*(ten fire-related catastrophes have been declared since 2023|five events declared in 2025|1 st in fire catastrophes declared|three new catastrophes declared to date)[^.]*\.", t):
        add("count of fire-related catastrophes (no dollar value)", None, None, "count statement", date, url, m.group(0).strip())
df = pd.DataFrame(rows).drop_duplicates(["event", "season", "insured_loss_cad", "estimate_kind", "quoted_sentence"]).sort_values(["season", "event", "published"])
cdd = pd.read_csv(os.path.join(L, "cdd_wildfire_events.csv"))
c = cdd[cdd.INSURANCE_PAYMENTS.fillna(0) > 0][["year", "PLACE", "INSURANCE_PAYMENTS", "INSURANCE_PAYMENTS_2025CAD", "EVENT_ID"]]
for r in c.itertuples():
    rows.append(dict(event=f"CDD event {int(r.EVENT_ID)}: {r.PLACE}", season=int(r.year), insured_loss_cad=r.INSURANCE_PAYMENTS, estimate_kind="CDD INSURANCE_PAYMENTS (nominal)",
                     published="CDD extract 2026-02-10", source_url="open.canada.ca dataset 1c3d15f9-9cfa-4010-8462-0d67e493d9b9", quoted_sentence=""))
df = pd.DataFrame(rows).drop_duplicates(["event", "season", "insured_loss_cad", "estimate_kind", "quoted_sentence"]).sort_values(["season", "event", "published"], na_position="last")
df["data_type"] = df.estimate_kind.str.startswith("CDD").map({True: "government (CDD)", False: "industry (CatIQ/IBC)"})
df.to_csv(os.path.join(L, "insured_losses_wildfire.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90)
print(df[["season", "event", "insured_loss_cad", "estimate_kind", "published", "data_type"]].to_string())
