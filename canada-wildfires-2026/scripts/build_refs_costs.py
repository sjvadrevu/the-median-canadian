#!/usr/bin/env python3
"""Add the sources behind the full wildfire bill (analysis/costs-full) and the Health Canada smoke estimates to
data/references.json.

One reference per source document (unique URL) used by a line in gov_costs.csv, econ_costs.csv or health_costs.csv,
or listed in gov_manifest.csv and health_manifest.csv. Publisher and title come from the manifests where the URL is
listed there, otherwise from the cost line. URLs already in the reference list keep their existing entry. Industry
sources (CatIQ, IBC) are labelled as industry data. Also updates the Matz et al. 2026 entry (Table 1 is now used) and
adds Chen et al. 2025 (CMAJ). Rerunnable: entries with ids starting "cost-" are rebuilt each run.

Usage: python scripts/build_refs_costs.py
"""
import csv
import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
C = os.path.join(ROOT, "analysis", "costs-full")


def urls_of(cell):
    out = []
    for u in re.split(r"\s*;\s*|\s+", str(cell or "")):
        u = u.strip().rstrip(".,)")
        if u.startswith("http"):
            out.append(u)
    return out


def rows(name):
    return list(csv.DictReader(open(os.path.join(C, name), encoding="utf-8")))


def files(kind, what):
    """gov_costs.csv, gov2_costs.csv, ... (later research rounds are picked up when they appear)."""
    fs = [os.path.basename(f) for f in glob.glob(os.path.join(C, f"{kind}*_{what}.csv"))
          if re.fullmatch(rf"{kind}\d*_{what}\.csv", os.path.basename(f))]
    return sorted(fs, key=lambda f: int(re.sub(r"\D", "", f) or 1))


def industry(text):
    return bool(re.search(r"\bINDUSTRY\b|CatIQ|Insurance Bureau|\bIBC\b", text or ""))


# News sites, Wikipedia and unofficial Hansard mirrors are used only to find official documents, so they are never
# cited as sources on the page.
NEWS = (r"ctvnews|ctv\.ca|cbc\.ca|radio-canada|globalnews|citynews|thestar|theglobeandmail|nationalpost|cp24|saltwire|"
        r"chronicleherald|lapresse|ledevoir|journaldemontreal|calgaryherald|edmontonjournal|vancouversun|"
        r"winnipegfreepress|cabinradio|nnsl|panow|sasktoday|castanet|infonews|kelownanow|reuters|bloomberg|apnews|"
        r"narcity|thenarwhal|cfjctoday|ground\.news|turtleislandnews|mbcradio|1059theregion|vocm|tbnewswatch|"
        r"kenoraonline|cheknews|timescolonist|theprovince|financialpost|aptnnews|theweathernetwork|pentictonherald|"
        r"vernonmatters|infotel|okanaganedge|everythinggp|mymcmurray|lakelandtoday|baytoday|insauga|opennwt|wikipedia")


def is_news(u):
    return bool(re.search(NEWS, u, flags=re.I))


def main():
    meta = {}  # url -> (publisher, title, coverage, accessed)
    for kind in ("gov", "econ", "health"):
        for f in files(kind, "manifest"):
            for r in rows(f):
                for u in urls_of(r.get("url")):
                    meta.setdefault(u, (r.get("publisher", ""), r.get("source") or r.get("title_or_description", ""),
                                        r.get("coverage", ""), (r.get("accessed") or r.get("accessed_utc") or "")[:10]))
    used = []  # (group, url, fallback title, fallback publisher, accessed, industry)
    for group, pub_col in [("gov", "payer"), ("econ", "jurisdiction"), ("health", "jurisdiction")]:
        for r in [x for f in files(group, "costs") for x in rows(f)]:
            for u in urls_of(r.get("url")):
                used.append((group, u, r.get("source_name", ""), r.get(pub_col, ""), r.get("accessed", ""),
                             industry(r.get("source_name", ""))))
    for group in ("gov", "health"):
        for r in [x for f in files(group, "manifest") for x in rows(f)]:
            for u in urls_of(r.get("url")):
                used.append((group, u, r.get("source", ""), r.get("publisher", ""), r.get("accessed", ""),
                             industry(r.get("source", "") + r.get("publisher", ""))))

    p = os.path.join(ROOT, "data", "references.json")
    d = json.load(open(p, encoding="utf-8"))
    refs = [r for r in d["references"] if not r["id"].startswith("cost-")]
    # the same two papers, reached through other addresses in the manifests
    alias = {"matz2026": ("Europe PMC full text", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12852501/fullTextXML"),
             "chen2025-cmaj": ("CMAJ article page", "https://www.cmaj.ca/content/197/17/E465")}
    have = set()
    for r in refs:
        have.add(r["url"])
        have.update(l["url"] for l in r.get("links", []))
    have.update(u for _, u in alias.values())
    seen, n, new = set(), {"gov": 0, "econ": 0, "health": 0}, []
    for group, u, title, pub, acc, ind in used:
        if u in seen or u in have or is_news(u):
            continue
        seen.add(u)
        n[group] += 1
        m = meta.get(u)
        publisher = (m[0] if m and m[0] else pub) or "See analysis/costs-full manifests"
        t = (m[1] if m and m[1] else title) or u
        t = re.sub(r"\s*\[INDUSTRY DATA[^\]]*\]", "", t).strip()
        new.append({"id": f"cost-{group}-{n[group]:02d}", "publisher": publisher.strip(), "title": t,
                    "version": (m[2] if m and m[2] else "As listed in analysis/costs-full"),
                    "url": u,
                    "licence": "Industry data (CatIQ or IBC), not government; not added to the bill" if ind
                    else "Open Government Licence or the publisher's terms",
                    "accessed": (acc or (m[3] if m else "") or "2026-10-22")[:10]})
    # Health Canada 2023 estimates (Table 1) and the Ontario study
    for r in refs:
        if r["id"] == "matz2026":
            r["title"] = ("Matz, C.J. and others. Health Impact Analysis of Wildfire Smoke-PM2.5 in Canada (2019 to 2023). "
                          "Volume 10, e2025GH001565 (Table 1: acute health impacts in 2023; Table S1: AQBAT coefficients)")
            r["accessed"] = "2026-10-22"
    refs = [r for r in refs if r["id"] != "chen2025-cmaj"]
    refs.append({"id": "chen2025-cmaj", "publisher": "Canadian Medical Association Journal",
                 "title": ("Chen, H., Kaufman, J.S., Chen, C. and others. Impact of the 2023 wildfire smoke episodes in Ontario, "
                           "Canada, on asthma and other health outcomes: an interrupted time-series analysis. 197(17): E465 to E477"),
                 "version": "2025", "url": "https://doi.org/10.1503/cmaj.241506",
                 "licence": "CMAJ terms (open access)", "accessed": "2026-10-22"})
    for r in refs:
        if r["id"] in alias:
            lab, u = alias[r["id"]]
            r["links"] = [l for l in r.get("links", []) if l["url"] != u] + [{"label": lab, "url": u}]
            have.add(u)
    d["references"] = refs + new
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(d["references"]), "references;", len(new), "cost sources added", n)


if __name__ == "__main__":
    main()
