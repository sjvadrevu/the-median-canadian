"""Step 7: Canadian Drought Monitor (AAFC) class at the fire (Alberta Wildfire RMD-001-2026 point,
52.7726 N 110.9347 W) and the share of the CFB Wainwright polygon (Alberta official DND layer) in each
class, for every published April-September map 2003-2026 (August 2003 not published).
Class = worst class polygon (D0..D4) containing the point; 'none' if no drought polygon.
Output: drought_wainwright.csv"""
import zipfile, geopandas as gpd, pandas as pd
from shapely.geometry import Point
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
B = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
RAW = f"{B}/analysis/cause/raw/cdm"
dl = pd.read_csv(f"{RAW}/download_log.csv", dtype={"month": str}); dl = dl[dl.status == "ok"]
pt = gpd.GeoSeries([Point(-110.934717, 52.772633)], crs=4326)
dnd = gpd.read_file(f"{B}/data/geo/dnd/ab_dnd_layer13.geojson"); base = dnd[dnd.MB_NAME.str.contains("Wainwright")].to_crs(3400).union_all()
rows = []
for _, r in dl.iterrows():
    z = f"{RAW}/{r.file}"; names = [n for n in zipfile.ZipFile(z).namelist() if n.lower().endswith(".shp")]
    cls_pt = "none"; share = {}
    for c in range(5):
        nm = [n for n in names if n.upper().endswith(f"_D{c}_LR.SHP")]
        if not nm: continue
        g = gpd.read_file(f"/vsizip/{z}/{nm[0]}", bbox=(-112, 52, -110, 53.5) if False else None)
        if g.empty: continue
        g = g.to_crs(3400); geom = g.geometry.make_valid().union_all()
        if geom.contains(pt.to_crs(3400).iloc[0]): cls_pt = f"D{c}"
        share[f"D{c}_share_base"] = round(geom.intersection(base).area / base.area, 3)
    rows.append(dict(year=int(r.year), month=int(r.month), class_at_fire=cls_pt, **share))
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(f"{O}/drought_wainwright.csv", index=False)
