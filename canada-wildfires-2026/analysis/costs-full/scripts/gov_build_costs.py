"""Government response costs of the 2023-2026 wildfires that are NOT in the current wildfire bill.

Bill (already counted, 2025 dollars): trees burned 2023-2026 at Crown stumpage ($13.0B); provincial
firefighting 2023-2025 for BC (Fire Management vote / BCWS total), AB (all wildfire lines), SK (SPSA season
costs) and ON (Emergency Fire Fighting, net of recoveries) ($6.4B); homes and buildings destroyed ($1.3B).

Every value below was read from an official record (see url column and gov_manifest.csv); values are typed in
with the exact figure printed in the source. 2025 dollars use the same CPI factors as analysis/economic-value
(Statistics Canada CPI all-items, v41690973 via Bank of Canada Valet, annual mean; 2026 = Jan-Sep mean),
factor = CPI(2025) / CPI(fire season year). A fiscal year Y to Y+1 is treated as fire season Y, as in
economic-value/07_cost_tally.py. additive_amount_cad is in 2025 dollars.

Run: python3 -I gov_build_costs.py   (writes ../gov_costs.csv and ../gov_manifest.csv)
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
BASE = os.path.dirname(os.path.dirname(OUT))            # .../wildfire
CPI = os.path.join(BASE, "analysis", "losses", "raw", "cpi", "boc_V41690973.json")
ACC = "2026-10-22"

obs = json.load(open(CPI))["observations"]
by = defaultdict(list)
for o in obs:
    by[int(o["d"][:4])].append(float(o["V41690973"]["v"]))
cpi = {y: sum(v) / len(v) for y, v in by.items()}
F = {y: cpi[2025] / cpi[y] for y in (2023, 2024, 2025, 2026)}

rows = []


def add(item, payer, jur, period, season, nominal, basis, src, url, overlaps, additive, add_nominal, notes):
    """add_nominal: the additive part in nominal dollars (None for 0)."""
    f = F[season]
    rows.append(dict(
        item=item, payer=payer, jurisdiction=jur, period=period,
        amount_nominal_cad=round(nominal, 2), amount_2025_cad=round(nominal * f, 2), basis=basis,
        source_name=src, url=url, accessed=ACC, overlaps_with=overlaps, additive=additive,
        additive_amount_cad=round((add_nominal or 0.0) * f, 2), notes=notes))


MUTUAL = ("Mutual aid: any crews this agency hired from BC, AB or SK are also inside those provinces' gross "
          "lines in the bill (amount not published; small)")

# ---------------------------------------------------------------- QUEBEC (SOPFEU, includes SAG airtankers)
SOP = {2023: ("https://a-ca.storyblok.com/f/2000396/x/9c87a40c30/rapport_annuel-2023-lr.pdf", 250878155, 2359376, 0,
              "AB 1,545,217; NT 814,159", 20751686),
       2024: ("https://a-ca.storyblok.com/f/2000396/x/b3c411594f/rapport_annuel-2024-lr.pdf", 155617236, 3644024, 0,
              "AB 1,570,471; BC 1,214,245; MB 277,407; Connecticut 382,955; ON 133,499; NL 43,781; NT 21,666", 1552553),
       2025: ("https://a-ca.storyblok.com/f/2000396/x/c22b63b6cb/8-5x11-rapport_annuel_2025-vf.pdf", 159658370, 14472397,
              11387356, "MB 5,190,958; SK 3,524,101; ON 1,992,310; NL 1,293,068; NS 1,012,583; AB 961,536; NB 247,815; "
              "BC 224,301; YT 15,520; CIFFC 10,205", 1340655)}
for y, (url, tot, exp, avion, who, isc) in SOP.items():
    net = tot - exp - avion
    extra = f"; less CL-415 avionics modernization {avion:,} (capital-type upgrade funded by a grant)" if avion else ""
    add("Quebec forest firefighting (SOPFEU total expenses, net of out-of-province billings)", "provincial",
        "QC", f"{y} season (calendar year)", y, net, "actual (audited financial statements)",
        f"SOPFEU Rapport annuel {y}, etat des resultats and annexe B", url,
        "None with bill lines. SAG airtanker operating and financing costs are inside these expenses "
        "(SOPFEU assumes airtanker operation surpluses or deficits). Contains suppression billed to Indigenous "
        f"Services Canada ({isc:,} in {y}), which is removed from the ISC line",
        "yes", net,
        f"Total expenses {tot:,} less billings to agencies outside Quebec {exp:,} ({who}){extra}. "
        "Removing out-of-province billings avoids counting crews Quebec sent to other provinces twice")

# ---------------------------------------------------------------- MANITOBA
NRIF24 = "https://www.gov.mb.ca/asset_library/en/annualreports/2024_2025/annual-report-nrif-24-25.pdf"
NRIF25 = "https://www.gov.mb.ca/asset_library/en/annualreports/2025_2026/annual-report-nrif-25-26.pdf"
PA26 = "https://www.gov.mb.ca/asset_library/en/finances/annual-report-and-public-accounts-2025-26.pdf"
add("Manitoba wildfire spending: Manitoba Wildfire Service + Wildfire Suppression appropriations", "provincial", "MB",
    "FY2023-24 (2023 season)", 2023, 53509000, "actual (departmental annual report)",
    "Natural Resources and Indigenous Futures Annual Report 2024-25 (prior-year actuals 25.4c and 25.4d)", NRIF24,
    MUTUAL, "yes", 53509000,
    "MWS 37,441k (12,087 salaries + 25,354 other) + Wildfire Suppression 16,068k. Emergency Expenditures that year "
    "were 29M for all hazards; the wildfire share is not published, so it is left out (floor)")
add("Manitoba wildfire spending: MWS + Wildfire Suppression + suppression paid from Emergency Expenditures",
    "provincial", "MB", "FY2024-25 (2024 season)", 2024, 79737000, "actual (departmental annual reports)",
    "NRIF Annual Report 2024-25 (MWS 38,871k, Suppression 16,166k) and 2025-26 footnote (24.7M recovered through "
    "Emergency Expenditures, Appropriation 27.1)", NRIF24 + " ; " + NRIF25,
    MUTUAL + ". MB sent crews to SK and NT in 2024 and recovered the cost (revenue, not netted; not separable)",
    "yes", 79737000, "55,037k + 24,700k")
add("Manitoba total wildfire suppression and Wildfire Service cost, 2025 season", "provincial", "MB",
    "FY2025-26 (2025 season)", 2025, 229000000, "actual (Public Accounts)",
    "Province of Manitoba Annual Report and Public Accounts 2025-26, 'Summary of Manitoba's Response to "
    "Unprecedented Wildfires in 2025'", PA26,
    MUTUAL + ". Evacuee costs (80M) and DFA program (12M) in the same table are NOT included here (evacuation and "
    "property lines)", "yes", 229000000,
    "Emergency expenditures wildfire suppression 175M + Manitoba Wildfire Service 40M + NRIF wildfire suppression 14M. "
    "Resolves the 229M vs 179M+129M question: 179M and 129M were mid-year Q1 figures; 229M is the audited year-end "
    "result (department view in NRIF report: 39.69 + 14.31 + 166.7 = 220.7M)")

# ---------------------------------------------------------------- NORTHWEST TERRITORIES
ME2526 = ("https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2025-02/"
          "TD%20275-20%281%29%202025-2026%20Main%20Estimates.pdf")
ME2627 = ("https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2026-02/"
          "TD%20448-20%281%29%202026-2027%20Main%20Estimates.pdf")
SUPP3 = ("https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2026-02/"
         "TD%20454-20%281%29%20Supplementary%20Estimates%20%28Operations%20Expenditures%29%20No%203%202025-2026.pdf")
HN = "https://www.ntlegislativeassembly.ca/sites/default/files/hansard/2025-11/HN251021_0.pdf"
add("NWT wildfire program: ECC Forest Management (fire presuppression, suppression, forest resources)", "territorial",
    "NT", "FY2023-24 (2023 season)", 2023, 150224000, "actual (Main Estimates actuals column)",
    "GNWT 2025-2026 Main Estimates (TD 275-20(1)), Wildlife and Forest Management program detail, 2023-2024 Actuals",
    ME2526, MUTUAL + ". DFAA order 263 (188.6M) reimburses part of this (DFAA is not additive)", "yes", 150224000,
    "Official Hansard PDF (Oct 21, 2025, pp. 2796-97, Finance Minister): suppression actuals 'just shy of $25 million' "
    "(2022-23), '$127 million' (2023-24), '$61 million' (2024-25). The program line adds the presuppression base and a "
    "small forest-resources section. Replaces the hansard.opennwt.ca transcription used before")
add("NWT wildfire program: ECC Forest Management", "territorial", "NT", "FY2024-25 (2024 season)", 2024, 89641000,
    "forecast (revised estimate, Feb 2025)", "GNWT 2025-2026 Main Estimates, 2024-2025 Revised Estimates", ME2526,
    MUTUAL, "yes", 89641000,
    "Suppression actual 61M per Hansard. Public Accounts 2024-25 Section II: Wildlife and Forest Management activity "
    "actual 107,048k (includes Wildlife ~16.4M and Compliance 0.75M), consistent with the revised figure")
add("NWT wildfire program: ECC Forest Management", "territorial", "NT", "FY2025-26 (2025 season)", 2025, 112085000,
    "forecast (appropriation; Public Accounts 2025-26 not yet tabled)",
    "GNWT 2026-2027 Main Estimates (2025-26 Revised 94,064k) + Supplementary Estimates (Operations) No. 3 2025-26 "
    "('shortfall in fire suppression' 18,021k)", ME2627 + " ; " + SUPP3, MUTUAL, "yes", 112085000,
    "Revised 94,064k already includes Supp. No. 2 fire suppression shortfall 39,509k (TD 388-20(1)); Supp. No. 3 was "
    "tabled with the Main Estimates and is not in the revised column")

# ---------------------------------------------------------------- YUKON
YT2526 = ("https://open.yukon.ca/information/2c63636e-348f-4529-8fe6-2c267e48e5b2/resource/"
          "55d25146-fef3-48fb-8266-3185baee5d67/download/fin-2025-26-budget-main-estimates-community-services.pdf")
YT2627 = "https://yukon.ca/sites/default/files/fin-2026-27-budget-main-estimates-community-services.pdf"
for y, per, amt, basis, src, url in [
        (2023, "FY2023-24 (2023 season)", 38308000, "actual (Main Estimates actuals column)",
         "Yukon 2025-26 Main Estimates, Community Services, Protective Services: Fire Management O&M, 2023-24 Actual", YT2526),
        (2024, "FY2024-25 (2024 season)", 47449000, "actual (Main Estimates actuals column)",
         "Yukon 2026-27 Main Estimates, Community Services, Fire Management O&M, 2024-25 Actual", YT2627),
        (2025, "FY2025-26 (2025 season)", 63927000, "forecast (Main Estimates forecast column)",
         "Yukon 2026-27 Main Estimates, Community Services, Fire Management O&M, 2025-26 Forecast", YT2627)]:
    add("Yukon Wildland Fire Management (Fire Management O&M)", "territorial", "YT", per, y, amt, basis, src, url,
        MUTUAL + " (2025: 8 initial-attack crews and 1 airtanker from BC)", "yes", amt,
        "Operating only; Fire Management capital excluded. 2025-26: estimate 30,812k plus 33.7M wildfire response in "
        "Supplementary Estimates No. 1" if y == 2025 else "Operating only; Fire Management capital excluded")

# ---------------------------------------------------------------- NOVA SCOTIA
NS = {2023: ("https://www.novascotia.ca/sites/default/files/documents/7-805/estimates-and-supplementary-detail-budget-2024-2025-en.pdf", 22516000, 7849000, "2024-25 Estimates"),
      2024: ("https://www.novascotia.ca/sites/default/files/documents/7-3890/budget-estimates-2025-26-en.pdf", 9318000, 8901000, "2025-26 Estimates"),
      2025: ("https://www.novascotia.ca/sites/default/files/documents/7-4172/budget-estimates-2026-27-en.pdf", 40881000, 11667000, "2026-27 Estimates")}
for y, (url, fc, est, book) in NS.items():
    add("Nova Scotia DNR Fleet and Forest Protection (wildfire prevention, detection, suppression, air services)",
        "provincial", "NS", f"FY{y}-{str(y+1)[2:]} ({y} season)", y, fc,
        "forecast (prior-year forecast printed in next Estimates; program actuals not published)",
        f"Nova Scotia {book}, Natural Resources, Regional Services: Fleet and Forest Protection (forecast column)", url,
        MUTUAL + ". DFAA order 257 (26.6M, 2023) reimburses part of NS 2023 costs (not additive)", "yes", fc,
        f"Estimate that year {est:,}. Line also carries the provincial air fleet; regional wildfire staff in the Central, "
        "Eastern and Western lines are not included (not separable)")

# ---------------------------------------------------------------- NEWFOUNDLAND AND LABRADOR
NL = {2023: ("https://www.gov.nl.ca/budget/2024/wp-content/uploads/sites/8/2024/03/Estimates-2024.pdf", 3767100, "Estimates 2024"),
      2024: ("https://www.gov.nl.ca/budget/2025/wp-content/uploads/sites/9/2025/04/Estimates-2025.pdf", 11889500, "Estimates 2025"),
      2025: ("https://www.gov.nl.ca/budget/2026/wp-content/uploads/sites/10/Estimates-2026.pdf", 32500200, "Estimates 2026")}
for y, (url, gross, book) in NL.items():
    add("Newfoundland and Labrador Fire Suppression and Communications (gross amount voted)", "provincial", "NL",
        f"FY{y}-{str(y+1)[2:]} ({y} season)", y, gross, "forecast (revised estimate printed in next Estimates)",
        f"Government of NL {book}, Forestry, Agriculture and Lands, Forest Protection: Fire Suppression and "
        "Communications, Revised column", url, MUTUAL, "yes", gross,
        "Gross before federal revenue (2023-24 2.875M, 2024-25 1.819M, 2025-26 5.501M federal cost-share). Water bomber "
        "fleet operations sit in Transportation and Infrastructure 'Government-Operated Aircraft' together with air "
        "ambulance and are not separable, so they are excluded")

# ---------------------------------------------------------------- BC lines missing from the bill
BCASR = {2023: "https://www.bcbudget.gov.bc.ca/Annual_Reports/2023_2024/pdf/ministry/for.pdf",
         2024: "https://www.bcbudget.gov.bc.ca/Annual_Reports/2024_2025/pdf/ministry/for.pdf",
         2025: "https://www.bcbudget.gov.bc.ca/Annual_Reports/2025_2026/pdf/ministry/for.pdf"}
for y, amt in [(2023, 40887000), (2024, 42234000), (2025, 57891000)]:
    add("BC Ministry of Forests 'Fire Preparedness' core business (separate from the Fire Management vote in the bill)",
        "provincial", "BC", f"FY{y}-{str(y+1)[2:]} ({y} season)", y, amt, "actual (Annual Service Plan Report)",
        f"BC Ministry of Forests {y}/{str(y+1)[2:]} Annual Service Plan Report, Financial Summary, operating expenses",
        BCASR[y], "None: the bill's BC line equals the Fire Management vote only (1,094.88M in 2023-24 and 769.4M in "
                  "2024-25 match the bill exactly)", "yes", amt,
        "Sub-vote covers fire prevention, fire operations, strategic initiatives, corporate wildfire services and wildfire "
        "risk (2026/27 Estimates vote description). Base program cost, like Alberta 2.1 already in the bill")
add("BC Fire Management vote, 2025-26 official actual minus the early estimate used in the bill", "provincial", "BC",
    "FY2025-26 (2025 season)", 2025, 135112000, "actual (Annual Service Plan Report) minus estimate",
    "BC Ministry of Forests 2025/26 Annual Service Plan Report: Fire Management actual 645,112k; bill uses 510.0M "
    "(BCWS estimate to 2025-11-01)", BCASR[2025],
    "Upward correction of the bill's own BC 2025 line (same definition as 2023 and 2024)", "yes", 135112000,
    "645,112k - 510,000k")

# ---------------------------------------------------------------- ONTARIO base line missing from the bill
ONPA = "https://data.ontario.ca/dataset/public-accounts-ministry-statements-and-schedules"
for y, amt in [(2023, 33203000), (2024, 33818000), (2025, 34453000)]:
    add("Ontario MNR Public Protection: 'Public safety and emergency response' (base fire program, net of recoveries)",
        "provincial", "ON", f"FY{y}-{str(y+1)[2:]} ({y} season)", y, amt, "actual (Public Accounts of Ontario)",
        "Public Accounts of Ontario, ministry statements (as compiled in data/smoke-cost/wildfire_spending_by_jurisdiction.csv)",
        ONPA, "None with the bill (bill counts only Emergency Fire Fighting)", "yes", amt,
        "Vote 2104 also covers aviation services and other provincially significant emergencies; net of recoveries "
        "(39.1M recoveries budgeted 2026-27). Treat as mostly wildfire base program; non-fire share not published")

# ---------------------------------------------------------------- 2026 season, provinces and territories
add("BC Fire Management, 2026-27 forecast", "provincial", "BC", "FY2026-27 (2026 season)", 2026, 850000000,
    "forecast (First Quarterly Report, Sept 2026)",
    "BC First Quarterly Report 2026/27: '$614 million for fire management costs ... in addition to the $236 million ... "
    "for a total spending forecast of $850 million'",
    "https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/quarterly-reports/2026-27_first_quarterly_report.pdf",
    "None (bill counts 2023-2025 only)", "yes", 850000000, "Season not finished at Q1")
add("BC Fire Preparedness, 2026-27 budget", "provincial", "BC", "FY2026-27 (2026 season)", 2026, 47291000,
    "budget (Estimates 2026/27)", "BC 2026/27 Estimates, Ministry of Forests, Fire Preparedness sub-vote",
    "https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Estimates.pdf", "None", "yes", 47291000, "")
add("Alberta wildfire spending, 2026-27 forecast at Q1", "provincial", "AB", "FY2026-27 (2026 season)", 2026, 273944000,
    "forecast (First Quarter Fiscal Update, Aug 2026; costs committed and incurred to July 2026)",
    "Alberta 2026-27 Estimates (2.1 Wildfire Management 169,244k) + 2026-27 First Quarter Fiscal Update ('$104.7 million "
    "for wildfire presuppression and response')",
    "https://open.alberta.ca/dataset/9c81a5a7-cdf1-49ad-a923-d1ecb42944e4/resource/eaeb7a75-0c9f-4964-be53-0f1cc889ffab/download/tbf-2026-27-first-quarter-fiscal-update-economic-statement.pdf",
    "None (bill counts 2023-2025 only)", "yes", 273944000,
    "Floor: the 104.7M covers costs only to July 2026 and includes some replanting of areas burned in 2025")
add("Ontario Emergency Forest Firefighting, 2026-27 forecast at Q1", "provincial", "ON", "FY2026-27 (2026 season)",
    2026, 150000000, "forecast (2026-27 First Quarter Finances, Aug 14 2026; unchanged from budget)",
    "Ontario Finances 2026-27 First Quarter, program expense table: 'Natural Resources - Emergency Forest Firefighting 150.0'",
    "https://www.ontario.ca/page/2026-27-first-quarter-finances", "None (bill counts 2023-2025 only)", "yes", 150000000,
    "Q1 forecast equals the year-start budget; final will be known in Public Accounts 2026-27")
for jur, item, amt, src, url, note in [
        ("MB", "Manitoba Wildfire Service + Wildfire Suppression, 2026-27 budget", 56648000,
         "Manitoba Estimates 2026-27, 25.4(c) 42,716k + 25.4(d) 13,932k",
         "https://www.gov.mb.ca/asset_library/en/budget2026/estimates_budget2026.pdf",
         "Q1 2026-27 report: Emergency Expenditures 277M over budget, mostly floods, 'and the 2026 wildfire response' "
         "(wildfire share not given; not added)"),
        ("NT", "NWT ECC Forest Management, 2026-27 budget", 65622000, "GNWT 2026-2027 Main Estimates, Forest Management",
         ME2627, "No 2026-27 fire supplementary tabled by Oct 21 2026; Finance Minister's Oct 21 2026 update cites "
                 "'increasing costs of wildfire emergencies' without a figure"),
        ("NS", "Nova Scotia Fleet and Forest Protection, 2026-27 budget", 21146000,
         "Nova Scotia 2026-27 Estimates, Fleet and Forest Protection",
         "https://www.novascotia.ca/sites/default/files/documents/7-4172/budget-estimates-2026-27-en.pdf", ""),
        ("NL", "NL Fire Suppression and Communications, 2026-27 budget (gross)", 11820800,
         "Government of NL Estimates 2026, 2.2.02, 2026-27 Estimates", NL[2025][0], "")]:
    add(item, "territorial" if jur == "NT" else "provincial", jur, "FY2026-27 (2026 season)", 2026, amt,
        "budget (no in-year update found)", src, url, MUTUAL, "yes", amt, "Floor for 2026. " + note)

# ---------------------------------------------------------------- FEDERAL
add("Parks Canada wildfire response, 2023 season", "federal", "Parks Canada", "FY2023-24 (2023 season)", 2023, 37900000,
    "allocation (additional funding received for costs incurred)",
    "Parks Canada 2024-25 Departmental Results Report: 'incurred additional costs when responding to an unprecedented "
    "number of wildfires ... and received $37.9 million in additional funding'; Budget 2024 Annex: 'Emergency Wildfires "
    "Response PCA 38' (2023-24)",
    "https://parks.canada.ca/agence-agency/bib-lib/rapports-reports/rmr-dpr/2024-2025",
    "Possible small overlap: Parks paid provinces for mutual-aid crews (in their gross lines) and was paid by provinces "
    "for the 303 Parks staff it redeployed", "yes", 37900000, "")
add("Parks Canada incident response and emergency operations, 2024-25 (Jasper; includes other 2024-25 fires)", "federal",
    "Parks Canada", "FY2024-25 (2024 season)", 2024, 59800000, "actual (spent in 2024-25, draft JRCC report)",
    "Jasper Recovery Coordination Centre (Parks Canada and Municipality of Jasper) Year Two Progress Report, DRAFT, "
    "Municipality of Jasper Committee of the Whole agenda, 2026-07-14: 'Incident response and emergency operations $59.8 "
    "million' (spent in 2024-2025), within 'Parks Canada spent $132.6 million'", "https://jasper-alberta.ca/Home/DownloadMeeting/8bcfc306-cd8c-4a73-91ac-cbf93fdea818?isEnglish=True",
    "Possible small overlap: mutual-aid crews from AB, BC and others billed to Parks are also in those provinces' gross "
    "lines (not separable). Re-entry and initial recovery (72.8M, incl. interim housing 29.1M and hazard management "
    "20.2M) excluded", "yes", 59800000,
    "Cross-check: Parks backgrounder 2025-02-06 allocated up to 45.2M Jasper incident response + 7.7M other fire pressures "
    "+ 80.1M recovery and re-entry = 133.1M; the 132.6M spent matches that envelope, so the 59.8M is taken as all "
    "2024-25 Parks response (allocations alone would give 52.9M)")
add("Alberta Disaster Recovery Program: Jasper incident response (municipal emergency operations, structural protection, "
    "mutual aid, transitional housing)", "provincial", "AB", "2024 season (spent to June 2026)", 2024, 25500000,
    "actual (spent to June 2026, draft JRCC report)",
    "JRCC Year Two Progress Report, DRAFT (Committee of the Whole agenda 2026-07-14), Government of Alberta Disaster "
    "Recovery Program table: 'Incident response $25.5 million'", "https://jasper-alberta.ca/Home/DownloadMeeting/8bcfc306-cd8c-4a73-91ac-cbf93fdea818?isEnglish=True",
    "Not in the bill's Alberta line (Forestry and Parks only). Overlaps: evacuation line for the transitional housing part "
    "(not split); Municipality of Jasper audited costs (35.5M 2024, 4.0M 2025, 'emergency response and site remediation') "
    "are the same spending, 90% reimbursed by this program, so count one or the other; DFAA reimburses part (not additive)",
    "yes", 25500000,
    "Province pays 90%, municipality 10%. Recovery (4.6M) and debris, remediation and infrastructure (5.8M) from the same "
    "table are left to the property and infrastructure lines. Other provinces' payments for municipal response costs "
    "were not found")
add("Department of National Defence Operation LENTUS, actual incremental cost", "federal", "DND/CAF",
    "FY2023-24 (2023 season)", 2023, 8855600, "actual (incremental cost; excludes Regular Force salaries)",
    "DND 2023-24 Departmental Results Report, supplementary table 'Costs of major CAF operations': Op LENTUS planned "
    "2,660.0k, actual 8,855.6k",
    "https://www.canada.ca/en/department-national-defence/corporate/reports-publications/departmental-results-report/2023-24-index/supp-information/costs-major-caf-ops.html",
    "None (federal; not cost-recovered from provinces in any record found)", "yes", 8855600,
    "LENTUS covers 'forest fires, floods and natural disasters'; DND's November 2024 briefing binder describes about "
    "1,760 members deployed in the 2023 wildfire season. Whether part of the 2023-24 cost was for non-fire events is not "
    "stated, so treat as an upper bound for wildfire")
PSURL = "https://open.canada.ca/data/dataset/432527ab-7aac-45b5-81d6-7597107a7013"
PSOV = ("Evacuation and property lines (other agents) if they count Red Cross, St. John Ambulance, SARVAC, Salvation "
        "Army or United Way relief funded by these agreements; count once")
add("Public Safety Canada wildfire agreements: Red Cross matching (AB 2023, NS 2023) and United Way NWT 2023 match",
    "federal", "Public Safety Canada", "2023 season", 2023, 12861659.19, "agreement values (commitments)",
    "Proactive Disclosure of Grants and Contributions (grants.csv, modified 2026-10-21): agreements 23323 (7,494,198.79 "
    "after amendment), 24219 (5,005,180.40), 23477 original (362,280)", PSURL, PSOV, "yes", 12861659.19,
    "Matching appeals fund evacuation-period relief and early recovery (mixed). Programs: 'Supporting the Canadian Red Cross's Urgent Relief Efforts Related to COVID-19, Floods and Wildfires' and "
    "Humanitarian Workforce. Public Accounts actuals by program, all events: Red Cross 8.46M (2023-24), 26.62M (2024-25); "
    "HWF 27.81M, 31.67M")
add("Public Safety Canada wildfire agreements: Humanitarian Workforce deployments (NL July 2024, Jasper Team Rubicon) "
    "and United Way NWT 2024", "federal", "Public Safety Canada", "2024 season", 2024, 4823467.78,
    "agreement values (commitments)",
    "Proactive Disclosure of Grants and Contributions: 24287 (634,747.46), 24286 (688,541.28), 24285 (643,403.04), "
    "24283 (257,600), 24292 (413,796), 23477 amendment increment (2,185,380)", PSURL, PSOV, "yes", 4823467.78,
    "Requests for Federal Assistance from NL (Labrador City and Happy Valley-Goose Bay evacuations) and Alberta (Jasper)")
add("Public Safety Canada: Red Cross early and long-term recovery support, 2024 Alberta wildfires (reference)", "federal",
    "Public Safety Canada", "2024 season", 2024, 12622466.32, "agreement value (commitment)",
    "Proactive Disclosure of Grants and Contributions: 24300 (12,622,466.32), 2024-11-19 to 2026-03-31", PSURL,
    "Property and recovery lines (household recovery support)", "no", None,
    "Recovery, not response (same rule as Parks Canada and ISC recovery); focus on Jasper")
add("Public Safety Canada wildfire agreements: Humanitarian Workforce deployments (Manitoba and NL 2025)", "federal",
    "Public Safety Canada", "2025 season", 2025, 3032836.80, "agreement values (commitments)",
    "Proactive Disclosure of Grants and Contributions: 26173 (1,487,712.80 after amendment), 26175 (601,500.48), 26219 "
    "(917,589.12), 26222 (26,034.40)", PSURL, PSOV, "yes", 3032836.80,
    "St. John Ambulance, SARVAC and Team Rubicon deployed on Requests for Federal Assistance")
add("Public Safety Canada: Red Cross early and long-term recovery support, 2025 Saskatchewan and NL wildfires (reference)",
    "federal", "Public Safety Canada", "2025 season", 2025, 5472268.81, "agreement values (commitments)",
    "Proactive Disclosure of Grants and Contributions: 26234 (2,818,066.48), 26235 (2,654,202.33), 2026-03-30 to 2027-03-31",
    PSURL, "Property and recovery lines (household recovery support)", "no", None, "Recovery, not response")
add("Crown-Indigenous Relations: support to Indigenous governments affected by the 2023 NWT wildfires", "federal",
    "CIRNAC", "FY2023-24 (2023 season)", 2023, 9000000, "allocation (Budget 2024)",
    "Budget 2024: '$9 million in 2023-24 to Crown-Indigenous Relations and Northern Affairs Canada to support Indigenous "
    "governments directly affected by the 2023 wildfires in the Northwest Territories'",
    "https://budget.canada.ca/2024/report-rapport/budget-2024.pdf",
    "Evacuation line if it counts NWT Indigenous governments' evacuation costs", "yes", 9000000, "Use of funds not itemized")

# ISC: official amounts; additive part is an estimate (wildfire share and response share not published)
EMAP = "https://www.sac-isc.gc.ca/eng/1685047435261"
ISCOV = ("Provincial firefighting lines (ISC pays BC, AB, SK, MB and ON wildfire agencies for on-reserve suppression; "
         "only Quebec's share is quantified and removed); evacuation line (other agent) if it counts ISC-funded "
         "First Nations evacuations or provincial evacuee costs recovered from ISC; homes line for recovery")
add("Indigenous Services Canada: 2023-24 wildfire response and recovery top-up (Fall Economic Statement 2023), reference",
    "federal", "ISC (EMAP)", "FY2023-24 (2023 season)", 2023, 260000000, "allocation (official, wildfire-specific)",
    "FES 2023 Annex: 'Support for Emergency Management Response and Recovery Activities on Reserve' ISC 260 (2023-24); "
    "Budget 2024: 'To support wildfire responses and recovery activities in First Nations communities, the 2023 Fall "
    "Economic Statement provided $260 million'",
    "https://budget.canada.ca/fes-eea/2023/report-rapport/FES-EEA-2023-en.pdf ; https://budget.canada.ca/2024/report-rapport/budget-2024.pdf",
    "Funds part of the EMAP 2023-24 reimbursements in the next row", "no", None,
    "Cross-check only: top-up on EMAP base funding (128M a year for response and recovery since 2022-23), so it is a "
    "lower bound for 2023-24 wildfire response plus recovery, not a total")
for y, per, resp, wf, fl, sop in [(2023, "FY2023-24 (2023 season)", 369501840, 90, 11, 20751686),
                                  (2024, "FY2024-25 (2024 season)", 294372464, 26, 5, 1552553),
                                  (2025, "FY2025-26 (2025 season)", 688648240, 73, 8, 1340655)]:
    sh = wf / (wf + fl)
    add("Indigenous Services Canada EMAP response costs reimbursed, all hazards", "federal", "ISC (EMAP)", per, y, resp,
        "actual (all hazards); additive part is an estimate",
        "ISC 'Emergency Management Assistance Program - key statistics' (modified 2026-06-30): response reimbursed; ISC "
        "wildland fire and flood evacuation statistics (modified 2026-06-01) for the wildfire share", EMAP, ISCOV,
        "partial", resp * sh - sop,
        f"ESTIMATE for the additive part: wildfire share of First Nations evacuation events that fiscal year "
        f"({wf} wildfire of {wf+fl} wildfire+flood = {sh:.3f}) x response, less SOPFEU suppression billed to ISC "
        f"({sop:,}, inside the Quebec line). ISC does not publish EMAP costs by hazard. Recovery reimbursed "
        f"({ {2023: '139.7M', 2024: '296.9M', 2025: '166.7M'}[y] }) excluded")

# ---------------------------------------------------------------- REFERENCE ROWS (not additive)
DF = "https://open.canada.ca/data/dataset/432527ab-7aac-45b5-81d6-7597107a7013"
for y, amt, who in [(2023, 793290412, "BC 358.9M, NT 188.6M, AB 149.6M, QC 36.3M, SK 33.0M, NS 26.6M, YT 0.2M"),
                    (2024, 183941983, "AB 106.4M, BC 71.4M, NT 6.1M"),
                    (2025, 12503476, "SK 8.5M, YT 4.0M (incomplete; no MB order yet)")]:
    add("Federal DFAA orders for 'interface fires' (Provincial Emergency Financial Assistance Orders)", "federal",
        "Public Safety Canada (DFAA)", f"{y} events", y, amt, "order (interim federal share at agreement date)",
        "Proactive Disclosure of Grants and Contributions, DFAA rows (analysis/losses/dfaa_wildfire_payments.csv)", DF,
        "Provincial firefighting lines (interface-fire firefighting is DFAA-eligible) and evacuation, infrastructure and "
        "property lines (other eligible categories)", "no", None,
        f"{who}. DFAA is a federal reimbursement of provincial/territorial costs, not an extra cost; see gov_notes.md")
for y, per, amt in [(2023, "FY2023-24 (2023 season)", 139688498), (2024, "FY2024-25 (2024 season)", 296917355),
                    (2025, "FY2025-26 (2025 season)", 166653736)]:
    add("ISC EMAP recovery costs reimbursed, all hazards (reference)", "federal", "ISC (EMAP)", per, y, amt,
        "actual (all hazards)", "ISC EMAP key statistics (modified 2026-06-30)", EMAP,
        "Homes, property and infrastructure lines (rebuilding on reserve)", "no", None,
        "Recovery is rebuilding, outside this response scope; hazard split not published")
add("Parks Canada Jasper re-entry and initial recovery operations (reference)", "federal", "Parks Canada",
    "FY2024-25 (2024 season)", 2024, 72800000, "actual (spent in 2024-25, draft JRCC report)",
    "JRCC Year Two Progress Report, DRAFT: 'Re-entry and initial recovery operations $72.8 million', incl. interim housing "
    "29.1M and hazard management 20.2M",
    "https://jasper-alberta.ca/Home/DownloadMeeting/8bcfc306-cd8c-4a73-91ac-cbf93fdea818?isEnglish=True",
    "Property, infrastructure and evacuation lines (interim housing, danger trees, repairs); econ_ counts the 20.2M hazard "
    "management", "no", None,
    "Rebuilding and displacement, not response. Allocation was up to 80.1M (backgrounder 2025-02-06). Budget 2025 Annex 1 "
    "'Jasper Wildfire Response and Rebuilding': 133M (2024-25), 43M (2025-26), 27M (2026-27), 3M a year to 2029-30")
for y, amt in [(2023, 521000), (2024, 1900000), (2025, 26300000)]:
    add("Saskatchewan cost of resources obtained from mutual-aid partners (reference)", "provincial", "SK",
        f"{y} season", y, amt, "actual (management figure reported by Provincial Auditor)",
        "Provincial Auditor of Saskatchewan 2026 Report Vol. 1 Ch. 5: 'about $26.3 million ... in 2025 (2024: $1.9 "
        "million; 2023: $521,000)'",
        "https://auditor.sk.ca/pub/publications/public_reports/2026/Volume%201/ch-05----saskatchewan-public-safety-agencyresource-planning-for-wildfire-response.pdf",
        "Inside SK firefighting in the bill", "no", None,
        "Imported crews are paid by the receiving agency (BC, QC, PE, Australia, Washington, Arizona, Mexico in 2025)")
for y, per, amt, det in [(2024, "FY2024-25 (2024 season)", 8353543, "air charter 4,784,841; wildfire support 3,568,702"),
                         (2025, "FY2025-26 (2025 season)", 13227375, "air charter 5,149,945; wildfire support 8,077,430")]:
    add("CIFFC pass-through 'activities for other organizations' (reference)", "provincial", "CIFFC", per, y, amt,
        "actual (audited statements, note 13)", f"CIFFC Financial Statements March 31, 2026, note 13: {det}",
        "https://ciffc.ca/publications/", "Paid by member agencies, inside provincial lines", "no", None,
        "CIFFC acts as agent; international crew costs are billed to the receiving agency. No federal payment for "
        "imported firefighters found")
add("Pan-Canadian Aerial Asset Program aircraft leases, 2026-27 (reference)", "federal", "NRCan via CIFFC",
    "FY2026-27 (2026 season)", 2026, 64000000, "allocation (Budget 2025: 257.6M over 4 years from 2026-27)",
    "Budget 2025 chapter 4 table 'Strengthening Canada's Emergency Management' 64 (2026-27)",
    "https://budget.canada.ca/2025/report-rapport/pdf/budget-2025.pdf",
    "None, but it is standing capacity like the NRCan programs the bill leaves out", "no", None,
    "Capacity, not incident response; listed so it can be added if the bill takes capacity costs")
add("Manitoba Emergency Expenditures 2023-24, all hazards (reference)", "provincial", "MB", "FY2023-24 (2023 season)",
    2023, 29000000, "actual (all hazards)",
    "Manitoba Annual Report and Public Accounts 2023-24: Emergency Expenditures 29M (budget 100M)",
    "https://manitoba.ca/asset_library/en/proactive/20232024/publicaccounts/AnnualReportPublicAccounts2023-2024.pdf",
    "Unknown wildfire share", "no", None,
    "Upper bound for MB 2023 wildfire suppression paid from Emergency Expenditures; the PA says the 2023 flood season "
    "did not result in significant expenses, but no wildfire split is published")

# ---------------------------------------------------------------- write
cols = ["item", "payer", "jurisdiction", "period", "amount_nominal_cad", "amount_2025_cad", "basis", "source_name", "url",
        "accessed", "overlaps_with", "additive", "additive_amount_cad", "notes"]
with open(os.path.join(OUT, "gov_costs.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    for r_ in rows:
        w.writerow(r_)

# summary
def tier(r_):
    if r_["additive"] == "no":
        return "reference"
    if "ESTIMATE" in r_["notes"]:
        return "estimate"
    if r_["period"].startswith("FY2026") or r_["period"].startswith("2026"):
        return "2026"
    return "official"

tot = defaultdict(float)
for r_ in rows:
    tot[tier(r_)] += r_["additive_amount_cad"]
print({k: round(v / 1e6, 1) for k, v in tot.items()})
print("CPI factors", {k: round(v, 6) for k, v in F.items()})
print(len(rows), "rows")

# ---------------------------------------------------------------- manifest
R = "raw/gov/"
RR = "../readiness/raw/"
MAN = [
    # name, publisher, url, local file, coverage, used for
    ("SOPFEU Rapport annuel 2023, 2024, 2025 (audited financial statements)", "SOPFEU",
     "https://a-ca.storyblok.com/f/2000396/x/9c87a40c30/rapport_annuel-2023-lr.pdf ; https://a-ca.storyblok.com/f/2000396/x/b3c411594f/rapport_annuel-2024-lr.pdf ; https://a-ca.storyblok.com/f/2000396/x/c22b63b6cb/8-5x11-rapport_annuel_2025-vf.pdf",
     RR + "quebec/sopfeu_ra2023.pdf ; sopfeu_ra2024.pdf ; sopfeu_ra2025.pdf", "calendar 2023-2025",
     "QC total expenses, out-of-province billings (annexe B), ISC billings, SAG airtanker arrangement"),
    ("Manitoba Natural Resources and Indigenous Futures Annual Reports 2024-25 and 2025-26", "Government of Manitoba",
     NRIF24 + " ; " + NRIF25, RR + "mb/annual-report-nrif-24-25.pdf ; " + RR + "mb/annual-report-nrif-25-26.pdf",
     "FY2023-24 to FY2025-26", "MWS and Wildfire Suppression actuals; EE-funded suppression 24.7M and 166.7M"),
    ("Manitoba Annual Report and Public Accounts 2023-24 and 2025-26", "Government of Manitoba",
     "https://manitoba.ca/asset_library/en/proactive/20232024/publicaccounts/AnnualReportPublicAccounts2023-2024.pdf ; " + PA26,
     RR + "mb/AnnualReportPublicAccounts2023-2024.pdf ; " + RR + "mb/annual-report-and-public-accounts-2025-26.pdf",
     "FY2023-24, FY2025-26", "2025 wildfire response table (229M firefighting); EE 2023-24 29M"),
    ("Manitoba Estimates 2026-27 and 2026/27 First Quarter Report", "Government of Manitoba",
     "https://www.gov.mb.ca/asset_library/en/budget2026/estimates_budget2026.pdf ; https://www.gov.mb.ca/asset_library/en/proactive/20262027/first-quarter-report-september2026.pdf",
     RR + "mb/estimates_budget2026.pdf ; " + R + "mb/mb_q1_2026-27.pdf", "FY2026-27", "2026 budget; EE overrun note"),
    ("GNWT Main Estimates 2024-25, 2025-26, 2026-27", "Legislative Assembly of the NWT (tabled documents)",
     "https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2024-05/TD%2093-20%281%29%202024-2025%20Main%20Estimates.pdf ; " + ME2526 + " ; " + ME2627,
     R + "nt/me2425.pdf ; me2526.pdf ; me2627.pdf", "FY2022-23 to FY2026-27", "Forest Management actuals, revised, mains"),
    ("GNWT Supplementary Estimates (Operations) No. 2 and No. 3 2025-26; No. 3 2024-25", "Legislative Assembly of the NWT",
     "https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2025-10/TD%20388-20%281%29%20Supplementary%20Estimates%20%28Operations%20Expenditures%29%20No%202%202025-2026.pdf ; " + SUPP3,
     R + "nt/TD388_supp2_2025-26.pdf ; TD454_supp3_2025-26.pdf ; TD386_supp3_2024-25.pdf", "FY2024-25, FY2025-26",
     "fire suppression shortfall 39,509k and 18,021k"),
    ("NWT Hansard, October 21 2025 (official PDF), pp. 2796-2799", "Legislative Assembly of the NWT", HN,
     R + "nt/HN251021.pdf", "2022-23 to 2025-26", "suppression actuals 25M, 127M, 61M (replaces opennwt transcription)"),
    ("GNWT Public Accounts 2023-24 and 2024-25, Section II (Schedule 2)", "GNWT Department of Finance",
     "https://www.fin.gov.nt.ca/sites/fin/files/resources/2023-2024_section_ii_-_non-consolidated_financial_statements.pdf ; https://www.fin.gov.nt.ca/sites/fin/files/resources/2024-2025_public_accounts_section_ii_-_non-consolidated_financial_statements.pdf",
     R + "nt/2023-2024_section_ii_-_non-consolidated_financial_statements.pdf ; 2024-2025_public_accounts_section_ii_-_non-consolidated_financial_statements.pdf",
     "FY2023-24, FY2024-25", "Wildlife and Forest Management activity actuals (cross-check)"),
    ("NWT Hansard October 20-21 2026", "Legislative Assembly of the NWT",
     "https://www.ntlegislativeassembly.ca/sites/default/files/hansard/2026-10/99HN261021.pdf", R + "nt/99HN261021.pdf",
     "FY2026-27", "fiscal update: wildfire pressures named, no figure"),
    ("Yukon Main Estimates 2025-26 and 2026-27, Community Services", "Government of Yukon", YT2526 + " ; " + YT2627,
     RR + "yt/est2526.pdf (2026-27 book read with WebFetch; yukon.ca blocks downloads)", "FY2023-24 to FY2025-26",
     "Fire Management O&M actuals and forecast"),
    ("Nova Scotia Estimates 2024-25, 2025-26, 2026-27", "Government of Nova Scotia", " ; ".join(v[0] for v in NS.values()),
     RR + "ns/est2425.pdf ; est2526.pdf ; budget-estimates-2026-27-en.pdf", "FY2023-24 to FY2026-27",
     "Fleet and Forest Protection forecasts and estimates"),
    ("Nova Scotia Additional Appropriations Sept 2023 and Feb 2026", "NS Department of Finance and Treasury Board",
     "https://notices.novascotia.ca/files/budget-forecast-notices/additional-appropriations-budget-forecast-update-september-2023.pdf ; https://www.novascotia.ca/sites/default/files/documents/7-4172/additional-appropriations-budget-2026-27-en.pdf",
     "(Sept 2023 read with WebFetch) ; " + RR + "ns/additional-appropriations-budget-2026-27-en.pdf", "FY2023-24, FY2025-26",
     "context only (wildfire and flood 13.7M; 4.2M and 1.1M)"),
    ("Newfoundland and Labrador Estimates 2024, 2025, 2026", "Government of NL", " ; ".join(v[0] for v in NL.values()),
     R + "nl/Estimates-2024.pdf ; Estimates-2025.pdf ; Estimates-2026.pdf", "FY2023-24 to FY2026-27",
     "2.2.02 / 3.2.02 Fire Suppression and Communications; 4.2.01 Government-Operated Aircraft"),
    ("BC Ministry of Forests Annual Service Plan Reports 2023/24, 2024/25, 2025/26", "Government of BC",
     " ; ".join(BCASR.values()), RR + "bc/for_asr_2023_2024.pdf ; for_asr_2024_2025.pdf ; for_asr_2025_2026.pdf",
     "FY2023-24 to FY2025-26", "Fire Preparedness and Fire Management actuals"),
    ("BC 2026/27 Estimates; First Quarterly Report 2026/27", "Government of BC",
     "https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Estimates.pdf ; https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/quarterly-reports/2026-27_first_quarterly_report.pdf ; https://news.gov.bc.ca/releases/2026FIN0031-001066",
     R + "bc/bc_2026_Estimates.pdf ; bc_2026-27_q1.pdf ; bc_fin_release_2026FIN0031.html", "FY2026-27",
     "Fire Preparedness budget; Fire Management forecast 850M"),
    ("Alberta 2026-27 First Quarter Fiscal Update and Economic Statement; 2026-27 Estimates", "Government of Alberta",
     "https://open.alberta.ca/dataset/9c81a5a7-cdf1-49ad-a923-d1ecb42944e4/resource/eaeb7a75-0c9f-4964-be53-0f1cc889ffab/download/tbf-2026-27-first-quarter-fiscal-update-economic-statement.pdf ; https://open.alberta.ca/dataset/65514c30-e9f9-4951-9bae-7134edbe293c/resource/71713b5f-01ab-4ec5-9c01-7e49aec66fc1/download/budget-2026-estimates-government-2026-27.pdf",
     R + "ab/ab_2026-27_q1.pdf ; " + RR + "ab/est2627.pdf", "FY2026-27", "104.7M presuppression and response; 2.1 base 169,244k"),
    ("Ontario 2026-27 First Quarter Finances; MNR Expenditure Estimates 2026-27; Public Accounts", "Government of Ontario",
     "https://www.ontario.ca/page/2026-27-first-quarter-finances ; https://www.ontario.ca/page/expenditure-estimates-ministry-natural-resources-2026-2027 ; " + ONPA,
     R + "on/on_2026-27_q1.html ; on_mnr_est_2026-27.html ; ../../../data/smoke-cost/wildfire_spending_by_jurisdiction.csv",
     "FY2023-24 to FY2026-27", "Emergency Forest Firefighting forecast; Public safety and emergency response actuals"),
    ("Saskatchewan 2026-27 First Quarter Financial Report; Provincial Auditor 2026 Vol 1 Ch 5", "Government of SK; Provincial Auditor",
     "https://publications.saskatchewan.ca/api/v1/products/129712/formats/156618/download ; https://auditor.sk.ca/pub/publications/public_reports/2026/Volume%201/ch-05----saskatchewan-public-safety-agencyresource-planning-for-wildfire-response.pdf",
     R + "sk/sk_129712.pdf ; sk_auditor_2026v1ch5.pdf", "2023-2026", "no 2026 wildfire variance at Q1; imported resource costs"),
    ("New Brunswick DNRED Annual Reports 2023-24 and 2024-25; Supplementary Appropriations Acts", "Government of NB / Legislative Assembly",
     "https://www.legnb.ca/content/house_business/61/2/tabled_documents/2026-03-02%20DNRED%202024-2025%20(2).pdf ; https://legnb.ca/content/house_business/61/2/bills/Bill-22-e.htm",
     R + "nb/dnred_2024-25.pdf ; 61_2_bills_Bill-22-e.htm", "FY2023-24 to FY2025-26", "no wildfire split found (not used for numbers)"),
    ("Parks Canada 2024-25 Departmental Results Report", "Parks Canada Agency",
     "https://parks.canada.ca/agence-agency/bib-lib/rapports-reports/rmr-dpr/2024-2025", R + "parks/drr2425.html",
     "FY2023-24, FY2024-25", "37.9M 2023-24 wildfire funding; Jasper context"),
    ("Parks Canada backgrounder: funding for 2024 wildfire season incl. Jasper (2025-02-06)", "Parks Canada Agency",
     "https://www.canada.ca/en/parks-canada/news/2025/02/government-of-canada-funding-for-2024-wildfire-season-in-parks-canada-administered-places-including-jasper-national-park-wildfire-response-recovery.html",
     "(read with WebFetch; canada.ca refuses shell downloads)", "FY2024-25", "45.2M response, 80.1M recovery, 7.7M other fires"),
    ("Jasper Recovery Coordination Centre Year Two Progress Report (DRAFT), in Municipality of Jasper Committee of the Whole agenda 2026-07-14",
     "Parks Canada and Municipality of Jasper (JRCC)",
     "https://jasper-alberta.ca/Home/DownloadMeeting/8bcfc306-cd8c-4a73-91ac-cbf93fdea818?isEnglish=True",
     R + "parks/jrcc_cow_2026-07-14.pdf", "FY2024-25 to June 2026",
     "Parks Canada 2024-25 spending (59.8M response, 72.8M re-entry and recovery); Alberta DRP Jasper incident response 25.5M"),
    ("Federal Budget 2024, Budget 2025 and Fall Economic Statement 2023 annexes", "Department of Finance Canada",
     "https://budget.canada.ca/2024/report-rapport/budget-2024.pdf ; https://budget.canada.ca/2025/report-rapport/pdf/budget-2025.pdf ; https://budget.canada.ca/fes-eea/2023/report-rapport/FES-EEA-2023-en.pdf",
     "../economic-value/raw/federal_budget/b2024.pdf ; b2025.pdf ; fes2023.pdf (text in raw/gov/isc/)", "FY2023-24 to FY2029-30",
     "ISC 260M (2023-24); PCA 38M (2023-24); Jasper 133/43/27M; ISC 706/111M; CIRNAC 9M; PCAA 64M"),
    ("DND 2023-24 Departmental Results Report: costs of major CAF operations; 2025-26 Departmental Plan planned costs", "National Defence",
     "https://www.canada.ca/en/department-national-defence/corporate/reports-publications/departmental-results-report/2023-24-index/supp-information/costs-major-caf-ops.html ; https://www.canada.ca/en/department-national-defence/corporate/reports-publications/departmental-plans/departmental-plan-2025-26/planned-costs-major-caf-operations.html",
     "(read with WebFetch)", "FY2023-24 to FY2025-26", "LENTUS 8,855.6k actual 2023-24; 2024-25 planned 8,000k only"),
    ("ISC Emergency Management Assistance Program key statistics (modified 2026-06-30)", "Indigenous Services Canada", EMAP,
     R + "isc/emap_key_stats.html", "FY2016-17 to FY2025-26", "response and recovery reimbursed by year"),
    ("ISC wildland fire and flood evacuation statistics (modified 2026-06-01)", "Indigenous Services Canada",
     "https://isc.gc.ca/eng/1583177459681/1583177553276", "../losses/raw/isc/evac_stats.html", "FY2016-17 to FY2025-26",
     "wildfire vs flood evacuation events (allocation key for estimates)"),
    ("ISC Evaluation of EMAP and ICSF; 2024-25 Details on transfer payment programs", "Indigenous Services Canada",
     "https://sac-isc.gc.ca/eng/1781294116892/1781294141535 ; https://www.sac-isc.gc.ca/eng/1752155909653/1752155974370",
     R + "isc/emap_eval.html ; tpp_2024-25.html", "FY2017-18 to FY2024-25", "EMAP spending totals; no hazard split"),
    ("Proactive Disclosure of Grants and Contributions (grants.csv, modified 2026-10-21)", "Government of Canada",
     PSURL, "../losses/raw/grants/grants_dfaa_wildfire_subset.csv ; ../economic-value/raw/grants/grants_wildfire_all.csv",
     "2018 to 2026", "Public Safety Red Cross and HWF wildfire agreements; DFAA orders"),
    ("GC InfoBase transfer payments (Public Accounts data)", "Treasury Board Secretariat",
     "https://www.tbs-sct.canada.ca/ems-sgd/edb-bdd/index-eng.html", "../policy/raw/infobase/tp_pt_en.csv",
     "FY2011-12 to FY2024-25", "EMAP, Red Cross, HWF and DFAA program actuals (context)"),
    ("DFAA Guidelines before April 1 2025, Interpretation Bulletin 10, and Guidelines from April 1 2025", "Public Safety Canada",
     "https://www.publicsafety.gc.ca/cnt/mrgnc-mngmnt/rcvr-dsstrs/gdlns-dsstr-ssstnc/index-en.aspx ; https://www.publicsafety.gc.ca/cnt/mrgnc-mngmnt/rcvr-dsstrs/gdlns-dsstr-ssstnc/index-b10-en.aspx ; https://www.publicsafety.gc.ca/cnt/mrgnc-mngmnt/rcvr-dsstrs/dsstr-fnncl-ssstnc-rrngmnts/2025/dfaa-gdlns-en.aspx",
     R + "dfaa/gdlns_pre2025.html ; bulletin10.html ; gdlns_2025.html", "events 2023-2026", "eligibility of firefighting, evacuation, infrastructure"),
    ("CIFFC Financial Statements March 31 2026", "CIFFC", "https://ciffc.ca/publications/", "../policy/raw/ciffc/fs2026.pdf",
     "FY2024-25, FY2025-26", "agent transactions; resource exchange"),
    ("CPI all-items Canada (v41690973)", "Statistics Canada via Bank of Canada Valet",
     "https://www.bankofcanada.ca/valet/observations/V41690973/json", "../losses/raw/cpi/boc_V41690973.json", "to 2026-09",
     "2025-dollar factors (same as economic-value)"),
]
with open(os.path.join(OUT, "gov_manifest.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["source", "publisher", "url", "local_file", "coverage", "used_for", "accessed"])
    for m in MAN:
        w.writerow(list(m) + [ACC])
print(len(MAN), "manifest rows")
