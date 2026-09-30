#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading simulation of analysis_plan.md, for the rules whose VALIDATION lower bound is above
the base (derived/E_classified.json), and for all alerts with the same exits.

The simulator and the cost model are post_detection_edge's (trade.simulate, trade.net_return,
the cost block of its LOCK.json): entry at the first read at or after the latency, take
profit filled at the level ("touch"), exit at the timeout otherwise, no stop; 1 % fee per
leg, 0.005 SOL per transaction, constant-product impact from the depth implied by the price.
A trade whose holding window is not observed is censored and counted, never scored.
Writes tables/E4_trading.md.
"""
from __future__ import annotations

import json
import os
from typing import Any

import ez_lib as L

import trade  # on sys.path through ez_lib

LOCK = json.load(open(os.path.join(L.ROOT, "post_detection_edge", "tables", "LOCK.json")))
COST = LOCK["cost_model"]
ENTRY_S = {"T0": 0, "D": 0, "P5": 5, "P10": 10, "P20": 20, "P30": 30, "P60": 60, "P120": 120, "P300": 300}
DELAYS = [0, 5, 10, 20, 30]
EXITS = [(tp, to) for tp in (1.5, 2.0, 3.0) for to in (300, 900, 1800, 3600)]
SIZES = [100, 500, 1000]
MIN_TRADES = 10


def run(sel: list[dict[str, Any]], series: dict[str, Any], src: dict[str, str], lat: float, tp: float, to: float,
        size: int, k: float) -> dict[str, Any]:
    res = []
    for r in sel:
        sim = trade.simulate(series.get(r["mint"]) or [], r["fine"], lat, tp, None, to, "touch")
        net = None
        if sim["status"] == "ok" and src.get(r["mint"]):
            p0 = r["p0"]
            net = trade.net_return(sim["gross"], sim["entry_mult"], p0, src[r["mint"]], r["t"], size, COST, k)
        res.append((r["cluster"], sim, net))
    return trade.summarise(res)


def cell(s: dict[str, Any]) -> str:
    if not s.get("n_ok"):
        return "n/a (0 of %d)" % s["n"]
    ci = s.get("net_ci") or (None, None)
    return "%d ok / %d | TP %.0f %% | gross %+.1f %% | net %+.1f %% [%s, %s]" % (
        s["n_ok"], s["n"], 100 * s["tp_rate"], 100 * s["gross_mean"], 100 * s.get("net_mean", float("nan")),
        L.fmt(None if ci[0] is None else 100 * ci[0], "%+.1f"), L.fmt(None if ci[1] is None else 100 * ci[1], "%+.1f"))


def main() -> None:
    rows = L.load()
    # P0 and its source (curve or pool): TRAIN rows are in the edge study's dev file, VALIDATION rows in
    # its test file (that study's TEST, run in 967f601, read here as it was in post_detection_forensics)
    base = {r["mint"]: r for name in ("dataset_dev.jsonl.gz", "dataset_test.sealed.jsonl.gz")
            for r in L.pde.read_rows(name)}
    for r in rows:
        r["p0"] = base[r["mint"]]["p0"] if r["mint"] in base else None
    src = {m: b["f"].get("p0_source") for m, b in base.items()}
    series = L.pde.load_series()
    cls = json.load(open(os.path.join(L.DERIVED, "E_classified.json")))
    kept = json.load(open(os.path.join(L.DERIVED, "E_kept.json")))
    lines = ["# E4. Trading simulation", "",
             "Rules whose VALIDATION lower bound is above the base, and all alerts with the same exits. Entry at the "
             "rule's cut-off plus the delay; take profit at the level or exit at the timeout, no stop. Net: $500, "
             "K x1, the cost model of post_detection_edge (fee %.0f %% per leg, %.3f SOL per transaction). Mean per "
             "trade, 95 %% cluster-bootstrap CI." % (100 * COST["fee_per_leg"], COST["fixed_sol_per_tx"]), ""]
    todo = [(fam, kept[fam]) for fam, c in cls.items() if c["val_holds"]]
    summary = []
    for fam, d in todo:
        cut = d["cut"]
        atoms = [tuple(a) for a in d["atoms"]]
        for split in ("train", "val"):
            allr = [r for r in rows if r["split"] == split and r["p0"]]
            sel = [r for r in allr if all(L.holds(r["f"][cut], a) for a in atoms)]
            lines += ["## %s, %s (%d selected of %d): `%s`" % (fam, split.upper(), len(sel), len(allr),
                                                               " AND ".join(L.text(a) for a in atoms)), "",
                      "| delay | exit | rule | all alerts |", "|---:|---|---|---|"]
            for dl in DELAYS:
                lat = ENTRY_S[cut] + dl
                for tp, to in EXITS:
                    s_rule = run(sel, series, src, lat, tp, to, 500, 1.0)
                    s_all = run(allr, series, src, lat, tp, to, 500, 1.0)
                    lines.append("| %d s | TP %gx, %d min | %s | %s |" % (dl, tp, to // 60, cell(s_rule), cell(s_all)))
                    summary.append((fam, split, dl, tp, to, s_rule.get("net_mean"),
                                    (s_rule.get("net_ci") or (None, None))[0], s_rule.get("n_ok", 0)))
            lines.append("")
            # sizes and depth, at the rule's own cut-off, 10 s delay, TP 2x within 15 min
            lat = ENTRY_S[cut] + 10
            lines.append("Sizes and depth, 10 s delay, TP 2x within 15 min: " + "; ".join(
                "$%d K x%g %s" % (sz, k, cell(run(sel, series, src, lat, 2.0, 900, sz, k)).split(" | ")[-1])
                for sz in SIZES for k in (1.0, 0.5)) + ".")
            lines.append("")
    val = [s for s in summary if s[1] == "val"]
    est = [s for s in val if s[7] >= MIN_TRADES]
    pos = [s for s in est if s[6] is not None and s[6] > 0]
    lines += ["## Summary", "",
              "VALIDATION cells (rule x delay x exit): %d; with at least %d simulated trades: %d; of those, net mean "
              "with a CI above 0: %d. A cell with fewer trades has no usable CI (a single trade gives a CI of zero "
              "width) and is not an estimate." % (len(val), MIN_TRADES, len(est), len(pos))]
    for fam in sorted({s[0] for s in val}):
        e = [s for s in est if s[0] == fam]
        lines.append("- %s: %d estimable cells, net mean from %s to %s." % (
            fam, len(e), L.fmt(min((100 * s[5] for s in e), default=None), "%+.1f %%"),
            L.fmt(max((100 * s[5] for s in e), default=None), "%+.1f %%")) if e else
            "- %s: no estimable cell (at most %d simulated trades)." % (fam, max(s[7] for s in val if s[0] == fam)))
    for s in pos:
        lines.append("- positive: %s, delay %d s, TP %gx within %d min: net %+.1f %%, CI low %+.1f %% (%d trades)." % (
            s[0], s[2], s[3], s[4] // 60, 100 * s[5], 100 * s[6], s[7]))
    L.write("E4_trading.md", lines)
    print("\n".join(lines[-(len(pos) + 3):]))


if __name__ == "__main__":
    main()
