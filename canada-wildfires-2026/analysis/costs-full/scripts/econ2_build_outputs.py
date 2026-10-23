"""econ2_build_outputs.py: assembles costs-full/econ2_costs.csv (same columns as econ_costs.csv) from
  - the econ2 satellite counts (work/econ2_sat/apply_<job>.csv from econ2_sat_04_apply.py),
  - work/econ2_gdp_sawmills.csv (econ2_gdp_sawmills.py),
  - hand-entered official items below, each with its source document (read 2026-10-22),
  - the bill's own building values (analysis/property/destroyed_value_estimates.csv, destroyed_value_official.csv; read only).
Rules (as econ_): official count first; value = count x 2021 Census average value of owner-occupied dwellings of the DAs of
the flagged footprints (median for the low case), the same basis as the bill's buildings line; only buildings above what
the bill already counts are added. Satellite-only events: central = flagged footprints each at its own DA average value
(the bill's own rule); low and high apply the count ratios seen on the check events with official counts (flagged/official
0.89 to 1.51, Barrington excluded, analysis/property/results.md): low = flagged / 1.51 at the median value, high = flagged /
0.89 at the average value (flagged / 0.31, the Barrington ratio, for long fires imaged after their last hotspot).
Counts that officials gave only to reporters (no official document found) are listed in separate rows as top-ups above the
satellite count, with additive 'no' and low 0: the sourcing rules allow news only as a pointer to an official document.
usage: python3 -I econ2_build_outputs.py -> econ2_costs.csv"""
import csv, os
import numpy as np, pandas as pd

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); AN = os.path.dirname(B)
SAT = os.path.join(B, "work", "econ2_sat"); P = os.path.join(AN, "property")
ACC = "2026-10-22"
COLS = ["item", "sector", "jurisdiction", "period", "amount_low_cad", "amount_central_cad", "amount_high_cad", "dollars_basis", "basis", "method",
        "source_name", "url", "accessed", "overlaps_with", "additive", "notes"]
rows = []
CENSUS = "2021 census values (same basis as the bill buildings line)"
RLO, RHI = 1.51, 0.89   # count ratio flagged/official on check events (Barrington excluded)


def add(**k):
    r = {c: k.get(c, "") for c in COLS}
    for c in ("amount_low_cad", "amount_central_cad", "amount_high_cad"):
        if r[c] != "" and r[c] is not None and not (isinstance(r[c], float) and np.isnan(r[c])):
            r[c] = int(round(float(r[c])))
    # in remote DAs the census median can exceed the average (CD fallback for one of them): keep low <= central <= high
    if all(isinstance(r[c], int) for c in ("amount_low_cad", "amount_central_cad", "amount_high_cad")):
        r["amount_low_cad"] = min(r["amount_low_cad"], r["amount_central_cad"])
        r["amount_high_cad"] = max(r["amount_high_cad"], r["amount_central_cad"])
    r["accessed"] = r["accessed"] or ACC
    rows.append(r)


import geopandas as gpd
# footprints within 500 m of a bill AOI of the same year are left to the bill (Lac du Bonnet and Denare Beach 2025)
BILL_AOI = {2025: [os.path.join(P, "work", "aoi_lacdubonnet2025.gpkg"), os.path.join(P, "work", "aoi_denare2025.gpkg")]}
_cache = {}


def load(job):
    if job in _cache:
        return _cache[job]
    f = os.path.join(SAT, f"apply_{job}.csv")
    if not os.path.exists(f):
        _cache[job] = None; return None
    d = pd.read_csv(f, low_memory=False)
    aoi = gpd.read_file(os.path.join(SAT, f"aoi_{job}.gpkg"))
    d["aoi"] = d.aoi.astype(str)
    d = d.merge(aoi[["fire_id", "prov", "year"]].rename(columns={"fire_id": "aoi"}), on="aoi", how="left")
    d["near_bill_aoi"] = False
    yr = int(aoi.year.iloc[0])
    for fa in BILL_AOI.get(yr, []):
        ga = gpd.read_file(fa).to_crs(3978)
        pts = gpd.GeoSeries(gpd.points_from_xy(d.x, d.y), crs=3978)
        d["near_bill_aoi"] |= pts.distance(ga.union_all()).values <= 500
    _cache[job] = d
    return d


def fmt(vc):
    """Counts as plain text, e.g. 'rural 19, St. John's 11'."""
    return ", ".join(f"{k} {v}" for k, v in vc.items())


def sat(job, sel=None):
    """Flagged likely-destroyed footprints within 500 m, not in the bill, for a job (optionally filtered)."""
    d = load(job)
    if d is None:
        return None
    d = d[d.likely_destroyed & (d.dist <= 500) & d.qa_pass]
    d = d.assign(in_bill=d.in_bill | d.near_bill_aoi)
    if sel is not None:
        d = d[sel(d)]
    allf = d; new = d[~d.in_bill]
    return dict(flagged=len(allf), new=len(new), new_avg_sum=float(new.avg_value.sum()), new_med_sum=float(new.median_value.sum()),
                mean_avg=float(allf.avg_value.mean()) if len(allf) else np.nan, mean_med=float(allf.median_value.mean()) if len(allf) else np.nan,
                share_DA=float((allf.value_src == "DA").mean()) if len(allf) else np.nan, places=fmt(new.place.value_counts().head(8)),
                fires=fmt(new.aoi.value_counts().head(8)))


pv = pd.read_csv(os.path.join(P, "destroyed_value_estimates.csv")).set_index("event")
po = pd.read_csv(os.path.join(P, "destroyed_value_official.csv")).set_index("event")
SATM = ("Satellite: Microsoft footprints within 500 m of the fire polygon flagged by the Jasper-calibrated Sentinel-2 rule "
        "(analysis/property method, run by scripts/econ2_sat_01 to 04), after the quality screen (unstable-offset clusters, fire polygons under 10 ha "
        "and polygons failing the 500-1000 m false-positive check dropped)")

# ---------------- GAP 1: buildings ----------------
# Two kinds of rows. Countable rows (additive yes): counts from official documents or from the satellite method, as the
# sourcing rules ask (official records first; news only as a pointer to an official document). News-reported rows
# (additive no): counts that officials gave only to reporters (no official document found), listed as top-ups above the
# satellite count so they can be checked or accepted; their low is 0 and they are left out of the totals.
SAT_URL = ("https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/NBAC_1972to2025_20260513_shp.zip ; https://earth-search.aws.element84.com/v1/search ; "
           "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv ; "
           "https://api.statcan.gc.ca/census-recensement/profile/sdmx/rest/data/STC_CP,DF_DA,1.3/A5..1.1474+1475.1")
SAT_SRC = ("satellite count (this round): NRCan National Burned Area Composite polygons, Copernicus Sentinel-2 L2A scenes (Earth Search), "
           "Microsoft building footprints, Statistics Canada 2021 Census DA dwelling values")
BCWS_URL = ("https://openmaps.gov.bc.ca/geo/pub/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_CURRENT_FIRE_POLYS_SP"
            "&outputFormat=json&srsName=EPSG:4326")
NEWS_ADD = "no (count reported only in news; add only if officials' statements in news are accepted)"
NEWS_NOTE = ("An official gave this count to reporters; no official document with it was found, so under the sourcing rules (news only as a "
             "pointer) it is listed but not added, and its low is 0.")


def news_overlap(a_extra, b_high, v):
    """Text for a news-reported row: how much of its high case is already inside the satellite row's allowance for missed buildings."""
    o = max(0.0, min(a_extra, b_high))
    if o < 0.5:
        return "no overlap with the satellite row's high case"
    return (f"in the high case it overlaps the satellite row's allowance for missed buildings (about {o:.0f} buildings, ${o * v / 1e6:.1f}M): "
            "if both rows are added, take that off the high")


# Bradley Creek BC 2026 (OKIB IR 1)
b26 = pv.loc["2026 outline 36076592"]; nb, va, vm = int(b26.flagged_500m), b26.proxy_value_avg_cad / b26.flagged_500m, b26.proxy_value_median_cad / b26.flagged_500m
s = sat("bc2026", lambda d: d.aoi == "K41351")
sat_bc = s["flagged"]
up_c, up_h = max(0, sat_bc - nb), max(0, sat_bc / RHI - nb)
add(item="Buildings above the bill count: Bradley Creek wildfire BC 2026 (Okanagan Indian Band IR 1), satellite re-count on the official perimeter", sector="property",
    jurisdiction="BC (Okanagan Indian Band)", period="2026", amount_low_cad=up_c * vm, amount_central_cad=up_c * va, amount_high_cad=up_h * va,
    dollars_basis=CENSUS, basis="computed (satellite) on the official BC Wildfire Service perimeter",
    method=(f"{SATM}. Re-count with BC Wildfire Service perimeter K41351 instead of the CWFIS M3 outline the bill used: {sat_bc} flagged within 500 m "
            f"({s['new']} not among the bill's flags), {up_c} above the bill's {nb}. Central at the mean DA average value of the bill's flagged footprints there "
            f"({va:,.0f}; CD fallback, reserve DA values suppressed); low at the median value ({vm:,.0f}); high = {sat_bc} / 0.89 - {nb} buildings."),
    source_name="BC Wildfire Service fire perimeter K41351 (BC Data Catalogue); " + SAT_SRC + "; analysis/property/destroyed_value_estimates.csv",
    url=BCWS_URL + " ; " + SAT_URL,
    overlaps_with=f"bill buildings line (adds only buildings above its {nb}); one of the two unnamed 2026 BC insured fire catastrophes (industry, not added)",
    additive="yes",
    notes=("No official structure total: the province referred questions to local governments and First Nations (CP, Sep 10, 2026), and OKIB's news posts "
           "to Oct 22, 2026 give no number. The chief's count is the next row. TELUS lost an 8 km pole line on Westside Road (OKIB post Aug 22, 2026; no cost)."))
bc_b = max(0, 230 - max(sat_bc, nb))
add(item="Buildings reported in news above the satellite count: Bradley Creek BC 2026 (Okanagan Indian Band chief: about 230 homes)", sector="property",
    jurisdiction="BC (Okanagan Indian Band)", period="2026", amount_low_cad=0, amount_central_cad=bc_b * va, amount_high_cad=bc_b * va,
    dollars_basis=CENSUS, basis="official's count reported in news x census value (no official document)",
    method=(f"(230 homes, the chief's count: 'more than 30' member homes and 'more than 200' on certificate-of-possession lands - {max(sat_bc, nb)} "
            f"in the satellite row and the bill) x {va:,.0f}, the value used in the satellite row."),
    source_name="Okanagan Indian Band Chief Dan Wilson, Aug 4 and Aug 6, 2026, reported by The Canadian Press (CTV) and APTN [NEWS REPORT]",
    url="https://www.ctvnews.ca/vancouver/bc-wildfires/article/devastation-chief-says-about-230-homes-destroyed-by-bc-wildfire/ ; https://www.aptnnews.ca/national-news/we-measure-it-in-memories-lost-bradley-creek-wildfire-leaves-okanagan-indian-band-community-facing-long-road-to-recovery/",
    overlaps_with="satellite row above (adds only buildings above it); " + news_overlap(up_h - up_c, bc_b, va),
    additive=NEWS_ADD,
    notes=NEWS_NOTE + " The gap is large: Microsoft footprints may miss manufactured homes on leased lots, and the rule's recall at Jasper was 0.83.")
# Pear Lake / Big Bar BC 2026
p26 = pv.loc["2026 outline 36077449"]; npl, pa, pm = int(p26.flagged_500m), p26.proxy_value_avg_cad / p26.flagged_500m, p26.proxy_value_median_cad / p26.flagged_500m
s = sat("bc2026", lambda d: d.aoi == "C40983")
sat_pl = s["flagged"]
pu_c, pu_h = max(0, sat_pl - npl), max(0, sat_pl / RHI - npl)
add(item="Buildings above the bill count: Pear Lake wildfire BC 2026 (TNRD Electoral Area E, Big Bar complex), satellite re-count on the official perimeter", sector="property",
    jurisdiction="BC (Thompson-Nicola Regional District)", period="2026", amount_low_cad=pu_c * pm, amount_central_cad=pu_c * pa, amount_high_cad=pu_h * pa,
    dollars_basis=CENSUS, basis="computed (satellite) on the official BC Wildfire Service perimeter",
    method=(f"{SATM}. Re-count with BC Wildfire Service perimeter C40983: {sat_pl} flagged within 500 m ({s['new']} not among the bill's flags) against the bill's {npl}, "
            f"so the central adds nothing; high = {sat_pl} / 0.89 - {npl} buildings at the mean DA average value of the bill's flagged footprints ({pa:,.0f})."),
    source_name="BC Wildfire Service fire perimeter C40983 (BC Data Catalogue); " + SAT_SRC,
    url=BCWS_URL + " ; " + SAT_URL,
    overlaps_with=f"bill buildings line (adds only buildings above its {npl}); one of the two unnamed 2026 BC insured fire catastrophes (industry, not added)",
    additive="yes", notes="The TNRD EOC notices to Oct 15, 2026 give no count; the TNRD spokesperson's count is the next row.")
pl_b = max(0, 120 - max(sat_pl, npl))
add(item="Buildings reported in news above the satellite count: Pear Lake BC 2026 (TNRD: about 120 properties with structure loss)", sector="property",
    jurisdiction="BC (Thompson-Nicola Regional District)", period="2026", amount_low_cad=0, amount_central_cad=pl_b * pa, amount_high_cad=pl_b * pa,
    dollars_basis=CENSUS, basis="official's count reported in news x census value (no official document)",
    method=(f"(120 properties with structure loss, TNRD count as of Aug 3, 2026, outbuildings included, Village of Clinton excluded - {max(sat_pl, npl)} in the "
            f"satellite row and the bill) x {pa:,.0f}. Properties are counted once although many lost several structures."),
    source_name="Thompson-Nicola Regional District spokesperson, Aug 5, 2026, reported by Castanet Kamloops and CFJC [NEWS REPORT]",
    url="https://www.castanetkamloops.net/news/Kamloops/627029/120-properties-mostly-residential-have-seen-structure-loss-due-to-Pear-Lake-wildfire ; https://cfjctoday.com/2026/08/05/recovery-is-going-to-be-different-for-everybody-at-least-120-tnrd-properties-suffer-structure-loss-in-pear-lake-fire/",
    overlaps_with="satellite row above (adds only buildings above it); " + news_overlap(pu_h - pu_c, pl_b, pa),
    additive=NEWS_ADD,
    notes=NEWS_NOTE + " TNRD said the count was expected to grow; the fire grew again after Aug 21, 2026. CP (Sep 10, 2026): the Big Bar complex 'destroyed about 120 structures outside Clinton'.")
# Bush Creek East 2023: Skwlax band structures (the bill's run already covers the whole fire, so there is no satellite row)
bo = po.loc["bushcreek2023"]; bf = int(pv.loc["bushcreek2023"].flagged_500m)
add(item="Buildings reported in news above the bill count: Bush Creek East BC 2023 (Skwlax te Secwepemculecw 85 and TNRD 9, with CSRD 176)",
    sector="property", jurisdiction="BC (CSRD, TNRD, Skwlax te Secwepemculecw)", period="2023",
    amount_low_cad=0, amount_central_cad=(270 - bf) * bo.local_avg_value, amount_high_cad=(270 - bf) * bo.local_avg_value,
    dollars_basis=CENSUS, basis="official counts, partly reported only in news, x census value",
    method=(f"(CSRD 176 + TNRD 9 + Skwlax 85 = 270 destroyed - {bf} flagged in the bill) x local average {bo.local_avg_value:,.0f}, the value basis of "
            f"property/destroyed_value_official.csv. Only the CSRD count has an official document, and it alone (176) is below the bill's {bf} flags for the whole fire."),
    source_name="Skwlax te Secwepemculecw communications coordinator citing the Canada Task Force 1 damage assessment, reported by CTV; TNRD count reported by Castanet, Sep 5, 2023 [NEWS REPORT]; CSRD Civic Alert Sep 5, 2023 (official: 176 lost, 50 partially damaged)",
    url="https://bc.ctvnews.ca/one-third-of-all-structures-on-b-c-first-nation-destroyed-by-bush-creek-east-wildfire-1.6536528 ; https://www.castanetkamloops.net/news/Salmon-Arm/445060/New-count-pegs-estimated-number-of-buildings-destroyed-by-Shuswap-blaze-at-270 ; https://www.csrd.bc.ca/CivicAlerts.aspx?AID=1724",
    overlaps_with=f"bill buildings line (adds only buildings above its {bf} flags, which already include some reserve buildings); Bush Creek insured row (industry, not added)",
    additive=NEWS_ADD, notes=NEWS_NOTE + " Skwlax: 85 destroyed, 13 partially damaged, 139 unscathed (one third of all structures on the First Nation's lands).")
# KFN 2023
s = sat("kfn2023", lambda d: d.place.astype(str).str.contains("HAY RIVER DENE"))
kv, km, kn = s["mean_avg"], s["mean_med"], s["new"]
add(item="Buildings not in the bill: Katl'odeeche First Nation NT 2023 (Hay River Dene Reserve 1), satellite count", sector="property",
    jurisdiction="NT (Katl'odeeche First Nation)", period="2023",
    amount_low_cad=kn / RLO * km, amount_central_cad=s["new_avg_sum"], amount_high_cad=kn / RHI * kv,
    dollars_basis=CENSUS, basis="computed (satellite)",
    method=(f"{SATM}: {kn} flagged within 500 m on the reserve (post window Jun 1 to Jul 31, 2023, after the May fire and before the August fire near Hay River). "
            "Central = each at its own DA average value; low = flagged / 1.51 at the median value; high = flagged / 0.89 (count ratios seen on the check events)."),
    source_name=SAT_SRC, url=SAT_URL,
    overlaps_with="none in the bill; econ_ Hay River and Enterprise rows cover the town and hamlet only (not the reserve); Hay River insured row (industry, not added)",
    additive="yes", notes=f"Reserve DA values from {s['share_DA']:.0%} DA (rest CD fallback). The chief's count is the next row.")
kb_c, kb_h = max(0, 19 - kn), max(0, 23 - kn)
add(item="Buildings reported in news above the satellite count: Katl'odeeche First Nation NT 2023 (chief: 18 family homes and the band office)", sector="property",
    jurisdiction="NT (Katl'odeeche First Nation)", period="2023", amount_low_cad=0, amount_central_cad=kb_c * kv, amount_high_cad=kb_h * kv,
    dollars_basis=CENSUS, basis="official's count reported in news x census value (no official document)",
    method=(f"(19 buildings: 18 family homes lost plus the band office, the chief's count - {kn} in the satellite row) x {kv:,.0f} (mean DA average value of the flagged "
            "footprints on the reserve). High adds 4 of the 5 damaged major buildings (smoke damage, may be condemned)."),
    source_name="Chief April Martel, reported by CBC North, May 2023 [NEWS REPORT]", url="https://amp.cbc.ca/news/canada/north/18-families-homes-lost-kfn-wildfire-1.6850420",
    overlaps_with="satellite row above (adds only buildings above it); " + news_overlap(kn / RHI - kn, kb_h, kv), additive=NEWS_ADD, notes=NEWS_NOTE)
# Kingston NL 2025 (NBAC 2025_684 also holds the May 2025 Small Point fire)
A = load("atl2025")
kin = A[(A.aoi == "2025_684") & (A.dist <= 0)]                     # footprints inside the burn: the local value sample
kfl = A[(A.aoi == "2025_684") & A.likely_destroyed & (A.dist <= 500)]
kgv, kgm = float(kin.avg_value.mean()), float(kin.median_value.mean())
koff = float(A[A.aoi == "2025_684"].dnbr_offset.median())
first = (f"The first run (fall 2025 window, job atl2025) is not used: drought-browned vegetation shifted the main cluster by +{koff:.0f} dNBR, beyond the "
         f"screen's +-100, and the rule flagged {len(kfl)} footprints ({len(kfl) / 203:.1f} times the official count).")
KS = load("kng2025")                                              # second run, summer windows (econ2_sat_05_kingston.py)
if KS is not None:
    kq = KS[KS.likely_destroyed & (KS.dist <= 500)]
    offs = sorted(KS.groupby(["cluster", KS.subcell.fillna(-1)]).dnbr_offset.first().round(0).astype(int).tolist())
    second = (f"A second run with summer windows (post Jun 15 to Aug 15, 2026; pre Jun 5 to Aug 25, 2024; scripts/econ2_sat_05_kingston.py) flags {len(kq)} "
              f"within 500 m ({int((KS.likely_destroyed & (KS.dist > 500) & (KS.dist <= 1000)).sum())} at 500 to 1,000 m), close to this count, but its scene "
              f"offsets ({', '.join(f'{o:+d}' for o in offs)} dNBR) also fail the screen and the two runs differ by a factor of {len(kfl) / max(1, len(kq)):.1f}, "
              "so no satellite count is used for Kingston (cross-check only).")
else:
    second = ""
kgn = 0                                                           # no usable satellite count
kg_c, kg_h = max(0, 203 - kgn), max(0, 248 - kgn)
add(item="Buildings reported in news: Kingston NL 2025 (premier: 203 structures destroyed; no usable satellite count)", sector="property", jurisdiction="NL", period="2025",
    amount_low_cad=0, amount_central_cad=kg_c * kgv, amount_high_cad=kg_h * kgv,
    dollars_basis=CENSUS, basis="official's count reported in news x census value (no official document)",
    method=(f"(203 structures, the premier's count of Aug 19, 2025: Kingston 12, Small Point-Broad Cove-Blackhead-Adam's Cove 33, Western Bay 86, Ochre Pit Cove 59, "
            f"Northern Bay 13; structures that lost power, may include sheds and commercial buildings) x {kgv:,.0f} (mean DA average value "
            f"of the {len(kin)} footprints inside the burn). High: 248 damaged or destroyed by the August fire and the May Small Point fire together (Canadian Press season review). "
            f"{first} {second}"),
    source_name="Premier of Newfoundland and Labrador, briefing of Aug 19, 2025, reported by The Weather Network and The Canadian Press [NEWS REPORT]; the gov.nl.ca releases of Aug 11 to Sep 5, 2025 give no count",
    url="https://www.theweathernetwork.com/en/news/weather/forecasts/kingston-fire-destroys-203-structures-says-n-l-premier ; https://www.pentictonherald.ca/spare_news/article_b925091e-2262-5b62-af55-6b6900e9ffab.html",
    overlaps_with=("econ_costs.csv row 'Kingston wildfire NL 2025: property losses with no official count (insured value used)' ($70M, industry): the same "
                   "buildings; if this row is accepted, drop that one. Kingston insured row (industry, not added)"),
    additive=NEWS_ADD, notes=NEWS_NOTE + " Insured (CatIQ, industry): over $70M.")
# Paddy's Pond (2025_685) excluded: the CP season review says no property damage
s2 = sat("atl2025", lambda d: (~d.aoi.isin(["2025_684", "2025_685"])) & (d.prov == "NL"))
if s2 and s2["flagged"]:  # Martin Lake area (2025_683), Holyrood area (2025_937), Grand Falls-Windsor area (2025_682) and others
    add(item="Buildings not in the bill: other Newfoundland 2025 fires (Trinity Bay area in July, Grand Falls-Windsor area and Holyrood area in August), satellite count", sector="property",
        jurisdiction="NL", period="2025", amount_low_cad=s2["new"] / RLO * s2["mean_med"], amount_central_cad=s2["new_avg_sum"],
        amount_high_cad=s2["new"] / RHI * s2["mean_avg"], dollars_basis=CENSUS, basis="computed (satellite)",
        method=f"{SATM}: {s2['new']} flagged (by NBAC fire: {s2['fires']}). Central = each at its own DA average value; low = flagged / 1.51 at the median value; high = flagged / 0.89 (count ratios seen on the check events).",
        source_name=SAT_SRC + "; no official counts", url=SAT_URL,
        overlaps_with="none in the bill", additive="yes",
        notes=(f"places (reserve, or nearest population centre within 30 km): {s2['places']}. Pointer only (CP season review): cabins lost at Martin Lake and "
               "Chance Harbour, no number; no property damage at Paddy's Pond (2025_685, excluded)."))
# Nova Scotia 2025
s = sat("atl2025", lambda d: d.aoi == "2025_680")
if s is not None:
    allfp = load("atl2025")
    ins = allfp[(allfp.aoi == "2025_680") & (allfp.dist <= 0)]
    lv = s["mean_avg"] if s["flagged"] else float(ins.avg_value.mean()); lm = s["mean_med"] if s["flagged"] else float(ins.median_value.mean())
    add(item="Buildings not in the bill: Long Lake wildfire NS 2025 (West Dalhousie, Annapolis County), provincial count", sector="property",
        jurisdiction="NS", period="2025", amount_low_cad=20 * lm, amount_central_cad=20 * lv, amount_high_cad=31 * lv,
        dollars_basis=CENSUS, basis="official count x census value",
        method=(f"20 homes destroyed (not all primary residences) x {lv:,.0f} (mean DA average value of {'flagged footprints' if s['flagged'] else 'footprints inside the fire'}); "
                f"high adds the 11 outbuildings lost or damaged on other properties. Satellite cross-check: {s['flagged']} flagged within 500 m "
                "(post window Jun 15 to Aug 15, 2026, the fire burned to Oct 7, 2025)."),
        source_name="Government of Nova Scotia news release, Twenty Homes Lost in Long Lake Wildfires, Aug 28, 2025",
        url="https://news.novascotia.ca/en/2025/08/28/twenty-homes-lost-long-lake-wildfires",
        overlaps_with="none in the bill", additive="yes", notes="505 civic addresses evacuated.")
    s3 = sat("atl2025", lambda d: (d.aoi != "2025_680") & (d.prov == "NS"))
    if s3 and s3["flagged"]:
        add(item="Buildings not in the bill: other Nova Scotia 2025 fires, satellite count", sector="property", jurisdiction="NS", period="2025",
            amount_low_cad=s3["new"] / RLO * s3["mean_med"], amount_central_cad=s3["new_avg_sum"], amount_high_cad=s3["new"] / RHI * s3["mean_avg"],
            dollars_basis=CENSUS, basis="computed (satellite)", method=f"{SATM}: {s3['new']} flagged (by NBAC fire: {s3['fires']}).",
            source_name=SAT_SRC + "; no official count found", url=SAT_URL, overlaps_with="none in the bill", additive="yes",
            notes=f"places (reserve, or nearest population centre within 30 km): {s3['places']}. Small NBAC polygons near towns can give false flags; check before use.")
# Manitoba 2025 outside the bill's Lac du Bonnet and Denare Beach footprints
s = sat("mb2025")
if s:
    nop = sat("mb2025", lambda d: d.aoi == "2025_439")             # the Nopiming / Bird River fire (50.9N 95.2W)
    n439 = nop["new"] if nop else 0
    add(item="Buildings not in the bill: Manitoba 2025 fires outside Lac du Bonnet (Leaf Rapids and Lynn Lake areas, Pinaymootang, Nopiming and others), satellite count",
        sector="property", jurisdiction="MB", period="2025",
        amount_low_cad=s["new"] / RLO * s["mean_med"], amount_central_cad=s["new_avg_sum"], amount_high_cad=s["new"] / 0.31 * s["mean_avg"],
        dollars_basis=CENSUS, basis="computed (satellite)",
        method=(f"{SATM}: {s['new']} flagged within 500 m of NBAC 2025 Manitoba polygons and not in the bill (Lac du Bonnet and Denare Beach areas removed); "
                f"by NBAC fire: {s['fires']}. Central = each at its own DA average value; low = flagged / 1.51 at the median value; high = flagged / 0.31 "
                "(the Barrington ratio: the window starts after a fire's last hotspot, so buildings burned in May are under-detected)."),
        source_name=SAT_SRC + "; Manitoba 2025 Wildfire Interim After Action Review (no building count)",
        url=SAT_URL + " ; https://manitoba.ca/asset_library/en/wildfire/wildfire-report-april-2026.pdf",
        overlaps_with="none in the bill (bill footprints and the Lac du Bonnet and Denare Beach areas removed); Flin Flon complex insured row (industry, not added)", additive="yes",
        notes=(f"places (reserve, or nearest population centre within 30 km): {s['places']}. Low DA values in Leaf Rapids and Lynn Lake (about $28k and $72k average) "
               "keep the value small. The RM of Lac du Bonnet reported 28 homes lost (the bill flags 50 there, no change). Provincial counts reported in news are the next row."))
    mb_c, mb_h = max(0, 21 - n439), max(0, 41 - n439)
    add(item="Buildings reported in news above the satellite count: Manitoba 2025, Nopiming Provincial Park (province: 21 cottages; about 20 structures at Beresford Lake)",
        sector="property", jurisdiction="MB", period="2025", amount_low_cad=0, amount_central_cad=mb_c * s["mean_avg"], amount_high_cad=mb_h * s["mean_avg"],
        dollars_basis=CENSUS, basis="official's count reported in news x census value (no official document)",
        method=(f"(21 cottages lost in Nopiming Provincial Park, provincial spokesperson - {n439} flagged by the satellite on that fire) x {s['mean_avg']:,.0f} "
                "(Manitoba flagged mean); high adds the about 20 structures damaged at Beresford Lake."),
        source_name="Manitoba provincial spokesperson (The Narwhal, 2026); Province of Manitoba update reported by CBC, May 22, 2025 [NEWS REPORT]",
        url="https://thenarwhal.ca/nopiming-wildfire-rebuild-report/ ; https://www.cbc.ca/lite/story/1.7540510",
        overlaps_with="satellite row above (adds only buildings above it); " + news_overlap(n439 / 0.31 - n439, mb_h, s["mean_avg"]),
        additive=NEWS_ADD, notes=NEWS_NOTE)
# Alberta 2023
s = sat("ab2023")
if s:
    f = load("ab2023")
    f = f[f.likely_destroyed & (f.dist <= 500) & f.qa_pass & ~f.in_bill]
    isfox = f.place.astype(str).str.contains("FOX LAKE 162")
    isstu = f.place.astype(str).str.contains("STURGEON LAKE 154")
    isep = (f.aoi == "2023_364") & f.lat.between(55.1, 55.5) & f.lon.between(-116.7, -116.0)   # East Prairie Metis Settlement, south of High Prairie
    fox, stu, ep = int(isfox.sum()), int(isstu.sum()), int(isep.sum())
    mv, mm, n = float(f.avg_value.mean()), float(f.median_value.mean()), len(f)
    add(item="Buildings not in the bill: Alberta 2023 fires (Peace country, Edson area, Grande Prairie area, East Prairie, Fox Lake, Sturgeon Lake and others), satellite count",
        sector="property", jurisdiction="AB", period="2023",
        amount_low_cad=n / RLO * mm, amount_central_cad=float(f.avg_value.sum()), amount_high_cad=n / 0.31 * mv,
        dollars_basis=CENSUS, basis="computed (satellite)",
        method=(f"{SATM}: {n} flagged within 500 m of NBAC 2023 Alberta polygons (by NBAC fire: {s['fires']}). Central = each at its own DA average value; "
                "low = flagged / 1.51 at the median value; high = flagged / 0.31 (the Barrington ratio): the window starts after a fire's last hotspot, so buildings "
                f"burned early in long spring fires are missed; at Fox Lake, Sturgeon Lake and East Prairie the satellite finds {fox + stu + ep} against 158 reported."),
        source_name=SAT_SRC + "; Yellowhead County update May 23, 2023 (homes lost, no count)",
        url=SAT_URL + " ; https://yhcounty.ca/county-office/news/a-month-of-fires-and-resilience",
        overlaps_with="none in the bill", additive="yes",
        notes=(f"places (reserve, or nearest population centre within 30 km): {fmt(f.place.value_counts().head(8))}; Drayton Valley area flags (34) fail the screen "
               "(offset 102, false-positive ratio 0.35). No provincial count exists; First Nation and settlement counts reported in news are the next row."))
    ab_parts = [max(0, 85 - fox), max(0, 45 - stu), max(0, 28 - ep)]
    ab_b = sum(ab_parts)
    add(item="Buildings reported in news above the satellite count: Alberta 2023 (Fox Lake more than 85, Sturgeon Lake at least 45, East Prairie Metis Settlement 28)",
        sector="property", jurisdiction="AB", period="2023", amount_low_cad=0, amount_central_cad=ab_b * mv, amount_high_cad=ab_b * mv,
        dollars_basis=CENSUS, basis="officials' counts reported in news x census value (no official document)",
        method=(f"(Fox Lake more than 85 structures - {fox} flagged on IR Fox Lake 162) + (Sturgeon Lake Cree Nation at least 45 homes - {stu}) + (East Prairie Metis "
                f"Settlement 28 buildings incl. 14 homes - {ep}) = {ab_b} buildings x {mv:,.0f} (Alberta flagged mean)."),
        source_name="Little Red River Cree Nation emergency team (Global News, May 10, 2023); Sturgeon Lake Cree Nation (CTV Edmonton, May 18, 2023); East Prairie Metis Settlement chair (CTV Edmonton, May 2023) [NEWS REPORT]",
        url="https://globalnews.ca/news/9687943/alberta-wildfires-fox-lake-little-red-river-cree-nation/amp ; https://edmonton.ctvnews.ca/it-s-heartbreaking-dozens-of-homes-destroyed-in-sturgeon-lake-cree-nation-west-of-valleyview-1.6404483 ; https://edmonton.ctvnews.ca/like-a-war-zone-28-buildings-destroyed-by-wildfire-in-alta-m%C3%A9tis-settlement-1.6391591",
        overlaps_with="satellite row above (adds only buildings above it); " + news_overlap((fox + stu + ep) / 0.31 - (fox + stu + ep), ab_b, mv),
        additive=NEWS_ADD, notes=NEWS_NOTE)
# Quebec 2023
s = sat("qc2023")
if s:
    add(item="Buildings not in the bill: Quebec 2023 fires (chalets, camps and homes), satellite count", sector="property", jurisdiction="QC", period="2023",
        amount_low_cad=s["new"] / RLO * s["mean_med"], amount_central_cad=s["new_avg_sum"], amount_high_cad=s["new"] / 0.31 * s["mean_avg"],
        dollars_basis=CENSUS, basis="computed (satellite)",
        method=(f"{SATM}: {s['new']} flagged within 500 m of NBAC 2023 Quebec polygons. Central = each at its own DA average value; low = flagged / 1.51 at the median value; "
                "high = flagged / 0.31 (the Barrington ratio) because long fires are imaged after their last hotspot and early losses are under-detected."),
        source_name=SAT_SRC + "; no official count found (ministry, SOPFEU and season reviews give none)", url=SAT_URL,
        overlaps_with="none in the bill; Quebec business liquidity aid (econ_, transfer)", additive="yes",
        notes=(f"top places (reserve, or nearest population centre within 30 km): {s['places']}. Many are seasonal chalets valued as owner-occupied dwellings, as in the bill. "
               "Pointer only: the Noovo season review (Nov 14, 2023) gives no building count."))
# New Brunswick 2025
s = sat("atl2025", lambda d: d.prov == "NB")
add(item="Buildings: New Brunswick 2025 fires", sector="property", jurisdiction="NB", period="2025", amount_low_cad=0, amount_central_cad=0,
    amount_high_cad=(s["new"] / RHI * s["mean_avg"]) if (s and s["new"]) else 0, dollars_basis=CENSUS, basis="official statement (none lost); satellite check",
    method=f"Official: no structures lost (as of Aug 20, 2025). Satellite check: {s['new'] if s else 0} flags pass the quality screen within 500 m of NBAC 2025 New Brunswick polygons (any would enter the high case only).",
    source_name="New Brunswick update reported by CP24/CTV, Aug 20, 2025", url="https://www.cp24.com/news/canada/2025/08/20/active-wildfires-in-new-brunswick-down-to-20-five-out-of-control",
    overlaps_with="none", additive="no (none lost)", notes="")
# Ontario 2026
add(item="Buildings: Ontario 2026 fires (Thunder Bay 36 near Collins and Armstrong; Fort Frances 14 near Upsala): no official count; bill keeps its satellite count",
    sector="property", jurisdiction="ON", period="2026", amount_low_cad=0, amount_central_cad=0, amount_high_cad=0, dollars_basis=CENSUS,
    basis="no official count", method="The bill flags 86 (Thunder Bay 36) and 59 (Fort Frances 14) buildings; no official count exists to correct them. Reports confirm losses in both places (Collins First Nation homes and community buildings; four lodges near Upsala), so the flags are not obviously false.",
    source_name="pointers: Wikipedia 2026 Canadian wildfires (BBC Jul 15, 2026, Collins First Nation); Global News Jul 16, 2026 (lodges near Upsala)",
    url="https://en.wikipedia.org/wiki/2026_Canadian_wildfires ; https://globalnews.ca/news/11968629/northern-ontario-fires-lodges-lost/",
    overlaps_with="bill buildings line", additive="no (already in the bill)", notes="")

# ---------------- GAP 2: insured (industry) ----------------
add(item="Insured losses (industry): two further BC fire catastrophes of 2026 (not named by CatIQ; at least $30M each)", sector="property", jurisdiction="BC",
    period="2026", amount_low_cad=60e6, amount_central_cad=60e6, amount_high_cad="", dollars_basis="nominal CAD, 2026", basis="industry lower bound",
    method="CatIQ: 'British Columbia has seen ... three new catastrophes declared to date' (Sep 15, 2026); Bald Range is one ($293M). CatIQ declares a catastrophe when insured losses exceed CAN $30 million, so the other two are at least $30M each.",
    source_name="CatIQ releases Sep 15, 2026 and Jan 13, 2025 (catastrophe definition) [INDUSTRY DATA]",
    url="https://public.catiq.com/2026/09/15/cad-313m-catiq-discloses-initial-loss-estimate-for-bald-range-fire/ ; https://public.catiq.com/2025/01/13/canadian-insured-losses-from-catastrophic-events-total-can-8-5-billion-in-2024/",
    overlaps_with="bill buildings line and econ2 Bradley Creek / Pear Lake rows (same homes); health_ evacuation (living expenses)", additive="no",
    notes="Most likely Bradley Creek and the Big Bar complex (not confirmed by CatIQ). Industry, cross-check only.")
add(item="Insured losses (industry): two 2025 fire catastrophes not disclosed (at least $30M each)", sector="property", jurisdiction="MB, SK, NL (provinces with no prior fire catastrophe)",
    period="2025", amount_low_cad=60e6, amount_central_cad=60e6, amount_high_cad="", dollars_basis="nominal CAD, 2025", basis="industry lower bound",
    method="CatIQ: 2025 was first in fire catastrophes declared, all 'in provinces that had never had a prior industry fire catastrophe'; three are public (Flin Flon complex $249M, Pisew over $50M, Kingston over $70M). Each other catastrophe exceeds $30M by definition.",
    source_name="CatIQ release Jan 20, 2026 [INDUSTRY DATA]", url="https://public.catiq.com/2026/01/20/canadian-insured-losses-from-catastrophic-events-total-cad-2-4-b-in-2025-societal-losses-total-3-4-b/",
    overlaps_with="econ2 building rows for MB and NL (same buildings); health_ evacuation", additive="no", notes="Final figures for the 2023 BC and NWT events are not public: CatIQ publishes updates only above the PERILS threshold (Bald Range release, Oct 6, 2026).")

# ---------------- GAP 3: utilities ----------------
dist = {"low": 20e3, "central": 32e6 / 1200, "high": 32e3}   # MB Hydro: $24M capital / 1,200 poles; $32M / 1,200; $32M / 1,000
tr = {k: (15e6 - 53 * v) / 57 for k, v in dist.items()}    # BC Hydro 2024: $15M for 57 transmission structures + 53 distribution poles
bch = {k: 1200 * dist[k] + 200 * tr[k] for k in dist}
add(item="BC Hydro wildfire repair and restoration, 2023 season (about 200 transmission structures and over 1,200 distribution poles)", sector="infrastructure",
    jurisdiction="BC (Crown utility)", period="FY2023-24", amount_low_cad=200 * 15e6 / 57, amount_central_cad=bch["central"], amount_high_cad=bch["high"],
    dollars_basis="nominal CAD, 2023-24", basis="estimate from official unit costs",
    method=(f"Units: about 200 transmission structures and over 1,200 distribution poles replaced in 2023 (BC Hydro). Unit costs: distribution pole "
            f"${dist['low']/1e3:.0f}k to ${dist['high']/1e3:.0f}k (central ${dist['central']/1e3:.1f}k; Manitoba Hydro 2025: $24M capital in H1 and $32M restoration for 1,000 to 1,200 poles; "
            f"SaskPower 2025: $8.5M for at least 300 poles); transmission structure = (BC Hydro's 2024 $15M - 53 poles x pole cost) / 57 structures = "
            f"${tr['central']/1e3:.0f}k. Central = 1,200 x pole + 200 x structure. Low = 200 x $15M/57 (BC Hydro's own 2024 cost per transmission structure, distribution ignored); high uses the dearest pole cost."),
    source_name="BC Hydro news releases (2025 'wildfire-season'; 2024 'preparing-for-wildfires'; 2023 Shuswap restoration: 430 poles, 22 km); BC Hydro 2024/25 Annual Service Plan Report; Manitoba Hydro Q2 2025-26 report; Manitoba 2025 Wildfire Interim After Action Review; SaskPower via Government of Saskatchewan release Nov 4, 2025",
    url="https://www.bchydro.com/news/press_centre/news_releases/2025/wildfire-season.html ; https://www.bchydro.com/news/conservation/2024/preparing-for-wildfires.html ; https://www.bchydro.com/news/press_centre/news_releases/2023/shuswap-restoration.html ; https://www.hydro.mb.ca/docs/corporate/quarterly-report-250930.pdf",
    overlaps_with="none (utility capital costs are outside the bill, gov_ and health_); econ_ BC Hydro 2024 row is a different season", additive="yes",
    notes="No 2023 dollar figure is published: BC Hydro's F26-F27 Revenue Requirements Application shows only the storm-account variance (F2024 storm restoration -$7.0M vs plan, evacuation relief $0.4M), and BCUC orders G-177-24, G-236-24, G-256-24 give no wildfire amounts.")
nlfd = [105659.50, 30989.00, 26996.14, 23603.27, 17648.47, 14181.39, 11983.19, 11843.20, 10887.50, 10101.63, 5345.00, 5140.96, 4925.00, 4524.97, 4050.87, 4043.40,
        3966.54, 3314.63, 2850.00, 2147.68, 1679.40, 992.75, 800.00]
add(item="Fire department equipment damaged or lost fighting the 2025 Kingston wildfire (23 fire departments, provincial reimbursement)", sector="infrastructure",
    jurisdiction="NL (municipal fire departments)", period="2025 (paid 2026-27)", amount_low_cad=sum(nlfd), amount_central_cad=sum(nlfd), amount_high_cad=sum(nlfd),
    dollars_basis="nominal CAD", basis="actual (claims approved)", method="Sum of the 23 claims in the backgrounder (includes $100,000 for a Bay de Verde response vehicle and some fuel costs).",
    source_name="Government of Newfoundland and Labrador news release, Aug 27, 2026 (Forestry, Agriculture and Lands)", url="https://www.gov.nl.ca/releases/2026/fal/0827n03/",
    overlaps_with="not in gov_ (gov_ NL line is the provincial Fire Suppression vote)", additive="yes (gov_ scope)", notes="")
add(item="SaskTel customer bill relief during the 2025 evacuations", sector="infrastructure", jurisdiction="SK (Crown utility)", period="2025",
    amount_low_cad=315000, amount_central_cad=315000, amount_high_cad=315000, dollars_basis="nominal CAD, 2025", basis="actual (approximate)",
    method="'the relief measures saved customers about $315,000'", source_name="Government of Saskatchewan news release, Nov 4, 2025",
    url="https://www.saskatchewan.ca/government/news-and-media/2025/november/04/crown-corporations-support-northern-wildfire-recovery-and-help-communities-and-families",
    overlaps_with="health_ evacuation (relief to evacuees)", additive="no (transfer)", notes="No SaskTel or SaskEnergy damage cost is published; SaskEnergy reports only maintaining service to La Ronge.")
for it, j, per, src, url, note in [
    ("Hydro-Quebec 2023 forest fires: smoke-triggered line trips and outages; no asset damage cost reported", "QC (Crown utility)", "2023", "Hydro-Quebec Annual Report 2023",
     "https://www.hydroquebec.com/data/documents-donnees/pdf/annual-report-2023-hydro-quebec.pdf", "Fires near Baie-James facilities; 'smoke triggered automatic service interruptions on certain transmission lines'."),
    ("NWT Power Corporation 2023: 'limited physical asset damage' (one Snare transmission tower and Behchoko distribution); no cost reported", "NT (Crown utility)", "FY2023-24",
     "NTPC Annual Report 2023-24", "https://www.ntpc.com/sites/default/files/2024-10/NTPC%20-%20Annual%20Report%20-%202023-24_1.pdf", "Lost sales during evacuations are not quantified."),
    ("Hydro One 2026: 'wildfire activity has not had a major impact in our operations'; some northern infrastructure affected; no cost reported", "ON (utility)", "2026",
     "Hydro One Q2 2026 analyst call transcript (Aug 12, 2026) and release", "https://www.hydroone.com/investorrelations/Reports/Hydro%20One%20Limited%202Q26%20Analyst%20Call%20Transcript.pdf",
     "No fires attributed to Hydro One assets.")]:
    add(item=it, sector="infrastructure", jurisdiction=j, period=per, amount_low_cad=0, amount_central_cad=0, amount_high_cad=0, dollars_basis="nominal CAD",
        basis="official statement (no material cost)", method="The utility's own report names wildfire effects but no damage cost; nothing to add.", source_name=src, url=url,
        overlaps_with="none", additive="no (nothing to add)", notes=note)

# ---------------- GAP 5: uninsured-loss and recovery programs ----------------
add(item="Saskatchewan 2025 wildfire recovery task team: cleanup, debris removal, landfills and temporary housing", sector="property (recovery)", jurisdiction="SK",
    period="FY2025-26 onward", amount_low_cad=18e6, amount_central_cad=29.93e6, amount_high_cad=29.93e6, dollars_basis="nominal CAD", basis="commitment (low = committed to date)",
    method="'$29.93 million ... 20 million was dedicated to cleanup, debris management, landfill expansion, and maintenance, and then another roughly $9.93 million towards temporary housing ... about $18 million has been committed' (ADM, recovery task team, Dec 1, 2025).",
    source_name="Legislative Assembly of Saskatchewan, Standing Committee on Intergovernmental Affairs and Justice, Hansard Dec 1, 2025, pp. 118-124",
    url="https://docs.legassembly.sk.ca/legdocs/Committees/IAJ/Debates/30L/20251201Debates-IAJ.pdf",
    overlaps_with="not in the bill's SK firefighting line (SPSA response, $295.3M of the supplementary estimate is 'evacuation and wildfire response'); not in health_ (its SK rows are evacuation-period hotels, food, payments, Red Cross); PDAP private claims are separate and unpublished",
    additive="yes", notes="About 250 Denare Beach properties cleaned and returned to owners in under four months (same source).")

# ---------------- GAP 6: forestry ----------------
gs = list(csv.DictReader(open(os.path.join(B, "work", "econ2_gdp_sawmills.csv"))))[0]
add(item="GDP lost: Sawmills and wood preservation, Canada (2023-05 to 2023-09)", sector="economic (GDP)", jurisdiction="Canada", period="2023",
    amount_low_cad=gs["low"], amount_central_cad=gs["central"], amount_high_cad=gs["high"], dollars_basis="nominal CAD (GDP implicit price index)",
    basis="computed", method=f"econ_02 method on NAICS 3211: straight-line baseline April to October 2023, months May to September, loss = (baseline - actual)/12; full ${float(gs['loss_nominal_full'])/1e6:.1f}M; attribution 'partial' (0/50/100%). {gs['detail']}",
    source_name="Statistics Canada Table 36-10-0434-01; The Daily, Monthly Survey of Manufacturing, September 2023 ('The wildfires in 2023 impacted production in many sawmills across Canada')",
    url="https://www150.statcan.gc.ca/n1/daily-quotidien/231115/dq231115a-eng.htm ; https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610043401",
    overlaps_with="econ_ forestry and logging GDP (a different industry, no double count of value added); the bill's timber line values standing trees (an input, not sawmill value added); health_ lost wages of evacuated mill workers",
    additive="yes", notes="Quebec mill shutdowns (four Resolute sawmills, two Remabec sawmills, Nordic Kraft pulp mill for a month) are described only by Desjardins (not official). No official salvage-cost figure exists; Quebec's special salvage plans (plans d'amenagement special) give volumes only.")

# ---------------- GAP 8: 2026 economy ----------------
add(item="2026 wildfire effect on GDP, jobs and oil output: none reported by Statistics Canada, the Bank of Canada or provincial finance ministries", sector="economic (GDP)",
    jurisdiction="Canada", period="2026", amount_low_cad=0, amount_central_cad=0, amount_high_cad=0, dollars_basis="nominal CAD", basis="official statements",
    method="StatCan Daily releases checked (GDP June and July 2026, Q2 2026 GDP, LFS August and September 2026, Sawmills June 2026, Natural resource indicators Q2 2026, Energy statistics July 2026, National tourism indicators Q2 2026, Travel August 2026, EI August 2026): no mention of wildfires. Bank of Canada MPR July 2026 and Business Outlook Survey Q3 2026: no mention. Alberta Q1 2026-27: 'limited wildfire disruptions supported activity'. BC Q1 2026/27: economy 'resilient despite wildfires', no figure.",
    source_name="Statistics Canada The Daily; Bank of Canada; Alberta 2026-27 First Quarter Fiscal Update; BC First Quarterly Report 2026/27",
    url="https://www150.statcan.gc.ca/n1/daily-quotidien/260929/dq260929a-eng.htm ; https://www.bankofcanada.ca/publications/mpr/mpr-2026-07-15/ ; https://open.alberta.ca/dataset/9c81a5a7-cdf1-49ad-a923-d1ecb42944e4/resource/eaeb7a75-0c9f-4964-be53-0f1cc889ffab/download/tbf-2026-27-first-quarter-fiscal-update-economic-statement.pdf",
    overlaps_with="none", additive="no (nothing to add)", notes="August 2026 GDP is released Oct 30, 2026 and the October MPR on Oct 28, 2026 (after this check).")

with open(os.path.join(B, "econ2_costs.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
d = pd.DataFrame(rows)
for c in ("amount_low_cad", "amount_central_cad", "amount_high_cad"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
add_ = d[d.additive.str.startswith("yes")]
print(d[["item", "amount_low_cad", "amount_central_cad", "amount_high_cad", "additive"]].assign(item=d.item.str[:95]).to_string())
print("additive total low/central/high ($M):", round(add_.amount_low_cad.sum() / 1e6, 1), round(add_.amount_central_cad.sum() / 1e6, 1), round(add_.amount_high_cad.sum() / 1e6, 1))
nw = d[d.additive.str.startswith("no (count reported only in news")]
print("news-reported rows (not added) low/central/high ($M):", round(nw.amount_low_cad.sum() / 1e6, 1), round(nw.amount_central_cad.sum() / 1e6, 1), round(nw.amount_high_cad.sum() / 1e6, 1))
