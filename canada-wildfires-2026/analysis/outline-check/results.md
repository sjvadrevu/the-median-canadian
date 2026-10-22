# 2026 M3 outlines with no agency-reported fire: evidence check

Scope: the 80 CWFIS M3 2026 outlines (of 718) with no NRCan CWFIF 2026 fire-list point inside or within 5 km (`analysis/people/scripts/00b_flag_m3_agency_match.py`, column `agency_match` in `analysis/people/work/fires_2026.gpkg`). They total 49,257 ha (equal-area). Nothing was removed: all 718 outlines keep their geometry and get a class. Original analysis from raw official data only.

## Scorecard

| | Unmatched (80) | Matched sample (80) |
|---|---|---|
| Wildfire | 30 (40,266 ha) | 38 |
| Agricultural or grass burn | 9 (1,456 ha) | 0 |
| Military range | 4 (896 ha) | 0 |
| Industrial or urban heat | 0 | 1 |
| Unclear | 37 (6,640 ha) | 41 |
| Agency record in a provincial list (5 km) | 16 | n/a |

- 82% of the unmatched area (40,266 of 49,257 ha) classifies as wildfire on land cover and satellite evidence alone.
- Only 13 of 80 (2,352 ha, 4.8% of the unmatched area) look like non-wildfire burns: 9 agricultural or grass burns, 4 on military ranges.
- 16 of the 80 do have an agency record in a provincial dataset within 5 km. 14 are Ontario MNR in-year fire perimeters (12 overlap the outline, 2 are 0.7 and 4.5 km away), 1 is inside a Manitoba Wildfire Service perimeter and 1 is inside an Alberta Wildfire perimeter. The CWFIF list point for the same fire is 5 to 20 km away (it marks the fire's origin, while the M3 outline is a piece of the larger fire).
- The rule is conservative, not biased against unmatched outlines. It sends half of the matched sample to "unclear", almost all for the same reason as the unmatched: mostly natural cover with only 1 or 2 detection days. Non-wildfire classes are rare among matched outlines (1 of 80 in the sample, 5 of all 638) and much more common among unmatched (13 of 80).

## Rule (fixed before any evidence was computed)

Written in `scripts/rule.py` (2026-10-21) after only the data schemas had been inspected. Thresholds were not changed after results were seen. The class uses only physical evidence that is independent of agency lists. Agency records are reported in separate columns, which keeps the matched sample a fair test.

- Land cover: NRCan Land Cover of Canada 2020, 30 m, read in a window per outline (no decimation was needed). Shares are of land pixels (water excluded).
  - natural = forest (1, 2, 5, 6) + shrub (8, 11) + wetland (14) + northern grass/lichen (12, 13)
  - agri = cropland (15) + temperate grassland (10)
  - urban (17) and barren (16) are tracked separately
- Detection days: distinct UTC days with at least one deduplicated hotspot inside the outline. Dedupe keeps one record per sensor per 1 km Albers cell per UTC day.
- Season: month of the first deduplicated detection.
- DND share:
  - Alberta: overlap with Government of Alberta DND Military Base and Air Weapons Range polygons.
  - Elsewhere: a proxy. Each Directory of Federal Real Property (DFRP) National Defence parcel of 100 ha or more is drawn as a circle with the parcel's land area, centred on its point.

First match wins:

| Step | Class | Condition |
|---|---|---|
| R1 | military range | DND share >= 0.50 |
| R2 | possible industrial or urban heat | urban + barren(16) share >= 0.30 |
| R3 | wildfire (unreported in agency lists for the 80) | natural >= 0.60 and detection days >= 3 |
| R4 | likely agricultural or grass burn | agri >= 0.50, detection days <= 3, first detection in Mar to May or Sep to Nov |
| R5 | unclear | everything else; `class_detail` says which condition failed |

## Results for the 80 unmatched outlines

Area by class:

| Class | Outlines | Area (ha) | Share of area |
|---|---|---|---|
| Wildfire (unreported in agency lists) | 30 | 40,266 | 81.7% |
| Likely agricultural or grass burn | 9 | 1,456 | 3.0% |
| Military range | 4 | 896 | 1.8% |
| Unclear | 37 | 6,640 | 13.5% |
| Total | 80 | 49,257 | 100% |

Province breakdown (count; area in ha):

| Prov | Wildfire | Agri/grass | Military | Unclear | Total | Area |
|---|---|---|---|---|---|---|
| AB | 4 | 2 | 2 | 1 | 9 | 1,236 |
| BC | 1 | 0 | 0 | 2 | 3 | 750 |
| MB | 5 | 5 | 1 | 7 | 18 | 7,594 |
| NL | 4 | 0 | 0 | 1 | 5 | 7,392 |
| NT | 4 | 0 | 0 | 0 | 4 | 866 |
| NU | 5 | 0 | 0 | 5 | 10 | 18,012 |
| ON | 6 | 0 | 1 | 10 | 17 | 8,612 |
| QC | 0 | 0 | 0 | 3 | 3 | 429 |
| SK | 1 | 2 | 0 | 7 | 10 | 4,232 |
| YT | 0 | 0 | 0 | 1 | 1 | 136 |

Month of first outline date (count):

| Month | Wildfire | Agri/grass | Military | Unclear |
|---|---|---|---|---|
| Apr | 0 | 3 | 2 | 2 |
| May | 1 | 5 | 1 | 8 |
| Jun | 10 | 0 | 0 | 6 |
| Jul | 17 | 0 | 1 | 18 |
| Aug | 2 | 0 | 0 | 3 |
| Oct | 0 | 1 | 0 | 0 |

- Military range (4):
  - CFB Suffield and CFB Wainwright (Alberta polygons, share 1.0)
  - near CFB Shilo, MB, and Garrison Petawawa, ON (DFRP proxy, share 1.0)
- Agricultural or grass burn (9): AB 2, MB 5, SK 2. All in April, May or October, 57 to 97% cropland or prairie grassland, 1 or 2 detection days. Includes the outlines nearest Winnipeg (20.5 km), Calgary (27.0 km) and Brandon (20.8 km). The Calgary one is also an Alberta Wildfire "Mutual Aid" fire (CCU-002-2026, 168 ha, 2026-04-30).
- Wildfire (30): mostly June and July in boreal forest or wetland, with 3 to 9 detection days. The three largest are 10,662, 5,320 and 1,143 ha, recorded as province NU near the Manitoba border, 75 to 99% natural cover. Others are in northwestern Ontario inside MNR perimeters (6), Newfoundland and Labrador (4, 1,237 to 2,468 ha), northern Manitoba (4,654 ha, inside MB perimeter NO083) and northern Alberta (4, nearest CWFIF points in the High Level, Grande Prairie and Peace River forest areas, 8 to 27 km away).
- Unclear (37):
  - 31 are mostly natural cover with only 1 or 2 detection days. These look like small or short wildfires; 8 of them have an Ontario MNR perimeter within 5 km (6 overlapping).
  - 3 are mostly agricultural but detected in summer. One is the outline nearest Ottawa-Gatineau and Kanata (36076329): 70% cropland, 5 detection days spread from 12 June to 25 July.
  - 3 are mixed cover.
- Sensitivity to the hotspot source (see caveat 1): with the specified daily-file hotspots only, 7 unmatched outlines move from wildfire to unclear (23 wildfire, 44 unclear). No outline moves into or out of the agricultural or military classes.

Earlier `analysis/people/results.md` describes the 80 as "mainly spring prairie, farm and southern Ontario burns". This evidence does not support that. 52 of 80 start in June to August, only 9 are farm or grass burns, and of the 17 Ontario outlines, 15 are in the northwestern boreal forest (14 with an MNR perimeter within 5 km), 1 is at Petawawa and 1 (near Ottawa, 70% cropland) is unclear.

## Check of the rule on matched outlines

Matched sample: 80 random agency-matched outlines (seed 20261021), stratified to the size quintiles of the unmatched set, 16 per bin. Province and month are not matched, because few agency-matched outlines are spring prairie fires.

| Class | Matched sample (80) | All matched (638) |
|---|---|---|
| Wildfire | 38 | 473 (5,104,530 ha) |
| Unclear | 41 | 160 (139,626 ha) |
| Agri/grass | 0 | 1 |
| Military | 0 | 2 |
| Industrial/urban | 1 | 2 |

- Specificity: non-wildfire classes hit 1 of 80 sampled and 5 of 638 matched (0.8%). Two of those 5 are agency-listed fires on CFB Gagetown (NB), which shows that "military range" describes location, not cause. The others are a 164 ha Saskatchewan fire on 66% cropland, an NT outline with 32% barren land, and a 178 ha BC outline near Comox (39% urban or barren).
- Sensitivity: low for small fires. 38 of the 41 unclear in the sample are "mostly natural cover, 1 or 2 detection days". The median sample outline is 143 ha with 3 detection days; the median unmatched outline is 138 ha with 2. So "unclear" in the 80 should be read as "too little satellite evidence to call", not as "not a fire".
- The unmatched set differs from the size-matched sample mainly in the 13 agricultural or military outlines (16% against 0%) and in somewhat less forest (median forest share 0.52 against 0.81).

## Agency records (reported, not used in the class)

For every outline the CSV gives the nearest record in each source, with ID, distance, date, gap in days to the outline's dates, and a note:
- CWFIF fire list: all years, including size, cause and prescribed flag
- BC Wildfire Service 2026 perimeters
- Ontario MNR in-year perimeters
- Manitoba Wildfire Service perimeters
- Alberta Wildfire perimeters
- Quebec SOPFEU/MSP 2026 points
- NWT 2026 points

Point sources count as a match only within 5 km and within 30 days of the outline's dates; polygon sources (all 2026) only need to be within 5 km. CNFDB points end in 2025 (version 20260811), so there are no 2026 records. Among the 638 matched outlines, 131 have their nearest CWFIF point more than 30 days from the outline dates. The original 5 km match had no date condition, so some matches may be coincidental.

## Caveats

1. **Hotspot file gap.** The specified file (`cwfis_hotspots_2026_canada.csv.gz`, from the CWFIS daily CSVs) is missing most VIIRS records for 29 June to 2 July 2026, plus scattered others such as 7 May in southern Manitoba. 39 of 718 outlines, mostly in Quebec, had zero detections inside them despite M3 HCOUNT > 0. The same publisher's WFS archive (`public:hotspots`) holds those records. It was downloaded for 2026 (1,352,431 rows, `scripts/03_fetch_wfs_hotspots.py`) and the class uses the deduplicated union: 274,507 detections inside outlines against 173,299 from the file alone. The archive also adds a third sensor, Sentinel-3 SLSTR. Five outlines still have zero detections inside. Both versions of the class are in the CSV (`class`, `class_file_only`).
2. **DND land outside Alberta is a proxy.** No national DND boundary layer was found: the CLSS services, open.canada.ca and the DFRP map service (503) were all tried. DFRP gives one point and a land area per parcel. Circles of equal area misplace irregular bases, so DND shares outside Alberta are approximate. Outline 36076456 (MB, 66.8 ha, April, 90% grassland) is 2.4 km from a CFB Shilo parcel point, scored DND share 0 and was classed agricultural or grass burn; it may be on the Shilo range.
3. **"Military range" and "agricultural burn" describe setting and timing, not cause.** No source here records ignition cause for unmatched outlines.
4. Land cover is from 2020, so post-2020 fire scars, clearing and new fields are not reflected.
5. Nunavut outlines are labelled NU by M3 (`prov`). The large ones sit near the Manitoba boundary in forest. Nunavut has no wildfire agency list, which alone explains some non-matches.
6. The 3-detection-day threshold misses short fires, as the matched check shows. The thresholds were kept as pre-registered.
7. Hotspot `rep_date` is treated as UTC (as in the data manifest).

## Files

- `outline_evidence.csv`: 160 rows (80 unmatched and 80 matched sample), 92 columns covering every evidence item and the class.
- `work/evidence_all_718.csv`: the same columns for all 718 outlines.
- `outline_class_2026.geojson`: all 718 outlines with `class`, `class_detail`, `matched`, `group` and key evidence. Simplified to 100 m, WGS84, 1.2 MB.
- `manifest.csv`: new data (DFRP, Alberta DND polygons, WFS hotspot archive) and the national DND layer that was not found.
- `scripts/`:
  - `rule.py`: the pre-registered rule
  - `01_dfrp_dnd.py`: extracts the DND parcels
  - `02_evidence.py`: computes the evidence and classifies
  - `03_fetch_wfs_hotspots.py`: downloads the WFS hotspot archive
  - `04_summary.py`: builds the tables (output in `work/04_summary.md`)
- Run order: 01, 03, 02, 04.
