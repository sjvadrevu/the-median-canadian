"""Download ECCC daily climate observations for the candidate station IDs (work/station_ids.csv) from
MSC GeoMet (https://api.weather.gc.ca/collections/climate-daily/items), 1990-06-01 to today, as CSV.
One gzip file per climate ID in raw/eccc/daily/<CLIMATE_IDENTIFIER>.csv.gz. Existing files are kept,
so the script can be rerun to resume. 4 parallel requests; failed IDs are listed in work/log_02.txt.
"""
import gzip
import io
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
import requests

from common import RAW, WORK, log

API = "https://api.weather.gc.ca/collections/climate-daily/items"
PROPS = ("CLIMATE_IDENTIFIER,LOCAL_DATE,MAX_TEMPERATURE,MIN_TEMPERATURE,MEAN_TEMPERATURE,"
         "TOTAL_PRECIPITATION,TOTAL_PRECIPITATION_FLAG,TOTAL_RAIN,TOTAL_SNOW,TOTAL_SNOW_FLAG,"
         "SNOW_ON_GROUND,SNOW_ON_GROUND_FLAG")
END = time.strftime("%Y-%m-%d")
D = RAW / "eccc" / "daily"
D.mkdir(parents=True, exist_ok=True)
fh = open(WORK / "log_02.txt", "a")
ids = pd.read_csv(WORK / "station_ids.csv", dtype={"CLIMATE_IDENTIFIER": str})
sess = requests.Session()


def get(cid):
    out = D / f"{cid}.csv.gz"
    if out.exists():
        return cid, "kept", 0
    parts, off, lim = [], 0, 10000
    while True:
        params = dict(f="csv", limit=lim, offset=off, CLIMATE_IDENTIFIER=cid, properties=PROPS,
                      sortby="LOCAL_DATE", datetime=f"1990-06-01/{END}")
        for attempt in range(6):
            try:
                r = sess.get(API, params=params, timeout=180)
                if r.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(5 * (attempt + 1))
        else:
            return cid, "failed", off
        txt = r.text
        lines = txt.count("\n")
        parts.append(txt if off == 0 else txt.split("\n", 1)[1])
        if lines - 1 < lim:
            break
        off += lim
    with gzip.open(out, "wt") as f:
        f.write("".join(parts))
    return cid, "ok", sum(p.count("\n") for p in parts) - 1


t0 = time.time()
with ThreadPoolExecutor(4) as ex:
    for k, (cid, st, n) in enumerate(ex.map(get, ids.CLIMATE_IDENTIFIER.unique())):
        if st != "kept":
            log(f"{k} {cid} {st} {n} rows {time.time() - t0:.0f}s", fh)
