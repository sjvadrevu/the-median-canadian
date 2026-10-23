# Property damage from Canadian wildfires, 2026 and 2023 to 2026

Original analysis from raw official data (government pages and layers, Statistics Canada, NRCan, Copernicus Sentinel-2, Microsoft building footprints). News was used only to locate datasets. Insured losses are industry data (CatIQ, IBC) and labelled as such. Run date 2026-10-21/22.

## Scorecard

| Measure | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| Official structures destroyed, listed events | 615 + about 200 impacted | 358 (townsite) | about 400 homes (SHOE region); about 700 structures SK season | about 150 damaged or destroyed (Bald Range) |
| Our satellite estimate, flagged within 500 m | 844 (4 events) | 417 (Jasper, in-sample) | 405 (2 events) | 488 after the quality screen (517 before; all 2026 outlines) |
| Value of destroyed dwellings, proxy (official counts) | $445 M | $275 M | $85 M | $117 M |
| Value of dwellings exposed (DA point inside fire) | $1.56 B | $0.69 B | $2.04 B | $1.17 B |
| Insured loss, industry, listed events | over $945 M | $1.304 B | over $369 M | $293 M |
| Roads inside burned area | 4,512 km | 755 km | 3,025 km | 1,280 km |

- 2026: the rule flags 517 buildings within 500 m of a 2026 fire outline (calibration band 475 to 569). Bald Range alone: 168 flagged vs about 150 official (damaged or destroyed, preliminary).
- Quality screen (added 2026-10-23; the same screen the second cost round applies to its new satellite counts): 29 of the 517 flags fail it, 23 on FOR_FIRE_014 (scene offsets beyond 100) and 6 on three small or noisy outlines. The bill counts the 488 that pass, worth $268 M (destroyed_value_estimates.csv; the failures are listed in work/screen_fail_2026.csv). The by-fire table below is before the screen. The 2023 to 2025 check events all pass.
- Rule accuracy on Jasper (structure-level truth, 5-fold spatial CV): precision 0.836, recall 0.832. On six other events with official counts only, flagged/official ranged 0.31 to 1.51.
- 2023 to 2026 union: 15,510 dwellings ($5.3 B, census proxy) in DAs whose representative point lies inside a fire; 486,438 dwellings ($174 B) in DAs touched by a fire.

## Method in one paragraph

Each Microsoft footprint within 1 km of a fire polygon gets Sentinel-2 L2A features: dNBR and dNDVI (pre minus post, x1000, offset by the median of pixels more than 1 km from any fire). Rule calibrated on the Municipality of Jasper's official structure-status layer: `dndvi_bmax >= 180 AND dnbr_r20_60 >= 40`, plus a fixed burn-context filter (at least 20% of pixels 100 to 250 m away with dNBR >= 100). Flags are counted inside the fire polygon or within 500 m (outlines from NBAC and CWFIS M3 miss unburned islands and edges; the 500 to 1,000 m band is a false-positive check). Estimate = flagged x P / R, band from 95% Wilson intervals of the CV precision and recall. That band covers the calibration sample only, not transfer error.

## Event table, 2023 to 2026

Official columns are as published. "Flagged" = our estimate (likely destroyed, within 500 m). Ratio = flagged / official.

| Event | Yr | Official destroyed | Official damaged | Publisher (source) | Flagged | Ratio |
|---|---|---|---|---|---|---|
| Upper Tantallon, NS | 2023 | about 200 structures (151 homes) | | [HRM / HRFE](https://www.halifax.ca/sites/default/files/documents/city-hall/regional-council/240820cow4.pdf) | 241 | 1.21 |
| Barrington Lake, NS | 2023 | 230 | 59 | [HRFE citing AAR](https://www.halifax.ca/sites/default/files/documents/city-hall/regional-council/240820cow4.pdf) | 72 | 0.31 |
| McDougall Creek, BC | 2023 | about 200 impacted (destroyed or damaged) | | [RDCO](https://www.rdco.com/media/k3apxusq/debris-management-plan-mcdougall-creek-wildfire.pdf) | 302 | 1.51 |
| Bush Creek East, BC | 2023 | 185 (CSRD 176, TNRD 9) | 52 | [CSRD](https://www.csrd.bc.ca/CivicAlerts.aspx?AID=1724), [TNRD](https://www.tnrd.ca/tnrd-confirms-structural-impacts-on-11-properties-due-to-bush-creek-east-fire/) | 229 | 1.24 |
| Hay River / Enterprise, NT | 2023 | no count | | [Town of Hay River](https://hayriver.com/2023-wildfire-updates/) | 105, unreliable | |
| Jasper, AB | 2024 | 358 (townsite); layer 567 all types | 31 | [Parks Canada](https://parks.canada.ca/pn-np/ab/jasper/gestion-management/serviceimmobilier-realty/retablissement-recovery/stat-dashboard), [MOJ layer](https://services7.arcgis.com/1glZz4XajYW77W8H/arcgis/rest/services/Damage_Assessment_Structures/FeatureServer/0) | 417 (in-sample) | 1.11 vs 374 matched |
| SHOE fire, Denare Beach, SK | 2025 | about 400 homes (region) | | [Gov. of SK (MNP)](https://www.saskatchewan.ca/-/media/news-release-backgrounders/2026/jun/mnp-2025-wildfire-report.pdf) | 355 | 0.89 |
| Lac du Bonnet, MB | 2025 | no count | | [Manitoba releases](https://news.gov.mb.ca/news/index.html?item=69398) | 50 | |
| Kingston, NL | 2025 | not read (HTTP 500) | | [Gov. of NL](https://www.gov.nl.ca/releases/2025/jps/0811n08/) | not run | |
| Bald Range, BC | 2026 | about 150 damaged or destroyed (110 RDOS F, 40 Summerland) | | [District of Summerland](https://www.summerland.ca/city-services/eoc/bald-range-wildfire-home/bald-range-wildfire-faq) | 168 (band 154 to 185) | 1.12 |
| Bradley Creek, BC (OKIB IR #1) | 2026 | no count published | | [OKIB news](https://www.okib.ca/wp-json/wp/v2/news) | 103 (band 95 to 113) | |

## 2026 by fire (our estimate, no official count unless stated)

Fires with at least 3 flagged buildings. Agency ID = largest NRCan CWFIF 2026 point inside or within 5 km. Full list: `estimates_2026_by_fire.csv`.

| Fire | Prov | Agency ID | Flagged 500 m | Band | Value proxy |
|---|---|---|---|---|---|
| Bald Range | BC | K51490 | 168 | 154 to 185 | $131 M |
| Bradley Creek | BC | K41351 | 103 | 95 to 113 | $65 M |
| unnamed | ON | THU_FIRE_036 | 86 | 79 to 95 | $19 M |
| unnamed | ON | FOR_FIRE_014 | 59 | 54 to 65 | $10 M |
| unnamed | BC | C40983 | 58 | 53 to 64 | $27 M |
| unnamed | BC | V10755 | 14 | 13 to 15 | $7 M |
| 5 fires, 3 to 4 each | BC, MB, NT | | 16 | | $12 M |
| 12 fires, 1 to 2 each | 6 prov. + NT | | 13 | | $3 M |
| All 2026 | | | 517 | 475 to 569 | $274 M |

Transfer range for the 2026 total: if the count ratios seen on other events (0.89 to 1.51, Barrington excluded) apply, the true 2026 total is about 340 to 580. A Barrington-like under-detection would put it far higher.

## Transfer checks (does the Jasper rule hold elsewhere?)

Only Jasper has a public structure-level layer (3,467 ArcGIS Online items screened), so per-event accuracy outside Jasper is count-level only.

| Event | Check | Result |
|---|---|---|
| Jasper 2024 | structure-level, 5-fold spatial CV | P 0.836, R 0.832, F1 0.834 |
| Tantallon 2023 | count | 1.21 |
| Barrington 2023 | count | 0.31 (large under-count, cause not found) |
| McDougall 2023 | count vs "impacted" | 1.51 |
| Bush Creek 2023 | count vs destroyed | 1.24 (0.97 vs destroyed + damaged) |
| Denare 2025 | count vs regional homes | 0.89 |
| Bald Range 2026 | count vs damaged or destroyed | 1.12 |
| All, 500 to 1,000 m band | false positives far outside fire | 0 to 7 per event (17 Bradley Creek, 44 all 2026) |

## Value of dwellings destroyed and exposed (census value proxy)

Proxy = 2021 Census average value of owner-occupied dwellings in the DA (fallback CD, then province), applied to all structures. Not insured, not market loss.

| Year | Destroyed, official count x local value | Destroyed, flagged x own DA value | Exposed dwellings, DA point inside | Exposed value | Exposed, DA touches fire |
|---|---|---|---|---|---|
| 2023 | $445 M (4 events) | $591 M | 4,675 | $1.56 B | $84.0 B |
| 2024 | $275 M (Jasper, 370 polygons) | $298 M | 1,724 | $0.69 B | $67.8 B |
| 2025 | $85 M (Denare) | $94 M | 7,251 | $2.04 B | $89.4 B |
| 2026 | $117 M (Bald Range) | $274 M | 2,470 | $1.17 B | $18.4 B |
| 2023 to 2026 | $922 M | $1,256 M | 15,510 | $5.34 B | $174.2 B |

Medians run about 10% lower (`destroyed_value_official.csv`, `destroyed_value_estimates.csv`, `exposed_dwelling_value_by_year.csv`). Bradley Creek values are CD fallback (reserve DA values suppressed).

## Infrastructure inside burned areas (km)

| Year | Roads | Highways | Rail | Main rail | Power lines |
|---|---|---|---|---|---|
| 2023 | 4,512 | 411 | 253 | 239 | 853 |
| 2024 | 755 | 172 | 61 | 59 | 78 |
| 2025 | 3,025 | 1,218 | 121 | 117 | 481 |
| 2026 | 1,280 | 191 | 252 | 207 | 269 |
| 2023 to 2026 | 9,503 | 1,986 | 686 | 620 | 1,676 |

Length inside fire polygons, not damage. 2026 is led by BC (518 km roads, 177 km rail, 193 km power lines). No official open data on service interruptions found.

## Insured losses (industry data, CatIQ / IBC)

| Year | Events | Insured (CAD) | Largest |
|---|---|---|---|
| 2023 | 5 | over $945 M | McDougall Creek over $480 M |
| 2024 | 1 | $1.304 B (final) | Jasper |
| 2025 | 3 | over $369 M | Flin Flon complex $249 M |
| 2026 | 1 | $293 M (45-day) | Bald Range (initial $313 M) |

Sums of published event estimates, not annual totals. Sources in `insured_losses_industry.csv`.

## Caveats

- Official counts mix units (homes, structures, properties, "impacted") and are approximate or preliminary; ratios carry that noise.
- The rule is calibrated on one event (Jasper townsite). A building that survives inside severely burned forest looks like a loss to it; the two Ontario clusters (near 50.2N 89.3W and 48.9N 90.7W) fit that risk and have no official count to check against.
- Barrington 2023 under-detection (0.31) is unexplained.
- Enterprise 2023 offsets were unstable (0 fallback in 5 of 7 cells, +83 to +85 dNBR in 2), so its 105 flags are not used in totals.
- M3 2026 outlines under-map some burns: 84 of Bradley Creek's flags lie 250 to 500 m outside the outline, in burned ground (median ring dNBR 217).
- Denare Beach and Enterprise were run in 20 km cells with per-cell offsets (single grids exceeded memory). One 5-footprint Denare cell had a -185 offset (no flags). Bald Range features come from the 2026 cluster run (same windows as the check-event design).
- Bush Creek burn context was rebuilt from the saved dNBR raster (validated on Tantallon: max difference 0.0025, 2 of 2,115 threshold flips).
- Footprints are Microsoft ML (ODbL), which misses some buildings and includes non-dwellings; 2026 post-fire imagery runs only to 2026-10-20.

## Files

Scripts `scripts/00` to `15` (new: `05b_add_context.py`, `05c_merge_cells.py`, `15_apply_2026.py`, `run_checks3.sh`, `run_checks4.sh`); outputs `estimates_2026_by_fire.csv`, `transfer_checks.csv`, `destroyed_value_official.csv`, `destroyed_value_estimates.csv`, plus the earlier calibration, exposure, infrastructure and insured CSVs; sources in `manifest.csv`.
