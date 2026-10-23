# People costs, second round: the gaps closed (2023 to 2026)

Checked 2026-10-22 (follow-up pass the same day). Dollars are 2025 CAD (CPI all-items, same basis and conventions as `health_costs.csv`; fiscal-year spending counts as the season year). No death counts or death values are used anywhere in this round. The first round's 2024 to 2026 health rows used a death-based scaling ratio; they are replaced here.

Files: `health2_costs.csv` (47 rows, same columns as `health_costs.csv`; 37 rows carry dollars), `health2_manifest.csv` (58 sources), helper tables `health2_aqbat_counts.csv`, `health2_aqbat_backtest.csv`, `health2_aqbat_province_shares.csv`, `health2_health_unit_costs.csv`, `health2_health_costs_by_province.csv`, `health2_days_away_events.csv`, `health2_lost_wages_by_year.csv`, `health2_ei_excess_claims.csv`. Scripts: `scripts/health2_01_aqbat_rebuild.py`, `scripts/health2_02_people_costs.py` (stops if any quoted number is missing from its saved source), `scripts/health2_03_manifest.py`. Downloads: `raw/health2/`.

## What changed in the follow-up pass

- Nova Scotia $500 payments: no official record of the total exists in any document reached, so the row is now additive = no. The news-relayed $3.6M is no longer used; the row shows an estimate built from official inputs, for reference only.
- NWT: travel and income support now use the audited 2023-24 Public Accounts actuals ($6.110M and $3.684M); new rows for the GNWT's $0.4M United Way fire relief grant, the $0.212M 2024-25 evacuation relief payments (Fort Good Hope) and the $2.279M business support (a transfer, not added). Supplementary Estimates No. 3 2023-24 was found: it only raised borrowing authority by $120M. No GNWT document splits the $204.6M by purpose; official components now cover 33% of it.
- Ontario: Ontario's own records replace the per-evacuee estimates: its expense line "First Nations Emergency Evacuations on behalf of Indigenous Services Canada" (2026 Budget) and ISC's payments to Ontario (Public Accounts of Ontario: $214.9M in FY2025-26).
- Days away 2023: official dates for Alberta (Drayton Valley, Fox Creek, Edson twice), Nova Scotia (Upper Tantallon, Shelburne County) and BC's August surge (official counts of people on order). The first version's Alberta "7 days or more" payment rule is dropped: the saved official record (SCSS annual report 2023-24) says eligibility was set by postal code and does not state a 7-day rule.

## Scorecard

| Gap | Result (2025 CAD) | Additive |
|---|---|---|
| 1. Evacuees 2026 | at least 22,194; central 30,022 (no national count exists) | count |
| 1. Evacuation cost 2026, off reserve (BC, NWT) | estimate $42.1M ($16.7M to $50.2M) | yes |
| 1. Evacuation cost 2026, First Nations (ISC) | estimate $128.0M (to $137.1M; floor 0) | partial |
| 1. Ontario 2026 First Nations evacuations for ISC | $136.6M official outlook, mostly spring floods | no |
| 2. Alberta 2025 evacuation payments | $4.6M official | yes |
| 2. Alberta 2023 Red Cross match | $8.0M ($7.7M to $8.0M) | yes |
| 2. Nova Scotia 2023 Red Cross match | $5.2M ($4.8M to $5.2M) | yes |
| 2. Nova Scotia 2023 $500 payments | no official total; estimate from official inputs $5.4M ($4.5M to $5.8M) | no (not counted) |
| 2. Manitoba 2025 Red Cross match | $7.9M ($6.9M to $8.9M) | no (inside MB's $80M) |
| 2. Quebec 2023 evacuee benefit | $13.1M official (to $14.0M) | yes |
| 2. Ontario First Nations evacuations for ISC, wildfire share | 2023 $2.0M ($1.1M to $3.3M); 2024 $0 (under $0.5M); 2025 $162.9M ($126.7M to $195.7M) | no (inside ISC in gov_) |
| 2. NWT travel support, final | $6.4M official (replaces $2.6M partial) | yes |
| 2. NWT income support, final | $3.8M official | no (replaces wages) |
| 2. GNWT United Way fire relief grant 2023 | $0.42M official | partial (low and central) |
| 2. NWT evacuation relief 2024 (Fort Good Hope) | $0.22M official | partial (low and central) |
| 2. NWT business support for the 2023 evacuation | $2.4M official | no (transfer) |
| 2. GNWT $204.6M split | 33% identified in official records ($68.4M nominal) | no (reference) |
| 3. Days away 2023 and 2024 | 2023: 12.5 days for 110,843 people in 19 events (NWT 22.0; Alberta, Nova Scotia, BC 8.8); 2024: 17.5 days (4 events, 17,118 people) | input |
| 3. Lost work revised (2023, 2024, 2026) | $345.3M ($227.5M to $482.9M) | yes (replaces) |
| 3. EI claims tied to wildfires | 2024: 3,054 official; 2023 NWT +646; 2025 MB +1,919 to +3,278 | count |
| 4. Health care 2024 to 2026, rebuilt | hospital $11.8M ($2.3M to $27.9M) | yes (replaces) |
| 4. Physician fees 2023 to 2026 | $3.2M ($1.1M to $8.1M) | yes |
| 4. Quebec and provincial unit costs, 2023 | +$0.09M | yes |
| 5. Health system costs of evacuations | $2.1M (Quebec $1.9M, Alberta $0.2M) | yes |

People costs after this round, counted once (first round plus this round, replaced rows removed):

| Line | Low ("at least") | Central | High | First round central |
|---|---|---|---|---|
| Health care | $7.7M | $25.4M | $53.3M | $17.4M |
| Evacuations | $433.5M | $587.6M | $950.1M | $382.2M |
| Lost work and wages | $310.0M | $464.2M | $653.9M | $446.2M |
| **Total** | **$751.3M** | **$1,077.2M** | **$1,657.3M** | **$845.8M** |

By season, central (low to high): 2023 $530.5M ($436.4M to $903.4M); 2024 $85.2M ($68.2M to $143.0M); 2025 $256.3M ($214.8M to $364.1M); 2026 $205.2M ($31.9M to $246.8M). 2026 central is mostly the ISC estimate ($128.0M).

How to combine without double counting: when adding `health2_costs.csv`, drop these first-round rows: the three "scaled from Health Canada 2023" health rows (2024, 2025, 2026), the three "Lost work and wages" rows for 2023, 2024 and 2026, and the partial NWT Evacuation Travel Support row. Partial rows: ISC 2026 counts in central and high only (like the gov_ ISC tier C estimate); the GNWT United Way grant and the 2024 NWT evacuation relief count in low and central only (the first-round GNWT high-case remainders already hold them). `combine_bill.py` was not changed.

## Gap 1: evacuations in 2026

**Count.** No national 2026 total is published (the CWFEDB summary ends at 2025; Public Safety Canada's June, July and August 2026 updates give none). Official pieces: BC, more than 20,000 people evacuated at once on August 8 (EMCR bulletin 2026-08-21; Public Safety says more than 10,000 were still under order on August 18); ISC, 8,805 First Nations people on reserve evacuated April 1 to October 2; NWT, Fort Simpson (1,100 in 2021) and Wrigley (117); Eabametoong (977 on reserve) was airlifted by the Canadian Armed Forces. Low 22,194 (BC + NWT + Eabametoong), central 30,022 (BC + ISC + NWT, assuming no overlap; BC's count includes some on-reserve people). BC's is a peak count, so the season total is higher.

**Days away found.** Fort Simpson 20 days (June 28 to July 18); Wrigley at least 25 (ordered June 29, still out July 24); Summerland ordered August 8, last listed downgrades August 16. Not enough for a national mean; the lost-work rows keep 7 / 12.5 / 18 days.

**Official 2026 costs.** None is wildfire-specific yet. Ontario's 2026-27 first quarter adds $140.0M nominal for "First Nations Emergency Evacuations on behalf of Indigenous Services Canada", fully federally funded and mostly the spring floods (information to June 30, before the July fire evacuations in northwestern Ontario); reference only. BC's first quarter keeps Emergency and Disaster Management Act spending at the $36M budget (to June 30, before the Okanagan fires); Manitoba's first quarter shows Emergency Expenditures $277M over budget, mostly June rains and floods, with the 2026 wildfire response included but not split; Saskatchewan shows no wildfire variance; Alberta's $104.7M is firefighting.

**Estimates.**
- First Nations (ISC, FY2026-27): 8,805 evacuees x ISC's wildfire response reimbursement per First Nations evacuee in the two previous years ($15,961 in FY2024-25: $294.4M x 26/31 / 15,469; $13,837 in FY2025-26: $688.6M x 73/81 / 44,852). Central $131M nominal, high $141M; floor 0, as for gov_'s ISC estimate. The per-evacuee rates may run high because the evacuee counts stop in August or September.
- Off reserve (BC, NWT): 21,217 evacuees x cost per evacuee from earlier official totals: Alberta 2025 payments $807 (low), BC's 2023 EMCR payments per person under order $2,034 ($118.6M / 24,300 households / 2.4 people per household; central), Manitoba 2025 evacuee costs $2,424 (high).

**Ontario and Sandy Lake.** Sandy Lake First Nation was evacuated in June 2025, so it sits in Ontario's 2025 figures (below), not 2026.

**Open, documents searched:** BC 2026 Q2 report (late November); ISC FY2026-27 EMAP statistics (mid-2027); Ontario 2026 annual report (2027); Manitoba, Saskatchewan and Alberta Q2 reports; ISC 2026 page (no days away). Searched: Public Safety Canada 2026 updates (June, July, August), ISC 2026 page, GNWT July 2026 bulletins, BC EMCR 2026 bulletins and RDOS updates, Ontario, BC, Manitoba, Saskatchewan and Alberta 2026-27 first-quarter reports.

## Gap 2: earlier evacuation costs

| Item | Result | Method and source |
|---|---|---|
| Alberta 2025 Emergency Evacuation Payments | $4.6M to over 4,500 Albertans (about 5,700 evacuated) | official: Alberta Assisted Living and Social Services Annual Report 2025-26 (ministry renamed from SCSS) |
| Alberta 2025 HARP approvals (high case only) | $37.1M (Grande Prairie $1.7M, Swan Hills and MD of Opportunity $4.3M, four counties $31.1M) | official: PSES Annual Report 2025-26; same treatment as the first round's 2023 DRP remainder |
| Alberta 2023 Red Cross match | $7.63M nominal (low $7.4M) | estimate: Alberta matched every dollar (Public Safety release 2023-05-11) in the same May 8 to June 6 window as Ottawa, and Public Safety counted $7,626,270 raised in it; low = the Red Cross's report of Alberta matching received. Alberta's own payment record was not found |
| Nova Scotia 2023 Red Cross match | $5.01M nominal (low $4.6M) | estimate: one-for-one commitment (NS release 2023-06-06) x $5,005,180 raised in the window (Public Safety); low = Red Cross report |
| Nova Scotia $500 per evacuated household | NOT COUNTED (additive = no). Reference estimate $5.2M nominal ($4.3M to $5.5M): about 10,410 households (8,663 to 11,053) | no official total exists in any document reached, and the only reported figure ($3.6M to 7,200 households by mid-June 2023) is a Red Cross statement relayed by CTV News, so it cannot be used. Estimate from official inputs: the rule (NS release 2023-05-29) x households = evacuees / Census 2021 people per occupied dwelling: 16,400 Upper Tantallon (HRM post incident analysis) / 2.31 (Halifax) + nearly 7,000 Shelburne County (same report) / 2.12 (county municipalities); low = "about 20,000" (NS release 2023-06-06) / 2.31; high = 23,400 / 2.12; assumes every eligible household was paid |
| Manitoba 2025 Red Cross match | $7.9M nominal ($6.9M to $8.9M) | estimate: match of every dollar for 30 days from May 28, cap $15M (MB release 2025-06-04), x donations in the window interpolated from the Red Cross's dated totals ($3.3M June 6, $8.9M July 9, $9.0M July 25). Not additive: it most likely sits inside Manitoba's audited $80M evacuee costs |
| Quebec 2023 evacuee benefit | more than $12,522,000 nominal paid on more than 8,911 claims (high 8,911 x $1,500) | official: MSP Rapport annuel de gestion 2023-2024, p. 13; $1,500 per evacuated principal residence per evacuation |
| Ontario First Nations evacuations on behalf of ISC | official all-hazard figures: Ontario expense $11M (2023-24 actual), $0M (2024-25 actual, rounded), $227M (2025-26 interim); ISC's payments to Ontario $93,432 (FY2023-24), $13,308,513 (FY2024-25), $214,949,965 (FY2025-26 actual). Wildfire share, nominal: 2023 $1.9M ($1.0M to $3.2M); 2024 $0 (under $0.5M); 2025 $162.9M ($126.7M to $195.7M) | ESTIMATE of the wildfire share: wildfire evacuees / all evacuees (2023: more than 600 of 3,519; 2025: 8,387 of 11,069, Ontario annual reports), low and high assuming the flood evacuees were hosted twice or half as long. 2025 cost: central = ISC's payments (Public Accounts of Ontario 2025-26, MEPR Statement of Revenue, p. 2-131), low = Emergency Management Ontario operating expense above its estimate ($270.9M - $63.2M), high = the 2026 Budget interim ($227M; Table 3.10). Not additive: ISC reimburses Ontario in full, inside gov_'s ISC estimate. Ontario added $99.3M (fall statement) and $50.7M (third quarter) for these evacuations during 2025-26 |
| NWT travel support, final | $6,110 thousand (8,712 applications paid) | official: GNWT Public Accounts 2023-24, Schedule 5 (grants, Finance); counts from Tabled Document 31-20(1) ($6,061,850 at 2024-02-14); replaces the first-round partial $2.5M |
| NWT income disruption support, final | $3,684 thousand (4,817 applications) | same sources; income replacement, so not added |
| GNWT United Way NWT fire relief grant | $400 thousand (unbudgeted) | official: Public Accounts 2023-24, Schedule 5; partial (inside the first-round GNWT high-case remainder); the federal match of United Way NWT donations is a separate federal payment in gov_ |
| NWT Emergency Evacuation Relief Program, FY2024-25 | $212 thousand | official: Public Accounts 2024-25, Schedule 5; the only NWT evacuation that fiscal year was Fort Good Hope (June to July 2024, EM Annual Report 2025); partial (inside the first-round 2024 GNWT remainder) |
| NWT business support for the 2023 evacuation (ITI) | $2,279 thousand, 50% funded by CanNor | official: GNWT 2025-26 Main Estimates, ITI cost shared agreements (2023-24 actuals); a transfer that compensates business losses, so not added (econ_ treats business supports the same way) |
| GNWT 2023-24 appropriations | Supplementary Estimates No. 2 (TD 967-19(2), Aug 28, 2023): fire suppression $75.0M; No. 3 (TD 974-19(2), Sept 27, 2023): borrowing authority +$120M "to accommodate unplanned expenditures as a result of fire related emergencies", no spending items; No. 4 (TD 29-20(1)): fire suppression $24.3M, ETSP $6.0M, MACA "2022 flood and 2023 wildfire response and recovery" $55.153M, ITI $1.0M. No special warrants in 2023-24. MACA received $91.645M of federal transfers labelled "2023 Wildfire" in 2023-24 (money that reimburses GNWT costs, most likely DFAA payments; not a separate cost) | reference |
| GNWT $204.6M split | components in official records $68.4M nominal (33%): Alberta's hosting cost recovered from the NWT $41.6M (Alberta 2023-24 revenue), ETSP $6.11M, EIDS $3.68M, United Way grant $0.40M, ITI business support $2.28M, community claims of Yellowknife $13.34M and Hay River $0.96M (audited, as in gov2_). About $136M remains unsplit (other community claims, recovery projects, GNWT department costs) | reference; the high-case adjustment is now -$6.69M nominal (-$7.0M) for the larger final ETSP and EIDS |

**Open, documents searched:**
- Nova Scotia $500 total (still open; row not counted): NS news releases 2023-05-29, 06-06, 06-22, 2023-09-28 (first budget update), 2024-07-26 (Public Accounts 2023-24) and the 22 daily wildfire updates of 2023-05-29 to 06-12 (they point to HRM and the Shelburne EMO for evacuation details); Summary of Additional Appropriations September 2023, December 2023 and February 2024; Accountability Reports 2023-24 of Municipal Affairs and Housing (EMO spent $91.2M against a $12.9M estimate, "$78.3M in partly recoverable Disaster Assistance relief for flooding and wildfires", no split) and of Labour, Skills and Immigration (no wildfire item); NS Public Accounts 2023-24 Supplementary Information (`pa-supplementary-2024.pdf`): notices.novascotia.ca resets every shell connection and WebFetch returned only pages 1 to 28 (the Municipal Affairs and Housing section starts at page 246); the Red Cross Nova Scotia appeal update of 2025-03-31 (appeal funds only, the provincial payments are not in it); nslegislature.ca (connection reset; the Public Accounts Committee transcript request was not approved, not retried).
- Alberta's own record of the 2023 match: Alberta grant payments disclosure 2023-24, 2024-25, 2025-26 (Red Cross payments listed are Pakistan relief, recovery operations and operating grants only); Blue Book supplier payments 2023-24 to 2025-26 (none); PSES 2023-24 annual report (names the match, no amount).
- Manitoba's matching payment: Manitoba release and Disclosure of Contracts (first round); the federal 2025 Manitoba agreement is not in the saved federal disclosure pages and search.open.canada.ca rejects requests.
- Ontario: closed with Ontario's own records. The wildfire share is an estimate because Ontario reports the line for all hazards. The Public Accounts of Canada Volume III route was not needed (tpsgc-pwgsc.gc.ca fails TLS in the shell; not retried).
- GNWT split by purpose: Supplementary Estimates No. 2, 3 and 4 2023-24; TD 31-20(1); TD 1007-19(2); Public Accounts 2023-24 and 2024-25 Section II; Main Estimates 2024-25, 2025-26 and 2026-27; NWT 2023 Wildfire Response Review (MNP, July 2024); EM Annual Report 2025 (Table 7 lists remaining recovery work, not costs by purpose); web search for a return to a written question on the costs (none found). No document splits the $204.6M.

## Gap 3: days away, lost work, EI and hours

**Days away (official start and end dates, evacuee-weighted; `health2_days_away_events.csv`).**
- 2023, NWT: 12 evacuations (MACA chronology, Tabled Document 1007-19(2); 2021 Census populations): 31,765 people, 22.0 days (Yellowknife area 21, Hay River 35, Fort Smith 37, Behchokǫ̀ 10).
- 2023, Alberta (Alberta Emergency Alerts archive, official alert pages with issue and update times): Drayton Valley (7,291) 12 days, whole town ordered May 4 at 23:09, order lifted May 16 at 13:54; Fox Creek (1,639) 18 days, May 6 to May 24; Edson (8,374) twice: 3 days (May 5 at 17:37 to May 8 at 08:16) and 6 days (June 9 at 18:22 to the downgrade on June 15 at 18:05).
- 2023, Nova Scotia: Upper Tantallon area 16,400 people (HRM post incident analysis, 2024): ordered May 28; the province said on June 6 that many had returned as orders were lifted (9 days, central and low); all properties reopened June 14 (17 days, high). Shelburne County, nearly 7,000 people: evacuations in place by May 29 and still for part of the county on June 8; orders lifted by noon June 9 (NS releases): 11 days.
- 2023, BC August surge: people on evacuation order 30,000 (Aug 20), more than 15,000 (Aug 26), 4,200 (Aug 31), about 370 (Sept 14) (BC releases); person-days by straight lines between these counts, starting at 30,000 on August 18 when the provincial state of emergency was declared: 275,000 person-days, 9.2 days per person on order on August 20 (7.2 low, without the two days before the first count).
- Outside the NWT, 79,078 people in these events averaged 8.8 days; all dated 2023 events together, 110,843 people, 12.5 days.
- 2024: Jasper residents 26 days, Labrador City (9,600) 10 days, Bunibonibee (about 2,400) 30 days, Fort Good Hope (380) 21 days: 17,118 people, 17.5 days.
- 2025: Ontario's 8,387 wildfire evacuees were hosted about one month; ESDC: orders lasted more than 18 days on average.
- Revised inputs for lost work: 2023 days 9.4 / 12.5 / 16.0 (dated events at their own days, the other 121,516 evacuees at 7 / 12.5 / 18); 2024 days 12.0 / 14.6 / 17.8. 2026 evacuees 22,194 / 30,022 / 30,022 (first round 20,847).

**Lost work and wages, revised (same formula and earnings as the first round):** 2023 $265.8M ($179.3M to $338.9M; first round $265.5M; the first version of this round $283.6M), 2024 $47.9M ($33.8M to $93.2M; was $41.1M), 2026 $31.5M ($14.4M to $50.9M; was $20.8M). 2025 unchanged ($118.9M).

**EI claims (counts only, transfers).** Official: more than 3,054 EI applications linked to the 2024 season by 2024-09-09, about half from Jasper (ESDC; Gazette RIAS). Estimates from StatCan Table 14-10-0005 (initial claims received, unadjusted, minus the same months in other years): NWT August and September 2023, about 646 extra claims (1,100 against 454); Manitoba June 2025, 1,919 to 3,278 extra (8,200 against 4,922; the lower figure removes the 28% June 2025 rise seen in eight other provinces). No clear signal for Alberta 2023, Nova Scotia 2023, BC 2023 or Labrador 2024.

**Hours lost.** No official count exists: the LFS mentions wildfires only in text, and public LFS tables give no absence-by-reason detail by province and month.

**Open, documents searched:**
- Quebec 2023 end dates (more than 15,000 evacuated by June 9, 2023 per the MSP release; 8,911 benefit claims): MSP annual report 2023-24 (no dates), quebec.ca program releases of 2023-06-09 and 2024-06-23, web searches for MSP and municipal notices on Chibougamau, Lebel-sur-Quévillon, Chapais and Sept-Îles (news reports only, which cannot be used). These evacuees stay at 7 / 12.5 / 18 days.
- Other Alberta 2023 events (Swan Hills, Valleyview, Little Red River Cree Nation, Sturgeon Lake, East Prairie and Peavine): not looked up event by event; they stay at the default days. Alberta's payment rule ("7 days or more") is not stated in the saved official record (SCSS annual report 2023-24: eligibility "largely determined by evacuee postal code"); the Alberta government's May 2023 release on the payments was not found on alberta.ca, and a republished copy (farms.com) was not fetched (request not approved; not retried).
- BC events before August 2023 (Fort St. John area in May, Tumbler Ridge in June) and the August orders by community: BC releases give province-wide counts only; a search for Central Okanagan emergency operations notices returned news reports only; Columbia Shuswap pages were not searched.
- Fort McMurray and Fort Nelson 2024: RMWB's post returns 404; Fort Nelson dates found only in news.
- National means for 2023 and 2024: CWFEDB event data are restricted (readme saved: "not publicly available in its full form").
- Searched before: CWFEDB summary, MACA chronology, NL releases, Canada Gazette, NWT EM annual report, Ontario annual reports, ESDC QP notes, StatCan 14-10-0005, LFS Daily releases (12), NWT Bureau of Statistics LFS pages (404).

## Gap 4: health care, rebuilt for 2024 to 2026

**Method.** For each Health Canada outcome k and season y: S(k, y) = sum over dissemination areas of the outcome's population weight x the share of days covered x (1 - exp(-beta_k x the May-September mean increment)). AQBAT applies its coefficients to seasonal means, and so does this. Coefficients and age groups are Health Canada's (Matz et al. 2026, Table S.1: respiratory ED visits and admissions 0.75% per 10 ug/m3, cardiac 0.71%, asthma symptom days 6.54% in ages 5 to 19, child bronchitis 9.34%, restricted activity days 4.93% and acute respiratory symptom days 2.66% in ages 5 and up). Ages 5 to 19 come from the 2021 Census by DA. Count(k, y) = Health Canada's 2023 count x S(k, y) / S(k, 2023): one national baseline rate per outcome, set so that our 2023 exposure reproduces Table 1 exactly. Manitoba, Newfoundland and Labrador and the NWT have no monitors in 2025 and 2026; their exposure is imputed from neighbours (central: mean of SK and ON for MB, QC and NS for NL, AB and YT for the NWT; high: the highest neighbour; low: none). This adds 6% in 2025 and 3% in 2026.

**Back-test.** The same anchoring predicts Health Canada's own 2019 to 2022 numbers within a factor of 0.58 to 1.66 (Health Canada divided by ours): 2019 about 0.63, 2020 about 0.79, 2021 about 1.6, 2022 about 0.59. Our exposure over-predicts light years and under-predicts 2021, a summer of late smoke; on average it runs 20% high. The range for 2024 to 2026 combines Health Canada's 2023 95% interval with this error band (in quadrature, log scale).

| Season | Ratio to 2023 | Respiratory ED | Cardiac ED | Respiratory admissions | Cardiac admissions |
|---|---|---|---|---|---|
| 2023 (Health Canada) | 1 | 1,700 | 610 | 350 | 460 |
| 2024 | 0.378 | 642 (346 to 1,159) | 231 (100 to 425) | 132 (67 to 221) | 174 (78 to 326) |
| 2025 | 0.674 | 1,145 (582 to 2,117) | 411 (168 to 777) | 236 (112 to 404) | 310 (131 to 595) |
| 2026 | 0.390 | 663 (346 to 1,206) | 238 (100 to 443) | 137 (67 to 230) | 179 (78 to 339) |

The first round's death-based ratios were 0.244, 0.604 and 0.272. Other outcomes (asthma symptom days, bronchitis, restricted activity days, symptom days) and Health Canada's welfare valuation are rebuilt as reference rows ($327M, $582M, $338M central; not spending).

**Unit costs (by province; `health2_health_unit_costs.csv`).** Visits and stays are split by province with each province's share of S (2025: Ontario 43%, Quebec 21%, Alberta 19%; 2026: Ontario 51%).
- ED, hospital: CIHI direct cost per visit, new data tables (FY2024-25 for 2024 to 2026: Canada excluding Quebec and Nunavut $251.9; FY2023-24: $241.6), times 1.929 for full cost, as in the first round.
- ED, Quebec: MSSS AS-471 2023-24, centre 6240 L'urgence, 25 establishments with 3.40 million visits: $287.38 direct cost per visit ($978.1M / 3.40M), against CIHI's $241.6 elsewhere. Quebec's FY2024-25 reports were not parsed; the FY2023-24 cost is carried forward by CPI.
- Stays: CIHI Patient Cost Estimator FY2021-22 by jurisdiction, which includes Quebec (respiratory $8,951, cardiac $9,488 per typical stay).
- Physician fees: CIHI publishes no cost per ED visit. Estimate: one hospital-outpatient assessment per visit at the National Physician Database FY2023-24 fee-for-service cost per service (Canada: other assessment $44.40 low, major assessment $83.51 central, major assessment plus out-of-hours special call $190.41 high; provincial values used). Stays: the Patient Cost Estimator's physician cost per typical stay (AB, BC, MB, NL, NS, ON, SK; others use the pooled value, about $951 respiratory and $1,178 cardiac). Fee-for-service only; doctors on alternative payment plans are assumed to cost the same per service.

**Health care results.** Hospital costs: 2024 $3.2M ($0.7M to $7.5M), 2025 $5.5M ($1.1M to $13.1M), 2026 $3.1M ($0.6M to $7.3M); these replace the first-round $2.0M, $5.0M and $2.2M. The 2023 re-costing with provincial and Quebec unit costs adds $0.09M (new 2023 hospital total $8.3M). Physician fees add $1.35M for 2023 and $0.52M, $0.87M and $0.51M for 2024 to 2026. Our own all-cause ED estimate stays a footnote, as in the first round.

**Open:** respiratory and cardiac ED and admission counts by province (CIHI data request); Quebec AS-471 2024-25; MUHC, CHU Sainte-Justine, IUCPQ, Nunavik and Cree Board AS-471 codes (not found by probing codes 1104-0000 to 1104-7500).

## Gap 5: health system and mental health costs of evacuations

- Quebec, 2023 (audited AS-471 2023-24): CRSSS de la Baie-James claimed $806,421 for the forest-fire emergency (several towns evacuated); CIUSSS du Saguenay-Lac-Saint-Jean received $338,713 of MSSS "feux de forêt" funding; CISSS de la Côte-Nord booked $712,687 for "feux de forêt". Total $1.86M nominal, additive.
- Alberta Health Services, 2023: $521,553 for the NWT evacuation (inside Alberta's $44.3M hosting row, not added) and $157,847 for the northwest Alberta fire (added).
- Mental health: no official dollar figure found. ISC pays evacuee mental wellness supports inside EMAP (in gov_). Searched: NWT Supplementary Estimates No. 2 and No. 4 2023-24 (no Health and Social Services wildfire item), NWT 2023 Wildfire Response Review, Manitoba 2025 after-action review (supports described, no dollars), ISC QP notes, Alberta grant payments 2023-24 to 2025-26 ("2023 AB Spring Wildfires - GOARI" $0.92M and $1.26M, recipients withheld, so not classed as health), the 25 Quebec AS-471 reports.

## Counting once

1. Replacements: listed under the scorecard. The first-round 2023 Health Canada-based hospital rows stay; the 2023 adjustment and physician rows add to them.
2. ISC: the 2023 to 2025 ISC estimate stays in gov_ (tier C; refined in gov2_). Ontario's First Nations evacuation rows and Manitoba's matching are reference rows because ISC or Manitoba's audited $80M already hold them. The 2026 ISC estimate is new (gov_ stops at FY2025-26) and is kept out of the floor; Ontario's 2026-27 line sits inside it.
3. Red Cross: federal matches are in gov_; provincial matches here are a different payer. Alberta's match may also sit inside the $175M 2023 DRP figure that the first round uses in the high case only. Nova Scotia's $500 payments are not counted at all (no official total); if a figure is found later it would add, but it also sits inside Nova Scotia's EMO 2023-24 disaster assistance line (gov2_, reference).
4. GNWT: the United Way grant, the 2024 evacuation relief, Yellowknife and Hay River (gov2_) count in low and central only, because the first-round high case already holds the GNWT remainders; the high-case adjustment (-$7.0M) removes the final ETSP and EIDS from that remainder. Business support and the federal "2023 Wildfire" transfers are not costs of their own.
5. Income transfers (NWT EIDS, EI, NWT and Jasper business supports) stay out; living-cost payments (Alberta, Quebec, NWT travel and relief) do not overlap lost wages.
6. DFAA stays out, as in the first round (the Quebec health claim, Nova Scotia's costs and the GNWT's costs are partly recovered through it).
7. The 2026 off-reserve estimate uses BC's peak count, which includes some First Nations evacuees also in ISC's count; the overlap is small next to the range.

## Access notes

- Blocked or failing: notices.novascotia.ca (shell connection reset; WebFetch returns only pages 1 to 28 of the roughly 390-page supplement), search.open.canada.ca (request rejected), tpsgc-pwgsc.gc.ca (TLS verification failure; WebFetch not approved), nslegislature.ca (connection reset; WebFetch not approved), farms.com copy of an Alberta release (WebFetch not approved), redcross.ca 2025 Manitoba page (WebFetch not approved; Red Cross media updates were read with WebFetch and its PDFs downloaded), StatCan WDS (reset; full-table CSV worked), canada.ca (curl times out; read with WebFetch), RMWB 2024 news post (404), alberta.ca without "www" (TLS failure; www.alberta.ca works). None was retried after a refusal.
- OpenNWT Hansard and CTV were used only as pointers; no value comes from news.
