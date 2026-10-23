# Wildfire 2026: people, smoke and cost (original analysis of official data)

> **Rebuild 2026-10-21.** 2026 exposure, city nearest fire, reserves and First Nations distances and `city_search_table.json` were regenerated: 13 CWFIS M3 outlines classed agricultural/grass burn or military range with no agency-reported fire (analysis/outline-check) are excluded from all 2026 distance analyses (step `00c_outline_class.py`), the outline class is carried in `city_nearest_fire.csv` and the search table, and fire management areas come from `data/geo/fma_v2.gpkg` (no Parks Canada unit rows). The 2026 figures in the text below are pre-rebuild; current values and a before/after table are in `../REBUILD.md`. Pre-rebuild outputs are in `../_before_rebuild/people/`. 2023 to 2025 figures and smoke and cost sections are unchanged.

Analysis date 2026-10-21. Fire data to 2026-10-20, smoke data to 2026-10-19. All numbers below come from the files in this folder; scripts are in `scripts/` (run order 00, 00b, 01, 02y per year and threshold, 02, 03, 04, 06, 07).

## Scorecard

| Measure | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| People within 50 km, fires of 1,000 ha or more | 2,207,121 | 912,733 | 2,375,037 | 1,046,523 |
| People within 10 km, fires of 1,000 ha or more | 378,068 | 61,111 | 124,473 | 118,631 |
| People within 50 km, all outlines | 17,708,752 | 16,312,518 | 17,651,911 | 5,080,422 |
| Reserves within 10 km, all outlines | 825 | 641 | 870 | 330 |
| First Nation communities within 10 km, all outlines | 148 | 117 | 183 | 38 |
| City-days with PM2.5 above 27, 45 cities, Jan 1 to Oct 19 | 1,106 | 381 | 575 | 286 |

The "all outlines" rows are not comparable across years: 2023 to 2025 are NBAC burned areas (include thousands of small agency-mapped fires near towns), 2026 is CWFIS M3 hotspot outlines. The 1,000 ha rows are the like-for-like comparison.

## 1. Exposure (people living near fire outlines)

Findings
- In 2026, 199,805 people (0.54% of Canadians) lived within 10 km of a CWFIS M3 fire outline, 1,097,836 within 25 km and 5,080,422 (13.73%) within 50 km; 4,843 lived inside an outline.
- Most of the 2026 50 km figure comes from 80 small M3 outlines with no agency-reported fire within 5 km (49,257 ha, 0.9% of 2026 outline area), mainly spring prairie, farm and southern Ontario burns near Calgary, Edmonton, Winnipeg, Saskatoon, Ottawa and Toronto. Using only the 638 outlines matched to an agency-reported 2026 fire, 142,628 people were within 10 km, 679,285 within 25 km and 1,273,691 within 50 km.
- Counting only fires of 1,000 ha or more, 118,631 people were within 10 km in 2026, against 378,068 in 2023, 61,111 in 2024 and 124,473 in 2025. Within 50 km: 1,046,523 in 2026, 2,207,121 in 2023, 912,733 in 2024, 2,375,037 in 2025.
- By province in 2026 (all outlines), BC had 105,597 people within 10 km and 716,400 within 50 km; Manitoba 27,764 and 1,132,705; Ontario 26,067 and 1,102,629; Alberta 6,488 and 1,293,003; New Brunswick 16,354 and 266,103; Saskatchewan 12,534 and 465,338. Nunavut, PEI and Yukon had nobody within 50 km.
- With fires of 1,000 ha or more, BC accounts for 91,751 of the 118,631 people within 10 km in 2026 and 576,124 of the 1,046,523 within 50 km. Alberta had 14,384 people within 50 km of a 1,000 ha fire in 2026 against 628,155 in 2025; Manitoba 13,186 against 722,339.
- By fire management area (1,000 ha or more), BC's Kamloops Fire Centre had the most people near 2026 fires: 85,502 within 10 km, 381,299 within 25 km and 446,540 within 50 km (75.6% of its residents within 50 km). Next: New Brunswick (whole province; no sub-provincial boundary published) 266,103 within 50 km, SK Prince Albert protection area 67,271, BC Southeast Fire Centre 55,579, Quebec (whole province) 47,881.
- 174 DAs have no 2021 population (StatCan symbol ".."): 137 have their centre inside a reserve polygon and 22 more are within 2 km of one (ON 57, QC 49, BC 28, AB 21, MB 16, SK 3). In 2026, 45 of them were within 50 km of an outline and 8 within 10 km. They are listed in `da_no_population.csv` and counted in the `n_da_nopop_within_*` columns; their people are not in any population total.

Method
- Population: 57,932 StatCan 2021 dissemination areas (DA), population from table 98-10-0015 (total 36,991,981). A DA counts as within a band if its representative point (a point inside the DA polygon) is inside or within 10, 25 or 50 km of an outline; bands are cumulative.
- Fires: 2026 = CWFIS FireM3 perimeters stamped 2026-10-20 (718 outlines); 2023 to 2025 = NBAC 1972 to 2025 version 20260513, prescribed burns removed (2,237, 1,958 and 1,939 polygons).
- Distance: geometries in ESRI:102001 Canada Albers Equal Area. Outline boundaries densified to 200 m segments, nearest boundary vertex found with a KD-tree, then the GEODESIC distance (GRS80 ellipsoid) is computed between the query point and that vertex; 0 if the point is inside an outline (tested on the original polygons). Check against exact point-to-polygon geodesic distance on 400 random 2026 DAs: maximum difference under 1 m. Planar Albers distances differ from geodesic by a median 0.09% and at most 1.37%, which is why geodesic is reported.
- Fire size thresholds: total outline area per fire ID (equal-area), 200 ha and 1,000 ha. Agency match: an NRCan CWFIF 2026 fire-list point (5,451 points) inside or within 5 km of the outline.
- Fire management areas from `fma_all.gpkg` (agency rows; Parks Canada units reported separately because they overlap). Five DA points fell just outside agency polygons (generalisation slivers) and were assigned to the nearest one.
- Sensitivity: using the DA polygon edge instead of its point (any part of the DA within the band) raises the 2026 50 km figure from 5,080,422 to 5,384,602 (columns `*_da_polygon`).

Files: `exposure_by_area.csv` (2026; national, province, fire management area, Parks Canada unit), `exposure_years.csv` (2023 to 2026; national, province, FMA; all, 200 ha, 1,000 ha, agency-matched and DA polygon columns), `da_no_population.csv`.

## 1b. First Nations

Findings
- In 2026, 330 of 3,322 reserves were within 10 km of an outline, 714 within 25 km and 1,409 within 50 km; 66 reserves overlapped an outline. 38 of 638 First Nation communities (ISC band locations) were within 10 km, 100 within 25 km and 195 within 50 km; 3 were inside an outline (Boothroyd and Boston Bar in BC, Liidlii Kue in NT).
- With fires of 1,000 ha or more only, 2026 counts are 164 reserves and 22 communities within 10 km, 745 reserves and 114 communities within 50 km. Comparable 2023 counts were 301 reserves and 32 communities within 10 km; 2024: 130 and 15; 2025: 286 and 33.
- People living on reserve are 0.92% of Canada's 2021 counted population (339,951 people in 1,706 DAs whose centre lies in a reserve polygon). Among people within 10 km of a 2026 outline, 11.04% (22,066) live on reserve, 12.0 times their population share. Within 50 km the share is 2.13% (108,147), 2.3 times. With fires of 1,000 ha or more: 9.68% within 10 km, 5.85% within 50 km.
- The over-representation holds every year within 10 km: on-reserve share 4.68% (2023), 2.43% (2024), 3.47% (2025), 11.04% (2026); with 1,000 ha fires 8.60%, 9.09%, 20.89%, 9.68%.
- By province in 2026 (50 km): BC 649 of 1,602 reserves and 71 of 201 communities; SK 427 of 826 and 26 of 70; MB 262 of 420 and 34 of 63; ON 37 of 203 and 31 of 139.

Method: reserves = Aboriginal Lands of Canada (edition 2.189) polygons with ALTYPE "Indian Reserve"; distance from the reserve polygon edge (0 = overlap). Communities = ISC First Nations Location points. On-reserve population = DAs whose representative point lies in a reserve polygon.

Files: `first_nations_exposure.csv` (year x national/province x band 0/10/25/50 km; all outlines, 200 ha, 1,000 ha, 2026 agency-matched), `reserves_within_50km_2026.csv`, `fn_communities_within_50km_2026.csv`.

## 2. Population centres closest to 2026 fires

Findings
- Of the 30 largest population centres, Kelowna was closest to a 2026 outline: 11.2 km from its edge (fire north of the city, detected 2026-08-02 to 2026-08-12, 1,733 ha). Next with an agency-matched fire: Halifax 63.1 km, Vancouver 67.2 km, Abbotsford 80.0 km, White Rock 94.1 km, Moncton 107.9 km.
- Ottawa - Gatineau (20.4 km), Winnipeg (20.5 km), Calgary (27.0 km), Saskatoon (35.4 km) and Kanata (41.2 km) had small unmatched outlines (62 to 172 ha) closer than any agency-reported fire; their nearest agency-matched fires were 154.9, 214.7, 98.0, 85.6 and 169.4 km away. Both distances are in the table.
- 26 population centres (294,990 people) had an outline within 10 km of their edge, 76 (2,552,127) within 25 km and 171 (4,970,437) within 50 km. Counting only agency-matched outlines, 15 centres (223,737 people) were within 10 km, the largest being Fredericton (8.7 km), Vernon (6.7 km) and Penticton (6.9 km). Summerland, BC was the only centre touched by an outline.

Method: 1,026 StatCan 2021 population centres (boundary parts dissolved by PCUID, population table 98-10-0011). Exact point/polygon-to-polygon shortest line in Albers, length measured geodesically. Edge distance and distance from the centre's representative point, compass direction from the centre to the fire.

File: `city_nearest_fire.csv` (all 1,026, with `top30` flag).

## 3. Smoke

Findings
- Coverage: 67 of the 70 smoke towns have PM2.5 data; 53 have 2026 data and 52 of those meet the coverage rule in 2026. No adequate 2026 data for Winnipeg, Brandon, Thompson, Flin Flon, St. John's, Oshawa, Thunder Bay, Yellowknife, Inuvik, Norman Wells, Fort Smith, Fort Simpson, Penticton, Vanderhoof, Iqaluit; none at all for Kanata, White Rock, Fort Nelson.
- Across the 45 cities with adequate coverage in all nine years, there were 286 city-days above 27 ug/m3 from Jan 1 to Oct 19, 2026: fifth of nine years (2023: 1,106; 2025: 575; 2018: 449; 2021: 407; 2024: 381; 2022: 134; 2020: 90; 2019: 72). Days above 100: 32 in 2026 against 200 in 2023.
- Most 2026 days above 27: Kamloops 24 (13 above 60, 6 above 100, worst 191.7 on 2026-08-07), Castlegar 23, Vernon 17, Golden 15, Cranbrook 14, Calgary 13, Windsor 13.
- Southern Ontario had its worst day of 2018 to 2026 on 2026-07-16: Windsor 322.5, Sault Ste. Marie 290.0, London 277.0, Kitchener 207.5, Guelph 187.7, Milton 185.4, Hamilton 175.2, Toronto 144.6, Barrie 129.4, St. Catharines - Niagara Falls 109.5 ug/m3 (city mean; real-time data). The episode ran 2026-07-15 to 07-17 in Toronto (69.2, 144.6, 69.9).
- Windsor is the only adequately covered city where 2026 ranks first of nine years for days above 27 (13 days, no tie). Halifax also ranks first, but only because all eight of its covered years had 0 days (a tie).
- Among the 30 largest centres, Montréal, Victoria, Halifax, Moncton and Sherbrooke had no day above 27 in 2026; Ottawa - Gatineau and Québec had one each, both in February (winter, not fire season).

Method
- Daily 24 h mean PM2.5 per city = mean of reporting stations (NAPS validated where available, else AirNow real-time). NAPS days need 18 or more valid hours. Thresholds are strictly greater than 27, 60 and 100 ug/m3 on the city mean. 27 is the 2020 CAAQS 24 h value; the standard is a 3-year average of annual 98th percentiles, so a day above 27 is not a formal exceedance.
- Coverage rule: a city-year is adequate when at least 115 of the 153 days from May 1 to Sep 30 (75%) have a value. Ranks use adequate years only and Jan 1 to Oct 19 counts for every year (2018 to 2025 had 8 to 43 city-days above 27 after Oct 19).
- Data basis per city-year: 2018 to 2023 mostly validated (54 to 59 cities validated, rest mixed); 2024 45 validated, 8 mixed, 12 real-time; 2025 and 2026 all real-time.
- No smoke is attributed to any fire (no smoke model). Days above 27 also include winter inversion and wood-smoke days; May to Sep columns are provided.

Files: `city_smoke_days.csv` (city x year: counts all-year and May to Sep, worst day and value, worst station, coverage, data basis, 2026 rank and ties), `city_smoke_daily_2026.csv` (daily 2026 values and band for a calendar).

## 4. Cost

Findings (each province on its own definition; not comparable across provinces)
- BC (BCWS total cost, nominal): 2023 was the costliest season at $1,094.8M ($385 per hectare, $218.92 per resident). 2024 $769.4M ($712/ha); 2025 $510.0M estimate to 2025-11-01 ($841/ha, $101.98 per resident). 2026 forecast $849.7M (Budget vote $235.7M plus First Quarterly Report overspend $614.0M; a fiscal-year Fire Management line, not the BCWS total) on 479,325 ha preliminary: $1,773/ha, $169.91 per resident. Trend 2008 to 2025: +$36.4M a year (log-linear +11.5% a year); mean $187.7M in 2008 to 2016 against $571.7M in 2017 to 2025; cost tracks area burned (r = 0.92).
- Ontario (Emergency Fire Fighting, net of recoveries, actual): $273.0M in 2025-26, the highest of 2015 to 2025 ($454/ha, $19.19 per resident). Trend +$11.8M a year (+7.5% a year), r = 0.89 with area. 2026-27 not yet published.
- Alberta (all wildfire program lines, voted actuals): $953.6M in 2023-24 ($304/ha, $223.71 per resident), $858.7M in 2024-25, $925.5M in 2025-26 ($1,229/ha, $217.13 per resident). Trend +$61.5M a year (+10.7% a year), r = 0.74. FY2022-23 missing; 2026 not available.
- Saskatchewan (SPSA season costs in 2025 dollars): $351.6M in 2025 ($118/ha, $310.46 per resident), against $11.9M to $110.0M in 2016 to 2024. Trend +$23.0M a year (+27.2% a year), r = 0.93. 2026 cost not available (only the whole-agency 2026-27 budget, $76.3M, not used).
- Cost per hectare falls as seasons grow (fixed costs spread over more area): BC log-trend -4.4% a year, ON -1.3%, SK -4.8%, AB +0.8%. Medians: BC $1,135/ha, ON $1,039/ha, AB $1,161/ha, SK $118/ha.

Method: spending from `wildfire_spending_by_jurisdiction.csv` matched to NFD final area burned (1990 to 2025) and CIFFC/NRCan preliminary 2026 area; per resident uses 2021 Census province populations (table 98-10-0001; no newer StatCan estimate file is in the data folder). Trends are least-squares slopes over actual/estimate years (2026 forecast excluded). BC, ON and AB are nominal dollars; SK is 2025 dollars.

Files: `cost_per_hectare.csv`, `cost_trend_by_province.csv`.

## 5. City search table

`city_search_table.json` (and flat `city_search_table_flat.csv`): 1,031 records, the 1,026 population centres plus 5 smoke-monitor towns that are not population centres (Buffalo Narrows, Fort Chipewyan, Fort McKay, Fort Simpson, Norman Wells; distance from the station location). Each record: nearest 2026 fire (edge and centre km, direction, dates, outline ha, agency match, nearest agency-matched distance); smoke by year 2018 to 2026 where a monitor exists (67 records; Kanata and White Rock carry the Ottawa - Gatineau and Vancouver series, flagged `proxy: true`); province cost per resident for BC, ON, AB, SK (592 records), null elsewhere.

## Caveats

1. 2026 outlines are CWFIS M3 hotspot outlines: equal-area outline area is 5,303,030 ha, about 18% above the official 4,500,985 ha, so outlines sit slightly closer to people than true burned edges. NBAC 2026 does not exist yet.
2. M3 and NBAC are different products. NBAC includes many small agency-mapped fires near towns that hotspots miss, which is why "all outlines" exposure is 16 to 18 million for 2023 to 2025 and 5 million for 2026. Use the 1,000 ha columns for year comparisons.
3. M3 includes burns that are not agency-reported wildfires (80 unmatched outlines: prairie and farm burns, military ranges such as Petawawa, Gagetown and Shilo, possible industrial heat). Reported separately, not removed. Some unmatched outlines may still be real fires handled by municipalities.
4. Population is 2021 Census at 2021 locations. On-reserve population is understated: 174 DAs (mostly incompletely enumerated reserves) have no count, so on-reserve shares are lower bounds.
5. Reserve counts include many small, unpopulated reserve parcels (BC especially); community points are band office locations, not all settlements.
6. Distances are to outlines anywhere in the season; being within 10 km does not mean a community was threatened or evacuated.
7. Smoke 2025 to 2026 is real-time (unvalidated) AirNow data. AirNow agreed with NAPS for 2018 to 2024 (r 0.99 to 1.00, median absolute difference 0.06 to 0.09 ug/m3), but individual values can change on validation. Some extreme values repeat exactly (400.29 at both Yellowknife 2023-09-22 and North Bay 2023-06-25), possibly an instrument ceiling. No Manitoba, NWT or Nunavut real-time data after 2024.
8. Cost definitions differ by province and status (BC estimates and forecast, ON and AB actuals, SK restated 2025 dollars). BC 2026 is a forecast on a different line from the BCWS series. No CPI deflation applied to BC, ON, AB.
9. Area burned for 2026 is preliminary year-to-date (2026-10-20).
