"""Priority 1: share of 2023-2026 area burned under full suppression vs modified / monitored / observation.

Two independent views.
A. Agency response label on each fire (work/fires.pkl from 02): share of agency-reported hectares by class within
   each province-year, applied to the official provincial total (NFD 2023-2025; 2026 official = agency fire list,
   which sums to the national official 4,500,984 ha). Parks Canada fires are counted in the province they lie in.
B. Official zone polygons over mapped burned area (NBAC 2023-2025, CWFIS M3 2026, the 240 m burn grids of
   analysis/forest), scaled to the official provincial total (official / mapped, same rule as analysis/forest):
     QC  SOPFEU intensive protection zone vs northern zone (data/geo/mb_qc_subareas/qc_sopfeu_protection_zones.gpkg)
     ON  MNR historical fire management zones (pre-2014; LIO_Open09/MapServer/32): Hudson Bay + Northern Boreal
         = extensive / observation; Boreal, Great Lakes-St. Lawrence, Southern = full or measured; Parks Zone separate
     YT  Yukon fire management zones (GeoYukon 2020): Critical + Full vs Strategic + Transitional + Wilderness
     AB  Forest Protection Area (Alberta Wildfire forest areas) vs outside it
Outputs: zone_share_agency_by_prov_year.csv, zone_share_polygons_by_prov_year.csv, zone_share_national.csv
"""
import json

import geopandas as gpd
import numpy as np
import pandas as pd
from affine import Affine
from rasterio import features

from common import BASE, DATA, OUT, RAW, WORK, SEASON

FW = BASE / "analysis/forest/work"
m = json.load(open(FW / "grid_meta.json"))
T = Affine(*m["transform"]); H, W = m["H"], m["W"]
asc = np.load(FW / "areal_scale_coarse.npy").astype("float64")
YEARS = [2023, 2024, 2025, 2026]

# ------------------------------------------------------------ official totals
n = pd.read_csv(SEASON / "NFD_-_Area_burned_by_month_-_EN_FR.csv")
off = n[n.Year.between(2023, 2025)].groupby(["ISO", "Year"])["Area (hectares)"].sum()
off.index.names = ["prov", "year"]
F = pd.read_pickle(WORK / "fires.pkl")
o26 = F[F.year == 2026].groupby("prov").size_ha.sum()
off = pd.concat([off, pd.concat({2026: o26}, names=["year", "prov"]).swaplevel()]).sort_index()

# ------------------------------------------------------------ A. agency labels
G = F[F.year.between(2023, 2026)]
pts = G.pivot_table(index=["prov", "year"], columns="resp", values="size_ha", aggfunc="sum", fill_value=0)
for k in ["full", "modified", "monitored", "zone_full", "zone_obs", "unclassified"]:
    if k not in pts:
        pts[k] = 0.0
pts = pts[["full", "modified", "monitored", "zone_full", "zone_obs", "unclassified"]]
tot = pts.sum(1)
share = pts.div(tot, axis=0)
A = share.mul(off.reindex(share.index), axis=0)
A.columns = [c + "_ha" for c in A.columns]
A["official_ha"] = off.reindex(share.index)
A["agency_points_ha"] = tot
A["points_over_official"] = tot / A.official_ha
A = A.reset_index()
A.to_csv(OUT / "zone_share_agency_by_prov_year.csv", index=False, float_format="%.1f")

# ------------------------------------------------------------ B. polygons
fma = pd.read_csv(DATA / "geo/fma_v2_attributes.csv")
prov_of = np.zeros(int(fma.fma_id.max()) + 1, dtype=object)
prov_of[:] = ""
prov_of[fma.fma_id.values] = fma.province.values
fid = np.load(FW / "fma_v2_id.npy", mmap_mode="r")


def zone_layers():
    zl = {}
    q = gpd.read_file(DATA / "geo/mb_qc_subareas/qc_sopfeu_protection_zones.gpkg")
    q["z"] = np.where(q.area_name.str.startswith("Intensive"), "full_zone", "observation_zone")
    zl["QC"] = q[["z", "geometry"]]
    o = gpd.read_file(RAW / "zones/on_fire_management_zones_hist.geojson")
    o["geometry"] = o.geometry.make_valid()
    o["z"] = o.FMZ_DESIGNATION.map({"Hudson Bay Zone": "observation_zone", "Northern Boreal Zone": "observation_zone",
                                    "Boreal Zone": "full_zone", "Great Lakes/St. Lawrence Zone": "full_zone",
                                    "Southern Ontario Zone": "full_zone", "Parks Zone": "parks_zone"})
    zl["ON"] = o[["z", "geometry"]]
    y = gpd.read_file("zip://" + str(RAW / "zones/yt_fire_management_zones.shp.zip"))
    y["z"] = np.where(y.FIRE_MZONE.isin(["Critical", "Full"]), "full_zone", "observation_zone")
    zl["YT"] = y[["z", "geometry"]]
    a = gpd.read_file(DATA / "geo/raw/ab_forest_areas.geojson")
    a["z"] = "full_zone"     # Forest Protection Area; everything outside is "outside_fpa"
    zl["AB"] = a[["z", "geometry"]]
    return zl


ZC = {"full_zone": 1, "observation_zone": 2, "parks_zone": 3}
ZN = {v: k for k, v in ZC.items()}
ZN[0] = "outside_fpa_or_unzoned"
zl = zone_layers()
rows = []
burn = {y: np.load(FW / f"burn_{y}.npy").astype(np.int64) for y in YEARS}
for p, g in zl.items():
    g = g.to_crs(m["crs"])
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    # raster window = zone layer bounds plus a 5-cell margin
    x0, y0, x1, y1 = g.total_bounds
    c0 = max(int((x0 - T.c) / 240) - 5, 0); c1 = min(int((x1 - T.c) / 240) + 5, W)
    r0 = max(int((T.f - y1) / 240) - 5, 0); r1 = min(int((T.f - y0) / 240) + 5, H)
    for y in YEARS:
        idx = burn[y]
        rr, cc = idx // W, idx % W
        # cells of this province (fma_v2 grid)
        pv = prov_of[np.asarray(fid[rr, cc])]
        sel = pv == p
        rr, cc = rr[sel], cc[sel]
        area = 5.76 / asc[np.minimum((rr) // m["step"], asc.shape[0] - 1), np.minimum(cc // m["step"], asc.shape[1] - 1)]
        inwin = (rr >= r0) & (rr < r1) & (cc >= c0) & (cc < c1)
        z = np.zeros(len(rr), dtype=np.uint8)
        if p not in globals().get("_zr", {}):
            tw = Affine(240, 0, T.c + c0 * 240, 0, -240, T.f - r0 * 240)
            # rasterize in priority order: observation, parks, then full on top only where not already set
            arr = np.zeros((r1 - r0, c1 - c0), dtype=np.uint8)
            for zname in ["observation_zone", "parks_zone", "full_zone"]:
                gg = g[g.z == zname]
                if len(gg):
                    a2 = features.rasterize(((geom, 1) for geom in gg.geometry), out_shape=arr.shape, transform=tw,
                                            fill=0, dtype="uint8")
                    arr[(a2 == 1) & (arr == 0)] = ZC[zname]
            globals().setdefault("_zr", {})[p] = arr
        arr = globals()["_zr"][p]
        z[inwin] = arr[rr[inwin] - r0, cc[inwin] - c0]
        for k in np.unique(z):
            rows.append(dict(prov=p, year=y, zone=ZN[int(k)], mapped_ha=float(area[z == k].sum())))
    print(p, "done", flush=True)
B = pd.DataFrame(rows).pivot_table(index=["prov", "year"], columns="zone", values="mapped_ha", fill_value=0)
B["mapped_total_ha"] = B.sum(1)
B["official_ha"] = off.reindex(B.index)
fac = B.official_ha / B.mapped_total_ha
for c in [c for c in B.columns if c.endswith("zone") or c.startswith("outside")]:
    B[c + "_scaled_ha"] = B[c] * fac
B["scale_factor"] = fac
B = B.reset_index()
B.to_csv(OUT / "zone_share_polygons_by_prov_year.csv", index=False, float_format="%.1f")
print(B.to_string())
