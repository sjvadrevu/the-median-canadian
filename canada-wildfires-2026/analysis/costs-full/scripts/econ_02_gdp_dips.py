"""econ_02_gdp_dips.py

Value added (GDP) lost in industries where Statistics Canada's monthly GDP releases attribute a
decline to wildfires, 2023 to 2025.

Data: Statistics Canada Table 36-10-0434-01 (GDP at basic prices by industry, monthly, seasonally
adjusted at annual rates, chained 2017 dollars). Converted to current dollars with the GDP implicit
price index (Table 36-10-0106-01, 2017=100) for the quarter of the event (economy-wide index; an
approximation for any single industry).

Loss in a month = (baseline - actual) / 12 (SAAR to monthly), floored at 0. Baseline = straight line
between the last month before the event and the first month after it (named per episode).
Attribution share (rule fixed before computing):
  - StatCan names wildfires as the cause:            low 50%, central 100%, high 100%
  - StatCan names wildfires plus other causes/"in part": low 0%,  central 50%,  high 100%
This is a computed estimate from official data; StatCan does not publish dollar impacts.

Usage: python3 -I econ_02_gdp_dips.py BASE_DIR
"""
import csv, os, sys

BASE = sys.argv[1]
T = os.path.join(BASE, 'raw/econ/statcan_tables')
OUT = os.path.join(BASE, 'work')

gdp = {}
with open(os.path.join(T, '36100434/36100434.csv'), encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['Seasonal adjustment'] == 'Seasonally adjusted at annual rates' and r['Prices'] == 'Chained (2017) dollars' and r['VALUE']:
            n = r['North American Industry Classification System (NAICS)']
            gdp.setdefault(n[n.rfind('['):], {})[r['REF_DATE']] = float(r['VALUE']) * 1e6

ipi = {}
with open(os.path.join(T, '36100106/36100106.csv'), encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['Estimates'] == 'Gross domestic product at market prices' and r['Index'] == 'Implicit price indexes' and r['VALUE']:
            ipi[r['REF_DATE']] = float(r['VALUE'])

def quarter_key(ym):
    y, m = map(int, ym.split('-'))
    qm = ((m - 1) // 3) * 3 + 1
    return f'{y}-{qm:02d}'

def add_months(ym, k):
    y, m = map(int, ym.split('-'))
    m += k
    while m > 12:
        m -= 12; y += 1
    while m < 1:
        m += 12; y -= 1
    return f'{y}-{m:02d}'

SHARES = {'sole': (0.5, 1.0, 1.0), 'partial': (0.0, 0.5, 1.0)}

# episode: (id, naics, label, before_month, after_month, months_affected, attribution, statcan quote, release url, overlaps)
EP = [
    ('gdp_og_2023', '[21111]', 'Oil and gas extraction (except oil sands), Canada', '2023-04', '2023-07', ['2023-05', '2023-06'], 'sole',
     'Oil and gas extraction (except oil sands) dropped 6.6% as a result of the forest fires in Alberta.',
     'https://www150.statcan.gc.ca/n1/daily-quotidien/230728/dq230728a-eng.htm', 'econ_oilgas_2023 (same loss, valued as production)'),
    ('gdp_iron_2023', '[21221]', 'Iron ore mining, Canada (Quebec and Labrador)', '2023-05', '2023-07', ['2023-06'], 'partial',
     'a 35.0% drop in the iron ore mining industry as a combination of wildfires and maintenance severely impacted production in northern Quebec and in Newfoundland and Labrador',
     'https://www150.statcan.gc.ca/n1/daily-quotidien/230901/dq230901b-eng.htm', 'none in bill'),
    ('gdp_rail_2023', '[482]', 'Rail transportation, Canada', '2023-05', '2023-07', ['2023-06'], 'sole',
     'wildfires also negatively impacted the rail transportation subsector (-6.6%)',
     'https://www150.statcan.gc.ca/n1/daily-quotidien/230901/dq230901b-eng.htm', 'partly the same event as iron ore (carloadings)'),
    ('gdp_accom_2023', '[721]', 'Accommodation services, Canada', '2023-04', '2023-10', ['2023-05', '2023-06', '2023-07', '2023-08', '2023-09'], 'partial',
     'Accommodation services (-1.6%) posted its first quarterly decline in the last five quarters in the second quarter, as forest fires which began in late April in Canada, coupled with poor air quality associated with fires, restrained or indirectly discouraged activity in recreational vehicle (RV) parks and recreational camps.',
     'https://www150.statcan.gc.ca/n1/daily-quotidien/230901/dq230901b-eng.htm', 'none in bill'),
    ('gdp_forestry_2023', '[113]', 'Forestry and logging, Canada', '2023-04', '2023-10', ['2023-05', '2023-06', '2023-07', '2023-08', '2023-09'], 'partial',
     'Growing drought and forest fires impact several sectors ... Forestry and logging (-4.5%) and fishing, hunting and trapping (-9.8%) were also down in the quarter',
     'https://www150.statcan.gc.ca/n1/daily-quotidien/230901/dq230901b-eng.htm', 'timber line values the standing trees burned (a stock); this is lost harvest activity (a flow); weak lumber markets are a confounder'),
    ('gdp_rail_2024', '[482]', 'Rail transportation, Canada (Jasper)', '2024-06', '2024-09', ['2024-07'], 'partial',
     'a 4.0% decline in July that resulted in part from the Jasper wildfires that temporarily halted some rail freight movements to and from key ports on the British Columbia Coast',
     'https://www150.statcan.gc.ca/n1/daily-quotidien/241031/dq241031a-eng.htm', 'none in bill; August 2024 excluded (rail lockout)'),
    ('gdp_iron_2024', '[21221]', 'Iron ore mining, Canada (Labrador and northern Quebec)', '2024-06', '2024-08', ['2024-07'], 'sole',
     'several iron ore mines temporarily shut down their operations in July in response to wildfires burning in regions of Labrador and Northern Quebec, contributing to a 4.8% decline in iron ore mining',
     'https://www150.statcan.gc.ca/n1/daily-quotidien/240927/dq240927a-eng.htm', 'none in bill'),
    ('gdp_accom_2024', '[721]', 'Accommodation services, Canada (western tourist destinations)', '2024-06', '2024-08', ['2024-07'], 'partial',
     'Accommodation services declined 2.0% in July, due in part to forest fires occurring at tourist destinations in Western Canada during the summer tourist season.',
     'https://www150.statcan.gc.ca/n1/daily-quotidien/240927/dq240927a-eng.htm', 'overlaps Jasper business interruption inside insured losses and the Parks Canada revenue line'),
    ('gdp_oilsands_2025', '[21114]', 'Oil sands extraction, Canada', '2025-04', '2025-06', ['2025-05'], 'partial',
     'several oil extraction facilities ramped up production following maintenance and wildfires disruptions around some facilities in May',
     'https://www150.statcan.gc.ca/n1/daily-quotidien/250829/dq250829b-eng.htm', 'econ_oilgas_2025 (same loss, valued as production)'),
]

rows = []
for (eid, code, label, b, a, months, attr, quote, url, ov) in EP:
    s = gdp[code]
    vb, va = s[b], s[a]
    # month index distance for interpolation
    def idx(ym):
        y, m = map(int, ym.split('-')); return y * 12 + m
    n = idx(a) - idx(b)
    loss_real = 0.0
    loss_nom = 0.0
    per = []
    for mth in months:
        k = idx(mth) - idx(b)
        base = vb + (va - vb) * k / n
        act = s[mth]
        l = max(0.0, base - act) / 12.0
        p = ipi[quarter_key(mth)] / 100.0
        loss_real += l
        loss_nom += l * p
        per.append(f'{mth}: base {base/1e6:,.0f} actual {act/1e6:,.0f} (SAAR $M 2017)')
    lo, ce, hi = SHARES[attr]
    rows.append(dict(id=eid, naics=code, industry=label, months=';'.join(months), baseline=f'{b} to {a} straight line',
                     attribution=attr, loss_real2017_full=round(loss_real), loss_nominal_full=round(loss_nom),
                     low=round(loss_nom * lo), central=round(loss_nom * ce), high=round(loss_nom * hi),
                     statcan_quote=quote, url=url, overlaps=ov, detail=' | '.join(per)))

with open(os.path.join(OUT, 'econ_gdp_dips.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
for r in rows:
    print(f"{r['id']:18s} {r['industry'][:50]:50s} full ${r['loss_nominal_full']/1e6:7.1f}M  low {r['low']/1e6:6.1f} central {r['central']/1e6:6.1f} high {r['high']/1e6:6.1f}")
    print('    ', r['detail'])
