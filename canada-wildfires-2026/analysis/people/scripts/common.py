"""Shared paths and helpers for the people/smoke/cost analysis.

Distance method (used everywhere):
  1. Geometries are projected to ESRI:102001 Canada Albers Equal Area Conic.
  2. The nearest fire polygon is found with an STRtree (geopandas sjoin_nearest)
     in that projection.
  3. The reported distance is the GEODESIC distance (GRS80 ellipsoid, pyproj.Geod)
     between the two end points of the shortest line between the geometries in the
     Albers plane. This removes the Albers scale error (a few percent away from the
     50N/70N standard parallels); only the choice of end point comes from the plane.
  Distance 0 = point/polygon inside or touching a fire outline.
"""
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from pyproj import Geod, Transformer

BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
DATA = f"{BASE}/data"
OUT = f"{BASE}/analysis/people"
WORK = f"{OUT}/work"
os.makedirs(WORK, exist_ok=True)

ALBERS = "ESRI:102001"
GEOD = Geod(ellps="GRS80")
_TO_LL = Transformer.from_crs(ALBERS, "EPSG:4617", always_xy=True)

PR_ABBR = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON",
           "46": "MB", "47": "SK", "48": "AB", "59": "BC", "60": "YT", "61": "NT", "62": "NU"}
PR_NAME = {"NL": "Newfoundland and Labrador", "PE": "Prince Edward Island", "NS": "Nova Scotia",
           "NB": "New Brunswick", "QC": "Quebec", "ON": "Ontario", "MB": "Manitoba",
           "SK": "Saskatchewan", "AB": "Alberta", "BC": "British Columbia", "YT": "Yukon",
           "NT": "Northwest Territories", "NU": "Nunavut"}
BANDS = [10, 25, 50]


def load_fires(year):
    """Fire outlines for a year in ESRI:102001. 2026 = CWFIS M3 perimeters (20261020);
    2023-2025 = NBAC 1972-2025 (20260513), prescribed burns excluded."""
    if year == 2026:
        g = gpd.read_file(f"{DATA}/fire/m3_perimeters_2026_cwfis_20261020.gpkg")
        g = g.rename(columns={"UID": "fire_uid", "prov": "fire_prov"})
        g["fire_first"] = g["FIRSTDATE"].astype(str).str[:10]
        g["fire_last"] = g["LASTDATE"].astype(str).str[:10]
        g = g[["fire_uid", "fire_prov", "fire_first", "fire_last", "geometry"]]
    else:
        g = gpd.read_file(f"{DATA}/fire/raw/nbac/shp/NBAC_merged_1972_to_2025_20260513.shp",
                          where=f"YEAR = {year}", engine="pyogrio")
        g = g[g["PRESCRIBED"].fillna("") != "true"]
        g = g.rename(columns={"NFIREID": "fire_uid", "ADMIN_NAME": "fire_prov"})
        g["fire_first"] = g["HS_SDATE"].astype(str).str[:10]
        g["fire_last"] = g["HS_EDATE"].astype(str).str[:10]
        g = g[["fire_uid", "fire_prov", "fire_first", "fire_last", "geometry"]]
    g = g.to_crs(ALBERS)
    g["geometry"] = shapely.make_valid(g.geometry.values)
    g = g[~g.geometry.is_empty].reset_index(drop=True)
    g["fire_idx"] = np.arange(len(g))
    return g


def geodesic_shortest(a_geoms, b_geoms):
    """Geodesic length (km) of the planar shortest line between paired geometries
    (both in ESRI:102001). Returns 0 where they intersect."""
    a = np.asarray(a_geoms)
    b = np.asarray(b_geoms)
    lines = shapely.shortest_line(a, b)
    coords = shapely.get_coordinates(lines).reshape(-1, 2, 2)
    lon1, lat1 = _TO_LL.transform(coords[:, 0, 0], coords[:, 0, 1])
    lon2, lat2 = _TO_LL.transform(coords[:, 1, 0], coords[:, 1, 1])
    _, _, d = GEOD.inv(lon1, lat1, lon2, lat2)
    d = np.asarray(d) / 1000.0
    inter = shapely.intersects(a, b)
    d[inter] = 0.0
    return d


def nearest_fire(gdf, fires, cols=("fire_uid", "fire_prov", "fire_first", "fire_last")):
    """For each row of gdf (ESRI:102001) return DataFrame with nearest fire attributes,
    planar distance (km) and geodesic distance (km)."""
    j = gpd.sjoin_nearest(gdf[["geometry"]], fires[["fire_idx", "geometry"]],
                          how="left", distance_col="d_plan_m")
    j = j[~j.index.duplicated(keep="first")]  # ties: keep one
    j = j.reindex(gdf.index)
    fi = j["fire_idx"].astype(int).values
    dgeo = geodesic_shortest(gdf.geometry.values, fires.geometry.values[fi])
    out = pd.DataFrame(index=gdf.index)
    out["d_plan_km"] = j["d_plan_m"].values / 1000.0
    out["d_km"] = dgeo
    for c in cols:
        out[c] = fires[c].values[fi]
    return out


# ---------------------------------------------------------------------------
# Fast method for large inputs (DA points/polygons, reserves, First Nations vs outlines):
#   fire-outline boundaries (original NBAC / M3 vertices, no simplification) densified to
#   <= 200 m segments; all boundary vertices go in a KD-tree (Albers). Distance = geodesic
#   (GRS80) distance from the query point (or each densified boundary vertex of a query
#   polygon) to the nearest fire-boundary vertex; 0 if the query geometry intersects an
#   outline (tested on the original polygons). Max error vs exact distance: 100 m.
# ---------------------------------------------------------------------------
from scipy.spatial import cKDTree

STEP_M = 200.0


def boundary_vertices(geoms, step=STEP_M, chunk=200):
    xs, ows = [], []
    for i0 in range(0, len(geoms), chunk):
        b = shapely.segmentize(shapely.boundary(geoms[i0:i0 + chunk]), step)
        xy, own = shapely.get_coordinates(b, return_index=True)
        xs.append(xy); ows.append((own + i0).astype(np.int32))
    return np.vstack(xs), np.concatenate(ows)


class VertexTree:
    def __init__(self, xy, owner):
        self.xy, self.owner = xy, owner
        self.tree = cKDTree(xy)

    def query_xy(self, xy):
        d, k = self.tree.query(xy)
        lo1, la1 = _TO_LL.transform(xy[:, 0], xy[:, 1])
        lo2, la2 = _TO_LL.transform(self.xy[k, 0], self.xy[k, 1])
        _, _, g = GEOD.inv(lo1, la1, lo2, la2)
        return np.asarray(g) / 1000.0, self.owner[k]

    def nearest(self, geoms, chunk=1500):
        """geoms: array of Albers geometries (points or polygons). Returns (d_km, owner)."""
        if np.all(shapely.get_type_id(geoms) == 0):
            return self.query_xy(shapely.get_coordinates(geoms))
        d = np.full(len(geoms), np.nan); fi = np.zeros(len(geoms), dtype=np.int64)
        for i0 in range(0, len(geoms), chunk):
            vb = shapely.segmentize(shapely.boundary(geoms[i0:i0 + chunk]), STEP_M)
            xy, gi = shapely.get_coordinates(vb, return_index=True)
            dd, ff = self.query_xy(xy)
            t = pd.DataFrame({"g": gi + i0, "d": dd, "fi": ff}).sort_values("d").drop_duplicates("g")
            d[t.g.values] = t.d.values; fi[t.g.values] = t.fi.values
        return d, fi


def inside_index(gdf, fires):
    """Series: index of gdf rows intersecting an outline -> fire_idx."""
    j = gpd.sjoin(gdf[["geometry"]], fires[["fire_idx", "geometry"]], how="inner", predicate="intersects")
    j = j[~j.index.duplicated()]
    return j["fire_idx"]
