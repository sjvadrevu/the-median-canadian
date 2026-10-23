"""Option visuals for slides 3 (health), 4 (costs) and 5 (carbon). Every value is read from the analysis files."""
import math
import os

import pandas as pd

from canmap import CanMap

AN = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis"))
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, 'Helvetica Neue', Arial, sans-serif"
TEXT, MUTED, FIRE = "#f4f6f9", "#c3cad4", "#ff6b4f"
LAND, EDGE = "#323a47", "#4d5768"


def _svg(W, H, y0=0):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H - y0:.0f}" viewBox="0 {y0:.0f} {W} {H - y0:.0f}" font-family="{FONT}">']


def _lab(x, y, t, size=22, col=TEXT, anchor="middle", weight=700):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{col}" text-anchor="{anchor}" '
            f'stroke="#10151c" stroke-width="6" stroke-linejoin="round" paint-order="stroke">{t}</text>')


def _smoke_col(v):
    # 0 to 27: low; 27 to 60; 60 to 100; above 100 (micrograms per cubic metre)
    stops = [(0, (52, 60, 72)), (10, (90, 96, 104)), (27, (233, 160, 92)), (60, (230, 90, 60)), (100, (160, 30, 40))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if v <= b:
            f = (v - a) / (b - a)
            return "rgb(%d,%d,%d)" % tuple(round(ca[i] + f * (cb[i] - ca[i])) for i in range(3))
    return "rgb(120,20,30)"


def smoke_calendar(W=928):
    d = pd.read_csv(os.path.join(AN, "health/daily_popweighted_pm25.csv"), parse_dates=["date"])
    d = d[d.group == "Canada"]
    years = [2023, 2024, 2025, 2026]
    days = pd.date_range("2023-05-01", "2023-09-30").strftime("%m-%d")
    left, cell_gap = 70, 1
    cw = (W - left) / len(days)
    ch = 46
    H = len(years) * (ch + 14) + 70
    el = _svg(W, H)
    worst = None
    for r, y in enumerate(years):
        dy = d[(d.date.dt.year == y)].set_index(d[d.date.dt.year == y].date.dt.strftime("%m-%d")).popw_pm25
        top = r * (ch + 14)
        el.append(_lab(0, top + ch / 2 + 8, str(y), 24, TEXT, "start"))
        for k, md in enumerate(days):
            v = dy.get(md)
            col = _smoke_col(v) if v == v and v is not None else "#222831"
            el.append(f'<rect x="{left + k * cw:.2f}" y="{top}" width="{max(cw - cell_gap, 0.5):.2f}" height="{ch}" fill="{col}"/>')
            if v is not None and v == v and (worst is None or v > worst[0]):
                worst = (v, y, md, left + k * cw, top)
    for m, md in [("May", "05-01"), ("Jun", "06-01"), ("Jul", "07-01"), ("Aug", "08-01"), ("Sep", "09-01")]:
        k = list(days).index(md)
        el.append(f'<text x="{left + k * cw:.1f}" y="{len(years) * (ch + 14) + 6}" font-size="20" fill="{MUTED}">{m}</text>')
    v, y, md, x, top = worst
    el.append(f'<rect x="{x - 1:.1f}" y="{top - 3}" width="{cw + 2:.1f}" height="{ch + 6}" fill="none" stroke="#fff" stroke-width="2.5"/>')
    lx = min(max(x, 260), W - 230)
    el.append(_lab(lx, top - 10 if top > 30 else top + ch + 30, f"Smokiest day: July 16, {y}", 22, TEXT))
    ly = len(years) * (ch + 14) + 46
    for i, (lab, val) in enumerate([("Clean", 5), ("Some smoke", 20), ("Unhealthy", 45), ("Very unhealthy", 80), ("Hazardous", 120)]):
        x0 = left + i * 168
        el.append(f'<rect x="{x0}" y="{ly - 16}" width="20" height="20" fill="{_smoke_col(val)}"/>')
        el.append(f'<text x="{x0 + 28}" y="{ly}" font-size="19" fill="{MUTED}">{lab}</text>')
    el.append("</svg>")
    return "".join(el), worst


def smoke_city_map(W=928):
    m = CanMap(W)
    c = pd.read_csv(os.path.join(AN, "people/city_smoke_days.csv"))
    c = c[(c.group == "top30_popcentre_2021") & c.year.between(2023, 2026)]
    days = c.groupby("city").days_gt27_may_sep.sum()
    t = pd.read_csv(os.path.join(AN, "people/city_search_table_flat.csv"), low_memory=False)
    t = t[t.is_population_centre == True].drop_duplicates("name").set_index("name")
    y0 = m.xy(-96, 61.5)[1]
    el = _svg(W, m.H - 40, y0)
    el.append(f'<path d="{m.base_path()}" fill="{LAND}" stroke="{EDGE}" stroke-width="1"/>')
    rows = []
    for city, nd in days.items():
        if city not in t.index:
            continue
        r = t.loc[city]
        x, y = m.xy(r.lon, r.lat)
        rows.append((nd, city, x, y, r.pop2021))
    for nd, city, x, y, pop in sorted(rows, key=lambda r: -r[4]):
        rad = 5 + 24 * math.sqrt(pop / 6e6)
        col = _smoke_col(20 + nd * 1.2)
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{col}" fill-opacity="0.9" stroke="#10151c" stroke-width="1.5"/>')
    top = sorted(rows, key=lambda r: -r[0])[:4]
    offs = {"Edmonton": (0, -22, "middle"), "Calgary": (-16, 8, "end"), "Saskatoon": (16, -10, "start"), "Regina": (16, 26, "start")}
    for nd, city, x, y, pop in top:
        dx, dy, an = offs.get(city, (0, -18, "middle"))
        el.append(_lab(x + dx, y + dy, f"{city}: {int(nd)} days", 20, TEXT, an))
    el.append("</svg>")
    return "".join(el), top


LOSS = [  # event ids in property/destroyed_value_estimates.csv, marker place (town in the StatCan table), label
    (["mcdougall2023", "bushcreek2023", "baldrange2026", "bradleycreek2026"], "Kelowna", "Okanagan and Shuswap"),
    (["jasper2024"], "Jasper", "Jasper"),
    (["tantallon2023"], "Halifax", "Upper Tantallon"),
    (["barrington2023"], "Shelburne", "Barrington Lake"),
    (["denare2025"], "Flin Flon", "Denare Beach"),
    (["lacdubonnet2025"], "Lac du Bonnet", "Lac du Bonnet"),
]


def loss_map(W=928):
    m = CanMap(W)
    pv = pd.read_csv(os.path.join(AN, "property/destroyed_value_estimates.csv")).set_index("event").proxy_value_avg_cad
    t = pd.read_csv(os.path.join(AN, "people/city_search_table_flat.csv"), low_memory=False)
    t = t[t.is_population_centre == True]
    y0 = m.xy(-96, 61.5)[1]
    el = _svg(W, m.H - 40, y0)
    el.append(f'<path d="{m.base_path()}" fill="{LAND}" stroke="{EDGE}" stroke-width="1"/>')
    vals = []
    for ev, town, label in LOSS:
        v = pv.reindex(ev).sum() / 1e6
        r = t[t.name == town]
        if town == "Shelburne":
            r = r[r.prov == "NS"]
        r = r.iloc[0]
        x, y = m.xy(r.lon, r.lat)
        vals.append((v, label, x, y))
    vmax = max(v for v, *_ in vals)
    for v, label, x, y in sorted(vals, key=lambda r: -r[0]):
        rad = 8 + 70 * math.sqrt(v / vmax)
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{FIRE}" fill-opacity="0.85" stroke="#10151c" stroke-width="2"/>')
    offs = {"Okanagan and Shuswap": (-40, 98, "start"), "Jasper": (10, -58, "middle"), "Upper Tantallon": (-30, -40, "middle"),
            "Barrington Lake": (-40, 44, "middle"), "Denare Beach": (34, -8, "start"), "Lac du Bonnet": (20, 40, "start")}
    for v, label, x, y in vals:
        dx, dy, an = offs[label]
        el.append(_lab(x + dx, y + dy, f"{label} ${v:,.0f}M", 21, TEXT, an))
    el.append("</svg>")
    other = pv.get("2026 all outlines", 0) / 1e6 - pv.reindex(["baldrange2026", "bradleycreek2026"]).sum() / 1e6
    return "".join(el), vals, other


def receipt(items, total_label, W=560):
    """A paper bill: items (label, dollars in billions)."""
    rows = len(items)
    H = 140 + rows * 64 + 110
    el = _svg(W, H)
    el.append(f'<path d="M0,0 H{W} V{H - 14} ' + " ".join(f"L{W - (i + 0.5) * W / 14:.1f},{H if i % 2 == 0 else H - 14}" for i in range(14)) +
              f' L0,{H - 14} Z" fill="#f4efe6"/>')
    ink = "#1b2330"
    el.append(f'<text x="{W / 2}" y="52" font-size="30" font-weight="800" fill="{ink}" text-anchor="middle">WILDFIRE BILL</text>')
    el.append(f'<text x="{W / 2}" y="84" font-size="20" fill="#5b6575" text-anchor="middle">Canada, 2023 to 2026</text>')
    el.append(f'<line x1="30" x2="{W - 30}" y1="106" y2="106" stroke="{ink}" stroke-dasharray="4 4"/>')
    y = 150
    for lab, v in items:
        el.append(f'<text x="34" y="{y}" font-size="24" fill="{ink}">{lab}</text>')
        el.append(f'<text x="{W - 34}" y="{y}" font-size="26" font-weight="700" fill="{ink}" text-anchor="end">${v:.1f}B</text>')
        y += 64
    el.append(f'<line x1="30" x2="{W - 30}" y1="{y - 34}" y2="{y - 34}" stroke="{ink}" stroke-width="2"/>')
    tot = sum(v for _, v in items)
    el.append(f'<text x="34" y="{y + 12}" font-size="28" font-weight="800" fill="{ink}">{total_label}</text>')
    el.append(f'<text x="{W - 34}" y="{y + 12}" font-size="36" font-weight="800" fill="#c0392b" text-anchor="end">${tot:.1f}B</text>')
    el.append("</svg>")
    return "".join(el), tot


def emissions_line(W=928, H=520):
    inv = pd.read_csv(os.path.join(AN, "threads/t1_official_inventory_lines.csv"))
    yrs = list(inv.year)
    nat = list(inv.national_total_excl_lulucf_kt / 1000)
    wf = list(inv.nir_wildfire_direct_immediate_kt_co2e / 1000)
    left, right, top, bottom = 76, 160, 30, 50
    pw, ph = W - left - right, H - top - bottom
    sx = lambda i: left + pw * i / (len(yrs) - 1)
    sy = lambda v: top + ph * (1000 - v) / 1000
    el = _svg(W, H)
    for g in (250, 500, 750, 1000):
        el.append(f'<line x1="{left}" x2="{W - right}" y1="{sy(g):.1f}" y2="{sy(g):.1f}" stroke="rgba(255,255,255,0.18)" stroke-width="2"/>')
        el.append(f'<text x="{left - 10}" y="{sy(g) + 7:.1f}" font-size="20" fill="{MUTED}" text-anchor="end">{g:,}</text>')
    for i, y in enumerate(yrs):
        if y % 2 == 0 or y == yrs[-1]:
            el.append(f'<text x="{sx(i):.1f}" y="{H - 14}" font-size="20" fill="{MUTED}" text-anchor="middle">{y}</text>')
    for vals, col, w in [(nat, "#c3cad4", 5), (wf, FIRE, 6)]:
        el.append(f'<polyline points="{" ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(vals))}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linejoin="round"/>')
    i23 = yrs.index(2023)
    el.append(f'<circle cx="{sx(i23):.1f}" cy="{sy(wf[i23]):.1f}" r="9" fill="{FIRE}"/>')
    el.append(_lab(sx(i23), sy(wf[i23]) - 18, f"Wildfires {wf[i23]:,.0f}", 24, FIRE))
    el.append(_lab(sx(len(yrs) - 1) + 8, sy(nat[-1]) + 8, "Official total", 21, "#c3cad4", "start"))
    el.append(_lab(sx(len(yrs) - 1) + 8, sy(wf[-1]) + 8, "Wildfires", 21, FIRE, "start"))
    el.append("</svg>")
    return "".join(el), (nat[i23], wf[i23])


def months_grid(W=928):
    inv = pd.read_csv(os.path.join(AN, "threads/t1_official_inventory_lines.csv")).set_index("year")
    nat = inv.loc[2023, "national_total_excl_lulucf_kt"] / 1000
    wf = inv.loc[2023, "nir_wildfire_direct_immediate_kt_co2e"] / 1000
    months = wf / (nat / 12)
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    n = math.ceil(months)
    cols = 6
    cw, chh, gap = (W - gap_x(cols)) / cols, 96, 12
    rows = math.ceil(n / cols)
    H = rows * (chh + gap)
    el = _svg(W, H)
    for k in range(n):
        r, c = divmod(k, cols)
        x, y = c * (cw + gap), r * (chh + gap)
        frac = min(1, months - k)
        el.append(f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{chh}" rx="8" fill="#3a4250"/>')
        el.append(f'<rect x="{x:.1f}" y="{y}" width="{cw * frac:.1f}" height="{chh}" rx="8" fill="{FIRE}"/>')
        el.append(f'<text x="{x + cw / 2:.1f}" y="{y + chh / 2 + 10}" font-size="26" font-weight="700" fill="#fff" text-anchor="middle">{names[k % 12]}</text>')
    el.append("</svg>")
    return "".join(el), months


def gap_x(cols, gap=12):
    return gap * (cols - 1)


def smoke_weeks(W=928):
    """Simpler calendar: one box per week, May to September, coloured by the week's smokiest day where Canadians live."""
    d = pd.read_csv(os.path.join(AN, "health/daily_popweighted_pm25.csv"), parse_dates=["date"])
    d = d[(d.group == "Canada") & d.date.dt.month.between(5, 9)].copy()
    d["year"] = d.date.dt.year
    d["wk"] = (d.date.dt.dayofyear - pd.to_datetime(d.year.astype(str) + "-05-01").dt.dayofyear) // 7
    wk = d.groupby(["year", "wk"]).popw_pm25.max().unstack()
    years = [2023, 2024, 2025, 2026]
    nw = 22
    left, gap = 74, 5
    cw = (W - left - gap * (nw - 1)) / nw
    ch = 64
    H = len(years) * (ch + 12) + 80
    el = _svg(W, H)
    worst = None
    for r, y in enumerate(years):
        top = r * (ch + 12)
        el.append(_lab(0, top + ch / 2 + 9, str(y), 26, TEXT, "start"))
        for k in range(nw):
            v = wk.loc[y].get(k) if y in wk.index else None
            ok = v is not None and v == v
            band = 0 if not ok or v <= 27 else (1 if v <= 60 else 2)
            col = ["#3a4250", "#e9a05c", "#c0392b"][band]
            el.append(f'<rect x="{left + k * (cw + gap):.1f}" y="{top}" width="{cw:.1f}" height="{ch}" rx="4" fill="{col}"/>')
            if ok and (worst is None or v > worst[0]):
                worst = (v, y, left + k * (cw + gap), top)
    for m, k in [("May", 0), ("Jun", 4.4), ("Jul", 8.7), ("Aug", 13.1), ("Sep", 17.6)]:
        el.append(f'<text x="{left + k * (cw + gap):.1f}" y="{len(years) * (ch + 12) + 8}" font-size="21" fill="{MUTED}">{m}</text>')
    ly = len(years) * (ch + 12) + 56
    for i, (lab, col) in enumerate([("Mostly clean air", "#3a4250"), ("Unhealthy smoke", "#e9a05c"), ("Very unhealthy smoke", "#c0392b")]):
        x0 = left + i * 270
        el.append(f'<rect x="{x0}" y="{ly - 18}" width="22" height="22" rx="4" fill="{col}" stroke="#6b7586"/>')
        el.append(f'<text x="{x0 + 30}" y="{ly}" font-size="21" fill="{MUTED}">{lab}</text>')
    el.append("</svg>")
    return "".join(el), worst


def smoke_day_map(day="2026-07-16", W=928):
    """Air-monitoring stations on one day, coloured by daily fine particles (PM2.5)."""
    m = CanMap(W)
    st = pd.read_csv(os.path.join(AN, "..", "data/smoke-cost/station_daily_pm25_2018_2026.csv"),
                     usecols=["naps_id", "date", "pm25", "Latitude", "Longitude"], dtype={"naps_id": str})
    st = st[st.date == day].dropna(subset=["Latitude", "Longitude", "pm25"])
    y0 = m.xy(-96, 61.5)[1]
    el = _svg(W, m.H - 40, y0)
    el.append(f'<path d="{m.base_path()}" fill="{LAND}" stroke="{EDGE}" stroke-width="1"/>')
    for _, r in st.sort_values("pm25").iterrows():
        x, y = m.xy(r.Longitude, r.Latitude)
        v = r.pm25
        col = "#5b6575" if v <= 27 else ("#e9a05c" if v <= 60 else ("#e0533a" if v <= 100 else "#8e1b2c"))
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{7 if v <= 27 else 10}" fill="{col}" stroke="#10151c" stroke-width="1.2"/>')
    ly = y0 + 22
    for i, (lab, col) in enumerate([("Clean", "#5b6575"), ("Unhealthy", "#e9a05c"), ("Very unhealthy", "#e0533a"), ("Hazardous", "#8e1b2c")]):
        x0 = 10 + i * 190
        el.append(f'<circle cx="{x0 + 10}" cy="{ly - 7}" r="9" fill="{col}"/>')
        el.append(f'<text x="{x0 + 26}" y="{ly}" font-size="20" fill="{MUTED}">{lab}</text>')
    el.append("</svg>")
    return "".join(el), len(st), int((st.pm25 > 100).sum())


def smoke_season_map(year=2023, W=928):
    """Air monitors coloured by the number of unhealthy smoke days (daily PM2.5 above 27), May to September."""
    m = CanMap(W)
    st = pd.read_csv(os.path.join(AN, "..", "data/smoke-cost/station_daily_pm25_2018_2026.csv"),
                     usecols=["naps_id", "date", "pm25", "Latitude", "Longitude"], dtype={"naps_id": str})
    st = st[(st.date >= f"{year}-05-01") & (st.date <= f"{year}-09-30")].dropna(subset=["Latitude", "Longitude", "pm25"])
    g = st.groupby("naps_id").agg(lat=("Latitude", "first"), lon=("Longitude", "first"), n=("pm25", "size"),
                                  days=("pm25", lambda s: int((s > 27).sum())))
    g = g[g.n >= 100]
    y0 = m.xy(-96, 61.5)[1]
    el = _svg(W, m.H, y0)
    el.append(f'<path d="{m.base_path()}" fill="{LAND}" stroke="{EDGE}" stroke-width="1"/>')
    bands = [(0, "#5b6575", "None"), (1, "#e9a05c", "1 to 9 days"), (10, "#e0533a", "10 to 19 days"), (20, "#8e1b2c", "20 days or more")]
    for _, r in g.sort_values("days").iterrows():
        x, y = m.xy(r.lon, r.lat)
        col = [c for lo, c, _ in bands if r.days >= lo][-1]
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{7 if r.days == 0 else 9}" fill="{col}" stroke="#10151c" stroke-width="1.2"/>')
    el.append("</svg>")
    legend = "".join(f'<span><i style="background:{c};border-radius:50%"></i>{lab}</span>' for _, c, lab in bands)
    return "".join(el), f'<div class="legend">{legend}</div>', len(g)


POLICY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "policy")


def policy_numbers():
    """Values for the government slide, read from analysis/policy."""
    m = pd.read_csv(os.path.join(POLICY, "measures.csv"))

    def row(pat):
        r = m[m["name"].str.contains(pat, regex=False)]
        assert len(r) == 1, pat
        return r.iloc[0]

    progs = [("Firefighting equipment and training", row("FMWCC contributions actually paid")),
             ("FireSmart and fire research", row("Wildfire Resilient Futures Initiative")),
             ("Four leased firefighting aircraft", row("National Aerial Wildfire Capacity")),
             ("Fire-watching satellite", row("WildFireSat"))]
    jars = [(lab, r["amount_announced_cad"] / 1e6, (0 if pd.isna(r["amount_spent_cad"]) else r["amount_spent_cad"]) / 1e6)
            for lab, r in progs]
    prov = {k: row(p) for k, p in [("BC", "Fire Management vote vs actual"), ("Alberta", "Wildfire base budget vs contingency"),
                                    ("Saskatchewan", "SPSA appropriation")]}
    ratios = {k: r["amount_spent_cad"] / r["amount_announced_cad"] for k, r in prov.items()}
    zone = row("Response-zone")
    r = pd.read_csv(os.path.join(POLICY, "research_underway.csv"))
    g = r[r["status_2026_10_22"].str.startswith("agreement active")]
    return dict(jars=jars, ratios=ratios, zone_status=zone["stage"], n_grants=len(g), grants_m=g["agreement_value"].sum() / 1e6)


NOTES = {"Fire-watching satellite": ("Launch", "2029"), "Four leased firefighting aircraft": ("$0 paid,", "starts 2026")}


def jars(items, W=928, H=300, gap=26):
    """One jar per program: width by money set aside, fill by money paid out."""
    tot = sum(a for _, a, _ in items)
    avail = W - gap * (len(items) - 1)
    top, jh = 46, 160
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">']
    x = 0
    for lab, a, p in items:
        w = avail * a / tot
        cx = x + w / 2
        el.append(f'<text x="{cx:.1f}" y="{top - 14}" font-size="27" font-weight="800" fill="{TEXT}" text-anchor="middle">${a:.0f}M</text>')
        el.append(f'<rect x="{x:.1f}" y="{top}" width="{w:.1f}" height="{jh}" rx="14" fill="rgba(255,255,255,0.06)" stroke="{MUTED}" stroke-width="3"/>')
        fh = jh * p / a
        if fh > 0:
            el.append(f'<rect x="{x + 3:.1f}" y="{top + jh - fh:.1f}" width="{w - 6:.1f}" height="{max(fh - 3, 3):.1f}" rx="10" fill="{FIRE}"/>')
        if lab in NOTES:
            for k, ln in enumerate(NOTES[lab]):
                el.append(f'<text x="{cx:.1f}" y="{top + jh / 2 - 4 + k * 28:.1f}" font-size="23" font-weight="700" fill="{TEXT}" text-anchor="middle">{ln}</text>')
        else:
            py = top + jh - fh - 12
            el.append(f'<text x="{cx:.1f}" y="{py:.1f}" font-size="24" font-weight="700" fill="{TEXT}" text-anchor="middle">${p:.0f}M paid</text>')
        words, lines, cur = lab.split(), [], ""
        for wd in words:
            if len(cur + " " + wd) * 12.5 > w + 30 and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        for k, ln in enumerate(lines):
            el.append(f'<text x="{cx:.1f}" y="{top + jh + 32 + k * 27}" font-size="22" fill="{TEXT}" text-anchor="middle">{ln}</text>')
        x += w + gap
    el.append("</svg>")
    return "".join(el)


LABEL_AT = {"BC": (-124.5, 54.5), "AB": (-114.8, 55.0), "SK": (-105.8, 55.0), "MB": (-97.6, 55.5), "ON": (-86.0, 50.5),
            "QC": (-72.5, 52.0), "NL": (-61.5, 53.6), "NB": (-66.4, 46.6), "NS": (-63.0, 45.0), "PE": (-63.2, 46.4),
            "YT": (-135.5, 63.0), "NT": (-118.0, 64.0), "NU": (-95.0, 65.5)}
BANDS = [(0, 25, "#ff6b4f"), (25, 50, "#f2a03d"), (50, 75, "#e8d27a"), (75, 1e9, "#8fc79a")]


def band_col(v):
    if v is None:
        return "#3a414c"
    for lo, hi, c in BANDS:
        if lo <= v < hi:
            return c


def cover_col(v):
    """Single-hue scale: deep red at 0% budget cover, pale at 100%."""
    if v is None:
        return "#3a414c"
    f = max(0.0, min(1.0, v / 100))
    c0, c1 = (214, 48, 31), (255, 222, 200)
    return "#%02x%02x%02x" % tuple(round(c0[i] + (c1[i] - c0[i]) * f) for i in range(3))


LABEL_NUDGE = {"NS": (-30, 75, "middle")}


def prov_map(vals, H=440, crop=(-139, 69.9), no_line=()):
    """Provinces shaded by budget cover (vals: prov -> pct). Provinces in no_line are hatched."""
    import json as _j
    from canmap import CanMap, BASE, _decode, _ring
    m = CanMap(W=928)
    topo = _j.load(open(BASE))
    arcs = _decode(topo)
    el = ['<defs><pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
          '<rect width="10" height="10" fill="#3a414c"/><line x1="0" y1="0" x2="0" y2="10" stroke="#6b7480" stroke-width="4"/></pattern></defs>']
    for g in topo["objects"]["provs"]["geometries"]:
        p = g["properties"]["p"]
        polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
        d = []
        for poly in polys:
            for r in poly:
                pts = _ring(arcs, r)
                if len(pts) >= 3:
                    d.append("M" + "L".join(f"{(x - m.minx) * m.sc:.1f},{(m.maxy - y) * m.sc:.1f}" for x, y in pts) + "Z")
        fill = "url(#hatch)" if p in no_line else cover_col(vals.get(p))
        el.append(f'<path d="{"".join(d)}" fill="{fill}" stroke="#0c1016" stroke-width="2"/>')
    for p, (lon, lat) in LABEL_AT.items():
        if p not in vals and p not in no_line:
            continue
        x, y = m.xy(lon, lat)
        dx, dy, anc = LABEL_NUDGE.get(p, (0, 0, "middle"))
        x, y = x + dx, y + dy
        if p in no_line:
            el.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="30" font-weight="800" fill="#fff" text-anchor="{anc}" paint-order="stroke" stroke="#11151b" stroke-width="6">{p}</text>'
                      f'<text x="{x:.0f}" y="{y + 30:.0f}" font-size="22" font-weight="700" fill="#fff" text-anchor="{anc}" paint-order="stroke" stroke="#11151b" stroke-width="6">no fire line</text>')
            continue
        v = vals[p]
        ink = "#fff" if v < 45 else "#11151b"
        halo = "" if (dx, dy) == (0, 0) else ' paint-order="stroke" stroke="#11151b" stroke-width="6"'
        if halo:
            ink = "#fff"
        el.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="30" font-weight="800" fill="{ink}" text-anchor="{anc}"{halo}>{p}</text>'
                  f'<text x="{x:.0f}" y="{y + 34:.0f}" font-size="32" font-weight="800" fill="{ink}" text-anchor="{anc}"{halo}>{v:.0f}%</text>')
    _, ytop = m.xy(*crop)
    Hv = m.H - ytop
    W = 928 * H / Hv
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H}" viewBox="0 {ytop:.0f} 928 {Hv:.0f}" '
            f'font-family="{FONT}" style="display:block;margin:0 auto">' + "".join(el) + "</svg>")


def cover_legend(W=520):
    stops = "".join(f'<stop offset="{k / 10:.1f}" stop-color="{cover_col(k * 10)}"/>' for k in range(11))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="56" viewBox="0 0 {W} 56" font-family="{FONT}">'
            f'<defs><linearGradient id="cg">{stops}</linearGradient></defs>'
            f'<rect x="0" y="4" width="{W}" height="18" rx="9" fill="url(#cg)"/>'
            f'<text x="0" y="50" font-size="21" fill="{MUTED}">0% of usual cost</text>'
            f'<text x="{W}" y="50" font-size="21" fill="{MUTED}" text-anchor="end">100%</text></svg>')


READY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "readiness")
STATUS_COL = {"red": "#ff6b4f", "amber": "#f2a03d", "green": "#7cc48a", "grey": "#5b6575", "none": None}


def scorecard_html():
    """Province readiness table as HTML; status colours from scorecard.csv."""
    sc = pd.read_csv(os.path.join(READY, "scorecard.csv"))

    def cell(txt, st, big=False):
        c = STATUS_COL.get(st)
        bar = f'<i style="background:{c}"></i>' if c else '<i style="background:transparent"></i>'
        return f'<td class="{"b" if big else ""}">{bar}<span>{txt}</span></td>'

    rows = []
    for _, r in sc.iterrows():
        b = "Not listed" if pd.isna(r["budget_pct"]) else f'{r["budget_pct"]:.0f}%'
        rows.append(f'<tr><th>{r["prov"]}</th>{cell(b, r["budget_status"], not pd.isna(r["budget_pct"]))}{cell(r["bombers"], r["bombers_status"])}'
                    f'{cell(r["crews_in"], r["crews_status"])}{cell(r["review"], r["review_status"])}</tr>')
    head = ('<tr><th></th><td class="h">Budget covers</td><td class="h">Water bombers</td>'
            '<td class="h">Crews brought in</td><td class="h">Review fixes</td></tr>')
    return f'<table class="score">{head}{"".join(rows)}</table>', sc


def timeline(W=928, row=74):
    """Vertical timeline: when each new piece of capacity arrives (analysis/readiness/timeline.csv)."""
    t = pd.read_csv(os.path.join(READY, "timeline.csv"))
    H = row * len(t) + 10
    xl = 34
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
          f'<line x1="{xl}" y1="{row / 2}" x2="{xl}" y2="{H - row / 2}" stroke="{MUTED}" stroke-width="3"/>']
    for k, r in t.iterrows():
        y = row / 2 + k * row
        el.append(f'<circle cx="{xl}" cy="{y:.0f}" r="11" fill="{FIRE}" stroke="#11151b" stroke-width="3"/>'
                  f'<text x="{xl + 32}" y="{y + 10:.0f}" font-size="30" font-weight="800" fill="{FIRE}">{r["when"]}</text>'
                  f'<text x="{xl + 262}" y="{y - 2:.0f}" font-size="27" font-weight="700" fill="{TEXT}">{r["item"]}</text>'
                  f'<text x="{xl + 262}" y="{y + 28:.0f}" font-size="22" fill="{MUTED}">{r["who"]}</text>')
    el.append("</svg>")
    return "".join(el)
