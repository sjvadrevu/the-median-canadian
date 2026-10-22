"""Extend AHCCD monthly series to September 2026 with ECCC climate-daily, offset-corrected.

Daily source: analysis/climate/work/site_month.csv (monthly totals and means computed from ECCC climate-daily,
MSC GeoMet api.weather.gc.ca/collections/climate-daily, 1990-06 to 2026-09, for 671 sites; replacement
climate IDs within 5 km and 100 m joined into one site; precipitation month valid with <= 3 missing days,
temperature month with <= 5 missing days; temperature = mean of daily (max+min)/2).
Link: an AHCCD station is linked to the daily site that contains its climate ID; otherwise to the nearest
daily site within 15 km and 100 m elevation.
Offsets, per station and calendar month, estimated on the overlap months (1990-06 to the AHCCD end):
  temperature: additive, mean(AHCCD - daily); needs >= 8 overlap years for that month, else the station's
               all-month mean offset
  precipitation: multiplicative, sum(AHCCD) / sum(daily) over overlap months; >= 8 overlap years for that
               month, else the station's all-month ratio (AHCCD adds gauge undercatch, trace and snow-density
               adjustments that raw daily totals lack, so the ratio is usually > 1)
Fill: every month from 1990-06 on with no AHCCD value takes daily x offset. Hold-out check: offsets are
re-estimated without the last 5 AHCCD years of each station and used to predict those years.
Station kept for the analysis only if linked and if, after filling, May-Aug (temperature) or Apr-Sep
(precipitation) is complete in at least 9 of 11 years 2016-2026 including 2025 and 2026.
Outputs: work/temp_monthly_filled.csv, work/prec_monthly_filled.csv, work/link_offsets.csv,
         offset_check.csv, work/log_02.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd

from common import WORK, OUT, CLIMATE, haversine, log

fh = open(WORK / "log_02.txt", "w")
ST = pd.read_csv(WORK / "ahccd_stations.csv", dtype={"station": str})
ST = ST[ST.near_forest_area]
SM = pd.read_csv(CLIMATE / "work" / "site_month.csv", dtype={"site": str})
SM["year"] = SM.month.str[:4].astype(int)
SM["mon"] = SM.month.str[5:7].astype(int)
META = pd.read_csv(CLIMATE / "work" / "site_meta.csv", dtype={"site": str})
mem = {}
for r in META.itertuples():
    for cid in str(r.member_ids).split(";"):
        mem.setdefault(cid, r.site)


def link(r):
    if r.station in mem:
        return mem[r.station], 0.0, "same climate ID"
    d = haversine(r.lat, r.lon, META.lat.values, META.lon.values)
    dz = np.abs(META.elev.values - r.elev)
    ok = (d <= 15) & ((dz <= 100) | np.isnan(dz))
    if not ok.any():
        return None, np.nan, "none"
    i = np.where(ok)[0][np.argmin(d[ok])]
    return META.site.iloc[i], float(d[i]), "nearest within 15 km"


AH = {"temp": pd.read_csv(WORK / "ahccd_temp_monthly.csv", dtype={"station": str}),
      "prec": pd.read_csv(WORK / "ahccd_prec_monthly.csv", dtype={"station": str})}
VAR = {"temp": ("tmean", "t"), "prec": ("prec", "p")}
offs, checks, filled, qc_rows = [], [], {"temp": [], "prec": []}, []
for kind in ["temp", "prec"]:
    av, dv = VAR[kind]
    A = AH[kind]
    for r in ST[ST.kind == kind].itertuples():
        site, dist, how = link(r)
        a = A[A.station == r.station][["year", "month", av]].rename(columns={"month": "mon", av: "ah"})
        if site is None:
            offs.append(dict(kind=kind, station=r.station, name=r.name, site=None, link=how))
            continue
        d = SM[SM.site == site][["year", "mon", dv]].rename(columns={dv: "dl"})
        m = a.merge(d, on=["year", "mon"], how="outer")
        ov = m[m.ah.notna() & m.dl.notna()]
        last_ah = int(a[a.ah.notna()].year.max())

        def estimate(ov):
            if kind == "temp":
                allm = (ov.ah - ov.dl).mean()
                g = ov.groupby("mon").apply(lambda x: (x.ah - x.dl).mean() if len(x) >= 8 else np.nan, include_groups=False)
            else:
                allm = ov.ah.sum() / ov.dl.sum() if ov.dl.sum() > 0 else np.nan
                g = ov.groupby("mon").apply(lambda x: x.ah.sum() / x.dl.sum() if len(x) >= 8 and x.dl.sum() > 0 else np.nan, include_groups=False)
            g = g.reindex(range(1, 13)).fillna(allm)
            return g, allm, len(ov)

        g, allm, nov = estimate(ov)
        # hold-out: last 5 AHCCD years
        tr = ov[ov.year <= last_ah - 5]
        te = ov[ov.year > last_ah - 5]
        if len(tr) >= 60 and len(te) >= 12:
            g2, _, _ = estimate(tr)
            if kind == "temp":
                pred = te.dl + te.mon.map(g2)
                err = pred - te.ah
                summer = te.mon.isin([5, 6, 7, 8])
                checks.append(dict(kind=kind, station=r.station, n_test_months=len(te),
                                   bias=err.mean(), mae=err.abs().mean(), bias_mjja=err[summer].mean(),
                                   raw_bias=(te.dl - te.ah).mean()))
            else:
                yy = te.assign(pred=te.dl * te.mon.map(g2))
                s = yy[yy.mon.isin([4, 5, 6, 7, 8, 9])].groupby("year")[["ah", "pred", "dl"]].sum()
                s = s[s.ah > 0]
                checks.append(dict(kind=kind, station=r.station, n_test_months=len(te),
                                   bias=(yy.pred.sum() / yy.ah.sum() - 1) * 100,
                                   mae=(np.abs(s.pred / s.ah - 1) * 100).mean(),
                                   bias_mjja=(s.pred.sum() / s.ah.sum() - 1) * 100,
                                   raw_bias=(s.dl.sum() / s.ah.sum() - 1) * 100))
        m["fill"] = m.dl + m.mon.map(g) if kind == "temp" else m.dl * m.mon.map(g)
        m["value"] = m.ah
        m["source"] = np.where(m.ah.notna(), "AHCCD", "")
        use = m.ah.isna() & m.fill.notna() & ((m.year > 1990) | ((m.year == 1990) & (m.mon >= 6)))
        # QC of filled months against the station's own AHCCD record for that calendar month:
        # precipitation above 1.5 x the AHCCD maximum, or temperature more than 5 SD from the AHCCD mean, is
        # treated as a daily-data error and left missing (e.g. Norman Wells 2015-16, ~200 mm per month).
        clim = a.groupby("mon").ah.agg(["max", "mean", "std"])
        if kind == "prec":
            bad = m.fill > 1.5 * m.mon.map(clim["max"])
        else:
            bad = (m.fill - m.mon.map(clim["mean"])).abs() > 5 * m.mon.map(clim["std"])
        qc_rows.append(dict(kind=kind, station=r.station, n_fill=int(use.sum()), n_rejected=int((use & bad).sum())))
        use = use & ~bad
        m.loc[use, "value"] = m.loc[use, "fill"]
        m.loc[use, "source"] = "daily+offset"
        m = m[m.value.notna() & (m.year >= 1940)]
        m = m[(m.year < 2026) | (m.mon <= 9)]
        m["station"] = r.station
        filled[kind].append(m[["station", "year", "mon", "value", "source"]])
        offs.append(dict(kind=kind, station=r.station, name=r.name, site=site, link=how, link_km=dist,
                         n_overlap_months=nov, offset_all=allm, offset_mjja=g.loc[[5, 6, 7, 8]].mean(),
                         offset_amjjas=g.loc[[4, 5, 6, 7, 8, 9]].mean(), last_ahccd_year=last_ah))
OF = pd.DataFrame(offs)
OF.to_csv(WORK / "link_offsets.csv", index=False)
CK = pd.DataFrame(checks)
CK.to_csv(OUT / "offset_check.csv", index=False)
for kind in ["temp", "prec"]:
    o = OF[OF.kind == kind]
    log(f"{kind}: {len(o)} stations, linked {o.site.notna().sum()} ({(o.link == 'same climate ID').sum()} same ID)", fh)
    log(f"  offset (all months) median {o.offset_all.median():.3f}, IQR {o.offset_all.quantile(.25):.3f} to {o.offset_all.quantile(.75):.3f}", fh)
    c = CK[CK.kind == kind]
    unit = "C" if kind == "temp" else "%"
    log(f"  hold-out (last 5 AHCCD years, {len(c)} stations): median bias {c.bias.median():.3f} {unit}, mean |bias| "
        f"{c.bias.abs().mean():.3f}; summer/season bias median {c.bias_mjja.median():.3f}; without offset {c.raw_bias.median():.3f}; "
        f"mean abs error per {'month' if kind == 'temp' else 'season'} {c.mae.median():.3f}", fh)

QC = pd.DataFrame(qc_rows)
QC.to_csv(WORK / "fill_qc.csv", index=False)
log("QC rejected filled months: " + str(QC.groupby("kind")[["n_fill", "n_rejected"]].sum().to_dict()), fh)
log("stations with rejections: " + str(QC[QC.n_rejected > 0].values.tolist()), fh)

# completeness filter on recent years
for kind, months in [("temp", [5, 6, 7, 8]), ("prec", [4, 5, 6, 7, 8, 9])]:
    F = pd.concat(filled[kind], ignore_index=True)
    q = F[F.mon.isin(months)].groupby(["station", "year"]).value.count().unstack()
    comp = (q == len(months)).reindex(columns=range(2016, 2027)).fillna(False)
    ok = (comp.sum(axis=1) >= 9) & comp[2025] & comp[2026]
    keep = ok[ok].index
    log(f"{kind}: {len(keep)} of {q.shape[0]} linked stations complete in >= 9 of 2016-2026 incl. 2025 and 2026", fh)
    share_fill = F[F.station.isin(keep) & F.mon.isin(months)].groupby(F.year // 10 * 10).source.apply(lambda s: (s != "AHCCD").mean())
    log(f"  share of season months from daily+offset by decade: {share_fill.round(3).to_dict()}", fh)
    F[F.station.isin(keep)].to_csv(WORK / f"{kind}_monthly_filled.csv", index=False)
