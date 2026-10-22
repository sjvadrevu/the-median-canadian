"""Build data/cities.json (find-your-city search) and data/smoke2026.json (daily 2026 smoke calendar)
from analysis/people/city_search_table.json and city_smoke_daily_2026.csv.

    python scripts/build_cities.py --src /path/to/wildfire

Places without their own air monitor point to the nearest monitored place within 40 km, labelled as such.
"""
import argparse
import os
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = Path(os.environ.get("WILDFIRE_SRC", "../wildfire"))
NEAR_KM = 40


def hav(a, b, c, d):
    r = math.radians
    x = math.sin(r(c - a) / 2) ** 2 + math.cos(r(a)) * math.cos(r(c)) * math.sin(r(d - b) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))


def clean(o):
    """Replace NaN with None so the output is valid JSON."""
    if isinstance(o, float) and math.isnan(o):
        return None
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    a = ap.parse_args()
    P = a.src / "analysis" / "people"
    T = json.load(open(P / "city_search_table.json", encoding="utf-8"))
    recs = T["records"]

    # daily 2026 series
    daily = {}
    with open(P / "city_smoke_daily_2026.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            daily.setdefault(r["city"], []).append(r)
    start = "2026-01-01"
    import datetime as dt
    d0 = dt.date.fromisoformat(start)
    last = max(dt.date.fromisoformat(r["date"]) for v in daily.values() for r in v)
    n = (last - d0).days + 1
    cal = {}
    for c, rs in daily.items():
        v = [None] * n
        st = [0] * n  # 1 = real-time, 2 = validated
        for r in rs:
            i = (dt.date.fromisoformat(r["date"]) - d0).days
            if r["pm25_city_mean"] not in ("", "nan"):
                v[i] = round(float(r["pm25_city_mean"]), 1)
                st[i] = 2 if r["data_status"].startswith("valid") else 1
        cal[c] = {"v": v, "rt": int(all(s != 2 for s in st))}

    # smoke series, stored once per monitor series
    smoke = {}
    for r in recs:
        s = r.get("smoke")
        if not s or s.get("proxy"):
            continue
        key = s["monitor_series"]
        if key in smoke:
            continue
        by = {}
        for y, d in s["by_year"].items():
            by[y] = [d["days_gt27"], d["days_gt60"], d["days_gt100"], d["worst_day"], d["worst_day_pm25"],
                     {"validated": "v", "real-time": "r", "mixed": "m"}.get(d["data_basis"], "m"), int(bool(d["adequate_coverage"]))]
        smoke[key] = {"lat": r["lat"], "lon": r["lon"], "y": by, "cal": key in cal}

    out = []
    for r in recs:
        nf = r.get("nearest_fire_2026") or {}
        s = r.get("smoke")
        sm = None
        if s and not s.get("proxy"):
            sm = [s["monitor_series"], 0]
        else:
            best = None
            for k, v in smoke.items():
                d = hav(r["lat"], r["lon"], v["lat"], v["lon"])
                if best is None or d < best[1]:
                    best = (k, d)
            if best and best[1] <= NEAR_KM:
                sm = [best[0], round(best[1])]
        pc = r.get("province_cost")
        cost = None
        if pc:
            cost = {"p": pc["province"], "def": pc["definition"], "yr": pc["latest_season"], "pr": pc["latest_cost_per_resident_cad"],
                    "st": pc["latest_status"], "ser": pc.get("series")}
        out.append({
            "n": r["name"], "p": r["prov"], "pop": r["pop2021"], "lat": r["lat"], "lon": r["lon"],
            "f": {"km": nf.get("edge_km"), "dir": nf.get("direction_from_centre"), "d1": nf.get("first_detected"),
                  "d2": nf.get("last_detected"), "ha": nf.get("outline_ha"), "cls": nf.get("outline_class"),
                  "ag": nf.get("agency_reported_fire_within_5km"), "agkm": nf.get("nearest_agency_matched_edge_km"),
                  "fp": nf.get("fire_prov")} if nf else None,
            "sm": sm, "cost": cost,
        })
    out.sort(key=lambda x: -(x["pop"] or 0))
    for k in smoke:
        smoke[k].pop("lat"); smoke[k].pop("lon")
    meta = {"fire_source": T["meta"]["fire_source"], "smoke_source": T["meta"]["smoke_source"], "cost_note": T["meta"]["cost_note"],
            "near_km": NEAR_KM}
    (ROOT / "data" / "cities.json").write_text(json.dumps(clean({"meta": meta, "smoke": smoke, "places": out}), ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    (ROOT / "data" / "smoke2026.json").write_text(json.dumps(clean({"start": start, "days": n, "cities": cal}), separators=(",", ":"), allow_nan=False), encoding="utf-8")
    for p in ("cities.json", "smoke2026.json"):
        q = ROOT / "data" / p
        print(f"{p:16s} {q.stat().st_size:>9,} bytes")
    print("places", len(out), "with smoke", sum(1 for o in out if o["sm"]), "calendar cities", len(cal))


if __name__ == "__main__":
    main()
