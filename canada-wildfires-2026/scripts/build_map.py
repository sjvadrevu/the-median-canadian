"""Build the map data in data/map/ from the analysis outputs.

Geometry is projected to Canada Atlas Lambert (EPSG:3978 parameters), simplified and written as
quantized TopoJSON with mapshaper (npm package mapshaper; set MAPSHAPER to its path if it is not on PATH).
Attributes are written by Python so every number is rounded on purpose.

    python scripts/build_map.py --src /path/to/wildfire

Needs site-build/fma_union_2023_2026.csv (made by scripts/fma_union.py) for the 2023 to 2026 union shares.
"""
import argparse
import csv
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "map"
DEFAULT_SRC = Path(os.environ.get("WILDFIRE_SRC", "../wildfire"))
PROJ = "+proj=lcc +lat_1=49 +lat_2=77 +lat_0=49 +lon_0=-95 +datum=NAD83 +units=m +no_defs"
MS = os.environ.get("MAPSHAPER", "mapshaper")


def ms(*args):
    cmd = [MS, *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr)


def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(x):
    if x in (None, "", "nan", "NaN"):
        return None
    v = float(x)
    return None if math.isnan(v) else v


def sig(x, n=3):
    if x is None:
        return None
    if x == 0:
        return 0
    return round(x, max(0, n - 1 - int(math.floor(math.log10(abs(x))))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    a = ap.parse_args()
    A = a.src / "analysis"
    OUT.mkdir(parents=True, exist_ok=True)
    q = "quantization=40000"

    # 1. Fire management areas + provinces dissolved from them (shared arcs, so borders match)
    ms("-i", A / "forest/fma_2026.geojson", "name=areas", "-proj", PROJ,
       "-filter-fields", "fma_id,province", "-rename-fields", "id=fma_id,p=province",
       "-simplify", "22%", "keep-shapes", "-clean",
       "-dissolve", "p", "+", "name=provs",
       "-o", OUT / "base.json", "target=areas,provs", "format=topojson", q)

    # 2. 2026 fire outlines
    with tempfile.TemporaryDirectory() as td:
        src = json.load(open(A / "forest/fires_2026_simplified.geojson", encoding="utf-8"))
        cls = {"wildfire": "w", "wildfire (unreported in agency lists)": "u", "unclear": "c",
               "likely agricultural or grass burn": "a", "military range": "m", "possible industrial or urban heat": "i"}
        for ft in src["features"]:
            p = ft["properties"]
            ft["properties"] = {"u": p["UID"], "p": p["province"], "d1": p["FIRSTDATE"][:10], "d2": p["LASTDATE"][:10],
                                "ha": round(p["official_scaled_ha"] or 0), "c": cls.get(p["outline_class"], "c")}
        tmp = Path(td) / "fires.geojson"
        tmp.write_text(json.dumps(src))
        ms("-i", tmp, "name=fires", "-proj", "from=wgs84", PROJ, "-simplify", "25%", "keep-shapes", "-clean",
           "-o", OUT / "fires.json", "format=topojson", q)

        # 3. Reburned land in the 2026 footprint (classes 1 to 3 only)
        ms("-i", A / "forest/reburn_2026.geojson", "name=reburn", "-proj", PROJ,
           "-filter", "cls > 0", "-filter-fields", "cls", "-simplify", "14%", "-filter-slivers", "min-area=1km2", "-clean",
           "-o", OUT / "reburn.json", "format=topojson", q)

        # 4. Federal boreal caribou ranges
        car = json.load(open(A / "wildlife/caribou_ranges_2026.geojson", encoding="utf-8"))
        for ft in car["features"]:
            p = ft["properties"]
            ft["properties"] = {"n": p["herd_range"], "p": p["province"], "s": round(p["fire_share_1987_2026_pct"], 1),
                                "s25": round(p["fire_share_1987_2025_pct"], 1), "b26": round(p["share_burned_2026_pct"], 2)}
        tmp = Path(td) / "caribou.geojson"
        tmp.write_text(json.dumps(car))
        ms("-i", tmp, "name=caribou", "-proj", "from=wgs84", PROJ, "-simplify", "15%", "keep-shapes", "-clean",
           "-o", OUT / "caribou.json", "format=topojson", q)

        # 5. BC community (drinking-water) watersheds more than 10% burned 2023 to 2026
        burned = {r["CW_CODE"]: r for r in rows(A / "threads/t6_bc_community_watersheds_burned.csv")}
        ws = json.load(open(A / "threads/raw/bc_water/WLS_COMMUNITY_WS_PUB_SVW.geojson", encoding="utf-8"))
        keep = []
        for ft in ws["features"]:
            p = ft["properties"]
            b = burned.get(p["CW_CODE"])
            if b and float(b["share_2023_2026"]) > 0.10:
                sysname = b["WATER_SYSTEM_NAME"] if b["WATER_SYSTEM_NAME"] not in ("NA", "") else (b["ORGANIZATION"] or "").strip()
                ft["properties"] = {"n": p["CW_NAME"], "w": sysname, "s": round(min(float(b["share_2023_2026"]), 1) * 100, 1)}
                keep.append(ft)
        ws["features"] = keep
        tmp = Path(td) / "ws.geojson"
        tmp.write_text(json.dumps(ws))
        ms("-i", tmp, "name=watersheds", "-proj", "from=EPSG:3005", PROJ, "-simplify", "30%", "keep-shapes", "-clean",
           "-o", OUT / "watersheds.json", "format=topojson", q)
        print("watersheds kept:", len(keep))

    # 6. Area attributes (one record per area)
    T = rows(A / "forest/fma_2026_table.csv")
    H = {r["fma_id"]: r for r in rows(A / "forest/fma_forest_share_by_year_1972_2025.csv")}
    U = {r["fma_id"]: r for r in rows(a.src / "site-build/fma_union_2023_2026.csv")}
    years = list(range(1972, 2026))
    areas = {}
    for r in T:
        i = r["fma_id"]
        hist = [f(H[i][str(y)]) for y in years] if i in H else [None] * len(years)
        hist.append(f(r["forest_share_burned_2026"]))
        u = U[i]
        areas[i] = {
            "n": r["area_name"], "p": r["province"], "lvl": r["area_level"],
            "fha": round(f(r["forest_ha"]) or 0),
            # share of forest burned per year 1972 to 2026, percent, mapped basis
            "h": [None if v is None else sig(v * 100, 3) for v in hist],
            "avg": sig((f(r["avg_share_1991_2020"]) or 0) * 100, 3),
            "s26sc": sig((f(r["forest_share_2026_scaled_sensitivity"]) or 0) * 100, 3),
            "rec26": r["record_2026"] == "True", "rec26sc": r["record_2026_if_scaled"] == "True",
            "ha26": round(f(r["official_scaled_ha_2026"])) if f(r["official_scaled_ha_2026"]) is not None else None,
            "ha26m": round(f(r["mapped_ha"]) or 0),
            "haM": {str(y): round(f(u[f"land_mapped_ha_{y}"]) or 0) for y in (2023, 2024, 2025)},
            "u4": sig((f(u["forest_share_union_2023_2026"]) or 0) * 100, 3),
            "u4ha": round(f(u["land_union_ha_2023_2026"]) or 0),
        }
    (OUT / "areas.json").write_text(json.dumps({"years_from": 1972, "areas": areas}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for p in sorted(OUT.glob("*.json")):
        print(f"{p.name:16s} {p.stat().st_size:>9,} bytes")


if __name__ == "__main__":
    main()
