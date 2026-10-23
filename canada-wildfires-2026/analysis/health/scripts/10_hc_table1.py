"""Extract Health Canada's 2023 acute health impacts of wildfire smoke (Matz et al. 2026, GeoHealth, Table 1)
from the Europe PMC full-text XML saved in raw/crf/matz2026.xml. Writes hc_matz2026_2023.csv (central, low, high)."""
import os
import re

import pandas as pd

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
t = open(os.path.join(H, "raw", "crf", "matz2026.xml"), encoding="utf-8").read()
tab = re.findall(r"<table-wrap[^>]*>.*?</table-wrap>", t, flags=re.S)[0]
rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tab, flags=re.S)
num = lambda s: float(s.replace(",", "").replace(" ", "").replace("$", "").replace("M", "e6").replace("B", "e9"))
out = []
for r in rows:
    cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, flags=re.S)]
    if len(cells) < 6 or not cells[5] or cells[5] == "2023":
        continue
    m = re.match(r"([\d, $.MB]+)\s*\[([\d, $.MB]+)[–-]([\d, $.MB]+)\]", cells[5])
    if not m:
        continue
    out.append(dict(outcome=re.sub(r"\s*[a-c]$", "", cells[0]), year=2023, central=num(m.group(1)), low=num(m.group(2)), high=num(m.group(3)),
                    source="Matz et al. 2026, GeoHealth, doi:10.1029/2025GH001565, Table 1 (Health Canada AQBAT)"))
df = pd.DataFrame(out)
df = df[~df.outcome.str.contains("death", case=False)]  # deaths are not used in this project
df.to_csv(os.path.join(H, "hc_matz2026_2023.csv"), index=False)
print(df[["outcome", "central", "low", "high"]].to_string())
