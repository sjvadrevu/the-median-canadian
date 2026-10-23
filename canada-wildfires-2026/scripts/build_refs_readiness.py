#!/usr/bin/env python3
"""Add the government response, readiness, health (CIHI) and coverage references to data/references.json.

Entries are built from the source manifests (analysis/readiness/manifest_west.csv, manifest_east.csv,
analysis/policy/manifest.csv, analysis/health/manifest.csv): one entry per jurisdiction or publisher, the
first URL as the main link and the rest as extra links. Rerunnable: entries with these ids are replaced.
"""
import csv
import json
import os
import re
from urllib.parse import urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
A = os.path.join(ROOT, "analysis")

# id: (publisher, title, url patterns that belong to it)
GROUPS = {
    "rd-bc": ("Government of British Columbia", "Fire Management budget and actual spending, BC Wildfire Service season summaries, Premier's Task Force on Emergencies (2024), 2026 readiness release",
              ["bcbudget.gov.bc.ca", "gov.bc.ca"]),
    "rd-ab": ("Government of Alberta; Legislative Assembly of Alberta; Office of the Auditor General of Alberta", "Wildfire Management estimates 2026-27, Forestry and Parks annual reports, Resource Stewardship committee transcript (2026), wildfire audit follow-up",
              ["alberta.ca", "assembly.ab.ca", "oag.ab.ca"]),
    "rd-sk": ("Provincial Auditor of Saskatchewan; Government of Saskatchewan", "SPSA resource planning for wildfire response (2026 Report Volume 1, Chapter 5), MNP review of the 2025 season and the province's response, Budget 2026 release",
              ["auditor.sk.ca", "saskatchewan.ca"]),
    "rd-mb": ("Government of Manitoba", "Estimates 2026/27, public accounts 2023-24 to 2025-26, Natural Resources annual reports, interim wildfire after-action report (April 2026)",
              ["gov.mb.ca", "manitoba.ca"]),
    "rd-nt": ("Government of the Northwest Territories; Legislative Assembly of the Northwest Territories", "Main Estimates 2026-27, supplementary estimates, 2023 wildfire response review (MNP), response to the 2023 after-action review, air tanker fleet pages",
              ["nt.ca"]),
    "rd-yt": ("Government of Yukon", "Community Services main estimates, fall 2025 supplementary estimates and wildland fire releases",
              ["yukon.ca"]),
    "rd-nu": ("Government of Nunavut", "Nunavut and the Canadian Interagency Forest Fire Centre formalize wildfire cooperation (June 2026)",
              ["gov.nu.ca"]),
    "rd-on": ("Government of Ontario; Auditor General of Ontario; Legislative Assembly of Ontario", "Expenditure estimates, Ministry of Natural Resources 2026-27; public accounts (emergency fire fighting); follow-up on management of hazards and emergencies (2024); estimates committee transcript (2024); newsroom releases",
              ["ontario.ca", "auditor.on.ca", "ola.org"]),
    "rd-qc": ("SOPFEU; Gouvernement du Québec", "SOPFEU annual reports 2022 to 2025; Budget 2026-2027; Service aérien gouvernemental airtanker fleet",
              ["sopfeu.qc.ca", "finances.gouv.qc.ca", "quebec.ca"]),
    "rd-nb": ("Government of New Brunswick", "Wildfire Management Preparedness Plan 2025-2030; Main Estimates 2026-27; wildfire releases 2026",
              ["gnb.ca"]),
    "rd-ns": ("Government of Nova Scotia", "2023 Wildfires After-Action Report; estimates 2024-25 to 2026-27 and additional appropriations; wildfire releases",
              ["gov.ns.ca", "novascotia.ca"]),
    "rd-nl": ("Government of Newfoundland and Labrador", "News releases 2025 and 2026 on water bombers, Labrador, Budget 2026 and the Auditor General's emergency management report",
              ["gov.nl.ca", "ag.gov.nl.ca"]),
    "rd-pe": ("Government of Prince Edward Island", "Wildfire response page", ["princeedwardisland.ca"]),
    "rd-pc": ("Parks Canada", "Question period notes and wildfire management pages", ["open.canada.ca/qpnotes", "parks.canada.ca"]),
    "ciffc-reports": ("Canadian Interagency Forest Fire Centre", "Canada Reports 2022 to 2025, annual reports 2023-24 and 2024-25, Strategic Plan 2024-2029, Aviation Challenges Workshop Report (2023), financial statements",
                      ["ciffc.ca"]),
    "ps-pcaa": ("Public Safety Canada", "Pan-Canadian Aerial Asset Program: backgrounder and releases (2025, 2026)", ["public-safety-canada"]),
    "senate-agfo": ("Senate of Canada, Standing Committee on Agriculture and Forestry", "Canada on fire (June 2026)", ["sencanada.ca"]),
    "fed-budgets": ("Department of Finance Canada", "Federal budgets 2019 to 2025, fall economic statements and the 2026 Economic and Fiscal Update", ["budget.canada.ca"]),
    "gc-infobase": ("Treasury Board of Canada Secretariat", "GC InfoBase open data: program spending, results and transfer payments", ["a35cf382-690c-4221-a971-cf0fd189a46f"]),
    "nrcan-programs": ("Natural Resources Canada", "Departmental Results Report 2024-25 and wildfire program pages (Fighting and Managing Wildfires in a Changing Climate, Wildfire Resilient Futures Initiative, WildFireSat)",
                       ["natural-resources.canada.ca", "canada.ca/en/natural-resources-canada", "canada.ca/fr/ressources-naturelles-canada"]),
    "nas": ("Government of Canada", "National Adaptation Strategy", ["climate-plan/national-adaptation-strategy", "national-adaptation"]),
    "grants-disclosure": ("Government of Canada", "Proactive disclosure of grants and contributions (wildfire agreements active after October 22, 2026)", ["432527ab-7aac-45b5-81d6-7597107a7013"]),
}
EXTRA = [
    {"id": "cihi-nacrs", "publisher": "Canadian Institute for Health Information",
     "title": "NACRS emergency department visits data tables, April 2021 to March 2026",
     "version": "Monthly, by province and age group", "url": "https://www.cihi.ca/sites/default/files/document/emergency-department-visits-apr-2025-mar-2026-data-tables-en.xlsx",
     "licence": "CIHI terms of use", "accessed": "2026-10-21"},
    {"id": "coverage-check", "publisher": "The Median Canadian",
     "title": "Coverage check of publicly reported major fires against NBAC and CWFIS outlines (analysis/coverage)",
     "version": "65 fires, 2023 to 2026", "url": "https://github.com/sjvadrevu/canada-wildfires-2026/tree/main/analysis/coverage",
     "licence": "Apache 2.0 (code), CC BY 4.0 (results)", "accessed": "2026-10-22"},
]


def urls_of(cell):
    out = []
    for u in re.split(r"\s;\s|\s+;|;\s+", str(cell or "")):
        u = u.strip().split(" ")[0].rstrip(",")
        if u.startswith("http"):
            out.append(u)
    return out


def main():
    rows = []
    for f, ucol, acol in [("readiness/manifest_west.csv", "url", "accessed"), ("readiness/manifest_east.csv", "url", "accessed"),
                          ("policy/manifest.csv", "url", "accessed")]:
        for r in csv.DictReader(open(os.path.join(A, f), encoding="utf-8")):
            if str(r.get("source", r.get("file", ""))).startswith("NOT REACHED"):
                continue
            for u in urls_of(r[ucol]):
                rows.append((u, r.get(acol) or "2026-10-22"))
    for r in csv.DictReader(open(os.path.join(A, "readiness/gaps_west.csv"), encoding="utf-8")):
        rows += [(u, r.get("accessed") or "2026-10-22") for u in urls_of(r.get("url"))]
    for r in csv.DictReader(open(os.path.join(A, "readiness/gaps_east.csv"), encoding="utf-8")):
        rows += [(u, r.get("accessed") or "2026-10-22") for u in urls_of(r.get("url"))]
    bucket = {k: [] for k in GROUPS}
    for u, acc in rows:
        for k, (_, _, pats) in GROUPS.items():
            if any(p in u for p in pats):
                if u not in [x[0] for x in bucket[k]]:
                    bucket[k].append((u, acc))
                break
    new = []
    for k, (pub, title, _) in GROUPS.items():
        if not bucket[k]:
            print("no url for", k)
            continue
        us = bucket[k]
        new.append({"id": k, "publisher": pub, "title": title, "version": "Documents listed in analysis/readiness and analysis/policy manifests",
                    "url": us[0][0], "links": [{"label": urlparse(u).netloc.replace("www.", ""), "url": u} for u, _ in us[1:8]],
                    "licence": "Open Government Licence or the publisher's terms", "accessed": max(a for _, a in us)})
    new += EXTRA
    p = os.path.join(ROOT, "data/references.json")
    d = json.load(open(p, encoding="utf-8"))
    ids = {r["id"] for r in new}
    d["references"] = [r for r in d["references"] if r["id"] not in ids] + new
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(d["references"]), "references;", len(new), "added or replaced")


if __name__ == "__main__":
    main()
