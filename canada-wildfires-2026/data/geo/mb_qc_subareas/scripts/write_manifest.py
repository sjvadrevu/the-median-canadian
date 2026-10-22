"""Write mb_qc_subareas/manifest.csv (same columns as geo/manifest.csv).
usage: python3 -I write_manifest.py OUT_DIR"""
import sys, os, csv
import pandas as pd
O = sys.argv[1]
val = pd.read_csv(f"{O}/validation.csv").set_index("layer")
D = "2026-10-21"
CRS = "ESRI:102001 Canada Albers Equal Area"
COLS = ["dataset", "publisher", "source_url", "local_path", "format", "size", "crs", "coverage",
        "record_count", "licence", "date_downloaded", "validation_notes"]


def size(p):
    b = os.path.getsize(f"{O}/{p}")
    return f"{b / 1e6:.1f}M"


def v(layer):
    r = val.loc[layer]
    return (f"Clipped to StatCan 2021 province polygon; rows sum {r.rows_sum_km2:,.0f} km2 vs province "
            f"{r.province_km2:,.0f} km2 ({r.diff_pct}%); residual gap {r.residual_gap_km2} km2, residual overlap "
            f"{r.residual_overlap_km2} km2; source overlaps resolved {r.source_overlap_resolved_km2} km2; source area "
            f"outside province clipped {r.source_outside_province_clipped_km2} km2; {r.slivers_merged_n} gap slivers "
            f"({r.slivers_merged_km2} km2) merged into adjacent unit; large uncovered area {r.remainder_km2:,.0f} km2 became the remainder row (final remainder area, incl. merged slivers, is in the attributes CSV); "
            f"all geometries valid = {r.all_valid}.")


MBL = "Not stated for the web-map file; gov.mb.ca site terms (manitoba.ca/legal/copyright.html) apply"
SOPL = "Not stated on sopfeu.qc.ca (SOPFEU content); attribute SOPFEU, confirm before redistribution"
rows = [
    ["MB recommended: Manitoba Wildfire Service fire regions (East, West, North + 2 shared areas + southern remainder)",
     "Manitoba Wildfire Service (derived in this project)",
     "https://www.gov.mb.ca/conservation_fire/Restrictions/MB_TravelRestrictionAreas_2025.js + restrictions_2025.js (region attribute)",
     "mb_fire_regions.gpkg (layer mb_fire_regions); mb_fire_regions_attributes.csv", "GeoPackage",
     size("mb_fire_regions.gpkg"), CRS, "Manitoba", int(val.loc["mb_fire_regions", "rows"]), MBL, D,
     "22 restriction areas dissolved on the agency's own region field (EAST 1-5, WEST 6,7,9-13, NORTH 15-22; Area 8 = EAST/WEST, Area 14 = WEST/NORTH kept as shared rows). Fire-number cross-check on 2026 FireView fires: 288 of 292 fires inside single-region areas match their EA/WE/NO prefix (4 EA/WE fires fall in NORTH areas); Area 8 holds 8 EA fires, Area 14 holds 17 WE + 1 NO; no 2026 fires fall in the southern remainder. " + v("mb_fire_regions")],
    ["MB alternative: Manitoba Wildfire Service fire and travel restriction areas (22 + southern remainder)",
     "Manitoba Wildfire Service", "https://www.gov.mb.ca/conservation_fire/Restrictions/MB_TravelRestrictionAreas_2025.js",
     "mb_fire_restriction_areas.gpkg; mb_fire_restriction_areas_attributes.csv", "GeoPackage",
     size("mb_fire_restriction_areas.gpkg"), CRS, "Manitoba (forested centre and north; south is remainder)",
     int(val.loc["mb_fire_restriction_areas", "rows"]), MBL, D,
     "Source: GeoJSON (CRS84) embedded in the MWS restrictions web map, 22 MultiPolygons, AREA_NUMBE 1-22; data file stamped 'updated June 27, 2025' and still served by the live page on 2026-10-21. " + v("mb_fire_restriction_areas")],
    ["MB fallback: Manitoba Forest Sections v5 (14 named sections)", "Manitoba Government (Forestry)",
     "https://services.arcgis.com/mMUesHYPkXjaFGfS/arcgis/rest/services/Manitoba_Forest_Sections_Version_5/FeatureServer/1",
     "mb_forest_sections.gpkg; mb_forest_sections_attributes.csv", "GeoPackage", size("mb_forest_sections.gpkg"),
     CRS, "Manitoba (full)", int(val.loc["mb_forest_sections", "rows"]), "Manitoba Open Data Licence", D,
     "17 source features; the 4 Highrock zones merged to one section -> 14 sections. Forestry, not fire. " + v("mb_forest_sections")],
    ["QC recommended: SOPFEU fire danger zones (zones de danger d'incendie, 65 + far-north remainder)", "SOPFEU",
     "https://www.sopfeu.qc.ca/layers/zdi.json (zone numbers/names joined to https://geofeux.sopfeu.qc.ca/sopfeu-api/public/danger-incendie)",
     "qc_sopfeu_fire_danger_zones.gpkg; qc_sopfeu_fire_danger_zones_attributes.csv", "GeoPackage",
     size("qc_sopfeu_fire_danger_zones.gpkg"), CRS, "Quebec (ZPI + southern part of northern zone; Nunavik is remainder)",
     int(val.loc["qc_sopfeu_fire_danger_zones", "rows"]), SOPL, D,
     "65 zones numbered 01-69 (09, 18, 19, 39 unused). Generalised polygons drawn over water; clipped. " + v("qc_sopfeu_fire_danger_zones")],
    ["QC alternative: SOPFEU protection zones (intensive protection zone, northern zone)", "SOPFEU",
     "https://www.sopfeu.qc.ca/layers/limite-intensive.json ; https://www.sopfeu.qc.ca/layers/limite-nordique.json",
     "qc_sopfeu_protection_zones.gpkg; qc_sopfeu_protection_zones_attributes.csv", "GeoPackage",
     size("qc_sopfeu_protection_zones.gpkg"), CRS, "Quebec (full)", int(val.loc["qc_sopfeu_protection_zones", "rows"]),
     SOPL, D, "Intensive zone = SOPFEU limite-intensive polygon clipped to the province; northern zone = province minus intensive zone (SOPFEU limite-nordique polygon differs from it by 1,233 km2 symmetric difference, i.e. 0.1%). " + v("qc_sopfeu_protection_zones")],
    ["QC fallback: 17 administrative regions as served by SOPFEU", "SOPFEU (geometry from Quebec SDA, generalised)",
     "https://www.sopfeu.qc.ca/layers/ra.json", "qc_admin_regions.gpkg; qc_admin_regions_attributes.csv", "GeoPackage",
     size("qc_admin_regions.gpkg"), CRS, "Quebec (full)", int(val.loc["qc_admin_regions", "rows"]),
     "Geometry from Quebec SDA (CC-BY 4.0); SOPFEU file licence not stated", D,
     "Official full-resolution alternative: MRNF Decoupages administratifs SDA (https://diffusion.mern.gouv.qc.ca/diffusion/RGQ/Vectoriel/Theme/Local/SDA_20k/GPKG/SDA.gpkg.zip; connection reset on 2026-10-21, not downloaded). " + v("qc_admin_regions")],
    ["Raw sources (as downloaded)", "Manitoba Wildfire Service; Manitoba Government; SOPFEU", "see rows above",
     "raw/mb/ (MB_TravelRestrictionAreas_2025.js, restrictions_2025.js, restrictions_map_2025.js, mb_forest_sections_v5.geojson, mb_fmus_v6.geojson, MB_Forest_Fires_Shapefile_2026-10-21.zip); raw/qc/ (zdi.json, limite-intensive.json, limite-nordique.json, ra.json, api_danger-incendie.json)",
     "JS/GeoJSON/JSON/zip", "", "EPSG:4326", "MB, QC", "", "as per rows above", D,
     "MB_Forest_Fires_Shapefile (FireView, 318 fires 2026) used only for the region cross-check. mb_fmus_v6 = 67 features / 62 FMUs (not built into a layer)."],
    ["NOT FOUND / NOT USED", "", "mli2.gov.mb.ca (CONNECT 502 via proxy, not retried); geoportal.gov.mb.ca + services.arcgis.com/mMUesHYPkXjaFGfS (237 services, no fire region layer); ArcGIS Online search; donneesquebec.ca CKAN search ('zone de protection intensive', 'SOPFEU', 'limite nordique'); geomatique.sopfeu.qc.ca WFS/WMS (fire layers only)",
     "", "", "", "", "", "", "", D,
     "No published polygon for Manitoba fire region limits in the agricultural south, MB fire response zones (White/Green/Yellow/Red appear only as a per-fire attribute), or the MRNF copy of the SOPFEU zone limits. Quebec UA (57 listed, public forest only, UA_GDB.zip 170 MB) recorded but not downloaded. No image tracing was needed."],
]
with open(f"{O}/manifest.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(COLS)
    w.writerows(rows)
print("wrote", len(rows))
