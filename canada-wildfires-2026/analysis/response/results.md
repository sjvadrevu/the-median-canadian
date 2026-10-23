# Did the 2023 to 2026 area burned come from fires that were not caught early?

Original analysis of raw official data only: CNFDB fire points (NFDB_point_20260811), the 2026 national agency fire list (CWFIS/CWFIF, as of 2026-10-20), NFD official totals, NBAC 2023 to 2025, CWFIS M3 2026 outlines and the CWFIS 2026 hotspot archive, StatCan National Road Network, and agency zone polygons (sources below). No news or prior analysis was used. Run 2026-10-22. Scripts: `scripts/run_all.sh` (01 to 09).

## Headline findings

1. **About half of the 2023 to 2026 area came from fires that were not under full suppression.** Of 35.90 M ha (official totals), 17.63 M ha (49.1%) came from fires the agencies labelled modified or monitored response, or that started in an observation zone (Quebec northern zone, Yukon strategic/transitional/wilderness zones). 12.20 M ha (34.0%) came from full-suppression fires. 6.07 M ha (16.9%) has no label, 96% of it Saskatchewan 2023 to 2025. The not-full share is 49% to 66% depending on how the unlabelled area falls, and 59% of the labelled area.
2. **2026 is the one year with a label on every fire:** 69.8% of the official 4.49 M ha came from modified (13.1%) or monitored (56.7%) fires; 30.2% from full-response fires. Saskatchewan's 2026 area was 91% modified response.
3. **Where policy is to watch, almost all area is watch-and-protect.** Not-full share of 2023 to 2026 area: Yukon 94%, NWT 90%, Quebec 78%, Manitoba 50%, Ontario 43%, BC 28%, Alberta 14% (mostly national-park fires). The polygon check agrees: 77.7% of Quebec's area burned in SOPFEU's northern zone, 94.5% of Yukon's in the strategic/transitional/wilderness zones, 53.5% of Ontario's in the pre-2014 Hudson Bay and Northern Boreal zones (plus 20.0% in the Parks zone), and 19.8% of Alberta's outside the Forest Protection Area.
4. **Full suppression usually works, but the escapes are a third of the total.** 90.2% of full-suppression fires (2023 to 2026) were held under 10 ha. Yet those fires still burned 12.20 M ha, and 90.7% of that came from 197 fires of 10,000 ha or more.
5. **Fast growth is the common thread.** In 2026, fires that passed an estimated 1,000 ha within 72 hours of first satellite detection produced 69.3% of the mapped area (80.4% when timed from the start of each outline's main burning run). Within 24 hours: 28.8% (45.8%). An independent check from archived M3 outline versions gives 56.9% within 72 hours. 98.1% of mapped 2026 area came from outlines that ended over 1,000 ha.
6. **Late detection explains little.** For 3,635 fires with both dates (2023 to 2026), the agency date was the same day as, or earlier than, the first satellite hotspot for 77.5% of area. The agency date was 3 or more days after the first hotspot for 12.4% of area, concentrated in Saskatchewan (29.3%), NWT (21.4%) and Yukon (16.5%).
7. **Remoteness matters for area, not for fire counts.** 69.6% of 2023 to 2026 area came from fires that started more than 10 km from any mapped road, 47.6% more than 25 km and 21.1% more than 50 km. Only 23.3%, 13.0% and 6.3% of fires started that far out. Of the area from fires starting over 50 km from a road, 75.5% was monitored or in an observation zone and 0.9% was full response.
8. **Early control is slipping for lightning fires.** The share of all fires held under 10 ha fell from 89.6% (1990s average) to 84.7% (2016 to 2025), -2.1 points per decade (p < 0.001). For lightning fires it fell from 85.3% to 75.1% (-4.8 points per decade, p < 0.001); for human fires it did not fall (93.3% to 94.2%). Among full-response fires (agencies that record response), the share held under 10 ha fell 1.4 points per decade (p = 0.004) and the share of their area from fires of 10,000 ha or more rose from 46% to 73% (p = 0.01).
9. **Area is always concentrated in a few fires.** The largest 1% of fires (233) burned 69.7% of 2023 to 2026 area; the largest 5% burned 96.1%. Nationally, fires of 10,000 ha or more made up 73% of area in the 1990s and 75% in 2016 to 2025 (no significant trend, p = 0.21); 2023 was 91%.
10. **Spending per hectare (note only, existing file):** provincial firefighting spending (AB, BC, ON, SK; 2025 dollars) per official hectare burned was $295 in 2023, $667 in 2024 and $416 in 2025, against $730 to $813 in 2016 to 2019.

**What this means for the bottom line.** The data partly support the idea. Roughly half to two-thirds of 2023 to 2026 area came from fires that agencies chose to monitor or manage rather than fully suppress, mostly in the NWT, northern Quebec, Yukon, Manitoba and very likely Saskatchewan, and these fires started far from roads. The rest is not a detection problem: about a third of the area came from full-suppression fires, a small number of which grew past 1,000 ha within one to three days of first detection. Detection delay accounts for a small share. The data do not say whether more suppression in remote zones was possible or worthwhile.

## Method

**Response class (scripts 02, 03, 03b).** Each agency fire point carries the agency's own label: CNFDB `RESPONSE` (BC, MB, NT, ON, Parks Canada, NS, PE: FUL/SUP = full, MOD/MDP = modified, MON/MNP = monitored), CNFDB `PROTZONE` where there is no response field (QC Intensive vs Nordique; YT Critical/Full vs Strategic/Transitional/Wilderness), and the 2026 list's `response_type` for all agencies. Alberta Wildfire records (FPA only) have no response field in CNFDB; they are counted as suppression because Alberta Wildfire's 2026 list labels 798 of 798 fires full response. Each province-year's share by class (agency final sizes) is applied to the official total (NFD 2023 to 2025; 2026 agency list, calendar-2026 fires, 4,493,606 ha). Parks Canada fires are counted in the province they lie in. A separate polygon check overlays official zone polygons on the mapped burn grids (NBAC 2023 to 2025, M3 2026, 240 m) and scales to official totals.

**Speed of escape (04).** 705 M3 2026 outlines (13 farm/grass/military outlines with no agency fire dropped). First detection = M3 FIRSTDATE. Every hotspot (WFS archive, all sensors) inside the outline after that is snapped to a 400 m cell; estimated area at time t = final outline area x share of the outline's cells detected by t. Second timing ("main run") starts at the run of detections that adds the most cells, after splitting at gaps of more than 7 days; this removes early holdover or unrelated detections that a merged outline swallowed. Cross-check: first archived M3 version of the fire at 1,000 ha or more.

**Detection lag (05).** NBAC 2023 to 2025: agency start date (AG_SDATE) minus first hotspot date (HS_SDATE), whole days. 2026: earliest agency report date of the list points inside each M3 outline minus M3 FIRSTDATE.

**Access (06).** Distance from the agency fire point to the nearest NRN road vertex (all classes, including resource/recreation and winter roads, densified to 200 m). Area weights as in 03. A no-winter-road version and a 2026 first-hotspot version are in the CSVs.

**Early control (07).** CNFDB 1990 to 2025 and the 2026 list, prescribed burns removed; share of fires with final size under 1 ha and under 10 ha, share of area from fires of 10,000 ha or more. Theil-Sen slope, Kendall p, 1990 to 2025.

## Per-province table (2023 to 2026)

| Prov | Official ha | Not full | No label | Area >25 km from road | Agency date 3+ d after hotspot | 2026: 1,000 ha in 72 h* | Fires <10 ha, 1990s / 2016-25 |
|---|---|---|---|---|---|---|---|
| NT | 8.87 M | 90% | 0% | 64% | 21% | 74% / 86% | 70% / 45% (p<0.001) |
| SK | 6.10 M | 4% | 95% | 33% | 29% | 73% / 85% | 85% / 76% (p=0.001) |
| QC | 5.30 M | 78% | 0% | 68% | 1% | 72% / 72% | 90% / 88% (n.s.) |
| BC | 5.01 M | 28% | 3% | 43% | 7% | 20% / 79% | 95% / 88% (p<0.001) |
| AB | 4.70 M | 14% | 0% | 28% | 4% | 87% / 87% | 92% / 93% (n.s.) |
| MB | 2.87 M | 50% | 0% | 29% | 5% | 73% / 73% | 75% / 64% (p=0.02) |
| ON | 1.88 M | 43% | 0% | 41% | 4% | 75% / 78% | 90% / 88% (n.s.) |
| YT | 0.92 M | 94% | 0% | 59% | 17% | 15% / 15% | 72% / 54% (p<0.001) |
| NL | 0.20 M | 48% | 49% | 67% | 7% | 85% / 86% | 86% / 87% (n.s.) |

\* Share of the province's mapped 2026 area from fires past 1,000 ha within 72 hours: from first detection / from main-run start. NS, NB, PE and NU have under 40,000 ha in total. Full columns: `province_summary.csv`.

## Response-zone boundaries found

| Province | What was found | Source | Used as |
|---|---|---|---|
| QC | SOPFEU intensive protection zone and northern zone | https://www.sopfeu.qc.ca/layers/limite-intensive.json (already local, `data/geo/mb_qc_subareas/qc_sopfeu_protection_zones.gpkg`) | Polygon check; CNFDB PROTZONE for 2023 to 2024 labels |
| ON | Historical fire management zones (6 zones, in force before the 2014 strategy, which replaced zones with fire-by-fire response) | https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open09/MapServer/32 (`raw/zones/on_fire_management_zones_hist.geojson`) | Polygon check only (current policy has no zones) |
| YT | Fire management zones (Critical, Full, Strategic, Transitional, Wilderness), 2020 | https://map-data.service.yukon.ca/GeoYukon/Emergency_Management/Fire_Management_Zones/Fire_Management_Zones.shp.zip | Polygon check; CNFDB PROTZONE labels |
| AB | Forest Protection Area (10 forest areas) | Alberta Wildfire forest area boundary MapServer (already local, `data/geo/raw/ab_forest_areas.geojson`) | Polygon check |
| SK | Not obtained. The SPSA layer "Strategies (Protection Features & Areas)" (zones: Primary Timber, Secondary Timber, Northern Area, others) is listed at gistest.saskatchewan.ca/arcgis/rest/services/SPSA/Applications/MapServer/5 but returns "Service not found" from shell and WebFetch; the public gis.saskatchewan.ca SPSA folder has only Protection Areas and Communities | (blocked) | 2026 list labels only |
| MB | No polygon published (found in the earlier step too); zone and response are attributes on each CNFDB record | CNFDB | Labels |
| NT | No zone layer in GNWT geomatics services | CNFDB, 2026 list | Labels |
| BC | No zone layer; BC assigns response fire by fire | CNFDB, 2026 list | Labels |
| NL | None found | 2026 list | Labels (2026 only) |

## Limits that change a finding

- **Saskatchewan 2023 to 2025 (5.80 M ha) has no response label**, which is why the national not-full share is a 49% to 66% range. Its 2026 area was 91% modified response, so the upper end is plausible but not shown by data.
- **"Modified" and "monitored" are the agency's response category, not "no action".** Modified fires often receive partial suppression. The split measures policy intent, not effort.
- **Agency start date (NBAC AG_SDATE) is not always the report date.** Some agencies record an estimated ignition date, which would make lags look shorter. The 2026 list date is the situation-report date. So the 12% figure is a lower-bound style estimate of late detection, not an exact one.
- **Escape timing is estimated from hotspot cells**, not from mapped daily perimeters (the CWFIS progression file starts too late in the season to use). Clouds and smoke delay detections, which makes growth look slower, so the 1,000 ha within 72 hours shares lean low.
- **NRN does not hold every forestry road.** Distances are to the nearest mapped public or resource road; missing logging roads would lower the remote shares in BC, AB, SK and ON.

## Files

- `zone_share_national.csv`, `zone_share_province_2023_2026.csv`, `zone_share_agency_by_prov_year.csv`, `zone_share_polygons_by_prov_year.csv`, `escaped_despite_full.csv`
- `escape_speed_2026_fires.csv`, `escape_speed_2026_summary.csv`, `size_concentration.csv`
- `detection_lag_fires.csv`, `detection_lag_summary.csv`
- `access_by_prov_year.csv`, `access_by_response.csv`, `access_m3_2026.csv`
- `early_control_by_year.csv`, `early_control_trends.csv`
- `cost_per_ha_note.csv`, `province_summary.csv`
- `raw/zones/` (Ontario and Yukon zone downloads), `work/` (road vertices, fire table, logs)
