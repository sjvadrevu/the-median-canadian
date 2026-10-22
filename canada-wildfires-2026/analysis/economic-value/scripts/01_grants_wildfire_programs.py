"""Stream-filter the federal Proactive Disclosure of Grants and Contributions (open.canada.ca dataset
432527ab-7aac-45b5-81d6-7597107a7013, grants.csv) from stdin. Keeps every row whose program name, purpose, title or
description mentions wildfire / wildland fire / forest fire (EN or FR), any context. Output: raw/grants/grants_wildfire_all.csv"""
import csv, io, os, re, sys
csv.field_size_limit(10**9)
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(L, "raw", "grants", "grants_wildfire_all.csv")
r = csv.DictReader(io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8-sig", errors="replace"))
fire = re.compile(r"wild ?fire|forest fire|wildland fire|feux? de for.t|incendies? de for.t|feux? de v.g.tation|feux? de forêt", re.I)
w = None; n = k = 0
for row in r:
    n += 1
    t = " ".join(str(row.get(c, "")) for c in ("prog_name_en", "prog_purpose_en", "description_en", "agreement_title_en", "expected_results_en", "prog_name_fr"))
    if fire.search(t):
        if w is None:
            w = csv.DictWriter(open(out, "w", newline="", encoding="utf-8"), fieldnames=r.fieldnames); w.writeheader()
        w.writerow(row); k += 1
    if n % 500000 == 0:
        print(n, "rows,", k, "kept", flush=True)
print("done", n, "rows,", k, "kept")
