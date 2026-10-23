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
    out["c3"] = dict(reached_2023=float(ex[ex.year == 2023].people_ge1day_gt27.iloc[0]),
                     reached_by_year=[[int(r.year), float(r.people_ge1day_gt27)] for r in ex.itertuples()],
                     ed_total=float(ed.loc[2023:2025, "extra_visits"].sum()),
                     ed_lo=float(ed.loc[2023:2025, "extra_visits_lo"].sum()),
                     ed_hi=float(ed.loc[2023:2025, "extra_visits_hi"].sum()),
                     ed_by_year=[dict(year=int(y), visits=float(r.extra_visits), lo=float(r.extra_visits_lo),
                                      hi=float(r.extra_visits_hi), provinces=int(r.provinces))
                                 for y, r in ed.iterrows()])

    # 4 ---------------------------------------------------------------------
    # The bill is a floor: three items with official records, in 2025 dollars where the tally converts them
    # (analysis/economic-value/cost_tally_by_year.csv), plus homes and buildings at census values.
    ct = pd.read_csv(os.path.join(AN, "economic-value/cost_tally_by_year.csv")).set_index("year")
    trees = ct.loc[2023:2026, "E_timber_value_stumpage"].sum() / 1e9
    ff3 = ct.loc[2023:2025, "A_provincial_firefighting"].sum() / 1e9
    vtot = sum(s["value"].values()) / 1000
    items = [("Trees burned, 2023 to 2026", trees), ("Firefighting in BC, Alberta, Saskatchewan and Ontario, 2023 to 2025", ff3),
             ("Homes and buildings destroyed", vtot)]
    pop = population_2026()
    bill = sum(b for _, b in items)
    ff_ratio = V("C28.mean_2023_2025_b") / V("C28.mean_2016_2022_b")
    assert 1.9 <= ff_ratio <= 2.2, ff_ratio  # the page says firefighting costs "doubled"
    # official records for items left out of the total (different bases, possible overlap)
    meas = pd.read_csv(os.path.join(AN, "policy/measures.csv"))
    dfaa = meas[meas.name.str.contains("Disaster Financial Assistance")].iloc[0]
    agx = pd.concat([pd.read_csv(os.path.join(RD, "agencies_west.csv")), pd.read_csv(os.path.join(RD, "agencies_east.csv"))])

    def acts(prefix):
        r = agx[agx.agency.str.startswith(prefix)].iloc[0]
        return dict(agency=r.agency, values=[clean(r.actual_2023_24_cad), clean(r.actual_2024_25_cad), clean(r.actual_2025_26_cad)],
                    basis=clean(r.actual_basis))
    out["c4"] = dict(items=[dict(label=a, b=round(float(b), 3)) for a, b in items],
                     total_b=bill, per_canadian=bill * 1e9 / pop["value"],
                     population_2026=pop["value"], population_source=pop["source"],
                     not_counted=["Firefighting in other provinces and territories", "Health care and evacuations", "Lost work and wages"],
                     records_left_out=dict(dfaa=dict(cad=float(dfaa.amount_spent_cad), label=dfaa["name"], url=dfaa.source_url),
                                           mb=acts("Manitoba"), qc=acts("Quebec"), yt=acts("Yukon")),
                     firefight_2023_2025_b=V("C28.mean_2023_2025_b"), firefight_2016_2022_b=V("C28.mean_2016_2022_b"),
                     firefight_ratio=ff_ratio,
                     firefight_by_year=[[int(y), round(float(v), 3)] for y, v in sorted(s["firefight"].items())],
                     value_by_year=[[int(y), round(float(v), 1)] for y, v in sorted(s["value"].items())],
                     buildings_by_year=[[int(y), int(v)] for y, v in sorted(s["value_bldg"].items())])

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
