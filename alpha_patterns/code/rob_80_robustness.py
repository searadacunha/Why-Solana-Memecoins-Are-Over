#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rob_80_robustness.py -- robustness and economics of every frozen candidate (after the OOS read).

Descriptive: nothing here can promote a candidate; a failed check can only demote it.
VALIDATION + OOS statistics are stratified by block (Mantel-Haenszel rate ratio, CMH p by day).
For each candidate:
  thresholds   each atom moved to the next DISTINCT quantile threshold, one at a time; a neighbour
               is 'tested' (>= 5 fires), 'small' (< 5 fires) or 'not_testable' (few-valued feature,
               missing atom, no distinct neighbour). The criterion needs >= 1 tested neighbour and
               every tested neighbour above a lift of 1.
  cut-offs     features rebuilt at alert - 2 s and alert - 5 s (fA2 / fA5), 'not_testable' otherwise
  labels       2x / 3x / 5x, confirmed and single read, 30 min / 1 h / 2 h
  periods      precision against the base rate week by week, all four blocks
  clusters     without the cluster that fires most; number of clusters firing
  extremes     mean net without the 2 best trades
  liquidity    without bonding-curve entries and without the lowest decile of pool SOL
  costs        $100 / $500 / $1000, K x0.5 / x2, exit at the touch, stop at -50 %, entry at +15 s
  path         time to target and lowest multiple before it among the hits
  frequency    fires per day of detector activity
  price        lift inside each tercile of the entry premium
"""
from __future__ import annotations

import json
import os
import time

import numpy as np

import ap_data as D
import ap_lib as A
import ap_mine as M
from val_60_validation import load_candidates


def strat_lift(f, y, rows, strata):
    """Rule statistics on `rows`, stratified: MH rate ratio and CMH one-sided p."""
    rr = rows[~np.isnan(y[rows])]
    if len(rr) == 0:
        return {"n": 0, "hits": 0, "prec": None, "base": None, "lift": None, "mh_lift": None, "p": None}
    ff, yy = f[rr], y[rr]
    n = int(ff.sum())
    st = M.strat_test(ff, yy, strata[rr])
    base = float(yy.mean())
    prec = float(yy[ff].mean()) if n else None
    return {"n": n, "hits": int(yy[ff].sum()) if n else 0, "prec": prec, "base": base,
            "lift": (prec / base if (prec is not None and base) else None), "mh_lift": st["mh_rr"], "p": st["p_cmh"]}


def atom_vec(X, names, d, thr=None):
    x = X[:, names.index(d["feat"])].astype(np.float64)
    ok = ~np.isnan(x)
    if d["op"] == "missing":
        return ~ok
    t = d["thr"] if thr is None else thr
    return ok & ((x <= t) if d["op"] == "<=" else (x > t))


def neighbour_thresholds(xref, d, quants):
    """Next distinct threshold below and above the atom's quantile; None when none exists."""
    cur = d["thr"]
    qs = list(quants)
    j = min(range(len(qs)), key=lambda z: abs(qs[z] - d["q"]))
    out = {}
    for step, lbl in ((-1, "lower"), (1, "higher")):
        thr = None
        k = j + step
        while 0 <= k < len(qs):
            v = float(np.quantile(xref, qs[k]))
            if v != cur:
                thr = v
                break
            k += step
        if thr is None:
            v = float(np.quantile(xref, 0.10 if step < 0 else 0.90))
            thr = v if v != cur else None
        out[lbl] = thr
    return out


def main() -> None:
    A.check_freeze()
    if not os.path.exists(A.OOS_DONE) or json.load(open(A.OOS_DONE)).get("status") != "done":
        raise SystemExit("OOS has not been read: robustness comes after it")
    mx = D.load_matrix()
    lab = D.label_arrays("oos", mx["mints"])
    X, names, blocks, t, days = mx["X"], mx["names"], mx["blocks"], mx["t"], mx["days"]
    elig, ex = lab["elig"], lab["extra"]
    atoms = json.load(open(os.path.join(A.DERIVED, "atoms.json")))
    ref = np.array(atoms["ref_rows"])
    quants = atoms["cfg"]["QUANTS"]
    hold = np.flatnonzero(elig & ((blocks == "VAL") | (blocks == "OOS")))
    rows_by = {b: np.flatnonzero(elig & (blocks == b)) for b in A.BLOCKS}
    week = ((t - A.utc("2026-08-24 00:00:00")) // (7 * 86400)).astype(int)
    prem = X[:, names.index("p_entry_over_operator")].astype(np.float64)
    pool = X[:, names.index("p_pool_sol")].astype(np.float64)
    src_pool = X[:, names.index("lv_src_pool")]
    q_prem = np.nanquantile(prem[ref], [1 / 3, 2 / 3])
    pool_p10 = np.nanquantile(pool[ref], 0.10)
    cl_ids = np.unique(mx["clusters"], return_inverse=True)[1]
    hold_all = (blocks == "VAL") | (blocks == "OOS")
    days_hold = len(set(days[hold_all]))
    out = []
    n_tests = 0
    for c in load_candidates():
        tg = c["target"]
        y = lab["y"][tg]
        f = c["fire"]
        k = {"Y2": 2, "Y3": 3, "Y5": 5}[tg]
        r: dict = {"id": c["id"], "target": tg, "text": c["text"], "kind": c["kind"]}
        hs = M.hold_summary(f, y, elig, blocks, days)
        r["blocks"] = hs["blocks"]
        r["hold"] = hs["hold"]
        n_tests += 1
        # thresholds (rules only)
        if c["rule"] is not None:
            vecs = [atom_vec(X, names, d) for d in c["atoms"]]
            neigh = []
            for i, d in enumerate(c["atoms"]):
                if d["op"] == "missing" or d["q"] is None:
                    neigh.append({"atom": d["feat"], "status": "not_testable", "reason": "missing atom or few-valued feature"})
                    continue
                x = X[ref, names.index(d["feat"])].astype(np.float64)
                x = x[~np.isnan(x)]
                for lbl, thr in neighbour_thresholds(x, d, quants).items():
                    if thr is None:
                        neigh.append({"atom": d["feat"], "move": lbl, "status": "not_testable", "reason": "no distinct neighbour"})
                        continue
                    g = atom_vec(X, names, d, thr)
                    for o, v in enumerate(vecs):
                        if o != i:
                            g = g & v
                    lo = strat_lift(g, y, hold, blocks)
                    n_tests += 1
                    neigh.append({"atom": d["feat"], "move": lbl, "thr": thr, "status": "tested" if lo["n"] >= 5 else "small", **lo})
            r["threshold_neighbours"] = neigh
            tested = [x for x in neigh if x["status"] == "tested"]
            r["threshold_n_tested"] = len(tested)
            r["threshold_n_small"] = sum(1 for x in neigh if x["status"] == "small")
            r["threshold_n_not_testable"] = sum(1 for x in neigh if x["status"] == "not_testable")
            lifts = [x["mh_lift"] for x in tested if x["mh_lift"] is not None]
            r["threshold_min_mh_lift"] = min(lifts) if lifts else None
            r["threshold_status"] = ("not_testable" if not tested else
                                     ("all_above_1" if all(x > 1 for x in lifts) and len(lifts) == len(tested) else "fails"))
            r["cutoffs"] = "not_testable"
            if any(d["feat"] in mx["variant_columns"] for d in c["atoms"]):
                r["cutoffs"] = {}
                for var in ("XA2", "XA5"):
                    g = np.ones(len(f), dtype=bool)
                    for d in c["atoms"]:
                        g &= atom_vec(mx[var] if d["feat"] in mx["variant_columns"] else X, names, d)
                    r["cutoffs"][var] = {**strat_lift(g, y, hold, blocks), "same_fires_share": float((g == f)[hold].mean())}
                    n_tests += 1
        else:
            r["threshold_status"] = "not_testable"
            r["cutoffs"] = "not_testable"
        # labels
        r["labels"] = {}
        for kk in A.MULTS:
            for h in A.HORIZONS:
                for kind in ("conf", "single"):
                    nm = "%s_%gx_%d" % (kind, kk, h)
                    r["labels"][nm] = strat_lift(f, ex[nm], np.flatnonzero(hold_all), blocks)
                    n_tests += 1
        # periods
        wk = {}
        for w in sorted(set(week[elig])):
            rows = np.flatnonzero(elig & (week == w))
            lo = strat_lift(f, y, rows, days)
            if lo["n"] >= 5:
                wk[int(w)] = lo
        r["weeks"] = wk
        r["weeks_above_base"] = "%d/%d" % (sum(1 for v in wk.values() if v["lift"] and v["lift"] > 1), len(wk))
        # clusters
        fh = f[hold]
        cc = cl_ids[hold][fh]
        r["clusters_firing_hold"] = int(len(set(cc)))
        r["days_firing_hold"] = int(len(set(days[hold][fh])))
        if len(cc):
            top = np.bincount(cc).argmax()
            r["top_cluster_share_of_fires"] = float((cc == top).mean())
            r["without_top_cluster"] = strat_lift(f, y, hold[cl_ids[hold] != top], blocks)
            n_tests += 1
        # liquidity
        r["liquid_only"] = strat_lift(f, y, hold[(src_pool[hold] == 1) & (pool[hold] > pool_p10)], blocks)
        # price strata
        r["premium_terciles"] = []
        for lo_, hi_ in ((-np.inf, q_prem[0]), (q_prem[0], q_prem[1]), (q_prem[1], np.inf)):
            r["premium_terciles"].append(strat_lift(f, y, hold[(prem[hold] > lo_) & (prem[hold] <= hi_)], blocks))
        r["premium_missing"] = strat_lift(f, y, hold[np.isnan(prem[hold])], blocks)
        n_tests += 5
        # economics
        eco = {}
        for strat in ("tp%g_next" % k, "tp%g_touch" % k, "tp%g_sl50_next" % k, "time60", "time300", "time900", "time3600"):
            for fld in ("net_100", "net_500", "net_1000", "net_500_k05", "net_500_k2"):
                v = ex["%s.%s" % (strat, fld)]
                st = M.net_stats(fh, v[hold], cl_ids[hold], 20000, 7)
                eco["%s.%s" % (strat, fld)] = {kk2: st.get(kk2) for kk2 in ("net_n", "net_censored", "net_clusters", "net_mean", "net_ci", "net_lb99", "net_win_share", "net_mean_all_alerts")}
                n_tests += 1
        v = ex["tp%g_next.net_500" % k][hold]
        m1 = fh & ~np.isnan(v)
        if m1.sum() > 4:
            eco["tp_next.net_500_without_2_best"] = float(np.sort(v[m1])[:-2].mean())
        v15 = ex.get("L15_tp%g_next.net_500" % k)
        if v15 is not None:
            st = M.net_stats(fh, v15[hold], cl_ids[hold], 20000, 7)
            eco["L15.tp_next.net_500"] = {kk2: st.get(kk2) for kk2 in ("net_n", "net_mean", "net_ci", "net_lb99")}
            r["L15_label"] = strat_lift(f, ex["L15_conf_%gx" % k], np.flatnonzero(hold_all), blocks)
        r["economics_hold"] = eco
        for b in ("VAL", "OOS"):
            rb = rows_by[b]
            st = M.net_stats(f[rb], ex["tp%g_next.net_500" % k][rb], cl_ids[rb], 20000, 7)
            r["net_500_" + b] = {kk2: st.get(kk2) for kk2 in ("net_n", "net_censored", "net_clusters", "net_mean", "net_ci", "net_lb99", "net_win_share")}
        # path among the hits
        th, lb_ = ex.get("t_hit_%gx" % k), ex.get("low_before_%gx" % k)
        if th is not None:
            m2 = fh & ~np.isnan(th[hold])
            if m2.sum():
                r["path_hits"] = {"n": int(m2.sum()), "t_hit_median_s": float(np.median(th[hold][m2])),
                                  "t_hit_p90_s": float(np.quantile(th[hold][m2], 0.9)),
                                  "low_before_median": float(np.median(lb_[hold][m2])),
                                  "low_before_p10": float(np.quantile(lb_[hold][m2], 0.1))}
        r["mae_median_fires"] = float(np.nanmedian(ex["mae_3600"][hold][fh])) if fh.sum() else None
        r["frequency"] = {"fires_all_alerts": int(f[hold_all].sum()), "alerts": int(hold_all.sum()),
                          "share": float(f[hold_all].mean()), "active_days": days_hold,
                          "fires_per_active_day": float(f[hold_all].sum() / days_hold)}
        out.append(r)
    A.write_json(os.path.join(A.TABLES, "robustness.json"),
                 {"written_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "candidates": out})
    A.registre("robustness", n_tests, "post-OOS descriptive robustness and economics of the frozen candidates",
               n=int(len(hold)), declare=False, sortie="tables/robustness.json")
    print("robustness written for %d candidates, %d descriptive computations" % (len(out), n_tests))


if __name__ == "__main__":
    main()
