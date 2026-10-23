"""Assemble wildfire spending rows from official documents into one long table.
Every row was read from the cited local file; amounts are as printed (units noted)."""
import pandas as pd, os, sys
OUT = sys.argv[1]
R = 'raw/spending'
rows = []
def add(j, fy, season, item, amt, unit, status, basis, src, local, note=''):
    rows.append(dict(jurisdiction=j, fiscal_year=fy, fire_season=season, line_item=item, amount=amt, unit=unit,
                     status=status, basis=basis, source_url=src, local_file=local, notes=note))

# ---- British Columbia: BCWS Wildfire Averages page (fire year Apr 1 - Mar 31) ----
bcsrc = 'https://www2.gov.bc.ca/gov/content/safety/wildfire-status/about-bcws/wildfire-statistics/wildfire-averages'
bc = {2008: 82.1, 2009: 382.1, 2010: 212.2, 2011: 53.5, 2012: 133.6, 2013: 122.2, 2014: 297.9, 2015: 277, 2016: 129,
      2017: 649, 2018: 615, 2019: 182.5, 2020: 193.7, 2021: 718.8, 2022: 411.9, 2023: 1094.8, 2024: 769.4}
for y, v in bc.items():
    add('BC', f'{y}/{str(y+1)[2:]}', y, 'BCWS total wildfire cost', v, 'CAD millions', 'estimated (BCWS "Total Cost (estimated)"; matches fiscal-year suppression totals)',
        'fire year Apr 1-Mar 31', bcsrc, 'raw/spending/bc/bc_wildfire_averages.html', 'page last updated 2026-02-03')
add('BC', '2025/26', 2025, 'Estimated cost of wildfire suppression', 510, 'CAD millions', 'estimate as of 2025-11-01',
    'season to Nov 1', 'https://www2.gov.bc.ca/gov/content/safety/wildfire-status/about-bcws/wildfire-history/wildfire-season-summary',
    'raw/spending/bc/bc_season_summary.html', 'page last updated 2026-01-02')
add('BC', '2025/26', 2025, 'Fire Management (statutory) total spending forecast', 665, 'CAD millions', 'forecast (Third Quarterly Report forecast cited in Budget 2026)',
    'fiscal year', 'https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Budget_and_Fiscal_Plan.pdf', 'raw/spending/bc/2026_Budget_and_Fiscal_Plan.pdf',
    'BFP 2026: "$60 million decrease in fire management costs - for a total spending forecast of $665 million"; also Table: Fire Management 665 / 236 / 236 / 236')
add('BC', '2026/27', 2026, 'Vote 31 Fire Management voted appropriation', 235.702, 'CAD millions', 'budget (Estimates 2026/27)',
    'fiscal year', 'https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Estimates.pdf', 'raw/spending/bc/2026_Estimates.pdf', '2025/26 Estimates: 238.047')
add('BC', '2026/27', 2026, 'Fire-management costs above Budget 2026', 614, 'CAD millions', 'forecast (First Quarterly Report, 2026-09-14)',
    'fiscal year', 'https://news.gov.bc.ca/releases/2026FIN0031-001066', 'raw/spending/bc/bc_2026FIN0031_q1_release.html',
    'Implied total forecast = 236 (BFP fiscal-plan line) + 614 = ~850; the ~$850M total figure itself appears in CBC reporting of the minister, not in the official release. Media deck: raw/spending/bc/bc_2026_27_Q1_MediaDeck.pdf (waterfall shows (614) Fire management costs)')

# ---- Ontario: Public Accounts ministry statements (actual, fiscal year Apr-Mar) ----
on = pd.read_csv(os.path.join(OUT, 'raw/spending/on_public_accounts_fire.csv'))
for r in on.itertuples():
    if r.amount_cad == 0:
        continue
    note = 'net of recoveries; operating expense; ministry renamed over time'
    if r.sub_item == 'Public Protection':
        note = 'FY2014-15 file not broken out by sub-item; activity total includes non-fire public safety/emergency response. ' + note
    add('ON', r.fiscal_year, int(r.fiscal_year[:4]), f'MNRF Public Protection: {r.sub_item}', round(r.amount_cad / 1e6, 3), 'CAD millions',
        'actual (Public Accounts of Ontario)', 'fiscal year Apr 1-Mar 31',
        'https://data.ontario.ca/dataset/public-accounts-ministry-statements-and-schedules', f'raw/spending/on_public_accounts/{r.source_file}', note)

# ---- Alberta: ministry annual reports, Lapse/Encumbrance schedule (voted actuals, $000) ----
ab = [
 ('2015-16', '7.1 Wildfire Management (operating, all wildfire incl. response)', 477440, 'af-2015-16-annual-report.pdf', 'https://open.alberta.ca/dataset/3bd2d2b9-6ccd-4d8d-a8a2-a5c15da00c2a/resource/6bec314a-0837-480e-bc34-1ef4126397da/download/af-2015-16-annual-report.pdf', ''),
 ('2016-17', '7.1 Wildfire Management (operating, all wildfire incl. response)', 323782, '2016-17-af-annual-report.pdf', 'https://open.alberta.ca/dataset/3bd2d2b9-6ccd-4d8d-a8a2-a5c15da00c2a/resource/733ab939-4f48-461d-b791-8bf6b1df1d6e/download/2016-17-af-annual-report.pdf', 'supplementary estimate 252,000'),
 ('2017-18', '7.1 Wildfire Management (operating, all wildfire incl. response)', 294190, 'agriculture-and-forestry-annual-report-2017-2018.pdf', 'https://open.alberta.ca/dataset/3bd2d2b9-6ccd-4d8d-a8a2-a5c15da00c2a/resource/ddda2788-fe47-49e7-b4f3-579c3a56f7ab/download/agriculture-and-forestry-annual-report-2017-2018.pdf', 'supplementary estimate 204,914'),
 ('2018-19', '6.1 Wildfire Management (operating, all wildfire incl. response)', 284058, 'agriculture-and-forestry-annual-report-2018-2019-web.pdf', 'https://open.alberta.ca/dataset/3bd2d2b9-6ccd-4d8d-a8a2-a5c15da00c2a/resource/bda692e4-785d-4864-9acc-c0263ffd2813/download/agriculture-and-forestry-annual-report-2018-2019-web.pdf', 'supplementary estimate 193,000'),
 ('2019-20', '6.1 Wildfire Management (operating)', 108979, 'af-annual-report-2019-2020.pdf', 'https://open.alberta.ca/dataset/3bd2d2b9-6ccd-4d8d-a8a2-a5c15da00c2a/resource/120fa133-bd20-4d9e-8aed-af8707cd90a5/download/af-annual-report-2019-2020.pdf', ''),
 ('2019-20', '6.2 Wildfire Presuppression and Response (operating vote)', 466748, 'af-annual-report-2019-2020.pdf', 'same', 'contingency section shows a (6,000) adjustment for 6.2'),
 ('2020-21', '6.1 Wildfire Management (operating)', 123171, 'af-annual-report-2020-2021.pdf', 'https://open.alberta.ca/dataset/3bd2d2b9-6ccd-4d8d-a8a2-a5c15da00c2a/resource/dcb9b9b4-588c-4267-b7b2-4a181d95e0eb/download/af-annual-report-2020-2021.pdf', ''),
 ('2020-21', '6.2 Wildfire Presuppression and Response (contingency vote)', 77532, 'af-annual-report-2020-2021.pdf', 'same', ''),
 ('2021-22', '6.1 Wildfire Management (operating)', 103701, 'afred-annual-report-2021-2022.pdf', 'https://open.alberta.ca/dataset/42eff03e-cddd-4f6f-8e05-e01d7e43c564/resource/3973288e-40a2-4c1b-ad7f-b9b2bff0f636/download/afred-annual-report-2021-2022.pdf', 'read from image table p.106 (PDF page 110)'),
 ('2021-22', '6.2 Wildfire Presuppression and Response (contingency vote)', 144027, 'afred-annual-report-2021-2022.pdf', 'same', 'read from image table p.107 (PDF page 111)'),
 ('2023-24', '2.1 Wildfire Management (operating)', 102467, 'fp-annual-report-2023-2024.pdf', 'https://open.alberta.ca/dataset/2dedbb29-e005-4802-bf6e-03bf77536add/resource/b86465e8-a8e3-45de-91d8-3fec19c700db/download/fp-annual-report-2023-2024.pdf', ''),
 ('2023-24', '2.3 Wildfire Presuppression and Response (operating vote)', 58111, 'fp-annual-report-2023-2024.pdf', 'same', 'narrative: overall presuppression and response cost $851M incl. $793M contingency'),
 ('2023-24', '2.3 Wildfire Presuppression and Response (contingency vote)', 793027, 'fp-annual-report-2023-2024.pdf', 'same', ''),
 ('2024-25', '2.1 Wildfire Management (operating)', 156582, 'fp-annual-report-2024-2025.pdf', 'https://open.alberta.ca/dataset/2dedbb29-e005-4802-bf6e-03bf77536add/resource/971986a2-35bb-4aa6-8316-05e3ba568a8a/download/fp-annual-report-2024-2025.pdf', ''),
 ('2024-25', '2.3 Wildfire Presuppression and Response (operating vote, supplementary)', 246743, 'fp-annual-report-2024-2025.pdf', 'same', ''),
 ('2024-25', '2.3 Wildfire Presuppression and Response (contingency vote)', 455422, 'fp-annual-report-2024-2025.pdf', 'same', ''),
 ('2025-26', '2.1 Wildfire Management (operating)', 164845, 'fp-annual-report-2025-2026.pdf', 'https://open.alberta.ca/dataset/2dedbb29-e005-4802-bf6e-03bf77536add/resource/db36b97e-fca3-4082-950b-4943de30687d/download/fp-annual-report-2025-2026.pdf', 'narrative: $169.4M base + $756.2M response'),
 ('2025-26', '2.1 Wildfire Management (contingency vote)', 4507, 'fp-annual-report-2025-2026.pdf', 'same', ''),
 ('2025-26', '2.3 Wildfire Presuppression and Response (contingency vote)', 756197, 'fp-annual-report-2025-2026.pdf', 'same', ''),
]
for fy, item, v, f, u, note in ab:
    add('AB', fy, int(fy[:4]), item, round(v / 1000, 3), 'CAD millions', 'actual (voted actuals, Lapse/Encumbrance schedule, unaudited)',
        'fiscal year Apr 1-Mar 31', u if u != 'same' else '', f'raw/spending/ab/{f}', note)

# ---- Saskatchewan: Provincial Auditor 2026 v1 ch.5, Figure 2 (calendar season, 2025 dollars) ----
sk = {2016: 24.3, 2017: 46.8, 2018: 38.1, 2019: 11.9, 2020: 24.2, 2021: 110.0, 2022: 51.0, 2023: 98.5, 2024: 95.2, 2025: 351.6}
for y, v in sk.items():
    add('SK', '', y, 'SPSA wildfire costs (season)', v, 'CAD millions (2025 dollars)', 'actual, inflation-adjusted to 2025$ (not nominal)',
        'calendar year Jan-Dec', 'https://auditor.sk.ca/pub/publications/public_reports/2026/Volume%201/ch-05----saskatchewan-public-safety-agencyresource-planning-for-wildfire-response.pdf',
        'raw/spending/sk/sk_auditor_2026v1_ch05_wildfire.pdf', 'Figure 2, adapted from SPSA 2025 Wildfire Statistics Report; 2016-24 restated with Bank of Canada calculator')
for fy, est, sup in [('2022-23', 79.7, 31.6), ('2023-24', 84.2, 47.0), ('2024-25', 74.4, 53.7), ('2025-26', 78.2, 313.2), ('2026-27', 76.3, None)]:
    add('SK', fy, int(fy[:4]), 'SPSA operating appropriation: budget estimates', est, 'CAD millions', 'budget', 'fiscal year', 'same as above', 'raw/spending/sk/sk_auditor_2026v1_ch05_wildfire.pdf', 'Figure 8; whole agency, not wildfire-only')
    if sup is not None:
        add('SK', fy, int(fy[:4]), 'SPSA operating appropriation: supplementary estimates', sup, 'CAD millions', 'appropriation (approved, not actual)', 'fiscal year', 'same as above', 'raw/spending/sk/sk_auditor_2026v1_ch05_wildfire.pdf', 'Figure 8' + ('; 2024-25 excludes $39.5M capital' if fy == '2024-25' else ''))

# ---- Manitoba: 2025/26 First Quarter Report ----
add('MB', '2025-26', 2025, 'Emergency Expenditures: wildfire response expended to date', 179, 'CAD millions', 'partial actual (to date, Q1 update)', 'fiscal year',
    'https://gov.mb.ca/asset_library/en/proactive/20252026/first-quarter-report-september2025.pdf', 'raw/spending/mb/mb_2025_26_q1_report.pdf', 'forecast over-expenditure vs budget $129M; DFAA recovery expected')
add('MB', '2025-26', 2025, 'Emergency Expenditures: forecast over-expenditure vs budget (wildfire)', 129, 'CAD millions', 'forecast', 'fiscal year',
    'https://gov.mb.ca/asset_library/en/proactive/20252026/first-quarter-report-september2025.pdf', 'raw/spending/mb/mb_2025_26_q1_report.pdf', '')

# ---- Northwest Territories: supplementary estimates (appropriations, not actuals) ----
add('NT', '2023-24', 2023, 'ECC Fire Suppression Shortfall for 2023 wildfire season (supplementary appropriation)', 75.0, 'CAD millions',
    'supplementary appropriation (not actual)', 'fiscal year',
    'https://ntlegislativeassembly.ca/sites/default/files/legacy/tabled_document_-_fin_-_supplementary_estimates_operations_expenditures_no._2_2023-2024.pdf',
    'raw/spending/nt/tabled_document_-_fin_-_supplementary_estimates_operations_expenditures_no._2_2023-2024.pdf', 'base budget not captured')
add('NT', '2025-26', 2025, 'ECC Wildlife and Forest Management: fire suppression shortfall (supplementary appropriation)', 39.509, 'CAD millions',
    'supplementary appropriation (not actual)', 'fiscal year',
    'https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2025-10/TD%20388-20%281%29%20Supplementary%20Estimates%20%28Operations%20Expenditures%29%20No%202%202025-2026.pdf',
    'raw/spending/nt/TD_388-20(1)_Supplementary_Estimates_(Operations_Expenditures)_No_2_2025-2026.pdf', 'activity total 71.937 -> 112.996 after supplementary; 2026-27 Supp No.1 contains no fire item')

df = pd.DataFrame(rows)
df.loc[df.source_url == 'same as above', 'source_url'] = 'https://auditor.sk.ca/pub/publications/public_reports/2026/Volume%201/ch-05----saskatchewan-public-safety-agencyresource-planning-for-wildfire-response.pdf'
df.to_csv(os.path.join(OUT, 'wildfire_spending_by_jurisdiction.csv'), index=False)
print(df.groupby('jurisdiction').agg(rows=('amount', 'size'), first=('fire_season', 'min'), last=('fire_season', 'max')))
