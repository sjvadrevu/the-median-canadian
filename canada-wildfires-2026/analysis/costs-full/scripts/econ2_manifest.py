"""econ2_manifest.py: every download and web read used by the econ2 round, with access time.
Sources: work/econ2_downloads.tsv (econ2_fetch.sh log), the StatCan Daily probe files (raw/econ2/statcan_daily/probe, fetched
with curl directly; time = file modification time), pages read with WebFetch (not saved; listed by hand below), round-one
files reused read-only (their URLs come from econ_manifest.csv, gov_manifest.csv and health_manifest.csv), and the data
services used by the satellite counts. Columns as econ_manifest.csv.
usage: python3 -I econ2_manifest.py -> costs-full/econ2_manifest.csv"""
import csv, datetime, hashlib, os, re

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []


def meta(path):
    p = os.path.join(B, path)
    if not os.path.exists(p):
        return "", ""
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    return os.path.getsize(p), h


def title_of(path):
    p = os.path.join(B, path)
    try:
        t = open(p, errors="ignore").read(200000)
        m = re.search(r"<title[^>]*>(.*?)</title>", t, re.S | re.I)
        if m:
            s = m.group(1).replace("&amp;", "&")
            s = re.sub(r"\s*(&#8212;|&#8211;|&mdash;|&ndash;|\u2014|\u2013)\s*", ": ", s)  # no em or en dashes in the manifest
            return " ".join(re.sub(r"&#160;|&nbsp;", " ", s).split())[:160]
    except Exception:
        pass
    return ""


PUB = [("statcan", "Statistics Canada"), ("bchydro", "BC Hydro"), ("bcuc", "BC Utilities Commission"), ("tnrd", "Thompson-Nicola Regional District"),
       ("eoc_tnrd", "Thompson-Nicola Regional District"), ("bcws", "BC Wildfire Service (BC Data Catalogue)"), ("csrd", "Columbia Shuswap Regional District"),
       ("nl/", "Government of Newfoundland and Labrador"), ("nlpower", "Newfoundland Power"), ("ns/", "Government of Nova Scotia"),
       ("nwt/", "Government of the Northwest Territories / NWT Legislative Assembly"), ("sk/", "Government of Saskatchewan"),
       ("hydroquebec", "Hydro-Quebec"), ("hydroone", "Hydro One"), ("boc", "Bank of Canada"), ("bc/", "Government of British Columbia"),
       ("quebec/desjardins", "Desjardins Economic Studies (not official; pointer only)"), ("ibc", "Insurance Bureau of Canada [INDUSTRY]"), ("cn/", "CN (SEC EDGAR)")]


def publisher(path):
    for k, v in PUB:
        if k in path:
            return v
    return ""


# 1. econ2_fetch.sh log
for line in open(os.path.join(B, "work", "econ2_downloads.tsv")):
    lp, url, ts, code, by, sha = line.rstrip("\n").split("\t")
    st = "ok" if code == "200" else f"failed (HTTP {code}); read with WebFetch where noted" if code in ("403",) else f"not used (HTTP {code})"
    rows.append(dict(local_path=lp if os.path.exists(os.path.join(B, lp)) else "", url=url, accessed_utc=ts, http_code=code, bytes=by, sha256_16=sha,
                     publisher=publisher(lp), title_or_description=title_of(lp) if lp.endswith((".htm", ".html")) else os.path.basename(lp),
                     data_type="industry" if "ibc" in lp else "official" if "desjardins" not in lp else "other (pointer)", status=st))
# 2. StatCan Daily probe
pd_ = os.path.join(B, "raw", "econ2", "statcan_daily", "probe")
for f in sorted(os.listdir(pd_)):
    lp = f"raw/econ2/statcan_daily/probe/{f}"; d = f[2:8]
    by, sha = meta(lp)
    ts = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(B, lp)), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows.append(dict(local_path=lp, url=f"https://www150.statcan.gc.ca/n1/daily-quotidien/{d}/{f[:-4]}-eng.htm", accessed_utc=ts, http_code=200, bytes=by,
                     sha256_16=sha, publisher="Statistics Canada", title_or_description=title_of(lp), data_type="official",
                     status="ok (checked for any wildfire mention: none)"))
# 3. pages read with WebFetch (not saved); accessed 2026-10-22 local time
WF = [
    ("https://www.castanetkamloops.net/news/Kamloops/627029/120-properties-mostly-residential-have-seen-structure-loss-due-to-Pear-Lake-wildfire", "Castanet Kamloops", "TNRD: 120 properties with structure loss, Pear Lake wildfire (Aug 5, 2026)", "news (pointer to TNRD statement)"),
    ("https://cfjctoday.com/2026/08/05/recovery-is-going-to-be-different-for-everybody-at-least-120-tnrd-properties-suffer-structure-loss-in-pear-lake-fire/", "CFJC Today", "TNRD spokesperson: about 120 properties, count as of Aug 3, 2026", "news (pointer)"),
    ("https://www.ctvnews.ca/vancouver/bc-wildfires/article/devastation-chief-says-about-230-homes-destroyed-by-bc-wildfire/", "CTV News / Canadian Press", "OKIB chief: about 230 homes destroyed (Aug 4, 2026)", "news (pointer to First Nation statement)"),
    ("https://www.aptnnews.ca/national-news/we-measure-it-in-memories-lost-bradley-creek-wildfire-leaves-okanagan-indian-band-community-facing-long-road-to-recovery/", "APTN News", "Chief Dan Wilson: more than 30 member homes and more than 200 homes on CP lands (Aug 6, 2026)", "news (pointer)"),
    ("https://cfjctoday.com/?p=1121129", "CFJC Today / Canadian Press", "BC season summary Sep 10, 2026: Ministry of Emergency Management gives no total; Big Bar complex about 120 structures", "news (pointer)"),
    ("https://www.theweathernetwork.com/en/news/weather/forecasts/kingston-fire-destroys-203-structures-says-n-l-premier", "The Weather Network", "NL premier: 203 structures destroyed, by community, based on structures that lost power (Aug 19, 2025)", "news (pointer to government briefing)"),
    ("https://www.pentictonherald.ca/spare_news/article_b925091e-2262-5b62-af55-6b6900e9ffab.html", "Canadian Press (Penticton Herald)", "NL 2025 season review article: Kingston 203; May Small Point fire over 45 buildings incl. 12 homes", "news (pointer)"),
    ("https://amp.cbc.ca/news/canada/north/18-families-homes-lost-kfn-wildfire-1.6850420", "CBC North", "KFN chief: 18 families lost homes; band office destroyed (May 2023)", "news (pointer to First Nation statement)"),
    ("https://globalnews.ca/news/9687943/alberta-wildfires-fox-lake-little-red-river-cree-nation/amp", "Global News", "LRRCN emergency team: more than 85 structures lost in Fox Lake (May 10, 2023)", "news (pointer)"),
    ("https://edmonton.ctvnews.ca/like-a-war-zone-28-buildings-destroyed-by-wildfire-in-alta-m%C3%A9tis-settlement-1.6391591", "CTV Edmonton", "East Prairie Metis Settlement chair: 28 buildings incl. 14 homes (May 2023)", "news (pointer)"),
    ("https://edmonton.ctvnews.ca/it-s-heartbreaking-dozens-of-homes-destroyed-in-sturgeon-lake-cree-nation-west-of-valleyview-1.6404483", "CTV Edmonton", "Sturgeon Lake Cree Nation: at least 45 homes (May 18, 2023)", "news (pointer)"),
    ("https://yhcounty.ca/county-office/news/a-month-of-fires-and-resilience", "Yellowhead County", "May 23, 2023 update: homes and other structures lost, no count", "official"),
    ("https://www.cbc.ca/1.7018764", "CBC", "Alberta 2023 season end: structures lost in Sturgeon Lake, East Prairie, Fox Lake, Yellowhead County, no count", "news"),
    ("https://thenarwhal.ca/nopiming-wildfire-rebuild-report/", "The Narwhal", "Manitoba spokesperson: 21 cottages lost in Nopiming Provincial Park (2025)", "news (pointer)"),
    ("https://www.cbc.ca/lite/story/1.7540510", "CBC Manitoba", "Province: about 20 structures at Beresford Lake and 19 seasonal sites (May 22, 2025)", "news (pointer)"),
    ("https://www.cbc.ca/1.7555776", "CBC Manitoba", "Sherridon fire June 2025: no structure count", "news"),
    ("https://www.theweathernetwork.com/en/news/lifestyle/community/28-homes-lost-in-deadly-manitoba-fire-rural-municipality-says-lac-du-bonnet", "The Weather Network / CBC", "RM of Lac du Bonnet: 28 homes lost (May 2025); context only, not used in any amount", "news (pointer)", "WebSearch result title and summary (page not fetched)"),
    ("https://cfjctoday.com/2026/07/28/mayor-of-clinton-b-c-says-crew-assessing-damage-in-community-after-wildfire/", "CFJC Today", "Clinton mayor, Pear Lake fire: crews assessing damage; no count", "news"),
    ("https://www.insauga.com/northern-ontario-wildfires-destroy-homes-buildings-in-first-nation-community/", "insauga", "Ontario 2026 First Nation losses (not read)", "news", "WebFetch failed (page not fetched)"),
    ("https://www.ctvnews.ca/montreal/article/quebecs-2023-wildfires-cost-more-than-8-billion-displaced-27000-people", "CTV Montreal", "Quebec 2023 fires: no building count", "news"),
    ("https://www.noovo.info/nouvelle/feux-de-foret-post-mortem-dune-saison-catastrophique.html", "Noovo", "Quebec 2023 season post mortem: no building count", "news"),
    ("https://www.cp24.com/news/canada/2025/08/20/active-wildfires-in-new-brunswick-down-to-20-five-out-of-control", "CP24 / CTV", "New Brunswick Aug 20, 2025: no structures lost to wildfires in the province", "news (pointer to NB government update)"),
    ("https://en.wikipedia.org/wiki/2026_Canadian_wildfires", "Wikipedia", "2026 fires with structure losses (pointer only)", "other (pointer)"),
    ("https://globalnews.ca/news/11968629/northern-ontario-fires-lodges-lost/", "Global News", "Upsala area fire 2026: four lodges destroyed (not official)", "news"),
    ("https://www.castanetkamloops.net/news/Salmon-Arm/445060/New-count-pegs-estimated-number-of-buildings-destroyed-by-Shuswap-blaze-at-270", "Castanet", "Bush Creek East: 270 destroyed = CSRD 176 + TNRD 9 + Skwlax 85 (Sep 5, 2023)", "news (pointer)"),
    ("https://bc.ctvnews.ca/one-third-of-all-structures-on-b-c-first-nation-destroyed-by-bush-creek-east-wildfire-1.6536528", "CTV Vancouver", "Skwlax communications coordinator citing Canada Task Force 1: 85 destroyed, 13 damaged, 139 unscathed", "news (pointer to First Nation statement)"),
    ("https://www.csrd.bc.ca/CivicAlerts.aspx?AID=1724", "Columbia Shuswap Regional District", "CSRD alert Sep 5, 2023: 176 total losses, 50 partially damaged", "official"),
    ("https://canadianunderwriter.ca/2026/01/20/how-2025s-insured-cat-losses-compare-to-recent-years/", "Canadian Underwriter", "2025 insured catastrophe review: only Flin Flon and La Ronge fires named", "industry news"),
    ("https://insurance-canada.ca/2025/09/17/ibc-damage-manitoba-saskatchewan-wildfires/", "Insurance-Canada.ca (IBC release)", "Flin Flon complex $249M; Pisew over $50M (CatIQ) [INDUSTRY]", "industry"),
    ("https://www.insurancebusinessmag.com/ca/news/catastrophe/insurers-mobilize-as-bc-wildfires-destroy-hundreds-of-homes-and-force-8000-from-their-properties-585215.aspx", "Insurance Business", "2026 BC fires: no insured figure", "industry news"),
    ("https://treefrogcreative.ca/?p=360313", "Tree Frog (IBC release repost)", "IBC 2025 annual: no per-fire insured figures", "industry"),
    ("https://www.ctvnews.ca/vancouver/bc-wildfires/article/with-500-plus-structures-damaged-or-lost-bcs-fire-season-is-among-the-worst/", "CTV / Canadian Press", "BC 2026: more than 500 structures destroyed or damaged (unattributed)", "news"),
    ("https://norma.lexum.com/bcuc/orders/en/522430/1/document.do", "BC Utilities Commission", "Order G-236-24 (BC Hydro storm costs regulatory account): no wildfire amounts", "official"),
    ("https://www.ordersdecisions.bcuc.com/bcuc/orders/en/522330/1/document.do", "BC Utilities Commission", "Order G-177-24: storm restoration account scope, no amounts", "official"),
    ("https://www.ordersdecisions.bcuc.com/bcuc/orders/en/522462/1/document.do", "BC Utilities Commission", "Order G-256-24: storm restoration and evacuation relief breakdown reporting, no amounts", "official"),
    ("https://life.ieee.org/?p=14904", "IEEE (event abstract)", "ATCO Jasper rebuild: 22 km underground mainline, 4 km mountain cable, 4.16 kV to 25 kV; no cost", "other"),
    ("https://www.jasperlocal.com/2026/01/19/atco-defends-new-overhead-power-lines/", "Jasper Local", "ATCO Jasper rebuild: no cost", "news"),
    ("https://efiling-webapi.auc.ab.ca/Document/Get/799233", "Alberta Utilities Commission", "Decision 28320-D01-2023 (2016 Wood Buffalo Z factor), no Jasper 2024", "official"),
    ("https://efiling-webapi.auc.ab.ca/Document/Get/787175", "Alberta Utilities Commission", "Decision 26573-D01-2023, no Jasper wildfire", "official"),
    ("https://efiling-webapi.auc.ab.ca/Document/Get/787932", "Alberta Utilities Commission", "Decision 27062-D01-2023 (ATCO Electric 2023-2025 GTA), no Jasper wildfire", "official"),
    ("https://icscanada.ca/2023-nova-scotia-wildfires-after-action-report/", "ICS Canada", "2023 NS wildfires after-action report page: more than 200 homes lost; no utility costs on page", "other"),
    ("https://www.sec.gov/Archives/edgar/data/16868/000001686824000049/a2024q3pressreleasestatssu.htm", "CN (SEC EDGAR 6-K)", "CN Q3 2024 release: wildfires named, not quantified", "official (company filing)"),
    ("https://www.sec.gov/Archives/edgar/data/16868/000001686823000025/a2023q2mda.htm", "CN (SEC EDGAR 6-K)", "CN Q2 2023 MD&A: wildfire customer outages, not quantified", "official (company filing)"),
    ("https://globalnews.ca/news/12043917/saskatchewan-spsa-disaster-relief/", "Global News", "SPSA $50M special warrant Sep 2026; no 2025 PDAP figures", "news"),
    ("https://www.mbcradio.com/2025/07/province-announces-20-million-to-support-those-affected-by-wildfires", "MBC Radio", "SK $20M recovery funding through PDAP (Jul 7, 2025)", "news (pointer)"),
    ("https://www.canada.ca/en/public-safety-canada/news/2024/12/government-of-canada-provides-disaster-recovery-funding-to-nova-scotia-for-wildfires-flooding-and-storm-dorian.html", "Public Safety Canada", "DFAA interim payment $15,990,330 to NS for 2023 wildfires (Dec 12, 2024)", "official"),
    ("https://atlantic.ctvnews.ca/3-6-million-given-out-so-far-to-nova-scotians-impacted-by-wildfires-1.6439192", "CTV Atlantic", "$3.6M in $500 household payments (Red Cross), 2023", "news"),
]
for w in WF:
    url, pub, desc, dt = w[:4]
    st = w[4] if len(w) > 4 else "read with WebFetch (not saved)"
    rows.append(dict(local_path="", url=url, accessed_utc="2026-10-22 (WebFetch)" if "WebFetch" in st and "failed" not in st else "2026-10-22",
                     http_code="", bytes="", sha256_16="", publisher=pub, title_or_description=desc, data_type=dt, status=st))
# 4. round-one and sibling files reused read-only
REUSE = [
    ("raw/econ/mbhydro/mbh_quarterly_250930.pdf", "https://www.hydro.mb.ca/docs/corporate/quarterly-report-250930.pdf", "Manitoba Hydro", "Quarterly report, six months to Sep 30, 2025: wildfire capital costs of almost $24M (pole unit cost for the BC Hydro 2023 estimate)"),
    ("raw/econ/mbhydro/mbh_working_together_wildfire.html", "https://www.hydro.mb.ca/articles/2025/10/working-together-through-wildfire/", "Manitoba Hydro", "Working together through wildfire (Oct 2025): restoration cost and poles replaced (pole unit cost)"),
    ("raw/econ/manitoba/mb_wildfire_report_april_2026.pdf", "https://manitoba.ca/asset_library/en/wildfire/wildfire-report-april-2026.pdf", "Government of Manitoba", "2025 Wildfire Interim After Action Review (more than 1,200 Manitoba Hydro poles; no building count)"),
    ("raw/econ/saskatchewan/sk_crowns_northern_recovery_2025-11-04.html", "https://www.saskatchewan.ca/government/news-and-media/2025/november/04/crown-corporations-support-northern-wildfire-recovery-and-help-communities-and-families", "Government of Saskatchewan", "Crown corporations release: SaskPower $8.5M; SaskTel customer relief about $315,000; SaskEnergy no damage"),
    ("raw/econ/saskatchewan/sk_iaj_debates_20251201.pdf", "https://docs.legassembly.sk.ca/legdocs/Committees/IAJ/Debates/30L/20251201Debates-IAJ.pdf", "Legislative Assembly of Saskatchewan", "IAJ committee Dec 1, 2025: recovery task team $29.93M ($20M cleanup, $9.93M temporary housing), about $18M committed"),
    ("raw/econ/ntpc/ntpc_annual_report_2023_24.pdf", "https://www.ntpc.com/sites/default/files/2024-10/NTPC%20-%20Annual%20Report%20-%202023-24_1.pdf", "NWT Power Corporation", "Annual Report 2023-24: limited physical asset damage"),
    ("raw/econ/bc2026/okib_news.json", "https://www.okib.ca/wp-json/wp/v2/news?per_page=50", "Okanagan Indian Band", "OKIB news posts Jul to Oct 2026: no count of homes lost; TELUS 8 km pole line lost"),
    ("raw/econ/nl/nl_exec_0827n01.html", "https://www.gov.nl.ca/releases/2025/exec/0827n01/", "Government of Newfoundland and Labrador", "Aug 27, 2025 household and business supports"),
    ("raw/econ/agri/bc_news_2023AF0056.html", "https://news.gov.bc.ca/releases/2023AF0056-001624", "Government of BC", "2023 Canada-BC Wildfire and Drought AgriRecovery: up to $71M, not an estimate of damage"),
    ("raw/econ/agri/aafc_qp_2024_00131.html", "https://search.open.canada.ca/qpnotes/record/aafc-aac%2CAAFC-2024-QP-00131", "Agriculture and Agri-Food Canada", "QP note: up to $219M federal AgriRecovery for 2023 drought and wildfires (BC, AB, SK)"),
    ("raw/econ/agri/aafc_qp_2025_00023.html", "https://search.open.canada.ca/qpnotes/record/aafc-aac%2CAAFC-2025-QP-00023", "Agriculture and Agri-Food Canada", "QP note: $365M federal-provincial for 2023 drought and wildfires"),
    ("raw/econ/statcan_tables/36100434/36100434.csv", "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610043401", "Statistics Canada", "Table 36-10-0434-01 GDP by industry, monthly"),
    ("raw/econ/statcan_tables/36100106/36100106.csv", "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610010601", "Statistics Canada", "Table 36-10-0106-01 GDP implicit price index"),
    ("raw/econ/catiq/catiq_2026-09-15_baldrange.html", "https://public.catiq.com/2026/09/15/cad-313m-catiq-discloses-initial-loss-estimate-for-bald-range-fire/", "CatIQ [INDUSTRY]", "three new BC fire catastrophes declared in 2026 to Sep 15"),
    ("raw/econ/catiq/catiq_2026-10-06_baldrange2.html", "https://public.catiq.com/2026/10/06/catiq-discloses-third-loss-estimate-for-june-july-severe-storm-event-in-ontario-and-quebec-updated-loss-for-bald-range-fire/", "CatIQ [INDUSTRY]", "Bald Range $293M falls below the PERILS reporting threshold"),
    ("raw/econ/catiq/catiq_2026-01-20_annual2025.html", "https://public.catiq.com/2026/01/20/canadian-insured-losses-from-catastrophic-events-total-cad-2-4-b-in-2025-societal-losses-total-3-4-b/", "CatIQ [INDUSTRY]", "2025: first in fire catastrophes declared, all in provinces with no prior fire catastrophe"),
    ("raw/econ/catiq/catiq_2025-01-13_annual2024.html", "https://public.catiq.com/2025/01/13/canadian-insured-losses-from-catastrophic-events-total-can-8-5-billion-in-2024/", "CatIQ [INDUSTRY]", "CatIQ catastrophe = insured losses above CAN $30 million"),
    ("raw/health/nwt/nwt_em_annual_report_2025.pdf", "https://www.maca.gov.nt.ca/sites/maca/files/resources/nwt_emergency_management_annual_report_2025.pdf", "GNWT MACA", "2023 fires estimated $204.6M event costs; recovery work remaining"),
    ("raw/health/bc/emcr-annual-payment-report-2023_24.pdf", "https://www2.gov.bc.ca/assets/gov/public-safety-and-emergency-services/emergency-preparedness-response-recovery/embc/reports/emcr-annual-payment-report-2023_24.pdf", "BC EMCR", "EDMA s.10(2) payments by event (DFA not split out)"),
    ("raw/gov/ab/ab_2026-27_q1.pdf", "https://open.alberta.ca/dataset/9c81a5a7-cdf1-49ad-a923-d1ecb42944e4/resource/eaeb7a75-0c9f-4964-be53-0f1cc889ffab/download/tbf-2026-27-first-quarter-fiscal-update-economic-statement.pdf", "Government of Alberta", "2026-27 Q1: limited wildfire disruptions supported oil activity"),
    ("raw/gov/bc/bc_2026-27_q1.pdf", "https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/quarterly-reports/2026-27_first_quarterly_report.pdf", "Government of BC", "2026/27 First Quarterly Report: wildfire spending; no economic quantification"),
    ("raw/gov/mb/mb_q1_2026-27.pdf", "https://www.gov.mb.ca/asset_library/en/proactive/20262027/first-quarter-report-september2026.pdf", "Government of Manitoba", "2026/27 Q1: 2026 wildfire response inside Emergency Expenditures"),
    ("../property/work/da_values_2021.csv", "https://api.statcan.gc.ca/census-recensement/profile/sdmx/rest/data/STC_CP,DF_DA,1.3/A5..1.1474+1475.1", "Statistics Canada", "2021 Census average and median value of owner-occupied dwellings by DA (analysis/property)"),
]
for lp, url, pub, desc in REUSE:
    by, sha = meta(lp)
    rows.append(dict(local_path=lp, url=url, accessed_utc="2026-10-22 (round one download, reused read-only)", http_code="", bytes=by, sha256_16=sha,
                     publisher=pub, title_or_description=desc, data_type="industry" if "INDUSTRY" in pub else "official", status="reused"))
# 5. data services used by the satellite counts
SVC = [("https://earth-search.aws.element84.com/v1/search", "Element 84 Earth Search (Copernicus Sentinel-2 L2A COGs, AWS open data)", "Sentinel-2 L2A scenes; scene ids in work/econ2_sat/scenes_<job>_part<k>.csv"),
       ("https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv", "Microsoft Global ML Building Footprints (ODbL)", "Canada quadkey tile parts listed in analysis/losses/raw/buildings/dataset-links.csv, streamed by econ2_sat_02_footprints.py"),
       ("https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/NBAC_1972to2025_20260513_shp.zip", "Natural Resources Canada, National Burned Area Composite", "2023 and 2025 fire polygons (project copy: data/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp)"),
       ("https://openmaps.gov.bc.ca/geo/pub/wfs (WHSE_LAND_AND_NATURAL_RESOURCE.PROT_CURRENT_FIRE_POLYS_SP)", "BC Wildfire Service, BC Data Catalogue", "2026 official fire perimeters (raw/econ2/bcws)"),
       ("data/geo/indigenous/al_ta", "Natural Resources Canada, Aboriginal Lands of Canada", "reserve names for labels (project copy)"),
       ("data/geo/statcan/lpc_000b21a_popcentres_2021.gpkg", "Statistics Canada", "2021 population centres for labels (project copy)")]
for url, pub, desc in SVC:
    rows.append(dict(local_path="", url=url, accessed_utc="2026-10-22/23 UTC (streamed during runs)", http_code="", bytes="", sha256_16="", publisher=pub,
                     title_or_description=desc, data_type="official" if "Microsoft" not in pub and "Element" not in pub else "open data", status="used by scripts/econ2_sat_*"))
cols = ["local_path", "url", "accessed_utc", "http_code", "bytes", "sha256_16", "publisher", "title_or_description", "data_type", "status"]
with open(os.path.join(B, "econ2_manifest.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(len(rows), "manifest rows")
