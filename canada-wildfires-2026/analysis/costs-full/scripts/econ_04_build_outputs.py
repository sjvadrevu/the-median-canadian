"""econ_04_build_outputs.py

Assembles costs-full/econ_costs.csv (one row per cost item), costs-full/econ_manifest.csv (every download
and web read, with access date) and work/econ_summary_table.md (additive totals) from:
  work/econ_oilgas_shutin_summary.csv   (econ_01)
  work/econ_gdp_dips.csv                (econ_02)
  work/econ_property_insured_vs_bill.csv, work/econ_property_topups.csv (econ_03)
  hand-entered official items below (each with its source document, read on 2026-10-22)

Usage: python3 -I econ_04_build_outputs.py BASE_DIR
"""
import csv, os, sys, re, html, subprocess

BASE = sys.argv[1]
W = os.path.join(BASE, 'work')
ACC = '2026-10-22'
COLS = ['item', 'sector', 'jurisdiction', 'period', 'amount_low_cad', 'amount_central_cad', 'amount_high_cad',
        'dollars_basis', 'basis', 'method', 'source_name', 'url', 'accessed', 'overlaps_with', 'additive', 'notes']
rows = []

def add(**k):
    r = {c: k.get(c, '') for c in COLS}
    for c in ('amount_low_cad', 'amount_central_cad', 'amount_high_cad'):
        if r[c] != '' and r[c] is not None:
            r[c] = int(round(float(r[c])))
    r['accessed'] = r['accessed'] or ACC
    rows.append(r)

# ---------------- PROPERTY ----------------
# insured losses per event (industry), not additive: they overlap the bill's buildings line
INSURED = [
    ('Upper Tantallon wildfire', 'NS', '2023', 247.5e6, 247.5e6, 'one-year CatIQ estimate in IBC report (initial was over $165M); 3,270 claims, personal property $240.7M',
     'IBC, Insurance Claims Update for 2023 Nova Scotia Wildfires and Flooding (CatIQ data)', 'https://a.storyblok.com/f/339220/645121db60/one-year-update-following-2023-nova-scotia-wildfires-and-flooding.pdf'),
    ('McDougall Creek wildfire (West Kelowna, Kelowna)', 'BC', '2023', 480e6, 480e6, 'initial CatIQ estimate, stated as over $480M; no later public update found',
     'IBC news release, Oct 3 2023 (CatIQ)', 'https://www.ibc.ca/news-insights/news/okanagan-and-shuswap-area-wildfires-cause-over-720-million-in-insured-damage'),
    ('Bush Creek East wildfire (North Shuswap)', 'BC', '2023', 240e6, 240e6, 'initial CatIQ estimate, stated as over $240M',
     'IBC news release, Oct 3 2023 (CatIQ)', 'https://www.ibc.ca/news-insights/news/okanagan-and-shuswap-area-wildfires-cause-over-720-million-in-insured-damage'),
    ('Hay River wildfire (Hay River, Enterprise)', 'NT', '2023', 30e6, 30e6, 'initial CatIQ estimate; IBC gives over $60M for Hay River and Behchoko-Yellowknife together',
     'IBC news release, Nov 20 2023 (CatIQ)', 'https://www.ibc.ca/news-insights/news/behchoko-yellowknife-and-hay-river-wildfires-cause-over-60-million-in-insured-damage'),
    ('Behchoko-Yellowknife wildfire', 'NT', '2023', 30e6, 30e6, 'initial CatIQ estimate (half of the over $60M NWT total as split in analysis/property)',
     'IBC news release, Nov 20 2023 (CatIQ)', 'https://www.ibc.ca/news-insights/news/behchoko-yellowknife-and-hay-river-wildfires-cause-over-60-million-in-insured-damage'),
    ('Jasper wildfire complex', 'AB', '2024', 1304e6, 1304e6, 'final CatIQ estimate two years after the event',
     'CatIQ news release, Jul 23 2026', 'https://public.catiq.com/2026/07/23/catiq-discloses-final-industry-loss-estimate-for-jasper-wildfire-complex-of-july-2024-second-estimate-for-prairies-severe-weather-outbreak-of-june-2026/'),
    ('Flin Flon wildfire complex (incl. Denare Beach)', 'MB/SK', '2025', 249e6, 249e6, 'CatIQ update',
     'IBC news release, Sep 4 2025 (CatIQ)', 'https://www.ibc.ca/news-insights/news/insured-damage-from-manitoba-and-saskatchewan-wildfires-nears-300-million'),
    ('Pisew wildfire (La Ronge, Air Ronge, Hall Lake)', 'SK', '2025', 50e6, 50e6, 'initial CatIQ estimate, stated as over $50M',
     'IBC news release, Sep 4 2025 (CatIQ)', 'https://www.ibc.ca/news-insights/news/insured-damage-from-manitoba-and-saskatchewan-wildfires-nears-300-million'),
    ('Kingston wildfire (Conception Bay North)', 'NL', '2025', 70e6, 70e6, 'initial CatIQ estimate, stated as over $70M',
     'IBC news release, Sep 17 2025 (CatIQ)', 'https://www.ibc.ca/news-insights/news/august-wildfire-in-newfoundland-and-labrador-causes-over-70-million-in-insured-damage'),
    ('Bald Range wildfire (Summerland)', 'BC', '2026', 293e6, 293e6, '45-day CatIQ estimate (initial was $313M)',
     'CatIQ news release, Oct 6 2026', 'https://public.catiq.com/2026/10/06/catiq-discloses-third-loss-estimate-for-june-july-severe-storm-event-in-ontario-and-quebec-updated-loss-for-bald-range-fire/'),
]
for (ev, j, y, lo, hi, note, src, url) in INSURED:
    add(item=f'Insured losses (industry): {ev}', sector='property', jurisdiction=j, period=y,
        amount_low_cad=lo, amount_central_cad=lo, amount_high_cad=hi, dollars_basis=f'nominal CAD, {y}', basis='estimate',
        method='Published insured-loss estimate (CatIQ survey of insurers); property (personal and commercial) and vehicle claims including loss adjustment expenses',
        source_name=src + ' [INDUSTRY DATA, not government]', url=url,
        overlaps_with='bill: buildings destroyed (same homes); health_/evacuation lines (claims include additional living expenses of evacuees); econ property adjustment rows',
        additive='no', notes=note + '. Used only to check the bill building values.')

# insured minus bill building value, six events with both (industry alternative)
iv = list(csv.DictReader(open(os.path.join(W, 'econ_property_insured_vs_bill.csv'))))
six = [r for r in iv if r['bill_key']]
exc = sum(float(r['insured_minus_bill_cad']) for r in six)
detail = '; '.join(f"{r['event']}: insured {float(r['insured_cad'])/1e6:.0f}M vs bill {float(r['bill_building_value_cad'])/1e6:.0f}M (x{r['ratio_insured_to_bill']})" for r in six)
add(item='Property adjustment (industry): insured losses above the bill building value, six events in the bill',
    sector='property', jurisdiction='NS, BC, AB, MB, SK', period='2023-2026', amount_low_cad=0, amount_central_cad=exc, amount_high_cad=exc,
    dollars_basis='nominal CAD (insured) minus 2021 census values (bill)', basis='computed',
    method='Sum over events of (CatIQ insured loss) minus (bill value: flagged buildings x DA average owner-occupied dwelling value, analysis/property/destroyed_value_estimates.csv)',
    source_name='CatIQ/IBC releases [INDUSTRY DATA]; analysis/property', url='see insured rows',
    overlaps_with='replaces part of the bill buildings line; includes additional living expenses during evacuation (health_/evacuation scope), contents, vehicles, commercial property and business interruption',
    additive='alternative (industry; use instead of the census-value proxy if industry data are accepted)',
    notes=detail + '. Insured losses run 1.4 to 4.4 times the bill value; total ratio 2.6. Low is 0 because official data give no basis for the gap.')

add(item='Kingston wildfire NL 2025: property losses with no official count (insured value used)', sector='property', jurisdiction='NL', period='2025',
    amount_low_cad=0, amount_central_cad=70e6, amount_high_cad=70e6, dollars_basis='nominal CAD, 2025', basis='estimate',
    method='CatIQ insured loss used as the only published value; no official written count of destroyed structures found (the gov.nl.ca releases checked, Aug 11 to Sep 5 2025, give none)',
    source_name='IBC news release, Sep 17 2025 (CatIQ) [INDUSTRY DATA]',
    url='https://www.ibc.ca/news-insights/news/august-wildfire-in-newfoundland-and-labrador-causes-over-70-million-in-insured-damage',
    overlaps_with='none in bill (bill has no NL buildings); includes evacuation living expenses (health_/evacuation scope)',
    additive='yes (industry only)', notes='Low is 0 under the official-data-first rule. The premier gave a count of 203 structures at a briefing (seen only in news; not used).')

tops = list(csv.DictReader(open(os.path.join(W, 'econ_property_topups.csv'))))
TOPSRC = {
    'Barrington': ('Halifax Regional Fire and Emergency report citing the Barrington after-action review; analysis/property/destroyed_value_official.csv',
                   'https://www.halifax.ca/sites/default/files/documents/city-hall/regional-council/240820cow4.pdf', 'NS', '2023', '2026-10-21'),
    'SHOE': ('Government of Saskatchewan, Review of the 2025 Saskatchewan Wildfire Season (MNP), p. 68-69',
             'https://www.saskatchewan.ca/-/media/news-release-backgrounders/2026/jun/mnp-2025-wildfire-report.pdf', 'SK', '2025', ACC),
    'Enterprise': ('Northwest Territories 2023 Wildfire Response Review, Final Report (GNWT ECC climate library); Statistics Canada 98-10-0015 (51 private dwellings); 2021 Census profile values',
                   'https://climatelibrary.ecc.gov.nt.ca/dataset/51b681f5-1a21-445e-8e2a-f8cd1e2aacaf/resource/40c8e28b-b886-4781-a2f0-032401888f2d/download/1._nwt_wildfire_response_review_report_and_appendices_final_compressed-9k.pdf', 'NT', '2023', ACC),
    'Hay River': ('Northwest Territories 2023 Wildfire Response Review, Case Study SS052-23; 2021 Census profile values',
                  'https://climatelibrary.ecc.gov.nt.ca/dataset/51b681f5-1a21-445e-8e2a-f8cd1e2aacaf/resource/40c8e28b-b886-4781-a2f0-032401888f2d/download/1._nwt_wildfire_response_review_report_and_appendices_final_compressed-9k.pdf', 'NT', '2023', ACC),
    'Behchoko': ('Northwest Territories 2023 Wildfire Response Review (executive summary and ZF015-23 case study); 2021 Census profile values',
                 'https://climatelibrary.ecc.gov.nt.ca/dataset/51b681f5-1a21-445e-8e2a-f8cd1e2aacaf/resource/40c8e28b-b886-4781-a2f0-032401888f2d/download/1._nwt_wildfire_response_review_report_and_appendices_final_compressed-9k.pdf', 'NT', '2023', ACC),
    'Saskatchewan 2025': ('Government of Saskatchewan, Review of the 2025 Saskatchewan Wildfire Season (MNP), p. 68: about 700 structures and 400 vehicles lost (SPSA estimate); 2021 Census profile values',
                          'https://www.saskatchewan.ca/-/media/news-release-backgrounders/2026/jun/mnp-2025-wildfire-report.pdf', 'SK', '2025', ACC),
}
for t in tops:
    key = next(k for k in TOPSRC if k in t['item'])
    src, url, j, y, acc = TOPSRC[key]
    add(item=f"Buildings not in the bill: {t['item']}", sector='property', jurisdiction=j, period=y,
        amount_low_cad=t['low'], amount_central_cad=t['central'], amount_high_cad=t['high'],
        dollars_basis='2021 census values (same basis as the bill buildings line)', basis='computed',
        method=f"Official count x 2021 Census average value of owner-occupied dwellings ({t['value_source']}); low uses the median value or the lower count; counts {t['count_low']} / {t['count_central']} / {t['count_high']}",
        source_name=src, url=url, accessed=acc,
        overlaps_with='insured rows for the same event (do not add both); not in the bill buildings line',
        additive='yes', notes=t['note'] + '. Structures include cabins and outbuildings but are valued as dwellings, as in the bill.')

# ---------------- INFRASTRUCTURE ----------------
JRCC = 'https://jasper-alberta.ca/Home/DownloadMeeting/8bcfc306-cd8c-4a73-91ac-cbf93fdea818?isEnglish=True'
add(item='Jasper National Park: Parks Canada hazard management (danger trees, road safety) in re-entry and initial recovery', sector='infrastructure',
    jurisdiction='AB (federal, Parks Canada)', period='FY2024-25', amount_low_cad=20.2e6, amount_central_cad=20.2e6, amount_high_cad=20.2e6,
    dollars_basis='nominal CAD, FY2024-25', basis='actual',
    method='Spent in 2024-25, as reported in the Jasper Recovery Coordination Centre Year Two Progress Report (draft), Recovery funding table',
    source_name='Jasper Recovery Coordination Centre (Parks Canada and Municipality of Jasper), Year Two Progress Report, in Municipality of Jasper Committee of the Whole agenda, Jul 14 2026',
    url=JRCC, overlaps_with='gov_ lines that count Parks Canada 2024-25 wildfire spending ($132.6M: $59.8M response, $72.8M re-entry and recovery) or the federal total of over $380M',
    additive='yes (check gov_)', notes='Part of the $72.8M re-entry and initial recovery line, which also holds $29.1M interim housing (displacement, not counted here).')
add(item='Jasper National Park: Parks Canada rebuild of park infrastructure (roads, campgrounds, trails, visitor and heritage assets, staff housing, hazard and contamination management, recovery staffing)',
    sector='infrastructure', jurisdiction='AB (federal, Parks Canada)', period='FY2025-26 to FY2026-27',
    amount_low_cad=53.7e6, amount_central_cad=187.3e6 * 53.7 / 75.6, amount_high_cad=685.4e6, dollars_basis='nominal CAD', basis='actual (low); committed (central, high)',
    method='Low: spent to Jun 9 2026 ($75.6M) minus interim housing ($21.9M) = $53.7M. Central: 2025-2027 allocation ($187.3M) x the non-housing share of spending to date (53.7/75.6 = 71%). High: allocation minus interim housing spent ($165.4M) plus the further $520M announced Jun 30 2026 for rebuilding essential assets, interim housing, risk reduction and reconstruction',
    source_name='Jasper Recovery Coordination Centre Year Two Progress Report (draft), Parks Canada rebuild funding table', url=JRCC,
    overlaps_with='gov_ federal Jasper total (over $380M to March 2027); recovery staffing includes Jasper field unit revenue replacement (overlaps the Parks Canada fee revenue row)',
    additive='yes (check gov_)', notes='The allocation also provides interim housing, hence the proportional central case. The $520M is a commitment, not spending, and includes housing and risk reduction.')
add(item='Jasper townsite: water and wastewater repairs (curb stops, service lines, mains) damaged by the fire and firefighting', sector='infrastructure',
    jurisdiction='AB (Municipality of Jasper)', period='2026', amount_low_cad=5.135e6, amount_central_cad=5.645e6, amount_high_cad=9.645e6,
    dollars_basis='nominal CAD, 2026 budgets', basis='estimate (approved budgets)',
    method='Phase 1 $2,015,000 (DRP $1,505,000, utility reserve $510,000; 75% judged direct damage); Phase 2 $7,630,000 (DRP $3,630,000, debenture $4,000,000; combines fire repairs with renewal of aged mains). Low: DRP-eligible parts; central: Phase 1 plus Phase 2 DRP part; high: both phases',
    source_name='Municipality of Jasper, RFD Wildfire Utility Repairs Phase 1 (Committee of the Whole, Apr 14 2026); Bylaw #284 Wildfire Utilities Infrastructure Repairs Borrowing Bylaw (Council, Aug 4 2026)',
    url='https://jasper-alberta.ca/Home/DownloadMeeting/35168787-ea6d-4c23-8065-1fb31c2dcca9?isEnglish=True ; https://jasper-alberta.ca/Home/DownloadMeeting/3ae126a2-a849-4efe-be13-ee1852ac6aaa?isEnglish=True',
    overlaps_with='Alberta Disaster Recovery Program pays $5.1M of it (gov_ if gov_ counts the DRP)', additive='yes (check gov_)', notes='')
add(item='Jasper: Municipality of Jasper direct wildfire costs (emergency response and site remediation)', sector='infrastructure',
    jurisdiction='AB (Municipality of Jasper)', period='2024-2025', amount_low_cad=39458559, amount_central_cad=39458559, amount_high_cad=39458559,
    dollars_basis='nominal CAD', basis='actual (audited)', method='Note 16 of the 2024 and 2025 audited financial statements: $35,489,847 (2024) + $3,968,712 (2025)',
    source_name='Municipality of Jasper, 2024 and 2025 Consolidated Financial Statements',
    url='https://jasper-alberta.ca/Home/DownloadDocument?docId=0a17aca2-b078-46e6-8944-0c77ffef6a97 ; https://jasper-alberta.ca/Home/DownloadDocument?docId=8d5ff8e7-21ce-4614-8722-3b1670e439bf',
    overlaps_with='gov_ response spending; 90% reimbursed by the Alberta DRP', additive='no (response, gov_ scope)',
    notes='Listed so it is not lost; mostly response. Loss on damaged municipal assets was only $16,712 (2024).')
add(item='Jasper: Alberta Disaster Recovery Program for the Municipality of Jasper (uninsurable losses)', sector='infrastructure',
    jurisdiction='AB', period='2024-2026', amount_low_cad=35.9e6, amount_central_cad=73.1e6, amount_high_cad=74e6, dollars_basis='nominal CAD',
    basis='actual (low); approved budget (central, high)',
    method='Spent to June 2026 $35.9M (incident response $25.5M, recovery $4.6M, debris, remediation and municipal infrastructure $5.8M); budget $73.1M (JRCC) or $74M (2024 financial statements)',
    source_name='JRCC Year Two Progress Report; Municipality of Jasper 2024 financial statements, Note 19', url=JRCC,
    overlaps_with='gov_ (provincial response and recovery; DFAA reimburses part); contains the Jasper water repair DRP share', additive='no (gov_ scope)', notes='')
add(item='Halifax (HRM) municipal costs of the 2023 wildfires (capital remediation of damaged assets and extraordinary operating costs)', sector='infrastructure',
    jurisdiction='NS (Halifax Regional Municipality)', period='2023', amount_low_cad=13.7e6, amount_central_cad=13.7e6, amount_high_cad=13.7e6,
    dollars_basis='nominal CAD, 2023', basis='estimate (preliminary)',
    method='Staff estimate of expenditures for the wildfires, Risk and Resiliency Reserve report dated Sep 11 2023',
    source_name='Halifax Regional Municipality, Audit and Finance Standing Committee Item 13.2.2, Sep 20 2023',
    url='https://www.halifax.ca/sites/default/files/documents/city-hall/standing-committees/230920afsc1322.pdf',
    overlaps_with='gov_ NS DFAA order for the 2023 interface fires ($26.6M federal); part is response overtime and security (gov_ scope)',
    additive='partial (check gov_)', notes='Preliminary; final cost not found. The report also notes about $10M of fencing costs expected to be recovered.')
add(item='Kelowna Glenmore Landfill repairs after the McDougall Creek fire (gas collection system, burnt waste)', sector='infrastructure',
    jurisdiction='BC (City of Kelowna)', period='2023', amount_low_cad=1.4e6, amount_central_cad=1.4e6, amount_high_cad=1.4e6,
    dollars_basis='nominal CAD, 2023', basis='actual (assessed)', method='Repairs assessed at $1.4M: $0.9M gas wells, pipes and headers; $0.5M relocating and securing burnt waste',
    source_name='City of Kelowna, When fire shut down the Glenmore Landfill (city page, Jan 2026)', url='https://www.kelowna.ca/node/581505',
    overlaps_with='BC Disaster Financial Assistance offset the costs (gov_ BC DFAA 2023 order)', additive='yes (check gov_)', notes='')
add(item='BC Hydro wildfire response and repair costs, 2024 season', sector='infrastructure', jurisdiction='BC (Crown utility)', period='FY2024-25',
    amount_low_cad=15e6, amount_central_cad=15e6, amount_high_cad=15e6, dollars_basis='nominal CAD, FY2024-25', basis='actual (approximate)',
    method='"approximately $15 million in response and repair costs"; 57 transmission structures and 53 distribution poles lost',
    source_name='BC Hydro 2024/25 Annual Service Plan Report', url='https://www.bcbudget.gov.bc.ca/Annual_Reports/2024_2025/pdf/agency/bchydro.pdf',
    overlaps_with='none known (utility costs are not in the bill)', additive='yes', notes='The 2023 season (1,400 poles and about 90 km of line replaced) has no published dollar figure.')
add(item='Manitoba Hydro wildfire restoration, 2025 season', sector='infrastructure', jurisdiction='MB (Crown utility)', period='FY2025-26',
    amount_low_cad=24e6, amount_central_cad=32e6, amount_high_cad=32e6, dollars_basis='nominal CAD, 2025', basis='actual (low); estimate (central)',
    method='Low: wildfire capital costs of almost $24M in the first six months of 2025-26 (Q2 report). Central: restoration cost estimated at $32M (news releases Sep 11 and Oct 2025); more than 1,000 poles damaged or destroyed',
    source_name='Manitoba Hydro Quarterly Report to Sep 30 2025; Manitoba Hydro news releases',
    url='https://www.hydro.mb.ca/docs/corporate/quarterly-report-250930.pdf ; https://www.hydro.mb.ca/articles/2025/09/northern-communities-power-restored-earlier-than-anticipated-after-wildfire-damage/',
    overlaps_with='none known', additive='yes', notes='Operating costs (overtime, contractors) are mentioned but not quantified separately.')
add(item='SaskPower wildfire supports and recovery in Denare Beach and Creighton, 2025', sector='infrastructure', jurisdiction='SK (Crown utility)', period='2025',
    amount_low_cad=8.5e6, amount_central_cad=8.5e6, amount_high_cad=8.5e6, dollars_basis='nominal CAD, 2025', basis='actual (approximate)',
    method='"about $8.5 million": rebuilding damaged lines, new service connections for incoming housing, a high clearance corridor for home deliveries; at least 300 poles repaired or replaced',
    source_name='Government of Saskatchewan news release, Crown Corporations Support Northern Wildfire Recovery, Nov 4 2025',
    url='https://www.saskatchewan.ca/government/news-and-media/2025/november/04/crown-corporations-support-northern-wildfire-recovery-and-help-communities-and-families',
    overlaps_with='none known', additive='yes', notes='Other Saskatchewan 2025 grid damage outside Denare Beach and Creighton not quantified.')

# ---------------- ECONOMIC ----------------
og = {r['item']: r for r in csv.DictReader(open(os.path.join(W, 'econ_oilgas_shutin_summary.csv')))}
OGSRC = ('Statistics Canada tables 25-10-0055-01 and 25-10-0063-01; Alberta Energy and Minerals Monthly Reference Price Calculations; AER ST-3 Oil Prices; Alberta BVM Components 2025',
         'https://www150.statcan.gc.ca/n1/tbl/csv/25100055-eng.zip ; https://www150.statcan.gc.ca/n1/tbl/csv/25100063-eng.zip ; https://open.alberta.ca/publications/monthly-reference-price-calculations-2023 ; https://static.aer.ca/prd/documents/sts/st3/ST3_2023-12_Oil_Prices.pdf ; https://static.aer.ca/prd/documents/sts/st3/prices_oil_2025.pdf ; https://open.alberta.ca/publications/bvm-components')
for key, label, price in [
    ('AB marketable natural gas 2023', 'Alberta natural gas production shut in by wildfires, May-June 2023', 'Alberta gas reference price ($2.00 and $1.94/GJ); high at the NGX Alberta market price ($2.268 and $2.204/GJ)'),
    ('AB light and medium crude oil 2023', 'Alberta light and medium crude oil shut in by wildfires, May-June 2023', 'AER APMC light crude price ($545.46 and $517.94/m3); low at medium crude price'),
    ('AB pentanes plus 2023', 'Alberta pentanes plus (natural gas liquids) lost with the gas shut-ins, May-June 2023', 'Alberta pentanes plus par price ($559.85 and $538.00/m3)'),
    ('AB in situ bitumen 2025', 'Alberta in situ bitumen shut in by wildfires, late May-June 2025', 'AER APMC ultra heavy crude price ($403.35 and $456.19/m3); high at WCS settlement price x exchange rate')]:
    r = og[key]
    unit = r['unit']
    add(item=label, sector='economic (oil and gas)', jurisdiction='AB', period=key[-4:],
        amount_low_cad=r['value_low'], amount_central_cad=r['value_central'], amount_high_cad=r['value_high'],
        dollars_basis=f'nominal CAD, {key[-4:]}', basis='computed',
        method=f"Shortfall = expected minus actual monthly production; expected = March-April daily level x month ratio of non-fire years (median; low and high = lowest and highest ratio). Volumes {float(r['vol_low'])/1e6:.2f} / {float(r['vol_central'])/1e6:.2f} / {float(r['vol_high'])/1e6:.2f} million {unit}. Valued at {price}"
               + ('. 2025 central counts only May 28-31 of the May shortfall (StatCan: fires shut production "towards the end of the month"; maintenance explains the rest)' if '2025' in key else ''),
        source_name=OGSRC[0], url=OGSRC[1],
        overlaps_with='GDP cross-check rows for the same months (do not add both); value includes royalties and wages (health_ lost-wage lines)',
        additive='yes', notes='Gross value of production not sold in those months; some was deferred rather than lost for good. Attribution to fire per Statistics Canada Daily releases of Jul 28 2023 and Jul 30 2025.')

gd = list(csv.DictReader(open(os.path.join(W, 'econ_gdp_dips.csv'))))
for r in gd:
    cross = r['id'] in ('gdp_og_2023', 'gdp_oilsands_2025')
    yr = r['months'][:4]
    add(item=('GDP cross-check: ' if cross else 'GDP lost: ') + r['industry'] + f" ({r['months'].replace(';', ', ')})",
        sector='economic (GDP)', jurisdiction='Canada', period=yr,
        amount_low_cad=r['low'], amount_central_cad=r['central'], amount_high_cad=r['high'],
        dollars_basis='nominal CAD (chained 2017 GDP x GDP implicit price index of the quarter)', basis='computed',
        method=f"Monthly real GDP at basic prices (36-10-0434-01, SAAR), loss = (baseline - actual)/12 with baseline {r['baseline']}; full loss ${float(r['loss_nominal_full'])/1e6:.1f}M; attribution rule '{r['attribution']}' (sole cause: 50/100/100%; wildfires plus other causes: 0/50/100%)",
        source_name='Statistics Canada, The Daily (GDP by industry) and Table 36-10-0434-01; Table 36-10-0106-01',
        url=r['url'] + ' ; https://www150.statcan.gc.ca/n1/tbl/csv/36100434-eng.zip',
        overlaps_with=r['overlaps'] + '; GDP includes wages (health_ lost-wage lines)',
        additive='alternative (cross-check of the production rows)' if cross else 'yes',
        notes='StatCan statement: "' + r['statcan_quote'] + '"')

# Parks Canada fees
add(item='Parks Canada fee revenue forgone, Jasper National Park (1.27 to 1.30 million fewer visits)', sector='economic (tourism)', jurisdiction='AB (federal)', period='FY2024-25',
    amount_low_cad=1270961 * 101.626e6 / 23727618, amount_central_cad=1303016 * (101.626e6 + 47.614e6) / 23727618, amount_high_cad=1303016 * 213.762e6 / 23727618,
    dollars_basis='nominal CAD, FY2023-24 rates', basis='computed',
    method='Lost visits (Parks Canada attendance: baseline 2,445,096 vs 1,142,080; 52% below the network trend) x network revenue per visit in FY2023-24 (entrance fees $101.6M; plus recreational fees $47.6M; all sales $213.8M; 23.73M visits)',
    source_name='Parks Canada attendance (open.canada.ca, analysis/economic-value/parks_fire_attendance.csv); Parks Canada Financial Statements 2024-25',
    url='https://parks.canada.ca/agence-agency/dp-pd/ef-fs/2024-2025dpr', overlaps_with='Parks Canada rebuild row (includes Jasper field unit revenue replacement); visits shifted to other parks (network fees rose in FY2024-25)',
    additive='no', notes='Parks Canada network entrance fees rose from $101.6M to $106.3M in FY2024-25, so this is a Jasper loss, not a national one.')
add(item='Parks Canada fee revenue forgone, Prince Albert National Park (77,000 to 93,000 fewer visits)', sector='economic (tourism)', jurisdiction='SK (federal)', period='FY2025-26',
    amount_low_cad=77436 * 106.287e6 / 23225829, amount_central_cad=77436 * (106.287e6 + 46.512e6) / 23225829, amount_high_cad=92746 * 222.537e6 / 23225829,
    dollars_basis='nominal CAD, FY2024-25 rates', basis='computed',
    method='Lost visits (baseline 291,521 vs 214,085; 32% below the network trend) x network revenue per visit in FY2024-25 (entrance $106.3M; plus recreational $46.5M; all sales $222.5M; 23.23M visits)',
    source_name='Parks Canada attendance; Parks Canada Financial Statements 2024-25', url='https://parks.canada.ca/agence-agency/dp-pd/ef-fs/2024-2025dpr',
    overlaps_with='accommodation GDP rows (different measure)', additive='yes', notes='Small. Possible displacement to other parks.')

# transfers and supports (not additive)
for (it, j, per, lo, ce, hi, meth, src, url, note) in [
    ('Jasper rent and licence relief (Parks Canada)', 'AB (federal)', '2024-2026', 7.6e6, 15.2e6, 15.2e6, '$15.2M committed, $7.6M provided to date', 'JRCC Year Two Progress Report', JRCC, 'Forgone rent paid by lessees; a transfer that offsets business losses'),
    ('Jasper municipal revenue and tax stabilization and tax relief (Government of Alberta)', 'AB', '2024-2026', 7183392, 8.5e6, 8.5e6, 'Recorded grants $3,193,762 (2024) + $3,989,630 (2025); committed $5.5M stabilization + $3M tax relief', 'Municipality of Jasper 2025 financial statements Note 16; JRCC report', JRCC, 'Lost municipal tax and fee revenue from destroyed property; a transfer'),
    ('Jasper business and tourism supports (PrairiesCan, Economic Development Canada, Alberta Tourism)', 'AB', '2024-2026', 11.4e6, 11.4e6, 11.4e6, 'Small business grants $3.35M, tourism initiatives $3M, Tourism Jasper $0.75M, pop-up village $1.8M, Alberta tourism $2.5M', 'JRCC Year Two Progress Report', JRCC, 'Transfers, not losses'),
    ('Quebec 2023 forest-fire business liquidity aid (loans and guarantees)', 'QC', '2023-2024', 3.6e6, 23e6, 50e6, '165 loans or guarantees totalling $23M by Apr 3 2024; up to $3.6M forgivable; $50M allocated', 'Gouvernement du Quebec news release, Apr 3 2024', 'https://www.quebec.ca/nouvelles/actualites/details/aide-financiere-a-la-suite-des-feux-de-foret-de-lete-2023-bonification-des-programmes-paupme-et-paresau-pour-soutenir-les-entreprises-touchees-54802', 'Loans, not losses; only the forgiven part is a cost to government'),
    ('BC 2023 Wildfire and Drought AgriRecovery Initiative (budget)', 'BC', '2023', 0, None, 71e6, 'Up to $71M federal-provincial budget for wildfire and drought costs; the province states it is not an estimate of damage', 'Government of British Columbia news release 2023AF0056-001624, Oct 20 2023', 'https://news.gov.bc.ca/releases/2023AF0056-001624', 'Wildfire share and actual payments not found'),
]:
    add(item=it, sector='economic (transfer or support)', jurisdiction=j, period=per, amount_low_cad=lo,
        amount_central_cad=('' if ce is None else ce), amount_high_cad=hi, dollars_basis='nominal CAD', basis='actual or committed',
        method=meth, source_name=src, url=url, overlaps_with='insured business interruption, GDP rows, gov_ support lines', additive='no (transfer)', notes=note)

# write econ_costs.csv
with open(os.path.join(BASE, 'econ_costs.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)

# summary of additive totals
def tot(filter_fn):
    s = [0.0, 0.0, 0.0]
    for r in rows:
        if filter_fn(r):
            for i, c in enumerate(('amount_low_cad', 'amount_central_cad', 'amount_high_cad')):
                s[i] += float(r[c] or 0)
    return s
groups = [
    ('Property: buildings missing or under-counted in the bill (official counts)', lambda r: r['sector'] == 'property' and r['additive'] == 'yes'),
    ('Property: Kingston NL, insured value (industry only)', lambda r: r['sector'] == 'property' and r['additive'] == 'yes (industry only)'),
    ('Infrastructure: utilities (BC Hydro, Manitoba Hydro, SaskPower)', lambda r: r['sector'] == 'infrastructure' and r['additive'] == 'yes'),
    ('Infrastructure: Jasper rebuild, Halifax, Kelowna (check gov_ for overlap)', lambda r: r['sector'] == 'infrastructure' and r['additive'] in ('yes (check gov_)', 'partial (check gov_)')),
    ('Economic: oil and gas shut in (2023, 2025)', lambda r: r['sector'] == 'economic (oil and gas)' and r['additive'] == 'yes'),
    ('Economic: GDP lost in mining, rail, accommodation, forestry (2023, 2024)', lambda r: r['sector'] == 'economic (GDP)' and r['additive'] == 'yes'),
    ('Economic: Parks Canada fees, Prince Albert', lambda r: r['sector'] == 'economic (tourism)' and r['additive'] == 'yes'),
]
lines = ['| Additive group | Low | Central | High |', '|---|---|---|---|']
grand = [0.0, 0.0, 0.0]
for name, fn in groups:
    s = tot(fn)
    grand = [a + b for a, b in zip(grand, s)]
    lines.append(f'| {name} | ${s[0]/1e6:,.0f} M | ${s[1]/1e6:,.0f} M | ${s[2]/1e6:,.0f} M |')
lines.append(f'| **Total additive** | **${grand[0]/1e6:,.0f} M** | **${grand[1]/1e6:,.0f} M** | **${grand[2]/1e6:,.0f} M** |')
alt = tot(lambda r: r['additive'].startswith('alternative (industry'))
lines.append(f'| Not in total: industry property adjustment (insured minus bill, six events) | ${alt[0]/1e6:,.0f} M | ${alt[1]/1e6:,.0f} M | ${alt[2]/1e6:,.0f} M |')
open(os.path.join(W, 'econ_summary_table.md'), 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print('rows', len(rows))

# ---------------- MANIFEST ----------------
WEB = [  # sources read with WebFetch (no local copy) or used as pointers only
    ('https://parks.canada.ca/agence-agency/dp-pd/ef-fs/2024-2025dpr', 'Parks Canada', 'Financial statements 2024-25 (revenues, Note 8 and statement of operations)', 'official', 'WebFetch (curl to parks.canada.ca timed out)'),
    ('https://www.canada.ca/en/parks-canada/news/2025/02/government-of-canada-funding-for-2024-wildfire-season-in-parks-canada-administered-places-including-jasper-national-park-wildfire-response-recovery.html', 'Parks Canada', 'Backgrounder: $133.1M for the 2024 wildfire season (cross-check of JRCC figures)', 'official', 'WebFetch (curl to canada.ca timed out)'),
    ('https://www.kelowna.ca/node/581505', 'City of Kelowna', 'When fire shut down the Glenmore Landfill ($1.4M repairs)', 'official', 'WebFetch'),
    ('https://www.saskatchewan.ca/government/news-and-media/2025/november/04/crown-corporations-support-northern-wildfire-recovery-and-help-communities-and-families', 'Government of Saskatchewan', 'Crown corporations support northern wildfire recovery (SaskPower $8.5M)', 'official', 'WebFetch (page is script-rendered; local copy has no text)'),
    ('https://www.gov.nl.ca/releases/2025/jps/0811n08/', 'Government of Newfoundland and Labrador', 'Wildfire advisory Aug 11 2025 (no damage count)', 'official', 'WebFetch'),
    ('https://efiling-webapi.auc.ab.ca/Document/Get/787175', 'Alberta Utilities Commission', 'Decision 26573-D01-2023 (ATCO, predates Jasper fire; not used)', 'official', 'WebFetch; curl failed'),
    ('https://www.ordersdecisions.bcuc.com/bcuc/decisions/en/518244/1/document.do', 'BC Utilities Commission', 'FortisBC 2022 rates decision (2021 Nk\'Mip fire Z-factor; not in scope, used to find the mechanism)', 'official', 'WebFetch'),
    ('https://www.westkelownacity.ca/en/our-community/mcdougall-creek-wildfire-information.aspx', 'City of West Kelowna', 'McDougall Creek wildfire information (no dollar figures)', 'official', 'WebFetch'),
    ('https://www.westkelownacity.ca/news/posts/council-highlights-aug-27-2024/', 'City of West Kelowna', 'Council highlights Aug 27 2024 (no wildfire dollar figures)', 'official', 'WebFetch'),
    ('https://www.jasperlocal.com/2026/04/15/wildfire-affected-utilities-require-9m-in-repairs/', 'Jasper Local', 'News pointer to the Apr 14 2026 utility repair report (no number taken)', 'news (pointer only)', 'WebFetch'),
    ('https://www.jasperlocal.com/2026/08/13/jasper-digs-into-next-phase-of-wildfire-utility-repairs/', 'Jasper Local', 'News pointer to Bylaw #284 (no number taken)', 'news (pointer only)', 'WebFetch'),
    ('https://cfjctoday.com/2026/09/10/b-c-wildfire-season-winding-down-with-lower-burned-area-but-high-structural-loss/', 'Canadian Press via CFJC', 'News pointer: 2026 BC structure losses (no number taken)', 'news (pointer only)', 'WebFetch'),
    ('https://www.ctvnews.ca/vancouver/bc-wildfires/article/with-500-plus-structures-damaged-or-lost-bcs-fire-season-is-among-the-worst/', 'CTV / Canadian Press', 'News pointer: 2026 BC structure losses (no number taken)', 'news (pointer only)', 'WebFetch'),
    ('https://www.theweathernetwork.com/en/news/weather/forecasts/kingston-fire-destroys-203-structures-says-n-l-premier', 'The Weather Network / Canadian Press', 'News pointer: NL premier count (no number taken)', 'news (pointer only)', 'WebFetch'),
    ('https://www.theweathernetwork.com/en/news/weather/severe/halifax-faces-more-than-20m-repair-bills-after-year-of-hurricane-fire-floods', 'The Weather Network / Canadian Press', 'News pointer to HRM report Sep 20 2023 (number taken from the HRM report)', 'news (pointer only)', 'WebFetch'),
    ('https://globalnews.ca/news/10106146/1-4-million-needed-repairs-kelowna-landfill-wildfires/', 'Global News', 'News pointer to Kelowna landfill repairs (number taken from kelowna.ca)', 'news (pointer only)', 'WebFetch'),
]
DESC = {  # local file -> (publisher, description, data type)
    'statcan_daily': ('Statistics Canada', 'The Daily release', 'official'),
    'statcan_tables': ('Statistics Canada', 'Full table download', 'official'),
    'ab_prices': ('Government of Alberta (Energy and Minerals)', 'Monthly reference price calculations / BVM components', 'official'),
    'aer_st3': ('Alberta Energy Regulator', 'ST-3 monthly statistics (prices, production)', 'official (regulator)'),
    'catiq': ('CatIQ', 'Insured loss release', 'industry'),
    'ibc': ('Insurance Bureau of Canada', 'Insured loss report (CatIQ data)', 'industry'),
    'jasper': ('Municipality of Jasper', 'Council agenda, budget or financial statements', 'official (municipal)'),
    'manitoba': ('Government of Manitoba', 'Report', 'official'),
    'mbhydro': ('Manitoba Hydro', 'Quarterly report or news release', 'official (Crown corporation)'),
    'saskatchewan': ('Government of Saskatchewan', 'Report or release', 'official'),
    'bchydro': ('BC Hydro', 'Annual service plan report or release', 'official (Crown corporation)'),
    'bcuc': ('BC Utilities Commission', 'Decision or order', 'official (regulator)'),
    'boc': ('Bank of Canada', 'Monetary Policy Report', 'official (central bank)'),
    'hrm': ('Halifax Regional Municipality', 'Committee report or minutes', 'official (municipal)'),
    'hydroquebec': ('Regie de l\'energie du Quebec', 'Hydro-Quebec rate case document', 'official (regulator)'),
    'nl': ('Government of Newfoundland and Labrador', 'News release', 'official'),
    'nshelburne': ('Municipality of the District of Shelburne', 'Council package', 'official (municipal)'),
    'ntpc': ('Northwest Territories Power Corporation', 'Annual report 2023-24', 'official (Crown corporation)'),
    'nwt': ('Government of the Northwest Territories', '2023 Wildfire Response Review', 'official (commissioned review)'),
    'quebec': ('Gouvernement du Quebec', 'News release', 'official'),
    'agri': ('Governments of BC / Canada', 'AgriRecovery release or QP note', 'official'),
    'bc2026': ('Okanagan Indian Band; Thompson-Nicola Regional District', 'Website posts (WordPress API)', 'official (First Nation / regional district)'),
    'statcan_geo': ('Statistics Canada', 'Boundary service (failed)', 'official'),
    'aucab': ('Alberta Utilities Commission', 'Document (curl failed)', 'official'),
}
def title_of(path):
    try:
        if path.endswith(('.htm', '.html')):
            s = open(path, encoding='utf-8', errors='ignore').read(200000)
            m = re.search(r'<title>(.*?)</title>', s, flags=re.S)
            return html.unescape(re.sub(r'\s+', ' ', m.group(1))).replace('\u2014', ':').replace('\u2013', '-').replace('\xa0', ' ').strip()[:150] if m else ''
        if path.endswith('.pdf'):
            t = subprocess.run(['pdftotext', '-l', '1', path, '-'], capture_output=True, text=True, timeout=60).stdout
            t = ' '.join(t.split()).replace('\u2014', ':').replace('\u2013', '-')
            return t[:150]
    except Exception:
        return ''
    return ''
man = []
seen = set()
for line in open(os.path.join(W, 'econ_downloads.tsv')):
    p, url, ts, code, size, sha = line.rstrip('\n').split('\t')
    if p in seen:
        continue
    seen.add(p)
    sub = p.split('/')[2]
    pub, desc, typ = DESC.get(sub, ('', '', ''))
    full = os.path.join(BASE, p)
    ok = code == '200' and int(size) > 500
    t = title_of(full) if ok else ''
    if 'Page not found' in t or "couldn't find" in t or 'Error 404' in t:
        ok = False
    man.append(dict(local_path=p, url=url, accessed_utc=ts, http_code=code, bytes=size, sha256_16=sha, publisher=pub,
                    title_or_description=(t or desc), data_type=typ, status=('ok' if ok else 'failed or not found')))
for (url, pub, desc, typ, how) in WEB:
    man.append(dict(local_path='(none: read with WebFetch)', url=url, accessed_utc=ACC, http_code='', bytes='', sha256_16='',
                    publisher=pub, title_or_description=desc, data_type=typ, status=how))
for (p, pub, desc) in [
    ('../property/destroyed_value_estimates.csv', 'this project (analysis/property)', 'Bill building values by event (flagged x DA average value)'),
    ('../property/destroyed_value_official.csv', 'this project (analysis/property)', 'Official counts x local values'),
    ('../property/raw/census/*_dwelling_value_2021.csv', 'Statistics Canada (via analysis/property)', '2021 Census average and median value of owner-occupied dwellings, accessed 2026-10-21'),
    ('../economic-value/parks_fire_attendance.csv; parks_attendance_long.csv', 'Parks Canada (via analysis/economic-value)', 'Attendance by park and fiscal year, accessed 2026-10-21'),
    ('../../data/geo/statcan/tables/98100015/98100015.csv', 'Statistics Canada (project data)', 'Population and dwelling counts 2021 by CSD (Enterprise 51 private dwellings)')]:
    man.append(dict(local_path=p, url='', accessed_utc='2026-10-21', http_code='', bytes='', sha256_16='', publisher=pub,
                    title_or_description=desc, data_type='official / project output', status='reused'))
with open(os.path.join(BASE, 'econ_manifest.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(man[0].keys())); w.writeheader(); w.writerows(man)
print('manifest rows', len(man), 'ok', sum(1 for m in man if m['status'] == 'ok'))
