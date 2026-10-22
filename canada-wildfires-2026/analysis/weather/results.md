# Fire weather in Canada's 2026 season: station analysis

> **Rebuild 2026-10-21.** Area summaries (`area_weather_2026.csv`, `area_grid_check.csv`, `fma_weather_for_join.csv`, `weather_vs_forest_by_fma.csv`, `work/summary_05.json`) were regenerated on `data/geo/fma_v2.gpkg` (186 areas; 54 with a consistent station). Station and national results are unchanged. Section 4 (forest join) now has results: see `../REBUILD.md`. Pre-rebuild outputs are in `../_before_rebuild/weather/`.

Source: CWFIS station Fire Weather Index (FWI) observations, 1990 to 2026-10-19, and CWFIS daily 2 km FWI grids, 2018 to 2026. Extreme means FWI 30 or more. High or above means FWI 19 or more. Season counts run from April 1 to October 19 every year. The normal is 1991 to 2020, with 1991 to 2025 also reported.

## Findings

### Station network and coverage
1. The archive has 2,873 station IDs. Joining replacement IDs within 5 km gives 2,339 sites. Of these, 116 sites in Canada meet the consistency rule (28 of 30 years, 1991 to 2020), and 103 of those 116 also meet the coverage rule in 2026. The median 2026 June to August coverage among the 116 is 100%.
2. The consistent stations are spread as follows: BC 25, ON 23, AB 15, SK 14, QC 12, MB 8, NB 4, NS 4, NT 4, YT 4, NL 2, PE 1, NU 0.
3. Under a relaxed rule (24 of 30 years), 276 sites qualify and 253 of them have usable 2026 data. Without joining replacement IDs, only 52 sites meet the strict rule and 37 have usable 2026 data.

### 1. Extreme days per station (103 stations)
4. Across the 103 stations, 2026 averaged 12.0 extreme days against a 1991 to 2020 normal of 11.4 days. That is a pooled ratio of 1.05 and ranks 2026 15th of 36 years (1991 to 2026) on mean extreme days.
5. 30 stations had more extreme days than their own normal in 2026 and 73 had fewer.
6. Only 1 of 103 stations had its most extreme year on record in 2026. Kamloops A had 118 extreme days, against a normal of 59.6 and a previous maximum of 110. Five stations placed 2026 in their top three years: Kamloops A, Princeton CS, Fort Simpson A, Yellowknife A, and Parent (QC, which only counts because it tied at 0 days).
7. For high-or-above days (FWI 19 or more), 2026 averaged 31.1 days against a normal of 30.8 (pooled ratio 1.01). One station set a record: Nanaimo A.

### 2. By province and fire management area
8. Nationally, the median station ratio of 2026 extreme days to normal is 0.64 against the 1991 to 2020 normal, and 0.61 against the 1991 to 2025 normal. Because the counts are skewed, the median ratio sits below 1 in a typical year: its median value across 1991 to 2020 is 0.62. 2026 ranks 20th of 36 years on this measure. By pooled ratio, the five highest years are 2021 (2.00), 2025 (1.72), 2001 (1.72), 2017 (1.66) and 2015 (1.59). 2023 scores 1.54 and 2026 scores 1.05.
9. The Northwest Territories is the only province or territory where the median station ratio is well above normal. The ratio is 2.53 across 4 stations (pooled 2.32), with 22.8 extreme days on average against 9.8 normal. No NT station set a record.
10. British Columbia has a median ratio of 0.77 but a pooled ratio of 1.43 (21.9 days against 15.3). The surplus is concentrated in the southern interior, and 1 of its 20 stations (5%) set a record.
11. Median ratios elsewhere: Saskatchewan 0.96 (14 stations), Alberta 0.85 (13), Manitoba 0.80 (8), New Brunswick 0.78 (4), Nova Scotia 0.52 (3), Ontario 0.37 (20), Yukon 0.06 (4), Quebec 0.00 (10), Newfoundland and Labrador 0.00 (2), PEI 0.00 (1). No station outside BC set a record.
12. Quebec's 10 consistent stations averaged 0.7 extreme days in 2026 against 1.9 normal (pooled ratio 0.37). Ontario's 20 averaged 1.6 against 2.9 (pooled ratio 0.53).
13. 42 of 99 fire management areas contain at least one consistent station (56 under the relaxed rule). The largest 2026 surpluses in median extreme days were:
    - Kamloops Fire Centre: +57.9 days (ratio 1.98, 3 stations)
    - North Slave: +23.2 (2.68, 1 station)
    - Deh Cho: +19.2 (4.31, 1 station)
    - South Slave: +4.7 (1.65, 2 stations)
    - Southeast Fire Centre: +4.4 (1.25, 3 stations)
    - Sioux Lookout: +3.1 (2.07, 1 station)
14. The largest 2026 deficits were:
    - Big River, SK: -12.4 days
    - Peace River Forest Area: -8.8
    - Dorintosh: -8.7
    - Fort McMurray Forest Area: -6.9
    - Dawson: -6.9
    - Prince George Fire Centre: -6.3

### 3. Timing
15. Nationally, the busiest 2026 day was May 26. That day, 24.3% of the 103 stations were at extreme FWI, against a 1991 to 2020 average of 6.1% for the date. The busiest 7-day window was centred on May 28, at 17.3% against 7.4%.
16. The national peak run was May 25 to May 27, 2026: three consecutive days above the 1991 to 2020 90th percentile for those dates. Over the season, 18 days were above the 90th percentile and 3 were above the 1991 to 2020 maximum.
17. Over the whole season, the national daily share at extreme FWI averaged 5.9% in 2026 against 5.6% normal. The 1991 to 2020 average curve peaks on July 30, so 2026's national peak came about two months earlier than the climatological peak.
18. The late-May peak was a Prairie event:
    - Saskatchewan peaked on May 26 at 85.7% of 14 stations (normal 13.4%), with a run above the 90th percentile from May 26 to May 29.
    - Manitoba peaked on May 26 at 50% of 8 stations, with a run from May 26 to May 29.
    - Alberta's single highest day was May 11 (76.9% of 13 stations, normal 13.8%). Its longest run above the 90th percentile was May 25 to May 27.
19. British Columbia peaked on June 24 at 50% of 20 stations (normal 7.7%), with a run from June 22 to June 25. It had 33 days above the 90th percentile and 11 days above the 1991 to 2020 maximum, the most of any province. Its longest run was early, from April 22 to April 27.
20. The Northwest Territories peaked on June 29, when all 4 stations were extreme (normal 12.5%). Its run lasted from June 29 to July 3, and it had 25 days above the 90th percentile.
21. Ontario peaked on June 5 at 15% of 20 stations (normal 0.8%), with a run from June 3 to June 5. Quebec peaked on June 4 at 30% of 10 stations (normal 1.0%), a single day.

### 4. Does weather explain where it burned
22. A rank correlation could not be computed. No fire-management-area table of forest share burned existed in analysis/forest/ when this run finished. The weather side is saved as fma_weather_for_join.csv (key fma_id). Running scripts/05_join_forest.py once that file exists will join it and report Spearman correlations.
23. One pattern is visible without the join. The station anomalies are highest in the NT and the BC southern interior. They are below normal in Ontario and Quebec, where the official 2026 area burned is large (about 749,000 ha and 754,000 ha according to the reference files in data/fire). Station fire weather therefore does not line up with burned area in eastern Canada. Network coverage is part of the reason (see caveat 1).

### 5. Spatial check with grids (short 2018 to 2025 baseline, check only)
24. Across 1.65 million 2 km cells in Canada, 2026 averaged 4.43 extreme days per cell against a 2018 to 2025 mean of 6.68 (ratio 0.66). In 1.9% of cells, 2026 was the highest year from 2018 to 2026.
25. Grid ratios of 2026 to the 2018 to 2025 mean, by province: NT 1.43, NL 1.09, BC 0.78, ON 0.71, AB 0.64, QC 0.56, SK 0.53, MB 0.37, YT 0.28, NU 0.27.
26. The 2018 to 2025 baseline contains 2021, 2023 and 2025, three of the most extreme station years since 1991. That is why the grid ratios run lower than the station ratios against 1991 to 2020. The ordering agrees: NT stands out on both.
27. Grid extreme days at the station cells match the station counts closely (Spearman 0.98 across 99 stations). This is expected, because the grid is interpolated from stations. Across the 42 fire management areas with stations, the station anomaly and the grid anomaly have a Spearman correlation of 0.55.

## Method
- **Data:** CWFIS station FWI v3.0 archive files for the 1990s to the 2020s (to 2026-09-30), plus the CWFIS daily files for 2026-10-01 to 10-19. The 2026-10-20 file is a partial day and was dropped.
- **Duplicate handling:** duplicate station-days were removed. From 2015 the archive also contains provincial agency stations ("ProvFwi").
- **Joining replacement station IDs:**
  - Station IDs whose coordinates are within 5 km of each other are joined into one site.
  - Each day takes the FWI from the member ID with the longest record that reported that day.
- **Coverage rule:**
  - A site-year qualifies if FWI was computed on at least 90% of days from June 1 to August 31 and at least 75% of days from May 1 to September 30.
  - A site is consistent if it qualifies in at least 28 of the 30 years from 1991 to 2020. A relaxed 24-of-30 rule is reported for sensitivity.
  - The suggested test of 90% of days from April 1 to September 30 could not be used. FWI is not computed before the snow-free start-up date, so no station passes that test in 28 of 30 years (0 sites; even 25 of 30 gives 4).
- **Counting:**
  - Extreme days (FWI 30 or more) and high-or-above days (FWI 19 or more) are counted per qualifying site-year. Days without a computed FWI count as not extreme.
  - Each station's normal is its mean over qualifying years. Rank compares 2026 with all qualifying years from 1991 to 2026, where 1 means most days. Tied years share the best rank.
  - A record means rank 1 with more than 0 days.
- **Summaries:**
  - Province and fire management area are assigned by the nearest non-park area polygon (polygons simplified to 500 m). Sites more than 20 km outside Canada (US stations) are dropped.
  - Area statistics use stations with usable 2026 data: median ratio, pooled ratio (sum of 2026 days divided by sum of normals), median anomaly in days, and share of stations at a record.
- **Daily share:**
  - The daily share is the share of the 103 stations at FWI 30 or more each day, using the same station set every year. The denominator is the stations that qualify that year.
  - The normal curve is the 1991 to 2020 mean for each calendar day, with the 90th percentile and maximum for that day also given. Provinces with fewer than 4 stations are omitted.
  - A peak run is consecutive days above the 1991 to 2020 90th percentile for the date.
- **Grids:**
  - Extreme days per 2 km cell from April 1 to October 19. A cell-year is used only if it has a value on at least 90% of the June to August grids.
  - The baseline is the 2018 to 2025 mean and needs at least 6 usable years.

## Files (analysis/weather/)
- **station_extreme_days.csv:** one row per site. The rule column is strict_28of30, or relaxed_24of30_only for the extra relaxed sites. Columns include coverage, 2026 counts, normals, ratios, ranks, record flags, member IDs, and the share of 2026 days taken from a replacement ID.
- **area_weather_2026.csv:** national, province and fire management area summaries for both rules. All 99 areas are listed, including those with 0 stations.
- **daily_extreme_share.csv:** daily 2026 share, 7-day mean, 1991 to 2020 mean, 90th percentile and maximum, and 1991 to 2025 mean, for CA and each province with at least 4 stations.
- **stations_2026_anomaly.geojson:** 103 stations for the site, with these fields: ext26, ext_norm, ratio, anom, rank, nyrs, record, hi26, hi_norm.
- **fma_weather_for_join.csv:** station and grid anomaly per fire management area, keyed on fma_id, for the forest join.
- **area_grid_check.csv** and **grid_extreme_days_2026.tif:** grid check. The .tif has 4 bands: 2026 days, baseline x10, anomaly x10, and a flag for 2026 being the highest year.
- **work/:** includes national_by_year.csv (the same national statistics for each year from 1991 to 2026), thread_check.csv, the sens_nothread/ sensitivity run, summary JSON files and logs.
- **scripts/:** run_all.sh runs 00 to 05 in order.

## Caveats
1. **The network does not sample where eastern fires burned.** The 103 long-record stations are mostly airports in the south. Quebec has one area (the whole province) with 10 stations, all in the south. As a check, Quebec's stations gave a pooled ratio of only 1.04 in 2023, a record burn year in Quebec (NBAC: 4.26 million ha, the highest since 1972). The Ontario and Quebec station results describe the populated south, not the northern boreal forest.
2. **Joining replacement IDs matters.** 46 of the 103 stations take more than half of their 2026 days from a replacement ID. Where two co-located IDs overlap with full seasons, their extreme-day counts differ by a median of 3.0 days a season (mean difference -0.6). Kamloops' 2026 value comes from ID 1163842, which averaged 4.6 more extreme days than the old ID in 8 overlap years. Even after subtracting that, 2026 (about 113) stays above the old maximum (110). Without joining IDs, the national result is 37 stations with a median ratio of 0.76 and a pooled ratio of 1.24 (12th of 36). The conclusion that 2026 was near normal nationally holds either way.
3. **Small samples:** NT, YT and NB have 4 stations each, NL 2, PE 1 and NU 0. NT's ratio rests on 4 stations, and its single-area results rest on 1 or 2.
4. **The median ratio sits below 1 in an ordinary year** because extreme-day counts are skewed, so always read it next to the typical-year value (0.62) or the pooled ratio.
5. **Season definition:** counts stop on October 19. FWI before snow-free start-up is not computed and is treated as not extreme.
6. **Grid limitations:**
   - Grids are stored as integers, so values from 29.5 to 29.9 count as 30.
   - Three daily grids are missing: 2024-04-05, 2025-06-20 and 2026-05-10.
   - Cell means are unweighted on a conformal projection.
   - The grid is interpolated from the same stations (plus agency stations), so it is not independent evidence.
7. **Area assignment:** fire management area boundaries were simplified to 500 m, so a station within about 500 m of a boundary could fall in the neighbouring area. National park polygons were not used.
8. **No forest join:** the forest-burned share was not available, so analysis 4 is not complete.
