# Rebuild 2026-10-21: new area layer, Parks Canada folded in, full hotspot archive, outline classes

One consolidated rebuild of the 2026 wildfire analysis. It uses only data and scripts already in this project. Pre-rebuild outputs (every top-level file of each affected analysis folder, plus logs and original scripts) are kept in `analysis/_before_rebuild/`. "Before" values below come from those files and "after" values come from the regenerated outputs.

## Scorecard: what moved

| Headline | Before | After |
|---|---|---|
| National ranking (NFD, 1990 to 2026) | 8th of 37 | 8th of 37 (unchanged) |
| Canada forest burned 2026 (mapped / scaled) | 1.04% / 0.88% | 1.04% / 0.88% (unchanged) |
| Canada forest burned 2023 to 2026 | 5.95% | 5.95% (unchanged) |
| Record-share areas, scaled basis (headline) | 6 | 9 (3 new Quebec zones) |
| Thunder Bay, 2026 vs 1991 to 2020 | 88 times | 88 times (unchanged) |
| Busiest 5 weeks, share of detections | 69.7% | 70.5% |
| Busiest 5 weeks, dates | Jun 22 to Jul 26 | Jun 22 to Jul 26 (unchanged) |
| People within 10 km of a 2026 outline | 199,805 | 158,441 |
| People within 50 km of a 2026 outline | 5,080,422 | 2,842,495 |
| On-reserve over-representation, 10 km | 12.0 times | 15.1 times |
| On-reserve over-representation, 50 km | 2.3 times | 4.0 times |
| Weather vs forest burned (median ratio, Spearman) | 0.67 (42 areas) | 0.71 (54 areas) |
| 2023 to 2026 run, actual / predicted | 14.1 times | 16.3 times |

- National numbers did not move, because the changes only redistribute area and do not change the totals. The exceptions are the hotspot timing and the people-near-fire numbers.
- Dropping 13 farm, grass and military-range burns cuts the 2026 "within 50 km" count by 44%. Most of the cut is near Calgary and Winnipeg. The 1,000 ha and agency-matched counts do not change.
- Splitting Quebec and Manitoba changes the area tables. Quebec's James Bay zones become some of the most-burned areas in Canada. Three Quebec zones join the scaled record list (Laforge-2, Caniapiscau, Fermont-Schefferville), and Manitoba Area 16 is a record on the mapped basis only.

## 1. What changed

**Change 1: new area layer.** The new layer is `data/geo/fma_v2.gpkg` (layer `fma_v2`), built by `data/geo/scripts/build_fma_v2.py`.
- It starts from `fma_all.gpkg`. The single Manitoba row (id 94) is replaced by `mb_qc_subareas/mb_fire_restriction_areas.gpkg`: 22 MWS areas plus the agricultural-south remainder, ids 1001 to 1023. The single Quebec row (id 92) is replaced by `qc_sopfeu_fire_danger_zones.gpkg`: 65 SOPFEU zones plus the far-north remainder, ids 2001 to 2066.
- The 47 Parks Canada rows are removed.
- The result has 186 rows with the same schema. All other ids are unchanged, and no old id is reused. Province areas match `fma_all` to 0.0000%.
- The crosswalk is `data/geo/fma_v2_crosswalk.csv` (284 rows). It lists 97 unchanged rows, the split of rows 92 and 94 with the share of old area, and each park against the v2 rows it overlaps.
- `fma_v2_attributes.csv` holds the attributes, and a manifest row was added.

**Change 2: Parks Canada.** There is no longer a separate Parks Canada layer in any area table.
- The official total per province is the agency total plus Parks Canada's 2026 official 124,872.1 ha. Parks Canada's total is allocated to provinces by the M3 outline area inside national parks (CLSS CLAB 2026-10-05 boundaries) in each province: NT 109,980 ha (88.1%), AB 13,659 ha (10.9%), MB 1,134 ha, BC 100 ha, others 0.
- Scaling factor = province official total / all M3 area in the province, parks included. The new factors are AB 1.033 (was 1.044), NT 0.822 (was 0.812) and MB 0.596 (was 0.595). The rest are unchanged.
- The official-scaled hectares still sum to 4,500,984.5 ha.
- **Footnote for every province figure: province totals include national parks inside them.**
- Rows that gained the park hectares: NWT South Slave (66,711 to 155,212 ha, Wood Buffalo NWT part), "AB outside mapped areas" (545 to 14,396 ha, Wood Buffalo AB part), North Slave (+10,025), Deh Cho (+7,527) and Sahtu (+3,912).

**Change 3: hotspots.** The timing analysis now uses the CWFIS WFS archive (`data/fire/raw/hotspots_wfs_2026/`, 294 daily files, 1,352,431 rows), cut at 2026-10-20 to match the old end date.
- The dedup rule is the same: one detection per sensor per 1 km cell per UTC day.
- The archive adds Sentinel-3 SLSTR as a third sensor, which the rule counts as its own sensor. A sensitivity without SLSTR is reported.

**Change 4: outline classes.**
- People step `00c_outline_class.py` attaches the class from `outline-check/outline_class_2026.geojson` to all 718 outlines.
- It drops 13 outlines (2,352 ha) from all 2026 distance analyses: 9 agricultural or grass burns and 4 military ranges, all with no agency-reported fire.
- Burned-area and forest statistics keep all 718.
- The class is added to `forest/fires_2026_simplified.geojson` (`outline_class`), `people/city_nearest_fire.csv` (`nearest_fire_outline_class`) and `city_search_table.json` (`outline_class`).

## 2. Before and after: every headline number

### Forest (analysis/forest)

| Number | Before | After |
|---|---|---|
| National rank, NFD 1990 to 2026 / NBAC 1972 to 2026 | 8th of 37 / 9th of 55 | same (ranking files byte-identical) |
| Canada forest burned 2026, mapped | 1.04% (3rd of 55) | 1.04% (3rd) |
| Same, scaled (x 0.849) | 0.88% (4th) | 0.88% (4th) |
| Canada forest burned 2023 to 2026 (union) | 5.95%, 20.78 M ha | 5.95%, 20.78 M ha |
| Distinct land burned 2023 to 2026, official-scaled | 35.79 M ha | 35.79 M ha |
| Thunder Bay share / 1991 to 2020 average / ratio | 12.8% / 0.15% / 88 times | same |
| Reburn share of the 2026 footprint | 15.8%, 713,125 ha | same |
| Areas in table | 146 (99 agency + 47 parks) | 186 |

Top areas by share of forest burned in 2026. The headline uses the scaled basis (share x province factor); the mapped share is in brackets.

| Rank | Before | After |
|---|---|---|
| 1 | Thunder Bay ON 11.2% (12.8%) | Thunder Bay ON 11.2% (12.8%) |
| 2 | North Slave NT 6.2% (7.7%) | Waskaganish QC 9.7% (10.5%) |
| 3 | Deh Cho NT 4.9% (6.1%) | North Slave NT 6.3% (7.7%) |
| 4 | Fort Frances ON 4.1% (4.7%) | LG-4 QC 5.0% (5.4%) |
| 5 | Wood Buffalo NP 3.6% (3.5%) | Deh Cho NT 5.0% (6.1%) |
| 6 | Cariboo BC 3.4% (3.2%) | Fort Frances ON 4.1% (4.7%) |
| 7 | Prince Albert SK 2.3% (2.6%) | Cariboo BC 3.4% (3.2%) |
| 8 | Denare Beach SK 2.3% (2.6%) | LG-3 QC 3.3% (3.6%) |

- Waskaganish, LG-4 and LG-3 burned more in 2023 (13.2%, 17.0%, 35.0%), so they are not records.
- Manitoba's top rows are Area 16 (3.9% mapped, 2.3% scaled), Area 18 (3.8% / 2.3%) and Area 17 (3.2% / 1.9%).
- Largest official-scaled hectares after the rebuild: North Slave 728,103; Deh Cho 601,794; Thunder Bay 433,453; Sahtu 317,796; Cariboo 247,140; Waskaganish 175,334; South Slave 155,212; Sioux Lookout 138,752; LG-4 118,008; Kamloops 116,778.

Areas whose 2026 share is the highest of 1972 to 2026 (`record_2026` mapped, `record_2026_if_scaled` scaled). **The headline uses the scaled list.**

| Basis | Before | After |
|---|---|---|
| Scaled (headline) | 6: Thunder Bay, Fort Frances, Sioux Lookout, North Slave, NL districts 22 and 20 | 9: the same 6 plus QC 59 Laforge-2 (3.3% vs 1.8% in 2023), 64 Caniapiscau (1.9% vs 1.1% in 2013), 65 Fermont-Schefferville (1.1% vs 0.7% in 2024) |
| Mapped only | 8: the 6 plus Deh Cho, NL 19c | 12: the 9 plus Deh Cho, NL 19c, MB Area 16 (3.9% vs 3.1% in 1981; scaled 2.3% is not a record) |
| Province, scaled | Ontario | Ontario (NL is a record on the mapped basis only, as before) |

### Timing (forest/05_hotspots.py)

| Number | Before (daily CSV file) | After (WFS archive) |
|---|---|---|
| Deduplicated detections in provinces | 191,455 | 321,515 (223,577 without SLSTR) |
| Busiest 5 weeks, national | Jun 22 to Jul 26, 69.7% | Jun 22 to Jul 26, 70.5% |
| Without SLSTR / VIIRS-I only / any sensor | n/a / 69.7% (Jul 6 to Aug 9) / 69.9% | 69.7% / 69.5% (Jun 22 to Jul 26) / 69.3% |
| Busiest week | Jul 13 to 19, 51,079 | Jul 13 to 19, 74,192 |
| Week of Jun 29 | 18,162 | 51,083 (the file's VIIRS gap) |
| July share of the year | 65% | 62% (199,040) |

- By province, the 5-week windows are unchanged for the large-fire provinces (NT's busiest single week moves to Jul 20). AB (see problem 7) and NS (now Jul 6 to Aug 9, 77 detections) change.
- The 5-week shares are: ON 91.8%, QC 94.7%, NL 96.9%, BC 83.2%, MB 87.6%, SK 80.8%, NT 74.9%.
- The VIIRS-only window now matches the national Jun 22 to Jul 26 window. Before the rebuild it fell two weeks later, an effect of the missing records.

### Weather (analysis/weather)

| Number | Before | After |
|---|---|---|
| Station and national results | 103 stations, pooled ratio 1.05 | unchanged |
| Areas / areas with a consistent station | 99 / 42 | 186 / 54 |
| Spearman, station median ratio of extreme days vs forest share burned | 0.67 (n 42) | 0.71 (n 54) |
| Spearman, station median anomaly (days) | 0.57 (n 42) | 0.44 (n 54) |
| Spearman, relaxed-rule anomaly | 0.56 (n 56) | 0.39 (n 85) |
| Spearman, grid ratio of means | 0.30 (n 96) | 0.38 (n 183) |
| Spearman, grid anomaly (days) | 0.01 | 0.00 |

All p-values are 0.001 or lower except the grid anomaly. The 12 new station areas are in southern Quebec and Manitoba, where the stations show near-normal or below-normal fire weather and little burning. That pulls the anomaly correlation down and raises the ratio correlation.

### Wildlife (fire management area summary only)

`wildlife/fma_2026.csv` now has 186 rows. Top shares of area burned (mapped):
- Before: Thunder Bay 12.17%, Deh Cho 4.62%, Fort Frances 3.81%, Denare Beach 2.79%, Cariboo 2.76%.
- After: Thunder Bay 12.17%, QC 50 Waskaganish 7.47%, Deh Cho 4.62%, QC 58 LG-4 4.19%, Fort Frances 3.81%, MB Area 16 3.44%, QC 59 Laforge-2 2.81%.

Caribou and protected-area results were not rerun.

### People (analysis/people), 2026

| Number | Before | After |
|---|---|---|
| People inside an outline | 4,843 | 4,843 |
| Within 10 km | 199,805 (0.54%) | 158,441 (0.43%) |
| Within 25 km | 1,097,836 | 806,474 |
| Within 50 km | 5,080,422 (13.73%) | 2,842,495 (7.68%) |
| Within 10 / 50 km, fires of 1,000 ha or more | 118,631 / 1,046,523 | unchanged |
| Within 10 / 50 km, agency-matched only | 142,628 / 1,273,691 | unchanged |
| Population centres with an outline within 10 / 25 / 50 km | 26 / 76 / 171 | 17 / 52 / 138 |
| Reserves within 10 / 50 km | 330 / 1,409 | 328 / 1,313 |
| First Nation communities within 10 / 50 km | 38 / 195 | 38 / 184 |
| On-reserve share of people within 10 km (population share 0.92%) | 11.04%, 12.0 times | 13.93%, 15.1 times |
| On-reserve share within 50 km | 2.13%, 2.3 times | 3.68%, 4.0 times |
| On-reserve, fires of 1,000 ha or more, 10 / 50 km | 9.68% / 5.85% | unchanged |

- By province, within 50 km: AB 1,293,003 to 105,402 (Calgary) and MB 1,132,705 to 175,859 (Winnipeg), with smaller drops in ON, SK and QC. BC, NB, NL, NS and NT are unchanged.
- By area, among fires of 1,000 ha or more, Kamloops is still first (85,502 within 10 km, 446,540 within 50 km). New Brunswick is second (266,103). The former "Quebec (whole province)" row (47,881) is now mostly QC 05 Val d'Or-Senneterre (32,264).
- The 21 Parks Canada unit rows are gone.

Nearest 2026 outline to the 30 largest population centres (edge distance, km; the class is the class of the nearest outline after the rebuild):

| City | Before | After | Class |
|---|---|---|---|
| Toronto | 257.0 | 306.0 | unclear |
| Montréal | 118.7 | 118.7 | unclear |
| Vancouver | 67.2 | 67.2 | wildfire |
| Calgary | 27.0 | 98.0 | unclear (agency-matched) |
| Edmonton | 167.1 | 193.9 | unclear (agency-matched) |
| Ottawa - Gatineau | 20.4 | 20.4 | unclear |
| Winnipeg | 20.5 | 64.5 | wildfire (unreported) |
| Québec | 365.1 | 365.1 | unclear |
| Hamilton | 338.7 | 379.7 | unclear |
| Kitchener | 359.7 | 421.1 | unclear |
| London | 437.9 | 501.7 | unclear |
| Victoria | 147.4 | 147.4 | wildfire |
| Halifax | 63.1 | 63.1 | wildfire |
| Oshawa | 247.3 | 287.7 | unclear |
| Windsor | 581.9 | 610.8 | wildfire |
| Saskatoon | 35.4 | 35.4 | unclear |
| St. Catharines - Niagara Falls | 331.9 | 350.7 | unclear |
| Regina | 100.8 | 100.8 | unclear |
| St. John's | 667.7 | 667.7 | unclear |
| Kelowna | 11.2 | 11.2 | wildfire |
| Barrie | 245.4 | 334.2 | unclear |
| Sherbrooke | 271.0 | 271.0 | unclear |
| Guelph | 344.8 | 408.3 | unclear |
| Kanata | 41.2 | 41.2 | unclear |
| Abbotsford | 80.0 | 80.0 | wildfire |
| Trois-Rivières | 257.6 | 257.6 | unclear |
| Kingston | 108.1 | 108.1 | unclear |
| Milton | 330.2 | 383.3 | unclear |
| Moncton | 107.9 | 107.9 | military range (agency-listed CFB Gagetown fire, kept) |
| White Rock | 94.1 | 94.1 | wildfire |

- The southern Ontario cities moved because their old nearest outline was the Petawawa military-range outline.
- Kelowna (11.2 km) is still the closest of the 30.
- The "nearest agency-matched fire" column is unchanged.

### Climate (analysis/climate, AREA_FILE=fma_v2, output in `climate/work/areas_fcd292dde04d/`)

The main `analysis/climate/` files (fma_all) were left as they were.

| Number | fma_all (before) | fma_v2 (after) |
|---|---|---|
| Areas in burn-correlation sample | 74 (Quebec 1) | 154 (Quebec 61, Prairies 44) |
| Within-area r, spring rain | -0.25 | -0.25 |
| Within-area r, 12-month precipitation | -0.26 | -0.21 |
| Within-area r, spring temperature | +0.23 | +0.18 |
| Within-area r, previous-summer / previous-fall rain | -0.12 / -0.11 | -0.07 / -0.09 |
| Within-area r, PDO MAM | -0.15 (p 0.02) | -0.11 (p 0.06) |
| Tests with p < 0.05, burn family | 65 of 294 | 76 of 294 |
| Quebec 2026: previous-fall rain | 70%, rank 2 (1 area) | median 70%, 36 of 65 zones top-5 driest |

The direction of every national relationship is unchanged; the sizes shrink slightly.

### Cause model (analysis/cause, AREA_FILE=fma_v2; main outputs in `analysis/cause/` overwritten, before copies in `_before_rebuild/cause/`)

| Number | Before (93 areas) | After (177 areas) |
|---|---|---|
| 2026 held out, Spearman actual vs expected (P_all) | 0.771 | 0.769 |
| 2026 held out, R2 | 0.518 | 0.568 |
| 2026 forest-weighted actual / expected (P_all) | 0.89% / 0.51% (1.7 times) | 0.89% / 0.29% (3.1 times) |
| Station panel (P_stn), Spearman, n | 0.719, 42 | 0.751, 55 |
| 2023 to 2026 run, actual / predicted (P_all) | 5.85% / 0.41%, 14.1 times (5.4 x calibration) | 5.85% / 0.36%, 16.3 times (5.2 x calibration) |
| Run without ignition block | 11.8 times | 15.4 times |
| Run, area average only | 28.6 times | 33.6 times |
| 2026 alone, LOYO-trained (P_all) | 9.1 times | 9.8 times |
| Largest 2026 surprises | Prince Albert 51, Thunder Bay 42, Fort Frances 26 | MB Area 16 80, Prince Albert 66, Thunder Bay 53, Fort Frances 41, Waskaganish 22 |

- The climate block joined 21 columns from the v2 climate panel, as before.
- The burn-history check against forest matches to 5.8e-14.
- National cause tables are unchanged.
- The "0.36% expected vs 0.89%" in `cause/results.md` was computed differently. The forest-weighted figures above use the same method for before and after.

### Economy (area summary only)

`economy/scripts/07c_timber_carbon_by_area_v2.py` writes `timber_biomass_carbon_by_area_v2.csv` (Canada, province and 94 v2 areas with 2026 burns; no national park level). The original script and output are untouched, because another process was working in `analysis/economy` during this rebuild.
- National mapped totals are identical.
- National 2026 scaled totals differ by at most 0.18% (biomass -0.18%, merchantable volume -0.15%). This comes only from moving the Parks Canada hectares into provincial factors.
- The 2023 to 2025 figures are unchanged.
- No other economy step summarises by fire management area.

## 3. Problems and caveats

1. **The "13" exclusion is the unmatched subset.** The pre-registered rule puts 16 of 718 outlines in the agricultural/grass or military classes. Three are agency-reported fires and were kept: two CFB Gagetown fires (NB) and one SK fire on cropland. If they were also dropped, Moncton's nearest outline (107.9 km, Gagetown) would move. This choice is recorded in `00c_outline_class.py` and `exclude_from_distance`.
2. **People counts are sensitive to a few small burns.** 44% of the old 50 km count came from 13 outlines (2,352 ha). The "unclear" class (197 outlines) is kept. This class covers the outlines nearest Ottawa (20.4 km), Saskatoon (35.4 km) and Kanata (41.2 km). The 1,000 ha columns stay the like-for-like comparison.
3. **M3 over-maps Manitoba, and the split is uneven.** Manitoba's own perimeters (within 4% of its official total) put 23% of its burn in Area 18. M3 puts 40% there, a difference of 45,015 ha. With 23 rows, Manitoba area hectares now depend on M3 shapes. MB Area 16's mapped record does not survive scaling.
4. **The Quebec split has only point-based validation.** SOPFEU fire points put 6.0% of Quebec's burn in Laforge-2, against 10.4% by M3 (+33,751 ha). Laforge-2 is a scaled record, so that claim rests on M3 shapes. LG-4 goes the other way (20.1% by points, 15.7% by M3).
5. **Quebec and Manitoba zone edges are generalised web-map lines** (good to about 1 to 5 km). The 20 m simplification changed one area by 0.32%, and the others by less.
6. **Parks Canada allocation follows mapped outline area,** because Parks Canada does not publish per-park 2026 hectares here. NWT points and the Alberta perimeters exclude park fires, so in `validation_split_by_area.csv` South Slave and "AB outside mapped areas" now show M3 shares above the agency-data shares.
7. **The Alberta hotspot peak is now industrial.** With the WFS archive, Alberta's busiest 5 weeks fall in Jan 12 to Feb 15 (32% of its detections), from persistent winter heat sources. No filter for non-fire heat is applied, as before.
8. **The hotspot counts are not comparable with the old ones.** SLSTR adds about 98,000 detections. Without SLSTR the archive still adds 17% over the old file (223,577 against 191,455), mostly in the Jun 29 week.
9. **Climate and cause were run in a separate area cache.**
   - Climate 05 was too slow when it simplified the full-detail fma_v2 rows, and it was stopped. It was patched to reuse `weather/work/fma_simple.gpkg`, which is now built from fma_v2, and the forest `fma_v2_id.npy` grid. This is the same path the default fma_all run takes.
   - Cause 02 also reuses the forest grid, and cause 09 reads the climate panel from the matching `climate/work/areas_<hash>/`.
   - Running cause again without AREA_FILE would mix fma_all areas with the new v2 scaling file (no PC row). Run it with `AREA_FILE=.../data/geo/fma_v2.gpkg`.
10. **Other analyses use the fma_all grids,** so the fma_all grids (`forest/work/fma_id.npy`, `park_id.npy`) were kept. The economy `01_cells.py` reads `sf["PC"]`, which no longer exists in `forest/scaling_factors_by_province.csv`. Rerunning it needs the same change as `07c`. It was not edited, because another process was working in that folder.
11. **The results.md texts were not rewritten.** The `results.md` in forest, weather, wildlife and people have a rebuild notice at the top. Their body text still quotes pre-rebuild numbers where they differ; this file is the reference.

## 4. Files

- **Data:** `data/geo/fma_v2.gpkg`, `fma_v2_attributes.csv`, `fma_v2_crosswalk.csv`, `scripts/build_fma_v2.py`, manifest row.
- **Forest scripts:**
  - Changed: `common.py` (FMA = fma_v2, WFS path), `02b`, `02`, `04` (rewritten), `05`, `06` (adds Manitoba and Quebec split checks), `08`.
  - New work files: `fma_v2_simplified.gpkg`, `fma_v2_id.npy` (uint16, 906 MB, shared with climate and cause), `m3_fma_v2_overlay.gpkg`.
- **Weather:** `00_simplify_fma.py` (fma_v2), `05_join_forest.py` (deterministic file choice).
- **Wildlife:** `01_prep.py` (step `fma_v2`), `07_fma.py` (layer argument).
- **People:** new `00c_outline_class.py`; changed `01`, `02`, `02y`, `06`, `07`.
- **Climate:** `05_areas_outcome.py` (reuse paths).
- **Cause:** `02_areas.py` (grid reuse), `09_model.py` (climate panel for the same area file).
- **Economy:** new `07c_timber_carbon_by_area_v2.py`.
