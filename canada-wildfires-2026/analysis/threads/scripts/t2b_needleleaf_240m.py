"""Thread 2: count of needleleaf pixels (Land Cover of Canada 2020 classes 1 temperate/sub-polar needleleaf and
2 sub-polar taiga needleleaf) per 240 m cell (8 x 8 block of 30 m pixels), same grid as
data/geo/landcover/lc2020_forest_count_240m.tif (and analysis/forest/work grid). Output uint8 GeoTIFF, 255 = no data."""
import numpy as np, rasterio
from rasterio.windows import Window
BASE = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
src_path = f"{BASE}/data/geo/landcover/landcover-2020-classification.tif"
out_path = f"{BASE}/analysis/threads/work/lc2020_needleleaf_count_240m.tif"
F = 8
with rasterio.open(src_path) as src:
    W, H = src.width // F * F, src.height // F * F
    prof = dict(driver="GTiff", dtype="uint8", count=1, width=W // F, height=H // F, crs=src.crs,
                transform=src.transform * src.transform.scale(F, F), compress="deflate", tiled=True,
                blockxsize=512, blockysize=512, nodata=255)
    step = 128 * F
    with rasterio.open(out_path, "w", **prof) as dst:
        for r0 in range(0, H, step):
            h = min(step, H - r0)
            a = src.read(1, window=Window(0, r0, W, h))
            f = np.isin(a, (1, 2)).reshape(h // F, F, W // F, F).sum(axis=(1, 3)).astype(np.uint8)
            v = (a != 0).reshape(h // F, F, W // F, F).sum(axis=(1, 3))
            f[v == 0] = 255
            dst.write(f, 1, window=Window(0, r0 // F, W // F, h // F))
            if r0 % (step * 20) == 0:
                print(r0, H, flush=True)
print("done")
