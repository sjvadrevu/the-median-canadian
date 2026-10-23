# Canada 2026 wildfire season: forest analysis results

> **Rebuild 2026-10-21.** The CSV and GeoJSON files in this folder were regenerated on the new area layer `data/geo/fma_v2.gpkg` (186 rows: Manitoba as 22 MWS fire and travel restriction areas + remainder, Quebec as 65 SOPFEU fire danger zones + remainder, no separate Parks Canada layer), with Parks Canada hectares folded into provinces (province totals include national parks inside them) and hotspots from the CWFIS WFS archive. Numbers in the text below are the pre-rebuild values where they differ; the current values and a before/after table are in `../REBUILD.md`. Pre-rebuild outputs are kept in `../_before_rebuild/forest/`.

Original analysis of official raw data downloaded 2026-10-20. All 2026 hectare figures are scaled to the official agency totals (CWFIF/CIFFC reported-fire-stats, as of 2026-10-20: 4,500,984.6 ha, 13 agencies including Parks Canada 124,872.1 ha). Shares of forest burned are ratios of mapped quantities and are not scaled. Folder: this file's folder (`analysis/forest/`). Scripts in `scripts/`, run in order 01, 02b, 02, 03 (then `03 2026`), 04, 05, 06, 07, 08.

## 1. Ranking of the 2026 total

Files: `ranking_canada.csv`, `ranking_province.csv`, `nbac_totals_by_year_admin.csv`. Script: `01_rankings.py`. Inputs: `data/smoke-cost/fire_area_count_by_agency_year.csv` (NFD 1990 to 2025, 12 provinces and territories, no Parks Canada series; 2026 CWFIF YTD), NBAC summary workbook `NBAC_summarystats_1972_to_2025_20260513.xlsx` (sheet sumstats_admin_name, adjusted hectares).

- Against the National Forestry Database, 2026 ranks 8th of 37 years (1990 to 2026). Like-for-like (2026 without Parks Canada, 4,376,112 ha), the larger years are 2023, 2025, 1995, 1994, 2024, 1998 and 2014. Including Parks Canada (4,500,985 ha) the rank is also 8th.
- The 2026 total (excluding Parks Canada) is 1.78 times the NFD 1991 to 2020 average of 2,465,091 ha and 0.95 times the 2016 to 2025 average of 4,630,258 ha.
- Against NBAC annual totals (all administrative units, including Parks Canada and DND), the official 2026 total ranks 9th of 55 years (1972 to 2026). Larger years: 2023, 2025, 1989, 1995, 1981, 1994, 2024, 1980. It is 2.09 times the NBAC 1991 to 2020 average (2,150,988 ha) and 1.12 times the 2016 to 2025 average (4,018,338 ha). NBAC is a satellite-mapped product and runs lower than agency estimates (2023: NBAC 14.80 M ha, NFD 17.61 M ha), so the NFD comparison is the like-for-like one.

By province (2026 official vs NFD 1990 to 2025; rank of 37):

| Prov | 2026 ha | NFD rank | x 1991-2020 | x 2016-2025 |
|---|---|---|---|---|
| ON | 748,717 | 2 (after 2021) | 4.43 | 2.80 |
| NL | 96,301 | 3 (after 1994, 2000) | 4.41 | 7.14 |
| QC | 753,935 | 5 | 2.77 | 1.55 |
| NT | 1,694,212 | 6 | 2.73 | 1.82 |
| BC | 479,325 | 7 | 2.81 | 0.58 |
| NS | 1,525 | 8 | 2.10 | 0.38 |
| MB | 264,268 | 10 | 0.98 | 0.58 |
| NB | 498 | 18 | 0.61 | 0.63 |
| SK | 312,281 | 18 | 0.63 | 0.39 |
| PE | 4 | 30 | 0.11 | 0.34 |
| AB | 17,780 | 32 | 0.07 | 0.03 |
| YT | 7,267 | 35 | 0.04 | 0.04 |

Against NBAC provincial totals (1972 to 2026, rank of 55), Ontario's 2026 official total is the largest on record and NWT ranks 5th; Parks Canada (NBAC PC series) ranks 10th. Full table in `ranking_province.csv`.

## 2. Fire management areas: official-scaled hectares and share of forest burned

Files: `fma_2026_table.csv` (146 rows: 99 agency rows that partition Canada, plus 47 overlapping Parks Canada rows, column `layer`), `scaling_factors_by_province.csv`, `province_forest_share_2026.csv`, `fma_forest_share_by_year_1972_2025.csv`, `fma_2026.geojson`. Script: `04_fma_forest.py`, `08_fma_geojson.py`.

- The official-scaled hectares across all 146 rows sum to 4,500,984.5 ha, equal to the official total. Nunavut is the only area without an official total (18,715 ha mapped by M3, not scaled, not in the sum).
- Scaling factors (official total / M3 outline area outside national parks): BC 1.084, AB 1.044, SK 0.867, MB 0.595, ON 0.873, QC 0.925, NB 0.070, NS 3.428, NL 0.794, YT 0.979, NT 0.812, Parks Canada 1.017 (official 124,872 ha / 122,743 ha mapped inside national parks). PE has no mapped outline (official 3.8 ha assigned to its single row).
- Largest areas by official-scaled hectares: Quebec (whole province) 753,935 ha; NWT North Slave 718,078 ha; NWT Deh Cho 594,267 ha; Ontario Thunder Bay 433,453 ha; NWT Sahtu 313,884 ha; Manitoba (whole province) 264,268 ha; BC Cariboo 247,143 ha; Ontario Sioux Lookout 138,752 ha; Wood Buffalo National Park 122,158 ha; BC Kamloops 116,779 ha.
- Highest share of forest burned in 2026: Ontario Thunder Bay 12.8% of its forest (1991 to 2020 average 0.15%, 88 times); NWT North Slave 7.7% (average 0.41%); NWT Deh Cho 6.1% (average 0.33%); Ontario Fort Frances 4.7% (average 0.06%); Wood Buffalo National Park 3.5% (average 0.56%); BC Cariboo 3.2% (average 0.37%).
- Areas whose 2026 share is the highest of 1972 to 2026 (mapped basis): Ontario Thunder Bay (12.8% vs previous high 3.0% in 1980), Fort Frances (4.7% vs 2.7% in 2021), Sioux Lookout (1.7% vs 1.5% in 1976); NWT North Slave (7.7% vs 5.1% in 2023), Deh Cho (6.1% vs 5.0% in 1995); NL Forest Management Districts 22 (1.13% vs 0.87% in 2024), 20 (0.05% vs 0.03% in 2016) and 19c (0.16% vs 0.14% in 2023).
- Because M3 outlines exceed official totals in most provinces, the same test was repeated with the 2026 share multiplied by the province scaling factor (`forest_share_2026_scaled_sensitivity`). Six of the eight remain records: Thunder Bay, Fort Frances, Sioux Lookout, North Slave, NL districts 22 and 20. Deh Cho (4.9% vs 5.0%) and NL district 19c drop out.
- By province (whole province polygon, agency layer): Ontario 1.25% of its forest burned (previous high 0.88%) and Newfoundland and Labrador 0.38% (previous high 0.33%) are the highest since 1972 on the mapped basis; scaled by the factor, Ontario stays a record (1.09%) and NL does not (0.30%). NWT 3.51% (high 4.73% in 2014), Manitoba 1.28%, Saskatchewan 1.15%, Quebec 0.78%, BC 0.59%.

## 3. Canada total

Files: `canada_totals.csv`, `canada_forest_share_by_year.csv`. Script: `04_fma_forest.py`.

- Canada's forest (Land Cover 2020 classes 1, 2, 5, 6, inside StatCan 2021 province and territory polygons, equal-area) is 349.4 M ha.
- Forest inside the 2026 M3 outlines is 3.64 M ha, 1.04% of Canada's forest. On the same basis this is the 3rd highest year of 1972 to 2026, after 2023 (2.61%) and 2025 (1.39%); the 1991 to 2020 average is 0.17%. Scaled by the national ratio of official to mapped area (0.849), the 2026 share is 0.88%, which would rank 4th (2024 was 0.93%).
- Cumulative 2023 to 2026 (union of NBAC 2023, 2024, 2025 and M3 2026 footprints, overlaps counted once): 20.78 M ha of forest, 5.95% of Canada's forest. The sum of the four annual forest figures is 20.85 M ha, so overlap between years removes 70,000 ha of forest.
- Cumulative area, all land: the union of mapped footprints is 32.22 M ha against a sum of annual mapped footprints of 32.32 M ha. Applying that ratio to the sum of official totals (NFD 2023 to 2025 plus 2026 official, 35.91 M ha) gives 35.79 M ha of distinct land burned in 2023 to 2026.

## 4. Reburns

Files: `reburn_2026_by_province.csv`, `reburn_2026_by_fma.csv`, `burned_twice_2023_2026_by_province.csv`, `reburn_2026.geojson`. Scripts: `04_fma_forest.py`, `07_reburn_geojson.py`.

- Of the 2026 footprint, 15.8% had burned at least once in 1972 to 2025 (NBAC). By time since the most recent burn: under 10 years (2017 to 2025) 2.4%, 10 to 30 years (1996 to 2016) 5.1%, over 30 years (1972 to 1995) 8.3%. Applied to the official total: 107,189 ha, 231,323 ha and 374,613 ha (713,125 ha in all); 3,787,860 ha had no recorded burn since 1972.
- By jurisdiction (share of 2026 footprint that is a reburn, official-scaled reburn hectares): NWT 13.8%, 233,266 ha; Saskatchewan 55.3%, 172,825 ha; Ontario 12.2%, 91,314 ha; Parks Canada 53.4%, 66,657 ha; Manitoba 17.1%, 45,181 ha; Quebec 5.7%, 43,264 ha; BC 7.6%, 36,221 ha; NL 10.6%, 10,234 ha; Alberta 29.6%, 5,271 ha.
- Share burned within the previous 10 years is highest in New Brunswick (50.9%, on a very small and over-mapped footprint, see section 6), Saskatchewan (9.5%), Parks Canada (8.6%) and BC (5.8%).
- Largest reburn areas by fire management area (official-scaled): North Slave 100,265 ha (14.0% of its 2026 footprint), Deh Cho 91,425 ha (15.4%), Wood Buffalo National Park 66,527 ha (54.5%), SK La Ronge 60,004 ha (66.6%), SK Stony Rapids 56,176 ha (50.1%), Thunder Bay 54,484 ha (12.6%).
- Within 2023 to 2026, 102,007 ha (mapped) burned in two or more of the four years, 0.32% of the 32.22 M ha union. Largest: Saskatchewan 32,173 ha, Alberta 12,219 ha (province polygon, including national parks; Alberta's 2026 agency total is 17,780 ha), BC 15,589 ha, NWT 13,598 ha, Ontario 10,084 ha.

## 5. Timing (satellite hotspots)

Files: `weekly_hotspots.csv`, `hotspot_peak5.csv`, `hotspot_dedup_summary.csv`. Script: `05_hotspots.py`. Input: `cwfis_hotspots_2026_canada.csv.gz` (751,301 rows, 2026-01-13 to 2026-10-20).

- Deduplication rule: one detection per sensor (VIIRS-I or MODIS) per 1 km x 1 km cell of an ESRI:102001 grid per UTC day. This leaves 191,650 detections (191,455 inside province polygons). Sensitivity: VIIRS-I only 130,807; any sensor, one per cell-day 154,717.
- Nationally, the busiest 5 consecutive weeks were 2026-06-22 to 2026-07-26, with 133,350 detections, 69.7% of the season's total. The busiest single week was 2026-07-13 to 2026-07-19 (51,079). The 5-week share is 69.7% to 69.9% under all three deduplication rules (VIIRS-only peak window shifts two weeks later, 2026-07-06 to 2026-08-09).
- By month: July 124,814 detections (65% of the year), August 42,901, June 16,887.
- Busiest 5 weeks by province: ON 2026-07-06 to 08-09 (94.1% of its detections), QC 06-15 to 07-19 (94.7%), NL 06-22 to 07-26 (94.8%), BC 07-20 to 08-23 (85.7%), MB 06-22 to 07-26 (83.7%), SK 06-22 to 07-26 (78.2%), NT 06-22 to 07-26 (73.4%), YT 07-20 to 08-23 (70.4%).

## 6. Validation of the split

Files: `scaling_factors_by_province.csv`, `validation_province.csv`, `validation_split_by_area.csv`, `work/burn_rasterize_log.csv`. Script: `06_validation.py`.

| Prov | Official ha | M3 mapped ha | Own data ha | Split quality |
|---|---|---|---|---|
| BC | 479,325 | 442,388 | 433,319 (perimeters) | Good: fire-centre shares within 1.2 points |
| ON | 748,717 | 857,610 | 837,564 (perimeters) | Good: largest gap Thunder Bay 11,678 ha |
| AB | 17,780 | 30,450 | 26,689 (perimeters) | Fair: Lac La Biche 2,170 ha (prov.) vs 281 ha (M3) |
| MB | 264,268 | 445,060 | 254,020 (perimeters) | Whole province only; M3 maps 68% more than official |
| SK | 312,281 | 360,182 | none | M3 only |
| QC | 753,935 | 814,858 | 737,653 (points) | Whole province only; points only |
| NT | 1,694,212 | 2,194,905 | 1,694,212 (points) | Weak: region split differs by up to 184,464 ha |
| NL | 96,301 | 121,264 | none | Districts are forestry, not fire, units |
| NB | 498 | 7,126 | none | Weak: factor 0.07 |
| NS | 1,525 | 445 | none | Weak: factor 3.43 |
| YT | 7,267 | 7,420 | none | M3 only |
| PE | 4 | 0 | none | No mapped fire |
| NU | none | 18,715 | none | No official total |
| PC | 124,872 | 122,743 | none | Good total match (factor 1.02) |

- Nationally, M3 outlines total 5,303,030 ha equal-area (2,608 ha offshore), 17.8% above the official 4,500,985 ha.
- NWT: allocating the official total by the agency's own fire points (fire size at point of origin) instead of M3 outlines would give North Slave 902,543 ha instead of 718,078 ha and Deh Cho 431,399 ha instead of 594,267 ha. The point method puts each whole fire in the region where it started, so neither method is exact.
- Alberta: 13,421 ha of M3 outline area in Alberta lies inside national parks (Wood Buffalo). Removing it gives a factor of 1.044; without removal it would be 0.584.
- Manitoba's own perimeters are within 4% of its official total, while M3 is 68% above. Manitoba hectares are unaffected (single area), but its 2026 forest share from M3 (1.28%) is likely overstated; scaled, 0.76%.

## Methods and caveats

- Areas: all vector areas in ESRI:102001. Raster work uses the Land Cover 2020 forest-count grid (240 m, EPSG:3979, Lambert conformal). Cell counts are converted to true area with the projection's areal scale factor (0.94 to 1.17, evaluated every 25 cells); rasterised burn areas match ESRI:102001 vector areas within 0.2% for every year 1972 to 2026 (`work/burn_rasterize_log.csv`).
- Rasterisation: a 240 m cell is in a polygon if its centre is inside it. NBAC and M3 coordinates (EPSG:3978 and NBAC's equivalent Lambert) are used directly on the EPSG:3979 grid (same projection parameters; NAD83 vs NAD83(CSRS) offset under 2 m).
- Forest: classes 1, 2, 5, 6 (needleleaf, taiga needleleaf, broadleaf, mixed). Shrubland and wetland are excluded. The 2020 map shows post-fire conditions, so land burned before 2020 and not yet regrown to forest is not counted as forest. This lowers historical (pre-2020) forest shares and is one reason 2026 can rank high against older years.
- 2026 footprint: CWFIS FireM3 perimeters (buffered hotspot outlines, include unburned islands). History: NBAC polygons (Landsat-mapped, also include islands; POLY_HA geometry used). The two products differ; the scaled sensitivity columns bracket the effect.
- Fire management areas: `fma_all.gpkg` simplified to 20 m part by part (max area change 0.69%, Mingan Archipelago; all others smaller) so overlays fit in memory; outputs for the site simplified further (1,000 m) for display only.
- Parks Canada: treated as a separate agency with its own total. Provincial factors use M3 area outside national parks. Forest shares for agency rows cover the whole area polygon, including any national park inside it.
- Average share 1991 to 2020 is the mean of the 30 annual shares (NBAC). "Record" means 2026 share above every year 1972 to 2025.
- Official series: NFD 1990 to 2025 (updated 2026-08-10, 12 jurisdictions, no Parks Canada). 2026 is preliminary situation-report data and will be revised.
- Hotspots: no filter for non-fire heat sources. January detections (789, mostly Alberta, week of 2026-01-12) are likely industrial and fall outside the peak window. rep_date is used as UTC.
- Not done: SOPFEU zones (Quebec) and Manitoba, NB, NS fire regions have no public boundaries, so these provinces have one row each.
