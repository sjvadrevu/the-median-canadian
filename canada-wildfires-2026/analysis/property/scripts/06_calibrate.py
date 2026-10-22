"""Calibrate the Sentinel-2 'likely destroyed' rule on official structure-status layers (Microsoft footprints labelled
by the official polygon they overlap; unlabelled footprints dropped). Positive = official 'Destroyed'.
Rules searched: building feature >= a AND ring feature >= b, over building features {dnbr_bmax, dnbr_bmed, dndvi_bmax}
and ring features {dnbr_r10_30, dnbr_r20_60, none}; a, b on a 10-unit grid. Selection criterion: F1.
Honest accuracy: 5-fold spatial cross-validation (500 m blocks; rule chosen on 4 folds, scored on the 5th).
Also scores the uncalibrated rules from analysis/losses (bmax>=440 & ring20-60>=270; lenient bmax>=270 & ring>=100).
usage: 06_calibrate.py features_<event>.csv [...]  -> calibration_rules.csv, calibration_accuracy.csv"""
import os, sys, itertools
import numpy as np, pandas as pd
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.concat([pd.read_csv(os.path.join(P, "work", f)) for f in sys.argv[1:]], ignore_index=True)
d = d[(d["set"] == "microsoft") & d.status.notna()].dropna(subset=["dnbr_bmax", "dnbr_r20_60"]).reset_index(drop=True)
d["y"] = (d.status == "Destroyed").astype(int)
print(d.groupby(["event", "status"]).size())
BF, RF = ["dnbr_bmax", "dnbr_bmed", "dndvi_bmax"], ["dnbr_r10_30", "dnbr_r20_60", None]
A = np.arange(0, 701, 10); B = np.arange(-50, 501, 10)
def scores(y, p):
    tp = int((p & (y == 1)).sum()); fp = int((p & (y == 0)).sum()); fn = int((~p & (y == 1)).sum()); tn = int((~p & (y == 0)).sum())
    pr = tp / (tp + fp) if tp + fp else np.nan; rc = tp / (tp + fn) if tp + fn else np.nan
    f1 = 2 * pr * rc / (pr + rc) if pr == pr and rc == rc and pr + rc else 0
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, precision=pr, recall=rc, f1=f1, predicted=tp + fp, actual=tp + fn)
def best(df):
    y = df.y.values; top = None
    for bf, rf in itertools.product(BF, RF):
        xb = df[bf].values[:, None] >= A[None, :]
        if rf is None:
            tp = (xb & (y[:, None] == 1)).sum(0); pp = xb.sum(0)
            f1 = 2 * tp / (pp + y.sum()); i = int(np.argmax(f1))
            cand = (f1[i], bf, A[i], rf, None)
        else:
            xr = df[rf].values
            for b in B:
                m = xb & (xr >= b)[:, None]
                tp = (m & (y[:, None] == 1)).sum(0); pp = m.sum(0); f1 = 2 * tp / (pp + y.sum()); i = int(np.argmax(f1))
                if top is None or f1[i] > top[0]: top = (f1[i], bf, A[i], rf, b)
            continue
        if top is None or cand[0] > top[0]: top = cand
    return top
def apply(df, r):
    _, bf, a, rf, b = r
    p = df[bf].values >= a
    return p & (df[rf].values >= b) if rf else p
# spatial blocks
rng = np.random.default_rng(42)
d["block"] = (np.floor(d.x / 500)).astype(int).astype(str) + "_" + (np.floor(d.y / 500)).astype(int).astype(str)
ub = d.block.unique(); fold = dict(zip(ub, rng.integers(0, 5, len(ub)))); d["fold"] = d.block.map(fold)
rows, pred = [], np.zeros(len(d), bool)
for k in range(5):
    tr, te = d.fold != k, d.fold == k
    r = best(d[tr]); pred[te.values] = apply(d[te], r)
    rows.append(dict(fold=k, rule=f"{r[1]}>={r[2]}" + (f" & {r[3]}>={r[4]}" if r[3] else ""), train_f1=round(r[0], 3), n_test=int(te.sum())))
cv = scores(d.y.values, pred)
final = best(d); pf = apply(d, final)
rule_txt = f"{final[1]} >= {final[2]}" + (f" AND {final[3]} >= {final[4]}" if final[3] else "")
acc = []
def add(name, p, sub=d):
    s = scores(sub.y.values, p); s.update(rule=name); acc.append(s)
add(f"calibrated, 5-fold spatial CV (rule re-fit per fold)", pred)
add(f"calibrated, in-sample: {rule_txt}", pf)
add("uncalibrated (analysis/losses): dnbr_bmax>=440 AND dnbr_r20_60>=270", (d.dnbr_bmax >= 440).values & (d.dnbr_r20_60 >= 270).values)
add("uncalibrated lenient: dnbr_bmax>=270 AND dnbr_r20_60>=100", (d.dnbr_bmax >= 270).values & (d.dnbr_r20_60 >= 100).values)
# destroyed-or-damaged target, calibrated rule
dd = d.assign(y=d.status.isin(["Destroyed", "Visible Damage"]).astype(int))
add("calibrated rule vs destroyed+visible damage", pf, dd)
acc = pd.DataFrame(acc)[["rule", "actual", "predicted", "tp", "fp", "fn", "tn", "precision", "recall", "f1"]].round(3)
acc.to_csv(os.path.join(P, "calibration_accuracy.csv"), index=False)
pd.DataFrame(rows + [dict(fold="all", rule=rule_txt, train_f1=round(final[0], 3), n_test=len(d))]).to_csv(os.path.join(P, "calibration_rules.csv"), index=False)
d.assign(pred_calibrated=pf, pred_cv=pred).to_csv(os.path.join(P, "work", "calibration_labelled.csv"), index=False)
print(pd.DataFrame(rows)); print(acc.to_string())
# sensitivity: precision/recall along the final rule's building threshold
_, bf, a, rf, b = final
sens = [dict(threshold=t, **scores(d.y.values, (d[bf].values >= t) & ((d[rf].values >= b) if rf else True))) for t in range(a - 100, a + 101, 20)]
pd.DataFrame(sens).round(3).to_csv(os.path.join(P, "calibration_sensitivity.csv"), index=False)
print(pd.DataFrame(sens).round(3)[["threshold", "predicted", "precision", "recall", "f1"]].to_string())
