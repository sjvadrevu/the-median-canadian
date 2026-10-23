"""Load CWFIS station FWI observations (1990-2026) into one compact table.

Keeps April 1 to October 19 rows only. Oct 1-19 2026 comes from the daily
'current' files (the Oct 20 file is a partial day and is dropped).
Outputs:
  work/obs.pkl   columns aes (category), date, fwi (float32)
  work/ids.pkl   one row per station id: latest name, wmo, lon, lat, prov_fwi flag
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

W = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RAW = os.path.join(W, "data", "fire", "raw", "fwi_stations")
OUT = os.path.join(W, "analysis", "weather", "work")

frames, metas = [], []


def keep(df):
    md = df["date"].dt.month * 100 + df["date"].dt.day
    return df[(md >= 401) & (md <= 1019)]


for f in sorted(glob.glob(os.path.join(RAW, "cwfis_fwi*sv3.0_ll.csv.bz2"))):
    print("reading", f, flush=True)
    for ch in pd.read_csv(f, usecols=["rep_date", "aes", "wmo", "name", "lon", "lat", "fwi", "opts"],
                          dtype={"aes": str, "wmo": str, "name": str, "opts": str}, chunksize=1_000_000):
        ch["date"] = pd.to_datetime(ch["rep_date"].str.slice(0, 10))
        ch = keep(ch)
        ch["aes"] = ch["aes"].str.strip()
        m = ch.sort_values("date").groupby("aes").agg(name=("name", "last"), wmo=("wmo", "last"), lon=("lon", "last"),
                                                       lat=("lat", "last"), last=("date", "max"),
                                                       prov_fwi=("opts", lambda s: s.fillna("").str.contains("ProvFwi").any()))
        metas.append(m.reset_index())
        frames.append(pd.DataFrame({"aes": ch["aes"].astype("category"), "date": ch["date"].values,
                                    "fwi": ch["fwi"].astype(np.float32).values}))

cur, curmeta = [], []
for f in sorted(glob.glob(os.path.join(RAW, "current", "cwfis_fwi_2026*.csv"))):
    if f.endswith("20261020.csv"):
        continue
    c = pd.read_csv(f, dtype=str, skipinitialspace=True)
    c = c[c["NAME"] != "NAME"]
    c["aes"] = c["AES"].str.strip()
    c["date"] = pd.to_datetime(c["REPDATE"].str.strip(), format="%Y%m%d")
    c["fwi"] = pd.to_numeric(c["FWI"].str.strip().replace("NULL", np.nan), errors="coerce").astype(np.float32)
    cur.append(c[["aes", "date", "fwi"]])
    curmeta.append(c[["aes", "NAME", "AGENCY"]])
cur = pd.concat(cur)
cur = cur[cur["date"] <= "2026-10-19"]

ids = pd.concat(metas).sort_values("last").groupby("aes").last()
ids["name"] = ids["name"].str.strip()
cm = pd.concat(curmeta).drop_duplicates("aes").set_index("aes")
print("Oct 2026 rows", len(cur), "ids", cur["aes"].nunique(), "matched to archive ids", cur["aes"].isin(ids.index).sum())
ids["agency_oct2026"] = cm["AGENCY"].str.strip().reindex(ids.index)

cur = cur[cur["aes"].isin(ids.index)]
cats = pd.CategoricalDtype(sorted(ids.index))
obs = pd.concat([f.assign(aes=f["aes"].astype(str).astype(cats)) for f in frames] +
                [cur.assign(aes=cur["aes"].astype(cats))], ignore_index=True)
del frames
n0 = len(obs)
obs = obs.sort_values(["aes", "date", "fwi"]).drop_duplicates(["aes", "date"], keep="first")
print("rows", n0, "after station-day dedupe", len(obs))
obs.reset_index(drop=True).to_pickle(os.path.join(OUT, "obs.pkl"))
ids.to_pickle(os.path.join(OUT, "ids.pkl"))
print(obs.groupby(obs["date"].dt.year)["aes"].nunique().to_string())
