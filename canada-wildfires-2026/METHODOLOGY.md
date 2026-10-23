# Methodology: Canada's wildfires, 2023 to 2026

Every number on the page and in the carousel comes from code and outputs in this repository. This file says how each one was made, where it is read from, how it was checked, and how to challenge it.

- Reproduce: [REPRODUCE.md](REPRODUCE.md). Data sources and licences: [data/SOURCES.md](data/SOURCES.md). Independent check of every claim: [methods/verification.md](methods/verification.md).
- Files kept out of the repo because of size, with how to regenerate each: [methods/skipped_files.csv](methods/skipped_files.csv).
- The analysis was run 2026-10-20 to 2026-10-22. Fire data run to 2026-10-20, smoke data to 2026-10-19. 2026 figures are preliminary.

## Contents

1. [Summary](#1-summary)
2. [Every published claim](#2-every-published-claim)
3. [How numbers flow to the page](#3-how-numbers-flow-to-the-page)
4. [Shared building blocks](#4-shared-building-blocks)
5. Analyses (5.15 readiness, 5.16 government response, 5.17 coverage check, 5.18 the bill, 5.19 page and slides): [forest](#51-forest-area-burned-share-of-forest-ranks-records) · [outline check](#52-outline-check-which-2026-outlines-are-not-wildfires) · [weather](#53-weather-station-fire-weather-2026) · [climate](#54-climate-winter-to-spring-chain) · [climate change](#55-climate-change-warming-drying-and-a-counterfactual) · [cause](#56-cause-ignitions-drought-and-the-expected-vs-actual-model) · [wildlife](#57-wildlife-caribou-ranges-and-protected-areas) · [people](#58-people-who-lived-near-fire-smoke-days-cost-per-resident) · [health](#59-health-smoke-exposure-and-modelled-deaths) · [losses](#510-losses-deaths-evacuations-buildings-payments) · [property](#511-property-buildings-likely-destroyed-and-their-value) · [economy](#512-economy-timber-carbon-jobs-infrastructure-scale) · [economic value](#513-economic-value-what-it-cost) · [threads](#514-threads-emissions-gap-reburns-overwintering-repeat-exposure-prescribed-fire-water)
6. [Independent verification](#6-independent-verification)
7. [How to challenge a number](#7-how-to-challenge-a-number)
8. [Things the files do not make clear](#8-things-the-files-do-not-make-clear)

## 1. Summary

**What we measured.** How much of Canada burned in 2023 to 2026 against every year since 1972, where it burned, what the weather, drought, ignitions and warming looked like, how far the burn went beyond what those drivers predict, who lived near the fires and breathed the smoke, what was destroyed, and what it cost.

**Data.** Raw public data only: NRCan fire perimeters (NBAC 1972 to 2025, CWFIS FireM3 2026 outlines), official agency totals (CWFIF/CIFFC, National Forestry Database), satellite hotspots, Land Cover of Canada 2020, ECCC climate and air-quality stations, AAFC Canadian Drought Monitor, Statistics Canada 2021 Census, Health Canada coefficients, TSB, Public Safety, ISC, provincial public accounts, Copernicus Sentinel-2, Microsoft building footprints, and others (250 rows in [data/SOURCES.md](data/SOURCES.md)). No number comes from news or third-party analysis; industry insured-loss estimates (CatIQ, IBC) are labelled as such.

**Main modelling choices.**

| Choice | What we did |
|---|---|
| 2026 burned area | CWFIS FireM3 hotspot outlines, scaled per province to the official total (they map about 18% more than official nationally) |
| Earlier years | NBAC polygons 1972 to 2025 (satellite-mapped); NFD official totals 1990 to 2025 for rankings |
| Forest | Land Cover 2020 classes 1, 2, 5, 6 on a 240 m grid; 349.4 M ha in Canada |
| Areas | 186 fire management areas (`data/geo/fma_v2.gpkg`); Quebec and Manitoba split into agency zones; Parks Canada folded into provinces |
| Non-wildfire outlines | A rule fixed before the evidence was computed classes all 718 2026 outlines; 16 are farm/grass or military; 13 unreported ones are dropped from distance analyses |
| Warming effect | Poisson panel regression of hectares burned on May to August temperature and rain, area fixed effects, 1972 to 2025; counterfactual removes the measured warming |
| Expected vs actual | Ridge regression on within-area anomalies (drought, fire weather, ignitions, fuel), trained 2003 to 2022 |
| Smoke | Nearest NAPS/AirNow station within 50 km for every dissemination area and day |
| Smoke deaths | Two published coefficients (Health Canada AQBAT 0.7%, Chen et al. 2021 1.9% per 10 ug/m3) applied to the smoke increment; modelled estimates, not counts. **Not shown on the page or the slides** (October 22, 2026): deaths are counted by coroners and no study reports wildfire smoke deaths for 2023 to 2026, so the modelled series is kept in `analysis/health/` for the record only |
| Emergency room visits | CIHI monthly ED visits (April 2021 to March 2026, 9 provinces and territories) regressed on the monthly smoke increment; extra visits = visits x (1 - 1/exp(beta x increment)), with the 95% interval of beta as the range (`analysis/health/scripts/09_ed_extra_visits.py`) |
| Readiness | 2026-27 base wildfire budget divided by the mean of 2023-24, 2024-25 and 2025-26 actual spending, from each government's own estimates and public accounts (section 5.15) |
| Buildings destroyed | Sentinel-2 dNDVI/dNBR rule calibrated on Jasper's official structure layer (precision 0.836, recall 0.832, 5-fold spatial CV) |
| Money | Provincial public accounts, federal disclosures, industry insured losses, timber at Crown stumpage, modelled deaths at Health Canada's value of a statistical life; kept in separate columns |

## 2. Every published claim

Values are the verified values from `story/verified_numbers.json`. "Status" is the verifier's verdict ([methods/verification.md](methods/verification.md) has the full reasoning). Paths are relative to `analysis/` unless they start with `data/`. C1b and X (counts the page text uses) are derived inside `scripts/build_story_json.py` from the same files; see section 3.

| ID | Claim (verified value) | Script | Output read | Status and note |
|---|---|---|---|---|
| C1 | Top four years since 1972 by share of forest burned: 2023 2.61%, 2025 1.39%, 2026 1.04%, 2024 0.93% (next 1989 0.81%) | forest/scripts/04_fma_forest.py | forest/canada_forest_share_by_year.csv, canada_totals.csv | Confirmed. 2026 mapped; scaled 0.88% puts it behind 2024, still top four |
| C2 | 2023 to 2026 burned 5.95% of Canada's forest (20.78 M ha), 1 ha in 17 | forest/scripts/04_fma_forest.py; economy/scripts/09_scale.py | forest/canada_totals.csv, economy/scale_comparisons.csv | Confirmed. Union, mapped forest basis |
| C3 | Highest earlier 4-year window 2.06% (1979 to 1982) | forest/scripts/04_fma_forest.py | forest/canada_forest_share_by_year.csv | Confirmed. Sum of annual shares; compare with 5.97% (sum), not 5.95% (union) |
| C4 | 35.79 M ha of distinct land burned 2023 to 2026, about Germany | forest/scripts/04_fma_forest.py; economy/scripts/09_scale.py | economy/scale_comparisons.csv | Corrected wording: distinct land, official-scaled; official 4-year sum is 35.91 M ha |
| C5 | 2026 official 4.50 M ha, 8th of 37 years (NFD 1990 to 2026) | forest/scripts/01_rankings.py | forest/ranking_canada.csv | Confirmed. Also 8th excluding Parks Canada; 9th of 55 on NBAC |
| C6 | May to August 2016 to 2026 was 1.15 C warmer than 1961 to 1990 (0.80 to 1.49) | climate-change/scripts/03_season_climate.py | climate-change/climate_recent_vs_normal.csv | Confirmed. Forest-weighted mean of areas |
| C7 | All 236 long-record stations warmed | climate-change/scripts/03_season_climate.py | climate-change/station_trends.csv | Confirmed on Theil-Sen (220 significant); 234 of 236 positive by OLS |
| C8 | +1 C May to August = +43.6% area burned (30.1% to 61.7%) | climate-change/scripts/09_sensitivity_counterfactual.py | climate-change/model_coefficients.csv | Confirmed. Within-area relation (M1) |
| C9 | Warming alone: 2023 to 2026 burn 1.53 times the 1961 to 1990 expectation (1.37 to 1.76), about a third | climate-change/scripts/09_sensitivity_counterfactual.py | climate-change/counterfactual_2023_2026.csv | Confirmed. 1.34 to 1.60 across models |
| C10 | April to September rain 2023 to 2026 was 84% of normal, driest 4-year window since 1950 | climate-change/scripts/03_season_climate.py | climate-change/climate_ranks_2023_2026.csv | Confirmed. Rank 1 of 74 |
| C11 | No long-term trend in April to September rain (+0.04 points per decade, p 0.93) | climate-change/scripts/03_season_climate.py | climate-change/climate_trends.csv | Confirmed |
| C12 | Forest in moderate drought or worse at some point April to September: 2023 55.4%, 2024 54.6%, 2025 75.1%, 2026 56.7%; 2003 to 2022 mean 14.8%, max 34.9% | cause/scripts/10_run_2023_2026.py | cause/run_driver_summary.csv | Corrected: draft used pre-rebuild values (53.7, 53.8, 72.2, 55.8; 14.4, 32.7) |
| C13 | 2026 lightning fires 2,960 vs 1991 to 2020 mean 3,245; human 2,190, fewest of 37 years | cause/scripts/04_cause.py | cause/cause_by_year_national.csv | Confirmed. NFD-comparable basis (no Parks Canada) |
| C14 | Lightning started 54.7% of 2026 fires, burned 95.0% of area | cause/scripts/04_cause.py | cause/cause_2026_by_agency.csv | Confirmed. Official basis with Parks Canada (3,019 lightning fires) |
| C15 | Model trained 2003 to 2022 predicted 2023 to 2026 at 0.36% vs 5.85% actual: 16.3 times (14.1 before rebuild); 5.2 times beyond its usual miss | cause/scripts/10_run_2023_2026.py | cause/run_model_check.csv | Confirmed. LOYO calibration ratio 3.1 |
| C16 | July 16, 2026: population-weighted PM2.5 67.0 ug/m3, smokiest day in the 2018 to 2026 record (previous 52.5, June 25, 2023) | health/scripts/03_exposure.py, 08_summary_tables.py | health/worst_days.csv | Corrected wording: the record starts in 2018 |
| C17 | 11,706,139 Ontarians had at least one day above 100 ug/m3 in 2026 | health/scripts/03_exposure.py | health/exposure_by_group.csv | Confirmed. May to September, 50 km assignment |
| C18 | (Not shown on the page or slides.) Modelled smoke deaths 2026: 98 (AQBAT) to 253 (Chen); 2023: 379 to 988 | health/scripts/05_modelled_deaths.py | health/modelled_acute_deaths_national.csv | Corrected: 2025 and 2026 exclude MB, NL, NT, NU; same-province 2023 is 362 to 943 |
| C19 | Direct deaths: 2023 1, 2024 1, 2025 2, 2026 7 (3 TSB aviation, 4 CAF members at CFB Wainwright) | losses/scripts/03_tsb.py (see note); `WAINWRIGHT_DEATHS` in scripts/build_story_json.py | losses/tsb_firefighting_occurrences.csv; DND release of Oct 18, 2026 | Corrected: the script sums the TSB injuries table and double counts; verified values use occurrence-level TotalFatalCount (2026 = A26W0082, 3 deaths). Updated 2026-10-22: the build adds the 4 Canadian Armed Forces members killed in the CFB Wainwright fire on Oct 17, 2026 (Department of National Defence), which are not an aviation occurrence |
| C20 | (Not shown on the page or slides.) Modelled smoke deaths outnumber direct deaths about 70 to 190 to one (pooled 795 to 2,079 smoke deaths over 11 direct deaths, 72.3 to 189.0, rounded to 10) | scripts/build_story_json.py (computed from the deaths series) | health/modelled_acute_deaths_national.csv; C19 | Corrected from "50 to 200"; verified as 114 to 297 before the Wainwright deaths were added on 2026-10-22, now recomputed in the build from the same smoke series |
| C21 | On reserve 3.3% vs off reserve 0.11% lived within 10 km of a 1,000 ha+ fire in 2 or more years (30.6 times) | threads/scripts/t4_repeat_exposure.py | threads/t4_repeat_exposure_summary.csv | Confirmed. On-reserve counts are lower bounds |
| C22 | Seven First Nation communities within 10 km of fire in all four years | threads/scripts/t4_repeat_exposure.py | threads/t4_fn_communities_years_exposed.csv | Confirmed. Any fire size; none at 200 ha+ |
| C23 | Buildings flagged likely destroyed: 2023 844 (4 events), 2024 417 (Jasper, in-sample), 2025 405 (2 events), 2026 517 (all outlines); precision 0.836, recall 0.832 | property/scripts/06_calibrate.py, 07_apply_rule.py, 15_apply_2026.py | property/calibration_accuracy.csv, estimates_2026_by_fire.csv, property/results.md event table | Corrected: event subsets, not national totals |
| C24 | Bald Range 2026: 168 flagged (154 to 185) vs about 150 official | property/scripts/15_apply_2026.py, 10_events_official.py | property/estimates_2026_by_fire.csv, events_official.csv | Confirmed |
| C25 | 9,503 km of roads and 686 km of rail inside burned areas 2023 to 2026 | economy/scripts/05b_infra_by_year.py | economy/infra_by_year.csv (also property/infrastructure_by_year.csv) | Confirmed. Mapped footprints, length inside, not damage |
| C26 | About $0.92 B dwelling value (census proxy) for structures lost or damaged at seven events with official counts | property/scripts/13_value_destroyed.py | property/destroyed_value_official.csv | Corrected wording: counts mix homes, structures and "damaged or destroyed" |
| C27 | Timber burned in 2023 at Crown stumpage $7.44 B, 7.2 times the $1.03 B stumpage collected | economic-value/scripts/05_timber_value.py | economic-value/timber_value_canada_year.csv | Confirmed. Value of standing timber, not a loss |
| C28 | Firefighting BC+ON+AB+SK $1.05 B a year 2016 to 2022 vs $2.15 B 2023 to 2025 (2025 dollars) | economic-value/scripts/07_cost_tally.py | economic-value/cost_tally_by_year.csv | Confirmed. 2022 lacks Alberta; 2016 to 2021 baseline gives 1.9 times |
| C29 | 2023 to 2026 all components $43.2 B (Chen); documented spending and losses at least $10.35 B | economic-value/scripts/07_cost_tally.py | economic-value/cost_tally_by_year.csv | Confirmed. With AQBAT $30.9 B; 2026 partial |
| C30 | 2023 to 2026 burned 11.2 years of the 2024 harvest (1,336 M m3) | economy/scripts/07_timber_carbon.py, 09_scale.py | economy/scale_comparisons.csv | Confirmed. Scaled union |
| C31 | Managed-forest wildfire emissions 2023: 870 Mt CO2e, 127% of the 686.9 Mt national total, which excludes them | threads/scripts/t1b_emissions_gap.py | threads/t1_official_inventory_lines.csv | Confirmed. NIR values rounded to 2 significant figures |
| C32 | Short-interval reburn in black spruce/jack pine: 2.3% (1990s) vs 7.5% (2023 to 2026); 36,282 vs 343,906 ha a year | threads/scripts/t2_reburn.py | threads/t2_reburn_by_period.csv | Confirmed. 15-year window |
| C33 | 14 of 51 federal boreal caribou ranges over 35% burned by fire 1987 to 2026 | wildlife/scripts/06_tables.py | wildlife/caribou_ranges_2026.csv | Confirmed. All 14 were over 35% before 2026 |
| C34 | Thunder Bay area 12.8% of its forest (mapped; 11.2% scaled), 88 times its 1991 to 2020 average, a record | forest/scripts/04_fma_forest.py | forest/fma_2026_table.csv | Confirmed |
| C35 | 9 fire areas set records on the scaled basis (12 mapped) | forest/scripts/04_fma_forest.py | forest/fma_2026_table.csv | Confirmed. Laforge-2 rests on M3 shapes |
| C36 | Waskaganish (QC zone 50) 10.5% mapped, 9.7% scaled, 110 times average, not a record | forest/scripts/04_fma_forest.py | forest/fma_2026_table.csv | Confirmed |
| C37 | 70.5% of 2026 satellite detections fell June 22 to July 26 | forest/scripts/05_hotspots.py | forest/hotspot_peak5.csv | Confirmed. 69.7% without Sentinel-3 SLSTR |
| C38 | 23 of BC's 466 community watersheds over 10% burned; 29 population centres (106,904 people) in national watersheds over 10% burned | threads/scripts/t6b_bc_water.py, t6_watersheds.py | threads/t6_bc_community_watersheds_summary.csv, t6_watershed_summary.csv | Confirmed. Burned watershed is not an affected supply |
| C39 | Jasper visits FY2024-25 down 53.3% vs pre-COVID baseline; network down 2.7% | economic-value/scripts/04_parks.py | economic-value/parks_fire_attendance.csv | Confirmed |
| C40 | Kamloops A: 118 extreme fire-weather days in 2026 vs normal 59.6, a record (previous 110) | weather/scripts/03_station_area_metrics.py | weather/station_extreme_days.csv | Confirmed. Replacement station ID runs about 4.6 days high; still a record when adjusted |

## 3. How numbers flow to the page

```
raw public data (data/SOURCES.md)
  -> analysis/<topic>/scripts/*.py
  -> analysis/<topic>/*.csv              (one output file per table; results.md describes them)
  -> story/verified_numbers.json          (an independent reader checked each claim against the CSVs;
                                           methods/verification.md)
  -> scripts/build_story_json.py          (copies the verified values, adds chart series read
                                           directly from the analysis CSVs, derives C1b and X)
  -> data/story.json                      -> index.html (the page reads only data/*.json)
  -> slides/make_slides.py                (reads verified_numbers.json and the same CSVs)
                                          -> the nine carousel PNGs
```

- `story/claims_draft.md` lists each claim with the folder its number should come from. A separate verification pass read every cited file, recomputed with short pandas checks where noted, and recorded the verified values and any corrections in `story/verified_numbers.json` and `methods/verification.md`. Those checks were done interactively and are not saved as scripts; each row in section 2 names the file and column needed to redo them.
- `scripts/build_story_json.py` reads `verified_numbers.json` when it exists (draft values otherwise, with the same keys). Chart series (yearly forest share, area burned, warming, run drivers, model check, smoke deaths, infrastructure, costs, emissions, reburns, caribou, weekly hotspots) are read from the CSVs at build time, not typed in.
- C1b (four-year hectare totals) and X (counts used in the page text, for example the number of fire areas and cities) are computed in `build_story_json.py` from `forest/canada_forest_share_by_year.csv`, `data/smoke-cost/fire_area_count_by_agency_year.csv`, `forest/fma_2026_table.csv`, `people/city_search_table.json` and `forest/scaling_factors_by_province.csv`.
- Map layers: `scripts/fma_union.py` (per-area 2023 to 2026 union, writes `site-build/fma_union_2023_2026.csv`) and `scripts/build_map.py` (TopoJSON via mapshaper). City search: `scripts/build_cities.py`.

## 4. Shared building blocks

### 4.1 Fire footprints

- **2026:** CWFIS FireM3 perimeters stamped 2026-10-20 (718 outlines; `data/fire/m3_perimeters_2026_cwfis_20261020.gpkg`). They are buffered hotspot outlines that include unburned islands. Equal-area geometry totals 5,303,030 ha, 17.8% above the official 4,500,985 ha.
- **1972 to 2025:** NBAC polygons, version 20260513 (Landsat-mapped). Prescribed burns are removed where the analysis says so (people, losses).
- **Official totals:** CWFIF/CIFFC year-to-date by agency as of 2026-10-20 (`data/fire/reference/nrcan_ytd_by-agency.json`), NFD 1990 to 2025 (`data/smoke-cost/fire_area_count_by_agency_year.csv`).

### 4.2 The 240 m grid and the forest mask

- Land Cover of Canada 2020 (30 m) is aggregated to a 240 m grid in EPSG:3979, holding the count of forest pixels (classes 1 needleleaf, 2 taiga needleleaf, 5 broadleaf, 6 mixed) per cell (`data/geo/scripts/forest_fraction.py`). Shrubland and wetland are excluded.
- Cell counts are converted to true area with the projection's areal scale factor (0.94 to 1.17, evaluated every 25 cells). Rasterised burn areas match equal-area vector areas within 0.2% for every year 1972 to 2026.
- A cell is burned in a year if its centre is inside an NBAC (or M3 for 2026) polygon (`forest/scripts/03_rasterize_burns.py`). These burn indices (`forest/work/burn_YYYY.npy`) are reused by cause, climate, climate-change, economy, threads and the site's per-area union.
- Because the land cover is from 2020, land that burned before 2020 and had not regrown into forest is not counted as forest. This lowers historical forest shares and is one reason recent years can rank high.

### 4.3 Fire management areas (fma_v2) and the rebuild

`data/geo/fma_v2.gpkg` (186 rows) is built in three steps:

1. `data/geo/scripts/build_fma_all.py` merges agency fire-management layers (BC fire centres, Alberta forest areas, Saskatchewan SPSA protection areas, Ontario fire management HQ areas, NWT regions, Yukon fire districts, NL forest management districts) clipped to StatCan 2021 province polygons; provinces without a public layer are one row. Parks Canada parks are separate overlapping rows (146 rows).
2. `data/geo/mb_qc_subareas/scripts/build_mb_qc_subareas.py` builds the Manitoba Wildfire Service fire and travel restriction areas (22 plus a southern remainder) and the SOPFEU fire danger zones (65 plus a far-north remainder) from the agencies' web-map files.
3. `data/geo/scripts/build_fma_v2.py` replaces the single Manitoba and Quebec rows with those zones and removes the 47 Parks Canada rows. Province areas match fma_all to 0.0000%. The crosswalk is `data/geo/fma_v2_crosswalk.csv`.

`analysis/REBUILD.md` documents the 2026-10-21 rebuild onto this layer, with before and after values for every headline. Where a topic's `results.md` text quotes an older number, REBUILD.md is the reference.

### 4.4 Scaling 2026 to official totals

- Per province: factor = official total (agency total plus that province's share of Parks Canada's 124,872.1 ha) / all M3 outline area in the province. Parks Canada's total is allocated to provinces by M3 outline area inside national parks: NT 88.1%, AB 10.9%, MB, BC.
- Factors after the rebuild include AB 1.033, NT 0.822, MB 0.596; NB 0.07 and NS 3.43 are weak (tiny areas). Full table: `forest/scaling_factors_by_province.csv`.
- "Mapped" numbers use outline area directly; "scaled" numbers multiply each cell or hectare by its province factor. Shares of forest burned are ratios of mapped quantities unless labelled scaled. The scaled hectares sum to 4,500,984.5 ha.
- For 2016 to 2025 (economy, threads), factors are NFD official provincial area / NBAC mapped area outside national parks.

### 4.5 Outline classes (the 16 farm, grass and military outlines)

`analysis/outline-check/scripts/rule.py` was written before any evidence was computed and classes every 2026 outline, first match wins: R1 military range (DND share at least 0.50), R2 industrial or urban heat (urban plus barren at least 0.30), R3 wildfire (natural cover at least 0.60 and at least 3 detection days), R4 agricultural or grass burn (cropland plus grassland at least 0.50, at most 3 detection days, first detection March to May or September to November), R5 unclear. 16 of 718 outlines fall in R1 or R4. Thirteen of them have no agency-reported fire and are dropped from every 2026 distance analysis (people, threads); three are agency-reported (two CFB Gagetown fires, one Saskatchewan cropland fire) and kept. The losses building count drops all 16. Burned-area and forest statistics keep all 718. See section 5.2.

### 4.6 Hotspots

CWFIS WFS archive (`public:hotspots`, 294 daily files, 1,352,431 rows to 2026-10-20). Deduplicated to one detection per sensor per 1 km cell (ESRI:102001) per UTC day. Sensors: VIIRS-I, MODIS and Sentinel-3 SLSTR; a sensitivity without SLSTR is reported. No filter for industrial heat.

### 4.7 Population

StatCan 2021 dissemination areas (57,932; 36,991,981 people) with population from table 98-10-0015, each represented by its representative point. On-reserve people are those in DAs whose point lies in an Aboriginal Lands (AL_TA) "Indian Reserve" polygon. 174 DAs have no 2021 count (mostly incompletely enumerated reserves), so on-reserve figures are lower bounds. Distances are geodesic (GRS80).

## 5. Analyses

Each subsection gives the question, data, method, assumptions, limits and what would change the result. Scripts, results and outputs are in `analysis/<topic>/`; every topic's `results.md` has the full findings and its `manifest.csv` lists its downloads.

### 5.1 Forest: area burned, share of forest, ranks, records

**Question.** How does 2026, and 2023 to 2026, rank against every year since 1972, nationally and by fire management area?

**Data.** NBAC 1972 to 2025, M3 2026, NFD 1990 to 2025, CWFIF 2026 totals, NBAC summary workbook, Land Cover 2020, fma_v2, hotspot archive.

**Method.** Scripts run 01, 02b, 02, 03 (then `03 2026`), 04, 05, 06, 07, 08.
1. `01_rankings.py`: rank the official 2026 total among NFD 1990 to 2025 and NBAC 1972 to 2025 annual totals, nationally and by province.
2. `02b_fma_simplified.py`, `02_grid.py`: simplify fma_v2 to 20 m part by part (largest area change 0.69%), rasterise area IDs, park IDs and forest counts onto the 240 m grid.
3. `03_rasterize_burns.py`: burned cell indices per year (section 4.2).
4. `04_fma_forest.py`: per area and year, mapped forest burned / area forest; 1991 to 2020 average share (mean of 30 annual shares); "record" = 2026 share above every year 1972 to 2025, on the mapped basis and with the share multiplied by the province factor (`record_2026_if_scaled`); 2023 to 2026 union (cells counted once); distinct land burned 2023 to 2026 = (union / sum of mapped footprints) x (sum of official totals, NFD 2023 to 2025 plus 2026 official) = 35.79 M ha; reburn shares (2026 footprint burned before since 1972, by time since last burn).
5. `05_hotspots.py`: weekly deduplicated detections and the busiest 5 consecutive weeks (C37).
6. `06_validation.py`: compares the M3 split within provinces against agency perimeters or points (BC, ON, AB, MB perimeters; QC SOPFEU points; NT points), including the Manitoba and Quebec zone splits.
7. `07_reburn_geojson.py`, `08_fma_geojson.py`: map layers.

**Assumptions.** M3 shapes allocate each province's official total correctly among its areas; forest = 2020 forest; the cell-centre rule.

**Limits.** M3 over-maps Manitoba (40% of its burn in Area 18 vs 23% on Manitoba's own perimeters); the Quebec split has only point-based validation (Laforge-2 6.0% by points vs 10.4% by M3), so the Laforge-2 scaled record rests on M3 shapes; zone edges in QC and MB are web-map lines good to about 1 to 5 km; 2026 is preliminary and NBAC 2026 will replace M3.

**What would change the result.** NBAC 2026 (expected spring 2027) replacing M3; revised official 2026 totals; a different forest definition (for example including wetland or shrub).

### 5.2 Outline check: which 2026 outlines are not wildfires

**Question.** Of the 80 M3 outlines with no agency-reported fire within 5 km, which are wildfires and which are farm, grass, military or industrial burns?

**Data.** Land Cover 2020 (30 m), deduplicated hotspots (file plus WFS archive), Alberta DND polygons, Directory of Federal Real Property DND parcels, CWFIF fire list and provincial perimeters and points.

**Method.** Run 01, 03, 02, 04. The rule (section 4.5) was fixed in `rule.py` on 2026-10-21 after only schemas had been inspected, and was not changed after results were seen. It uses only physical evidence; agency records are reported in separate columns. Outside Alberta, DND land is a proxy: each DFRP DND parcel of 100 ha or more is a circle of its land area at its point. A check sample of 80 agency-matched outlines (seed 20261021, stratified to the size quintiles of the unmatched set) tests specificity.

**Results used elsewhere.** Unmatched 80: 30 wildfire (40,266 ha), 9 agricultural or grass (1,456 ha), 4 military (896 ha), 37 unclear. Non-wildfire classes hit 5 of 638 matched outlines (0.8%). `outline_class_2026.geojson` carries the class for all 718.

**Limits.** DND proxy circles misplace irregular bases (one Shilo outline may be misclassed); "military" and "agricultural" describe setting and timing, not cause; the 3-detection-day threshold misses short fires, so "unclear" means too little satellite evidence, not "not a fire".

**What would change the result.** A national DND boundary layer; agency records for the 37 unclear outlines; different thresholds (pre-registered, so not tuned).

### 5.3 Weather: station fire weather 2026

**Question.** Was 2026 fire weather unusual, and where?

**Data.** CWFIS station FWI v3.0 archive 1990 to 2026-09-30 plus daily files to 2026-10-19; CWFIS 2 km daily FWI grids 2018 to 2026.

**Method.** `run_all.sh` runs 00 to 05. Station IDs within 5 km are joined into one site (each day takes the member with the longest record). A site-year qualifies with FWI on at least 90% of June to August days and 75% of May to September days; a site is consistent if it qualifies in 28 of 30 years 1991 to 2020 (116 sites; 103 with usable 2026 data). Extreme day = FWI 30 or more, April 1 to October 19. Normal = the site's mean over qualifying 1991 to 2020 years; record = rank 1 with more than 0 days. Areas take stations by nearest non-park area polygon (simplified 500 m). Grids are a check only (2018 to 2025 baseline).

**Assumptions.** Days without computed FWI (before snow-free start-up) are not extreme.

**Limits.** Long-record stations are mostly southern airports, so eastern boreal fire weather is poorly sampled; 46 of 103 stations take most of their 2026 days from a replacement ID (Kamloops' replacement runs about 4.6 days high; adjusted 2026 is about 113, still above the old maximum of 110).

**What would change the result.** A denser northern network; treating replacement IDs as separate stations (37 stations, pooled ratio 1.24 instead of 1.05).

### 5.4 Climate: winter-to-spring chain

**Question.** Did snow, spring temperature, rain and climate indices line up with where it burned?

**Data.** NOAA CPC and PSL indices (ONI, PDO, AO, NAO), ECCC climate-daily via MSC GeoMet (1,591 climate IDs, 671 sites), CanSWE v8.

**Method.** `run_all.sh` runs 01 to 08; with `AREA_FILE=data/geo/fma_v2.gpkg` area outputs go to `work/areas_<hash>/` (the fma_v2 run is `work/areas_fcd292dde04d/`, included in the repo because the cause model reads its `climate_panel.csv`). Station anomalies are medians per area (stations inside or within 50 km, else the nearest 3 within 250 km). Within-area rank correlation r_w: each variable converted to its percentile among the area's own years, then pooled. p-values from 999 permutations of year labels applied to all areas at once; 95% intervals from 1,000 bootstrap resamples of years; Benjamini-Hochberg q within each test family (294 burn tests, 399 chain tests).

**Limits.** The 10 hPa polar vortex series could not be downloaded (PSL HTTP 503); the AO January to March mean is used as a documented proxy. Quebec rests on southern stations. CanSWE ends in 2025.

**What would change the result.** The real vortex series; northern stations; a longer record (35 years cannot separate a 0.1 to 0.15 correlation from zero).

### 5.5 Climate change: warming, drying and a counterfactual

**Question.** How much has fire-season climate changed, and how much of the 2023 to 2026 burn goes with that change?

**Data.** ECCC AHCCD homogenized monthly temperature (Gen3, to 2023) and adjusted precipitation (Gen2, to 2017), extended with offset-corrected climate-daily; climate-hourly noon observations 1953 to 2026; CWFIS station FWI; NBAC, M3 2026 scaled, CNFDB 1959 to 1971.

**Method.** `run_all.sh`, single-threaded.
1. Stations: 236 temperature and 76 precipitation AHCCD stations inside or within 50 km of a forested area with data in 9 of 11 years 2016 to 2026.
2. Extension past AHCCD: climate-daily times a per-station, per-month offset fitted on the overlap; hold-out test: temperature bias +0.001 C, precipitation season-total bias +0.3%.
3. Area values are forest-weighted; "Canada" = forest-weighted mean over the 177 forested areas (forest at least 100,000 ha and 5% of land, Nunavut excluded).
4. Trends: OLS slope with a 95% interval widened for lag-1 autocorrelation; Theil-Sen with Mann-Kendall p. Area-burned trends use log hectares with year-bootstrap intervals (1,000 resamples).
5. FWI from station weather 1953 to 2026: Van Wagner (1987) equations in `scripts/fwi.py` (reproduces the standard test day), noon temperature, humidity and wind, rain approximated as half of the previous and half of the current day, April 1 start-up (FFMC 85, DMC 6, DC 15).
6. Panel model (`09_sensitivity_counterfactual.py`), 164 areas, 8,743 area-years, fit on 1972 to 2025, 2026 predicted:
   - M1 (main): Poisson pseudo-maximum likelihood, E[ha] = exp(area fixed effect + linear year trend + b1 x T_MJJA anomaly + b2 x ln(P_AMJJAS / normal) + b3 x ln(P_prev Sep-Mar / normal)).
   - M0: area fixed effects only. M2: area plus year fixed effects. M3: OLS of log10(share of land burned + 1e-4) with area fixed effects and trend. M1 refit on 1972 to 2022 as a check.
   - Effect of +1 C = exp(b1) - 1. Uncertainty: 500 bootstrap resamples of fitting years (all areas of a drawn year together).
7. Counterfactual: each area-year keeps its fixed effect and trend; temperature is lowered by the regional 2016 to 2026 minus 1961 to 1990 May to August difference (BC 1.41, North 1.41, Atlantic 1.09, Quebec 1.06, Prairies 1.01, Ontario 0.89 C); ratio = expected hectares under observed climate / under the counterfactual, summed over 2023 to 2026 (C9: 1.53). The "rain to normal" rows also remove the 2023 to 2025 dryness, which is mostly weather (no precipitation trend), so the warming-only row is the one tied to a measured trend.

**Assumptions.** The 1972 to 2025 within-area relation holds at 2023 to 2026 temperatures (edge of the observed range).

**Limits.** Statistical, not physical, attribution; it does not separate human-caused from natural change in the inputs; sparse northern precipitation stations attenuate sensitivities; noon wind fell at airports partly through instrument change.

**What would change the result.** Detection and attribution with climate models; a different response form (for example threshold effects); better northern precipitation data.

### 5.6 Cause: ignitions, drought, and the expected vs actual model

**Question.** Who started the fires that burned, did drought, fire weather, ignitions or fuel explain 2026 and 2023 to 2026, and by how much did the run exceed what they predict?

**Data.** CNFDB points 1990 to 2025 (438 prescribed removed), CWFIF 2026 fire list (5,474 fires) and by-cause totals, NFD cause tables, NWT fire points (for discovery dates), AAFC Canadian Drought Monitor monthly shapefiles April to September 2003 to 2026 (143 files), forest grid, weather stations, climate panel.

**Method.** `run_all.sh` runs 01 to 10 with `AREA_FILE=data/geo/fma_v2.gpkg`.
1. `03_fires.py`, `04_cause.py`: fire points assigned to areas by the 240 m grid (snapped within 10 km); cause shares nationally (official API basis including Parks Canada, C14) and on the NFD-comparable basis (C13); Theil-Sen trends.
2. `05_timing.py`: ignition season (10th and 90th percentile of report dates) and area milestones (each fire's final size credited to its report date).
3. `06_drought.py`: each CDM class burned onto a 1.2 km grid (worst class per cell), share of area and forest-weighted share per area and month. Territories show no assessment before 2015 and are treated as missing then. About 35 minutes.
4. `07_burn_history.py`: share of forest burned in the previous 10 and 20 years.
5. `09_model.py` (panel 2003 to 2025, 177 areas after the rebuild):
   - Outcome y = log10(forest share burned + 1e-4); 2026 scaled by province.
   - Blocks in chain order, as within-area anomalies: climate (columns of the climate panel), drought (D1+ April to June mean, D1+ and D2+ season maximum), weather (station extreme-day anomaly, station areas only), ignitions (log(1 + lightning fires), log(1 + human fires), ignition-season start), fuel (previous 10 and 20 year burn share).
   - Ridge regression (alpha = 10, standardized anomalies) on top of each area's mean; gradient boosting (HistGradientBoosting, 200 iterations, learning rate 0.05, 15 leaf nodes, min 20 per leaf) with permutation importance; a two-part logistic check (C = 0.5) for share at least 0.1%.
   - Skill by leave-one-year-out; within-area R2 is skill beyond each area's own average. 2026 is held out.
6. `10_run_2023_2026.py`: the same ridge trained on 2003 to 2022 predicts 2023 to 2026 as a block. Ratio = actual / predicted forest-weighted share summed over four years (C15: 5.85% / 0.36% = 16.3). Because back-transforming log predictions understates totals even in normal years, the same ratio for 2003 to 2022 leave-one-year-out predictions (3.1) is the calibration baseline; 16.3 / 3.1 = 5.2 times beyond the model's usual miss. Also reports national drivers by year with ranks and z-scores (C12).

**Assumptions.** Linear in anomalies; ignition counts are partly outcomes (they are known only after the season), so the "without ignitions" rows are what conditions alone explain.

**Limits.** No open lightning archive for 2026 (lightning-caused fire counts are used instead); the CDM is an expert-blended map and its season maximum includes August and September; drought in 2023 to 2026 is outside the training range (extrapolation); `cause/results.md` body text is pre-rebuild (14.1 times, 2.6 baseline); REBUILD.md and the CSVs are current.

**What would change the result.** A lightning stroke archive; fire-spread and suppression data; nonlinear models; NBAC 2026.

### 5.7 Wildlife: caribou ranges and protected areas

**Question.** How much of each boreal caribou range and each protected area burned in 2026 and over 40 years?

**Data.** ECCC boreal caribou ranges (2012, 51 ranges), Quebec and Saskatchewan caribou layers, CPCAD 2025 (21,509 terrestrial records), CLAB national parks, NBAC 1987 to 2025, M3 2026, Land Cover 2020.

**Method.** Exact vector overlay on a 100 km tile grid (1,511 tiles). Per target: A = area, m = inside 2026 outlines, u = inside the 1987 to 2025 union, um = inside both. 2026 share = m / A; 40-year share = (u + m - um) / A; change caused by 2026 = (m - um) / A. Forest from the 240 m grid. Provincial perimeter cross-check for BC, ON, MB ranges.

**Limits.** 2026 shares are mapped M3 shares (about 18% high nationally, more in Manitoba). Fire-only disturbance is a lower bound: the federal 65% undisturbed threshold also counts human disturbance buffered 500 m, which is not included. Caribou and protected-area results were not rerun in the rebuild (they do not depend on the area layer).

**What would change the result.** NBAC 2026; a human disturbance layer; revised provincial range boundaries.

### 5.8 People: who lived near fire, smoke days, cost per resident

**Question.** How many people lived near 2026 and earlier fires, which cities were closest, how smoky were cities, and what did firefighting cost per resident?

**Data.** DA population and points, AL_TA reserves, ISC First Nations locations, population centres, M3 2026 and NBAC 2023 to 2025 (prescribed removed), city daily PM2.5 2018 to 2026 (`data/smoke-cost/`), provincial spending (`data/smoke-cost/wildfire_spending_by_jurisdiction.csv`).

**Method.** Run 00, 00b, 00c, 01, 02y per year and threshold, 02, 03, 04, 06, 07.
1. Distance: outline boundaries densified to 200 m, nearest vertex by KD-tree, then geodesic distance (0 if inside). Checked against exact geodesic point-to-polygon distance on 400 DAs (under 1 m).
2. Bands 10, 25, 50 km, cumulative; fire size thresholds (all, 200 ha, 1,000 ha per fire ID); agency match = CWFIF point inside or within 5 km.
3. `00c_outline_class.py` drops the 13 unreported farm, grass and military outlines from 2026 distances (REBUILD.md change 4).
4. City smoke: daily mean of reporting stations (NAPS validated where available, else AirNow real-time; NAPS day needs 18 valid hours); thresholds strictly above 27, 60, 100 ug/m3; a city-year is adequate with values on 115 of 153 May to September days. The page counts only the fire season, May 1 to November 30 (2026 to October 19): `scripts/build_cities.py` recomputes the smoky-day counts, the worst day of each year and the 2026 calendar for that window from `data/smoke-cost/city_daily_pm25_2018_2026.csv`, so winter wood-smoke and inversion days (for example Ottawa, February 17, 2026) are not shown. `people/city_smoke_days.csv` keeps the calendar-year counts.
5. Cost: spending matched to NFD and 2026 preliminary area; per resident on 2021 Census populations.

**Limits.** Being within 10 km is not being threatened or evacuated; NBAC and M3 differ (use the 1,000 ha columns across years); 2025 and 2026 smoke is real-time data; cost definitions differ by province. `people/results.md` body text is pre-rebuild for 2026 exposure.

**What would change the result.** NBAC 2026; updated population; validated 2025 and 2026 NAPS data.

### 5.9 Health: smoke exposure and modelled deaths

**Question.** How much smoke did Canadians breathe in 2026 against 2018 to 2025, and what do published coefficients imply for deaths?

**Data.** Station-daily PM2.5 2018 to 2026 (NAPS validated 2018 to 2024, AirNow real-time otherwise; `data/smoke-cost/scripts/build_pm25.py`), DA populations, Census Profile age and income by DA, StatCan weekly deaths (13-10-0810, 13-10-0768) and populations (17-10-0005), CIHI ED data tables.

**Method.** Run 01 to 08.
1. Exposure: each DA gets, each day, the 24 h PM2.5 of the nearest station reporting that day within 50 km (25 km sensitivity). Population-weighted daily means (C16); person-days and people above thresholds (C17).
2. Background: for each station and calendar month, the median of its daily values over 2018 to 2024 (at least 60 values). Increment = max(0, PM2.5 - background) per DA-day.
3. Modelled acute deaths (`05_modelled_deaths.py`): deaths = sum over DAs and May 1 to September 30 days of baseline daily death rate (province, year) x DA population x (1 - exp(-beta x increment)), beta = ln(1 + percent / 100) / 10.
   - AQBAT: 0.7% per 10 ug/m3 (95% CI 0 to 1.04), Health Canada's acute all internal-cause mortality coefficient (source study Huang et al. 2023), as listed in Supporting Information Table S1 of Matz et al. 2026, GeoHealth, doi:10.1029/2025GH001565.
   - Chen: RR 1.019 (1.016 to 1.022) per 10 ug/m3 of wildfire-related PM2.5, Chen G. et al. 2021, Lancet Planetary Health 5(9):e579-e587.
   - Baseline rate: weekly deaths minus accidents and suicide, weeks ending May 7 to October 6, divided by days and July 1 population; 2026 uses 2025 rates.
   - Net (the central figure): subtract, per province and coefficient, the lowest 2018 to 2024 seasonal total, which removes ordinary above-median days. Ranges are the coefficient's 95% CI only.
4. Record tests: quasi-Poisson weekly deaths and monthly ED visits against the smoke increment (exploratory; low power).

**Assumptions.** Nearest-station exposure; the quietest year had no wildfire smoke; coefficients transfer to these populations.

**On the page (October 22, 2026).** The page shows Health Canada's own 2023 estimates (Matz and others, 2026, GeoHealth, Table 1, AQBAT; `analysis/health/hc_matz2026_2023.csv` from `scripts/10_hc_table1.py`): asthma symptom days in children, restricted activity days, respiratory and cardiac emergency visits and hospital admissions, each with its 95% range. Death rows are dropped by the script. The CIHI-based estimate of extra emergency visits (`ed_extra_visits_by_year.csv`) is not used: it rests on one significant fit of six, and Health Canada's Ontario study (Chen and others, 2025, CMAJ) found a rise in asthma visits only.

**Limits.** No monitor data after 2024 for Manitoba, NWT, Nunavut and most of NL, so 2025 and 2026 national figures cover 9 provinces and territories; 65% of on-reserve residents have no station within 50 km; real-time 2025 and 2026 data; modelled, not observed, deaths.

**What would change the result.** Validated NAPS 2025 and 2026; Manitoba data; different coefficients (the two used bracket a factor of about 2.6); a smoke model in place of the statistical background.

### 5.10 Losses: deaths, evacuations, buildings, payments

**Question.** What do official records say about direct deaths, evacuations, buildings in the fire zone, and federal disaster payments?

**Data.** Canadian Disaster Database, ISC evacuation tables and pages, TSB air occurrence data, AWCBC, Public Safety QP notes, Microsoft building footprints (ODbL), Sentinel-2, federal Grants and Contributions disclosure (DFAA orders), CatIQ and IBC posts, CPI.

**Method.** Run 01 to 10, then 12, 13, 11.
- Aviation deaths (`03_tsb.py`): occurrences whose operation type is fire fighting or fire management, plus four found by keyword and read. **Known error:** the script sums FatalCount from the TSB injuries table, which double counts; the published C19 uses the occurrence-level TotalFatalCount and summary carried into `tsb_firefighting_occurrences.csv` (2023 1, 2024 1, 2026 3; 2025's 2 deaths are the Lac du Bonnet civilians from Public Safety QP notes). `losses/results.md` and `tsb_firefighting_by_year.csv` still show the double-counted values (2024 2, 2026 6) and the knock-on "deadliest since 1995" statement, which is wrong.
- Buildings exposed: footprint centroid inside or within 100 m of an outline; all 16 classed non-wildfire outlines dropped (section 4.5).
- An earlier, uncalibrated dNBR rule here (146 likely destroyed in 2026; lenient 297) is superseded by the calibrated property estimate (section 5.11). `human_cost_2023_2026.csv` still carries the old figure.
- DFAA: Provincial Emergency Financial Assistance Orders for "interface fires" from the disclosure file (values at agreement date, interim).
- CDD costs normalised to 2025 dollars with annual CPI.

**Limits.** The CDD stops at 2022; ISC evacuee figures are partial; no open dataset identifies ground firefighter deaths.

**What would change the result.** New TSB records or revisions; CDD updates; final DFAA settlements.

### 5.11 Property: buildings likely destroyed and their value

**Question.** How many buildings did fires likely destroy, and what were they worth?

**Data.** Microsoft Global ML Building Footprints (release 2026-02-03, ODbL 1.0), Sentinel-2 L2A from Earth Search STAC, Municipality of Jasper Damage Assessment Structures layer (structure-level truth), official event counts (municipal and provincial documents), 2021 Census dwelling values (SDMX API), NRN, NRWN, CanVec.

**Method.** Scripts 00 to 15.
1. Features (`05_event_features.py`, `08_features_2026.py`, `s2lib.py`): for each footprint within 1 km of a fire, pre- and post-fire Sentinel-2 composites; dNBR and dNDVI = (pre - post) x 1000, offset by the median of pixels more than 1 km from any fire; building maxima and medians on the pixels the footprint touches; ring medians at 10 to 30 m and 20 to 60 m; burn context = share of pixels 100 to 250 m away with dNBR at least 100.
2. Calibration (`06_calibrate.py`): Jasper footprints labelled by the official structure layer (positive = "Destroyed"; 374 destroyed in the labelled set). Search rules "building feature >= a AND ring feature >= b" over {dnbr_bmax, dnbr_bmed, dndvi_bmax} x {dnbr_r10_30, dnbr_r20_60, none} on a 10-unit grid, chosen by F1. Honest accuracy by 5-fold spatial cross-validation (500 m blocks; rule re-chosen on 4 folds, scored on the fifth): **precision 0.836, recall 0.832, F1 0.834** (in-sample 0.856, 0.861). Final rule: `dndvi_bmax >= 180 AND dnbr_r20_60 >= 40`, plus burn context at least 0.20.
3. Apply (`07_apply_rule.py`, `15_apply_2026.py`): flags counted inside the fire polygon or within 500 m (outlines miss unburned islands and edges); the 500 to 1,000 m band is a false-positive check (0 to 7 per event). Estimate = flagged x P / R; band from 95% Wilson intervals of P and R. The band covers calibration sampling error only, not transfer error.
4. Transfer checks (`14_transfer_checks.py`): flagged / official count at six events: 0.31 (Barrington, unexplained) to 1.51.
5. Value (`12_value_exposed.py`, `13_value_destroyed.py`): 2021 Census average owner-occupied dwelling value in the DA (fallback census division, then province), applied to official counts (C26) and to flags. A proxy, not insured or market loss.
6. Infrastructure (`09_infra.py`): length inside burned areas.

**Limits.** Calibrated on one event (Jasper townsite); surviving buildings under burned forest canopy can be flagged (two Ontario clusters); official counts mix units; coverage differs by year (C23).

**What would change the result.** Structure-level truth from more events; post-fire imagery after October 20, 2026; official 2026 counts.

### 5.12 Economy: timber, carbon, jobs, infrastructure, scale

**Question.** How much wood, biomass and carbon burned, how many forestry jobs and kilometres of roads and rail were in burned areas, and how big is it in familiar terms?

**Data.** NFI kNN 2011 250 m volume and biomass, SCANFI v2 biomass (2015, 2020, 2025), NFD harvest, NIR 2026, 2021 Census industry by census division (98-10-0592), NRN, NRWN, CanVec power lines, NRCan mill list, UN Demographic Yearbook areas.

**Method.** Run order 01, 01b, 02 (x3, plus `02b_run_scanfi_1622.sh`), 03, 04 (x2), 05, 05b, 06, 06b, 07, 07b, 08, 08b, 09; `07c` for the fma_v2 area summary.
- Volume: kNN merchantable and total volume at cell centres on the 240 m burned cells; scaled by province factors. Years of harvest = burned merchantable volume / NFD 2024 harvest (C30).
- Carbon: carbon = 0.5 x dry biomass; CO2 = carbon x 44/12; combusted share LOW = foliage only, HIGH = foliage + branches + bark, both measured from kNN biomass components on the same cells (2026: 11.0% and 34.2%). Ground fuels, dead wood, CH4 and N2O are excluded, so this is a floor-to-mid estimate.
- Infrastructure: grid method for all years (lines cut into 30 m pieces assigned to the cell holding the midpoint, projection-scale corrected), checked against an exact vector clip for 2026 (inside lengths agree within 1%) (C25).
- Scale: area comparisons against UN DYB countries and Canadian provinces and cities (`09_scale.py`, C4).

**Limits.** kNN volume is from 2011; burned volume is not lost supply (salvage, most northern forest is outside the harvest land base); jobs are 2021 residents by place of residence. `01_cells.py` reads a Parks Canada scaling row that the rebuild removed; rerunning it needs the same change as `07c` (REBUILD.md problem 10).

**What would change the result.** A newer national volume map; NFD 2025 harvest; ground-fuel combustion data.

### 5.13 Economic value: what it cost

**Question.** What did 2023 to 2026 cost in spending, losses and valuations, against 2016 to 2022?

**Data.** NFD Crown stumpage revenue and harvest on Crown land, BC Budget and Fiscal Plan stumpage rates, provincial public accounts (BC, ON, AB, SK), federal Grants and Contributions (NRCan wildland fire programs, DFAA), CatIQ and CDD insured losses, health modelled deaths, Health Canada value of a statistical life, Parks Canada and Ontario Parks attendance, tenure layers, CPI.

**Method.** Run 02, 03, 05, 04, 04b, 06, 07, 08, 09, then 10.
- Timber value (`05_timber_value.py`): scaled merchantable volume burned x stumpage price per m3 = NFD stumpage charges / NFD Crown harvest (BC: fiscal-plan total stumpage rate). Gaps carry the last value (rules in `timber_prices_by_province_year.csv`); NWT and Nunavut report no stumpage, so value 0 (C27). Value of standing timber, not a loss.
- Cost tally (`07_cost_tally.py`), 2025 dollars by CPI: A provincial firefighting (four provinces as published, not harmonised), B federal NRCan agreements (spread evenly over their term), C DFAA, D insured, E timber at stumpage, F modelled deaths x VSL $9,158,296 (2023 CAD; Matz et al. 2026 Table S2, from Chestnut and De Civita 2009). A to D and E, F are kept separate and summed only in the last column (C28, C29).
- Parks (`04_parks.py`): baseline = mean of FY2017-18 to 2019-20 (excluding years the park itself burned 1,000 ha or more); control = 84 places reported every year (C39).
- BC difference-in-differences on BC Stats LFS by economic region (descriptive; the gap predates the fires).

**Limits.** Statistics Canada tables (roundwood value, GDP, LFS by ER outside BC) could not be downloaded; scripts pick them up when present. 2026 is a floor (most cash components unpublished). Firefighting definitions differ by province; 2022 lacks Alberta.

**What would change the result.** StatCan roundwood value; 2026 public accounts; a different VSL; final insured figures.

### 5.14 Threads: emissions gap, reburns, overwintering, repeat exposure, prescribed fire, water

- **T1 emissions gap** (`t1a`, `t1a2`, `t1b`): NIR 2026 Tables 6-1 and 6-5 read directly; managed-forest wildfire emissions are a memo line outside the national total (C31). The GHG managed-forest boundary is not open GIS data, so NRCan's official image was georeferenced (affine fit to provinces, pixels 12 to 13 km; validated at 229.2 Mha vs the NIR's 230 Mha) to split our aboveground CO2 estimate into managed and unmanaged.
- **T2 reburns** (`t2a`, `t2b`, `t2`): on the 240 m grid, a cell reburns within k years if its previous burn falls in Y-k to Y-1. Black spruce/jack pine leading forest from SCANFI v2 (black spruce plus jack pine crown closure at least 50% of total, total at least 10%), map epoch at or before the window start, read from the 480 m overview (noisy per cell, unbiased for large areas) (C32).
- **T3 overwintering** (`t3a`, `t3`, `t3b`): November to April detections near the previous season's NBAC perimeters, excluding persistent heat cells and NPRI facilities within 2 km, clustered at 3 km. Low confidence (slash burning cannot be excluded).
- **T4 repeat exposure** (`t4_repeat_exposure.py`): reuses the people distance files; exposed = within 10 km of an outline in a year; counts years exposed 2023 to 2026 (C21, C22).
- **T5 prescribed burning** (`t5_prescribed.py`): CNFDB and NBAC prescribed flags; a reporting record, not a programme measure.
- **T6 drinking water** (`t6_watersheds.py`, `t6b_bc_water.py`): burned share of NHN work units and of BC's 466 community watersheds (exact overlay), 2023 to 2026 union; population centres assigned to the containing work unit; no upstream routing (C38).

### 5.15 Readiness: are provinces ready for another season like 2023 to 2026?

**Question.** For each fire agency: does the 2026-27 budget cover what fires have cost lately, what aircraft and crews does it have, where have auditors and reviews found gaps, and how many of their recommendations are done?

**Data.** Official records only, listed with URLs and access dates in `analysis/readiness/manifest_west.csv` and `manifest_east.csv`: provincial and territorial estimates and public accounts, supplementary estimates and special warrants, auditor general reports, commissioned after-action reviews, agency annual reports and pages, legislature transcripts, CIFFC Canada Reports and annual reports. News was used only to find documents; a number found only in news was left out and marked "not found in official record".

**Method.**
1. `agencies_west.csv`, `agencies_east.csv`: one row per agency, every value with its basis (which line of which document, forecast or actual).
2. Budget cover = 2026-27 base wildfire budget / mean(actual 2023-24, 2024-25, 2025-26). Computed in `analysis/readiness/scripts/04_scorecard.py` (`scorecard.csv`, columns `budget_2026_27_m`, `avg_actual_m`, `budget_pct`) and again on the page from the agency rows (`scripts/build_chapters.py`).
3. `gaps_west.csv`, `gaps_east.csv`: each gap in one plain line with a short verbatim quote and its source.
4. Slide colour rule (`scorecard.csv`): red = a problem on record with no fix in place; amber = a fix ordered or under way; grey = not found. Budget: under 50% red, 50% to 80% amber, 80% and over green. The page uses no status colours; it shows spending and budget as nested circles.

**Limits.** Budget bases differ: Saskatchewan's line is the whole public safety agency and its spending is by fire season; Manitoba adds an all-hazard emergency vote; the Northwest Territories' line includes forestry; Quebec has no separate wildfire line; Yukon's 2026-27 figure could not be read; some 2025-26 values are forecasts. Recommendation counts are as published, and several governments publish none.

### 5.16 Government response and research under way

`analysis/policy/`: federal and provincial measures 2019 to 2026 (`measures.csv`, 38 rows: announced, spent where a payment record exists, stage), and federal research and monitoring (`research_underway.csv`: 5 programs and 53 grant or contribution agreements active after October 22, 2026, from the federal proactive disclosure file). "Paid by March 2025" sums payment records for the four largest new programs; the satellite (WildFireSat) has no separable spending record. The timeline on the page is `analysis/readiness/timeline.csv`, each row with its source.

### 5.17 Coverage check: are all the major reported fires in the data?

`analysis/coverage/`: 65 fires reported in news and official releases from 2023 to 2026 (news used only as a checklist) were matched to NBAC and 2026 outlines by year, distance (30 km) and dates, and by agency fire number or name where available. 63 matched. Gaps: CFB Wainwright (no satellite outline; estimated separately in `analysis/wainwright`), Thunder Lake AB (structural fires, too small), Walsh River NL (outline far smaller than the agency record), Long Lake AB 2023 (NBAC joins it with BC fires). The national total uses agency totals, so these do not change it. `labels.csv` gives the eight labelled fires on the chapter 1 map.

### 5.18 The bill

`analysis/costs-full/` brings together every cost with a public record, each dollar counted once. `scripts/combine_bill.py` reads `gov*_costs.csv` (government firefighting and emergency response), `econ*_costs.csv` (property, infrastructure and economic losses) and `health*_costs.csv` (health care, evacuations, lost work), so later research rounds (`gov2_costs.csv` and so on) are added by re-running it, and writes `combined_bill.csv` (one row per line) and `bill_summary.json`.

- **Receipt on the page and the slide** (`bill_summary.json`, block `slide`): trees burned 2023 to 2026 at Crown stumpage and provincial firefighting in BC, Alberta, Saskatchewan and Ontario (`analysis/economic-value/cost_tally_by_year.csv`, 2025 dollars); firefighting and emergency response elsewhere, 2023 to 2025 (official spending); 2026 firefighting from government forecasts and budgets; homes and buildings at census home values (`analysis/property`) plus buildings, infrastructure and repairs not in that count; evacuations and hospital care, including Indigenous Services Canada's on-reserve emergency response estimate (central value); lost work and business.
- **Counting rules**: official spending in full; estimates at the low end of their range; lost wages and lost business output overlap, so only the larger is counted; federal disaster payments (DFAA) are not added because they repay provinces for costs already counted; insured losses (industry data) are not added (they run about 2.6 times census home values for the six events with both, `work/econ_property_insured_vs_bill.csv`).
- **Per Canadian** = total divided by Canada's July 1, 2026 population (Statistics Canada 17-10-0005-01, `data/canada_population_2026.csv`), rounded down to the nearest $10.
- **On the page**, "How the bill was counted" lists every line with its amount, basis, source and range (`scripts/build_chapters.py`, from `combined_bill.csv` and the cost files) and the items still without a public record (the "Not found" sections of `gov*_notes.md`, `econ*_notes.md` and `health*_notes.md`, with access notes and figures quoted from news reports left out).
- Each source document in the cost files and manifests is in `data/references.json` (`scripts/build_refs_costs.py`). Raw downloads (`analysis/costs-full/raw/`, about 775 MB) are not in the repo; the manifests list every URL and `scripts/econ_fetch.sh` and `scripts/download_data.py` fetch them.

### 5.19 How the page and the slides share numbers

`scripts/build_chapters.py` imports `slides/make_slides_merge.py` (the carousel builder) and writes `data/chapters.json` from the same functions and files, plus `data/map/burn_2023_2026.png` (the 2023 to 2026 outlines drawn in the same pixel box as the carousel map). `scripts/build_refs_readiness.py` adds the government, readiness, CIHI and coverage references to `data/references.json` from the manifests.

## 6. Independent verification

`methods/verification.md` is the full independent check of C1 to C40, done 2026-10-22 by reading every cited file (and REBUILD.md, which supersedes `results.md` text where they differ) without modifying any analysis file. It lists eight claims that needed correction (C4, C12, C16, C18, C19, C20, C23, C26) and the caveats carried into the page. The verified values are in `story/verified_numbers.json`, which is the only source of claim numbers for the page and the slides.

## 7. How to challenge a number

1. **Open an issue** on the repository with the claim ID (for example "C15") in the title, the number you dispute, and what you think it should be and why. For numbers that are not a claim, name the CSV and row.
2. **Trace it.** Find the claim in section 2: it names the script, the output file and the verifier's note. The topic's `results.md` explains the method and lists every output file.
3. **Recompute it from the output.** Every claim can be recomputed from the CSVs in this repo without downloading anything. For example, C3 is the maximum 4-year rolling sum of `share_forest_burned` in `analysis/forest/canada_forest_share_by_year.csv` before 2023.
4. **Rerun the analysis.** Follow [REPRODUCE.md](REPRODUCE.md): download the raw data, run the topic's scripts in order, and compare the regenerated CSV with the one in the repo (`git diff`).
5. **Rebuild the page numbers.** `python scripts/build_story_json.py --src .` regenerates `data/story.json` from the verified values and the CSVs.

## 8. Things the files do not make clear

These are gaps in the record as it stands, stated rather than filled in:

- The verification pass recomputed values with short interactive pandas checks that were not saved as scripts (section 3).
- `losses/scripts/03_tsb.py` has the double-count error described in 5.10; the script was not changed, so rerunning it reproduces the wrong yearly totals. The correct per-occurrence values are in its own output file.
- Several `results.md` bodies (forest, weather, wildlife, people, cause) quote pre-rebuild numbers; REBUILD.md has a rebuild notice and the current values. Pre-rebuild files (`analysis/_before_rebuild/`) are not in the repo, so the "before" values in REBUILD.md and in C12 and C15 cannot be recomputed from the repo.
- The climate block in the cause model: `cause/results.md` says the climate panel did not exist at its first run; REBUILD.md says the rebuilt run joined 21 columns from the fma_v2 climate panel. The current `model_*` CSVs are from the rebuilt run.
- Some raw inputs were fetched "in an earlier step" and their manifests give a layer name rather than a full download URL (several data/geo boundary layers, the Quebec SOPFEU points, the official totals snapshots). The snapshots are kept in the repo; the boundary layers need the named service.
- The TSB raw files were deleted after the run (manifest note); they are re-downloadable from the TSB, but the copy used is not preserved.
- The analyses of the 2026 response (analysis/response), the Wainwright burn (analysis/wainwright), readiness (analysis/readiness), government measures (analysis/policy) and the coverage check (analysis/coverage) are in the repo; `scripts/sync_analysis.py` refreshes them with one command.
- The emergency room estimate is one significant result among six fits in `analysis/health/results.md` (all-month fits show no effect), so the page shows its full range.
