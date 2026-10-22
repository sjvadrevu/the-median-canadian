# Manitoba and Quebec fire sub-areas: options

Retrieved 2026-10-21. All built layers are in the `fma_all` schema (fma_id, agency, area_name, province, area_level, boundary_status, source, area_km2_equal_area), in ESRI:102001, clipped to the StatCan 2021 province polygon. Rows sum to the province area with no gaps or overlaps (see `validation.csv`). `fma_id` starts at 1001 (MB) and 2001 (QC) so it does not clash with `fma_all`. `fma_all.gpkg` was not modified.

## Recommendation

| | Manitoba | Quebec |
|---|---|---|
| Use | `mb_fire_regions.gpkg` (6 rows) | `qc_sopfeu_fire_danger_zones.gpkg` (66 rows) |
| Why | The agency's own East / West / North regions, which it uses for fire numbers and bulletins | SOPFEU's own daily-reporting zones. Every SOPFEU fire record carries its zone |
| Finer option | `mb_fire_restriction_areas.gpkg` (22 areas + remainder) | n/a (the 65 zones are already fine-grained) |
| Coarser option | n/a | `qc_sopfeu_protection_zones.gpkg` (intensive zone + northern zone) |
| Caveat | Areas 8 and 14 are labelled "EAST/WEST" and "WEST/NORTH" by the agency, so they are kept as shared rows. The agricultural south (97,192 km², 15%) has no MWS area polygon, so it is a remainder row | Nunavik and the far north (519,551 km², 34%) have no danger zone, so it is a remainder row. Zone edges are generalised |

## Manitoba candidates

| | (a) MWS fire regions | (a) MWS fire and travel restriction areas | (b) Map image to trace | (c) Forest Sections v5 / FMUs v6 | (d) Natural Resources regions |
|---|---|---|---|---|---|
| Publisher | Manitoba Wildfire Service (derived from the layer at right) | Manitoba Wildfire Service | MWS | Manitoba Government (Forestry) | Manitoba NRIF |
| URL | as at right + `restrictions_2025.js` (region field) | gov.mb.ca/conservation_fire/Restrictions/MB_TravelRestrictionAreas_2025.js | n/a | services.arcgis.com/mMUesHYPkXjaFGfS/.../Manitoba_Forest_Sections_Version_5/FeatureServer/1 ; .../Manitoba_FMUs_Version_6/FeatureServer/1 | none found |
| Format | GeoJSON in JS, plus a JSON region table | GeoJSON (CRS84) in JS | n/a | ArcGIS REST | n/a |
| Licence | Not stated for the file; gov.mb.ca site terms | Same | n/a | Manitoba Open Data Licence | n/a |
| Units | 3 regions + 2 shared areas + remainder | 22 areas + remainder | n/a | 14 sections; 62 FMUs (67 features) | n/a |
| Used in fire reporting? | Yes. MWS bulletins report by "East / West / North region" (news.gov.mb.ca items 69378, 69398); 2026 FireView fire numbers carry EA/WE/NO prefixes, and 288 of 292 fires in single-region areas match | Yes. Restrictions are issued by area ("areas 1, 2 and 3 at Level 3, Area 5 at Level 2, Area 8 at Level 1", same releases); this is the official restrictions map | n/a | No. These are forestry reporting units | No |
| Coverage | Forested centre and north. South is a remainder | Same | n/a | Whole province | n/a |
| Download | Done, built | Done, built | Not needed (vector found) | Done. Sections built as fallback; FMUs kept raw | mli2.gov.mb.ca blocked (CONNECT 502); not on geoportal or ArcGIS Online |
| Verdict | **Recommended** | Finer alternative | Not needed | Fallback only | Not available |

## Quebec candidates

| | (a) SOPFEU fire danger zones (ZDI) | (a) SOPFEU protection zones | (b) MRNF limit / fire zone layers | (c) Forest management units (UA) | (d) 17 administrative regions |
|---|---|---|---|---|---|
| Publisher | SOPFEU | SOPFEU | MRNF / Données Québec | MRNF | SOPFEU copy of Quebec SDA; MRNF SDA |
| URL | sopfeu.qc.ca/layers/zdi.json (+ geofeux.sopfeu.qc.ca/sopfeu-api/public/danger-incendie) | sopfeu.qc.ca/layers/limite-intensive.json ; limite-nordique.json | donneesquebec.ca (only "Limite territoriale des forêts attribuables") | diffusion.mffp.gouv.qc.ca/.../UA/UA_GDB.zip | sopfeu.qc.ca/layers/ra.json ; diffusion.mern.gouv.qc.ca/.../SDA.gpkg.zip |
| Format | JSON with GeoJSON strings | JSON with GeoJSON strings | SHP (polyline) | FGDB/GPKG | JSON / GPKG |
| Licence | Not stated (SOPFEU content) | Not stated (SOPFEU content) | CC-BY 4.0 | CC-BY 4.0 | SDA: CC-BY 4.0 |
| Units | 65 zones (numbered 01 to 69) + remainder | 2 | n/a (a line, and it is a forestry limit) | 57 listed, public forest only | 17 |
| Used in fire reporting? | Yes. Daily fire danger is published per zone. In the SOPFEU web map each fire record has `Zdi.Id`, and the map counts fires per zone | Yes. Situation reports and the fire map are split into "zone de protection intensive" and "zone nordique" | No | No | Partly. The SOPFEU map uses these for region focus and fire counts by region |
| Coverage | Intensive zone + southern northern zone. Nunavik is the remainder | Whole province | n/a | Public forest only, with gaps | Whole province |
| Download | Done, built | Done, built | Not useful | Listed only (170 MB, gappy) | SOPFEU copy built. MRNF SDA reset the connection |
| Verdict | **Recommended** | Coarse companion layer | Not suitable | Not suitable | Fallback |

## Method and accuracy

- Source polygons were made valid, projected to ESRI:102001 and dissolved by unit number. Overlaps between neighbouring source polygons go to the lower-numbered unit (MB areas 441 km² in total, mostly between Areas 2 and 3; QC zones 0 km²).
- Each layer was clipped to the StatCan 2021 province polygon. Gap pieces of 2,000 km² or more become the labelled remainder row. Smaller gap pieces (digitising slivers, coastal islands) are merged into the touching unit with the longest shared boundary, or into the nearest unit if nothing touches. The remainder is included in that merge.
- Both agency layers are generalised web-map geometry, not survey boundaries. The Quebec zones were drawn over open water (36,512 km² was clipped off), so edges are good to roughly 1 to 5 km. They suit a provincial map, not parcel-level work.
- Nothing was traced from an image, because vector boundaries were found for both provinces.
- The Manitoba restriction file is stamped "updated June 27, 2025" and was still the file served by the live restrictions page on 2026-10-21.
- Fire-response zones (White / Green / Yellow / Red) exist only as an attribute on Manitoba fire records; no polygon layer for them was found.
