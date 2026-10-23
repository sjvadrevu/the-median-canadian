# Coverage check: reported major fires vs our outlines

Original check against our files. The reported list was built from news and agency pages only as a checklist; reported sizes are not for publication.

## Scorecard

| | Count |
|---|---|
| Reported major fires checked | 65 |
| With an outline in our data (same year, within 30 km, dates overlap start +/- 45 days) | 63 |
| Missing | 2 |
| Mapped area far below reported (under half) | 1 |
| Expected agency ID or name checked / found inside outline | 33 / 33 |

| Year | Checked | In our data |
|---|---|---|
| 2023 | 17 | 17 |
| 2024 | 12 | 12 |
| 2025 | 23 | 23 |
| 2026 | 13 | 11 |

## Gaps

- Thunder Lake structural fires (AB, 2026): NOT IN DATA: no M3 outline and no CWFIF fire-list point within 20 km. Structural fires inside a hamlet, likely too small or brief for satellite outlines.
- CFB Wainwright fire (AB, 2026): NOT IN DATA: no M3 outline for Oct 17 (M3 file of 2026-10-20 and refreshed 2026-10-22). Only 9 VIIRS hotspots; they never entered the M3 product. The only 2026 outline nearby is M3 36076649 (113 ha, Apr 21 to May 1, class military range). Our Sentinel-2 estimate is about 1,090 ha (analysis/wainwright).
- Walsh River fire (NL, 2026): MAPPED AREA FAR BELOW: M3 outline 90 ha from a single detection day (outline-check class unclear) vs CWFIF NL 622 at 682 ha, 11 km from Labrador City, reported 2026-06-29. Likely cloud or smoke gaps; outline under-maps the fire.

## All fires

| Year | Fire | Prov | In data | Our ha | Outline | ID match |
|---|---|---|---|---|---|---|
| 2023 | Long Lake Complex (HWF-036) | AB | yes | 518,067 | NBAC 2023_354 | yes |
| 2023 | Paskwa fire (HWF-030) | AB | yes | 72,812 | NBAC 2023_681 | yes |
| 2023 | Edson-area fire | AB | yes | 234,997 | NBAC 2023_366 |  |
| 2023 | Drayton Valley-area fire | AB | yes | 4,442 | NBAC 2023_709 |  |
| 2023 | Donnie Creek (G80280) | BC | yes | 443,387 | NBAC 2023_359 | yes |
| 2023 | McDougall Creek | BC | yes | 12,877 | NBAC 2023_834 | yes |
| 2023 | Bush Creek East | BC | yes | 34,610 | NBAC 2023_897 | yes |
| 2023 | Yellowknife / Behchoko fire (ZF015) | NT | yes | 133,046 | NBAC 2023_331 | yes |
| 2023 | Hay River / Enterprise fire (August) | NT | yes | 433,014 | NBAC 2023_321 |  |
| 2023 | Hay River fire (May) | NT | yes | 2,773 | NBAC 2023_320 |  |
| 2023 | Wood Buffalo NP Fire 7 (Fort Smith) | NT | yes | 350,826 | NBAC 2023_317 | yes |
| 2023 | Tantallon (Westwood Hills) fire | NS | yes | 849 | NBAC 2023_581 |  |
| 2023 | Barrington Lake fire | NS | yes | 21,260 | NBAC 2023_582 | yes |
| 2023 | Lebel-sur-Quevillon fires | QC | yes | 359,389 | NBAC 2023_345 |  |
| 2023 | Chibougamau fire | QC | yes | 178,317 | NBAC 2023_340 |  |
| 2023 | Sept-Iles fire | QC | yes | 638 | NBAC 2023_468 |  |
| 2023 | Pimicikamak (Cross Lake) fire | MB | yes | 2,271 | NBAC 2023_139 |  |
| 2024 | Jasper wildfire complex | AB | yes | 30,829 | NBAC 2024_451 |  |
| 2024 | Fort McMurray fire (MWF-017) | AB | yes | 17,368 | NBAC 2024_150 | yes |
| 2024 | Parker Lake fire | BC | yes | 9,170 | NBAC 2024_176 | yes |
| 2024 | Patry Creek fire | BC | yes | 99,708 | NBAC 2024_192 | yes |
| 2024 | Antler Creek fire | BC | yes | 11,104 | NBAC 2024_166 | yes |
| 2024 | Dogtooth FSR fire | BC | yes | 4,478 | NBAC 2024_247 | yes |
| 2024 | Cranberry Portage fire | MB | yes | 28,724 | NBAC 2024_323 |  |
| 2024 | Bunibonibee / Nisichawayasihk area fire | MB | yes | 8,458 | NBAC 2024_300 |  |
| 2024 | Labrador City fire | NL | yes | 9,901 | NBAC 2024_553 |  |
| 2024 | Churchill Falls fire | NL | yes | 4,089 | NBAC 2024_569 |  |
| 2024 | Fort Good Hope fire | NT | yes | 6,863 | NBAC 2024_21 |  |
| 2024 | Sandy Bay fire | SK | yes | 47,849 | NBAC 2024_390 |  |
| 2025 | Lac du Bonnet fire | MB | yes | 3,472 | NBAC 2025_106 |  |
| 2025 | Flin Flon / Creighton / Denare Beach fire | MB | yes | 407,908 | NBAC 2025_433 |  |
| 2025 | Denare Beach (same fire, SK side) | SK | yes | 407,908 | NBAC 2025_433 |  |
| 2025 | Shoe fire (merged with Camp fire) | SK | yes | 610,738 | NBAC 2025_273 | yes |
| 2025 | Pisew fire | SK | yes | 173,471 | NBAC 2025_428 | yes |
| 2025 | Pelican 2 fire | SK | yes | 33,203 | NBAC 2025_702 | yes |
| 2025 | Muskeg fire | SK | yes | 240,927 | NBAC 2025_238 | yes |
| 2025 | Garden Hill First Nation fire | MB | yes | 68,890 | NBAC 2025_435 |  |
| 2025 | Mathias Colomb (Pukatawagan) fire | MB | yes | 130,969 | NBAC 2025_432 |  |
| 2025 | Tataskweyak Cree Nation fire | MB | yes | 24,300 | NBAC 2025_15 |  |
| 2025 | Kenora 20 (Ingolf fire) | ON | yes | 27,317 | NBAC 2025_41 | yes |
| 2025 | Red Lake 12 | ON | yes | 155,662 | NBAC 2025_594 | yes |
| 2025 | Red Lake 62 | ON | yes | 29,021 | NBAC 2025_646 | yes |
| 2025 | Swan Hills fire | AB | yes | 12,910 | NBAC 2025_513 |  |
| 2025 | Chipewyan Lake fire | AB | yes | 106,501 | NBAC 2025_480 |  |
| 2025 | Kiskatinaw River fire | BC | yes | 15,551 | NBAC 2025_488 | yes |
| 2025 | Beef Trail Creek fire | BC | yes | 11,832 | NBAC 2025_566 | yes |
| 2025 | Mount Underwood fire | BC | yes | 3,252 | NBAC 2025_529 | yes |
| 2025 | Fort Providence fire (SS014) | NT | yes | 111,816 | NBAC 2025_236 | yes |
| 2025 | Kingston fire | NL | yes | 9,629 | NBAC 2025_684 | yes |
| 2025 | Paddy's Pond fire | NL | yes | 294 | NBAC 2025_685 | yes |
| 2025 | Conception Bay North fires (May) | NL | yes | 9,629 | NBAC 2025_684 |  |
| 2025 | Long Lake fire | NS | yes | 8,074 | NBAC 2025_680 | yes |
| 2026 | Thunder Bay 36 | ON | yes | 351,688 | M3 36077765 | yes |
| 2026 | Thunder Bay 36 (Namaygoosisagagun) | ON | yes | 351,688 | M3 36077765 | yes |
| 2026 | Thunder Bay district fire near Gull Bay FN | ON | yes | 351,688 | M3 36077765 |  |
| 2026 | Fire near Eabametoong FN (Fort Hope) | ON | yes | 10,863 | M3 36077790 |  |
| 2026 | Fire near Lac La Croix FN | ON | yes | 1,840 | M3 36077724 |  |
| 2026 | Bald Range | BC | yes | 25,502 | M3 36076584 | yes |
| 2026 | Bradley Creek | BC | yes | 2,114 | M3 36076592 | yes |
| 2026 | Pear Lake (Big Bar complex) | BC | yes | 172,459 | M3 36077449 |  |
| 2026 | Fort Simpson fire (FS016-26) | NT | yes | 97,021 | M3 36077461 | yes |
| 2026 | Lobstick fire | SK | yes | 14,679 | M3 36077523 | yes |
| 2026 | Walsh River fire | NL | yes | 90 | M3 36076864 |  |
| 2026 | Thunder Lake structural fires | AB | no |  |  |  |
| 2026 | CFB Wainwright fire | AB | no |  |  |  |

## Labels for the national map (labels.csv)

| Label | Lon | Lat | Outline |
|---|---|---|---|
| Thunder Bay district, 2026 | -89.1497 | 50.5341 | M3 36077765 |
| Summerland, 2026 | -119.7889 | 49.6056 | M3 36076584 |
| Jasper, 2024 | -117.9533 | 52.7757 | NBAC 2024_451 |
| Yellowknife, 2023 | -115.0525 | 62.7425 | NBAC 2023_331 |
| Flin Flon / Denare Beach, 2025 | -101.9974 | 54.8372 | NBAC 2025_433 |
| Lebel-sur-Quevillon, 2023 | -76.1465 | 48.9138 | NBAC 2023_345 |
| Shelburne County, 2023 | -65.3872 | 43.6006 | NBAC 2023_582 |
| Kingston NL, 2025 | -53.114 | 47.8555 | NBAC 2025_684 |

## Method

- Outlines: NBAC 2023 to 2025 (NBAC_merged_1972_to_2025_20260513, parts sharing a GID dissolved, since NBAC splits a fire at province lines) and CWFIS M3 2026 (m3_perimeters_2026_cwfis_20261020.gpkg, 718 polygons, classes from analysis/outline-check). Areas are equal-area (EPSG:3978).
- Reported location: nearest community geocoded with NRCan Geographical Names; Donnie Creek uses the CNFDB point; Wainwright uses the Alberta Wildfire point RMD-001-2026.
- Match: same-year outline within 30 km whose first to last dates overlap the reported start +/- 45 days. If an agency ID or name was expected, the outline holding that CNFDB (2023 to 2025) or CWFIF fire-list (2026) point within 2 km is chosen; otherwise the nearest outline of 500 ha or more.
- "Our ha" is the chosen outline; coverage.csv note also gives the sum of all matching outlines within 30 km.
- Scripts: scripts/checklist.py, 01_geocode.py, 02_coverage.py, 03_outputs.py.
