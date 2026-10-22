"""Ontario Parks visitation (data.ontario.ca 'Visitation to Provincial Parks', calendar years 2020-2025, by park and zone).
Zone totals and the Northwest zone (where the 2021, 2025 and 2026 Ontario fires burned) against the other zones.
Ministry data notes are kept verbatim in the output. Output: ontario_parks_zone_visitation.csv, ontario_parks_nw_parks.csv"""
import pandas as pd
from vcommon import RAW, OUT
f = RAW / "parks" / "on_parks_visitation_2025.xlsx"
d = pd.read_excel(f, sheet_name="Data")
d.columns = ["zone", "park", "year", "day", "camper", "total", "occ"] + list(d.columns[7:])
d["total"] = pd.to_numeric(d.total, errors="coerce")
z = d.pivot_table(index="zone", columns="year", values="total", aggfunc="sum")
z.loc["All zones"] = z.sum()
z.loc["All except Northwest"] = z.drop(index=["Northwest/Nord-Ouest", "All zones"]).sum()
z.to_csv(OUT / "ontario_parks_zone_visitation.csv")
nw = d[d.zone.str.startswith("Northwest")].pivot_table(index="park", columns="year", values="total", aggfunc="sum")
nw.to_csv(OUT / "ontario_parks_nw_parks.csv")
pd.set_option("display.width", 200)
print(z.round(0).to_string())
print(nw.sort_values(2024, ascending=False).head(25).round(0).to_string())
