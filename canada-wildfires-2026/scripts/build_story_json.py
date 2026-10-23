"""Build data/story.json: every number the page shows, in one file.

Claims (C1 to C40) come from story/verified_numbers.json when it exists, otherwise from the
draft values below (same keys, so the page reads either). Chart series are read from the
analysis CSVs. Re-run after any change to refresh the whole site's numbers in one step:

    python scripts/build_story_json.py --src /path/to/wildfire

where --src is the folder holding analysis/ and story/.
"""
import argparse
import os
import copy
import csv
import datetime as dt
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = Path(os.environ.get("WILDFIRE_SRC", "../wildfire"))

# Draft values from story/claims_draft.md, written with the same keys as verified_numbers.json.
DRAFT = {
    "C1": {"share_pct": {"2023": 2.61, "2025": 1.39, "2026": 1.04, "2024": 0.93, "1989": 0.81}},
    "C2": {"union_pct": 5.95, "sum_pct": 5.97, "forest_union_mha": 20.78, "one_in": 17},
    "C3": {"max_prior_window_pct": 2.06, "window": "1979-1982"},
    "C4": {"distinct_land_scaled_mha": 35.79, "official_sum_mha": 35.91, "germany_ratio": 1.0},
    "C5": {"official_2026_mha": 4.50, "rank": 8, "of_years": 37},
    "C6": {"warming_c": 1.15, "lo": 0.80, "hi": 1.49},
    "C7": {"stations": 236, "positive_theil_sen": 236},
    "C8": {"pct_per_degree": 44, "lo": 30, "hi": 62},
    "C9": {"ratio": 1.53, "lo": 1.37, "hi": 1.76, "share_attributable": 0.347},
    "C10": {"pct_of_normal": 84.0, "rank": 1, "of_windows": 74},
    "C11": {"trend_pct_per_decade_1950_2026": 0.04},
    "C12": {"d1_max_pct": {"2023": 53.7, "2024": 53.8, "2025": 72.2, "2026": 55.8}, "mean_2003_2022": 14.4, "max_2003_2022": 32.7},
    "C13": {"lightning_2026_nfd": 2960, "lightning_mean_1991_2020": 3245, "human_2026": 2190, "human_rank": "lowest of 37"},
    "C14": {"fire_share_pct": 54.7, "area_share_pct": 95.0},
    "C15": {"ratio_after": 16.3, "actual_pct": 5.85, "predicted_pct": 0.36, "beyond_calibration": 5.2},
    "C16": {"date": "2026-07-16", "popw_pm25": 67.0, "previous_high": 52.5, "previous_date": "2023-06-25"},
    "C17": {"ontario_people_gt100": 11700000},
    "C18": {"2026": {"aqbat": 98, "chen": 253}, "2023": {"aqbat": 379, "chen": 988}},
    "C19": {"direct_deaths": {"2023": 1, "2024": 2, "2025": 2, "2026": 6}},
    "C20": {"pooled_ratio_lo": 50, "pooled_ratio_hi": 200},
    "C21": {"on_reserve_pct": 3.3, "off_reserve_pct": 0.11, "ratio": 31},
    "C22": {"communities": 7, "names": ["Chemawawin Cree Nation", "Kanaka Bar", "Lake St. Martin"]},
    "C23": {"flagged": {"2023": 844, "2024": 417, "2025": 405, "2026": 517}, "total": 2183, "precision": 0.836, "recall": 0.832,
            "coverage": {"2023": "4 events", "2024": "Jasper in-sample", "2025": "2 events", "2026": "all outlines"}},
    "C24": {"flagged": 168, "official_approx": 150},
    "C25": {"roads_km": 9503, "rail_km": 686},
    "C26": {"value_cad_m": 922, "events": 7},
    "C27": {"timber_2023_nominal_b": 7.44, "stumpage_collected_2023_b": 1.03, "ratio": 7.2},
    "C28": {"mean_2016_2022_b": 1.05, "mean_2023_2025_b": 2.15, "ratio": 2.04},
    "C29": {"all_components_chen_b": 43.2, "documented_spending_losses_b": 10.35},
    "C30": {"years_of_2024_harvest": 11.2, "merch_volume_mm3": 1336},
    "C31": {"managed_wildfire_2023_mt": 870, "national_total_2023_mt": 686.9, "share_pct": 127},
    "C32": {"share_1990s_pct": 2.3, "share_2023_2026_pct": 7.5, "ha_per_year_1990s": 36282, "ha_per_year_2023_2026": 343906},
    "C33": {"ranges_over_35pct": 14, "of_ranges": 51},
    "C34": {"share_mapped_pct": 12.8, "share_scaled_pct": 11.2, "ratio": 88, "record": True},
    "C35": {"records_scaled": 9, "records_mapped": 12},
    "C36": {"share_mapped_pct": 10.5, "share_scaled_pct": 9.7, "ratio": 110, "record": False},
    "C37": {"peak5_share_pct": 70.5, "window": "2026-06-22 to 2026-07-26"},
    "C38": {"bc_watersheds_over_10pct": 23, "bc_watersheds_total": 466, "nhn_units_over_10pct": 110, "pop_centres": 29, "people": 106904},
    "C39": {"jasper_change_pct": -53.3, "network_change_pct": -2.7},
    "C40": {"extreme_days_2026": 118, "normal_1991_2020": 59.6, "previous_max": 110, "record": True},
}


# Deaths in the fires that are not in the TSB aviation records C19 is built from. Each entry is an official count
# with its source; the build adds it to C19 and recomputes C20 from the result.
WAINWRIGHT_DEATHS = 4  # Canadian Armed Forces members killed in the fire at CFB Wainwright, Alberta, on Oct 17, 2026
WAINWRIGHT_SOURCE = ("Department of National Defence, news release of Oct 18, 2026, 'Four Canadian Armed Forces members "
                     "killed during training in CFB Wainwright': https://www.canada.ca/en/department-national-defence/news/"
                     "2026/10/four-canadian-armed-forces-members-killed-during-training-in-cfb-wainwright.html")


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x, nd=None):
    if x in (None, "", "nan"):
        return None
    v = float(x)
    if math.isnan(v):
        return None
    return round(v, nd) if nd is not None else v


def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            deep_merge(a[k], v)
        else:
            a[k] = v
    return a


def load_claims(src):
    claims = {k: {"status": "draft", **copy.deepcopy(v)} for k, v in DRAFT.items()}
    vf = src / "story" / "verified_numbers.json"
    source = "draft"
    if vf.exists():
        ver = json.load(open(vf, encoding="utf-8"))
        if isinstance(ver, dict) and "claims" in ver:
            ver = ver["claims"]
        if isinstance(ver, list):
            ver = {c["id"]: c for c in ver}
        for cid, vals in ver.items():
            if not isinstance(vals, dict):
                continue
            vals = dict(vals)
            vals.pop("id", None)
            if isinstance(vals.get("values"), dict):
                vals = {**vals.pop("values"), **vals}
            claims.setdefault(cid, {})
            # verified values replace draft values key by key; draft-only keys are dropped when the
            # verifier marks a claim corrected, so stale draft numbers can never show.
            if vals.get("status") == "corrected":
                claims[cid] = {}
            deep_merge(claims[cid], vals)
        source = "verified_numbers.json"
    return claims, source


def series(A, claims, warn):
    S = {}
    # 1. Share of Canada's forest burned, 1972 to 2026 (mapped basis)
    r = rows(A / "forest" / "canada_forest_share_by_year.csv")
    S["forest_share"] = [[int(x[""]), round(float(x["share_forest_burned"]) * 100, 3)] for x in r]
    # 1b. Hectares burned each year, Canada: NBAC 1972 to 2025 plus the 2026 official total
    r = rows(A / "climate-change" / "area_burned_series.csv")
    S["hectares"] = [[int(x["year"]), round(float(x["hectares"]))] for x in r if x["scope"] == "Canada" and int(x["year"]) >= 1972]
    # 2. May to August temperature anomaly vs 1961 to 1990, Canada, 1950 to 2026
    r = rows(A / "climate-change" / "climate_series.csv")
    S["temp_anom"] = [[int(x["year"]), round(float(x["value"]), 2)] for x in r if x["scope"] == "Canada" and x["variable"] == "t_mjja"]
    # 3. Drought: forest-weighted share in moderate drought or worse (CDM D1+) at some point April to September
    r = rows(A / "cause" / "run_national_drivers.csv")
    S["drought"] = [[int(x["year"]), round(float(x["drought_d1_area_max_apr_sep_forest_weighted"]) * 100, 1)]
                    for x in r if x["drought_d1_area_max_apr_sep_forest_weighted"] not in ("", "nan")]
    # 4. Model: forest share burned, actual vs expected (trained 2003 to 2022; 2003 to 2022 leave-one-year-out)
    r = rows(A / "cause" / "run_model_check.csv")
    S["model"] = [[int(x["year"]), round(float(x["actual"]) * 100, 3), round(float(x["predicted"]) * 100, 3)]
                  for x in r if x["model"] == "P_all"]
    # 5. Smoke deaths (modelled, net) by coefficient vs direct deaths
    r = rows(A / "health" / "modelled_acute_deaths_national.csv")
    sm = {}
    for x in r:
        k = "aqbat" if x["coefficient"].startswith("AQBAT") else "chen"
        sm.setdefault(int(x["year"]), {})[k] = round(float(x["net_c"]))
        sm[int(x["year"])]["provinces_not_reported"] = x["provinces_not_reported"]
    dd = claims.get("C19", {}).get("direct_deaths", {})
    S["deaths"] = [[y, sm[y]["aqbat"], sm[y]["chen"], dd.get(str(y)), sm[y]["provinces_not_reported"]] for y in (2023, 2024, 2025, 2026)]
    # C20: smoke deaths for each death in the fires, pooled over 2023 to 2026 from the same series, rounded to 10
    lo_sum, hi_sum = sum(r[1] for r in S["deaths"]), sum(r[2] for r in S["deaths"])
    d_sum = sum(r[3] or 0 for r in S["deaths"])
    claims["C20"] = {
        "status": "derived", "basis": "sum of modelled smoke deaths 2023 to 2026 / sum of direct deaths (C19, including Wainwright)",
        "smoke_lo_sum": lo_sum, "smoke_hi_sum": hi_sum, "direct_sum": d_sum,
        "pooled_ratio_lo_exact": round(lo_sum / d_sum, 1), "pooled_ratio_hi_exact": round(hi_sum / d_sum, 1),
        "pooled_ratio_lo": int(round(lo_sum / d_sum, -1)), "pooled_ratio_hi": int(round(hi_sum / d_sum, -1)),
        "by_year": {str(r[0]): [round(r[1] / r[3]), round(r[2] / r[3])] for r in S["deaths"] if r[3]},
        "verified_before_wainwright": {"pooled_ratio_lo": 114, "pooled_ratio_hi": 297},
    }
    # 6. Roads inside burned area by year (km), 2016 to 2026
    r = rows(A / "property" / "infrastructure_by_year.csv")
    S["roads"] = [[int(x["year"]), round(float(x["roads_all_km"]))] for x in r if x["band"] == "inside" and x["year"].isdigit()]
    # 7. Provincial firefighting (BC, ON, AB, SK), 2025 dollars, billions
    r = rows(A / "economic-value" / "cost_tally_by_year.csv")
    S["firefighting"] = []
    for x in r:
        y = int(x["year"])
        if y > 2025:
            continue  # 2026 has BC only
        missing = [p for p in ("AB", "BC", "ON", "SK") if x[f"A_{p}"] in ("", "nan")]
        S["firefighting"].append([y, round(float(x["A_provincial_firefighting"]) / 1e9, 2), missing])
    # 8. Official managed-forest wildfire emissions vs national total (Mt CO2e)
    r = rows(A / "threads" / "t1_official_inventory_lines.csv")
    S["co2"] = [[int(x["year"]), round(float(x["nir_wildfire_direct_immediate_kt_co2e"]) / 1000), round(float(x["national_total_excl_lulucf_kt"]) / 1000, 1)] for x in r]
    # 9. Short-interval reburn (15 years), black spruce / jack pine forest, by period
    r = rows(A / "threads" / "t2_reburn_by_period.csv")
    S["reburn"] = [[x["period"], round(float(x["reburn_share"]) * 100, 1)] for x in r if x["k"] == "15" and x["basis"] == "SCANFI BS/JP"]
    # 10. Caribou ranges over 35% burned by fire, 1987 to 2026
    r = rows(A / "wildlife" / "caribou_ranges_2026.csv")
    car = sorted(r, key=lambda x: -float(x["fire_share_1987_2026_pct"]))
    S["caribou"] = [[x["herd_range"], x["province"], round(float(x["fire_share_1987_2026_pct"]), 1)] for x in car if float(x["fire_share_1987_2026_pct"]) > 35]
    # 11. Weekly 2026 satellite detections, national and by province
    r = rows(A / "forest" / "weekly_hotspots.csv")
    provs = ["BC", "AB", "SK", "MB", "ON", "QC", "NB", "NS", "PE", "NL", "YT", "NT", "NU"]
    S["hotspots"] = {"weeks": [x["week_start"] for x in r], "CAN": [int(x["CAN"]) for x in r], **{p: [int(x[p]) for x in r] for p in provs}}
    pk = rows(A / "forest" / "hotspot_peak5.csv")
    S["hotspot_peak"] = {x["series"]: {"start": x["peak5_start"], "end": x["peak5_end"], "share": round(float(x["peak5_share"]) * 100, 1),
                                       "total": int(x["total_detections"])} for x in pk if x["series"] in ["CAN"] + provs}

    # C1b: four-year totals in hectares, derived here from the series (no separate verification file entry)
    ha = dict(S["hectares"])
    win = {y: sum(ha[y - k] for k in range(4)) for y in ha if y - 3 in ha}
    prev = max((v, y) for y, v in win.items() if y <= 2022)
    off = {}
    for x in rows(A.parent / "data" / "smoke-cost" / "fire_area_count_by_agency_year.csv"):
        off[int(x["year"])] = off.get(int(x["year"]), 0) + float(x["area_burned_ha"] or 0)
    off[2026] = ha[2026]  # 2026 official total (agencies plus Parks Canada)
    owin = {y: sum(off[y - k] for k in range(4)) for y in off if y - 3 in off}
    oprev = max((v, y) for y, v in owin.items() if y <= 2022)
    claims.setdefault("C1b", {}).update({
        "status": "derived", "basis": "NBAC 1972 to 2025 plus 2026 official; official = NFD 1990 to 2025 plus 2026 official",
        "ha_2023_2026_mha": round(win[2026] / 1e6, 1), "prev_max_mha": round(prev[0] / 1e6, 1), "prev_window": f"{prev[1] - 3}-{prev[1]}",
        "ratio": round(win[2026] / prev[0], 1),
        "official_2023_2026_mha": round(owin[2026] / 1e6, 1), "official_prev_max_mha": round(oprev[0] / 1e6, 1),
        "official_prev_window": f"{oprev[1] - 3}-{oprev[1]}", "official_ratio": round(owin[2026] / oprev[0], 1),
        "rank_by_ha": {str(y): sorted(ha.values(), reverse=True).index(ha[y]) + 1 for y in (2023, 2024, 2025, 2026)}, "of_years": len(ha),
    })

    # X: counts and context figures the page text uses (each read from its source file where one exists)
    T = rows(A / "forest" / "fma_2026_table.csv")
    city = json.load(open(A / "people" / "city_search_table.json", encoding="utf-8"))
    sf = rows(A / "forest" / "scaling_factors_by_province.csv")
    mapped = sum(float(x["m3_mapped_ha"] or 0) for x in sf)
    official = sum(float(x["official_2026_ha"] or 0) for x in sf)
    tr = [float(x["ratio_flagged_to_official"]) for x in rows(A / "property" / "transfer_checks.csv")
          if not x["event"].startswith("jasper") and x.get("ratio_flagged_to_official") not in (None, "", "nan")]
    hum = claims.get("C13", {}).get("human_rank", "lowest of 37")
    claims["X"] = {
        "status": "derived",
        "fma_areas": len(T),
        "places": city["meta"]["n_records"],
        "climate_areas": 164,  # climate-change/results.md, section 4 panel coverage
        "model_areas": 177,    # cause model eligible areas (REBUILD.md, after rebuild)
        "human_rank_years": int("".join(ch for ch in str(hum) if ch.isdigit()) or 37),
        "outline_excess_pct": round((mapped / official - 1) * 100),
        "direct_2025_public_safety": 2,  # Lac du Bonnet, MB, Public Safety Canada Question Period notes
        "transfer_lo": round(min(tr), 2) if tr else 0.31, "transfer_hi": round(max(tr), 2) if tr else 1.51,
        "peak_start": S["hotspot_peak"]["CAN"]["start"], "peak_end": S["hotspot_peak"]["CAN"]["end"],
    }

    # consistency checks between claims and series
    c12 = claims.get("C12", {}).get("d1_max_pct", {})
    dr = dict((y, v) for y, v in S["drought"])
    for y, v in c12.items():
        if abs(dr.get(int(y), -99) - v) > 0.06:
            warn.append(f"C12 {y}: claim {v} vs series {dr.get(int(y))}")
    fs = dict(S["forest_share"])
    for y, v in claims.get("C1", {}).get("share_pct", {}).items():
        if abs(fs[int(y)] - v) > 0.006:
            warn.append(f"C1 {y}: claim {v} vs series {fs[int(y)]}")
    return S


def largest(A, claims, S):
    """L: the largest and closest fires (analysis/largest); W: the CFB Wainwright fire (analysis/wainwright)."""
    F = rows(A / "largest" / "fires_2023_2026.csv")

    def rec(x):
        g = lambda k: x[k] if x[k] not in ("", "nan") else None
        return {"k": x["key"], "y": int(x["year"]), "n": g("agency_name"), "id": g("agency_id"), "p": g("provinces"),
                "ha": round(float(x["ha"])), "c": x["cause"], "s": g("start"), "sb": x["start_basis"],
                "co": x["carryover"] == "True", "b": int(x["bldg_inside_or_100m"]), "bi": int(x["bldg_inside"]),
                "fa": g("fire_area"), "pc": g("nearest_pc"), "km": None if g("nearest_pc_km") is None else round(float(x["nearest_pc_km"])),
                "a1k": int(x["agency_points_1000ha"]), "ra": int(x["rank_area"]), "ry": int(x["rank_area_in_year"]),
                "src": x["source"]}
    S["largest"] = [rec(x) for x in sorted(F, key=lambda x: int(x["rank_area"]))[:10]]
    S["closest"] = [rec(x) for x in sorted((x for x in F if 1 <= int(x["rank_buildings"]) <= 10), key=lambda x: int(x["rank_buildings"]))]
    big26 = min((x for x in F if x["year"] == "2026"), key=lambda x: int(x["rank_area"]))
    co = {int(x["year"]): x for x in rows(A / "largest" / "carryover_by_year.csv")}
    ca = {int(x["year"]): x for x in rows(A / "largest" / "cause_area_by_year.csv")}
    tot = sum(float(co[y]["total_ha"]) for y in co)
    hum = {y: float(ca[y].get("human", 0) or 0) for y in ca}
    top_co = max((x for x in F if x["carryover"] == "True"), key=lambda x: float(x["ha"]))
    top_h = {y: max((x for x in F if x["year"] == str(y) and x["cause"] == "human"), key=lambda x: float(x["ha"]), default=None) for y in co}
    claims["L"] = {
        "status": "derived", "basis": "mapped hectares: NBAC 2023 to 2025, CWFIS M3 outlines 2026 (wildfire classes)",
        "fires": len(F), "total_mha": round(tot / 1e6, 2),
        "top_ha": S["largest"][0]["ha"], "top_bldg": S["closest"][0]["b"],
        "largest_2026": rec(big26),
        "carryover_fires": sum(int(float(co[y]["carryover_fires"])) for y in co),
        "carryover_ha": round(sum(float(co[y]["carryover_ha"]) for y in co)),
        "carryover_share_pct": round(sum(float(co[y]["carryover_ha"]) for y in co) / tot * 100, 1),
        "carryover_by_year": {str(y): {"fires": int(float(co[y]["carryover_fires"])), "ha": round(float(co[y]["carryover_ha"]))} for y in sorted(co)},
        "carryover_largest": rec(top_co),
        "human_share_pct": {str(y): round(hum[y] / float(ca[y]["total_ha"]) * 100, 1) for y in sorted(ca)},
        "human_share_2023_2026_pct": round(sum(hum.values()) / tot * 100, 1),
        "human_largest": {str(y): rec(top_h[y]) for y in sorted(top_h) if top_h[y]},
        "no_agency_2026_ha": round(float(ca[2026].get("no agency record", 0) or 0)),
        "buildings_years": "2023 to 2026",
    }
    # W: CFB Wainwright, Oct 17, 2026
    Wd = A / "wainwright"
    be = {x["threshold"]: x for x in rows(Wd / "burn_estimate.csv")}
    off = rows(A / "largest" / "wainwright_official.csv")[0]
    hr = {x["local_standard_time"][11:16]: x for x in rows(Wd / "weather_oct17_hourly.csv") if x["climate_id"] == "301S001"}
    rk = next(x for x in rows(Wd / "weather_oct17_ranks.csv") if x["station"].startswith("WAINWRIGHT") and x["metric"] == "daily max wind gust"
              and x["comparison"].startswith("mid-October"))
    by = [x for x in rows(Wd / "base_burns_by_year.csv") if x["base"] == "Wainwright" and x["source"] == "NBAC"]
    yrs = {int(x["year"]) for x in by if 1991 <= int(x["year"]) <= 2025 and float(x["ha_inside_base"]) > 0}
    geo = rows(Wd / "burn_geometry.csv")[0]
    pre, post = hr["14:00"], hr["15:00"]  # local standard time = MDT minus 1 hour: 3 p.m. and 4 p.m. MDT
    claims["W"] = {
        "status": "derived", "note": "area estimated from Sentinel-2 images (no official perimeter); deaths from DND",
        "est_ha": round(float(be["0.27"]["area_ha"]), -1), "est_lo_ha": round(float(be["0.44"]["area_ha"]), -1),
        "est_hi_ha": round(float(be["0.2"]["area_ha"]), -1), "est_ha_exact": float(be["0.27"]["area_ha"]),
        "outside_base_ha": round(float(be["0.27"]["outside_base_ha"])), "length_km": float(geo["length_km"]),
        "official_ha": float(off["AREA_ESTIMATE"]), "official_id": off["LABEL"],
        "deaths": WAINWRIGHT_DEATHS,
        "wind_3pm_kmh": float(pre["wind_kmh"]), "wind_4pm_kmh": float(post["wind_kmh"]),
        "dir_3pm_deg": float(pre["wind_dir_10deg"]) * 10, "dir_4pm_deg": float(post["wind_dir_10deg"]) * 10,
        "temp_drop_c": round(float(pre["temp_c"]) - float(post["temp_c"]), 1), "rh_3pm": float(pre["rh_pct"]), "rh_4pm": float(post["rh_pct"]),
        "gust_kmh": float(rk["oct17_value"]), "gust_rank": int(rk["rank_of_oct17"]), "gust_days": int(rk["n_days"]),
        "gust_prev_max": float(rk["max_in_set"]), "gust_years": rk["years"],
        "base_years_burned": len(yrs), "base_years_of": 35,
        "ratio_to_largest": round(float(S["largest"][0]["ha"]) / float(be["0.27"]["area_ha"])),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    a = ap.parse_args()
    A = a.src / "analysis"
    claims, source = load_claims(a.src)
    # C19 counts TSB aviation deaths (and 2025's two Public Safety deaths); add the Wainwright deaths to 2026
    c19 = claims.setdefault("C19", {})
    dd = c19.setdefault("direct_deaths", {})
    c19["tsb_2026"] = dd.get("2026", 0)
    c19["wainwright_2026"] = WAINWRIGHT_DEATHS
    c19["wainwright_source"] = WAINWRIGHT_SOURCE
    dd["2026"] = c19["tsb_2026"] + WAINWRIGHT_DEATHS
    warn = []
    S = series(A, claims, warn)
    largest(A, claims, S)
    # The page shows no modelled smoke deaths (deaths are counted by coroners, and no study reports wildfire
    # smoke deaths for 2023 to 2026). The modelled series stays in analysis/health/ for the record only.
    for k in ("C18", "C20"):
        claims.pop(k, None)
    for k in [k for k in claims.get("C29", {}) if k.startswith("all_components") or k == "basis"]:
        claims["C29"].pop(k, None)
    S.pop("deaths", None)
    out = {
        "meta": {"built": dt.date.today().isoformat(), "claims_source": source,
                 "note": "Every number on the page comes from this file. Claims are keyed C1 to C40."},
        "claims": claims,
        "series": S,
    }
    p = ROOT / "data" / "story.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {p} ({p.stat().st_size:,} bytes) from {source}")
    for w in warn:
        print("WARNING", w)


if __name__ == "__main__":
    main()
