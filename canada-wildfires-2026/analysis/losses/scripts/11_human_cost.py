"""Combine everything into one 'human cost' table for 2023-2026 (human_cost_2023_2026.csv), each cell with source and
coverage. Values are read from the outputs of scripts 01-10 and 13, from analysis/health (not recomputed), and from
the official text records listed in the 'source' column (ISC page, Question Period notes)."""
import os
import pandas as pd

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(L))
Y = [2023, 2024, 2025, 2026]
rows = []
def add(measure, vals, source, coverage, kind):
    r = dict(measure=measure); r.update({str(y): vals.get(y, "") for y in Y}); r.update(source=source, coverage=coverage, kind=kind); rows.append(r)

# Direct deaths and injuries
t = pd.read_csv(os.path.join(L, "tsb_firefighting_by_year.csv"), index_col=0)
add("Deaths in wildfire aviation occurrences (firefighting, fire management, confirmed wildfire work)",
    {y: int(t.at[y, "wildfire_work_fatalities"]) for y in Y}, "TSB air occurrence data (ASIS), files dated 2026-10-21; tsb_firefighting_by_year.csv",
    "Canada, occurrences to 2026-10-08; aviation only; recent records can still be updated", "official count")
add("Serious injuries in wildfire aviation occurrences", {y: int(t.at[y, "wildfire_work_serious_injuries"]) for y in Y},
    "TSB ASIS (as above)", "as above", "official count")
add("Minor injuries in wildfire aviation occurrences", {y: int(t.at[y, "wildfire_work_minor_injuries"]) for y in Y},
    "TSB ASIS (as above)", "as above", "official count")
add("Other direct wildfire deaths stated in federal records", {2025: "2 (Lac du Bonnet, MB)"},
    "Public Safety Canada Question Period notes PS-2025-QP-005 (2025-10-01) and PS-2026-QP-006 (2026-01-16), open.canada.ca QP notes dataset",
    "2025 only; no national official compilation of wildfire deaths exists for 2023-2026 (CDD ends 2022-12)", "official statement")
add("Canadian Disaster Database wildfire deaths / injured / evacuated", {y: "not yet in CDD" for y in Y},
    "CDD extract (open.canada.ca 1c3d15f9..., modified 2026-02-10)", "latest event in the whole CDD starts 2022-12-22; latest wildfire event 2022-06-30 to 2022-09-27", "official database")
# Evacuations
add("People evacuated, all of Canada", {2023: "over 200,000", 2024: "no national figure (Jasper alone about 25,000)", 2025: "over 70,000", 2026: "no national figure"},
    "PS Question Period notes PS-2024-QP-1--MEP-011 (2023-09-21), PS-2024-QP-1--MEP-001 (2024-09-16), PS-2025-QP-005 (2025-10-01)",
    "rounded statements at those dates; not a dataset", "official statement")
s = pd.read_csv(os.path.join(L, "isc_season_snapshots.csv")).set_index("season")
f = pd.read_csv(os.path.join(L, "isc_wildfire_evacuations_by_fiscal_year.csv")).set_index("fy_start")
add("First Nations people evacuated (on reserve, EMAP-eligible)",
    {2023: "not published per year", 2024: f"over {s.at[2024,'people_evacuated']:,} (Apr 1-Sep 30)", 2025: f"over {s.at[2025,'people_evacuated']:,} (Apr 1-Aug 20)",
     2026: f"{s.at[2026,'people_evacuated']:,} (Apr 1-Oct 2)"},
    "ISC QP notes ISC-2025-QP-00780, ISC-2025-QP-00808; ISC 'Wildfire evacuation information for Indigenous peoples' (modified 2026-10-05)",
    "partial seasons as stated; 10-year total FY2016-17 to FY2025-26 = 143,724 (ISC statistics page)", "official statement")
add("First Nations wildfire evacuation events (fiscal year starting April)", {y: int(f.at[y, "total"]) for y in [2023, 2024, 2025]} | {2026: "FY2026-27 not yet published"},
    "ISC 'Wildland fire and flood evacuation statistics' page (modified 2026-06-01)", "fiscal years; numbers not final", "official count")
add("First Nations affected by wildfire (EMAP)", {2024: int(s.at[2024, "first_nations_affected"]), 2025: int(s.at[2025, "first_nations_affected"]), 2026: int(s.at[2026, "first_nations_affected"])},
    "ISC (as above)", "same partial seasons", "official statement")
# Buildings
p = os.path.join(L, "buildings_exposure_by_year_nbac.csv")
nb = pd.read_csv(p) if os.path.exists(p) else pd.DataFrame(columns=["year", "prov", "inside", "within_100m"])
nb = nb[nb.prov == "Canada"].set_index("year")
pv = pd.read_csv(os.path.join(L, "buildings_exposure_by_province.csv"), index_col=0)
vals = {y: f"{int(nb.at[y,'inside']):,} inside + {int(nb.at[y,'within_100m']):,} within 100 m" for y in nb.index if y in Y}
vals[2026] = f"{int(pv.at['Canada','inside']):,} inside + {int(pv.at['Canada','within_100m']):,} within 100 m"
add("Buildings exposed (footprints inside burned area or within 100 m)", vals,
    "Microsoft Global ML Building Footprints (release 2026-02-03) vs NBAC 2023-2025 polygons and CWFIS M3 2026 outlines (farm/grass and military-range outlines excluded); scripts 05, 05b, 07",
    "exposure, not loss; footprint imagery dates vary, so 2023-2025 counts miss buildings already gone from the imagery; 2026 uses hotspot-derived outlines to 2026-10-20", "our computation")
d = pd.read_csv(os.path.join(L, "dnbr_by_fire.csv"))
add("Buildings likely destroyed (Sentinel-2 dNBR, our estimate)",
    {2026: f"{int(d['likely destroyed'].sum())} (lenient rule {int(d['lenient_possibly_destroyed'].sum())}); {int(d['damaged surroundings'].sum())} with burned surroundings"},
    "Sentinel-2 L2A (Earth Search STAC), scripts 08 and 10; scenes in dnbr_scenes.csv",
    f"2026 only; the {len(d)} fires with 10 or more buildings inside ({int(d.buildings_classified.sum()):,} buildings); not calibrated to an official count", "our estimate")
# Smoke deaths (reuse analysis/health)
h = pd.read_csv(os.path.join(W, "analysis", "health", "modelled_acute_deaths_national.csv"))
def fmt(coef, y):
    r = h[(h.coefficient.str.startswith(coef)) & (h.year == y)].iloc[0]
    return f"{r.net_c:.0f} ({r.net_lo:.0f} to {r.net_hi:.0f})"
add("Modelled acute deaths from wildfire smoke, Chen 2021 coefficient (net, central and 95% range)", {y: fmt("Chen", y) for y in Y},
    "analysis/health/modelled_acute_deaths_national.csv (not recomputed)", "2023-2024: 12 provinces/territories (not NU); 2025-2026: 9 (not MB, NL, NT, NU); 2026 PM2.5 to 2026-10-19", "model estimate")
add("Modelled acute deaths from wildfire smoke, AQBAT coefficient (net, central and 95% range)", {y: fmt("AQBAT", y) for y in Y},
    "analysis/health/modelled_acute_deaths_national.csv (not recomputed)", "as above", "model estimate")
# Insured
add("Insured loss, wildfire events (industry data)",
    {2023: "no wildfire-specific public figure (all perils CAD 3.1 B)", 2024: "Jasper CAD 1.304 B (final); all perils CAD 9.1 B",
     2025: "no wildfire-specific public figure (all perils CAD 2.4 B; 5 fire catastrophes declared)", 2026: "Bald Range CAD 293 M (45-day estimate); other 2026 fire events not public"},
    "CatIQ press releases on public.catiq.com and IBC releases citing CatIQ; insured_losses_wildfire.csv", "industry data, not government; only publicly disclosed events", "industry estimate")
# Government payments
gp = os.path.join(L, "dfaa_wildfire_payments.csv")
gv = {y: "none listed" for y in Y}
if os.path.exists(gp):
    g = pd.read_csv(gp)
    for y in Y:
        gy = g[g.event_year == y]
        if len(gy): gv[y] = f"CAD {gy.agreement_value.sum()/1e6:,.1f} M in {len(gy)} DFAA agreement rows"
add("Federal disaster payments for wildfires (DFAA)", gv,
    "CDD (to 2022) and federal Grants and Contributions proactive disclosure (script 12/13)", "see results.md for coverage of the disclosure data", "official records")
out = pd.DataFrame(rows)
out.to_csv(os.path.join(L, "human_cost_2023_2026.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
print(out[["measure"] + [str(y) for y in Y]].to_string())
