"""Canadian Forest Fire Weather Index System, daily equations of Van Wagner (1987), vectorized with numpy.

Inputs per day: noon temperature T (C), relative humidity H (%), 10 m wind W (km/h), 24-h rain r (mm), month.
Day-length factors are the standard Canadian values for latitudes north of 30N (Van Wagner 1987, tables 1-2).
All functions take arrays (one element per station-season) and return arrays.
"""
import numpy as np

EL = np.array([6.5, 7.5, 9.0, 12.8, 13.9, 13.9, 12.4, 10.9, 9.4, 8.0, 7.0, 6.0])      # DMC effective day length
FL = np.array([-1.6, -1.6, -1.6, 0.9, 3.8, 5.8, 6.4, 5.0, 2.4, 0.4, -1.6, -1.6])      # DC day-length adjustment


def ffmc(fo, T, H, W, r):
    mo = 147.2 * (101.0 - fo) / (59.5 + fo)
    rf = r - 0.5
    wet = r > 0.5
    rfs = np.where(wet, rf, 1.0)
    add = 42.5 * rfs * np.exp(-100.0 / (251.0 - mo)) * (1.0 - np.exp(-6.93 / rfs))
    add = np.where(mo > 150.0, add + 0.0015 * (mo - 150.0) ** 2 * np.sqrt(rfs), add)
    mo = np.where(wet, np.minimum(mo + add, 250.0), mo)
    ed = 0.942 * H ** 0.679 + 11.0 * np.exp((H - 100.0) / 10.0) + 0.18 * (21.1 - T) * (1.0 - np.exp(-0.115 * H))
    ew = 0.618 * H ** 0.753 + 10.0 * np.exp((H - 100.0) / 10.0) + 0.18 * (21.1 - T) * (1.0 - np.exp(-0.115 * H))
    ko = 0.424 * (1.0 - (H / 100.0) ** 1.7) + 0.0694 * np.sqrt(W) * (1.0 - (H / 100.0) ** 8)
    kd = ko * 0.581 * np.exp(0.0365 * T)
    k1 = 0.424 * (1.0 - ((100.0 - H) / 100.0) ** 1.7) + 0.0694 * np.sqrt(W) * (1.0 - ((100.0 - H) / 100.0) ** 8)
    kw = k1 * 0.581 * np.exp(0.0365 * T)
    m = np.where(mo > ed, ed + (mo - ed) * 10.0 ** (-kd), np.where(mo < ew, ew - (ew - mo) * 10.0 ** (-kw), mo))
    f = 59.5 * (250.0 - m) / (147.2 + m)
    return np.clip(f, 0.0, 101.0)


def dmc(po, T, H, r, mon):
    T = np.maximum(T, -1.1)
    rk = 1.894 * (T + 1.1) * (100.0 - H) * EL[mon - 1] * 1e-4
    wet = r > 1.5
    re = 0.92 * r - 1.27
    mo = 20.0 + np.exp(5.6348 - po / 43.43)
    pos = np.maximum(po, 1e-6)
    b = np.where(po <= 33.0, 100.0 / (0.5 + 0.3 * po), np.where(po <= 65.0, 14.0 - 1.3 * np.log(pos), 6.2 * np.log(pos) - 17.2))
    res = np.where(wet, re, 0.0)
    mr = mo + 1000.0 * res / (48.77 + b * res)
    pr = np.maximum(244.72 - 43.43 * np.log(np.maximum(mr - 20.0, 1e-9)), 0.0)
    pr = np.where(wet, pr, po)
    return np.maximum(pr + rk, 0.0)


def dc(do, T, r, mon):
    T = np.maximum(T, -2.8)
    pe = np.maximum((0.36 * (T + 2.8) + FL[mon - 1]) / 2.0, 0.0)
    wet = r > 2.8
    rd = 0.83 * r - 1.27
    Qo = 800.0 * np.exp(-do / 400.0)
    Qr = Qo + 3.937 * np.where(wet, rd, 0.0)
    Dr = np.maximum(400.0 * np.log(800.0 / Qr), 0.0)
    Dr = np.where(wet, Dr, do)
    return Dr + pe


def isi(f, W):
    fm = 147.2 * (101.0 - f) / (59.5 + f)
    sf = 19.115 * np.exp(-0.1386 * fm) * (1.0 + fm ** 5.31 / 4.93e7)
    return sf * np.exp(0.05039 * W)


def bui(p, d):
    s = p + 0.4 * d
    s = np.where(s > 0, s, 1.0)
    u1 = 0.8 * p * d / s
    u2 = p - (1.0 - 0.8 * d / s) * (0.92 + (0.0114 * p) ** 1.7)
    u = np.where(p <= 0.4 * d, u1, u2)
    return np.where((p <= 0) | (d < 0), 0.0, np.maximum(u, 0.0))


def fwi(R, U):
    bb = np.where(U <= 80.0, 0.1 * R * (0.626 * U ** 0.809 + 2.0), 0.1 * R * (1000.0 / (25.0 + 108.64 * np.exp(-0.023 * U))))
    out = np.where(bb > 1.0, np.exp(2.72 * (0.434 * np.log(np.maximum(bb, 1e-9))) ** 0.647), bb)
    return out


def run_season(T, H, W, r, mon, f0=85.0, p0=6.0, d0=15.0):
    """T, H, W, r: arrays (n_series, n_days); mon: (n_days,). Days with any missing T/H/W keep the previous codes
    and get FWI = NaN. Missing rain is treated as 0 (callers count it). Returns ffmc, dmc, dc, isi, bui, fwi."""
    n, nd = T.shape
    f = np.full(n, f0); p = np.full(n, p0); d = np.full(n, d0)
    out = {k: np.full((n, nd), np.nan) for k in ("ffmc", "dmc", "dc", "isi", "bui", "fwi")}
    for j in range(nd):
        t, h, w, rr = T[:, j], H[:, j], W[:, j], r[:, j]
        ok = np.isfinite(t) & np.isfinite(h) & np.isfinite(w)
        rr = np.where(np.isfinite(rr), rr, 0.0)
        hh = np.clip(np.where(ok, h, 50.0), 0.0, 100.0)
        tt = np.where(ok, t, 10.0)
        ww = np.maximum(np.where(ok, w, 0.0), 0.0)
        fn = ffmc(f, tt, hh, ww, rr)
        pn = dmc(p, tt, hh, rr, mon[j])
        dn = dc(d, tt, rr, mon[j])
        f = np.where(ok, fn, f); p = np.where(ok, pn, p); d = np.where(ok, dn, d)
        R = isi(f, ww)
        U = bui(p, d)
        F = fwi(R, U)
        for k, v in (("ffmc", f), ("dmc", p), ("dc", d), ("isi", R), ("bui", U), ("fwi", F)):
            out[k][:, j] = np.where(ok, v, np.nan)
    return out


if __name__ == "__main__":
    # check against the worked example in Van Wagner and Pickett (1985) / cffdrs test values:
    # day 1: T 17, H 42, W 25, r 0, month 4, start 85/6/15 -> FFMC 87.69, DMC 8.55, DC 19.01, ISI 10.85, BUI 8.49, FWI 10.10
    o = run_season(np.array([[17.0]]), np.array([[42.0]]), np.array([[25.0]]), np.array([[0.0]]), np.array([4]))
    print({k: round(float(v[0, 0]), 2) for k, v in o.items()})
