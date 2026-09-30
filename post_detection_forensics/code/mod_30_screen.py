#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Level 1 and 2: every PRE_ENTRY feature alone, then simple pairs, TRAIN then
VALIDATION. Target 2x within 1 h, both entries.

Level 1  AUC of each feature in TRAIN with a normal-approximation p,
         Benjamini-Hochberg across all of them; then the same AUC in
         VALIDATION, unchanged. A feature "replicates" if it passes BH in TRAIN
         and keeps its direction in VALIDATION with p < 0.05 there.
Level 2  pairs among the 15 strongest TRAIN features: both split at their TRAIN
         median, the rate of the best of the four cells against the rest,
         Fisher test in TRAIN, BH across all pairs, and the same cell in
         VALIDATION.
Every test is counted and written with the table.
"""
from __future__ import annotations

import math
import os
import sys

import fml
from feat_30_build import FAMILY, STUDY, read_rows

sys.path.insert(0, os.path.join(os.path.dirname(STUDY), "post_detection_edge", "code"))
import pde

TARGET = "2x_1h"


def auc_p(a: float, n1: int, n0: int) -> float:
    se = math.sqrt((n1 + n0 + 1) / (12.0 * n1 * n0))
    return math.erfc(abs(a - 0.5) / se / math.sqrt(2))


def main() -> None:
    rows = read_rows("forensic_rows.jsonl.gz")
    out = ["# T2. Univariate and pairwise screen (TRAIN, then VALIDATION)", "",
           "Target: 2x within 1 h of the entry, complete-case. Regenerate: "
           "`python3 post_detection_forensics/code/mod_30_screen.py`.", ""]
    n_tests = 0
    for entry in ("A", "V"):
        key = "%s_%s" % (entry, TARGET)
        tr = [r for r in rows if r["split"] == "train" and r["y"].get(key) is not None and (entry == "A" or r["fine"])]
        va = [r for r in rows if r["split"] == "val" and r["y"].get(key) is not None and (entry == "A" or r["fine"])]
        res = []
        for f in sorted(FAMILY):
            t = [(r["f" + entry].get(f), r["y"][key]) for r in tr if r["f" + entry].get(f) is not None]
            v = [(r["f" + entry].get(f), r["y"][key]) for r in va if r["f" + entry].get(f) is not None]
            if len(t) < 50 or len({x for x, _ in t}) < 2:
                continue
            a = fml.roc_auc([x for x, _ in t], [y for _, y in t])
            n1 = sum(y for _, y in t)
            if a is None or not n1 or n1 == len(t):
                continue
            av = fml.roc_auc([x for x, _ in v], [y for _, y in v]) if v else None
            pv = auc_p(av, sum(y for _, y in v), len(v) - sum(y for _, y in v)) if av is not None else None
            res.append({"f": f, "fam": FAMILY[f], "n": len(t), "auc": a, "p": auc_p(a, n1, len(t) - n1),
                        "nv": len(v), "aucv": av, "pv": pv})
            n_tests += 1
        adj = pde.bh([r["p"] for r in res])
        for r, q in zip(res, adj):
            r["q"] = q
            r["rep"] = (q < 0.05 and r["aucv"] is not None and (r["auc"] - 0.5) * (r["aucv"] - 0.5) > 0
                        and r["pv"] is not None and r["pv"] < 0.05)
        res.sort(key=lambda r: -abs(r["auc"] - 0.5))
        out += ["## Entry %s: level 1 (%d features; TRAIN N %d, VALIDATION N %d)" % (entry, len(res), len(tr), len(va)),
                "", "Passing BH in TRAIN: %d. Replicating in VALIDATION: %d." % (
                    sum(1 for r in res if r["q"] < 0.05), sum(1 for r in res if r["rep"])), "",
                "| feature | family | N train | AUC train | q (BH) | N val | AUC val | p val | replicates |",
                "|---|---|---:|---:|---:|---:|---:|---:|---|"]
        for r in res[:40]:
            out.append("| %s | %s | %d | %.3f | %.4f | %d | %s | %s | %s |" % (
                r["f"], r["fam"], r["n"], r["auc"], r["q"], r["nv"],
                "n/a" if r["aucv"] is None else "%.3f" % r["aucv"], "n/a" if r["pv"] is None else "%.4f" % r["pv"],
                "yes" if r["rep"] else "no"))
        # level 2
        top = [r["f"] for r in res[:15]]
        pairs = []
        for i, a in enumerate(top):
            for b in top[i + 1:]:
                xs = [(r["f" + entry].get(a), r["f" + entry].get(b), r["y"][key]) for r in tr
                      if r["f" + entry].get(a) is not None and r["f" + entry].get(b) is not None]
                if len(xs) < 80:
                    continue
                ma = sorted(x for x, _, _ in xs)[len(xs) // 2]
                mb = sorted(x for _, x, _ in xs)[len(xs) // 2]
                best = None
                for sa in (0, 1):
                    for sb in (0, 1):
                        cell = [y for x1, x2, y in xs if (x1 > ma) == sa and (x2 > mb) == sb]
                        rest = [y for x1, x2, y in xs if not ((x1 > ma) == sa and (x2 > mb) == sb)]
                        if len(cell) < 20:
                            continue
                        rate = sum(cell) / len(cell)
                        if best is None or rate > best[0]:
                            best = (rate, sa, sb, sum(cell), len(cell), sum(rest), len(rest))
                if best is None:
                    continue
                rate, sa, sb, k, n, kr, nr = best
                p = pde.fisher_greater(k, n - k, kr, nr - kr) * 4       # best of 4 cells
                vv = [r["y"][key] for r in va if r["f" + entry].get(a) is not None and r["f" + entry].get(b) is not None
                      and (r["f" + entry][a] > ma) == sa and (r["f" + entry][b] > mb) == sb]
                pairs.append({"a": a, "b": b, "cell": "%s %s median, %s %s median" % (
                    a, ">" if sa else "<=", b, ">" if sb else "<="), "k": k, "n": n, "p": min(1.0, p),
                    "vk": sum(vv), "vn": len(vv)})
                n_tests += 1
        adj = pde.bh([p["p"] for p in pairs]) if pairs else []
        base_t = sum(r["y"][key] for r in tr) / len(tr)
        base_v = sum(r["y"][key] for r in va) / len(va) if va else float("nan")
        pairs = sorted(zip(pairs, adj), key=lambda z: z[1])
        out += ["", "## Entry %s: level 2, %d pairs among the 15 strongest TRAIN features" % (entry, len(pairs)), "",
                "Base rate TRAIN %.1f %%, VALIDATION %.1f %%. Passing BH in TRAIN: %d." % (
                    100 * base_t, 100 * base_v, sum(1 for _, q in pairs if q < 0.05)), "",
                "| best cell | TRAIN | q (BH) | VALIDATION |", "|---|---|---:|---|"]
        for p, q in pairs[:15]:
            out.append("| %s | %s | %.4f | %s |" % (p["cell"], pde.rate_cell(p["k"], p["n"]), q,
                                                   pde.rate_cell(p["vk"], p["vn"])))
        out.append("")
    out.append("Tests run by this script: %d." % n_tests)
    with open(os.path.join(STUDY, "tables", "T2_screen.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
