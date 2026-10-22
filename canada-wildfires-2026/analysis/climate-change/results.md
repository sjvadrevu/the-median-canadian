# Climate change and Canada's fire seasons, from raw official data

Original analysis, 2026-10-21. Sources: ECCC Adjusted and Homogenized Canadian Climate Data (AHCCD) monthly temperature (third generation, to 2023) and precipitation (second generation, to December 2017), extended to September 2026 with offset-corrected ECCC climate-daily; ECCC climate-hourly noon observations and climate-daily records 1953 to 2026 (MSC GeoMet); CWFIS station FWI 1990 to 2026; NBAC 1972 to 2025, CWFIS M3 2026 scaled to official totals, CNFDB fire points 1959 to 2025. No published attribution study or outside analysis is used. Areas are the 186 rows of `data/geo/fma_v2.gpkg`; "forested areas" are the 177 eligible areas of the cause model (forest at least 100,000 ha and at least 5% of land, Nunavut excluded). "Canada" climate values are forest-weighted means of area values. Folder: `analysis/climate-change/`.

## Scorecard

| Question | Answer from the data |
|---|---|
| Fire-season warming, May to August, Canada 1950 to 2026 | +0.22 C per decade (95%: +0.17 to +0.26); every one of 236 long stations warmed, 93% significantly |
| 2016 to 2026 vs 1961 to 1990, May to August | +1.15 C (95%: +0.80 to +1.49); BC and North +1.41 C, Ontario +0.89 C |
| Long-term trend in fire-season precipitation | None nationally: April to September +0.04 points of normal per decade (95%: -0.89 to +0.97) |
| 2023 to 2026 climate | 2023 warmest and driest April to September since 1950; the 4-year mean is the driest April to September window (84% of normal) and 2nd warmest |
| Extreme fire-weather days, CWFIS fixed stations 1990 to 2026 | +1.9 days per decade (95%: +0.8 to +3.0) on a normal of 11.0; BC +3.3, Prairies +3.6; east flat |
| Computed FWI back to 1953 | No significant 1953 to 2026 trend nationally (-0.1 days per decade); 2016 to 2026 is +3.2 days above 1961 to 1990 (p 0.02); the 1950s to 1960s were high, partly from higher recorded wind |
| Area burned trend, hectares 1972 to 2026 | +19% per decade (95%: +2% to +36%); without 2023 to 2026: +8% (95%: -8% to +26%), not significant |
| Sensitivity, within area | +1 C May to August anomaly: +44% area burned (95%: +30% to +62%); April to September rain 10% below normal: +22% (+15% to +32%) |
| 2023 to 2026, observed vs 1961 to 1990 climate (warming removed, rain at normal) | 3.3 times as much area burned (95%: 2.7 to 6.0); warming alone 1.53 times (1.37 to 1.76) |
| Snow season | Earlier melt and fewer snow-cover days 1956 to 2005 (-1.2 and -1.7 days per decade); no trend 1991 to 2026; too few stations span the whole period |

## 1. Long-term change in fire-season climate

Files: `climate_series.csv`, `climate_trends.csv`, `climate_recent_vs_normal.csv`, `climate_ranks_2023_2026.csv`, `station_trends.csv`, `climate_area_year.csv`, `offset_check.csv`.

**Stations.** 323 AHCCD temperature stations and 161 precipitation stations have long records and lie inside or within 50 km of a forested area. After linking each to its current climate-daily site and requiring data in at least 9 of the 11 years 2016 to 2026 (including 2025 and 2026), 236 temperature stations and 76 precipitation stations remain. Precipitation stations by province: BC 26, ON 12, AB 8, QC 6, MB 5, NL 5, NT 4, NS 4, NB 3, SK 2, PE 1. Every forested area has temperature (81% of forest within 50 km of a station). Precipitation covers 164 of 177 areas; 60% of forest is within 50 km of a precipitation station and 34% relies on the nearest 3 stations within 300 km.

**Extension past the AHCCD end.** AHCCD temperature ends in 2023 and AHCCD precipitation in 2017 (many precipitation records end 2010 to 2014); the GeoMet ahccd-monthly collection ends in 2020, so the ECCC CDAS files were used. Later months come from climate-daily times a per-station, per-month offset estimated on the 1990 to AHCCD-end overlap. Temperature offsets are small (median +0.02 C). Precipitation ratios have median 1.11 (AHCCD adds gauge undercatch, trace and snow-density adjustments). Hold-out test (offsets fitted without each station's last 5 AHCCD years, then used to predict them): temperature median bias +0.001 C, mean absolute monthly error 0.11 C; precipitation season-total median bias +0.3% with a median absolute error of 1.6%, against -6.0% without the offset. 41 filled precipitation months above 1.5 times the station's AHCCD maximum were rejected as daily-data errors (for example Norman Wells 2015 to 2016, about 200 mm per month). Share of season months from the daily extension: temperature 1% in 1990 to 2019 and 45% in 2020 to 2026; precipitation 53% in the 2010s and 100% in 2020 to 2026.

**May to August temperature** (anomaly vs 1961 to 1990):
- Canada: +0.22 C per decade 1950 to 2026 (OLS 95%, autocorrelation-adjusted: +0.17 to +0.26; Theil-Sen +0.22); +0.25 C per decade 1972 to 2026. Regions 1950 to 2026: North +0.26, BC +0.22, Atlantic +0.21, Quebec +0.21, Prairies +0.19, Ontario +0.19 C per decade; all p below 0.001.
- 2016 to 2026 minus 1961 to 1990: Canada +1.15 C (95%: +0.80 to +1.49); BC +1.41, North +1.41, Atlantic +1.09, Quebec +1.06, Prairies +1.01, Ontario +0.89 C.
- All 236 stations have a positive Theil-Sen trend; 220 (93.2%) are significant at p below 0.05 and none is significantly negative. Station median +0.215 C per decade.
- 2023 was the warmest May to August since 1950 in the national series (+2.09 C, z = +4.7 against 1961 to 1990), 2024 3rd, 2026 7th, 2025 10th of 77. The 2023 to 2026 mean (+1.52 C) is the 2nd warmest 4-year window of 74. Regional 4-year windows: Atlantic and Prairies 1st, BC and Quebec 2nd, North 3rd, Ontario 6th.

**Precipitation** (% of the station's 1961 to 1990 mean; trends in percentage points of normal per decade):
- No significant long-term national trend in any window. 1950 to 2026: April to September +0.04 (95%: -0.89 to +0.97), previous September to March -0.28 (-1.52 to +0.95), 12 months October to September -0.15 (-0.99 to +0.69). The only significant regional trend is wetter April to September in Quebec (+0.99, p 0.01) and drier previous fall and winter in Quebec over 1972 to 2026 (-1.5, p 0.04). 1972 to 2026 trends lean dry in BC (April to September -2.6, p 0.06) and the Prairies (-1.9, p 0.05).
- 2016 to 2026 minus 1961 to 1990, April to September: Canada -6.0 points (95%: -13.3 to +1.3, p 0.10); BC -13.3 (-24.0 to -2.5, p 0.02); Prairies -7.7, North -6.9, Ontario -5.2 (none significant). Previous fall and winter: Ontario -13.8 (p 0.01), Quebec -9.4 (p less than 0.01). 12-month: Ontario -9.8 (p 0.02), Quebec -4.4 (p 0.02).
- Station trends: April to September positive at 61% of 76 stations (9% significantly up, 3% significantly down); previous fall and winter positive at 47% (11% up, 12% down).
- 2023 to 2026 in the 1950 to 2026 distribution (rank 1 = driest): April to September 2023 77% of normal (1st), 2024 86% (4th), 2025 79% (2nd), 2026 94% (17th). Previous fall and winter: 2024 75% (1st), 2023 2nd, 2025 3rd, 2026 15th. 12-month: 2023 1st, 2025 2nd, 2024 3rd, 2026 27th. The 4-year means are the driest windows since 1950 for April to September (84%) and previous fall and winter (82%), and 2nd driest for 12 months (85%). Regional 4-year April to September: BC 71% and Ontario 86% rank 1st, North 2nd, Prairies 4th, Atlantic 9th, Quebec 26th (99%).

So the warming is a steady, station-by-station trend; the 2023 to 2025 dryness is extreme but sits on a precipitation record with no national trend.

## 2. Fire weather trend

Files: `cwfis_extreme_days_series.csv`, `cwfis_extreme_days_trends.csv`, `cwfis_site_trends.csv`, `fwi_sites.csv`, `fwi_extreme_days_series.csv`, `fwi_extreme_days_trends.csv`, `fwi_site_trends.csv`, `fwi_validation.csv`.

**CWFIS station FWI, 1990 to 2026, fixed stations.** The 116 sites of analysis/weather that qualify in at least 28 of 30 years 1991 to 2020; a site-year counts only if it qualifies. Extreme day: FWI 30 or more, April 1 to October 19. Series: mean of each site's anomaly from its own 1991 to 2020 mean.
- Canada: +1.91 extreme days per decade (95%: +0.79 to +3.03, p 0.001) on a 1991 to 2020 normal of 11.0 days; days with FWI 19 or more +3.3 per decade (+1.3 to +5.4). Without 2023 to 2026 (1990 to 2022): +1.87 (+0.52 to +3.23, p 0.008).
- BC +3.26 days per decade (+1.69 to +4.83), Prairies +3.61 (+1.01 to +6.20), North +1.09 (-0.47 to +2.66). Ontario -0.10, Quebec -0.04, Atlantic -0.11 (all near zero, normals 1.7 to 2.9 days).
- Sites: 48 with positive slopes, 10 negative, 58 zero (mostly eastern sites with almost no extreme days); 26 significantly increasing (BC 10, Prairies 14), 1 significantly decreasing.

**FWI computed from station weather, 1953 to 2026.** Method:
- Equations: the Canadian FWI System daily equations of Van Wagner (1987), implemented in `scripts/fwi.py` (reproduces the standard first test day: FFMC 87.69, DMC 8.55, DC 19.01, ISI 10.85, BUI 8.49, FWI 10.10).
- Inputs: 12:00 LST temperature, relative humidity and wind from climate-hourly. Rain is noon-to-noon, approximated as half of the previous and half of the current climate-day total precipitation.
- Season: every season starts April 1 with the standard start-up codes (FFMC 85, DMC 6, DC 15; no overwintering) and runs to October 31.
- Station records: climate IDs are joined only within 3 km and 100 m elevation of each site's primary ID, for example Victoria Int'l A 1018620 followed by 1018621.
- Qualifying seasons: the analysis/weather coverage rule, plus rain present on 90% of days.
- Stations: 147 sites computed. The fixed set is 79 sites that qualify in at least 60 of 74 seasons, 24 of 30 in 1961 to 1990 and 9 of 11 in 2016 to 2026: Prairies 18, Atlantic 16, BC 15, Ontario 14, Quebec 9, North 7.
- Validation against CWFIS station FWI at 108 matching sites, May to September 1990 to 2026: median daily correlation 0.92 and median bias +0.17 FWI. The computed series has more extreme days (median 7.0 vs 4.4 per year), probably from the April start-up without snow-melt timing and the rain approximation. The yearly extreme-day counts correlate at a median 0.83, and site trends correlate at 0.73.

Results (fixed set, anomaly vs each site's 1961 to 1990 mean):
- Canada 1953 to 2026: -0.13 extreme days per decade (95%: -0.68 to +0.43), no trend. 1972 to 2026: +0.80 (+0.12 to +1.48). 1990 to 2026: +2.32 (+1.33 to +3.31), which matches the CWFIS archive (+1.9).
- 2016 to 2026 minus 1961 to 1990: +3.2 extreme days (normal 11.0, p 0.02); FWI 19 or more +7.1 days (p 0.006); mean May to September FWI +1.5 (p 0.004).
- The long series is U-shaped: extreme days averaged 13.8 in the 1950s and 13.4 in the 1960s, 7.9 in the 1990s, and 15.1 in 2020 to 2026. 2025 ranks 2nd of 74 seasons, 2021 5th, 2023 9th, 2026 18th.
- The components explain the shape. Noon temperature rose +0.24 C per decade and noon humidity fell -0.20 points per decade, both significant and both raising FWI. Recorded noon wind fell -0.39 km/h per decade, 1.4 km/h above normal in the 1950s and 0.9 km/h below it in 2016 to 2026, which lowers FWI. Much of that wind drop is likely instrument and exposure change at airports, not climate; the data cannot separate the two.
- With wind held at each site's 1991 to 2020 monthly mean: Canada +0.36 days per decade 1953 to 2026 (95%: -0.08 to +0.80, p 0.10), and 2016 to 2026 is +4.5 days above 1961 to 1990 (p 0.003). The Prairies difference is +9.5 days (p 0.03); BC is +1.07 days per decade 1953 to 2026 (+0.26 to +1.88).
- Regions, observed wind: BC 2016 to 2026 is +9.8 days above 1961 to 1990 (normal 14.3, p less than 0.001), and its 1990 to 2026 trend is +5.2 days per decade. Prairies +5.2 days (normal 26.8, not significant), with +5.1 per decade 1990 to 2026. Ontario, Quebec and Atlantic show no increase; Ontario and Quebec decline slightly over 1953 to 2026 with observed wind and are flat with fixed wind.

## 3. Area burned trend

Files: `area_burned_series.csv`, `area_burned_decades.csv`, `area_burned_trends.csv`, `cnfdb_overlap_check.csv`, `work/area_burned_ha_1972_2026.csv`.

**Two measures.**
- Hectares burned: NBAC all-land hectares, 1972 to 2025. 2026 is the official total, 4.50 M ha (agencies plus Parks Canada).
- Share of forest burned: forest is Land Cover 2020, the analysis/forest basis. This measure is biased over time. Forest hectares per burned hectare fall from 0.52 in the 1970s to 0.39 in the 1990s, 0.26 in the 2000s and 0.19 in the 2010s, then rise to 0.66 in 2020 to 2026. Land that burned in about 1995 to 2019 and had not regrown into forest by 2020 does not count as forest, so forest shares are too low for those years and too high, relatively, for 2020 onward. Trends are therefore stated on hectares. The forest share is reported only for completeness.

**1959 to 1971.** CNFDB fires of 200 ha or more were checked against NBAC for 1972 to 1991:
- Canada passes the check: the NBAC/CNFDB ratio is 0.97 in 1972 to 1981 and 0.92 in 1982 to 1991, and log-correlation is 0.98. So do BC, Prairies, Ontario, Quebec and North.
- Atlantic fails (log-correlation 0.62) and is not extended.
- 1959 to 1971 hectares are CNFDB totals times the 1972 to 1981 ratio. Early detection and reporting were less complete, which can bias the early years low.

**Decadal mean hectares, Canada:** 1960s 0.86 M, 1970s 1.36 M, 1980s 2.45 M, 1990s 2.43 M, 2000s 1.56 M, 2010s 2.52 M, 2020 to 2026 5.29 M ha per year. 1972 to 2022 averaged 2.07 M ha per year and 2023 to 2026 averaged 7.88 M ha. Ranks among 1972 to 2026: 2023 1st (14.80 M ha), 2025 2nd (7.31 M), 2024 7th (4.92 M), 2026 9th (4.50 M).

**Trends (log of hectares, % per decade, 95% interval from 1,000 bootstrap resamples of years):**

| Scope | 1972 to 2026 | 1972 to 2022 | 1959 to 2026 | 1959 to 2022 |
|---|---|---|---|---|
| Canada | +19% (+2 to +36) | +8% (-8 to +26) | +26% (+13 to +39) | +20% (+6 to +34) |
| BC | +65% (+30 to +105) | +40% (+8 to +82) | +30% (+5 to +61) | +15% (-9 to +44) |
| Prairies | +23% (+2 to +45) | +14% (-6 to +37) | +31% (+15 to +48) | +26% (+8 to +44) |
| Ontario | +6% (-23 to +39) | -8% (-35 to +29) | +46% (+12 to +85) | +38% (+5 to +80) |
| Quebec | -2% (-27 to +33) | -11% (-32 to +19) | +9% (-11 to +36) | +4% (-14 to +30) |
| North | +15% (-6 to +40) | +1% (-18 to +26) | +26% (+6 to +44) | +18% (-1 to +38) |
| Atlantic | -16% (-38 to +11) | -31% (-50 to -4) | not extended | not extended |

- The national 1972 to 2026 increase depends on 2023 to 2026: without them the trend is +8% per decade and not distinguishable from zero. BC is the one region with a significant increase that survives dropping 2023 to 2026 (+40% per decade, 1972 to 2022). Atlantic burning declined.
- The 1959 to 2022 increases rest on the CNFDB-scaled 1960s, which may be under-reported, so they are an upper bound on the early rise.
- Share of forest burned, Canada 1972 to 2026: +7% per decade (-12 to +27); 1972 to 2022: -10% (-24 to +5). The decline to 2022 reflects the 2020 land-cover bias described above.

## 4. Sensitivity and counterfactual

Files: `model_coefficients.csv`, `counterfactual_2023_2026.csv`, `counterfactual_by_year.csv`, `counterfactual_by_region.csv`, `model_fit_check.csv`, `work/panel_climate_burn.csv`.

**Panel.**
- Coverage: 164 forested areas, 8,743 area-years, 1972 to 2026. These areas hold 93.6% of eligible forest and 92.1% of the hectares burned in eligible areas in 2023 to 2026.
- Outcome: all-land hectares burned per area and year, from the analysis/forest rasters (2026 scaled to official).
- Predictors, all from section 1: May to August temperature anomaly, ln(April to September precipitation / normal), and ln(previous September to March precipitation / normal).

**Models.** All are fit on 1972 to 2025; 2026 is predicted, not fit. The structure follows the cause model: area fixed effects make every effect within-area. The ignition and fuel blocks are left out, because lightning-fire counts are themselves partly weather.
- M1, main: Poisson pseudo-maximum likelihood (PPML) with area fixed effects and a linear year trend.
- M0: area fixed effects only.
- M2: area plus year fixed effects. Here the climate effect comes only from differences between areas within the same year, which absorbs everything common to a year.
- M3: OLS of log10(share of land burned + 1e-4) with area fixed effects and a trend, the cause model's outcome form.
- M1 fit on 1972 to 2022 only, as a robustness check.
- Uncertainty: 500 bootstrap resamples of fitting years, all areas of a drawn year together.

**Sensitivities (M1, 95% bootstrap interval):**
- A May to August temperature anomaly of +1 C means +43.6% area burned (+30.1% to +61.7%).
- April to September precipitation 10% below normal means +22.0% (+14.9% to +32.0%).
- Previous fall and winter precipitation has no detectable effect (+0.2% for 10% below normal; -5.0% to +6.9%).
- Other models, +1 C: M0 +45.0%, M2 +33.3% (+12.5% to +61.4%), M3 +26.9% (+17.5% to +37.9%), M1 on 1972 to 2022 +48.7%. Rain 10% below normal: M2 +16.2%, M3 +16.0%, M1 on 1972 to 2022 +28.8%.

**Fit.** National yearly totals, actual vs fitted, have a rank correlation of 0.63 over 1972 to 2025.
- The model underpredicts the run. Actual 2023 to 2026 hectares are 1.17 times M1's prediction under observed climate (29.0 M ha vs 24.9 M ha). By year: 2023 1.08, 2024 1.17, 2025 1.26, 2026 1.33 (2026 out of sample).
- The other models: M2 1.07 times, M3 0.96 times. M1 fit on 1972 to 2022 predicts 2023 to 2026 at 1.02 times its prediction; its 2023 to 2025 years are out of sample.
- The underprediction is far smaller than in the cause model (16.3 times per area in log terms). This model is fit on hectares, which the large burns dominate, and gives no area-by-area skill score.

**Counterfactual for 2023 to 2026.**
- Every area-year keeps its own fixed effect and trend value.
- Temperature is shifted down by the observed regional warming: the 2016 to 2026 minus 1961 to 1990 May to August difference (BC 1.41, North 1.41, Atlantic 1.09, Quebec 1.06, Prairies 1.01, Ontario 0.89 C).
- The ratio is expected hectares under observed climate divided by expected hectares under the counterfactual, summed over 2023 to 2026.
- "Model" weighting uses model expectations. "Actual" weighting multiplies each area-year's actual hectares by the model's climate factor.

| Scenario | M1 model-weighted | M1 actual-weighted | M2 (year FE) | M3 (log share) |
|---|---|---|---|---|
| Warming removed and rain set to normal (requested) | 3.33 (2.66 to 6.04) | 2.79 (2.34 to 3.53) | 2.41 (1.63 to 4.75) | 2.56 (2.07 to 3.24) |
| Warming removed only | 1.53 (1.37 to 1.76) | 1.53 (1.36 to 1.76) | 1.40 (1.15 to 1.76) | 1.34 (1.22 to 1.48) |
| Rain set to normal only | 2.21 (1.79 to 3.67) | 1.84 (1.63 to 2.22) | 1.74 (1.35 to 2.97) | 1.92 (1.55 to 2.39) |
| Warming removed and rain shifted by the 2016 to 2026 regional difference | 1.76 (1.55 to 2.08) | 1.76 (1.56 to 2.08) | 1.54 (1.25 to 1.98) | 1.50 (1.37 to 1.66) |

- Requested counterfactual (M1, model-weighted): under 1961 to 1990 climate the model expects 1/3.33 of the area burned under observed climate, so 70% of the expected 2023 to 2026 area burned goes with the climate departure. By year: 2023 4.84, 2024 2.34, 2025 3.57, 2026 1.87. By region: North 5.19, BC 3.57, Prairies 2.83, Quebec 2.40, Ontario 2.24, Atlantic 1.95.
- Warming only (M1): 1.53 times, i.e. 35% of expected area burned goes with the 1.15 C national warming. It is nearly the same each year (1.51 to 1.55). By region: North and BC 1.66, Atlantic 1.48, Quebec 1.47, Prairies 1.44, Ontario 1.38. Across all models and fitting periods the warming-only ratio is 1.34 to 1.60.
- The rain part is the larger share of the requested ratio, and it is mostly the 2023 to 2025 dryness itself. Section 1 finds no significant long-term precipitation trend, so the rain-to-normal step removes weather as much as it removes climate change. The warming-only row is the part tied to a measured long-term trend.

**What this is.** This is a statistical counterfactual: the observed within-area relation between seasonal climate and area burned, 1972 to 2025, applied to a shift in climate inputs. It is not a physical attribution. It does not simulate fire spread, fuel or ignition, and it does not separate natural variability from human-caused change in the climate inputs. It assumes the 1972 to 2025 response holds at 2023 to 2026 temperatures, which lie at the edge of the observed range.

## 5. Snow season

Files: `snow_sites.csv`, `snow_series.csv`, `snow_trends.csv`, `snow_trends_split_periods.csv`, `snow_site_trends.csv`, `snow_ranks_2023_2026.csv`.

Definitions:
- Snow-cover days: days with snow on ground of 1 cm or more, October 1 to June 30. A winter needs at most 20% of days missing, and the count is scaled to the full window.
- Melt date: the first day after January 31 that starts 14 consecutive snow-free days.
- Fixed sets: sites whose normal snow cover is at least 30 days.

Data limitation: many airports stopped reporting snow on ground between 2003 and 2013 (Winnipeg Richardson A, for example, after 2002). Only 8 sites meet a full 1956 to 2026 rule (at least 45 of 71 winters): BC 4, Ontario 2, North 2. The trend is therefore given for two overlapping periods.
- 1956 to 2005 (94 sites for snow cover, 87 for melt):
  - Canada: snow-cover days -1.7 per decade (95%: -3.3 to -0.1, p 0.04) and melt -1.2 days per decade (-2.3 to -0.1, p 0.03), earlier.
  - BC: snow cover -4.6 days per decade (p 0.004) and melt -3.0 days per decade (p 0.003). North: melt -1.7 days per decade (p 0.002).
  - Sites: 69 of 94 have fewer snow-cover days (11 significantly, 1 significantly more), and 58 of 87 melt earlier (15 significantly, none later).
- 1991 to 2026 (analysis/climate stations: 100 for snow cover, November to April, and 70 for melt):
  - Canada: no trend, snow cover -0.6 days per decade (-3.2 to +2.0) and melt +0.1 days per decade (-2.0 to +2.1).
  - Sites split evenly: 12 significantly fewer snow-cover days and 14 significantly more. North melt is earlier (-2.6 days per decade, p 0.02, 3 sites).
- Full-period set (8 sites): snow cover -1.0 days per decade (-2.4 to +0.5), not significant. In that set, winter 2023-24 has the 2nd fewest snow-cover days of 71 (-24 days) and the 2nd earliest melt (-17 days). 2024-25 is 7th fewest. 2022-23 and 2025-26 were not low.

## What this can and cannot say about climate change

Can:
- Fire-season temperature in Canada's forested regions has risen about 1.15 C since 1961 to 1990, and the rise is a trend, not a few hot years. It shows at every long homogenized station and in every region. 2023 was the hottest May to August since 1950.
- Precipitation shows no long-term national trend since 1950. The 2023 to 2025 dryness was extreme (driest 4-year April to September window since 1950) but is not part of a measured drying trend, except a lean toward drier summers in BC and the Prairies since 1972 and drier falls and winters in Ontario and Quebec in 2016 to 2026.
- Extreme fire-weather days have increased since 1990 in the west (BC, Prairies) at the fixed CWFIS stations, and 2016 to 2026 has more extreme days than 1961 to 1990 in the station-computed FWI. Eastern Canada (Ontario, Quebec, Atlantic) shows no increase in station fire weather.
- Area burned has risen since 1972, but the national trend is not statistically distinguishable from zero without 2023 to 2026; BC's rise is.
- Within an area, warmer and drier fire seasons go with much more burning: about +44% per +1 C and +22% per 10% less April to September rain. On that relation alone, the observed warming multiplies the expected 2023 to 2026 area burned by about 1.5 (1.3 to 1.6 across models). Warming plus the dry seasons multiply it by about 2.4 to 3.3.

Cannot:
- Attribute the warming or the dryness to human influence. That needs climate models or detection and attribution methods, which this analysis does not use. "Observed warming" here is a measured change, whatever its cause.
- Give a physical attribution of area burned. The counterfactual is a regression extrapolation. It assumes the 1972 to 2025 relation holds at record temperatures and leaves out fuel build-up, ignition, suppression, and the effect of reburns and earlier burns.
- Separate the rain effect of 2023 to 2025 from climate change: setting rain to normal mostly removes weather.
- Measure the long-term fire-weather trend cleanly before 1990. Recorded noon wind fell 1.4 to 2 km/h at many airports between the 1950s and 1990s, which is likely partly instrument and exposure change. With wind held fixed, the 1953 to 2026 national trend is +0.36 extreme days per decade (p 0.10).
- Represent northern Quebec, northern Ontario, Labrador and much of the territories well. Precipitation stations are sparse there (34% of forest relies on stations up to 300 km away). Errors in those inputs weaken (attenuate) the estimated sensitivities.
- Compare forest-share burned across decades: the 2020 land cover undercounts forest that burned in 1995 to 2019.
- Give a full 1956 to 2026 snow trend: too few stations kept reporting snow on ground.
- Precipitation after 2017 is unadjusted daily data scaled by station ratios, not AHCCD itself. The hold-out test shows the scaling is unbiased to within 1% on season totals, but year-specific gauge changes after 2017 are not corrected.

## Method summary and files

Scripts (`scripts/`, run in order by `run_all.sh`; single-threaded):
- `01_ahccd_parse.py` parses AHCCD and selects stations.
- `02_fill_monthly.py` extends AHCCD with offsets, with QC and the hold-out test.
- `03_season_climate.py` builds the season variables, the area, region and national series, trends, differences and ranks.
- `04_select_long_stations.py` and `05_download_long.py` select and download the long hourly and daily records (anchored IDs within 3 km).
- `06_cwfis_fwi_trend.py` computes the CWFIS fixed-station trends.
- `07_area_burned_trend.py` builds the area burned series, the CNFDB check and the trends.
- `08_area_outcome.py` sums all-land hectares per area, 1972 to 2026.
- `09_sensitivity_counterfactual.py` fits the PPML and OLS panels, runs the bootstrap and computes the counterfactuals.
- `fwi.py` holds the FWI equations; `10_compute_fwi.py` computes station FWI, the trends and the validation.
- `11_snow_season.py` covers the snow season.
- `12_manifest.py` writes the manifest.

Trend statistics, everywhere:
- OLS slope with a 95% interval widened for lag-1 autocorrelation (effective sample size).
- Theil-Sen slope with its 95% interval, and the Mann-Kendall p-value.
- Area burned trends use log hectares with year-bootstrap intervals.

Downloads and reused inputs, with URLs, sizes and hashes, are listed in `manifest.csv`. Downloaded data are in `raw/` (AHCCD CDAS files; 306 hourly-noon and about 1,000 daily climate-ID files). Intermediate tables and logs are in `work/` (`log_01.txt` to `log_11.txt`).
