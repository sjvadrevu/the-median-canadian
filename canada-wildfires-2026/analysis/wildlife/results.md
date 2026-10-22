# Wildfire 2026: caribou ranges, protected areas and forest habitat

> **Rebuild 2026-10-21.** `fma_2026.csv` (section 5) was regenerated on `data/geo/fma_v2.gpkg` (186 areas, no Parks Canada rows). Caribou and protected-area results do not depend on the area layer and were not rerun. See `../REBUILD.md`; pre-rebuild file in `../_before_rebuild/wildlife/`.

Original analysis of official raw data, run 2026-10-21. 2026 fire extent = CWFIS FireM3 outlines dated 2026-10-20. Past fire = NRCan National Burned Area Composite (NBAC) 1987 to 2025. All areas computed in Canada Albers Equal Area (ESRI:102001).

Read this first: the 2026 outlines are hotspot-derived and run about 18% above official totals nationally (5,303,030 mapped ha vs NRCan 4,500,985 ha). Every 2026 share below is a share of the mapped outline, so 2026 shares are likely overstated by roughly that amount on average, and by more in some provinces (see caveats). Hectares and km2 for 2026 are labelled "mapped" and are not official area burned.

## 1. Boreal caribou ranges (ECCC 2012 recovery strategy, 51 ranges)

- Brightsand (ON4) had the largest 2026 share of any range: 16.67% of its 22,209 km2 range lies inside 2026 outlines (3,703 mapped km2).
- The next highest 2026 shares were Northwest Territories (NT1) 3.24%, Nipigon (ON5) 2.49%, Wapisu (MB8) 2.27%, Val d'Or (QC1) 1.69%, Saskatchewan Boreal Shield (SK2) 1.32%, Caribou Mountains (AB4) 1.22%, Kississing (MB2) 1.18%, Quebec (QC6) 1.16% and Red Wine Mountain (NL2) 1.04%.
- NT1 had the largest mapped area inside 2026 outlines of any range: 14,295 mapped km2, followed by QC6 with 7,241 mapped km2 and ON4 with 3,703 mapped km2.
- 26 of the 51 ranges intersect a 2026 outline; the other 25 have none, including all 5 BC ranges and 9 of the 12 Alberta ranges.
- Across the union of all 51 ranges (2,403,854 km2), 1.36% lies inside 2026 outlines (32,779 mapped km2).
- Fire in the last 40 years (union of NBAC 1987 to 2025 plus 2026 outlines, reburns counted once) now covers 24.43% of the combined range area, up 1.19 points from 23.24% for 1987 to 2025 alone.
- The largest 40-year increase caused by 2026 was in Brightsand: from 10.56% to 25.38% (+14.82 points). Next were NT1 +2.90 points (28.08% to 30.98%), Nipigon +2.44 points (6.69% to 9.13%), Wapisu +2.26 points and Val d'Or +1.69 points. No other range rose by more than 1.2 points.
- 87.15% of the 2026 outline area inside the ranges fell on ground with no NBAC fire since 1987, so most of the 2026 burn added new disturbance rather than reburning recent fire. Exceptions with heavy reburning: SK1 (only 23.85% of its 2026 burn was on unburned ground) and SK2 (43.16%).
- 14 ranges now have fire-only disturbance above 35% of the range: Calendar (BC2) 75.84%, Richardson (AB8) 62.71%, Saskatchewan Boreal Shield (SK2) 56.06%, Owl-Flinstone (MB13) 52.35%, Snake-Sahtahneh (BC3) 52.18%, Bistcho (AB2) 47.59%, Caribou Mountains (AB4) 45.78%, Kississing (MB2) 40.96%, Atikaki-Bernes (MB12) 39.64%, Slave Lake (AB12) 39.27%, Naosap (MB3) 38.24%, Nipisi (AB11) 37.30%, Saskatchewan Boreal Plain (SK1) 35.80% and Maxhamish (BC1) 35.08%.
- All 14 were already above 35% from 1987 to 2025 fire alone; 2026 did not push any new range over 35%. The closest are Manitoba North (MB9) at 34.00% (up from 33.15%) and Berens (ON2) at 33.57%.
- These fire-only figures are a lower bound of total disturbance. The federal 65% undisturbed threshold counts fire under 40 years plus human disturbance buffered by 500 m; we have no human disturbance layer, so true total disturbance is higher in every range.

## 2. Provincial caribou layers

Quebec (15 forest-ecotype local populations, 2022 layer):
- Nottaway had the highest 2026 share: 5.61% (2,415 mapped km2), raising its 40-year fire share from 16.18% to 21.54% (+5.37 points).
- Next were Détour 2.81% (+2.74 points, to 7.94%) and Caniapiscau 2.31% (+2.24 points, to 14.71%). No other Quebec population exceeded 0.7%.
- Secteur Baie-James is the only Quebec population with fire-only disturbance above 35%: 47.19% (46.59% before 2026).
- Across the union of all 15 populations (660,445 km2), 0.94% lies inside 2026 outlines and the 40-year fire share rose from 16.94% to 17.83%.
- Several Quebec populations extend outside Quebec (Détour into Ontario, Lac Joseph and Joir River into Labrador), and populations overlap; areas are full polygon areas, not the Quebec-only Sup_KM2 attribute.

Saskatchewan (5 range units):
- SK1 (176,833 km2) had 1.29% inside 2026 outlines; its 40-year fire share rose from 55.44% to 56.00%.
- SK2 Central 0.37% and SK2 East 0.31%; SK2 West Northern and SK2 West Southern had none.
- Four of the five units exceed 35% fire-only disturbance: SK2 West Northern 66.72%, SK1 56.00%, SK2 West Southern 42.31%, SK2 Central 40.83%. Only SK2 East (7.29%) is below.
- Across the union (286,549 km2), the 40-year fire share is 48.56% (48.19% before 2026).

## 3. Protected and conserved areas (CPCAD 2025, terrestrial, all statuses, overlaps dissolved)

- Nationally, 0.84% of protected and conserved land lies inside 2026 outlines: 11,744 mapped km2 of 1,401,921 km2.
- By province (CPCAD location field): Ontario 2.77% (3,339 mapped km2), Northwest Territories 1.89% (4,473), Quebec 0.74% (1,893), Manitoba 0.64% (463), British Columbia 0.50% (945), Saskatchewan 0.48% (305), Alberta 0.26% (269), Newfoundland and Labrador 0.16% (45), Yukon 0.01%, Nunavut, Nova Scotia, New Brunswick and PEI 0.00%.
- Our dissolved protected area per province matches the official CPCAD 2025 statistics within 0.1% everywhere except Alberta (104,149 vs 103,055 km2, +1.1%).
- 128 protected or conserved areas (records dissolved by parent ID) intersect a 2026 outline.
- Largest affected by mapped area: Wabakimi Provincial Park, ON (2,054 mapped km2, 23.01% of the park); Wood Buffalo National Park (1,201, 2.64%); Edéhzhíe Protected Area, NT (949, 6.67%); Quetico Provincial Park, ON (851, 18.01%); Tłı̨chǫ Wenek'e Cultural Heritage Zone, NT (783, 4.69%); Johnny Hoe River conservation zone, NT (690, 16.67%); proposed collines de Muskuchii Biodiversity Reserve, QC (523, 65.27%); Dè Wexèlahodı ha-le, NT (325, 32.56%); Caribous-de-Nottaway reserve, QC (315, 13.30%); BC Old Growth Management Areas OECM (289, 2.00%).
- Among sizeable areas, the highest shares were the proposed ruisseau Niquet Biodiversity Reserve, QC (97.40% of 165 km2), Muskuchii (65.27% of 801 km2) and Marble Range Park, BC (58.89% of 192 km2).
- National parks: five of 47 intersect a 2026 outline. Wood Buffalo 2.64% (1,201 mapped km2), Mount Revelstoke 0.37% (0.98), Wapusk 0.10% (11), Thaidene Nene 0.09% (13), Nahanni under 0.01% (1.5). The other 42 have none.

## 4. Forest habitat (Land Cover of Canada 2020 forest classes)

- Inside the 51 caribou ranges (union), 22,948 mapped km2 of 2020 forest lies inside 2026 outlines, 1.77% of the 1,296,244 km2 of forest in the ranges. Forest is 70% of the 2026 outline area inside the ranges (22,948 of 32,779 mapped km2).
- By range: NT1 10,069 mapped km2 of forest (4.13% of its forest), QC6 5,019 (1.43%), Brightsand 2,967 (17.91%), ON9 Far North 1,517 (1.13%), SK2 1,145 (1.73%), Nipigon 755 (2.92%).
- Quebec populations (union): 4,244 mapped km2 of forest, 1.10% of their forest; Nottaway lost the largest share, 7.22% (1,522 mapped km2).
- Saskatchewan units (union): 1,245 mapped km2 of forest, 1.07%.
- Inside protected and conserved areas nationally: 8,097 mapped km2 of forest, 1.69% of the 479,722 km2 of forest they contain. Ontario 2,730 (4.70% of protected forest), NT 2,689 (4.02%), QC 1,295 (1.16%), BC 751 (0.71%), MB 330 (1.20%).
- Wood Buffalo National Park: 701 mapped km2 of forest, 3.53% of the park's forest.

## 5. Fire management areas (2026 mapped share)

- Ontario's Thunder Bay fire management headquarters area had the highest share: 12.17% (4,965 mapped km2).
- Next: Deh Cho region, NT 4.62% (7,321); Fort Frances, ON 3.81%; Denare Beach, SK 2.79%; Cariboo Fire Centre, BC 2.76% (2,280); North Slave, NT 2.76% (8,858, the largest mapped area of any unit).

## Cross-check with provincial perimeters

- For the 27 ECCC ranges in BC, Ontario and Manitoba, 2026 shares were recomputed with each province's own 2026 perimeters. Ontario agrees closely: Brightsand 16.50% (M3 16.67%), Nipigon 2.41% (2.49%). Manitoba is lower with provincial perimeters: Wapisu 1.68% (M3 2.27%), Kississing 0.55% (1.18%), MB9 0.86% (1.02%). BC ranges are 0% under both. Values are in column check_share_2026_provincial_perimeters_pct.

## Method

1. Inputs reprojected to ESRI:102001 and repaired with make_valid (01_prep.py). NBAC read in one sequential pass, 43,938 polygons for 1987 to 2025; equal-area totals per year match the NBAC POLY_HA field (e.g. 2025 7,307,919 ha).
2. Exact vector overlay on a 100 km tile grid (02_overlay.py, 1,511 tiles): per tile, NBAC 1987 to 2025 polygons are unioned (reburns counted once), M3 outlines unioned, and each target clipped and intersected. Per target: A = area, m = area inside 2026 outlines, u = area inside the 1987 to 2025 union, um = area inside both. 2026 share = m/A; 40-year share = (u + m - um)/A; change caused by 2026 = (m - um)/A, i.e. newly burned ground not already burned since 1987. Overlapping ranges and populations are each computed in full; unions are computed separately.
3. Protected areas: all 21,509 terrestrial CPCAD 2025 records (PA, OECM, interim), unioned within each CPCAD location (province) and nationally. Per-area list dissolved by PARENT_ID (03_cpcad_features.py).
4. Forest: 240 m forest-count raster (count of 30 m forest pixels, classes 1, 2, 5, 6) rasterized against targets and outlines by cell centre in EPSG:3979, with each pixel's area corrected from nominal 900 m2 by the projection's areal scale factor (04_forest.py). Raster target areas match vector areas within 0.01% (union of ranges 2,403,840 vs 2,403,854 km2).
5. Provincial perimeter check (05_provincial_check.py), tables and GeoJSON (06_tables.py), fire management areas (07_fma.py).

## Files

- caribou_ranges_2026.csv: 51 ranges plus union row; rank, 2026 share, mapped km2, 40-year shares before and after 2026, change, share of 2026 burn on previously unburned ground, over-35% flags, forest, provincial-perimeter check.
- caribou_ranges_2026.geojson: same fields, ranges simplified 500 m, WGS84, 5 decimal places, all geometries valid.
- caribou_provincial_layers_2026.csv: Quebec and Saskatchewan layers.
- protected_areas_2026.csv: 128 protected or conserved areas intersecting 2026 outlines.
- protected_by_province_2026.csv: share by province with official CPCAD totals for comparison.
- national_parks_2026.csv: all 47 national parks.
- fma_2026.csv: 146 fire management areas.
- scripts/01 to 07; intermediates in work/ (overlay_results.csv, forest_results.csv, provincial_perimeter_check.csv, tile checkpoint).

## Caveats

- 2026 shares come from M3 outlines, which exceed official totals by about 18% nationally. Ratio of mapped outline to official area by province (Parks Canada fires are reported separately at 124,872 ha, so the ratios for AB and NT are approximate): MB 1.64, NT 1.29, NL 1.27, SK 1.20, ON 1.15, QC 1.08, BC 0.92. Manitoba range and protected area shares are the most overstated. In Ontario the province's own perimeters are themselves 12% above its official total and agree with M3 inside caribou ranges.
- Fire-only disturbance is a lower bound. Human disturbance (roads, cutblocks, seismic lines, mines, settlements, buffered 500 m) is not included, so no range's status against the 65% undisturbed threshold can be stated from this analysis.
- The 40-year window is 1987 to 2026, mixing final NBAC polygons (1987 to 2025) with preliminary 2026 outlines. NBAC 2026 will replace M3 next spring and will likely lower the 2026 figures.
- NBAC flags 411 polygons (all years) as prescribed burns; any in 1987 to 2025 were kept as burned area.
- The ranges are the 2012 federal definitions; several provinces have since revised boundaries (e.g. Quebec's 15 populations differ from the 6 federal QC ranges).
- Fires too small to appear in M3 are missing, so ranges with 0.00% may have had small fires.
- Forest uses 2020 land cover, so forest burned in 2021 to 2025 that is no longer forest is not counted, and the forest classes exclude shrubland and wetland.
- Protected-area provinces follow the CPCAD location field (e.g. Wood Buffalo is listed under AB although part is in NT).
