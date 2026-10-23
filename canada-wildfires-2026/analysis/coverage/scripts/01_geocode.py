"""Geocode checklist communities with NRCan Geographical Names (geogratis) API.
Output: work/geocode.csv. Overrides: tuple (lat, lon) in checklist; 'CNFDB:<NFDBFIREID suffix>' uses the agency point."""
import json, os, sys, urllib.parse, urllib.request, zipfile
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from checklist import FIRES
W = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, '..', 'work', 'geocode.csv')
PROV = dict(NL=10, NS=12, NB=13, QC=24, ON=35, MB=46, SK=47, AB=48, BC=59, YT=60, NT=61)
POP = ['CITY', 'TOWN', 'VILG', 'UNP', 'HAM', 'IR', 'MUN1', 'MUN2', 'MUN3', 'RES', 'SET', 'CFB']

nfdb = None
rows = []
for f in FIRES:
    g = f['geo']
    if isinstance(g, tuple):
        rows.append(dict(name=f['name'], year=f['year'], lat=g[0], lon=g[1], geo_name='override (agency point)', geo_code=''))
        continue
    if g.startswith('CNFDB:'):
        if nfdb is None:
            z = zipfile.ZipFile(os.path.join(W, 'data/fire/raw/nfdb/NFDB_point_txt.zip'))
            nfdb = pd.read_csv(z.open('NFDB_point_20260811.txt'), low_memory=False, encoding='utf-8-sig')
        r = nfdb[nfdb.NFDBFIREID.str.endswith(g[6:])].iloc[0]
        rows.append(dict(name=f['name'], year=f['year'], lat=r.LATITUDE, lon=r.LONGITUDE, geo_name='CNFDB point ' + r.FIRE_ID, geo_code=''))
        continue
    q = urllib.parse.urlencode(dict(q=g, province=PROV[f['prov']]))
    d = json.load(urllib.request.urlopen(f'https://geogratis.gc.ca/services/geoname/en/geonames.json?{q}', timeout=60))
    items = [i for i in d['items'] if i['concise']['code'] in POP]
    exact = [i for i in items if i['name'].lower() == g.lower()]
    it = (exact or items or d['items'])[0]
    rows.append(dict(name=f['name'], year=f['year'], lat=it['latitude'], lon=it['longitude'], geo_name=it['name'], geo_code=it['concise']['code']))
pd.DataFrame(rows).to_csv(OUT, index=False)
print(pd.DataFrame(rows).to_string())
