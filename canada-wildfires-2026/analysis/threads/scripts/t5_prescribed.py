"""Thread 5: prescribed burns by province and year, 1980-2025, from CNFDB points (and NBAC flag as check).

Prescribed burn = any of: PRESCRIBED == 'PB' or '1'; CAUSE2 == 'H-PB'; FIRE_TYPE in ('PB', 'Prescribed Burn').
Wildfire = every other record (all causes) with YEAR 1980-2025.
Outputs: t5_prescribed_by_prov_year.csv, t5_prescribed_national_year.csv, t5_prescribed_trend.csv,
         t5_prescribed_flag_crosstab.csv
"""
import zipfile
import numpy as np
import pandas as pd
import pyogrio
from scipy import stats

BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
OUT = f"{BASE}/analysis/threads"
z = zipfile.ZipFile(f"{BASE}/data/fire/raw/nfdb/NFDB_point_txt.zip")
d = pd.read_csv(z.open("NFDB_point_20260811.txt"), encoding="utf-8-sig", low_memory=False)
for c in ["PRESCRIBED", "CAUSE2", "FIRE_TYPE", "SRC_AGENCY", "NAT_PARK"]:
    d[c] = d[c].astype(str).str.strip()
d["SIZE_HA"] = pd.to_numeric(d.SIZE_HA, errors="coerce").clip(lower=0)
f_presc = d.PRESCRIBED.isin(["PB", "1"])
f_cause = d.CAUSE2.eq("H-PB")
f_type = d.FIRE_TYPE.isin(["PB", "Prescribed Burn"])
d["pb"] = f_presc | f_cause | f_type
ct = pd.crosstab([f_presc.rename("PRESCRIBED_PB"), f_cause.rename("CAUSE2_H-PB")], f_type.rename("FIRE_TYPE_PB"))
ct.to_csv(f"{OUT}/t5_prescribed_flag_crosstab.csv")
print(ct)
d = d[(d.YEAR >= 1980) & (d.YEAR <= 2025)].copy()
# reporting agency: Parks Canada records keep SRC_AGENCY = PC; province for PC from lat/lon not needed, keep PC separate
d["prov"] = d.SRC_AGENCY
g = d.groupby(["prov", "YEAR", "pb"]).agg(n=("SIZE_HA", "size"), ha=("SIZE_HA", "sum")).reset_index()
w = g.pivot_table(index=["prov", "YEAR"], columns="pb", values=["n", "ha"], fill_value=0)
w.columns = [f"{a}_{'pb' if b else 'wild'}" for a, b in w.columns]
w = w.reset_index()
w.to_csv(f"{OUT}/t5_prescribed_by_prov_year.csv", index=False)
nat = w.groupby("YEAR")[[c for c in w.columns if c.startswith(("n_", "ha_"))]].sum().reset_index()
nat["pb_share_of_area"] = nat.ha_pb / (nat.ha_pb + nat.ha_wild)
nat["pb_per_1000_wild_ha"] = nat.ha_pb / nat.ha_wild * 1000
nat.to_csv(f"{OUT}/t5_prescribed_national_year.csv", index=False)
print(nat.to_string())
# trends: Theil-Sen slope and Kendall tau on annual counts and area, Canada and each agency with any PB
rows = []
for key, sub in [("Canada", nat)] + [(p, w[w.prov == p]) for p in sorted(w.prov.unique())]:
    sub = sub.set_index("YEAR")[["n_pb", "ha_pb", "ha_wild"]].reindex(range(1980, 2026), fill_value=0)
    if sub.n_pb.sum() == 0:
        continue
    for var in ["n_pb", "ha_pb", "ha_wild"]:
        y = sub[var].values.astype(float)
        tau, p = stats.kendalltau(sub.index, y)
        sl = stats.theilslopes(y, sub.index)[0]
        rows.append(dict(area=key, var=var, total_1980_2025=y.sum(), mean_1980_1999=y[:20].mean(),
                         mean_2000_2009=y[20:30].mean(), mean_2010_2019=y[30:40].mean(), mean_2020_2025=y[40:].mean(),
                         theil_sen_per_yr=sl, kendall_tau=tau, p=p,
                         first_year=int(sub.index[y > 0].min()) if (y > 0).any() else None,
                         last_year=int(sub.index[y > 0].max()) if (y > 0).any() else None))
tr = pd.DataFrame(rows)
tr.to_csv(f"{OUT}/t5_prescribed_trend.csv", index=False)
print(tr.to_string())
# NBAC cross-check: polygons flagged PRESCRIBED
nb = pyogrio.read_dataframe(f"{BASE}/data/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp", read_geometry=False,
                            columns=["YEAR", "PRESCRIBED", "ADMIN_NAME", "POLY_HA"])
nb = nb[nb.YEAR.between(1980, 2025)]
nb["pb"] = nb.PRESCRIBED.astype(str).str.lower().eq("true")
x = nb.groupby(["ADMIN_NAME", "pb"]).agg(n=("POLY_HA", "size"), ha=("POLY_HA", "sum")).unstack(fill_value=0)
x.columns = [f"{a}_{'pb' if b else 'other'}" for a, b in x.columns]
x.to_csv(f"{OUT}/t5_nbac_prescribed_by_admin.csv")
y = nb[nb.pb].groupby("YEAR").agg(n=("POLY_HA", "size"), ha=("POLY_HA", "sum"))
y.to_csv(f"{OUT}/t5_nbac_prescribed_by_year.csv")
print(x[x.n_pb > 0]); print(y.to_string())
