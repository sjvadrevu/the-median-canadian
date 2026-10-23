"""Step 4: summary tables for results.md from work/evidence_all_718.csv (prints markdown)."""
import pandas as pd, numpy as np
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/outline-check"
a = pd.read_csv(f"{O}/work/evidence_all_718.csv")
a["class_s"] = a["class"].str.replace(" (unreported in agency lists)", "", regex=False)
a["class_f"] = a["class_file_only"].str.replace(" (unreported in agency lists)", "", regex=False)
ORDER = ["wildfire", "likely agricultural or grass burn", "military range", "possible industrial or urban heat", "unclear"]

def tab(d, col="class_s"):
    t = d.groupby(col).agg(outlines=("fire_uid", "size"), area_ha=("area_ha", "sum")).reindex(ORDER).fillna(0)
    t["area_ha"] = t.area_ha.round(0).astype(int); t["outlines"] = t.outlines.astype(int)
    return t

for grp in ["unmatched", "matched sample"]:
    d = a[a.group == grp]
    print(f"\n### {grp} (union detections)\n", tab(d).to_markdown())
    print(f"\n### {grp} (file-only detections)\n", tab(d, "class_f").to_markdown())
m = a[a.agency_match]
print("\n### all 638 matched\n", tab(m).to_markdown())
u = a[a.group == "unmatched"]
print("\n### unmatched province x class\n", pd.crosstab(u.prov, u.class_s, margins=True).to_markdown())
print("\n### unmatched month x class\n", pd.crosstab(u.month, u.class_s, margins=True).to_markdown())
print("\n### unmatched with agency record in another list\n",
      u.groupby(["agency_sources_5km"]).fire_uid.size().to_markdown())
print(pd.crosstab(u.class_s, u.agency_record_5km_any_source).to_markdown())
print("\n### class changes file-only -> union (unmatched)\n", pd.crosstab(u.class_f, u.class_s).to_markdown())
s = a[a.group == "matched sample"]
print("\n### class changes file-only -> union (sample)\n", pd.crosstab(s.class_f, s.class_s).to_markdown())
print("\n### unclear detail (unmatched)\n", u[u.class_s == "unclear"].class_detail.str.replace(r"[\d.]+", "#", regex=True).value_counts().to_markdown())
print("\n### unclear detail (sample)\n", s[s.class_s == "unclear"].class_detail.str.replace(r"[\d.]+", "#", regex=True).value_counts().to_markdown())
print("\n### medians\n", a.groupby("group")[["area_ha", "det_days", "lc_natural", "lc_agri", "lc_forest", "lc_cropland"]].median().round(2).to_markdown())
print("\n### non-wildfire matched\n", m[m.class_s != "wildfire"][m.class_s != "unclear"][["fire_uid", "group", "class", "class_detail", "prov", "area_ha", "dnd_nearest", "cwfif_nearest_note"]].to_markdown(index=False))
print("\n### unmatched near DND (<5 km) but not military\n", u[(u.dnd_nearest_km < 5) & (u.class_s != "military range")][["fire_uid", "class", "prov", "area_ha", "dnd_nearest", "dnd_nearest_km", "dnd_share"]].to_markdown(index=False))
print("\n### detection totals\n", a[["n_hotspots_raw_file", "n_hotspots_raw_wfs", "n_det_file", "n_det"]].sum().to_dict())
print("zero detections union:", (a.n_det == 0).sum(), " file-only:", (a.n_det_file == 0).sum())
