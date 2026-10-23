# Property, infrastructure and economic costs not yet in the wildfire bill (2023 to 2026)

Run 2026-10-22. Scope: costs outside the current bill (trees at Crown stumpage; firefighting in BC, AB, SK, ON; homes and buildings destroyed at census values). Government firefighting and response spending, health, evacuation and lost wages belong to the gov_ and health_ files and are not counted here. Every number comes from an official record unless labelled INDUSTRY (CatIQ or IBC). News was used only to find documents. Rows, sources and access dates: `econ_costs.csv`; downloads: `econ_manifest.csv`; scripts: `scripts/econ_01` to `econ_04`.

## Scorecard: additive totals (CAD, nominal unless stated)

| Additive group | Low | Central | High |
|---|---|---|---|
| Property: buildings missing or under-counted in the bill (official counts) | $89 M | $119 M | $139 M |
| Property: Kingston NL, insured value (industry only) | $0 M | $70 M | $70 M |
| Infrastructure: utilities (BC Hydro, Manitoba Hydro, SaskPower) | $48 M | $56 M | $56 M |
| Infrastructure: Jasper rebuild, Halifax, Kelowna (check gov_ for overlap) | $94 M | $174 M | $730 M |
| Economic: oil and gas shut in (2023, 2025) | $246 M | $575 M | $1,276 M |
| Economic: GDP lost in mining, rail, accommodation, forestry (2023, 2024) | $29 M | $278 M | $497 M |
| Economic: Parks Canada fees, Prince Albert | $0 M | $1 M | $1 M |
| **Total additive** | **$506 M** | **$1,271 M** | **$2,769 M** |
| Not in total: industry property adjustment (insured minus bill, six events) | $0 M | $1,733 M | $1,733 M |

- Official records alone (dropping the Kingston industry row): $506 M / $1,201 M / $2,699 M.
- The biggest single swing is the Jasper high case, which adds the $520 M federal rebuild commitment of June 30, 2026 (not yet spent).
- Main check on the bill: insured losses (industry) run 2.6 times the bill's building value for the six events that have both ($2.81 B insured against $1.08 B in the bill). The census-value proxy leaves out contents, vehicles, commercial property, business interruption and the gap between market value and rebuild cost. Using insured losses instead would add $1.73 B. That figure also contains evacuation living expenses (health_ scope), so it is shown as an alternative, not added.

## 1. Insured losses (INDUSTRY) and the check on building values

| Event | Insured (CatIQ) | Bill value | Ratio |
|---|---|---|---|
| Upper Tantallon NS 2023 | $247.5 M (one year) | $100.2 M | 2.47 |
| McDougall Creek BC 2023 | over $480 M | $345.4 M | 1.39 |
| Bush Creek East BC 2023 | over $240 M | $129.9 M | 1.85 |
| Jasper AB 2024 | $1,304 M (final) | $297.8 M | 4.38 |
| Flin Flon complex MB/SK 2025 | $249 M | $75.8 M (Denare only) | 3.28 |
| Bald Range BC 2026 | $293 M (45-day) | $131.0 M | 2.24 |

- Events with insured losses but no buildings in the bill: Kingston NL 2025 (over $70 M), Pisew SK 2025 (over $50 M), Hay River NT 2023 (over $30 M), Behchoko-Yellowknife NT 2023 (over $30 M). Only Kingston is added (no official written count was found); the others are covered by official-count rows below or are mostly evacuation claims.
- Tantallon claims: about 3,000 to 3,270 claims for $247.5 M against 151 homes lost, so many claims are for smoke damage and living expenses. CatIQ notes Jasper has the highest average claim value in its database.

## 2. Buildings missing from the bill or under-counted (official counts)

Method: official count x 2021 Census average value of owner-occupied dwellings (CSD, else CD), the same basis the bill uses for official counts. Low uses the median value or the lower count.

| Item | Count | Central |
|---|---|---|
| Barrington Lake NS 2023: 230 destroyed (HRFE citing the after-action review) against 72 flagged in the bill | +158 | $34.0 M |
| SHOE fire SK 2025: about 400 homes in the region (MNP review) against 355 flagged | +45 | $9.6 M |
| Enterprise NT 2023: 80 to 90% of structures lost (NWT 2023 Wildfire Response Review); 51 private dwellings | 43 | $7.8 M |
| Hay River NT 2023: 4 homes Patterson Road, 3 or 4 Paradise Gardens, 2 cabins | 9 | $2.7 M |
| Behchoko NT 2023: 4 structures confirmed (high: 22) | 4 | $0.9 M |
| Saskatchewan 2025 outside the SHOE region: about 700 structures lost in the season (SPSA estimate) minus about 412 | 288 | $63.5 M |

The SPSA estimate also counts about 400 vehicles lost in Saskatchewan in 2025; no official value exists, so they are not valued.

## 3. Public infrastructure

- **Jasper, Parks Canada** (JRCC Year Two Progress Report, draft, in the Municipality of Jasper agenda of July 14, 2026):
  - Hazard management 2024-25: $20.2 M.
  - Rebuild 2025-27: $187.3 M allocated, of which $75.6 M was spent by June 9, 2026 ($21.9 M of that on interim housing, excluded here). Low $53.7 M, central $133.0 M (non-housing share), high $685.4 M with the $520 M announced June 30, 2026.
  - The federal government reports over $380 M in total for Jasper response and recovery to March 2027. gov_ must not count the same money.
- **Jasper townsite water and sewer** (RFD of April 14, 2026; Bylaw #284 of August 4, 2026): Phase 1 $2.015 M; Phase 2 $7.63 M, which also renews aged mains. Low $5.1 M (the DRP-eligible parts), high $9.6 M.
- **Halifax**: $13.7 M preliminary estimate for the 2023 wildfires (HRM staff report, September 2023). It mixes asset remediation with response overtime.
- **Kelowna Glenmore Landfill** (McDougall Creek): $1.4 M.
- **Utilities**:
  - BC Hydro 2024 season: about $15 M (2024/25 service plan report). The 2023 season replaced 1,400 poles and about 90 km of line, but no dollar figure was published.
  - Manitoba Hydro 2025: $32 M restoration estimate ($24 M capital in the first half of 2025-26).
  - SaskPower 2025: about $8.5 M in Denare Beach and Creighton.
- **Listed but not added** (gov_ scope):
  - Municipality of Jasper response and site remediation, $39.5 M (audited).
  - Alberta Disaster Recovery Program for Jasper, $73.1 M budget, $35.9 M spent.

## 4. Economic losses

- **Oil and gas** (computed from Statistics Canada production tables 25-10-0055 and 25-10-0063):
  - Shortfall = expected minus actual output. Expected output = the March-April daily level x the month's ratio in non-fire years. Central uses the median ratio; low and high use the lowest and highest.
  - Prices are official: Alberta gas reference price, AER APMC crude prices, Alberta pentanes plus par price, and WCS (BVM component) for the high case.
  - 2023 (StatCan: "dropped 6.6% as a result of the forest fires in Alberta"):
    - Gas: 32 to 76 million GJ, $64 M to $169 M.
    - Light and medium crude: 1.5 to 2.7 million bbl, $121 M to $226 M.
    - Pentanes plus: 0.7 to 3.0 million bbl, $61 M to $260 M.
  - 2025 in situ bitumen: 0 to 8.2 million bbl, $0 to $620 M. The central case ($163 M) counts only May 28 to 31 of the May shortfall, because StatCan puts the rest of May down to maintenance.
  - These are gross sales not made in those months. Some of the output was deferred rather than lost for good.
  - Check on the method: applied to May and June 2016 (Fort McMurray) it gives 27 to 41 million bbl lost.
- **GDP** (monthly GDP 36-10-0434):
  - Loss = straight-line baseline minus actual, divided by 12, converted with the GDP implicit price index.
  - Attribution follows StatCan's own wording: 50/100/100% where StatCan names wildfires as the cause, 0/50/100% where it names other causes too.
  - Central values: iron ore 2023 $26 M, rail 2023 $43 M, accommodation 2023 $145 M (weakest attribution), forestry 2023 $26 M, rail 2024 (Jasper) $11 M, iron ore 2024 $15 M, accommodation 2024 $12 M.
  - The oil and gas GDP rows ($266 M for 2023, $129 M for 2025) cross-check the production rows and are not added.
  - StatCan's May to July 2026 GDP releases do not mention wildfires. Statements are in `work/econ_statcan_wildfire_statements.csv`.
- **Tourism**:
  - Prince Albert NP, FY2025-26: 77,000 fewer visits, about $0.5 M in fees.
  - Jasper fees: $5 M to $12 M for 1.3 M fewer visits. Not added, because Parks Canada's network fees rose that year and the Jasper rebuild allocation already funds the Jasper field unit's lost revenue.
  - National accommodation GDP (above) is the net tourism loss.
- **Agriculture**: the 2023 BC Wildfire and Drought AgriRecovery budget was up to $71 M. BC says this "is not an estimate of damage", and the wildfire share and payments are not published. Not added.
- **Transfers, not added**:
  - Jasper rent and licence relief, $15.2 M.
  - Jasper municipal revenue stabilization and tax relief, $8.5 M.
  - Jasper business and tourism grants, $11.4 M.
  - Quebec 2023 business liquidity loans, $23 M.

## 5. Overlaps

- No additive row overlaps the bill's trees or firefighting lines.
- **Property rows** add to the bill's buildings line (different buildings). Do not add the insured rows for the same events on top of them.
- **Infrastructure, check gov_**:
  - The Jasper rows overlap gov_ if it counts the federal Jasper total or the Alberta DRP.
  - Halifax and Kelowna overlap the NS and BC DFAA orders if gov_ counts them.
- **Oil and gas against GDP**: these are alternatives (gross output against value added). The production rows are added; the GDP oil and gas rows are not.
- **GDP and health_**: GDP and production values include wages. health_ lost-wage lines for the same workers would double count.
- **Insured losses** include evacuation living expenses, which overlap health_/evacuation.

## 6. Not found (no official dollar figure or count)

**Property counts**
- Bradley Creek BC 2026: OKIB published no count. The chief told news media about 230 homes; the bill flags 103.
- Pear Lake / Big Bar BC 2026: TNRD published no count (news: 120 or more properties; the bill flags 58).
- Kátł'odeeche First Nation 2023 ("numerous structures").
- Tulita 12 Mile NT 2023 (about 10, cited from CBC).
- Kingston NL 2025: no written count (the premier's 203 was given at a briefing).
- Alberta 2023 (Fox Lake and others).
- Manitoba 2025 outside Lac du Bonnet.
- Quebec 2023.
- NS and NB 2025.
- Ontario 2026.
- Bush Creek East band structures (news: 85).

**Insured losses**
- Two of the five 2025 fire catastrophes.
- Two of the three 2026 BC fire catastrophes.
- Final figures for the 2023 BC and NWT events.

**Infrastructure**
- BC Hydro 2023 ($).
- FortisBC 2023 and 2026 (no exogenous-cost filing found).
- ATCO Jasper 2024.
- Hydro-Quebec 2023 (a reliability effect only).
- NTPC 2023 ("limited physical asset damage").
- Nova Scotia Power 2023, Newfoundland Power 2025, Hydro One 2026.
- SaskTel and SaskEnergy.
- Saskatchewan Highways 106 and 167 (damage reported, no cost).
- BC and NWT highways; CN rail.
- Municipal costs for West Kelowna, RDCO, CSRD, Westbank FN, OKIB, Summerland, RDOS, Denare Beach, Creighton, Flin Flon, Hay River, Enterprise, Barrington and Shelburne (only a $24,737 tax reduction found), and the Thunder Bay area.

**Uninsured-loss programs**
- SK PDAP, BC DFA, NWT disaster assistance and NL housing assistance: no wildfire totals published.

**Economic**
- Official mill curtailment data; Quebec forest industry losses beyond the GDP figure.
- Crop and livestock losses.
- The wildfire share of AgriRecovery or AgriStability payments.
- Any 2026 economic impact.

## 7. Data access and pointers for other files

- Statistics Canada's site and tables downloaded normally this session. canada.ca and parks.canada.ca timed out from the shell and were read with WebFetch.
- For gov_:
  - Manitoba 2025-26 wildfire expenses, $374 M (Q2 report).
  - Parks Canada 2024-25 response, $59.8 M, plus $72.8 M re-entry.
  - Jasper evacuation payments, $7.5 M.
  - Red Cross matching funds: $12.6 M federal and $12.1 M Alberta.
- For health_: StatCan says the May 2025 wildfire hours lost were offset by overtime ("virtually nil" net effect).
