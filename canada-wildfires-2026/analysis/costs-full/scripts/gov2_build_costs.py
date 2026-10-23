"""Second round of government response costs (gaps left by gov_costs.csv), 2023 to 2026.

Writes costs-full/gov2_costs.csv. Same columns as gov_costs.csv plus:
  low, central, high  : 2025 dollars. For rows marked yes/partial they are the ADDITIVE amounts under the
                        floor, central and high cases. For replacement rows (ISC) they are the replacement values.
  range_meaning       : says which of the two it is.
CPI factors to 2025 dollars are the same as gov_costs.csv (CPI all-items, annual mean; 2026 = Jan-Sep mean).
A fiscal year Y to Y+1 is fire season Y. Every input below is quoted in gov2_notes.md with its source.
"""
import csv
import json
import os

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
F = {2023: 1.045033, 2024: 1.020723, 2025: 1.0, 2026: 0.975604}
ACC = '2026-10-22'
M = 1e6
rows = []


def add(item, payer, jur, period, season, nominal, basis, source, url, overlaps, additive, add_c,
        notes, low=None, central=None, high=None, meaning='additive amount, 2025 dollars'):
    f = F[season]
    a25 = None if nominal is None else round(nominal * f, 2)
    if central is None:
        central = add_c
    if low is None:
        low = central
    if high is None:
        high = central
    rows.append(dict(item=item, payer=payer, jurisdiction=jur, period=period,
                     amount_nominal_cad=None if nominal is None else round(nominal, 2), amount_2025_cad=a25,
                     basis=basis, source_name=source, url=url, accessed=ACC, overlaps_with=overlaps,
                     additive=additive, additive_amount_cad=round(add_c, 2), notes=notes,
                     low=round(low, 2), central=round(central, 2), high=round(high, 2), range_meaning=meaning))


# ---------------------------------------------------------------- 1. New Brunswick
NB_PA2 = ('https://legnb.ca/content/house_business/61/2/tabled_documents/2025-12-19%20Public%20Accounts%20Volume%202-Comptes%20publics%20volume%202.pdf ; '
          'https://legnb.ca/content/house_business/61/1/tabled_documents/2024-12-17%20Public%20Accounts%20-%20Comptes%20publics%20(Vol.%202),%202024.pdf')
NB_ME = ('https://www.legnb.ca/content/house_business/61/1/tabled_documents/2025-03-18%20Main%20Estimates-Budget%20principal,%202025-2026.pdf ; '
         'https://www.legnb.ca/content/house_business/61/2/tabled_documents/2026-03-17%20Main%20Estimates%202026-2027%20-%20Budget%20principal,%202026-2027%20.pdf')
NB_SUPP = 'https://www.legnb.ca/content/house_business/61/2/tabled_documents/2025-2026%20Supplementary%20Estimates,%20Vol.%201-Budget%20suppl%C3%A9mentaire,%20vol.%201,%202025-2026.pdf'
NB_Q3 = 'https://www.gnb.ca/content/dam/GNB3/org/ftb-fct/doc/2025-2026-third-quarter-report.pdf'
NB_PA1 = 'https://www.gnb.ca/content/dam/GNB3/org/ftb-fct/doc/public-accounts-vol-1-2026.pdf'
FPL = 'https://forestprotectionlimited.com/?p=2002'
fp = {2023: 15.5789, 2024: 19.9280}          # Forest Protection component actual, $M (PA Vol 2)
rec = {2023: 3.8426, 2024: 3.1669, 2025: 3.800, 2026: 3.972}   # out-of-province fire recoveries, $M
s_lo = 9.0 / fp[2023]                         # suppression share stated for 2023 (about $9M of $15.6M)
s_c = (s_lo + 1) / 2
nb_ovl = ('None with bill lines. Out-of-province fire recoveries are subtracted because those crews are inside the '
          'importing provinces\' lines. Federal spruce budworm money is paid to Forest Protection Limited directly (outside this component). No NB wildfire DFAA orders 2023-2025')
for yr, label in ((2023, 'FY2023-24 (2023 season)'), (2024, 'FY2024-25 (2024 season)')):
    lo = s_lo * fp[yr] - rec[yr]; ce = s_c * fp[yr] - rec[yr]; hi = fp[yr] - rec[yr]
    add('New Brunswick wildfire program: DNR Forest Protection component, fire share, net of out-of-province fire recoveries',
        'provincial', 'NB', label, yr, ce * M, 'estimate built from Public Accounts actuals (component covers fire, insects and disease)',
        f'NB Public Accounts Vol 2 (FY2024-25 with FY2023-24 comparative): Forest Protection actual {fp[yr]*1000:,.1f}k; Fire Recovery Out-of-Province {rec[yr]*1000:,.1f}k; FPL post of the provincial statement (about $9M spent in the 2023 fire season)',
        NB_PA2 + ' ; ' + FPL, nb_ovl, 'yes', ce * M * F[yr],
        f'ESTIMATE. Fire share low {s_lo:.3f} (2023 suppression-only share), central {s_c:.3f} (midpoint), high 1.0 (whole component). Value = share x component - recoveries',
        lo * M * F[yr], ce * M * F[yr], hi * M * F[yr])
lo = 14.0 + s_lo * 23.29 - rec[2025]; ce = 14.0 + s_c * 23.29 - rec[2025]; hi = 37.29 - rec[2025]
add('New Brunswick wildfire program: DNR Forest Protection component, fire share, net of out-of-province fire recoveries',
    'provincial', 'NB', 'FY2025-26 (2025 season)', 2025, ce * M,
    'estimate built from Main Estimates, Supplementary Estimates and Q3 report (PA Vol 2 for 2025-26 due Dec 2026)',
    'NB Main Estimates 2025-26 Forest Protection 23,290k; Supplementary Estimates 2025-26 Vol 1: 14,000k to Forest Protection; Q3 2025-26 report: Natural Resources over budget by $14.5M mainly due to fire suppression and mobilizations; 2026-27 Main Estimates: Fire Recovery Out-of-Province revised 3,800k',
    NB_ME + ' ; ' + NB_SUPP + ' ; ' + NB_Q3 + ' ; ' + NB_PA1, nb_ovl, 'yes', ce * M,
    'ESTIMATE. The 14.0M supplementary is all fire; the 23.29M base takes the fire share. PA Vol 1 2025-26 (audited, Schedule 22): Natural Resources 175.0M actual vs 161.7M budget, increase due mainly to fire suppression and mobilization',
    lo * M, ce * M, hi * M)
lo = s_lo * 29.126 - rec[2026]; ce = s_c * 29.126 - rec[2026]; hi = 29.126 - rec[2026]
add('New Brunswick wildfire program, 2026-27 budget (Forest Protection fire share, net of budgeted recoveries)',
    'provincial', 'NB', 'FY2026-27 (2026 season)', 2026, ce * M, 'budget-based estimate (no in-year update)',
    'NB Main Estimates 2026-27: Forest Protection 29,126k; Fire Recovery Out-of-Province estimate 3,972k',
    NB_ME, nb_ovl + '. 2026 season (tier B)', 'yes', ce * M * F[2026],
    'ESTIMATE, 2026 season. CIFFC: 497 ha, 367 fires to Oct 22 2026 (quiet), so the budget is used as the cost',
    lo * M * F[2026], ce * M * F[2026], hi * M * F[2026])

# ---------------------------------------------------------------- 2. Prince Edward Island
PE24 = 'https://docs.assembly.pe.ca/download/dms?objectId=9abfe316-e0fe-4f13-8cbc-bd4481e6c501&fileName=Premier.King.02292024.2024-25%20Estimates%20of%20Revenue%20and%20Expenditure.pdf'
PE25 = 'https://qatauth.gpei.ca/sites/default/files/publications/estimates_book_2025-26.pdf'
PE26 = 'https://www.princeedwardisland.ca/sites/default/files/9350/2026%20Operating%20Estimates%20Book.pdf'
pe_ovl = 'None (PEI has no aircraft; no PEI wildfire DFAA orders)'
add('Prince Edward Island Forest Fire Protection (Forests, Fish and Wildlife Division)', 'provincial', 'PE',
    'FY2023-24 (2023 season)', 2023, 950600, 'forecast (budget forecast printed in next Estimates)',
    'PEI Estimates 2024-25, Environment, Energy and Climate Action: Forest Fire Protection, 2023-24 Forecast 950,600 (Estimate 783,300)',
    PE24, pe_ovl, 'yes', 950600 * F[2023], 'Subdivision covers forest fire prevention and suppression on private and public lands',
    783300 * F[2023], 950600 * F[2023], 950600 * F[2023])
add('Prince Edward Island Forest Fire Protection', 'provincial', 'PE', 'FY2024-25 (2024 season)', 2024, 948500,
    'forecast (budget forecast printed in next Estimates)', 'PEI Estimates 2025-26: Forest Fire Protection, 2024-25 Forecast 948,500 (Estimate 1,095,100)',
    PE25, pe_ovl, 'yes', 948500 * F[2024], '')
add('Prince Edward Island Forest Fire Protection', 'provincial', 'PE', 'FY2025-26 (2025 season)', 2025, 1170000,
    'budget (2025-26 Estimate; the 2025-26 forecast in the 2026-27 book could not be read)',
    'PEI Estimates 2025-26: Forest Fire Protection, 2025-26 Estimate 1,170,000; 2026-27 Operating Estimates Book: Land and Environment 2025-26 forecast 42,341,000 vs estimate 41,032,000',
    PE25 + ' ; ' + PE26, pe_ovl, 'yes', 1170000,
    'ESTIMATE. High adds the whole department-level 2025-26 overrun (1.309M), an upper bound; 2025: 15 fires, 13 ha (CIFFC)',
    1170000, 1170000, 1170000 + 1309000)
add('Prince Edward Island Forest Fire Protection, 2026-27', 'provincial', 'PE', 'FY2026-27 (2026 season)', 2026, 1170000,
    'estimate (2026-27 line not readable; 2025-26 Estimate used as proxy)', 'PEI Estimates 2025-26 (proxy); 2026-27 book detail pages not retrievable',
    PE25 + ' ; ' + PE26, pe_ovl + '. 2026 season (tier B)', 'yes', 1170000 * F[2026], 'ESTIMATE. 2026: 8 fires, 4 ha (CIFFC)',
    948500 * F[2026], 1170000 * F[2026], 1170000 * F[2026])

# ---------------------------------------------------------------- 3. Nova Scotia
NS_AR23 = 'https://www.novascotia.ca/sites/default/files/documents/1-2534/accountability-report-2023-24-department-natural-resources-and-renewables-en.pdf'
NS_AR24 = 'https://www.novascotia.ca/sites/default/files/documents/1-2256/accountability-report-2024-25-department-natural-resources-en.pdf'
NS_SUB = 'https://nslegislature.ca/sites/default/files/pdfs/committees/sub/sub_20240321.pdf'
NS_DEC = 'https://news.novascotia.ca/en/2025/12/18/second-budget-2025-26-update-released'
NS_FEB26 = 'https://www.novascotia.ca/sites/default/files/documents/7-4172/additional-appropriations-budget-2026-27-en.pdf'
NS_DMAH = 'https://www.novascotia.ca/sites/default/files/documents/1-2536/accountability-report-2023-24-department-municipal-affairs-and-housing-en.pdf'
add('Nova Scotia Fleet and Forest Protection 2023-24: actual-based figure (estimate + $15M wildfire overrun) minus the forecast already in gov_costs.csv',
    'provincial', 'NS', 'FY2023-24 (2023 season)', 2023, 0.333e6, 'actual (Accountability Report variance explanation) minus forecast',
    'NS DNRR Accountability Report 2023-24: "Expense Actuals are $46.5 million higher than authority due to ... $15 million increase related to wildfires including large scale wildfires"; Estimates: Fleet and Forest Protection estimate 7,849k',
    NS_AR23 + ' ; ' + NS_SUB, 'Upward correction of the gov_ NS 2023-24 row (22,516k forecast); same definition', 'yes', 0.333e6 * F[2023],
    'Actual-based 7,849k + 15,000k = 22,849k. Minister, Subcommittee on Supply 2024-03-21: suppression forecast about $12M, actual spend about $8.7M after recoveries; AR: recoveries for wildfires $3.6M (source of recoveries not stated, so gross is kept)')
add('Nova Scotia Fleet and Forest Protection 2024-25: Accountability Report shows no wildfire variance (gov_ forecast kept)',
    'provincial', 'NS', 'FY2024-25 (2024 season)', 2024, 0, 'actual (no wildfire variance reported)',
    'NS DNR Accountability Report 2024-25: expense variance explained by 2 Billion Trees, resource management, parks; recoveries include $0.2M out-of-province firefighting',
    NS_AR24, 'Same as gov_ NS 2024-25 row', 'no', 0,
    'Actual close to estimate 8,901k; gov_ uses forecast 9,318k (difference within 0.4M; not changed)')
add('Nova Scotia 2025-26: contingency drawn for wildfires and drought in summer 2025 (reference for the gov_ forecast)',
    'provincial', 'NS', 'FY2025-26 (2025 season)', 2025, 24.9e6, 'in-year allocation (second forecast update, Dec 2025)',
    'NS news release 2025-12-18: "To cover the costs of fighting wildfires and drought in the summer of 2025, the Province drew $24.9 million from the $200 million contingency"',
    NS_DEC, 'Inside the gov_ NS 2025-26 Fleet and Forest Protection forecast (40,881k) for the firefighting part; drought part is agriculture', 'no', 0,
    'Supports the forecast; the 2025-26 Accountability Report (actuals) is not yet published')
add('Nova Scotia Public Works wildfire-related costs, 2025-26 additional appropriation', 'provincial', 'NS',
    'FY2025-26 (2025 season)', 2025, 1.1e6, 'additional appropriation (final forecast, Feb 2026)',
    'NS Summary of Additional Appropriations, February 2026: Public Works "$1.1 million for wildfire related costs"',
    NS_FEB26, 'None (Public Works is outside the DNR line in gov_)', 'yes', 1.1e6, '')
add('Nova Scotia Emergency Management Office 2023-24 disaster assistance relief for floods and wildfires (reference)',
    'provincial', 'NS', 'FY2023-24 (2023 season)', 2023, 78.341e6, 'actual over estimate (all events, floods and wildfires)',
    'NS DMAH Accountability Report 2023-24: EMO expenses 91,221k vs 12,880k estimate; "$78.3M in partly recoverable Disaster Assistance relief for flooding and wildfires"',
    NS_DMAH, 'Evacuation, municipal response (Halifax, Shelburne County) and household recovery lines; DFAA NS 2023 order', 'no', 0,
    'Wildfire share not published (July 2023 flood is in the same line); not counted')

# ---------------------------------------------------------------- 4. Manitoba
MB_ED = 'https://www.gov.mb.ca/jec/reports/pdfs/23_24_editnr_ar.pdf'
MB_PA = 'https://manitoba.ca/asset_library/en/proactive/20232024/publicaccounts/AnnualReportPublicAccounts2023-2024.pdf'
MB_Q1 = 'https://www.gov.mb.ca/asset_library/en/proactive/20262027/first-quarter-report-september2026.pdf'
add('Manitoba Emergency Expenditures 2023-24: wildfire suppression share', 'provincial', 'MB', 'FY2023-24 (2023 season)', 2023, 0,
    'actual (department annual report and Public Accounts)',
    'EDITNR Annual Report 2023-24: Wildfire Suppression 16,069k vs 13,932k authority, overspend explained in-department, no Emergency Expenditures recovery noted; Public Accounts 2023-24: Emergency Expenditures 29M, "the 2023 flood season did not result in significant expenses"',
    MB_ED + ' ; ' + MB_PA, 'gov_ MB 2023-24 row (53.5M) already holds the department wildfire spending', 'partial', 0,
    'Central and floor 0: in 2024-25 the department reported its Emergency Expenditures wildfire charge (24.7M); in 2023-24 it reported none. High case allows all 29M (all hazards, includes an August 2023 severe weather event)',
    0, 0, 29e6 * F[2023])
mb26_c = 79.737 * F[2024]; mb26_l = 53.509 * F[2023]; mb26_h = mb26_c * 264268 / 237345; mb_b = 55.26602
add('Manitoba 2026 wildfire costs above the budget already in gov_ (estimate)', 'provincial', 'MB', 'FY2026-27 (2026 season)', 2026,
    mb26_c / F[2026] * M, 'estimate from past seasons (no in-year wildfire figure; Q1 Emergency Expenditures overrun is mostly floods)',
    'gov_ MB actuals 2023 (53.5M) and 2024 (79.7M); NFD area 2023 199,199 ha, 2024 237,345 ha; CIFFC 2026 264,268 ha, 318 fires; Q1 2026-27: Emergency Expenditures 277M over budget for June rains DFA, flood recovery, flood health costs and the 2026 wildfire response',
    MB_Q1 + ' ; https://api.cwfif.nrcan.gc.ca/reported-fire-stats/ytd/by-agency?date=2026-10-22',
    'Increment over gov_ MB 2026-27 budget row (55.3M in 2025 dollars). Q1 EE overrun (277M) not used', 'yes', (mb26_c - mb_b) * M,
    'ESTIMATE. Central: 2024 cost (similar area); low: 2023 cost; high: 2024 cost scaled by area',
    (mb26_l - mb_b) * M, (mb26_c - mb_b) * M, (mb26_h - mb_b) * M)

# ---------------------------------------------------------------- 5. NWT, Yukon, Quebec, Saskatchewan, Parks, DND, Public Safety
add('NWT 2025-26 final (no new document; gov_ appropriation figure kept)', 'territorial', 'NT', 'FY2025-26 (2025 season)', 2025, 0,
    'no final figure tabled', 'NWT tabled documents to TD 590-20(1) (Oct 2026): no 2025-26 Public Accounts, interim financial report or Supplementary Estimates No. 4 2025-26; Supplementary Estimates No. 1 2026-27 has no fire item',
    'https://www.ntlegislativeassembly.ca/documents-proceedings/tabled-documents ; https://www.fin.gov.nt.ca/en/resources/public-accounts',
    'gov_ NT 2025-26 row (112.1M)', 'no', 0, 'Open: the 2025-26 interim financial report was tabled in October last year; not yet this year')
add('Yukon 2025-26 Fire Management: Supplementary Estimates No. 2 adds nothing for Community Services (gov_ forecast confirmed)',
    'territorial', 'YT', 'FY2025-26 (2025 season)', 2025, 0, 'appropriation (Supplementary Estimates No. 2, tabled Oct 2026)',
    'Yukon 2025-26 Supplementary Estimates No. 2, S-16: Community Services voted to date 158,671k, supplementary nil, revised vote 158,671k',
    'https://open.yukon.ca/information/644f8f82-fc1f-4e8e-9a7f-568100d4bb10/resource/5f219582-0cb4-4fd5-946c-1dc157fcb6f4/download/fin-2025-26-budget-supp-2-operation-and-maintenance-appropriations-summary-department-and-corpor.pdf',
    'gov_ YT 2025-26 row (63.9M forecast)', 'no', 0, '2025-26 Public Accounts not yet released (2024-25 posted 2025-11-05)')
qc_b, qc24, qc23 = 133.798617, 155.122590, 259.710231
qc_hi = qc_b + (qc24 - qc_b) / (265199 - 8302) * (753935 - 8302)
qc_lo = qc_b + (qc23 - qc_b) / (4288263 - 8302) * (753935 - 8302)
qc_c = (qc_hi + qc_lo) / 2
add('Quebec SOPFEU 2026 season cost (estimate; annual report due spring 2027)', 'provincial', 'QC', '2026 season (calendar year)', 2026,
    qc_c / F[2026] * M, 'estimate from SOPFEU audited costs and area burned',
    'gov_ SOPFEU costs net of exports (2025 dollars) 2023 259.7M, 2024 155.1M, 2025 133.8M; NFD QC area 2023 4,288,263 ha, 2024 265,199 ha, 2025 8,302 ha; CIFFC 2026 753,935 ha, 651 fires',
    'https://api.cwfif.nrcan.gc.ca/reported-fire-stats/ytd/by-agency?date=2026-10-22 ; https://a-ca.storyblok.com/f/2000396/x/c22b63b6cb/8-5x11-rapport_annuel_2025-vf.pdf',
    'None (no QC 2026 row in gov_). Exports to other provinces not removable yet', 'yes', qc_c * M,
    'ESTIMATE. Base = 2025 cost; marginal cost per hectare from 2024 (high) or 2023 (low, very large northern area); central = mean',
    qc_lo * M, qc_c * M, qc_hi * M)
fit = {r['name'][:2]: r for r in json.load(open(os.path.join(D, 'work', 'gov2_season2026_fit.json')))}
sk = fit['SK']
add('Saskatchewan SPSA 2026 season wildfire cost (estimate)', 'provincial', 'SK', '2026 season (calendar year)', 2026,
    sk['central_2025d_m'] / F[2026] * M, 'estimate (regression of SPSA season costs on area burned, 2016-2025)',
    'Provincial Auditor 2026 Vol 1 Ch 5 season costs (2025 dollars) 2016-2025; NFD area; CIFFC 2026 312,280 ha, 353 fires; Q1 2026-27 report shows no wildfire variance',
    'https://auditor.sk.ca/pub/publications/public_reports/2026/Volume%201/ch-05----saskatchewan-public-safety-agencyresource-planning-for-wildfire-response.pdf ; https://api.cwfif.nrcan.gc.ca/reported-fire-stats/ytd/by-agency?date=2026-10-22',
    'None (no SK 2026 row in gov_; same definition as the bill\'s SK line)', 'yes', sk['central_2025d_m'] * M,
    f"ESTIMATE. cost = {sk['intercept_m']} + {sk['slope_m_per_100k_ha']} per 100,000 ha (2025 $M); low/high = 10th/90th percentile of leave-one-out errors. The Aug 2026 special warrant ($50M) is for flood and wildfire disaster relief (PDAP), not suppression",
    sk['low_2025d_m'] * M, sk['central_2025d_m'] * M, sk['high_2025d_m'] * M)
QP_PC = 'https://search.open.canada.ca/qpnotes/record/ec%2CSOS-QP-00001'
JRCC = 'https://jasper-alberta.ca/Home/DownloadMeeting/8bcfc306-cd8c-4a73-91ac-cbf93fdea818?isEnglish=True'
PC_BG = 'https://www.canada.ca/en/parks-canada/news/2025/02/government-of-canada-funding-for-2024-wildfire-season-in-parks-canada-administered-places-including-jasper-national-park-wildfire-response-recovery.html'
PC_DRR = 'https://parks.canada.ca/agence-agency/bib-lib/rapports-reports/rmr-dpr/2024-2025'
add('Parks Canada 2024 season: suppression and response beyond the 59.8M already counted', 'federal', 'Parks Canada', '2024 season', 2024,
    30.6e6, "Parks Canada's own season estimate (Question Period note) minus amounts already placed; floor from the February 2025 funding backgrounder",
    'QP note SOS-QP-00001 (received 2025-09-03): "Parks Canada estimates that the cost of wildfire suppression and response was approximately $163.2M for the 2024 season"; JRCC: 2024-25 Parks spending 132.6M = 59.8M response + 72.8M re-entry and initial recovery; Parks backgrounder 2025-02-06: 133.1M for the 2024 season = up to 45.2M Incident Response in Jasper + 80.1M Recovery and Re-entry + 7.7M Other Fire Pressures (Wood Buffalo and Kootenay fires); DRR 2024-25: expenses 188.1M above plan "primarily due to the additional costs incurred in response to wildfires, particularly in Jasper"',
    QP_PC + ' ; ' + JRCC + ' ; ' + PC_BG + ' ; ' + PC_DRR,
    'gov_ Parks 2024-25 response row (59.8M); re-entry 72.8M (gov_ reference, econ_ counts 20.2M hazard management; interim housing 29.1M uncounted)', 'partial', 30.6e6 * F[2024],
    '163.2 - 59.8 - 72.8 = 30.6M not explained by the Jasper 2024-25 breakdown (other parks\' 2024 fires, base-funded suppression, costs after March 2025). Low = the 7.7M Other Fire Pressures funding (fires outside Jasper, in no bill line); high adds re-entry operations other than hazard trees and interim housing (163.2 - 59.8 - 20.2 - 29.1 = 54.1M). The DRR has no wildfire cost line and its "over $160 million" is the whole federal Jasper package (Parks 133.1M, CMHC 9.4M, DFAA advance 19.6M), so it does not replace the 163.2M',
    7.7e6 * F[2024], 30.6e6 * F[2024], 54.1e6 * F[2024])
pc_ha, pc_fire = 37.9e6 / 1007529, 37.9e6 / 123
for yr, ha, nf in ((2025, 68633, 87), (2026, 124872, 89)):
    lo, hi = pc_ha * ha, pc_fire * nf; ce = (lo + hi) / 2
    add(f'Parks Canada wildfire response, {yr} season (estimate)', 'federal', 'Parks Canada', f'FY{yr}-{str(yr+1)[2:]} ({yr} season)', yr, ce,
        'estimate scaled from the 2023 season incremental cost',
        f'Parks 2023-24: 37.9M additional funding for an unprecedented season (1,007,529 ha, 123 fires, CIFFC); CIFFC {yr}: {ha:,} ha, {nf} fires; no Parks wildfire item in Supplementary Estimates (B) or (C) 2025-26 or (A) 2026-27; QP note: no new resources for suppression',
        'https://parks.canada.ca/agence-agency/bib-lib/rapports-reports/rmr-dpr/2024-2025 ; https://api.cwfif.nrcan.gc.ca/reported-fire-stats/ytd/by-agency ; https://www.canada.ca/content/dam/tbs-sct/documents/planned-government-spending/supplementary-estimates/explanation-requirements-c-2025-26.csv',
        'Possible small overlap with provincial mutual-aid lines', 'yes', ce * F[yr],
        'ESTIMATE. Low scales by area, high by fire count, central is the mean. 2025-26 Q2 QFR: rentals fell because helicopter and equipment rentals for the 2024 Jasper response were not needed',
        lo * F[yr], ce * F[yr], hi * F[yr])
add('Parks Canada National Fire Management Program funding, Supplementary Estimates (A) 2026-27 (reference)', 'federal', 'Parks Canada',
    'FY2026-27 (2026 season)', 2026, 7418555, 'appropriation (capacity)', 'Supplementary Estimates (A) 2026-27: "Funding for the National Fire Management Program" 7,298,555 (vote 1A) + 120,000 (vote 5A)',
    'https://www.canada.ca/content/dam/tbs-sct/documents/planned-government-spending/supplementary-estimates/explanation-requirements-a-2026-27.csv',
    'Standing capacity, like the federal aircraft leases reference row in gov_', 'no', 0, 'Part of the $47.8M over five years announced 2026-05-28')
lentus_c = 8.8556e6 / 56960        # $ per peak-person-day, 2023-24 (DRR actual / LENTUS page deployments)
lentus_l = 1.2603e6 / 19600        # 2022-23 (Fiona, about 700 members for 4 weeks)
for yr, pd_c, pd_l, pd_h, note in (
        (2024, 4010, 4010, 4010, 'Labrador City 70 x 15, Jasper/Hinton 120 x 15, Semo 110 x 8, Bunibonibee airlift about 70 x 4'),
        (2025, 5520, 4880, 6800, 'MB 170 x 6, ON 70 x 4, MB 60 x 6, SK Griffons 40 x 32 (20 to 80), NL 100 x 23, NS Greenwood 20 x 14; 6,770 evacuees flown'),
        (2026, 520, 520, 520, 'ON Eabametoong 60 x 4 (14 CC-130 flights), BC Vernon cadet camp 10 x 28')):
    ce, lo, hi = pd_c * lentus_c, pd_l * lentus_l, pd_h * lentus_c * 2
    add(f'Department of National Defence Operation LENTUS wildfire deployments, FY{yr}-{str(yr+1)[2:]} (estimate)', 'federal', 'DND/CAF',
        f'FY{yr}-{str(yr+1)[2:]} ({yr} season)', yr, ce, 'estimate (incremental cost per peak-person-day from DRR actuals x deployments)',
        f'DND DRR 2023-24 LENTUS actual 8,855.6k for about 56,960 peak-person-days of 2023 wildfire deployments; DRR 2022-23 LENTUS actual 1,260.3k (Fiona); Operation LENTUS page deployments: {note}',
        'https://www.canada.ca/en/department-national-defence/corporate/reports-publications/departmental-results-report/2023-24-index/supp-information/costs-major-caf-ops.html ; https://www.canada.ca/en/department-national-defence/services/operations/military-operations/current-operations/operation-lentus.html',
        'None (not cost-recovered from provinces)', 'yes', ce * F[yr],
        'ESTIMATE. Central uses the 2023-24 unit cost (about $155 per peak-person-day); low the 2022-23 unit cost (about $64); high doubles central for airlift-heavy evacuations. The 2024-25 DRR table could not be read; the 2026-27 Departmental Plan shows LENTUS planned 0.0 for 2025-26 to 2027-28',
        lo * F[yr], ce * F[yr], hi * F[yr])
add('Public Safety Canada: match of Red Cross donations for the 2025 Saskatchewan, Manitoba and NL wildfires', 'federal', 'Public Safety Canada',
    '2025 season', 2025, 1564823, 'appropriation (Supplementary Estimates (C) 2025-26, vote 5c)',
    'Supplementary Estimates (C) 2025-26: "Funding to match donations raised by the Canadian Red Cross in response to the 2025 Saskatchewan, Manitoba..." 1,564,823',
    'https://www.canada.ca/content/dam/tbs-sct/documents/planned-government-spending/supplementary-estimates/explanation-requirements-c-2025-26.csv',
    'Evacuation lines if they count Red Cross relief paid from the federal match (health_ SK Red Cross row is provincial money)', 'yes', 1564823, '')

# ---------------------------------------------------------------- 6. ISC (replacement range for the gov_ tier C estimate)
ISC_URL = ('https://www.sac-isc.gc.ca/eng/1685047435261 ; https://search.open.canada.ca/qpnotes/record/isc-sac%2CISC-2026-QP-00844 ; '
           'https://www.canada.ca/en/auditor-general/our-work/audit-reports/parl-oag-202211-08-e.html')
for yr, R, s, sop in ((2023, 369.501840, 90 / 101, 20.751686), (2024, 294.372464, 26 / 31, 1.552553), (2025, 688.648240, 73 / 81, 1.340655)):
    ce = s * R - sop; lo = 0.67 * s * R - sop; hi = R - sop
    add('Indigenous Services Canada EMAP response, wildfire share (refined range; replaces the gov_ tier C rows)', 'federal', 'ISC (EMAP)',
        f'FY{yr}-{str(yr+1)[2:]} ({yr} season)', yr, ce * M, 'estimate (ISC publishes no hazard split)',
        f'EMAP response reimbursed {R*1000:,.0f}k; wildfire share of fire+flood evacuation events {s:.3f}; key statistics: floods and wildfires were 67% of all emergencies 2009-2025; SOPFEU billing to ISC {sop*1000:,.0f}k removed',
        ISC_URL, 'Replaces gov_ ISC EMAP rows (central unchanged); evacuation lines for First Nations evacuees; provincial agencies paid for on-reserve suppression',
        'no (replacement)', 0,
        'Low also assumes other hazards (loss of services, severe weather, contamination, landslides: 33% of events) cost as much per event; high = all response costs. No wildfire-only figure found in DRRs, QP notes 2025-2026, OAG 2022 Report 8 or Supplementary Estimates (B) 2025-26 (705.9M all-hazard)',
        lo * M * F[yr], ce * M * F[yr], hi * M * F[yr], meaning='replacement value, 2025 dollars')

# ---------------------------------------------------------------- 7. Municipal and regional response
add('City of West Kelowna 2023 McDougall Creek response (provincial reimbursements in the audited statements)', 'municipal', 'BC (West Kelowna)',
    '2023 season (calendar year)', 2023, 12397453, 'actual (audited statements; wildfire label inferred)',
    'City of West Kelowna 2023 financial statements: provincial conditional transfers "Other" 12,397,453 (2022: 564,906); General Government 18.45M vs 8.03M budget, Protective Services 23.86M vs 19.54M',
    'https://media-003-ca.cdn.govstack.com/westkelownacity-ca/media/vvopbara/2023-cwk-financial-statements-signed.pdf',
    'Inside health_ BC EMCR 2023 interface fire payments (BC reimburses 100% of eligible local response costs)', 'partial', 0,
    'Gross range 12.4M to 14.7M (over-budget amount). Additive 0 except a high-case 2.3M if the over-budget gap was unreimbursed wildfire cost',
    0, 0, (14.74 - 12.40) * M * F[2023])
add('Northern Rockies Regional Municipality 2024 Fort Nelson (Parker Lake) response (estimate from over-budget spending)', 'municipal', 'BC (Northern Rockies)',
    '2024 season (calendar year)', 2024, 4.68e6, 'estimate (audited statements, budget vs actual)',
    'NRRM 2024 audited statements: General Government 8.19M vs 5.11M budget; Protective Services 4.71M vs 3.11M',
    'https://nr.civicweb.net/document/229056', 'Inside health_ BC EMCR 2024 fires payments', 'no', 0,
    'Gross 3.1M (general government only) to 4.7M; not labelled wildfire in the statements')
add('Town of Hay River 2023 wildfire civil emergency costs', 'municipal', 'NT (Hay River)', '2023 season (calendar year)', 2023, 955246,
    'actual (audited statements, 2023 comparative)', 'Town of Hay River 2024 audited statements, Schedule 7: Civil emergency 955,246 (2023); Schedule of government transfers: GNWT Fire reimbursement 936,830 (2023)',
    'https://hayriver.com/wp-content/uploads/2025/11/1.-2024-Town-of-HR-Financial-Statements-FINAL-8-20.pdf',
    'Inside health_ GNWT 2023 remainder row (high case only) and the DFAA NWT order', 'partial', 955246 * F[2023],
    'Additive in floor and central; drop in the high case. The 2023 statements PDF is a scan; the 2024 comparative column was used',
    955246 * F[2023], 955246 * F[2023], 0)
add('City of Yellowknife 2023 wildfire response costs (claimed under disaster financial assistance)', 'municipal', 'NT (Yellowknife)', '2023 season', 2023, 13.341e6,
    'actual (audited statements, costs incurred to Dec 31 2024)',
    'City of Yellowknife 2024 financial statements Note 21: "accrued revenues equal to 75% of the costs incurred to date of $13.34 million"; receivable from the Disaster Financial Assistance Arrangements program 7.26M',
    'https://www.yellowknife.ca/en/city-government/resources/Reports/Annual_Report/2024-FINANCIAL-STATEMENTS.pdf ; https://www.yellowknife.ca/en/city-government/resources/Reports/Annual_Report/2023-FINANCIAL-REPORT.pdf',
    'Inside health_ GNWT 2023 remainder row (high case only; GNWT processes community claims) and the DFAA NWT order', 'partial', 13.341e6 * F[2023],
    'Additive in floor and central; drop in the high case', 13.341e6 * F[2023], 13.341e6 * F[2023], 0)
add('Halifax (HRM) 2023 Tantallon wildfire: operating response part', 'municipal', 'NS (Halifax)', 'FY2023-24 (2023 season)', 2023, 2.3e6,
    'forecast (Q1 2023-24 report)', 'HRM First Quarter Financial Report 2023-24: "Tantallon Wildfire response costs $2.3M"; event total actuals 11,386,847 + commitments 2,329,204 = 13,716,051',
    'https://cdn.halifax.ca/media/83626 ; https://cdn.halifax.ca/media/87746', 'Inside the econ_ Halifax row (13.7M, partial)', 'no', 0,
    'HRM 2023-24 annual report: 22.7M incurred to March 31 2024 for Fiona, the wildfire and the July flood; with the Sept 2023 Fiona (4.4M) and flood (2.4M) estimates the wildfire share would be about 15.9M, 2.2M above the econ_ row')
RMWB_Q3_25 = 'https://media-003-ca.cdn.govstack.com/rmwb-017-ca/media/43qlj1v1/q3-2025-financial-performance-report.pdf'
RMWB_FS24 = 'https://www.rmwb.ca/media/xenbm1zl/2024-consolidated-financial-statements-rmwb.pdf'
RMWB_FS25 = 'https://www.rmwb.ca/media/gnxjegpp/2025-audited-consolidated-fs.pdf'
add('Regional Municipality of Wood Buffalo 2023 Rocky River fire response (Disaster Recovery Program)', 'municipal', 'AB (Wood Buffalo)', '2023 season', 2023, 8.2e6,
    'estimate (municipal project estimate, DRP approved)', 'RMWB 2025 Q3 Financial Performance Report: Rocky River Fire DRP Response estimate $8.2M, reimbursed at 90%; actuals to Sep 30 2025 4,324,057; 2024 audited statements Note 25(c): expenses 3,735,045 (2023) and 440,906 (2024)',
    'https://www.rmwb.ca/media/mlhnpa05/q2-2024-financial-performance-report-presented-to-council.pdf ; ' + RMWB_Q3_25 + ' ; ' + RMWB_FS24,
    'Inside health_ Alberta 2023 DRP remainder row (high case only)', 'partial', 8.2e6 * F[2023],
    'Additive in floor and central; drop in the high case. Low = actuals recorded to Sep 30 2025; central = the municipal project estimate', 4324057 * F[2023], 8.2e6 * F[2023], 0)
add('Regional Municipality of Wood Buffalo 2023 Fort Fitzgerald fire: support for NWT evacuees (reference)', 'municipal', 'AB (Wood Buffalo)', '2023 season', 2023, 1427966,
    'actual (mutual aid claim, paid in 2025)', 'RMWB 2025 audited statements Note 16(b): Northwest Territories Mutual Aid Agreement, $1,427,966 received in 2025 (receivable 1,417,090 at end of 2024); 2024 Q2 report: reimbursed 100% via the Government of Alberta, which invoices the NWT',
    'https://www.rmwb.ca/media/mlhnpa05/q2-2024-financial-performance-report-presented-to-council.pdf ; ' + RMWB_FS25,
    'Inside health_ Alberta costs of hosting NWT evacuees', 'no', 0, '')
add('Regional Municipality of Wood Buffalo 2024 MWF-017 fire response (Beacon Hill and Abasand evacuation; Disaster Recovery Program)', 'municipal', 'AB (Wood Buffalo)',
    '2024 season', 2024, 2661767, 'estimate (municipal project estimate, DRP approved at 90%) with audited actuals as the floor',
    'RMWB 2025 Q3 Financial Performance Report: 2024 MWF-017 DRP Response project estimate 2,661,767, expected eligible 2,395,590, actuals to Sep 30 2025 241,954; 2024 audited statements Note 25(d): 2024 expenses 243,030 (salaries 100,987, contracted services 104,736, materials 37,307), DRP revenue 218,727',
    RMWB_Q3_25 + ' ; ' + RMWB_FS24 + ' ; https://media-003-ca.cdn.govstack.com/rmwb-017-ca/media/gzhj3rpg/q4-2024-financial-performance-report-presented-to-council.pdf',
    'Alberta DRP pays 90% (no Alberta 2024 DRP line for Wood Buffalo in the bill; DFAA Alberta 2024 order not counted). health_ Alberta 2024 Emergency Evacuation Payments are payments to people, not municipal costs', 'yes', 2661767 * F[2024],
    'ESTIMATE range: low = expenses recorded in the 2024 audited statements; central and high = the municipal project estimate (invoices still being collected in Sep 2025, as for Rocky River where actuals reached about half the estimate)',
    243030 * F[2024], 2661767 * F[2024], 2661767 * F[2024])
add('Regional Municipality of Wood Buffalo 2025: no wildfire response cost recorded', 'municipal', 'AB (Wood Buffalo)', '2025 season', 2025, 0, 'actual (audited statements)',
    'RMWB 2025 audited statements: Disaster Recovery Program approvals only for the 2020 river break-up, 2023 Rocky River fire and 2024 MWF-017; Disaster and emergency measures 9,587,875 (2024: 9,569,508; budget 8,534,181); Q1 to Q3 2025 Financial Performance Reports list no 2025 fire event',
    RMWB_FS25 + ' ; ' + RMWB_Q3_25 + ' ; https://media-003-ca.cdn.govstack.com/rmwb-017-ca/media/2ewl2qhs/q2-2025-financial-performance-report-presented-to-council.pdf',
    'None', 'no', 0, 'Closed: nothing to add for 2025 (the 1.1M over budget in disaster and emergency measures is the same level as 2024 and not tied to an event)')

# Flin Flon (MB) 2025: the only northern municipal figure for 2025, also used to scale Denare Beach, Creighton and Enterprise
FF_PLAN = 'https://cityofflinflon.ca/uploads/dm/151442/2026_Financial_Plan.pdf'
FF_FS = 'https://cityofflinflon.ca/uploads/dm/151440/2025_Audit_Report.pdf'
MB_PA26 = 'https://www.gov.mb.ca/asset_library/en/finances/annual-report-and-public-accounts-2025-26.pdf'
ff_ps = 1955852 - 743800            # protective services, actual minus budget (audited 2025)
ff_rev = 811483 - 40000             # Fire Dept-Services revenue above budget (payer not stated)
ff_lo, ff_hi = ff_ps - ff_rev, ff_ps
ff_c = (ff_lo + ff_hi) / 2
add('City of Flin Flon 2025 wildfire emergency response (protective services above budget, mostly the EMO account)', 'municipal', 'MB (Flin Flon)',
    '2025 season (calendar year)', 2025, ff_c, 'estimate built from the 2025 audited statements and the 2026 Financial Plan (2025 actuals by account)',
    'City of Flin Flon 2026 Financial Plan (adopted April 30 2026), 2025 actual vs budget: EMO 1,171,249 vs 25,000; Fire 579,916 vs 501,050; revenue Fire Dept-Services 811,483 vs 40,000. 2025 audited statements: Protective services 1,955,852 vs budget 743,800 (2024: 872,569); Note 14(c): compensation higher "due to extraordinary overtime incurred during wildfire emergency response activities ... A substantial portion of these costs was eligible for reimbursement under the Province of Manitoba\'s Disaster Financial Assistance Program"; receivable from the Province 3,168,978 (2024: 240,469)',
    FF_PLAN + ' ; ' + FF_FS,
    'Manitoba pays most of it through its Disaster Financial Assistance program ("DFA program and other operating costs" 12M in the 2025 wildfire summary, Public Accounts 2025-26 p. 12); that 12M is in no bill line (health_ left it to property lines), so this row is additive. If a later line counts the 12M, drop the reimbursed part of this row. Aviation fuel sold by the City airport to the Manitoba Wildfire Service (contracts of 1.15M in 2025) is inside the MB suppression line and not counted',
    'yes', ff_c,
    'ESTIMATE. High = protective services over budget (audited). Low = the same minus the extra Fire Dept-Services revenue, in case that revenue was paid by a wildfire agency already counted (payer not stated). Central = midpoint. EMO alone was 1,146,249 over budget',
    ff_lo, ff_c, ff_hi)
# Per-resident rates (2025 dollars) from the three official northern municipal figures
r_ff_lo, r_ff_c = ff_lo / 4940, ff_c / 4940                  # Flin Flon (MB part), Census 2021 4,940
r_hr = 955246 * F[2023] / 3169                               # Hay River 2023, Census 2021 3,169
r_yk = 13.341e6 * F[2023] / 20340                            # Yellowknife 2023, Census 2021 20,340
r_lo, r_c, r_hi = r_ff_lo, sorted([r_ff_c, r_hr, r_yk])[1], max(r_ff_c, r_hr, r_yk)
rate_txt = (f'per resident (2025 dollars): Flin Flon 2025 {r_ff_lo:,.0f} to {ff_hi/4940:,.0f} (central {r_ff_c:,.0f}), Hay River 2023 {r_hr:,.0f}, '
            f'Yellowknife 2023 {r_yk:,.0f}; low = lowest, central = median of the three central figures ({r_c:,.0f}), high = highest ({r_hi:,.0f})')
POP = 'https://api.statcan.gc.ca/census-recensement/profile/sdmx/rest/data/STC_CP,DF_CSD/A5..1.1.1'
SK_PDAP = 'https://publications.saskatchewan.ca/api/v1/products/120675/formats/151461/download'
SK_IAJ = 'https://docs.legassembly.sk.ca/legdocs/Committees/IAJ/Debates/30L/20251201Debates-IAJ.pdf'
pop_sk = 699 + 1203
add('Northern Village of Denare Beach and Town of Creighton 2025 (Wolf fire): local emergency response (estimate)', 'municipal', 'SK (Denare Beach, Creighton)',
    '2025 season', 2025, r_c * pop_sk, 'estimate (per-resident cost from official municipal figures x Census 2021 population)',
    f'No municipal figure is published. Census 2021: Denare Beach 699, Creighton 1,203. {rate_txt}. PDAP 2026 General Claim Guidelines: municipal deductible 0.10% of taxable assessment, then PDAP pays 100% of eligible costs; SPSA (Hansard IAJ 2025-12-01): about $22M for heavy sprinkler contractors and about $8.9M in salaries and parts for the Denare Beach protection, paid by SPSA',
    POP + ' ; ' + SK_PDAP + ' ; ' + SK_IAJ + ' ; ' + FF_FS + ' ; ' + FF_PLAN,
    'Saskatchewan PDAP payments for 2025 are in no bill line (the SK DFAA order is not counted). SPSA suppression, sprinklers and structure protection sit in the bill\'s SK firefighting line and SPSA evacuee hotels, food, payments and the Red Cross pledge in health_ SK rows, so only local EOC, staff and administration costs are estimated here. Debris removal (the $20M recovery fund) is recovery, not counted',
    'yes', r_c * pop_sk, 'ESTIMATE. Denare Beach lost about 200 homes, so the high end is plausible for it',
    r_lo * pop_sk, r_c * pop_sk, r_hi * pop_sk)
pop_ent = 75
add('Hamlet of Enterprise 2023: hamlet response costs (estimate)', 'municipal', 'NT (Enterprise)', '2023 season', 2023, r_c * pop_ent / F[2023],
    'estimate (per-resident cost from official municipal figures x Census 2021 population)',
    f'No hamlet figure is published. Census 2021: Enterprise 75. {rate_txt}. GNWT TD 112-20(1): MACA delivered hazardous materials removal on 25 lots, debris clean-up, environmental reviews and temporary accommodation to Aug 31 2024 (territorial costs). TD 176-20(1): the hamlet\'s $6.2M modular home proposal was not pursued',
    POP + ' ; https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2024-06/TD%20112-20%281%29%20Follow-up%20Letter%20for%20Oral%20Question%20163-20%281%29%20Supports%20Available%20for%20Residents%20of%20Enterprise.pdf ; https://ntlegislativeassembly.ca/sites/default/files/tabled-documents/2024-10/TD%20176-20%281%29%20GNWT%20Response%20to%20Motion%2038-20%281%29%20Consideration%20for%20Hamlet%20of%20Enterprise%20to%20Receive%20Top-Up%20Federal%20Funding.pdf',
    'Inside health_ GNWT 2023 remainder row (high case only) and the DFAA NWT order, like Hay River and Yellowknife', 'partial', r_c * pop_ent,
    'ESTIMATE. Additive in floor and central; drop in the high case. Gross high (Yellowknife rate) in amount terms: ' + f'{r_hi * pop_ent:,.0f}',
    r_lo * pop_ent, r_c * pop_ent, 0)
BAR_FS = 'https://barringtonmunicipality.com/5907-mob-financial-statement-march-31-2024/file'
MODS_FS = 'https://www.municipalityofshelburne.ca/wp-content/uploads/2024/11/FS-March-31-2024.pdf'
MODS_JUL = 'https://www.municipalityofshelburne.ca/wp-content/uploads/2023/07/2023.07.12_PACKAGE_CouncilMeeting_Redacted.pdf'
BAR_AAR = 'https://www.barringtonmunicipality.com/municipal-documents/5716-barrington-lake-wildfire-after-action-review-04032024-1'
sh_lo = (371583 - 94194) + (236356 - 77330)
sh_hi = 371583 + 236356
add('Shelburne County 2023 Barrington Lake wildfire: municipal fire and emergency costs above budget (Municipality of Barrington and Municipality of the District of Shelburne)', 'municipal', 'NS (Shelburne County)',
    'FY2023-24 (2023 season)', 2023, sh_lo, 'actual (audited statements, budget vs actual; wildfire link from council records)',
    'Barrington audited statements to March 31 2024: Fire services coordinator 371,583 (budget 94,194; prior year 83,293), EMO 15,634 (budget 30,220); MODS audited statements to March 31 2024: Other fire protection 236,356 (budget 77,330; prior year 46,770), Other protective services 165,182 (budget 166,678); MODS July 12 2023 council package: the Shelburne County EMO account is "over budget due to the fire response, many of the costs charged to this account are expected to be recovered from the Province"',
    BAR_FS + ' ; ' + MODS_FS + ' ; ' + MODS_JUL + ' ; ' + BAR_AAR,
    'NS EMO 2023-24 disaster assistance relief (78.3M, floods and wildfires) would hold any later reimbursement; it is a reference row only. No provincial reimbursement shows in either FY2023-24 statement (Barrington conditional transfers fell to 134,675 from 237,634), so no overlap with the NS DNR firefighting line was found',
    'yes', sh_lo * F[2023],
    'Low and central = the two fire lines above budget (277,389 + 159,026); high = the two lines in full. The Towns of Shelburne and Lockeport were billed 5,245 and 2,095 for shared EMO costs (inside the MODS figures)',
    sh_lo * F[2023], sh_lo * F[2023], sh_hi * F[2023])
add('Thunder Bay district 2026: host city and affected First Nations (Whitesand, Collins, Whitewater Lake, Neskantaga, Eabametoong and others), response and hosting', 'municipal and First Nations',
    'ON (Thunder Bay district)', '2026 season', 2026, None, 'no published figure; counted inside the ISC 2026 estimate',
    'City of Thunder Bay release 2026-07-22: EOC activated for the regional wildfire situation and now standing down; continues to support evacuees from several northwestern Ontario communities. Ontario ran a provincially led reception centre at Fort William Gardens (City-owned). No dollar figure in any official record found',
    'https://www.thunderbay.ca/en/news/city-transitions-to-enhanced-wildfire-monitoring-while-maintaining-regional-support.aspx ; https://isc.gc.ca/eng/1686078907307/1686078925161 ; https://www.ontario.ca/page/2026-27-first-quarter-finances',
    'health2 ISC 2026 wildfire response estimate (8,805 First Nations evacuees, central 128M, partial) covers First Nations response and the hosting ISC reimburses through Ontario', 'no', 0,
    'Open, small: the City\'s own EOC overtime and Ontario\'s support for evacuees from unorganized areas (Armstrong, Cushing Lake) are not published and have no official count to scale from. Next official records: Ontario 2026-27 Q2 (mid-November 2026), ISC FY2026-27 EMAP figures (mid-2027), City of Thunder Bay 2026 statements (mid-2027)')
bc23 = 123408913.0
add('BC 2026 fires: local authority response and Emergency Support Services paid by EMCR, incl. Summerland, RDOS, TNRD, OKIB (estimate)', 'provincial', 'BC',
    'FY2026-27 (2026 season)', 2026, 0.5 * bc23 / F[2026], 'estimate scaled from 2023 EMCR payments by people evacuated',
    'health_ BC EMCR payments for 2023 interface fires 123.4M (2025 dollars) for about 24,300 households under order (about 58,000 people at 2.4 per household); BC info bulletin 2026: more than 20,000 people evacuated when the provincial emergency was declared Aug 8 2026, more than 1,500 hotel rooms block-booked',
    'https://news.gov.bc.ca/releases/2026EMCR0037-000977 ; https://news.gov.bc.ca/releases/2026EMCR0036-000952 ; https://www2.gov.bc.ca/assets/gov/public-safety-and-emergency-services/emergency-preparedness-response-recovery/embc/reports/emcr-annual-payment-report-2025_26.pdf',
    'None now: health_ has no BC 2026 row. If an official 2026 EMCR figure is added there, drop this row', 'yes', 0.5 * bc23,
    'ESTIMATE. Low 0.34 x 2023 (20,000 / 58,000), central 0.5, high equal to 2023. First EMCR payments for 2026 fires will appear in the FY2026-27 payment report (mid-2027)',
    0.343 * bc23, 0.5 * bc23, bc23)

# ---------------------------------------------------------------- 8. 2026 in-year updates and estimates
on = fit['ON']; on_b = 146.34061798
add('Ontario Emergency Forest Firefighting 2026-27 above the Q1 forecast already in gov_ (estimate)', 'provincial', 'ON', 'FY2026-27 (2026 season)', 2026,
    on['central_2025d_m'] / F[2026] * M, 'estimate (regression of Public Accounts EFF actuals on area burned, 2015-2025)',
    'Ontario Public Accounts EFF net actuals 2015-16 to 2025-26 (in 2025 dollars); NFD area; CIFFC 2026 748,716 ha, 812 fires (record area); Q1 2026-27 forecast 150.0M = budget',
    'https://data.ontario.ca/dataset/public-accounts-ministry-statements-and-schedules ; https://www.ontario.ca/page/2026-27-first-quarter-finances ; https://api.cwfif.nrcan.gc.ca/reported-fire-stats/ytd/by-agency?date=2026-10-22',
    'Increment over gov_ ON 2026-27 Q1 row (146.3M in 2025 dollars)', 'yes', (on['central_2025d_m'] - on_b) * M,
    f"ESTIMATE. cost = {on['intercept_m']} + {on['slope_m_per_100k_ha']} per 100,000 ha (2025 $M); predicted 2026 {on['central_2025d_m']}M (low {on['low_2025d_m']}, high {on['high_2025d_m']}, leave-one-out 10th/90th percentile errors). 2021 (784,564 ha) cost 248.9M nominal; 2025 (600,939 ha) 273.0M",
    (on['low_2025d_m'] - on_b) * M, (on['central_2025d_m'] - on_b) * M, (on['high_2025d_m'] - on_b) * M)
nt_b = 64.02109356
nt_l, nt_h = 91.49865, 112.085
add('NWT 2026-27 wildfire costs above the budget already in gov_ (estimate)', 'territorial', 'NT', 'FY2026-27 (2026 season)', 2026,
    (nt_l + nt_h) / 2 / F[2026] * M, 'estimate from the two most similar seasons',
    'gov_ NT Forest Management 2024-25 (91.5M, 1,699,043 ha) and 2025-26 (112.1M, 1,116,129 ha) in 2025 dollars; CIFFC 2026 1,694,212 ha, 290 fires; Finance Minister fiscal update Oct 21 2026 cites "increasing costs of wildfire emergencies" with no figure',
    'https://api.cwfif.nrcan.gc.ca/reported-fire-stats/ytd/by-agency?date=2026-10-22 ; https://www.ntlegislativeassembly.ca/sites/default/files/hansard/2026-10/99HN261021.pdf',
    'Increment over gov_ NT 2026-27 budget row (64.0M in 2025 dollars)', 'yes', ((nt_l + nt_h) / 2 - nt_b) * M,
    'ESTIMATE. Central = mean of 2024 and 2025; low = 2024; high = 2025. No 2026-27 fire supplementary tabled to TD 590',
    (nt_l - nt_b) * M, ((nt_l + nt_h) / 2 - nt_b) * M, (nt_h - nt_b) * M)
add('Yukon Fire Management 2026-27 (estimate; budget line printed as a graphic and not readable)', 'territorial', 'YT', 'FY2026-27 (2026 season)', 2026,
    30.812e6, 'estimate (base budget proxy)', 'Yukon Main Estimates: Fire Management O&M estimate 26,114k (2024-25), 30,812k (2025-26); CIFFC 2026: 7,266 ha, 81 fires (very quiet season); no 2026-27 supplementary yet',
    'https://yukon.ca/sites/default/files/fin-2026-27-budget-main-estimates-community-services.pdf ; https://api.cwfif.nrcan.gc.ca/reported-fire-stats/ytd/by-agency?date=2026-10-22',
    'None (no YT 2026 row in gov_)', 'yes', 30.812e6 * F[2026],
    'ESTIMATE. Central = 2025-26 base; low = 2024-25 base; high = central + 15% for growth in the base',
    26.114e6 * F[2026], 30.812e6 * F[2026], 30.812e6 * 1.15 * F[2026])
nl_c = 11.8895 * 96301 / 68079
add('Newfoundland and Labrador fire suppression 2026-27 above the budget already in gov_ (estimate)', 'provincial', 'NL', 'FY2026-27 (2026 season)', 2026,
    nl_c * M, 'estimate from past seasons', 'gov_ NL revised 2024-25 11.89M (68,079 ha) and 2025-26 32.50M (18,480 ha, 243 fires, Kingston interface fire); budget 2026-27 11.82M; CIFFC 2026 96,301 ha, 133 fires',
    'https://www.gov.nl.ca/budget/2026/wp-content/uploads/sites/10/Estimates-2026.pdf ; https://api.cwfif.nrcan.gc.ca/reported-fire-stats/ytd/by-agency?date=2026-10-22',
    'Increment over gov_ NL 2026-27 budget row', 'yes', (nl_c - 11.8208) * M * F[2026],
    'ESTIMATE. Central scales 2024 by area; low = budget; high = 2025 level',
    0, (nl_c - 11.8208) * M * F[2026], (32.5002 - 11.8208) * M * F[2026])
add('Nova Scotia 2026: no in-year cost update (budget in gov_ kept)', 'provincial', 'NS', 'FY2026-27 (2026 season)', 2026, 0, 'no update',
    'NS news release 2026-10-22: 114 wildfires, 1,521 ha; $6.8M wildfire response funding in the 2026-27 budget; $6.5M aircraft contract',
    'https://news.novascotia.ca/en/2026/10/22/investments-dedicated-crews-strengthened-2026-wildfire-response', 'gov_ NS 2026-27 budget row', 'no', 0, '')
add('BC and Alberta 2026: no official cost update after the Q1 reports already in gov_', 'provincial', 'BC, AB', 'FY2026-27 (2026 season)', 2026, 0, 'no update',
    'BC First Quarterly Report 2026/27 (850M); Alberta 2026-27 Q1 update (104.7M to July); next updates due late November',
    'https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/quarterly-reports/2026-27_first_quarterly_report.pdf',
    'gov_ BC and AB 2026-27 rows', 'no', 0, 'CIFFC 2026: BC 479,334 ha; AB 17,780 ha (quiet)')

cols = ['item', 'payer', 'jurisdiction', 'period', 'amount_nominal_cad', 'amount_2025_cad', 'basis', 'source_name', 'url', 'accessed',
        'overlaps_with', 'additive', 'additive_amount_cad', 'notes', 'low', 'central', 'high', 'range_meaning']
with open(os.path.join(D, 'gov2_costs.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print(len(rows), 'rows')
for r in rows:
    if r['additive'] != 'no' and r['range_meaning'].startswith('additive'):
        print(f"{r['jurisdiction'][:22]:22s} {r['period'][:26]:26s} {r['additive']:8s} low {r['low']/M:8.1f} central {r['central']/M:8.1f} high {r['high']/M:8.1f}  {r['item'][:70]}")
