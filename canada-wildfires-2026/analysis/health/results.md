# Wildfire 2026: the health side (original analysis of official data)

Analysis date 2026-10-21. PM2.5 to 2026-10-19. Scripts in `scripts/` (run 01 to 08 in order). Sources and licences in `manifest.csv`. No news, and no other people's results, are used. Two published coefficient sets are used only in section 4, as approved, and every number from them is a MODELLED ESTIMATE, not a count.

## Scorecard (May to September, 50 km station assignment)

| Measure | 2018 | 2021 | 2023 | 2025 | 2026 |
|---|---|---|---|---|---|
| Person-days above 27 ug/m3 (9 provinces with data every year) | 113.6M | 126.7M | 378.7M | 329.6M | 104.9M |
| Person-days above 100 (same 9) | 21.3M | 9.9M | 44.8M | 7.4M | 18.7M |
| People with at least 1 day above 100 (same 9) | 8.0M | 4.1M | 17.2M | 4.0M | 12.2M |
| Worst day, Canada pop-weighted mean PM2.5 | 31.9 (Aug 15) | 33.7 (Jul 19) | 52.5 (Jun 25) | 43.4 (Jun 6) | 67.0 (Jul 16) |
| Modelled acute deaths, AQBAT, net (range) | 120 (0 to 176) | 128 (0 to 188) | 379 (0 to 557) | 219 (0 to 323) | 98 (0 to 144) |
| Modelled acute deaths, Chen 2021, net (range) | 312 (266 to 358) | 335 (284 to 384) | 988 (840 to 1,133) | 578 (490 to 665) | 253 (216 to 290) |

The 9 provinces are AB, BC, NB, NS, ON, PE, QC, SK, YT (35.06M people); Manitoba, Newfoundland and Labrador, NWT and Nunavut have no usable station data for 2025 and 2026. Modelled deaths for 2025 and 2026 cover the same 9; 2018 to 2024 also include MB, NL and NT.

## 1. Population-weighted smoke exposure

Findings
- July 16, 2026 was the smokiest single day for Canadians in 2018 to 2026: the population-weighted mean of daily PM2.5 across covered Canadians was 66.95 ug/m3, above the previous high of 52.52 on 2023-06-25. Ontario's population-weighted mean that day was 147.85 ug/m3. The plume was recorded at about 30 Ontario stations at once (for example Windsor 322, Sarnia 320, Sault Ste. Marie 290, London 277, Toronto 137 city mean of stations), while Quebec stations stayed below 20, so it is a coherent smoke event, not one faulty monitor.
- In May to September 2026, Canadians spent 104,962,913 person-days above 27 ug/m3, 41,722,643 above 60 and 18,744,917 above 100 (all provinces with data). 12,196,616 people (38.1% of people with a station within 50 km) had at least one day above 100.
- Ranking 2026 against 2018 to 2025 on the 9 provinces with data in every year: 5th of 9 for person-days above 27 (2023 378.7M, 2025 329.6M, 2021 126.7M, 2018 113.6M, 2026 104.9M), 4th for person-days above 60 (2023 104.6M, 2025 48.3M, 2018 45.2M, 2026 41.7M), 3rd for person-days above 100 (2023 44.8M, 2018 21.3M, 2026 18.7M) and 2nd for people with at least one day above 100 (2023 17.16M, 2026 12.20M, 2018 8.02M). 2026 was a short, intense season for the most people: fewer smoky days overall than 2023 or 2025, but one very high day over the most populated region.
- Smoke above background (the wildfire-season increment, method below) in 2026 was 13.34 billion person-ug-days in the 9 provinces, 5th of 9 years (2023 34.03B, 2025 22.47B, 2018 15.31B, 2021 13.98B).
- Population-weighted mean PM2.5 May to September 2026 was 7.82 ug/m3 (increment above background 2.74); 2023 was 12.53 (6.98), 2025 9.88 (4.64), the quietest year 2019 6.24 (1.35).
- By province, May to September 2026: Ontario 50,318,505 person-days above 27, 31,143,563 above 60, 17,091,085 above 100, and 11,706,139 people with a day above 100; Alberta 34,721,780 above 27 (5,964,694 above 60, 14,257 above 100); BC 15,949,393 above 27 (1,639,575 above 100; 476,220 people with a day above 100); Saskatchewan 3,257,480 above 27 (only 56% of person-days covered); Quebec 527,100; New Brunswick 119,984; NS, PE 0. Ontario's 2026 person-days above 100 (17.1M) and people with a day above 100 (11.7M) are the highest of 2018 to 2026 (2023: 8.7M and 5.0M; every other year 0), while its person-days above 27 (50.3M) were well below 2023 (146.9M) and 2025 (163.3M).
- Worst day by province in 2026: ON 147.85 (Jul 16), AB 62.66 (Jul 24), SK 34.70 (Aug 26), BC 33.26 (Aug 6), YT 31.40 (Jul 11), NB 21.40 (Jun 30), QC 20.34 (Feb 17, not fire season), PE 18.41 (Jul 15), NS 15.05 (May 20).
- CMAs, May to September 2026 (days above 27 per covered resident): Kamloops 25.7, Calgary 12.2, Kelowna 11.9, Edmonton 6.9, London 6.0, Regina 5.6, Windsor 5.0, Toronto 4.0, Hamilton 4.0, Kitchener - Cambridge - Waterloo 4.0, Saskatoon 4.1, Vancouver 1.3, Montreal 0.0. Every resident of Toronto (6,205,161), Hamilton, London, Kitchener - Cambridge - Waterloo, St. Catharines - Niagara and nearly all of Windsor and Oshawa had at least one day above 100; Toronto alone accounts for 6,394,249 person-days above 100. Calgary had the second-most person-days above 27 (18,043,255) but none above 100.
- Kamloops in 2026 (25.7 days above 27 per resident) was close to its worst year (33.0 in 2021); Calgary 12.2 against 22.1 in 2023; Edmonton 6.9 against 44.6 in 2023; Saskatoon 4.1 against 41.0 in 2023.
- Outside fire season (January to April and October to December of the same year), person-days above 27 ranged from 11.8M (2025) to 57.3M (2018), and days above 100 were almost absent (746,297 person-days in 2022, 69,023 in 2021, 0 in other years). In 2026, January to April plus October 1 to 19 had 29.1M person-days above 27 and none above 60. These winter days (wood smoke, inversions) are why the May to September columns are the fire-season measure.

Method
- Each 2021 dissemination area (DA, 57,932, 36,991,981 people) gets, each day, the 24 h PM2.5 of the nearest station reporting that day within 50 km (great-circle distance from the DA representative point). If no station within 50 km reported that day, the DA has no value that day. Sensitivity at 25 km in `exposure_by_group_R25.csv`.
- Coverage at 50 km: 33.5M people (90.5%) have a station within 50 km on some day of May to September 2018 to 2024, and 89.6% to 90.3% of person-days are covered; 2025 and 2026 drop to 85.7% and 85.9% because Manitoba, NL (except one site), NWT and Nunavut have no real-time data. At 25 km, 2026 coverage is 74.9% of person-days and the 2026 national figures are 90.5M person-days above 27 and 15.7M above 100, so the pattern holds.
- Thresholds are strictly greater than 27, 60 and 100 ug/m3. 27 is the 2020 CAAQS 24 h value, which is a 3-year statistic, so a day above 27 is not a formal exceedance.
- Background and wildfire-season increment: for each station and calendar month, background = median of that station's daily values over 2018 to 2024 (at least 60 values; otherwise all years, 421 station-months). Increment = max(0, PM2.5 minus background) on each DA-day. A median is used because smoke days are a minority of days in any month over seven years. The increment also picks up ordinary above-median days without smoke (about 1.35 ug/m3 on average in 2019, the quietest year), so for health estimates a net version subtracts each province's lowest 2018 to 2024 total (section 4).
- Data status: 2018 to 2023 mostly NAPS validated; 2024 mixed (54.1M of 91.4M person-days above 27 rest on real-time data); 2025 and 2026 entirely real-time AirNow (column `person_days_gt27_realtime`).

Files: `exposure_by_group.csv` (radius, year, period May-Sep / Jan1-Oct19 / calendar year / Oct-Apr, dimension national / province / cma / reserve, weight total / age / low income), `exposure_by_group_R25.csv`, `national_comparable.csv`, `daily_popweighted_pm25.csv` (Canada and province daily series), `worst_days.csv`, `cma_may_sep.csv`.

## 2. Who was most exposed

Findings (May to September; per covered person, so coverage gaps do not drive the comparison)
- Children under 5 had slightly more smoke days than the population as a whole in every heavy year: 12.83 days above 27 per covered child in 2023 against 11.90 for everyone, 10.81 against 10.40 in 2025, 3.43 against 3.30 in 2026. Their increment above background was also higher (2023: 7.44 against 6.98 ug/m3; 2026: 2.79 against 2.74). This reflects where young families live (more in the Prairies and suburban Ontario), not a different response.
- People 65 and over had slightly fewer smoke days than average: 10.93 in 2023, 9.94 in 2025, 3.10 in 2026. In 2026 their share with a day above 100 was close to average (37.3% of covered 65+ against 38.1%).
- People in low income (LIM-AT) had fewer smoke days than the population in the low-income universe: 11.20 against 11.89 in 2023, 10.19 against 10.41 in 2025, 3.04 against 3.31 in 2026. At DA level, low income is concentrated in large eastern cities that had less smoke in 2023 and 2025. They are also less covered by monitors (83.3% of low-income people have a station within 50 km in 2026, 87.0% of the universe).
- On-reserve population: only 35% of the 339,951 people counted in on-reserve DAs have any station within 50 km (about 120,000 people), against 87% to 91% off reserve. For those covered, smoke days were higher than off reserve in most years: 13.77 days above 27 per covered person in 2023 (11.89 off reserve), 5.33 in 2026 (3.30), but 6.90 in 2025 (10.42). On-reserve people with a day above 100: 67,297 in 2023, 16,862 in 2025, 25,686 in 2026 (covered only). For the other 65% there is no monitor-based estimate; their exposure is unknown, not zero. 174 reserve-area DAs have no 2021 population count and are not in any total.
- Age and income data are missing for DAs that StatCan suppresses (age for 56,163 of 57,932 DAs, income for 54,191); 8,877 people are in DAs with population but no age data.

Method: Census Profile 2021 counts by DA (StatCan SDMX API): children 0 to 4, 65 and over, people in low income (LIM-AT, private households) and the LIM universe as the comparison base. Each group's exposure is the same DA-day PM2.5 weighted by the group's count in the DA. This is an area-level (ecological) comparison: it shows where groups live relative to smoke, not individual exposure (indoor air, outdoor work, filtration).

File: `group_comparison.csv` (also all rows in `exposure_by_group.csv` with weight = age_0_4, age_65p, lim_low_income, lim_universe, and dimension = reserve).

## 3. Health records: what open official data exist, and what they show

Inventory (detail in `manifest.csv`)

| Source | Resolution | Latest data | Covers 2026 fire season |
|---|---|---|---|
| StatCan 13-10-0810 weekly deaths by cause, province | weekly | ON 2025-11-22; AB, BC 2026-05-02 | No |
| StatCan 13-10-0768 weekly deaths by age, province | weekly | same | No |
| CIHI NACRS ED visits by province, month, age | monthly, all causes | March 2026 | No |
| CIHI hospital stays data tables | annual, top 10 causes | FY2024-25 | No |
| Quebec MSSS cumulative ED file | cumulative by period | Sep 2026 | Only as cumulative totals |
| Alberta open data LGA ED visits | annual | not checked | No |
| PHO, BCCDC, PHAC | no open weekly ED or smoke-outcome download found | | No |

- No open official health record covers the 2026 smoke season at a weekly or monthly level as of 2026-10-21. The Ontario week of July 16, 2026 cannot be tested: Ontario's provisional weekly deaths end at the week of 2025-11-22 and CIHI monthly ED data end in March 2026.
- Weekly deaths, 2018 to 2025 fire seasons (quasi-Poisson, year fixed effects, seasonality, smoke increment at lag 0 and 1): pooled across 12 provinces and territories (1,907 province-weeks), deaths changed by +0.05% per 10 ug/m3 of weekly mean increment (95% CI -0.50% to +0.60%, p = 0.87). No single province shows a significant rise; the closest are Quebec +1.62% (-0.53 to +3.82, p = 0.14) and Manitoba +1.44% (-1.40 to +4.36). The pooled upper bound (0.60%) is below the 1.9% per 10 ug/m3 in the wildfire-specific coefficient used in section 4 and close to the AQBAT 0.7%, but the test averages exposure over whole provinces and whole weeks, which dilutes any effect, so it does not rule out effects at the scale of a city on a smoky day.
- Smokiest weeks against the model's no-smoke expectation: Ontario week ending 2023-07-01 (weekly mean increment 34.9 ug/m3): 1,960 non-accidental, non-COVID deaths against 1,933 expected (+1.4%); Quebec same week 1,205 against 1,208; Quebec 2025-08-09 1,310 against 1,247 (+5.1%); BC 2020-09-19 715 against 697 (+2.6%); BC 2018-08-25 565 against 626 (-9.7%); Alberta 2023-05-20 505 against 536 (-5.8%). Ratios range from 0.77 to 1.14 across the provinces' top three weeks with no consistent direction (`weekly_deaths_top_smoke_weeks.csv`).
- Monthly ED visits (CIHI, April 2021 to March 2026, 9 provinces/territories, all causes): for May to September months, visits rose 1.71% per 10 ug/m3 of monthly mean increment (95% CI 0.16% to 3.28%, p = 0.03, 213 province-months); children 0 to 4 +2.10% (-3.15 to +7.64), 65+ +1.19% (-0.10 to +2.50). Using all months the estimate is -0.18% (-1.62 to +1.29). This is one significant result out of six fits, with all-cause visits and month-level exposure, so it is suggestive only.

Method: StatCan weekly deaths, place of occurrence, outcome = all causes minus accidents, suicide and COVID-19. Weekly exposure = mean of the province's daily population-weighted increment over the 7 days of the StatCan week; weeks kept only if stations covered at least 50% of the province population; the last 10 published weeks of each province dropped (still filling in). CIHI: Table 2 of each fiscal-year data-table file, province x fiscal-year and province x calendar-month fixed effects, log(days) offset. Quasi-Poisson standard errors without autocorrelation correction.

Files: `weekly_deaths_vs_smoke.csv`, `weekly_deaths_model.csv`, `weekly_deaths_top_smoke_weeks.csv`, `monthly_ed_vs_smoke.csv`, `monthly_ed_model.csv`, `baseline_death_rates.csv`.

## 4. Modelled health outcomes (estimates, not counts)

Findings
- Short-term (acute) premature deaths from the wildfire-season PM2.5 increment, net of each province's quietest 2018 to 2024 year, Canada (provinces with data):
  - Health Canada AQBAT coefficient: 2018 120 (range 0 to 176), 2019 16, 2020 44, 2021 128 (0 to 188), 2022 25, 2023 379 (0 to 557), 2024 99 (0 to 145), 2025 219 (0 to 323, 9 provinces), 2026 98 (0 to 144, 9 provinces).
  - Wildfire-specific coefficient (Chen 2021): 2018 312 (266 to 358), 2019 40, 2020 111, 2021 335 (284 to 384), 2022 66, 2023 988 (840 to 1,133), 2024 260 (220 to 299), 2025 578 (490 to 665), 2026 253 (216 to 290).
  - On the same 9 provinces every year, 2026 (AQBAT 98, Chen 253) ranks 5th of 9, after 2023 (362, 943), 2025 (219, 578), 2018 (115, 299) and 2021 (115, 301), and just ahead of 2024 (88, 232).
- By province, 2026, AQBAT (Chen in brackets): Ontario 55.7, range 0 to 81.1 (140.7, 120.6 to 160.1); Alberta 23.4 (62.1); BC 14.5 (37.9); Quebec 2.5 (6.7); Saskatchewan 1.6 (4.2, 56% covered); NS 0.4, NB 0.3, PE 0.1, YT 0.0. Ontario's 2026 estimate is about half of its 2023 (124.6 / 327.7) and 2025 (99.2 / 262.8) estimates. Manitoba, NL, NWT and Nunavut are not estimated for 2025 and 2026 (no monitor data).
- Gross versions (no subtraction of the quietest year) are 2.6 to 5.3 times the net figure in light years (2019, 2020, 2022), 1.2 times in 2023 and 1.7 times in 2026 (AQBAT 167, Chen 437); see `gross_*` columns.
- Not estimated: respiratory and cardiac hospital admissions, respiratory and cardiac emergency visits, and asthma symptom days. The AQBAT coefficients exist (respiratory admissions and ED visits 0.75% per 10 ug/m3, 95% CI 0.5 to 1.01; cardiac 0.71%, 0.38 to 1.04; asthma symptom days in asthmatic children 5 to 19, 6.54%, 1.36 to 11.73), but no open official baseline rate by province exists for these outcomes: CIHI publishes monthly ED visits for all causes only and annual hospital tables for the top 10 causes only; asthma needs asthma prevalence among 5 to 19 year olds and a baseline symptom-day rate, which are not open (the CCHS covers ages 12 and up; AQBAT's internal baseline rates sit inside its web application). What would be needed: CIHI DAD and NACRS counts of respiratory (ICD-10 J00-J99) and circulatory (I00-I99) admissions and ED visits by province for May to September, via a CIHI data request, or AQBAT's own baseline file from Health Canada.

Method
- Attributable deaths = sum over DAs and May 1 to Sep 30 days of: baseline daily death rate (province, year) x DA population x (1 - exp(-beta x increment)), with beta = ln(1 + percent/100) / 10. Only DAs with a station within 50 km that day count (85.9% to 90.3% of person-days), so national totals understate uncovered areas.
- Coefficients: (a) AQBAT acute all internal-cause mortality, 0.7% per 10 ug/m3 (95% CI 0 to 1.04), source study Huang et al. 2023, as listed in Supporting Information Table S1 of Matz et al. 2026, GeoHealth, doi:10.1029/2025GH001565 (Health Canada's coefficient for wildfire smoke assessments; derived from all-source PM2.5). (b) Chen G. et al. 2021, Lancet Planetary Health 5(9):e579-e587, all-cause mortality RR 1.019 (1.016 to 1.022) per 10 ug/m3 of wildfire-related PM2.5, 3-day moving average, 749 locations in 43 countries including Canada (abstract values). Applied here to daily increments; summed over a season this equals applying it to a 3-day average except at the season edges. Ranges are the coefficient's 95% CI only (no Monte Carlo, no baseline or exposure uncertainty).
- Baseline: StatCan weekly deaths by province, all causes minus accidents and suicide, weeks ending May 7 to Oct 6, divided by days and the July 1 population (17-10-0005). 2018 to 2025 use their own year; 2026 uses 2025 rates (weekly data end before May 2026). Place of occurrence is used as a stand-in for place of residence.
- Wildfire increment versus background: gross uses the increment defined in section 1; net subtracts, province by province and coefficient by coefficient, the lowest 2018 to 2024 seasonal total, which removes ordinary above-median days. Net is the central figure.

Files: `modelled_acute_deaths_by_province.csv`, `modelled_acute_deaths_national.csv`.

## Caveats

1. PM2.5 for 2025 and 2026 is real-time AirNow data, not validated. AirNow matched NAPS for 2018 to 2024 (r 0.99 to 1.00, median absolute difference 0.06 to 0.09 ug/m3), but single values can change on validation. 2024 is partly real-time.
2. No monitor data after 2024 for Manitoba (except Flin Flon, below 1% coverage), NWT and Nunavut, and only one NL site, so 2025 and 2026 national totals exclude them; Manitoba had heavy smoke in 2025 (Flin Flon daily 1,405 ug/m3 on 2025-06-05). Saskatchewan coverage is 56% to 60%. Nunavut has had almost no data since 2019.
3. Monitors sit in towns. 65% of on-reserve residents and much of rural and northern Canada have no station within 50 km; results describe covered people only.
4. Nearest-station assignment ignores gradients between station and home and indoor exposure.
5. The increment is a statistical background split, not a smoke model; it does not separate wildfire smoke from other above-normal pollution, and the net correction assumes the quietest year had no wildfire smoke.
6. Population is 2021 Census for every year.
7. The health tests are ecological and low-powered (province-week and province-month), use place of occurrence (evacuations move deaths: Yellowknife, Aug 2023), and use provisional, rounded counts. A null result is not evidence of no effect.
8. Modelled deaths are estimates from published coefficients applied to our exposure, not observed deaths. The AQBAT mortality lower bound is 0. The Chen coefficient comes from a multi-country study and is applied to non-accidental deaths, not all deaths.
9. Several StatCan www12 download pages (Census Profile CSV, Geographic Attribute File) returned a security-check page (HTTP 403), so the SDMX API and the cartographic boundary service were used instead.
