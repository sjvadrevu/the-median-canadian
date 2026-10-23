"""econ_03_property_checks.py

1. Insured losses (industry, CatIQ via IBC/CatIQ releases) compared with the bill's building values
   (analysis/property/destroyed_value_estimates.csv: flagged buildings x DA average dwelling value).
2. Buildings missing from the bill or under-counted, valued the same way the bill values official counts
   (official count x 2021 Census average value of owner-occupied dwellings, CSD, else CD).

Usage: python3 -I econ_03_property_checks.py BASE_DIR PROPERTY_DIR
Writes work/econ_property_insured_vs_bill.csv and work/econ_property_topups.csv
"""
import csv, os, sys

BASE, PROP = sys.argv[1], sys.argv[2]
OUT = os.path.join(BASE, 'work')

est = {r['event']: r for r in csv.DictReader(open(os.path.join(PROP, 'destroyed_value_estimates.csv')))}
off = {r['event']: r for r in csv.DictReader(open(os.path.join(PROP, 'destroyed_value_official.csv')))}

def census(level_file, code, char):
    for r in csv.DictReader(open(os.path.join(PROP, 'raw', 'census', level_file))):
        if r['ALT_GEO_CODE'] == code and r['CHARACTERISTIC'] == char and r['OBS_VALUE']:
            return float(r['OBS_VALUE'])
    return None

def value(csd, cd):
    avg = census('csd_dwelling_value_2021.csv', csd, '1475') if csd else None
    med = census('csd_dwelling_value_2021.csv', csd, '1474') if csd else None
    src = f'CSD {csd}'
    if avg is None:
        avg = census('cd_dwelling_value_2021.csv', cd, '1475'); med = census('cd_dwelling_value_2021.csv', cd, '1474'); src = f'CD {cd}'
    return avg, med, src

# ---- 1. insured vs bill (industry figures; 'over' = lower bound as published) ----
INS = [
    # event key in bill, label, insured CAD, qualifier, stage, source url
    ('tantallon2023', 'Upper Tantallon NS 2023', 247.5e6, 'about', 'one-year (CatIQ via IBC report, July 2024)',
     'https://a.storyblok.com/f/339220/645121db60/one-year-update-following-2023-nova-scotia-wildfires-and-flooding.pdf'),
    ('mcdougall2023', 'McDougall Creek BC 2023', 480e6, 'over', 'initial (Oct 2023)',
     'https://www.ibc.ca/news-insights/news/okanagan-and-shuswap-area-wildfires-cause-over-720-million-in-insured-damage'),
    ('bushcreek2023', 'Bush Creek East BC 2023', 240e6, 'over', 'initial (Oct 2023)',
     'https://www.ibc.ca/news-insights/news/okanagan-and-shuswap-area-wildfires-cause-over-720-million-in-insured-damage'),
    ('jasper2024', 'Jasper AB 2024', 1304e6, 'exact', 'final, two years (July 2026)',
     'https://public.catiq.com/2026/07/23/catiq-discloses-final-industry-loss-estimate-for-jasper-wildfire-complex-of-july-2024-second-estimate-for-prairies-severe-weather-outbreak-of-june-2026/'),
    ('denare2025', 'Flin Flon complex MB/SK 2025 (bill covers Denare Beach only)', 249e6, 'exact', 'update (Sept 2025)',
     'https://www.ibc.ca/news-insights/news/insured-damage-from-manitoba-and-saskatchewan-wildfires-nears-300-million'),
    ('baldrange2026', 'Bald Range BC 2026', 293e6, 'exact', '45-day (Oct 2026)',
     'https://public.catiq.com/2026/10/06/catiq-discloses-third-loss-estimate-for-june-july-severe-storm-event-in-ontario-and-quebec-updated-loss-for-bald-range-fire/'),
]
rows = []
for key, label, ins, q, stage, url in INS:
    bill = float(est[key]['proxy_value_avg_cad'])
    rows.append(dict(event=label, bill_key=key, insured_cad=ins, insured_qualifier=q, insured_stage=stage,
                     bill_building_value_cad=round(bill), ratio_insured_to_bill=round(ins / bill, 2),
                     insured_minus_bill_cad=round(ins - bill), url=url))
tot_ins = sum(r['insured_cad'] for r in rows); tot_bill = sum(r['bill_building_value_cad'] for r in rows)
rows.append(dict(event='Six events with both', bill_key='', insured_cad=tot_ins, insured_qualifier='sum', insured_stage='',
                 bill_building_value_cad=tot_bill, ratio_insured_to_bill=round(tot_ins / tot_bill, 2),
                 insured_minus_bill_cad=round(tot_ins - tot_bill), url=''))
with open(os.path.join(OUT, 'econ_property_insured_vs_bill.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for r in rows:
    print(f"{r['event'][:50]:50s} insured {r['insured_cad']/1e6:8.1f}  bill {r['bill_building_value_cad']/1e6:7.1f}  ratio {r['ratio_insured_to_bill']:5.2f}  excess {r['insured_minus_bill_cad']/1e6:8.1f}")

# ---- 2. top-ups (official counts) ----
top = []
# 2a. Barrington Lake NS 2023: official 230 destroyed vs 72 flagged in the bill
b_off_avg = float(off['barrington2023']['proxy_value_avg_cad']); b_off_med = float(off['barrington2023']['proxy_value_median_cad'])
b_bill = float(est['barrington2023']['proxy_value_avg_cad'])
top.append(dict(item='Barrington Lake NS 2023: official count above flagged count', count_low=230, count_central=230, count_high=230,
                value_source='DA average (property/destroyed_value_official.csv)',
                low=b_off_med - b_bill, central=b_off_avg - b_bill, high=b_off_avg - b_bill,
                note='230 destroyed (HRFE citing the Barrington after-action review) x local value, minus the bill value for 72 flagged buildings'))
# 2b. SHOE fire / Denare Beach SK 2025: about 400 permanent residences (region) + about a dozen commercial
d_off_avg = float(off['denare2025']['proxy_value_avg_cad']); d_off_med = float(off['denare2025']['proxy_value_median_cad'])
d_bill = float(est['denare2025']['proxy_value_avg_cad'])
d_local_avg = float(off['denare2025']['local_avg_value'])
top.append(dict(item='SHOE fire, Denare Beach region SK 2025: official count above flagged count', count_low=400, count_central=400, count_high=412,
                value_source='DA/CD average (property/destroyed_value_official.csv)',
                low=max(0.0, d_off_med - d_bill), central=d_off_avg - d_bill, high=d_off_avg + 12 * d_local_avg - d_bill,
                note='about 400 permanent residences (MNP review for Government of Saskatchewan); high adds about a dozen commercial and resort properties at the same local value'))
# 2c. Enterprise NT 2023: 80 to 90 percent of structures lost; 51 private dwellings (2021 Census, 98-10-0015)
ea, em, es = value('6105003', '6105')
top.append(dict(item='Enterprise NT 2023 (not in bill)', count_low=0.8 * 51, count_central=0.85 * 51, count_high=0.9 * 51,
                value_source=es, low=0.8 * 51 * min(ea, em), central=0.85 * 51 * ea, high=0.9 * 51 * max(ea, em),
                note='80 to 90 percent of structures lost (NWT 2023 Wildfire Response Review); applied to 51 private dwellings'))
# 2d. Hay River NT 2023: 4 homes Patterson Road + 3 or 4 Paradise Gardens + 2 cabins
ha, hm, hs = value('6105016', '6105')
top.append(dict(item='Hay River NT 2023, Patterson Road and Paradise Gardens (not in bill)', count_low=7, count_central=9, count_high=10,
                value_source=hs, low=7 * hm, central=9 * ha, high=10 * ha,
                note='4 homes Patterson Road, 3 or 4 Paradise Gardens, 2 cabins (NWT 2023 Wildfire Response Review)'))
# 2e. Behchoko NT 2023: 4 structures confirmed; 15 burned along Highway 3 and 3 more reported
ba, bm, bs = value('6103031', '6103')
top.append(dict(item='Behchoko NT 2023 (not in bill)', count_low=4, count_central=4, count_high=22,
                value_source=bs, low=4 * bm, central=4 * ba, high=22 * ba,
                note='4 structures confirmed; high adds 15 structures burned along Highway 3 and 3 more reported (NWT 2023 Wildfire Response Review)'))
# 2f. Saskatchewan 2025 other structures: about 700 lost in the season (SPSA estimate); about 400 + 12 in the SHOE region
sa, sm, ss = value(None, '4718')
top.append(dict(item='Saskatchewan 2025 structures outside the SHOE region (not in bill)', count_low=288, count_central=288, count_high=345,
                value_source=ss + ' (Division No. 18)', low=288 * sm, central=288 * sa, high=345 * sa,
                note='about 700 structures lost in 2025 (SPSA estimate, MNP review) minus about 412 in the SHOE region (high: minus the 355 flagged in the bill)'))
with open(os.path.join(OUT, 'econ_property_topups.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(top[0].keys())); w.writeheader()
    for t in top:
        w.writerow({k: (round(v, 1) if isinstance(v, float) else v) for k, v in t.items()})
for t in top:
    print(f"{t['item'][:70]:70s} {t['low']/1e6:7.2f} {t['central']/1e6:7.2f} {t['high']/1e6:7.2f}  ({t['value_source']})")
print('sum topups', sum(t['low'] for t in top) / 1e6, sum(t['central'] for t in top) / 1e6, sum(t['high'] for t in top) / 1e6)
