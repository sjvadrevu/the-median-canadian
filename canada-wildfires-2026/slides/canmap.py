"""Small Canada base map for slide graphics: provinces from the site's base.json (TopoJSON, lon/lat),
already in Canada Lambert conformal (EPSG:3978) and scaled to a pixel box."""
import json
import os

from pyproj import Transformer

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "map", "base.json")
_T = Transformer.from_crs(4326, 3978, always_xy=True)


def _decode(topo):
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs


def _ring(arcs, idxs):
    out = []
    for i in idxs:
        a = arcs[i] if i >= 0 else list(reversed(arcs[~i]))
        out.extend(a if not out else a[1:])
    return out


class CanMap:
    def __init__(self, W=928, obj="provs", lat_min=41.5):
        topo = json.load(open(BASE))
        arcs = _decode(topo)
        rings = []
        for g in topo["objects"][obj]["geometries"]:
            polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
            for poly in polys:
                for r in poly:
                    rings.append(_ring(arcs, r))
        self.rings = rings  # base.json is already in EPSG:3978
        xs = [p[0] for r in self.rings for p in r]
        ys = [p[1] for r in self.rings for p in r]
        self.minx, self.maxx, self.miny, self.maxy = min(xs), max(xs), min(ys), max(ys)
        self.W = W
        self.sc = W / (self.maxx - self.minx)
        self.H = (self.maxy - self.miny) * self.sc

    def xy(self, lon, lat):
        x, y = _T.transform(lon, lat)
        return (x - self.minx) * self.sc, (self.maxy - y) * self.sc

    def base_path(self, step=1):
        out = []
        for r in self.rings:
            if len(r) < 3:
                continue
            pts = r[::step] + [r[-1]]
            out.append("M" + "L".join(f"{(x - self.minx) * self.sc:.1f},{(self.maxy - y) * self.sc:.1f}" for x, y in pts) + "Z")
        return "".join(out)
