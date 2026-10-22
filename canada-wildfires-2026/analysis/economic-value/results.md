# Economic value of Canadian wildfires: 2026, 2023 to 2026, and 2016 to 2022 (original analysis of official data)

Run 2026-10-21. Every number comes from raw official files listed in `manifest.csv` (industry insured losses are labelled). No news or third-party analysis is used as a source of numbers. Scripts are in `scripts/` (run order 02, 03, 05, 04, 04b, 06, 07, 08, 09, then 10 (BC LFS fallback); 00 writes the manifest; 01 streams the federal grants file). Dollars are 2025 dollars (CPI all-items annual average) unless marked nominal.

## Scorecard

| Measure | 2026 | 2023 to 2026 | 2016 to 2022 average |
|---|---|---|---|
| Timber burned, value at Crown stumpage | $1.59 B | $12.64 B (four seasons, nominal) | $1.89 B a year (nominal) |
| Provincial firefighting, BC + ON + AB + SK | $0.83 B (BC only so far) | $7.28 B | $1.05 B a year |
| Federal DFAA wildfire orders | none yet | $1.03 B (2025 incomplete) | 2016 only: $0.60 B |
| Insured losses (industry, named events) | $0.29 B (Bald Range, early) | $1.60 B nominal (Jasper + Bald Range) | 2016 $4.60 B (Fort McMurray) |
| Smoke deaths valued at Health Canada VSL (Chen) | $2.43 B | $19.90 B | $1.65 B a year (2018 to 2022) |
| Jasper National Park visits, fire year | n/a | 2024-25: 1.14 M, 53% below baseline | baseline 2.45 M |

## 1. Value of standing timber burned

Method
- Volume: scaled merchantable volume burned per province and year (NFI kNN 2011 volume on NBAC 2016 to 2025 and CWFIS M3 2026 footprints, scaled to official provincial area), from `analysis/economy/timber_carbon_by_year.csv`.
- Stumpage price (government revenue per m3): NFD "Statement of Revenues from the Sale of Timber from Provincial Crown Land", stumpage charges, divided by NFD roundwood harvested on provincial land, 2016 to 2024. For BC the provincial Budget and Fiscal Plan "Total stumpage rates ($Cdn/cubic metre)" is used for every year (updated forecast for the fiscal year containing the fire season; 2026/27 = Budget 2026 estimate). The two BC measures agree within 1 to 3 dollars a year (for example 2018 $20.84 both; 2024 $15.03 fiscal plan vs $14.51 NFD).
- Gaps: years after the last NFD year carry the last value (all provinces except BC for 2025 and 2026; Ontario after 2023; New Brunswick after 2021). Ontario 2020 to 2022 (NFD "not available") use the mean of 2019 and 2023. NWT and Nunavut report no Crown stumpage revenue, so their burned timber has a stumpage value of zero. Every price and its basis is in `timber_prices_by_province_year.csv`.
- This is the value of standing timber burned, not a loss. Most burned forest is outside harvest plans, much can be salvaged, and harvest is capped by allowable annual cut rather than by standing stock.

Findings
- 2026: 169.1 million m3 of merchantable wood burned, worth $1.593 B at Crown stumpage (nominal; $1.554 B in 2025 dollars). BC $957 M (62.8 M m3 at $15.24), Ontario $293 M (56.7 M m3 at $5.17), Quebec $266 M (19.2 M m3 at $13.83), Saskatchewan $44 M, Manitoba $26 M, Newfoundland and Labrador $3.8 M, Alberta $1.5 M.
- 2023: $7.442 B nominal ($7.777 B in 2025 dollars), the largest of 2016 to 2026. BC $3.99 B, Quebec $2.13 B, Alberta $642 M, Saskatchewan $468 M, Ontario $149 M.
- 2024: $1.536 B. 2025: $2.073 B (Saskatchewan $772 M, Manitoba $527 M, BC $442 M, Ontario $209 M).
- 2023 to 2026, sum of the four seasons: $12.64 B nominal ($12.97 B in 2025 dollars). The distinct 2023 to 2026 burned area (each hectare once, 1,336 million m3) valued at each province's volume-weighted 2023 to 2026 price: $12.60 B (BC $6.46 B, Quebec $2.51 B, Saskatchewan $1.44 B, Alberta $0.83 B, Ontario $0.66 B, Manitoba $0.63 B).
- 2016 to 2022 averaged $1.89 B a year nominal ($2.25 B in 2025 dollars); 2021 was $5.94 B and 2018 $3.99 B, both driven by high BC stumpage ($37.14 and $20.84 per m3).
- Context: total Crown stumpage charges collected in Canada (NFD, all provinces) were $1.03 B in 2023 and $0.85 B in 2024. The stumpage value of timber burned in 2023 was 7.2 times what Crown stumpage actually raised that year.
- Price, not volume, swings the value: BC burned 62.8 M m3 in 2026 against 213.5 M m3 in 2023, but 2026 BC stumpage ($15.24) is lower than in any year since 2017.

Inside forest management tenure (cell centre inside the polygon; scaled merchantable volume; value at stumpage)

| Layer | 2023 | 2024 | 2025 | 2026 | 2023 to 2026 distinct |
|---|---|---|---|---|---|
| Alberta FMAs, share of AB volume | 67% | 32% | 76% | 25% | 64% |
| Alberta FMAs, volume (M m3) | 110.3 | 8.0 | 22.2 | 0.11 | 140.4 |
| Ontario FMUs, share | 40% | 12% | 26% | 38% | 34% |
| Ontario FMUs, volume (M m3) | 11.5 | 0.43 | 10.4 | 21.6 | 43.9 |
| Quebec UAs, share | 46% | 7% | 20% | 17% | 41% |
| Quebec UAs, volume (M m3) | 62.8 | 0.53 | 0.03 | 3.28 | 66.6 |
| Sask. commercial forest, share | 43% | 44% | 74% | 47% | 61% |
| Sask. commercial forest, volume (M m3) | 29.1 | 13.3 | 100.8 | 3.6 | 145.5 |
| BC Tree Farm Licences, share | 0.6% | 5.0% | 1.7% | 0.9% | 1.6% |

- Value at stumpage inside these layers (AB FMA + ON FMU + QC UA + SK commercial forest + BC TFL): $1.70 B in 2023, $168 M in 2024, $712 M in 2025, $187 M in 2026.
- 2026 value inside tenure: Ontario FMUs $112 M (21.6 M m3, of 56.7 M m3 burned in Ontario), Quebec UAs $45 M, Saskatchewan commercial forest $21 M, BC TFLs $8.8 M, Alberta FMAs $0.4 M.
- BC Timber Supply Areas cover essentially the whole province (100% of every year's burned BC volume falls inside a TSA or TFL), so they do not separate harvestable from unharvestable forest. No open timber harvesting land base layer was used.
- Files: `tenure_volume_by_year.csv`, `timber_value_in_tenure.csv`.

Industry (roundwood) value: see section 1b.

Files: `timber_prices_by_province_year.csv`, `timber_value_by_province_year.csv`, `timber_value_canada_year.csv`, `timber_value_union_2023_2026.csv`.

## 1b. Roundwood (industry) value and lumber prices

Not computed. The industry value per m3 needs Statistics Canada tables (output of forestry and logging by province, 36-10-0488; industrial product price index for lumber, 18-10-0266; raw materials price index, 18-10-0268). www150.statcan.gc.ca served its maintenance page or reset connections for every attempt from 21:2x to 22:4x ET on 2026-10-21 (polling script `scripts/00_fetch_statcan.sh`, log `raw/statcan/fetch.log`), as it did throughout the earlier steps of this project. The National Forestry Database no longer publishes a value-of-roundwood table (its current download list has only the Crown revenue statement). `05_timber_value.py` and `07_cost_tally.py` pick up a `work/roundwood_value_per_m3.csv` (prov, year, price_roundwood, price_roundwood_basis) automatically once it exists.

Context from official BC data that did download: the BC Market Pricing System lumber values used for Interior stumpage calculations from April 2026 were $337 to $452 per thousand board feet for most species and zones (cedar $1,266), and the BC Budget 2026 assumes an SPF 2x4 price of US$467 (2025) and US$470 (2026) per thousand board feet.

## 2. Jobs and output in burned regions

Statistics Canada tables 14-10-0387/0391/0392 (LFS by economic region), 14-10-0202 (SEPH by industry) and 36-10-0402 (GDP by industry and province) could not be downloaded (site down, see 1b), so the national economic-region comparison and the forestry-and-logging GDP series 2016 to 2025 are not done. What follows uses official data that did download: BC Stats' republication of the LFS for BC (annual averages 2016 to 2025 and 3-month moving averages to September 2026, by economic region; BC employment by detailed industry 1987 to 2025), the 2021 Census industry counts aggregated to economic regions, and burned area per 2021 economic region (all provinces).

Burned share of land by economic region, 2023 to 2026 (distinct area, official-scaled; `er_burned_by_year.csv`, all 76 ERs)
- Saskatchewan Northern 22.5% (5.91 M ha); BC Northeast 15.3%; Alberta Wood Buffalo--Cold Lake 13.2%; Alberta Athabasca--Grande Prairie--Peace River 12.4% (forestry 5.1% of 2021 employment, 6,130 forestry jobs); NWT 7.9%; Manitoba North 6.5%; Nord-du-Québec 6.4% (forestry 5.7%); Banff--Jasper--Rocky Mountain House 6.0%; BC Thompson--Okanagan 5.9%; BC Lower Mainland--Southwest 5.0%; Abitibi-Témiscamingue 4.8% (forestry 5.1%); BC Nechako 3.7% (forestry 15.7%, the most forestry-dependent ER in Canada); Ontario Northwest 3.4% (forestry 4.1%); BC Cariboo 2.3% (forestry 11.3%).
- 2021 Census forestry jobs (NAICS 113, 1153, 321, 322) by ER are in `er_census_jobs_2021.csv` (CD-to-ER map in `work/cd_to_er_2021.csv`, all 293 CDs matched).

BC difference-in-differences (descriptive; `bc_er_did.csv`, `bc_er_employment.csv`)
- Treated: the five interior and northern ERs (Thompson--Okanagan, Kootenay, Cariboo, North Coast and Nechako, Northeast), 2.0% to 15.3% of land burned in 2023 to 2026 and 3% to 11% of employment in forestry. Control: Vancouver Island and Coast (0.3% burned) and Lower Mainland--Southwest (5.0% burned, almost all in thinly populated Squamish-Lillooet and the Fraser Canyon; 0.8% forestry).
- Employment, 2016 to 2019 average to 2023 to 2025 average: treated +5.6% (523,400 to 552,500), control +14.3% (2.056 M to 2.350 M). Difference: 8.7 percentage points lower growth in the burned interior.
- The gap is not attributable to fire. The treated-to-control employment ratio was flat from 2016 to 2021 (0.251 to 0.263), then fell every year from 2022 (0.249) to 2025 (0.230), starting before the 2023 season and continuing at the same pace through low-fire 2024. It coincides with BC forest-industry contraction (BC forestry, wood and paper employment fell from 61,200 in 2016 to 42,800 in 2024 and 47,400 in 2025; forestry and logging alone from 18,900 to 14,700) and with metro population growth. US softwood duties and mill closures for fibre supply are confounders this design cannot separate.
- By region (post vs pre, minus control): Northeast -18.9 points (the most burned, 15.3%), Cariboo -16.5, North Coast and Nechako -13.7, Kootenay -4.2, Thompson--Okanagan -3.3. The ranking follows forestry dependence at least as closely as burned share (Cariboo and Nechako are the two most forestry-dependent ERs in Canada; Thompson--Okanagan burned 5.9% but changed least).
- 2026 season (January to September 3-month moving averages, 2026 vs the same months of 2025): treated +2.0%, control -1.1%. No sign of a 2026 fire shock in BC employment; Cariboo +9.7%, Thompson--Okanagan +1.8%, North Coast and Nechako -4.0%, Northeast -3.5%. LFS estimates for regions of 35,000 to 90,000 workers carry sampling error of several percent.

Jobs exposed (from `analysis/economy`, 2021 Census, constant): 43,425 forestry jobs in the 66 census divisions with 100 ha or more burned in 2026 and 75,035 in the 120 such divisions in 2023 to 2026; 10,775 forestry jobs in divisions with 1% or more of land burned in 2026 against 80 to 14,975 a year in 2016 to 2022. These are exposure counts, not job losses.

## 3. Tourism: park attendance

Method: Parks Canada attendance by place and fiscal year (April to March, 2001-02 to 2025-26). Fire season Y falls in fiscal year Y to Y+1; the 2026 season (FY2026-27) is not yet published. Burned hectares per national park come from the burned 240 m cells inside the CLAB legislative boundaries. Baseline = mean of the pre-COVID FY2017-18 to 2019-20, excluding any of those years in which the park itself burned 1,000 ha or more. Control = the 84 places reported in every year 2016-17 to 2025-26 (22.2 M visits in FY2024-25). "Excess" = park change relative to the network change.

Findings
- Jasper (2024 fire, 31,637 ha mapped inside the park; town evacuated July 2024): FY2024-25 attendance 1,142,080 against a baseline of 2,445,096, down 53.3% (1.30 M fewer visits), while the network fell 2.7%; 52% below the network trend. FY2025-26 recovered to 2,392,849 (2.1% below baseline, 10% below the network, which rose 9%).
- Wood Buffalo (709,974 ha burned in 2023; 34,525 ha in 2024; 36,881 ha in 2025; 120,079 ha in 2026): FY2023-24 1,503 visits, FY2024-25 1,141 and FY2025-26 2,412, against 4,002 in FY2017-20 (down 62%, 71% and 40%). Every baseline year also had over 1,000 ha burned in the park, so the baseline itself is a fire-affected one.
- Prince Albert (10,673 ha burned in 2025): FY2025-26 214,085 visits, 26.6% below its baseline (291,521) while the network rose 7.7%, 32% below trend. In 2018 (18,436 ha) the drop was 7.3%.
- Nahanni (42,337 ha in 2021): FY2021-22 251 visits against 770 (down 67%); the 2023 (52,501 ha) and 2024 (24,476 ha) fires show no drop (736 and 836).
- Waterton Lakes (19,162 ha, Kenow fire, September 2017): FY2017-18 568,807 visits, 31% above a baseline built from the two following years (the fire came late in the season and the park then had reduced access, so the baseline is the depressed post-fire years).
- Parks with small 2023 to 2026 burns show no measurable change: Glacier 2023 (1,540 ha) 4.1% below baseline; Riding Mountain 2025 (1,103 ha) 4.3% below.
- Ontario Parks (calendar years 2020 to 2025): the Northwest zone, where the 2025 and 2026 Ontario fires burned, had 896,466 visits in 2025, 9.9% above 2023 (815,550), while all other zones rose 15.6%. The ministry's own notes record fire closures at Quetico and Woodland Caribou in 2021 (Woodland Caribou 203 visits in 2021 against 1,831 to 4,269 in 2022 to 2023). The 2024 Woodland Caribou value (227,840) equals the "All" row value and is an evident data error. 2026 is not yet published.
- Not found as open data: BC Parks attendance after FY2010-11, Alberta, Saskatchewan, Manitoba and Quebec provincial park attendance.

Files: `parks_attendance_long.csv`, `parks_burned_ha_by_year.csv`, `parks_fire_attendance.csv`, `ontario_parks_zone_visitation.csv`, `ontario_parks_nw_parks.csv`.

## 4. Total cost tally 2016 to 2026

Components (2025 dollars, millions; blank = no data). Documented spending and losses (A to D) and valuations (E, F) are shown separately and summed only in the last column.

| Year | Firefight (4 prov) | Fed NRCan | DFAA | Insured | A to D | Timber | Health Chen | Health AQBAT | All (Chen) |
|---|---|---|---|---|---|---|---|---|---|
| 2016 | 740 |  | 599 | 4,604 | 5,944 | 191 |  |  | 6,135 |
| 2017 | 1,382 |  |  | 164 | 1,545 | 2,320 |  |  | 3,865 |
| 2018 | 1,401 |  |  |  | 1,401 | 4,912 | 2,989 | 1,146 | 9,302 |
| 2019 | 1,092 | 1 |  |  | 1,093 | 390 | 386 | 151 | 1,869 |
| 2020 | 642 | 2 |  |  | 644 | 197 | 1,061 | 420 | 1,902 |
| 2021 | 1,519 | 3 |  | 208 | 1,730 | 6,883 | 3,202 | 1,220 | 11,815 |
| 2022 | 602 | 35 | 27 |  | 664 | 860 | 628 | 235 | 2,152 |
| 2023 | 2,455 | 58 | 829 |  | 3,342 | 7,777 | 9,456 | 3,629 | 20,575 |
| 2024 | 1,932 | 89 | 188 | 1,331 | 3,540 | 1,567 | 2,486 | 944 | 7,593 |
| 2025 | 2,060 | 144 | 13 |  | 2,217 | 2,073 | 5,531 | 2,094 | 9,821 |
| 2026 | 829 | 139 |  | 286 | 1,254 | 1,554 | 2,425 | 942 | 5,233 |
| 2023 to 2026 | 7,276 | 431 | 1,029 | 1,617 | 10,353 | 12,971 | 19,898 | 7,609 | 43,222 |
| 2016 to 2022 mean (years with data only) | 1,054 | 10 | 313 | 1,658 | 1,860 | 2,251 | 1,653 | 635 | 5,292 |

Component definitions
- A. Provincial firefighting, four provinces with consistent series: BC (BCWS total wildfire cost; 2025 is BCWS's estimated suppression cost as of 2025-11-01; 2026 is the Fire Management fiscal-year forecast, Budget 2026 vote $235.7 M plus a $614 M First Quarterly Report overrun, a broader line, nominal $849.7 M); Ontario (Emergency Fire Fighting, net of recoveries, Public Accounts); Alberta (all wildfire program lines, voted actuals; 2022 not in the source file); Saskatchewan (SPSA season wildfire costs, published already in 2025 dollars). Other jurisdictions have no comparable series (Manitoba 2025: $179 M spent to the Q1 update plus a $129 M forecast overrun; NWT supplementary appropriations of $75 M in 2023 and $39.5 M in 2025; not added).
- B. Federal NRCan wildland-fire contribution agreements (Grants and Contributions disclosure, 148 agreements, $728.6 M in total): Fighting and Managing Wildfires in a Changing Climate $248.9 M (51 agreements), National Aerial Wildfire Capacity (CIFFC, signed 2026-02-19, to 2031) $316.8 M, FireSmart $91.0 M, Foundational Wildland Fire Knowledge $41.8 M, Wildland Fire Resilience $14.5 M, Centre of Excellence $11.7 M, Indigenous Fire Knowledge $3.9 M. Agreement values are multi-year commitments; the tally spreads each evenly over its term (an allocation assumption). Signed by fiscal year of start: 2022 $147 M, 2023 $107 M, 2024 $135 M, 2025 $333 M.
- Federal budget measures (allocations quoted, not added because they are multi-year and overlap B): Budget 2022 "$269 million over five years ... to help provinces and territories procure firefighting equipment"; Budget 2022 "$346.1 million to train 1,000 fire fighters and provide them with new equipment, and $169.9 million to create a new wildfire satellite monitoring system"; Budget 2024 cites "$260 million" from the 2023 Fall Economic Statement "to support wildfire responses and recovery activities in First Nations communities"; Budget 2025 "$257.6 million over four years, starting in 2026-27, to Natural Resources Canada to lease four aircraft". Military deployments (Operation LENTUS) have no open cost series.
- C. Federal DFAA: CDD federal DFAA payments for 2016 ($468.7 M nominal, Fort McMurray); the CDD records 0 for 2017 to 2021, which means not recorded, not zero. 2022 to 2025: DFAA Provincial Emergency Financial Assistance Orders for "interface fires" (values at agreement date): 2022 $24.7 M, 2023 $793.3 M, 2024 $183.9 M, 2025 $12.5 M (incomplete). No 2026 order yet.
- D. Insured losses: CDD insurance payments (Fort McMurray 2016 $3.6 B, BC 2017 $130 M, Lytton and Central Okanagan 2021 $179 M, nominal) and CatIQ industry estimates (Jasper 2024 $1.304 B final; Bald Range 2026 $293 M at 45 days). No public wildfire-only figure exists for 2018 to 2020, 2022, 2023 or 2025.
- E. Value of standing timber burned at Crown stumpage (section 1). A valuation, not a cash cost.
- F. Health: modelled net acute smoke deaths from `analysis/health` multiplied by Health Canada's AQBAT value of a statistical life, $9,158,296 (2023 CAD; low $4,931,390, high $13,385,201), published by Health Canada authors in Matz et al. 2026 (GeoHealth, doi 10.1029/2025GH001565, Table S2, mortality valuation from Chestnut and De Civita 2009), converted to 2025 dollars. Health model years are 2018 to 2026; 2025 and 2026 cover 9 provinces and territories (not MB, NL, NT, NU). This is a valuation of modelled deaths, not spending, and covers acute mortality only (no morbidity, no chronic exposure). The Treasury Board Cost-Benefit Analysis Guide could not be retrieved (canada.ca connections reset; publications.gc.ca archive page returned HTTP 502), so its VSL is not used.
- Cross-check: Matz et al. (Health Canada) value acute premature deaths at $3.6 B for 2023 (2023 CAD); our AQBAT-coefficient deaths x the same VSL give $3.47 B (2023 CAD; $3.63 B in 2025 dollars). For 2019 to 2022 our AQBAT values are lower than theirs ($0.15 B to $1.22 B in 2025 dollars against their $0.45 B to $2.5 B), because our exposure model gives fewer deaths in those years.

Findings
- Provincial firefighting (four provinces) averaged $1.05 B a year in 2016 to 2022 and $2.15 B a year in 2023 to 2025, 2.0 times as much; 2023 was the highest at $2.46 B (BC $1.14 B, Alberta $1.00 B, Ontario $216 M, Saskatchewan $98 M). Saskatchewan 2025 ($352 M) was 3.6 times its previous high (2021, $110 M).
- Documented spending and losses (A to D): $3.34 B in 2023, $3.54 B in 2024 (Jasper insured loss $1.33 B), $2.22 B in 2025, and $1.25 B so far for 2026 (BC firefighting, federal programs and one early insured estimate only). 2016 remains the largest year at $5.94 B because of Fort McMurray.
- With valuations (timber at stumpage and smoke deaths, Chen coefficient): $20.6 B in 2023, $7.6 B in 2024, $9.8 B in 2025 and $5.2 B so far in 2026; $43.2 B for 2023 to 2026. 2016 to 2022 averaged $5.3 B a year (with health only from 2018).
- The valued smoke deaths are the largest single component in 2023 ($9.46 B Chen; $3.63 B AQBAT), larger than timber ($7.78 B) and than all documented spending and losses ($3.34 B).
- For 2026 most cash components are not yet published (see the coverage table); the 2026 total is a floor.

Coverage (yes = value present; missing = not published or not found)

| Year | BC | ON | AB | SK | Fed NRCan | DFAA | Insured | Timber stump | Timber roundwood | Health |
|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | yes | yes | yes | yes | missing | yes | yes | yes | missing | missing |
| 2017 | yes | yes | yes | yes | missing | missing | yes | yes | missing | missing |
| 2018 | yes | yes | yes | yes | missing | missing | missing | yes | missing | yes |
| 2019 | yes | yes | yes | yes | yes | missing | missing | yes | missing | yes |
| 2020 | yes | yes | yes | yes | yes | missing | missing | yes | missing | yes |
| 2021 | yes | yes | yes | yes | yes | missing | yes | yes | missing | yes |
| 2022 | yes | yes | missing | yes | yes | yes | missing | yes | missing | yes |
| 2023 | yes | yes | yes | yes | yes | yes | missing | yes | missing | yes |
| 2024 | yes | yes | yes | yes | yes | yes | yes | yes | missing | yes |
| 2025 | yes | yes | yes | yes | yes | yes | missing | yes | missing | yes |
| 2026 | yes | missing | missing | missing | yes | missing | yes | yes | missing | yes |

Notes: Health starts in 2018 (exposure model years). Insured "missing" means no public wildfire-only figure. DFAA 2017 to 2021 are blank in the CDD (not zero), 2025 is incomplete and 2026 has no order yet. Roundwood value is missing for every year because Statistics Canada was unreachable (section 1b).

Files: `cost_tally_by_year.csv` (wide, 2025 dollars), `cost_tally_long.csv` (every value with nominal amount, status and source; health rows carry low and high), `cost_tally_coverage.csv`, `federal_wildfire_programs_agreements.csv`, `federal_wildfire_programs_by_year.csv`, `raw/federal_budget/budget_wildfire_sentences.json`.

## Caveats

1. Timber volumes come from the 2011 kNN map on 240 m cells; 2026 uses coarse M3 outlines scaled to official area. Values are standing timber at Crown stumpage, not lost harvest.
2. Stumpage for 2025 and 2026 (outside BC) carries 2024 NFD rates; Ontario 2020 to 2022 and 2024 onward and New Brunswick after 2021 are filled as stated. Alberta and Saskatchewan dues move with lumber prices, so carried values can be off in either direction.
3. Tenure overlays use centre-in-polygon on 240 m cells; Ontario FMU geometry was generalised by about 50 m on download.
4. Firefighting series differ in scope by province (BC includes all BCWS costs; Ontario only emergency firefighting net of recoveries; Alberta all program lines; Saskatchewan agency season costs). They are summed as published, not harmonised.
5. Federal agreement values are commitments, not disbursements, and the straight-line spread is an assumption. DFAA order values are interim and arrive one to two years after the event.
6. Insured losses are industry figures (CatIQ) or CDD compilations, for named events only.
7. Health valuations apply one VSL to modelled deaths; they are valuations for comparison, not costs anyone paid.
8. Park attendance is affected by closures, access, weather, prices and travel trends; the network control removes only system-wide shifts.
