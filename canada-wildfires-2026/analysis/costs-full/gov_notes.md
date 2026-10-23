# Government response costs not yet in the wildfire bill (2023 to 2026)

Checked 2026-10-22. Files: `gov_costs.csv` (61 rows), `gov_manifest.csv` (32 sources), script `scripts/gov_build_costs.py`, downloads in `raw/gov/` (plus files already in `../readiness/raw/`, `../losses/raw/`, `../policy/raw/`, `../economic-value/raw/`).

Every number comes from an official record: estimates, public accounts, annual and departmental results reports, supplementary estimates, Hansard PDF, budget annexes, audited statements, auditor reports, proactive disclosure. No number is taken from news. Dollars are nominal and 2025 dollars, using the same CPI factors as `analysis/economic-value` (CPI all-items, v41690973, annual mean; 2026 is the January to September mean): 2023 x1.045033, 2024 x1.020723, 2025 x1.0, 2026 x0.975604. A fiscal year Y to Y+1 counts as fire season Y, as in the existing tally. `additive_amount_cad` is in 2025 dollars.

## Summary: what to add to the bill (2025 dollars)

| Line | 2023 | 2024 | 2025 | Total |
|---|---|---|---|---|
| Quebec SOPFEU, net of exports | $259.7M | $155.1M | $133.8M | $548.6M |
| Manitoba | $55.9M | $81.4M | $229.0M | $366.3M |
| Northwest Territories | $157.0M | $91.5M | $112.1M | $360.6M |
| Yukon | $40.0M | $48.4M | $63.9M | $152.4M |
| Nova Scotia (forecasts) | $23.5M | $9.5M | $40.9M | $73.9M |
| Newfoundland and Labrador (revised) | $3.9M | $12.1M | $32.5M | $48.6M |
| BC Fire Preparedness line | $42.7M | $43.1M | $57.9M | $143.7M |
| BC 2025-26 actual minus bill estimate | | | $135.1M | $135.1M |
| Ontario base fire program line | $34.7M | $34.5M | $34.5M | $103.7M |
| Parks Canada response | $39.6M | $61.0M | not found | $100.6M |
| Alberta DRP, Jasper municipal incident response | | $26.0M | | $26.0M |
| Public Safety Canada (Red Cross matching, HWF) | $13.4M | $4.9M | $3.0M | $21.4M |
| CIRNAC, NWT Indigenous governments | $9.4M | | | $9.4M |
| DND Operation LENTUS | $9.3M | not found | not found | $9.3M |
| **A. 2023 to 2025, official records** | **$689.3M** | **$567.7M** | **$842.7M** | **$2,099.6M** |
| B. 2026 season, forecasts and budgets | | | | $1,440.5M |
| C. ISC on-reserve response, estimate | $322.4M | $250.4M | $619.3M | $1,192.1M |
| A + B | | | | $3,540.1M |
| A + B + C | | | | $4,732.2M |

2026 (B): BC Fire Management $829.3M (Q1 forecast $850M nominal) and Fire Preparedness $46.1M (budget); Alberta $267.3M (Q1, costs to July only); Ontario $146.3M (Q1 equals budget); Manitoba $55.3M, NWT $64.0M, Nova Scotia $20.6M, NL $11.5M (budgets, no in-year update). Saskatchewan, Quebec, Yukon, New Brunswick and PEI 2026 not found; no federal 2026 response cost found yet.

Not additive (reference rows): DFAA orders ($829.0M, $187.8M, $12.5M), ISC recovery, Parks Canada Jasper re-entry and recovery ($72.8M spent 2024-25), Red Cross recovery agreements ($18.4M), the 2023 Fall Economic Statement ISC top-up ($260M, a cross-check), SK and CIFFC mutual-aid payments, the federal aircraft leases for 2026 ($64M), Manitoba's all-hazard Emergency Expenditures for 2023-24 ($29M).

## Method notes by item

**Quebec (SOPFEU, including SAG airtankers).** SOPFEU audited total expenses: $250.9M (2023), $155.6M (2024), $159.7M (2025), calendar years. Subtracted: billings to agencies outside Quebec (annexe B "hors Québec": $2.36M, $3.64M, $14.47M), because those crews' costs also sit in the importing provinces' lines; and in 2025 the CL-415 avionics modernization ($11.39M, a capital-type upgrade funded by a grant). SAG airtanker costs are already inside SOPFEU: its statements say "Les excédents ou les déficits de l'opération des avions-citernes sont assumés par l'Organisme", and airtanker operating and financing costs are expensed in presuppression. No separate SAG wildfire cost was found. SOPFEU billed Indigenous Services Canada $20.75M (2023), $1.55M (2024) and $1.34M (2025) for northern-zone protection; these stay in the Quebec line and are removed from ISC.

**Manitoba.** The $229M vs $179M + $129M question is resolved: $179M and $129M were Q1 mid-year figures; the 2025-26 Public Accounts table "Summary of Manitoba's Response to Unprecedented Wildfires in 2025" gives the audited result: wildfire suppression from Emergency Expenditures $175M, Manitoba Wildfire Service $40M, NRIF wildfire suppression $14M (total $229M). The same table's evacuee costs ($80M) and DFA program ($12M) are left to the evacuation and property lines. 2024-25: MWS $38.871M + Suppression $16.166M + $24.7M paid from Emergency Expenditures (NRIF 2025-26 footnote) = $79.7M. 2023-24: MWS + Suppression $53.5M; the wildfire share of that year's $29M all-hazard Emergency Expenditures is not published, so it is not added.

**Northwest Territories.** Official records replace the transcription site. Hansard PDF, October 21 2025, pp. 2796-97 (Finance Minister): suppression actuals "just shy of $25 million" (2022-23), "$127 million" (2023-24), "$61 million" (2024-25). For comparability with BC and Alberta (whole program), the line used is ECC Forest Management (presuppression, suppression and a small forest-resources section): $150.2M actual 2023-24 (Main Estimates 2025-26, actuals column), $89.6M revised 2024-25, $112.1M for 2025-26 (revised $94.1M, which includes the $39.5M Supplementary No. 2 suppression shortfall, plus $18.0M Supplementary No. 3 "shortfall in fire suppression"). Public Accounts 2024-25 activity actual ($107.0M incl. Wildlife) is consistent. 2025-26 Public Accounts not yet tabled.

**Yukon.** Fire Management O&M: $38.3M actual (2023-24), $47.4M actual (2024-25), $63.9M forecast (2025-26; estimate $30.8M plus $33.7M wildfire response in Supplementary Estimates No. 1). Capital excluded.

**Nova Scotia.** Only forecasts exist at program level: Fleet and Forest Protection $22.5M (2023-24), $9.3M (2024-25), $40.9M (2025-26), each the prior-year forecast printed in the next Estimates. The line includes the provincial air fleet; regional wildfire staff in the Central, Eastern and Western lines are not separable and are excluded. No program-level actuals are published.

**Newfoundland and Labrador.** The budget site worked on 2026-10-22. Fire Suppression and Communications, gross amount voted, revised: $3.8M (2023-24), $11.9M (2024-25), $32.5M (2025-26). Water bomber operations sit in Transportation and Infrastructure "Government-Operated Aircraft" with air ambulance and are not separable (excluded).

**BC and Ontario lines missing from the bill.** BC's Ministry of Forests has a "Fire Preparedness" core business separate from the Fire Management vote that the bill uses (the bill's 2023 and 2024 BC figures equal the Fire Management vote exactly): $40.9M, $42.2M, $57.9M actual. BC's 2025-26 Fire Management actual is $645.1M, against the $510.0M early estimate in the bill: add $135.1M. Ontario's "Public safety and emergency response" base line (net of recoveries; also covers aviation and other emergencies) was $33.2M, $33.8M, $34.5M. These are base program costs, like Alberta's 2.1 line already in the bill; drop them if the bill should hold event costs only.

**Parks Canada.** 2023-24: the 2024-25 Departmental Results Report says Parks "incurred additional costs when responding to an unprecedented number of wildfires ... and received $37.9 million in additional funding" (Budget 2024 annex: "Emergency Wildfires Response PCA 38"). 2024-25: the Jasper Recovery Coordination Centre Year Two Progress Report (Parks Canada and the Municipality of Jasper; a DRAFT tabled at the municipal Committee of the Whole on 2026-07-14) says "In 2024-2025, Parks Canada spent $132.6 million", of which "Incident response and emergency operations $59.8 million" and re-entry and initial recovery $72.8M (interim housing $29.1M, hazard management $20.2M). The $132.6M matches the $133.1M envelope in Parks Canada's February 6, 2025 backgrounder (up to $45.2M Jasper incident response, $7.7M other fire pressures, $80.1M recovery and re-entry), so $59.8M is used as all 2024-25 Parks response; recovery is left to the property and infrastructure lines. 2025-26 and 2026-27 response costs not found (Budget 2025's $43M for 2025-26 mixes response and rebuilding).

**Alberta Disaster Recovery Program, Jasper.** Same JRCC report: the province (90%) and municipality (10%) spent $25.5M to June 2026 on "Incident response": municipal emergency operations, structural protection, mutual aid and transitional housing. It is outside the bill's Alberta line (Forestry and Parks). The Municipality of Jasper's audited statements ($35.5M in 2024, $4.0M in 2025, "emergency response and site remediation") record the same spending, so only one may be counted. Other provinces' payments for municipal response costs were not searched for.

**Department of National Defence.** DND 2023-24 Departmental Results Report, costs of major CAF operations: Op LENTUS actual incremental cost $8,855.6k (planned $2,660.0k). Incremental cost excludes Regular Force salaries. LENTUS covers all natural disasters; DND's November 2024 briefing binder describes about 1,760 members deployed in the 2023 wildfire season. Whether part of the 2023-24 cost was for non-fire events is not stated, so it is an upper bound for wildfire. 2024-25 and 2025-26 actuals could not be retrieved (canada.ca pages failed; the 2025-26 Departmental Plan shows only 2024-25 planned $8.0M).

**Public Safety Canada.** Wildfire-specific agreements in the Grants and Contributions disclosure (latest amendment value): Red Cross matching for Alberta 2023 ($7.49M) and Nova Scotia 2023 ($5.01M), United Way NWT ($0.36M for 2023, raised to $2.55M to cover 2024), Humanitarian Workforce deployments for Labrador July 2024 ($2.22M), Jasper (Team Rubicon $0.41M), Manitoba 2025 ($2.09M) and NL 2025 ($0.94M). Values are commitments. Red Cross 'early and long-term recovery' agreements for Alberta 2024 ($12.62M), Saskatchewan 2025 ($2.82M) and NL 2025 ($2.65M) are recovery, so they are reference rows only (same rule as Parks Canada and ISC recovery). No Government Operations Centre cost is published. CIRNAC: Budget 2024 gave $9M in 2023-24 to Indigenous governments affected by the 2023 NWT fires.

**Indigenous Services Canada (estimate, tier C).** ISC publishes EMAP response costs reimbursed for all hazards: $369.5M (2023-24), $294.4M (2024-25), $688.6M (2025-26); recovery $139.7M, $296.9M, $166.7M. It publishes no split by hazard. The estimate applies the wildfire share of First Nations evacuation events in each fiscal year (90 of 101, 26 of 31, 73 of 81, from ISC's evacuation statistics) to response costs, then subtracts SOPFEU's ISC billings. Recovery (rebuilding) is excluded. Cross-check: Budget 2024 says the 2023 Fall Economic Statement provided $260 million "To support wildfire responses and recovery activities in First Nations communities"; it was a top-up on EMAP's base, so a lower bound for response plus recovery. Keep tier C separate from the floor.

**Imported crews and CIFFC cost recovery.** The receiving agency pays. Manitoba's NRIF 2024-25 annual report, on its crews sent to Saskatchewan and the NWT: "Costs for this support was recovered from the receiving province and territory under the Canadian Inter-Agency Forest Fire Centre (CIFFC) and Great Lakes Forest Fire Compact (GLIFFC) agreements". Saskatchewan's Provincial Auditor: obtaining resources from partners cost "about $26.3 million ... in 2025 (2024: $1.9 million; 2023: $521,000)", inside SK's line. CIFFC handles only agent transactions (air charter and "wildfire support": $8.4M in 2024-25, $13.2M in 2025-26), paid by members. No federal payment for imported international firefighters was found. Not additive.

## DFAA: what is eligible, and the decision

Guidelines for disasters before April 1, 2025 (apply to 2023 and 2024 events), section 1.4: the DFAA do not apply to "the fighting of forest, prairie, grass or wild fires, except where they pose a threat to built-up areas, and then primarily for pre-emptive actions, evacuation and damaged infrastructure restoration." Interpretation Bulletin 10 (June 2023) defines an interface fire as one that "poses a threat to built-up areas ... and results in an evacuation, or property damage, or disruption of the delivery of essential goods and services", allows pre-emptive costs "typically up to two weeks prior to the evacuation order", and repeats that "public sector response costs for regular salaries, normal operating expenses, and emergency service costs related to routine emergency management functions ... are not eligible."

Guidelines for disasters from April 1, 2025 (apply to 2025 and 2026 events), section 9.5.6: "Wildland firefighting costs are only eligible for wildland urban interface fires"; section 9.6: "General wildland firefighting costs are ineligible, unless they are for a wildland urban interface fire"; only overtime is eligible for permanent staff. Evacuations (9.5.2), emergency shelter, food and supports, including host jurisdictions' costs (9.5.3), and infrastructure and home repair streams are eligible.

Decision: additive part of DFAA = $0. DFAA is the federal share of costs that provinces and territories already pay: interface firefighting (inside the provincial firefighting lines), and evacuation, shelter, infrastructure repair and household assistance (the evacuation, infrastructure and property lines). Adding the orders ($793.3M for 2023, $183.9M for 2024, $12.5M so far for 2025, nominal) would count the same dollars twice. Use DFAA only as evidence of who paid, or as a floor for a jurisdiction where those other lines have no figure (after removing interface firefighting, which cannot be separated in the orders).

## Overlaps left in the numbers

- Mutual aid: costs of crews that MB, NT, YT, NS, NL and Parks Canada hired from BC, AB or SK are also in those provinces' gross lines in the bill. Not published; small next to the totals. Quebec's exports are removed; Ontario's line is already net of recoveries.
- ISC pays BC, AB, SK, MB and ON wildfire agencies for on-reserve suppression (for example $2.38M a year to BC Wildfire Service, ISC QP note 2023). Only Quebec's share is quantified and removed.
- The econ_ file counts Parks Canada Jasper hazard management ($20.2M) and rebuild rows; they sit in Parks re-entry and recovery, which is excluded here, so there is no overlap with the $59.8M response row. Its Municipality of Jasper cost row is the same spending as the Alberta DRP incident response row here; keep only one.
- Public Safety, CIRNAC and ISC lines overlap the evacuation line if that line counts Red Cross, NGO or ISC-funded evacuee support, or provincial evacuee costs recovered from ISC (for example Manitoba's $80M in 2025-26). Count once.

## Not found

- Manitoba: wildfire share of 2023-24 Emergency Expenditures ($29M all hazards); 2026 wildfire share of the $277M Q1 Emergency Expenditures overrun (mostly floods).
- NWT: 2025-26 final actual (Public Accounts not yet tabled); any 2026-27 wildfire figure (the October 21, 2026 fiscal update names "increasing costs of wildfire emergencies" without a number).
- Yukon: 2025-26 actual; 2026-27 Fire Management estimate (column not readable; yukon.ca blocks downloads); any 2026-27 supplementary.
- Nova Scotia: program-level actuals for any year.
- New Brunswick: any wildfire-only spending, 2023-24 to 2026-27. The Forest Protection component (fire, insects, disease; $29.1M estimate 2026-27) has no published actuals; the 2025-26 Supplementary Appropriations Act gives Natural Resources $14M without saying what for.
- Newfoundland and Labrador: final actuals (only revised estimates); water bomber operating costs (mixed with air ambulance).
- Prince Edward Island: wildfire spending for 2023 to 2025 (no published figure found; PEI has no aircraft and burns 8 to 15 ha a year).
- Nunavut: no wildfire suppression program or budget line (joined CIFFC June 2026).
- Quebec: 2026 SOPFEU results (annual report not yet out); any SAG cost outside SOPFEU (none identified).
- Saskatchewan: 2026 season cost (Q1 report of August 27, 2026 shows no wildfire variance).
- BC, Alberta, Ontario 2026: final costs (Q1 forecasts only; Alberta's covers July only).
- Parks Canada: audited spending against the "up to" amounts; 2025 and 2026 response costs.
- DND: LENTUS actual incremental costs for 2024-25 and 2025-26.
- ISC: EMAP costs by hazard; 2026-27 costs.
- Public Safety Canada: Government Operations Centre wildfire costs; 2026 agreements (none disclosed yet).
- CIFFC: dollar value of imports by province (only Saskatchewan's, via its Auditor).
- Municipal response costs outside Jasper (for example Halifax, West Kelowna and Kelowna, Yellowknife and Hay River, La Ronge, Flin Flon) and the provincial programs that reimburse them: not searched in this pass. The econ_ file lists Halifax 2023 as partly response.
- Access notes: canada.ca refuses shell downloads (read with WebFetch); one WebFetch to news.gov.bc.ca was blocked by an unanswered permission prompt and the page was read with curl instead; open.canada.ca's API returned 504 late in the session, so the full Question Period notes file was not re-streamed.
