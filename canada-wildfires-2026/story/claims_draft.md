# Draft claims for the week 2 wildfire post (to be verified)

Base folder: analysis/
Each claim: ID | claim | where the number should come from (folder; read results.md, REBUILD.md, CSVs, scripts)

## Slide 1: result
C1 | The four largest fire years since 1972 by share of Canada's forest burned are 2023, 2025, 2026, 2024 (2023 2.61%, 2025 1.39%, 2026 1.04%, 2024 0.93%; next 1989 0.81%) | forest/canada_forest_share_by_year.csv (+2026 from forest/canada_totals.csv)
C2 | 2023 to 2026 burned about 6% of Canada's forest (5.95% to 5.97%), 1 hectare in every 17 | forest/, economy/scale_comparisons.csv
C3 | Highest earlier 4-year window: 2.06% (1979 to 1982) | forest/canada_forest_share_by_year.csv (rolling sum)
C4 | 2023 to 2026 official area burned 35.79 million ha, about the size of Germany | economy/scale_comparisons.csv
C5 | 2026 official total 4.50 million ha, 8th of 37 years since 1990 (NFD) | forest/ranking_canada.csv, REBUILD.md

## Slide 2: climate
C6 | May to August fire season 2016 to 2026 was 1.15°C warmer than 1961 to 1990 (95% range 0.80 to 1.49) | climate-change/
C7 | All 236 long-record temperature stations warmed | climate-change/
C8 | +1°C May to August means about 44% more area burned (30% to 62%) | climate-change/model_coefficients.csv
C9 | Warming alone: 2023 to 2026 burn about 1.53 times what 1961 to 1990 temperatures would give (1.37 to 1.76), i.e. about a third of the burn | climate-change/counterfactual_2023_2026.csv

## Slide 3: drought
C10 | April to September rain 2023 to 2026 was the driest 4-year window since 1950, 84% of normal | climate-change/
C11 | No long-term trend in April to September precipitation | climate-change/climate_trends.csv
C12 | Share of modelled forest in moderate drought or worse at some point Apr to Sep: 2023 53.7%, 2024 53.8%, 2025 72.2%, 2026 55.8%; 2003 to 2022 average 14.4%, max 32.7% | cause/

## Slide 4: expected vs actual
C13 | 2026 lightning-caused fires below the 1991 to 2020 average (2,960 vs 3,245 comparable basis); human-caused fires 2,190, fewest in 37 years | cause/
C14 | Lightning started 54.7% of 2026 fires but burned 95.0% of area | cause/
C15 | Cause model trained on 2003 to 2022 predicted 2023 to 2026 forest share burned at about one-sixteenth of actual (ratio 16.3 after rebuild; 14.1 before) | cause/, REBUILD.md

## Slide 5: people
C16 | July 16, 2026 was the smokiest single day for Canadians since 2018: population-weighted 67.0 µg/m³ vs previous high 52.5 (June 25, 2023) | health/
C17 | 11.7 million Ontarians had at least one day above 100 µg/m³ in 2026, most of any year 2018 to 2026 | health/
C18 | Modelled smoke deaths (short-term) 2026: 98 (Health Canada coefficient) to 253 (wildfire-specific); 2023: 379 to 988 | health/
C19 | Direct wildfire deaths in federal records: 2023 1, 2024 2, 2025 2, 2026 6 (TSB aviation 2026; check the 2026 count of 6 against the TSB record for the June 24 crash near Fort Simpson) | losses/
C20 | Ratio smoke deaths to direct deaths roughly 50 to 200 | derived from C18, C19 per year
C21 | People on reserves were about 31 times more likely than people off reserve to live within 10 km of a fire of 1,000 ha or more in 2 or more of 2023 to 2026 (3.3% vs 0.11%) | threads/t4_*
C22 | Seven First Nation communities were within 10 km of fire in all four years (incl. Chemawawin, Kanaka Bar, Lake St. Martin) | threads/t4_fn_communities_years_exposed.csv

## Slide 6: property
C23 | Buildings likely destroyed (our Sentinel-2 estimate, calibrated on Jasper, CV precision 0.836, recall 0.832): 2023 844, 2024 417, 2025 405, 2026 517 (about 2,200 total) | property/
C24 | Bald Range 2026: 168 flagged vs about 150 official (District of Summerland) | property/estimates_2026_by_fire.csv, events_official.csv
C25 | 9,503 km of roads and 686 km of rail inside burned areas 2023 to 2026 | economy/infra_by_year.csv
C26 | Value of homes destroyed on official counts 2023 to 2026: $922 million (census value proxy) | property/destroyed_value_official.csv

## Slide 7: economy
C27 | Timber burned in 2023 valued at Crown stumpage: $7.44 billion nominal, 7.2 times the $1.03 billion stumpage Canada collected in 2023 | economic-value/timber_value_by_province_year.csv
C28 | Firefighting in BC, ON, AB, SK: $1.05 billion a year 2016 to 2022 vs $2.15 billion a year 2023 to 2025 (2025 dollars) | economic-value/cost_tally_by_year.csv
C29 | Total 2023 to 2026 including timber and smoke deaths valued: $43.2 billion; spending and losses only at least $10.35 billion | economic-value/cost_tally_by_year.csv
C30 | 2023 to 2026 burned 11.2 years of Canada's 2024 harvest (1,336 million m3 merchantable) | economy/

## Slide 8: environment
C31 | Canada's national emissions total excludes wildfire CO2; managed-forest wildfire emissions in 2023 were 870 Mt CO2e, 127% of the 686.9 Mt national total | threads/t1_official_inventory_lines.csv
C32 | Short-interval reburn (within 15 years) in black spruce and jack pine forest: 2.3% of burned area in the 1990s vs 7.5% in 2023 to 2026; 36,282 vs 343,906 ha a year | threads/
C33 | 14 federal boreal caribou ranges have more than 35% of their area burned by fire in 1987 to 2026 | wildlife/caribou_ranges_2026.csv

## Website extras
C34 | Thunder Bay fire area burned 12.8% of its forest in 2026, 88 times its 1991 to 2020 average, its highest on record | forest/fma_2026_table.csv
C35 | 9 fire areas set records on the scaled basis | forest/fma_2026_table.csv
C36 | Waskaganish (QC zone 50) burned 10.5% mapped (9.7% scaled), 110 times its average | forest/fma_2026_table.csv
C37 | 70.5% of 2026 satellite detections fell June 22 to July 26 | forest/hotspot_peak5.csv
C38 | 23 of BC's 466 community watersheds more than 10% burned 2023 to 2026; 29 population centres (106,904 people) in national watersheds more than 10% burned | threads/
C39 | Jasper visits 2024-25 down 53% vs pre-COVID baseline while all parks down 2.7% | economic-value/parks_fire_attendance.csv
C40 | Kamloops fire weather station: 118 extreme days in 2026 vs normal 59.6, a record | weather/
