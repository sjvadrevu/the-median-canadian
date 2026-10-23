"""Build measures.csv, research_underway.csv and summary numbers for the policy analysis.
Inputs: work/fed_program_spending.csv, work/fed_transfer_payments.csv (from 01_infobase_extract.py),
../economic-value/raw/grants/grants_wildfire_all.csv (federal proactive disclosure, wildfire rows),
../economic-value/federal_wildfire_programs_agreements.csv, ../../data/smoke-cost/wildfire_spending_by_jurisdiction.csv.
Curated measure records below are transcribed from the primary documents named in each row (raw/ copies where held).
Run: python3 -I scripts/02_build_outputs.py"""
import pandas as pd, os
B = os.path.dirname(os.path.abspath(__file__)) + '/../'
A = B + '../'
IB = 'https://open.canada.ca/data/en/dataset/a35cf382-690c-4221-a971-cf0fd189a46f'
FIN = {
 'b2019': 'https://www.budget.canada.ca/2019/docs/plan/budget-2019-en.pdf',
 'b2021': 'https://www.budget.canada.ca/2021/pdf/budget-2021-en.pdf',
 'b2022': 'https://www.budget.canada.ca/2022/pdf/budget-2022-en.pdf',
 'fes2023': 'https://www.budget.canada.ca/fes-eea/2023/report-rapport/FES-EEA-2023-en.pdf',
 'b2024': 'https://budget.canada.ca/2024/report-rapport/budget-2024.pdf',
 'b2025': 'https://budget.canada.ca/2025/report-rapport/pdf/budget-2025.pdf',
 'seu2026': 'https://budget.canada.ca/update-miseajour/2026/report-rapport/toc-tdm-en.html',
}
NR = 'https://natural-resources.canada.ca/'
TP5 = NR + 'corporate/planning-reporting/departmental-results-reports/details-transfer-payment-programs-over-5-million'
TPU5 = NR + 'corporate/planning-reporting/departmental-results-reports/details-transfer-payment-programs-under-5-million'
D = '2026-10-22'

# ---------- computed federal spending (Public Accounts transfer payments, InfoBase) ----------
tp = pd.read_csv(B + 'work/fed_transfer_payments.csv')
def tpsum(pat, org=134):
    x = tp[(tp.org_id == org) & tp.description.str.contains(pat, case=False)]
    return x.expenditures.sum(), x.authorities.sum(), ', '.join(sorted(x.fy_ef.str.replace('FY ', '')))
fm_sp, fm_au, fm_y = tpsum('Fighting and Managing')
rcf_sp, rcf_au, _ = tpsum('Resilient Communities')
kn_sp, kn_au, _ = tpsum('Foundational Wildland Fire Knowledge')
coe_sp, coe_au, _ = tpsum('Centre of Excellence')
wfr_sp, wfr_au, _ = tpsum('Wildland Fire Resilience')
sp = pd.read_csv(B + 'work/fed_program_spending.csv')
btl = sp[sp.program_id == 'BTL12'].set_index('fy_ef')
isc = sp[sp.label == 'ISC Emergency Management Assistance'].set_index('fy_ef')
dmaf_tp = tp[tp.description.str.contains('Disaster Mitigation and Adaptation Fund')]
dfaa = pd.read_csv(A + 'losses/dfaa_wildfire_payments.csv')
dfaa_2325 = dfaa[dfaa.event_year.between(2023, 2025)].agreement_value.sum()

g = pd.read_csv(A + 'economic-value/raw/grants/grants_wildfire_all.csv', low_memory=False)
g = g.sort_values('amendment_number').drop_duplicates('ref_number', keep='last')
dmaf_wf = g[g.prog_name_en.str.contains('Disaster M', na=False) & g.agreement_title_en.str.contains('ildfire', na=False)]

M = []
def m(level, jur, name, kind, yr, ann, spent, basis, target, finding, stage, status, url, acc=D):
    M.append(dict(level=level, jurisdiction=jur, name=name, budget_or_nonbudget=kind, year_announced=yr,
                  amount_announced_cad=ann, amount_spent_cad=spent, spent_basis=basis, target=target,
                  finding_addressed=finding, stage=stage, status_2026_10_22=status, source_url=url, accessed=acc))

F1 = 'F1 monitored/modified share'; F2 = 'F2 fast growth to 1,000 ha in 3 days'; F3 = 'F3 remote starts >10 km from road'
F4 = 'F4 early control of lightning fires'; F0 = 'none of F1-F4 (recovery, evacuation or all-hazard)'

# ---------------- FEDERAL ----------------
m('federal', 'Canada (ISC)', 'Emergency management on-reserve: resiliency and EM (all hazards) incl. FireSmart on-reserve expansion', 'budget', 2019,
  211.0e6, None, 'not broken out; ISC Emergency Management Assistance program actual 2019-20 to 2024-25 in InfoBase is response-driven (e.g. 2024-25 $678.7M actual vs $197.4M planned)',
  '$211.0M over 5 years from 2019-20, $49.4M/yr ongoing', F0, 'spending (not separable)', 'Ongoing; FireSmart share not reported separately',
  FIN['b2019'] + ' ; ' + IB)
m('federal', 'Canada (Parks Canada)', 'Wildfire preparedness in national parks (National Wildfire Program)', 'budget', 2021, 100.6e6, None,
  'not broken out in held InfoBase extract', '$100.6M over 5 years from 2021-22; 2026 update extends $9M/yr', f'{F4}; {F1}', 'funded',
  'Extended in 2026 Economic and Fiscal Update ($9M/yr 2026-27 to 2030-31); 2026-27 indicator targets 200 ha FireSmart vegetation treatment (BGW08), no result yet',
  FIN['b2021'] + ' ; ' + FIN['seu2026'])
m('federal', 'Canada (NRCan)', 'Mapping northern wildfire risk and CIFFC capacity', 'budget', 2021, 28.7e6, 4.0e6,
  'CIFFC grant $1.0M/yr 2021-22 to 2024-25 (Public Accounts); mapping spending not separable; Indigenous mapping contributions $0 spent of $225k authorities',
  '$28.7M over 5 years from 2021-22', f'{F3}', 'spending', 'Extended in 2026 update ($6M/yr 2026-27 to 2030-31, Wildfire Risk Mapping)',
  FIN['b2021'] + ' ; ' + IB + ' ; ' + FIN['seu2026'])
m('federal', 'Canada (INFC)', 'Disaster Mitigation and Adaptation Fund top-up (all hazards, wildfire eligible)', 'budget', 2021, 1.4e9,
  float(dmaf_tp[dmaf_tp.fy_ef >= 'FY 2021-22'].expenditures.sum()),
  f'All DMAF contributions FY2021-22 to 2024-25 (all hazards). Wildfire-titled DMAF agreements in proactive disclosure: {len(dmaf_wf)} worth ${dmaf_wf.agreement_value.sum()/1e6:.1f}M (NWT fuel storage, SK risk reduction, Whistler fuel treatment, NWT resilience, southern Yukon hazard mitigation)',
  '$1.4B over 12 years from 2021-22', f'{F2} (fuel treatment near communities)', 'spending', 'Wildfire projects run to 2028 to 2033; no wildfire outcome indicator published',
  FIN['b2021'] + ' ; https://open.canada.ca/data/en/dataset/432527ab-7aac-45b5-81d6-7597107a7013')
m('federal', 'Canada (NRCan)', 'FMWCC Equipment Fund: provinces/territories buy firefighting equipment', 'budget', 2022, 269.0e6, None,
  'see FMWCC contributions row; 2024-25: 12 P/T agreements, NRCan incremental equipment investment over $42M',
  '$269M over 5 years from 2022-23', f'{F4}; {F2}', 'delivered with indicator', 'Fund closed to applications; agreements with BC, AB, SK, MB, ON, QC, NB, NS, PE, YT and others announced 2023-2025',
  NR + 'forests-forestry/wildland-fires/fighting-managing-wildfires-changing-climate-program ; ' + TP5)
m('federal', 'Canada (NRCan)', 'FMWCC Training Fund: train 1,000 additional community-based firefighters', 'budget', 2022, 37.9e6, None,
  'see FMWCC contributions row', '1,000 additional trained firefighters', f'{F4}; {F3}', 'results reported',
  '2024-25 DRR: 20 agreements trained 112 community-based firefighters (Type I-III) and 83 Indigenous participants; IAFF trained 421 structural firefighters in WUI. NRCan 2025-08-18 release: "on track to train over 2,800" (projection). Cumulative count against 1,000 not published as a result',
  TP5 + ' ; https://www.canada.ca/en/natural-resources-canada/news/2025/08/canada-invests-in-firefighting-training.html')
m('federal', 'Canada (NRCan)', 'FMWCC contributions actually paid (Equipment + Training, NRCan share of $346.1M program)', 'budget', 2022, 306.9e6, fm_sp,
  f'Public Accounts transfer payments FY{fm_y}; authorities ${fm_au/1e6:.1f}M', '$306.9M NRCan ($269M + $37.9M) over 2022-23 to 2026-27',
  f'{F4}; {F2}', 'spending', f'${fm_sp/1e6:.1f}M paid in first 3 of 5 years ({fm_sp/306.9e6:.0%})', IB + ' ; ' + TP5)
m('federal', 'Canada (ISC)', 'Firefighting equipment for First Nations communities', 'budget', 2022, 39.2e6, None,
  'not separable in held records', '$39.2M over 5 years from 2022-23', f'{F3}', 'funded', 'No spending or results figure found in held records', FIN['b2022'])
m('federal', 'Canada (CSA, NRCan, ECCC)', 'WildFireSat wildfire monitoring satellite system', 'budget', 2022, 169.9e6, None,
  'CSA Space Utilization variance notes: $13.8M reprofiled 2021-22 after scope change; later variances "due to delays in obtaining project and contract authority approvals"',
  'Daily monitoring of all active fires; launch targeted 2029', f'{F2}', 'announced only (no satellite)',
  'Launch still targeted for 2029 (NRCan page modified 2026-05-06). Earlier contract terminated; CSA posted a new Request for Information 2026-05-22 (NRCan e-bulletin Issue 6, Aug 2026)',
  NR + 'forests-forestry/wildland-fires/wildfiresat-canadian-operational-mission ; ' + NR + 'forests-forestry/wildland-fires/wildfiresat-e-bulletin ; ' + IB)
m('federal', 'Canada (NRCan)', 'Wildfire Resilient Futures Initiative (FireSmart, foundational knowledge, Centre of Excellence)', 'budget (Adaptation Action Plan)', 2023, 285.0e6,
  rcf_sp + kn_sp + coe_sp, f'Public Accounts: Resilient Communities through FireSmart ${rcf_sp/1e6:.1f}M of ${rcf_au/1e6:.1f}M authorities; Foundational Knowledge ${kn_sp/1e6:.2f}M of ${kn_au/1e6:.1f}M; Centre of Excellence ${coe_sp/1e6:.2f}M of ${coe_au/1e6:.2f}M (FY2023-24 to 2024-25)',
  '$285M over 5 years from 2023-24 ($150.7M FireSmart, $48M knowledge, Centre of Excellence)', f'{F2}; {F1}', 'spending',
  f'${(rcf_sp+kn_sp+coe_sp)/1e6:.1f}M paid in first 2 of 5 years ({(rcf_sp+kn_sp+coe_sp)/285e6:.0%}). 2024-25 results: 75 FireSmart initiatives completed in 52 communities, 618 ha vegetation treated, 118 in progress',
  NR + 'forests-forestry/wildland-fires/wildfire-resilient-futures-initiative ; ' + TP5 + ' ; ' + IB)
m('federal', 'Canada', 'National Adaptation Strategy wildfire target', 'non-budget', 2023, None, None, '',
  'High-risk communities, including northern and Indigenous, develop wildfire community prevention and mitigation plans by 2030, with up to 15% implemented by 2028',
  f'{F2}', 'announced only (target)', 'No national progress figure found in held records; NAS PDF download failed (HTML saved), target text read from canada.ca page modified 2023-08-01',
  'https://www.canada.ca/en/services/environment/weather/climatechange/climate-plan/national-adaptation-strategy/full-strategy.html')
m('federal', 'Canada (ISC)', 'Emergency response and recovery on reserve (2023 wildfires)', 'budget (FES)', 2023, 260.0e6, None,
  'ISC Emergency Management Assistance actual 2023-24 $595.2M vs planned $207.9M (all hazards)', 'one-time 2023-24', F0, 'spending', 'Spent within EMAP; not separable',
  FIN['fes2023'] + ' ; ' + IB)
m('federal', 'Canada (CCFM/NRCan)', 'Canadian Wildland Fire Prevention and Mitigation Strategy', 'non-budget', 2024, None, None, '',
  'Whole-of-society prevention and mitigation vision', f'{F2}', 'announced only (strategy)', 'Released June 2024 per NRCan 2024-25 DRR; no indicator',
  NR + 'corporate/planning-reporting/departmental-results-reports/natural-resource-canada-s-2024-25-departmental-results-report')
m('federal', 'Canada (NRCan)', 'IAFF wildland-urban interface training', 'budget', 2024, 0.8e6, None, 'within FMWCC', 'train structural firefighters for WUI', F0,
  'results reported', '421 structural firefighters trained (2024-25 DRR)', FIN['b2024'] + ' ; ' + TP5)
m('federal', 'Canada (ISC, CIRNAC)', 'First Nations climate resiliency and structural mitigation', 'budget', 2024, 145.2e6, None, 'not separable',
  '$145.2M over 5 years from 2024-25 (all climate hazards)', f'{F2} (community protection)', 'funded', 'No wildfire-specific result found', FIN['b2024'])
m('federal', 'Canada (CIRNAC)', 'Support to Indigenous governments affected by 2023 NWT wildfires', 'budget', 2024, 9.0e6, None, '', 'one-time 2023-24', F0,
  'funded', 'One-time', FIN['b2024'])
m('federal', 'Canada (Parks Canada)', 'Emergency wildfires response (2023)', 'budget', 2024, 38.0e6, None, '', 'one-time 2023-24', F0, 'funded', 'One-time', FIN['b2024'])
m('federal', 'Canada (NRCan to CIFFC)', 'National Aerial Wildfire Capacity: lease four aircraft for P/T use', 'budget', 2025, 257.6e6, 0.0,
  'CIFFC audited statements to 2026-03-31: agreement signed 2026-02-19, up to $316.75M over 2026-04-01 to 2031-03-31, no funds received or spent at year end',
  'Four leased aircraft available to provinces and territories', f'{F4}; {F2}', 'funded',
  'Contribution agreement in force from 2026-04-01; no aircraft delivery figure found in held records for the 2026 season',
  FIN['b2025'] + ' ; https://ciffc.ca/publications/ (CIFFC financial statements 2026-03-31, note 15)')
m('federal', 'Canada (NRCan to CIFFC)', 'CIFFC Frontline Gear Support Initiative', 'non-budget (program agreement)', 2026, 19.0e6, 0.0,
  'Signed 2026-07-22, up to $5M/yr to 2029-30', 'Equipment, deployment, training exchanges', f'{F4}', 'funded', 'Agreement signed after year end', 'https://ciffc.ca/publications/ (CIFFC financial statements 2026-03-31, note 16)')
m('federal', 'Canada (Parks Canada)', 'Jasper wildfire response and rebuilding Jasper National Park', 'budget', 2025, 212.0e6, None, '', '2024-25 to 2029-30', F0, 'funded', 'Recovery', FIN['b2025'])
m('federal', 'Canada (NRCan, PC)', 'Extending Wildfire Risk Mapping ($6M/yr) and National Wildfire Program ($9M/yr)', 'budget', 2026, 75.0e6, None, '',
  '2026-27 to 2030-31', f'{F3}; {F4}', 'announced only', 'Announced in 2026 Economic and Fiscal Update; not yet in Estimates held', FIN['seu2026'])
m('federal', 'Canada (PS)', 'Disaster Financial Assistance Arrangements, wildfire events 2023 to 2025', 'non-budget (statutory cost-sharing)', 2023, None, dfaa_2325,
  'Sum of DFAA payment orders for 2023, 2024 and 2025 wildfire events in proactive disclosure (interim; final claims pending)', 'Federal share of eligible response and recovery costs', F0,
  'spending', '2023 events $793M; 2024 events $184M; 2025 events $12.5M so far', 'https://open.canada.ca/data/en/dataset/432527ab-7aac-45b5-81d6-7597107a7013')
m('federal', 'Canada (NRCan)', 'Wildfire Risk Management program, total actual spending (all NRCan wildfire activity incl. CWFIS)', 'budget (program total)', 2020, float(btl.planned_spending_1.sum()),
  float(btl.actual_spending.sum()), 'InfoBase actual 2020-21 to 2024-25; planned figure includes 2025-26 plan $165.8M', 'CWFIS uptime 97% in season', f'{F2}; {F4}', 'results reported',
  'Actual rose from $12.1M (2020-21) to $100.8M (2024-25); 2024-25 actual 77% of planned ($130.4M). CWFIS uptime 99.9% in 2024 vs 97% target', IB)

# ---------------- PROVINCES / TERRITORIES ----------------
SP = 'https://www2.gov.bc.ca/gov/content/safety/wildfire-status/about-bcws/wildfire-statistics/wildfire-averages'
m('provincial', 'BC', 'Fire Management vote vs actual (base budget vs emergency spending)', 'budget', 2026, 235.702e6, 849.7e6,
  'Budget 2026 vote $235.7M plus $614.0M over budget forecast (First Quarterly Report 2026-09-14); BCWS total cost 2023 $1,094.8M, 2024 $769.4M, 2025 estimate $510M',
  'base vote', F0, 'spending', 'Emergency costs run 2 to 4 times the voted base', 'https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Estimates.pdf ; https://news.gov.bc.ca/releases/2026FIN0031-001066 ; ' + SP, '2026-10-20')
m('provincial', 'BC', 'BCWS 2026 readiness: year-round positions, aircraft, cameras, night-vision helicopters', 'non-budget (operations)', 2026, 35.0e6, None,
  '$14M equipment + $21M Prince George depot (Budget 2024 capital)', 'more than 600 year-round positions; 28 fixed-wing aircraft in 8 tanker groups; 4 night-vision helicopters (260 missions in 2025); camera network', f'{F4}; {F2}',
  'delivered with indicator', 'Reported in place for 2026 season', 'https://news.gov.bc.ca/releases/2026FOR0005-000267')
m('provincial', 'AB', 'Wildfire base budget vs contingency spending', 'budget', 2025, 164.8e6, 925.5e6,
  '2025-26 voted actuals: 2.1 Wildfire Management $164.8M operating; 2.3 Presuppression and Response $756.2M from contingency (2023-24: $793.0M contingency; 2024-25: $455.4M contingency + $246.7M supplementary)',
  'base operating line', F0, 'spending', 'Response funded mostly from contingency each year', 'https://open.alberta.ca/dataset/2dedbb29-e005-4802-bf6e-03bf77536add/resource/db36b97e-fca3-4082-950b-4943de30687d/download/fp-annual-report-2025-2026.pdf', '2026-10-20')
m('provincial', 'AB', '2026 season additions: night-vision and hoist helicopters', 'non-budget (operations)', 2026, None, None, '',
  '3 more night-vision helicopters (7 total), 2 hoist helicopters', f'{F4}', 'announced only (no primary page reached)',
  'Statement found only as a reprint on kutd.awna.com (2026-03-06); alberta.ca original not reached, so not counted', 'not reached: alberta.ca release')
m('provincial', 'ON', 'Emergency Forest Firefighting estimate vs actual', 'budget', 2026, 149.95e6, 273.0e6,
  '2026-27 Estimates net $149.95M (gross $161.0M); actual 2025-26 $273.0M, 2024-25 $171.0M, 2023-24 $206.5M (Public Accounts)',
  'base estimate', F0, 'spending', '2026-27 estimate is 55% of the 2025-26 actual', 'https://www.ontario.ca/page/expenditure-estimates-ministry-natural-resources-2026-2027 ; https://data.ontario.ca/dataset/public-accounts-ministry-statements-and-schedules')
m('provincial', 'SK', 'SPSA appropriation: budget vs supplementary', 'budget', 2025, 78.2e6, 351.6e6,
  'Budget estimates $78.2M + supplementary $313.2M (2025-26); 2025 season cost $351.6M (2025 dollars); 2026-27 budget $76.3M',
  'base appropriation', F0, 'spending', 'Provincial Auditor: variable response costs exceeded initial budget by over $70M every year since 2023',
  'https://auditor.sk.ca/pub/publications/public_reports/2026/Volume%201/ch-05----saskatchewan-public-safety-agencyresource-planning-for-wildfire-response.pdf', '2026-10-20')
m('provincial', 'SK', 'Provincial Auditor audit of SPSA resource planning (after-action type review)', 'non-budget (audit)', 2026, None, None, '',
  '11 recommendations', f'{F4}; {F2}', 'results reported',
  'Initial-attack success (held under 10 ha) fell to 70% in 2025 from 76% in 2024; mutual-aid contracted resources $26.3M in 2025 vs $1.9M in 2024; 21 of 89 higher-risk northern communities lack a preparedness plan; air tankers grounded by engineer vacancies (31 of 37 filled)',
  'https://auditor.sk.ca/pub/publications/public_reports/2026/Volume%201/2026-report-v1__resource-planning-for-wildfire-response--news-release.pdf')
m('provincial', 'MB', 'Emergency Expenditures: wildfire response 2025-26', 'budget', 2025, None, 308.0e6,
  '$179M expended to Q1 plus $129M forecast over-expenditure (First Quarter Report, Sept 2025)', '', F0, 'spending', 'Over budget', 'https://gov.mb.ca/asset_library/en/proactive/20252026/first-quarter-report-september2025.pdf', '2026-10-20')
m('provincial', 'MB', 'Purchase of three DHC-515 waterbombers', 'non-budget', 2025, None, None, '', 'three new airtankers', f'{F4}', 'announced only (no primary page reached)',
  'Only trade press and news found; no gov.mb.ca release reached in this run, so not counted', 'not reached: news.gov.mb.ca')
m('provincial', 'QC', 'Canada-Quebec wildfire equipment (SOPFEU): vehicles, drones, telecoms, avionics', 'budget (cost-shared)', 2025, 64.0e6, None, '',
  '$32M federal + $32M Quebec over 3 years', f'{F4}', 'funded', 'Delivery not reported in held records',
  'https://www.canada.ca/fr/ressources-naturelles-canada/nouvelles/2025/01/le-canada-et-le-quebec-annoncent-un-investissement-majeur-dans-des-equipements-de-lutte-contre-les-feux-de-foret.html')
m('provincial', 'NT', 'Fire suppression shortfall supplementary appropriations', 'budget', 2023, None, 114.5e6,
  '$75.0M (2023-24) and $39.5M (2025-26) supplementary appropriations', '', F0, 'spending', 'Appropriated', 'https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2025-10/TD%20388-20%281%29%20Supplementary%20Estimates%20%28Operations%20Expenditures%29%20No%202%202025-2026.pdf', '2026-10-20')
m('provincial', 'NT', '2023 wildfire After-Action Review and GNWT response', 'non-budget (review)', 2025, None, None, '',
  '35 recommendations', f'{F1}; {F2}', 'results reported (partial)',
  'GNWT response Oct 2025: agrees 26, generally agrees 5, partially 3, disagrees 1 (territorial EM agency). 1 recommendation complete; most ongoing. Earlier 2024 independent review: crews and aircraft brought on earlier, new prevention and mitigation programs. Response zones not addressed',
  'https://www.maca.gov.nt.ca/en/content/gnwt-response-2023-after-action-review-recommendations ; https://www.gov.nt.ca/en/newsroom/independent-review-recommends-improvements-wildfire-response-government-provides-responses')
m('provincial', 'NT', 'NWT community wildfire resilience and fuel storage (DMAF)', 'budget (federal cost-shared)', 2020, 41.7e6, None, '',
  'fuel storage $21.75M (2020-2028); community resilience $19.99M (2024-2033)', f'{F2}', 'funded', 'Under way', 'https://open.canada.ca/data/en/dataset/432527ab-7aac-45b5-81d6-7597107a7013')
m('provincial', 'YT', 'Southern Yukon wildfire hazard mitigation (DMAF)', 'budget (federal cost-shared)', 2025, 13.84e6, None, '', 'fuel breaks 2025-2033', f'{F2}', 'funded', 'Under way', 'https://open.canada.ca/data/en/dataset/432527ab-7aac-45b5-81d6-7597107a7013')
m('provincial', 'all agencies', 'Response-zone (monitor vs full response) policy changes', 'non-budget', None, None, None, '',
  '', f'{F1}; {F3}', 'none found', 'No change to QC northern zone, YT zones, ON zones or NWT values-at-risk policy found in records reached; NWT 2025 response does not address zones', '')

ms = pd.DataFrame(M)
ms.to_csv(B + 'measures.csv', index=False)

# ---------------- RESEARCH UNDERWAY ----------------
g['end'] = pd.to_datetime(g.agreement_end_date, errors='coerce')
g['org'] = g.owner_org_title.str.split(' [|] ').str[0]
res_orgs = ['National Research Council Canada', 'Canadian Space Agency', 'Natural Sciences and Engineering Research Council of Canada',
            'Canadian Institutes of Health Research', 'Environment and Climate Change Canada', 'Polar Knowledge Canada', 'Social Sciences and Humanities Research Council of Canada']
r = g[(g.org.isin(res_orgs) | g.prog_name_en.str.contains('Knowledge|Centre of Excellence|Wildland Fire Resilience', na=False))
      & (g.end >= D) & (g.ref_number != '1516-HQ-000023') & ~g.prog_name_en.str.contains('CanExport|Youth Employment', na=False)]
R = r[['org', 'prog_name_en', 'recipient_legal_name', 'recipient_province', 'agreement_title_en', 'agreement_value', 'agreement_start_date', 'agreement_end_date']].copy()
R.insert(0, 'kind', 'grant/contribution agreement')
R['status_2026_10_22'] = 'agreement active (end date after 2026-10-22)'
R['source_url'] = 'https://open.canada.ca/data/en/dataset/432527ab-7aac-45b5-81d6-7597107a7013'
R['accessed'] = '2026-10-21'
prog = pd.DataFrame([
 dict(kind='federal mission', org='CSA, NRCan, ECCC', prog_name_en='WildFireSat', recipient_legal_name='federal', recipient_province='', agreement_title_en='Satellite to monitor all active fires daily',
      agreement_value=169.9e6, agreement_start_date='2022-23', agreement_end_date='launch target 2029', status_2026_10_22='Earlier contract terminated; new RFI 2026-05-22; no satellite built',
      source_url=NR + 'forests-forestry/wildland-fires/wildfiresat-e-bulletin', accessed=D),
 dict(kind='federal program', org='Natural Resources Canada', prog_name_en='Canadian Forest Service fire research, CWFIS and predictive services (Wildfire Risk Management BTL12)', recipient_legal_name='federal', recipient_province='',
      agreement_title_en='CWFIS, fire weather and smoke forecasting, fuel type layer, national risk assessment', agreement_value=165.8e6, agreement_start_date='ongoing', agreement_end_date='2025-26 plan',
      status_2026_10_22='2024-25 actual $100.8M; CWFIS uptime 99.9%; updated fuel type layer released; 56 map products', source_url=IB + ' ; ' + NR + 'corporate/planning-reporting/departmental-results-reports/natural-resource-canada-s-2024-25-departmental-results-report', accessed=D),
 dict(kind='federal program', org='Natural Resources Canada', prog_name_en='WRFI Building and Mobilizing Foundational Wildland Fire Knowledge', recipient_legal_name='multiple', recipient_province='',
      agreement_title_en='Mission-oriented research projects, demonstration sites, Indigenous fire knowledge', agreement_value=48.0e6, agreement_start_date='2024-25', agreement_end_date='2027-28',
      status_2026_10_22=f'19 agreements; ${kn_sp/1e6:.2f}M paid by 2024-25; 22 researchers recruited', source_url=TP5, accessed=D),
 dict(kind='federal program', org='Natural Resources Canada', prog_name_en='Wildfire Resilience Consortium of Canada (Centre of Excellence)', recipient_legal_name='Wildfire Resilience Consortium of Canada', recipient_province='',
      agreement_title_en='National centre for wildland fire innovation and knowledge exchange', agreement_value=11.725e6, agreement_start_date='2025-02-17', agreement_end_date='2028-03-31',
      status_2026_10_22=f'${coe_sp/1e6:.2f}M paid in 2024-25', source_url=TPU5, accessed=D),
 dict(kind='federal program', org='Natural Resources Canada', prog_name_en='Mapping community wildfire risk (Indigenous engagement)', recipient_legal_name='federal', recipient_province='',
      agreement_title_en='Engagement on design of contribution program', agreement_value=225000.0, agreement_start_date='2021-22', agreement_end_date='ongoing',
      status_2026_10_22='$0 paid against $225k authorities 2021-22 to 2024-25; liaison officer hire planned 2025-26', source_url=TPU5, accessed=D),
])
R = pd.concat([prog, R], ignore_index=True)
R.to_csv(B + 'research_underway.csv', index=False)

# ---------------- summary numbers ----------------
fed = ms[ms.level == 'federal']
prev = fed[fed.name.str.contains('Equipment Fund|Training Fund|First Nations communities|WildFireSat|Resilient Futures|Aerial|Mapping|preparedness in national|Extending|Frontline')]
print('federal prevention/capacity announced 2021-2026 ($M):', round(prev.amount_announced_cad.sum() / 1e6, 1))
print('FMWCC paid', fm_sp / 1e6, 'WRFI paid', (rcf_sp + kn_sp + coe_sp) / 1e6, 'BTL12 actual', btl.actual_spending.sum() / 1e6)
print('DFAA 2023-25 events', dfaa_2325 / 1e6, 'DMAF wildfire', dmaf_wf.agreement_value.sum() / 1e6, len(dmaf_wf))
print('research rows', len(R), 'active agreements value', r.agreement_value.sum() / 1e6)
