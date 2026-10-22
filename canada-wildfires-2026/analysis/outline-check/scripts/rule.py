"""Classification rule for 2026 CWFIS M3 outlines. WRITTEN 2026-10-21 BEFORE ANY EVIDENCE
WAS COMPUTED OR LOOKED AT (only data schemas had been inspected). Do not tune after results.

The class uses ONLY physical evidence independent of agency lists (land cover, satellite
detections, DND land). Agency records are reported as separate columns, so the matched sample
(outlines that DO have an agency-reported fire) is a fair check of the rule: if the rule works,
nearly all of them should come out as "wildfire".

Land-cover groups (NRCan Land Cover of Canada 2020, 30 m, NALCMS legend). Shares are of LAND
pixels inside the outline (water 18 and nodata 0 excluded):
  forest   = 1 temperate/sub-polar needleleaf, 2 sub-polar taiga needleleaf,
             5 temperate/sub-polar broadleaf deciduous, 6 mixed forest
  shrub    = 8 temperate/sub-polar shrubland, 11 sub-polar/polar shrubland-lichen-moss
  grass    = 10 temperate/sub-polar grassland (prairie), 12 sub-polar/polar grassland-lichen-moss
  wetland  = 14
  cropland = 15
  urban    = 17
  barren   = 13 sub-polar/polar barren-lichen-moss, 16 barren lands; snow/ice 19
  natural  = forest + shrub + wetland + classes 12 and 13 (northern tundra types)
  agri     = cropland + class 10 (temperate grassland: prairie pasture/rangeland)

Detection days = distinct UTC days with at least one deduplicated hotspot inside the outline
(dedupe: one record per sensor per 1 km Albers grid cell per UTC day).
Season of the outline = month of its first deduplicated detection (fallback FIRSTDATE).
Spring/fall = March-May or September-November.

DND share = share of the outline's area on Department of National Defence land:
  Alberta: Government of Alberta official DND Military Base + Air Weapons Range polygons.
  Elsewhere: proxy from the Directory of Federal Real Property (custodian National Defence):
  union of circles centred on each DND parcel point with the parcel's land area
  (parcels >= 100 ha). The proxy is coarse; it is labelled as such in the output.

Rule, first match wins:
  R1 "military range"                       DND share >= 0.50
  R2 "possible industrial or urban heat"    urban + barren-16 share >= 0.30
  R3 "wildfire (unreported in agency lists)" natural share >= 0.60 and detection days >= 3
  R4 "likely agricultural or grass burn"    agri share >= 0.50 and detection days <= 3
                                            and season spring/fall
  R5 "unclear"                              everything else (class_detail says why)

For outlines that do have an agency match, R3's label is reported as "wildfire" (the
"unreported" wording applies only to the 80 unmatched).
"""
FOREST = (1, 2, 5, 6)
SHRUB = (8, 11)
GRASS = (10, 12)
WETLAND = (14,)
CROPLAND = (15,)
URBAN = (17,)
BARREN = (13, 16, 19)
WATER = 18
NATURAL = FOREST + SHRUB + WETLAND + (12, 13)
AGRI = (15, 10)
URBAN_BARREN = (17, 16)

DND_MIN = 0.50
URBAN_MIN = 0.30
NATURAL_MIN = 0.60
DAYS_SEVERAL = 3
AGRI_MIN = 0.50
AGRI_MAX_DAYS = 3
SPRING_FALL = (3, 4, 5, 9, 10, 11)
DFRP_MIN_HA = 100.0
AGENCY_KM = 5.0          # agency evidence: record within 5 km of the outline
AGENCY_DAYS = 30         # point records: date within [first-30 d, last+30 d]


def classify(dnd_share, urban_barren, natural, agri, det_days, season_month):
    if dnd_share is not None and dnd_share >= DND_MIN:
        return "military range", f"DND share {dnd_share:.2f}"
    if urban_barren >= URBAN_MIN:
        return "possible industrial or urban heat", f"urban+barren {urban_barren:.2f}"
    if natural >= NATURAL_MIN and det_days >= DAYS_SEVERAL:
        return "wildfire", f"natural {natural:.2f}, {det_days} detection days"
    sf = season_month in SPRING_FALL
    if agri >= AGRI_MIN and det_days <= AGRI_MAX_DAYS and sf:
        return "likely agricultural or grass burn", f"agri {agri:.2f}, {det_days} days, month {season_month}"
    # unclear: say which condition failed
    if natural >= NATURAL_MIN:
        why = f"mostly natural cover ({natural:.2f}) but only {det_days} detection day(s)"
    elif agri >= AGRI_MIN:
        why = (f"mostly agricultural/grass ({agri:.2f}) but "
               + ("summer" if not sf else f"{det_days} detection days"))
    else:
        why = f"mixed cover (natural {natural:.2f}, agri {agri:.2f}), {det_days} detection days"
    return "unclear", why
