"""Event table of OFFICIAL structure-damage figures, 2023-2026. Every number below was read from the issuing
organization's own page, PDF or feature service (copies under raw/), never from news. Counts from the Jasper feature
service are recomputed from the downloaded features. Blank = no official figure found (see 'searched')."""
import os, json
import pandas as pd, geopandas as gpd
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
j = gpd.read_file(os.path.join(P, "raw", "jasper", "jasper_damage_assessment_structures.geojson"))
j["Status"] = j.Status.fillna("").str.strip()
jc = j.Status.value_counts().to_dict()
jt = j[j.Value_Type.fillna("").str.strip() == "Jasper"].Status.value_counts().to_dict()
E = [
 dict(event="Jasper wildfire complex", year=2024, prov="AB", community="Jasper townsite and Jasper National Park",
      destroyed=jc.get("Destroyed"), damaged=jc.get("Visible Damage"), no_damage=jc.get("No Visible Damage"), destroyed_or_damaged=None,
      unit="structures (polygons; all types incl. park facilities)", as_of="2024-08 (rapid assessment; layer last edited 2026-08-28)",
      publisher="Municipality of Jasper (ArcGIS Online owner MOJ_GIS)", source="https://services7.arcgis.com/1glZz4XajYW77W8H/arcgis/rest/services/Damage_Assessment_Structures/FeatureServer/0",
      quote="layer snippet: 'Rapid damage assessment of structures - municipality of Jasper and surrounding areas. August 2024.'",
      licence="public ArcGIS Online item; no licence stated", point_data=True,
      note=f"2,800 polygons; {jc.get('',0)} have no status. Value_Type 'Jasper' (townsite buildings): {jt.get('Destroyed')} destroyed, {jt.get('Visible Damage')} visible damage, {jt.get('No Visible Damage')} no visible damage."),
 dict(event="Jasper wildfire complex", year=2024, prov="AB", community="Jasper townsite", destroyed=358, damaged=None, no_damage=None, destroyed_or_damaged=None,
      unit="structures (townsite)", as_of="page modified 2026-10-02", publisher="Parks Canada",
      source="https://parks.canada.ca/pn-np/ab/jasper/gestion-management/serviceimmobilier-realty/retablissement-recovery/stat-dashboard",
      quote="The initial rapid assessment identified 358 destroyed structures immediately following the 2024 Jasper wildfire. Further assessment showed that remediation was required at 375 properties. ... it is anticipated that rebuilding is required at 374 properties.",
      licence="Government of Canada terms (canada.ca)", point_data=False, note="374 properties to rebuild; 472 parcels carry a rebuild status in the Municipality's 'Rebuild Status of Fire-Destroyed Properties' layer (raw/jasper)."),
 dict(event="Upper Tantallon / Hammonds Plains wildfire", year=2023, prov="NS", community="Halifax Regional Municipality", destroyed=200, damaged=None, no_damage=None, destroyed_or_damaged=None,
      unit="structures (approx.), incl. 151 homes", as_of="2024-08-20 (report to Committee of the Whole)", publisher="Halifax Regional Fire & Emergency (HRM)",
      source="https://www.halifax.ca/sites/default/files/documents/city-hall/regional-council/240820cow4.pdf",
      quote="...required the evacuation of 16,400 people, and resulted in the loss of approximately 200 structures, including 151 homes.",
      licence="HRM public document", point_data=False, note="HRM: 166 properties fenced; 174 structure investigations; building permits for 120 dwelling units by 2024-05-13 (halifax.ca 'Moving forward' page)."),
 dict(event="Barrington Lake wildfire", year=2023, prov="NS", community="Shelburne County", destroyed=230, damaged=59, no_damage=None, destroyed_or_damaged=None,
      unit="structures", as_of="cited 2024-08-20", publisher="Halifax Regional Fire & Emergency (HRM), citing the Barrington Lake after-action review",
      source="https://www.halifax.ca/sites/default/files/documents/city-hall/regional-council/240820cow4.pdf",
      quote="...Shelburne County, which burned for weeks, destroying more than 23,000 hectares, 230 structures destroyed, 59 structures damaged, and requiring the evacuation of nearly 7,000 residents.",
      licence="HRM public document", point_data=False, note="Province of NS (2025-01-10): tax relief 'apply to 165 residential properties that were destroyed' across the two 2023 fires; NS after-action report: 'more than 200 homes lost'."),
 dict(event="McDougall Creek wildfire (with Clark Creek, Walroy Lake)", year=2023, prov="BC", community="West Kelowna, Westbank FN, Kelowna, Lake Country, RDCO", destroyed=None, damaged=None, no_damage=None, destroyed_or_damaged=200,
      unit="structures impacted (approx.)", as_of="2023-09 (plan); appendix dated 2023-10-10", publisher="City of Kelowna for the Central Okanagan Regional Emergency Program (RDCO site)",
      source="https://www.rdco.com/media/k3apxusq/debris-management-plan-mcdougall-creek-wildfire.pdf",
      quote="...burned some 14,000 hectares of land and impacted some 200 structures in five communities.",
      licence="RDCO public document", point_data=False, note="City of West Kelowna update 2023-08-26: 'total properties as of today remain at 84' damaged and/or lost (City only). RDCO property-status tool (cordemergency.ca/propertyinfo) could not be read (403 / permission timeout)."),
 dict(event="Bush Creek East wildfire", year=2023, prov="BC", community="North Shuswap (CSRD)", destroyed=176, damaged=50, no_damage=None, destroyed_or_damaged=None,
      unit="structures (approx.)", as_of="2023-09-04 14:00 (posted 2023-09-05)", publisher="Columbia Shuswap Regional District",
      source="https://www.csrd.bc.ca/CivicAlerts.aspx?AID=1724",
      quote="176 total structure losses, up from the previous total of 131 ... 50 partially damaged structures, up from the previous total of 37.",
      licence="CSRD public notice", point_data=False, note="Approximate; CSRD notes a full damage assessment could not be completed."),
 dict(event="Bush Creek East wildfire", year=2023, prov="BC", community="TNRD Electoral Area P", destroyed=9, damaged=2, no_damage=None, destroyed_or_damaged=None,
      unit="properties with structures destroyed / damaged", as_of="2023-08-23", publisher="Thompson-Nicola Regional District",
      source="https://www.tnrd.ca/tnrd-confirms-structural-impacts-on-11-properties-due-to-bush-creek-east-fire/",
      quote="structural impacts on 11 properties ... nine properties [where] structures have been destroyed and two [where] structures have been damaged",
      licence="TNRD public notice", point_data=False, note="Little Shuswap Lake Band losses: no official band publication found."),
 dict(event="Hay River / Enterprise wildfire", year=2023, prov="NT", community="Enterprise, Hay River corridor", destroyed=None, damaged=None, no_damage=None, destroyed_or_damaged=None,
      unit="", as_of="2023-08-13", publisher="Town of Hay River", source="https://hayriver.com/2023-wildfire-updates/",
      quote="Fires have led to property and structural loss in the area of Paradise Gardens south through Enterprise.",
      licence="", point_data=False, note="No count. GNWT newsroom and MACA chronology returned 503 / connection reset."),
 dict(event="SHOE fire (Flin Flon complex) and 2025 season", year=2025, prov="SK", community="Denare Beach and region", destroyed=400, damaged=None, no_damage=None, destroyed_or_damaged=None,
      unit="permanent residences (approx.), region of the SHOE fire", as_of="report published 2026-06", publisher="Government of Saskatchewan (MNP review of the 2025 season, citing SPSA estimates)",
      source="https://www.saskatchewan.ca/-/media/news-release-backgrounders/2026/jun/mnp-2025-wildfire-report.pdf",
      quote="These impacts included the destruction of approximately 400 permanent residences in the region (with approximately half being in Denare Beach) ... SPSA estimates indicate that more than half of the approximately 700 structures and 400 vehicles lost during the 2025 Wildfire Season are attributable to the SHOE Fire.",
      licence="Government of Saskatchewan terms", point_data=False, note="Season-wide SK: about 700 structures lost (SPSA estimate). 'detailed inventories of losses were not available'."),
 dict(event="Bald Range wildfire", year=2026, prov="BC", community="District of Summerland and RDOS Area F", destroyed=None, damaged=None, no_damage=None, destroyed_or_damaged=150,
      unit="structures damaged or destroyed (approx., preliminary)", as_of="FAQ page read 2026-10-21", publisher="District of Summerland",
      source="https://www.summerland.ca/city-services/eoc/bald-range-wildfire-home/bald-range-wildfire-faq",
      quote="Preliminary damage assessments indicate that approximately 110 structures have been damaged or destroyed in RDOS Electoral Area \"F\" (including Faulder and Meadow Valley), and approximately 40 structures within the District of Summerland.",
      licence="municipal web page", point_data=False, note="110 (RDOS Area F) + 40 (Summerland); not split into destroyed vs damaged; no structure-level layer published."),
 dict(event="Bradley Creek wildfire", year=2026, prov="BC", community="Okanagan Indian Band IR #1", destroyed=None, damaged=None, no_damage=None, destroyed_or_damaged=None,
      unit="", as_of="okib.ca news to 2026-10-20", publisher="Okanagan Indian Band", source="https://www.okib.ca/wp-json/wp/v2/news",
      quote="Members who experienced total loss are being supported through a separate recovery process.", licence="", point_data=False,
      note="All 88 OKIB news posts 2026-07-25 to 2026-10-20 read: no count of homes or structures lost is published."),
 dict(event="Lac du Bonnet wildfire", year=2025, prov="MB", community="RM of Lac du Bonnet", destroyed=None, damaged=None, no_damage=None, destroyed_or_damaged=None,
      unit="", as_of="", publisher="Province of Manitoba news releases (9 read, May-June 2025)", source="https://news.gov.mb.ca/news/index.html?item=69398",
      quote="", licence="", point_data=False, note="No structure count in provincial releases; RM of Lac du Bonnet site not located."),
 dict(event="Kingston wildfire", year=2025, prov="NL", community="Conception Bay North", destroyed=None, damaged=None, no_damage=None, destroyed_or_damaged=None,
      unit="", as_of="", publisher="Government of Newfoundland and Labrador", source="https://www.gov.nl.ca/releases/2025/jps/0811n08/",
      quote="", licence="", point_data=False, note="gov.nl.ca release pages returned HTTP 500 for every request."),
]
d = pd.DataFrame(E)
d.to_csv(os.path.join(P, "events_official.csv"), index=False)
print(d[["event", "year", "prov", "destroyed", "damaged", "destroyed_or_damaged", "unit"]].to_string())
