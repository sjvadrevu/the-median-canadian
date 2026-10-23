#!/usr/bin/env python3
"""Download the raw public datasets that have a plain file URL, from the official source.

Reads data/sources.csv (built by scripts/build_sources.py from every manifest.csv). For each row with status
"direct" it downloads the file into data/raw/<manifest folder>/ and links it to the path the analysis scripts
read (the manifest's local_path), so the scripts find it without changes.

Rows that are queries, per-station or per-day requests (status "fetch script") are downloaded by the analysis
scripts themselves; see data/SOURCES.md and REPRODUCE.md. Rows marked "manual" are web pages or documents.

Notes:
- Live feeds change. A file downloaded today can differ from the copy used for the story (accessed
  2026-10-20 to 2026-10-22). Where a manifest recorded a hash (sha256_16), it is checked and a mismatch is
  reported, not fatal. Dated snapshots of the live official totals are kept in the repo (data/fire/reference,
  season/).
- Some files are large (Land Cover 2020 is about 2.1 GB, the NBAC zip about 1.3 GB, NFDB polygons about
  0.8 GB). Use --max-mb to skip large files or --only to pick rows.
- Archives are linked as downloaded. Where a script reads the unpacked files (for example NBAC, read from
  data/fire/raw/nbac/shp/), unzip the archive in that folder; the manifest's local_path says which.
- Uses only the Python standard library. Proxies and CA bundles come from the usual environment variables
  (HTTPS_PROXY, SSL_CERT_FILE).

Usage:
    python scripts/download_data.py --list
    python scripts/download_data.py                      # every direct row
    python scripts/download_data.py --only nbac ahccd    # rows whose id, dataset or URL contains a word
    python scripts/download_data.py --dry-run
"""
import argparse
import csv
import hashlib
import os
import shutil
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

# Rows whose manifest lists several files under one URL pattern: the full list of files to fetch.
EXTRA = {
    "data.fire.01": [f"https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/perimeters.{e}" for e in
                     ("shp", "dbf", "shx", "prj", "cpg")],
    "data.fire.02": [f"https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/progression.{e}" for e in
                     ("shp", "dbf", "shx", "prj", "cpg")],
    "data.fire.19": [f"https://cwfis.cfs.nrcan.gc.ca/downloads/fwi_obs/cwfis_fwi{d}sv3.0_ll.csv.bz2" for d in
                     ("1990", "2000", "2010", "2020")],
}


def fname(url):
    p = urlparse(url)
    if "api/file" in p.path and "path=" in p.query:
        return unquote(p.query.split("path=")[1].split("&")[0]).rstrip("/").split("/")[-1]
    return unquote(p.path.rstrip("/").split("/")[-1]) or "download"


def link(target, expected, many=False):
    """Make expected point at target (relative symlink); copy if symlinks are not available."""
    if not expected:
        return
    exp = ROOT / expected
    if expected.endswith("/") or (exp.exists() and exp.is_dir()) or not Path(expected).suffix:
        exp = exp / target.name
    elif many or any(c in exp.name for c in "*?<>{}") or exp.suffix.lower() != target.suffix.lower():
        # several files, a wildcard, or a different file type (for example a zip the scripts read unpacked):
        # link the file under its own name in the folder the scripts read from
        exp = exp.parent / target.name
    if exp.exists() or exp.is_symlink():
        return
    exp.parent.mkdir(parents=True, exist_ok=True)
    try:
        exp.symlink_to(os.path.relpath(target, exp.parent))
    except OSError:
        shutil.copy2(target, exp)


def fetch(url, dest, max_mb):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return "exists"
    req = urllib.request.Request(url, headers={"User-Agent": "canada-wildfires-2026 reproducibility download"})
    with urllib.request.urlopen(req, timeout=120) as r:
        size = int(r.headers.get("Content-Length") or 0)
        if max_mb and size > max_mb * 1e6:
            return f"skipped ({size / 1e6:.0f} MB > --max-mb)"
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            shutil.copyfileobj(r, f, length=1 << 20)
        tmp.rename(dest)
    return f"ok ({dest.stat().st_size / 1e6:.1f} MB)"


def main():
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list rows and their status, download nothing")
    ap.add_argument("--only", nargs="*", help="only rows whose id, dataset or URL contains one of these words")
    ap.add_argument("--max-mb", type=float, default=0, help="skip files larger than this (0 = no limit)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rows = list(csv.DictReader(open(ROOT / "data" / "sources.csv", encoding="utf-8")))
    if a.only:
        rows = [r for r in rows if any(w.lower() in (r["id"] + r["dataset"] + r["url"]).lower() for w in a.only)]
    if a.list:
        for r in rows:
            print(f"{r['id']:32} {r['status']:16} {r['dataset'][:70]}")
        return
    fails = 0
    for r in rows:
        if r["status"] != "direct":
            continue
        scope = r["manifest"].rsplit("/", 1)[0]
        for url in EXTRA.get(r["id"], [r["url"]]):
            dest = RAW / scope / fname(url)
            if a.dry_run:
                print(f"{r['id']}: {url} -> {dest.relative_to(ROOT)} (link: {r['expected_path'] or 'none'})")
                continue
            try:
                st = fetch(url, dest, a.max_mb)
                if dest.exists():
                    link(dest, r["expected_path"], many=r["id"] in EXTRA)
                    if r.get("sha256_16"):
                        h = hashlib.sha256(dest.read_bytes()).hexdigest()[:16]
                        if h != r["sha256_16"]:
                            st += f"; hash differs from manifest ({h} vs {r['sha256_16']}): the source has changed"
            except Exception as e:  # report and continue
                st = f"FAILED: {e}"
                fails += 1
            print(f"{r['id']}: {st}  {url}")
    if fails:
        print(f"{fails} downloads failed; see data/SOURCES.md for the source page of each.", file=sys.stderr)


if __name__ == "__main__":
    main()
