"""Gap 4: rebuild Health Canada's AQBAT acute morbidity estimates for 2024, 2025 and 2026 from our own
population-weighted smoke exposure, anchored so that 2023 reproduces Health Canada's Table 1.

No death counts or death values are used anywhere in this script.

Inputs (our own computed files, analysis/health):
  work/dates.csv, work/R50_da_combo.csv, work/R50_combo_inc.npy (daily PM2.5 increment above the station-month
  2018-2024 median, the same increment as exposure_by_group.csv), work/R50_combo_pm.npy (coverage), work/da_attr.csv
  hc_matz2026_2023.csv (Health Canada 2023 counts) and raw/crf/matz2026.txt + GH2-10-e2025GH001565-s001.docx
  (Table 1 for 2019-2022 and Table S.1 coefficients; every number is checked against the saved text)
Downloaded (costs-full/raw/health2/census): Census 2021 counts aged 5-9, 10-14, 15-19 by dissemination area (SDMX API).

Method (AQBAT works on seasonal means, so this does too):
  For outcome k with coefficient beta_k = ln(1 + pct_k/100) / 10 and age weight w_k:
    S(k, y) = sum over dissemination areas of  w_k(DA) x cov(DA, y) x (1 - exp(-beta_k x mean_inc(DA, y)))
  where mean_inc is the May-September mean of the daily increment over the days the DA had a station within 50 km,
  and cov is the share of the 153 season days covered.
  Anchor: count(k, y) = HC(k, 2023) x S(k, y) / S(k, 2023). This sets one national baseline rate per outcome
  so that our 2023 exposure reproduces Health Canada's 2023 count exactly; baseline rates are assumed uniform
  across provinces and constant over years.
  Provinces whose monitors stop (MB, NL, NT in 2025 and 2026; under 50% of person-days covered): exposure imputed
  from neighbours (central: mean of the neighbours' seasonal means; high: the highest neighbour; low: no imputation).
  Back-test: the same anchoring predicts 2019-2022, which are compared with Health Canada's own Table 1 values.
  Range: Health Canada's 2023 95% interval combined (in quadrature, on the log scale) with the back-test error range.

Outputs (costs-full/): health2_aqbat_counts.csv, health2_aqbat_backtest.csv, health2_aqbat_province_shares.csv
"""
import os
import re
import zipfile
import html

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CF = os.path.dirname(HERE)
AN = os.path.dirname(CF)
H = os.path.join(AN, "health")
WK = os.path.join(H, "work")
R2 = os.path.join(CF, "raw", "health2")


def norm(t):
    return re.sub(r"\s+", " ", t.replace(" ", " ").replace("\xa0", " "))


# ------------------------------------------------------------------ Health Canada numbers, checked against saved text
MATZ = norm(open(os.path.join(H, "raw", "crf", "matz2026.txt"), encoding="utf-8").read())
T1 = {  # outcome: {year: (central, low, high)} from Matz et al. 2026 Table 1 (2019-2022); 2023 from hc_matz2026_2023.csv
    "Respiratory emergency room visits": {2019: (220, 140, 290), 2020: (330, 220, 440), 2021: (1200, 770, 1600), 2022: (210, 140, 290)},
    "Cardiac emergency room visits": {2019: (74, 40, 110), 2020: (120, 65, 180), 2021: (420, 220, 610), 2022: (74, 39, 110)},
    "Respiratory hospital admissions": {2019: (43, 28, 57), 2020: (66, 43, 88), 2021: (230, 150, 310), 2022: (42, 28, 57)},
    "Cardiac hospital admissions": {2019: (56, 30, 83), 2020: (93, 50, 140), 2021: (320, 170, 470), 2022: (56, 30, 82)},
    "Asthma symptom days": {2019: (140000, 30000, 260000), 2020: (230000, 49000, 420000), 2021: (780000, 160000, 1400000), 2022: (140000, 30000, 260000)},
    "Child acute bronchitis episodes": {2019: (2800, 0, 6400), 2020: (4600, 0, 10000), 2021: (15000, 0, 34000), 2022: (2800, 0, 6400)},
    "Restricted activity days": {2019: (870000, 530000, 1200000), 2020: (1500000, 910000, 2100000), 2021: (4700000, 2900000, 6500000), 2022: (850000, 520000, 1200000)},
    "Acute respiratory symptom days": {2019: (1600000, 0, 3200000), 2020: (2700000, 0, 5500000), 2021: (8700000, 0, 18000000), 2022: (1600000, 0, 3200000)},
}
for q in ["Respiratory emergency room visits 220 [140–290] 330 [220–440] 1,200 [770–1,600] 210 [140–290]",
          "Cardiac emergency room visits 74 [40–110] 120 [65–180] 420 [220–610] 74 [39–110]",
          "Respiratory hospital admissions 43 [28–57] 66 [43–88] 230 [150–310] 42 [28–57]",
          "Cardiac hospital admissions 56 [30–83] 93 [50–140] 320 [170–470] 56 [30–82]",
          "Asthma symptom days c 140,000 [30,000–260,000] 230,000 [49,000–420,000] 780,000 [160,000–1,400,000] 140,000 [30,000–260,000]",
          "Child acute bronchitis episodes 2,800 [0–6,400] 4,600 [0–10,000] 15,000 [0–34,000] 2,800 [0–6,400]",
          "Restricted activity days 870,000 [530,000–1,200,000] 1,500,000 [910,000–2,100,000] 4,700,000 [2,900,000–6,500,000] 850,000 [520,000–1,200,000]",
          "Acute respiratory symptom days 1,600,000 [0–3,200,000] 2,700, 000 [0–5,500,000] 8,700,000 [0–18,000,000] 1,600,000 [0–3,200,000]"]:
    assert norm(q) in MATZ, q
hc23 = pd.read_csv(os.path.join(H, "hc_matz2026_2023.csv")).set_index("outcome")
for k in T1:
    T1[k][2023] = tuple(float(hc23.loc[k, c]) for c in ("central", "low", "high"))

# Table S.1 coefficients (percent per 10 ug/m3, mean, 2.5%, 97.5%) and age groups, checked against the SI docx
z = zipfile.ZipFile(os.path.join(H, "raw", "crf", "GH2-10-e2025GH001565-s001.docx"))
SI = norm(html.unescape(re.sub(r"<[^>]+>", " ", z.read("word/document.xml").decode("utf-8"))))
CRF = {"Respiratory emergency room visits": (0.75, 0.5, 1.01, "all"),
       "Cardiac emergency room visits": (0.71, 0.38, 1.04, "all"),
       "Respiratory hospital admissions": (0.75, 0.5, 1.01, "all"),
       "Cardiac hospital admissions": (0.71, 0.38, 1.04, "all"),
       "Asthma symptom days": (6.54, 1.36, 11.73, "5-19"),
       "Child acute bronchitis episodes": (9.34, -2.31, 22.37, "5-19"),
       "Restricted activity days": (4.93, 2.87, 7.03, "5+"),
       "Acute respiratory symptom days": (2.66, -0.06, 5.38, "5+")}
for frag in ["Respiratory Hospital Admissions all 0.75 0.5 1.01 Normal Burnett et al., 1995",
             "Cardiac Hospital Admissions all 0.71 0.38 1.04 Normal Burnett et al., 1995",
             "Respiratory Emergency Room Visits all 0.75 0.5 1.01 Normal",
             "Cardiac Emergency Room Visits all 0.71 0.38 1.04 Normal",
             "Child Acute Bronchitis Episodes 5-19 9.34 -2.31 22.37 Normal",
             "Asthma Symptom Days 5-19 (asthmatics) 6.54 1.36 11.73 Normal",
             "Restricted Activity Days 5-19 (non-asthma), 20+ 4.93 2.87 7.03 Normal",
             "Acute Respiratory Symptom Days 5-19 (non-asthma), 20+ 2.66 -0.06 5.38 Normal"]:
    assert norm(frag) in SI.replace(" | ", " "), frag


def beta(pct):
    return np.log(1 + pct / 100.0) / 10.0


# ------------------------------------------------------------------ exposure and population weights
dates = pd.to_datetime(pd.read_csv(os.path.join(WK, "dates.csv")).date)
yr, mo = dates.dt.year.values, dates.dt.month.values
inc = np.load(os.path.join(WK, "R50_combo_inc.npy"))
pm = np.load(os.path.join(WK, "R50_combo_pm.npy"))
dmap = pd.read_csv(os.path.join(WK, "R50_da_combo.csv"), dtype={"DAUID": str})
da = pd.read_csv(os.path.join(WK, "da_attr.csv"), dtype={"DAUID": str, "DGUID": str}).merge(dmap[["DAUID", "combo"]], on="DAUID")
ag = pd.read_csv(os.path.join(R2, "census", "da_profile_age_5_19.csv"), usecols=["REF_AREA", "CHARACTERISTIC", "OBS_VALUE"],
                 dtype={"REF_AREA": str})
assert set(ag.CHARACTERISTIC.unique()) == {11, 12, 14}
a519 = ag.pivot_table(index="REF_AREA", columns="CHARACTERISTIC", values="OBS_VALUE", aggfunc="first")
a519 = (a519[11] + a519[12] + a519[14]).rename("age_5_19")
da = da.merge(a519, left_on="DGUID", right_index=True, how="left")
pop = da.pop2021.fillna(0).values
has_age = da.age_total.notna() & da.age_5_19.notna()
sh519 = da.loc[has_age, "age_5_19"].sum() / da.loc[has_age, "age_total"].sum()
sh04 = da.loc[da.age_total.notna(), "age_0_4"].sum() / da.loc[da.age_total.notna(), "age_total"].sum()
w519 = np.where(has_age, da.age_5_19.fillna(0) / da.age_total.where(da.age_total > 0, np.nan) * pop, sh519 * pop)
w519 = np.nan_to_num(w519)
w5p = np.where(da.age_total.notna(), pop - np.nan_to_num(da.age_0_4.fillna(0) / da.age_total.where(da.age_total > 0, np.nan) * pop), (1 - sh04) * pop)
W = {"all": pop, "5-19": w519, "5+": np.maximum(w5p, 0)}
prov = da.prov.values
PROVS = sorted(set(prov))
combo = da.combo.values

season = {}
for y in range(2018, 2027):
    sel = (yr == y) & (mo >= 5) & (mo <= 9)
    P, I = pm[:, sel], inc[:, sel]
    ncov = np.isfinite(P).sum(1)
    s_inc = np.where(np.isfinite(I), I, 0).sum(1)
    mean_c = np.where(ncov > 0, s_inc / np.maximum(ncov, 1), 0.0)
    season[y] = (mean_c[combo], (ncov / sel.sum())[combo])

# province coverage share and pop-weighted seasonal mean (for the imputation rule)
pc = []
for y, (m, c) in season.items():
    for p in PROVS:
        s = prov == p
        cp = (pop[s] * c[s]).sum()
        pc.append(dict(year=y, prov=p, cov_share=cp / pop[s].sum(), mean_inc=(pop[s] * c[s] * m[s]).sum() / cp if cp > 0 else np.nan))
pc = pd.DataFrame(pc)
cov_typ = np.mean([season[y][1] for y in range(2018, 2025)], axis=0)        # DA's typical coverage, 2018-2024
REF = {"MB": ["SK", "ON"], "NL": ["QC", "NS"], "NT": ["AB", "YT"]}        # neighbours used for imputation


def S_prov(k, y, b, mode):
    """Exposure term by province for outcome k, year y, coefficient b; mode = 'none' / 'central' / 'high' imputation."""
    m, c = season[y]
    w = W[CRF[k][3]]
    out = {}
    for p in PROVS:
        s = prov == p
        row = pc[(pc.year == y) & (pc.prov == p)].iloc[0]
        if row.cov_share >= 0.5 or p == "NU":
            out[p] = float((w[s] * c[s] * (1 - np.exp(-b * m[s]))).sum())
        elif p in REF and mode != "none":
            refm = pc[(pc.year == y) & pc.prov.isin(REF[p])].mean_inc
            mi = refm.mean() if mode == "central" else refm.max()
            out[p] = float((w[s] * cov_typ[s] * (1 - np.exp(-b * mi))).sum())
        else:
            out[p] = 0.0
    return out


rows, shares, bt = [], [], []
for k, (pc_c, pc_lo, pc_hi, grp) in CRF.items():
    b = beta(pc_c)
    S23 = sum(S_prov(k, 2023, b, "central").values())
    ratio = {}
    for y in range(2018, 2027):
        ratio[y] = {md: sum(S_prov(k, y, b, md).values()) / S23 for md in ("none", "central", "high")}
    # back-test against Health Canada 2019-2022
    errs = []
    for y in (2019, 2020, 2021, 2022):
        pred = T1[k][2023][0] * ratio[y]["central"]
        errs.append(np.log(T1[k][y][0] / pred))
        bt.append(dict(outcome=k, year=y, hc_central=T1[k][y][0], predicted_central=round(pred, 1),
                       hc_over_predicted=round(T1[k][y][0] / pred, 3)))
    e_lo, e_hi = min(errs), max(errs)          # log(HC / predicted)
    c23, l23, h23 = T1[k][2023]
    crf_lo = np.log(l23 / c23) if l23 > 0 else -np.inf
    crf_hi = np.log(h23 / c23)
    for y in range(2019, 2027):
        r = ratio[y]
        cen = c23 * r["central"]
        lo = 0.0 if not np.isfinite(crf_lo) else c23 * r["none"] * np.exp(-np.sqrt(crf_lo ** 2 + min(e_lo, 0) ** 2))
        hi = c23 * r["high"] * np.exp(np.sqrt(crf_hi ** 2 + max(e_hi, 0) ** 2))
        official = y <= 2023
        rows.append(dict(outcome=k, year=y, source="Health Canada Table 1 (official)" if official else "our AQBAT rebuild anchored to 2023",
                         central=T1[k][y][0] if official else round(cen, 1),
                         low=T1[k][y][1] if official else round(lo, 1),
                         high=T1[k][y][2] if official else round(hi, 1),
                         rebuild_central=round(cen, 1), ratio_to_2023_central=round(r["central"], 4),
                         ratio_to_2023_no_imputation=round(r["none"], 4), ratio_to_2023_high_imputation=round(r["high"], 4),
                         backtest_log_err_min=round(e_lo, 3), backtest_log_err_max=round(e_hi, 3)))
    if k == "Respiratory emergency room visits" or k == "Respiratory hospital admissions":
        for y in range(2023, 2027):
            sp = S_prov(k, y, b, "central")
            tot = sum(sp.values())
            for p, v in sp.items():
                shares.append(dict(outcome=k, year=y, prov=p, share=v / tot if tot else 0.0,
                                   imputed=bool(pc[(pc.year == y) & (pc.prov == p)].cov_share.iloc[0] < 0.5 and p in REF),
                                   cov_share=round(float(pc[(pc.year == y) & (pc.prov == p)].cov_share.iloc[0]), 3),
                                   popw_mean_increment=round(float(pc[(pc.year == y) & (pc.prov == p)].mean_inc.iloc[0]), 3)))

out = pd.DataFrame(rows)
out.to_csv(os.path.join(CF, "health2_aqbat_counts.csv"), index=False)
pd.DataFrame(bt).to_csv(os.path.join(CF, "health2_aqbat_backtest.csv"), index=False)
pd.DataFrame(shares).to_csv(os.path.join(CF, "health2_aqbat_province_shares.csv"), index=False)

pd.set_option("display.width", 250)
print(out[out.year >= 2023][["outcome", "year", "central", "low", "high", "ratio_to_2023_central", "ratio_to_2023_no_imputation",
                             "ratio_to_2023_high_imputation", "backtest_log_err_min", "backtest_log_err_max"]].to_string(index=False))
print(pd.DataFrame(bt).pivot(index="outcome", columns="year", values="hc_over_predicted").to_string())
print(pc[pc.year >= 2023].pivot(index="prov", columns="year", values="cov_share").round(2).to_string())
print("5-19 share", round(sh519, 4), "0-4 share", round(sh04, 4))
