#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pat_35_composites.py -- pre-specified composite patterns evaluated on DISCOVERY only.

Input: tables/composite_patterns.json (patterns written BEFORE this evaluation; conditions are
feature high (>= DISCOVERY quantile q) / low (<= q) / gt0 / eq0). For each pattern and each target
(Y2 / Y3 / Y5 at 1 h from +5 s), on the eligible DISCOVERY rows only:
  N, days, clusters, base rate, precision, lift, cluster-capped lift, one-sided Wilson lower bound
  of the lift, coverage (share of all DISCOVERY alerts), expected trades per active day, successes,
  failures, break-even precision of the pre-declared trade, expected value (mean net at $500 and
  $100 of the pre-declared trade among the fires), the same for the complement (negative filters).
Robustness, DISCOVERY only: stricter and looser quantiles (q +- 0.15), the alert - 2 s rebuild of
the features that have one (pg_* and fA), DISCOVERY halves and weeks; coherence = every variant keeps
the pattern's direction on Y2 and Y3.
New information: lift of the pattern without its pg_* conditions, of its pg_* conditions alone, and
the largest Jaccard between the pattern's firing set and any single existing (non-pg) atom.
Registered as exploratory. No SELECTION, VALIDATION or OOS label is read.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

import numpy as np

import ap_data as D
import ap_lib as A
import ap_mine as M

STEP = 0.15
CATEGORY = {   # report categories (owner's instruction) by pattern family and direction
    "E_WASH": "TOP WASH", "D_COORDINATION": "TOP COORDINATION", "F_FUNDING_COORD": "TOP FUNDING x COORDINATION",
    "A_REAL_DEMAND": "TOP DIVERSITY x VOLUME", "C_BUY_RUN": "TOP BUY-RUN", "B_ORGANIC_RELAY": "TOP ORGANIC RELAY",
    "G_CREATOR_EARLY": "TOP CREATOR x WALLET HISTORY", "H_BUNDLE_POST": "TOP BUNDLE x POST-BUNDLE",
    "I_BOT_SCRIPT": "TOP COORDINATION",
}


def threshold(x_ref, op, q):
    """Threshold value and the comparison actually applied (>= / > or <= / <) on DISCOVERY values."""
    v = x_ref[~np.isnan(x_ref)]
    if op == "gt0":
        return 0.0, "gt"
    if op == "eq0":
        return 0.0, "eq"
    q = min(0.95, max(0.05, q))
    thr = float(np.quantile(v, q))
    if op == "high":
        return thr, ("ge" if thr > v.min() else "gt")
    return thr, ("le" if thr < v.max() else "lt")


def apply(x, thr, cmp):
    ok = ~np.isnan(x)
    if cmp == "ge":
        return ok & (x >= thr)
    if cmp == "gt":
        return ok & (x > thr)
    if cmp == "le":
        return ok & (x <= thr)
    if cmp == "lt":
        return ok & (x < thr)
    return ok & (x == thr)


def fire_vector(X, names, conds, rows_ref, shift=0.0, Xvar=None, varcols=None):
    """Firing vector over all rows; thresholds from rows_ref (DISCOVERY). shift moves every quantile
    towards strictness (+) or looseness (-). Xvar / varcols: use the - 2 s variant where it exists."""
    f = np.ones(X.shape[0], dtype=bool)
    used = []
    for c in conds:
        j = names.index(c["feature"])
        src = Xvar if (Xvar is not None and c["feature"] in varcols) else X
        x = src[:, j].astype(np.float64)
        q = c.get("q", 0.5)
        if c["op"] == "high":
            q = q + shift
        elif c["op"] == "low":
            q = q - shift
        thr, cmp = threshold(X[rows_ref, j].astype(np.float64), c["op"], q)
        f &= apply(x, thr, cmp)
        used.append({"feature": c["feature"], "op": c["op"], "q": c.get("q"), "thr": thr, "cmp": cmp})
    return f, used


def stats(f, rows, y, days, clusters, Kd, cap, net500, net100, be):
    fr = f[rows]
    yy = y[rows]
    n = int(fr.sum())
    base = float(yy.mean())
    out = {"n": n, "base": base, "successes": int(yy[fr].sum()), "failures": int(n - yy[fr].sum()),
           "days": int(len(set(days[rows][fr]))), "clusters": int(len(set(clusters[rows][fr])))}
    if n == 0:
        out.update(precision=None, lift=None, capped_lift=None, lift_lb=None, ev_500=None, ev_100=None, complement_precision=None)
        return out
    p = float(yy[fr].mean())
    ne, he, pe = M.capped(fr[None, :].astype(np.float32), yy.astype(np.float32), Kd, cap)
    base_e = float(M.capped(np.ones((1, len(rows)), dtype=np.float32), yy.astype(np.float32), Kd, cap)[2][0])
    lb = float(A.wilson_lb_vec(np.array([yy[fr].sum()]), np.array([n]), z=1.2816)[0])
    out.update(precision=p, lift=(p / base if base else None), capped_lift=(float(pe[0] / base_e) if base_e else None),
               capped_n=float(ne[0]), lift_lb=(lb / base if base else None),
               ev_500=(float(np.nanmean(net500[rows][fr])) if (~np.isnan(net500[rows][fr])).sum() else None),
               ev_100=(float(np.nanmean(net100[rows][fr])) if (~np.isnan(net100[rows][fr])).sum() else None),
               break_even=be, above_break_even=bool(p > be),
               complement_precision=(float(yy[~fr].mean()) if (~fr).sum() else None),
               complement_ev_500=(float(np.nanmean(net500[rows][~fr])) if (~np.isnan(net500[rows][~fr])).sum() else None))
    return out


def main() -> None:
    lib_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(A.TABLES, "composite_patterns.json")
    lib = json.load(open(lib_path))["patterns"]
    mx = D.load_matrix()
    lab = D.label_arrays("discovery", mx["mints"])
    rows = np.flatnonzero(lab["elig"])
    assert set(mx["blocks"][rows]) == {"DISC"}
    X, XA2, names, days, clusters = mx["X"], mx["XA2"], mx["names"], mx["days"], mx["clusters"]
    varcols = set(mx["variant_columns"]) | {n for n in names if n.startswith("pg_")}
    excl = D.excluded_features()
    for p in lib:
        for c in p["conditions"]:
            if c["feature"] not in names:
                raise SystemExit("unknown feature %s in %s" % (c["feature"], p["id"]))
            if c["feature"] in excl:
                raise SystemExit("excluded feature %s in %s" % (c["feature"], p["id"]))
    Kd = M.cluster_onehot(clusters[rows])
    cap = M.CFG["CAP"]
    ex = lab["extra"]
    nets = {tg: (ex["%s.net_500" % A.STRAT_OF[tg]], ex["%s.net_100" % A.STRAT_OF[tg]]) for tg in A.TARGETS}
    be = {}
    for tg in A.TARGETS:
        v, y = nets[tg][0][rows], lab["y"][tg][rows]
        ok = ~np.isnan(v)
        w, l = v[ok & (y == 1)].mean(), v[ok & (y == 0)].mean()
        be[tg] = float(-l / (w - l))
    active_days = len(set(days[rows]))
    n_disc_alerts = int((mx["blocks"] == "DISC").sum())
    # single existing atoms (non-pg) for the reformulation check, DISCOVERY rows
    B, desc, _ = M.prepare_atoms(X, names, mx["meta"], rows, excl, D.no_missing_features())
    keep = np.array([not d["feat"].startswith("pg_") for d in desc])
    Bd = B[keep][:, rows]
    desc_e = [d for d, k in zip(desc, keep) if k]
    week = ((mx["t"] - A.utc("2026-08-24 00:00:00")) // (7 * 86400)).astype(int)
    h = len(rows) // 2
    results = []
    n_tests = 0
    for p in lib:
        f, used = fire_vector(X, names, p["conditions"], rows)
        rec = {"id": p["id"], "family": p["family"], "direction": p["direction"], "source": p.get("source", "?"),
               "category": CATEGORY.get(p["family"], "?"), "conditions": used, "rationale": p["rationale"], "fragility": p["fragility"],
               "features_families": sorted({mx["meta"][c["feature"]]["family"] for c in p["conditions"]}),
               "coverage": float(f[mx["blocks"] == "DISC"].mean()),
               "expected_trades_per_active_day": float(f[mx["blocks"] == "DISC"].sum() / active_days),
               "n_fires_all_disc_alerts": int(f[mx["blocks"] == "DISC"].sum()), "disc_alerts": n_disc_alerts, "active_days": active_days}
        if p["direction"] == "negative_filter":
            rec["category"] = "TOP NEGATIVE FILTERS"
        rec["main"] = {tg: stats(f, rows, lab["y"][tg], days, clusters, Kd, cap, nets[tg][0], nets[tg][1], be[tg]) for tg in A.TARGETS}
        n_tests += 3
        # robustness variants
        rec["variants"] = {}
        for name, kw in (("strict", {"shift": STEP}), ("loose", {"shift": -STEP}), ("cut2", {"Xvar": XA2, "varcols": varcols})):
            g, _ = fire_vector(X, names, p["conditions"], rows, **kw)
            rec["variants"][name] = {tg: stats(g, rows, lab["y"][tg], days, clusters, Kd, cap, nets[tg][0], nets[tg][1], be[tg]) for tg in ("Y2", "Y3")}
            rec["variants"][name]["same_fires_share"] = float((g == f)[rows].mean())
            n_tests += 2
        # sub-periods
        sub = {}
        for lbl, rr in (("half1", rows[:h]), ("half2", rows[h:])):
            sub[lbl] = {tg: {"n": int(f[rr].sum()), "precision": (float(lab["y"][tg][rr][f[rr]].mean()) if f[rr].sum() else None),
                             "base": float(lab["y"][tg][rr].mean())} for tg in ("Y2", "Y3")}
            n_tests += 2
        wk = {}
        for w in sorted(set(week[rows])):
            rr = rows[week[rows] == w]
            if f[rr].sum() >= 5:
                y2 = lab["y"]["Y2"][rr]
                wk[int(w)] = {"n": int(f[rr].sum()), "precision_x2": float(y2[f[rr]].mean()), "base_x2": float(y2.mean())}
                n_tests += 1
        rec["subperiods"] = {"halves": sub, "weeks": wk}
        # new information: without pg conditions, pg only, closest existing single atom
        conds_e = [c for c in p["conditions"] if not c["feature"].startswith("pg_")]
        conds_p = [c for c in p["conditions"] if c["feature"].startswith("pg_")]
        parts = {}
        for lbl, cc in (("existing_only", conds_e), ("pg_only", conds_p)):
            if cc:
                g, _ = fire_vector(X, names, cc, rows)
                parts[lbl] = {tg: stats(g, rows, lab["y"][tg], days, clusters, Kd, cap, nets[tg][0], nets[tg][1], be[tg]) for tg in ("Y2", "Y3")}
                n_tests += 2
        fd = f[rows].astype(np.float32)
        inter = Bd.astype(np.float32) @ fd
        union = Bd.sum(1) + fd.sum() - inter
        jac = inter / np.maximum(union, 1)
        k = int(np.argmax(jac))
        rec["new_information"] = {"parts": parts, "closest_existing_atom": M.rule_text((0,), [desc_e[k]]) if len(desc_e) else None,
                                  "closest_existing_atom_jaccard": float(jac[k]) if len(desc_e) else None}
        # coherence of the direction across variants and halves (Y2 and Y3)
        sign = 1 if p["direction"] == "positive" else -1
        checks = []
        for tg in ("Y2", "Y3"):
            for v in ("strict", "loose", "cut2"):
                s_ = rec["variants"][v][tg]
                checks.append(s_["lift"] is not None and s_["n"] >= 8 and sign * (s_["lift"] - 1) > 0)
            for hl in ("half1", "half2"):
                s_ = sub[hl][tg]
                checks.append(s_["precision"] is not None and s_["n"] >= 5 and sign * (s_["precision"] - s_["base"]) > 0)
        rec["robustness"] = {"checks_passed": int(sum(checks)), "checks_total": len(checks), "coherent": bool(all(checks))}
        results.append(rec)
    A.registre("composites_discovery", n_tests, "pre-specified composite patterns on DISCOVERY (%d patterns, variants, halves, weeks, parts)" % len(lib),
               {"library": os.path.relpath(lib_path, A.STUDY)}, n=int(len(rows)), declare=False, sortie="tables/composite_patterns_results.json")
    A.write_json(os.path.join(A.TABLES, "composite_patterns_results.json"),
                 {"break_even": be, "active_days": active_days, "n_rows": int(len(rows)), "patterns": results})
    for r in results:
        m2, m3 = r["main"]["Y2"], r["main"]["Y3"]
        print("%-36s %-24s n %3d d %2d cl %2d | x2 %s lift %s (cap %s) | x3 %s lift %s | EV500 %s | robust %d/%d | pg-only x2 lift %s | jac %.2f %s" % (
            r["id"], r["category"][:24], m2["n"], m2["days"], m2["clusters"],
            "%.2f" % m2["precision"] if m2["precision"] is not None else "n/a", "%.2f" % m2["lift"] if m2["lift"] else "n/a",
            "%.2f" % m2["capped_lift"] if m2["capped_lift"] else "n/a",
            "%.2f" % m3["precision"] if m3["precision"] is not None else "n/a", "%.2f" % m3["lift"] if m3["lift"] else "n/a",
            "%.2f" % m2["ev_500"] if m2["ev_500"] is not None else "n/a", r["robustness"]["checks_passed"], r["robustness"]["checks_total"],
            "%.2f" % r["new_information"]["parts"]["pg_only"]["Y2"]["lift"] if r["new_information"]["parts"].get("pg_only", {}).get("Y2", {}).get("lift") else "n/a",
            r["new_information"]["closest_existing_atom_jaccard"] or 0, (r["new_information"]["closest_existing_atom"] or "")[:40]))


if __name__ == "__main__":
    main()
