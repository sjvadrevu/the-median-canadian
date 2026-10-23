"""Step 1: read Sentinel-2 L2A (Element84 Earth Search COGs, tile 12UWD) windows around the
CFB Wainwright fire for pre-fire (2026-10-01, 2026-10-04), intermediate (2026-10-14, 2026-10-19)
and post-fire (2026-10-21) dates. Saves B04,B03,B02 (resampled to 20 m), B8A, B12, SCL as one
compressed npz per scene in work/s2/. Window: lon -111.0..-110.55, lat 52.60..52.90 (EPSG:32612).
"""
import numpy as np, rasterio, os, sys
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from pyproj import Transformer
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
os.makedirs(f"{O}/work/s2", exist_ok=True)
SC = ["S2C_12UWD_20261001_0_L2A", "S2C_12UWD_20261004_0_L2A", "S2C_12UWD_20261014_0_L2A",
      "S2B_12UWD_20261019_0_L2A", "S2C_12UWD_20261021_0_L2A"]
BASE = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/12/U/WD/2026/10"
t = Transformer.from_crs(4326, 32612, always_xy=True)
x0, y0 = t.transform(-111.0, 52.60); x1, y1 = t.transform(-110.55, 52.90)
xa, xb = min(x0, x1), max(x0, x1); ya, yb = min(y0, y1), max(y0, y1)
# snap to 20 m grid
xa = np.floor(xa / 20) * 20; xb = np.ceil(xb / 20) * 20; ya = np.floor(ya / 20) * 20; yb = np.ceil(yb / 20) * 20
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
for s in SC:
    out = f"{O}/work/s2/{s}.npz"
    if os.path.exists(out):
        continue
    arr = {}
    for b in ["B8A", "B12", "SCL", "B04", "B03", "B02"]:
        with rasterio.open(f"{BASE}/{s}/{b}.tif") as r:
            w = from_bounds(xa, ya, xb, yb, r.transform)
            h = int(round((yb - ya) / 20)); wd = int(round((xb - xa) / 20))
            rs = Resampling.nearest if b == "SCL" else Resampling.average
            arr[b] = r.read(1, window=w, out_shape=(h, wd), resampling=rs, boundless=True, fill_value=0)
    np.savez_compressed(out, transform=np.array([xa, yb, 20.0]), **arr)
    print(s, {k: v.shape for k, v in arr.items()}, flush=True)
