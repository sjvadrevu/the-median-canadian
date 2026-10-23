"""Stream-filter the federal Proactive Disclosure - Grants and Contributions CSV (open.canada.ca dataset
432527ab-7aac-45b5-81d6-7597107a7013, grants.csv, 2.3 GB, modified 2026-10-21) from stdin. Kept: rows whose program
name or description mentions Disaster Financial Assistance (DFAA) and rows from any department whose text mentions
wildfire/forest fire together with recovery/evacuation/disaster. Nothing else is written to disk."""
import csv, io, os, re, sys
csv.field_size_limit(10**9)
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(L, "raw", "grants", "grants_dfaa_wildfire_subset.csv"); os.makedirs(os.path.dirname(out), exist_ok=True)
r = csv.DictReader(io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8-sig", errors="replace"))
w = None; n = k = 0
dfaa = re.compile(r"disaster financial assistance|\bDFAA\b|accords d'aide financi.re en cas de catastrophe", re.I)
fire = re.compile(r"wild ?fire|forest fire|wildland fire|feux? de for.t|incendies? de for.t", re.I)
ctx = re.compile(r"recover|evacuat|disaster|emergency|rebuild|response", re.I)
for row in r:
    n += 1
    t = " ".join(str(row.get(c, "")) for c in ("prog_name_en", "prog_purpose_en", "description_en", "agreement_title_en", "expected_results_en"))
    if dfaa.search(t) or (fire.search(t) and ctx.search(t)):
        if w is None:
            w = csv.DictWriter(open(out, "w", newline="", encoding="utf-8"), fieldnames=r.fieldnames); w.writeheader()
        w.writerow(row); k += 1
    if n % 500000 == 0:
        print(n, "rows,", k, "kept", flush=True)
print("done", n, "rows,", k, "kept")
