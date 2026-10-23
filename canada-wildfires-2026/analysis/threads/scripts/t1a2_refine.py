"""Thread 1a2: refine the managed-forest image fit with a looser Canada-land mask (JPEG whites >= 237, frame and
legend excluded), starting from the t1a solution (single Nelder-Mead run). Overwrites work/mf_affine.json."""
import json, numpy as np
from PIL import Image
from scipy import ndimage
from scipy.optimize import minimize
import geopandas as gpd
from rasterio import features
from affine import Affine
BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
T = f"{BASE}/analysis/threads"
img = np.array(Image.open(f"{T}/raw/managed_forest/Managed_unmanaged_forests_e.jpg").convert("RGB")).astype(int)
cls = np.load(f"{T}/work/mf_class_img.npy")
H, W = cls.shape
white = (img.min(2) >= 237) & (img.max(2) - img.min(2) < 20)
land = np.isin(cls, [1, 2]) | white
land = ndimage.binary_closing(land, iterations=1)
valid = np.ones_like(land); valid[35:100, 380:530] = False; valid[:6] = False; valid[-6:] = False; valid[:, :6] = False; valid[:, -6:] = False
prov = gpd.read_file(f"{BASE}/data/geo/statcan/lpr_000b21a_e_provinces_2021.gpkg").to_crs("EPSG:3978")
B0 = prov.total_bounds; RX0, RY0, RES = B0[0] - 50000, B0[3] + 50000, 2000.0
RW, RH = int((B0[2] - B0[0] + 100000) / RES), int((B0[3] - B0[1] + 100000) / RES)
ref = features.rasterize(((g, 1) for g in prov.geometry.simplify(1000)), out_shape=(RH, RW),
                         transform=Affine(RES, 0, RX0, 0, -RES, RY0), fill=0, dtype="uint8").astype(bool)
cols, rows = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
def render(p):
    sx, sy, tx, ty = p
    ci = np.floor((tx + cols * sx - RX0) / RES).astype(int); ri = np.floor((RY0 - (ty - rows * sy)) / RES).astype(int)
    ok = (ci >= 0) & (ci < RW) & (ri >= 0) & (ri < RH)
    out = np.zeros((H, W), bool); out[ok] = ref[ri[ok], ci[ok]]; return out
def loss(p):
    m = render(p); return 1 - (m & land & valid).sum() / ((m | land) & valid).sum()
A = json.load(open(f"{T}/work/mf_affine.json"))
p0 = [A["sx"], A["sy"], A["tx"], A["ty"]]
print("start IoU (new mask)", 1 - loss(p0))
r = minimize(loss, p0, method="Nelder-Mead", options=dict(xatol=10, fatol=1e-7, maxiter=600))
print("refined IoU", 1 - r.fun, r.x)
# forest-only check: share of image forest pixels (green+tan) falling on Canada land
m = render(r.x); fp = np.isin(cls, [1, 2])
print("forest-coloured pixels on Canada land", (m & fp).sum() / fp.sum())
sx, sy, tx, ty = r.x
json.dump(dict(sx=sx, sy=sy, tx=tx, ty=ty, iou=1 - r.fun, iou_first_pass=A["iou"], crs="EPSG:3978",
               forest_px_on_land=float((m & fp).sum() / fp.sum()), note="pixel col = (x - tx)/sx, row = (ty - y)/sy"),
          open(f"{T}/work/mf_affine.json", "w"), indent=1)
Image.fromarray((np.stack([m * 255, land * 255, fp * 255], -1)).astype(np.uint8)).save(f"{T}/work/mf_fit_check2.png")
