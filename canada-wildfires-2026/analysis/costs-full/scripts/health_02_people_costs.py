"""People costs of the 2023 to 2026 wildfires: health care, evacuations, lost work and wages.

Every hard-coded number below is checked against the saved official file it came from
(function `check`), so a typo stops the script. Values read from data files are parsed directly.
All dollar amounts are converted to 2025 dollars with CPI all-items (StatCan series via Bank of
Canada Valet V41690973), the same basis as the existing wildfire bill (cost_tally_by_year.csv).

Run after health_01_ed_costs.py. Outputs (in costs-full/):
  health_costs.csv, health_lost_wages_by_year.csv, health_hc_morbidity_costs.csv
"""
import csv
import html
import json
import os
import re
import warnings

import openpyxl
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
CF = os.path.dirname(HERE)
AN = os.path.dirname(CF)
RAW = os.path.join(CF, "raw", "health")
ACC = "2026-10-22"


def text(path):
    p = path if os.path.isabs(path) else os.path.join(RAW, path)
    t = open(p, encoding="utf-8", errors="ignore").read()
    if p.endswith((".html", ".htm", ".xml")):
        t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = t.replace("ﬁ", "fi").replace("‑", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", t)


_cache = {}


def check(path, *quotes):
    """Stop if a quoted string is not in the saved source file."""
    if path not in _cache:
        _cache[path] = text(path)
    for q in quotes:
        assert re.sub(r"\s+", " ", q) in _cache[path], f"not found in {path}: {q}"


# ---------------------------------------------------------------- CPI
obs = json.load(open(os.path.join(AN, "losses", "raw", "cpi", "boc_V41690973.json")))["observations"]
cpi = pd.DataFrame([(o["d"], float(o["V41690973"]["v"])) for o in obs], columns=["d", "v"])
cpi["d"] = pd.to_datetime(cpi.d)
CPI_Y = cpi.groupby(cpi.d.dt.year).v.mean()          # 2026 = January to September mean


def cpi_fy(y):
    return cpi[(cpi.d >= f"{y}-04-01") & (cpi.d <= f"{y + 1}-03-01")].v.mean()


C25 = CPI_Y[2025]


def to25_y(v, y):
    return v * C25 / CPI_Y[y]


def to25_fy(v, y):
    """Spending reported for fiscal year y to y+1 counts as fire season y and uses the season-year CPI,
    the same convention as the bill (economic-value/scripts/07_cost_tally.py) and gov_costs.csv.
    Fiscal-year CPI (cpi_fy) is used only for CIHI unit prices, which are fiscal-year price levels."""
    return v * C25 / CPI_Y[y]


BASIS = "2025 CAD (CPI all-items annual average)"
rows = []


def add(**k):
    base = dict(item="", jurisdiction="", period="", quantity="", unit_cost="", amount_low_cad="",
                amount_central_cad="", amount_high_cad="", dollars_basis=BASIS, method="", source_name="",
                url="", accessed=ACC, overlaps_with="", additive="no", notes="")
    base.update(k)
    for c in ("amount_low_cad", "amount_central_cad", "amount_high_cad"):
        if base[c] != "":
            base[c] = round(float(base[c]))
    rows.append(base)


# =============================================================== 1. HEALTH CARE
# 1a. Health Canada AQBAT counts for 2023 (Matz et al. 2026, GeoHealth, Table 1)
MATZ = os.path.join(AN, "health", "raw", "crf", "matz2026.xml")
check(MATZ, "Respiratory emergency room visits", "1,700 [1,200\u20132,300]", "Respiratory hospital admissions",
      "350 [230\u2013460]", "Cardiac emergency room visits", "610 [320\u2013890]", "Cardiac hospital admissions",
      "460 [250\u2013680]", "Asthma symptom days", "1,100,000 [240,000\u20132,000,000]",
      "Acute morbidity valuation (2023 CAD)", "$820M [$150M\u2013$2.0B]", "6,800,000 [4,100,000\u20139,400,000]",
      "12,000,000 [0\u201325,000,000]", "22,000 [0\u201350,000]", "The baseline incidence rates of health outcomes were derived from 2023 data")
HC = {  # outcome: (central, low, high)
    "resp_ed": (1700, 1200, 2300), "card_ed": (610, 320, 890),
    "resp_adm": (350, 230, 460), "card_adm": (460, 250, 680)}

# unit costs: ED from CIHI 2025 data tables (direct and full), admissions from CIHI Patient Cost Estimator
ed = pd.read_csv(os.path.join(CF, "health_ed_by_province_year.csv"))
ed_direct = float(ed[ed.prov == "QC"].direct_cost_fy2023_24.iloc[0])     # Canada excl. QC and NU
ed_full = float(ed[ed.prov == "QC"].full_cost_fy2023_24.iloc[0])
wb = openpyxl.load_workbook(os.path.join(RAW, "patient-cost-estimator-results-en.xlsx"), read_only=True)
pr = list(wb["Table 1"].iter_rows(values_only=True))
hdr = [re.sub(r"\s+", " ", str(h)).strip() for h in pr[1][:14]]
pce = pd.DataFrame([r[:14] for r in pr[2:] if r[0] and len(str(r[0])) == 9 and str(r[0]).startswith("20")], columns=hdr)
pce = pce[(pce["Fiscal year"] == "2021\u20132022") & (pce["Jurisdiction"] == "Canada")].copy()
pce["vol"] = pd.to_numeric(pce["Volume (typical cases)"].astype(str).str.replace("*", "", regex=False), errors="coerce")
HCOL = "Estimated average hospital cost (all age groups)"
cmg = pce.groupby(["Case Mix Group", "Case Mix Group (description)"]).agg(vol=("vol", "sum"), cost=(HCOL, "first")).reset_index()
RESP = ["139", "138", "136", "147", "141", "097"]     # COPD, viral pneumonia, bacterial pneumonia, asthma, URI/LRI, influenza
CARD = ["196", "202", "194", "204", "208"]            # heart failure, arrhythmia, MI, unstable angina, angina/chest pain (all without angiogram)


def wavg(codes):
    s = cmg[cmg["Case Mix Group"].isin(codes)]
    return float((s.vol * s.cost).sum() / s.vol.sum()), float(s.cost.min()), float(s.cost.max()), s


resp_c, resp_lo, resp_hi, resp_tab = wavg(RESP)
card_c, card_lo, card_hi, card_tab = wavg(CARD)
f_ed = C25 / cpi_fy(2023)          # CIHI ED costs are FY2023-2024 dollars
f_pce = C25 / cpi_fy(2021)         # PCE costs are FY2021-2022 dollars

ed_n = [HC["resp_ed"][i] + HC["card_ed"][i] for i in range(3)]          # central, low, high
ed_amt = (ed_n[1] * ed_direct * f_ed, ed_n[0] * ed_full * f_ed, ed_n[2] * ed_full * f_ed)
adm_amt = (HC["resp_adm"][1] * resp_lo * f_pce + HC["card_adm"][1] * card_lo * f_pce,
           HC["resp_adm"][0] * resp_c * f_pce + HC["card_adm"][0] * card_c * f_pce,
           HC["resp_adm"][2] * resp_hi * f_pce + HC["card_adm"][2] * card_hi * f_pce)
MATZ_SRC = ("Matz C.J. et al. (Health Canada and ECCC) 2026, Health Impact Analysis of Wildfire Smoke-PM2.5 in Canada "
            "(2019-2023), GeoHealth 10(2):e2025GH001565, doi:10.1029/2025GH001565, Table 1 (AQBAT, 2023 column)")
MATZ_URL = "https://doi.org/10.1029/2025GH001565 (full text read via https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12852501/fullTextXML)"
CIHI_ED_SRC = ("CIHI, Spending Trends in Health Service Delivery, 2014-2015 to 2023-2024, Data Tables (2025), Table 4.1 "
               "(Emergency, cost per visit, FY2023-2024); full cost ratio 304/157.6 from CIHI (2020) Hospital Spending: "
               "Focus on the Emergency Department")
CIHI_ED_URL = ("https://www.cihi.ca/sites/default/files/document/spending-trends-health-service-delivery-2014-2023-data-tables-en.xlsx ; "
               "https://www.cihi.ca/sites/default/files/document/hospital-spending-highlights-2020-en.pdf")
CIHI_PCE_SRC = "CIHI Patient Cost Estimator Results (2024), Table 1, Canada, FY2021-2022, typical inpatients, hospital cost (all ages)"
CIHI_PCE_URL = "https://www.cihi.ca/sites/default/files/document/patient-cost-estimator-results-en.xlsx"

add(item="Health care: extra respiratory and cardiac emergency visits from wildfire smoke (Health Canada count x CIHI cost)",
    jurisdiction="Canada", period="2023 (May-Sep)", quantity=f"{ed_n[0]} visits ({ed_n[1]} to {ed_n[2]})",
    unit_cost=f"CIHI direct cost per ED visit {ed_direct:.1f}; full hospital cost {ed_full:.2f} (FY2023-24 dollars)",
    amount_low_cad=ed_amt[0], amount_central_cad=ed_amt[1], amount_high_cad=ed_amt[2],
    method="Health Canada AQBAT counts (1,700 respiratory + 610 cardiac ED visits, 95% range) x CIHI cost per visit; low = low count x direct cost, central and high = full cost; FY2023-24 dollars to 2025 dollars by CPI",
    source_name=MATZ_SRC + "; " + CIHI_ED_SRC, url=MATZ_URL + " ; " + CIHI_ED_URL,
    overlaps_with="none in the bill; overlaps our own all-cause ED estimate (do not add both)", additive="yes",
    notes="Official modelled count, not observed. Physician fees excluded (CIHI hospital costs exclude physician compensation). Quebec and Nunavut are not in CIHI's cost table; the Canada (excl. QC, NU) cost is used for the national count.")
add(item="Health care: extra respiratory and cardiac hospital admissions from wildfire smoke (Health Canada count x CIHI cost)",
    jurisdiction="Canada", period="2023 (May-Sep)",
    quantity=f"{HC['resp_adm'][0]} respiratory ({HC['resp_adm'][1]} to {HC['resp_adm'][2]}) + {HC['card_adm'][0]} cardiac ({HC['card_adm'][1]} to {HC['card_adm'][2]}) admissions",
    unit_cost=f"respiratory {resp_c:.0f} (range {resp_lo:.0f} to {resp_hi:.0f}); cardiac {card_c:.0f} (range {card_lo:.0f} to {card_hi:.0f}) per typical stay, FY2021-22 dollars",
    amount_low_cad=adm_amt[0], amount_central_cad=adm_amt[1], amount_high_cad=adm_amt[2],
    method="Health Canada AQBAT admissions x CIHI Patient Cost Estimator average hospital cost per typical case; central = volume-weighted mean of the main medical CMGs (respiratory: COPD, viral and bacterial pneumonia, asthma, upper/lower respiratory infection, influenza; cardiac without angiogram: heart failure, arrhythmia, MI, unstable angina, angina/chest pain); low = low count x cheapest CMG, high = high count x dearest CMG; FY2021-22 dollars to 2025 by CPI",
    source_name=MATZ_SRC + "; " + CIHI_PCE_SRC, url=MATZ_URL + " ; " + CIHI_PCE_URL,
    overlaps_with="none in the bill", additive="yes",
    notes="Our own analysis has no admission counts (no open baseline by province), so admissions come only from Health Canada. Physician costs not available for Canada in the PCE table and are excluded. Latest PCE year is 2021-22; CPI understates hospital cost growth since then.")

# 1b. 2024 to 2026 scaled from Health Canada 2023 by our AQBAT burden ratio (9 common provinces)
md = pd.read_csv(os.path.join(AN, "health", "modelled_acute_deaths_national.csv"))
aq = md[md.coefficient.str.startswith("AQBAT")].set_index("year")
r23 = aq.loc[2023, "net_c_common_provinces"]
base23 = [ed_amt[i] + adm_amt[i] for i in range(3)]          # 2025 dollars
hc_scaled = []
for y in (2024, 2025, 2026):
    ratio = aq.loc[y, "net_c_common_provinces"] / r23
    hc_scaled.append((y, ratio))
    add(item="Health care: smoke-related emergency visits and admissions, scaled from Health Canada 2023",
        jurisdiction="Canada (scaling ratio from AB BC NB NS ON PE QC SK YT)", period=f"{y} (May-Sep)",
        quantity=f"ratio {ratio:.3f} of 2023 (about {ed_n[0] * ratio:.0f} ED visits and {(HC['resp_adm'][0] + HC['card_adm'][0]) * ratio:.0f} admissions)",
        unit_cost="as 2023 rows", amount_low_cad=base23[0] * ratio, amount_central_cad=base23[1] * ratio,
        amount_high_cad=base23[2] * ratio,
        method=f"2023 Health Canada-based cost x ratio of our AQBAT net smoke burden in {y} to 2023 (net modelled acute deaths, 9 provinces with data every year: {aq.loc[y, 'net_c_common_provinces']:.1f} / {r23:.1f}); assumes morbidity scales with the same exposure-weighted burden",
        source_name="analysis/health/modelled_acute_deaths_national.csv (our exposure, Health Canada AQBAT coefficient) with the 2023 rows above",
        url="analysis/health/results.md section 4", overlaps_with="our own all-cause ED estimate (do not add both)",
        additive="yes", notes="ESTIMATE, not an official count: Health Canada has published no morbidity numbers after 2023. Our 2023 AQBAT deaths (379) match Health Canada's (400), which supports the scaling. Excludes MB, NL, NT, NU in 2025 and 2026 (no monitors), so those years are low. 2026 smoke to 2026-10-19.")

# 1c. our own all-cause ED estimate (suggestive only; not additive)
for y, s in ed.groupby("year"):
    add(item="Health care: extra all-cause emergency visits, our own CIHI NACRS estimate (SUGGESTIVE ONLY)",
        jurisdiction="AB BC MB NS ON PE QC SK YT" + (" (2025: no MB, NS)" if y == 2025 else ""), period=f"{y} (May-Sep)",
        quantity=f"{s.extra_c.sum():.0f} visits ({s.extra_lo.sum():.0f} to {s.extra_hi.sum():.0f})",
        unit_cost="CIHI direct cost per ED visit by province, FY2023-24 (AB 246.1, BC 278.4, MB 231.0, NS 320.2, ON 222.9, PE 184.7, SK 248.7, YT 192.8, QC uses Canada excl. QC/NU 241.6); full = x1.929",
        amount_low_cad=s.amount_low_2025d.sum(), amount_central_cad=s.amount_central_2025d.sum(),
        amount_high_cad=s.amount_high_2025d.sum(),
        method="our monthly CIHI ED model (+1.71% per 10 ug/m3, 95% CI 0.16 to 3.28) by province x CIHI cost; low = low visits x direct cost, central and high = full cost; detail in health_ed_by_province_year.csv",
        source_name="analysis/health/scripts/09_ed_extra_visits.py (CIHI NACRS data tables) + " + CIHI_ED_SRC,
        url=CIHI_ED_URL, overlaps_with="Health Canada-based rows above (same visits, different method)",
        additive="no",
        notes="Central is suggestive only: one significant fit of six (all-months fit -0.18%), and Health Canada's own Ontario study (Chen et al. 2025 CMAJ) found no rise in non-asthma ED visits in June 2023. Use only the low end in any 'at least' statement; not in the totals.")

# 1d. Health Canada outcomes without a health care dollar figure (reference)
add(item="Health Canada: acute morbidity valuation of wildfire smoke, 2023 (not health care spending)",
    jurisdiction="Canada", period="2023", quantity="all acute non-fatal outcomes in Table 1",
    amount_low_cad=to25_y(150e6, 2023), amount_central_cad=to25_y(820e6, 2023), amount_high_cad=to25_y(2.0e9, 2023),
    method="Health Canada AQBAT socio-economic valuation (medical costs, reduced productivity, pain and suffering); 2023 dollars to 2025 by CPI",
    source_name=MATZ_SRC, url=MATZ_URL, overlaps_with="health care rows above (medical costs inside it); lost work (restricted activity days)",
    additive="no", notes="A welfare value, not money spent; excludes deaths. Includes 12,000,000 acute respiratory symptom days (0 to 25,000,000), 1,100,000 asthma symptom days in children 5-19 (240,000 to 2,000,000), 22,000 child acute bronchitis episodes (0 to 50,000), 6,800,000 restricted activity days (4,100,000 to 9,400,000).")
add(item="Health Canada / Public Health Ontario study: asthma emergency visits during June 2023 smoke, Ontario",
    jurisdiction="ON", period="June 2023", quantity="+23.6% asthma ED visits (95% CI 13.2% to 34.9%) at 1-day lag after the early June episode; no detected effect on other respiratory, ischemic heart disease or non-cardiorespiratory ED visits",
    method="interrupted time series (published); no absolute excess count reported",
    source_name="Chen H, Kaufman JS, Chen C, et al. Impact of the 2023 wildfire smoke episodes in Ontario, Canada, on asthma and other health outcomes: an interrupted time-series analysis. CMAJ 2025;197:E465-77",
    url="https://doi.org/10.1503/cmaj.241506 (read via https://www.cmaj.ca/content/197/17/E465)", additive="no", dollars_basis="",
    notes="Supports Health Canada's small counts and argues against our all-cause ED estimate as a central figure. Baseline NACRS asthma ED visits about 317 a day (April-July 2023).")
add(item="Health care: hospital admissions in our own analysis", jurisdiction="Canada", period="2023-2026",
    quantity="not estimated", dollars_basis="", method="none",
    source_name="analysis/health/results.md section 4 ('Not estimated: respiratory and cardiac hospital admissions')",
    url="analysis/health/results.md", additive="no",
    notes="No open official baseline by province; no counts invented. Health Canada's 2023 admissions are used instead (row above).")

# =============================================================== 2. EVACUATIONS
# CWFEDB evacuee counts (NRCan)
wbe = openpyxl.load_workbook(os.path.join(RAW, "cwfis_evacs", "CWFEDB_1980to2025_sumstats_v20260203.xlsx"), read_only=True, data_only=True)
EV = {}
for r in wbe.worksheets[0].iter_rows(values_only=True):
    if isinstance(r[0], int) and r[0] >= 2023:
        EV[r[0]] = (r[1], r[2])
assert EV[2023] == (282, 232359) and EV[2024] == (91, 56423) and EV[2025] == (197, 86574), EV
CWF_SRC = "Natural Resources Canada, Canadian Wildland Fire Evacuation Database (CWFEDB) Summary Stats 1980-2025, v2026-02-03"
CWF_URL = "https://cwfis.cfs.nrcan.gc.ca/downloads/evacs/CWFEDB_1980to2025_sumstats_v20260203.xlsx"
for y in (2023, 2024, 2025):
    add(item="People evacuated by wildfire (count, no dollars)", jurisdiction="Canada", period=str(y),
        quantity=f"{EV[y][1]} evacuees in {EV[y][0]} evacuations", dollars_basis="", method="official database summary",
        source_name=CWF_SRC, url=CWF_URL, additive="no",
        notes={2023: "Public Safety Canada QP note PS-2023-QP-1--MEP-004 (2023-09-21): 'over 200,000 people'.",
               2024: "Includes Jasper; ESDC (SOR/2025-10) says more than 20,000 evacuated from Jasper park and town on July 22-23, 2024 (town population 4,738 in 2021).",
               2025: "ESDC QP note EF_063_20260105 (2025-09-15): about 85,000 evacuated by early September, evacuation orders lasted more than 18 days on average, about 30% at least 21 days. Public Safety PS-2025-QP-005: over 70,000."}[y])

add(item="People evacuated by wildfire (count, no dollars; PARTIAL)", jurisdiction="Canada", period="2026",
    quantity="at least 20,847: 8,805 First Nations on reserve (ISC, Apr 1 to Oct 2, 2026) + 12,042 District of Summerland residents (whole District under order 2026-08-08; 2021 Census population)",
    dollars_basis="", method="sum of two official counts; no national 2026 total published",
    source_name="ISC Wildfire evacuation information for Indigenous peoples (modified 2026-10-05); District of Summerland Evacuation Order 2026-08-08 and RDOS EOC update 2026-08-08 (5,688 Summerland properties, 416 RDOS, 38 Penticton Indian Band properties on order); Statistics Canada Census Profile 2021 (CSD 5907035)",
    url="https://isc.gc.ca/eng/1686078907307/1686078925161 ; https://www.summerland.ca/docs/default-source/your-city-hall/council/council's-corner/2026/20260808-evacuation-order---entire-community.pdf ; https://www.rdos.bc.ca/newsandevents/rdos-news/information-releases/article/5811 ; https://api.statcan.gc.ca/census-recensement/profile/sdmx/rest/data/STC_CP,DF_CSD/A5.2021A00055907035.1.1.1",
    additive="no", notes="Other 2026 evacuations off reserve (BC Okanagan and Central Okanagan, NWT, Ontario, Manitoba) have no official total yet.")

# Alberta
check("ab/scss_2023_24.txt", "Over 37,000 wildfire evacuees were provided Emergency Evacuation Payments in 2023, totaling $47.1 million")
check("ab/scss_2024_25.txt", "Approximately 17,550 Albertans were required to evacuate their homes in 2024 due to wildfires",
      "provided $12.6 million in evacuation payments to over 12,273 Albertans, including 3,541 children")
check("ab/pses_2023_24.txt", "$44.3 million for the 2023 Northwest Territories wildfire support", "$175 million for the 2023 Alberta wildfires")
AB_DFAA = "DFAA (Alberta 2023 order CAD 149.6 M, 2024 CAD 106.4 M; reimburses eligible provincial costs incl. evacuation); Alberta Disaster Recovery Program totals"
add(item="Evacuations: Alberta Emergency Evacuation Payments", jurisdiction="AB", period="2023 (FY2023-24)",
    quantity="over 37,000 evacuees paid", unit_cost="1,250 per adult, 500 per child (evacuated 7 days or more)",
    amount_low_cad=to25_fy(47.1e6, 2023), amount_central_cad=to25_fy(47.1e6, 2023), amount_high_cad=to25_fy(47.1e6, 2023),
    method="official program total", source_name="Alberta Seniors, Community and Social Services Annual Report 2023-2024, p. 17",
    url="https://open.alberta.ca/dataset/3a6b50d8-c1f2-4e9a-94ec-62f1e0a34e59/resource/552b6d31-c765-46b6-917a-10b24a7d97c4/download/scss-annual-report-2023-2024.pdf",
    overlaps_with=AB_DFAA + "; Alberta's CAD 175 M 2023 wildfire DRP total (PSES annual report)", additive="yes",
    notes="Payments are for basic needs (shelter, food, clothing, transport), not income, so they do not overlap lost wages.")
add(item="Evacuations: Alberta Emergency Evacuation Payments", jurisdiction="AB", period="2024 (FY2024-25)",
    quantity="over 12,273 Albertans paid (3,541 children); about 17,550 Albertans evacuated",
    amount_low_cad=to25_fy(12.6e6, 2024), amount_central_cad=to25_fy(12.6e6, 2024), amount_high_cad=to25_fy(12.6e6, 2024),
    method="official program total", source_name="Alberta Seniors, Community and Social Services Annual Report 2024-2025, p. 18",
    url="https://open.alberta.ca/dataset/3a6b50d8-c1f2-4e9a-94ec-62f1e0a34e59/resource/5b876aae-aaae-4c93-a9a1-4fe1305c7b39/download/scss-annual-report-2024-2025.pdf",
    overlaps_with=AB_DFAA, additive="yes", notes="Communities: Chipewyan Lake, Fort McMurray, Fox Lake, Garden River, Janvier, Jasper, John D'Or Prairie.")
add(item="Evacuations: Alberta costs of hosting Northwest Territories evacuees", jurisdiction="AB (for NT)", period="2023 (FY2023-24)",
    quantity="more than 20,000 NWT evacuees hosted",
    amount_low_cad=to25_fy(44.3e6, 2023), amount_central_cad=to25_fy(44.3e6, 2023), amount_high_cad=to25_fy(44.3e6, 2023),
    method="approved funding for Alberta emergency operations and Alberta local authorities that supported NWT evacuees",
    source_name="Alberta Public Safety and Emergency Services Annual Report 2023-2024, pp. 3, 37 and 48",
    url="https://open.alberta.ca/dataset/2b228e33-89ac-42d0-9c60-218d9ffb9f30/resource/15e58606-1375-4070-97e2-b331fc44cea2/download/pses-annual-report-2023-2024.pdf",
    overlaps_with="recovered from GNWT (CAD 46.4 M revenue for 2023 NWT evacuation events) and inside GNWT's CAD 204.6 M 2023 estimate; DFAA NWT 2023 order CAD 188.6 M",
    additive="yes", notes="Counted once here; the GNWT remainder row below subtracts it.")
add(item="Evacuations and response: Alberta 2023 wildfire Disaster Recovery Program costs not itemized above (high case only)",
    jurisdiction="AB", period="2023 (FY2023-24)", amount_low_cad=0, amount_central_cad=0,
    amount_high_cad=to25_fy(175e6 - 47.1e6, 2023),
    method="approved DRP funding CAD 175 M for the 2023 Alberta wildfires (21 ministries, 33 local authorities) minus the CAD 47.1 M evacuation payments, which may be inside it",
    source_name="Alberta Public Safety and Emergency Services Annual Report 2023-2024, p. 37",
    url="https://open.alberta.ca/dataset/2b228e33-89ac-42d0-9c60-218d9ffb9f30/resource/15e58606-1375-4070-97e2-b331fc44cea2/download/pses-annual-report-2023-2024.pdf",
    overlaps_with="property and infrastructure recovery (other agents); any provincial ministry wildfire costs already in the bill's Alberta line; DFAA Alberta 2023 order",
    additive="yes", notes="Mix of local authority response, ministry emergency costs and recovery that Alberta does not split; counted only in the high case.")

# Northwest Territories
check("pages/gnwt_eids_full_payments_20230907.html", "approximately $3.1 million", "Approximately 800 EIDS payments",
      "Approximately 4,600 ETSP payments", "the full $750 as a one-time payment")
check("nwt/emar2025.txt", "2023 Wildfires with an estimated $204.6 million in costs", "2024 Wildfires with an estimated $7.4 million",
      "2025 Wildfires with an estimated $9.5 million")
eids = 800 * 750
add(item="Evacuations: NWT Evacuation Travel Support Program (partial, to 2023-09-05)", jurisdiction="NT", period="2023",
    quantity="about 4,600 payments", unit_cost="750 per vehicle leaving the NWT, 400 within the NWT",
    amount_low_cad=to25_y(3.1e6 - eids, 2023), amount_central_cad=to25_y(3.1e6 - eids, 2023), amount_high_cad=to25_y(3.1e6 - eids, 2023),
    method="GNWT combined ETSP + EIDS total (about CAD 3.1 M) minus about 800 EIDS payments x 750",
    source_name="GNWT news release 2023-09-07, Applicants now receiving full Evacuee Income Disruption Support Payments",
    url="https://www.gov.nt.ca/en/newsroom/applicants-now-receiving-full-evacuee-income-disruption-support-payments",
    overlaps_with="inside GNWT's CAD 204.6 M 2023 estimate; DFAA", additive="yes",
    notes="Partial: applications were still open; no final total found.")
add(item="Evacuations: NWT Evacuee Income Disruption Support (partial, to 2023-09-05)", jurisdiction="NT", period="2023",
    quantity="about 800 payments", unit_cost="750", amount_low_cad=to25_y(eids, 2023), amount_central_cad=to25_y(eids, 2023),
    amount_high_cad=to25_y(eids, 2023), method="800 x 750", source_name="GNWT news release 2023-09-07",
    url="https://www.gov.nt.ca/en/newsroom/applicants-now-receiving-full-evacuee-income-disruption-support-payments",
    overlaps_with="lost work and wages (income replacement)", additive="no", notes="Not added: it compensates lost income already counted in lost wages.")
for y, tot, item_sum in ((2023, 204.6e6, 44.3e6 + 3.1e6), (2024, 7.4e6, 0.0), (2025, 9.5e6, 0.0)):
    add(item="Evacuations and response: GNWT wildfire emergency costs not itemized above (high case only)", jurisdiction="NT", period=str(y),
        amount_low_cad=0, amount_central_cad=0, amount_high_cad=to25_y(tot - item_sum, y),
        method=f"GNWT estimated event cost CAD {tot / 1e6:.1f} M" + (" minus Alberta hosting (44.3 M) and ETSP/EIDS (3.1 M)" if item_sum else ""),
        source_name="GNWT Municipal and Community Affairs, NWT Emergency Management Annual Report 2025 (Feb 2026), Table 7",
        url="https://www.maca.gov.nt.ca/sites/maca/files/resources/nwt_emergency_management_annual_report_2025.pdf",
        overlaps_with="DFAA NWT orders (2023 CAD 188.6 M, 2024 CAD 6.1 M); property and infrastructure recovery (other agents)",
        additive="yes", notes="Mix of evacuation, response and recovery that GNWT does not split; counted only in the high case.")

# British Columbia: EMCR payments under the Emergency and Disaster Management Act s.10(2)
check("bc/emcr_2023_24.txt", "2023 Interface fires 101.291")
check("bc/emcr_2024_25.txt", "2024 Interface fires 19.286", "2023 Interface fires 11.606")
check("bc/emcr_2025_26.txt", "2025 Interface fires 5.354", "2024 Interface fires 0.761", "2023 Interface fires 5.710")
check("pages/bc_news_2024EMCR0001-000004.html", "24,300 households", "7,000 households")
BC_URL = ("https://www2.gov.bc.ca/assets/gov/public-safety-and-emergency-services/emergency-preparedness-response-recovery/embc/reports/"
          "emcr-annual-payment-report-2023_24.pdf ; ...emcr-annual-payment-report_2024_25.pdf ; ...emcr-annual-payment-report-2025_26.pdf")
for y, parts in ((2023, [(2023, 101.291), (2024, 11.606), (2025, 5.710)]), (2024, [(2024, 19.286), (2025, 0.761)]), (2025, [(2025, 5.354)])):
    v = sum(to25_fy(p * 1e6, fy) for fy, p in parts)
    add(item="Evacuations and local emergency response: BC EMCR payments for interface fires", jurisdiction="BC", period=f"{y} fires",
        quantity=" + ".join(f"FY{fy}-{str(fy + 1)[2:]} {p:.3f} M" for fy, p in parts),
        amount_low_cad=v, amount_central_cad=v, amount_high_cad=v,
        method="sum of Emergency and Disaster Management Act s.10(2) payments by fiscal year for the event, each converted with its fiscal-year CPI",
        source_name="BC Emergency Management and Climate Readiness, Payments under EDMA Section 10(2), fiscal years ended March 31, 2024, 2025 and 2026",
        url=BC_URL, overlaps_with="DFAA (BC 2023 order CAD 358.9 M, 2024 CAD 71.4 M); government response spending (gov_ files) if they include EMCR; ISC reimbursements for First Nations evacuees",
        additive="yes", notes="Covers Emergency Support Services for evacuees plus local authority and First Nation response and some recovery; EMCR does not split them. " +
        ("2023: about 24,300 households under evacuation order; more than 7,000 households received ESS (BC news release 2024-01-04)." if y == 2023 else "") +
        ("2025: only the first fiscal year of payments so far." if y == 2025 else ""))

# Saskatchewan (Hansard, Standing Committee on Intergovernmental Affairs and Justice, 2025-12-01)
SKF = "sk/iaj_20251201.htm"
check(SKF, "we spent $13 million in hotel supports for community evacuations", "$3.2 million to support 3,054 households",
      "pledged 15 million through the Red Cross", "We also spent $9,800,500", "we supported 18,324 individuals",
      "We were at $890,000 in evacuation support", "approximately 11,500 evacuees with direct or financial support")
SK_SRC = "Legislative Assembly of Saskatchewan, Standing Committee on Intergovernmental Affairs and Justice, Hansard 2025-12-01 (SPSA officials)"
SK_URL = "https://docs.legassembly.sk.ca/legdocs/Committees/IAJ/Debates/30L/20251201Debates-IAJ-HTML.htm"
SK_OV = "DFAA (SK 2025 order CAD 8.5 M so far); ISC EMAP (on-reserve evacuees served by SPSA may be reimbursed by ISC)"
add(item="Evacuations: Saskatchewan Public Safety Agency evacuation support", jurisdiction="SK", period="2023 (FY2023-24)",
    amount_low_cad=to25_fy(0.89e6, 2023), amount_central_cad=to25_fy(0.89e6, 2023), amount_high_cad=to25_fy(0.89e6, 2023),
    method="official statement", source_name=SK_SRC, url=SK_URL, overlaps_with=SK_OV, additive="yes",
    notes="SPSA: evacuation support was under CAD 1 M a year in 2021-22 to 2024-25; 2023-24 was the high at CAD 890,000. 2024 not costed (under 1 M, exact value not stated).")
add(item="Evacuations: SPSA hotels for community evacuations and food support for self-evacuees", jurisdiction="SK", period="2025",
    quantity="hotels CAD 13 M; food CAD 3.2 M to 3,054 households", amount_low_cad=to25_y(16.2e6, 2025),
    amount_central_cad=to25_y(16.2e6, 2025), amount_high_cad=to25_y(16.2e6, 2025),
    method="official statement", source_name=SK_SRC, url=SK_URL, overlaps_with=SK_OV, additive="yes",
    notes="If ISC reimbursed the on-reserve share, that share is also inside the ISC EMAP estimate in gov_costs.csv (tier C, outside the floor).")
add(item="Evacuations: Saskatchewan direct payments to evacuated adults", jurisdiction="SK", period="2025",
    quantity="18,324 individuals over 18", amount_low_cad=to25_y(9800500, 2025), amount_central_cad=to25_y(9800500, 2025),
    amount_high_cad=to25_y(9800500, 2025), method="official statement", source_name=SK_SRC, url=SK_URL, overlaps_with=SK_OV,
    additive="yes", notes="For groceries and support while away; not income replacement.")
add(item="Evacuations: Saskatchewan funding to the Canadian Red Cross for evacuees", jurisdiction="SK", period="2025",
    amount_low_cad=to25_y(15e6, 2025), amount_central_cad=to25_y(15e6, 2025), amount_high_cad=to25_y(15e6, 2025),
    method="official statement (pledged)", source_name=SK_SRC, url=SK_URL, overlaps_with=SK_OV, additive="yes",
    notes="Government money given to the Red Cross (a pledge; final payment not found).")

# Manitoba: Disclosure of Contracts, Canadian Red Cross, 'Emergency services related to forest fires'
mb = json.load(open(os.path.join(RAW, "mb", "rc_2025.json"))) + json.load(open(os.path.join(RAW, "mb", "rc_2024.json")))
mb = [x for x in mb if x["rationale"] == "Emergency services related to forest fires"]
mb25 = sum(x["contractValue"] for x in mb if x["contractDate"].startswith("2025"))
mb24 = sum(x["contractValue"] for x in mb if x["contractDate"].startswith("2024"))
assert abs(mb25 - 52923021.13) < 1 and abs(mb24 - 49437.74) < 1, (mb25, mb24)
check("mb/wf2026.txt", "More than 33,000 Manitobans were evacuated")
check("mb/second-quarter-report-december2025.txt", "Wildfire Expenses 374")
check("mb/pa2025_26.txt", "Evacuee related costs 80", "Wildfire suppression 175", "wildfire response 321")
MB_URL = "https://web.gov.mb.ca/DisclosureOfContracts/ (vendor CANADIAN RED CROSS; JSON /DisclosureOfContracts/json/en/contracts/Vendor/?vendor=CANADIAN%20RED%20CROSS&year=2025)"
add(item="Evacuations: Manitoba evacuee related costs (Emergency Expenditures)", jurisdiction="MB", period="2025 (FY2025-26)",
    quantity="more than 33,000 Manitobans evacuated (59 communities)",
    amount_low_cad=to25_fy(80e6, 2025), amount_central_cad=to25_fy(80e6, 2025), amount_high_cad=to25_fy(80e6, 2025),
    method="audited year-end figure",
    source_name="Province of Manitoba, Annual Report and Public Accounts 2025-26, p. 12, 'Summary of Manitoba's Response to Unprecedented Wildfires in 2025'; Manitoba 2025 Wildfire Interim After Action Review (April 2026) for evacuee count",
    url="https://www.gov.mb.ca/asset_library/en/finances/annual-report-and-public-accounts-2025-26.pdf ; https://manitoba.ca/asset_library/en/wildfire/wildfire-report-april-2026.pdf",
    overlaps_with="gov_costs.csv Manitoba row counts only the 175 M suppression + 40 M + 14 M, so no overlap there; ISC EMAP estimate in gov_ (tier C) if Manitoba recovered First Nations evacuee costs from ISC; DFAA (no 2025 Manitoba order yet)",
    additive="yes", notes="The same table lists DFA program and other operating costs (12 M), left to property lines. Includes the Red Cross contracts below.")
add(item="Evacuations: Manitoba contracts with the Canadian Red Cross for evacuee services (inside the 80 M)", jurisdiction="MB", period="2025",
    quantity="2 contracts: 30,000,000.00 (2025-06-26) + 22,923,021.13 (2025-10-02)",
    amount_low_cad=to25_y(mb25, 2025), amount_central_cad=to25_y(mb25, 2025), amount_high_cad=to25_y(mb25, 2025),
    method="official contract disclosure, contract values (Transportation and Infrastructure; rationale 'Emergency services related to forest fires')",
    source_name="Government of Manitoba, Disclosure of Contracts (contracts of CAD 10,000 or more)", url=MB_URL,
    overlaps_with="Manitoba evacuee related costs (80 M) above", additive="no",
    notes="Shows what the 80 M bought: about two thirds went to the Red Cross for evacuee lodging, registration and care. Contract values, not final payments.")
add(item="Evacuations: Manitoba contract with the Canadian Red Cross for evacuee services", jurisdiction="MB", period="2024",
    quantity="1 contract (2024-05-07)", amount_low_cad=to25_y(mb24, 2024), amount_central_cad=to25_y(mb24, 2024),
    amount_high_cad=to25_y(mb24, 2024), method="official contract disclosure", source_name="Government of Manitoba, Disclosure of Contracts",
    url=MB_URL, overlaps_with="ISC EMAP; DFAA", additive="yes", notes="")

# Indigenous Services Canada: EMAP response reimbursements x wildfire share of First Nations evacuation events
check("isc/emap_key_stats.html", "For 2023 to 2024: Response: $369,501,840", "For 2024 to 2025: Response: $294,372,464",
      "For 2025 to 2026: Response: $688,648,240", "Date modified: 2026-06-30")
ISCEV = os.path.join(AN, "losses", "raw", "isc", "evac_stats.html")
check(ISCEV, "2023 to 2024: 86 short term, 4 long term*", "2024 to 2025: 26 short term", "2025 t0 2026: 52 short term, 21 long term*",
      "2023 to 2024: 11 short term", "2024 to 2025: 5 short term", "2025 to 2026: 7 short term, 1 long term*")
ISC = {2023: (369501840, 90, 11), 2024: (294372464, 26, 5), 2025: (688648240, 73, 8)}
for y, (resp, wf, fl) in ISC.items():
    share = wf / (wf + fl)
    add(item="Evacuations and response on reserve: ISC Emergency Management Assistance Program response reimbursements, wildfire share",
        jurisdiction="First Nations on reserve (all provinces)", period=f"FY{y}-{str(y + 1)[2:]}",
        quantity=f"response CAD {resp:,}; wildfire evacuations {wf}, flood evacuations {fl}",
        unit_cost=f"wildfire share {share:.3f}",
        amount_low_cad=to25_fy(resp * share, y), amount_central_cad=to25_fy(resp * share, y), amount_high_cad=to25_fy(resp, y),
        method="EMAP response costs reimbursed in the fiscal year x share of First Nations evacuation events that were wildfires (ISC evacuation statistics); high = all response costs",
        source_name="Indigenous Services Canada, Emergency Management Assistance Program - key statistics (modified 2026-06-30); ISC Wildland fire and flood evacuation statistics (modified 2026-06-01)",
        url="https://www.sac-isc.gc.ca/eng/1685047435261/1685047540188 ; https://isc.gc.ca/eng/1583177459681/1583177553276",
        overlaps_with="ALREADY COUNTED in gov_costs.csv (ISC EMAP response, tier C estimate, after removing SOPFEU suppression billed to ISC); provincial evacuation rows for First Nations evacuees (MB, SK, BC, AB host costs that ISC reimburses); ISC's Red Cross agreement 2324-HQ-000001 is paid from this; on-reserve suppression ISC pays to provincial agencies",
        additive="no", notes="Not added here because gov_ counts it; it is mostly First Nations evacuation costs, so the slide may show it under evacuations, counted once. All-hazard response reimbursements on reserve (evacuation travel, lodging, meals, community response; may include some on-reserve firefighting). The wildfire split is an assumption. Fiscal-year cash basis. FY2026-27 not yet published.")

# Federal agreements with the Canadian Red Cross (Public Safety Canada, proactive disclosure)
RCF = "grants/rc_ps-sp_1.html"
check(RCF, "7,494,198.79", "Alberta Fires 2023 Matching Program", "5,005,180.40", "Nova Scotia 2023 Matching Program", "688,541.28",
      "Support to Labrador Wildfires 2024", "12,622,466.32", "2024 Alberta Wildfires", "2,818,066.48", "2025 Saskatchewan Wildfires",
      "2,654,202.33", "2025 Newfoundland and Labrador Wildfires")
check("pages/ps_committee_note_donation_matching_20240322.html", "7,626,270", "5,005,180")
PSRC = [("Alberta Fires 2023 Matching Program (federal match of Red Cross donations)", "AB", 2023, 7494198.79,
         "Federal match. Agreement first disclosed at 5,589,208.00 (2023-05-08), amended to 7,494,198.79 (2024-11-06); Public Safety says 7,626,270 was raised and eligible to be matched. Alberta also matched; its amount was not found."),
        ("Nova Scotia 2023 Matching Program (federal match)", "NS", 2023, 5005180.40, "Nova Scotia also matched every dollar; its amount was not found."),
        ("Support to Labrador Wildfires 2024 (Red Cross shelter for evacuees, Humanitarian Workforce program)", "NL", 2024, 688541.28, ""),
        ("Early and Long-Term Recovery Support for those Impacted by the 2024 Alberta Wildfires (Jasper focus)", "AB", 2024, 12622466.32,
         "Recovery support; part may overlap property or recovery lines of other agents."),
        ("Early and Long-Term Recovery Support for those Impacted by the 2025 Saskatchewan Wildfires", "SK", 2025, 2818066.48, "Recovery support."),
        ("Early and Long-Term Recovery Support for those Impacted by the 2025 Newfoundland and Labrador Wildfires", "NL", 2025, 2654202.33, "Recovery support.")]
for name, j, y, v, n in PSRC:
    rec = name.startswith("Early and Long-Term Recovery")
    add(item="Evacuations and relief: federal agreement with the Canadian Red Cross - " + name, jurisdiction=j, period=str(y),
        amount_low_cad=to25_y(v, y), amount_central_cad=to25_y(v, y), amount_high_cad=to25_y(v, y),
        method="agreement value in the federal Grants and Contributions proactive disclosure (Public Safety Canada)",
        source_name="Government of Canada, Proactive Disclosure - Grants and Contributions (search.open.canada.ca, owner Public Safety Canada, 'Red Cross')",
        url="https://search.open.canada.ca/grants/?owner_org=ps-sp&search_text=%22Red%20Cross%22",
        overlaps_with=("reference row in gov_costs.csv too; household recovery support overlaps the property lines" if rec
                       else "ALREADY COUNTED in gov_costs.csv (Public Safety Canada wildfire agreements rows)"),
        additive="no", notes=n + " Agreement value is the committed amount. Not added here: " +
        ("recovery support is a transfer toward losses counted in the property lines." if rec else "gov_ counts it."))

# EI and other income support (transfers: overlap lost wages; not additive)
QP = pd.read_csv(os.path.join(AN, "losses", "raw", "isc", "qpnotes_wildfire_subset.csv"))
q = dict(zip(QP.reference_number, (QP.response_en.fillna("") + " " + QP.background_en.fillna("") + " " + QP.additional_information_en.fillna(""))))
assert "As of September 9, 2024, over 3,054 EI applications had been received related to the 2024 wildfire season." in q["CSDec2024_009"]
assert "about 85,000 Canadians have been evacuated due to wildfires this year" in q["EF_063_20260105"]
assert "evacuations orders have lasted more than 18 days" in q["EF_063_20260105"]
check("pages/gazette_sor2025-10_ei_pilot23.html", "$3.8 million", "$1.8 million", "August 17, 2024", "September 12, 2024")
add(item="Income support: EI disaster pilot (300-hour credit), Jasper and Bunibonibee Cree Nation, expected benefits", jurisdiction="AB, MB", period="2024 evacuations (claims to 2025-07-19)",
    quantity="about 1,030 claims", amount_low_cad=to25_y(3.8e6, 2024), amount_central_cad=to25_y(4.3e6, 2024), amount_high_cad=to25_y(4.3e6, 2024),
    method="regulatory impact analysis: CAD 3.8 M present value (4.3 M undiscounted) in benefits; ESDC operating cost CAD 1.8 M not included here",
    source_name="Canada Gazette Part II, SOR/2025-10, Regulations Amending the Employment Insurance Regulations (Pilot Project No. 23), RIAS",
    url="https://gazette.gc.ca/rp-pr/p2/2025/2025-02-12/html/sor-dors10-eng.html", overlaps_with="lost work and wages (benefits replace lost income)",
    additive="no", notes="Transfer. ESDC also reported over 3,054 EI applications linked to the 2024 season by 2024-09-09 (QP note CSDec2024_009). Jasper order July 22 to August 17, 2024; Bunibonibee August 13 to September 12, 2024.")

# =============================================================== 3. LOST WORK AND WAGES
sc = os.path.join(RAW, "statcan")
awe = pd.read_csv(os.path.join(sc, "14100204", "14100204.csv"), usecols=["REF_DATE", "GEO", "Type of employees", "Overtime",
                  "North American Industry Classification System (NAICS)", "VALUE"])
awe = awe[(awe.GEO == "Canada") & (awe["Type of employees"] == "All employees") & (awe.Overtime == "Including overtime")
          & awe["North American Industry Classification System (NAICS)"].str.startswith("Industrial aggregate excluding unclassified")]
AWE = awe.set_index("REF_DATE").VALUE.to_dict()
mon = pd.read_csv(os.path.join(sc, "14100223", "14100223.csv"), usecols=["REF_DATE", "GEO", "Estimate",
                  "North American Industry Classification System (NAICS)", "VALUE"])
mon = mon[(mon.GEO == "Canada") & mon.Estimate.str.startswith("Average weekly earnings")
          & mon["North American Industry Classification System (NAICS)"].str.startswith("Industrial aggregate excluding unclassified")
          & mon.REF_DATE.str.startswith("2026")]
AWE[2026] = mon.VALUE.mean()
awe_2026_months = f"{mon.REF_DATE.min()} to {mon.REF_DATE.max()}"
lfs = pd.read_csv(os.path.join(sc, "14100327", "14100327.csv"), usecols=["REF_DATE", "GEO", "Labour force characteristics", "Gender", "Age group", "VALUE"])
EMP = lfs[(lfs.GEO == "Canada") & (lfs.Gender == "Total - Gender") & (lfs["Age group"] == "15 years and over")
          & (lfs["Labour force characteristics"] == "Employment")].set_index("REF_DATE").VALUE.to_dict()
pop = pd.read_csv(os.path.join(AN, "health", "raw", "deaths", "17100005", "17100005.csv"), usecols=["REF_DATE", "GEO", "Gender", "Age group", "VALUE"])
POP = pop[(pop.GEO == "Canada") & (pop.Gender == "Total - gender") & (pop["Age group"] == "All ages")].set_index("REF_DATE").VALUE.to_dict()
ER = {y: EMP[y] * 1000 / POP[y] for y in (2023, 2024, 2025)}
ER[2026] = ER[2025]
check("pages/statcan_41-20-0002_2023004_status_fn_snapshot.html", "Employment rate 47.2 47.1 60.2 58.7 76.0 74.1")
FNF = 47.1 / 74.1                     # on-reserve vs non-Indigenous employment rate, 2021 Census, ages 25-64
FN_SHARE_LONGRUN = 0.275              # Christianson et al. 2024 (CWFEDB 1980-2021): First Nations on reserve = 27.5% of evacuees
csd = {r["REF_AREA"]: int(r["OBS_VALUE"]) for r in csv.DictReader(open(os.path.join(sc, "csd_pop_jasper_ykn.csv")))}
JASPER, SUMMERLAND = csd["2021A00054815033"], csd["2021A00055907035"]
assert JASPER == 4738 and SUMMERLAND == 12042
check("bc2026/summerland_20260808_order.pdf.txt" if os.path.exists(os.path.join(RAW, "bc2026", "summerland_20260808_order.pdf.txt")) else "bc2026/rdos_5811.html",
      "The entire District of Summerland is on Evacuation Order (5,688 properties)")
ISC_FN = {2024: 15469, 2025: 44852, 2026: 8805}
N = {2023: (EV[2023][1],) * 3,
     2024: (EV[2024][1] - (25000 - JASPER), EV[2024][1] - (20000 - JASPER), EV[2024][1]),
     2025: (EV[2025][1],) * 3,
     2026: (ISC_FN[2026] + SUMMERLAND,) * 3}            # low, central, high
FN = {2023: (round(FN_SHARE_LONGRUN * EV[2023][1]), 0, 0), 2024: (ISC_FN[2024], ISC_FN[2024], 0),
      2025: (ISC_FN[2025], ISC_FN[2025], 0), 2026: (ISC_FN[2026], ISC_FN[2026], 0)}
D = {2023: (7.0, 12.5, 18.0), 2024: (7.0, 12.5, 18.0), 2025: (12.5, 18.0, 21.0), 2026: (7.0, 12.5, 18.0)}
wrows = []
for y in (2023, 2024, 2025, 2026):
    res = []
    for k in range(3):
        n, fn, d = N[y][k], FN[y][k], D[y][k]
        workers = (n - fn) * ER[y] + fn * ER[y] * FNF
        wdays = workers * d * 5 / 7
        wage = wdays * AWE[y] / 5
        res.append((n, fn, workers, d, wdays, wage, to25_y(wage, y)))
    wrows.append(dict(year=y, evacuees_low=res[0][0], evacuees_central=res[1][0], evacuees_high=res[2][0],
                      fn_on_reserve_adjusted_low=res[0][1], fn_on_reserve_adjusted_central=res[1][1],
                      employed_per_person=round(ER[y], 5), fn_employment_factor=round(FNF, 4),
                      workers_low=round(res[0][2]), workers_central=round(res[1][2]), workers_high=round(res[2][2]),
                      days_away_low=res[0][3], days_away_central=res[1][3], days_away_high=res[2][3],
                      workdays_lost_low=round(res[0][4]), workdays_lost_central=round(res[1][4]), workdays_lost_high=round(res[2][4]),
                      avg_weekly_earnings=round(AWE[y], 2), wages_nominal_low=round(res[0][5]), wages_nominal_central=round(res[1][5]),
                      wages_nominal_high=round(res[2][5]), wages_2025d_low=round(res[0][6]), wages_2025d_central=round(res[1][6]),
                      wages_2025d_high=round(res[2][6])))
    note = {2023: "Evacuees: CWFEDB. Low case treats 27.5% as First Nations on reserve (long-run CWFEDB share; ISC publishes no 2023 count).",
            2024: f"Evacuees: CWFEDB 56,423 minus Jasper non-residents (central: 20,000 evacuated per ESDC minus 4,738 residents; low: 25,000 per Public Safety minus 4,738; high: none removed). First Nations 15,469 (ISC, Apr-Sep 2024).",
            2025: "Evacuees: CWFEDB. First Nations 44,852 (ISC, Apr 1 to Aug 20, 2025). Days: ESDC average order length more than 18 days (central), 30% lasted 21 days or more (high 21), long-run CWFEDB 12.5 (low).",
            2026: f"PARTIAL: only ISC First Nations evacuees (8,805, Apr 1 to Oct 2, 2026) and the District of Summerland ({SUMMERLAND:,} residents, whole District ordered out 2026-08-08). No national 2026 count exists yet. Earnings: SEPH {awe_2026_months} mean; employment ratio of 2025."}[y]
    add(item="Lost work and wages of evacuated workers", jurisdiction="Canada", period=str(y),
        quantity=f"{round(res[1][4]):,} workdays lost ({round(res[0][4]):,} to {round(res[2][4]):,})",
        unit_cost=f"SEPH average weekly earnings {AWE[y]:.2f} / 5 per workday (nominal {y})",
        amount_low_cad=res[0][6], amount_central_cad=res[1][6], amount_high_cad=res[2][6],
        method="evacuees x employed persons per resident (LFS employment 15+ / July 1 population) x days away x 5/7 workdays x daily earnings; First Nations on-reserve evacuees get 0.636 of the employment ratio (2021 Census on-reserve vs non-Indigenous employment rate) in low and central",
        source_name=CWF_SRC + "; StatCan 14-10-0204-01 (SEPH annual AWE incl. overtime, all employees), 14-10-0223-01 (monthly), 14-10-0327-01 (LFS), 17-10-0005-01 (population); Christianson et al. 2024 IJWF 33 WF23097 (CWFEDB: 7.2 M person-days for 576,747 evacuees = 12.5 days; median event 7 days); ESDC QP note EF_063_20260105; ISC; StatCan 41-20-0002 (2023)",
        url=CWF_URL + " ; https://www150.statcan.gc.ca/n1/tbl/csv/14100204-eng.zip ; https://www150.statcan.gc.ca/n1/tbl/csv/14100327-eng.zip ; https://doi.org/10.1071/WF23097 ; https://search.open.canada.ca/qpnotes/record/esdc-edsc,EF_063_20260105",
        overlaps_with="econ_costs.csv GDP-loss and production rows (oil and gas shut-ins AB 2023 and 2025, accommodation, rail, iron ore, forestry): their value includes wages of the same evacuated workers, so count those wages once; EI benefits, NWT Evacuee Income Disruption Support, Nova Scotia Emergency Relief Grant and the EI pilot replace part of this income (transfers; not added). Alberta and Saskatchewan evacuation payments are for living costs and do not overlap.",
        additive="yes", notes=note + " Gross loss of work time, whoever bears it (worker or employer). Ignores remote work and paid leave (overstates) and self-employed income, workers outside evacuation zones whose workplaces closed, and smoke-related absences (understate).")
pd.DataFrame(wrows).to_csv(os.path.join(CF, "health_lost_wages_by_year.csv"), index=False)

# HC morbidity cost detail file
det = []
for lbl, tab in (("respiratory", resp_tab), ("cardiac", card_tab)):
    for _, r in tab.iterrows():
        det.append(dict(group=lbl, cmg=r["Case Mix Group"], cmg_description=r["Case Mix Group (description)"],
                        typical_cases_fy2021_22=int(r.vol), avg_hospital_cost_fy2021_22=r.cost))
pd.DataFrame(det).to_csv(os.path.join(CF, "health_hc_morbidity_costs.csv"), index=False)

# =============================================================== write
cols = ["item", "jurisdiction", "period", "quantity", "unit_cost", "amount_low_cad", "amount_central_cad", "amount_high_cad",
        "dollars_basis", "method", "source_name", "url", "accessed", "overlaps_with", "additive", "notes"]
df = pd.DataFrame(rows)[cols]
txt = " ".join(df.astype(str).values.ravel())
assert "\u2014" not in txt, "em dash in output"
df.to_csv(os.path.join(CF, "health_costs.csv"), index=False)

# summary
a = df[df.additive == "yes"].copy()
for c in ("amount_low_cad", "amount_central_cad", "amount_high_cad"):
    a[c] = pd.to_numeric(a[c])


def grp(i):
    return "Health care" if i.startswith("Health care") else ("Lost work and wages" if i.startswith("Lost work") else "Evacuations")


a["group"] = a.item.map(grp)
s = a.groupby("group")[["amount_low_cad", "amount_central_cad", "amount_high_cad"]].sum()
s.loc["TOTAL"] = s.sum()
print((s / 1e6).round(1).to_string())
print()
print(f"ED unit cost direct {ed_direct}, full {ed_full:.2f}; PCE resp {resp_c:.0f} ({resp_lo:.0f}-{resp_hi:.0f}), card {card_c:.0f} ({card_lo:.0f}-{card_hi:.0f}); f_ed {f_ed:.4f} f_pce {f_pce:.4f}")
print("HC 2023 ED", [round(x) for x in ed_amt], "adm", [round(x) for x in adm_amt])
print("scaling", [(y, round(r, 4)) for y, r in hc_scaled])
print(pd.DataFrame(wrows)[["year", "workers_central", "workdays_lost_central", "wages_2025d_low", "wages_2025d_central", "wages_2025d_high"]].to_string(index=False))
print("rows", len(df), "additive", len(a))
