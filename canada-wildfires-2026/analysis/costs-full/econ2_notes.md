# Property, infrastructure and economic costs: second round (2023 to 2026)

Run 2026-10-22 and 23. Closes the gaps left open in `econ_notes.md` (section 6). Rows, sources and access dates: `econ2_costs.csv` (same columns as `econ_costs.csv`); every download and web read: `econ2_manifest.csv`; scripts: `scripts/econ2_*`; satellite work files: `work/econ2_sat/`. Official records first; industry data (CatIQ, IBC) labelled and never added; news used only to find a document or to report an official's statement, never as the basis of an added row. Other cost files were not edited.

## Scorecard: what this round adds to the bill (CAD, census-value basis for buildings, nominal otherwise)

| Additive group | Low | Central | High |
|---|---|---|---|
| Buildings above the bill's own counts: satellite re-count on official perimeters (Bradley Creek, Pear Lake) | $10.2M | $11.3M | $23.6M |
| Buildings in places the bill does not cover: satellite or official document (KFN, other NL, Long Lake NS, Manitoba, Alberta 2023, Quebec 2023) | $61.0M | $92.9M | $296.0M |
| Utilities and equipment (BC Hydro 2023 estimate; Kingston fire-department equipment) | $52.9M | $80.0M | $85.4M |
| Recovery program (Saskatchewan 2025 cleanup and temporary housing) | $18.0M | $29.9M | $29.9M |
| Economic (sawmill GDP, 2023) | $0.0M | $32.2M | $64.4M |
| **Total additive rows** | **$142.1M** | **$246.3M** | **$499.3M** |
| Not added: buildings counted by officials but reported only in news (7 rows, section 1) | $0.0M | $219.7M | $233.5M |
| Not added: insured lower bounds for four unnamed fire catastrophes (industry) | at least $120M | | |

- Every additive row rests on an official document or on the project's satellite method, so all of them pass the rules of `scripts/combine_bill.py` (its news filter drops lines whose figures come from news reports). No additive row replaces an econ_ row.
- Officials' counts that exist only in news reports are separate rows, each a top-up above the satellite (or bill) count, with low 0 and additive "no": the OKIB chief's about 230 homes, TNRD's about 120 properties, Skwlax's 85, the KFN chief's 19, the NL premier's 203, Manitoba's 21 Nopiming cottages, and 158 buildings at Fox Lake, Sturgeon Lake and East Prairie. If the bill accepts officials' statements reported in news, they add $219.7M central; the econ_ Kingston insured-value row ($70M) must then be dropped, for a net +$149.7M. In the high case they overlap the satellite rows' allowances for missed buildings (each row gives the amount).
- The biggest additive rows: BC Hydro 2023 ($79.7M central, an estimate from official unit costs, since BC Hydro published no cost), Alberta 2023 ($42.9M, satellite), the 2023 sawmill GDP dip ($32.2M) and Saskatchewan's recovery program ($29.9M).
- Kingston NL: two satellite runs both fail the scene-offset screen, so no census-value row is added and the bill keeps the econ_ Kingston row (insured value, industry). The premier's count is a news-reported row.
- Everything else that was asked for either has an official "nothing to add" (Hydro-Quebec, NTPC, Hydro One, New Brunswick buildings, the 2026 economy) or no published figure (listed in section 9 with the documents searched).

## 1. Buildings destroyed (gap 1)

Rule, as in econ_: official count first, valued at the 2021 Census average value of owner-occupied dwellings of the DAs where the buildings stood (median for the low case), the bill's own basis. Only buildings above what the bill already flags are added. Where no official document gives a count, the project's satellite method counts them.

**Satellite method (this round).** The analysis/property method was re-run unchanged on new polygons (`econ2_sat_01` to `05`): Microsoft footprints within 1 km of the fire, Sentinel-2 L2A composites (up to 6 lowest-cloud scenes per tile, pre and post), the Jasper-calibrated rule (dNDVI on the building >= 180 and dNBR 20 to 60 m >= 40, plus burn context), counted within 500 m. Polygons: NBAC 2023 (Alberta, Quebec, Hay River area) and NBAC 2025 (Manitoba, Nova Scotia, New Brunswick, Newfoundland); for Bradley Creek and Pear Lake the official BC Wildfire Service perimeters instead of the CWFIS M3 outlines the bill used. Image windows start the day after the fire's last hotspot (next summer when the fire burned past mid-September). Value: each flagged footprint at its own DA value, as the bill.

A quality screen was added because the new areas include farmland and small fires that the check events did not: (1) clusters with a scene offset beyond +-100 dNBR are dropped (analysis/property dropped Enterprise 2023 for unstable offsets); (2) a fire polygon is dropped when its 500 to 1,000 m band has more than 26% as many flags as its 0 to 500 m band (the worst ratio among the bill's main events is Bradley Creek, 26 per 103); (3) fire polygons under 10 ha are dropped (the burn-context test needs 3.3 ha burned in the 100 to 250 m ring). The bill's main events all pass. Applied to the bill itself, the screen would drop 23 of the 59 Fort Frances 14 flags (Ontario 2026, offsets beyond 100) and 7 flags on two small 2026 outlines, about $6M at the bill's values; the bill is not changed here. The screen removed, for example, 22 flags beside a 0.3 ha Annapolis Valley fire that had 77 more flags 500 to 1,000 m away. For satellite counts the range uses the count ratios seen on the check events: low = flagged / 1.51 at the median value (the most over-counted check event, McDougall Creek); high = flagged / 0.89 for fires imaged soon after they burned (other Newfoundland fires, Katl'odeeche, the BC re-counts), and flagged / 0.31 (the Barrington under-count) where long fires are imaged only after their last hotspot (Manitoba, Alberta, Quebec), because vegetation regrows around ruins burned months earlier. Alberta shows the effect: at Fox Lake, Sturgeon Lake and East Prairie the satellite finds 22 buildings against 158 reported.

**Counts reported only in news.** For seven events the only count is an official's statement in a news report; no release, bulletin, notice or report with the number was found (checked: OKIB news posts to Oct 22, 2026; TNRD EOC notices to Oct 15, 2026; gov.nl.ca releases of Aug 11 to Sep 5, 2025; Manitoba's 2025 Interim After Action Review; Yellowhead County's May 2023 update; the CSRD alert). The sourcing rules allow news only as a pointer to an official document, so these counts are not the basis of any additive row. Each is listed as its own row: the official's count minus the satellite (or bill) count, at the same value, low 0, additive "no". They are there to be checked against a document later, or accepted by a decision on the bill.

| Event | Official count (who) | Satellite | Bill | Added, central | News-reported row |
|---|---|---|---|---|---|
| Bradley Creek BC 2026 | about 230 homes (OKIB chief, news) | 121 (BCWS perimeter) | 103 | $11.3M | $68.6M |
| Pear Lake BC 2026 | about 120 properties (TNRD, news) | 57 (BCWS perimeter) | 58 | $0.0M | $29.0M |
| Bush Creek East BC 2023 | 270: CSRD 176 (alert), TNRD 9 and Skwlax 85 (news) | 229 (bill run) | 229 | $0.0M | $23.2M |
| Katl'odeeche FN NT 2023 | 19: 18 homes, band office (chief, news) | 10 | 0 | $2.2M | $2.0M |
| Kingston NL 2025 | 203 structures (premier, news) | not usable (two runs) | 0 | none (econ_ insured row stays) | $40.5M |
| Other NL 2025 fires | none (cabins lost, no number) | 33 | 0 | $7.9M | |
| Long Lake NS 2025 | 20 homes, 11 outbuildings (provincial release) | 13 | 0 | $3.9M | |
| Other NS and all NB 2025 | NB: none lost (province) | 0 pass the screen | 0 | $0.0M | |
| Manitoba 2025, outside Lac du Bonnet | Nopiming 21 cottages (province, news) | 116 (12 on Nopiming) | 0 | $15.3M | $1.8M |
| Alberta 2023 | Fox Lake >85, Sturgeon Lake >=45, East Prairie 28 (news) | 107 (22 at those three) | 0 | $42.9M | $54.6M |
| Quebec 2023 | none published | 119 | 0 | $20.7M | |
| Ontario 2026 | none published | not re-run | 145 | $0.0M | |

Notes by event:
- **Bradley Creek, BC 2026.** The province gave no total and said "local governments and First Nations are the best source" (CP, Sep 10, 2026); OKIB's own posts (to Oct 22, 2026) give no number. On the official BCWS perimeter the satellite flags 121: 102 of the bill's 103 again plus 19 more, so the additive row adds 18 buildings ($11.3M central; high 33 buildings, $20.8M). The chief's count (about 230 homes: "more than 30" member homes and "more than 200" on certificate-of-possession lands) is the news-reported row, 109 buildings more ($68.6M). The gap is large; footprints may miss manufactured homes on leased lots.
- **Pear Lake / Big Bar, BC 2026.** The satellite re-count on BCWS perimeter C40983 finds 57 against the bill's 58, so the additive row adds nothing (high $2.8M). TNRD: about 120 properties with structure loss as of Aug 3, 2026, outbuildings included, Clinton village excluded, "expected to grow" (spokesperson to Castanet and CFJC; the TNRD EOC notices give no count): news-reported row, 62 more ($29.0M).
- **Bush Creek East, BC 2023.** Skwlax te Secwepemculecw: 85 destroyed, 13 damaged, 139 unscathed (communications coordinator citing the Canada Task Force 1 assessment, CTV). With CSRD 176 (official alert) and TNRD 9 (Castanet) the total is 270 against 229 flagged. Only the CSRD part has a document, and it alone is below the bill, so the 41 extra buildings ($23.2M) are a news-reported row.
- **Katl'odeeche First Nation, NT 2023.** The satellite flags 10 on the reserve ($2.2M added). Chief: 18 families lost homes and the band office burned; five major buildings damaged (CBC): news-reported row, 9 more ($2.0M; high 13 with four damaged buildings).
- **Kingston, NL 2025.** The premier's 203 (Aug 19, 2025) came from structures that lost power, by community; the province published no written count (the gov.nl.ca releases of Aug 11 to Sep 5, 2025 give none). Two satellite runs: fall 2025 against fall 2024 (drought-browned vegetation shifted the main cluster by +154 dNBR; 433 flagged, 2.1 times the official count) and summer 2026 against summer 2024 (`econ2_sat_05_kingston.py`: 199 flagged within 500 m, none 500 to 1,000 m out, close to the official count, but scene offsets of +98 to +261). Both fail the offset screen and they disagree by a factor of 2.2, so neither is counted. The bill keeps the econ_ Kingston row (CatIQ insured value, over $70M, industry). The premier's count at the DA values of the 690 footprints inside the burn is the news-reported row ($40.5M central; high 248 structures, adding the May 2025 Small Point fire, CP). If the bill accepts that row, drop the econ_ row.
- **Nova Scotia 2025.** Long Lake: 20 homes destroyed and 11 outbuildings lost or damaged (provincial release, Aug 28, 2025); the satellite finds 13. No other NS fire passes the screen.
- **New Brunswick 2025.** "No structures have been lost due to the wildfires in the province" (provincial update reported by CP24, Aug 20, 2025); no NB flag passes the screen.
- **Manitoba 2025 outside Lac du Bonnet.** No provincial building count (the 2025 Interim After Action Review gives none). The satellite finds 116 buildings outside the bill's areas (33 near Leaf Rapids, 24 near Lynn Lake, 20 on Pinaymootang (Fairford 50), 12 on the Nopiming fire, others small), valued low because DA values there are $28k to $72k: $15.3M central, high $73.4M (the Barrington ratio, for May losses imaged after the last hotspot). Partial provincial counts reported in news: 21 Nopiming cottages (spokesperson, The Narwhal) and about 20 structures at Beresford Lake (province, CBC, May 22, 2025): news-reported row, 9 more cottages ($1.8M; high 29 with Beresford Lake). The RM of Lac du Bonnet's 28 homes are inside the bill (it flags 50 there, unchanged).
- **Alberta 2023.** No provincial count. Fox Lake: more than 85 structures (Little Red River Cree Nation, Global News, May 10, 2023); Sturgeon Lake Cree Nation: at least 45 homes (CTV); East Prairie Metis Settlement: 28 buildings incl. 14 homes (settlement chair, CTV); Yellowhead County: homes lost, no count (county update). The satellite finds 107 buildings ($42.9M central; high $138.5M with the Barrington ratio): 22 at the three places with counts and 85 elsewhere (23 on one fire in the Peace country near 56.3N 119.3W, 15 on a fire south of Edson in Yellowhead and Clearwater counties, 12 southwest of Grande Prairie, others small). Drayton Valley's 34 flags fail the screen. The reported counts add 136 buildings above the satellite at the three places: news-reported row, $54.6M.
- **Quebec 2023.** No official building count exists (ministry, SOPFEU and season reviews give none). The satellite finds 119 (44 on one large fire east of Lebel-sur-Quevillon, 21 to 98 km from the town, 10 of them within 30 km; 7 at Lac-Simon; the rest bush camps across Nord-du-Quebec and the Cote-Nord); 5 more lie 500 to 1,000 m out. Central $20.7M. Camps that survived inside severely burned forest can look destroyed to the rule, the known risk noted in analysis/property.
- **Ontario 2026.** No official count. Reports confirm losses where the bill's two clusters are (Collins First Nation on Thunder Bay 36; lodges near Upsala on Fort Frances 14), so the bill's 86 and 59 flags stand; nothing added.

## 2. Insured losses (gap 2, industry, cross-check only)

- 2026: CatIQ says British Columbia had "three new catastrophes declared to date" (Sep 15, 2026). Bald Range is one ($293M, 45-day). CatIQ declares a catastrophe above $30M insured, so the other two (most likely Bradley Creek and the Big Bar complex; CatIQ does not name them) are at least $30M each: at least $60M.
- 2025: five fire catastrophes, all "in provinces that had never had a prior industry fire catastrophe" (CatIQ, Jan 20, 2026). Public: Flin Flon complex $249M, Pisew over $50M, Kingston over $70M. The other two: at least $30M each.
- Final figures for McDougall Creek, Bush Creek East, Hay River and Behchoko-Yellowknife (2023) are not public. CatIQ posts updates only for events above the PERILS threshold (its Bald Range update says $293M "falls below the PERILS reporting threshold"), so the initial IBC figures in econ_ stand.
- Cross-check against this round's building values: Kingston insured over $70M against $41M census value (1.7 times, inside the 1.4 to 4.4 range of econ_).

## 3. Utilities (gap 3)

- **BC Hydro 2023: estimate $52.6M / $79.7M / $85.1M.** BC Hydro replaced "approximately 200 transmission structures and over 1,200 distribution poles" in 2023 (info bulletin Apr 16, 2025) but published no cost. Unit costs from official figures: a distribution pole costs $20k to $32k to restore (Manitoba Hydro 2025: $24M capital in the first half and $32M in total for 1,000 to 1,200 poles; SaskPower 2025: $8.5M for at least 300 poles plus other work); a transmission structure about $238k (BC Hydro's own 2024 cost, $15M for 57 structures and 53 poles, less the poles). Central = 1,200 poles + 200 structures. Low = 200 structures at BC Hydro's full 2024 cost per structure, poles ignored. BC Hydro's F26-F27 revenue requirements show only the storm-account variance (F2024 storm restoration -$7.0M against plan; evacuation relief $0.4M), which is not a wildfire cost.
- **Hydro-Quebec 2023: nothing to add.** The 2023 annual report describes smoke-triggered line trips and outages, no asset damage or cost.
- **NWT Power Corporation 2023: nothing to add.** "Limited physical asset damage" (one Snare transmission tower and distribution in Behchoko); lost sales during evacuations not quantified.
- **Hydro One 2026: nothing to add.** "Wildfire activity has not had a major impact in our operations" (Q2 call, Aug 12, 2026); some northern infrastructure affected.
- **SaskTel 2025:** customer bill relief of about $315,000 (a transfer, not added); no damage cost. **SaskEnergy:** no damage reported.
- **Manitoba Hydro 2025:** the Interim After Action Review now says more than 1,200 poles (econ_ used "more than 1,000"); no new dollar figure, econ_ row unchanged.
- **Fire department equipment, Kingston 2025: $307,674** (23 departments; NL release Aug 27, 2026). Added (response equipment, not in gov_).
- TELUS lost an 8 km pole line on Westside Road in the Bradley Creek fire (OKIB post); no cost.

## 4. Highways and rail (gap 4)

No dollar figure is published for any item. The econ_ rail GDP rows (2023 $43M, 2024 Jasper $11M) remain the only rail measure; they are output lost, not repair cost. Details and documents in section 9.

## 5. Uninsured-loss and recovery programs (gap 5)

- **Saskatchewan 2025: $18.0M / $29.9M / $29.9M added.** The recovery task team committed $29.93M ($20M cleanup, debris and landfills; $9.93M temporary housing), about $18M of it by Dec 1, 2025 (Hansard). About 250 Denare Beach lots were cleaned and returned to owners. This is outside the bill's SPSA response line ($295.3M of the supplementary estimate was "evacuation and wildfire response") and outside health_. PDAP payments to private claimants are not published (claims were due in December 2025).
- **BC:** Disaster Financial Assistance is paid under EDMA s.10(2) and sits inside EMCR's payments by event ($101.3M for the 2023 interface fires in FY2023-24), which health_ already counts in full ($118.6M over three years). No DFA split is published. Not added.
- **NWT:** uninsured homes were not eligible for rebuilding help (fire insurance was available; DFAA does not consider affordability, TD 112-20(1), June 2024). MACA instead removed debris and hazardous material (25 Enterprise lots) and housed uninsured homeowners to Aug 31, 2024; these costs sit inside the GNWT's $204.6M 2023 event estimate (health_ high case). Not added.
- **NL:** NL-DFAP for the summer 2025 fires covers local authorities only, not households (activated Jun 25, 2026; claims to Sep 25, 2026). Households whose primary home was uninhabitable and uninsured got $1,000 to $1,500 a month (no total published). Not added.
- **Nova Scotia 2023:** a wildfire DFA program paid up to $200,000 per eligible low-income household, small business or non-profit for uninsurable losses (applications to Jan 31, 2024); no total published. The federal DFAA interim payment for the 2023 fires was $15.99M (Dec 12, 2024), all categories, already reflected as non-additive in gov_.

## 6. Forestry (gap 6)

- **Sawmills 2023: $0 / $32.2M / $64.4M added.** Statistics Canada: "The wildfires in 2023 impacted production in many sawmills across Canada" (Monthly Survey of Manufacturing, Sep 2023). Same method as the econ_ GDP rows: sawmill GDP (NAICS 3211) fell below a straight line from April to October 2023 by $64.4M over May to September; StatCan also cites log prices and weak demand, so the share is 0/50/100%. Pulp and paper also dipped ($14.8M) but StatCan names no fire effect; not added.
- No official count of mill curtailments exists. Quebec's shutdowns (four Resolute sawmills, two Remabec sawmills, the Nordic Kraft pulp mill for a month) are described only by Desjardins Economic Studies. Salvage: Quebec's special salvage plans (plans d'amenagement special, by fire) give volumes, not costs.

## 7. Farms (gap 7)

Nothing new to add. The only wildfire-related program is BC's 2023 Wildfire and Drought AgriRecovery (up to $71M, "not an estimate of damage"; econ_ lists it as a transfer). Payments and the wildfire share are not published; the Alberta and Saskatchewan 2023 AgriRecovery initiatives were for drought (livestock feed). AgriStability does not record cause.

## 8. 2026 economic impact (gap 8)

Nothing to add: no official source reports a measurable 2026 effect. Statistics Canada's Daily releases checked (GDP June and July 2026, Q2 GDP, LFS August and September, sawmills June, natural resource indicators Q2, energy statistics July, national tourism indicators Q2, travel August, EI August) do not mention wildfires. The Bank of Canada's July 2026 MPR and Q3 2026 Business Outlook Survey do not either. Alberta's Q1 update says "limited wildfire disruptions supported activity" (oil). BC's Q1 report says the economy is "resilient despite wildfires", with no figure. August GDP (Oct 30) and the October MPR (Oct 28) come after this check.

## 9. Still open, with the documents searched

| Item | Documents searched |
|---|---|
| FortisBC 2023 and 2026 | BCUC orders G-177-24, G-236-24, G-256-24 (BC Hydro only); FortisBC bill-credit notice (OKIB post, Aug 22, 2026) |
| ATCO Electric, Jasper 2024 | AUC decisions 28320-D01-2023, 26573-D01-2023, 27062-D01-2023 (no Jasper 2024); IEEE abstract (22 km underground mainline, no cost); Municipality of Jasper agendas, budgets, statements (franchise fees only) |
| Nova Scotia Power 2023 | ICS Canada after-action report page; no NSUARB filing found |
| Newfoundland Power 2025 | NP wildfire page and news list; NL-DFAP and NL releases (no utility figure) |
| SK highways 106 and 167 | SK Highways Annual Report 2025-26 ("increases for forest fire support activities", no amount); SPSA bulletins Jun 12, Jun 17, Jul 3, Jul 9, 2025 (closures only); Crown release Nov 4, 2025 |
| BC highways 2023 to 2026 | Transportation ministry annual service plan reports 2023/24, 2024/25, 2025/26 (no wildfire repair cost) |
| NWT highways 2023 | Supplementary Estimates (Operations) No. 2 2023-24 (fire suppression only); NWT Emergency Management Annual Report 2025 ($204.6M event total, no split) |
| CN and CPKC | CN Q2 2023 MD&A and Q3 2024 release (wildfires named, not quantified); CPKC not reached |
| PDAP, BC DFA, NS DFA totals | SK Hansard Dec 1, 2025; EMCR s.10(2) reports FY2023-24 to FY2025-26; NS releases Nov 17, 2023; Public Safety Canada Dec 12, 2024 |
| AgriRecovery wildfire share | BC release 2023AF0056; AAFC QP notes 2024-QP-00131 and 2025-QP-00023 |
| Insured finals 2023 BC and NWT | CatIQ public releases 2024 to 2026; IBC releases Oct 3 and Nov 20, 2023 |

The web search budget for this run ran out partway (200 searches shared by all agents in the session), after the searches above; the items in this table could be retried in a follow-up.

## 10. Overlaps and how to add this to the bill

- Additive building rows add only buildings above the bill's own flags (Bradley Creek and Pear Lake re-counts) or in places the bill does not cover (KFN, other NL, Long Lake, Manitoba outside Lac du Bonnet and Denare Beach, Alberta 2023, Quebec 2023). Satellite flags that match a bill footprint, or lie within 500 m of the bill's Lac du Bonnet or Denare Beach areas, are not counted.
- News-reported rows (additive "no") sit on top of the satellite rows or the bill: each adds only buildings above them. If they are accepted, add their low and central as given; in the high case subtract the overlap each row states (the satellite row's allowance for missed buildings covers some of the same buildings).
- econ_ rows: no additive row replaces one. The news-reported Kingston row would replace the econ_ Kingston insured-value row if accepted. No other econ_ row covers these buildings (econ_ Hay River and Enterprise rows cover the town and hamlet, not the reserve; econ_ Saskatchewan rows are SK only).
- Insured rows are industry and overlap the same buildings and the health_ evacuation lines; never add them.
- BC Hydro 2023 is a different season from econ_ BC Hydro 2024. The NL fire-department grant is not in gov_. The SK recovery row is outside the bill's SK firefighting line and health_.
- The sawmill row is value added of a different industry from the econ_ forestry and logging row; like all GDP rows it includes wages that health_ lost-wage lines also count for evacuated workers.
- Census-value caveat as in the bill: cabins, outbuildings and chalets are valued as owner-occupied dwellings; reserve DA values are often suppressed, so CD values are used.

## 11. Access notes

- WebSearch hit its session limit partway through; later work used saved documents, direct fetches of official pages and the satellite runs.
- One request to sec.gov carried the user's email address in its User-Agent header by mistake (a connectivity test); no other personal data was sent. CN filings were then read with WebFetch.
- The Sentinel-2 runs were network-bound and memory-heavy. Workers were stopped and restarted several times (some ran out of memory and were relaunched with 10 km sub-cells), each time resuming from its saved output. A final check found every cluster with a footprint within 500 m of a fire of 10 ha or more processed (361 clusters in six jobs, plus the 2 Kingston clusters of the summer-window run added on Oct 23), all with imagery; footprints processed twice are dropped before counting.
