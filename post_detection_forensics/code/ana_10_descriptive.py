#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1 of analysis_plan.md: every SAFE feature, winners against losers.

Winners = confirmed 2x within 15 min (A_conf_2x_15m = 1), losers = 0, cut-off
A. TRAIN: mean, median, q10 / q25 / q75 / q90 of each group, absolute and
relative difference of the medians with a cluster-bootstrap CI, Mann-Whitney p
(from the AUC), AUC as effect size, Benjamini-Hochberg across every feature.
VALIDATION: the same AUC, p and difference, unchanged. A feature "replicates"
when it passes BH in TRAIN and keeps its direction in VALIDATION with p < 0.05.
"""
from __future__ import annotations

import json
import os

import ana_lib as L
import fml


def stats(pairs: list[tuple[float, int]]) -> dict:
    w = [x for x, y in pairs if y == 1]
    lo = [x for x, y in pairs if y == 0]
    a = fml.roc_auc([x for x, _ in pairs], [y for _, y in pairs])
    return {"n1": len(w), "n0": len(lo), "auc": a, "p": L.auc_p(a, len(w), len(lo)) if a is not None else None,
            "w": [sum(w) / len(w) if w else None] + [L.q(w, p) for p in (0.5, 0.1, 0.25, 0.75, 0.9)],
            "l": [sum(lo) / len(lo) if lo else None] + [L.q(lo, p) for p in (0.5, 0.1, 0.25, 0.75, 0.9)]}


def main() -> None:
    rows = L.load()
    res = []
    for f in L.SAFE:
        out = {"f": f, "fam": L.FAM[f]}
        for sp in ("train", "val"):
            pts = [(x.get(f), y) for r, x, y in L.xy(rows, sp) if x.get(f) is not None]
            if len(pts) < 50 or not 0 < sum(y for _, y in pts) < len(pts) or len({x for x, _ in pts}) < 2:
                out[sp] = None
                continue
            st = stats(pts)
            clus = [(r["cluster"], (x.get(f), y)) for r, x, y in L.xy(rows, sp) if x.get(f) is not None]
            st["ci"] = L.boot(clus, L.med_diff)
            out[sp] = st
        if out.get("train"):
            res.append(out)
    adj = L.pde.bh([r["train"]["p"] for r in res])
    for r, qv in zip(res, adj):
        r["q"] = qv
        v = r.get("val")
        r["rep"] = bool(qv < 0.05 and v and v["p"] is not None and v["p"] < 0.05
                        and (r["train"]["auc"] - 0.5) * (v["auc"] - 0.5) > 0)
    res.sort(key=lambda r: -abs(r["train"]["auc"] - 0.5))

    def f3(x: object) -> str:
        return "n/a" if x is None else ("%.3g" % x)
    lines = ["# D1. Winners vs losers, every SAFE feature (primary label, cut-off A)", "",
             "Winners: confirmed 2x within 15 min of P0. TRAIN is exploration; VALIDATION re-measures. Median "
             "difference = winners minus losers, 95 %% cluster-bootstrap CI. Tests: %d features, BH in TRAIN."
             % len(res),
             "", "Passing BH in TRAIN: %d. Replicating in VALIDATION: %d." % (
                 sum(1 for r in res if r["q"] < 0.05), sum(1 for r in res if r["rep"])), "",
             "| feature | family | TRAIN n win / lose | mean win / lose | median win / lose | q10-q90 win | "
             "q10-q90 lose | median diff [CI] | rel. diff | AUC | q (BH) | VAL AUC | VAL p | VAL median diff [CI] "
             "| replicates |",
             "|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|"]
    for r in res:
        t, v = r["train"], r.get("val")
        md = (t["w"][1] or 0) - (t["l"][1] or 0) if t["w"][1] is not None and t["l"][1] is not None else None
        rel = md / abs(t["l"][1]) if md is not None and t["l"][1] else None
        lines.append("| %s | %s | %d / %d | %s / %s | %s / %s | %s-%s | %s-%s | %s [%s, %s] | %s | %.3f | %.4f "
                     "| %s | %s | %s | %s |" % (
                         r["f"], r["fam"], t["n1"], t["n0"], f3(t["w"][0]), f3(t["l"][0]), f3(t["w"][1]),
                         f3(t["l"][1]), f3(t["w"][2]), f3(t["w"][5]), f3(t["l"][2]), f3(t["l"][5]), f3(md),
                         f3(t["ci"][0]), f3(t["ci"][1]), "n/a" if rel is None else "%+.0f %%" % (100 * rel),
                         t["auc"], r["q"], "n/a" if not v else "%.3f" % v["auc"],
                         "n/a" if not v else "%.4f" % v["p"],
                         "n/a" if not v else "%s [%s, %s]" % (f3((v["w"][1] or 0) - (v["l"][1] or 0)),
                                                              f3(v["ci"][0]), f3(v["ci"][1])),
                         "yes" if r["rep"] else "no"))
    L.write("D1_descriptive.md", lines)
    with open(os.path.join(L.FB.DERIVED, "D1_summary.json"), "w") as fh:
        json.dump({"bh_train": sorted(r["f"] for r in res if r["q"] < 0.05),
                   "replicates": sorted(r["f"] for r in res if r["rep"])}, fh, indent=1)
    print("\n".join(lines[:6]))


if __name__ == "__main__":
    main()
