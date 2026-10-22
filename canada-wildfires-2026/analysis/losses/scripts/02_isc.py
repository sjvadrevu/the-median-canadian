"""ISC First Nations wildfire evacuations.
Inputs (raw/isc/):
  evac_stats.html  ISC 'Wildland fire and flood evacuation statistics between April 1, 2016 and March 31, 2026'
                   https://isc.gc.ca/eng/1583177459681/1583177553276 (date modified 2026-06-01)
  wildfire_evac_info.html  ISC 'Wildfire evacuation information for Indigenous peoples' (current situation, 2026 season)
                   https://isc.gc.ca/eng/1686078907307/1686078925161 (date modified 2026-10-05)
  qpnotes_wildfire_subset.csv  rows of the federal Proactive Disclosure - Question Period notes dataset
                   (open.canada.ca ecd1a913-47da-47fc-8f96-2432be420986, qpnotes.csv modified 2026-10-21) mentioning wildfires
Outputs: isc_wildfire_evacuations_by_fiscal_year.csv, isc_wildfire_evacuees_by_province_2016_2026.csv, isc_season_snapshots.csv
"""
import html, os, re
import pandas as pd

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(L, "raw", "isc")

def text(p):
    t = open(p, encoding="utf-8").read()
    m = re.search(r"<main.*?</main>", t, re.S); t = m.group(0) if m else t
    t = re.sub(r"<script.*?</script>", "", t, flags=re.S)
    t = re.sub(r"</(tr|p|h\d|li|caption|div)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t)).replace("\xa0", " ")
    return "\n".join(x.strip() for x in t.splitlines() if x.strip())

t = text(os.path.join(R, "evac_stats.html"))
wf = t[t.rindex("Number of First Nations wildfire evacuations"):]
rows = []
for m in re.finditer(r"(20\d\d) t[o0] (20\d\d):\s*(\d+) short term(?:, (\d+) long term)?", wf):
    s, l = int(m.group(3)), int(m.group(4) or 0)
    rows.append(dict(fiscal_year=f"{m.group(1)}-{m.group(2)[2:]}", fy_start=int(m.group(1)), short_term=s, long_term=l, total=s + l))
fy = pd.DataFrame(rows)
fy["rank_total_of_10"] = fy.total.rank(ascending=False, method="min").astype(int)
fy["source"] = "ISC evacuation statistics page, date modified 2026-06-01 (numbers not final)"
fy.to_csv(os.path.join(L, "isc_wildfire_evacuations_by_fiscal_year.csv"), index=False)

st = t.rindex("Number of First Nations wildfire evacuees by province or territory between")
sec = t[st:t.index("Number of First Nations wildfire evacuations", st)]
pr = []
for m in re.finditer(r"\n([A-Z][A-Za-z ]+?):\s*([\d,]+)(?: \(includes ([\d,]+) long term)?", sec):
    pr.append(dict(province=m.group(1).strip(), evacuees_fy2016_17_to_fy2025_26=int(m.group(2).replace(",", "")),
                   of_which_long_term=int((m.group(3) or "0").replace(",", ""))))
pr = pd.DataFrame(pr)
pr.to_csv(os.path.join(L, "isc_wildfire_evacuees_by_province_2016_2026.csv"), index=False)

# Season snapshots: ISC live page (2026) and ISC/PS question period notes (official briefing records)
c = text(os.path.join(R, "wildfire_evac_info.html"))
m = re.search(r"Since April 1, 2026, there have been:\s*([\d,]+) wildland fires.*?([\d,]+) First Nations on reserve and eligible under EMAP impacted\s*([\d,]+) First Nations on reserve and eligible under EMAP evacuated.*?as of (\w+ \d+, 2026).*?([\d,]+) individuals currently evacuated", c, re.S)
snap = [dict(season=2026, period="2026-04-01 to " + m.group(4), wildfire_events=int(m.group(1)), first_nations_affected=int(m.group(2)),
             people_evacuated=int(m.group(3).replace(",", "")), communities_evacuated=None,
             source="ISC 'Wildfire evacuation information for Indigenous peoples', date modified 2026-10-05",
             note=f"label reads 'First Nations on reserve and eligible under EMAP evacuated'; value is people (ISC); {m.group(5)} still evacuated on {m.group(4)}")]
q = pd.read_csv(os.path.join(R, "qpnotes_wildfire_subset.csv"))
pat = re.compile(r"Between April 1 and (\w+ \d+), (20\d\d), (\d+) wildfire events affected (\d+) First Nations communities, forcing evacuations and displacing over ([\d,]+) people from (\d+) communities")
seen = set()
for _, r in q.sort_values("date_received").iterrows():
    for m in pat.finditer(str(r.response_en) + " " + str(r.background_en)):
        if m.group(2) in seen: continue
        seen.add(m.group(2))
        snap.append(dict(season=int(m.group(2)), period=f"{m.group(2)}-04-01 to {m.group(1)}, {m.group(2)}", wildfire_events=int(m.group(3)),
                         first_nations_affected=int(m.group(4)), people_evacuated=int(m.group(5).replace(",", "")), communities_evacuated=int(m.group(6)),
                         source=f"Question Period note {r.reference_number} (ISC), dated {r.date_received}", note="'over' N people"))
pd.DataFrame(snap).sort_values("season").to_csv(os.path.join(L, "isc_season_snapshots.csv"), index=False)
print(fy.to_string()); print(pr.to_string()); print(pd.DataFrame(snap).to_string())
