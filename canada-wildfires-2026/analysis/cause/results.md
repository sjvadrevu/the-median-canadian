# What drove Canada's 2026 wildfires: cause analysis

Original analysis of official raw data only (agency fire lists, CNFDB, NFD, NBAC, CWFIS M3 and station FWI, AAFC Canadian Drought Monitor). No news or third-party analysis was used. Run date 2026-10-21. Folder: `analysis/cause/`. Scripts: `scripts/run_all.sh` runs 01 to 10. New downloads are listed in `manifest.csv`.

## Bottom line

1. Almost all of 2026's burned area came from lightning fires far from people. Lightning started 54.7% of fires but burned 95.0% of the area (4,275,480 of 4,500,984 ha). Human-caused fires were 40.0% of fires and 4.9% of area.
2. 2026 did not have more ignitions than usual. Nationally, lightning-caused fires (2,960, NFD-comparable) were below the 1991 to 2020 average (3,245). Human-caused fires (2,190) were the fewest of 37 years.
3. The 2026 season did not start early. The ignition season began on a normal date, and area burned piled up late and fast, between about June 22 and July 16.
4. The driver that stands out is drought. In 2026, 55.8% of the forest in the modelled areas was in moderate drought or worse (CDM D1+) at some point from April to September. The 2003 to 2022 average was 14.4%, and no year in that period went above 32.7%. Every big-burn area in 2026 was in deep drought.
5. Station fire weather was near normal nationally (12.0 extreme days against 11.4). The two exceptions were the NWT and BC's Kamloops region, where it was extreme.
6. A transparent model using drought, fire weather, ignitions and recent burn explains part of where it burned. It does not explain how much burned. For 2026 held out, it ranks the 93 areas well (Spearman 0.76). It expected only 0.36% of the modelled forest to burn, against 0.89% actual. The 2023 to 2026 run as a whole is underpredicted about 14 times.
7. A post can say the following. In the data, 2026's fires were lightning fires in drought-hit northern forest, and the drought was unusually widespread. The data cannot show why the run was this large. Known drivers cover only part of it, and none of this is a climate attribution.

## 1. Ignition cause

Files: `cause_2026_by_agency.csv`, `cause_2026_by_area.csv`, `cause_by_year_national.csv`, `cause_by_year_province.csv`, `cause_trends.csv`, `cause_by_area_year.csv`, `cnfdb_completeness.csv`, `distance_to_population.csv`. Scripts: `03_fires.py`, `04_cause.py`.

### 2026 nationally (official CWFIS/CWFIF API, as of 2026-10-20, 13 agencies)
- **Fires:** 5,516 in total. Lightning 3,019 (54.7%), human 2,209 (40.0%), undetermined 288 (5.2%).
- **Area:** 4,500,984 ha in total. Lightning 4,275,480 ha (95.0%), human 220,114 ha (4.9%), undetermined 5,391 ha (0.1%).
- **Human share of known-cause fires:** 42.5% on the NFD-comparable basis (without Parks Canada). This is third lowest of 37 years; the 1991 to 2020 mean is 53.2%.
- **Human share of known-cause area:** 5.0%, against a 1991 to 2020 mean of 11.2% and a median of 8.3%.
- **Lightning-fire area:** 4.15 M ha on the NFD basis, 9th largest of 37 years.

### 2026 by province (official)
Human share of known-cause fires and of area:

| Province | Share of fires | Share of area |
|---|---|---|
| NT | 4% | 0.0% |
| MB | 12% | 0.4% |
| ON | 30% | 11.0% |
| BC | 39% | 26.4% |
| QC | 39% | 1.2% |
| SK | 46% | 0.1% |
| AB | 64% | 2.8% |
| NL | 62% | 0.0% |
| NB | 98% | 93.9% |
| NS | 100% | 100% |

In NB and NS the area is tiny (498 ha and 1,525 ha). BC reports no "undetermined" fires.

### 2026 by fire management area
These figures come from fire-list points located in each area.
- 90% of the human-caused area is in three areas:
  - BC Coastal Fire Centre: 90,163 ha, 192 human-caused fires
  - Ontario Dryden: 77,794 ha
  - BC Kamloops: 31,127 ha
- Everywhere else, the big burns are lightning fires:
  - North Slave: 903,810 ha from 78 lightning fires
  - Quebec: 733,712 ha
  - Deh Cho: 431,640 ha
  - Thunder Bay: 309,258 ha
  - Sahtu: 297,743 ha
  - Manitoba: 284,584 ha
- Areas with lightning-fire counts well above their 1991 to 2020 average:

| Area | 2026 lightning fires | 1991-2020 average | Ratio |
|---|---|---|---|
| Sahtu | 83 | 28.5 | 2.9 |
| Sioux Lookout | 113 | 67.4 | 1.7 |
| North Slave | 78 | 51.8 | 1.5 |
| Fort Frances | 61 | 41.3 | 1.5 |
| Quebec | 368 | 240.2 | 1.5 |
| Thunder Bay | 64 | 47.3 | 1.4 |
| NL District 22 | 23 | 2.5 | 9.1 |

### History (NFD 1990 to 2025, 12 provinces and territories)
- **No national trend in the human share.** Human share of known-cause fires: -0.6 points per decade (95% range -2.7 to +1.8, p = 0.62). Human share of area: -0.4 points per decade (p = 0.60).
- **Both counts are falling.**

| Fire count | 1990s average | 2016 to 2025 average | Theil-Sen trend per decade | p |
|---|---|---|---|---|
| Human-caused | 4,261 | 2,875 | -521 | < 0.001 |
| Lightning-caused | 4,004 | 2,649 | -380 | 0.025 |

  Reporting practice may contribute; this cannot be separated with these data.
- **Provincial trends with p ≤ 0.05:**
  - Alberta's human share of fires rose 9.9 points per decade (38.5% in the 1990s, 65.4% in 2016 to 2025).
  - BC's human share of area fell 12.1 points per decade.
  - Yukon's human share of fires fell 6.2 points per decade.
  - New Brunswick's human share of fires rose 1.9 points per decade.
  - With 12 provinces and 6 variables, a few p < 0.05 results are expected by chance.
- **Notable years:** 2025 had the largest human-caused area on record, 2.10 M ha (25% of known-cause area). 2020 had 63.5%, in a very small year.
- **CNFDB points against NFD:** fire counts agree within about 5%. Point area totals for Alberta are 8% to 37% of NFD in 1994, 1996, 2003, 2007, 2013, 2014 and 2017 (`cnfdb_completeness.csv`). Point-based area by cause is therefore used only within areas, not for national totals.

### Distance to population
Distance from each fire's origin to the nearest populated 2021 dissemination-area point.

| Cause, period | Median distance | Within 10 km | Beyond 50 km |
|---|---|---|---|
| Human, 2026 | 4.9 km | 74.5% | 1.3% |
| Lightning, 2026 | 27.3 km | 20.6% | 30.2% |
| Human, 1991 to 2015 | 5.1 km | 70.5% | 2.6% |
| Lightning, 1991 to 2015 | 23.1 km | 21.9% | 19.6% |

- Weighted by area, 56.6% of 2026 human-fire area burned from fires starting within 10 km of people.
- 66.3% of 2026 lightning-fire area came from fires starting more than 50 km away.
- In 2026 lightning fires started farther out than usual: 30.2% beyond 50 km, against 21.1% in 2016 to 2025.

## 2. Season timing

Files: `timing_by_year_scope.csv`, `timing_trends.csv`, `timing_m3_by_year.csv`, `timing_by_area_year.csv`. Script: `05_timing.py`. Each fire's final size is credited to its report date. The satellite (M3) series shows when area actually burned.

### Canada 1990 to 2025: no significant change
| Measure | Theil-Sen trend | p |
|---|---|---|
| Ignition-season start (10th percentile of fire report dates) | -1.0 days per decade | 0.26 |
| Ignition-season end (90th percentile) | -0.8 days per decade | 0.59 |
| Date 10% of area had started | -5.0 days per decade | 0.12 |
| Date 50% of area had started | -1.9 days per decade | 0.56 |
| Date 90% of area had started | -0.7 days per decade | 0.68 |

The season is neither starting measurably earlier nor ending later at the national scale.

### 2026: a normal start, then a late and compressed burn
- **Ignition season:** began May 2 (day 122.3; 1991 to 2020 mean day 121.2).
- **Area milestones (report-date basis):**
  - 10% of area by June 22 (day 173; 1991 to 2020 mean day 146), 4th latest of 37
  - 50% by June 28 (day 179; mean 173.6)
  - 90% by July 16 (day 197; mean 204.9), 9th earliest of 37
- **Satellite M3 basis** (2012 to 2025 mean in brackets): 10% by June 28 (160.3), 50% by July 14 (191.4), 90% by August 9 (225.1).
- The first 1,000 ha fire came on May 22 (day 142), 4th latest of 37. The day-30 "first 200 ha fire" is a single 259 ha Alberta report from January 30 and is not meaningful.

### Provincial trends with p ≤ 0.05
These are 13 provinces times 10 measures, so some are chance results.
- BC's first 1,000 ha fire is coming 13.2 days earlier per decade (p = 0.02), and BC's 90%-of-area date 9.3 days per decade earlier (p = 0.05).
- NWT's first 1,000 ha fire is 6.9 days per decade earlier (p = 0.02).
- Ontario's ignition-season start is 6.1 days per decade **later** (p = 0.01). Manitoba's is 4.7 days later (p = 0.05).
- NB and NL ignition seasons start 3.6 and 4.3 days per decade earlier.

## 3. Drought (AAFC Canadian Drought Monitor)

Files: `drought_by_area_month.csv`, `drought_by_area_year.csv`, `drought_coverage_check.csv`. Script: `06_drought.py`.

**Source.** 143 monthly "areas of drought" shapefiles, April to September 2003 to 2026, from agriculture.canada.ca (open.canada.ca dataset 292646cd). April to September 2002 does not exist (the series starts November 2002), and August 2003 is not published.

**Method.** Each class D0 to D4 is burned onto a 1.2 km grid, with the worst class kept per cell. The share of each area is computed by true area, and also weighted by forest.

**Coverage problem.** No part of Yukon or the NWT shows any dryness in 2003 to 2014, then dryness appears most years from 2015. The territories were evidently not assessed before 2015, so those values are treated as missing in the model. Quebec and Labrador values are very low in early years, which may also reflect thinner northern assessment.

**Findings.**
- **2026 drought share across all modelled areas (forest-weighted):**

| Measure | 2026 | 2003 to 2022 |
|---|---|---|
| D1+ (moderate or worse), season maximum | 55.8%, 2nd of 24 years (after 2025) | mean 14.4%, max 32.7% |
| D2+ (severe or worse), season maximum | 30.7%, 2nd of 24 | mean 4.5%, max 14.3% |
| D1+, April to June mean | 13.1%, 6th of 24 | n/a |

  The drought built during summer. Share of Canada's grid in D1+: April 8.9%, May 7.3%, June 14.6%, July 30.7%, August 35.3%, September 33.1%.
- **The 2026 big-burn areas were in deep drought** (D1+ and D2+ season maximum; 2003 to 2025 area averages in brackets):

| Area | D1+ max | D2+ max |
|---|---|---|
| Thunder Bay | 100% (31%) | 76% (12%) |
| Fort Frances | 100% | 78% |
| North Slave | 100% | 98% (16%) |
| Cariboo | 100% | 91% |
| Kamloops | 98% | 92% |
| Sioux Lookout | 97% | 66% |
| Deh Cho | 73% | 48% |

- Exceptions:
  - Prince Albert (SK) burned 2.3% of its forest with 0% CDM drought, mostly from one 18,068 ha lightning fire.
  - Sahtu (NT) burned 2.0% with 31% D1+.

## 4. Fuel and past fire

File: `burn_history_by_area_year.csv`. Script: `07_burn_history.py`. These are shares of each area's forest burned in the previous 10, 20 and 40 years, from NBAC on the 240 m grid of analysis/forest. The yearly shares match `analysis/forest/fma_forest_share_by_year_1972_2025.csv` exactly (maximum difference 3e-14).

- **Big 2026 burns came from both lightly and heavily burned areas.**
  - Thunder Bay and Fort Frances had burned only 1.3% and 2.9% of their forest in the previous 10 years.
  - North Slave and Deh Cho had burned 14.9% and 13.2%.
- **Areas burned hardest in 2023 to 2025 burned much less in 2026 than the model expected:**

| Area | Previous-10-year share | 2026 actual | 2026 expected |
|---|---|---|---|
| La Ronge | 27.8% | 1.5% | 4.0% |
| Île-à-la-Crosse | n/a | 0.43% | 2.8% |
| Weyakwin | n/a | 0.0% | 0.72% |
| Denare Beach | 32.9% | 2.3% | 5.5% |

  This fits fuel limitation after recent burns, but it is a handful of areas.
- **Across the 2003 to 2025 panel the relation runs the other way.** Within an area, more burning in the previous 10 years goes with slightly more burning this year (Spearman 0.13; ridge coefficient positive). Recent burn behaves as a marker of an active fire period more than as a fuel brake. The data do not support a general claim either way.
- The 2026 reburn share (15.8% of the 2026 footprint had burned since 1972) is in `analysis/forest/results.md`.

## 5. Expected vs actual model

Files: `model_panel.csv`, `model_skill.csv`, `model_chain_links.csv`, `model_rank_correlations.csv`, `model_importance.csv`, `model_2026_by_area.csv`. Script: `09_model.py`.

### Set-up
- **Panel:** fire management area by year, 93 of 99 areas. Excluded: Nunavut and areas with under 100,000 ha of forest or under 5% forest cover.
- **Outcome:** log10 of forest share burned plus 0.0001. The 2026 value is scaled to official totals by province.
- **Predictors, in chain order:**
  - drought: CDM D1+ April to June mean, D1+ and D2+ season maximum
  - fire weather: station extreme-day anomaly, available for 42 areas only
  - ignitions: lightning-caused fire count, human-caused fire count, ignition-season start
  - fuel: previous 10 and 20 year burn share
- **Models:** area fixed effects plus ridge regression on within-area anomalies; gradient boosting with permutation importance; a two-part logistic check.
- **Validation:** leave-one-year-out over 2003 to 2025. 2026 is held out.
- **Climate block:** the script joins `analysis/climate/climate_panel.csv` as a first "climate" block when that file exists. It did not exist at this run, so that link is untested. Rerun `09_model.py` and `10_run_2023_2026.py` once it appears.

### Out-of-sample skill (leave-one-year-out, 2003 to 2025)
"Within-area R²" is skill beyond each area's own long-run average. It is the honest measure of what the drivers add.

| Model | All 93 areas: within-area R² | 42 station areas: within-area R² | Year totals, Spearman (93 / 42) |
|---|---|---|---|
| Area average only | -0.09 | -0.09 | n/a |
| + drought | 0.07 | 0.15 | 0.47 / 0.51 |
| + fire weather | n/a | 0.21 | n/a / 0.63 |
| + ignitions | 0.19 | 0.30 | 0.58 / 0.70 |
| + fuel (full chain) | 0.19 | 0.31 | 0.69 / 0.78 |
| Full chain without ignition counts | 0.08 | 0.22 | 0.60 / 0.62 |
| Gradient boosting, all | 0.20 | 0.32 | 0.75 / 0.73 |

- Total R² (including the area average) is 0.51 to 0.57.
- The across-area rank correlation within a year is about 0.75 for every model. Most of "where it burns" is just which areas always burn.
- The two-part check (will at least 0.1% of forest burn?) has AUC 0.88.

### Which links carry predictive skill
- **Drought and lightning-fire counts carry most of it.** Within-area Spearman with the outcome:
  - lightning-fire count 0.43
  - D1+ maximum 0.39
  - D2+ maximum 0.37
  - station extreme days 0.45 (42 areas)
  - human-fire count 0.14
  - previous-10-year burn 0.13
  - ignition-season start 0.08
- **Permutation importance (gradient boosting, all areas):** area average 0.163, lightning count 0.145, human count 0.050, D1+ maximum 0.027, others under 0.01.
- **Drought to fire weather:** a weak link. Drought explains within-area R² 0.11 of the station extreme-day anomaly.
- **Fire weather or drought to lightning-fire counts:** no out-of-sample skill (within-area R² -0.04 and -0.03). Lightning-caused fire counts are not predicted by these conditions here.
- **Fuel alone:** no skill (-0.07).
- **Ignition counts and leakage:** counts are only known after the season and partly result from fire conditions. Fires are also counted where they spread. Their skill is partly descriptive, not predictive. The "without ignition counts" row (0.08 or 0.22) is what conditions alone explain.

### 2026 held out (trained on 2003 to 2025)
- **Ranking areas:** Spearman across the 93 areas 0.76, R² 0.60 (area average alone: 0.62 and 0.24). Without ignition counts: 0.73 and 0.52.
- **Amount, forest-weighted share of modelled forest burned:**

| | All 93 areas | 42 station areas |
|---|---|---|
| Actual | 0.89% | 0.96% |
| Full model | 0.36% | 0.58% |
| Without ignitions | 0.31% | 0.50% |
| Area average only | 0.075% | n/a |

  The model gets the direction and the ranking but about 40% of the amount.
- **Burned far more than expected** (full model, all areas):

| Area | Actual | Expected | Ratio | Notes |
|---|---|---|---|---|
| Prince Albert (SK) | 2.3% | 0.02% | 77 | no CDM drought, one large lightning fire |
| Thunder Bay (ON) | 11.2% | 0.17% | 61 | drought and extra lightning fires were the largest contributors, but extreme beyond anything in its record; local station fire weather was normal (-0.1 days) |
| Fort Frances (ON) | 4.1% | 0.12% | 31 | drought and lightning fires |
| Hudson Bay (SK) | 0.33% | 0.01% | 16 | |
| BC Coastal | 0.98% | 0.11% | 8 | mostly human-caused area |
| Deh Cho (NT) | 4.9% | 0.69% | 7 | |
| Dryden (ON) | 0.61% | 0.11% | 5 | mostly human-caused area |
| Sahtu (NT) | 2.0% | 0.41% | 5 | lightning fires 2.9 times normal |
| Cariboo, Quebec, Sioux Lookout, Kamloops | | | 3 to 4 | |

- **Burned far less than expected** (expected in brackets):
  - Weyakwin 0.0% (0.72%)
  - Fort McMurray 0.0% (0.29%)
  - Île-à-la-Crosse 0.43% (2.8%)
  - La Ronge 1.5% (4.0%)
  - Denare Beach 2.3% (5.5%)
  - Kenora, Dawson, Prince George, Northwest BC

  All except Dawson and Northwest BC are areas with heavy recent burns (see section 4).
- North Slave (6.2% vs 5.8% expected with stations) was predicted well because station fire weather was extreme there.

### How much is and is not explained
- Drivers in the chain explain about 19% of the year-to-year variance within areas (31% where stations exist). Without counting ignitions after the fact, the figures are 8% and 22%.
- They predict the ranking of years nationally reasonably well (Spearman 0.69 to 0.78).
- They underpredict the size of the biggest years. For 2026 the full model gives about 40% of the actual share. The largest misses (Thunder Bay, Fort Frances, Prince Albert) are not explained by any driver measured here.

## 6. The 2023 to 2026 run

Files: `run_national_drivers.csv`, `run_driver_summary.csv`, `run_by_area.csv`, `run_model_check.csv`. Script: `10_run_2023_2026.py`.

### Which drivers were unusual in all four years
- **Drought: yes, in all four years.** Forest-weighted CDM D1+ season maximum:
  - 2023 53.7%, 2024 53.8%, 2025 72.2%, 2026 55.8%
  - 2003 to 2022: mean 14.4%, max 32.7%. All four years are above every earlier year.
  - D2+ maximum (19.5% to 38.6%) is also above the earlier maximum of 14.3% in all four years.
  - The southern-provinces subset (BC, AB, SK, MB, ON and the Maritimes), where CDM coverage is consistent from 2003, gives the same result. D1+ was 57.4% to 75.4% against an earlier maximum of 50.9% (2021).
  - Early-season (April to June) D1+: top four in 2023 to 2025, 6th in 2026.
- **Fire weather: not in all four years.** Station mean extreme days:
  - 2023 17.2 (6th of 36), 2025 19.5 (2nd), 2024 13.4 (11th), 2026 12.0 (15th)
  - The 1991 to 2022 mean is 11.5.
- **Lightning-caused fires: not unusual.** 2023 3,827 (6th of 36); 2024, 2025 and 2026 were below the 1991 to 2022 mean of 3,228 (ranks 20, 28 and 22).
- **Human-caused fires: below normal** in all four years.
- **Ignition-season start: normal.**
- **Area burned by lightning fires: above the 1991 to 2022 75th percentile in all four years** (ranks 1, 5, 3 and 9 of 36). This is the outcome, not a driver.
- **Recent-burn share: rose** to 4.6%, 5.4% and 6.6% (2024 to 2026), a consequence of the run itself.

### By area
- 99.3% of the forest burned in 2023 to 2026 (forest-weighted, 79 areas with drought data) was in areas whose run-average D1+ maximum was above their own 2003 to 2022 average.
- 91.7% was in areas with above-average lightning-fire counts.
- 61.5% was in areas with above-average station extreme days (42 areas only).
- 43% was in areas with above-average human-fire counts, and 45% in areas with a later ignition-season start. These last two are no signal.
- The run is concentrated in Saskatchewan, the NWT, northern Alberta and northwestern Ontario. Île-à-la-Crosse, Weyakwin, Lower Fishing Lake and Denare Beach burned 31% to 43% of their forest over the four years, 13 to 56 times their 2003 to 2022 rate.

### Does the model predict the run? No
Ridge with area effects trained on 2003 to 2022, predicting 2023 to 2026 as a block (sum of the four yearly forest-weighted shares, modelled areas):

| Model | Actual | Predicted | Ratio |
|---|---|---|---|
| Full | 5.85% | 0.41% | 14.1 |
| Without ignitions | 5.85% | 0.50% | 11.8 |
| Area average only | 5.85% | 0.20% | 28.6 |

- Back-transforming log predictions understates totals even in ordinary years. For 2003 to 2022 the out-of-sample actual-to-predicted ratio was 2.6. The run is therefore underpredicted about 5.4 times beyond that normal bias.
- The drivers double the expected amount relative to area averages, but they do not come close to the run.
- The drought shares of 2023 to 2026 are outside the training range, so the model is extrapolating. A linear-in-anomaly model cannot capture a threshold or a compounding effect, if one exists.

## 7. Lightning data

No open national lightning archive covers the 2026 season or earlier years.
- **ECCC "Lightning Density Data" (CLDN, 2.5 km, 10-minute; open.canada.ca dataset 75dfb8cb):** the MSC Datamart keeps dated folders only from 2026-09-22 (about 30 days).
- **GeoMet WMS layer Lightning_2.5km_Density:** the time dimension covers the last 3 hours.
- **Raw CLDN strokes:** not open.

Lightning-caused fire counts (agency cause codes) are used instead. They measure lightning that started a reported fire, not lightning itself. They therefore mix lightning frequency with how dry the fuel was and how fires were detected.

## What the data can and cannot say about causes

**Can say**
- Who started the fires that burned the area: lightning, 95% of 2026 area and most of every large year.
- That human-caused fires in 2026 were near people (median 4.9 km) and few.
- That 2026 had no excess of ignitions nationally.
- That drought covered an unprecedented share of the forest (in the 2003 to 2026 CDM record) in each of 2023 to 2026.
- That areas with deeper drought and more lightning fires burned more, within the record. These are associations, measured out of sample.

**Cannot say**
- **That drought caused the burns.** The drought shares, fire weather and burned area all respond to the same hot, dry weather. The CDM is an expert-blended map that may draw on impact reports, so partial circularity cannot be ruled out. The season-maximum CDM share includes August and September, after much of the burning.
- **Why the 2023 to 2026 run was so large.** The measured drivers underpredict it about 5 times beyond normal model bias. Something not in these data contributes: fire spread and suppression capacity, fuel structure, multi-day wind events, or nonlinear effects of drought beyond its historical range.
- **Anything about climate change.** No attribution was computed. The CDM record starts in 2003 and its northern coverage changed (territories from 2015), so no long-term drought trend is claimed.
- **Fire weather in the eastern boreal.** Station coverage is thin and southern. Station fire weather was normal at Thunder Bay and in Quebec, where large areas burned.
- **Fuel limitation as a general rule.** Heavily burned SK areas burned less than expected in 2026, but the panel-wide relation is positive.
- **Exact timing of area growth.** Report-date timing credits a fire's final size to its start date. The M3 satellite timing exists only from 2012.

## Method notes and caveats
- **Fire points**
  - CNFDB `NFDB_point_20260811`, 1990 to 2025, with 438 prescribed burns removed.
  - The 2026 list is the CWFIF API fire list: 5,474 fires reported in calendar 2026, 4,493,582 ha. It drops 42 holdovers from earlier years.
  - NT records carry a placeholder date (2026-01-01), so GNWT discovery dates were used (290 of 290 matched).
  - Points are assigned to areas by the 240 m grid of analysis/forest, then snapped within 10 km. 263 points (3,514 ha) fall outside all areas.
  - A fire's whole size counts at its origin point.
- **Population:** StatCan 2021 dissemination-area representative points with population above 0 (56,686), and population-centre representative points, in Canada Albers. In remote areas a DA point can be far from where people actually live.
- **Outcome**
  - NBAC 1972 to 2025 and CWFIS M3 2026. M3 maps 17.8% more than official totals nationally, so 2026 is scaled by province factors.
  - Forest is Land Cover 2020, so forest burned before 2020 and not yet regrown is not counted. This biases historical shares low.
- **Weather:** the consistent stations of analysis/weather (strict rule). 39 to 43 areas have a station each year.
- **Areas**
  - Quebec and Manitoba are single areas, which hides where in them it burned.
  - All scripts take `AREA_FILE=<gpkg>` (same columns as `fma_all.gpkg`). A new file gets its own `work/areas_<hash>/` cache: grid, area forest, fire assignment.
  - With a new area file, `02_areas.py` rebuilds the 240 m grid (uint16). Every later step then reruns unchanged.
- **Machine:** the machine is shared. `09_model.py` forces single-threaded gradient boosting; the full run takes about 2 minutes. `06_drought.py` takes about 35 minutes.

## Files
- **Inputs:** `data/fire/raw/nfdb/NFDB_point_txt.zip`; `season/nrcan_fire_list.json`; `season/nrcan_ytd_by-agency_..._group_by_cause_true.json`; `season/NFD_-_Area_burned_by_cause_class_-_EN_FR.csv`; `season/NFD_-_Number_of_fires_by_cause_class_-_EN_FR.csv`; `data/fire/raw/provincial/nt/nt_fires_points_2026.json`; `data/fire/raw/m3_2026/cwfis_firem3_estimated_cumulative_area_burned_by_day_*.csv`; `data/geo/statcan/da_2021_pop_points.gpkg`, `popcentres_2021_pop.gpkg`; `data/geo/fma_all.gpkg`; `analysis/forest/work/` (grid, forest counts, burn rasters); `analysis/forest/scaling_factors_by_province.csv`, `canada_forest_share_by_year.csv`; `analysis/weather/station_extreme_days.csv`, `work/site_year.pkl`, `work/national_by_year.csv`; `raw/cdm/` (new).
- **Scripts:** `scripts/common.py`, `01_download_cdm.sh`, `02_areas.py`, `03_fires.py`, `04_cause.py`, `05_timing.py`, `06_drought.py`, `07_burn_history.py`, `08_weather_panel.py`, `09_model.py`, `10_run_2023_2026.py`, `run_all.sh`.
- **Work:** `work/areas_<hash>/` (areas.csv, area_forest.csv, fires_all.pkl, logs).
