# CFB Wainwright fire, October 17, 2026: original analysis from raw official data

Official facts used only as context (Department of National Defence release, Oct 18, 2026): fire ignited about 4 p.m. MDT on Oct 17 during live-fire training (Exercise APOLLO SHOOTER) at CFB Wainwright; high winds spread it rapidly, over the unit administrative area and beyond the base; 4 CAF members killed, 39 injured. No news numbers are used below. Every number comes from the files listed.

Time zones: CWFIS hotspot times are UTC. ECCC hourly "local" times are local standard time (LST = UTC-7), one hour behind MDT. Both are converted to MDT in the text.

## Scorecard

| Question | Finding |
|---|---|
| Satellite record | 8 VIIRS hotspots at 2:49 p.m. MDT Oct 17 (one overpass), 1 at 2:32 p.m. MDT Oct 18. Nothing else Oct 17 to 22. |
| Official perimeter | None. No CWFIS M3 outline (file of Oct 22). Alberta Wildfire has a point record only (RMD-001-2026, 40 ha estimate). |
| Area burned (ESTIMATE) | About 1,090 ha from Sentinel-2 (range 670 to 1,160 ha), 6.3 km long, oriented WNW to ESE. |
| Beyond the base (ESTIMATE) | About 95 ha outside the Alberta DND polygon (range 21 to 110 ha), reaching about 1.1 km past the boundary (0.9 to 1.4 km). |
| Weather at the fire hour | A cold front reached Wainwright between 3 and 4 p.m. MDT: wind 32 to 48 km/h, gust 82 km/h, after a 23.3 C, 16% RH afternoon. |
| How rare for mid-October | Highest daily gust in 31 years of Oct 10 to 24 days at Wainwright; 2nd strongest afternoon wind; 2nd lowest afternoon RH; largest one-hour temperature drop. |
| Fire danger (noon FWI) | FFMC 91.8 (6th highest of 420 mid-October days); FWI 30.8 (rank 64 of 366, 83rd percentile). The noon index misses the afternoon wind. |
| Background dryness | No drought: the Canadian Drought Monitor shows no class at the fire in any month April to September 2026. June to mid-October precipitation was 121% of normal at Wainwright. The fall was mild: no night at or below -2 C by Oct 17, a first in 27 years. |
| Military areas burning | Wainwright burned in 25 of 35 years (1991 to 2025) in NBAC. 39% of its satellite fire episodes (2003 to 2026) start in fall, and October detections occur in 13 of 24 years. |
| October fires nationally | No national trend in the October share of fires (CNFDB 1990-2025, p = 0.97) or of hotspots (MODIS 2003-2026). Alberta's October fire count is rising (p = 0.05). 2026 had the lowest Sep 1 to Oct 22 hotspot share in 24 years (1.5%). |

## 1. The fire itself

### Satellite hotspots, Oct 10 to 22, 2026

Source: CWFIS WFS hotspot archive (`public:hotspots`), box 52.2 to 53.3 N, 111.8 to 110.0 W, all records since Oct 10 (`raw/wfs_hotspots_wainwright_20261010_on.csv`, 12 records).

- Oct 17, 20:49 UTC (2:49 p.m. MDT): 8 VIIRS I-band detections from NOAA-20, all inside the CFB Wainwright polygon, between 52.769 and 52.788 N and 110.928 and 110.902 W (about 2.2 km north to south and 1.8 km east to west). They are 1.8 to 3.6 km inside the base boundary. Fire radiative power was 5.8 to 11.5 MW per pixel.
- This detection is about 70 minutes before the "about 4 p.m." time in the DND release. The Alberta Wildfire record (below) gives 4:00 p.m. MDT for assessment or assistance. The data cannot say whether the 2:49 p.m. detections were the same fire or range fires burning earlier in the afternoon. They lie in the northwest part of the later burn scar.
- Oct 18, 20:32 UTC (2:32 p.m. MDT): 1 VIIRS detection (NOAA-20) at 52.7467 N, 110.8654 W, 630 m outside the Alberta DND polygon and inside the eastern end of the mapped scar.
- Oct 14, 20:51 UTC: 1 VIIRS detection (NOAA-21) at 52.7549 N, 110.9389 W, inside the base, near the southwest end of the later scar.
- Oct 20: 2 detections near 53.17 N, 110.09 W, 60 km from the base, unrelated.
- No other detections Oct 17 to 22 in the box (no night-time VIIRS, MODIS or Sentinel-3 detections). A fast grass fire can start and burn out between overpasses, so the hotspot record shows only a snapshot of the fire.
- CWFIS interpolated conditions attached to the Oct 17 detections: 19.8 C, RH 23%, wind 16.8 km/h, FFMC 91.8, ISI 12.9, FWI 34.4, fuel type D1, grass curing 70%. These are the CWFIS noon values, not the conditions at the fire hour.

### Perimeters

- CWFIS FireM3 perimeters, refreshed file of 2026-10-22 15:15 UTC (`raw/m3_20261022/`): no outline for this fire. The only 2026 outline at Wainwright is UID 36166192 (88 ha, Apr 21 to May 1).
- The CWFIS daily FireM3 hotspot CSVs for Oct 17 to 22 (`raw/cwfis_daily/`) have no records in the box, although the WFS archive has the 9 detections above. The Oct 17 detections never entered the M3 product, so no M3 outline exists.
- Alberta Wildfire ArcGIS feeds, 12 layers queried (`raw/ab_feed/`): no active or extinguished perimeter polygon. There is one point record in Active_Mutual_Aid_Wildfires and wildfire_location_non_active: RMD-001-2026, fire type "Mutual Aid", 52.772633 N, 110.934717 W, AREA_ESTIMATE 40 ha, size class C, assessment/assistance date 2026-10-17 22:00 UTC (4:00 p.m. MDT), status "Assistance Ended" at 2026-10-20 10:02. This 40 ha figure is the only official area value. It is far below the satellite-mapped scar, which suggests it is an early or partial estimate. The feed does not say.

### Estimated area burned (ESTIMATE, no official perimeter)

Method (`scripts/01_s2_read.py` to `04_burn_map.py`, `15_burn_geometry.py`):
- Sentinel-2 L2A, tile 12UWD, 20 m. Pre-fire 2026-10-04 (2.5% cloud). Post-fire 2026-10-19 (S2B). The 2026-10-21 scene was checked, but the fire is outside its swath.
- dNBR = NBR(Oct 4) minus NBR(Oct 19), NBR = (B8A - B12)/(B8A + B12). Cloud, shadow, snow and water pixels (SCL) are masked. A 2 x 2 opening is applied. Kept: 8-connected patches of dNBR at or above the threshold that touch, within 300 m, the Oct 17 or 18 detections or the Alberta point.
- The 2026-10-14 scene (before the fire, partly cloudy) shows no scar: of the 62% of the mapped scar that was clear on Oct 14, only 0.3% already had dNBR of 0.27 or more. The scar therefore formed after 18:39 UTC Oct 14. One VIIRS detection at 20:51 UTC Oct 14 lies near the scar's southwest end, so a small part burned on Oct 14 cannot be ruled out.

| dNBR threshold | Area (ha) | Inside base (ha) | Outside base (ha) | Max distance beyond boundary |
|---|---|---|---|---|
| 0.10 | not usable (leaks into unburned land, 13,904 ha) | | | |
| 0.20 | 1,161 | 1,051 | 110 | 1.4 km |
| 0.27 (main) | 1,089 | 994 | 95 | 1.1 km |
| 0.44 | 673 | 652 | 21 | 0.9 km |

- Main estimate: about 1,090 ha (range 670 to 1,160 ha), median dNBR 0.47. The scar runs 6.3 km on a bearing of 112 degrees (WNW to ESE), from 52.789 N 110.945 W to 52.741 N 110.859 W. Its far end is 5.4 km from the centre of the 2:49 p.m. hotspot cluster.
- Beyond the base: the burn crosses the east edge of the Alberta "C.F.B. Wainwright" polygon, onto land between the two base polygons, south of the town. About 95 ha (range 21 to 110 ha) lies outside, up to about 1.1 km (0.9 to 1.4 km) past the boundary. The Alberta layer is the only official boundary used. Whether that land is DND-owned (for example cantonment land) cannot be told from it.
- Uncertainty: thin cloud covered the area east of the boundary on Oct 19 (masked pixels in a 500 m ring around the burn: 3.9%). Unmasked haze can lower or raise dNBR there, so the outside area is the least certain part. A small water-margin area near the lake is excluded by the water mask. Cured grass gives lower dNBR than forest, so lightly burned grass may be missed at 0.27.
- Files: `burn_estimate.csv`, `burn_geometry.csv`, `burn_estimate_T27.geojson`, `burn_outside_base_T27.geojson`, `burn_map.png`, `work/burn_T*.gpkg`.

Other 2026 fall burning nearby: on Sep 20, 2026, 22 detections (MODIS and VIIRS) fell inside the base 1.2 km south of the Oct 17 scar. This is the dark scar south of the lake already visible on the Oct 4 image. On Oct 7, 2025, there were 83 detections in the southeast of the training area.

## 2. Conditions on October 17

### Hourly observations (ECCC climate-hourly; times converted to MDT)

WAINWRIGHT CFB AIRFIELD 21 (301S001), about 15 km west-northwest of the burn:

| MDT | Temp C | RH % | Wind dir (deg) | Wind km/h |
|---|---|---|---|---|
| 1 p.m. | 20.2 | 23 | 220 | 15 |
| 2 p.m. | 22.8 | 16 | 230 | 30 |
| 3 p.m. | 23.3 | 17 | 240 | 32 |
| 4 p.m. | 12.9 | 43 | 310 | 48 |
| 5 p.m. | 12.0 | 42 | 310 | 42 |
| 6 p.m. | 11.1 | 44 | 310 | 31 |
| 7 p.m. | 10.3 | 44 | 300 | 29 |

- A cold front passed Wainwright between the 3 p.m. and 4 p.m. MDT observations. The wind turned from southwest (240 deg) to northwest (310 deg) and rose from 32 to 48 km/h. Temperature fell 10.4 C in one hour and RH rose from 17% to 43%. The daily maximum gust was 82 km/h from 270 deg. No precipitation fell.
- Ignition at about 4 p.m. MDT coincides with the front's arrival. A northwest wind fits the burn scar's WNW to ESE orientation (long axis 112 deg).
- The same front reached the other stations at nearly the same time. Hourly wind jumped to 63 km/h at Lloydminster and 54 to 57 km/h at Coronation (4 and 5 p.m. MDT), and to 62 km/h at Vegreville (3 p.m. MDT). Daily maximum gusts: Vegreville 100 km/h, Lloydminster 98, Coronation 95, Wainwright 82, Ranfurly 72 (`weather_oct17_hourly.csv`).

### Rank against every mid-October day and against summer (`weather_oct17_ranks.csv`)

"Mid-October" means every Oct 10 to 24 day of earlier years at that station. "Summer" means every Jun 1 to Aug 31 day, 2026 included. Afternoon means 11 a.m. to 6 p.m. MDT.

| Station / metric | Oct 17 | Mid-October rank (days, years) | Summer percentile |
|---|---|---|---|
| Wainwright daily max gust | 82 km/h | 1st of 429 (1995-2025); previous max 74 (Oct 24, 1999) | 99.6 (rank 10 of 2,783) |
| Wainwright afternoon max hourly wind | 48 km/h | 2nd of 458 (1995-2025); max 56 (Oct 24, 1999) | 99.7 |
| Wainwright afternoon min RH | 16% | 2nd lowest of 457; lowest 11% (Oct 17, 2018) | 99.3 |
| Wainwright one-hour temperature drop | 10.4 C | 1st of 441; previous max 8.4 C | 99.9 |
| Wainwright daily max temperature | 23.3 C | 10th of 417 | 48th (a typical summer day) |
| Vegreville daily max gust | 100 km/h | 1st of 265 (2008-2025) | 100 (highest of 1,737 summer days) |
| Lloydminster daily max gust | 98 km/h | 1st of 226 (2010-2025) | 99.9 |
| Coronation daily max gust | 95 km/h | 3rd of 327 (2004-2025) | 99.7 |
| Ranfurly daily max gust | 72 km/h | 3rd of 177 (2014-2025) | 99.4 |

### Fire Weather Index (CWFIS station data, noon LST observation)

Wainwright CFB on Oct 17: temperature 20.2 C, RH 23%, wind 14.7 km/h, FFMC 91.8, ISI 11.6, FWI 30.8, BUI 77.6, DC 461.5.

| Index | Mid-October rank (Wainwright, 1995-2025) | Percentile among mid-October days | Summer percentile |
|---|---|---|---|
| FFMC 91.8 | 6th of 420 | 98.8 | 88.4 |
| ISI 11.6 | 54th of 366 | 85.2 | 83.4 |
| FWI 30.8 | 64th of 366 | 82.5 | 85.2 |
| BUI 77.6 | 208th of 366 | 43.2 | 75.5 |
| DC 461.5 | 250th of 420 | 40.7 | 71.2 |

- Neighbouring CWFIS stations agree. Hughenden AGCM (22 km): FFMC 91.7 (2nd of 215 mid-October days, 2008-2025), FWI 36.4 (88.9th percentile). Edgerton AGCM (32 km): FFMC 90.7 (8th of 224).
- The CWFIS daily FWI grid (2 km) at the fire point gives FWI 35 on Oct 17: 12th of 120 mid-October days 2018-2025 (90th percentile) and 93rd percentile of summer days (`work/fwi_grid_at_fire.csv`).
- Fine fuels were near their driest for the season (FFMC). Deep fuels (BUI, DC) were ordinary for mid-October. The noon indices use the noon wind of 14.7 km/h and do not capture the front.
- ILLUSTRATIVE ESTIMATE, not an official value: recomputing ISI with the noon FFMC (91.8) and the 4 p.m. MDT wind (48 km/h) gives ISI about 62 and FWI about 88. That is close to the highest noon FWI in any Wainwright summer (91.9, Aug 23, 2001); the mid-October maximum is 131.8 (Oct 24, 1999). The 3 p.m. MDT wind of 32 km/h gives ISI 28 and FWI 54 (`work/isi_afternoon_illustrative.csv`). The front also raised RH, which would lower the hourly FFMC, so these values are upper-bound illustrations.

### Days since rain (`weather_rain_freeze.csv`, daily totals to Oct 16)

| Station | Last day with 1 mm or more | Last day with 5 mm or more | Last day with 10 mm or more |
|---|---|---|---|
| Wainwright CFB | Oct 8 (9 days) | Sep 10 (37 days) | Sep 7 (40 days) |
| Fabyan | Oct 10 (7 days) | Sep 25 (22 days) | Sep 7 (40 days) |
| Lloydminster | Oct 10 (7 days) | Aug 23 (55 days) | Aug 23 (55 days) |
| Coronation | Oct 11 (6 days) | Sep 7 (40 days) | Sep 7 (40 days) |

Wainwright had only light rain (0.2 to under 1 mm) after Oct 8, the last on Oct 12. Fabyan has 22 missing precipitation days between Aug 1 and Oct 16.

## 3. Background dryness

### Canadian Drought Monitor (`drought_wainwright.csv`)

- 2026: no drought class (not even D0, abnormally dry) at the fire point in any month from April to September. In August, D0 covered 15.8% of the base polygon. In September, none of it.
- Earlier years at the fire point: August was D1 or worse in 5 of 22 years (2008, 2009, 2015, 2021, 2023) and D0 or worse in 9. September was D1 or worse in 4 of 23 years (2009 D3, 2021, 2023, 2025 D2) and D0 or worse in 8.
- 2026 was among the non-drought years. The fire was not preceded by a seasonal drought.

### Precipitation June 1 to October 16 (`weather_precip_jun_oct.csv`)

| Station | 2026 (mm) | Baseline mean (mm) | % of baseline | Rank (1 = driest) |
|---|---|---|---|---|
| Lloydminster A (3013961) | 355.4 | 263.5 (1991-2020, 28 complete years) | 135% | 39th of 43 (1982-2026) |
| Wainwright CFB (301S001) | 236.1 | 195.7 (1998-2018, 17 complete years) | 121% | 17th of 22 |

- The wet total comes from June: Wainwright had 106.5 mm vs 56.3 normal and Lloydminster 138.6 vs 83.8. July and August were near or below normal at Wainwright (51.2 vs 55.7; 36.9 vs 48.8). September was above normal at Wainwright (38.0 vs 25.2) and below at Lloydminster (21.8 vs 33.7). Oct 1 to 16 was below normal at both (3.5 vs 9.7; 6.4 vs 10.5).
- Fabyan (record from 1966), Coronation and Monitor have more than 5% of days missing in the 2026 window and are not ranked.

### Freeze and snow timing (grass curing context; `weather_freeze_by_oct17.csv`)

- Lowest minimum temperature from Aug 15 to Oct 17, 2026: Wainwright -1.6 C, the mildest in 27 complete years (1996-2025). The median of earlier years is -7.5 C. Every earlier year had reached -2 C or lower by Oct 17. Lloydminster A: -1.5 C, also the mildest of 43 years (median -7.2 C). Coronation reached -5.8 C (4th mildest of 29).
- First frost (0 C or below) at Wainwright came on Sep 27, 2026. The median first-frost day in earlier years is day 265 (Sep 22).
- Snow: no snow on the ground at any station Sep 1 to Oct 17. Snowfall was 0 except 0.8 cm at Monitor.
- CWFIS assigned 70% grass curing to the Oct 17 detections. No hard freeze had occurred. The data do not measure the curing state of the training-area grass directly.

## 4. How often military training areas burn

Boundaries (`scripts/10_bases.py`, `work/bases.gpkg`). Official polygons: Wainwright and Suffield (Government of Alberta DND layer), Gagetown (GeoNB, from PWGSC), Petawawa and Meaford (Ontario LIO "Federal Land Other", Military Base). Shilo, Dundurn and Valcartier are PROXIES, because no official polygon was found: each DFRP DND parcel is drawn as a circle of its land area. Results for those three are approximate.

### Mapped burns: NBAC 1972-2025 and CWFIS M3 2026 (`base_burns_summary.csv`, `base_burns_by_year.csv`, `base_burns_fires.csv`)

| Base | Area (ha) | NBAC fires | Years with a burn | Burned area inside (ha, cumulative) | 2026 M3 outlines |
|---|---|---|---|---|---|
| Wainwright | 61,384 | 64 | 25 (1991-2025) | 121,736 | 1 (113 ha, April) |
| Gagetown | 109,815 | 24 | 13 | 28,533 | 2 (7,126 ha, spring) |
| Shilo (proxy) | 34,687 | 10 | 10 | 15,510 | 1 (480 ha, spring) |
| Petawawa | 37,843 | 14 | 9 | 5,428 | 1 (110 ha, spring) |
| Suffield | 265,594 | 2 | 2 | 1,058 | 1 (193 ha, summer) |
| Dundurn (proxy) | 23,591 | 1 | 1 | 1,014 | 0 |
| Valcartier (proxy) | 15,867 | 1 | 1 | 2 | 0 |
| Meaford | 7,344 | 0 | 0 | 0 | 0 |

- Wainwright is the most-burned base by far. NBAC maps burns there in 25 of the 35 years from 1991 to 2025, about 3,500 ha a year on average, or about 2 times the base's area in total over 35 years. The largest years are 1998 (15,755 ha), 2002 (14,145 ha), 2001 (12,838 ha) and 2018 (10,363 ha).
- NBAC has start dates for only 6 of the 64 Wainwright fires (4 spring, 2 fall), so it cannot give a season split there. NBAC under-maps prairie grass fires: Suffield, a grassland range, has only 2 NBAC polygons.
- CNFDB fire points inside the bases (agency reports) exist only for Gagetown (26), Petawawa (33), Shilo (12) and Valcartier (33). None exist for Wainwright, Suffield, Dundurn or Meaford, which suggests DND range fires on those bases are not in the national agency record.

### Satellite fire activity by season (CWFIS hotspot archive; `base_hotspots_summary.csv`, `base_hotspots_by_year.csv`)

Detection days are UTC dates with at least one hotspot inside the base. Episodes are runs of detection days no more than 5 days apart. MODIS only (Terra and Aqua), 2003 to Oct 22, 2026, gives a consistent sensor set. Spring is March to May, summer June to August, fall September to November.

| Base | Years with detections (of 24) | Episodes | Spring | Summer | Fall | Fall share of episodes | Fall share of detection days | Years with October detections |
|---|---|---|---|---|---|---|---|---|
| Wainwright | 20 | 69 | 40 | 2 | 27 | 39% | 35% | 13 |
| Suffield | 19 | 81 | 25 | 28 | 28 | 35% | 33% | 11 |
| Shilo (proxy) | 18 | 46 | 22 | 7 | 17 | 37% | 32% | 5 |
| Petawawa | 20 | 41 | 26 | 11 | 4 | 10% | 10% | 3 |
| Gagetown | 24 | 60 | 55 | 2 | 3 | 5% | 8% | 2 |
| Dundurn (proxy) | 10 | 12 | 7 | 3 | 2 | 17% | 24% | 0 |
| Valcartier (proxy) | 11 | 13 | 12 | 1 | 0 | 0% | 0% | 0 |
| Meaford | 2 | 2 | 1 | 1 | 0 | 0% | 0% | 0 |

- The prairie training areas (Wainwright, Suffield, Shilo) burn in fall far more often than the eastern forest bases. About 35 to 39% of their fire episodes start in September to November. At Gagetown, Petawawa and Valcartier, burning is overwhelmingly a spring event.
- Wainwright had October detections in 13 of 24 MODIS years. With all sensors (2002-2026) it had them in 16 years, including 2026 (Oct 14 and Oct 17). The biggest October event in the record before 2026 was Oct 7, 2025 (83 detections, all sensors).
- All sensors combined (first detection 1997 to 2005 depending on base): Wainwright 76 episodes, 41% in fall; Suffield 92 episodes, 36% in fall.
- Hotspots include prescribed and range burns. They cannot separate wildfire from deliberate burning on the ranges.

## 5. Late-season fires nationally

### CNFDB fire points 1990-2025 (`late_season_cnfdb_by_year.csv`, `late_season_trends_cnfdb.csv`)

- Canada: the share of dated fires starting in October shows no trend (Kendall tau -0.005, p = 0.97). It averaged 2.4% in 1990-1999 and 3.3% in 2016-2025. The September to October share also shows no trend (tau -0.05, p = 0.64). The number of October fires does not rise (tau -0.17, p = 0.15), while total fires fall strongly (tau -0.42, p < 0.001).
- The highest October shares were 2022 (391 fires, 7.3%) and 2025 (389 fires, 6.3%), the two largest October counts since 1991 (376). These are spikes in single years, not a steady rise.
- Alberta: October fires rose from 35.9 a year (1990-1999) to 53.9 (2016-2025). The trend is +6.7 fires per decade (Theil-Sen), tau 0.23, p = 0.05. September to October fires rose from 85.7 to 131.8 a year (tau 0.25, p = 0.03). The October share of Alberta fires did not change significantly (tau 0.17, p = 0.15).
- Caveat: 2000 to 2003 have 394 to 1,222 national fires without a month. Agency reporting practices differ over time.

### CWFIS hotspots (`late_season_hotspots_by_year.csv`, `late_season_trends_hotspots.csv`)

Counts are made server-side (WFS resultType=hits) for hotspots whose agency field is one of the 13 provinces and territories. The windows Jan 1 to Oct 22 and Sep 1 to Oct 22 make every year comparable with 2026 (the Oct 22, 2026 data are partial, up to about 15:00 UTC). MODIS only (2003-2026) is the consistent series. All sensors (VIIRS, MODIS, Sentinel-3) is shown for 2018-2026. Hotspots include fall agricultural stubble burning on the Prairies.

- 2026 has the quietest late season in the MODIS record. Only 1.5% of 2026 MODIS hotspots to Oct 22 fell between Sep 1 and Oct 22 (1,176 of 76,868), the lowest share of 24 years (median of 2003-2025: 8.1%). October 1 to 22, 2026 had 590 MODIS hotspots, 21st of 24. With all sensors, 2026 is 9th of 9 for the Sep 1 to Oct 22 share (1.2%) and 9th of 9 for the Oct 1 to 22 count (6,153).
- No trend in the late-season share: MODIS Sep 1 to Oct 22 share, Kendall tau 0.007, p = 0.98; Oct 1 to 22 share, tau -0.15, p = 0.34. The Sep 1 to Oct 22 count rises weakly (tau 0.27, p = 0.07). This is driven by large late fire activity in 2017, 2023, 2024 and 2025 (2023: 53,464 MODIS hotspots), not by a growing share of the season.
- The largest late-season shares were 2020 (27.9%, in a year with very few hotspots overall), 2022 (22.9%), 2006 (19.3%) and 2023 (17.8%). The highest October 1 to 22 counts were 2017 (3,986), 2015 (3,127) and 2022 (2,640).
- Conclusion from both sources: October fires are not becoming a larger share of Canada's fire activity. Big late-season years recur, most recently 2022 and 2025 in agency counts. Alberta's agency record does show more October fires since 1990. The Wainwright fire came in a fall with less national late-season fire activity than any year since 2003.

## Method notes and coverage

- Scripts, in order, in `scripts/`: 01 to 04 and 15 (Sentinel-2 burn estimate), 05 (ECCC download), 06 (CWFIS station FWI extraction), 07 (drought), 08 and 09 (weather ranks, rain, freeze), 10 to 12 (bases, NBAC/CNFDB/M3, hotspots in bases), 13 and 14 (late season nationally). All run single-threaded.
- Station distances to the burn centre: Wainwright CFB 15 km, Hughenden 22 km, Fabyan 23 km, Edgerton 32 km, Lloydminster 82 km, Coronation 85 km, Monitor 87 km, Ranfurly 92 km, Vegreville 115 km.
- Rank 1 = most extreme. Percentile = share of comparison days less extreme than Oct 17. Max gusts: ECCC reports a gust only when it is 31 km/h or more. Days with other data but no gust are counted as under 31 km/h.
- Everything labelled ESTIMATE (burned area, outside area, distance, afternoon ISI/FWI) is derived here and is not an official figure.
