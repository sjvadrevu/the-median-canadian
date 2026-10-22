"""Aggregate 30 m Land Cover of Canada 2020 to 240 m forest fraction (8x8 blocks).
Forest classes: 1 needleleaf, 2 taiga needleleaf, 5 broadleaf deciduous, 6 mixed.
Output uint8: 0-64 = count of forest pixels in block (fraction = v/64 of all 64 pixels),
plus band 2 = count of valid (non-nodata) pixels. Also writes a 30 m->240 m class histogram CSV."""
import sys, numpy as np, rasterio
from rasterio.windows import Window
src_path, out_path, hist_path = sys.argv[1:4]
F = 8
FOREST = np.array([1, 2, 5, 6])
with rasterio.open(src_path) as src:
    W, H = src.width // F * F, src.height // F * F
    prof = dict(driver="GTiff", dtype="uint8", count=2, width=W // F, height=H // F, crs=src.crs,
                transform=src.transform * src.transform.scale(F, F), compress="deflate", tiled=True,
                blockxsize=512, blockysize=512, nodata=255)
    hist = np.zeros(256, dtype=np.int64)
    step = 128 * F
    with rasterio.open(out_path, "w", **prof) as dst:
        for r0 in range(0, H, step):
            h = min(step, H - r0)
            a = src.read(1, window=Window(0, r0, W, h))
            for c in (0,1,2,5,6,8,10,11,12,13,14,15,16,17,18,19):
                hist[c] += np.count_nonzero(a == c)
            f = np.isin(a, FOREST).reshape(h // F, F, W // F, F).sum(axis=(1, 3)).astype(np.uint8)
            v = (a != 0).reshape(h // F, F, W // F, F).sum(axis=(1, 3)).astype(np.uint8)
            f[v == 0] = 255
            dst.write(f, 1, window=Window(0, r0 // F, W // F, h // F))
            dst.write(v, 2, window=Window(0, r0 // F, W // F, h // F))
            print(r0, H, flush=True)
with open(hist_path, "w") as fh:
    fh.write("class,pixels_30m,area_km2\n")
    for c in np.nonzero(hist)[0]:
        fh.write(f"{c},{hist[c]},{hist[c] * 900 / 1e6:.3f}\n")
