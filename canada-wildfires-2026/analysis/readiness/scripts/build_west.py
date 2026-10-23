"""Build agencies_west.csv, gaps_west.csv, manifest_west.csv from values verified in official records.
All values typed here were read from the files in ../raw/ or from WebFetch of official pages (see manifest)."""
import csv, os

OUT = os.path.join(os.path.dirname(__file__), "..")
ACC = "2026-10-22"

def pct(budget, actuals):
    a = [x for x in actuals if x is not None]
    if budget is None or len(a) != 3:
        return ""
    return f"{100 * budget / (sum(a) / 3):.1f}"

U = {
 "bc_est": "https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Estimates.pdf",
 "bc_bfp": "https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Budget_and_Fiscal_Plan.pdf",
 "bc_asr24": "https://www.bcbudget.gov.bc.ca/Annual_Reports/2023_2024/pdf/ministry/for.pdf",
 "bc_asr25": "https://www.bcbudget.gov.bc.ca/Annual_Reports/2024_2025/pdf/ministry/for.pdf",
 "bc_asr26": "https://www.bcbudget.gov.bc.ca/Annual_Reports/2025_2026/pdf/ministry/for.pdf",
 "bc_rel": "https://news.gov.bc.ca/releases/2026FOR0005-000267",
 "bc_q1": "https://news.gov.bc.ca/releases/2026FIN0031-001066",
 "bc_sum": "https://www2.gov.bc.ca/gov/content/safety/wildfire-status/about-bcws/wildfire-history/wildfire-season-summary",
 "bc_ptf": "https://www2.gov.bc.ca/assets/gov/public-safety-and-emergency-services/emergency-preparedness-response-recovery/embc/reports/premiers_task_force_on_emergencies_report-april2024.pdf",
 "bc_ptfpage": "https://www2.gov.bc.ca/gov/content/safety/emergency-management/emergency-management/about/em-taskforce",
 "ab_est": "https://open.alberta.ca/dataset/65514c30-e9f9-4951-9bae-7134edbe293c/resource/71713b5f-01ab-4ec5-9c01-7e49aec66fc1/download/budget-2026-estimates-government-2026-27.pdf",
 "ab_ar24": "https://open.alberta.ca/dataset/2dedbb29-e005-4802-bf6e-03bf77536add/resource/b86465e8-a8e3-45de-91d8-3fec19c700db/download/fp-annual-report-2023-2024.pdf",
 "ab_ar25": "https://open.alberta.ca/dataset/2dedbb29-e005-4802-bf6e-03bf77536add/resource/971986a2-35bb-4aa6-8316-05e3ba568a8a/download/fp-annual-report-2024-2025.pdf",
 "ab_ar26": "https://open.alberta.ca/dataset/2dedbb29-e005-4802-bf6e-03bf77536add/resource/db36b97e-fca3-4082-950b-4943de30687d/download/fp-annual-report-2025-2026.pdf",
 "ab_rs": "https://docs.assembly.ab.ca/LADDAR_files/docs/committees/rs/legislature_31/session_2/20260309_1900_01_rs.pdf",
 "ciffc25": "https://ciffc.ca/publications/ (CIFFC 2025 Annual Report / Canada Report 2025, file cr2025.pdf)",
 "sk_aud": "https://auditor.sk.ca/pub/publications/public_reports/2026/Volume%201/ch-05----saskatchewan-public-safety-agencyresource-planning-for-wildfire-response.pdf",
 "sk_mnp": "https://publications.saskatchewan.ca/api/v1/products/128921/formats/154702/download",
 "sk_resp": "https://publications.saskatchewan.ca/api/v1/products/128921/formats/154732/download",
 "sk_bud": "https://www.saskatchewan.ca/government/news-and-media/2026/march/18/$880-million-to-protect-saskatchewan-and-strengthen-community-safety",
 "mb_est": "https://www.gov.mb.ca/asset_library/en/budget2026/estimates_budget2026.pdf",
 "mb_pa26": "https://www.gov.mb.ca/asset_library/en/finances/annual-report-and-public-accounts-2025-26.pdf",
 "mb_reesi": "https://www.gov.mb.ca/asset_library/en/finances/reesi-2025-26.pdf",
 "mb_pa25": "https://www.gov.mb.ca/asset_library/en/proactive/20242025/publicaccounts/AnnualReportPublicAccounts2024-25.pdf",
 "mb_pa24": "https://manitoba.ca/asset_library/en/proactive/20232024/publicaccounts/AnnualReportPublicAccounts2023-2024.pdf",
 "mb_ar25": "https://www.gov.mb.ca/asset_library/en/annualreports/2024_2025/annual-report-nrif-24-25.pdf",
 "mb_ar26": "https://www.gov.mb.ca/asset_library/en/annualreports/2025_2026/annual-report-nrif-25-26.pdf",
 "mb_aar": "https://manitoba.ca/asset_library/en/wildfire/wildfire-report-april-2026.pdf",
 "mb_rel": "https://news.gov.mb.ca/news/print,index.html?item=73482",
 "nt_me": "https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2026-02/TD%20448-20%281%29%202026-2027%20Main%20Estimates.pdf",
 "nt_fr": "https://www.fin.gov.nt.ca/sites/fin/files/budget_2026-27_fiscal_review_paper.pdf",
 "nt_h": "https://www.ntlegislativeassembly.ca/sites/default/files/hansard/2025-11/HN251021_0.pdf",
 "nt_s24": "https://ntlegislativeassembly.ca/sites/default/files/legacy/tabled_document_-_fin_-_supplementary_estimates_operations_expenditures_no._2_2023-2024.pdf",
 "nt_s26": "https://www.ntlegislativeassembly.ca/sites/default/files/tabled-documents/2025-10/TD%20388-20%281%29%20Supplementary%20Estimates%20%28Operations%20Expenditures%29%20No%202%202025-2026.pdf",
 "nt_mnp": "https://www.gov.nt.ca/sites/flagship/files/documents/1._nwt_wildfire_response_review_report_and_appendices_final_compressed-9k.pdf",
 "nt_mnprel": "https://www.gov.nt.ca/en/newsroom/independent-review-recommends-improvements-wildfire-response-government-provides-responses",
 "nt_aar": "https://www.maca.gov.nt.ca/en/content/gnwt-response-2023-after-action-review-recommendations",
 "nt_air": "https://www.gov.nt.ca/ecc/en/services/wildfire-operations/air-tanker-fleet",
 "nt_det": "https://www.gov.nt.ca/ecc/en/services/wildfire-operations/detecting-wildfire",
 "nt_prep": "https://www.gov.nt.ca/en/newsroom/jay-macdonald-preparations-2026-wildfire-season",
 "nt_prep2": "https://www.gov.nt.ca/en/newsroom/jay-macdonald-preparedness-2026-wildfire-season",
 "yt_est": "https://yukon.ca/sites/default/files/fin-2026-27-budget-main-estimates-community-services.pdf",
 "yt_est25": "https://open.yukon.ca/information/2c63636e-348f-4529-8fe6-2c267e48e5b2/resource/55d25146-fef3-48fb-8266-3185baee5d67/download/fin-2025-26-budget-main-estimates-community-services.pdf",
 "yt_sup": "https://yukon.ca/en/news/supplementary-estimates-provide-update-previous-government-spending-and-plan-remainder-fiscal-year",
 "yt_spring": "https://open.yukon.ca/information/4bf375ef-ff94-444e-b951-d0b3fccc1b1a/resource/e221bc58-c562-4f92-b6eb-d26c5da9de6f/download/fin_spring_2026.pdf",
 "yt_rel": "https://yukon.ca/en/news/yukon-wildland-fire-management-ready-2026-fire-season",
 "yt_imp": "https://open.yukon.ca/information/1c3bd405-4e15-4b2d-9054-4e23c7eacaa4/resource/02114668-b64a-487c-b902-39990c65dfe2/download/cs-imported-initial-attack-crews-aircraft-assist-yukon-fire-response-06-21-2025.pdf",
 "nu_rel": "https://gov.nu.ca/en/newsroom/government-nunavut-and-canadian-interagency-forest-fire-centre-formalize-wildfire",
}

rows = []

# ---------------- BC ----------------
bc = dict(agency="British Columbia (BCWS)",
 budget_2026_27_cad=235702000, budget_basis="Estimates 2026/27, Vote 31 Fire Management (voted base); Budget 2026 fiscal plan carries $236M a year for 2026/27 to 2028/29",
 actual_2023_24_cad=1094880000, actual_2024_25_cad=769400000, actual_2025_26_cad=645112000,
 actual_basis="Actual: Ministry of Forests Annual Service Plan Reports, Fire Management line (estimated 204.1/232.7/238.0 + other authorizations = actual). 2026/27 forecast at Q1: $614M above budget",
 overrun_mechanism="Statutory spending above the voted base (Budget and Fiscal Plan lists 'Fire management costs' under 'Statutory spending'; service plan shows 'Other Authorizations' of $890.8M, $536.7M, $407.1M)",
 firefighters="~1,300 BCWS firefighters + ~1,200 contract personnel (2025); 700+ contract firefighter personnel arranged for 2026", firefighters_year="2025 (2026 contracts)",
 airtankers="28 fixed-wing aircraft in 8 tanker groups (2026); 27 airtanker and birddog aircraft engaged at 2025 peak; 36 in 2023",
 helicopters="Long-term 2026: 7 medium, 4 intermediate, 3 rappel medium, 4 heavy (18) + 2 parattack jumpships; ~120 call-when-needed carriers; 4 night-vision (doubled in 2025, 260 missions)",
 year_round_staff="600+ year-round positions (2026); 2024: ~500 permanent and 300 seasonal staff; 2025: 600 permanent and 300 seasonal support staff",
 detection_notes="Province-wide AI-assisted wildfire camera network in research/partnership stage (2025/26 service plan report); improved weather stations; night-vision helicopters used for detection",
 vacancies_or_outages="Not found in official record",
 review_name="Premier's Expert Task Force on Emergencies (summary of recommendations, April 2024); no BC Auditor General wildfire operations audit found",
 review_recs_total="31", review_recs_implemented="Not reported (page last updated 2024-04-04; Premier: 'Many ... are already underway')",
 ia_success_by_year="2023: 80% of wildfires contained at 5 ha or less; 2024: not stated; 2025: 85% contained under 4 ha",
 zone_policy_change="No change found in official record",
 imports_personnel="2023: ~1,750 out-of-province personnel; 2024: 3 out-of-province IMTs, ~600 resources requested via CIFFC (not all personnel); 2025: no count ('less need for out-of-province resource support')",
 stated_plans_2026_27="600+ year-round positions; record ~2,400 seasonal applications; $14M ground equipment; $21M Prince George depot; 10 more Type 2 structure-protection units; AI camera network",
 source_urls=";".join([U["bc_est"],U["bc_bfp"],U["bc_asr24"],U["bc_asr25"],U["bc_asr26"],U["bc_rel"],U["bc_q1"],U["bc_sum"],U["bc_ptf"],U["bc_ptfpage"]]))
bc["budget_pct_of_avg_actual"] = pct(235.702, [1094.88, 769.4, 645.112])
rows.append(bc)

# ---------------- AB ----------------
ab = dict(agency="Alberta (Alberta Wildfire, Forestry and Parks)",
 budget_2026_27_cad=169244000, budget_basis="2026-27 Government Estimates, Forestry and Parks 2.1 Wildfire Management (operating); 2.3 Presuppression and Response has no estimate (funded from the $2.0B government-wide Contingency vote, down from $4.0B in 2025-26); capital 2.1 $24.8M",
 actual_2023_24_cad=953605000, actual_2024_25_cad=858747000, actual_2025_26_cad=925549000,
 actual_basis="Actual (unaudited voted actuals, ministry annual reports): 2.1 + 2.3 operating, supplementary and contingency votes. 2023-24: 102.5+58.1+793.0; 2024-25: 156.6+246.7+455.4; 2025-26: 164.8+4.5+756.2",
 overrun_mechanism="Contingency vote (Treasury Board and Finance; $793.0M 2023-24, $455.4M 2024-25, $756.2M 2025-26) plus supplementary estimate ($246.7M 2024-25)",
 firefighters="2024: 544 helitack and unit crew seasonal personnel + 373 seasonal support; 2023: budget for up to 432 seasonal firefighters; Firetack: 38 contracts x 8 crew (2026, Hansard)", firefighters_year="2024",
 airtankers="18 ready in 2025 (4 owned, 14 contracted); 5 DHC-515 on order (~$400M, $120M deposit 2025-26), first by spring 2031",
 helicopters="2 hoist-equipped helicopters (2025); night-vision helicopters to total 7 in 2026 (3 added, minister in estimates committee)",
 year_round_staff="+192 FTEs in 2024 (Budget 2024 funded 100 new government firefighters); crews worked through winter 2024-25",
 detection_notes="Dispatch Lite mobile tool giving lookouts real-time detection data; infrared drones; radiosondes",
 vacancies_or_outages="Not found in official record",
 review_name="No post-2023 auditor general or independent review of Alberta Wildfire found (last OAG follow-up Nov 2021: 2 of 2 recs implemented)",
 review_recs_total="", review_recs_implemented="",
 ia_success_by_year="Contained by 10 a.m. next day (target 95%): 2021 95.3%, 2022 94.0%, 2023 87.2%, 2024 86.1% (first reported 88.5%), 2025 88.1%",
 zone_policy_change="No change found in official record",
 imports_personnel="2023: 4,231 firefighters and support personnel; 2024: not found; 2025: 1,086 (231 Canadian + 855 international; annual report says 'more than 1,085')",
 stated_plans_2026_27="Base wildfire funding ~$169M; expand night-vision fleet to 7, hoist program, infrared drones; $4.2M capital for wildfire apps; $125,000 municipal initial attack pilot; DHC-515 payments in later budgets",
 source_urls=";".join([U["ab_est"],U["ab_ar24"],U["ab_ar25"],U["ab_ar26"],U["ab_rs"],U["ciffc25"]]))
ab["budget_pct_of_avg_actual"] = pct(169.244, [953.605, 858.747, 925.549])
rows.append(ab)

# ---------------- SK ----------------
sk = dict(agency="Saskatchewan (SPSA)",
 budget_2026_27_cad=76300000, budget_basis="SPSA operating appropriation in 2026-27 Estimates (whole agency, not wildfire only; Provincial Auditor Figure 8). Government release: $140M for SPSA in 2026-27 incl. +$21.5M capital for Q400 airtankers",
 actual_2023_24_cad=98600000, actual_2024_25_cad=95200000, actual_2025_26_cad=351600000,
 actual_basis="Total wildfire costs by fire season 2023/2024/2025 (SPSA wildfire statistics reports via Provincial Auditor Figure 11); season, not fiscal year",
 overrun_mechanism="Special warrants and supplementary estimates after the season ($47.0M 2023-24, $53.7M 2024-25, $313.2M 2025-26; only 20% of 2025-26 operating funding approved before the season)",
 firefighters="Type 1 (agency): 226 positions, 23 vacant (Jan 2026); Type 2 (contracted): 410 positions; ~400 Type 2 used in 2025", firefighters_year="2026",
 airtankers="Owns 17 aircraft incl. 4 land-based airtankers (3 Convair 580A ~70 years old) and 6 CL-215T (~40 years old); buying 4 Dash 8-Q400 airtankers (~$187M over 4 years, 1st delivered 2025, 2nd due Q2 2026)",
 helicopters="8 long-term contracts + 36 short-term contracts used in 2025 (82 short-term contracts held); short-term = 85% of 23,971 hours",
 year_round_staff="Operations Division ~757 staff (367 FTE); all key positions seasonal except aircraft maintenance engineers",
 detection_notes="Detection towers in regional plans (no count found); 2024 review recommended exploring drones; 2025 review: 'accelerate ... advanced fire modelling and detection technologies'",
 vacancies_or_outages="Pilots 38 planned, 3 vacant; AMEs 36, 5 vacant; air attack officers 10, 2 vacant (Jan 2026); 2 CL-215T unavailable since Nov 2024",
 review_name="Provincial Auditor 2026 Vol 1 Ch 5 (11 recs); MNP Review of the 2025 Saskatchewan Wildfire Season (May 2026, 11 recs); SPSA 2024 season review (25 recs, 18 opportunities)",
 review_recs_total="11 (Auditor) + 11 (MNP 2025 review)", review_recs_implemented="Auditor: not yet reported (audit March 2026); MNP: province directed SPSA to implement all 11 with 'immediate actions' (June 2026); SPSA was not tracking 2024 review recs at March 2026",
 ia_success_by_year="Fires held under 10 ha (Auditor analysis): 2021 59%, 2022 77%, 2023 73%, 2024 76%, 2025 70%; SPSA does not track it",
 zone_policy_change="No change found in official record (response prioritized by values at risk)",
 imports_personnel="2023: 0 personnel (2 aircraft); 2024: 112 personnel; 2025: 916 personnel (823 CIFFC + 52 Northwest Compact + 41 Great Plains) and 12 aircraft",
 stated_plans_2026_27="Q400 airtanker replacement; FireSmart grants up to $40,000; community wildfire reservists; five-year local vendor procurement; jurisdictional scan of SPSA structure; base capital increase of $1.5M denied for 2026-27",
 source_urls=";".join([U["sk_aud"],U["sk_mnp"],U["sk_resp"],U["sk_bud"]]))
sk["budget_pct_of_avg_actual"] = pct(76.3, [98.6, 95.2, 351.6])
rows.append(sk)

# ---------------- MB ----------------
mb = dict(agency="Manitoba (Manitoba Wildfire Service)",
 budget_2026_27_cad=56648000, budget_basis="Estimates 2026/27: 25.4(c) Manitoba Wildfire Service $42.716M + 25.4(d) Wildfire Suppression $13.932M; separate all-hazard Emergency Expenditures vote $50.0M (unchanged)",
 actual_2023_24_cad=53509000, actual_2024_25_cad=55037000, actual_2025_26_cad=229000000,
 actual_basis="Actual. 2023-24 and 2024-25: NRIF annual report, MWS + Wildfire Suppression only (all-hazard Emergency Expenditures were $29M and $30M; wildfire share not separated). 2025-26: Public Accounts, emergency wildfire suppression $175M + NRIF wildfire costs $54M (total 2025 response incl. evacuees $321M)",
 overrun_mechanism="Emergency Expenditures vote plus special warrants ($350M for wildfire response in 2025-26 enabling appropriations)",
 firefighters="+19 firefighters and 3 new initial attack crews funded in Budget 2026; 244 emergency firefighters certified 2025-26 (228 in 2024-25)", firefighters_year="2026",
 airtankers="3 DHC-515 ordered ($80M down payment) to replace CL-215s 'in service for nearly 40 years'; first delivery 2031; owned fleet count not found",
 helicopters="Long-term contract intermediate and medium helicopters (count not given); casual-hire intermediate hours 12,628 in 2025 vs 3,045 in 2024",
 year_round_staff="Manitoba Wildfire Service 58.20 FTEs (2024-25 and 2025-26)",
 detection_notes="$1.2M over three years for weather information and fire mapping systems",
 vacancies_or_outages="Variance notes cite 'filling of vacancies' (no count)",
 review_name="2025 Wildfire After Action Review (interim April 2026; final with recommendations due fall 2026, third-party analysis by Alberta Emergency Management Agency)",
 review_recs_total="Final not yet published (interim lists actions only)", review_recs_implemented="Not applicable yet",
 ia_success_by_year="Not found in official record",
 zone_policy_change="No change found in official record",
 imports_personnel="2025: 1,509 (CIFFC: 1,214 firefighters + 176 IMT/support; Great Lakes Compact: 103 firefighters + 16 IMT/support) plus 8 airtankers; 2023-2024: not found",
 stated_plans_2026_27="19 firefighters, 3 IA crews, new Thompson initial attack base (negotiation), Grace Lake bunkhouse, $1.1M aerial firefighting services, $1.2M weather/mapping, value protection trailers",
 source_urls=";".join([U["mb_est"],U["mb_pa26"],U["mb_reesi"],U["mb_pa25"],U["mb_pa24"],U["mb_ar25"],U["mb_ar26"],U["mb_aar"],U["mb_rel"]]))
mb["budget_pct_of_avg_actual"] = pct(56.648, [53.509, 55.037, 229.0])
rows.append(mb)

# ---------------- NT ----------------
nt = dict(agency="Northwest Territories (ECC Wildfire)",
 budget_2026_27_cad=65622000, budget_basis="2026-27 Main Estimates, ECC Wildlife and Forest Management: Forest Management program (fire presuppression, suppression and forest resources; fire-only line not split). 2025-26 Main was $51.4M. Government also raised its supplementary reserve from $35M to $210M",
 actual_2023_24_cad=127000000, actual_2024_25_cad=61000000, actual_2025_26_cad=94064000,
 actual_basis="2023-24 and 2024-25: wildfire suppression actuals stated by Finance Minister in Hansard 2025-10-21 (pp. 2796 to 2797, official Hansard PDF). 2025-26: Forest Management revised estimate (appropriation, not actual) incl. $39.5M suppression shortfall. Mixed basis",
 overrun_mechanism="Supplementary appropriations for 'fire suppression shortfall' ($75.0M 2023-24, $39.5M 2025-26)",
 firefighters="134 wildland firefighters in 2023 (46 GNWT + 22 four-person contract crews), down from 165 in 1991", firefighters_year="2023",
 airtankers="10 airtankers (8 AT-802A Fire Boss, 2 L-188 Electra) + 4 bird dogs; ownership not stated",
 helicopters="Not found in official record",
 year_round_staff="Not found in official record",
 detection_notes="5 lookout stations; 50 ECC weather stations",
 vacancies_or_outages="2023 review: 'understaffing'; untrained crews deployed before first training session",
 review_name="NWT 2023 Wildfire Response Review (MNP, Aug 2024, ECC wildfire operations); separate 2023 After-Action Review on emergency response (35 recs)",
 review_recs_total="25 recommendations + 17 opportunities for improvement (MNP); 35 (AAR)", review_recs_implemented="MNP: GNWT responded to all, 'implementation ... is ongoing' (no count); AAR: 1 of 35 complete (Oct 2025)",
 ia_success_by_year="Not found in official record",
 zone_policy_change="No change found; Forest Fire Management Policy 23.03 'directs ECC to allow wildfires to burn' unless values at risk",
 imports_personnel="2023: 568 personnel (review main text; appendix says 31 crews/620 people + 102 overhead via CIFFC); 2024-2025: not found",
 stated_plans_2026_27="Territorial Wildfire Centre in Fort Smith (groundbreaking 2026); territorial WUI program; 2 more structure protection trailers (6 total); 7 new duty officers; $1.6M FireSmart work",
 source_urls=";".join([U["nt_me"],U["nt_fr"],U["nt_h"],U["nt_s24"],U["nt_s26"],U["nt_mnp"],U["nt_mnprel"],U["nt_aar"],U["nt_air"],U["nt_det"],U["nt_prep"],U["nt_prep2"]]))
nt["budget_pct_of_avg_actual"] = pct(65.622, [127.0, 61.0, 94.064])
rows.append(nt)

# ---------------- YT ----------------
yt = dict(agency="Yukon (Wildland Fire Management)",
 budget_2026_27_cad="", budget_basis="2026-27 Main Estimates Fire Management O&M column not legible in extracted PDF (yukon.ca blocks download); 2025-26 Main Estimate was $30.812M; government holds a $100M 2026-27 contingency covering 'fires or floods'",
 actual_2023_24_cad=38308000, actual_2024_25_cad=47449000, actual_2025_26_cad=63927000,
 actual_basis="Community Services Main Estimates, Protective Services Fire Management O&M: 2023-24 actual (2025-26 book), 2024-25 actual and 2025-26 forecast (2026-27 book, read via WebFetch); 2025-26 = forecast",
 overrun_mechanism="Supplementary estimates ($33.7M for wildfire response in 2025-26 Supplementary Estimates No. 1); contingency",
 firefighters="26 crews (Government of Yukon + Yukon First Nations contract crews) and 92 staff managing crews and aircraft", firefighters_year="2026",
 airtankers="2 contracted airtanker groups (2026)", helicopters="Contracted (count not given)",
 year_round_staff="Not found in official record",
 detection_notes="Six regional bases; public Fire Line; no detection counts found",
 vacancies_or_outages="Not found in official record",
 review_name="No post-2023 auditor or independent review of Wildland Fire Management found",
 review_recs_total="", review_recs_implemented="",
 ia_success_by_year="2025: 87% of full-response fires contained before 1.5 ha (CIFFC 2025 report, Yukon section); other years not found",
 zone_policy_change="No change found; 2025 fires: 62 full response, 7 modified, 89 monitored",
 imports_personnel="2025: 8 initial-attack crews and 1 large airtanker from BC Wildfire (June 2025; personnel count not given); 2023-2024 not found",
 stated_plans_2026_27="26 crews, 2 contracted airtanker groups; Whitehorse South fuel break (60% complete end 2025); community wildfire protection plans",
 source_urls=";".join([U["yt_est"],U["yt_est25"],U["yt_sup"],U["yt_spring"],U["yt_rel"],U["yt_imp"],U["ciffc25"]]))
yt["budget_pct_of_avg_actual"] = ""
rows.append(yt)

# ---------------- NU ----------------
nu = dict(agency="Nunavut",
 budget_2026_27_cad="", budget_basis="No wildfire suppression budget line found; Department of Community Services is responsible",
 actual_basis="", overrun_mechanism="",
 firefighters="", airtankers="", helicopters="", year_round_staff="", detection_notes="",
 vacancies_or_outages="", review_name="", review_recs_total="", review_recs_implemented="", ia_success_by_year="",
 zone_policy_change="", imports_personnel="",
 stated_plans_2026_27="Joined CIFFC June 8, 2026 for mutual aid, ICS training and FireSmart; no standalone suppression program found",
 source_urls=U["nu_rel"])
rows.append(nu)

COLS = ["agency","budget_2026_27_cad","budget_basis","actual_2023_24_cad","actual_2024_25_cad","actual_2025_26_cad","actual_basis","budget_pct_of_avg_actual","overrun_mechanism","firefighters","firefighters_year","airtankers","helicopters","year_round_staff","detection_notes","vacancies_or_outages","review_name","review_recs_total","review_recs_implemented","ia_success_by_year","zone_policy_change","imports_personnel","stated_plans_2026_27","source_urls"]
with open(os.path.join(OUT, "agencies_west.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in COLS})

# ---------------- gaps ----------------
G = [
 ("British Columbia (BCWS)","Base budget covers about a quarter of what fire seasons cost","Fire Management ... 665 236 236 236 ... Current year costs are already well above the 20 year average.","BC Budget and Fiscal Plan 2026/27",U["bc_bfp"]),
 ("British Columbia (BCWS)","2026 season already forecast $614M over the voted fire budget","The fire-management expenditures are forecast to be $614 million higher than the budget.","BC First Quarterly Report 2026/27 release",U["bc_q1"]),
 ("British Columbia (BCWS)","Task force called for readiness for more frequent extreme seasons and more firefighting tools","maintain a proactive operational posture that is prepared for more frequent extreme seasons","Premier's Expert Task Force on Emergencies",U["bc_ptf"]),
 ("British Columbia (BCWS)","Workforce pipeline named as a gap","strengthening recruitment and career pathways for wildfire and emergency management","Premier's Expert Task Force on Emergencies",U["bc_ptf"]),
 ("British Columbia (BCWS)","No public progress count on the 31 task force recommendations","Many of the task force's 31 recommendations are already underway","Premier's Expert Task Force summary (Premier's message); page last updated 2024-04-04",U["bc_ptfpage"]),
 ("Alberta (Alberta Wildfire, Forestry and Parks)","Response money is never in the budget; it comes from a shared contingency that was halved for 2026-27","CONTINGENCY 4,000,000 3,114,244 2,000,000 (2025-26 Budget, Forecast, 2026-27 Estimate, $000)","Alberta 2026-27 Government Estimates",U["ab_est"]),
 ("Alberta (Alberta Wildfire, Forestry and Parks)","Missed its 10 a.m. containment target three seasons running","The 2025 wildfire season result of 88.1 per cent was below the 95 per cent target.","Forestry and Parks Annual Report 2025-26",U["ab_ar26"]),
 ("Alberta (Alberta Wildfire, Forestry and Parks)","New government airtankers will not arrive until 2031","The first aircraft is to arrive by spring 2031.","Forestry and Parks Annual Report 2025-26",U["ab_ar26"]),
 ("Alberta (Alberta Wildfire, Forestry and Parks)","Heavy reliance on imported crews in big years","4,231 firefighters and support personnel imported from around the world","Forestry and Parks Annual Report 2023-24",U["ab_ar24"]),
 ("Saskatchewan (SPSA)","Budget does not include expected firefighting costs","exceeded the Agency's initial budget by more than $70 million a year over each of the last three years","Provincial Auditor 2026 Vol 1 Ch 5",U["sk_aud"]),
 ("Saskatchewan (SPSA)","Same staffing plan every year despite bigger seasons","It continues to plan for the same number of key personnel each year even though the number and magnitude of fires have grown","Provincial Auditor 2026 Vol 1 Ch 5",U["sk_aud"]),
 ("Saskatchewan (SPSA)","Aging airtankers, two out of service","Two of these planes have not been available since November 2024 due to repairs.","Provincial Auditor 2026 Vol 1 Ch 5",U["sk_aud"]),
 ("Saskatchewan (SPSA)","Firefighter and aviation vacancies","Type 1 Firefighters 226 [positions] 23 [vacancies] (2026); Aircraft Maintenance Engineers 36 / 5","Provincial Auditor 2026 Vol 1 Ch 5, Figure 5",U["sk_aud"]),
 ("Saskatchewan (SPSA)","Imported help arrives late and costs more","It took on average 15 days for external personnel (e.g., firefighters) to arrive and deploy to fires","Provincial Auditor 2026 Vol 1 Ch 5",U["sk_aud"]),
 ("Saskatchewan (SPSA)","Initial attack success falling and not tracked","in 2022 the Agency had an initial attack success rate of 77% compared to 70% in 2025","Provincial Auditor 2026 Vol 1 Ch 5",U["sk_aud"]),
 ("Saskatchewan (SPSA)","Not ready for a 2025-scale season; late hiring","it was not fully prepared for a wildfire season of the scale and complexity seen in 2025","MNP Review of the 2025 Saskatchewan Wildfire Season",U["sk_mnp"]),
 ("Saskatchewan (SPSA)","Recruitment and training start after the season begins","Recruitment, training and onboarding begin late, often after the fire season has already started.","MNP Review of the 2025 Saskatchewan Wildfire Season",U["sk_mnp"]),
 ("Saskatchewan (SPSA)","Unfilled permanent roles due to funding","Persistent funding constraints for permanent FTE positions have led to critical roles going unfilled","MNP Review of the 2025 Saskatchewan Wildfire Season",U["sk_mnp"]),
 ("Manitoba (Manitoba Wildfire Service)","Base budget a fraction of a bad year; emergency vote stayed at $50M","EMERGENCY EXPENDITURES ... 50,000 50,000 (2026/27 and 2025/26, $000)","Manitoba Estimates of Expenditure 2026/27",U["mb_est"]),
 ("Manitoba (Manitoba Wildfire Service)","2025 overrun needed special warrants","$350 million in additional operating expenditure authority for enabling appropriations to accommodate costs related to wildfires","Manitoba Annual Report and Public Accounts 2025-26",U["mb_pa26"]),
 ("Manitoba (Manitoba Wildfire Service)","Aging water bombers; replacements years away","replace aging Canadair CL-215 water bombers that have been in service for nearly 40 years ... first aircraft will be delivered in 2031","NRIF Annual Report 2025-26",U["mb_ar26"]),
 ("Manitoba (Manitoba Wildfire Service)","System tested beyond capacity in 2025","The response tested existing plans, systems, and capacity across Manitoba's emergency management framework.","2025 Wildfire Interim After Action Review",U["mb_aar"]),
 ("Manitoba (Manitoba Wildfire Service)","Final review and recommendations set for fall 2026","A comprehensive final report, including validated findings and recommendations, will be completed in fall 2026.","2025 Wildfire Interim After Action Review",U["mb_aar"]),
 ("Northwest Territories (ECC Wildfire)","Fewer firefighters than in 1991","The number of wildland firefighters in the NWT has declined for the past 32 years","NWT 2023 Wildfire Response Review (MNP)",U["nt_mnp"]),
 ("Northwest Territories (ECC Wildfire)","Depends on imported crews and specialists","highlighted the NWT's reliance on imported resources, including crews, and specialist support","NWT 2023 Wildfire Response Review (MNP)",U["nt_mnp"]),
 ("Northwest Territories (ECC Wildfire)","Untrained crews deployed early in season","resulted in untrained crews being deployed and previously trained crews being pulled from active duty","NWT 2023 Wildfire Response Review (MNP)",U["nt_mnp"]),
 ("Northwest Territories (ECC Wildfire)","Aircraft shortages and mismatched aircraft","difficulties were encountered in matching aircraft type to requirements, with inadequate aircraft often dispatched","NWT 2023 Wildfire Response Review (MNP)",U["nt_mnp"]),
 ("Northwest Territories (ECC Wildfire)","Firefighting budget set below recent costs and topped up later in the year","Obviously if we under budget, then we come back to the Assembly for supplementary appropriation (Finance Minister; base budget almost $21M in 2023-24 and $24.3M in 2024-25, against actual costs of $127M and $61M)","NWT Hansard, October 21, 2025, p. 2797",U["nt_h"]),
 ("Northwest Territories (ECC Wildfire)","1 of 35 recommendations from the 2023 after-action review completed by October 2025","GNWT response timeline: #23 completed; others ongoing or not yet started (Oct 2025)","GNWT Response to 2023 After-Action Review",U["nt_aar"]),
 ("Yukon (Wildland Fire Management)","Fire budget set well below recent costs and topped up mid-year","$33.7 million for costs related to wildfire response (2025-26 Supplementary Estimates No. 1)","Yukon government release 2025-12-09",U["yt_sup"]),
 ("Yukon (Wildland Fire Management)","Relied on imported crews in 2025","Eight initial-attack crews and a large airtanker have arrived in the Yukon from BC Wildfire","Yukon Wildland Fire Management bulletin 2025-06-21",U["yt_imp"]),
 ("Nunavut","No territorial suppression capacity found; joined CIFFC only in 2026","formalizes Nunavut's membership in the Canadian Interagency Forest Fire Centre (June 8, 2026)","Government of Nunavut release",U["nu_rel"]),
]
with open(os.path.join(OUT, "gaps_west.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["agency","gap","evidence","source_name","url","accessed"])
    for a,g,e,s,u in G:
        w.writerow([a,g,e,s,u,ACC])

# ---------------- manifest ----------------
M = [
 ("raw/bc/for_asr_2023_2024.pdf (.txt)",U["bc_asr24"],"Fire Management estimated/other authorizations/actual"),
 ("raw/bc/for_asr_2024_2025.pdf (.txt)",U["bc_asr25"],""),
 ("raw/bc/for_asr_2025_2026.pdf (.txt)",U["bc_asr26"],"2025-26 actual $645.1M; night-vision fleet; camera network"),
 ("raw/bc/premiers_task_force_2024.pdf (ptf.txt)",U["bc_ptf"],"31 recommendations per Premier's message (32 'recommended' statements in text)"),
 ("(WebFetch)",U["bc_rel"],"2026 readiness release, 2026-03-16"),
 ("(WebFetch) + ../../data/smoke-cost/raw/spending/bc/bc_season_summary.html.txt",U["bc_sum"],"season summaries 2023-2025; page updated 2026-01-02"),
 ("(WebFetch)",U["bc_ptfpage"],"no implementation status; last updated 2024-04-04"),
 ("../../data/smoke-cost/raw/spending/bc/est2026.txt, bfp2026.txt (reused)",U["bc_est"]+" ; "+U["bc_bfp"],"Vote 31 $235.702M; fiscal plan $236M/yr"),
 ("raw/ab/est2627.pdf (.txt), est2627.xlsx",U["ab_est"],"2.1 Wildfire Management $169.244M; contingency $2.0B"),
 ("raw/ab/rs_20260309.pdf (rs.txt)",U["ab_rs"],"Standing Committee on Resource Stewardship, Forestry and Parks estimates, 2026-03-09"),
 ("../../data/smoke-cost/raw/spending/ab/fp-annual-report-2023-2024/2024-2025/2025-2026.txt (reused)",U["ab_ar26"],"voted actuals, IA measure, imports, airtankers"),
 ("(WebFetch)","https://www.oag.ab.ca/reports/wildfire-management-processes-for-prevention-and-review-and-improvement-aoi/","2021 follow-up; 2 of 2 implemented (pre-2023)"),
 ("NOT USED (reprint)","https://kutd.awna.com/releases/start-of-2026-wildfire-season-minister-loewen/","Pointer only; alberta.ca original not found; figures confirmed instead in Hansard"),
 ("../../data/smoke-cost/raw/spending/sk/sk.txt (reused)",U["sk_aud"],"Provincial Auditor chapter: vacancies, fleet, IA, imports, budget"),
 ("raw/sk/pubsask_128921.pdf (rev2025.txt)",U["sk_mnp"],"MNP review of 2025 season, dated 2026-05-22, 11 recommendations"),
 ("raw/sk/pubsask_128921_154732.pdf (immediate.txt)",U["sk_resp"],"Province response table, June 2026"),
 ("(WebFetch)",U["sk_bud"],"$140M SPSA, +$21.5M capital, Q400s"),
 ("raw/mb/estimates_budget2026.pdf (est2026.txt)",U["mb_est"],"MWS $42.716M, suppression $13.932M, emergency $50M"),
 ("raw/mb/annual-report-and-public-accounts-2025-26.pdf (.txt)",U["mb_pa26"],"wildfire cost breakdown 2025-26; special warrants"),
 ("raw/mb/reesi-2025-26.pdf (.txt)",U["mb_reesi"],"Emergency Expenditures detail"),
 ("raw/mb/AnnualReportPublicAccounts2024-25.pdf, AnnualReportPublicAccounts2023-2024.pdf",U["mb_pa25"]+" ; "+U["mb_pa24"],"Emergency Expenditures $30M (2024-25), $29M (2023-24)"),
 ("raw/mb/annual-report-nrif-24-25.pdf (.txt)",U["mb_ar25"],"MWS actuals 2023-24/2024-25"),
 ("raw/mb/annual-report-nrif-25-26.pdf (nrif2526.txt)",U["mb_ar26"],"imports 2025, DHC-515, aircraft hours"),
 ("raw/mb/wildfire-report-april-2026.pdf (war.txt)",U["mb_aar"],"Interim AAR"),
 ("(WebFetch)",U["mb_rel"],"Interim AAR release 2026-04-21"),
 ("raw/nt/main_est_2026_27.pdf (me.txt)",U["nt_me"],"Forest Management $65.622M"),
 ("raw/nt/budget_2026-27_fiscal_review_paper.pdf (.txt)",U["nt_fr"],"supplementary reserve $35M to $210M; wildfires cut 2025-26 surplus $60M"),
 ("raw/nt/mnp_review.pdf (mnp.txt)",U["nt_mnp"],"25 recs + 17 OFIs; 134 firefighters; 568 imports"),
 ("../costs-full/raw/gov/nt/HN251021.pdf (.txt)",U["nt_h"],"Official Hansard, October 21, 2025: Finance Minister on the fire budget and supplementary appropriations, pp. 2796 to 2797"),
 ("(WebFetch)",U["nt_aar"],"35 recs response counts"),
 ("(WebFetch)",U["nt_air"]+" ; "+U["nt_det"],"fleet and lookouts; no update date"),
 ("(WebFetch)",U["nt_prep"]+" ; "+U["nt_prep2"],"2026 minister statements; no dates on page"),
 ("../../data/smoke-cost/raw/spending/nt/*.pdf (reused)",U["nt_s24"]+" ; "+U["nt_s26"],"supplementary appropriations"),
 ("(WebFetch only; curl blocked by Cloudflare)",U["yt_est"],"Fire Management row; 2026-27 estimate column not legible"),
 ("raw/yt/est2526.pdf (.txt)",U["yt_est25"],"2023-24 actual $38.308M; 2025-26 estimate column not legible"),
 ("raw/yt/fin_fall_2025.pdf (fall25.txt)","https://open.yukon.ca/information/1f39f8cb-c1ce-4fd9-85c1-f859fc636456/resource/8749bd2c-6f4b-44dc-8996-4b896279a219/download/fin_fall_2025.pdf","$33.7M wildfire response"),
 ("(WebFetch)",U["yt_sup"]+" ; "+U["yt_spring"]+" ; "+U["yt_rel"]+" ; "+U["yt_imp"],"Yukon releases and briefing notes"),
 ("../policy/raw/ciffc/cr2025.pdf -> raw/cr2025.txt, cr2025_raw.txt",U["ciffc25"],"agency sections 2025"),
 ("(WebFetch)",U["nu_rel"],"Nunavut joins CIFFC 2026-06-08"),
]
with open(os.path.join(OUT, "manifest_west.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["file","url","accessed","notes"])
    for a,u,n in M:
        w.writerow([a,u,ACC,n])
print("ok")
for r in rows:
    print(r["agency"], r.get("budget_pct_of_avg_actual"))
