"""Combine the cost files into one wildfire bill, counting each dollar once.

Inputs
- economic-value/cost_tally_by_year.csv: trees burned (timber at Crown stumpage) and firefighting in BC, AB, SK and ON.
- costs-full/gov*_costs.csv, econ*_costs.csv, health*_costs.csv: research rounds 1, 2, ... Later rounds add lines and,
  where their notes say so, replace earlier lines (REPLACED below).
- Buildings destroyed at census home values come from the property analysis and are added by the slide and page
  builders (they are not in these files).

Rules
- Floor ("at least", the figure on the slide): official spending in full and every estimate at the low end of its
  range. Lost wages and lost output overlap, so the floor counts the larger of the two groups.
- Not in the floor: the value of standing timber burned (a valuation, not a cost: most burned forest is outside
  harvest plans, much can be salvaged and harvest is capped by the allowable cut; economic-value/results.md), and the
  Indigenous Services Canada on-reserve estimate (it partly repays provinces' evacuation costs that are counted, and
  the overlap is not published; gov_notes.md, health_notes.md). Both stay in the file as reference lines.
- Central and high: estimates at their central and high values; lost wages and lost output both added (they may
  partly overlap).
- Firefighting in the 2026 season (forecasts, budgets and estimates from area burned; the season is not closed) is
  its own line.
- A line whose dollar figure comes from a news report is not counted (news is used only to find documents).
- Transfers (federal disaster assistance, income support, EI) are not added: they pay for costs already counted.

Outputs: costs-full/combined_bill.csv (one row per line: receipt line, amount counted in the floor, low, central,
high, source file, note) and costs-full/bill_summary.json (totals by receipt line for the three cases).
"""
import glob
import json
import os
import re

import pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
AN = os.path.join(D, "..")

# Lines a later round replaces: (file, item starts with, period pattern or None, reason)
REPLACED = [
    ("gov_costs.csv", "Indigenous Services Canada EMAP response costs reimbursed, all hazards", None,
     "replaced by the refined wildfire-share range in gov2_costs.csv"),
    ("health_costs.csv", "Health care: smoke-related emergency visits and admissions, scaled from Health Canada 2023", None,
     "replaced by the rebuilt 2024 to 2026 counts in health2_costs.csv"),
    ("health_costs.csv", "Lost work and wages of evacuated workers", r"^(2023|2024|2026)$",
     "replaced by the revised 2023, 2024 and 2026 rows in health2_costs.csv"),
    ("health_costs.csv", "Evacuations: NWT Evacuation Travel Support Program (partial", None,
     "replaced by the final figure in health2_costs.csv"),
    ("gov2_costs.csv", "BC 2026 fires: local authority response and Emergency Support Services", None,
     "same costs as the 2026 off-reserve evacuation estimate in health2_costs.csv"),
]
NEWS = (r"ctvnews|ctv\.ca|cbc\.ca|radio-canada|globalnews|citynews|thestar|theglobeandmail|nationalpost|cp24|saltwire|"
        r"chronicleherald|lapresse|ledevoir|journaldemontreal|calgaryherald|edmontonjournal|vancouversun|"
        r"winnipegfreepress|cabinradio|nnsl|panow|sasktoday|castanet|infonews|kelownanow|reuters|bloomberg|apnews")
# Low-end corrections where one research file's floor overlaps another's: (file, item starts with, reason)
FLOOR_ZERO = [
    ("gov2_costs.csv", "Parks Canada 2024 season: suppression and response beyond",
     "Parks Canada's 2024-25 response spending, counted in another line, covers these fires too"),
]
# receipt lines, in slide order (trees: reference line, not part of the floor)
RECEIPT = ["trees", "fight", "fight26", "build", "evac", "work"]
FLOOR = ["fight", "fight26", "build", "evac", "work"]
dropped = []


def read_costs(kind):
    """All cost files of one kind (gov_costs.csv, gov2_costs.csv, ...) in round order, each row tagged with its file."""
    fs = sorted((f for f in glob.glob(os.path.join(D, f"{kind}*_costs.csv"))
                 if re.fullmatch(rf"{kind}\d*_costs\.csv", os.path.basename(f))),
                key=lambda f: int(re.sub(r"\D", "", os.path.basename(f)) or 1))
    return pd.concat([pd.read_csv(f).assign(_file=os.path.basename(f)) for f in fs], ignore_index=True)


def keep(r):
    """False for a line a later round replaces, or one whose figure comes from a news report (logged)."""
    for f, start, per, why in REPLACED:
        if r["_file"] == f and str(r["item"]).startswith(start) and (per is None or re.search(per, str(r["period"]))):
            dropped.append(dict(file=f, item=r["item"], period=r["period"], reason=why))
            return False
    if re.search(NEWS, f'{r.get("url", "")} {r.get("source_name", "")} {r.get("method", "")}', flags=re.I):
        dropped.append(dict(file=r["_file"], item=r["item"], period=r["period"],
                            reason="not counted: the dollar figure comes from a news report"))
        return False
    return True


def is2026(r):
    return bool(re.search(r"2026-27|2026 season|^2026\b|FY2026", str(r["period"])))


rows = []


def add(line, cat, item, lo, ce, hi, src, note=""):
    for f, start, why in FLOOR_ZERO:
        if src == f and item.startswith(start):
            lo = 0.0
            note = "not added in the floor: " + why + ("; " + note if note else "")
    rows.append(dict(line=line, cat=cat, item=item, low=float(lo or 0), central=float(ce or 0), high=float(hi or 0),
                     src=src, note=note))


tally = pd.read_csv(os.path.join(AN, "economic-value", "cost_tally_by_year.csv")).set_index("year")
trees = tally.loc[2023:2026, "E_timber_value_stumpage"].sum()
fight4 = tally.loc[2023:2025, "A_provincial_firefighting"].sum()
add("trees", "trees", "Timber burned at Crown stumpage, 2023 to 2026", trees, trees, trees, "economic-value/cost_tally_by_year.csv")
add("fight", "fight", "Firefighting, BC, AB, SK and ON, 2023 to 2025", fight4, fight4, fight4, "economic-value/cost_tally_by_year.csv")

# Government: firefighting, response and relief. Round 1 gives one amount; later rounds give low, central and high.
RELIEF = r"Public Safety Canada|CIRNAC|^ISC|\((?!federal)[A-Z][a-z]"
g = read_costs("gov")
for _, r in g.iterrows():
    a = str(r["additive"])
    if not keep(r):
        continue
    if "low" in r and pd.notna(r.get("low")):
        lo, ce, hi = r["low"], r["central"], r["high"]
    else:
        lo = ce = hi = r["additive_amount_cad"]
    juris = str(r["jurisdiction"])
    isc = juris.startswith("ISC")
    if a == "no (replacement)" and isc:
        add("evac", "isc", f'{r["item"]} ({r["period"]})', lo, ce, hi, r["_file"],
            "mostly First Nations evacuations")
        continue
    if not (a.startswith("yes") or a.startswith("partial")):
        continue
    if isc:  # round-1 ISC estimate rows are replaced above; anything else from ISC is relief
        add("evac", "isc", f'{r["item"]} ({r["period"]})', lo, ce, hi, r["_file"])
    elif is2026(r) and not re.search(RELIEF, juris):
        add("fight26", "fight_2026", f'{r["item"]} ({r["period"]})', lo, ce, hi, r["_file"])
    elif re.search(RELIEF, juris):
        add("evac", "evac", f'{r["item"]} ({r["period"]})', lo, ce, hi, r["_file"])
    else:
        add("fight", "fight", f'{r["item"]} ({r["period"]})', lo, ce, hi, r["_file"])

# Property, infrastructure and the economy
e = read_costs("econ")
for _, r in e.iterrows():
    a = str(r["additive"])
    if not (a.startswith("yes") or a.startswith("partial")) or not keep(r):
        continue
    sec = str(r["sector"])
    if sec.startswith(("property", "infrastructure")):
        add("build", "build", r["item"], r["amount_low_cad"], r["amount_central_cad"], r["amount_high_cad"], r["_file"])
    else:
        add("work", "output", r["item"], r["amount_low_cad"], r["amount_central_cad"], r["amount_high_cad"], r["_file"])

# People: health care, evacuations, lost work
h = read_costs("health")
for _, r in h.iterrows():
    a = str(r["additive"])
    if not (a.startswith("yes") or a.startswith("partial")) or not keep(r):
        continue
    it = str(r["item"])
    lo, ce, hi = r["amount_low_cad"], r["amount_central_cad"], r["amount_high_cad"]
    if a.startswith("partial") and "ISC" in it:
        add("evac", "isc", f'{it} ({r["period"]})', lo, ce, hi, r["_file"], "mostly First Nations evacuations")
    elif it.startswith("Health care"):
        add("evac", "health", f'{it} ({r["period"]})', lo, ce, hi, r["_file"])
    elif it.startswith("Lost work"):
        add("work", "wages", f'{it} ({r["period"]})', lo, ce, hi, r["_file"])
    else:
        add("evac", "evac", f'{it} ({r["period"]})', lo, ce, hi, r["_file"])

df = pd.DataFrame(rows)
# Floor: each line at its low end; of the two overlapping work groups only the larger is counted
wages, output = (df.loc[df.cat == c, "low"].sum() for c in ("wages", "output"))
keep_work = "output" if output >= wages else "wages"
df["counted"] = df["low"]
skip = df.cat.isin(["wages", "output"]) & (df.cat != keep_work)
df.loc[skip, "counted"] = 0.0
df.loc[skip, "note"] = ("not added in the floor: overlaps lost " + ("output" if keep_work == "output" else "wages") +
                        ", the larger of the two is counted")
z = (df.counted == 0) & (df.high != 0) & ~skip & ~df.note.str.startswith("not added in the floor")
zero = "not added in the floor: estimate starts at zero or appears only in the high case"
df.loc[z, "note"] = [zero + (f"; {n}" if n else "") for n in df.loc[z, "note"]]
# reference lines outside the floor
df.loc[df.cat == "trees", "counted"] = 0.0
df.loc[df.cat == "trees", "note"] = ("not a cost: the value of standing timber burned, most of it outside harvest plans; "
                                     "much can be salvaged")
df.loc[df.cat == "isc", "counted"] = 0.0
df.loc[df.cat == "isc", "note"] = ("not added: an estimate that partly repays provinces' evacuation costs counted above; "
                                   "mostly First Nations evacuations")
assert not set(df.line) - set(RECEIPT)
df.to_csv(os.path.join(D, "combined_bill.csv"), index=False)
pd.DataFrame(dropped).to_csv(os.path.join(D, "work", "combine_bill_dropped.csv"), index=False)


def tot(line, k):
    return float(df.loc[df.line == line, k].sum())


out = {"note": "CAD, 2025 dollars; 'build' excludes buildings destroyed at census home values (added by the builders)",
       "rules": __doc__.split("Rules\n")[1].split("\n\nOutputs")[0],
       "floor_work_group": keep_work}
for k in ("low", "central", "high"):
    out[k] = {ln: tot(ln, k) for ln in RECEIPT}
out["low"]["work"] = max(wages, output)
for k in ("central", "high"):
    out[k]["work"] = tot("work", k)
out["slide"] = {ln: float(df.loc[df.line == ln, "counted"].sum()) for ln in FLOOR}
out["slide"]["trees_reference"] = float(df.loc[df.cat == "trees", "low"].sum())
out["slide"]["isc_estimate_low"] = float(df.loc[df.cat == "isc", "low"].sum())
out["slide"]["isc_estimate_central"] = float(df.loc[df.cat == "isc", "central"].sum())
out["slide"]["isc_estimate_high"] = float(df.loc[df.cat == "isc", "high"].sum())
assert abs(out["slide"]["work"] - out["low"]["work"]) < 1
assert abs(out["slide"]["evac"] + out["slide"]["isc_estimate_low"] - out["low"]["evac"]) < 1
json.dump(out, open(os.path.join(D, "bill_summary.json"), "w"), indent=1)
for k in ("low", "central", "high"):
    print(k, {a: round(b / 1e9, 3) for a, b in out[k].items()}, "total", round(sum(out[k].values()) / 1e9, 2))
print("dropped:", len(dropped), "lines (work/combine_bill_dropped.csv)")
