"""econ2_gdp_sawmills.py: value added lost in sawmills (NAICS 3211) during the 2023 wildfire season, by the same method as
econ_02_gdp_dips.py (unchanged rules, applied to one more industry).

Attribution: Statistics Canada, The Daily, Monthly Survey of Manufacturing, September 2023 (2023-11-15): "The wildfires in
2023 impacted production in many sawmills across Canada." The same paragraph cites rising log prices; sales had fallen for
five quarters before the fires (weak demand). Wildfires plus other causes -> 'partial' share (low 0%, central 50%,
high 100%), the econ_02 rule fixed before computing.
Data: Table 36-10-0434-01 (GDP at basic prices, monthly, SAAR, chained 2017 dollars) and 36-10-0106-01 (GDP implicit price
index), the round-one downloads in raw/econ/statcan_tables (read only).
Loss in a month = max(0, baseline - actual) / 12; baseline = straight line April 2023 to October 2023; months May to
September 2023. Paper (NAICS 3221) is shown for reference only: StatCan names no wildfire effect for pulp and paper.
usage: python3 -I econ2_gdp_sawmills.py  -> work/econ2_gdp_sawmills.csv"""
import csv, os

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(B, "raw", "econ", "statcan_tables")
gdp = {}
with open(os.path.join(T, "36100434", "36100434.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["Seasonal adjustment"] == "Seasonally adjusted at annual rates" and r["Prices"] == "Chained (2017) dollars" and r["VALUE"]:
            n = r["North American Industry Classification System (NAICS)"]
            gdp.setdefault(n[n.rfind("["):], {})[r["REF_DATE"]] = float(r["VALUE"]) * 1e6
ipi = {}
with open(os.path.join(T, "36100106", "36100106.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["Estimates"] == "Gross domestic product at market prices" and r["Index"] == "Implicit price indexes" and r["VALUE"]:
            ipi[r["REF_DATE"]] = float(r["VALUE"])


def qk(ym):
    y, m = map(int, ym.split("-")); return f"{y}-{((m - 1) // 3) * 3 + 1:02d}"


def idx(ym):
    y, m = map(int, ym.split("-")); return y * 12 + m


EP = [("gdp_sawmills_2023", "[3211]", "Sawmills and wood preservation, Canada", "2023-04", "2023-10",
       ["2023-05", "2023-06", "2023-07", "2023-08", "2023-09"], (0.0, 0.5, 1.0)),
      ("ref_pulp_paper_2023", "[3221]", "Pulp, paper and paperboard mills, Canada (reference only)", "2023-04", "2023-10",
       ["2023-05", "2023-06", "2023-07", "2023-08", "2023-09"], (0.0, 0.0, 0.0))]
rows = []
for eid, code, label, b, a, months, (lo, ce, hi) in EP:
    s = gdp[code]; vb, va = s[b], s[a]; n = idx(a) - idx(b)
    lr = ln = 0.0; det = []
    for mth in months:
        base = vb + (va - vb) * (idx(mth) - idx(b)) / n
        l = max(0.0, base - s[mth]) / 12.0
        lr += l; ln += l * ipi[qk(mth)] / 100.0
        det.append(f"{mth}: base {base/1e6:,.0f} actual {s[mth]/1e6:,.0f}")
    rows.append(dict(id=eid, naics=code, industry=label, months=";".join(months), baseline=f"{b} to {a} straight line",
                     loss_real2017_full=round(lr), loss_nominal_full=round(ln), low=round(ln * lo), central=round(ln * ce), high=round(ln * hi),
                     detail=" | ".join(det)))
with open(os.path.join(B, "work", "econ2_gdp_sawmills.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for r in rows:
    print(r["id"], f"full {r['loss_nominal_full']/1e6:.1f}M low {r['low']/1e6:.1f} central {r['central']/1e6:.1f} high {r['high']/1e6:.1f}")
    print("   ", r["detail"])
