#!/usr/bin/env python3
"""Build data/sources.csv and data/SOURCES.md from every manifest.csv in the repo.

The manifests were written by each analysis step and use different column names. This script maps them to one
schema, classifies each row, and records how scripts/download_data.py fetches it:

- direct: one plain file URL; download_data.py fetches it into data/raw/ and links it to where the scripts read it.
- fetch script: a query, template or API that a script in the repo fetches (the script is named).
- manual: a web page, document or service that has no single-file URL; open the URL.
- snapshot in repo: a dated copy of a live feed kept in the repo (data/fire/reference, season/).
- derived: built by a script in this repo; not downloaded.
- not used: rows the manifests record as failed, not found or not used (kept so the search is visible).

Licences come from the manifests. Where a manifest has no licence column (analysis/climate,
analysis/climate-change, analysis/wainwright), the licence is filled from the publisher and marked
"(not in manifest)".

Usage: python scripts/build_sources.py
"""
import csv
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE_EXT = (".zip", ".csv", ".gz", ".bz2", ".tif", ".tiff", ".xlsx", ".xls", ".json", ".geojson", ".gpkg", ".shp",
            ".pdf", ".txt", ".ascii", ".dat", ".nc", ".doc", ".docx", ".jpg", ".xml", ".data")
TEMPLATE = re.compile(r"[{}<>]|YYYY|YYMM|\.\.")

PUBLISHER_LICENCE = [  # used only when the manifest has no licence column
    ("ECCC", "Open Government Licence - Canada (not in manifest)"),
    ("Environment and Climate Change", "Open Government Licence - Canada (not in manifest)"),
    ("NRCan", "Open Government Licence - Canada (not in manifest)"),
    ("NOAA", "US Government work, public domain (not in manifest)"),
    ("Zenodo", "see Zenodo record (not in manifest)"),
    ("Statistics Canada", "Statistics Canada Open Licence (not in manifest)"),
    ("Government of Alberta", "Open Government Licence - Alberta (not in manifest)"),
]


def g(r, *keys):
    for k in keys:
        if r.get(k):
            return r[k].strip()
    return ""


def urls(text):
    return re.findall(r"(?:https?|ftp)://[^\s;,()]+", text)


def scripts_text():
    out = {}
    for p in list(ROOT.glob("analysis/*/scripts/**/*")) + list(ROOT.glob("data/**/scripts/*")):
        if p.is_file() and p.suffix in (".py", ".sh"):
            out[p] = p.read_text(encoding="utf-8", errors="ignore")
    return out


def classify(dataset, publisher, url_field, local, date, scope, S):
    d = dataset.upper()
    if "reference/" in local or "season/" in local:
        return "snapshot in repo", ""
    if d.startswith(("FAILED", "NOT FOUND", "NOT USED", "SUPERSEDED")) or "not downloaded" in local.lower() \
            or "downloaded, not used" in dataset or "checked only" in dataset:
        return "not used", ""
    low = (publisher + " " + url_field).lower()
    if ("derived" in low or "this project" in low or date == "reused" or url_field.startswith(("see ", "scripts/"))
            or publisher.startswith("analysis/") or not url_field):
        if "reference/" in local or "season/" in local:
            return "snapshot in repo", ""
        return "derived", ""
    u = urls(url_field)
    if not u:
        return "manual", ""
    first = u[0].rstrip(".")
    # a fetch script in the repo that names this host and path
    key = re.sub(r"^(?:https?|ftp)://", "", first).split("?")[0]
    key = "/".join(key.split("/")[:4])
    tn = re.search(r"typeNames?[= ]+(?:pub:)?([A-Za-z0-9_.:]+)", url_field)
    if tn:
        key = tn.group(1).split(":")[-1]
    hits = sorted({str(p.relative_to(ROOT)) for p, t in S.items()
                   if key and key in t and "manifest" not in p.name})
    if TEMPLATE.search(url_field.split(";")[0]) or "typeName" in url_field or "/query" in first \
            or "MapServer" in first or "FeatureServer" in first or "wfs" in first.lower() or "api/" in first and "api/file" not in first:
        return ("fetch script" if hits else "manual"), "; ".join(hits[:3])
    if first.lower().split("?")[0].endswith(FILE_EXT) or "api/file?path=" in first:
        if "earlier" in date or "earlier" in url_field:
            return "direct", "; ".join(hits[:3])
        return "direct", "; ".join(hits[:3])
    return ("fetch script" if hits else "manual"), "; ".join(hits[:3])


def first_local(local):
    t = re.split(r"\s*[;(]\s*|\s+\.\.\s+|\s+\+\s+", local)[0].strip()
    t = t.split(" ")[0]
    return t if "/" in t or "." in t else ""


def expected(scope, local):
    t = first_local(local)
    if not t:
        return ""
    p = t if t.startswith(("data/", "analysis/")) else f"{scope}/{t}"
    p = os.path.normpath(p) + ("/" if t.endswith("/") else "")
    return p


def used_by(local, scope, S):
    name = Path(first_local(local)).name if first_local(local) else ""
    topics = set()
    if scope.startswith("analysis/"):
        topics.add(scope.split("/")[1])
    if name and not any(c in name for c in "*<>{}"):
        for p, t in S.items():
            if name in t and p.parts[len(ROOT.parts)] == "analysis":
                topics.add(p.parts[len(ROOT.parts) + 1])
            elif name in t:
                topics.add("data/" + p.parts[len(ROOT.parts) + 1])
    return ", ".join(sorted(topics))


def main():
    S = scripts_text()
    rows = []
    mans = sorted(ROOT.glob("data/**/manifest.csv")) + sorted(ROOT.glob("analysis/*/manifest.csv"))
    for m in mans:
        scope = str(m.parent.relative_to(ROOT))
        with open(m, encoding="utf-8") as f:
            for i, r in enumerate(csv.DictReader(f), 1):
                dataset = g(r, "dataset", "description")
                publisher = g(r, "publisher", "source")
                url_field = g(r, "source_url", "url")
                local = g(r, "local_path", "path")
                date = g(r, "date_downloaded", "date_accessed", "downloaded")
                lic = g(r, "licence")
                if not lic and "licence" not in r:
                    lic = next((v for k, v in PUBLISHER_LICENCE if k.lower() in publisher.lower()), "")
                if re.search(r"microsoft|building footprint", dataset + publisher, re.I):
                    lic = "ODbL 1.0 (derived building data published here is also ODbL 1.0)"
                status, via = classify(dataset, publisher, url_field, local, date, scope, S)
                u = urls(url_field)
                rows.append({
                    "id": f"{scope.replace('/', '.')}.{i:02d}", "manifest": f"{scope}/manifest.csv", "row": i,
                    "dataset": dataset, "publisher": publisher, "url": u[0].rstrip(".") if u else "",
                    "url_field": url_field, "licence": lic, "date_accessed": date,
                    "used_for": g(r, "used_in") or used_by(local, scope, S),
                    "expected_path": expected(scope, local),
                    "status": status, "scripts_naming_source": via,
                    "sha256_16": g(r, "sha256_16"),
                })
    with open(ROOT / "data" / "sources.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def cell(s, n=None):
        s = (s or "").replace("|", "/").replace("\n", " ")
        return s if n is None or len(s) <= n else s[: n - 1].rstrip() + "..."

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    L = ["# Data sources", "",
         "Every dataset listed in the project's manifests, generated by `scripts/build_sources.py` from each "
         "`manifest.csv` (the machine-readable version is `data/sources.csv`). Each manifest holds fuller "
         "validation notes for its rows.", "",
         "Download everything that has a plain file URL with `python scripts/download_data.py` (files go to "
         "`data/raw/` and are linked to the path the scripts read). Rows marked *fetch script* are downloaded by the "
         "named script, because they are queries or per-station or per-day requests. Rows marked *manual* are web "
         "pages, PDFs or services without a single-file URL (the manifest's own notes say how each was read). "
         "The script names come from a search of the repo's scripts for the URL or layer name, so treat them as a "
         "pointer, not a guarantee. *Snapshot in repo* rows are dated copies of live feeds "
         "kept in the repo, because the live feed cannot return the same numbers later.", "",
         "## Licences", "",
         "- Most federal data: Open Government Licence - Canada; Statistics Canada data: Statistics Canada Open Licence. "
         "Provincial data: the province's open government licence where one is stated; the manifests say where none was.",
         "- **Microsoft Global ML Building Footprints are ODbL 1.0.** Any building data derived from them and published "
         "here (for example `analysis/losses/buildings_2026_near_outlines.gpkg` and the building counts in "
         "`analysis/losses/` and `analysis/property/`) is also made available under ODbL 1.0, with attribution to "
         "Microsoft.",
         "- Copernicus Sentinel-2 data: Copernicus open data terms (contains modified Copernicus Sentinel data 2023 to 2026).",
         "- Matz et al. 2026 supporting information (AQBAT coefficients): CC BY-NC 4.0, as recorded in the manifest.",
         "- Where a licence cell says \"(not in manifest)\", the manifest had no licence column and the licence was filled "
         "from the publisher.", "",
         "Row counts by status: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + ".", ""]
    for man in [str(m.relative_to(ROOT)) for m in mans]:
        rs = [r for r in rows if r["manifest"] == man]
        L += [f"## `{man}`", "",
              "| ID | Dataset | Publisher | URL | Licence | Accessed | Used for | Status |",
              "|---|---|---|---|---|---|---|---|"]
        for r in rs:
            url = f"[link]({r['url']})" if r["url"] else cell(r["url_field"], 60)
            st = r["status"] + (f" (named in {r['scripts_naming_source']})"
                                if r["scripts_naming_source"] and r["status"] != "direct" else "")
            L.append(f"| {r['id']} | {cell(r['dataset'], 110)} | {cell(r['publisher'], 60)} | {url} | "
                     f"{cell(r['licence'], 70)} | {cell(r['date_accessed'], 24)} | {cell(r['used_for'], 60)} | {cell(st)} |")
        L.append("")
    (ROOT / "data" / "SOURCES.md").write_text("\n".join(L), encoding="utf-8")
    print(f"{len(rows)} rows; " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
