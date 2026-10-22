"""Apply the calibrated rule (calibration_rules.csv, fold 'all') and the uncalibrated analysis/losses rule to the
feature files of the given events. Counts Microsoft footprints flagged 'likely destroyed' by distance to the fire
polygon (inside, 0-250 m, 250-500 m, 500-1000 m outside). The 500-1000 m band is a false-positive check: few
buildings that far outside a mapped perimeter burn.
Burn-context filter (fixed, not tuned for precision): at least 20% of pixels 100-250 m from the building have dNBR >= 100
(USGS low severity or worse). 0.20 is the highest value that keeps every Jasper true positive (lowest observed 0.233);
it removes isolated changes (construction, harvest, clearing) away from any burned patch.
'likely_destroyed' = calibrated rule AND burn context; 'rule_only' = calibrated rule alone. usage: 07_apply_rule.py <event> [...] -> work/apply_<event>.csv"""
import os, sys, re
import numpy as np, pandas as pd
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rule = pd.read_csv(os.path.join(P, "calibration_rules.csv")).query("fold == 'all'").rule.iloc[0]
conds = [re.match(r"\s*(\w+)\s*>=\s*(-?[\d.]+)", c).groups() for c in rule.split("AND")]
def flag(df):
    m = np.ones(len(df), bool)
    for f, v in conds: m &= (df[f] >= float(v)).fillna(False).values
    return m
rows = []
for ev in sys.argv[1:]:
    d = pd.read_csv(os.path.join(P, "work", f"features_{ev}.csv")).query("set == 'microsoft'").copy()
    d["band"] = pd.cut(d.dist_fire_m.fillna(1e9), [-1, 0.5, 250, 500, 1000, 1e10], labels=["inside", "0-250 m", "250-500 m", "500-1000 m", ">1000 m"])
    d["rule_only"] = flag(d)
    d["burn_context"] = (d.dnbr_r100_250_share100 >= 0.20).fillna(False).values
    d["likely_destroyed"] = d.rule_only & d.burn_context
    d["old_rule"] = ((d.dnbr_bmax >= 440) & (d.dnbr_r20_60 >= 270)).values
    d["no_data"] = d[[f for f, _ in conds]].isna().any(axis=1)
    d.to_csv(os.path.join(P, "work", f"apply_{ev}.csv"), index=False)
    g = d.groupby("band", observed=False).agg(footprints=("x", "size"), likely_destroyed=("likely_destroyed", "sum"), rule_only=("rule_only", "sum"), old_rule=("old_rule", "sum"), no_data=("no_data", "sum"))
    g["share"] = (g.likely_destroyed / g.footprints).round(3)
    print(ev, rule); print(g.to_string())
