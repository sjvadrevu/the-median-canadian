# People costs of the 2023 to 2026 wildfires: health care, evacuations, lost work

Checked 2026-10-22. All dollars are 2025 CAD (CPI all-items annual mean, the bill's basis; 2026 = January to September mean; spending reported by fiscal year counts as the season year, as in the bill and `gov_costs.csv`). Deaths and value-of-life numbers are excluded.

Files: `health_costs.csv` (48 rows; `additive` = yes on 26), `health_ed_by_province_year.csv`, `health_hc_morbidity_costs.csv`, `health_lost_wages_by_year.csv`, `health_manifest.csv` (40 sources). Scripts: `scripts/health_01_ed_costs.py`, `scripts/health_02_people_costs.py` (checks every quoted figure against the saved source file and stops on a mismatch), `scripts/health_03_manifest.py`. Downloads: `raw/health/`.

## Scorecard: additive totals, counted once against gov_ and econ_

| Line | Low ("at least") | Central | High |
|---|---|---|---|
| Health care (hospital costs of smoke illness) | $4.4M | $17.4M | $31.1M |
| Evacuations (government evacuee support) | $382.2M | $382.2M | $697.2M |
| Lost work and wages (evacuated workers) | $247.7M | $446.2M | $682.6M |
| **Total people costs** | **$634.3M** | **$845.8M** | **$1,410.9M** |

By season (central; low and high in brackets):

| Season | Health care | Evacuations | Lost work | Total |
|---|---|---|---|---|
| 2023 | $8.2M ($2.1M to $14.7M) | $222.5M (to $520.4M) | $265.5M ($133.8M to $382.3M) | $496.1M |
| 2024 | $2.0M ($0.5M to $3.6M) | $33.4M (to $40.9M) | $41.1M ($19.8M to $94.0M) | $76.4M |
| 2025 | $5.0M ($1.3M to $8.9M) | $126.4M (to $135.9M) | $118.9M ($82.6M to $171.0M) | $250.2M |
| 2026 (partial) | $2.2M ($0.6M to $4.0M) | none found | $20.8M ($11.6M to $35.3M) | $23.0M |

Memo, counted once in `gov_costs.csv`, not here: Indigenous Services Canada (ISC) on-reserve response reimbursements, wildfire share, $1,192.1M for FY2023-24 to FY2025-26 (gov_ tier C, an estimate kept outside the floor). They are mostly First Nations evacuation costs. If the slide shows them under "evacuations", move them from gov_, do not copy them. Also in gov_: Public Safety Canada Red Cross matching and Humanitarian Workforce agreements ($21.4M).

Suggested bill lines: "Health care and evacuations: $0.40B (at least $0.39B; high $0.73B)" and "Lost work and wages: $0.45B ($0.25B to $0.68B)". For an "at least" total, add the low column ($0.63B).

## Recommendation for the public slide (health)

Use Health Canada's numbers, not ours. Health Canada (Matz et al. 2026, GeoHealth, Table 1, AQBAT) estimates that wildfire smoke in 2023 caused about **2,300 extra emergency visits** (1,700 respiratory and 610 cardiac; 95% range 1,520 to 3,190), **810 extra hospital admissions** (350 respiratory, 460 cardiac; 480 to 1,140) and **1.1 million asthma symptom days in children** aged 5 to 19 (240,000 to 2,000,000). At CIHI's average costs those visits and stays cost hospitals **about $8 million in 2023** ($2M to $15M), and about $17 million for 2023 to 2026 once later years are scaled. Say "at least $4 million" if a floor is needed.

Why: it is an official, government-authored, peer-reviewed estimate with national coverage and a standard method. Our own estimate (174,000 extra all-cause emergency visits in 2023 to 2025) rests on one significant fit of six (all-months fit -0.18%), and Health Canada's own Ontario study of June 2023 found a rise in asthma visits (+23.6%) but none in other respiratory, heart or non-cardiorespiratory visits. Our central figure ($83M) should not appear on the slide; at most a footnote: "our own analysis of hospital records hints at more emergency visits, but the signal is weak."

On the slide, say the dollar figure is hospital costs only. Health Canada puts a welfare value of $820M (2023 dollars; $150M to $2.0B) on 2023's non-fatal smoke illness, including pain, suffering and restricted activity days. That is not spending and is not added.

## Method by item

### Health care

- **2023, Health Canada counts x CIHI unit costs (additive).** Emergency visits: CIHI direct cost per ED visit, FY2023-24, Canada excluding Quebec and Nunavut, $241.6 (Spending Trends in Health Service Delivery data tables, 2025, Table 4.1). CIHI's full hospital cost per visit (adds imaging, laboratory, housekeeping, administration) was $304 against a direct $158 in 2018-19 (CIHI 2020), a ratio of 1.929, giving $466.0. Low = low count x direct cost; central and high = full cost. Admissions: CIHI Patient Cost Estimator, Canada, FY2021-22 (latest), average hospital cost per typical stay, volume-weighted over the main medical case mix groups: respiratory $7,489 (COPD, viral and bacterial pneumonia, asthma, respiratory infections, influenza; range $3,482 to $10,491), cardiac $7,758 (heart failure, arrhythmia, heart attack, unstable angina, chest pain, all without angiogram; range $2,742 to $9,797). Low = low count x cheapest group, high = high count x dearest group. Unit prices go to 2025 dollars with fiscal-year CPI. Physician fees are excluded (CIHI hospital costs exclude physician pay; no national physician cost per visit was found).
- **2024 to 2026, scaled (additive, estimate).** Health Canada has published no morbidity numbers after 2023. The 2023 cost is multiplied by the ratio of our AQBAT net smoke burden in each year to 2023, on the 9 provinces with data every year (modelled acute deaths 88.2, 218.8 and 98.4 against 362.1): 0.244, 0.604, 0.272. Support for this: our 2023 AQBAT figure (379 deaths) matches Health Canada's (400). Manitoba, NL, NWT and Nunavut have no monitors in 2025 and 2026, so those years are low.
- **Our own all-cause ED estimate (not additive, suggestive only).** 174,131 visits (16,587 to 329,059) x CIHI province costs: $4.1M low, $83.3M central, $157.4M high ($43.2M at direct cost only). Detail in `health_ed_by_province_year.csv`. Coverage: AB BC MB NS ON PE QC SK YT; 2025 without MB and NS; CIHI NACRS covers about 75% of ED visits in BC, MB and PE.
- **Admissions in our own analysis:** none estimated (no open baseline by province); no counts invented.
- **Other Health Canada outcomes, 2023 (reference):** 12,000,000 acute respiratory symptom days (0 to 25,000,000), 22,000 child acute bronchitis episodes (0 to 50,000), 6,800,000 restricted activity days (4,100,000 to 9,400,000); acute morbidity valuation $820M in 2023 dollars ($857M in 2025 dollars).
- **Health Canada and Public Health Ontario study (reference):** Chen H, Kaufman JS, Chen C, et al. CMAJ 2025;197:E465-77, doi:10.1503/cmaj.241506. Ontario, June 2023: asthma ED visits +23.6% (95% CI 13.2% to 34.9%) one day after the early June smoke, for up to 5 days; no effect detected on other outcomes in either episode; no absolute excess published.

### Evacuations

People evacuated (NRCan Canadian Wildland Fire Evacuation Database, summary v2026-02-03): **232,359 in 2023** (282 evacuations), **56,423 in 2024** (91), **86,574 in 2025** (197). 2026 has no national count; official partial counts are 8,805 First Nations people on reserve (ISC, to October 2) and the whole District of Summerland (12,042 residents in 2021; order of 2026-08-08). Other statements: over 200,000 in 2023 (Public Safety), about 85,000 by early September 2025 with orders lasting more than 18 days on average (ESDC), more than 33,000 Manitobans in 2025 (Manitoba), about 17,550 Albertans in 2024 (Alberta), about 11,500 Saskatchewan evacuees given direct or financial support in 2025 (SPSA).

Additive items (all official totals, so low = central; nominal amounts shown):

| Item | Nominal | Source |
|---|---|---|
| Alberta Emergency Evacuation Payments 2023: over 37,000 evacuees | $47.1M | SCSS Annual Report 2023-24, p. 17 |
| Alberta Emergency Evacuation Payments 2024: 12,273 Albertans | $12.6M | SCSS Annual Report 2024-25, p. 18 |
| Alberta costs of hosting more than 20,000 NWT evacuees, 2023 | $44.3M | PSES Annual Report 2023-24, p. 37 |
| NWT Evacuation Travel Support, to 2023-09-05 (partial) | about $2.5M | GNWT release 2023-09-07 ($3.1M with income support, minus 800 x $750) |
| BC EMCR payments for 2023 interface fires (FY23-24 to FY25-26) | $118.6M | EDMA s.10(2) payment reports |
| BC EMCR payments for 2024 interface fires | $20.0M | same |
| BC EMCR payments for 2025 interface fires (first year) | $5.4M | same |
| Saskatchewan evacuation support FY2023-24 | $0.89M | Hansard, Sask. IAJ committee, 2025-12-01 |
| Saskatchewan 2025: hotels $13M, food $3.2M, adult payments $9.8M, Red Cross $15M | $41.0M | same |
| Manitoba evacuee related costs 2025 | $80M | Public Accounts 2025-26, p. 12 (audited) |
| Manitoba Red Cross contract 2024 | $0.05M | Disclosure of Contracts |

High case only (event costs that governments do not split between evacuation, response and recovery): GNWT estimated costs not itemized above, 2023 $157.2M ($204.6M minus Alberta hosting and travel and income support), 2024 $7.4M, 2025 $9.5M (NWT Emergency Management Annual Report 2025); Alberta 2023 Disaster Recovery Program $127.9M ($175M minus the evacuation payments).

Reference only (not additive): ISC EMAP response (in gov_); Public Safety Red Cross matching (Alberta 2023 $7.49M, Nova Scotia 2023 $5.01M) and Labrador 2024 shelter ($0.69M) (in gov_); Red Cross recovery agreements (Alberta 2024 $12.62M, Saskatchewan 2025 $2.82M, NL 2025 $2.65M; transfers toward property losses); Manitoba Red Cross contracts 2025 ($52.9M, inside the $80M); NWT income support ($0.6M, replaces wages); EI disaster pilot for Jasper and Bunibonibee ($4.3M benefits, replaces wages).

Notes: BC's EMCR payments include Emergency Support Services plus local authority and First Nation response and some recovery (EMCR does not split them). Alberta and Saskatchewan payments are for shelter, food, clothing and transport, not income.

### Lost work and wages

Formula, per season: evacuees x employed persons per resident x days away x 5/7 workdays x (average weekly earnings / 5).

| Input | 2023 | 2024 | 2025 | 2026 (partial) |
|---|---|---|---|---|
| Evacuees (central) | 232,359 | 41,161 | 86,574 | 20,847 |
| First Nations on reserve (lower employment) | 0 (low: 63,899) | 15,469 | 44,852 | 8,805 |
| Employed per resident (LFS 15+ / population) | 0.508 | 0.504 | 0.505 | 0.505 |
| Days away: low / central / high | 7 / 12.5 / 18 | 7 / 12.5 / 18 | 12.5 / 18 / 21 | 7 / 12.5 / 18 |
| Average weekly earnings (SEPH) | $1,204.92 | $1,260.20 | $1,302.86 | $1,336.35 |
| Workdays lost (central) | 1.05M | 0.16M | 0.46M | 0.08M |

Total workdays lost: 1.75M central (0.97M to 2.67M).

Assumptions, each stated:
- Evacuees: NRCan CWFEDB. 2024 removes Jasper non-residents: central 20,000 evacuated (ESDC) minus 4,738 residents (2021 Census); low uses Public Safety's 25,000; high removes none. 2026 is only ISC plus Summerland.
- Workers: national employed persons (LFS, ages 15+) divided by total population (July 1 estimates), so children and retirees are allowed for. First Nations evacuees on reserve get 0.636 of that ratio (2021 Census employment rate, ages 25 to 64: 47.1% on reserve, 74.1% non-Indigenous). ISC counts are used where published (2024, 2025, 2026); 2023 has none, so the central uses no adjustment and the low applies the long-run CWFEDB share of 27.5%.
- Days away: CWFEDB 1980 to 2021 recorded 7.2 million person-days for 576,747 evacuees, 12.5 days each (central); the median evacuation lasted 7 days (low); ESDC's 2025 average order length of more than 18 days is the high for other years and the central for 2025, with 21 days as the 2025 high (about 30% of 2025 orders lasted 21 days or more). Cross-checks: Yellowknife (20,340 residents) was out 21 days (2023-08-16 to 09-06); Jasper 26 days (2024-07-22 to 08-17); Bunibonibee 30 days (2024-08-13 to 09-12); over 37,000 Albertans were away 7 days or more in 2023.
- Earnings: SEPH average weekly earnings including overtime, all employees, Canada, annual (2026: January to July mean); one workday = one fifth of a week; calendar days x 5/7.
- The loss is gross work time lost, whoever bears it (worker or employer). Not modelled: remote work and paid leave (would lower it); self-employed income at employee rates; workers outside evacuation zones whose workplaces closed, and smoke-related absences (would raise it).
- No official estimate of hours lost exists: the LFS Daily releases for May 2023 to August 2026 mention wildfires but give no count; ESDC reported over 3,054 EI applications linked to the 2024 season by 2024-09-09.

## Double counting: how each overlap is handled

1. **DFAA.** gov_ keeps DFAA orders non-additive (they are the federal share of provincial costs). The provincial evacuation rows here are gross provincial costs, so they can be added as long as DFAA stays out of the total.
2. **ISC.** ISC reimburses provinces, host communities and the Red Cross for First Nations evacuees. ISC EMAP response is counted once, in gov_ tier C, outside the floor. If tier C is added, part of Manitoba's $80M and Saskatchewan's $41M may be counted twice (share not published).
3. **Red Cross.** Federal matching and workforce agreements are counted in gov_; recovery agreements are reference everywhere. Provincial money to the Red Cross is counted here only for Saskatchewan ($15M pledge) and inside Manitoba's $80M.
4. **Lost wages and evacuation payments.** Payments that replace income (EI, the EI pilot, NWT income support, Nova Scotia's Emergency Relief Grant) are transfers and are not added. Payments for living costs (Alberta, Saskatchewan) are counted as evacuation costs; they do not overlap lost wages.
5. **Lost wages and the wider economy.** econ_ GDP-loss and production rows (Alberta oil and gas shut-ins 2023 and 2025, accommodation, rail, iron ore, forestry) include wages of evacuated workers in those sectors. The overlap could not be quantified from public data. Count those wages once: if both are added, say the total overlaps for those sectors, or use the low end of lost wages.
6. **Insured losses.** econ_ insured losses include additional living expenses of evacuated policyholders; that is a different payer for the same kind of cost as government evacuee support. Mark it if the econ_ property adjustment is used.
7. **Health.** The Health Canada-based rows and our own ED estimate measure the same visits; only the Health Canada-based rows are additive. Health Canada's valuation includes medical costs and restricted activity days, so it is added to neither health care nor lost work.
8. **High-case remainders.** GNWT and Alberta remainders include response and recovery, which may overlap property and infrastructure lines and gov_ firefighting; they appear only in the high case.

## Could not find

Health care:
- Health Canada morbidity estimates for 2024, 2025 or 2026; BC Centre for Disease Control or Alberta Health reports with counts of smoke-related emergency visits.
- Open counts of respiratory and cardiac ED visits and admissions by province and month (a CIHI data request would be needed).
- CIHI ED cost per visit after FY2023-24 and for Quebec; Patient Cost Estimator after FY2021-22; physician fees per ED visit or stay; medicines, clinic visits and mental health costs.

Evacuations:
- A national 2026 evacuee count; national average days away for 2023 and 2024.
- Alberta 2025 evacuation payments (SCSS 2025-26 annual report not found).
- Provincial Red Cross matching amounts: Alberta 2023, Nova Scotia 2023, Manitoba 2025 (Manitoba matched up to $15M). Federal 2025 Manitoba matching agreement not yet disclosed.
- Nova Scotia totals for the $500-per-household payment and the Emergency Relief Grant; Quebec 2023 evacuee allowances; Ontario provincial evacuation and host costs.
- Final NWT travel and income support totals; GNWT split of its $204.6M between evacuation, response and recovery; BC Emergency Support Services alone; BC 2026 costs and evacuee count; Saskatchewan 2024 exact (under $1M).
- ISC costs by hazard and for FY2026-27; the purpose of ISC's Red Cross agreement 2324-HQ-000001 (disclosed only as "Other Program Reporting"); Canadian Red Cross audited figures by appeal (only unaudited appeal updates exist).

Lost work:
- An official count of work hours or days lost to evacuations (LFS); EI claims linked to wildfires for 2023 and 2025; employment status of evacuees.

## Access notes

- Statistics Canada (www150) worked this session: full-table CSVs for 14-10-0204, 14-10-0223 and 14-10-0327 and The Daily pages downloaded. Its WDS endpoint answers 405 to a plain GET (not needed). Census www12 pages gave 403, so the Census Profile SDMX API was used for Summerland, Jasper and Yellowknife.
- The open.canada.ca CKAN API timed out and then returned 504; the Question Period notes came from the losses agent's saved subset and the grants from search.open.canada.ca.
- The CMAJ, CSIRO (Christianson et al.) and canada.ca (2025-06-04) pages refused curl (403 or empty reply) but were read with WebFetch; no local copies.
- The CWFIS fire-database page is a JavaScript application; the evacuation summary file sits at /downloads/evacs/.
- The NWT emergency management report returned 504 once and downloaded on retry.
