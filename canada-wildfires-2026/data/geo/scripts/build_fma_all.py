"""Merge fire-agency management areas into fma_all (agency, area_name, province, ...).
Provincial/territorial agency areas are clipped to StatCan 2021 province polygons; where an
agency has no public boundary layer, the whole province is one row (boundary_status says so).
Parks Canada national parks are added as separate rows (they overlap provincial rows by design).
usage: build_fma_all.py GEO_DIR"""
import sys, warnings
import pandas as pd, geopandas as gpd
warnings.filterwarnings("ignore")
G = sys.argv[1]
EA = "ESRI:102001"
prov = gpd.read_file(f"{G}/statcan/lpr_000b21a_e_provinces_2021.gpkg").to_crs(EA)
prov["province"] = prov["PREABBR"].str.replace(".", "", regex=False)
ABBR = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON", "46": "MB",
        "47": "SK", "48": "AB", "59": "BC", "60": "YT", "61": "NT", "62": "NU"}
prov["province"] = prov["PRUID"].map(ABBR)

parts = []
def add(path, pcode, agency, namecol, level, src, status="official agency boundary", rename=None):
    g = gpd.read_file(path).to_crs(EA)
    g["geometry"] = g.make_valid()
    g["area_name"] = g[namecol].astype(str).str.strip()
    if rename:
        g["area_name"] = g["area_name"].map(lambda x: rename.get(x, x))
    g = g.dissolve("area_name", as_index=False)
    p = prov.loc[prov.province == pcode, "geometry"].union_all()
    g["geometry"] = g.geometry.intersection(p)
    g["agency"], g["province"], g["area_level"] = agency, pcode, level
    g["source"], g["boundary_status"] = src, status
    parts.append(g[["agency", "area_name", "province", "area_level", "boundary_status", "source", "geometry"]])

R = f"{G}/raw"; F = f"{G}/fma"
add(f"{R}/bc_WHSE_LEGAL_ADMIN_BOUNDARIES.DRP_MOF_FIRE_CENTRES_SP.geojson", "BC", "BC Wildfire Service",
    "MOF_FIRE_CENTRE_NAME", "fire centre", "BC Data Catalogue WHSE_LEGAL_ADMIN_BOUNDARIES.DRP_MOF_FIRE_CENTRES_SP")
add(f"{R}/ab_forest_areas.geojson", "AB", "Alberta Wildfire", "FA_NAME", "forest area",
    "Alberta geospatial.alberta.ca wildfire/wildfire_forest_area_boundary/MapServer")
add(f"{F}/sk_spsa_protection_areas.geojson", "SK", "Saskatchewan Public Safety Agency", "PA", "protection area",
    "gis.saskatchewan.ca SPSA/ProtectionAreas/MapServer/1")
add(f"{R}/on_fire_mgmt_hq_areas.geojson", "ON", "Ontario Forest Fires (MNR AFFES)", "OFFICIAL_NAME",
    "fire management headquarters area", "Ontario GeoHub LIO_Open09/MapServer/53")
add(f"{R}/nt_regions.geojson", "NT", "GNWT Forest Management Division (ECC)", "REGION", "administrative region",
    "data.sac-isc.gc.ca NT_Administrative_Regions/FeatureServer/0",
    status="official GNWT administrative region (used by NWT wildfire program for regional reporting)")
add(f"zip://{R}/yt_fire_districts.shp.zip", "YT", "Yukon Wildland Fire Management", "DISTRICT", "fire district",
    "GeoYukon Fire_Districts.shp.zip")
nl = pd.concat([gpd.read_file(f"{F}/nl_forest_mgmt_districts_newfoundland.geojson"),
                gpd.read_file(f"{F}/nl_forest_mgmt_districts_labrador.geojson")], ignore_index=True)
nl["district"] = "Forest Management District " + nl["MD_NUM"].astype(str)
nl.to_file(f"{F}/nl_forest_mgmt_districts.geojson", driver="GeoJSON")
add(f"{F}/nl_forest_mgmt_districts.geojson", "NL", "NL Forestry and Agrifoods Agency (Wildfire)", "district",
    "forest management district", "NL services8.arcgis.com FFA_ForestManagementDistricts_NL and _LB FeatureServer/6",
    status="official NL forest management district (forestry administrative unit, not a fire-specific zone)")

fma = pd.concat(parts, ignore_index=True)
rows = [fma]
for _, p in prov.iterrows():
    mine = fma[fma.province == p.province]
    if len(mine):
        rest = p.geometry.difference(mine.union_all())
        if rest.area / 1e6 > 500:
            rows.append(gpd.GeoDataFrame([{"agency": mine.agency.iloc[0], "area_name": f"{p.province} outside mapped areas",
                "province": p.province, "area_level": "remainder", "boundary_status": "StatCan province minus agency areas",
                "source": "derived", "geometry": rest}], crs=EA))
    else:
        agency = {"MB": "Manitoba Wildfire Service", "QC": "SOPFEU", "NB": "NB Department of Natural Resources (Forest Fire)",
                  "NS": "NS Department of Natural Resources (Wildfire)", "PE": "PEI Forests, Fish and Wildlife",
                  "NU": "Government of Nunavut (no organised wildfire suppression)"}[p.province]
        rows.append(gpd.GeoDataFrame([{"agency": agency, "area_name": f"{p.PRENAME} (whole province/territory)",
            "province": p.province, "area_level": "province", "boundary_status": "no public fire-area boundary layer found; whole province",
            "source": "StatCan 2021 cartographic boundary", "geometry": p.geometry}], crs=EA))
fma = pd.concat(rows, ignore_index=True)

pk = gpd.read_file(f"{G}/parks/clab/CLAB_CA_2026-10-05.shp").to_crs(EA)
pk["geometry"] = pk.make_valid()
pk = gpd.GeoDataFrame({"agency": "Parks Canada", "area_name": pk.NAME_E.str.title(), "province": pk.CPC_CODE,
                       "area_level": "national park / park reserve / urban park (" + pk.CLAB_TYPE + ")",
                       "boundary_status": "official legislative boundary; overlaps provincial rows",
                       "source": "NRCan CLSS CLAB_CA_2026-10-05", "geometry": pk.geometry}, crs=EA)
fma = gpd.GeoDataFrame(pd.concat([fma, pk], ignore_index=True), crs=EA)
fma = fma[~fma.geometry.is_empty].reset_index(drop=True)
fma["fma_id"] = range(1, len(fma) + 1)
fma["area_km2_equal_area"] = fma.area / 1e6
fma = fma[["fma_id", "agency", "area_name", "province", "area_level", "boundary_status", "source", "area_km2_equal_area", "geometry"]]
fma.to_file(f"{G}/fma_all.gpkg", layer="fma_all", driver="GPKG")
fma.drop(columns="geometry").to_csv(f"{G}/fma_all_attributes.csv", index=False)
print(fma.drop(columns="geometry").to_string())
nonpk = fma[fma.agency != "Parks Canada"]
chk = nonpk.groupby("province").area_km2_equal_area.sum().to_frame("fma_km2").join(
    prov.set_index("province").area.div(1e6).rename("prov_km2"))
chk["diff_pct"] = 100 * (chk.fma_km2 / chk.prov_km2 - 1)
print(chk.to_string()); print("valid", fma.is_valid.all(), "rows", len(fma))
