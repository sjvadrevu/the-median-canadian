#!/usr/bin/env python3
"""Build data/chapters.json and data/map/burn_2023_2026.png for the story chapters on the site.

Every value is computed from the same analysis files the carousel reads (slides/make_slides_merge.py),
so the site and the slides show the same numbers:

- Chapter 1: agency totals (data/smoke-cost/fire_area_count_by_agency_year.csv), Germany's area
  (analysis/graphics/canada_burned_germany_paths.json) and fire labels (analysis/coverage/labels.csv).
- Chapter 2: story/verified_numbers.json (C6, C9, C10) and the yearly temperature, drought and area series.
- Chapter 3: analysis/health/exposure_by_group.csv and analysis/health/ed_extra_visits_by_year.csv.
- Chapter 4: C27 timber, provincial firefighting (analysis/economic-value/cost_tally_by_year.csv) and
  homes and buildings (analysis/property/destroyed_value_estimates.csv).
- Chapter 5: analysis/threads/t1_official_inventory_lines.csv.
- Chapter 6: analysis/readiness/ (agencies_west.csv, agencies_east.csv, scorecard.csv, gaps_*.csv,
  national_ciffc.csv, highlights.csv).
- Chapter 7: analysis/readiness/timeline.csv, analysis/policy/measures.csv, analysis/policy/research_underway.csv.
- Chapter 8: the three rows of the last slide.

Usage: python scripts/build_chapters.py   (needs pandas, pyproj; Playwright Chromium for the burn PNG)
"""
import json
import math
import os
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "slides"))
import make_slides_merge as ms  # noqa: E402
import option_visuals as ov  # noqa: E402
from canmap import CanMap  # noqa: E402

AN = os.path.join(ROOT, "analysis")
RD = os.path.join(AN, "readiness")
V = ms.V


def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def recs(df):
    return [{k: clean(v) for k, v in r.items()} for r in df.to_dict("records")]


def main():
    s = ms.series()
    out = {"built": pd.Timestamp.today().strftime("%Y-%m-%d"),
           "note": "Built by scripts/build_chapters.py from the same files as the carousel."}

    # 1 ---------------------------------------------------------------------
    g = json.load(open(os.path.join(AN, "graphics/canada_burned_germany_paths.json")))
    m = CanMap(W=928)
    lab = pd.read_csv(os.path.join(AN, "coverage/labels.csv"))
    labels = []
    for _, r in lab.iterrows():
        x, y = m.xy(r["lon"], r["lat"])
        name, yr = r["label"].rsplit(", ", 1)
        short = {"Thunder Bay district": "Thunder Bay", "Flin Flon / Denare Beach": "Flin Flon",
                 "Shelburne County": "Shelburne", "Lebel-sur-Quevillon": "Lebel-sur-Quévillon"}.get(name, name)
        txt, side = ms.LABEL_TEXT[r["label"]]
        labels.append(dict(name=short, year=int(yr), text=txt, side=side, x=round(x, 1), y=round(y, 1),
                           outline=r["outline_id"], ha=int(r["our_area_ha"])))
    ag = pd.read_csv(os.path.join(ROOT, "data/smoke-cost/fire_area_count_by_agency_year.csv"))
    yearly = (ag.groupby("year").area_burned_ha.sum() / 1e6)
    roll4 = yearly.rolling(4).sum()
    out["c1"] = dict(total_mha=s["agency_run"], prior_max_mha=s["agency_prior_max"],
                     prior_max_end=s["agency_prior_end"], ratio=s["agency_run"] / s["agency_prior_max"],
                     germany_mha=g["germany_ha"] / 1e6, germany_path=g["germany_centred"],
                     map_w=g["W"], map_h=g["H"], crop_top=300, labels=labels,
                     roll4=[[int(y), round(float(v), 3)] for y, v in roll4.dropna().items()],
                     yearly=[[int(y), round(float(v), 3)] for y, v in yearly.items()])

    # 2 ---------------------------------------------------------------------
    pts = [dict(year=y, temp=round(float(s["temp"][y]), 3), drought=round(float(s["drought"][y]), 2),
                mha=round(float(s["agency_year"][y]), 3)) for y in range(2003, 2027)]
    out["c2"] = dict(warming_c=V("C6.warming_c"), share_from_warming=V("C9.share_attributable"),
                     one_in=round(1 / V("C9.share_attributable")), rain_pct=V("C10.pct_of_normal"),
                     d1_max_2003_2022=V("C12.max_2003_2022"), points=pts)

    # 3 ---------------------------------------------------------------------
    exg = pd.read_csv(os.path.join(AN, "health/exposure_by_group.csv"))
    ex = exg[(exg.radius_km == 50) & (exg.period == "May-Sep") & (exg.dimension == "national") &
             (exg.weight == "total_pop")]
    ed = s["ed"]
    hc = pd.read_csv(os.path.join(AN, "health/hc_matz2026_2023.csv")).set_index("outcome")
    assert not hc.index.str.contains("death", case=False).any()
    hc_rows = [("Asthma symptom days in children aged 5 to 19", "Asthma symptom days"),
               ("Days with activity restricted by smoke", "Restricted activity days"),
               ("Emergency visits for breathing problems", "Respiratory emergency room visits"),
               ("Emergency visits for heart problems", "Cardiac emergency room visits"),
               ("Hospital admissions for breathing problems", "Respiratory hospital admissions"),
               ("Hospital admissions for heart problems", "Cardiac hospital admissions")]
    out["c3"] = dict(hc_2023=[dict(label=a, central=float(hc.loc[k, "central"]), low=float(hc.loc[k, "low"]), high=float(hc.loc[k, "high"]))
                              for a, k in hc_rows],
                     hc_asthma_days=float(hc.loc["Asthma symptom days", "central"]),
                     reached_2023=float(ex[ex.year == 2023].people_ge1day_gt27.iloc[0]),
                     reached_by_year=[[int(r.year), float(r.people_ge1day_gt27)] for r in ex.itertuples()],
                     ed_total=float(ed.loc[2023:2025, "extra_visits"].sum()),
                     ed_lo=float(ed.loc[2023:2025, "extra_visits_lo"].sum()),
                     ed_hi=float(ed.loc[2023:2025, "extra_visits_hi"].sum()),
                     ed_by_year=[dict(year=int(y), visits=float(r.extra_visits), lo=float(r.extra_visits_lo),
                                      hi=float(r.extra_visits_hi), provinces=int(r.provinces))
                                 for y, r in ed.iterrows()])

    # 4 ---------------------------------------------------------------------
    # The bill (analysis/costs-full/scripts/combine_bill.py): every line counted once. Receipt = bill_summary.json
    # "slide": floor values, plus the 2026 government forecasts and budgets and the Indigenous Services Canada
    # on-reserve estimate. Homes and buildings add the census-value building total to the extra building lines.
    bs = json.load(open(os.path.join(AN, "costs-full/bill_summary.json")))
    sl = bs["slide"]
    vtot = sum(s["value"].values()) / 1000
    receipt = [("trees", "Trees burned, 2023 to 2026", sl["trees_2023_2026"] / 1e9),
               ("fight", "Firefighting, 2023 to 2025", sl["firefighting_response_2023_2025"] / 1e9),
               ("fight26", "Firefighting, 2026 forecasts", sl["firefighting_2026_forecasts"] / 1e9),
               ("build", "Homes, buildings and repairs", vtot + sl["buildings_infrastructure_extra"] / 1e9),
               ("evac", "Evacuations and hospital care", sl["evacuations_health_incl_isc"] / 1e9),
               ("work", "Lost work and business", sl["lost_work_and_output"] / 1e9)]
    total = sum(v for _, _, v in receipt)
    pop = population_2026()
    ff_ratio = V("C28.mean_2023_2025_b") / V("C28.mean_2016_2022_b")
    assert 1.9 <= ff_ratio <= 2.2, ff_ratio  # the page says firefighting costs "doubled"
    cb = pd.read_csv(os.path.join(AN, "costs-full/combined_bill.csv"))
    lines = bill_lines(cb, vtot)
    # every line adds up to the receipt, category by category
    for k, _, v in receipt:
        got = sum(l["counted"] for l in lines if l["cat"] == k) / 1e9
        assert abs(got - v) < 0.0015, (k, got, v)
    ins = pd.read_csv(os.path.join(AN, "costs-full/work/econ_property_insured_vs_bill.csv"))
    ins_all = ins[ins.event == "Six events with both"].iloc[0]
    out["c4"] = dict(items=[dict(key=k, label=lab, b=round(v, 3)) for k, lab, v in receipt],
                     total_b=total, per_canadian=total * 1e9 / pop["value"],
                     population_2026=pop["value"], population_source=pop["source"],
                     isc_estimate_b=sl["isc_estimate"] / 1e9, lines=lines, not_found=not_found(),
                     dfaa_b=dfaa_total() / 1e9,
                     insured_ratio=float(ins_all.insured_cad / ins_all.bill_building_value_cad), insured_events=int(len(ins) - 1),
                     firefight_2023_2025_b=V("C28.mean_2023_2025_b"), firefight_2016_2022_b=V("C28.mean_2016_2022_b"),
                     firefight_ratio=ff_ratio,
                     firefight_by_year=[[int(y), round(float(v), 3)] for y, v in sorted(s["firefight"].items())])
    out.setdefault("cites", {}).update(bill_cites(lines))

    # 5 ---------------------------------------------------------------------
    out["c5"] = dict(wildfire_2023_mt=V("C31.managed_wildfire_2023_mt"), official_2023_mt=V("C31.national_total_2023_mt"),
                     months_of_emissions=12 * V("C31.managed_wildfire_2023_mt") / V("C31.national_total_2023_mt"),
                     co2=[dict(year=y, official=round(n, 1), wildfire=round(w, 1)) for y, (n, w) in sorted(s["co2"].items())])

    # 6 ---------------------------------------------------------------------
    ag_w = pd.read_csv(os.path.join(RD, "agencies_west.csv"))
    ag_e = pd.read_csv(os.path.join(RD, "agencies_east.csv"))
    agencies = pd.concat([ag_w, ag_e], ignore_index=True)
    gaps = pd.concat([pd.read_csv(os.path.join(RD, "gaps_west.csv")), pd.read_csv(os.path.join(RD, "gaps_east.csv"))],
                     ignore_index=True)
    code = {"British Columbia": "BC", "Alberta": "AB", "Saskatchewan": "SK", "Manitoba": "MB",
            "Northwest Territories": "NT", "Yukon": "YT", "Nunavut": "NU", "Ontario": "ON", "Quebec": "QC",
            "New Brunswick": "NB", "Nova Scotia": "NS", "Newfoundland and Labrador": "NL",
            "Prince Edward Island": "PE", "Parks Canada": "PC", "National (CIFFC)": "CA"}

    def code_of(name):
        for k, v in code.items():
            if str(name).startswith(k):
                return v
        return None

    agencies["code"] = agencies["agency"].map(code_of)
    gaps["code"] = gaps["agency"].map(code_of)
    cards = []
    for r in recs(agencies):
        acts = [r.get("actual_2023_24_cad"), r.get("actual_2024_25_cad"), r.get("actual_2025_26_cad")]
        cover = None
        if r.get("budget_2026_27_cad") and all(a is not None for a in acts):
            cover = 100 * r["budget_2026_27_cad"] / (sum(acts) / 3)
        r["cover_pct"] = cover
        r["gaps"] = [dict(gap=gg["gap"], quote=clean(gg.get("evidence")), source=clean(gg.get("source_name")),
                          url=clean(gg.get("url"))) for gg in recs(gaps[gaps.code == r["code"]])]
        cards.append(r)
    hl = pd.read_csv(os.path.join(RD, "highlights.csv"))
    nat = pd.read_csv(os.path.join(RD, "national_ciffc.csv"))
    sc = pd.read_csv(os.path.join(RD, "scorecard.csv"))
    out["c6"] = dict(cards=cards, highlights=recs(hl), national=recs(nat), scorecard=recs(sc),
                     cover_min=float(sc.budget_pct.min()), cover_max=float(sc.budget_pct.max()))

    # 7 ---------------------------------------------------------------------
    pol = ov.policy_numbers()
    meas = pd.read_csv(os.path.join(AN, "policy/measures.csv"))
    res = pd.read_csv(os.path.join(AN, "policy/research_underway.csv"))
    res = res[res.status_2026_10_22.str.startswith("agreement active")]
    tl7 = pd.read_csv(os.path.join(RD, "timeline.csv"))
    out["c7"] = dict(timeline=recs(tl7), satellite_year=int(tl7[tl7.item.str.contains("satellite")].when.iloc[0]),
                     programs=[dict(name=a, set_m=round(b, 1), paid_m=round(c, 1)) for a, b, c in pol["jars"]],
                     set_total_m=sum(b for _, b, _ in pol["jars"]), paid_total_m=sum(c for _, _, c in pol["jars"]),
                     intl_2023=int(nat.loc[nat.year == 2023, "international_personnel_imported"].iloc[0]),
                     measures=recs(meas[["level", "jurisdiction", "name", "budget_or_nonbudget", "year_announced",
                                         "amount_announced_cad", "amount_spent_cad", "stage", "source_url"]]),
                     research=[dict(title=clean(r.agreement_title_en), org=clean(r.org),
                                    recipient=clean(str(r.recipient_legal_name).split("|")[0]),
                                    prov=clean(r.recipient_province), value=clean(r.agreement_value),
                                    end=clean(str(r.agreement_end_date)[:10]), url=clean(r.source_url))
                               for r in res.itertuples()],
                     research_total_m=pol["grants_m"], n_research=pol["n_grants"])

    # 8 ---------------------------------------------------------------------
    tl = pd.read_csv(os.path.join(RD, "timeline.csv"))
    bombers_ab_mb = int(tl[tl.who.str.contains("AB") & tl.item.str.contains("water bombers")].when.iloc[0])
    out["c8"] = dict(one_in=round(1 / V("C9.share_attributable")), fast_in_10=round(sum(s["escape72"]) / 20), bombers_year=bombers_ab_mb,
                     fast_range=[float(s["escape72"][0]), float(s["escape72"][1])],
                     cover_min=out["c6"]["cover_min"], cover_max=out["c6"]["cover_max"])

    # Coverage check ----------------------------------------------------------
    import re
    cv = pd.read_csv(os.path.join(AN, "coverage/coverage.csv"))
    walsh = cv[cv.name == "Walsh River fire"].iloc[0]
    wainwright_ha = json.load(open(os.path.join(ROOT, "data/story.json")))["claims"].get("W", {}).get("est_ha")
    out["coverage"] = dict(n_checked=len(cv), n_in=int((cv.in_our_data == "yes").sum()),
                           walsh_ours_ha=float(walsh.our_area_ha),
                           walsh_agency_ha=float(re.search(r"at ([\d,]+) ha", walsh.note).group(1).replace(",", "")),
                           wainwright_est_ha=wainwright_ha)

    json.dump(out, open(os.path.join(ROOT, "data/chapters.json"), "w"), separators=(",", ":"), default=clean)
    print("wrote data/chapters.json", os.path.getsize(os.path.join(ROOT, "data/chapters.json")) // 1024, "KB")
    burn_png(g)


def ref_by_url():
    refs = json.load(open(os.path.join(ROOT, "data/references.json")))["references"]
    by_url = {}
    for r in refs:
        by_url.setdefault(r["url"], r["id"])
        for l in r.get("links", []):
            by_url.setdefault(l["url"], r["id"])
    return by_url


def split_urls(cell):
    import re
    return [u.rstrip(".,)") for u in re.split(r"\s*;\s*|\s+", str(cell or "")) if u.startswith("http")]


def bill_lines(cb, vtot):
    """Every line of the bill with what is counted, its range, basis and sources. Lines come from combined_bill.csv
    (which reads gov*_costs.csv, econ*_costs.csv and health*_costs.csv, so later research rounds appear here once
    combine_bill.py is re-run); the cost files give each line's basis and source."""
    by_url = ref_by_url()
    info = {}
    import re
    for f in sorted(os.listdir(os.path.join(AN, "costs-full"))):
        if not re.fullmatch(r"(gov|econ|health)\d*_costs\.csv", f):
            continue
        for r in pd.read_csv(os.path.join(AN, "costs-full", f)).fillna("").to_dict("records"):
            if f.startswith("gov"):
                basis = r.get("basis", "")
            elif f.startswith("econ"):
                basis = "; ".join(x for x in (r.get("basis", ""), r.get("dollars_basis", "")) if x)
            else:
                basis = r.get("method", "")
            d = dict(basis=str(basis), source=str(r.get("source_name", "")), urls=split_urls(r.get("url")))
            info[(f, str(r["item"]))] = d
            info[(f, f'{r["item"]} ({r.get("period", "")})')] = d
            info[(f, f'{r["item"]} ({r.get("period", "")}), estimate')] = d
    # lost wages and lost output overlap: the floor keeps the larger group
    wages = cb.loc[cb.cat == "wages", "low"].sum()
    output = cb.loc[cb.cat == "output", "low"].sum()
    keep_work = "output" if output >= wages else "wages"
    out = [dict(cat="build", label="Homes and buildings destroyed (official counts and a satellite check, at census home values)",
                counted=vtot * 1e9, low=vtot * 1e9, high=vtot * 1e9, note="",
                basis="Buildings destroyed x 2021 Census average value of owner-occupied dwellings",
                source="analysis/property (official damage counts; Sentinel-2 check)",
                refs=["jasper-damage", "hrfe", "rdco", "csrd", "tnrd", "mnp-sk", "summerland", "census-profile", "sentinel2", "msbuildings"])]
    for _, r in cb.iterrows():
        cat, item = r["cat"], str(r["item"])
        isc = "Indigenous Services Canada" in item and item.endswith("estimate")
        if cat == "trees":
            k, counted, note = "trees", r["low"], ""
        elif cat == "fight_2026":
            k, counted, note = "fight26", r["ref"], "government forecast or budget"
        elif isc:
            k, counted, note = "evac", r["central"], "estimate; mostly First Nations evacuations"
        elif cat == "fight":
            k, counted, note = "fight", r["low"], ""
        elif cat == "build":
            k, counted, note = "build", r["low"], ""
        elif cat in ("evac", "health"):
            k, counted, note = "evac", r["low"], ""
        elif cat in ("wages", "output"):
            k = "work"
            counted = r["low"] if cat == keep_work else 0.0
            note = "" if cat == keep_work else "not added: overlaps lost output, the larger of the two is counted"
        else:
            continue
        if counted == 0 and not note:
            note = "not added: estimate starts at zero or appears only in the high case"
        src = str(r["src"])
        d = info.get((src, item), {})
        if src.startswith("economic-value"):
            d = dict(basis="Provincial public accounts (2025 dollars)" if cat == "fight" else
                     "Timber volume burned x provincial Crown stumpage price (2025 dollars)",
                     source="analysis/economic-value/cost_tally_by_year.csv", urls=[])
        if re.search(r"death", d.get("basis", "") + d.get("source", ""), flags=re.I):
            # the page shows no modelled smoke deaths; these lines scale Health Canada's 2023 hospital cost by smoke exposure
            d = dict(d, basis="Health Canada's 2023 hospital cost, scaled to this year by smoke exposure where people live",
                     source="Health Canada estimates for 2023 and air monitor smoke levels")
        refs = ({"trees": ["nfd-revenue", "bc-budget", "knn2011", "nbac", "cwfis-m3", "cpi"],
                 "fight": ["bcws-cost", "bc-budget", "on-pa", "ab-ar", "sk-auditor", "cpi"]}.get(cat, [])
                if src.startswith("economic-value") else [])
        refs += [by_url[u] for u in d.get("urls", []) if u in by_url and by_url[u] not in refs]
        out.append(dict(cat=k, label=item, counted=float(counted), low=float(r["low"] if cat != "fight_2026" else r["ref"]),
                        high=float(r["high"] if cat != "fight_2026" else r["ref"]), note=note,
                        basis=d.get("basis", ""), source=d.get("source", src), refs=refs))
    return out


def dfaa_total():
    """Federal Disaster Financial Assistance Arrangements orders for wildfire events (not added to the bill)."""
    import re
    tot = 0.0
    for f in sorted(os.listdir(os.path.join(AN, "costs-full"))):
        if re.fullmatch(r"gov\d*_costs\.csv", f):
            g = pd.read_csv(os.path.join(AN, "costs-full", f))
            tot += g[g.item.str.contains("DFAA")].amount_nominal_cad.sum()
    return float(tot)


def not_found():
    """Specific items still without a public record, from the 'Not found' sections of the notes files
    (gov*_notes.md, econ*_notes.md, health*_notes.md, so later research rounds are picked up when re-run).
    For the page each item is shortened: asides that mention news reports and figures quoted from the news are
    dropped (news is used only to find documents), and industry insured-loss gaps are left out (not part of the bill)."""
    import re
    label = {"gov": "Firefighting and emergency response", "econ": "Property, infrastructure and the economy",
             "health": "Health care, evacuations and work"}
    res = []
    for f in sorted(os.listdir(os.path.join(AN, "costs-full"))):
        m0 = re.fullmatch(r"(gov|econ|health)\d*_notes\.md", f)
        if not m0:
            continue
        t = open(os.path.join(AN, "costs-full", f), encoding="utf-8").read()
        m = re.search(r"^## (?:\d+\. )?(?:Not found|Could not find)[^\n]*\n(.*?)(?=^## |\Z)", t, flags=re.S | re.M)
        if not m:
            continue
        head = None
        for line in m.group(1).splitlines():
            s = line.strip()
            h = re.match(r"^\*\*(.+?)\*\*\s*$", s) or re.match(r"^([A-Z][^:]{2,40}):\s*$", s)
            if h:
                head = h.group(1)
                continue
            b = re.match(r"^- (.+)$", s)
            if not b or b.group(1).lower().startswith("access notes") or (head or "").lower().startswith("insured"):
                continue
            x = b.group(1)
            pre = re.match(r"^([^:()]{2,60}):\s", x)
            access = r"\b(news|media|told|CBC|cited from|premier|briefing|HTTP|WebFetch|curl|downloads?|readable|refused|blocks)\b"
            x = re.sub(r"\s*\([^()]*" + access + r"[^()]*\)", "", x, flags=re.I)
            parts = re.split(r"(?<=[.;])\s+", x)
            x = " ".join(p for p in parts if not re.search(access + r"|the bill flags", p, flags=re.I)).strip()
            x = re.sub(r"\s+", " ", x).strip(" ;")
            if x and pre and not x.startswith(pre.group(1)):
                x = f"{pre.group(1)}: {x}"
            if x:
                res.append(dict(file=f, group=label[m0.group(1)] + (f": {head}" if head else ""), text=x))
    return res


def bill_cites(lines):
    """Reference ids behind each receipt line and the notes beside the bill."""
    ids = {}
    for l in lines:
        for r in l["refs"]:
            ids.setdefault(l["cat"], [])
            if r not in ids[l["cat"]]:
                ids[l["cat"]].append(r)
    out = {f"bill_{k}": ",".join(v) for k, v in ids.items()}
    import re
    out["bill_evac"] = ",".join(["matz2026"] + [x for x in out.get("bill_evac", "").split(",") if x and x != "matz2026"])
    by_url = ref_by_url()
    for key, pref, pat in [("bill_insured", "econ", "Insured losses"), ("bill_dfaa", "gov", "DFAA")]:
        us = []
        for f in sorted(os.listdir(os.path.join(AN, "costs-full"))):
            if re.fullmatch(rf"{pref}\d*_costs\.csv", f):
                d = pd.read_csv(os.path.join(AN, "costs-full", f)).fillna("")
                us += [u for x in d[d.item.str.contains(pat)].url for u in split_urls(x)]
        out[key] = ",".join(dict.fromkeys(by_url[u] for u in us if u in by_url))
    return out


def population_2026():
    """Canada's population on July 1, 2026 (Statistics Canada table 17-10-0005-01). The raw table is read when it is
    present (analysis/health/raw is not kept in the repo); the extracted value is kept in data/canada_population_2026.csv."""
    keep = os.path.join(ROOT, "data/canada_population_2026.csv")
    src = os.environ.get("WILDFIRE_SRC", ROOT)
    raw = [os.path.join(b, "analysis/health/raw/deaths/17100005/17100005.csv") for b in (ROOT, src)]
    raw = next((r for r in raw if os.path.exists(r)), None)
    if raw:
        d = pd.read_csv(raw, low_memory=False, encoding="utf-8-sig")
        x = d[(d.GEO == "Canada") & (d.REF_DATE.astype(str) == "2026") & (d["Age group"] == "All ages") &
              (d.Gender.str.startswith("Total"))]
        assert len(x) == 1
        pd.DataFrame([dict(ref_date="2026-07-01", geo="Canada", value=int(x.VALUE.iloc[0]),
                           source="Statistics Canada, Table 17-10-0005-01, Population estimates on July 1, by age and gender",
                           vector=x.VECTOR.iloc[0], url="https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000501")]).to_csv(keep, index=False)
    k = pd.read_csv(keep).iloc[0]
    return dict(value=int(k.value), source=k.source)


def burn_png(g):
    """Burned outlines 2023 to 2026 as a transparent PNG at 2x, same pixel box as CanMap(W=928)."""
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    W, H = g["W"], g["H"]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * 2}" height="{H * 2:.0f}" viewBox="0 0 {W} {H:.0f}">'
           f'<path d="{g["burn"]}" fill="#e2482f" stroke="#e2482f" stroke-width="0.6"/></svg>')
    page = f"<html><body style='margin:0;background:transparent'>{svg}</body></html>"
    tmp = os.path.join(ROOT, "data/map/_burn.html")
    open(tmp, "w").write(page)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W * 2, "height": int(H * 2) + 1})
        pg.goto("file://" + tmp)
        pg.locator("svg").screenshot(path=os.path.join(ROOT, "data/map/burn_2023_2026.png"), omit_background=True)
        b.close()
    os.remove(tmp)
    print("wrote data/map/burn_2023_2026.png", os.path.getsize(os.path.join(ROOT, "data/map/burn_2023_2026.png")) // 1024, "KB")


if __name__ == "__main__":
    main()
