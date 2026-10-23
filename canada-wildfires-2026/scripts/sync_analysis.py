#!/usr/bin/env python3
"""Copy the analysis (scripts, results, manifests, derived outputs) from a working folder into this repo.

Rerunnable. Every run applies the same rules:

- analysis/<topic>/: scripts/ (recursively), results.md, manifest.csv and every top-level output file.
  raw/ and work/ are skipped, except the small work files listed in WORK_ALLOW (published numbers are
  read from them). Topic folders whose name starts with "_" (for example _before_rebuild) are skipped.
- data/<group>/: manifest.csv, scripts/ and top-level derived files (plus data/fire/reference and
  data/geo/mb_qc_subareas, same rules). Raw downloads are skipped; scripts/download_data.py fetches them.
- story/: claims_draft.md and verified_numbers.json; story/verification.md goes to methods/verification.md.
- slides/: the carousel builders (make_slides_merge.py builds the final 8 slides). site-build/: the per-area union table the map reads.
- Any file over MAX_MB, any *.log, __pycache__ and *.pyc are skipped.

Machine-specific absolute paths are rewritten on the way in:
- Python: the working-folder prefix becomes an expression that reads the WILDFIRE_ROOT environment
  variable and otherwise falls back to the repo root (found from the script's own location).
- Shell: the same, with ${WILDFIRE_ROOT:-<repo root from $0>}.
- A hard-coded proxy CA bundle passed to GDAL is removed (GDAL still reads CURL_CA_BUNDLE from the
  environment if you set it).
- Text files (md, csv, json, txt): the working-folder prefix is removed, so paths read repo-relative.

Every skipped file over MAX_MB is listed individually, and every skipped raw/ or work/ folder is listed with
its file count and size, in methods/skipped_files.csv, with how to regenerate it.

Usage:
    python scripts/sync_analysis.py --src /path/to/wildfire                      # every topic
    python scripts/sync_analysis.py --src /path/to/wildfire --exclude response wainwright
    python scripts/sync_analysis.py --src /path/to/wildfire --topics response wainwright --no-shared
The source folder can also be given with WILDFIRE_SRC.
"""
import argparse
import csv
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_MB = 20.0
SKIP_DIRS = {"raw", "work", "__pycache__"}
SKIP_SUFFIX = {".log", ".pyc"}
TEXT_SUFFIX = {".md", ".csv", ".json", ".txt", ".geojson", ".xml", ".yml", ".yaml", ".R", ".sql"}

# Small work files that published numbers or the site build read (path relative to the source root).
WORK_ALLOW = [
    # Climate panel and correlations for the fma_v2 areas (REBUILD.md section 2, "Climate"); the cause model
    # (C15, C12) reads climate_panel.csv from here.
    "analysis/climate/work/areas_fcd292dde04d/*.csv",
    "analysis/climate/work/areas_fcd292dde04d/*.json",
]
DATA_GROUPS = ["fire", "geo", "smoke-cost", "geo/mb_qc_subareas"]
DATA_EXTRA_DIRS = ["data/fire/reference"]
# Top-level data files skipped on purpose: a raw download kept at top level, and alternative Manitoba and
# Quebec zone layers that build_fma_v2.py does not use (it uses mb_fire_restriction_areas and
# qc_sopfeu_fire_danger_zones).
DATA_SKIP = {
    "data/fire/cwfis_hotspots_2026_canada.csv.gz": "raw download (CWFIS 2026 hotspots CSV)",
    "data/geo/mb_qc_subareas/mb_fire_regions.gpkg": "alternative layer, not used by fma_v2",
    "data/geo/mb_qc_subareas/mb_forest_sections.gpkg": "alternative layer, not used by fma_v2",
    "data/geo/mb_qc_subareas/qc_admin_regions.gpkg": "alternative layer, not used by fma_v2",
    "data/geo/mb_qc_subareas/qc_sopfeu_protection_zones.gpkg": "alternative layer, not used by fma_v2",
}
STORY = {"story/claims_draft.md": "story/claims_draft.md",
         "story/verified_numbers.json": "story/verified_numbers.json",
         "story/verification.md": "methods/verification.md"}
SLIDES = ["slides/make_slides.py", "slides/make_slides_photo.py", "slides/make_slides_merge.py",
          "slides/option_visuals.py", "slides/canmap.py"]
SITE_BUILD = ["site-build/fma_union_2023_2026.csv"]
SHARED_DOCS = ["analysis/REBUILD.md"]
# Snapshots of live official feeds (NRCan CIFFC/CWFIS API, NFD tables, SOPFEU points) that the cause and forest
# scripts read from season/. A live API cannot return the same snapshot later, so these are kept as dated copies.
SEASON_FILES = [
    "season/nrcan_fire_list.json",
    "season/nrcan_ytd_by-agency_by-response-type_group_by_stage_of_control_true_group_by_status_true_group_by_cause_true.json",
    "season/nrcan_ytd_by-agency.json",
    "season/NFD_-_Area_burned_by_cause_class_-_EN_FR.csv",
    "season/NFD_-_Number_of_fires_by_cause_class_-_EN_FR.csv",
    "season/NFD_-_Area_burned_by_month_-_EN_FR.csv",
    "season/perimeters/qc_points_feux_historique_2026.geojson",
]

PY_ROOT = ('__import__("os").environ.get("WILDFIRE_ROOT", '
           'str(__import__("pathlib").Path(__file__).resolve().parents[{depth}]))')
SH_ROOT = '${{WILDFIRE_ROOT:-$(cd "$(dirname "$0")/{up}" && pwd)}}'


def rewrite(text, suffix, rel_parts, src_prefixes):
    """Rewrite absolute working-folder paths. rel_parts = path parts of the file inside the repo."""
    depth = len(rel_parts) - 1  # parents[depth] of the file is the repo root; also the number of ../ steps
    for pre in src_prefixes:
        if suffix == ".py":
            # "PRE/x/y" -> (ROOT_EXPR + "/x/y");  "PRE" -> ROOT_EXPR
            text = re.sub(r'(["\'])' + re.escape(pre) + r'(/[^"\']*)?\1',
                          lambda m: (PY_ROOT.format(depth=depth) +
                                     (f' + "{m.group(2)}"' if m.group(2) else "")), text)
        elif suffix == ".sh":
            up = "/".join([".."] * depth) or "."
            text = text.replace(pre, SH_ROOT.format(up=up))
        else:
            text = text.replace(pre + "/", "").replace(pre, ".")
    text = re.sub(r',\s*CURL_CA_BUNDLE="/[^"]*ca-bundle[^"]*"', "", text)
    if suffix == ".py":
        # the repo carries no literal em dash character; a plain string holding one becomes its escape (same value)
        text = text.replace('"\u2014"', '"\\u2014"')
    return text


def copy_file(src, dst, rel_parts, prefixes, log):
    dst.parent.mkdir(parents=True, exist_ok=True)
    suf = src.suffix
    if suf in TEXT_SUFFIX or suf in {".py", ".sh"}:
        try:
            t = src.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(src, dst)
            log["copied"] += 1
            return
        t2 = rewrite(t, suf, rel_parts, prefixes)
        if t2 != t:
            log["rewritten"].append(str(Path(*rel_parts)))
        if not dst.exists() or dst.read_text(encoding="utf-8", errors="replace") != t2:
            dst.write_text(t2, encoding="utf-8")
    else:
        if not dst.exists() or dst.stat().st_size != src.stat().st_size or dst.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, dst)
    log["copied"] += 1
    log["bytes"] += src.stat().st_size


def too_big(p):
    return p.stat().st_size > MAX_MB * 1e6


def dir_stats(d):
    n = s = 0
    for p in d.rglob("*"):
        if p.is_file():
            n += 1
            s += p.stat().st_size
    return n, s


def writer_scripts(name, script_dirs):
    """Scripts that mention a file name (best guess at what writes or downloads it)."""
    hits = []
    for sd in script_dirs:
        if not sd.exists():
            continue
        for p in sorted(sd.rglob("*")):
            if p.suffix in {".py", ".sh"} and "__pycache__" not in p.parts and "manifest" not in p.name:
                try:
                    if name in p.read_text(encoding="utf-8", errors="ignore"):
                        hits.append(p)
                except OSError:
                    pass
    return hits


def regen_note(rel, src_root, kind):
    parts = Path(rel).parts
    if parts[0] == "analysis":
        topic = parts[1]
        sdirs = [src_root / "analysis" / topic / "scripts"]
    else:
        sdirs = [src_root / "data" / parts[1] / "scripts", src_root / "data" / "geo" / "mb_qc_subareas" / "scripts"]
    name = Path(rel).name
    hits = writer_scripts(name, sdirs)
    stem_hits = [] if hits else writer_scripts(Path(rel).stem.split("_20")[0], sdirs)
    refs = ", ".join(str(h.relative_to(src_root)) for h in (hits or stem_hits)[:3])
    if kind in ("raw folder", "download folder") or "raw" in parts or "download folder" in kind:
        base = "Public download: python scripts/download_data.py (see data/SOURCES.md)"
        return base + (f"; fetched or read by {refs}" if refs else "")
    if kind == "work folder" or "work" in parts:
        return ("Intermediate: rerun the topic's scripts in the order in REPRODUCE.md"
                + (f"; written or read by {refs}" if refs else ""))
    if parts[0] == "data" and len(parts) >= 3 and parts[2] not in ("scripts",) and not refs:
        return "Public download: python scripts/download_data.py (see data/SOURCES.md)"
    return "Derived: rerun " + (refs if refs else "the folder's scripts (REPRODUCE.md)")


def sync(args):
    src = Path(args.src).resolve()
    if not (src / "analysis").is_dir():
        sys.exit(f"{src} has no analysis/ folder")
    prefixes = sorted({str(src), os.path.realpath(src)}, key=len, reverse=True)
    log = {"copied": 0, "bytes": 0, "rewritten": []}
    skipped = []  # (path, bytes, kind, files)

    topics = sorted(p.name for p in (src / "analysis").iterdir() if p.is_dir() and not p.name.startswith("_"))
    if args.topics:
        topics = [t for t in topics if t in args.topics]
    topics = [t for t in topics if t not in (args.exclude or [])]

    def walk(sub_src, sub_rel, allow_subdirs=True):
        for p in sorted(sub_src.iterdir()):
            rel = Path(sub_rel) / p.name
            if p.is_dir():
                if p.name in SKIP_DIRS:
                    if p.name != "__pycache__":
                        n, s = dir_stats(p)
                        skipped.append((str(rel) + "/", s, f"{p.name} folder", n))
                    continue
                if allow_subdirs:
                    walk(p, rel, allow_subdirs)
                continue
            if p.suffix in SKIP_SUFFIX:
                continue
            if too_big(p):
                skipped.append((str(rel), p.stat().st_size, "over size limit", 1))
                continue
            copy_file(p, ROOT / rel, rel.parts, prefixes, log)

    for t in topics:
        tsrc = src / "analysis" / t
        # top-level files only (raw/ and work/ are skipped, scripts/ is walked)
        for p in sorted(tsrc.iterdir()):
            rel = Path("analysis") / t / p.name
            if p.is_dir():
                if p.name == "scripts":
                    walk(p, rel)
                elif p.name in SKIP_DIRS:
                    n, s = dir_stats(p)
                    skipped.append((str(rel) + "/", s, f"{p.name} folder", n))
                else:
                    walk(p, rel)
                continue
            if p.suffix in SKIP_SUFFIX:
                continue
            if too_big(p):
                skipped.append((str(rel), p.stat().st_size, "over size limit", 1))
                continue
            copy_file(p, ROOT / rel, rel.parts, prefixes, log)
        print(f"analysis/{t}: done")

    allow_files = []
    for pat in WORK_ALLOW:
        if pat.split("/")[1] in topics:
            allow_files += sorted(src.glob(pat))
    for p in allow_files:
        if not too_big(p):
            rel = p.relative_to(src)
            copy_file(p, ROOT / rel, rel.parts, prefixes, log)

    if not args.no_shared:
        for g in DATA_GROUPS:
            gsrc = src / "data" / g
            if not gsrc.is_dir():
                continue
            for p in sorted(gsrc.iterdir()):
                rel = Path("data") / g / p.name
                if p.is_dir():
                    if p.name == "scripts":
                        walk(p, rel)
                    elif str(rel) in DATA_EXTRA_DIRS:
                        walk(p, rel)
                    elif ("data/" + g + "/" + p.name) in [f"data/{x}" for x in DATA_GROUPS]:
                        continue  # handled as its own group
                    else:
                        n, s = dir_stats(p)
                        skipped.append((str(rel) + "/", s, "raw folder" if p.name == "raw" else "download folder", n))
                    continue
                if p.suffix in SKIP_SUFFIX or p.suffix == ".png":
                    continue
                if str(rel) in DATA_SKIP:
                    skipped.append((str(rel), p.stat().st_size, DATA_SKIP[str(rel)], 1))
                    (ROOT / rel).unlink(missing_ok=True)
                    continue
                if too_big(p):
                    skipped.append((str(rel), p.stat().st_size, "over size limit", 1))
                    continue
                copy_file(p, ROOT / rel, rel.parts, prefixes, log)
        for s_rel, d_rel in STORY.items():
            if (src / s_rel).exists():
                copy_file(src / s_rel, ROOT / d_rel, Path(d_rel).parts, prefixes, log)
        for rel in SLIDES + SITE_BUILD + SHARED_DOCS + SEASON_FILES:
            if (src / rel).exists():
                copy_file(src / rel, ROOT / rel, Path(rel).parts, prefixes, log)

    # skipped-file list: merge with the existing one so partial runs keep other topics' rows
    out = ROOT / "methods" / "skipped_files.csv"
    out.parent.mkdir(exist_ok=True)
    rows = {}
    if out.exists():
        with open(out, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["path"]] = r
    scopes = [f"analysis/{t}/" for t in topics] + ([] if args.no_shared else ["data/"])
    rows = {k: v for k, v in rows.items() if not any(k.startswith(s) for s in scopes)}
    for rel, size, kind, n in skipped:
        rows[rel] = {"path": rel, "kind": kind, "files": n, "size_mb": f"{size / 1e6:.1f}",
                     "regenerate": regen_note(rel, src, kind)}
        if kind.endswith("folder"):
            # list every large file inside the skipped folder individually as well
            for p in sorted((src / rel).rglob("*")):
                if p.is_file() and too_big(p):
                    r2 = str(p.relative_to(src))
                    rows[r2] = {"path": r2, "kind": "large file in " + kind, "files": 1,
                                "size_mb": f"{p.stat().st_size / 1e6:.1f}", "regenerate": regen_note(r2, src, kind)}
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "kind", "files", "size_mb", "regenerate"])
        w.writeheader()
        for k in sorted(rows):
            w.writerow(rows[k])
    print(f"copied {log['copied']} files ({log['bytes'] / 1e6:.1f} MB); rewrote paths in {len(log['rewritten'])}; "
          f"skipped list: {out.relative_to(ROOT)} ({len(rows)} rows)")
    for r in log["rewritten"]:
        print("  path rewrite:", r)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=os.environ.get("WILDFIRE_SRC"), required=os.environ.get("WILDFIRE_SRC") is None,
                    help="working folder that holds analysis/, data/, story/ (or set WILDFIRE_SRC)")
    ap.add_argument("--topics", nargs="*", help="only these analysis topics")
    ap.add_argument("--exclude", nargs="*", help="skip these analysis topics")
    ap.add_argument("--no-shared", action="store_true", help="skip data/, story/, slides/, site-build/")
    sync(ap.parse_args())
