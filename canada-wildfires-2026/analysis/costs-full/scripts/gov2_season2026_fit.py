"""Fit season cost against area burned (official data) to estimate 2026 costs where no in-year update exists.

Inputs: Ontario Public Accounts Emergency Forest Firefighting (net, nominal, fiscal year = season),
SK Provincial Auditor season costs (2025 dollars), NFD/CWFIF area burned by agency.
Model: cost_2025$ = a + b * area_ha (OLS), plus a log-log check. Low/high = 10th/90th percentile of
leave-one-out prediction errors added to the central prediction (empirical band, n small).
"""
import os, sys, json
import numpy as np, pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
AN = os.path.abspath(os.path.join(D, '..', '..'))
area = pd.read_csv(os.path.join(AN, '..', 'data', 'smoke-cost', 'fire_area_count_by_agency_year.csv'))
cpi = {2015: 126.6, 2016: 128.4, 2017: 130.4, 2018: 133.4, 2019: 136.0, 2020: 137.0, 2021: 141.6,
       2022: 151.2, 2023: 157.1, 2024: 160.9, 2025: 157.1 * 1.045033, 2026: 157.1 * 1.045033 / 0.975604}
to25 = {y: cpi[2025] / v for y, v in cpi.items()}

on_nom = {2015: 94.864, 2016: 107.2, 2017: 117.289, 2018: 207.844, 2019: 136.04, 2020: 121.071,
          2021: 248.883, 2022: 95.897, 2023: 206.473, 2024: 171.041, 2025: 272.996}
sk_25 = {2016: 24.3, 2017: 46.8, 2018: 38.1, 2019: 11.9, 2020: 24.2, 2021: 110.0, 2022: 51.0,
         2023: 98.5, 2024: 95.2, 2025: 351.6}

def fit(name, cost25, iso):
    a = area[area.ISO == iso].set_index('year')['area_burned_ha']
    yrs = sorted(cost25)
    x = np.array([a[y] for y in yrs]) / 1e5   # per 100,000 ha
    y = np.array([cost25[y] for y in yrs])
    A = np.vstack([np.ones_like(x), x]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    # leave-one-out errors
    errs = []
    for i in range(len(yrs)):
        m = np.ones(len(yrs), bool); m[i] = False
        c, *_ = np.linalg.lstsq(A[m], y[m], rcond=None)
        errs.append(y[i] - (c[0] + c[1] * x[i]))
    errs = np.array(errs)
    x26 = a[2026] / 1e5
    central = coef[0] + coef[1] * x26
    lo = central + np.percentile(errs, 10)
    hi = central + np.percentile(errs, 90)
    out = dict(name=name, years=yrs, intercept_m=round(coef[0], 2), slope_m_per_100k_ha=round(coef[1], 2),
               area_2026_ha=int(a[2026]), central_2025d_m=round(central, 1), low_2025d_m=round(lo, 1),
               high_2025d_m=round(hi, 1), loo_err_p10=round(np.percentile(errs, 10), 1),
               loo_err_p90=round(np.percentile(errs, 90), 1))
    print(json.dumps(out))
    return out

res = [fit('ON Emergency Forest Firefighting (net)', {y: v * to25[y] for y, v in on_nom.items()}, 'ON'),
       fit('SK SPSA season wildfire cost', sk_25, 'SK')]
json.dump(res, open(os.path.join(AN, 'costs-full', 'work', 'gov2_season2026_fit.json'), 'w'), indent=1)
