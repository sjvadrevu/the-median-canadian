"""Thread 1a: georeference NRCan's official managed/unmanaged forest map image.

The GHG-inventory managed-forest boundary is not published as open GIS data (checked: open.canada.ca,
NFIS ccfm_managed_forests WFS/WMS, NFI tables; the NFIS 'Map of Forest Management in Canada' states it
differs from the GHG managed-forest map). The only official depiction found is the NRCan image
Managed_unmanaged_forests_e.jpg (570 x 383 px). This script:
  1. classifies image pixels: managed (green), unmanaged (tan), Canada other land (white), else;
  2. fits an affine transform from EPSG:3978 (NAD83 Canada Atlas Lambert, assumed map projection)
     to image pixels by maximising overlap of the image's Canada-land mask with StatCan 2021
     province polygons (Nelder-Mead on IoU, multi-start);
  3. writes work/mf_class_img.npy, work/mf_affine.json (pixel <- 3978 coords) and a fit log.
"""
import json, sys
import numpy as np
from PIL import Image
import geopandas as gpd
from rasterio import features
from affine import Affine
from scipy.optimize import minimize
from scipy import ndimage

BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
T = f"{BASE}/analysis/threads"
img = np.array(Image.open(f"{T}/raw/managed_forest/Managed_unmanaged_forests_e.jpg").convert("RGB")).astype(int)
R, G, B = img[..., 0], img[..., 1], img[..., 2]
H, W = R.shape
green = (G - R > 40) & (G - B > 40)
tan = (R - B > 30) & (G - B > 25) & (np.abs(R - G) < 30) & (R > 150) & ~green
white = (R > 241) & (G > 241) & (B > 241)
blue = (B - R > 25) & ~green & ~tan
cls = np.zeros((H, W), np.uint8)          # 0 other (US grey, lines, text)
cls[white] = 3                            # Canada non-forest land
cls[tan] = 2                              # unmanaged forest
cls[green] = 1                            # managed forest
cls[blue] = 9                             # water
# legend box (top right) is white: blank it out of the land mask
leg = np.zeros_like(cls, bool); leg[35:100, 380:530] = True
cls[leg & (cls != 9)] = 0
np.save(f"{T}/work/mf_class_img.npy", cls)
land_img = np.isin(cls, [1, 2, 3])
# close thin boundary lines inside Canada
land_img = ndimage.binary_closing(land_img, iterations=2) & ~leg
valid = ~leg

prov = gpd.read_file(f"{BASE}/data/geo/statcan/lpr_000b21a_e_provinces_2021.gpkg").to_crs("EPSG:3978")
# reference Canada mask rasterised once on a 2 km EPSG:3978 grid; candidate transforms sample it at image pixel centres
B0 = prov.total_bounds
RX0, RY0, RES = B0[0] - 50000, B0[3] + 50000, 2000.0
RW, RH = int((B0[2] - B0[0] + 100000) / RES), int((B0[3] - B0[1] + 100000) / RES)
ref = features.rasterize(((g, 1) for g in prov.geometry.simplify(1000)), out_shape=(RH, RW),
                         transform=Affine(RES, 0, RX0, 0, -RES, RY0), fill=0, dtype="uint8").astype(bool)
cols, rows = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)


def render(p):
    sx, sy, tx, ty = p  # x = tx + col*sx ; y = ty - row*sy
    X = tx + cols * sx; Y = ty - rows * sy
    ci = np.floor((X - RX0) / RES).astype(int); ri = np.floor((RY0 - Y) / RES).astype(int)
    ok = (ci >= 0) & (ci < RW) & (ri >= 0) & (ri < RH)
    out = np.zeros((H, W), bool); out[ok] = ref[ri[ok], ci[ok]]
    return out


def loss(p):
    m = render(p)
    inter = (m & land_img & valid).sum(); uni = ((m | land_img) & valid).sum()
    return 1 - inter / uni


# initial guess: Canada in 3978 spans x -2.35e6..3.1e6, y 0.3e6..4.8e6 ; image Canada spans approx cols 40..520, rows 20..360
xs, ys = np.where(land_img.T)
x0, x1 = np.percentile(xs, [0.5, 99.5]); y0, y1 = np.percentile(ys, [0.5, 99.5])
best = None
for fx in (0.95, 1.0, 1.05):
    for fy in (0.95, 1.0, 1.05):
        sx = (B0[2] - B0[0]) / (x1 - x0) * fx; sy = (B0[3] - B0[1]) / (y1 - y0) * fy
        p0 = [sx, sy, B0[0] - x0 * sx, B0[3] + y0 * sy]
        r = minimize(loss, p0, method="Nelder-Mead", options=dict(xatol=20, fatol=1e-6, maxiter=800))
        print(fx, fy, r.fun, r.x, flush=True)
        if best is None or r.fun < best.fun:
            best = r
sx, sy, tx, ty = best.x
json.dump(dict(sx=sx, sy=sy, tx=tx, ty=ty, iou=1 - best.fun, crs="EPSG:3978",
               note="pixel col = (x - tx)/sx, row = (ty - y)/sy"), open(f"{T}/work/mf_affine.json", "w"), indent=1)
m = render(best.x)
print("IoU", 1 - best.fun, "pixel size km", sx / 1e3, sy / 1e3)
print("class pixel counts", {k: int((cls == k).sum()) for k in (0, 1, 2, 3, 9)})
Image.fromarray((np.stack([m * 255, land_img * 255, np.zeros_like(m)], -1)).astype(np.uint8)).save(f"{T}/work/mf_fit_check.png")
