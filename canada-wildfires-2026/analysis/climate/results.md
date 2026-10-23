# Winter-to-spring climate chain and area burned, Canada 1991 to 2026

Original analysis of raw official data downloaded 2026-10-21: NOAA CPC and PSL climate indices, ECCC daily station climate data (MSC GeoMet API), ECCC CanSWE snow survey data. Outcome: share of forest burned and hectares burned per fire management area and year, recomputed from the analysis/forest burn rasters (NBAC 1991 to 2025, CWFIS M3 outlines 2026; matches analysis/forest to 1e-14). Folder: analysis/climate/. Panel for the cause model: climate_panel.csv.

## Scorecard

- The 2023 to 2026 run was unusually dry, not unusually low in snow everywhere. Nationally (median across the 99 areas), its 4-year mean was the most fire-favouring 4-year window since 1991 (rank 1 of 33) for 12-month precipitation (87% of normal), previous-summer rain (85%), previous-fall rain (76%), winter snowfall (84%) and months since a wet month; 2nd for winter precipitation (88%); 3rd for April to June rain (90%); 4th for spring heat (+0.54 C) and melt date (4.8 days early).
- 2026 itself was not a classic low-snow, hot-spring year outside BC and the Northwest Territories. Nationally the median area had more snow than normal (snowfall 108%, maximum depth 114%), a normal melt date and a slightly cool spring (-0.4 C). What 2026 shared with 2023 to 2025 was a dry previous fall (76% of normal nationally; 30 of 98 areas had a top-5 driest fall) and a dry previous summer (81%; 32 of 88 areas top-5 driest).
- Across 74 fire-prone areas, 1991 to 2025, the variables that track area burned within an area are spring rain (within-area rank correlation r = -0.25), 12-month precipitation (-0.26), spring temperature (+0.23), previous-summer and previous-fall rain (-0.12, -0.11), months since a wet month (+0.11), snowfall (-0.13) and melt date (-0.12). All pass a 10% false discovery rate.
- Winter climate indices (ENSO, AO, NAO, PDO in winter, the polar vortex proxy) do not predict area burned directly in any region (all |r| at most 0.16, none passes the false discovery rate). Winter ENSO does shift BC snow and spring heat strongly (El Nino: less snow, r = -0.42; earlier melt, -0.38; warmer April to June, +0.48), but that link does not carry through to BC area burned (r = +0.03).
- Spring PDO is the one index with a consistent sign: a negative spring PDO goes with more burning in BC (r = -0.28) and the Prairies (-0.24), not passing the false discovery rate (q = 0.17, 0.12). The 2023 to 2026 spring PDO mean (-1.63) is the 3rd lowest 4-year window since 1951.

## 1. Climate indices, winters 2022-23 to 2025-26

Files: indices_by_fire_year.csv, indices_2023_2026.csv, run_windows_2023_2026.csv. Ranks are among fire years 1951 to 2026 (76 years, 1 = highest value); z is against 1991 to 2020.

- ENSO (ONI, December to February): 2023 -0.55 (La Nina), 2024 +1.84 (El Nino, 4th highest of 76), 2025 -0.46 (neutral), 2026 -0.39 (neutral). In winter 2025-26 the ONI was -0.57, -0.61 and -0.60 in SON, OND and NDJ 2025, then rose to -0.39 in DJF; that is three seasons at La Nina strength, short of the five overlapping seasons CPC uses for an episode. The ONI then climbed to +0.46 in MAM and +2.16 in JAS 2026 (El Nino developing during the fire season). The 4-year DJF mean (+0.11) is ordinary (rank 29 of 73 windows).
- PDO: strongly negative throughout. DJF: 2023 -1.35, 2024 -1.39, 2025 -1.33, 2026 -1.06. MAM: 2023 -2.11 (lowest of 76), 2024 -1.86 (3rd lowest), 2025 -1.17, 2026 -1.40. The 4-year means rank 71 of 73 windows (3rd lowest) for both DJF and MAM.
- Arctic Oscillation (DJF): 2023 -0.60, 2024 +0.07, 2025 -0.42, 2026 -1.01 (z -1.0; January 2026 -2.05, February -1.26). Spring AO 2026 was +0.95 (6th highest). The 4-year DJF mean (-0.49) is rank 44 of 73.
- NAO (DJF): +0.68, +1.08, +0.76, -0.11. Spring NAO 2026 +1.11 (3rd highest of 76).
- Polar vortex: the planned measure (NCEP/NCAR R1 zonal-mean wind, 10 hPa, 60N) could not be downloaded; the PSL THREDDS server and the PSL time-series service returned HTTP 503 or no data all day on 2026-10-21. The documented proxy is the January to March mean AO (column vortex_jfm, vortex_source says which was used): 2023 +0.40, 2024 -0.06, 2025 -0.13, 2026 -0.42, 4-year mean -0.05 (rank 27 of 73). The AO is a tropospheric measure; it follows stratospheric vortex anomalies with a lag of weeks, but it is not the vortex itself. Rerunning scripts/run_all.sh picks up the real series automatically when the server responds.

## 2. Winter and spring 2026 by region

Files: ranks_2026.csv (long), area_2026_summary.csv (wide), region_2026_summary.csv. Region value = median across areas of the area anomaly. Rank: 1 = most fire-favouring year of 1991 to 2026 (least snow, earliest melt, warmest, driest, longest since a wet month).

- BC: the only region with the low-snow, warm, dry spring pattern. Snowfall 69% of normal, maximum depth 63%, April to June temperature +1.2 C, April to June rain 65% (median area rank 2 of 36; 5 of 6 fire centres in their 5 driest springs). Kamloops: rain 53% (rank 2), temperature +1.6 C (rank 3), maximum depth 67% (rank 3). Cariboo: 12-month precipitation 76% (rank 2), temperature +1.5 C (rank 3), snowfall 70% (rank 6).
- North (YT, NT, NU): little snowfall (67%) but deep maximum snow (115%), normal melt, normal spring temperature (-0.1 C), and long-running dryness: previous-summer rain 48% of normal (median area rank 4; 9 of 12 areas in their top 5 driest), 12-month precipitation 79%. North Slave (Yellowknife area): April to June rain 32% (rank 3 of 35), previous summer 38% (rank 4), 12-month 52% (rank 3), 27 months since a wet month (rank 1, longest since 1991). Deh Cho: previous-summer rain 26% (rank 1), 12-month 49% (rank 1), spring rain 44% (rank 2), snow cover 11 days short (rank 2). Both rest on one station each.
- Ontario: snowy winter (maximum depth 134%, snow cover +17 days), slightly cool spring (-0.4 C), spring rain 82%, previous fall 75%, 12-month 90%. Thunder Bay: maximum depth 142% (rank 33 of 34, among the deepest), spring -0.6 C, but spring rain 83% (rank 10) and 12-month precipitation 74% (rank 3 of 34). Sioux Lookout: deepest snow since 1991 (148%), spring rain 79% (rank 13), previous fall 68% (rank 10). Fort Frances: winter precipitation 39% (rank 3), spring rain 81% (rank 10). In Ontario, 2026's large burns did not follow a low-snow or warm spring; they followed a dry fall and a dry spring.
- Prairies: snowy (snowfall 127%, maximum depth 124%), melt 8 days late, spring -0.4 C, spring rain 105%; previous fall 70% (10 of 25 areas top 5 driest). Manitoba: previous-summer rain 63%, the driest since 1991 (rank 1 of 36).
- Quebec (one area, stations in the south): snow near normal, spring +0.1 C, spring rain 123% (rank 33, wet), previous fall 70% (rank 2 of 36), winter precipitation 86% (rank 7).
- Atlantic: snowfall 118%, spring -0.7 C, spring rain 103%, previous summer 73% (17 of 30 areas top 5 driest). NL district 22 (record 2026 burn share in analysis/forest): spring rain 58% (rank 4), winter precipitation 47% (rank 3), 11.5 months since a wet month (rank 3).
- Canada (median of 99 areas): 3 of 99 areas had a top-5 warmest spring, 13 of 95 a top-5 driest spring, 32 of 88 a top-5 driest previous summer, 30 of 98 a top-5 driest previous fall, 18 of 91 a top-5 driest 12 months.

## 3. The 2023 to 2026 run against earlier decades

Files: run_2023_2026_by_region.csv (median area value and share of areas on the fire-favouring side, each year and each decade), run_windows_2023_2026.csv (rank of the 4-year mean among the 33 windows ending 1994 to 2026).

National medians, each year 2023, 2024, 2025, 2026 (1991 to 2020 median in brackets):
- Snowfall % of normal: 85, 67, 75, 108 (101). Maximum snow depth %: 104, 72, 88, 114 (97).
- Melt date anomaly (days): -9.1, -7.0, -3.2, 0.0 (-0.2).
- April to June temperature anomaly: +0.8, +1.0, +0.7, -0.4 C (-0.2). Share of areas warmer than their own median: 85%, 88%, 97%, 42%.
- April to June rain %: 81, 103, 79, 98 (98).
- Previous-summer rain %: 88, 87, 86, 81 (99). Previous-fall rain %: 72, 74, 83, 76 (98). 12-month precipitation %: 81, 88, 84, 94 (99). In every one of the four years the national previous-summer, previous-fall and 12-month values were below the 1991 to 2020 median.

The 4-year window, rank among 33 (1 = most fire-favouring):
- Canada: snowfall 1, 12-month precipitation 1, previous summer 1, previous fall 1, months since wet 1, winter precipitation 2, spring rain 3, spring temperature 4, melt date 4; maximum depth 13, snow-cover days 20 (not unusual).
- BC: snowfall 1, maximum depth 1, spring rain 1 (75%), previous fall 1, 12-month 1, CanSWE 1 April SWE (2022 to 2025) 2, previous summer 3, winter precipitation 4, spring temperature 5. BC is the region where the whole chain (low snow, warm, dry) lined up.
- Prairies: spring temperature 2 (+0.87 C), previous summer 2, previous fall 2, months since wet 2, 12-month 3; snow not unusual (snowfall 13, maximum depth 22).
- Ontario: previous fall 1, 12-month 1, spring rain 3, winter precipitation 6, previous summer 6, melt 8, spring temperature 9; snow-cover days 24 and maximum depth 22 (snowy).
- Quebec: previous fall 1, winter precipitation 3, spring temperature 4, maximum depth 5, snow-cover days 6; spring rain 27 and previous summer 33 (wet), so the Quebec station record (southern Quebec) does not show a dry run except in fall and winter.
- North: snowfall 1 (64%), previous summer 1 (66%), 12-month 1 (80%), spring temperature 5; maximum depth 28 (deep).
- Atlantic: previous fall 1, 12-month 1, CanSWE SWE 1 (60% of normal, 2022 to 2025), snowfall 2, melt 3 (7.8 days early), snow-cover days 4, maximum depth 5.
- Decades for comparison (national median): 2011 to 2020 snowfall 105%, previous-fall rain 99%, 12-month 100%, spring temperature -0.1 C. No earlier decade mean is far from normal; for 12-month, previous-summer and previous-fall precipitation the 2023 to 2026 departures are the largest 4-year departures since 1991.

## 4. Relationships with area burned (1991 to 2025)

Files: correlations_burn.csv (294 tests), correlations_chain.csv (399 tests). Statistic: within-area rank correlation r_w (each variable converted to its percentile rank among the area's own years, then pooled; this removes area fixed effects). Sample: 74 areas with at least 100,000 ha of forest and burning in at least 5 of the 35 years (Prairies 24, North 16, Ontario 15, Atlantic 12, BC 6, Quebec 1), up to 2,590 area-years. p-values: 999 permutations of year labels applied to all areas at once (so the effective sample is about 35 years, not 2,590 area-years); 95% intervals: 1,000 bootstrap resamples of years; q: Benjamini-Hochberg false discovery rate within each family.

Canada, outcome share of forest burned (r_w, 95% interval, p, q):
- 12-month precipitation -0.26 (-0.33 to -0.18), p 0.001, q 0.013; 61 of 74 areas negative.
- April to June rain -0.25 (-0.32 to -0.18), p 0.001, q 0.013; 65 of 74 negative.
- April to June temperature +0.23 (0.12 to 0.32), p 0.001, q 0.013; 66 of 74 positive.
- Snowfall -0.13 (-0.20 to -0.05), p 0.008, q 0.053. Melt date -0.12 (-0.20 to -0.05), p 0.006, q 0.042 (earlier melt, more burning).
- Previous-summer rain -0.12, previous-fall rain -0.11, months since a wet month +0.11 (q 0.02 to 0.03).
- Maximum snow depth -0.06, snow-cover days -0.07, CanSWE 1 April SWE -0.08, winter precipitation -0.09: not significant.
- Indices: ONI DJF +0.03 (p 0.71), PDO DJF -0.08, AO DJF -0.12 (p 0.09, q 0.28), NAO DJF +0.03, vortex proxy -0.09, PDO MAM -0.15 (p 0.02, q 0.11).
- log10 hectares burned gives the same picture (r_w within 0.04 of the forest-share values nationally).

By region (share of forest burned; * = q below 0.10):
- BC (6 areas): spring rain -0.39*, 12-month -0.37*, spring temperature +0.34*, PDO MAM -0.28, winter precipitation -0.21, previous summer -0.20, SWE -0.20, melt -0.15, snowfall -0.12, ONI DJF +0.03.
- Prairies (24): 12-month -0.38*, spring rain -0.33*, spring temperature +0.22*, months since wet +0.21*, previous fall -0.21*, previous summer -0.19*, winter precipitation -0.19*, PDO MAM -0.24, snowfall -0.14.
- Ontario (15): spring temperature +0.28*, spring rain -0.26*, 12-month -0.26*, melt date -0.19*, snowfall -0.15, AO DJF -0.15.
- North (16): spring temperature +0.24*, melt date -0.24* (7 areas), 12-month -0.22*, spring rain -0.16.
- Quebec (1 area, 35 years): nothing passes; largest are maximum depth -0.38 and spring NAO -0.36. Southern stations do not sample the northern forest where Quebec burns (see analysis/weather caveat 1).
- Atlantic (12): nothing passes; largest is spring rain -0.13. Burns are small and sporadic in most NL districts.

## 5. The chain step by step

Within-area rank correlations, 1991 to 2025, all areas with data (correlations_chain.csv).

Step 1, winter index to snow and spring:
- ENSO (DJF ONI) matters in the west and north. BC: El Nino winters bring less snowfall (-0.42*), fewer snow-cover days (-0.52*), less depth (-0.33*), earlier melt (-0.38*) and warmer April to June (+0.48*; with spring ONI +0.58*). North: warmer spring (+0.44*). Quebec: less snowfall (-0.43*). Prairies, Ontario, Atlantic: weak (|r| at most 0.27, none significant).
- PDO (DJF): BC fewer snow-cover days (-0.41*); North fewer snow-cover days (-0.30*) and less SWE (-0.34*). Spring PDO: cooler spring in Quebec (-0.47*) and Atlantic (-0.40*) when positive.
- AO, DJF, and the vortex proxy (AO JFM): east-side effects. Atlantic: positive winter AO goes with more snowfall (+0.28*) and later melt (+0.38*); vortex proxy with later melt in Quebec (+0.43*) and Atlantic (+0.36*) and a cooler spring in the Atlantic (-0.45*; Canada -0.28*). Spring NAO: cooler spring nationally (-0.30*), Quebec (-0.47*) and Atlantic (-0.46*).
- The same index has opposite or no meaning across regions: ONI to snowfall is -0.42 in BC and -0.02 in the Atlantic; ONI to spring temperature is +0.48 in BC and -0.26 in the Atlantic; PDO DJF to snow-cover days is -0.41 in BC and +0.29 to +0.41 in Ontario and Quebec (not significant).

Step 2, snow to melt to spring: more snowfall means later melt (Canada +0.26*, BC +0.53*, Ontario +0.38*); deeper snow, later melt (+0.19*, BC +0.45*). Earlier melt goes with a warmer April to June in every region (Canada -0.49*, Quebec -0.75*); this is partly the same weather (a warm spring melts snow early), not only a lagged effect. Melt date has no link to spring rain (Canada +0.04). Winter precipitation drives snowfall (+0.56*) and depth (+0.45*). In BC, warm springs are also dry springs (-0.39*); elsewhere not.

Step 3, to area burned: spring rain and 12-month precipitation (-0.25, -0.26) and spring temperature (+0.23) are the strongest links; snow and melt are weaker (-0.12 to -0.13) and depth, cover days and SWE are not significant.

Through the whole chain: indices do not reach area burned. In BC the path ENSO to spring temperature (+0.48) to burn (+0.34) would imply about +0.16 if it were the only path; the observed ONI to burn correlation is +0.03 (interval -0.23 to +0.27, 6 areas, 35 years). With 35 years the data cannot separate a real +0.1 to +0.15 link from zero.

## 6. Multiple testing and strength

- Burn family: 294 tests; 65 have p below 0.05 (about 15 expected by chance); 51 pass a 10% false discovery rate. Chain family: 399 tests; 86 below 0.05 (about 20 expected); 54 pass. The national precipitation and temperature results (q 0.013) are robust to the testing burden; regional index results are not.
- Correlations of 0.2 to 0.4 mean that a single climate variable explains roughly 4% to 15% of the year-to-year ranking of burn within an area. Most of the variation is elsewhere (ignition, summer weather, fire suppression, fuel and past burns), which is what the cause model adds.

## 7. What the data can and cannot say

Can:
- Rank each area's 2026 and 2023 to 2026 winter, spring and multi-season precipitation against its own 1991 to 2026 history, with station counts.
- Show that the 2023 to 2026 run stands out nationally for multi-season dryness (the most extreme 4-year window since 1991 for 12-month, previous-summer and previous-fall precipitation) more than for snow.
- Show that spring rain, 12-month precipitation and spring temperature track area burned within areas, consistently in sign across BC, the Prairies, Ontario and the North.

Cannot:
- Say that ENSO, AO, NAO, PDO or the polar vortex cause or predict area burned: no index passes the false discovery rate for burn in any region, and 35 years (one value per year shared by all areas) is a small sample. A negative spring PDO is the most consistent candidate (BC -0.28, Prairies -0.24) and needs a longer record.
- Describe the polar vortex directly: the 10 hPa wind series could not be downloaded; the AO proxy is a surface measure.
- Describe northern Quebec, northern Ontario or Labrador snow and rain well: long-record stations are mostly airports in the south (analysis/weather caveat 1 applies). Quebec is one area with all stations south of about 50N. Several northern areas rest on one station (North Slave, Deh Cho), or on the nearest stations up to 250 km away (basis = nearest).
- Compare 2026 burn to earlier years on the same product: 2026 burn is CWFIS M3 outlines (larger than official totals by 18% nationally), earlier years NBAC; 2026 is ranked but not used in the correlations.
- Give 2026 snow water equivalent: CanSWE ends in 2025.
- Separate cause from co-occurrence in the snow-melt-temperature step: early melt and a warm spring are largely the same weather.

## Method

- Areas: the 99 non-park rows of data/geo/fma_all.gpkg (set AREA_FILE for another layer; area-dependent results then go to work/areas_<hash>/ so the main files are not overwritten; scripts/run_all.sh --areas-only reruns 05 to 08).
- Stations: ECCC climate station inventory (8,435 stations). Climate IDs within 5 km and 100 m elevation are joined into one site (as in analysis/weather); for each day and variable the member with the longest record supplies the value, others fill gaps. 671 candidate sites (1,591 IDs) whose combined daily records cover at least 85% of June 1990 to June 2026 and report to at least June 2026 were downloaded. A site is used for a variable if it has a valid value in at least 24 of the 30 fire years 1991 to 2020: snowfall 206 sites, maximum depth 194, snow-cover days 144, melt date 102, spring temperature 464, spring rain 386, previous summer 405, previous fall 375, winter precipitation 314, 12-month 221, months since wet 434 (28-of-30 counts are in work/station_normals.csv: for example melt date 35, spring temperature 291).
- Fire year y: winter November y-1 to April y; DJF = December y-1 to February y; spring April to June y; previous summer June to August y-1; previous fall September to November y-1; winter precipitation November y-1 to March y; 12-month July y-1 to June y.
- Variables: snowfall total November to April (at most 10% days missing); days with snow on ground of at least 1 cm, November to April (at most 10% missing, scaled); maximum snow depth November to April (at most 20% missing); melt date = day after the last day with snow on ground between November 1 and July 31 (at most 15% missing February to June, at least 5 reports in the 14 days after); April to June mean of daily (max+min)/2 (each month at most 5 days missing); precipitation totals from months with at most 3 missing days; months since a wet month counted back from May (wet = at least 125% of that calendar month's 1991 to 2020 mean; up to 2 missing months skipped). CanSWE: 1 April SWE = measurement nearest 1 April within 10 days, stations with 20 of 30 normal years and normal at least 10 mm (650 stations).
- Quality control: snow-on-ground years with a 0 cm maximum at sites whose usual maximum is at least 10 cm (290 site-years) and 0 cm snowfall years that contradict depth or the site's usual snowfall (63) set missing; melt dates more than max(5 scaled MADs, 30 days) from the site median set missing (19, for example Yellowknife A 2023: 1 August).
- Station anomalies: precipitation, snowfall, depth and SWE as % of the site's 1991 to 2020 mean; temperature, snow-cover days and melt date as differences. Stations serve every area that contains them or lies within 50 km of its boundary; areas without such a station take the nearest 3 within 250 km (basis column). Area value = median of station anomalies; dropped when fewer than half of the area's usual number of stations reported (this removed, for example, Quebec SWE after the Hydro-Quebec station IDs changed).
- Outcome: burned_ha (all land) and forest_burned_ha (Land Cover 2020 forest classes 1, 2, 5, 6) per area and year from analysis/forest/work/burn_YYYY.npy and the 240 m area grid; forest_share_burned = forest_burned_ha / forest_ha. Mapped hectares, not official totals.

## Files (analysis/climate/)

- climate_panel.csv: one row per area_id x year, 99 areas x 1991 to 2026 = 3,564 rows. Key: area_id (= fma_id), year. Climate columns (each with n_<var> = stations used that year and basis_<var> = inside_or_50km or nearest): snowfall_pct, snow_cover_days_anom, max_snow_depth_pct, melt_anom_days (+ = later), melt_doy_median (day of year), swe_apr1_pct (to 2025), t_amj_anom_c, p_amj_pct, p_jja_prev_pct, p_son_prev_pct, p_ndjfm_pct, p_12m_pct, months_since_wet. Index columns (same for all areas in a year): oni_djf, enso_winter_phase, oni_mam, pdo_djf, pdo_mam, ao_djf, ao_mam, ao_jfm, nao_djf, nao_mam, vortex_jfm, vortex_source. Outcome columns: burned_ha, forest_burned_ha, forest_ha, forest_share_burned, log10_burned_ha, burn_source.
- indices_by_fire_year.csv (1951 to 2026), indices_2023_2026.csv, ranks_2026.csv, area_2026_summary.csv, region_2026_summary.csv, run_2023_2026_by_region.csv, run_windows_2023_2026.csv, correlations_burn.csv, correlations_chain.csv, station_list.csv (stations used per variable and area, with distance, member IDs), manifest.csv (downloads with URL, size, hash).
- scripts/: run_all.sh runs 01 to 08. 01 station inventory, 02 download, 03 indices, 04 station metrics, 04b CanSWE, 05 areas and outcome, 06 panel, 07 ranks and correlations, 08 4-year windows. raw/ holds the downloads (135 MB); work/ holds intermediate tables and logs.
