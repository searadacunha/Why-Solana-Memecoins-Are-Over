#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading simulation of analysis_plan.md for the family rules whose VALIDATION lower bound is above
the base (derived/S_kept.json), with the simulator and costs of post_detection_edge (as in
entry_zone/code/ez_40_trade.py): entry at the alert plus 0 / 5 / 10 / 20 / 30 s, take profit at
1.5 / 2 / 3x or exit at the timeout of 5 / 15 / 30 / 60 min, no stop, $500 (and $100 / $1,000 at
10 s, 2x, 15 min). A cell with fewer than 10 simulated trades is not an estimate.
Writes tables/S4_trading.md.
"""

from __future__ import annotations

import json
import os
from typing import Any

import sc_20_analysis as S
import trade  # on sys.path through sc_20_analysis

COST = json.load(open(os.path.join(S.ROOT, "post_detection_edge", "tables", "LOCK.json")))["cost_model"]
DELAYS = [0, 5, 10, 20, 30]
EXITS = [(tp, to) for tp in (1.5, 2.0, 3.0) for to in (300, 900, 1800, 3600)]
MIN_TRADES = 10


def run(
    sel: list[dict[str, Any]], series: dict[str, Any], src: dict[str, str], lat: float, tp: float, to: float, size: int
) -> dict[str, Any]:
    res = []
    for r in sel:
        sim = trade.simulate(series.get(r["mint"]) or [], r["fine"], lat, tp, None, to, "touch")
        net = None
        if sim["status"] == "ok" and src.get(r["mint"]) and r.get("p0"):
            net = trade.net_return(sim["gross"], sim["entry_mult"], r["p0"], src[r["mint"]], r["t"], size, COST, 1.0)
        res.append((r["cluster"], sim, net))
    return trade.summarise(res)


def cell(s: dict[str, Any]) -> str:
    if s.get("n_ok", 0) < MIN_TRADES:
        return "not estimable (%d trades)" % s.get("n_ok", 0)
    ci = s.get("net_ci") or (None, None)
    return "%d trades | TP %.0f %% | net %+.1f %% [%s, %s]" % (
        s["n_ok"],
        100 * s["tp_rate"],
        100 * s["net_mean"],
        S.fmt(None if ci[0] is None else 100 * ci[0], "%+.1f"),
        S.fmt(None if ci[1] is None else 100 * ci[1], "%+.1f"),
    )


def main() -> None:
    rows = S.load()
    base = {
        r["mint"]: r for name in ("dataset_dev.jsonl.gz", "dataset_test.sealed.jsonl.gz") for r in S.pde.read_rows(name)
    }
    src = {m: b["f"].get("p0_source") for m, b in base.items()}
    series = S.pde.load_series()
    kept = json.load(open(os.path.join(S.STUDY, "derived", "S_kept.json")))["rules"]
    lines = [
        "# S4. Trading simulation (rules whose VALIDATION lower bound is above the base)",
        "",
        "Net mean per trade at $500, cost model of post_detection_edge, 95 %% cluster-bootstrap CI; the same "
        "exits on every alert as the reference. Cells with fewer than %d trades are not estimates." % MIN_TRADES,
        "",
    ]
    pos, est = [], 0
    for fam, d in kept.items():
        if not d["val_holds"]:
            continue
        v = d["var"]
        a = None
        for cand in S.atoms_for(v, S.pop(rows, "train", [v])):
            if S.text(cand) == d["rule"]:
                a = cand
        if a is None:
            continue
        for sp in ("train", "val"):
            allr = [r for r in rows if r["split"] == sp]
            sel = [r for r in allr if S.holds(r["f"], a)]
            lines += [
                "## %s, %s: `%s` (%d of %d alerts)" % (fam, sp.upper(), d["rule"], len(sel), len(allr)),
                "",
                "| delay | exit | rule | all alerts |",
                "|---:|---|---|---|",
            ]
            for dl in DELAYS:
                for tp, to in EXITS:
                    sr, sa = run(sel, series, src, dl, tp, to, 500), run(allr, series, src, dl, tp, to, 500)
                    lines.append("| %d s | TP %gx, %d min | %s | %s |" % (dl, tp, to // 60, cell(sr), cell(sa)))
                    if sp == "val" and sr.get("n_ok", 0) >= MIN_TRADES:
                        est += 1
                        if (sr.get("net_ci") or (None, None))[0] is not None and sr["net_ci"][0] > 0:
                            pos.append((fam, dl, tp, to, sr["net_mean"]))
            lines.append("")
            lines.append(
                "Sizes, 10 s delay, TP 2x within 15 min: "
                + "; ".join("$%d %s" % (sz, cell(run(sel, series, src, 10, 2.0, 900, sz))) for sz in (100, 500, 1000))
                + "."
            )
            lines.append("")
    lines += [
        "## Summary",
        "",
        "Estimable VALIDATION cells: %d; with a net mean whose CI is above 0: %d." % (est, len(pos)),
    ]
    for p in pos:
        lines.append(
            "- %s, delay %d s, TP %gx within %d min: net %+.1f %%." % (p[0], p[1], p[2], p[3] // 60, 100 * p[4])
        )
    S.write("S4_trading.md", lines)
    print("\n".join(lines[-(len(pos) + 3) :]))


if __name__ == "__main__":
    main()
