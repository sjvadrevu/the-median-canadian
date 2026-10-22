"""Thread 3b: restrict holdover clusters to those inside/near a previous-season fire of 1,000 ha or more
(small prior polygons in BC/AB are often slash or debris burning sites); summary by winter, province, class."""
import pandas as pd
T = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/threads"
c = pd.read_csv(f"{T}/t3_holdover_clusters.csv")
c["prev_fire_ge_1000ha"] = c.prev_fire_ha >= 1000
out = c.groupby(["winter", "prev_fire_ge_1000ha", "cls"]).agg(clusters=("cluster", "size"), detections=("n_det", "sum"), det_days=("n_days", "sum")).reset_index()
out.to_csv(f"{T}/t3_holdover_by_prior_fire_size.csv", index=False)
print(out.to_string())
big = c[c.prev_fire_ge_1000ha]
print(big.groupby(["winter", "prov"]).size().unstack(fill_value=0))
print(big[big.cls.str.startswith("deep")][["winter", "prov", "n_det", "n_days", "first", "last", "prev_fire_uid", "prev_fire_ha", "lat", "lon"]].to_string())
