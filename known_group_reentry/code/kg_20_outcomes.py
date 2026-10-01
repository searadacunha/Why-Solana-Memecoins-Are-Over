#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outcomes and simulated trades of analysis_plan.md sections 4-5, from the post-detection-edge snapshot (frozen
spot series, its coverage rules, its simulator and cost model, imported unchanged). Written after the features
were frozen (commit 8bae78e). Writes derived/kg_outcomes.jsonl.gz and derived/KG_OUTCOMES.json (sha256).
"""

from __future__ import annotations

import bisect
import gzip
import hashlib
import json
import math
import os
import sys
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "post_detection_edge", "code"))
import pde  # noqa: E402
import trade  # noqa: E402

FEATURES = os.path.join(STUDY, "derived", "kg_features.jsonl.gz")
OUT = os.path.join(STUDY, "derived", "kg_outcomes.jsonl.gz")
META = os.path.join(STUDY, "derived", "KG_OUTCOMES.json")
LATS = (0, 5, 15, 30)
HS = (5, 10, 30, 60, 300, 900, 3600)
BIN_H = (60, 300, 900, 3600)
BIN_K = (1.10, 1.25, 1.50, 2.00)
TIME_EXITS = (10, 30, 60, 300, 900)
TPSL = ((1.25, 0.90), (1.50, 0.85), (2.00, 0.80))
TPSL_TIMEOUT = 900
SIZES = (100, 500, 1000)
COST = {"fee_per_leg": 0.01, "fixed_sol_per_tx": 0.005, "k_pool": 1.39e10, "k_curve": 30 * 1.073e9}
NOFEE = dict(COST, fee_per_leg=0.0, fixed_sol_per_tx=0.0)
PRIMARY = ("L5", "tp1.50_sl0.85")


def point_and_mae(
    pts: list[tuple[float, float]], t_in: float, m_in: float, h: float, fine: bool
) -> tuple[Optional[float], Optional[float], Optional[float], bool]:
    """(point return at entry + h, MFE, MAE over the window, observed)."""
    mx, obs = pde.window(pts, t_in, h, fine)
    i = bisect.bisect_right(pts, (t_in, math.inf))
    inside = [m for dt, m in pts[i:] if dt <= t_in + h]
    j = bisect.bisect_left(pts, (t_in + h, -math.inf))
    pt = None
    if obs and j < len(pts) and pts[j][0] - (t_in + h) <= pde.gap_limit(fine, h):
        pt = pts[j][1] / m_in
    return (pt, (mx / m_in) if mx is not None else None, (min(inside) / m_in) if inside else None, obs)


def target_path(
    pts: list[tuple[float, float]], t_in: float, m_in: float, k: float, h: float
) -> tuple[Optional[float], Optional[float]]:
    """(time to k x entry within h, lowest multiple before it) on the reads; (None, low) if not reached."""
    i = bisect.bisect_right(pts, (t_in, math.inf))
    low = 1.0
    for dt, m in pts[i:]:
        if dt > t_in + h:
            break
        r = m / m_in
        if r >= k:
            return dt - t_in, low
        low = min(low, r)
    return None, low


def nets(sim: dict[str, Any], r: dict[str, Any]) -> dict[str, Any]:
    src = r["f"]["p0_source"]
    out: dict[str, Any] = {}
    for sz in SIZES:
        out["net_%d" % sz] = trade.net_return(sim["gross"], sim["entry_mult"], r["p0"], src, r["t"], sz, COST)
    out["net_500_k05"] = trade.net_return(sim["gross"], sim["entry_mult"], r["p0"], src, r["t"], 500, COST, 0.5)
    out["net_500_k2"] = trade.net_return(sim["gross"], sim["entry_mult"], r["p0"], src, r["t"], 500, COST, 2.0)
    no_impact = trade.net_return(sim["gross"], sim["entry_mult"], r["p0"], src, r["t"], 500, COST, 1e9)
    out["fees_500"] = no_impact - (sim["gross"] - 1)
    out["slippage_500"] = out["net_500"] - no_impact
    return out


def main() -> None:
    S = pde.load_series()
    feats = [json.loads(x) for x in gzip.open(FEATURES, "rt", encoding="utf8")]
    rows = []
    for r in feats:
        pts = S.get(r["mint"]) or []
        o: dict[str, Any] = {"mint": r["mint"], "has_series": bool(pts)}
        for lat in LATS:
            ent = pde.entry_point(pts, lat) if pts else None
            key = "L%d" % lat
            if ent is None:
                o[key] = None
                continue
            t_in, m_in = ent
            d: dict[str, Any] = {"entry_dt": t_in, "entry_mult": m_in}
            for h in HS:
                pt, mfe, mae, obs = point_and_mae(pts, t_in, m_in, h, r["fine"])
                d["h%d" % h] = {"ret": pt, "mfe": mfe, "mae": mae, "obs": obs}
            for h in BIN_H:
                mx, obs = pde.window(pts, t_in, h, r["fine"])
                for k in BIN_K:
                    d["y_%.2f_%d" % (k, h)] = pde.outcome((mx / m_in) if mx is not None else None, obs, k)
            ttt, low = target_path(pts, t_in, m_in, 1.5, 3600)
            d["time_to_1.5"] = ttt
            d["low_before_1.5"] = low
            sims = {}
            for te in TIME_EXITS:
                sims["time%d" % te] = trade.simulate(pts, r["fine"], lat, math.inf, None, te)
            for tp, sl in TPSL:
                sims["tp%.2f_sl%.2f" % (tp, sl)] = trade.simulate(pts, r["fine"], lat, tp, sl, TPSL_TIMEOUT)
            sims["tp1.50_sl0.85_next"] = trade.simulate(pts, r["fine"], lat, 1.5, 0.85, TPSL_TIMEOUT, "next")
            for name, sim in sims.items():
                if sim["status"] == "ok":
                    sim.update(nets(sim, r))
            d["trades"] = sims
            o[key] = d
        rows.append(o)
    raw = "".join(json.dumps(x, sort_keys=True) + "\n" for x in rows).encode()
    with open(OUT, "wb") as fh:
        fh.write(gzip.compress(raw, mtime=0))
    meta = {
        "sha256_outcomes": hashlib.sha256(open(OUT, "rb").read()).hexdigest(),
        "rows": len(rows),
        "with_series": sum(1 for x in rows if x["has_series"]),
        "entries": {"L%d" % lat: sum(1 for x in rows if x.get("L%d" % lat)) for lat in LATS},
        "primary_observed": sum(1 for x in rows if x.get("L5") and x["L5"]["y_1.50_900"] is not None),
        "primary_trades_ok": sum(1 for x in rows if x.get("L5") and x["L5"]["trades"][PRIMARY[1]]["status"] == "ok"),
    }
    json.dump(meta, open(META, "w"), indent=1, sort_keys=True)
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
