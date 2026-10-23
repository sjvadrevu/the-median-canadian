"""Build east readiness outputs from values transcribed from official records held in raw/.
Usage: python3 -I east_03_build_outputs.py READINESS_DIR"""
import csv, os, sys

OUT = sys.argv[1]
ACC = "2026-10-22"

U = {
 "on_est": "https://www.ontario.ca/page/expenditure-estimates-ministry-natural-resources-2026-2027",
 "on_pa": "https://data.ontario.ca/dataset/public-accounts-ministry-statements-and-schedules",
 "on_r_2026_09": "https://news.ontario.ca/en/release/1008002/ontario-investing-an-additional-20-million-to-strengthen-wildland-firefighting",
 "on_r_2026_03": "https://news.ontario.ca/en/release/1007233/ontario-ready-for-2026-wildland-fire-season",
 "on_r_2025_11": "https://news.ontario.ca/en/release/1006689/ontarios-2025-wildland-fire-season-officially-ends",
 "on_r_2024_10": "https://news.ontario.ca/en/release/1005182/ontario-increasing-wildland-firefighting-capacity",
 "on_r_2024_03": "https://news.ontario.ca/en/release/1004337/ontario-launches-new-incentive-payment-for-wildland-firefighting-staff",
 "on_r_2023_10": "https://news.ontario.ca/en/release/1003719/ontario-marks-the-end-of-a-challenging-wildland-fire-season",
 "on_ag": "https://www.auditor.on.ca/en/content/annualreports/arreports/en24/1-10FU_mgmthazards_en24.pdf",
 "on_plans": "https://www.ontario.ca/page/published-plans-and-annual-reports-2025-2026-ministry-natural-resources",
 "on_avn": "https://www.ontario.ca/page/aviation-services",
 "on_strat": "https://www.ontario.ca/page/wildland-fire-management-strategy",
 "on_hansard": "https://www.ola.org/en/legislative-business/committees/interior/parliament-43/transcripts/committee-transcript-2024-jun-10",
 "on_ero": "https://ero.ontario.ca/notice/019-8756",
 "cr2023": "https://ciffc.ca/download/canada-reports/?wpdmdl=1585&filename=CIFFC_2023CanadaReport_FINAL.pdf",
 "cr2024": "https://ciffc.ca/download/canada-reports/?wpdmdl=1585&filename=1788899106wpdm_Canada_Report_2024_EN_Version.pdf",
 "cr2025": "https://ciffc.ca/download/canada-reports/?wpdmdl=1585&filename=Canada-Report-2025_EN_Version.pdf",
 "ar2324": "https://ciffc.ca/download/ciffc-annual-reports-2/?wpdmdl=3479&filename=ENG-FINAL-Annual-Report-2023-24.pdf",
 "ar2425": "https://ciffc.ca/download/ciffc-annual-reports-2/?wpdmdl=3479&filename=1783523083wpdm_2024-2025-CIFFC-Annual-Report.pdf",
 "avw": "https://ciffc.ca/download/aviation-challenges-workshop-report/?wpdmdl=1675&filename=CIFFC_Aviation_Challenges_Workshop_Report_2023.pdf",
 "sp2024": "https://ciffc.ca/download/ciffc-annual-reports/?wpdmdl=1587&filename=CIFFC_Stategic_Plan_2024-2029_2023_12_21.pdf",
 "pcaa": "https://www.canada.ca/en/public-safety-canada/news/2026/05/pan-canadian-aerial-asset-program.html",
 "pcaa_rel": "https://www.canada.ca/en/public-safety-canada/news/2026/05/government-of-canada-funds-10-new-wildfire-firefighting-aircraft-and-two-firefighting-support-assets-to-boost-nationwide-response-capacity.html",
 "b2025": "https://budget.canada.ca/2025/report-rapport/pdf/budget-2025.pdf",
 "senate": "https://sencanada.ca/en/info-page/parl-45-1/agfo-canada-on-fire/",
 "qc_ra2025": "https://a-ca.storyblok.com/f/2000396/x/c22b63b6cb/8-5x11-rapport_annuel_2025-vf.pdf",
 "qc_ra2024": "https://a-ca.storyblok.com/f/2000396/x/b3c411594f/rapport_annuel-2024-lr.pdf",
 "qc_ra2023": "https://a-ca.storyblok.com/f/2000396/x/9c87a40c30/rapport_annuel-2023-lr.pdf",
 "qc_ra2022": "https://a-ca.storyblok.com/f/2000396/x/a4ad21eda8/rapport_annuel-2022-lr.pdf",
 "qc_sag": "https://www.quebec.ca/gouvernement/services-organisations-publiques/service-aerien-gouvernemental/incendies-de-foret",
 "qc_bud": "https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf",
 "qc_pagd": "https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/secretariat-du-conseil-du-tresor/publications-adm/budgets/2026-2027/2_plans_annuels_gestion_depenses_mo.pdf",
 "qc_16m": "https://www.quebec.ca/nouvelles/actualites/details/lutte-contre-les-feux-de-foret-le-gouvernement-du-quebec-annonce-un-soutien-de-16-m-pour-la-sopfeu-52023",
 "qc_fed": "https://www.canada.ca/fr/ressources-naturelles-canada/nouvelles/2025/01/le-canada-et-le-quebec-annoncent-un-investissement-majeur-dans-des-equipements-de-lutte-contre-les-feux-de-foret.html",
 "nb_plan": "https://www.gnb.ca/content/dam/GNB3/t/ls/em/ep/fs-fw/docs/wildfire-management-preparedness-plan-2025-2030-en.pdf",
 "nb_plan_pg": "https://www.gnb.ca/en/topic/laws-safety/emergency-preparedness-alerts/wildfires/wildfire-management-plan.html",
 "nb_r_08": "https://www.gnb.ca/en/news/n-b.2026.08.government-unveils-new-wildfire-management-plan.html",
 "nb_r_04": "https://www.gnb.ca/en/news/n-b.2026.04.government-boosts-wildfire-readiness-season-begins-early.html",
 "nb_est": "https://www.gnb.ca/content/dam/GNB3/gov/budget/docs/main-estimates-budget-principal-2026-2027.pdf",
 "ns_aar": "https://www.gov.ns.ca/natr/forestprotection/wildfire/nova-scotia-wildfires-2023-after-action-report.pdf",
 "ns_r_2024_04": "https://news.novascotia.ca/en/2024/04/29/wildfire-report-highlights-strengths-areas-improvement",
 "ns_r_2023_12": "https://news.novascotia.ca/en/2023/12/15/province-purchasing-new-helicopter-water-bombers",
 "ns_r_2026_05": "https://news.novascotia.ca/en/2026/05/13/nova-scotia-contracts-four-fixed-wing-water-bombers",
 "ns_r_2026_10": "https://news.novascotia.ca/en/2026/10/22/investments-dedicated-crews-strengthened-2026-wildfire-response",
 "ns_r_2026_07": "https://news.novascotia.ca/en/2026/07/14/new-department-natural-resources-helicopters",
 "ns_est2627": "https://www.novascotia.ca/sites/default/files/documents/7-4172/budget-estimates-2026-27-en.pdf",
 "ns_est2526": "https://www.novascotia.ca/sites/default/files/documents/7-3890/budget-estimates-2025-26-en.pdf",
 "ns_est2425": "https://www.novascotia.ca/sites/default/files/documents/7-805/estimates-and-supplementary-detail-budget-2024-2025-en.pdf",
 "ns_addapp": "https://www.novascotia.ca/sites/default/files/documents/7-4172/additional-appropriations-budget-2026-27-en.pdf",
 "nl_r_2026_04": "https://www.gov.nl.ca/releases/2026/ti/0413n01/",
 "nl_r_2026_06": "https://www.gov.nl.ca/releases/2026/fal/0604n02/",
 "nl_r_2026_07": "https://www.gov.nl.ca/releases/2026/fal/0714n01/",
 "nl_r_2026_04b": "https://www.gov.nl.ca/releases/2026/exec/0424n03/",
 "nl_r_2026_04ag": "https://www.gov.nl.ca/releases/2026/fal/0423n07/",
 "nl_r_2025_04": "https://www.gov.nl.ca/releases/?p=56169",
 "nl_r_2025_05": "https://www.gov.nl.ca/releases/?p=56433",
 "nl_r_2026_09": "https://www.gov.nl.ca/releases/?p=62633",
 "pe_page": "https://www.princeedwardisland.ca/en/information/land-and-environment/wildfire-response-in-pei",
 "pc_qp": "https://search.open.canada.ca/qpnotes/record/ec%2CSOS-QP-00001",
 "pc_fire": "https://parks.canada.ca/nature/science/conservation/feu-fire/incendies-wildfires",
 "pc_dp": "https://parks.canada.ca/agence-agency/bib-lib/plans/dp/plan-ministeriel-2026-2027-departmental-plan",
}
J = lambda *k: " ; ".join(U[x] for x in k)

def pct(b, acts):
    if b is None or any(a is None for a in acts):
        return ""
    return f"{100 * b / (sum(acts) / len(acts)):.1f}"

cols = ["agency","budget_2026_27_cad","budget_basis","actual_2023_24_cad","actual_2024_25_cad","actual_2025_26_cad","actual_basis",
        "budget_pct_of_avg_actual","overrun_mechanism","firefighters","firefighters_year","airtankers","helicopters","year_round_staff",
        "detection_notes","vacancies_or_outages","review_name","review_recs_total","review_recs_implemented","ia_success_by_year",
        "zone_policy_change","imports_personnel","stated_plans_2026_27","source_urls"]

rows = []
on_b, on_a = 149951400, [206473000, 171041000, 272996000]
rows.append({
 "agency": "Ontario (MNR Aviation, Forest Fire and Emergency Services)",
 "budget_2026_27_cad": on_b,
 "budget_basis": "2026-27 Expenditure Estimates, vote 2104-1 Emergency fire fighting, net of $11.0M recoveries (gross $160,952,400). Province calls this the year-start emergency firefighting budget, doubled from $70M to $150M (release 2026-09-14). Separate line Public safety and emergency response net $58,397,300; aircraft capital $14,064,500",
 "actual_2023_24_cad": on_a[0], "actual_2024_25_cad": on_a[1], "actual_2025_26_cad": on_a[2],
 "actual_basis": "Public Accounts of Ontario, MNR Public Protection: Emergency Fire Fighting, net of recoveries, fiscal Apr-Mar; all three are actuals",
 "budget_pct_of_avg_actual": pct(on_b, on_a),
 "overrun_mechanism": "Spend beyond the base and seek more from Treasury Board in season (Deputy Minister, Estimates committee 2024-06-10: 'we might come back to the Treasury Board and ask for more funding'); totals reported after the fact in Public Accounts",
 "firefighters": "More than 1,000 front-line wildland fire rangers and aviation crew members (eligible for 2024 retention payment); about 143 fire crews (MPP figure, Minister: 'we are in that range', June 2024)",
 "firefighters_year": "2024",
 "airtankers": "9 CL-415 owned (page updated 2026-01-08); 6 DHC-515 on order, expected early 2030s; fleet age not stated officially",
 "helicopters": "13 contracted (after 4 medium added, Oct 2024); owned count not stated ('various helicopters, including several Eurocopters'); 5 new helicopters announced in $650M fleet investment (2026). Total fleet 28 specialized aircraft (2026). Also 6 DHC-6 Twin Otters, 5 DHC-2T Turbo Beavers",
 "year_round_staff": "More than 170 permanent fire management positions added since 2024 (about 100 filled 2024-2025, 68 added for 2026)",
 "detection_notes": "Detection by aircraft and public; no count of detection aircraft published. 126 ministry weather stations (AG 2022)",
 "vacancies_or_outages": "No vacancy count published. AG 2024 follow-up: training records paper-based, 'honour system', IT system does not flag expiring training",
 "review_name": "Auditor General of Ontario 2022 audit Management of Hazards and Emergencies in the Environment; follow-up Dec 2024",
 "review_recs_total": "70 recommended actions (55 for MNR)",
 "review_recs_implemented": "9 of 70 fully implemented (13%) as of 2024-11-20; MNR fully implemented 9% of its 55 and made little or no progress on 58%; forest fire items (response times, after-action reviews, training tracking) little or no progress",
 "ia_success_by_year": "Initial attack success and effectiveness: 2022-23 92%; 2023-24 91%; baseline 94%; target 95% for 2025-26 (2024-25 and later not found)",
 "zone_policy_change": "None since 2023. 2014 Wildland Fire Management Strategy replaced the 2004 zones with fire-by-fire assessment; some fires 'will be monitored'. Strategy update under modernization due April 2027 (AG). Wildland Fire Management Act in force 2026-01-01 (ERO decision 2025-12-19) does not change zones",
 "imports_personnel": "2023: received 104 personnel (Mexico, Idaho, CFS) plus aircraft; exported 635 (417 FireRangers, 218 overhead). 2024: no imports reported; exported 588 firefighters, 198 overhead, 6 CL-415, 4 helicopters. 2025: received personnel, equipment and aircraft from AB, QC, BC, NB and US (count not given); exported 409 personnel and 6 aircraft",
 "stated_plans_2026_27": "68 permanent positions for 2026; $650M aerial fleet (6 DHC-515, 5 helicopters); $20M+ rebuild of Vedette and Socket Lake forward attack bases before 2027 season, Ranger Lake and Ogoki next; PIMS training system modernization (spring 2026); program modernization by April 2027",
 "source_urls": J("on_est","on_pa","on_r_2026_09","on_r_2026_03","on_r_2025_11","on_r_2024_10","on_r_2024_03","on_r_2023_10","on_ag","on_plans","on_avn","on_strat","on_hansard","on_ero","cr2023","cr2024","cr2025"),
})

rows.append({
 "agency": "Quebec (SOPFEU with MSP; SAG airtankers; MRNF)",
 "budget_2026_27_cad": "",
 "budget_basis": "No separate wildfire line in Quebec 2026-27 budget. MSP program 5 Securite civile et securite incendie: $125,511,400 budget 2026-27 vs $179,319,400 probable 2025-26; MSP says the drop reflects 2025-26 spending on disaster recovery and SOPFEU fire suppression that is not carried into the base. SOPFEU base government contribution fixed at $45,818,684 (2025)",
 "actual_2023_24_cad": 250878155, "actual_2024_25_cad": 155617236, "actual_2025_26_cad": 159658370,
 "actual_basis": "SOPFEU audited total expenses (charges), calendar years 2023, 2024, 2025 (not fiscal). Includes costs of out-of-province missions (billed revenue $14.5M in 2025). Members' assessments (government and industry): 2023 $213,316,831; 2024 $115,646,200; 2025 $95,257,025. SAG airtanker costs partly outside SOPFEU",
 "budget_pct_of_avg_actual": "",
 "overrun_mechanism": "Suppression assessment billed to members after the season (2025 $49.4M, 2024 $69.8M); in-year additions by government (fall 2023 update $16M for SOPFEU; 2025-26 +$2M SOPFEU suppression recorded in Budget 2026-27)",
 "firefighters": "312 forest firefighters (2025); 282 (2024); 232 (2023). Plus 290 regular staff and 119 other seasonal staff (2025); 681 trained auxiliary combatants in 2025 vs target 781",
 "firefighters_year": "2025",
 "airtankers": "SAG fleet 14 (8 CL-415, 4 CL-215P, 2 CL-215T), page dated 2026-07-13; SOPFEU lists 17 airtankers available in 2025 (+2 vs 2024; 15 in 2023 and 2024 plus 4 AT-802F in 2024) including contracted CL-215s",
 "helicopters": "21 under long-term lease (summer 2025); 19 (2024); 16 (2023)",
 "year_round_staff": "290 regular employees (2025, +59 vs 2024); 231 (2024); more than 65 new positions created and filled in 2025",
 "detection_notes": "27 detection aircraft under contract; 11 bird-dog and transport aircraft (2025). Public made first detection of 85% of fires in 2024",
 "vacancies_or_outages": "2024: one CL-415 out for avionics work; possible unavailability of 3 airtankers from SAG pilot shortage, covered by contracted CL-215s, 4 AT-802F and 3 heavy helicopters. 2025: one CL-415 out; 4 SAG aircraft expected unavailable for lack of pilots and technicians, covered by 4 contracted CL-215s. HR director post vacant in 2024",
 "review_name": "No independent or auditor review of the 2023 season found. SOPFEU annual reports describe 2023 capacity exceedance",
 "review_recs_total": "", "review_recs_implemented": "",
 "ia_success_by_year": "Initial attack within one hour: 2022 91.1%; 2023 66.9%. Intervention objective, intensive zone: 2025 76.1% (2024 not found). Fires detected before 0.5 ha: 2022 92.6%; 2023 72.4%",
 "zone_policy_change": "No formal change found. Intensive zone full response; northern zone (north of about 51st parallel) fought only for values in the special northern protection plan (8 of 31 northern fires fought in 2025). SOPFEU notes more northern interventions as an operational challenge (2024)",
 "imports_personnel": "2023: more than 2,070 people from outside regular operations in June-July, including CAF and out-of-province crews from France, Portugal, Spain, US, Korea and others; exported more than 150. 2024: no imports reported; exported to MB, AB, BC, NT, Connecticut. 2025: no imports reported; exported a record 620 personnel (10,923 person-days)",
 "stated_plans_2026_27": "Continue growth plan begun 2024 (capacity effects expected over next 3 years); MSP capacity grant $19.25M in 2025; $64M Canada-Quebec equipment (2025-2027); CL-415 avionics modernization 56.2% done, prototype awaiting Transport Canada certification; prevention plan 2025-2027",
 "source_urls": J("qc_ra2025","qc_ra2024","qc_ra2023","qc_ra2022","qc_sag","qc_bud","qc_pagd","qc_16m","qc_fed","cr2023","cr2024","cr2025"),
})

rows.append({
 "agency": "New Brunswick (DNR Wildfire Management Branch; FPL aviation)",
 "budget_2026_27_cad": 29126000,
 "budget_basis": "Main Estimates 2026-27, Natural Resources program, Forest Protection component (fire, insects and disease; not wildfire only). Budget 2026-27 adds $6.7M for wildfire preparedness (74 year-round rangers, 4 Fire Boss)",
 "actual_2023_24_cad": "", "actual_2024_25_cad": "", "actual_2025_26_cad": "",
 "actual_basis": "Not found in official record at component level. Natural Resources program 2025-26 revised $133,227,000 vs estimate $116,898,000 (not attributed to wildfire)",
 "budget_pct_of_avg_actual": "",
 "overrun_mechanism": "Not stated in records reached",
 "firefighters": "Total forest ranger count not published; 74 seasonal ranger positions converted to year-round (2026)",
 "firefighters_year": "2026",
 "airtankers": "Contracted from Forest Protection Limited; 4 new Fire Boss added to FPL contract for 2026; total fleet count not stated",
 "helicopters": "Not stated",
 "year_round_staff": "74 positions converted to year-round (2026)",
 "detection_notes": "30 DNR weather stations plus 30 monitored (plan 2026)",
 "vacancies_or_outages": "2025 after-action review: training and staffing gaps; personnel fatigued after more than 40 days of sustained operations",
 "review_name": "2025 wildfire season After-Action Review and Wildfire Management Preparedness Plan 2025-2030 (published 2026-08-31); also a third-party review of the wildfire program and air operations (not published)",
 "review_recs_total": "16 strategic and operational actions with completion years (1 year 1, 5 each in years 2 to 4)",
 "review_recs_implemented": "No status published; 74 year-round conversions, new equipment and community plans reported done",
 "ia_success_by_year": "",
 "zone_policy_change": "None found (full response province)",
 "imports_personnel": "2023: exported 236 (record). 2024: exported 157. 2025: exported 158, and for the first time requested out-of-province firefighters (count not given)",
 "stated_plans_2026_27": "Plan 2025-2030 pillars: communication, workforce capacity, partnerships, infrastructure and tools, decision rules; FMWCC over $25M over 4 years; WRFI $13M over 4 years; $2.6M community wildfire plans (2025-26)",
 "source_urls": J("nb_plan","nb_plan_pg","nb_r_08","nb_r_04","nb_est","cr2023","cr2024","cr2025"),
})

ns_b, ns_a = 21146000, [22516000, 9318000, 40881000]
rows.append({
 "agency": "Nova Scotia (DNR Forest Protection)",
 "budget_2026_27_cad": ns_b,
 "budget_basis": "Estimates 2026-27, Regional Services, Fleet and Forest Protection line ($21.146M; 2025-26 estimate was $11.667M). Covers government air fleet and forest protection; regional suppression staff costs sit in other lines. Budget 2026-27 includes $6.8M wildfire response (4 AT-802 + bird dog contract $6.5M, 3 air attack officers $0.3M)",
 "actual_2023_24_cad": ns_a[0], "actual_2024_25_cad": ns_a[1], "actual_2025_26_cad": ns_a[2],
 "actual_basis": "Forecast, not final actual: 2023-24 forecast in 2024-25 Estimates; 2024-25 forecast in 2025-26 Estimates; 2025-26 forecast in 2026-27 Estimates (same line)",
 "budget_pct_of_avg_actual": pct(ns_b, ns_a),
 "overrun_mechanism": "Additional appropriations under the Finance Act (Feb 2026: Natural Resources $34.2M incl. $4.2M operating incl. seasonal wildfire support; Public Works $1.1M wildfire costs)",
 "firefighters": "About 300 wildland firefighters, plus 60 trained municipal and volunteer firefighters available",
 "firefighters_year": "2024",
 "airtankers": "None owned; 4 Air Tractor AT-802 contracted May 13 to Sept 30, 2026 (extendable) with 1 bird dog",
 "helicopters": "4 new Airbus H125 in service July 2026 (replaced 4 bought in 2016)",
 "year_round_staff": "",
 "detection_notes": "",
 "vacancies_or_outages": "AAR 2024: air operations manager role 'dependent on one person'; IMT has 'limited capacity'",
 "review_name": "2023 Nova Scotia Wildfires After-Action Report (Calian, 2024-03-08); 2025 post-season review under way (CIFFC 2025)",
 "review_recs_total": "63 recommendations (20 opportunities for improvement)",
 "review_recs_implemented": "Not found in official record (department accepted all; no published status)",
 "ia_success_by_year": "",
 "zone_policy_change": "None found (full response province)",
 "imports_personnel": "2023: imported from CIFFC and NFFPC partners (count not in Canada Report). 2024: one of its highest export years. 2025: 'resources were brought in from nearly every Canadian wildland fire agency'; exported three 20-person crews and specialists. 2026: mutual aid from NL",
 "stated_plans_2026_27": "Contracted fixed-wing tankers each season; new helicopters; FireSmart expansion; Fire Safety and Services Act; $3M fire services standards",
 "source_urls": J("ns_aar","ns_r_2024_04","ns_r_2023_12","ns_r_2026_05","ns_r_2026_07","ns_r_2026_10","ns_est2627","ns_est2526","ns_est2425","ns_addapp","cr2023","cr2024","cr2025"),
})

rows.append({
 "agency": "Newfoundland and Labrador (FAL wildfire; TI air services)",
 "budget_2026_27_cad": "",
 "budget_basis": "Not found: gov.nl.ca budget site offline on 2026-10-22 ('Temporary Disruption to Government Websites'). Budget 2026 new wildfire and emergency items over $7M (coveralls $1.7M, P25 radios $2.9M, trailers, training); $1.76M more helicopter support; 25 firefighters 2026-27 and 25 in 2027-28 ($730K)",
 "actual_2023_24_cad": "", "actual_2024_25_cad": "", "actual_2025_26_cad": "",
 "actual_basis": "Not found (estimates and public accounts not reachable)",
 "budget_pct_of_avg_actual": "",
 "overrun_mechanism": "Not found",
 "firefighters": "More than 100 wildland firefighters at 22 forest management district offices; +25 in 2026-27, +25 in 2027-28, +6 for Labrador",
 "firefighters_year": "2026",
 "airtankers": "5 CL-415 owned (one damaged on Burin Peninsula, out of service until April 2026 after $14.8M repair); 2 bird dog aircraft being procured (2025)",
 "helicopters": "Contracted; count not stated ($1.76M increase in 2026-27)",
 "year_round_staff": "",
 "detection_notes": "",
 "vacancies_or_outages": "One of five CL-415 out of service through the 2025 season (repair contract April 2025, return April 2026)",
 "review_name": "Auditor General of NL: Emergency Management and Business Continuity Plans (April 2026); no wildfire after-action review found",
 "review_recs_total": "10 (all accepted)",
 "review_recs_implemented": "Some addressed per minister (plans updated); no count published",
 "ia_success_by_year": "",
 "zone_policy_change": "None found. Interior Labrador fires mostly monitored or modified response (CIFFC 2023)",
 "imports_personnel": "2023: exported where possible. 2024: imported from NS, NB, QC, ON, SK, Parks Canada and CIFFC contractors for Labrador fires; exported to MB. 2025: imported from BC, NB, QC, ON, Parks Canada and contractors; exported firefighters to MB, IMT to AB and YT, CL-415 to NB and NS",
 "stated_plans_2026_27": "Atlantic Wildfire Centre in Gander ($32M federal-provincial to 2030); seasonal waterbomber base in Wabush (planning); 2 structural protection units for Labrador; $2.26M for 58 community wildfire plans",
 "source_urls": J("nl_r_2026_04","nl_r_2026_06","nl_r_2026_07","nl_r_2026_04b","nl_r_2026_04ag","nl_r_2025_04","nl_r_2025_05","nl_r_2026_09","cr2023","cr2024","cr2025"),
})

rows.append({
 "agency": "Prince Edward Island (Forests, Fish and Wildlife wildfire protection)",
 "budget_2026_27_cad": "",
 "budget_basis": "Not found: 2026 Operating Estimates PDF refused by site (403 to script; WebFetch text ended at page 72, before Land and Environment). Page says budget includes five new forest fire vehicles and a $550,000 forest fire prevention fund",
 "actual_2023_24_cad": "", "actual_2024_25_cad": "", "actual_2025_26_cad": "",
 "actual_basis": "Not found",
 "budget_pct_of_avg_actual": "",
 "overrun_mechanism": "Not found",
 "firefighters": "Not stated; five wildland fire trucks at volunteer fire departments",
 "firefighters_year": "",
 "airtankers": "0 ('PEI does not have any air operations or water bombers')",
 "helicopters": "0",
 "year_round_staff": "",
 "detection_notes": "",
 "vacancies_or_outages": "",
 "review_name": "None found",
 "review_recs_total": "", "review_recs_implemented": "",
 "ia_success_by_year": "",
 "zone_policy_change": "None found",
 "imports_personnel": "2023: exported to AB, NS, QC, BC. 2024: exported to NT, AB, Parks Canada, MB. 2025: exported 45 personnel. No imports reported",
 "stated_plans_2026_27": "Five new forest fire vehicles; $550,000 prevention fund including training; 'continue investing in its staff and resources' (CIFFC 2025)",
 "source_urls": J("pe_page","cr2023","cr2024","cr2025"),
})

rows.append({
 "agency": "Parks Canada (National Fire Management Program)",
 "budget_2026_27_cad": "",
 "budget_basis": "Not separable. Budget 2021 $100.6M over 5 years; 2026 update extends $9M/yr from 2026-27 (see policy/measures.csv)",
 "actual_2023_24_cad": "", "actual_2024_25_cad": "", "actual_2025_26_cad": "",
 "actual_basis": "Not separable in InfoBase",
 "budget_pct_of_avg_actual": "",
 "overrun_mechanism": "One-time federal funding (Budget 2024: $38M for 2023 response)",
 "firefighters": "National cadre of 300 wildland fire management personnel; 22 four-person fire crews and 5 national incident management teams",
 "firefighters_year": "2025",
 "airtankers": "None owned; contracted resources",
 "helicopters": "Long-term helicopter contracts; count not stated",
 "year_round_staff": "",
 "detection_notes": "",
 "vacancies_or_outages": "",
 "review_name": "Jasper 2024: Town of Jasper municipal after-action review (Satya Inc.); Parks Canada's own reviews 'being conducted' (CIFFC 2024), not found published",
 "review_recs_total": "", "review_recs_implemented": "",
 "ia_success_by_year": "",
 "zone_policy_change": "Red (full), yellow (modified) and green (monitored) zones per park; no change found",
 "imports_personnel": "2023: 303 PC personnel redeployed internally (8,718 person-days), plus help from ON, AB, NT, New Zealand. 2024 Jasper: 173 fire crew personnel and 62 single resources via CIFFC; exported 65. 2025: deployed 334 personnel to 10 locations; exported 40",
 "stated_plans_2026_27": "Prescribed fire, thinning and community fire guards (Departmental Plan 2026-27)",
 "source_urls": J("pc_qp","pc_fire","pc_dp","cr2023","cr2024","cr2025"),
})

rows.append({
 "agency": "National (CIFFC)",
 "budget_2026_27_cad": "",
 "budget_basis": "Pan-Canadian Aerial Asset Program: $316.7M over five years via NRCan contribution to CIFFC (Budget 2025 $257.6M over 4 years for leases); 2026 leases are 150-day contracts",
 "actual_2023_24_cad": "", "actual_2024_25_cad": "", "actual_2025_26_cad": "",
 "actual_basis": "CIFFC audited statements to 2026-03-31: no PCAA funds received or spent (see policy/measures.csv)",
 "budget_pct_of_avg_actual": "",
 "overrun_mechanism": "International imports under arrangements with 12 countries (2023)",
 "firefighters": "No official national firefighter count found",
 "firefighters_year": "",
 "airtankers": "PCAA 2026: 4 Dash 8-400 AT (Conair), 1 TBM 960 air attack; CIFFC 2023: 'the Canadian airtanker fleet is aging'; DHC-515 delivery may take seven years from order",
 "helicopters": "PCAA 2026: 3 AS332 L/L1 (Coldstream), 2 S-92A (VIH)",
 "year_round_staff": "CIFFC: 16 staff positions, 14 filled (2023-24)",
 "detection_notes": "WildFireSat not launched (target 2029, see policy/measures.csv)",
 "vacancies_or_outages": "Aircrew and aviation maintenance engineer shortages 'expected to persist or worsen' (CIFFC 2023)",
 "review_name": "CIFFC Aviation Challenges Workshop Report 2023; Senate AGFO 'Canada on fire' (2026-06-10)",
 "review_recs_total": "Senate: 15 recommendations (Rec 3: national fleet of modern firefighting aircraft)",
 "review_recs_implemented": "",
 "ia_success_by_year": "",
 "zone_policy_change": "",
 "imports_personnel": "International personnel imported: 2023 5,504; 2024 626; 2025 1,595",
 "stated_plans_2026_27": "PCAA aircraft prepositioned by fire activity; Frontline Gear Support $19M to 2030; CIFFC Strategic Plan 2024-2029 goal 1: develop firefighting capacity",
 "source_urls": J("cr2023","cr2024","cr2025","ar2324","ar2425","avw","sp2024","pcaa","pcaa_rel","b2025","senate"),
})

with open(os.path.join(OUT, "agencies_east.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

# national table
nat = [
 (2022, 0, "", "", "", "CIFFC Annual Report 2023-24 (footnote: '0 days were spent at National Preparedness Level 5 during the 2022 fire season')", U["ar2324"]),
 (2023, 120, 368, "", 5504, "CIFFC Canada Report 2023 (NPL 5 record 120 days; country tiles: US 2,450, South Africa 861, Australia 646, Mexico 391, France 353, Korea 150, Costa Rica 146, Portugal 140, Brazil 105, Spain 100, New Zealand 100, Chile 62); CIFFC Annual Report 2023-24 (368 resource orders; 'over 5,500 international')", U["cr2023"] + " ; " + U["ar2324"]),
 (2024, 39, 223, "", 626, "CIFFC Canada Report 2024 (NPL 5: 39 days; 626 international personnel in text, country tiles sum 627: Australia 284, South Africa 216, Costa Rica 93, New Zealand 28, US 6); CIFFC Annual Report 2024-25 (223 orders)", U["cr2024"] + " ; " + U["ar2425"]),
 (2025, 89, "", "", 1595, "CIFFC Canada Report 2025 (NPL 5: 89 days, second longest; 1,595 international: US 628, Mexico 349, Australia 295, Costa Rica 201, Chile 63, New Zealand 59); order count not published (2025-26 annual report not yet posted)", U["cr2025"]),
 (2026, "", "", "", "", "No CIFFC Canada Report for 2026 yet; Public Safety Canada 2026 updates give no NPL or import counts", U["pcaa_rel"]),
]
with open(os.path.join(OUT, "national_ciffc.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["year","apl5_days","requests_total","requests_unfilled","international_personnel_imported","source","url"]); w.writerows(nat)

# gaps
G = []
def g(agency, gap, ev, orig, src, url):
    G.append([agency, gap, ev, orig, src, url, ACC])

g("Ontario","Year-start firefighting budget ($150M) is 55% of the 2025-26 actual ($273M); overruns are funded after the fact","You keep on plowing and spend what you need to spend.","","Ontario Standing Committee on the Interior, Estimates, 2024-06-10 (Minister Smith)",U["on_hansard"])
g("Ontario","No tracking of whether response-time targets are met","the Ministry did not provide any supporting documentation to demonstrate how it is tracking whether the required response times are being met","","Auditor General of Ontario, 2024 follow-up",U["on_ag"])
g("Ontario","After-action reviews done for few fire emergencies and not followed up","the Ministry had prepared after-action reports for only two of the 11 declared emergencies for forest fires from 2017–2021","","Auditor General of Ontario, 2024 follow-up",U["on_ag"])
g("Ontario","Firefighter training records kept on paper; certification relies on trust","This redundant process leads to delays in updating records and creates reliance on an “honour system,”","","Auditor General of Ontario, 2024 follow-up",U["on_ag"])
g("Ontario","Most audit actions on hazards, including fire, not progressed","for 50% of our recommended actions there has been little or no progress","","Auditor General of Ontario, 2024 follow-up",U["on_ag"])
g("Ontario","Initial attack success below target and slipping","Initial attack success and effectiveness: 92% (2022-23), 91% (2023-24), target 95% (2025-26)","","Ontario MNR Published plans and annual reports 2025-2026",U["on_plans"])
g("Ontario","New waterbombers will not arrive until the 2030s","six new De Havilland, DHC-515 waterbombers to expand Ontario’s air fleet, which are expected to arrive in the early 2030s","","Ontario news release 2025-11-03",U["on_r_2025_11"])
g("Ontario","FireSmart support excludes First Nations and unorganized territories; few communities funded","this pilot project offers funding to only two to four recipients per year. Unorganized territories and First Nation communities are not eligible","","Auditor General of Ontario, 2024 follow-up",U["on_ag"])

g("Quebec","Capacity was exceeded in 2023 and fires were left unfought","several fires therefore remained under observation without being fought according to the standard process; deviations from operating standards were accepted for lack of firefighting resources","plusieurs incendies sont par conséquent demeurés sous observation sans être combattus selon la séquence standardisée des processus établis. Des dérogations aux standards opérationnels habituels ont ainsi été acceptées et appliquées par manque de ressources de combat","SOPFEU Rapport annuel 2023",U["qc_ra2023"])
g("Quebec","Initial attack within one hour fell from 91% (2022) to 67% (2023)","Initial attack of fires in under one hour: 66.9%","Attaque initiale des feux en moins d’une heure : 66,9 %","SOPFEU Rapport annuel 2023 (2022 value 91.1% in Rapport annuel 2022)",U["qc_ra2023"])
g("Quebec","Government airtankers grounded by pilot and technician shortages","the anticipated unavailability of four SAG aircraft due to a lack of pilots and technicians","l’indisponibilité anticipée de quatre appareils du SAG, en raison d’un manque de pilotes et de techniciens","SOPFEU Rapport annuel 2025",U["qc_ra2025"])
g("Quebec","CL-415 avionics upgrade funded in 2019 still not certified","the prototype is still awaiting this certification","le prototype est toujours en attente de cette certification","SOPFEU Rapport annuel 2025",U["qc_ra2025"])
g("Quebec","Auxiliary firefighter targets missed two years running","681 auxiliary combatants were trained, compared with a target of 781","681 combattants auxiliaires ont été formés, comparativement à un objectif de 781","SOPFEU Rapport annuel 2025",U["qc_ra2025"])
g("Quebec","Rising wage and aircraft contract costs push SOPFEU into deficit","the Society must deal with rising salaries and higher costs of aircraft and airtanker contracts","la Société doit composer avec la hausse des salaires et l’augmentation des coûts liés aux contrats d’aéronefs et d’avions-citernes","SOPFEU Rapport annuel 2025",U["qc_ra2025"])
g("Quebec","More fires in the northern zone strain operations","this poses operational challenges that the organization and its partners will need to address","Cela pose des défis opérationnels sur lesquels l’organisation et ses partenaires devront se pencher","SOPFEU Rapport annuel 2024",U["qc_ra2024"])
g("Quebec","2026-27 budget does not carry 2025-26 suppression spending forward","expenses incurred in 2025-26 for major disaster recovery and forest fire suppression by SOPFEU","les dépenses encourues, en 2025-2026, pour la gestion du rétablissement des sinistres majeurs et pour la suppression des feux de forêt par la SOPFEU","Quebec Plans annuels de gestion des dépenses 2026-2027 (Sécurité publique, programme 5)",U["qc_pagd"])

g("New Brunswick","Needed outside firefighters for the first time in 2025","marking the first time that the province has needed to augment its own firefighter staff with out-of-province firefighters","","NB Wildfire Management Preparedness Plan 2025-2030",U["nb_plan"])
g("New Brunswick","Workforce too thin for long or complex fire periods","Staffing levels, reliance on volunteers, rotation capacity, and succession planning present challenges during prolonged or high intensity wildfire activity.","","NB Wildfire Management Preparedness Plan 2025-2030",U["nb_plan"])
g("New Brunswick","Crew fatigue after 40+ days of continuous operations","provincial wildfire personnel had been engaged in sustained operations for more than 40 days and were experiencing significant fatigue","","NB Wildfire Management Preparedness Plan 2025-2030",U["nb_plan"])
g("New Brunswick","Training and staffing gaps strained supervisors","Training and staffing gaps placed added pressure on supervisors.","","NB Wildfire Management Preparedness Plan 2025-2030",U["nb_plan"])
g("New Brunswick","Aircraft and bases need modernizing","Modernizing aircraft and base infrastructure and refining operating procedures with contracted partners","","NB Wildfire Management Preparedness Plan 2025-2030",U["nb_plan"])
g("New Brunswick","Equipment and logistics gaps","Equipment and logistical gaps created operational challenges.","","NB Wildfire Management Preparedness Plan 2025-2030",U["nb_plan"])

g("Nova Scotia","Incident management team too small","a heavy reliance on the expertise of the Incident Management Team (IMT) members for decision making and response function; a team that already has limited capacity","","2023 Nova Scotia Wildfires After-Action Report (Calian)",U["ns_aar"])
g("Nova Scotia","Air operations depend on one person","The air operations manager should identify personnel that can be activated to assist with the role during an extended period of operations (currently this is dependent on one person).","","2023 Nova Scotia Wildfires After-Action Report (Calian)",U["ns_aar"])
g("Nova Scotia","Response plans out of date","some agency/municipal plans are outdated, inflexible, and do not adequately address the growing risks and response requirements of wildfires","","2023 Nova Scotia Wildfires After-Action Report (Calian)",U["ns_aar"])
g("Nova Scotia","No owned fixed-wing tankers; buying takes up to a decade, so tankers are leased per season","the wait list to buy a fixed wing aircraft can be up to 10 years","","Nova Scotia news release 2023-12-15",U["ns_r_2023_12"])
g("Nova Scotia","Heavy reliance on outside help in 2025","Resources were brought in from nearly every Canadian wildland fire agency, with only two exceptions","","CIFFC Canada Report 2025 (Nova Scotia section)",U["cr2025"])
g("Nova Scotia","Base budget far below spending; topped up with extra funding later in the year","Fleet and Forest Protection: 2025-26 estimate $11,667K, forecast $40,881K; 2026-27 estimate $21,146K","","Nova Scotia Estimates 2026-27, Natural Resources",U["ns_est2627"])
g("Nova Scotia","No public status on the 63 after-action recommendations","The Department accepts all recommendations and has already begun implementing some of the recommendations","","Nova Scotia news release 2024-04-29",U["ns_r_2024_04"])

g("Newfoundland and Labrador","Only four of five waterbombers available through 2025","The scope of work for the contract will address these structural repairs, as well as required maintenance, allowing the water bomber to return to service for the 2026-27 fire season.","","NL news release 2025-04-23",U["nl_r_2025_04"])
g("Newfoundland and Labrador","No waterbomber base in Labrador West; planning under way","Continue the planning process to establish infrastructure in Wabush to support a seasonal presence for a waterbomber in Labrador West.","","NL news release 2026-07-14",U["nl_r_2026_07"])
g("Newfoundland and Labrador","Emergency plans lagged; fires pulled staff from planning","Dealing with emergency situations, such as the 2025 wildfires, flooding in Badger, and other emerging situations, can divert focus and attention from administrative and planning duties.","","NL Minister statement on Auditor General report 2026-04-23",U["nl_r_2026_04ag"])
g("Newfoundland and Labrador","About 100 wildland firefighters provincewide after a record 243-fire season in 2025","More than 100 wildland firefighters are stationed at 22 Forestry Management District offices","","NL news release 2026-06-04",U["nl_r_2026_06"])

g("Prince Edward Island","No aerial firefighting capacity of its own","PEI does not have any air operations or water bombers.","","PEI Wildfire response in PEI page (2026-09-16)",U["pe_page"])

g("Parks Canada","Small national cadre of fire staff","national cadre of 300 wildland fire management personnel","","Question Period Note SOS-QP-00001 (2025-09-03)",U["pc_qp"])
g("Parks Canada","2023 needed double the usual internal redeployments","303 PC fire personnel ... were redeployed ... almost double the recent typical level of about 160","","CIFFC Canada Report 2023 (Parks Canada section)",U["cr2023"])

g("National (CIFFC)","Record time with all national resources committed","120 days spent at National Preparedness Level 5","","CIFFC Annual Report 2023-24",U["ar2324"])
g("National (CIFFC)","Domestic capacity runs out in big years; depends on imports","Due to resource requirements exceeding Canadian domestic capacity between July and September, agencies relied on our international partners","","CIFFC Annual Report 2024-25",U["ar2425"])
g("National (CIFFC)","Aging airtanker fleet","With few exceptions, the Canadian airtanker fleet is aging, with some platforms reaching the end of operational life","","CIFFC Aviation Challenges Workshop Report 2023",U["avw"])
g("National (CIFFC)","Pilot and aircraft engineer shortages","The current shortages are expected to persist or worsen.","","CIFFC Aviation Challenges Workshop Report 2023",U["avw"])
g("National (CIFFC)","New scooper aircraft take years to arrive","If a Canadian operator signs an order today, they may not see the aircraft for seven years","","CIFFC Aviation Challenges Workshop Report 2023",U["avw"])
g("National (CIFFC)","Fleet sizes not based on a needs model","These choices may have been made without a robust resource selection/needs model to guide decision making.","","CIFFC Aviation Challenges Workshop Report 2023",U["avw"])
g("National (CIFFC)","Unfilled request data exist but are not published","CIFFC ‘unable to fill’ Air Tanker Exchange request (2012-2022)","","CIFFC Aviation Challenges Workshop Report 2023 (listed as a data source to review)",U["avw"])
g("National (CIFFC)","National coordination centre stretched","The Coordination Centre and operations staff were stretched to capacity during the summer of 2023.","","CIFFC Annual Report 2023-24",U["ar2324"])
g("National (CIFFC)","Federal surge aircraft are seasonal leases only","150-day contract May 1, 2026, until September 27, 2026","","Public Safety Canada backgrounder Pan-Canadian Aerial Asset Program (2026-05-25)",U["pcaa"])
g("National (CIFFC)","Senate calls for a national fleet","create and fund a national fleet of modern firefighting aircraft, that are in good working order","","Senate AGFO report Canada on fire (2026-06-10), Recommendation 3",U["senate"])

with open(os.path.join(OUT, "gaps_east.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["agency","gap","evidence","evidence_original_language","source_name","url","accessed"]); w.writerows(G)

print(len(rows), "agency rows;", len(G), "gaps")
for r in rows:
    print(r["agency"][:40], r["budget_pct_of_avg_actual"])
