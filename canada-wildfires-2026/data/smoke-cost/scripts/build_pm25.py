"""Build station-daily and city-daily PM2.5 for Canada, 2018-01-01 .. latest.

Sources
- NAPS validated hourly PM2.5 (ECCC), 2018-2024: raw/naps/PM25_YYYY.csv
- AirNow daily PM2.5-24hr (real-time, unvalidated): May-Sep 2018-2026 archive (people/airnow_daily)
  plus raw/airnow/daily_extra (2025-01-01 .. 2026-10-19, non May-Sep dates)
- NAPS station list (coords, StatCan population centre code): raw/naps/StationsNAPS-StationsSNPA.csv
- StatCan 2021 population centres (table 98-10-0011): raw/statcan/98100011.csv

Rules
- NAPS daily mean = mean of valid hours (value != -999) when >= 18 valid hours; else missing.
- Co-located NAPS instruments (several method codes for same station-date): keep the instrument
  with most valid hours; ties broken by lowest method code. Count recorded in n_instruments.
- AirNow AQSID -> NAPS ID = last 6 characters (prefixes 000 / CC0 vary by year).
- Primary series per station-date: NAPS validated if present, else AirNow real-time.
- City value = mean across stations reporting that day; max station also given.
"""
import glob, io, os, sys
import pandas as pd
import numpy as np

BASE = sys.argv[1]  # .../wildfire
RAW = os.path.join(BASE, 'data/smoke-cost/raw')
OUT = os.path.join(BASE, 'data/smoke-cost')

# ---------- stations ----------
lines = open(f'{RAW}/naps/StationsNAPS-StationsSNPA.csv', encoding='utf-8-sig').read().splitlines()
end = next(i for i, l in enumerate(lines) if l.startswith('"**********Definitions'))
st = pd.read_csv(io.StringIO('\n'.join([lines[4]] + lines[6:end])), dtype=str)
st = st.rename(columns={'Province/Territory_EN': 'Province'})
st['pc_code'] = st['PC'].str.extract(r'^(\d{4})\.')[0]

# ---------- NAPS hourly -> daily ----------
frames = []
for y in range(2018, 2025):
    f = f'{RAW}/naps/PM25_{y}.csv'
    with open(f, encoding='utf-8-sig', errors='replace') as fh:
        skip = next(i for i, l in enumerate(fh) if l.startswith('Pollutant//'))
    d = pd.read_csv(f, skiprows=skip, encoding='utf-8-sig', encoding_errors='replace', dtype={2: str})
    d.columns = [c.split('//')[0].strip() for c in d.columns]
    hrs = [c for c in d.columns if c.startswith('H') and c[1:].isdigit()]
    v = d[hrs].replace(-999, np.nan)
    d['n_hours'] = v.notna().sum(axis=1)
    d['pm25'] = v.mean(axis=1)
    d = d.sort_values(['NAPS ID', 'Date', 'n_hours', 'Method Code'], ascending=[True, True, False, True])
    ninst = d.groupby(['NAPS ID', 'Date']).size().rename('n_instruments')
    d = d.drop_duplicates(['NAPS ID', 'Date']).join(ninst, on=['NAPS ID', 'Date'])
    d.loc[d.n_hours < 18, 'pm25'] = np.nan
    frames.append(d[['NAPS ID', 'Date', 'pm25', 'n_hours', 'n_instruments', 'Method Code']])
naps = pd.concat(frames).rename(columns={'NAPS ID': 'naps_id', 'Date': 'date', 'Method Code': 'method_code'})
naps['date'] = pd.to_datetime(naps['date'])
naps['source'] = 'NAPS_validated'

# ---------- AirNow daily ----------
files = glob.glob(f'{RAW}/airnow/daily_mayseptember/pm25_*.txt') + glob.glob(f'{RAW}/airnow/daily_extra/pm25_*.txt')
rows = []
for f in files:
    for l in open(f, encoding='latin-1'):
        p = l.rstrip('\n').split('|')
        if len(p) < 8 or p[3] != 'PM2.5-24hr':
            continue
        sid = p[1]
        # Canadian AirNow IDs: 9-char 000xxxxxx / CC0xxxxxx, or 12-char 124 + (000|CC0) + NAPS id (from 2022)
        if not ((len(sid) == 9 and sid[:3] in ('000', 'CC0')) or (len(sid) == 12 and sid.startswith('124'))):
            continue
        rows.append((p[0], sid, p[2], p[5], p[7].strip()))
an = pd.DataFrame(rows, columns=['date', 'aqsid', 'site', 'pm25', 'agency'])
an['date'] = pd.to_datetime(an['date'], format='%m/%d/%y')
an['pm25'] = pd.to_numeric(an['pm25'], errors='coerce')
an['naps_id'] = an['aqsid'].str[-6:]
an = an.sort_values(['naps_id', 'date', 'aqsid']).drop_duplicates(['naps_id', 'date'])
an['source'] = 'AirNow_realtime'
# AirNow sites not in the 2024 NAPS station list: take coordinates/name from AirNow site file
loc = pd.read_csv(f'{RAW}/airnow/Monitoring_Site_Locations_V2.dat', sep='|', dtype=str)
loc = loc[(loc.CountryFIPS == 'CA') & (loc.Parameter == 'PM2.5')].copy()
loc['naps_id'] = loc.AQSID.str[-6:]
loc = loc[loc.Latitude.astype(float) != 0].drop_duplicates('naps_id')
extra = an[~an.naps_id.isin(st.NAPS_ID)].drop_duplicates('naps_id')[['naps_id', 'site', 'agency']]
extra = extra.merge(loc[['naps_id', 'Latitude', 'Longitude']], on='naps_id', how='left')
extra.to_csv(f'{OUT}/airnow_sites_not_in_naps_list.csv', index=False)
st = pd.concat([st, pd.DataFrame({'NAPS_ID': extra.naps_id, 'Station_Name': extra.site + ' (AirNow name)',
                                  'City': None, 'Province': None, 'Latitude': extra.Latitude,
                                  'Longitude': extra.Longitude, 'PM2.5_Continuous': 'AirNow-only'})],
               ignore_index=True)

# ---------- station-daily (both sources, long) ----------
sd = pd.concat([
    naps[['naps_id', 'date', 'pm25', 'source', 'n_hours', 'n_instruments', 'method_code']],
    an[['naps_id', 'date', 'pm25', 'source', 'aqsid', 'agency']],
], ignore_index=True)
sd = sd.merge(st[['NAPS_ID', 'Station_Name', 'City', 'Province', 'Latitude', 'Longitude', 'PC', 'CMA/CA']],
              left_on='naps_id', right_on='NAPS_ID', how='left').drop(columns='NAPS_ID')
sd = sd[sd.pm25.notna()]
sd['date'] = sd['date'].dt.date
sd.sort_values(['naps_id', 'date', 'source']).to_csv(f'{OUT}/station_daily_pm25_2018_2026.csv', index=False)

# primary: NAPS if available else AirNow
sd['rank'] = (sd.source != 'NAPS_validated').astype(int)
prim = sd.sort_values('rank').drop_duplicates(['naps_id', 'date'])

# ---------- validation: AirNow vs NAPS overlap ----------
ov = naps.merge(an, on=['naps_id', 'date'], suffixes=('_naps', '_an')).dropna(subset=['pm25_naps', 'pm25_an'])
ov['diff'] = ov.pm25_an - ov.pm25_naps
val = ov.groupby(ov.date.dt.year).agg(n=('diff', 'size'), mean_diff=('diff', 'mean'),
                                       mad=('diff', lambda x: x.abs().median()),
                                       r=('diff', lambda x: np.corrcoef(ov.loc[x.index, 'pm25_naps'], ov.loc[x.index, 'pm25_an'])[0, 1]))
val.round(3).to_csv(f'{OUT}/validation_airnow_vs_naps.csv')

# ---------- city definitions ----------
pc = pd.read_csv(f'{RAW}/statcan/98100011.csv')
pc = pc[pc.DGUID.str.contains('S0510', na=False)].copy()
popcol = pc.columns[4]
pc['pc_code'] = pc.DGUID.str[-4:]
pc = pc.sort_values(popcol, ascending=False).head(30)
cities = []
for rank, r in enumerate(pc.itertuples(), 1):
    ids = st[(st.pc_code == r.pc_code) & st['PM2.5_Continuous'].notna()].NAPS_ID.tolist()
    cities.append(dict(city=r.GEO, group='top30_popcentre_2021', pop_rank_2021=rank,
                       population_2021=getattr(r, '_5'), pc_code=r.pc_code, naps_ids=ids))
# northern / fire-region towns: NAPS City field match (stations with continuous PM2.5)
towns = {
    'Whitehorse': ['WHITEHORSE'], 'Yellowknife': ['YELLOWKNIFE'], 'Inuvik': ['INUVIK'],
    'Norman Wells': ['NORMAN WELLS'], 'Fort Smith': ['FORT SMITH'], 'Fort Simpson': ['FORT SIMPSON'],
    'Iqaluit': ['IQALUIT'], 'Fort McMurray': ['FORT MCMURRAY'], 'Fort Chipewyan': ['FORT CHIPEWYAN'],
    'Fort McKay': ['FORT MCKAY'], 'Grande Prairie': ['GRANDE PRAIRIE'], 'Hinton': ['HINTON'], 'Edson': ['EDSON'],
    'Cold Lake': ['COLD LAKE'], 'Fort St. John': ['FORT ST. JOHN'], 'Fort Nelson': ['FORT NELSON'],
    'Prince George': ['PRINCE GEORGE'], 'Quesnel': ['QUESNEL'], 'Williams Lake': ['WILLIAMS LAKE'],
    'Kamloops': ['KAMLOOPS'], 'Vernon': ['VERNON'], 'Penticton': ['PENTICTON'], 'Castlegar': ['CASTLEGAR'],
    'Cranbrook': ['CRANBROOK'], 'Golden': ['GOLDEN'], 'Smithers': ['SMITHERS'], 'Burns Lake': ['BURNS LAKE'],
    'Vanderhoof': ['VANDERHOOF'], 'Houston BC': ['HOUSTON'], 'Prince Albert': ['PRINCE ALBERT'],
    'Buffalo Narrows': ['BUFFALO NARROWS'], 'Flin Flon': ['FLIN FLON'], 'Thompson': ['THOMPSON'],
    'Brandon': ['BRANDON'], 'Thunder Bay': ['THUNDER BAY'], 'Sudbury': ['SUDBURY'],
    'Sault Ste. Marie': ['SAULT STE. MARIE'], 'North Bay': ['NORTH BAY'], 'Rouyn-Noranda': ['ROUYN-NORANDA'],
    'Labrador City': ['LABRADOR CITY'],
}
top_ids = {i for c in cities for i in c['naps_ids']}
for name, keys in towns.items():
    m = st['PM2.5_Continuous'].notna() & st.City.str.upper().isin(keys)
    ids = st[m].NAPS_ID.tolist()
    # AirNow-only stations (not yet in NAPS 2024 station list), assigned by AirNow site name
    ids += {'Thunder Bay': ['060808'], 'Penticton': ['100605']}.get(name, [])
    cities.append(dict(city=name, group='north_fire_region', pop_rank_2021=None, population_2021=None,
                       pc_code=None, naps_ids=ids))

# ---------- city-daily ----------
out, meta = [], []
for c in cities:
    s = prim[prim.naps_id.isin(c['naps_ids'])]
    for yr in range(2018, 2027):
        sy = s[pd.to_datetime(s.date).dt.year == yr]
        meta.append(dict(city=c['city'], year=yr, stations_reporting=';'.join(sorted(sy.naps_id.unique())),
                         n_days=sy.date.nunique(),
                         days_naps=sy[sy.source == 'NAPS_validated'].date.nunique(),
                         days_airnow=sy[sy.source == 'AirNow_realtime'].date.nunique()))
    if s.empty:
        continue
    g = s.groupby('date').agg(pm25_mean_of_stations=('pm25', 'mean'), pm25_max_station=('pm25', 'max'),
                              n_stations=('pm25', 'size'),
                              n_naps_validated=('source', lambda x: (x == 'NAPS_validated').sum()),
                              n_airnow_realtime=('source', lambda x: (x == 'AirNow_realtime').sum()),
                              stations=('naps_id', lambda x: ';'.join(sorted(x)))).reset_index()
    g.insert(0, 'city', c['city']); g.insert(1, 'group', c['group'])
    g['data_status'] = np.where(g.n_airnow_realtime == 0, 'validated',
                                np.where(g.n_naps_validated == 0, 'realtime', 'mixed'))
    out.append(g)
cd = pd.concat(out)
cd['pm25_mean_of_stations'] = cd.pm25_mean_of_stations.round(2)
cd.to_csv(f'{OUT}/city_daily_pm25_2018_2026.csv', index=False)

defs = pd.DataFrame([{**c, 'naps_ids': ';'.join(c['naps_ids'])} for c in cities])
sn = st.set_index('NAPS_ID')
defs['station_names'] = [';'.join(f"{i}:{sn.loc[i,'Station_Name']}" for i in c['naps_ids']) for c in cities]
defs.to_csv(f'{OUT}/city_station_map.csv', index=False)
pd.DataFrame(meta).to_csv(f'{OUT}/city_year_coverage.csv', index=False)

st[st['PM2.5_Continuous'].notna()][['NAPS_ID', 'Station_Name', 'Status', 'City', 'Province', 'Latitude', 'Longitude',
    'Start_Date', 'End_Date', 'PM2.5_Continuous', 'PC', 'CMA/CA', 'Urbanization']].to_csv(
    f'{OUT}/stations_pm25_naps.csv', index=False)

print('station-daily rows', len(sd), 'NAPS', (sd.source == 'NAPS_validated').sum(), 'AirNow', (sd.source == 'AirNow_realtime').sum())
print('city-daily rows', len(cd), 'cities with data', cd.city.nunique(), 'of', len(cities))
print('date range', cd.date.min(), cd.date.max())
print(val.round(2))
