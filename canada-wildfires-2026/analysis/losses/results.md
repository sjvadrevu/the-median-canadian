# Wildfire losses: deaths, injuries, evacuations, buildings, money (2026, 2023 to 2026, and history)

Original analysis from raw official data, run 2026-10-21. News articles were used only to find official files; no number below comes from news. Industry data (CatIQ, IBC) is labelled as such. Files are in `analysis/losses/`; sources and download dates are in `manifest.csv`.

## Scorecard: human cost 2023 to 2026

| Measure | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| Deaths, wildfire aviation (TSB) | 1 | 2 | 0 | 6 |
| Other direct deaths in federal records | none found | none found | 2 (MB) | none found |
| People evacuated, Canada (federal statements) | over 200,000 | no national figure | over 70,000 | no national figure |
| First Nations people evacuated (ISC) | not published | over 15,469 | over 44,852 | 8,805 |
| First Nations evacuation events, fiscal year (ISC) | 90 (most of 10 years) | 26 | 73 (2nd) | not yet published |
| Buildings inside burned area (+ within 100 m) | 2,739 (+3,478) | 332 (+1,358) | 2,161 (+2,438) | 2,504 (+214) |
| Buildings likely destroyed (our dNBR estimate) | n/a | n/a | n/a | 146 (lenient rule 297) |
| Modelled smoke deaths, Chen (AQBAT) | 988 (379) | 260 (99) | 578 (219) | 253 (98) |
| Insured loss, wildfire (industry) | no public wildfire figure | Jasper CAD 1.304 B | no public wildfire figure | Bald Range CAD 293 M (45-day) |
| Federal disaster payments (DFAA) | CAD 793 M (7 orders) | CAD 184 M (3) | CAD 12.5 M (2, incomplete) | none yet |

Full table with source and coverage for every cell: `human_cost_2023_2026.csv`.

## Where official records lag behind 2026

- The Canadian Disaster Database stops at 2022. Its latest event starts 2022-12-22, and its latest wildfire event ran 2022-06-30 to 2022-09-27 (British Columbia). The open extract was refreshed on 2026-02-10 but added nothing after 2022. Public Safety Canada says events are added "some years after they are seen to have been concluded". It holds no 2023, 2024, 2025 or 2026 wildfire, so the CDD cannot rank 2023 to 2026 at all.
- ISC's fiscal-year evacuation table ends March 31, 2026 (page modified 2026-06-01, "numbers are not final"). The 2026 season figure (8,805 people to October 2) comes from ISC's live situation page, not from the table.
- AWCBC work-injury statistics end at 2024 and cannot separate wildfire work.
- TSB aviation data is current (files dated 2026-10-21, occurrences to 2026-10-08), but recent records can still change.
- Insured losses: CatIQ publishes per-event estimates in stages (initial, 45-day, 90-day, final at 2 years). The 2026 Bald Range figure is an early estimate.
- StatCan's site (www150.statcan.gc.ca) was unreachable all session (maintenance page and connection resets). CPI came from the same StatCan series served by the Bank of Canada, which starts in 1995, so CDD costs before 1995 stay in nominal dollars.

## 1. Canadian Disaster Database (Public Safety Canada)

- The CDD lists 123 wildfire events from 1903 to 2022, with 410 deaths, 14 injured and 418,067 evacuated in total.
- Most deaths are early: 233 in the 1916 Cochrane and Matheson fire (ON), 73 in Cochrane 1911, and 43 in Haileybury 1922. From 2000 to 2022 the CDD records 8 wildfire deaths: 1 in 2009, 2 in 2010, 1 in 2015, 2 in Fort McMurray 2016, and 2 in Lytton 2021.
- The largest evacuations were Fort McMurray 2016 (90,000), British Columbia 2017 (65,000), southeastern BC and southwestern Alberta 2003 (48,501), and northern Manitoba 1989 (25,000).
- By year, 2016 ranks first for both evacuated (92,702) and cost (CAD 5.20 B in 2025 dollars). 2017 ranks second for evacuated (65,000) and 2003 third (49,766).
- Costliest events, in 2025 dollars: Fort McMurray 2016 at CAD 5.20 B (nominal 4.07 B: insurance 3.6 B, federal DFAA 0.469 B), Slave Lake 2011 at CAD 0.80 B (insurance 0.528 B), BC 2014 at CAD 0.39 B, and BC 2010 at CAD 0.36 B.
- 1995 to 2022 totals in 2025 dollars: 95 events, CAD 7.99 B recorded cost, CAD 5.70 B insurance payments, and CAD 1.27 B federal DFAA payments. Provincial DFAA payments total CAD 17.4 M and provincial department payments CAD 693 M (both nominal). Federal DFAA payments appear on only 13 wildfire events since 1903.
- Coverage is uneven, as PS warns ("may not be suitable for comparative analysis"). Many events record cost as 0 or blank, meaning unknown. For example, 2021 shows only 2,753 evacuated, which cannot be the full 2021 total.
- Method: TOTAL_COST is used when it is above 0, otherwise the sum of the payment fields. This matters for Lytton 2021, where only insurance (CAD 102 M) is filled. Costs were normalised to 2025 dollars with annual average CPI (all-items, Canada). The open extract has no normalised-cost column.
- Files: `cdd_wildfire_events.csv`, `cdd_wildfire_by_year.csv` (ranks; years after 2022 left blank, not zero), `cdd_wildfire_by_decade.csv`; script `scripts/01_cdd.py`.

## 2. First Nations evacuations (Indigenous Services Canada)

- Evacuation events by fiscal year (April to March): 2016-17: 14, 2017-18: 29, 2018-19: 32, 2019-20: 16, 2020-21: 5, 2021-22: 57, 2022-23: 12, 2023-24: 90, 2024-25: 26, 2025-26: 73.
- FY2023-24 (90) is the highest of the 10 years and FY2025-26 (73) the second. FY2025-26 also has the most long-term evacuations (21 longer than 60 days, against at most 7 in any earlier year).
- The 10-year total is 354 events. The 2023 to 2025 seasons (FY2023-24 to FY2025-26) hold 189 of them (53%), against 165 in the 7 earlier years.
- Evacuees over the 10 years, FY2016-17 to FY2025-26: 143,724 people (12,314 long-term). By province: Manitoba 48,083, Alberta 28,216, Saskatchewan 27,647, Ontario 17,707, BC 11,848, Quebec 8,924, NWT 799 (2 eligible communities only), Yukon 462, Nova Scotia 20, Newfoundland 18. ISC does not publish evacuees per year or per community.
- Season figures in ISC records: April 1 to September 30, 2024: 91 wildfire events affected 84 First Nations and displaced over 15,469 people from 26 communities. April 1 to August 20, 2025: 119 events, 95 First Nations, over 44,852 people from 60 communities. April 1 to October 2, 2026: 87 wildland fires, 83 First Nations impacted, and 8,805 evacuated, with 87 people still evacuated on October 2.
- On ISC's own figures, 2026 displaced about a fifth of 2025's First Nations evacuees (8,805 vs over 44,852) despite a similar number of fires.
- Community-level and per-year evacuee tables are not published as open data. The NRCan "Wildfire Evacuations 1980-2003" dataset is only a map image.
- Files: `isc_wildfire_evacuations_by_fiscal_year.csv`, `isc_wildfire_evacuees_by_province_2016_2026.csv`, `isc_season_snapshots.csv`; script `scripts/02_isc.py`.

## 3. Firefighter and worker deaths and injuries

**Aviation (TSB air occurrence data, official):**
- Wildfire-work aircraft are those whose operation type is "fire fighting / fire management", plus 4 occurrences found by keyword whose TSB summary describes wildfire work (A04W0165, A19P0059, A23W0082, A25A0051). Each keyword match with a death or serious injury since 1995 was read; the others were smoke-affected or unrelated flights.
- Deaths by year: 2023: 1 (A23W0082, Bell 205 bucketing near Haig Lake, AB, July 19), 2024: 2 (A24W0079, Bell 212 on fire suppression near Fort Good Hope, NT, June 28), 2025: 0, 2026: 6 (A26W0082, Commander 690C air attack / bird-dog flight from Fort Simpson, NT, June 24).
- 2026 is the deadliest year for wildfire aviation since 1995. The previous high was 5 in 1995.
- 2023 to 2026 total 9 deaths, the most in any 4-year window since 1995 (previous maximum 7). The 1995 to 2022 average is 0.89 deaths a year (25 in 28 years).
- Serious injuries 2023 to 2026: 0, 0, 1 (NS, 2025-08-15, helicopter refilling a bucket), 0. Minor injuries: 2, 0, 0, 1.
- Wildfire-work occurrences: 23, 19, 22 and 12 (2026 to 2026-10-08), against 5 to 36 a year since 1995.
- Files: `tsb_firefighting_by_year.csv`, `tsb_firefighting_occurrences.csv` (every occurrence with summary), `tsb_wildfire_text_matches.csv`; script `scripts/03_tsb.py`.

**Ground firefighters and other workers:**
- No official open dataset identifies wildland-firefighter deaths or injuries.
- AWCBC public tables (latest 2024) use one combined industry group, "Agriculture, forestry, fishing and hunting", with 175 accepted fatalities in 2024. Its event codes count all fires: "Fire" fatalities were X (3 or fewer) in 2022, 5 in 2023 and 4 in 2024. Aircraft-accident fatalities (all industries) were 7, 11 and 18.
- These numbers are context only and are not wildfire counts. File: `awcbc_fatalities_context_2022_2024.csv`; script `scripts/04_awcbc.py`.

**Civilian deaths:** the only official statement found for 2023 to 2026 is Public Safety's note that two Manitobans died in Lac du Bonnet in 2025 (QP notes PS-2025-QP-005 and PS-2026-QP-006).

## 4. Insured losses (industry data, not government)

- CatIQ publishes only selected event estimates publicly; the full database is subscription-only. No public wildfire-only annual total exists. Values used, from CatIQ's own posts:
  - Jasper wildfire complex 2024: CAD 1.304 B (final estimate, 2026-07-22). It is the second-costliest Canadian wildfire, after Fort McMurray 2016 at CAD 3.64 B (as quoted by CatIQ).
  - Bald Range fire, Summerland BC, 2026: CAD 313 M initial (2026-09-15), revised to CAD 293 M at 45 days (2026-10-06).
- All-peril catastrophe totals for context: 2023 CAD 3.1 B, 2024 CAD 8.5 B (later 9.1 B), 2025 CAD 2.4 B.
- Fire catastrophe counts from CatIQ: 2025 had the most fire catastrophes declared of any year (five), "ten fire-related catastrophes have been declared since 2023" (as of July 2025), and BC had three fire catastrophes declared in 2026 by September 15.
- CDD insurance payments (government compilation) for history: Fort McMurray 2016 CAD 3.6 B, Slave Lake 2011 CAD 528 M, BC 2017 CAD 130 M, Lytton 2021 CAD 102 M, Central Okanagan 2021 CAD 77 M.
- File: `insured_losses_wildfire.csv` (each value with its quoted sentence and URL); script `scripts/06_insured.py`.

## 5. Buildings exposed to 2026 fires

- Method: Microsoft Global ML Building Footprints (release 2026-02-03) against the 718 CWFIS M3 2026 outlines. The 16 outlines classed "likely agricultural or grass burn" (10) or "military range" (6) were dropped. The 2 "possible industrial or urban heat" outlines were kept apart and contain no buildings.
- 251 footprint tiles (361,131 footprints) were streamed and discarded. A building counts as inside if its footprint centroid is inside an outline, and as within 100 m if the centroid is outside every outline but within 100 m of one.
- Result: 2,504 buildings inside 2026 outlines and 214 more within 100 m (2,718 in total). This is exposure, not loss.
- By province (inside + within 100 m): BC 2,107 + 144, Ontario 202 + 37, NWT 147 + 9, Manitoba 13 + 17, Quebec 20 + 2, Saskatchewan 13 + 2, Alberta 2 + 3.
- By fire area: BC Kamloops Fire Centre 988, BC Cariboo 849, BC Coastal 408, Ontario Thunder Bay 227, NWT Deh Cho 155, Manitoba Area 22 26, Saskatchewan Prince Albert 10.
- By community (largest groups): around Summerland 613 near plus 145 inside the Summerland population centre; near Boston Bar First Nation 285; near Liidlii Kue First Nation (Fort Simpson) 154; near Ts'kw'aylaxw First Nation 116; near Whitesand First Nation 103; near Lac des Mille Lacs First Nation 97; near Peachland 57. In BC, 738 buildings have no named community within 25 km (mostly rural properties in fire 36077449).
- 9 fires have 10 or more buildings inside. They hold 2,439 of the 2,504 buildings inside.
- Community rule: the reserve or settlement polygon name (AL_TA) if the building is inside one; else the 2021 population-centre name if inside one; else the nearest population centre or First Nation within 25 km ("near ..."). Fire area comes from `data/geo/fma_v2.gpkg`.
- Same method on NBAC final burned-area polygons (prescribed burns excluded):
  - 2023: 2,739 buildings inside and 3,478 within 100 m. Inside counts: Alberta 1,050, BC 869, Nova Scotia 528, Quebec 178, NWT 64.
  - 2024: 332 inside and 1,358 within 100 m. Parks Canada lands (Jasper) account for 104 inside and 441 within 100 m.
  - 2025: 2,161 inside and 2,438 within 100 m. Inside counts: Saskatchewan 792, Newfoundland and Labrador 716, Manitoba 381.
- On buildings inside burned areas, 2026 (2,504) ranks second of the 4 years, behind 2023 (2,739).
- The years are not fully comparable:
  - 2026 uses coarse hotspot-derived M3 outlines. They put more buildings "inside" and fewer "within 100 m" than NBAC's mapped edges, which follow unburned town areas.
  - Buildings destroyed before the footprint imagery date may be missing, which undercounts the earlier years.
  - In 2024, only 104 footprints fall inside NBAC polygons on Parks Canada land, although CatIQ reports 358 of the Jasper townsite's 1,113 structures damaged or destroyed. Whether NBAC excludes the townsite or footprints are missing was not resolved here.
- Files: `buildings_exposure_by_fire.csv`, `buildings_exposure_by_community.csv`, `buildings_exposure_by_province.csv`, `buildings_exposure_by_fire_area.csv`, `buildings_2026_near_outlines.gpkg` (points), `buildings_exposure_by_year_nbac.csv`; scripts `scripts/05_buildings.py`, `05b_buildings_nbac.py`, `07_buildings_summary.py`.
- Limits:
  - M3 outlines are hotspot-derived and coarse, so they can include unburned islands and miss burned edges.
  - Footprints come from imagery of various dates, and remote northern settlements may be under-mapped.
  - The original Microsoft Canadian release (2019) is no longer publicly downloadable (HTTP 409). StatCan's ODB could not be fetched while StatCan was down.

## 6. Buildings likely destroyed in 2026 (our estimate from Sentinel-2)

- All 9 fires with 10 or more buildings inside were done: 2,634 buildings.
- Imagery: Sentinel-2 L2A from AWS Earth Search STAC (keyless). For each fire, the post-fire composite uses up to 6 lowest-cloud scenes after the fire's last detection (or the last 30 days to 2026-10-20 for fires still active). The pre-fire composite uses the same calendar window in 2025 (anniversary pairing, to match vegetation season).
- Compositing: per-pixel median of NBR = (B8A - B12) / (B8A + B12), with the scene classification layer masking cloud, shadow and snow.
- dNBR = (pre - post) x 1000, minus the median dNBR of pixels more than 1 km outside all 2026 outlines (offsets -56 to +40). All scene IDs and dates are in `dnbr_scenes.csv`. Post scenes are from August 7 to October 20, 2026, mostly late September and October.
- Thresholds are the standard USGS / FIREMON dNBR classes (Key and Benson 2006): unburned -100 to 99, low 100 to 269, moderate-low 270 to 439, moderate-high 440 to 659, high 660 and above.
- A building is **likely destroyed** if the highest dNBR on the 20 m pixels its footprint touches is at least 440 (moderate-high) and the median dNBR of the 20 to 60 m ring around it is at least 270 (moderate burn around it). **Damaged surroundings** means a ring median of at least 100 that misses the destroyed test. **Unburned** means a ring median below 100 and a building value below 270.
- Results by fire (likely destroyed / damaged surroundings / unburned):
  - Bald Range, Summerland (BC, 816 buildings): 58 / 158 / 600.
  - Whitesand area (ON, 124): 53 / 52 / 19.
  - Fire 36077449 near Ts'kw'aylaxw and High Bar (BC, 904): 15 / 128 / 750 (11 no clear data).
  - Lac des Mille Lacs area (ON, 102): 12 / 43 / 47.
  - Boston Bar area (BC, 424): 7 / 28 / 387.
  - Nickeyeah reserve area (BC, 35): 1 / 12 / 22.
  - Okanagan reserve area (BC, 49): 0 / 11 / 38.
  - Fort Simpson / Liidlii Kue (NT, 154): 0 / 7 / 147.
  - Norway House (MB, 26): 0 / 0 / 26.
- Total: 146 likely destroyed, 439 with burned surroundings, 2,036 unburned and 13 with no clear data.
- A lenient rule (building at least 270 and ring at least 100) gives 297 possibly destroyed.
- Calibration:
  - No official destroyed-structure count was found published as data for any 2026 fire. The District of Summerland and RDOS pages list orders and properties, not counts. The threshold is therefore not calibrated.
  - Spot check: the District of Summerland Prohibit Entry Order of 2026-09-29 lists 29 properties. These were geocoded with the BC Address Geocoder and matched to the nearest classified building within 60 m.
  - 17 matched: 10 classed "damaged surroundings", 7 "unburned", none "likely destroyed". 5 of the 17 pass the lenient rule. 12 had no footprint within 60 m.
  - The order covers properties with ongoing hazards, not only destroyed buildings. Even so, the check shows the main rule is conservative in this orchard and grassland setting, where a burned house often sits in moderate rather than high dNBR at 20 m.
  - Read 146 as a lower bound and 297 as a looser upper reference.
  - In closed forest (the Ontario fires) the opposite error is likely: a cabin under a high-severity canopy can be classed destroyed even if it survived.
- Technical note: the STAC metadata lists a reflectance offset of -0.1, but the pixel values do not carry it (with it, 5 to 25% of SWIR pixels over vegetation turn negative). NBR is a ratio, so only the scale is used.
- Files: `dnbr_buildings.csv` (every building with dNBR values and class), `dnbr_by_fire.csv`, `dnbr_by_community.csv`, `dnbr_scenes.csv`, `summerland_prohibit_entry_check.csv`, `work/dnbr_<fire_uid>.tif`; scripts `scripts/08_dnbr.py`, `09_summerland_check.py`, `10_dnbr_summary.py`.

## 7. Combined human-cost table

- See the scorecard and `human_cost_2023_2026.csv` (script `scripts/11_human_cost.py`).
- Modelled smoke deaths are copied from `analysis/health/modelled_acute_deaths_national.csv` (net, central with 95% range), not recomputed:
  - Chen 2021: 2023: 988 (840 to 1,133); 2024: 260 (220 to 299); 2025: 578 (490 to 665); 2026: 253 (216 to 290).
  - AQBAT: 379 (0 to 557), 99 (0 to 145), 219 (0 to 323), 98 (0 to 144).
  - 2025 and 2026 cover 9 provinces and territories (not MB, NL, NT, NU). These are model estimates, not counts.
- Modelled smoke deaths outnumber recorded direct deaths by two orders of magnitude in every year. For 2023 to 2026: about 2,079 (Chen) or 795 (AQBAT) modelled, against 11 direct deaths in official records (9 aviation + 2 Manitoba).

## 8. Federal disaster payments (DFAA)

**Source:** the CDD ends in 2022, so 2023 to 2025 come from the federal Proactive Disclosure of Grants and Contributions (open.canada.ca, grants.csv modified 2026-10-21; 1,328,384 rows streamed, 292 kept). Its rows for the program "(DFAA) Disaster Financial Assistance Arrangements" disclose each Provincial Emergency Financial Assistance Order with a value. These values are the federal amounts set in each order (interim or advance payments at the agreement date), not final settlements. Disclosures dated 2018 to 2022 show value 0, so earlier events cannot be compared on this source.

**Wildfire ("interface fires") DFAA orders by event year:**
- 2022: CAD 24.7 M (BC).
- 2023: CAD 793.3 M in 7 orders. BC 358.9 M, NWT 188.6 M, AB 149.6 M, QC 36.3 M, SK 33.0 M, NS 26.6 M, YT 0.2 M.
- 2024: CAD 183.9 M in 3 orders. AB 106.4 M (the Jasper year), BC 71.4 M, NWT 6.1 M.
- 2025: CAD 12.5 M in 2 orders so far. SK 8.5 M, YT 4.0 M; dated 2025-09-18. Manitoba, which had the 2025 deaths and large evacuations, has no 2025 fire order yet.
- 2026: none yet. The latest DFAA order in the data is dated 2025-11-21.

**Comparison with history:**
- The 2023 wildfire orders alone (CAD 793 M nominal) are close to the CDD's total federal DFAA for all wildfires from 1903 to 2022 (CAD 942 M nominal, 1.27 B in 2025 dollars).
- They exceed the largest single CDD event, Fort McMurray 2016 (CAD 469 M nominal, 599 M in 2025 dollars).
- In 2023, wildfire orders were 82% of all DFAA order value for 2023 events (793 M of 972 M).

**Lag:** DFAA orders come one to two years after the event. 2025 is incomplete and 2026 has nothing yet.

Files: `dfaa_wildfire_payments.csv`, `dfaa_all_events_by_year.csv`, `raw/grants/grants_dfaa_wildfire_subset.csv`; scripts `scripts/12_grants_filter.py`, `13_dfaa.py`.

## Files

- Scripts in `scripts/`: run 01 to 10, then 12, 13 and 11 (11 reads the DFAA output). 00 writes the manifest.
- Raw downloads in `raw/`. The TSB CSVs were deleted after the run and can be re-downloaded (see manifest). The full QP-note and grants files were streamed and only subsets kept.
- Intermediates in `work/`: building parts, dNBR rasters, logs.
