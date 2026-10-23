"""Step 7: city search table for the site (city_search_table.json + .csv).
One record per StatCan 2021 population centre (1,026) plus the smoke-monitor towns that are
not population centres. Fields: nearest 2026 fire (from city_nearest_fire.csv), smoke-day
counts 2018-2026 where the PC has its own PM2.5 monitor (Kanata and White Rock have none;
the Ottawa - Gatineau and Vancouver series are attached as clearly flagged proxies),
province wildfire cost per resident (BC, ON, AB, SK only; 2021 census population).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

near = pd.read_csv(f"{OUT}/city_nearest_fire.csv", dtype={"pcuid": str})
smoke = pd.read_csv(f"{OUT}/city_smoke_days.csv", dtype={"pc_code": str})
smap = pd.read_csv(f"{DATA}/smoke-cost/city_station_map.csv", dtype={"pc_code": str})
cost = pd.read_csv(f"{OUT}/cost_per_hectare.csv")

# smoke city -> PCUID
name_fix = {"Houston BC": ("Houston", "BC"), "Golden": ("Golden", "BC"), "Sudbury": ("Sudbury", "ON")}
city2pc = {}
for _, r in smap.iterrows():
    if isinstance(r.pc_code, str) and r.pc_code:
        city2pc[r.city] = r.pc_code
        continue
    nm, pv = name_fix.get(r.city, (r.city, None))
    h = near[near.name == nm]
    if pv:
        h = h[h.prov.str.contains(pv)]
    if len(h) == 1:
        city2pc[r.city] = h.pcuid.iloc[0]
pc2city = {v: k for k, v in city2pc.items()}
proxies = {"Kanata": "Ottawa - Gatineau", "White Rock": "Vancouver"}
not_pc = sorted(set(smap.city) - set(city2pc))
print("smoke cities matched to PCs:", len(city2pc), "not PCs:", not_pc)


def smoke_block(city, proxy_for=None):
    g = smoke[smoke.city == city].sort_values("year")
    if g.empty:
        return None
    yrs = {}
    for _, r in g.iterrows():
        yrs[str(int(r.year))] = dict(days_gt27=int(r.days_gt27), days_gt60=int(r.days_gt60),
                                     days_gt100=int(r.days_gt100), days_with_data=int(r.days_with_data),
                                     adequate_coverage=bool(r.adequate), data_basis=r.data_basis,
                                     worst_day=r.worst_day, worst_day_pm25=float(r.worst_day_pm25))
    last = g.iloc[-1]
    blk = dict(monitor_series=city, proxy=proxy_for is not None, by_year=yrs)
    if proxy_for:
        blk["proxy_note"] = f"No PM2.5 monitor inside {proxy_for}; series is for {city}."
    r26 = g[g.year == 2026]
    if len(r26) and r26.adequate.iloc[0]:
        r26 = r26.iloc[0]
        blk["rank_2026_days_gt27"] = int(r26.rank2026_days_gt27)
        blk["rank_2026_of_years"] = int(r26.n_adequate_years)
        blk["years_tied_with_2026"] = int(r26.years_tied2026_days_gt27)
    return blk


cost_by_prov = {}
for p, g in cost.groupby("province"):
    g = g.sort_values("fire_season")
    act = g[~g.cost_status.str.startswith("forecast")]
    la = act.iloc[-1]
    blk = dict(province=p, definition=la.definition, unit=la.unit,
               latest_season=int(la.fire_season), latest_cost_cad_m=float(la.cost_cad_m),
               latest_cost_per_resident_cad=float(la.cost_per_resident_cad), latest_status=la.cost_status,
               population_basis="2021 Census")
    f26 = g[g.fire_season == 2026]
    if len(f26):
        f = f26.iloc[0]
        blk.update(cost_2026_cad_m=float(f.cost_cad_m), cost_2026_per_resident_cad=float(f.cost_per_resident_cad),
                   cost_2026_status=f.cost_status, cost_2026_definition=f.definition)
    else:
        blk["cost_2026_status"] = "not available"
    blk["series"] = {str(int(r.fire_season)): float(r.cost_per_resident_cad) for _, r in g.iterrows()}
    cost_by_prov[p] = blk

recs = []
for _, r in near.iterrows():
    provs = r.prov.split(",")
    rec = dict(pcuid=r.pcuid, name=r["name"], prov=r.prov, pop2021=int(r.pop2021), pop_rank_2021=int(r.pop_rank_2021),
               lat=float(r.lat), lon=float(r.lon), is_population_centre=True,
               nearest_fire_2026=dict(edge_km=float(r.nearest_fire_edge_km), centre_km=float(r.nearest_fire_centre_km),
                                      direction_from_centre=r.direction_from_centre, fire_prov=r.nearest_fire_prov,
                                      first_detected=r.nearest_fire_first_detected,
                                      last_detected=r.nearest_fire_last_detected,
                                      outline_ha=float(r.nearest_fire_outline_ha),
                                      agency_reported_fire_within_5km=bool(r.nearest_fire_agency_match),
                                      outline_class=r.nearest_fire_outline_class,
                                      nearest_agency_matched_edge_km=float(r.nearest_agency_matched_fire_edge_km)))
    if r.pcuid in pc2city:
        rec["smoke"] = smoke_block(pc2city[r.pcuid])
    elif r["name"] in proxies:
        rec["smoke"] = smoke_block(proxies[r["name"]], proxy_for=r["name"])
    else:
        rec["smoke"] = None
    cp = [cost_by_prov[p] for p in provs if p in cost_by_prov]
    rec["province_cost"] = {k: v for k, v in cp[0].items()} if cp else None
    recs.append(rec)

# smoke towns that are not population centres: own record with nearest fire from station location
st = pd.read_csv(f"{DATA}/smoke-cost/stations_pm25_naps.csv", dtype=str)
extra = pd.read_csv(f"{DATA}/smoke-cost/airnow_sites_not_in_naps_list.csv", dtype=str)
fires = gpd.read_file(f"{WORK}/fires_2026.gpkg")
fires = fires[~fires.exclude_from_distance.astype(bool)].reset_index(drop=True)   # 00c: non-wildfire burns out
fires["fire_idx"] = np.arange(len(fires))
for c in not_pc:
    ids = smap.loc[smap.city == c, "naps_ids"].iloc[0]
    ids = [i for i in str(ids).split(";") if i]
    s = st[st.NAPS_ID.isin(ids)]
    if s.empty:
        continue
    lat, lon = s.Latitude.astype(float).mean(), s.Longitude.astype(float).mean()
    g = gpd.GeoDataFrame(geometry=gpd.points_from_xy([lon], [lat]), crs="EPSG:4326").to_crs(ALBERS)
    nf = nearest_fire(g, fires)
    pr = s.Province.iloc[0]
    rec = dict(pcuid=None, name=c, prov=pr, pop2021=None, lat=round(lat, 4), lon=round(lon, 4),
               is_population_centre=False,
               nearest_fire_2026=dict(edge_km=None, centre_km=round(float(nf.d_km.iloc[0]), 1),
                                      fire_prov=nf.fire_prov.iloc[0],
                                      outline_class=fires.set_index("fire_uid").loc[nf.fire_uid.iloc[0], "outline_class"], first_detected=nf.fire_first.iloc[0],
                                      last_detected=nf.fire_last.iloc[0],
                                      note="distance from the monitoring station location"),
               smoke=smoke_block(c))
    prov_abbr = {v.upper(): k for k, v in PR_NAME.items()}.get(pr.upper(), pr)
    rec["prov"] = prov_abbr
    rec["province_cost"] = cost_by_prov.get(prov_abbr)
    recs.append(rec)

meta = dict(
    generated="2026-10-21",
    fire_source="CWFIS FireM3 2026 perimeters, file stamped 2026-10-20 (hotspot-derived outlines, preliminary); 13 outlines classed agricultural/grass burn or military range with no agency-reported fire excluded (analysis/outline-check)",
    distance="geodesic km (GRS80); nearest candidate found in ESRI:102001 Canada Albers Equal Area",
    smoke_source="NAPS validated 2018-2024 + AirNow real-time 2024-2026 (city mean of stations, 24 h PM2.5); counts days with mean > 27, > 60, > 100 ug/m3; 2026 to Oct 19",
    smoke_rank="rank of 2026 among years 2018-2026 with adequate coverage (>= 115 of 153 May-Sep days), by days > 27 Jan 1-Oct 19; 1 = most",
    cost_note="Provincial definitions differ (BC BCWS total cost; ON Emergency Fire Fighting net of recoveries; AB all wildfire program lines; SK season costs in 2025 dollars). Not comparable across provinces. Per resident uses 2021 Census population.",
    n_records=len(recs))
with open(f"{OUT}/city_search_table.json", "w", encoding="utf-8") as fh:
    json.dump(dict(meta=meta, records=recs), fh, ensure_ascii=False, indent=1, default=lambda o: None if pd.isna(o) else o)

flat = pd.json_normalize(recs, sep=".")
flat = flat[[c for c in flat.columns if not c.startswith("smoke.by_year") and not c.startswith("province_cost.series")]]
flat.to_csv(f"{OUT}/city_search_table_flat.csv", index=False)
print("records", len(recs), "with smoke", sum(r["smoke"] is not None for r in recs),
      "with cost", sum(r["province_cost"] is not None for r in recs))
