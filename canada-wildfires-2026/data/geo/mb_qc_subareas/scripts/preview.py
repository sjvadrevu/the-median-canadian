"""Quick-look PNG of the built layers. usage: python3 -I preview.py OUT_DIR"""
import sys
import geopandas as gpd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
O = sys.argv[1]
L = ["mb_fire_regions", "mb_fire_restriction_areas", "qc_sopfeu_fire_danger_zones", "qc_sopfeu_protection_zones"]
fig, ax = plt.subplots(2, 2, figsize=(14, 14))
for a, l in zip(ax.flat, L):
    g = gpd.read_file(f"{O}/{l}.gpkg")
    g["geometry"] = g.simplify(1000).make_valid()
    rem = g.area_level == "remainder"
    g[~rem].plot(ax=a, column="area_name", cmap="tab20", edgecolor="black", linewidth=0.4)
    g[rem].plot(ax=a, color="#dddddd", edgecolor="black", linewidth=0.4, hatch="//")
    for _, r in g.iterrows():
        p = r.geometry.representative_point()
        a.annotate(r.area_name[:22], (p.x, p.y), fontsize=5, ha="center")
    a.set_title(f"{l} ({len(g)} rows)")
    a.set_axis_off()
plt.tight_layout()
plt.savefig(f"{O}/preview.png", dpi=110)
print("ok")
