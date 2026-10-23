"""Step 1: extract all Department of National Defence parcels from the Directory of Federal
Real Property (DFRP) open dataset (TBS, XML, one record per property, parcels with lat/lon and
land area). Streams the XML (iterparse) to keep memory low.
Output: work/dfrp_dnd_parcels.csv and data/geo/dnd/dfrp_dnd_parcels.gpkg (points, ESRI:102001)
with eq_radius_m = radius of a circle with the parcel's land area."""
import zipfile, xml.etree.ElementTree as ET, csv, math, sys
import pandas as pd, geopandas as gpd
B = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3]))
Z = f"{B}/data/geo/dnd/dfrp-rbif.zip"
rows, cust = [], {}
with zipfile.ZipFile(Z) as z, z.open("dfrp-rbif.xml") as fh:
    for ev, el in ET.iterparse(fh, events=("end",)):
        if el.tag != "Property":
            continue
        c = el.find("Custodian")
        code = c.get("code"); name = c.findtext("Name_E")
        cust[code] = name
        if code == "DND":
            for p in el.iter("Parcel"):
                loc = p.find("Location")
                la = p.findtext("Land_Area")
                rows.append(dict(
                    property_number=el.findtext("Property_Number"), parcel=p.get("Number"),
                    name=el.findtext("Property_Name_E"), primary_use=el.findtext("Primary_Use_E"),
                    interest=el.findtext("Interest_Type_E"),
                    land_ha=float(la) if la not in (None, "") else float("nan"),
                    province=loc.findtext("Province_E") if loc is not None else None,
                    municipality=loc.findtext("Municipality_E") if loc is not None else None,
                    lat=float(loc.findtext("Latitude")) if loc is not None and loc.findtext("Latitude") else float("nan"),
                    lon=float(loc.findtext("Longitude")) if loc is not None and loc.findtext("Longitude") else float("nan"),
                    pos_acc_m=loc.findtext("Positional_Accuracy") if loc is not None else None,
                    loc_type=loc.get("type") if loc is not None else None))
        el.clear()
print("DND custodian name:", cust.get("DND"))
df = pd.DataFrame(rows)
print("DND parcels", len(df), "with coords", df.lat.notna().sum(), "canadian", (df.loc_type == "canadian").sum(),
      "land ha total", round(df.land_ha.sum()))
df = df[df.lat.notna() & (df.loc_type == "canadian")]
df["eq_radius_m"] = (df.land_ha.fillna(0) * 1e4 / math.pi) ** 0.5
df.to_csv(f"{B}/analysis/outline-check/work/dfrp_dnd_parcels.csv", index=False)
g = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4617").to_crs("ESRI:102001")
g.to_file(f"{B}/data/geo/dnd/dfrp_dnd_parcels.gpkg", driver="GPKG")
print(df.sort_values("land_ha", ascending=False).head(25)[["name", "province", "land_ha", "primary_use"]].to_string())
