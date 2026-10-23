"""Province readiness scorecard for the carousel and site.

Budget share is computed from agencies_west.csv / agencies_east.csv (2026-27 base budget as a share of the
2023-24 to 2025-26 average actual). The other cells are short plain-language summaries of the official
records listed in gaps_*.csv and agencies_*.csv; each row cites the record it summarizes.
Status rule (crews column is not rated): red = problem on record with no fix in place; amber = fix ordered or under way; grey = not found.
"""
import os

import pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
a = pd.concat([pd.read_csv(os.path.join(D, "agencies_west.csv")), pd.read_csv(os.path.join(D, "agencies_east.csv"))])


def money(prefix):
    r = a[a["agency"].str.startswith(prefix)].iloc[0]
    acts = [r["actual_2023_24_cad"], r["actual_2024_25_cad"], r["actual_2025_26_cad"]]
    avg = None if any(pd.isna(x) for x in acts) else sum(acts) / 3
    bud = None if pd.isna(r["budget_2026_27_cad"]) else r["budget_2026_27_cad"]
    return bud, avg


def pct(prefix):
    bud, avg = money(prefix)
    return None if bud is None or avg is None else 100 * bud / avg


# prov, agency prefix, water bombers (text, status), crews brought in (text, status), review fixes (text, status)
ROWS = [
    ("BC", "British Columbia", ("28 contracted", "grey"), ("About 1,750 in 2023", "none"), ("31 advised, no count", "amber")),
    ("AB", "Alberta", ("New ones in 2031", "amber"), ("4,231 in 2023", "none"), ("No review", "red")),
    ("SK", "Saskatchewan", ("40 to 70 years old, 2 grounded", "red"), ("916 in 2025", "none"), ("22 advised, not tracked", "red")),
    ("MB", "Manitoba", ("Nearly 40 years old, new in 2031", "amber"), ("1,509 in 2025", "none"), ("Review not out", "grey")),
    ("ON", "Ontario", ("New ones early 2030s", "amber"), ("104 in 2023", "none"), ("9 of 70 done", "red")),
    ("QC", "Quebec", ("Some idle, pilot shortage", "red"), ("Over 2,070 in 2023", "none"), ("No review", "red")),
    ("NT", "Northwest Territories", ("10 airtankers", "grey"), ("568 in 2023", "none"), ("1 of 35 done", "red")),
    ("NS", "Nova Scotia", ("None owned, 4 leased", "red"), ("From nearly every agency, 2025", "none"), ("63 advised, no count", "amber")),
]
out = []
for prov, pre, wb, cr, rv in ROWS:
    p = pct(pre)
    bud, avg = money(pre)
    out.append(dict(prov=prov, budget_2026_27_m=None if bud is None else round(bud / 1e6, 1),
                    avg_actual_m=None if avg is None else round(avg / 1e6, 1), budget_pct=None if p is None else round(p, 1),
                    budget_status="grey" if p is None else ("red" if p < 50 else "amber" if p < 80 else "green"),
                    bombers=wb[0], bombers_status=wb[1], crews_in=cr[0], crews_status=cr[1],
                    review=rv[0], review_status=rv[1]))
pd.DataFrame(out).to_csv(os.path.join(D, "scorecard.csv"), index=False)
print(pd.DataFrame(out).to_string())
