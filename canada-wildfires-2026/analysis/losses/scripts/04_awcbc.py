"""AWCBC National Work Injury, Disease and Fatality Statistics 2022-2024 (publication PDF, created 2026-07-14):
accepted fatalities for event codes 46 (aircraft accident), 50/51/59 (fire) from Table 28 and for industry
'Agriculture, Forestry, Fishing and Hunting' from Table 36, Canada total by year. Context only: AWCBC public
tables do not identify wildfire, wildland firefighters or forestry separately from agriculture/fishing."""
import os, re, subprocess
import pandas as pd

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(L, "raw", "awcbc")
txt = os.path.join(R, "nwisp.txt")
if not os.path.exists(txt):
    subprocess.run(["pdftotext", "-layout", os.path.join(R, "NWISP-2022-2024.pdf"), txt], check=True)
lines = open(txt, encoding="utf-8").read().splitlines()

def block(title):
    idx = [i for i, l in enumerate(lines) if l.strip().startswith(title)]
    return idx

def rows_after(start, code, n=12):
    """Return {year: total} for event code row starting at line with '^\\s*code\\s'."""
    out = {}
    for i in range(start, min(start + 400, len(lines))):
        if re.match(rf"^\s*{code}\s+\S", lines[i]):
            for j in range(i, i + n):
                m = re.search(r"\s(2022|2023|2024)\s+([\dX,x]+)\s", lines[j])
                if m and m.group(1) not in out:
                    out[m.group(1)] = m.group(2)
            break
    return out

res = []
t28 = block("Number of Fatalities, by Event and Jurisdiction,")
for code, name in [(46, "Aircraft accident"), (50, "Fire or explosion, unspecified"), (51, "Fire"), (59, "Fire or explosion, n.e.c.")]:
    for s in t28:
        r = rows_after(s, code)
        if r:
            for y, v in r.items():
                res.append(dict(table="Table 28 fatalities by event", category=f"{code} {name}", year=int(y), canada_total=v))
            break
t36 = block("Number of Fatalities, by Industry and Jurisdiction,")
for s in t36:
    for i in range(s, s + 120):
        if "Agriculture, Forestry" in lines[i] or "Agriculture, forestry" in lines[i]:
            for j in range(i, i + 8):
                m = re.search(r"\s(2022|2023|2024)\s+([\dX,x]+)\s", lines[j])
                if m:
                    res.append(dict(table="Table 36 fatalities by industry", category="11 Agriculture, Forestry, Fishing and Hunting", year=int(m.group(1)), canada_total=m.group(2)))
            break
    if any(r["table"].startswith("Table 36") for r in res):
        break
df = pd.DataFrame(res).drop_duplicates(["table", "category", "year"]).sort_values(["category", "year"])
df["note"] = "X = 3 or fewer (suppressed). Not wildfire-specific."
df.to_csv(os.path.join(L, "awcbc_fatalities_context_2022_2024.csv"), index=False)
print(df.to_string())
