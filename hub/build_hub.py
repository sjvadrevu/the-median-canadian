"""Build the hub page of The Median Canadian (index.html at the repository root).

Each post appears with its cover slide, the same first image as the Instagram post. Every finding and
number listed for a post is read from that week's own files, so the hub cannot drift from the week's
site, and the build stops if a published finding no longer holds for the data.

Usage, from the repository root:
  python3 hub/build_hub.py      writes index.html

Week 1 lives in its own repository until it moves here: clone https://github.com/sjvadrevu/ab-referendum-live
into ab-referendum-live/ at the repository root first (the folder is ignored by git until the move).
Needs Python 3 and Pillow.
"""
import html, json, math, re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://sjvadrevu.github.io/the-median-canadian/"
AB, WF = ROOT / "ab-referendum-live", ROOT / "canada-wildfires-2026"
# where each week's site lives: (link from the hub, absolute address for sharing)
WEEK_URL = {
    1: ("https://sjvadrevu.github.io/ab-referendum-live/", "https://sjvadrevu.github.io/ab-referendum-live/"),
    2: ("canada-wildfires-2026/", SITE + "canada-wildfires-2026/"),
}
E = html.escape
NUMW = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
HERO_N = 3  # the carousel shows the newest three posts

def nf(v, d=0):
    """Number with thousands separators, rounded half up."""
    q = Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return f"{q:,.{d}f}"


# =====================================================================================
# Week 1: Alberta's separation vote (same rules as the week 1 site and slides)
# =====================================================================================
assert (AB / "data.json").exists(), "clone https://github.com/sjvadrevu/ab-referendum-live into ab-referendum-live/ first"
d = json.load(open(AB / "data.json"))
M = json.load(open(AB / "map.json"))
C = json.load(open(AB / "context.json"))
site1 = (AB / "index.html").read_text()
MINV = int(re.search(r"const MINV\s*=\s*(\d+)", site1).group(1))
Q = {q["n"]: (q["yes"], q["no"]) for q in d["questions"]}


def pair(v):
    t = v[0] + v[1]
    return v[0] / t * 100, v[1] / t * 100


rem, sep = pair(Q[10])                     # Question 10: first answer is Remain
ratio = round(max(rem, sep) / min(rem, sep))
rp = d["summary"]["rep"] / d["summary"]["tot"] * 100
rows = []
for w, x in d["wards"].items():
    v = x["v"][9]
    t = sum(v) if v else 0
    if t < MINV:
        continue
    c = C[w]["p23"]
    rows.append(dict(w=w, n=M["names"][w], rem=v[0] / t * 100, ref=v[1] / t * 100,
                     ucp=c["ucp"], ndp=c["ndp"], win=c["win"], v=v))

# Checks: each published finding must still hold for the count in the repository.
sep_rows = sorted((r for r in rows if r["ref"] > r["rem"]), key=lambda r: -r["ref"])
assert len(sep_rows) == 2, f"'All but two ridings' no longer holds ({len(sep_rows)})"
ucp_rows = [r for r in rows if r["win"] == "UCP"]
gaps = [r["ucp"] - r["ref"] for r in ucp_rows]
assert min(gaps) > 0, "'In every UCP seat, fewer voted to separate' no longer holds"
TOSS = 3


def outcome(r):
    sh = {"sep": r["ref"], "ndp": r["ndp"], "mod": max(0, 100 - r["ref"] - r["ndp"])}
    o = sorted(sh.items(), key=lambda kv: -kv[1])
    return o[0][0], o[0][1] - o[1][1]


outs = [outcome(r) for r in rows]
n_toss = sum(1 for _, m in outs if m < TOSS)
n_sep = sum(1 for p, m in outs if m >= TOSS and p == "sep")
SEATS = len(M["ab"]["d"])
MAJ = SEATS // 2 + 1
assert n_sep + n_toss < MAJ, "seat forecast no longer costs a separatist UCP its majority"
yes = {n: pair(Q[n])[0] for n in range(1, 10)}
assert all(yes[n] > 50 for n in range(1, 6)), "immigration questions no longer all have majority support"
# Questions 1 to 9: same wording rule as the week 1 site, so the hub reads what the site reads.
lo1, hi1 = min(yes[n] for n in range(1, 6)), max(yes[n] for n in range(1, 6))
lo2, hi2 = min(yes[n] for n in range(6, 10)), max(yes[n] for n in range(6, 10))
q_head = ("Albertans want tighter immigration rules but are split on changing the constitution" if lo2 > 46 and hi2 < 54 else
          "Albertans want tighter immigration rules and constitutional change" if lo2 >= 54 else
          "Albertans want tighter immigration rules but reject constitutional change" if hi2 <= 46 else
          "Albertans want tighter immigration rules but are divided on the constitution")
q_line = (f"All five immigration and citizenship questions had more Yes than No votes, {nf(lo1)}% to {nf(hi1)}% Yes. "
          f"The four constitution questions drew {nf(lo2)}% to {nf(hi2)}% Yes.")
POLLS = [(n, int(a), int(b)) for n, a, b in
         re.findall(r'\{n:"([^"]+)", d:"[^"]*", s:\d+, a:(\d+), b:(\d+)', site1)]
assert len(POLLS) == 4
poll_avg = sum(a / (a + b) * 100 for _, a, b in POLLS) / len(POLLS)
assert rem - poll_avg >= 1, "polls no longer understated support for staying"
assert 22 <= sep <= 28, "'about a quarter of the vote' no longer holds"
ucp_sep = sum(r["v"][1] for r in ucp_rows) / sum(sum(r["v"]) for r in ucp_rows) * 100
assert ucp_sep < 50, "separation is no longer a minority in UCP seats"

w1_find = [
    dict(k="Question 10", h=f"Albertans rejected the separation process {NUMW[ratio]} to one",
         l=f"Remain {nf(rem, 1)}%, separation {nf(sep, 1)}%, with {nf(rp)}% of voting places counted.", a="#insights"),
    dict(k="Question 10 by riding", h="All but two ridings voted to remain in Canada",
         l=f"{sep_rows[0]['n']} ({nf(sep_rows[0]['ref'])}%) and {sep_rows[1]['n']} ({nf(sep_rows[1]['ref'])}%) voted to separate.",
         a="#explore"),
    dict(k="The UCP's 2023 seats", h="In every UCP seat, fewer people voted to separate than voted UCP in 2023",
         l=f"Out of every 100 voters in these seats, {nf(min(gaps))} to {nf(max(gaps))} fewer voted to separate than had voted UCP.",
         a="#patterns"),
    dict(k="Seat forecast", h="If the UCP decides to take up the separation cause, it will cost them the government",
         l=f"In a three-way race, a separatist UCP would hold {n_sep} of {SEATS} seats. A majority is {MAJ}.",
         a="#seatsPanel"),
    dict(k="Questions 1 to 9", h=q_head, l=q_line, a="#explore"),
    dict(k="Polls vs the count", h="Polls understated support for staying",
         l=f"The last four polls before the vote put Remain at {nf(poll_avg)}% among decided voters. The count has it at {nf(rem)}%.",
         a="#insights"),
    dict(k="The bottom line", h="Separation is a minority issue, including within UCP",
         l="A UCP that took up separation would be campaigning for the separation side, about a quarter of the vote.",
         a="#patterns"),
]

# =====================================================================================
# Week 2: Canada's wildfires (text and numbers exactly as the week 2 site renders them)
# =====================================================================================
CH = json.load(open(WF / "data/chapters.json"))
STORY = json.load(open(WF / "data/story.json"))
site2 = (WF / "index.html").read_text()
F = {  # the week 2 site's own number formats
    "int": lambda v: nf(v, 0), "d1": lambda v: nf(v, 1), "pct0": lambda v: nf(v, 0) + "%",
    "mil0": lambda v: nf(v / 1e6, 0) + " million", "mil1": lambda v: nf(v / 1e6, 1) + " million",
    "fl0": lambda v: nf(math.floor(v), 0), "deg1": lambda v: nf(v, 1) + " °C",
    "dbl": lambda v: "more than double" if v >= 2 else nf(v, 1) + " times", "b100": lambda v: nf(v / 1000, 2),
}


def resolve(path):
    obj, path = (CH, path[1:]) if path.startswith("@") else (STORY["claims"], path)
    assert "/" not in path, path
    for part in path.split("."):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def fill(fragment):
    fragment = re.sub(r"<sup\b.*?</sup>", "", fragment, flags=re.S)
    fragment = re.sub(r'<span data-n="([^"]+)" data-f="([^"]+)"></span>',
                      lambda m: F[m.group(2)](resolve(m.group(1))), fragment)
    assert "data-n" not in fragment, fragment
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


w2_find = []
for i in range(1, 9):
    m = re.search(r'id="c%d">.*?<span class="chK">(.*?)</span>\s*<h2 class="chH">(.*?)</h2>\s*<p class="reveal">(.*?)</p>' % i,
                  site2, re.S)
    assert m, f"chapter {i} not found on the week 2 site"
    w2_find.append(dict(k=fill(m.group(1)), h=fill(m.group(2)), l=fill(m.group(3)), a=f"#c{i}"))

# =====================================================================================
# Posts, newest first. Every week: its folder, one entry here and its cover slide in covers/.
# =====================================================================================
POSTS = [
    dict(n=2, folder="canada-wildfires-2026", title="Canada's wildfires", place="Canada", period="2023 to 2026",
         tags=["Nature", "Health", "Money"],
         alt="Week 2 cover: From the forest to our homes. Canada's wildfires, 2023 to 2026.", find=w2_find),
    dict(n=1, folder="ab-referendum-live", title="Alberta's separation vote", place="Alberta", period="October 19, 2026",
         tags=["Elections"],
         alt="Week 1 cover: Albertans rejected the separation process three to one.", find=w1_find),
]
# Every week's folder in the repository needs its card here and its cover slide in covers/.
week_dirs = sorted(x.name for x in ROOT.iterdir() if x.is_dir() and (x / "index.html").exists())
missing = [w for w in week_dirs if w not in {p["folder"] for p in POSTS}]
assert not missing, f"week folders without a hub card (add them to POSTS with their cover in covers/): {missing}"
assert [p["n"] for p in POSTS] == sorted((p["n"] for p in POSTS), reverse=True), "POSTS must be newest first"
for p in POSTS:
    p["href"], p["share"] = WEEK_URL[p["n"]]
    found = sorted((ROOT / "covers").glob(f"week-{p['n']:02d}-cover.*"))
    assert found, f"no cover slide for week {p['n']} in covers/"
    im = Image.open(found[0]).convert("RGB")
    assert abs(im.width / im.height - 0.8) < 0.01, f"week {p['n']} cover is not 4:5 ({im.size})"
    p["cover"] = "covers/" + found[0].name     # one file serves the slide and the list
    p["thumb"] = f'<img src="{p["cover"]}" alt="" width="240" height="300" decoding="async">'

# Wording checks the style guide asks for on every published word.
BANNED = [r"\u2014", r"\bnow\b", r"\btoday\b", r"\bcurrently\b", r"\bwon\b", r"\blost\b", r"\bcarried\b", r"\bbeat\b"]
for p in POSTS:
    for f in p["find"]:
        for b in BANNED:
            assert not re.search(b, " ".join(f.values()), re.I), (b, f)

# Search suggestions shown when a search finds nothing: each must find something.
SUGS = ["smoke", "UCP", "cost", "immigration"]
for s in SUGS:
    assert any(s.lower() in " ".join(f["k"] + " " + f["h"] + " " + f["l"] for f in p["find"]).lower() for p in POSTS), s

# =====================================================================================
# Page
# =====================================================================================
ICON = dict(
    arrow='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    search='<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    pause='<svg class="i-pause" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="4" width="5" height="16" rx="1.5"/><rect x="14" y="4" width="5" height="16" rx="1.5"/></svg>',
    play='<svg class="i-play" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15a1 1 0 0 0 1.5.86l12-7.5a1 1 0 0 0 0-1.72l-12-7.5A1 1 0 0 0 7 4.5z"/></svg>',
    left='<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
    right='<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>',
    close='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    share='<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 8l5-5 5 5"/><path d="M5 13v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5"/></svg>',
    chev='<svg class="chev" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>',
)

hero_posts = POSTS[:HERO_N]
slides = []
for i, p in enumerate(hero_posts):
    tops = "".join(f"<li>{E(f['h'])}</li>" for f in p["find"][:3])
    pri = ' fetchpriority="high"' if i == 0 else ""
    slides.append(f'''<a class="slide" href="{p["href"]}" role="group" aria-roledescription="slide" aria-label="{i + 1} of {len(hero_posts)}: Week {p["n"]}, {E(p["title"])}">
      <div class="cover"><img src="{p["cover"]}" alt="{E(p["alt"])}" width="1080" height="1350" decoding="async"{pri}></div>
      <div class="info">
        <span class="ik">Week {p["n"]} · {E(p["period"])}</span>
        <h2 class="it">{E(p["title"])}</h2>
        <ul class="ifind">{tops}</ul>
        <span class="cta">Explore<span class="cta-long">&nbsp;the story</span>{ICON["arrow"]}</span>
      </div>
    </a>''')
bars = "".join(f'<button class="bar" type="button" aria-label="Show week {p["n"]}"><i><b></b></i></button>' for p in hero_posts)

wm_light, wm_dark, icon = "assets/logo.png", "assets/logo-dark.png", "assets/logo-icon.png"
tags = sorted({t for p in POSTS for t in p["tags"]}, key=lambda t: (-sum(t in p["tags"] for p in POSTS), t))
n_find = sum(len(p["find"]) for p in POSTS)
data = dict(posts=[{k: p[k] for k in ("n", "title", "place", "period", "tags", "href", "share", "thumb", "find")} for p in POSTS],
            sugs=SUGS, icons={k: ICON[k] for k in ("arrow", "share", "chev")})

TEMPLATE = (ROOT / "hub" / "hub_template.html").read_text()
page = (TEMPLATE
        .replace("@@SITE_CSS@@", ":root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}img{max-width:100%}")
        .replace("@@ICON_FAV@@", icon).replace("@@WM_LIGHT@@", wm_light).replace("@@WM_DARK@@", wm_dark)
        .replace("@@SLIDES@@", "".join(slides)).replace("@@BARS@@", bars)
        .replace("@@CHIPS@@", "".join(f'<button class="chip" type="button" data-t="{E(t)}" aria-pressed="false">{E(t)}</button>' for t in tags))
        .replace("@@COUNT@@", f"{len(POSTS)} posts · {n_find} findings")
        .replace("@@DATA@@", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
        .replace("@@ICON_SEARCH@@", ICON["search"]).replace("@@ICON_PAUSE@@", ICON["pause"]).replace("@@ICON_PLAY@@", ICON["play"])
        .replace("@@ICON_LEFT@@", ICON["left"]).replace("@@ICON_RIGHT@@", ICON["right"]).replace("@@ICON_CLOSE@@", ICON["close"]))
assert "@@" not in page, re.findall(r"@@\w+@@", page)
assert "\u2014" not in page, "em dash in page"
head, body = page.split("<!--BODY-->")
desc = "A curious Canadian explaining Canada through numbers, every week."
meta = (f'<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f'<meta name="color-scheme" content="light dark">\n<link rel="canonical" href="{SITE}">\n'
        f'<meta property="og:type" content="website">\n<meta property="og:site_name" content="The Median Canadian">\n'
        f'<meta property="og:title" content="The Median Canadian">\n<meta property="og:description" content="{desc}">\n'
        f'<meta property="og:url" content="{SITE}">\n<meta property="og:image" content="{SITE}assets/logo-icon.png">\n'
        f'<meta name="twitter:card" content="summary">\n<link rel="apple-touch-icon" href="assets/logo-icon.png">\n')
out = ROOT / "index.html"
text = f'<!doctype html>\n<html lang="en-CA">\n<head>\n{meta}{head.strip()}\n</head>\n<body>\n{body.strip()}\n</body>\n</html>\n'
out.write_text(text)
print(f"wrote {out} {len(text) / 1024:.0f} KB | week 1 remain {nf(rem, 1)} ({nf(rp)}% counted) | "
      f"questions: {q_head} | week 2 findings: " + " / ".join(f["h"] for f in w2_find))
