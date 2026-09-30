#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ez_lib.py -- shared by the entry-zone scripts: the frozen table (sha256 checked against
derived/EZ_FREEZE.json), the variables by family, atoms and their bitmasks, the
selection metric of analysis_plan.md, and the statistics.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import random
import statistics
import sys
from collections import defaultdict
from typing import Any, Callable, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "post_detection_edge", "code"))
import pde  # noqa: E402

DERIVED = os.path.join(STUDY, "derived")
TABLES = os.path.join(STUDY, "tables")
TABLE = os.path.join(DERIVED, "ez_table.jsonl.gz")
FREEZE = os.path.join(DERIVED, "EZ_FREEZE.json")
CUTS = ["T0", "D", "P5", "P10", "P20", "P30", "P60", "P120", "P300"]
PRIMARY = "conf_2"
MIN_N = 40
SEED = 20260930
B = 1000

SOL_VARS = ["sol_total", "sol_bundle", "sol_outside", "sol_early_total", "sol_mean", "sol_median", "sol_max",
            "sol_top2", "sol_top3", "top1_share", "sol_hhi", "sol_early_max"]
CAP_VARS = ["cap_%s_%s" % (g, s) for g in ("all", "snipers", "early")
            for s in ("sum", "max", "median", "n_ge1", "n_ge2", "n_ge5", "n_ge10", "n_ge20",
                      "spent_over_available", "spent_ratio_median")]
FUND_VARS = (["fu_first_median", "fu_first_max", "fu_first_min", "fu_first_sum", "fu_share_1sol_about",
              "fu_share_1sol_exact", "fu_share_hub", "fu_n_funders", "fu_top_funder_n", "fu_funder_hhi",
              "fu_ticket_over_recv_24h_median"]
             + ["fu_%s_%s_%s" % (a, w, b) for w in ("1h", "6h", "24h", "7d")
                for a, b in (("recv", "sum"), ("recv", "median"), ("recv", "max"), ("ntx", "sum"),
                             ("nfunders", "max"))])
FAMILIES: dict[str, list[str]] = {
    "market cap": ["mc_usd"],
    "premium": ["premium"],
    "other price": ["log_price", "pool_sol", "curve_left_sol", "mult_since_alert"],
    "SOL engaged": SOL_VARS,
    "counts and timing": ["n_buyers", "n_snipers", "n_early", "t_since_creation", "buys_5s", "buys_10s",
                          "t_first_outside"],
    "capacity": CAP_VARS,
    "funding": FUND_VARS}
FAM_OF = {v: f for f, vs in FAMILIES.items() for v in vs}
SOL_GRID = [1, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
SOL_ZONES = [(20, 40), (40, 60), (60, 80), (80, 100)]
SOL_GRID_VARS = {"sol_total", "sol_bundle", "sol_outside", "sol_early_total", "sol_max", "sol_top2", "sol_top3",
                 "sol_early_max"}
COUNT_GRID_VARS = {v for v in CAP_VARS if "_n_ge" in v} | {"n_snipers", "n_early", "n_buyers"}
COUNT_GRID = [1, 2, 3, 5]
MC_WIDTHS = [5000, 10000, 20000, 25000]


def load() -> list[dict[str, Any]]:
    doc = json.load(open(FREEZE))
    if hashlib.sha256(open(TABLE, "rb").read()).hexdigest() != doc["sha256"]:
        sys.exit("the entry-zone table differs from the frozen one")
    with gzip.open(TABLE, "rt", encoding="utf8") as fh:
        return [json.loads(x) for x in fh]


def observed(rows: Sequence[dict[str, Any]], cut: str, split: str) -> list[dict[str, Any]]:
    return [r for r in rows if r["split"] == split and r["y"][cut].get(PRIMARY) is not None]


def q(v: Sequence[Optional[float]], p: float) -> Optional[float]:
    s = sorted(x for x in v if x is not None)
    return s[int(p * (len(s) - 1))] if s else None


def wilson_lb(k: int, n: int) -> float:
    return (pde.wilson(k, n)[0] or 0.0) if n else 0.0


def rate(k: int, n: int) -> str:
    return pde.rate_cell(k, n)


# atoms: (cut, var, op, a, b); ops: le (v <= a), gt (v > a), in (a < v <= b), ge (v >= a), lt (v < a),
# zone (a <= v < b)
def holds(x: dict[str, Any], atom: tuple) -> bool:
    _, v, op, a, b = atom
    z = x.get(v)
    if z is None:
        return False
    return {"le": lambda: z <= a, "gt": lambda: z > a, "in": lambda: a < z <= b, "ge": lambda: z >= a,
            "lt": lambda: z < a, "zone": lambda: a <= z < b}[op]()


def text(atom: tuple) -> str:
    c, v, op, a, b = atom

    def f(u: float) -> str:
        return "%.4g" % u
    s = {"le": lambda: "%s <= %s" % (v, f(a)), "gt": lambda: "%s > %s" % (v, f(a)),
         "in": lambda: "%s < %s <= %s" % (f(a), v, f(b)), "ge": lambda: "%s >= %s" % (v, f(a)),
         "lt": lambda: "%s < %s" % (v, f(a)), "zone": lambda: "%s <= %s < %s" % (f(a), v, f(b))}[op]()
    return "[%s] %s" % (c, s)


def atoms_for(cut: str, var: str, tr: Sequence[dict[str, Any]], intervals: bool = True) -> list[tuple]:
    """TRAIN deciles as bounds (and intervals), plus the declared grids of analysis_plan.md."""
    xs = [r["f"][cut].get(var) for r in tr]
    xs = [x for x in xs if x is not None]
    if len(xs) < MIN_N or len(set(xs)) < 2:
        return []
    qs = sorted({q(xs, k / 10) for k in range(1, 10)})
    out = [(cut, var, "le", t, None) for t in qs] + [(cut, var, "gt", t, None) for t in qs]
    if intervals:
        out += [(cut, var, "in", a, b) for i, a in enumerate(qs) for b in qs[i + 1:]]
    lo, hi = q(xs, 0.01), q(xs, 0.99)
    if var in SOL_GRID_VARS:
        grid = SOL_GRID + [g for g in range(125, int(hi) + 25, 25)]
        out += [(cut, var, "ge", g, None) for g in grid if lo < g <= hi]
        out += [(cut, var, "lt", g, None) for g in grid if lo < g <= hi]
        out += [(cut, var, "zone", a, b) for a, b in SOL_ZONES]
    if var in COUNT_GRID_VARS:
        out += [(cut, var, "ge", g, None) for g in COUNT_GRID] + [(cut, var, "lt", g, None) for g in COUNT_GRID]
    if var == "mc_usd":
        # tranches over the bulk only (up to the TRAIN 95th percentile): P0 has a real tail to tens of
        # millions of USD (a buy on the pool inside the creation block), which the deciles already cover
        hi = q(xs, 0.95)
        for w in MC_WIDTHS:
            start = int(lo // w) * w
            edges = list(range(start, int(hi) + w, w))
            out += [(cut, var, "ge", e, None) for e in edges if lo < e <= hi]
            out += [(cut, var, "lt", e, None) for e in edges if lo < e <= hi]
            if intervals:
                out += [(cut, var, "zone", e, e + w) for e in edges]
    return sorted(set(out), key=lambda a: (a[1], a[2], a[3], a[4] or 0))


def mask(rows: Sequence[dict[str, Any]], atom: tuple) -> int:
    c = atom[0]
    return sum(1 << i for i, r in enumerate(rows) if holds(r["f"][c], atom))


def ybits(rows: Sequence[dict[str, Any]], cut: str, label: str = PRIMARY) -> int:
    return sum(1 << i for i, r in enumerate(rows) if r["y"][cut].get(label) == 1)


def metric(k: int, n: int, base: float) -> float:
    return wilson_lb(k, n) - base if n >= MIN_N else -1.0


def boot_lift(sel: Sequence[dict[str, Any]], allr: Sequence[dict[str, Any]], cut: str,
              pred: Callable[[dict[str, Any]], bool], b: int = B) -> tuple[Optional[float], Optional[float]]:
    """95 % CI of rate(selected) - rate(all), resampling operator clusters."""
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in allr:
        by[r["cluster"]].append(r)
    keys = sorted(by)
    rng = random.Random(SEED)
    out = []
    for _ in range(b):
        smp = [r for _ in keys for r in by[keys[rng.randrange(len(keys))]]]
        s = [r for r in smp if pred(r)]
        if not s:
            continue
        out.append(sum(r["y"][cut][PRIMARY] for r in s) / len(s) - sum(r["y"][cut][PRIMARY] for r in smp) / len(smp))
    if len(out) < b // 2:
        return None, None
    out.sort()
    return out[int(0.025 * (len(out) - 1))], out[int(0.975 * (len(out) - 1))]


def describe(sel: Sequence[dict[str, Any]], allr: Sequence[dict[str, Any]], cut: str) -> dict[str, Any]:
    """Rates at 1.5 / 2 / 3x, time to 2x, drawdown, for a selection against its population."""
    d: dict[str, Any] = {"n": len(sel), "n_all": len(allr), "excluded": len(allr) - len(sel)}
    for k in ("1.5", "2", "3"):
        ys = [r["y"][cut].get("conf_" + k) for r in sel]
        d["k_" + k] = sum(1 for y in ys if y == 1)
        d["base_" + k] = sum(1 for r in allr if r["y"][cut].get("conf_" + k) == 1) / len(allr) if allr else None
    tt = [r["y"][cut].get("t_2x_s") for r in sel if r["y"][cut].get("t_2x_s") is not None]
    dd = [r["y"][cut].get("drawdown") for r in sel if r["y"][cut].get("drawdown") is not None]
    d["t_2x_median"] = statistics.median(tt) if tt else None
    d["drawdown_median"] = statistics.median(dd) if dd else None
    return d


def write(name: str, lines: list[str]) -> None:
    os.makedirs(TABLES, exist_ok=True)
    with open(os.path.join(TABLES, name), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")


def auc(scores: Sequence[float], y: Sequence[int]) -> Optional[float]:
    return pde.auc(scores, y)


def fmt(x: Optional[float], p: str = "%.3f") -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else p % x
