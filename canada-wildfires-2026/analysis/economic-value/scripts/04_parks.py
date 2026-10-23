"""Parks Canada attendance (open.canada.ca, fiscal years April-March, 2001-02 to 2025-26) against area burned inside each
national park (NRCan CLAB legislative boundaries, burned 240 m cells NBAC 2016-2025 / M3 2026, cell-centre rule).

Fire season Y falls in fiscal year Y-(Y+1). Baseline per park = mean of the pre-COVID FY2017-18, 2018-19 and 2019-20, excluding any of them in which that park
itself burned 1,000 ha or more (all three used, flagged, if every one burned). Relative change = park attendance / park baseline; network change = the same ratio
for the sum of all places reported in every year (control); 'excess' = park ratio / network ratio - 1.
'UR' (under review) and 0 are treated as missing. FY2026-27 (the 2026 season) is not yet published.
Outputs: parks_attendance_long.csv, parks_burned_ha_by_year.csv, parks_fire_attendance.csv
"""
import re


def rd(f):
    try:
        return pd.read_csv(f, encoding="utf-8-sig", dtype=str)
    except UnicodeDecodeError:
        return pd.read_csv(f, encoding="cp1252", dtype=str)
import numpy as np
import pandas as pd
import geopandas as gpd
from vcommon import RAW, OUT, DATA, burned_cells, rasterize_idx_window
from grid import meta

P = RAW / "parks"
long = []
w = rd(P / "parks-canada-attendance-2001_02-to-2018_19.csv")
for c in w.columns[1:]:
    for pl, v in zip(w.Place, w[c]):
        long.append((pl.strip(), int(c[:4]), v))
for f in sorted(P.glob("parks-canada-attendance-20*_*.csv")) + [P / "parks-canada-attendance-2019-20.csv"]:
    if "to-2018" in f.name:
        continue
    d = rd(f)
    fy = int(re.search(r"(20\d\d)", d.columns[1]).group(1))
    for pl, v in zip(d.Place, d.iloc[:, 1]):
        long.append((str(pl).strip(), fy, v))
a = pd.DataFrame(long, columns=["place", "fy_start", "raw"]).drop_duplicates(["place", "fy_start"])
a["visits"] = pd.to_numeric(a.raw.str.replace(",", "", regex=False), errors="coerce")
a.loc[a.visits <= 0, "visits"] = np.nan
a.to_csv(OUT / "parks_attendance_long.csv", index=False)

# burned area per national park
m = meta()
clab = gpd.read_file(DATA / "geo" / "parks" / "clab" / "CLAB_CA_2026-10-05.shp").to_crs(m["crs"])
cells = burned_cells()
cells = cells[cells.year > 0]
rows = []
for _, p in clab.iterrows():
    idx = rasterize_idx_window(list(gpd.GeoSeries([p.geometry]).explode(index_parts=False)))
    ins = cells[np.isin(cells.idx.values, idx)]
    by = ins.groupby("year").area_ha.sum()
    for y in range(2016, 2027):
        rows.append(dict(park=p.NAME_E, clab_id=p.CLAB_ID, year=y, burned_ha_mapped=float(by.get(y, 0.0)),
                         park_cells=len(idx)))
b = pd.DataFrame(rows)
b["park_ha_grid"] = b.park_cells * 5.76
b.to_csv(OUT / "parks_burned_ha_by_year.csv", index=False)

# name matching CLAB -> attendance 'place'
def norm(s):
    s = s.upper().replace(" OF CANADA", "").replace("NATIONAL PARK RESERVE", "NATIONAL PARK RESERVE").strip()
    return re.sub(r"[^A-Z ]", "", s)
places = a.place.unique()
pmap = {}
for nm in b.park.unique():
    n = norm(nm)
    cand = [pl for pl in places if norm(pl) == n or norm(pl).startswith(n.replace(" NATIONAL PARK RESERVE", "").replace(" NATIONAL PARK", "") + " NATIONAL")]
    if "REVELSTOKE" in n or n.startswith("GLACIER"):
        cand = [pl for pl in places if "Revelstoke" in pl and "Glacier" in pl]
    pmap[nm] = cand[0] if cand else None

# network control: places with a value in every FY 2016..2025
piv = a.pivot(index="place", columns="fy_start", values="visits")
full = piv.loc[:, 2016:2025].dropna()
net = full.sum()
base_fys = [2017, 2018, 2019]
out = []
burn = b.pivot_table(index="park", columns="year", values="burned_ha_mapped")
for park, pl in pmap.items():
    if pl is None or park not in burn.index:
        continue
    bp = burn.loc[park]
    if bp.max() < 1000:
        continue
    s = piv.loc[pl]
    bfy = [f for f in base_fys if bp.get(f, 0) < 1000 and pd.notna(s.get(f))]
    flag = ""
    if not bfy:
        bfy = [f for f in base_fys if pd.notna(s.get(f))]
        flag = "every baseline year had 1,000 ha or more burned in the park"
    if not bfy:
        continue
    base = s[bfy].mean(); nbase = net[bfy].mean()
    for y in range(2016, 2027):
        v = s.get(y, np.nan); nv = net.get(y, np.nan)
        out.append(dict(park=park, place=pl, fire_year=y, fiscal_year=f"{y}-{str(y + 1)[2:]}", burned_ha_mapped=bp.get(y, 0.0),
                        visits=v, baseline_visits=base, baseline_fys=";".join(map(str, bfy)), change_vs_baseline=v / base - 1 if pd.notna(v) else np.nan,
                        network_change_vs_baseline=nv / nbase - 1 if pd.notna(nv) else np.nan,
                        excess_vs_network=(v / base) / (nv / nbase) - 1 if pd.notna(v) and pd.notna(nv) else np.nan,
                        baseline_flag=flag))
o = pd.DataFrame(out)
o.to_csv(OUT / "parks_fire_attendance.csv", index=False)
pd.set_option("display.width", 250)
print("network places:", len(full), "network visits", net.round(0).to_dict())
print(o[o.burned_ha_mapped >= 1000][["park", "fire_year", "burned_ha_mapped", "visits", "baseline_visits", "change_vs_baseline", "network_change_vs_baseline", "excess_vs_network"]].round(3).to_string())
print(o[o.park.str.contains("JASPER")].round(3).to_string())
print({k: v for k, v in pmap.items()})
