#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_10_labels.py -- labels and simulated trades from the frozen price series.

Entry = first price read in [5, 15] s after the alert (pde.entry_point), a spot price, not a fill.
Labels Yk_H: k x the entry price reached within H seconds of the entry, k in 2/3/5, H in 30 min / 1 h / 2 h.
  conf   = two consecutive reads at or above k x entry (primary; a single spike is not a fill)
  single = one read
  None   = window not observed under the coverage rule of pde.py (censored), never a miss.
Path facts at 1 h: time to the confirmed hit, lowest multiple before it, MFE, MAE.
Trades at 1 h (post_detection_edge/code/trade.py, unchanged cost model): take profit at k x with
exit at the next read or at the touch, optional stop at -50 %, and pure time exits.

The script prints coverage counts only, never a rate. Every block is written; reading them is
gated by ap_lib.load_labels(stage).
"""
from __future__ import annotations

import os
import sys
from collections import Counter

import ap_lib as A

sys.path.insert(0, os.path.join(A.W, "post_detection_edge", "code"))
import pde  # noqa: E402
import trade  # noqa: E402

NEVER = 1e12


def path_labels(pts, fine, dt_e, m_e):
    out = {}
    for h in A.HORIZONS:
        mx, ok = pde.window(pts, dt_e, h, fine)
        ins = [(dt - dt_e, m / m_e) for dt, m in pts if dt_e < dt <= dt_e + h]
        tag = "%d" % h
        out["obs_" + tag] = bool(ok)
        out["mfe_" + tag] = (mx / m_e) if (ok and mx is not None) else None
        out["mae_" + tag] = min(r for _, r in ins) if (ok and ins) else None
        for k in A.MULTS:
            name = "%gx_%s" % (k, tag)
            if not ok:
                out["single_" + name] = out["conf_" + name] = None
                continue
            out["single_" + name] = int(any(r >= k for _, r in ins))
            hit = None
            for (d1, r1), (d2, r2) in zip(ins, ins[1:]):
                if r1 >= k and r2 >= k:
                    hit = d2
                    break
            out["conf_" + name] = int(hit is not None)
            if h == A.PRIMARY_H:
                out["t_hit_%gx" % k] = hit
                out["low_before_%gx" % k] = (min(r for d, r in ins if d <= hit) if hit is not None else None)
    return out


def trades(pts, fine, lat, p0, src, t):
    out = {}
    specs = []
    for k in A.MULTS:
        specs.append(("tp%g_next" % k, k, None, 3600, "next"))
        specs.append(("tp%g_touch" % k, k, None, 3600, "touch"))
        specs.append(("tp%g_sl50_next" % k, k, 0.5, 3600, "next"))
    for to in (60, 300, 900, 3600):
        specs.append(("time%d" % to, NEVER, None, to, "next"))
    for name, tp, sl, to, mode in specs:
        sim = trade.simulate(pts, fine, lat, tp, sl, to, mode)
        rec = {"status": sim["status"]}
        if sim["status"] == "ok":
            rec.update(reason=sim["reason"], gross=sim["gross"], dt=sim["dt"])
            for sz in A.SIZES:
                rec["net_%d" % sz] = trade.net_return(sim["gross"], sim["entry_mult"], p0, src, t, sz, A.COST)
            rec["net_500_k05"] = trade.net_return(sim["gross"], sim["entry_mult"], p0, src, t, 500, A.COST, 0.5)
            rec["net_500_k2"] = trade.net_return(sim["gross"], sim["entry_mult"], p0, src, t, 500, A.COST, 2.0)
        out[name] = rec
    return out


def main() -> None:
    base = A.load_base()
    series = pde.load_series()
    src_of = {}
    for path in (A.PDE_DEV, A.PDE_TEST):
        for r in A.jl(path):
            src_of[r["mint"]] = r["f"]["p0_source"]
    rep: Counter = Counter()
    rows = []
    for b in base:
        m = b["mint"]
        pts = series.get(m) or []
        rec = {"mint": m, "t": b["t"], "block": b["block"], "fine": b["fine"], "cluster": b["cluster"],
               "has_series": bool(pts), "p0_source": src_of[m]}
        rep["alerts_" + b["block"]] += 1
        if any(dt + b["t"] >= A.T_SNAP for dt, _ in pts):
            raise ValueError("price read after the snapshot: " + m)
        ent = pde.entry_point(pts, A.LAT) if pts else None
        rec["entry"] = None
        if ent is not None:
            dt_e, m_e = ent
            rec["entry"] = {"dt": dt_e, "mult": m_e}
            rec.update(path_labels(pts, b["fine"], dt_e, m_e))
            rec["trades"] = trades(pts, b["fine"], A.LAT, b["p0"], src_of[m], b["t"])
            rep["entry_" + b["block"]] += 1
            rep["obs1h_" + b["block"]] += rec["obs_3600"]
        # latency sensitivity: entry at +15 s
        e15 = pde.entry_point(pts, 15.0) if pts else None
        if e15 is not None:
            pl = path_labels(pts, b["fine"], e15[0], e15[1])
            rec["L15"] = {"entry_mult": e15[1], "obs_3600": pl["obs_3600"],
                          **{"conf_%gx" % k: pl["conf_%gx_3600" % k] for k in A.MULTS},
                          "trades": {n: v for n, v in trades(pts, b["fine"], 15.0, b["p0"], src_of[m], b["t"]).items()
                                     if n.endswith("_next") and "sl" not in n}}
        rows.append(rec)
    A.write_jl(os.path.join(A.DERIVED, "labels.jsonl.gz"), rows)
    A.write_json(os.path.join(A.DERIVED, "labels_coverage.json"), dict(sorted(rep.items())))
    for k, v in sorted(rep.items()):
        print("%-16s %d" % (k, v))


if __name__ == "__main__":
    main()
