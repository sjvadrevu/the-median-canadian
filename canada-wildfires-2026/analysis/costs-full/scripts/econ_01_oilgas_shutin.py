"""econ_01_oilgas_shutin.py

Oil and gas production lost (shut in) to wildfires in Alberta, 2023 and 2025, valued at
official average prices.

Volumes: Statistics Canada Table 25-10-0055-01 (marketable natural gas, GJ, monthly, by province)
and Table 25-10-0063-01 (crude oil and equivalent, barrels, monthly, by province and type).
Prices: Alberta Energy and Minerals "Monthly Reference Price Calculations" (gas reference price,
NGX Alberta market price, pentanes plus par price) and AER ST-3 "Oil Prices" (APMC average Crown
sales prices for light, medium and ultra heavy crude, $/m3). WCS settlement price and exchange rate
from Alberta's "BVM Components 2025" (high case for bitumen).

Counterfactual (computed, not published by any agency):
  expected daily production in month m of year Y = (mean daily production in March and April of Y)
  x ratio r_m, where r_m = (month m daily) / (March-April daily) in non-fire comparison years.
  Shortfall = expected - actual (floored at 0), times days in month.
  Central = median comparison-year ratio; low = lowest ratio; high = highest ratio.
Episodes valued: May and June 2023 (west-central Alberta gas, light and medium crude, pentanes plus;
StatCan attributes the May 2023 drop to forest fires), May and June 2025 (Alberta in situ bitumen;
StatCan cites wildfire shutdowns in late May 2025 alongside maintenance).
Validation episode (not added): May and June 2016 (Fort McMurray), all oil sands.

Usage: python3 -I econ_01_oilgas_shutin.py BASE_DIR
"""
import csv, calendar, sys, statistics, os, json

BASE = sys.argv[1]
T = os.path.join(BASE, 'raw/econ/statcan_tables')
OUT = os.path.join(BASE, 'work')
M3_PER_BBL = 0.158987295

def load_gas():
    d = {}
    with open(os.path.join(T, '25100055/25100055.csv'), encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['Supply and disposition'] == 'Marketable production' and r['UOM'] == 'Gigajoules' and r['VALUE']:
                d.setdefault(r['GEO'], {})[r['REF_DATE']] = float(r['VALUE']) * 1e3  # thousands of GJ -> GJ
    return d

def load_oil():
    d = {}
    with open(os.path.join(T, '25100063/25100063.csv'), encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['UOM'] == 'Barrels' and r['VALUE']:
                d.setdefault((r['GEO'], r['Supply and disposition']), {})[r['REF_DATE']] = float(r['VALUE'])
    return d

def daily(series, y, m):
    k = f'{y}-{m:02d}'
    if k not in series:
        return None
    return series[k] / calendar.monthrange(y, m)[1]

def ref(series, y):
    a, b = daily(series, y, 3), daily(series, y, 4)
    return (a + b) / 2

def shortfall(series, year, months, comp_years):
    rows = []
    for m in months:
        ratios = [daily(series, cy, m) / ref(series, cy) for cy in comp_years]
        r_med, r_lo, r_hi = statistics.median(ratios), min(ratios), max(ratios)
        base = ref(series, year)
        act = daily(series, year, m)
        days = calendar.monthrange(year, m)[1]
        out = {}
        for tag, r in (('low', r_lo), ('central', r_med), ('high', r_hi)):
            out[tag] = max(0.0, base * r - act) * days
        rows.append(dict(year=year, month=m, days=days, ref_daily=base, actual_daily=act,
                         ratio_low=r_lo, ratio_central=r_med, ratio_high=r_hi,
                         actual_ratio=act / base,
                         short_low=out['low'], short_central=out['central'], short_high=out['high']))
    return rows

gas = load_gas()
oil = load_oil()

# Official prices (copied from the downloaded PDFs; see econ_manifest.csv)
# Alberta Energy and Minerals, Monthly Reference Price Calculations, May and June 2023 / 2025
GAS_RP = {(2023, 5): 2.00, (2023, 6): 1.94, (2025, 5): 1.65, (2025, 6): 1.05}          # $/GJ, gas reference price
GAS_AMP = {(2023, 5): 2.268, (2023, 6): None, (2025, 5): None, (2025, 6): None}        # $/GJ NGX AMP (filled below if parsed)
PENT_PAR = {(2023, 5): 559.85, (2023, 6): 538.00}                                       # $/m3 pentanes plus par price
# AER ST-3 Oil Prices (APMC average Crown sales price, $/m3)
AER_LIGHT = {(2023, 5): 545.46, (2023, 6): 517.94, (2025, 5): 481.42, (2025, 6): 537.82}
AER_MED = {(2023, 5): 522.12, (2023, 6): 473.96, (2025, 5): 458.00, (2025, 6): 509.38}
AER_UHEAVY = {(2025, 5): 403.35, (2025, 6): 456.19, (2016, 5): None, (2016, 6): None}
# Alberta BVM components 2025: WCS settlement price (US$/bbl) and exchange rate (C$/US$)
WCS = {(2025, 5): (51.57, 1.38600), (2025, 6): (58.22, 1.36740)}

amp_path = os.path.join(OUT, 'econ_ab_gas_amp.json')
if os.path.exists(amp_path):
    GAS_AMP.update({tuple(map(int, k.split('-'))): v for k, v in json.load(open(amp_path)).items()})

results = []
detail = []

def add(item, rows, unit, price_fn_c, price_fn_lo=None, price_fn_hi=None, note=''):
    tot = {'low': 0.0, 'central': 0.0, 'high': 0.0}
    vol = {'low': 0.0, 'central': 0.0, 'high': 0.0}
    for r in rows:
        y, m = r['year'], r['month']
        pc = price_fn_c(y, m)
        pl = price_fn_lo(y, m) if price_fn_lo else pc
        ph = price_fn_hi(y, m) if price_fn_hi else pc
        for tag, p in (('low', pl), ('central', pc), ('high', ph)):
            v = r['short_' + tag]
            vol[tag] += v
            tot[tag] += v * p
        detail.append(dict(item=item, unit=unit, **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()},
                           price_central=pc, price_low=pl, price_high=ph))
    results.append(dict(item=item, unit=unit, vol_low=vol['low'], vol_central=vol['central'], vol_high=vol['high'],
                        value_low=tot['low'], value_central=tot['central'], value_high=tot['high'], note=note))

# ---- 2023 episode ----
COMP_2023 = [2017, 2018, 2019, 2021, 2022, 2024]   # exclude 2016 (fire), 2020 (COVID), 2023, 2025 (fire years)
g = shortfall(gas['Alberta'], 2023, [5, 6], COMP_2023)
add('AB marketable natural gas 2023', g, 'GJ',
    lambda y, m: GAS_RP[(y, m)], None,
    lambda y, m: GAS_AMP.get((y, m)) or GAS_RP[(y, m)],
    'central/low at Alberta gas reference price; high at NGX Alberta market price where parsed')
lm = shortfall(oil[('Alberta', 'Light and medium crude oil')], 2023, [5, 6], COMP_2023)
add('AB light and medium crude oil 2023', lm, 'bbl',
    lambda y, m: AER_LIGHT[(y, m)] * M3_PER_BBL,
    lambda y, m: AER_MED[(y, m)] * M3_PER_BBL,
    lambda y, m: AER_LIGHT[(y, m)] * M3_PER_BBL,
    'central/high at AER APMC light crude price; low at medium crude price')
pp = shortfall(oil[('Alberta', 'Pentanes plus')], 2023, [5, 6], COMP_2023)
add('AB pentanes plus 2023', pp, 'bbl',
    lambda y, m: PENT_PAR[(y, m)] * M3_PER_BBL, None, None,
    'Alberta pentanes plus par price')
# BC gas check (StatCan does not attribute a BC drop to fire)
gbc = shortfall(gas['British Columbia'], 2023, [5, 6], COMP_2023)
add('BC marketable natural gas 2023 (check only)', gbc, 'GJ', lambda y, m: GAS_RP[(y, m)], None, None,
    'check only, not added: no official statement links BC gas output to fire')

# ---- 2025 episode ----
COMP_2025 = [2017, 2018, 2019, 2021, 2022, 2023, 2024]   # exclude 2016 (fire), 2020 (COVID)
ins = shortfall(oil[('Alberta', 'In-Situ crude bitumen production')], 2025, [5, 6], COMP_2025)
# StatCan (Energy statistics, May 2025): fires "temporarily shut down some production towards the end of
# the month"; the rest of the May drop is attributed to maintenance. Central case therefore counts only
# 4 of 31 May days (May 28 to 31) of the May shortfall; the high case keeps all of May.
for r in ins:
    if r['month'] == 5:
        r['short_central'] = r['short_central'] * 4 / 31
        r['short_low'] = 0.0
def wcs_cad_bbl(y, m):
    p, fx = WCS[(y, m)]
    return p * fx
add('AB in situ bitumen 2025', ins, 'bbl',
    lambda y, m: AER_UHEAVY[(y, m)] * M3_PER_BBL, None, wcs_cad_bbl,
    'central/low at AER APMC ultra heavy crude price; high at WCS settlement price (BVM component) in C$')
# checks for 2025 conventional and gas
g25 = shortfall(gas['Alberta'], 2025, [5, 6], COMP_2023[:-1] + [2024])
add('AB marketable natural gas 2025 (check only)', g25, 'GJ', lambda y, m: GAS_RP[(y, m)], None, None, 'check only')

# ---- 2016 validation (Fort McMurray), volumes only ----
COMP_2016 = [2017, 2018, 2019, 2021, 2022, 2023, 2024]
v16 = {}
for comp in ['In-Situ crude bitumen production', 'Mined crude bitumen production', 'Crude oil production']:
    rows = shortfall(oil[('Alberta', comp)], 2016, [5, 6], COMP_2016)
    v16[comp] = {t: sum(r['short_' + t] for r in rows) for t in ('low', 'central', 'high')}

with open(os.path.join(OUT, 'econ_oilgas_shutin_detail.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(detail[0].keys()))
    w.writeheader(); w.writerows(detail)
with open(os.path.join(OUT, 'econ_oilgas_shutin_summary.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    w.writeheader()
    for r in results:
        w.writerow({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()})

for r in results:
    print(f"{r['item']:45s} vol {r['vol_low']/1e6:7.2f} {r['vol_central']/1e6:7.2f} {r['vol_high']/1e6:7.2f} M{r['unit']}  "
          f"value ${r['value_low']/1e6:7.1f} {r['value_central']/1e6:7.1f} {r['value_high']/1e6:7.1f} M")
for d in detail:
    print(d['item'][:30], d['year'], d['month'], 'actual ratio', round(d['actual_ratio'], 3), 'ratios', round(d['ratio_low'], 3), round(d['ratio_central'], 3), round(d['ratio_high'], 3))
print('2016 validation (million bbl, May-June):', {k: {t: round(v / 1e6, 1) for t, v in x.items()} for k, x in v16.items()})
