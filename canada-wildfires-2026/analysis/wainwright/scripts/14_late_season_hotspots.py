"""Step 14: late-season share of satellite hotspots in Canada, CWFIS WFS archive (public:hotspots), counted
server-side with resultType=hits. Canada = agency field in the 13 province/territory codes.
Windows by UTC date: Jan 1-Oct 22 (to-date denominator, comparable with 2026), Sep 1-Oct 22, Oct 1-22,
plus full Sep-Oct and full year for years before 2026.
Sensor sets: MODIS (Terra+Aqua) 2003-2026 (consistent sensors); all sensors 2018-2026.
Caveat: hotspots include agricultural and other non-wildfire burns (prairie fall stubble burning).
Output: late_season_hotspots_by_year.csv, late_season_trends_hotspots.csv"""
import re, time, requests, pandas as pd, os
from scipy.stats import kendalltau, theilslopes
O = __import__("os").environ.get("WILDFIRE_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[3])) + "/analysis/wainwright"
U = "https://cwfis.cfs.nrcan.gc.ca/geoserver/public/wfs"
AG = "agency IN ('BC','AB','SK','MB','ON','QC','NB','NS','PE','NL','YT','NT','NU')"
out_f = f"{O}/late_season_hotspots_by_year.csv"
done = pd.read_csv(out_f) if os.path.exists(out_f) else pd.DataFrame(columns=["sensor_set", "year"])
S = requests.Session()
def hits(a, b, sensor):
    q = f"rep_date >= '{a}T00:00:00Z' AND rep_date < '{b}T00:00:00Z' AND {AG}" + (" AND sensor = 'MODIS'" if sensor == "MODIS" else "")
    for k in range(6):
        try:
            r = S.get(U, params=dict(service="WFS", version="2.0.0", request="GetFeature", typeNames="public:hotspots",
                                     resultType="hits", CQL_FILTER=q), timeout=900)
            m = re.search(r'numberMatched="(\d+)"', r.text)
            if m: return int(m.group(1))
        except requests.RequestException: pass
        time.sleep(15 * (k + 1))
    return None
rows = done.to_dict("records")
for sset, y0 in [("MODIS", 2003), ("all", 2018)]:
    for y in range(y0, 2027):
        if ((done.sensor_set == sset) & (done.year == y)).any(): continue
        r = dict(sensor_set=sset, year=y, to_oct22=hits(f"{y}-01-01", f"{y}-10-23", sset), sep1_oct22=hits(f"{y}-09-01", f"{y}-10-23", sset),
                 oct1_22=hits(f"{y}-10-01", f"{y}-10-23", sset))
        if y < 2026:
            r.update(full_year=hits(f"{y}-01-01", f"{y+1}-01-01", sset), sep_oct=hits(f"{y}-09-01", f"{y}-11-01", sset), oct=hits(f"{y}-10-01", f"{y}-11-01", sset))
        rows.append(r); print(r, flush=True)
        pd.DataFrame(rows).to_csv(out_f, index=False)
Y = pd.DataFrame(rows).sort_values(["sensor_set", "year"])
Y["share_sep1_oct22_of_to_date"] = (Y.sep1_oct22 / Y.to_oct22).round(4); Y["share_oct1_22_of_to_date"] = (Y.oct1_22 / Y.to_oct22).round(4)
Y["share_sep_oct_of_year"] = (Y.sep_oct / Y.full_year).round(4); Y["share_oct_of_year"] = (Y.oct / Y.full_year).round(4)
for sset, g in Y.groupby("sensor_set"):
    Y.loc[g.index, "rank_share_sep1_oct22_desc"] = g.share_sep1_oct22_of_to_date.rank(ascending=False, method="min")
    Y.loc[g.index, "rank_oct1_22_count_desc"] = g.oct1_22.rank(ascending=False, method="min")
Y.to_csv(out_f, index=False)
tr = []
for sset, g in Y.groupby("sensor_set"):
    for m in ["share_sep1_oct22_of_to_date", "share_oct1_22_of_to_date", "oct1_22", "sep1_oct22"]:
        t = kendalltau(g.year, g[m]); sl = theilslopes(g[m], g.year)
        tr.append(dict(source="CWFIS hotspots", scope="Canada", sensor_set=sset, metric=m, years=f"{g.year.min()}-{g.year.max()}", n_years=len(g),
                       theil_sen_per_decade=round(sl[0] * 10, 4), kendall_tau=round(t.statistic, 3), p_value=round(t.pvalue, 4),
                       value_2026=g[g.year == 2026][m].iloc[0]))
pd.DataFrame(tr).to_csv(f"{O}/late_season_trends_hotspots.csv", index=False)
pd.set_option("display.width", 250); print(Y.to_string()); print(pd.DataFrame(tr).to_string())
