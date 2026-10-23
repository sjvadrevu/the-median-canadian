#!/usr/bin/env python3
"""Week 2 carousel: Canada's wildfires, 2023 to 2026 (The Median Canadian).

One command rebuilds everything:
    python3 make_slides.py

Steps: load numbers (verified_numbers.json if present, else the draft readings
below), read chart series from the analysis CSVs, write slides.html, render
each slide with Playwright Chromium (/opt/pw-browsers) to
the-median-canadian-wildfires-n-of-9.png, and print a fit report
(content bottom vs wordmark top, overflow, one-line source line, banned words).
"""
import html
import json
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))
AN = os.path.join(BASE, "analysis")
VERIFIED = os.path.join(BASE, "story", "verified_numbers.json")
N_SLIDES = 9
PHOTO_DIR = "photos_v2"  # watermarked previews for review; swap for licensed files before posting
# slide: (file, background-position, background-size)
PHOTOS = {
    1: ("s1_6188-64594005.jpg", "50% 40%", "cover"),
    2: ("s2_6019-60231329.jpg", "50% 30%", "cover"),
    3: ("s3_1848-53916235.jpg", "62% 50%", "cover"),
    4: ("s4_1848-49409649.jpg", "50% 20%", "cover"),
    5: ("s5_6019-67126902.jpg", "50% 20%", "cover"),
    6: ("s6_4197-65297456.jpg", "50% 15%", "cover"),
    7: ("s7_1525-22526195.jpg", "50% 0%", "cover"),
    8: ("s8_1848-64409449.jpg", "50% 30%", "cover"),
    9: ("s9_6188-67448389.jpg", "50% 60%", "cover"),
}
# photographer or supplier as listed by All Canada Photos; check against the licence before posting
CREDITS = {
    1: "IMAGO / had fotos", 2: "Josephine Skinner / Cavan Images", 3: "Horst Mahr / imageBROKER",
    4: "Mats Silvan / imageBROKER", 5: "Cavan Images", 6: "PeopleImages", 7: "Hrolens / Ingram Publishing",
    8: "imagoDens / imageBROKER", 9: "Mikel Bilbao / IMAGO / Zoonar",
}
WAINWRIGHT_DEATHS = 4  # CAF members, CFB Wainwright fire, Oct 17, 2026 (DND release, Oct 18, 2026)

# ---------------------------------------------------------------- numbers
# Keys are dotted paths into verified_numbers.json (claim id, then field).
# Values here are the fallback readings of the draft and analysis files.
DEFAULTS = {
    "C1.share_pct.2023": 2.61, "C1.share_pct.2024": 0.93,
    "C1.share_pct.2025": 1.39, "C1.share_pct.2026": 1.04,
    "C1.share_pct.1989": 0.81, "S1.official_2026_ha": 4500984.5,
    "C2.union_pct": 5.95, "C2.one_in": 17,
    "C4.distinct_land_scaled_mha": 35.79,
    "C6.warming_c": 1.15, "C6.lo": 0.80, "C6.hi": 1.49,
    "C7.stations": 236,
    "C8.pct_per_degree": 43.6,
    "C9.ratio": 1.53, "C9.lo": 1.37, "C9.hi": 1.76, "C9.share_attributable": 0.347,
    "C10.pct_of_normal": 84.0,
    "C12.d1_max_pct.2023": 55.4, "C12.d1_max_pct.2024": 54.6,
    "C12.d1_max_pct.2025": 75.1, "C12.d1_max_pct.2026": 56.7,
    "C12.mean_2003_2022": 14.8, "C12.max_2003_2022": 34.9,
    "C13.lightning_2026_nfd": 2960, "C13.lightning_mean_1991_2020": 3245,
    "C13.human_2026": 2190,
    "C15.ratio_after": 16.3, "C14.area_share_pct": 95.0, "C15.beyond_calibration": 5.2,
    "C16.popw_pm25": 67.0, "C16.previous_high": 52.5,
    "C18.2023.aqbat": 379, "C18.2023.chen": 988,
    "C18.2026.aqbat": 98, "C18.2026.chen": 253,
    "C19.direct_deaths.2023": 1, "C19.direct_deaths.2024": 1,
    "C19.direct_deaths.2025": 2, "C19.direct_deaths.2026": 3,
    "C20.pooled_ratio_lo": 114, "C20.pooled_ratio_hi": 297,
    "C21.ratio": 30.6, "C21.on_reserve_pct": 3.3, "C21.off_reserve_pct": 0.11,
    "C23.flagged.2023": 844, "C23.flagged.2024": 417,
    "C23.flagged.2025": 405, "C23.flagged.2026": 517,
    "C23.total": 2183, "C23.precision": 0.836, "C23.recall": 0.832,
    "C25.roads_km": 9503, "C25.rail_km": 686,
    "C27.timber_2023_nominal_b": 7.44, "C27.stumpage_collected_2023_b": 1.03,
    "C27.ratio": 7.2,
    "C28.mean_2016_2022_b": 1.05, "C28.mean_2023_2025_b": 2.15, "C28.ratio": 2.04,
    "C31.managed_wildfire_2023_mt": 870, "C31.national_total_2023_mt": 686.9,
    "C32.share_1990s_pct": 2.3, "C32.share_2023_2026_pct": 7.5,
}


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


NUM = dict(DEFAULTS)
NUM_SOURCE = {k: "draft" for k in DEFAULTS}
if os.path.exists(VERIFIED):
    ver = flatten(json.load(open(VERIFIED)))
    for k in DEFAULTS:
        if k in ver and isinstance(ver[k], (int, float)):
            NUM[k] = ver[k]
            NUM_SOURCE[k] = "verified"


def V(key):
    return NUM[key]


# ---------------------------------------------------------------- formatting
def f1(x):
    return f"{x:.1f}"


def fint(x):
    return f"{int(round(x)):,}"


def ratio_words(x):
    words = {2: "twice", 3: "three times", 4: "four times", 5: "five times",
             6: "six times", 7: "seven times", 8: "eight times", 9: "nine times",
             10: "ten times"}
    return words.get(int(round(x)), f"{int(round(x))} times")


def esc(s):
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- series
def series():
    s = {}
    fs = pd.read_csv(os.path.join(AN, "forest/canada_forest_share_by_year.csv"), index_col=0)
    s["forest"] = (fs["share_forest_burned"] * 100).to_dict()
    nb = pd.read_csv(os.path.join(AN, "forest/nbac_totals_by_year_admin.csv")).set_index("YEAR").CANADA
    area = {int(y): v / 1e6 for y, v in nb.items() if y <= 2025}
    area[2026] = V("S1.official_2026_ha") / 1e6
    s["area"] = area
    ser = pd.Series(area).sort_index()
    r4 = ser.rolling(4).sum()
    s["area_run"] = float(r4.loc[2026])
    s["area_prior_max"] = float(r4.loc[:2022].max())
    s["area_prior_end"] = int(r4.loc[:2022].idxmax())
    ag = pd.read_csv(os.path.join(BASE, "data/smoke-cost/fire_area_count_by_agency_year.csv"))
    ag4 = ag.groupby("year").area_burned_ha.sum().rolling(4).sum() / 1e6
    s["agency_run"], s["agency_prior_max"] = float(ag4.loc[2026]), float(ag4.loc[:2022].max())
    s["agency_prior_end"] = int(ag4.loc[:2022].idxmax())
    s["agency_year"] = (ag.groupby("year").area_burned_ha.sum() / 1e6).to_dict()
    ed = pd.read_csv(os.path.join(AN, "health/ed_extra_visits_by_year.csv")).set_index("year")
    s["ed"] = ed
    pv = pd.read_csv(os.path.join(AN, "property/destroyed_value_estimates.csv"))
    ev = {2023: ["tantallon2023", "barrington2023", "mcdougall2023", "bushcreek2023"], 2024: ["jasper2024"],
          2025: ["denare2025", "lacdubonnet2025"], 2026: ["2026 all outlines"]}
    s["value"] = {y: pv[pv.event.isin(e)].proxy_value_avg_cad.sum() / 1e6 for y, e in ev.items()}
    s["value_bldg"] = {y: int(pv[pv.event.isin(e)].flagged_500m.sum()) for y, e in ev.items()}
    cs = pd.read_csv(os.path.join(AN, "climate-change/climate_series.csv"))
    t = cs[(cs.scope == "Canada") & (cs.variable == "t_mjja")]
    s["temp"] = dict(zip(t.year.astype(int), t.value))
    rd = pd.read_csv(os.path.join(AN, "cause/run_national_drivers.csv"))
    d = rd[rd.year >= 2003]
    s["drought"] = dict(zip(d.year.astype(int), d.drought_d1_area_max_apr_sep_forest_weighted * 100))
    base = rd[(rd.year >= 1991) & (rd.year <= 2020)]
    s["fires_avg"] = float((base.n_lightning_fires + base.n_human_fires).mean())
    r = rd[rd.year >= 2023]
    s["fires"] = dict(zip(r.year.astype(int), r.n_lightning_fires + r.n_human_fires))
    mc = pd.read_csv(os.path.join(AN, "cause/run_model_check.csv"))
    mc = mc[(mc.model == "P_all") & mc.scheme.str.startswith("train")]
    s["model"] = {int(y): (a * 100, p * 100) for y, a, p in zip(mc.year, mc.actual, mc.predicted)}
    hd = pd.read_csv(os.path.join(AN, "health/modelled_acute_deaths_national.csv"))
    lo = hd[hd.coefficient.str.startswith("AQBAT")].set_index("year").net_c
    hi = hd[hd.coefficient.str.startswith("Chen")].set_index("year").net_c
    s["smoke"] = {y: (lo[y], hi[y]) for y in range(2023, 2027)}
    ct = pd.read_csv(os.path.join(AN, "economic-value/cost_tally_by_year.csv"))
    ct = ct[(ct.year >= 2016) & (ct.year <= 2025)]
    s["firefight"] = dict(zip(ct.year.astype(int), ct.A_provincial_firefighting / 1e9))
    inv = pd.read_csv(os.path.join(AN, "threads/t1_official_inventory_lines.csv"))
    s["co2"] = {int(y): (n / 1000, w / 1000) for y, n, w in zip(
        inv.year, inv.national_total_excl_lulucf_kt, inv.nir_wildfire_direct_immediate_kt_co2e)}
    rb = pd.read_csv(os.path.join(AN, "threads/t2_reburn_by_period.csv"))
    rb = rb[(rb.k == 15) & (rb.basis == "SCANFI BS/JP")]
    s["reburn"] = dict(zip(rb.period, rb.reburn_share * 100))
    rs = os.path.join(AN, "response")
    es = pd.read_csv(os.path.join(rs, "escape_speed_2026_summary.csv")).set_index("prov").loc["Canada"]
    s["escape72"] = (es.share_area_fires_1000ha_within_72h * 100, es.main_run_share_area_fires_1000ha_within_72h * 100)
    zs = pd.read_csv(os.path.join(rs, "zone_share_national.csv")).set_index("year").loc["2023-2026"]
    s["monitored"] = (zs.iloc[list(zs.index).index("not_suppression_share_low")] * 100,
                      zs.iloc[len(zs) - 1] * 100)
    return s


def consistency(s):
    """Warn when chart series disagree with the numbers dict."""
    warn = []
    for y in (2023, 2024, 2025, 2026):
        if abs(s["forest"][y] - V(f"C1.share_pct.{y}")) > 0.006:
            warn.append(f"forest {y}: chart {s['forest'][y]:.3f} vs {V(f'C1.share_pct.{y}')}")
        if abs(s["drought"][y] - V(f"C12.d1_max_pct.{y}")) > 0.06:
            warn.append(f"drought {y}: chart {s['drought'][y]:.2f} vs {V(f'C12.d1_max_pct.{y}')}")
    for y in (2023, 2026):
        lo, hi = s["smoke"][y]
        if round(lo) != V(f"C18.{y}.aqbat") or round(hi) != V(f"C18.{y}.chen"):
            warn.append(f"smoke {y}: chart {lo:.0f}-{hi:.0f}")
    return warn


# ---------------------------------------------------------------- SVG charts
TEXT, MUTED, GRID, FIRE, FOREST, NEUTRAL = "#f4f6f9", "#c3cad4", "rgba(255,255,255,0.22)", "#ff6b4f", "#6fd39a", "#8e98a8"
HALO = "#10151c"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, 'Helvetica Neue', Arial, sans-serif"


def tw(text, size, bold=True):
    return len(text) * size * (0.58 if bold else 0.53)


def label_el(x, y, text, size=24, color=TEXT, anchor="middle", weight=700):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}" stroke="{HALO}" stroke-width="7" stroke-linejoin="round" '
            f'paint-order="stroke">{esc(text)}</text>')


def place_labels(items, size, W=928):
    """items: (x, y_bottom, text, color). Push labels up until no overlap."""
    placed, out = [], []
    for x, yb, text, color in sorted(items, key=lambda i: i[1], reverse=True):
        w, h = tw(text, size), size * 1.05
        x = min(x, W - 10 - w / 2)
        y = yb
        while any(abs(x - px) < (w + pw) / 2 + 4 and abs(y - py) < (h + ph) / 2 + 2 for px, py, pw, ph in placed):
            y -= 2
        placed.append((x, y, w, h))
        out.append(label_el(x, y, text, size, color))
    return out


def bars(cats, values, *, W=928, H=360, ymin=0.0, ymax=None, colors=None, labels=None,
         ticks=None, grid=None, gridfmt=str, refs=(), group=None, lsize=24, ranges=None,
         bar_frac=0.72, tick_size=21, fan=None):
    """Vertical bar chart. values: list per category (or list of lists for groups)."""
    left, right, top, bottom = 76, 8, 44, 36
    pw, ph = W - left - right, H - top - bottom
    n = len(cats)
    ymax = ymax or max(max(v) if isinstance(v, (list, tuple)) else v for v in values) * 1.12
    sy = lambda v: top + ph * (ymax - v) / (ymax - ymin)
    slot = pw / n
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
          f'font-family="{FONT}">']
    for g in grid or []:
        el.append(f'<line x1="{left}" x2="{W - right}" y1="{sy(g):.1f}" y2="{sy(g):.1f}" stroke="{GRID}" stroke-width="2"/>')
        el.append(f'<text x="{left - 10}" y="{sy(g) + 7:.1f}" font-size="20" fill="{MUTED}" text-anchor="end">{esc(gridfmt(g))}</text>')
    labs = []
    for i, c in enumerate(cats):
        x0 = left + i * slot
        vals = values[i] if group else [values[i]]
        k = len(vals)
        bw = slot * bar_frac / k
        start = x0 + (slot - bw * k) / 2
        for j, v in enumerate(vals):
            col = (group[j] if group else (colors[i] if colors else NEUTRAL))
            bx = start + j * bw
            y1, y0 = sy(max(v, 0)), sy(min(v, 0))
            if ranges and ranges[i][j] is not None:  # light extension to high value
                hy = sy(ranges[i][j])
                el.append(f'<rect x="{bx:.1f}" y="{hy:.1f}" width="{bw:.1f}" height="{y1 - hy:.1f}" fill="{NEUTRAL}"/>')
            el.append(f'<rect x="{bx:.1f}" y="{y1:.1f}" width="{bw:.1f}" height="{max(y0 - y1, 1.5):.1f}" fill="{col}"/>')
            lab = labels[i][j] if group and labels else (labels[i] if labels else None)
            if lab:
                ytop = sy(ranges[i][j]) if ranges and ranges[i][j] is not None else y1
                lc = TEXT if not group else (group[j] if group[j] != NEUTRAL else MUTED)
                labs.append((bx + bw / 2, ytop - 9, lab, lc))
        if ticks is None or c in ticks:
            cx = x0 + slot / 2
            anc = "end" if cx + tw(c, tick_size, False) / 2 > W else "middle"
            tx = W - 2 if anc == "end" else cx
            el.append(f'<text x="{tx:.1f}" y="{H - 8}" font-size="{tick_size}" fill="{MUTED}" text-anchor="{anc}">{esc(c)}</text>')
    # zero line
    el.append(f'<line x1="{left}" x2="{W - right}" y1="{sy(0):.1f}" y2="{sy(0):.1f}" stroke="{TEXT}" stroke-width="2"/>')
    for r in refs:
        i0, i1 = r.get("span", (0, n - 1))
        xa, xb = left + i0 * slot, left + (i1 + 1) * slot
        y = sy(r["value"])
        el.append(f'<line x1="{xa:.1f}" x2="{xb:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{r.get("color", FOREST)}" '
                  f'stroke-width="3" stroke-dasharray="9 7"/>')
        if r.get("label"):
            anchor = r.get("anchor", "start")
            lx = xa + 6 if anchor == "start" else xb - 6
            el.append(label_el(lx, y - 10 + r.get("dy", 0), r["label"], 21, r.get("color", FOREST), anchor, 600))
    for idx, txt, col in fan or []:  # bracket over a run of bars with one label above it
        x0b = left + idx[0] * slot + slot * (1 - bar_frac) / 2
        x1b = left + idx[-1] * slot + slot * (1 + bar_frac) / 2
        yb = sy(max(values[i] for i in idx)) - 12
        el.append(f'<path d="M{x0b:.1f},{yb + 8:.1f} V{yb:.1f} H{x1b:.1f} V{yb + 8:.1f}" fill="none" stroke="{col}" stroke-width="2"/>')
        w = tw(txt, lsize)
        cx = min(max((x0b + x1b) / 2, left + w / 2), W - 10 - w / 2)
        el.append(label_el(cx, yb - 12, txt, lsize, col))
    el.extend(place_labels(labs, lsize, W))
    el.append("</svg>")
    return "".join(el)


def hbars(rows, W=928, row_h=58, vmax=None, fmt=str):
    """Horizontal bars: rows of (label, value, color)."""
    lw = 230
    vmax = vmax or max(r[1] for r in rows) * 1.25
    H = row_h * len(rows)
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">']
    for i, (lab, v, col) in enumerate(rows):
        y = i * row_h
        bw = (W - lw - 110) * v / vmax
        el.append(f'<text x="0" y="{y + row_h * 0.62:.1f}" font-size="24" fill="{TEXT}">{esc(lab)}</text>')
        el.append(f'<rect x="{lw}" y="{y + 10}" width="{bw:.1f}" height="{row_h - 20}" fill="{col}"/>')
        el.append(label_el(lw + bw + 10, y + row_h * 0.64, fmt(v), 24, TEXT, "start"))
    el.append(f'<line x1="{lw}" x2="{lw}" y1="0" y2="{H}" stroke="{TEXT}" stroke-width="2"/>')
    el.append("</svg>")
    return "".join(el)


# ---------------------------------------------------------------- slides
def legend(items):
    return '<div class="legend">' + "".join(
        f'<span><i style="background:{c}"></i>{esc(t)}</span>' for t, c in items) + "</div>"


def build(s):
    yrs = list(range(1972, 2027))
    run = {2023, 2024, 2025, 2026}
    slides = []

    # 1 Result -------------------------------------------------------------
    ay = list(range(1990, 2027))
    pe = s["agency_prior_end"]
    prior = set(range(pe - 3, pe + 1))
    ch1 = bars([str(y) for y in ay], [s["agency_year"][y] for y in ay], H=300, ymax=19,
               colors=[FIRE if y in run else NEUTRAL for y in ay],
               fan=[([ay.index(y) for y in sorted(run)], f"2023 to 2026: {f1(s['agency_run'])}", FIRE)],
               ticks={"1990", "2000", "2010", "2020"}, grid=[5, 10, 15],
               gridfmt=lambda g: f"{g}", bar_frac=0.78, lsize=22)
    slides.append(dict(
        kicker="Canada's wildfires, 2023 to 2026",
        head="Wildfires burned 35.9 million hectares from 2023 to 2026, about the size of Germany",
        body=f'''
<div class="bigrow"><div class="big fire">2×</div>
<div class="bigcap">the land burned in any earlier four years since 1990</div></div>
<div class="note">Land burned each year, million hectares</div>
<div class="chart">{ch1}</div>
<p class="body sm">This is about {round(V("C2.union_pct"))}% of Canada's forest.</p>
<p class="foot">Totals reported by provincial, territorial and Parks Canada fire agencies, 1990 to 2026.</p>''',
        source="CCFM National Forestry Database; CWFIS · Canada, 1990 to 2026 · Oct 2026 · CC BY 4.0"))

    # 2 Climate ------------------------------------------------------------
    ty = list(range(1950, 2027))
    tlab = [("+" + f1(s["temp"][y]) + "°C") if y == 2023 else None for y in ty]
    ch2 = bars([str(y) for y in ty], [s["temp"][y] for y in ty], H=236, ymin=-1.5, ymax=2.6,
               colors=[FIRE if y in run else NEUTRAL for y in ty], labels=tlab,
               ticks={"1950", "1970", "1990", "2010", "2026"}, grid=[-1, 1, 2],
               gridfmt=lambda g: f"{g:+d}°C", bar_frac=0.8, lsize=22,
               refs=[dict(value=V("C6.warming_c"), span=(66, 76), color=TEXT)])
    share = V("C9.share_attributable")
    third = "about a third" if 0.29 <= share <= 0.38 else f"about {round(share * 100)}%"
    slides.append(dict(
        kicker="Climate",
        head="Summers in Canada's forests are 1.1°C warmer than in the 1960s to 1980s",
        body=f'''
<div class="statrow">
  <div><div class="stat fire">1 in {round(1 / V("C9.share_attributable"))}</div><div class="statcap">hectares burned in 2023 to 2026 came from the warming</div></div>
  <div><div class="stat fire">2×</div><div class="statcap">Canada warms twice as fast as the world, mostly from human activity</div></div>
</div>
<div class="note">Summer temperature each year, compared with 1961 to 1990</div>
<div class="chart">{ch2}</div>
<p class="foot">Sources: ECCC climate data; Canada's Changing Climate Report (2019); IPCC AR6.</p>''',
        source="ECCC homogenized climate data and station records · forested Canada, 1950 to 2026 · Oct 2026 · CC BY 4.0"))

    # 3 Drought ------------------------------------------------------------
    dy = list(range(2003, 2027))
    dlab = [f"{round(V(f'C12.d1_max_pct.{y}'))}%" if y in run else
            (f"{round(s['drought'][y])}%" if abs(s["drought"][y] - V("C12.max_2003_2022")) < 0.1 else None) for y in dy]
    ch3 = bars([str(y) for y in dy], [s["drought"][y] for y in dy], H=300, ymax=85,
               colors=[FIRE if y in run else NEUTRAL for y in dy], labels=dlab,
               ticks={"2003", "2008", "2013", "2018", "2023"}, grid=[25, 50, 75],
               gridfmt=lambda g: f"{g}%", lsize=24,
               refs=[dict(value=V("C12.mean_2003_2022"), span=(0, 19),
                          label=f"2003 to 2022 average {round(V('C12.mean_2003_2022'))}%")])
    slides.append(dict(
        kicker="Drought",
        head="2023 to 2026 were the driest four years since 1950",
        body=f'''
<div class="bigrow"><div class="big">{round(V("C10.pct_of_normal"))}%</div>
<div class="bigcap">of usual April to September rain fell, on average, from 2023 to 2026</div></div>
<div class="note">Share of the forest in drought, April to September</div>
<div class="chart">{ch3}</div>
<p class="body">Each of these years had more forest in drought than any year from 2003 to 2022.</p>
<p class="foot">Sources: Canadian Drought Monitor; ECCC weather stations.</p>''',
        source="AAFC Canadian Drought Monitor; ECCC climate data · Canada, 1950 to 2026 · Oct 2026 · CC BY 4.0"))

    # 4 Expected vs actual -------------------------------------------------
    ry = [2023, 2024, 2025, 2026]
    ch4a = bars([str(y) for y in ry], [s["fires"][y] for y in ry], H=260, ymax=8200,
                colors=[NEUTRAL] * 4, labels=[fint(s["fires"][y]) for y in ry], grid=[4000, 8000],
                gridfmt=lambda g: f"{g // 1000}k", bar_frac=0.5,
                refs=[dict(value=s["fires_avg"], span=(0, 3))])
    ch4b = bars([str(y) for y in ry], [list(s["model"][y]) for y in ry], H=180, ymax=3.0,
                group=[FIRE, NEUTRAL], grid=[1, 2, 3], gridfmt=lambda g: f"{g}%",
                labels=[[f"{s['model'][y][0]:.1f}%", f"{s['model'][y][1]:.2f}%"] for y in ry], bar_frac=0.6)
    slides.append(dict(
        kicker="Causes",
        head="Fewer fires started than average, and they burned more land than predicted",
        body=f'''
<div class="note">Number of fires each year; dashed line: the 1991 to 2020 average, {fint(s["fires_avg"])}</div>
<div class="chart">{ch4a}</div>
<p class="body sm">People started {fint(V("C13.human_2026"))} fires in 2026, the lowest number in 37 years.</p>
<div class="statrow">
  <div><div class="stat fire">{round(V("C14.area_share_pct"))}%</div><div class="statcap">of the land burned in 2026 was from fires started by lightning</div></div>
  <div><div class="stat fire">{round(V("C15.ratio_after"))} times</div><div class="statcap">the forest area predicted from drought and weather</div></div>
</div>
<p class="foot">Prediction from 2003 to 2022 drought, weather and fire records.</p>''',
        source="NRCan Fire Database, CWFIS; AAFC Drought Monitor · Canada, 1991 to 2026 · Oct 2026 · CC BY 4.0"))

    # 5 People -------------------------------------------------------------
    direct = {y: int(V(f"C19.direct_deaths.{y}")) + (WAINWRIGHT_DEATHS if y == 2026 else 0) for y in ry}
    sm = {y: (V(f"C18.{y}.aqbat"), V(f"C18.{y}.chen")) if y in (2023, 2026) else
          (round(s["smoke"][y][0]), round(s["smoke"][y][1])) for y in ry}
    ch5 = bars([str(y) for y in ry], [[sm[y][0], direct[y]] for y in ry], H=215, ymax=1100,
               group=[MUTED, FIRE], ranges=[[sm[y][1], None] for y in ry],
               labels=[[f"{fint(sm[y][0])} to {fint(sm[y][1])}", str(direct[y])] for y in ry],
               grid=[500, 1000], gridfmt=lambda g: fint(g), bar_frac=0.62)
    lo_r = sum(sm[y][0] for y in ry) / sum(direct.values())
    hi_r = sum(sm[y][1] for y in ry) / sum(direct.values())
    lo_w, hi_w = int(round(lo_r, -1)), int(round(hi_r, -1))
    ed = s["ed"]
    ed_tot = ed.loc[2023:2025, "extra_visits"].sum()
    ed_lo, ed_hi = ed.loc[2023:2025, "extra_visits_lo"].sum(), ed.loc[2023:2025, "extra_visits_hi"].sum()
    sd_lo, sd_hi = sum(sm[y][0] for y in ry), sum(sm[y][1] for y in ry)
    slides.append(dict(
        kicker="Health",
        head=f"Wildfire smoke caused about {fint(round(ed_tot, -3))} extra emergency room visits and {fint(round(sd_lo, -2))} to {fint(round(sd_hi, -2))} early deaths",
        body=f'''
{legend([("Smoke deaths, low", MUTED), ("high", NEUTRAL), ("Deaths in the fires", FIRE)])}
<div class="chart">{ch5}</div>
<p class="body sm">Smoke caused {lo_w} to {hi_w} early deaths for each death in the fires.</p>
<p class="foot">Emergency visits: 2023 to 2025; 2026 data not yet released. Early deaths: range from two health studies. Deaths in the fires include 4 soldiers at CFB Wainwright.</p>''',
        source="CIHI NACRS; NAPS and AirNow PM2.5; StatCan; TSB; DND · 2023 to 2026 · Oct 2026 · CC BY 4.0"))

    # 6 Property -----------------------------------------------------------
    val = s["value"]
    ch6 = bars([str(y) for y in ry], [val[y] for y in ry], H=300, ymax=720,
               colors=[FIRE] * 4, labels=[f"${fint(val[y])}M" for y in ry],
               grid=[250, 500], gridfmt=lambda g: f"${g}M", bar_frac=0.5, tick_size=22)
    vtot = sum(val.values()) / 1000
    slides.append(dict(
        kicker="Property",
        head=f"Fires destroyed homes and buildings worth about ${vtot:.1f} billion",
        body=f'''
<div class="note">Value of homes and buildings destroyed, by year</div>
<div class="chart">{ch6}</div>
<div class="statrow">
  <div><div class="stat">{fint(V("C25.roads_km"))} km</div><div class="statcap">of roads ran through burned land</div></div>
  <div><div class="stat">{fint(V("C25.rail_km"))} km</div><div class="statcap">of railway ran through burned land</div></div>
</div>
<p class="foot">About {fint(round(sum(s["value_bldg"].values()), -2))} buildings, found in satellite photos and valued at local census home values.</p>''',
        source="Sentinel-2; Microsoft footprints; StatCan Census, roads; NRCan rail · 2023 to 2026 · Oct 2026 · CC BY 4.0"))

    # 7 Economy ------------------------------------------------------------
    fy = list(range(2016, 2026))
    ch7 = bars([str(y) for y in fy], [s["firefight"][y] for y in fy], H=300, ymax=2.9,
               colors=[FIRE if y in run else NEUTRAL for y in fy],
               labels=[f"${s['firefight'][y]:.1f}B" if y in run or y == 2021 else None for y in fy],
               grid=[1, 2], gridfmt=lambda g: f"${g}B", bar_frac=0.66, lsize=22,
               refs=[dict(value=V("C28.mean_2016_2022_b"), span=(0, 6),
                          label=f"2016 to 2022 average ${V('C28.mean_2016_2022_b'):.1f}B", dy=-38)])
    slides.append(dict(
        kicker="Economy",
        head=f"Fires burned ${f1(V('C27.timber_2023_nominal_b'))} billion of trees in 2023, and firefighting costs doubled",
        body=f'''
<div class="statrow">
  <div><div class="stat fire">${f1(V("C27.timber_2023_nominal_b"))}B</div><div class="statcap">value of the trees burned in 2023</div></div>
  <div><div class="stat fire">${V("C28.mean_2023_2025_b"):.1f}B</div><div class="statcap">firefighting a year in 2023 to 2025, up from ${V("C28.mean_2016_2022_b"):.1f}B</div></div>
</div>
<div class="note">Firefighting cost each year, BC, Ontario, Alberta and Saskatchewan, 2025 dollars</div>
<div class="chart">{ch7}</div>
<p class="foot">Trees valued at provincial cutting fees. 2026 not yet reported.</p>''',
        source="National Forestry Database; BC, ON, AB, SK public accounts · 2016 to 2025 · Oct 2026 · CC BY 4.0"))

    # 8 Environment --------------------------------------------------------
    cy = list(range(2016, 2025))
    ch8 = bars([str(y) for y in cy], [list(s["co2"][y]) for y in cy], H=420, ymax=1000,
               group=[NEUTRAL, FIRE], grid=[500, 1000], gridfmt=lambda g: fint(g),
               labels=[[fint(s["co2"][y][0]) if y == 2023 else None, fint(s["co2"][y][1])] for y in cy],
               bar_frac=0.78, lsize=21)
    rb = s["reburn"]
    ch8b = hbars([("1990s", rb["1990-1999"], NEUTRAL), ("2023 to 2026", rb["2023-2026"], FIRE)],
                 row_h=56, vmax=10, fmt=lambda v: f"{f1(v)}%")
    slides.append(dict(
        kicker="Environment",
        head="Wildfire emissions in 2023 were larger than Canada's official emissions total",
        body=f'''
{legend([("Canada's official total", NEUTRAL), ("Wildfires", FIRE)])}
<div class="note">Million tonnes of CO₂ each year</div>
<div class="chart">{ch8}</div>
<p class="body sm">Canada reports wildfire emissions separately from its official total.</p>
<p class="foot">Official inventory 2026, forests managed for timber only; 2025 and 2026 not yet reported.</p>''',
        source="ECCC National Inventory Report 2026; NBAC; SCANFI · Canada, 1990 to 2026 · Oct 2026 · CC BY 4.0"))

    # 9 Bottom line --------------------------------------------------------
    slides.append(dict(
        kicker="Bottom line",
        head="Most land burned in remote fires that grew fast, in hotter and drier seasons from global warming",
        body=f'''
<ul class="needs">
<li><b>About {round(sum(s["escape72"]) / 20)} in 10</b> hectares burned in fires that grew past 1,000 hectares within 3 days. Needed: faster response to remote fires.</li>
<li><b>{"At least half" if s["monitored"][0] >= 45 else str(round(s["monitored"][0])) + "%"}</b> of the land burned in fires that agencies chose to monitor. Needed: a review of which fires to fight.</li>
<li><b>Smoke illness, smoke deaths and wildfire carbon</b> are outside official counts. Needed: count them.</li>
</ul>
<div class="explore"><div class="ex1">Explore the full story and the data</div>
<div class="ex2">Link in bio · sjvadrevu.github.io/canada-wildfires-2026</div></div>
<div class="brand"><img src="logo-dark.png" alt="The Median Canadian"></div>
<div class="sources"><b>Data sources.</b> NRCan Canadian Wildland Fire Information System (NBAC, M3 outlines, National Fire Database, CNFDB), Land Cover 2020 and SCANFI; ECCC homogenized climate data, climate stations and National Inventory Report 2026; AAFC Canadian Drought Monitor; NAPS and AirNow air quality; Statistics Canada 2021 Census and road network; NRCan rail network; Transportation Safety Board; Public Safety Canada; Health Canada AQBAT and Chen et al. 2021 coefficients; Copernicus Sentinel-2; Microsoft building footprints (ODbL); National Forestry Database; provincial public accounts (BC, ON, AB, SK); agency fire response records; IPCC AR6 and ECCC Canada's Changing Climate Report.</div>
<div class="sources"><b>Licence.</b> Analysis and charts CC BY 4.0, The Median Canadian. Source data under the Open Government Licence (Canada) and each source's own licence. Photos: All Canada Photos, licensed separately and not covered by CC BY 4.0.</div>''',
        source=None, last=True))
    return slides


CSS = f"""
:root {{ --text:{TEXT}; --muted:{MUTED}; --grid:{GRID}; --fire:{FIRE}; --forest:{FOREST}; --neutral:{NEUTRAL}; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#0c1016; font-family:{FONT}; color:var(--text); }}
.slide {{ position:relative; width:1080px; height:1350px; background:#0c1016; overflow:hidden; }}
.photo {{ position:absolute; inset:0; background-size:cover; background-repeat:no-repeat; }}
.shade {{ position:absolute; inset:0; background:linear-gradient(180deg, rgba(8,11,16,0.55) 0%, rgba(8,11,16,0.30) 14%, rgba(8,11,16,0.45) 30%, rgba(8,11,16,0.62) 100%); }}
.content {{ position:absolute; top:80px; left:76px; right:76px; }}
.kicker {{ font-size:27px; font-weight:700; text-transform:uppercase; letter-spacing:0.09em; color:#ffd2c7; text-shadow:0 2px 10px rgba(0,0,0,0.8); }}
h1 {{ font-size:74px; font-weight:800; line-height:1.07; letter-spacing:-0.022em; color:#fff; margin-top:18px; text-shadow:0 3px 18px rgba(0,0,0,0.85), 0 1px 3px rgba(0,0,0,0.9); }}
h1.four {{ font-size:60px; }}
#s9 h1 {{ font-size:54px; }}
#s9 .sources {{ font-size:16px; margin-top:14px; }}
#s9 .needs {{ font-size:30px; }}
#s9 .needs li {{ margin-top:8px; }}
#s9 .brand {{ margin-top:24px; }}
#s9 .brand img {{ height:84px; }}
#s9 .explore {{ margin-top:20px; padding:22px 30px; }}
.card {{ margin:26px -34px 0; padding:4px 34px 26px; background:rgba(10,13,19,0.78); border-radius:26px; backdrop-filter:blur(3px); }}
.body {{ font-size:33px; line-height:1.42; margin-top:22px; }}
.body.sm {{ margin-top:14px; }}
.bigrow {{ display:flex; align-items:center; gap:30px; margin-top:22px; }}
.big {{ font-size:128px; font-weight:800; line-height:1; letter-spacing:-0.03em; white-space:nowrap; }}
.fire {{ color:var(--fire); }}
.bigcap {{ font-size:30px; line-height:1.3; color:var(--text); }}
.note {{ font-size:24px; color:var(--muted); margin-top:22px; line-height:1.3; }}
.chart {{ margin-top:8px; line-height:0; }}
.legend {{ display:flex; gap:28px; flex-wrap:wrap; margin-top:22px; font-size:24px; color:var(--text); }}
.legend i {{ display:inline-block; width:22px; height:22px; margin-right:10px; vertical-align:-3px; }}
.statrow {{ display:flex; gap:40px; margin-top:22px; }}
.statrow > div {{ flex:1; }}
.stat {{ font-size:88px; font-weight:800; line-height:1.05; letter-spacing:-0.02em; white-space:nowrap; }}
.statcap {{ font-size:27px; line-height:1.3; margin-top:4px; }}
.sub {{ font-size:33px; font-weight:700; margin-top:22px; line-height:1.25; }}
.foot {{ font-size:21px; line-height:1.38; color:var(--muted); margin-top:18px; }}
.footer-logo {{ position:absolute; left:76px; bottom:64px; height:78px; filter:drop-shadow(0 2px 8px rgba(0,0,0,0.7)); }}
.pagenum {{ position:absolute; right:76px; bottom:64px; height:78px; line-height:78px; font-size:27px; font-weight:700; color:#fff; text-shadow:0 2px 8px rgba(0,0,0,0.8); }}
.source {{ position:absolute; left:76px; right:76px; bottom:22px; font-size:18px; color:#d5dae1; white-space:nowrap; overflow:hidden; text-shadow:0 1px 6px rgba(0,0,0,0.9); }}
.credit {{ position:absolute; top:24px; right:30px; font-size:16px; color:rgba(255,255,255,0.85); text-shadow:0 1px 5px rgba(0,0,0,0.9); }}
.needs {{ margin-top:22px; padding-left:34px; font-size:31px; line-height:1.32; }}
.needs li {{ margin-top:12px; }}
.explore {{ margin-top:24px; border:3px solid rgba(255,255,255,0.3); border-radius:22px; padding:30px 34px; }}
.ex1 {{ font-size:40px; font-weight:800; line-height:1.15; }}
.ex2 {{ font-size:28px; color:var(--muted); margin-top:12px; }}
.brand {{ margin-top:40px; }}
.brand img {{ height:110px; display:block; }}
.tagline {{ font-size:30px; line-height:1.35; margin-top:14px; }}
.sources {{ font-size:20px; line-height:1.42; color:var(--muted); margin-top:26px; }}
.sources b {{ color:var(--text); }}
"""


def page(slides):
    out = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Wildfires carousel</title><style>{CSS}</style></head><body>"]
    for i, sl in enumerate(slides, 1):
        f, pos, size = PHOTOS[i]
        out.append(f'<section class="slide" id="s{i}"><div class="photo" style="background-image:url(\'{PHOTO_DIR}/{f}\');'
                   f'background-position:{pos};background-size:{size}"></div><div class="shade"></div><div class="content">')
        out.append(f'<div class="kicker">{esc(sl["kicker"])}</div><h1>{esc(sl["head"])}</h1><div class="card">{sl["body"]}</div></div>')
        if not sl.get("last"):
            out.append('<img class="footer-logo" src="logo-dark.png" alt="The Median Canadian">')
        out.append(f'<div class="pagenum">{"Swipe →" if i == 1 else f"{i}/{N_SLIDES}"}</div>')
        if sl["source"]:
            out.append(f'<div class="source">{esc(sl["source"])}</div>')
        out.append(f'<div class="credit">Photo: {esc(CREDITS[i])} / All Canada Photos, not CC BY</div>')
        out.append("</section>")
    out.append("""<script>
for (const h of document.querySelectorAll('h1')) {
  const lines = Math.round(h.getBoundingClientRect().height / (74 * 1.07));
  if (lines >= 4) h.classList.add('four');
}
</script></body></html>""")
    return "".join(out)


MEASURE = """(id) => {
  const s = document.getElementById(id), top = s.getBoundingClientRect().top;
  const c = s.querySelector('.content');
  let bottom = 0, right = 0;
  for (const e of c.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.height === 0 && r.width === 0) continue;
    bottom = Math.max(bottom, r.bottom - top); right = Math.max(right, r.right - s.getBoundingClientRect().left);
  }
  const logo = s.querySelector('.footer-logo'), pn = s.querySelector('.pagenum'), src = s.querySelector('.source');
  const h = s.querySelector('h1');
  return {
    bottom, right,
    logoTop: logo ? logo.getBoundingClientRect().top - top : null,
    pageTop: pn.getBoundingClientRect().top - top,
    logoLoaded: logo ? (logo.complete && logo.naturalWidth > 0) : true,
    headLines: Math.round(h.getBoundingClientRect().height / parseFloat(getComputedStyle(h).lineHeight)),
    headSize: getComputedStyle(h).fontSize,
    srcOneLine: src ? (src.scrollWidth <= src.clientWidth + 1) : true,
    srcTop: src ? src.getBoundingClientRect().top - top : null,
    logoBottom: logo ? logo.getBoundingClientRect().bottom - top : null,
  };
}"""

BANNED = [r"\bnow\b", r"\btoday\b", r"\bcurrently\b", "\u2014"]


def main():
    s = series()
    warns = consistency(s)
    slides = build(s)
    html_text = page(slides)
    out_html = os.path.join(HERE, "slides_photo.html")
    open(out_html, "w").write(html_text)

    visible = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", html_text, flags=re.S)
    for pat in BANNED:
        for m in re.finditer(pat, visible):
            warns.append(f"banned text {pat!r}: ...{visible[max(0, m.start() - 40):m.end() + 40]}...")

    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    from playwright.sync_api import sync_playwright
    report, ok = [], True
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        pg.goto("file://" + out_html)
        pg.wait_for_load_state("networkidle")
        for i in range(1, N_SLIDES + 1):
            m = pg.evaluate(MEASURE, f"s{i}")
            limit = m["logoTop"] if m["logoTop"] is not None else m["pageTop"]
            gap = limit - m["bottom"]
            issues = []
            if gap < 18:
                issues.append(f"content too close to footer (gap {gap:.0f}px)")
            if m["right"] > 1080 - 40 + 1:
                issues.append(f"content wider than margin (right {m['right']:.0f})")
            if not m["srcOneLine"]:
                issues.append("source line wraps or clips")
            if not m["logoLoaded"]:
                issues.append("logo not loaded")
            if m["srcTop"] is not None and m["logoBottom"] is not None and m["srcTop"] < m["logoBottom"]:
                issues.append("source line overlaps logo")
            ok &= not issues
            report.append(f"slide {i}: content bottom {m['bottom']:.0f}, footer top {limit:.0f}, gap {gap:.0f}px, "
                          f"heading {m['headLines']} lines at {m['headSize']}" + (f"  !! {'; '.join(issues)}" if issues else "  ok"))
            pg.locator(f"#s{i}").screenshot(path=os.path.join(HERE, f"photo-preview/the-median-canadian-wildfires-{i}-of-{N_SLIDES}.png"))
        b.close()

    nver = sum(1 for v in NUM_SOURCE.values() if v == "verified")
    print(f"numbers: {nver} of {len(NUM)} from verified_numbers.json" if os.path.exists(VERIFIED)
          else "numbers: verified_numbers.json not found, using draft readings")
    missing = [k for k, v in NUM_SOURCE.items() if v == "draft"]
    if os.path.exists(VERIFIED) and missing:
        print("  not in verified file (draft value kept):", ", ".join(missing))
    print("\n".join(report))
    for w in warns:
        print("WARNING:", w)
    sys.exit(0 if ok and not warns else 1)


if __name__ == "__main__":
    main()
