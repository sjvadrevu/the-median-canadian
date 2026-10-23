"""Area burned and fire counts by agency/year: NFD (1990-2025, final) + CWFIF ytd/by-agency (2026, preliminary).
Usage: python3 -I build_fire.py <smoke-cost dir>"""
import pandas as pd, json, sys, os
D = sys.argv[1]; R = os.path.join(D, 'raw/fire/nfdp_http/')
a = pd.read_csv(R + 'NFD - Area burned by cause class - EN FR.csv', encoding='latin-1'); a.columns = ['year'] + list(a.columns[1:])
n = pd.read_csv(R + 'NFD - Number of fires by cause class - EN FR.csv', encoding='latin-1'); n.columns = ['year'] + list(n.columns[1:])
A = a.groupby(['year', 'ISO', 'Jurisdiction'])['Area (hectares)'].sum().rename('area_burned_ha')
N = n.groupby(['year', 'ISO', 'Jurisdiction'])['Number'].sum().rename('fire_count')
t = pd.concat([A, N], axis=1).reset_index()
t['source'] = 'NFD (CCFM) cause-class tables, summed over causes; qualifier a; updated 2026-08-10'
t['status'] = 'final (agency-reported annual)'
c = json.load(open(os.path.join(D, 'raw/fire/ciffc/ytd_by-agency.json')))
names = {'AB': 'Alberta', 'BC': 'British Columbia', 'MB': 'Manitoba', 'NB': 'New Brunswick', 'NL': 'Newfoundland and Labrador',
         'NS': 'Nova Scotia', 'NT': 'Northwest Territories', 'ON': 'Ontario', 'PC': 'Parks Canada', 'PE': 'Prince Edward Island',
         'QC': 'Quebec', 'SK': 'Saskatchewan', 'YT': 'Yukon'}
cr = pd.DataFrame([dict(year=2026, ISO=r['agency_code'], Jurisdiction=names.get(r['agency_code'], r['agency_code']),
                        area_burned_ha=r['area_burned'], fire_count=r['fire_count'],
                        source='CWFIF reported-fire-stats ytd/by-agency (CIFFC statistics backend), as of ' + r['date'],
                        status='preliminary YTD (agency situation reports)') for r in c if r['agency_code'] != 'total'])
pd.concat([t, cr]).sort_values(['year', 'ISO']).to_csv(os.path.join(D, 'fire_area_count_by_agency_year.csv'), index=False)
