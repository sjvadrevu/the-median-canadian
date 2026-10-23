"""Step 6: extract CWFIS station FWI observations (daily, noon LST) for stations within ~60 km of
the fire from the 1990s-2020s archives (streamed from .bz2) plus the 'current' daily files
(Oct 2026, including any newer than 2026-10-20 fetched into raw/cwfis_current/).
Output work/cwfis_fwi_near.csv (one row per station-date; current files override archive)."""
import bz2, csv, glob, os, pandas as pd, requests
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
R = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/data/fire/raw/fwi_stations"
AES = {"301S001", "3013362", "3012192", "3012790", "3010060", "3010650", "3015480", "3016802", "3013644", "3010992", "3015501"}
os.makedirs(f"{O}/raw/cwfis_current", exist_ok=True)
for d in ["20261021", "20261022"]:
    f = f"{O}/raw/cwfis_current/cwfis_fwi_{d}.csv"
    if not os.path.exists(f):
        r = requests.get(f"https://cwfis.cfs.nrcan.gc.ca/downloads/fwi_obs/current/cwfis_fwi_{d}.csv", timeout=120)
        print(d, r.status_code)
        if r.status_code == 200 and r.text.startswith("NAME"): open(f, "w").write(r.text)
rows = []
for fn in sorted(glob.glob(f"{R}/cwfis_fwi*sv3.0_ll.csv.bz2")):
    with bz2.open(fn, "rt") as fh:
        rd = csv.reader(fh); h = [c.strip() for c in next(rd)]; ia = h.index("aes")
        for r in rd:
            if len(r) > ia and r[ia].strip() in AES:
                x = dict(zip(h, [c.strip() for c in r])); x["src"] = os.path.basename(fn); rows.append(x)
    print(fn, len(rows), flush=True)
a = pd.DataFrame(rows); a["date"] = a.rep_date.str[:10]
cur = []
for fn in sorted(glob.glob(f"{R}/current/cwfis_fwi_*.csv") + glob.glob(f"{O}/raw/cwfis_current/cwfis_fwi_*.csv")):
    d = pd.read_csv(fn, skipinitialspace=True, dtype=str); d.columns = [c.strip().lower() for c in d.columns]
    d = d.apply(lambda s: s.str.strip()); d = d[d.aes.isin(AES)]
    d["date"] = pd.to_datetime(d.repdate).dt.strftime("%Y-%m-%d"); d["src"] = os.path.basename(fn); cur.append(d)
c = pd.concat(cur).rename(columns={"wg": "wg"})
keep = ["aes", "name", "date", "temp", "td", "rh", "ws", "wdir", "precip", "ffmc", "dmc", "dc", "isi", "bui", "fwi", "dsr", "src"]
a = a[[k for k in keep if k in a.columns]]; c = c[[k for k in keep + ["wg"] if k in c.columns]]
out = pd.concat([a[~(a.aes + a.date).isin(c.aes + c.date)], c]).sort_values(["aes", "date"])
out.to_csv(f"{O}/work/cwfis_fwi_near.csv", index=False)
print(out.groupby("aes").date.agg(["min", "max", "count"]))
