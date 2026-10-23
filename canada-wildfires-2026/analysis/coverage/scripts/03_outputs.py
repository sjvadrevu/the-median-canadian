"""Write coverage.csv, results.md and labels.csv from work/coverage_raw.csv."""
import os, re
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.abspath(os.path.join(HERE, '..'))
df = pd.read_csv(os.path.join(OUTD, 'work', 'coverage_raw.csv'))


def rep_ha(s):
    s = str(s).replace(',', '')
    m = re.search(r'(\d+(?:\.\d+)?)\s*km2', s)
    if m:
        return float(m.group(1)) * 100
    m = re.search(r'(\d+(?:\.\d+)?)\s*ha', s)
    return float(m.group(1)) if m else None


# Hand-written context per fire (explanations), keyed by name. Only from our data and the checklist sources.
CTX = {
 'Long Lake Complex (HWF-036)': 'NBAC GID 2023_354 joins HWF036 with neighbouring BC holdover fires (Ekwan Tower, G90628) across the AB/BC line, so the GID area (518,067 ha) is far above the AB fire alone.',
 'Edson-area fire': 'Picked outline holds CNFDB EWF031 Pembina Complex; which agency fire forced the Edson evacuation is not confirmed.',
 'Drayton Valley-area fire': 'No CNFDB point inside the picked outline; agency ID not confirmed.',
 'Hay River / Enterprise fire (August)': 'Same NBAC outline as the large 2023 SS052-23 fire; NBAC maps one season-long outline.',
 'Hay River fire (May)': 'Nearest outline SS005-23 (May). The big SS052-23 outline also lies within 2 km.',
 'Tantallon (Westwood Hills) fire': 'CNFDB NS 09-011-2023 (970 ha) inside.',
 'Sept-Iles fire': 'Nearest outline >= 500 ha picked; a 34,709 ha outline (CNFDB QC 20231080172) lies 24 km away. Which fire forced the evacuation is not confirmed.',
 'Lebel-sur-Quevillon fires': 'Part of the large 2023 Quebec complex; agency ID not confirmed.',
 'Chibougamau fire': 'Outline 26 km from town; agency ID not confirmed.',
 'Jasper wildfire complex': 'CNFDB 2024JA010 Jasper Wildfire Complex inside (name match).',
 'Labrador City fire': 'Nearest outline >= 500 ha picked (5.7 km); a larger 25,886 ha outline lies 28 km away; NL agency ID not confirmed.',
 'Flin Flon / Creighton / Denare Beach fire': 'One NBAC fire across MB and SK (GID shared); includes MB WE017 and SK 25DB-WOLF.',
 'Denare Beach (same fire, SK side)': 'Same NBAC fire as Flin Flon row.',
 'Conception Bay North fires (May)': 'NBAC merges the May burns (CNFDB 2025-149 Adams Cove) into the August Kingston outline; first date 2025-05-07.',
 'Kingston fire': 'NBAC outline also holds the May Conception Bay North burns (see that row).',
 'Thunder Bay district fire near Gull Bay FN': 'Nearest 2026 outline >= 500 ha is the Thunder Bay 36 outline, 28 km away; no separate outline near Gull Bay.',
 'Fire near Eabametoong FN (Fort Hope)': 'Outline holds ON NIP_FIRE_045.',
 'Fire near Lac La Croix FN': 'No CWFIF point inside; 3 outlines within 30 km (7,104 ha together).',
 'Pear Lake (Big Bar complex)': 'Outline holds BC 2026-C40983 (largest BC fire of 2026 in the CWFIF list); the name Pear Lake is not in our files.',
 'Walsh River fire': 'MAPPED AREA FAR BELOW: M3 outline 90 ha from a single detection day (outline-check class unclear) vs CWFIF NL 622 at 682 ha, 11 km from Labrador City, reported 2026-06-29. Likely cloud or smoke gaps; outline under-maps the fire.',
 'Thunder Lake structural fires': 'NOT IN DATA: no M3 outline and no CWFIF fire-list point within 20 km. Structural fires inside a hamlet, likely too small or brief for satellite outlines.',
 'CFB Wainwright fire': 'NOT IN DATA: no M3 outline for Oct 17 (M3 file of 2026-10-20 and refreshed 2026-10-22). Only 9 VIIRS hotspots; they never entered the M3 product. The only 2026 outline nearby is M3 36076649 (113 ha, Apr 21 to May 1, class military range). Our Sentinel-2 estimate is about 1,090 ha (analysis/wainwright).',
 'Fort Simpson fire (FS016-26)': 'Outline holds NT FS016-26.',
 'Bradley Creek': 'Outline holds BC 2026-K41351.',
 'Bald Range': 'Outline holds BC 2026-K51490.',
}

rows = []
for r in df.itertuples():
    rh = rep_ha(r.reported_size)
    notes = []
    if r.in_our_data == 'yes':
        if r.id_or_name_match == 'yes':
            notes.append('agency ID/name matches')
        elif r.id_or_name_match == 'no':
            notes.append('expected agency ID/name not found inside')
        if rh and float(r.cluster_area_ha) < 0.5 * rh:
            notes.append(f'MAPPED AREA FAR BELOW reported ({float(r.cluster_area_ha):,.0f} vs {rh:,.0f} ha)')
        notes.append(f'{r.dist_km} km from community; first {r.first_det}, last {r.last_det}; {int(r.n_outlines_30km)} outline(s) within 30 km = {float(r.cluster_area_ha):,.0f} ha')
        if isinstance(r.outline_class, str) and r.outline_class:
            notes.append(f'outline-check class: {r.outline_class}')
        notes.append(f'agency points inside: {r.agency_ids_in_outline}' if isinstance(r.agency_ids_in_outline, str) else 'no agency point inside')
    else:
        notes.append(str(r.date_filter))
    if r.name in CTX:
        notes.insert(0, CTX[r.name])
    rows.append(dict(year=r.year, name=r.name, province=r.province, community=r.community, lat=r.lat, lon=r.lon,
                     reported_size=r.reported_size, source_url=r.source_url, notable_for=r.notable_for,
                     in_our_data=r.in_our_data,
                     our_area_ha=int(r.our_area_ha) if r.in_our_data == 'yes' else '',
                     our_outline_id=r.our_outline_id if r.in_our_data == 'yes' else '',
                     first_det=r.first_det if r.in_our_data == 'yes' else '', last_det=r.last_det if r.in_our_data == 'yes' else '',
                     id_or_name_match=r.id_or_name_match if isinstance(r.id_or_name_match, str) else '',
                     outline_rep_lon=r.outline_rep_lon, outline_rep_lat=r.outline_rep_lat,
                     note=' | '.join(notes)))
cov = pd.DataFrame(rows)
cov.to_csv(os.path.join(OUTD, 'coverage.csv'), index=False)

# ---- labels: 8 most notable, spread across the country, rep point of OUR outline ----
LAB = [
 ('Thunder Bay 36', 'Thunder Bay district, 2026'),
 ('Bald Range', 'Summerland, 2026'),
 ('Jasper wildfire complex', 'Jasper, 2024'),
 ('Yellowknife / Behchoko fire (ZF015)', 'Yellowknife, 2023'),
 ('Flin Flon / Creighton / Denare Beach fire', 'Flin Flon / Denare Beach, 2025'),
 ('Lebel-sur-Quevillon fires', 'Lebel-sur-Quevillon, 2023'),
 ('Barrington Lake fire', 'Shelburne County, 2023'),
 ('Kingston fire', 'Kingston NL, 2025'),
]
lab = []
for n, t in LAB:
    r = cov[cov.name == n].iloc[0]
    assert r.in_our_data == 'yes'
    lab.append(dict(label=t, lon=r.outline_rep_lon, lat=r.outline_rep_lat, outline_id=r.our_outline_id, our_area_ha=r.our_area_ha))
pd.DataFrame(lab).to_csv(os.path.join(OUTD, 'labels.csv'), index=False)

# ---- results.md ----
n = len(cov); yes = (cov.in_our_data == 'yes').sum()
far = cov[cov.note.str.contains('FAR BELOW')]
miss = cov[cov.in_our_data == 'no']
by = cov.groupby('year').agg(checked=('name', 'size'), in_data=('in_our_data', lambda s: (s == 'yes').sum()))
idm = cov[cov.id_or_name_match != '']
lines = ['# Coverage check: reported major fires vs our outlines', '',
         'Original check against our files. The reported list was built from news and agency pages only as a checklist; reported sizes are not for publication.', '',
         '## Scorecard', '',
         '| | Count |', '|---|---|',
         f'| Reported major fires checked | {n} |',
         f'| With an outline in our data (same year, within 30 km, dates overlap start +/- 45 days) | {yes} |',
         f'| Missing | {len(miss)} |',
         f'| Mapped area far below reported (under half) | {len(far)} |',
         f'| Expected agency ID or name checked / found inside outline | {len(idm)} / {(idm.id_or_name_match == "yes").sum()} |', '',
         '| Year | Checked | In our data |', '|---|---|---|']
lines += [f'| {y} | {r.checked} | {r.in_data} |' for y, r in by.iterrows()]
lines += ['', '## Gaps', '']
for r in pd.concat([miss, far]).itertuples():
    lines.append(f'- {r.name} ({r.province}, {r.year}): {r.note.split(" | ")[0]}')
lines += ['', '## All fires', '', '| Year | Fire | Prov | In data | Our ha | Outline | ID match |', '|---|---|---|---|---|---|---|']
for r in cov.itertuples():
    a = f'{int(r.our_area_ha):,}' if r.our_area_ha != '' else ''
    lines.append(f'| {r.year} | {r.name} | {r.province} | {r.in_our_data} | {a} | {r.our_outline_id} | {r.id_or_name_match} |')
lines += ['', '## Labels for the national map (labels.csv)', '', '| Label | Lon | Lat | Outline |', '|---|---|---|---|']
lines += [f'| {l["label"]} | {l["lon"]} | {l["lat"]} | {l["outline_id"]} |' for l in lab]
lines += ['', '## Method', '',
          '- Outlines: NBAC 2023 to 2025 (NBAC_merged_1972_to_2025_20260513, parts sharing a GID dissolved, since NBAC splits a fire at province lines) and CWFIS M3 2026 (m3_perimeters_2026_cwfis_20261020.gpkg, 718 polygons, classes from analysis/outline-check). Areas are equal-area (EPSG:3978).',
          '- Reported location: nearest community geocoded with NRCan Geographical Names; Donnie Creek uses the CNFDB point; Wainwright uses the Alberta Wildfire point RMD-001-2026.',
          '- Match: same-year outline within 30 km whose first to last dates overlap the reported start +/- 45 days. If an agency ID or name was expected, the outline holding that CNFDB (2023 to 2025) or CWFIF fire-list (2026) point within 2 km is chosen; otherwise the nearest outline of 500 ha or more.',
          '- "Our ha" is the chosen outline; coverage.csv note also gives the sum of all matching outlines within 30 km.',
          '- Scripts: scripts/checklist.py, 01_geocode.py, 02_coverage.py, 03_outputs.py.']
open(os.path.join(OUTD, 'results.md'), 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
