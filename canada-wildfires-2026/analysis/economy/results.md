# Canada's 2026 wildfire season: economy, livelihoods and scale (original analysis of official data)

Analysis date 2026-10-21. Fire data to 2026-10-20. Every number comes from the files in this folder; scripts are in `scripts/` (run order: 01, 01b, 02 (x3, plus 02b_run_scanfi_1622.sh), 03, 04 (x2), 05, 05b, 06, 06b, 07, 07b, 08, 08b, 09). Sources are listed in `manifest.csv`.

Two lenses throughout: (1) 2026 alone, (2) 2023 to 2026 combined (union of footprints, each hectare counted once). Per-year series 2016 to 2026 are in `timber_carbon_by_year.csv`, `jobs_by_year.csv`, `infra_by_year.csv`, `dwellings_by_year.csv` and `scale_by_year.csv`.

"Mapped" means measured on the satellite footprints (NBAC for 2016 to 2025, CWFIS M3 outlines for 2026; M3 is 17.8% above the official 2026 total). "Scaled" means each burned cell is multiplied by its province's official/mapped ratio for that year (2026 factors from `analysis/forest/scaling_factors_by_province.csv`; 2016 to 2025 factors = NFD official provincial area / NBAC mapped area outside national parks, `work/scale_factors_2016_2025.csv`). On the mapped forest-share basis the four largest years since 1972 are 2023 (2.61% of forest), 2025 (1.39%), 2026 (1.04%) and 2024 (0.93%); the next is 1989 (0.81%).

## Scorecard

| Measure | 2026 | 2023 to 2026 |
|---|---|---|
| Area burned (official) | 4.50 M ha | 35.79 M ha distinct |
| Share of Canada's forest | 1.04% (1 ha in 96) | 5.95% (1 ha in 17) |
| Merchantable wood, scaled | 169 M m3 | 1,336 M m3 |
| Years of national harvest (2024) | 1.4 | 11.2 |
| CO2, our estimate, scaled | 39 to 120 Mt | 360 to 1,156 Mt |
| Share of 2024 national emissions | 5.6% to 17.5% | 53% to 169% |
| Forestry jobs in CDs touched | 43,425 | 75,035 |
| Roads inside burned area | 1,280 km (2,185 within 1 km) | 9,503 km |
| Dwellings in DAs touched | 45,718 | 486,438 |

## 1. Timber and forest value

Findings, 2026
- Inside the 2026 burned area there were 181.8 million m3 of merchantable wood on the mapped footprint, 169.1 million m3 scaled to official totals (NFI kNN 2011 volume map). Total stem volume was 296.1 million m3 (mapped). Pre-fire aboveground biomass (SCANFI v2, 2025 map) was 213.2 million tonnes mapped, 191.6 million tonnes scaled.
- Canada harvested 118.98 million m3 of roundwood in 2024 (NFD, latest year) and 127.9 million m3 a year on average in 2020 to 2024. The 2026 burned merchantable volume equals 1.42 years of the 2024 harvest (scaled; 1.53 mapped) or 1.32 years of the 2020 to 2024 average.
- By province (scaled, years of that province's 2024 harvest): Ontario 56.7 million m3, 4.3 years; British Columbia 62.8 million m3, 1.6 years; Manitoba 4.4 million m3, 4.0 years; Saskatchewan 7.8 million m3, 1.8 years; Newfoundland and Labrador 2.5 million m3, 1.8 years; Quebec 19.2 million m3, 0.74 years; Alberta 0.44 million m3, 0.02 years. NWT burned 14.8 million m3 against a harvest of 36,637 m3 (404 years); the ratio is not meaningful because almost no NWT forest is harvested.
- Largest volumes by fire management area (scaled): Ontario Thunder Bay 29.8 million m3; BC Coastal Fire Centre 23.3 million m3 on 90,068 mapped ha (dense coastal stands); BC Cariboo 23.3 million m3; Quebec 19.2 million m3; BC Kamloops 13.2 million m3; Ontario Sioux Lookout 11.9 million m3; NWT Deh Cho 8.7 million m3; Ontario Fort Frances 8.2 million m3.

Findings, 2023 to 2026
- Merchantable volume in the combined burned area: 1,133.7 million m3 mapped, 1,336.0 million m3 scaled; 9.5 to 11.2 years of the 2024 national harvest (8.9 to 10.4 years of the 2020 to 2024 average). Total stem volume 2,026.7 million m3 mapped, 4.2% of Canada's total tree volume in the NFI (48,189 million m3). Pre-fire aboveground biomass 1,658 million tonnes, 5.5% of the NFI national aboveground biomass (30,064 million tonnes).
- By province (scaled, years of 2024 harvest): BC 377.1 million m3, 9.7 years; Saskatchewan 239.4 million m3, 56.7 years; Alberta 220.4 million m3, 9.9 years; Quebec 162.3 million m3, 6.3 years; Ontario 128.4 million m3, 9.8 years; Manitoba 109.6 million m3, 99 years; NWT 78.7 million m3.
- Largest areas: BC Prince George Fire Centre 177.4 million m3; Quebec 162.3; Manitoba 109.6; Alberta High Level 66.4; Saskatchewan Île-à-la-Crosse 63.1 and La Ronge 60.4; BC Kamloops 56.3 and Cariboo 41.6 (million m3, scaled).

Per year (Canada, scaled merchantable volume burned vs that year's harvest; 2025 and 2026 compared with 2024, the latest NFD year)

| Year | Area scaled (M ha) | Merch. volume (M m3) | Harvest (M m3) | Years of harvest |
|---|---|---|---|---|
| 2016 | 1.33 | 36.0 | 157.2 | 0.23 |
| 2017 | 3.71 | 149.3 | 154.1 | 0.97 |
| 2018 | 2.37 | 225.3 | 156.2 | 1.44 |
| 2019 | 1.91 | 82.6 | 141.3 | 0.58 |
| 2020 | 0.22 | 12.1 | 140.2 | 0.09 |
| 2021 | 4.12 | 261.2 | 139.4 | 1.87 |
| 2022 | 1.61 | 49.1 | 130.0 | 0.38 |
| 2023 | 18.38 | 662.2 | 110.8 | 5.97 |
| 2024 | 5.47 | 171.4 | 119.0 | 1.44 |
| 2025 | 8.48 | 339.1 | 119.0 | 2.85 |
| 2026 | 4.52 | 169.1 | 119.0 | 1.42 |

- 2016 to 2022 averaged 116.5 million m3 of merchantable wood burned a year (scaled); 2023 to 2026 averaged 335.5 million m3 a year, 2.9 times as much, while the national harvest fell from 157.2 million m3 (2016) to 119.0 million m3 (2024).
- Check on the biomass maps: on land that burned in 2023, SCANFI aboveground biomass falls from 828.6 million tonnes (2020 map) to 406.9 million tonnes (2025 map), a 51% drop; for 2024 burns 244.0 to 103.9 million tonnes (57%). For 2026 burns the 2020 and 2025 maps agree (212.7 vs 213.2 million tonnes), as expected before the fire.

Method
- Burned area: 240 m grid cells (EPSG:3979) from `analysis/forest` (cell-centre rule; NBAC 2016 to 2025, M3 2026). 5,359,901 cells in the 2023 to 2026 union (32.22 M ha mapped), 2,184,959 cells for 2016 to 2022.
- Biomass: SCANFI v2 30 m aboveground biomass, summed over the 64 pixels of each 240 m cell (pixel assigned by its centre; true area from the projection's areal scale). Pre-fire map: 2015 for 2016 to 2020 fires, 2020 for 2021 to 2025, 2025 for 2026; the 2023 to 2026 union uses the map before each cell's first burn in the period.
- Volume: NFI kNN 2011 250 m merchantable and total volume, sampled at cell centres. It is the only open national volume map; 9.5 million m3 of the 2026 volume (5.2%) and 72.2 million m3 of the union volume (6.4%) sit on cells that burned again between 2011 and 2022, where the 2011 value is out of date. kNN 2011 aboveground biomass on 2026 cells (211.3 million tonnes) agrees with SCANFI 2025 (213.2) within 1%.
- Harvest: NFD net merchantable roundwood harvested, all categories, species and tenures, by province and year.
- Files: `timber_biomass_carbon_by_area.csv` (Canada, province, fire management area, national park; scopes 2023, 2024, 2025, 2026, union), `timber_carbon_by_year.csv` (2016 to 2026 and union, Canada and province), `harvest_nfd_by_province.csv`.

## 2. Carbon (our estimate, assumption based)

Assumptions, stated as such: carbon = 0.5 x dry biomass. Combusted share of pre-fire live aboveground biomass: LOW = foliage only (all foliage burns, nothing else), HIGH = foliage + branches + stem bark (all non-stem biomass burns, stem wood stays standing). The two shares are measured, not assumed: they come from the kNN 2011 biomass components over the same burned cells (2026: 11.0% and 34.2%; union: 10.1% and 32.4%). CO2 = carbon x 44/12. Not included: dead wood, litter, peat and soil organic layers (often the largest fire source), CH4, N2O and later decay. The range is therefore a floor-to-mid estimate of aboveground combustion, not total fire emissions.

Findings
- 2026: 38.6 to 120.0 million tonnes CO2 (scaled; 42.9 to 133.6 mapped). Against Canada's 2024 inventory total of 684.7 Mt CO2e (NIR 2026, latest year) that is 5.6% to 17.5%, or 21 to 64 days of national emissions; 0.48 to 1.50 years of emissions from all passenger cars, light trucks and motorcycles (79.9 Mt); 1.6 to 5.1 years of light-duty gasoline cars alone (23.6 Mt); 0.78 to 2.42 years of the electricity sector (49.6 Mt).
- 2023 to 2026: 359.9 to 1,156.1 million tonnes CO2 (scaled; 306.2 to 983.8 mapped), 0.53 to 1.69 years of 2024 national emissions; 4.5 to 14.5 years of all passenger cars, light trucks and motorcycles.
- Per year (scaled, low to high, Mt CO2, and share of that year's national total): 2016 15 to 49 (2.1% to 6.7%); 2017 36 to 116 (4.9% to 15.7%); 2018 38 to 132 (5.1% to 17.7%); 2019 22 to 81 (3.0% to 10.8%); 2020 2 to 7 (0.3% to 1.1%); 2021 46 to 154 (6.7% to 22.2%); 2022 15 to 48 (2.2% to 6.9%); 2023 183 to 610 (26.7% to 88.9%); 2024 51 to 166 (7.5% to 24.3%); 2025 83 to 256 (12.2% to 37.4% of 2024); 2026 39 to 120 (5.6% to 17.5% of 2024). Average 25 to 84 Mt a year in 2016 to 2022 against 89 to 288 Mt a year in 2023 to 2026.
- Official context (not like-for-like): the NIR reports wildfire direct immediate emissions in the managed forest only, all carbon pools, CO2 + CH4 + N2O, outside the national total: 870 Mt CO2e in 2023 (750 Mt CO2), 320 Mt CO2e in 2024, 260 Mt in 2021, 220 Mt in 2018. Our aboveground-only high case is below the official managed-forest figure every year (2023: 610 vs 870), consistent with ground fuels being excluded here.
- By province, 2026 (scaled, Mt CO2): BC 8.9 to 33.3; NWT 10.0 to 29.5; Ontario 6.8 to 21.8; Quebec 7.5 to 20.2; Manitoba 2.3 to 6.0; NL 2.1 to 5.0; Saskatchewan 1.4 to 4.2.

Files: `timber_biomass_carbon_by_area.csv` (columns co2_low_*, co2_high_*, foliage_share, nonstem_share), `timber_carbon_by_year.csv`, inventory inputs in `raw/ghg/`.

## 3. Livelihoods

National reference (2021 Census, employed residents): 178,825 forestry jobs (NAICS 113 forestry and logging 26,175; 1153 support activities 15,950; 321 wood products 86,750; 322 paper 49,950), 1.03% of 17.32 million employed; 99,190 accommodation jobs (NAICS 721, of which 7212 RV parks and recreational camps 10,215), 0.57%. "High dependence" = at least three times the national share: forestry 3.10% or more, accommodation 1.72% or more.

Findings, 2026
- 66 census divisions (CDs) had at least 100 ha burned in 2026. They hold 1,805,125 employed residents, 43,425 forestry jobs and 18,545 accommodation jobs. 22 of them are forestry-dependent, with 32,155 forestry jobs (BC 11 CDs, 19,565 jobs; Ontario 5, 6,535; Quebec 3, 2,920; Alberta 1, 2,475; NB 1, 340; Manitoba 1, 320). 12 are accommodation-dependent, with 4,535 accommodation jobs (BC 7, 4,140).
- 15 CDs had 1% or more of their land burned in 2026: 10,775 forestry and 5,195 accommodation jobs. Forestry-dependent among them: Thunder Bay (ON, 5.5% of land burned, 2,250 forestry jobs, 3.6% of employment), Thompson-Nicola (BC, 5.4%, 2,525 jobs), Rainy River (ON, 5.6%, 460 jobs, 5.5%), Nord-du-Québec (1.0%, 1,095 jobs, 5.7%), Queens (NB, 1.4%, 340 jobs, 8.4%). Accommodation-dependent: Squamish-Lillooet (BC, 2.4% burned, 1,390 accommodation jobs, 5.0% of employment), Okanagan-Similkameen (BC, 2.5%), NWT Region 4 (3.9%), Manitoba Division No. 23 (1.7%).
- Within 25 km of a fire of 1,000 ha or more: 69 CDs, 45,945 forestry and 25,025 accommodation jobs; 20 forestry-dependent CDs with 30,285 forestry jobs. (Counting all outlines, including small farm and spring burns near cities: 101 CDs, 59,920 forestry jobs.)
- Mills (NRCan list, published 2016): one mill lies inside a 2026 outline (West Fraser sawmill, Chasm, BC); none within 0 to 1 km; 6 within 1 to 10 km (Kalesnikoff sawmill at Thrums BC; Tolko plywood plant and sawmill at Armstrong BC; Whitesand First Nation pellet plant at Armstrong ON; Mercer pulp mill and Interfor sawmill at Castlegar BC); 32 within 10 to 25 km (BC 22, Ontario 6, NB 2, AB 1, MB 1).

Findings, 2023 to 2026
- 120 CDs had at least 100 ha burned: 3.81 million employed, 75,035 forestry jobs (42% of the national total) and 36,940 accommodation jobs. 41 are forestry-dependent with 51,465 forestry jobs; 21 accommodation-dependent with 7,850 accommodation jobs.
- 50 CDs had 1% or more of their land burned: 37,995 forestry jobs, 16,175 accommodation jobs; 20 forestry-dependent CDs with 29,065 forestry jobs (including La Tuque, Maria-Chapdelaine, La Haute-Côte-Nord, Bulkley-Nechako, Cariboo, Thompson-Nicola, Thunder Bay, Kenora, Rainy River, Alberta Division No. 17).
- Most burned CDs (share of land, 2023 to 2026): Northern Rockies BC 21.9%; NWT Region 4 16.8%; Saskatchewan Division No. 18 16.5%; NWT Region 3 15.5%; Alberta Division No. 16 14.5%; Alberta Division No. 17 11.7% (forestry 10.3% of employment); La Vallée-de-l'Or QC 11.2%; Manitoba Division No. 21 11.0%.

Per year (Canada; CDs with 1% or more of land burned; 2021 jobs held constant)

| Year | CDs | Forestry jobs | Accommodation jobs | Forestry-dependent CDs |
|---|---|---|---|---|
| 2016 | 2 | 80 | 265 | 0 |
| 2017 | 8 | 8,970 | 2,970 | 3 |
| 2018 | 9 | 10,700 | 1,850 | 5 |
| 2019 | 2 | 2,555 | 610 | 1 |
| 2020 | 2 | 695 | 180 | 1 |
| 2021 | 16 | 14,975 | 6,345 | 9 |
| 2022 | 6 | 1,225 | 1,245 | 0 |
| 2023 | 26 | 22,375 | 8,345 | 12 |
| 2024 | 13 | 8,015 | 3,150 | 4 |
| 2025 | 19 | 10,520 | 3,775 | 5 |
| 2026 | 15 | 10,775 | 5,195 | 5 |

The "touched" (100 ha) series is in `jobs_by_year.csv` (2026: 66 CDs; 2023: 86; 2021: 67; 2018: 72).

Method: StatCan table 98-10-0592-01 (employed, all ages and genders, all classes of worker) for Canada, provinces and 293 CDs, fetched through the WDS API (`raw/statcan/`). Industry groups (4-digit NAICS) are only published down to CD level; CSD tables carry 2-digit sectors only, so CDs are the community unit here. CD polygons = 2021 DA polygons dissolved by CD code. Burned area per CD from the 240 m cells; distances in ESRI:102001.

Files: `census_divisions_jobs_and_fire.csv` (293 CDs: jobs, shares, burned ha 2026 and union, distances, flags), `jobs_by_province_fire_scope.csv`, `jobs_by_year.csv`, `jobs_canada_provinces_2021.csv`, `mills_distance_to_2026_fires.csv`.

## 4. Infrastructure and dwellings

Findings, 2026 (mapped M3 outlines; exact vector clip, geodesic length)
- Railways: 252.1 km of track inside the 2026 outlines and 328.9 km within 1 km (main line 206.4 and 270.6 km). BC 177.5 km inside (222.0 within 1 km), Ontario 71.6 km (90.4).
- Power lines (CanVec 1:50K, no voltage attribute): 269.8 km inside, 396.8 km within 1 km. BC 192.9 km inside (247.4), Manitoba 30.2 (65.5), Saskatchewan 17.6 (24.9), Ontario 10.7 (20.2), NWT 10.1, Quebec 4.3 (17.6).
- Roads (NRN, exact vector clip): 1,279.7 km inside and 2,184.7 km within 1 km (grid method: 1,280 and 2,108 km). By class inside: resource/recreation 468 km, local streets 369 km, expressway/highway 191 km, collector 115 km, arterial 59 km, winter roads 48 km. By province inside: BC 518 km, Ontario 397 km, NWT 140 km, Saskatchewan 94 km, Manitoba 54 km, NB 31 km, Quebec 27 km.
- Dwellings: 206 dissemination areas (DA) intersect a 2026 outline; they hold 45,718 private dwellings (31,219 occupied) and 78,585 people (2021). In the 25 DAs whose centre point lies inside an outline: 2,470 dwellings, 4,843 people (BC 1,502, NL 556, NWT 324, MB 88 dwellings). These are dwellings in areas intersecting fires, not losses.

Findings, 2023 to 2026 (grid method)
- Roads 9,503 km inside burned area, 20,862 km within about 1 km (resource/recreation 3,366 km, collector 2,451, expressway/highway 1,978, local 773 inside). Alberta 3,242 km inside, Saskatchewan 1,907, BC 1,300, Ontario 794, Manitoba 769, NWT 642.
- Railways 686 km inside, 1,569 km within 1 km. Power lines 1,675 km inside, 2,923 km within 1 km (Quebec 485, Manitoba 439, BC 326, Alberta 142 km inside).
- Dwellings: 1,715 DAs intersect a burned area (486,438 dwellings, 895,805 people); 107 DAs have their centre inside (15,510 dwellings, 37,525 people). With fires of 1,000 ha or more only: 512 DAs (123,751 dwellings) and 93 DAs (13,698 dwellings).

Per year (Canada; roads, rail and power inside burned area, grid method; dwellings in DAs intersecting fires of 1,000 ha or more)

| Year | Roads km | Rail km | Power line km | Dwellings (DA, fires 1,000 ha+) |
|---|---|---|---|---|
| 2016 | 423 | 81 | 229 | 20,593 |
| 2017 | 1,081 | 19 | 87 | 29,738 |
| 2018 | 624 | 15 | 112 | 39,728 |
| 2019 | 510 | 84 | 108 | 13,770 |
| 2020 | 200 | 0 | 31 | 9,459 |
| 2021 | 1,098 | 105 | 250 | 53,218 |
| 2022 | 233 | 16 | 69 | 13,835 |
| 2023 | 4,512 | 253 | 853 | 70,458 |
| 2024 | 755 | 61 | 78 | 23,900 |
| 2025 | 3,025 | 121 | 481 | 45,273 |
| 2026 | 1,280 | 252 | 269 | 27,661 |

Method
- 2026 vector clip (`05_infra.py`): lines clipped to the dissolved M3 outlines and to a 1,000 m buffer (ESRI:102001), length measured geodesically (GRS80).
- Grid method for all years (`05b_infra_by_year.py`): lines cut into pieces of at most 30 m, each piece assigned to the 240 m cell holding its midpoint, ground length corrected for projection scale; "inside" = burned cells of that year, "within about 1 km" = burned cells dilated by a 1,000 m disc. Check against the 2026 vector clip: rail 252.2 vs 252.1 km inside, 323.6 vs 328.9 km within 1 km; power 269.3 vs 269.8 and 387.7 vs 396.8 km; roads in BC, AB, SK, MB and ON (vector clip finished for these five) 1,078.2 vs 1,078.1 km inside and 1,789 vs 1,856 km within 1 km. Inside lengths agree within 1%; the grid's "within about 1 km" runs 2% to 4% low. All provinces, roads: 1,279.7 km (vector) vs 1,280 km (grid) inside; 2,184.7 vs 2,108 km within 1 km.
- Dwellings: StatCan table 98-10-0015-01 at DA level. Dissemination-block counts (finer) are only in the Geographic Attribute File on www12.statcan.gc.ca, which refused download (HTTP 403), so DAs are the finest unit; a rural DA can be large, so "DA intersects" is an upper bound and "DA centre inside" a tighter count. 2021 stock used for every year.

Files: `infra_by_year.csv` (kind x class x year x province x band), `work/infra_segments_2026_*.gpkg/.csv` (clipped 2026 lines), `dwellings_2026_by_province.csv`, `dwellings_by_year.csv`.

## 5. Scale translations (each from official numbers)

Area (2026 official 4,500,985 ha; 2023 to 2026 distinct land 35,793,959 ha, official-scaled union from `analysis/forest`)
- 2026: about the size of Estonia (0.99 times), Denmark (1.05), the Netherlands (1.08) or Switzerland (1.09); 0.85 times the land area of Nova Scotia; 71 times the City of Toronto, 55 times Calgary, 16 times Ottawa, 123 times Montréal.
- 2023 to 2026: about the size of Germany (1.00 times) or Japan (0.95); 1.00 times the land area of Newfoundland and Labrador; 0.56 times Alberta's land; 1.46 times the United Kingdom; 567 times Toronto, 436 times Calgary, 128 times Ottawa.
- Each year 2016 to 2026 against its closest country and province: `scale_by_year.csv` (for example 2021 = Switzerland, 0.99; 2023 = Uruguay, 1.01, or half of Newfoundland and Labrador; 2025 = Austria, 1.00, or 1.18 times New Brunswick).

Forest share
- 2026: 1.04% of Canada's forest (mapped), one hectare in every 96; scaled to the official area 0.88%, one in every 113. 2023 to 2026: 5.95%, one hectare in every 17. Earlier years: 2016 one in 1,926; 2017 one in 414; 2021 one in 130; 2023 one in 38; 2024 one in 108; 2025 one in 72.

Trees
- No official stems-per-hectare figure exists for Canada: the NFI standard reports (tables 1 to 22) give area, volume, biomass and carbon but no tree counts, so no tree count is given here. Volume and biomass are used instead: 2026 burned 0.6% of Canada's total tree volume and 0.7% of its aboveground tree biomass; 2023 to 2026 burned 4.2% and 5.5%.

Wood and carbon: see sections 1 and 2 (1.4 years of national harvest for 2026, 11.2 years for 2023 to 2026; CO2 equal to 21 to 64 days of national emissions for 2026 and 0.53 to 1.69 years for 2023 to 2026).

Files: `scale_comparisons.csv` (every comparison with its value, comparator, ratio, plain sentence and inputs), `scale_by_year.csv`, `country_area_ratios.csv` (all UN DYB countries).

## Caveats

1. 2026 footprints are CWFIS M3 hotspot outlines (include unburned islands, 17.8% above official area); 2016 to 2025 are NBAC. Scaled figures correct the total per province but not where inside the province the excess lies. NB's 2026 factor is 0.07 and NS's 3.43, so their scaled values are weak. NBAC includes many small agency-mapped fires near towns that M3 misses; dwellings and "touched" counts are more comparable across years with the 1,000 ha and 1% filters.
2. Volume is from 2011 (only open national map). Burned merchantable volume is not all lost: salvage is possible, and most northern burned forest (NWT, northern SK, MB, QC) lies outside the harvested land base, so "years of harvest" compares physical quantities, not lost supply.
3. Carbon is our estimate. It covers aboveground live biomass only, with a measured but assumed combustion range; ground fuels, which dominate boreal fire emissions, are excluded. Official NIR wildfire figures cover only the managed forest and are reported outside the national total.
4. NFD harvest for 2025 and 2026 is not yet published (2024 used). NB 2020 to 2024 repeats one value (qualifier E); Alberta 2024 is preliminary. NIR national totals end in 2024.
5. Jobs are 2021 Census residents by place of residence, constant for all years; CD is the finest unit with 4-digit industries; unpublished series counted as 0. A CD touched by fire does not mean jobs were lost.
6. Mill list is old (compiled 2001 to 2011, published 2016) and mixes sources.
7. Rail layer is the 2019 NRWN; power lines have no voltage attribute; roads are NRN editions dated 2026-06-26.
8. Area comparisons use land area for Canadian provinces and cities and total surface area (land plus inland water) for countries.
