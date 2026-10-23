"""Write manifest.csv: every downloaded and reused input with source, URL, size and hash."""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd

from common import OUT, RAW

AH = "https://eccc-opendata-01.collab.science.gc.ca/CDAS/products/AHCCD/"


def h16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()[:16]


rows = []
desc = {"Homog_monthly_mean_temp_Gen3.zip": "AHCCD third-generation homogenized monthly mean temperature, 780 stations, updated to 2023",
        "Adj_monthly_total_prec.zip": "AHCCD second-generation adjusted monthly total precipitation, 463 stations, updated to Dec 2017",
        "Adj_monthly_rain.zip": "AHCCD adjusted monthly rain (downloaded, not used)",
        "Adj_monthly_snow.zip": "AHCCD adjusted monthly snowfall (downloaded, not used)",
        "Temperature_Stations_Gen3.xls": "AHCCD temperature station list (coordinates, joined flag)",
        "Precipitation_Stations.xls": "AHCCD precipitation station list",
        "Temperature_Documentation_Gen3.doc": "AHCCD temperature documentation",
        "Precipitation_Documentation.doc": "AHCCD precipitation documentation"}
for f, d in desc.items():
    p = RAW / "ahccd" / f
    rows.append(dict(path=f"raw/ahccd/{f}", source="ECCC AHCCD (open data)", url=AH + f, downloaded="2026-10-21",
                     bytes=p.stat().st_size, sha256_16=h16(p), description=d))
p = RAW / "ahccd" / "ahccd_stations.json"
rows.append(dict(path="raw/ahccd/ahccd_stations.json", source="ECCC MSC GeoMet", url="https://api.weather.gc.ca/collections/ahccd-stations/items?f=json&limit=2000",
                 downloaded="2026-10-21", bytes=p.stat().st_size, sha256_16=h16(p),
                 description="GeoMet AHCCD station list; checked only: the GeoMet ahccd-monthly collection ends in 2020 and has no precipitation after 2017, so the CDAS zip files were used"))
for sub, url, d in [("eccc_hourly_noon", "https://api.weather.gc.ca/collections/climate-hourly/items?f=csv&CLIMATE_IDENTIFIER=<id>&LOCAL_HOUR=12&datetime=1953-01-01/2026-10-20&properties=CLIMATE_IDENTIFIER,LOCAL_DATE,TEMP,RELATIVE_HUMIDITY,WIND_SPEED,PRECIP_AMOUNT",
                     "12:00 LST hourly observations (temperature, RH, wind) for FWI, one gzip CSV per climate ID"),
                    ("eccc_daily", "https://api.weather.gc.ca/collections/climate-daily/items?f=csv&CLIMATE_IDENTIFIER=<id>&datetime=1950-01-01/<end>&properties=CLIMATE_IDENTIFIER,LOCAL_DATE,MAX_TEMPERATURE,MIN_TEMPERATURE,TOTAL_PRECIPITATION,TOTAL_RAIN,TOTAL_SNOW,SNOW_ON_GROUND",
                     "daily climate (precipitation for FWI rain, snow on ground); end = 1990-05-31 for IDs already in analysis/climate/raw/eccc/daily (reused from 1990-06), else 2026-10-20")]:
    fs = sorted((RAW / sub).glob("*.csv.gz"))
    rows.append(dict(path=f"raw/{sub}/<CLIMATE_IDENTIFIER>.csv.gz", source="ECCC MSC GeoMet", url=url, downloaded="2026-10-21",
                     bytes=sum(f.stat().st_size for f in fs), sha256_16="", description=f"{len(fs)} files; {d}"))
for path, src, d in [
    ("../climate/work/site_month.csv", "analysis/climate (ECCC climate-daily 1990-06 to 2026-10)", "monthly precipitation and temperature per daily site, used to extend AHCCD (02)"),
    ("../climate/work/site_meta.csv", "analysis/climate", "member climate IDs per daily site"),
    ("../climate/raw/eccc/climate_stations.json", "analysis/climate (ECCC MSC GeoMet climate-stations)", "station inventory for the long-record selection (04)"),
    ("../climate/raw/eccc/daily/<id>.csv.gz", "analysis/climate", "daily records 1990-06 to 2026-10, reused for FWI rain and snow"),
    ("../climate/work/areas_fcd292dde04d/areas_1km.gpkg", "analysis/climate (fma_v2 areas, 1 km simplified)", "station-to-area distances"),
    ("../cause/work/areas_fcd292dde04d/areas.csv, area_forest.csv", "analysis/cause (fma_v2)", "area attributes, forest and land hectares"),
    ("../cause/burn_history_by_area_year.csv", "analysis/cause (NBAC 1972-2025, CWFIS M3 2026)", "forest share burned per area and year"),
    ("../forest/work/burn_YYYY.npy, fma_v2_id.npy, forest_count.npy, areal_scale_coarse.npy, grid_meta.json", "analysis/forest", "240 m burn rasters for all-land hectares per area (08)"),
    ("../forest/nbac_totals_by_year_admin.csv", "analysis/forest (NBAC 1972-2025)", "NBAC hectares by province and year"),
    ("../forest/scaling_factors_by_province.csv", "analysis/forest", "official 2026 hectares by province and M3 scaling factors"),
    ("../../data/fire/raw/nfdb/NFDB_point_txt.zip", "NRCan CFS CNFDB points (version 20260811)", "fires >= 200 ha 1959-1971 extension (07)"),
    ("../weather/work/site_year.pkl, site_daily.pkl, site_meta.pkl; ../weather/station_extreme_days.csv", "analysis/weather (CWFIS station FWI 1990-2026)", "fixed-station extreme-day counts (06) and FWI validation (10)")]:
    rows.append(dict(path=path, source=src, url="", downloaded="reused", bytes="", sha256_16="", description=d))
pd.DataFrame(rows).to_csv(OUT / "manifest.csv", index=False)
print(len(rows), "manifest rows")
