"""Summarise dnbr_buildings.csv by fire (and community) with the main rule and a lenient sensitivity rule.
Lenient 'possibly destroyed': building dNBR max >= 270 and ring median >= 100 (low-to-moderate burn reaching the
footprint). Output: dnbr_by_fire.csv, dnbr_by_community.csv"""
import os
import pandas as pd

L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_csv(os.path.join(L, "dnbr_buildings.csv"))
sc = pd.read_csv(os.path.join(L, "dnbr_scenes.csv"))
ex = pd.read_csv(os.path.join(L, "buildings_exposure_by_fire.csv")).set_index("fire_uid")
d["lenient_possibly_destroyed"] = (d.dnbr_building_max >= 270) & (d.dnbr_ring_median >= 100)
order = ["likely destroyed", "damaged surroundings", "unburned", "no clear data"]
def tab(keys):
    t = d.groupby(keys).building_class.value_counts().unstack(fill_value=0).reindex(columns=order, fill_value=0)
    t["buildings_classified"] = t.sum(axis=1)
    t["lenient_possibly_destroyed"] = d.groupby(keys).lenient_possibly_destroyed.sum()
    t["likely_destroyed_inside_only"] = d[d.zone == "inside"].groupby(keys).building_class.apply(lambda s: int((s == "likely destroyed").sum()))
    return t.fillna(0)
f = tab(["fire_uid"])
s = sc.groupby(["fire_uid", "period"]).agg(scenes=("scene_id", lambda x: " ".join(x)), dates=("date", lambda x: f"{min(x)} to {max(x)}")).unstack("period")
s.columns = [f"{a}_{b}" for a, b in s.columns]
f = f.join(ex[["prov", "main_communities", "fire_area", "first_date", "last_date", "area_ha", "inside", "within_100m"]]).join(s)
f = f.join(d.groupby("fire_uid").dnbr_offset.first())
f.sort_values("buildings_classified", ascending=False).to_csv(os.path.join(L, "dnbr_by_fire.csv"))
tab(["prov", "community_group"]).sort_values("likely destroyed", ascending=False).to_csv(os.path.join(L, "dnbr_by_community.csv"))
pd.set_option("display.width", 250)
print(f[order + ["buildings_classified", "lenient_possibly_destroyed", "prov", "main_communities"]].to_string())
print(f[order + ["buildings_classified", "lenient_possibly_destroyed"]].sum())
