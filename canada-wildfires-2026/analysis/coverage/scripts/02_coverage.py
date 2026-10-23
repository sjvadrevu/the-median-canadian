"""Coverage check: are publicly reported major fires 2023 to 2026 in our outline data?
Inputs: NBAC 2023-2025 polygons, CWFIS M3 2026 polygons (file of 2026-10-20), outline classes
(analysis/outline-check), CNFDB points 2023-2025 (names/IDs), CWFIF 2026 fire list points (IDs).
Rule: candidate outlines = same year, within RADIUS km of the reported location, first/last dates
overlapping the reported start date +/- DATE_WIN days. Chosen outline = largest candidate.
Cluster area = sum of all candidates (M3 splits one fire into several polygons)."""
import os, re, sys, json, zipfile
import resource
import numpy as np, pandas as pd, geopandas as gpd, pyogrio
from shapely.geometry import Point
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from checklist import FIRES
W = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUTD = os.path.abspath(os.path.join(HERE, '..'))
RADIUS = 30_000
DATE_WIN = 45
CRS = 'EPSG:3978'

geo = pd.read_csv(os.path.join(OUTD, 'work', 'geocode.csv'))

# --- outlines ---
NBAC = os.path.join(W, 'data/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp')
NBAC_CRS = pyogrio.read_info(NBAC)['crs']


def read_nbac(year, lon, lat, half=40_000):
    """Read NBAC polygons of one year inside a box around the point (memory-safe)."""
    p = gpd.GeoSeries([Point(lon, lat)], crs='EPSG:4326').to_crs(NBAC_CRS).iloc[0]
    nb = pyogrio.read_dataframe(NBAC, where=f'YEAR = {year}', bbox=(p.x - half, p.y - half, p.x + half, p.y + half))
    if len(nb) == 0:
        return None
    gids = "','".join(sorted(nb.GID.astype(str).unique()))
    nb = pyogrio.read_dataframe(NBAC, where=f"GID IN ('{gids}')")  # all parts (NBAC splits a fire by province)
    nb = nb.set_crs(NBAC_CRS, allow_override=True).to_crs(CRS)
    nb['year'] = nb.YEAR.astype(int)
    nb['oid'] = 'NBAC ' + nb.GID.astype(str)
    nb['area_ha'] = nb.geometry.area / 1e4
    nb['first'] = pd.concat([pd.to_datetime(nb.HS_SDATE, errors='coerce'), pd.to_datetime(nb.AG_SDATE, errors='coerce')], axis=1).min(axis=1)
    nb['last'] = pd.concat([pd.to_datetime(nb.HS_EDATE, errors='coerce'), pd.to_datetime(nb.AG_EDATE, errors='coerce'), pd.to_datetime(nb.CAPDATE, errors='coerce')], axis=1).max(axis=1)
    nb['src'], nb['oclass'] = 'NBAC', ''
    nb = nb.dissolve(by='oid', aggfunc=dict(src='first', year='first', first='min', last='max', oclass='first')).reset_index()
    nb['area_ha'] = nb.geometry.area / 1e4
    return gpd.GeoDataFrame(nb[cols], geometry='geometry', crs=CRS)


cols = ['oid', 'src', 'year', 'area_ha', 'first', 'last', 'oclass', 'geometry']
m3 = gpd.read_file(os.path.join(W, 'data/fire/m3_perimeters_2026_cwfis_20261020.gpkg')).to_crs(CRS)
cls = gpd.read_file(os.path.join(W, 'analysis/outline-check/outline_class_2026.geojson'))[['fire_uid', 'class']]
m3 = m3.merge(cls, left_on='UID', right_on='fire_uid', how='left')
m3['year'] = 2026
m3['oid'] = 'M3 ' + m3.UID.astype(str)
m3['area_ha'] = m3.area_ha_albers
m3['first'] = pd.to_datetime(m3.FIRSTDATE.str[:10])
m3['last'] = pd.to_datetime(m3.LASTDATE.str[:10])
m3['src'], m3['oclass'] = 'M3', m3['class'].fillna('')
M3 = gpd.GeoDataFrame(m3[cols], geometry='geometry', crs=CRS)

# --- agency points (IDs / names) ---
z = zipfile.ZipFile(os.path.join(W, 'data/fire/raw/nfdb/NFDB_point_txt.zip'))
cn = pd.read_csv(z.open('NFDB_point_20260811.txt'), low_memory=False, encoding='utf-8-sig')
cn = cn[cn.YEAR >= 2023]
cn = gpd.GeoDataFrame(cn, geometry=gpd.points_from_xy(cn.LONGITUDE, cn.LATITUDE), crs='EPSG:4326').to_crs(CRS)
cn['aid'] = cn.FIRE_ID.astype(str).str.strip()
cn['aname'] = cn.FIRENAME.astype(str).str.strip()
cn['asize'] = cn.SIZE_HA
cn['ayear'] = cn.YEAR
fl = pd.DataFrame(json.load(open(os.path.join(W, 'data/fire/reference/nrcan_fire_list.json'))))
fl = fl[fl.fire_year == 2026]
fl = gpd.GeoDataFrame(fl, geometry=gpd.points_from_xy(fl.longitude, fl.latitude), crs='EPSG:4326').to_crs(CRS)
fl['aid'] = fl.agency_code + ' ' + fl.agency_fire_id.astype(str)
fl['aname'], fl['asize'], fl['ayear'] = '', fl.fire_size, 2026
AG = pd.concat([cn[['aid', 'aname', 'asize', 'ayear', 'geometry']], fl[['aid', 'aname', 'asize', 'ayear', 'geometry']]], ignore_index=True)
AG = gpd.GeoDataFrame(AG, geometry='geometry', crs=CRS)


def norm_id(s):
    """'HWF-036-2023' -> 'HWF36'; 'THU_FIRE_036' -> 'THU36'; '2023-G80280' -> 'G80280'."""
    s = str(s).upper().replace('_FIRE_', '')
    s = re.sub(r'^(19|20)\d\d-?', '', s)
    s = re.sub(r'-(19|20)?\d\d$', '', s) if re.match(r'^[A-Z]{2,3}-?\d', s) else s
    return re.sub(r'(?<=[A-Z])0+(?=\d)', '', re.sub(r'[^A-Z0-9]', '', s))


def agency_in(geom, year, buf=2000):
    x0, y0, x1, y1 = geom.bounds
    a = AG[AG.ayear == year].cx[x0 - buf:x1 + buf, y0 - buf:y1 + buf]
    a = a[a.dwithin(geom, buf)].sort_values('asize', ascending=False)
    return a


rows = []
for f, g in zip(FIRES, geo.itertuples()):
    y = f['year']
    print('>>', f['name'], round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6,2), 'GB', flush=True)
    pt = gpd.GeoSeries([Point(g.lon, g.lat)], crs='EPSG:4326').to_crs(CRS).iloc[0]
    start = pd.Timestamp(f['start'])
    src = M3 if y == 2026 else read_nbac(y, g.lon, g.lat)
    cand = src.iloc[0:0].copy() if src is None else src[src.intersects(pt.buffer(RADIUS))].copy()
    cand['dist_km'] = cand.distance(pt) / 1000
    cand = cand[cand.dist_km <= RADIUS / 1000]
    lo, hi = start - pd.Timedelta(days=DATE_WIN), start + pd.Timedelta(days=DATE_WIN)
    dated = cand[(cand['first'].isna() | (cand['first'] <= hi)) & (cand['last'].isna() | (cand['last'] >= lo))]
    use = dated
    other = cand[~cand.index.isin(dated.index)]
    r = dict(year=y, name=f['name'], province=f['prov'], community=f['community'],
             lat=round(g.lat, 4), lon=round(g.lon, 4), reported_size=f['size'], source_url=f['url'],
             notable_for=f['notable'], expect_id=f['expect_id'])
    if len(use) == 0:
        r.update(in_our_data='no', our_area_ha='', our_outline_id='', first_det='', last_det='', dist_km='',
                 n_outlines_30km=0, cluster_area_ha='', outline_class='', agency_ids_in_outline='', id_or_name_match='',
                 date_filter=('; '.join(f"{o.oid} {o.area_ha:.0f} ha {str(o['first'])[:10]} to {str(o['last'])[:10]} at {o.dist_km:.1f} km" for _, o in other.iterrows())
                              and 'same-year outline(s) outside date window: ' + '; '.join(f"{o.oid} {o.area_ha:.0f} ha {str(o['first'])[:10]} to {str(o['last'])[:10]} at {o.dist_km:.1f} km" for _, o in other.iterrows())) or 'no same-year outline within 30 km')
    else:
        want = norm_id(f['expect_id']) if f['expect_id'] else None

        def matches(ag):
            for a in ag.itertuples():
                if want and (norm_id(a.aid.split(' ')[-1]) == want or want in norm_id(a.aid)):
                    return True
                if f['expect_name'] and f['expect_name'].lower() in str(a.aname).lower():
                    return True
            return False
        hit = None
        if want or f['expect_name']:
            for c in use.sort_values('area_ha', ascending=False).itertuples():
                if matches(agency_in(c.geometry, y)):
                    hit = c.Index
                    break
        if hit is not None:
            best, how = use.loc[hit], 'agency ID/name match'
        else:
            big = use[use.area_ha >= 500]
            best = (big if len(big) else use).sort_values('dist_km').iloc[0]
            how = 'nearest outline >= 500 ha' if len(big) else 'nearest outline'
        ag = agency_in(best.geometry, y)
        ids = [f"{a.aid}{(' ' + a.aname) if a.aname and a.aname != 'nan' else ''} ({a.asize:.0f} ha)" for a in ag.head(3).itertuples()]
        match = ('yes' if hit is not None else 'no') if (want or f['expect_name']) else ''
        r.update(in_our_data='yes', our_area_ha=round(best.area_ha), our_outline_id=best.oid,
                 first_det=str(best['first'])[:10], last_det=str(best['last'])[:10], dist_km=round(best.dist_km, 1),
                 n_outlines_30km=len(use), cluster_area_ha=round(use.area_ha.sum()), outline_class=best.oclass,
                 agency_ids_in_outline='; '.join(ids), id_or_name_match=match,
                 rep_lon=best.geometry, pick=how, date_filter='date-matched')
    rows.append(r)

df = pd.DataFrame(rows)
# representative point of chosen outline, lon/lat
rp = []
for v in df.get('rep_lon', pd.Series([None] * len(df))):
    if isinstance(v, float) or v is None:
        rp.append((np.nan, np.nan))
    else:
        p = gpd.GeoSeries([v.representative_point()], crs=CRS).to_crs('EPSG:4326').iloc[0]
        rp.append((round(p.x, 4), round(p.y, 4)))
df['outline_rep_lon'] = [a for a, b in rp]
df['outline_rep_lat'] = [b for a, b in rp]
df = df.drop(columns=['rep_lon'], errors='ignore')
df.to_csv(os.path.join(OUTD, 'work', 'coverage_raw.csv'), index=False)
pd.set_option('display.width', 250)
print(df[['year', 'name', 'in_our_data', 'our_area_ha', 'cluster_area_ha', 'our_outline_id', 'first_det', 'last_det', 'dist_km',
          'n_outlines_30km', 'outline_class', 'id_or_name_match', 'agency_ids_in_outline', 'pick', 'date_filter']].to_string())
