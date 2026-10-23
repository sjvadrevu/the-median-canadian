# Six threads: emissions gap, reburns, overwintering fires, repeat exposure, prescribed burning, drinking water

Original analysis of raw official data, run 2026-10-21. No numbers come from articles. Scripts are in `scripts/` (t1a, t1a2, t1b, t2a, t2b, t2, t3a, t3, t3b, t4, t5, t6, t6b) and logs in `work/`. Sources are listed in `manifest.csv`. "Mapped" means satellite footprints (NBAC 1972 to 2025, CWFIS M3 outlines for 2026, which run about 18% above the official 2026 total). "Scaled" means each cell is multiplied by its province's official/mapped ratio, as in `analysis/economy`.

## Scorecard

| Thread | Headline | Status |
|---|---|---|
| 1 Emissions gap | All wildfire CO2 is outside the national total. The 2023 official managed-forest wildfire line alone (870 Mt CO2e) is 127% of the national total (686.9 Mt) | Done. The managed boundary comes from a georeferenced official image |
| 2 Reburns | In BS/JP-leading forest, 7.5% of 2023 to 2026 burned area had burned within 15 years, against 2.3% in the 1990s | Done. Regrowth check skipped |
| 3 Overwintering | 2023-24: 32 clusters with Dec to Mar detections; 2024-25: 11; 2025-26: 5. No 2026 spring fire is credibly linked to one | Done, with low confidence |
| 4 Repeat exposure | 30.8% of on-reserve people lived within 10 km of fire in 2 or more of the 4 years, against 6.4% off reserve (1,000 ha fires: 3.3% vs 0.11%) | Done |
| 5 Prescribed burning | CNFDB holds only 438 prescribed burns in 1980 to 2025 (166,396 ha), 66% of them Parks Canada | Done. The source is very incomplete |
| 6 Drinking water | 110 of 1,341 NHN watersheds were more than 10% burned in 2023 to 2026; they contain 29 population centres (106,904 people). In BC, 23 of 466 community watersheds were over 10% burned | Done. No upstream routing |

## 1. What Canada's official emissions total leaves out

**Findings**

**Official inventory (NIR 2026; values in Tables 6-1 and 6-5 are published rounded to 2 significant figures)**
- National total excluding LULUCF: 686.9 Mt in 2023 and 684.7 Mt in 2024. The CSV category 0 equals the sum of all non-LULUCF categories, within 0.05 Mt.
- LULUCF total: -8.7 Mt in 2023 and +4.3 Mt in 2024. Forest Land: +1.3 Mt and -1.2 Mt.
- Managed forest area: 230,000 kha in every year.
- Wildfire direct immediate emissions in the managed forest:

| Year | Mt CO2e | Mt CO2 | Share of national total |
|---|---|---|---|
| 2016 | 93 | 80 | 12.8% |
| 2017 | 200 | 170 | 27.1% |
| 2018 | 220 | 190 | 29.4% |
| 2019 | 130 | 110 | 17.4% |
| 2020 | 12 | 11 | 1.8% |
| 2021 | 260 | 220 | 37.6% |
| 2022 | 79 | 68 | 11.4% |
| 2023 | 870 | 750 | 126.7% |
| 2024 | 320 | 270 | 46.7% |

- How these are excluded: Table 6-5 lists them under "emissions/removals from lands impacted by natural disturbances". Its footnote says these are "tracked but not reported", and the "Reported estimates" line leaves them out. Table 6-1 shows natural disturbances as a separate transparency line: 1,000 Mt in 2023 and 430 Mt in 2024. That line says it is "not a reporting category".
- Wildfire in unmanaged forest is not estimated anywhere in the inventory.
- So none of the wildfire CO2 is in the national total. The managed part appears only as a memo line; the unmanaged part does not appear at all.

**Our aboveground estimate (economy method), split managed and unmanaged**

Low to high range, scaled, Mt CO2:

| Year | All burned area | Unmanaged forest | All, share of national | Unmanaged, share of national |
|---|---|---|---|---|
| 2016 | 14.8 to 48.8 | 2.3 to 6.6 | 2.0% to 6.7% | 0.3% to 0.9% |
| 2017 | 36.0 to 116.2 | 10.8 to 30.0 | 4.9% to 15.7% | 1.5% to 4.1% |
| 2018 | 37.8 to 132.2 | 3.4 to 10.6 | 5.0% to 17.6% | 0.5% to 1.4% |
| 2019 | 19.6 to 78.4 | 3.4 to 10.2 | 2.6% to 10.5% | 0.4% to 1.4% |
| 2020 | 2.0 to 7.2 | 0.3 to 0.9 | 0.3% to 1.1% | 0.04% to 0.13% |
| 2021 | 46.5 to 153.2 | 6.3 to 18.9 | 6.7% to 22.2% | 0.9% to 2.7% |
| 2022 | 15.0 to 47.5 | 3.5 to 10.1 | 2.2% to 6.8% | 0.5% to 1.5% |
| 2023 | 175.2 to 602.9 | 40.2 to 120.0 | 25.5% to 87.8% | 5.8% to 17.5% |
| 2024 | 49.5 to 163.4 | 13.3 to 39.2 | 7.2% to 23.9% | 1.9% to 5.7% |
| 2025 | 81.1 to 254.1 | 14.6 to 43.1 | 11.8% to 37.1% | 2.1% to 6.3% |
| 2026 | 39.4 to 121.4 | 15.7 to 43.2 | 5.8% to 17.7% | 2.3% to 6.3% |

- 2025 and 2026 are compared with the 2024 inventory, the latest year.
- Share of burned area in the managed forest (mapped): 2023 61.8%, 2024 62.4%, 2025 77.4%, 2026 48.2%. The 2016 to 2022 range is 53.8% to 81.6%. 2026 is the lowest share in the series because the NWT burned most.
- Our managed-forest high case is below the official managed figure every year. In 2023 it was 483 Mt CO2 against 750 Mt CO2. This fits with ground fuels, dead wood and peat being left out of our estimate.
- The combined figure that is outside the total each year is the official managed line plus our unmanaged range. For 2023 that is 870 + 40 to 120 = 910 to 990 Mt CO2e, 132% to 144% of the national total. This mixes the official all-pools figure with our aboveground-only figure, so it is a floor for the unmanaged part.

**Method**
- Managed boundary: the GHG managed-forest boundary is not published as open GIS data. I checked open.canada.ca, the NFIS ccfm_managed_forests WFS/WMS and NFI tables.
- The NFIS "Map of Forest Management in Canada" does not work as the boundary. Its own abstract says it differs from the GHG managed-forest map, and its classes cover all of Canada.
- I therefore georeferenced NRCan's official managed/unmanaged image (570 x 383 px) by fitting an affine transform to StatCan provinces in EPSG:3978. The fit has pixels of 12.0 x 13.0 km and a land-mask IoU of 0.75; 99.0% of forest-coloured pixels land on Canadian land.
- Validation: LC2020 forest inside the managed class comes to 229.2 Mha of 349.5 Mha (65.6%). The NIR reports 230,000 kha.
- Non-forest pixels take the class of the nearest forest-coloured pixel.
- CO2 per cell follows the economy step 07b exactly (SCANFI pre-fire biomass, kNN foliage and non-stem shares). Province-year totals match `../economy/timber_carbon_by_year.csv`.
- Files: `t1_official_inventory_lines.csv`, `t1_wildfire_co2_managed_split_by_year.csv`, `t1_managed_forest_area_check.csv`, `work/mf_affine.json`, `work/mf_fit_check2.png`.

**Coverage and caveats**
- The boundary is accurate to about 1 image pixel (12 to 13 km), and the image's own date is not stated.
- The rounding of the official values (2 significant figures) carries into every ratio.

## 2. Reburns and regrowth risk

**Findings**

Share of each period's burned area that had burned within the previous 15 years:

| Period | All burned area | BS/JP-leading forest (SCANFI, pre-window map) |
|---|---|---|
| 1990s | 2.9% | 2.3% |
| 2000s | 3.0% | 2.9% |
| 2010s | 3.2% | 3.4% |
| 2020 to 2022 | 4.5% | 5.5% |
| 2023 to 2026 | 6.6% (535,185 ha a year) | 7.5% (343,906 ha a year) |

- In the 1990s the reburned area was 71,247 ha a year (all burned area) and 36,282 ha a year (BS/JP).
- The rise holds for every window in BS/JP forest. In the 1990s compared with 2023 to 2026:

| Window | 1990s | 2023 to 2026 |
|---|---|---|
| 5 years | 0.75% | 1.13% |
| 10 years | 1.17% | 5.0% |
| 15 years | 2.3% | 7.5% |
| 20 years | 3.1% | 9.7% |

- Reburned BS/JP area per year rose about 9.5 times on the 15-year window: from 36,282 ha in the 1990s to 343,906 ha in 2023 to 2026.
- By year (15-year window, all area): 2023 5.5%, 2024 5.7%, 2025 10.8%, 2026 4.7% (the 2026 basis is M3).
- By province, 2023 to 2026 combined, 15-year window (all area), reburned hectares and share:

| Province | Reburned (ha) | Share |
|---|---|---|
| SK | 689,658 | 15.3% |
| NT | 639,417 | 7.5% |
| AB | 260,566 | 6.2% |
| BC | 168,469 | 4.0% |
| MB | 163,221 | 5.9% |
| ON | 118,877 | 6.7% |
| QC | 76,414 | 1.4% |

- In BS/JP forest: SK 16.1%, NT 8.1%, ON 7.5%, AB 7.0%, MB 6.2%.
- Largest fire management areas (15-year window): NWT South Slave 386,444 ha (14.8%), SK La Ronge 227,378 ha (18.5%), Île-à-la-Crosse 151,980 ha, NWT North Slave 150,881 ha, SK Denare Beach 130,905 ha (24.0%).
- Quebec 51 Eastmain: 43% of its 2023 to 2026 burn was reburn within 15 years, but on only 64,344 ha.
- The LC2020 needleleaf filter gives low and falling shares (1.9% for 2023 to 2026). This is expected and should not be used: the 2020 map shows post-fire cover, so recently burned land is rarely classed as needleleaf. The filter therefore removes exactly the short-interval reburns. It is reported only as a check.

**Method**
- Grid: the 240 m cell-centre grid from `analysis/forest` (NBAC 1972 to 2025 including prescribed burns; M3 2026, all 718 outlines). There are 20.29 M cells ever burned.
- Reburn within k years: the cell's most recent previous burn falls in years Y-k to Y-1.
- SCANFI v2 BS/JP-leading: black spruce + jack pine crown closure is at least 50% of total closure, with total closure at least 10%. The map epoch is the one at or before the start of the window (1985 to 2020).
- The SCANFI layers are read from the 1/16 overview (480 m), which is a decimated sample: it matched the top-left pixel of each block 38% of the time (r = 0.65) and the block mean with r = 0.56. It is therefore noisy per cell but unbiased for large-area shares.
- Files: `t2_reburn_national_by_year.csv`, `t2_reburn_by_period.csv`, `t2_reburn_2023_2026_by_province.csv`, `t2_reburn_2023_2026_by_fma.csv`, `work/lc2020_needleleaf_count_240m.tif`.

**Not done: regrowth check (NDVI recovery)**
- I skipped it. A Landsat, Sentinel-2 or MODIS time series over millions of hectares needs downloads well beyond the 5.5 GB of free disk and the shared 2-core machine.
- The reburn result does not depend on it.

**Caveats**
- 2026 uses M3 outlines, which are larger than the true burned area and include unburned islands.
- Early NBAC years (1970s and 1980s) are less complete, which slightly understates reburns in the 1990s windows.

## 3. Overwintering ("zombie") fires

**Findings**

Satellite detections from November to April inside or within 1 km of the previous season's NBAC perimeters:

| Winter | Detections near prior perimeters | Removed as persistent | Removed near facility | Kept | Clusters |
|---|---|---|---|---|---|
| 2023-24 | 342 | 37 | 23 | 282 | 81 |
| 2024-25 | 248 | 85 | 18 | 145 | 42 |
| 2025-26 | 74 | 17 | 1 | 56 | 23 |

- Deduplicated winter detections across Canada: 11,189, 10,229 and 8,497.
- Clusters with any December to March detection (the deep-winter holdover signal):
  - 2023-24: 32 (AB 15, BC 16, MB 1)
  - 2024-25: 11 (AB 10, BC 1)
  - 2025-26: 5 (BC 4, AB 1)
- Restricting to prior fires of at least 1,000 ha, which removes likely slash-pile and debris burning on small polygons, leaves 20, 3 and 2 deep-winter clusters.
- The 2023-24 cases sit on large 2023 fires: Donnie Creek BC (465,679 ha NBAC polygon), a 217,958 ha fire and a 101,337 ha fire in northern Alberta, and several fires of 17,000 to 54,000 ha near Edson and Grande Prairie.
- Other classes:

| Class | 2023-24 | 2024-25 | 2025-26 |
|---|---|---|---|
| "November only" (likely late tail of the season) | 20 | 12 | 18 |
| "April only" (spring burning, ambiguous) | 29 | 19 | 0 |

- 2026 spring fires: 22 agency fires reported from March to June 2026 lie within 2 km of a 2025-26 cluster detection. 21 are tiny human-caused fires (0.01 to 0.6 ha) near Lac La Biche, matched to a single November detection on a 2 ha prior polygon. The other is a 0.01 ha human fire in the Peace River area. None looks like a holdover re-emerging, so no 2026 spring fire can be credibly traced to an overwintering fire.
- The agency list does record carry-overs. The NRCan 2026 fire list holds 60 fires with fire year 2025 that were still being reported in 2026: AB 16 (464,129 ha) and BC 44 (696,666 ha). 22 of them were re-reported in March 2026.
- Only 2 of these 60 lie within 2 km of a satellite cluster (median distance 118 km in AB and 143 km in BC). Satellite winter detection therefore misses most agency-tracked carry-over fires, which likely smoulder below detection thresholds.

**Method**
- Hotspots: CWFIS annual archives 2023 to 2025 plus the 2026 WFS daily archive, 7.12 M raw rows, deduplicated to one per sensor per 1 km Albers cell per UTC day (1.95 M, of which 1.71 M are in Canada).
- Persistent exclusion: the cell or one of its 8 neighbours has detections in at least 3 of the calendar years 2023 to 2026, or winter detections in at least 2 winters.
- Facility exclusion: within 2 km of any of 18,130 NPRI facility locations reported in 2010 or later. NPRI covers oil sands, gas plants and mills.
- Clusters are formed by 3 km single linkage.
- Files: `t3_winter_filter_summary.csv`, `t3_holdover_clusters.csv`, `t3_holdover_detections.csv`, `t3_holdover_by_winter_province.csv`, `t3_holdover_by_prior_fire_size.csv`, `t3_spring2026_fires_near_holdovers.csv`, `t3_agency_carryover_fires_in_2026_list.csv`.

**Caveats**
- Winter satellite detection is sparse (short days, snow, cloud).
- Slash and debris burning in BC and Alberta from November to March cannot be told apart from holdovers without agency burn-permit data, which was not found as open data. The 1,000 ha subset is the more defensible count.

## 4. Repeat exposure of First Nations, 2023 to 2026

**Findings**

Exposed = within 10 km of a fire outline in a year (NBAC 2023 to 2025 without prescribed burns; M3 2026 without the 13 agricultural, grass and military outlines).

| Measure (all outlines) | 2+ years | 3+ years | All 4 years |
|---|---|---|---|
| Reserves (of 3,322) | 731 (22.0%) | 272 | 66 |
| Populated reserves (of 765) | 252 (32.9%) | 107 | 26 |
| First Nation communities (of 638) | 135 (21.2%) | 45 | 7 |
| Population centres (of 1,026) | 158 (15.4%) | 49 | 5 |
| On-reserve people | 104,668 (30.8%) | 34,581 (10.2%) | 4,664 (1.4%) |
| Off-reserve people | 2,356,483 (6.4%) | 400,141 (1.1%) | 9,158 (0.03%) |

- On-reserve people are about 4.8 times more likely than others to have had 2 or more exposed years, and about 9 times more likely to have had 3 or more.
- On the like-for-like basis (fires of 1,000 ha or more), 2 or more years covers:
  - 164 reserves and 12 communities
  - 11,295 on-reserve people (3.3%) against 39,737 off-reserve people (0.11%), about 31 times
  - 6 population centres
- At 200 ha or more, the figures are 6.7% on reserve against 0.19% off reserve.
- Exposed in all 4 years:
  - Communities (7): Chemawawin Cree Nation, Kanaka Bar, Lake St. Martin, Little Saskatchewan, Penticton, Siska, Skuppah
  - Most populated reserves: Norway House 17 (MB, 5,363), Okanagan 1 (3,335), Penticton 1 (2,080), Chemawawin 2 (1,264), Fairford 50 (1,144)
- On-reserve people with 2 or more exposed years, by province: MB 34,051 (59.9% of on-reserve people), BC 32,374 (38.6%), SK 21,127 (37.9%), AB 9,671 (21.9%).
- Population centres exposed all 4 years: Peachland, Naramata, Penticton, Summerland (BC) and Chemawawin 2 (MB).

**Method**
- Reuses the geodesic distance files in `../people/work/`. Population centre distances were computed here as polygon edge distance in Albers.
- The "all outlines" rows mix NBAC (many small agency-mapped fires near southern towns, such as southern Quebec and Nova Scotia) with M3 for 2026. Use the 200 ha and 1,000 ha rows for comparisons.
- Files: `t4_repeat_exposure_summary.csv`, `t4_repeat_exposure_by_province.csv`, `t4_reserves_years_exposed.csv`, `t4_fn_communities_years_exposed.csv`, `t4_popcentres_years_exposed.csv`.

**Caveats**
- 174 incompletely enumerated reserve DAs have no population, so on-reserve counts are lower bounds.
- Being within 10 km is not the same as being evacuated.

## 5. Prescribed burning, 1980 to 2025

**Findings**
- The CNFDB (version 20260811) flags only 438 prescribed burns in 1980 to 2025, covering 166,396 ha. That is 0.12% of the 139.5 M ha of other fires.
- None are recorded before 1993.
- By agency:

| Agency | Burns | Area (ha) | Years |
|---|---|---|---|
| Parks Canada | 291 | 90,087 | 2008 to 2025 |
| Ontario | 79 | 23,073 | 1994 to 2025 |
| NWT | 36 | 52,424 | 1993 to 2000 only |
| Alberta | 24 | 793 | 1999 to 2011 |
| Yukon | 7 | 10 | 2022 |
| PEI | 1 | 9 | 2025 |

- BC, SK, MB, QC and the Atlantic provinces have none.
- Trend:

| Period | Burns a year | Area a year (ha) |
|---|---|---|
| 1980 to 1999 | 2.9 | 2,945 |
| 2000s | 8.0 | 2,097 |
| 2010s | 20.1 | 7,259 |
| 2020 to 2025 | 16.5 | 2,325 |

- The rise in recorded counts is significant (Kendall tau 0.61, p < 0.001; Theil-Sen +0.44 burns a year), and so is the rise in area (tau 0.42, p < 0.001).
- Wildfire area shows no significant trend over the same years (tau 0.17, p = 0.10).
- The prescribed share of area peaked in 2018 at 1.6% (37,178 ha). In 2023 it was 0.0007% (131 ha).
- NBAC flags 411 prescribed polygons, which gives a similar picture: Parks Canada 379 (153,714 ha), BC 4 (13,447 ha), AB 14, ON 12, QC 1, SK 1. The NBAC peak was 2017, with 35,629 ha.

**Method**
- A record counts as prescribed if PRESCRIBED is 'PB' or '1', CAUSE2 is 'H-PB', or FIRE_TYPE is 'PB' or 'Prescribed Burn'. The crosstab of these flags is in `t5_prescribed_flag_crosstab.csv`.
- Files: `t5_prescribed_by_prov_year.csv`, `t5_prescribed_national_year.csv`, `t5_prescribed_trend.csv`, `t5_nbac_prescribed_by_admin.csv`, `t5_nbac_prescribed_by_year.csv`.

**Caveat: this is a reporting record, not a measure of the national prescribed-fire programme**
- Most provincial prescribed and cultural burns are not submitted to the CNFDB as prescribed records.
- The trend mostly reflects Parks Canada and Ontario reporting.
- The NFD cause tables have no prescribed class.

## 6. Drinking water sources

**Findings: national (NRCan NHN work units, burned share 2023 to 2026, union of footprints)**

| Burned share | Watersheds (of 1,341) | Population centres inside | People |
|---|---|---|---|
| Over 5% | 168 | 43 | 142,136 |
| Over 10% | 110 | 29 | 106,904 |
| Over 20% | 47 | 8 | 20,401 |

- At the WSC sub-sub-drainage level, 100 of 971 areas were more than 10% burned, containing 30 population centres (108,086 people).
- Most burned watersheds: Great Slave Lake - Outlet 84.6%, Lower Sakami (QC) 49.2%, Kakisa 48.1%, Central Slave 45.8%, Petitot 45.7%.
- Largest population centres in watersheds more than 10% burned:

| Population centre | Population | Watershed burned |
|---|---|---|
| Yellowknife | 19,673 | 12.1% |
| Thompson | 12,329 | 16.7% |
| Whitecourt | 9,195 | 15.1% |
| Edson | 8,166 | 15.1% |
| Chibougamau | 6,491 | 13.1% |
| La Ronge | 5,317 | 42.3% |
| Flin Flon | 4,722 | 22.5% |
| Hope | 4,434 | 17.8% |
| Peace River | 4,264 | 12.4% |
| Hay River | 2,380 | 13.8% |
| Fort Smith | 1,749 | 45.8% |

- A single year above 10%: 2023 had 47 watersheds (14 centres), 2025 had 23 (11 centres) and 2026 had 10 (1 centre, Hope).

**Findings: British Columbia (published drinking-water intake data)**
- BC publishes its 466 designated Community Watersheds, each the drainage area upstream of a licensed community water intake. I used these in place of the simple method, as the brief asked.
- 61 had any area burned in 2023 to 2026, 26 were more than 5% burned, 23 more than 10% (14 named water systems) and 15 more than 50%.
- Fully or nearly fully burned watersheds include:
  - Boston Bar Integrated Water System (Two Mile and One & One Quarter watersheds at 100%, Stoyoma at 90.7%)
  - North Bend (Drachmann, 100%)
  - Clinton (94.5% of 6,630 ha)
  - WestBank (Rose Valley 93.5%, Lambly 11.1%)
  - Kahmoose IR 4 & 5B (Jamieson, 100%)
  - Coutlie Creek (100%)
- The largest system with an intake in a watershed more than 10% burned is Kimberley (Matthew Creek, 13.2%, reported population served 6,746).
- Of 337 surface-water intakes in DWS_SOURCE_POINT, 10 are in a community watershed or NHN work unit more than 10% burned (reported population served 7,648) and 35 above 5% (21,420).
- Population served is blank for many intakes, and the connection counts in the community-watershed summary repeat per system, so they are not added up as people.

**Method**
- Burned share = burned 240 m cells (NBAC 2023 to 2025 and M3 2026, all outlines, union) divided by the unit's grid area.
- Work units include open water and marine areas (for example Hudson Bay, the Arctic coast and the Great Lakes), so shares there are diluted.
- Each population centre is assigned the work unit containing its representative point.
- The NHN index carries no flow topology, so "downstream of" a burned watershed is not modelled; only the containing watershed is used.
- BC watersheds use exact vector overlay with the fire outlines.
- Files: `t6_workunit_burned_share.csv`, `t6_ssda_burned_share.csv`, `t6_popcentres_watershed.csv`, `t6_watershed_summary.csv`, `t6_bc_community_watersheds_burned.csv`, `t6_bc_community_watersheds_summary.csv`, `t6_bc_surface_intakes.csv`, `t6_bc_surface_intakes_summary.csv`.

**Not covered**
- Other provinces' intake locations were not searched beyond BC, apart from Ontario and Quebec source-protection layers, which were not checked.
- A watershed that burned is not the same as a water supply that was affected; treatment type is listed in the BC file.

## What failed or was limited
- **Official GHG managed-forest boundary:** not available as open GIS data. A georeferenced official image was used instead, validated at 229.2 Mha against the NIR's 230 Mha.
- **NFIS GHG-line WMS layer:** rendered no line.
- **Regrowth (NDVI) check:** skipped for disk and compute reasons.
- **SCANFI species maps:** full 30 m rasters (3 to 6 GB each) did not fit on disk, so the 480 m decimated overview was used.
- **Overwintering:** slash burning cannot be excluded without burn-permit data. Satellite detections match agency carry-over records poorly.
- **Prescribed burns:** the CNFDB record is incomplete for most provinces.
- **Watersheds:** no upstream routing. Intake data only for BC.
- **Run history:** a container restart and two out-of-memory kills interrupted runs. Every output was regenerated or validated after the restart: threads 1, 3, 4 and 5 were complete before it, thread 6 was completed before it (t6 national and t6b BC), and thread 2 was rerun to completion after it.
