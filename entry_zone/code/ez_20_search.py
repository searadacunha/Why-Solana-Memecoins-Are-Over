#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The rule search of analysis_plan.md, TRAIN only, then VALIDATION once.

1. Singles, per family: every atom of every variable of the family at every cut-off;
   metric = Wilson 95 % lower bound of the primary rate minus the TRAIN base at that
   cut-off, TRAIN N >= 40. Best per family; 200 permutations of the TRAIN labels within
   each cut-off rerun the search for the family's p.
2. Combinations of one cut-off, any family, bound atoms only (an interval is a pair of
   bounds): pairs exhaustive, with the same 200 permutations; triples and quadruples by a
   beam of the 200 best, observed only.
3. VALIDATION, once, for each family's best rule and the best combination; the 20 best
   TRAIN rules of each family are listed with their VALIDATION rate, never used.
Also the descriptive bins of market cap and premium (TRAIN deciles and 10k USD
tranches), with the rates of both splits.

Writes tables/E0_bins.md, tables/E1_singles.md, tables/E2_combinations.md and
derived/E_kept.json.
"""
from __future__ import annotations

import json
import os
import random
from multiprocessing import Pool
from typing import Any

import ez_lib as L

N_PERM, BEAM = 200, 200


def perm_ybits(tr: list[dict[str, Any]], cut: str, p: int) -> int:
    ys = [r["y"][cut][L.PRIMARY] for r in tr]
    rng = random.Random(L.SEED + 1000 * L.CUTS.index(cut) + p)
    rng.shuffle(ys)
    return sum(1 << i for i, y in enumerate(ys) if y == 1)


def cut_job(cut: str) -> dict[str, Any]:
    """Everything that is computed per cut-off: single atoms by family, pairs, beam, and their nulls."""
    rows = L.load()
    tr = L.observed(rows, cut, "train")
    base = sum(r["y"][cut][L.PRIMARY] for r in tr) / len(tr)
    y = L.ybits(tr, cut)
    yp = [perm_ybits(tr, cut, p) for p in range(N_PERM)]
    out: dict[str, Any] = {"cut": cut, "base": base, "n": len(tr), "singles": {}, "null_singles": {}}
    # singles
    for fam, vs in L.FAMILIES.items():
        res, null = [], [-1.0] * N_PERM
        for v in vs:
            for a in L.atoms_for(cut, v, tr):
                m = L.mask(tr, a)
                n = m.bit_count()
                if n < L.MIN_N:
                    continue
                k = (m & y).bit_count()
                res.append((L.metric(k, n, base), n, k, a))
                for p in range(N_PERM):
                    kp = (m & yp[p]).bit_count()
                    if kp > (null[p] + base) * n:
                        null[p] = max(null[p], L.metric(kp, n, base))
        res.sort(key=lambda z: (-z[0], -z[1]))
        out["singles"][fam] = res[:20]
        out["null_singles"][fam] = null
    # combinations: bound atoms of every family
    atoms = [a for v in L.FAM_OF for a in L.atoms_for(cut, v, tr, intervals=False) if a[2] != "zone"]
    masks = [L.mask(tr, a) for a in atoms]
    keep = [i for i, m in enumerate(masks) if m.bit_count() >= L.MIN_N]
    pairs, null_pairs = [], [-1.0] * N_PERM
    for ii, i in enumerate(keep):
        mi = masks[i]
        for j in keep[ii + 1:]:
            m = mi & masks[j]
            n = m.bit_count()
            if n < L.MIN_N:
                continue
            k = (m & y).bit_count()
            s = L.metric(k, n, base)
            pairs.append((s, n, k, (i, j)))
            for p in range(N_PERM):
                kp = (m & yp[p]).bit_count()
                if kp > (null_pairs[p] + base) * n:
                    null_pairs[p] = max(null_pairs[p], L.metric(kp, n, base))
    pairs.sort(key=lambda z: (-z[0], -z[1]))
    best = [(s, n, k, idx) for s, n, k, idx in pairs[:BEAM]]
    found = list(pairs[:BEAM])
    for size in (3, 4):
        nxt: dict[tuple[int, ...], tuple] = {}
        for _, _, _, idx in best:
            m0 = 0
            for i in idx:
                m0 = masks[i] if m0 == 0 else m0 & masks[i]
            for j in keep:
                if j in idx:
                    continue
                key = tuple(sorted(idx + (j,)))
                if key in nxt:
                    continue
                m = m0 & masks[j]
                n = m.bit_count()
                if n < L.MIN_N:
                    continue
                k = (m & y).bit_count()
                nxt[key] = (L.metric(k, n, base), n, k, key)
        best = sorted(nxt.values(), key=lambda z: (-z[0], -z[1]))[:BEAM]
        found += best
    found.sort(key=lambda z: (-z[0], -z[1]))
    out["combos"] = [(s, n, k, [atoms[i] for i in idx]) for s, n, k, idx in found[:20]]
    out["n_pairs"] = len(pairs)
    out["n_atoms_combo"] = len(keep)
    out["null_pairs"] = null_pairs
    return out


def evaluate(rows: list[dict[str, Any]], cut: str, atoms: list[tuple], split: str) -> dict[str, Any]:
    allr = L.observed(rows, cut, split)
    sel = [r for r in allr if all(L.holds(r["f"][cut], a) for a in atoms)]
    d = L.describe(sel, allr, cut)
    d["base"] = d["base_2"]
    d["ci"] = L.pde.wilson(d["k_2"], d["n"]) if d["n"] else (None, None)
    d["lift_ci"] = L.boot_lift(sel, allr, cut, lambda r: all(L.holds(r["f"][cut], a) for a in atoms))
    if len(atoms) == 1 and atoms[0][2] in ("le", "gt", "lt", "ge"):
        pts = [(r["f"][cut].get(atoms[0][1]), r["y"][cut][L.PRIMARY]) for r in allr
               if r["f"][cut].get(atoms[0][1]) is not None]
        sign = -1 if atoms[0][2] in ("le", "lt") else 1
        d["auc"] = L.auc([sign * x for x, _ in pts], [yy for _, yy in pts]) if pts else None
    return d


def bins(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["# E0. Market cap and premium bins (bins fixed on TRAIN; VALIDATION shown for every bin, never used)",
             "", "Rates of confirmed 1.5x / 2x / 3x within 15 min of the entry at that cut-off, median time to "
             "the 2x, median drawdown before it.", ""]
    for var, widths in (("mc_usd", [10000]), ("premium", [])):
        for cut in L.CUTS[1:]:
            tr, va = L.observed(rows, cut, "train"), L.observed(rows, cut, "val")
            xs = [r["f"][cut].get(var) for r in tr if r["f"][cut].get(var) is not None]
            if not xs:
                continue
            edges = [L.q(xs, k / 10) for k in range(1, 10)]
            specs = [("TRAIN decile %d" % (i + 1), lo, hi) for i, (lo, hi) in
                     enumerate(zip([-1e30] + edges, edges + [1e30]))]
            for w in widths:
                lo_, hi_ = L.q(xs, 0.01), L.q(xs, 0.99)
                e = int(lo_ // w) * w
                while e < hi_:
                    specs.append(("%dk-%dk" % (e // 1000, (e + w) // 1000), e, e + w))
                    e += w
            lines += ["## %s at %s" % (var, cut), "", "| bin | range | TRAIN N | TRAIN 1.5x / 2x / 3x | VAL N | "
                      "VAL 1.5x / 2x / 3x | VAL t2x (s) | VAL drawdown |", "|---|---|---:|---|---:|---|---:|---:|"]
            for name, lo, hi in specs:
                def inb(r: dict[str, Any]) -> bool:
                    x = r["f"][cut].get(var)
                    return x is not None and lo < x <= hi if "decile" in name else x is not None and lo <= x < hi
                st, sv = [r for r in tr if inb(r)], [r for r in va if inb(r)]
                dt, dv = L.describe(st, tr, cut), L.describe(sv, va, cut)

                def three(d: dict[str, Any]) -> str:
                    n = d["n"]
                    return " / ".join("%.0f %%" % (100 * d["k_" + k] / n) if n else "-" for k in ("1.5", "2", "3"))
                lines.append("| %s | %s to %s | %d | %s | %d | %s | %s | %s |" % (
                    name, L.fmt(lo if lo > -1e29 else None, "%.4g"), L.fmt(hi if hi < 1e29 else None, "%.4g"),
                    dt["n"], three(dt), dv["n"], three(dv), L.fmt(dv["t_2x_median"], "%.0f"),
                    L.fmt(dv["drawdown_median"], "%+.2f")))
            lines.append("")
    return lines


def main() -> None:
    rows = L.load()
    L.write("E0_bins.md", bins(rows))
    with Pool(min(len(L.CUTS), os.cpu_count() or 2)) as pool:
        res = pool.map(cut_job, L.CUTS)
    kept: dict[str, Any] = {}
    lines = ["# E1. Single conditions, by family (TRAIN choice, VALIDATION once)", "",
             "Metric: Wilson 95 %% lower bound of the TRAIN rate minus the TRAIN base at the cut-off, TRAIN N >= "
             "%d. p: share of %d label permutations (within each cut-off) whose best rule of the family reaches the "
             "observed metric." % (L.MIN_N, N_PERM), "",
             "TRAIN bases by cut-off: %s." % ", ".join("%s %.1f %% (N %d)" % (o["cut"], 100 * o["base"], o["n"])
                                                       for o in res), ""]
    for fam in L.FAMILIES:
        cand = [(s, n, k, a, o["cut"]) for o in res for s, n, k, a in o["singles"][fam]]
        cand.sort(key=lambda z: (-z[0], -z[1]))
        null = [max(o["null_singles"][fam][p] for o in res) for p in range(N_PERM)]
        if not cand:
            continue
        s, n, k, a, cut = cand[0]
        p = sum(1 for x in null if x >= s) / N_PERM
        tr_d, va_d = evaluate(rows, cut, [a], "train"), evaluate(rows, cut, [a], "val")
        kept[fam] = {"cut": cut, "atoms": [list(a)], "metric": s, "p": p, "train": tr_d, "val": va_d}
        lines += ["## %s" % fam, "", "Best: `%s`, TRAIN metric %+.3f, permutation p %.3f (null best: median %+.3f, "
                  "95th %+.3f)." % (L.text(a), s, p, sorted(null)[N_PERM // 2], sorted(null)[int(0.95 * N_PERM)]), "",
                  "| rule | cut | TRAIN 2x [CI] | TRAIN 1.5x / 3x | VAL 2x [CI] | VAL base | VAL 1.5x / 3x | VAL t2x / "
                  "drawdown | VAL lift CI | VAL AUC |", "|---|---|---|---|---|---:|---|---|---|---:|"]
        for i, (s2, n2, k2, a2, c2) in enumerate(cand[:20]):
            t2, v2 = (tr_d, va_d) if i == 0 else (evaluate(rows, c2, [a2], "train"), evaluate(rows, c2, [a2], "val"))
            lines.append("| %s%s | %s | %s | %s / %s | %s | %.1f %% | %s / %s | %s s / %s | [%s, %s] | %s |" % (
                "**" if i == 0 else "", L.text(a2).split("] ", 1)[1], c2, L.rate(t2["k_2"], t2["n"]),
                L.rate(t2["k_1.5"], t2["n"]).split(" [")[0], L.rate(t2["k_3"], t2["n"]).split(" [")[0],
                L.rate(v2["k_2"], v2["n"]), 100 * (v2["base"] or 0), L.rate(v2["k_1.5"], v2["n"]).split(" [")[0],
                L.rate(v2["k_3"], v2["n"]).split(" [")[0], L.fmt(v2["t_2x_median"], "%.0f"),
                L.fmt(v2["drawdown_median"], "%+.2f"), L.fmt(v2["lift_ci"][0], "%+.3f"),
                L.fmt(v2["lift_ci"][1], "%+.3f"), L.fmt(v2.get("auc"))))
        lines.append("")
    L.write("E1_singles.md", lines)
    # combinations
    cand = [(s, n, k, atoms, o["cut"]) for o in res for s, n, k, atoms in o["combos"]]
    cand.sort(key=lambda z: (-z[0], -z[1]))
    null = [max(o["null_pairs"][p] for o in res) for p in range(N_PERM)]
    s, n, k, atoms, cut = cand[0]
    p = sum(1 for x in null if x >= s) / N_PERM
    tr_d, va_d = evaluate(rows, cut, atoms, "train"), evaluate(rows, cut, atoms, "val")
    kept["combination"] = {"cut": cut, "atoms": [list(a) for a in atoms], "metric": s, "p": p, "train": tr_d,
                           "val": va_d}
    lines = ["# E2. Combinations of 2 to 4 conditions (one cut-off, any family; TRAIN choice, VALIDATION once)", "",
             "Atoms per cut-off (bounds, N >= %d): %s. Pairs evaluated: %s. Triples and quadruples: beam of %d." % (
                 L.MIN_N, ", ".join("%s %d" % (o["cut"], o["n_atoms_combo"]) for o in res),
                 ", ".join("%s %d" % (o["cut"], o["n_pairs"]) for o in res), BEAM),
             "", "Best: `%s`, TRAIN metric %+.3f, permutation p of the pairs %.3f (null best: median %+.3f, 95th %+.3f;"
             " a triple or quadruple comes from a larger search and its true p is higher)." % (
                 " AND ".join(L.text(a) for a in atoms), s, p, sorted(null)[N_PERM // 2],
                 sorted(null)[int(0.95 * N_PERM)]), "",
             "| rule | cut | TRAIN 2x [CI] | VAL 2x [CI] | VAL base | VAL 1.5x / 3x | VAL t2x / drawdown "
             "| VAL lift CI |",
             "|---|---|---|---|---:|---|---|---|"]
    for i, (s2, n2, k2, a2, c2) in enumerate(cand[:20]):
        t2, v2 = (tr_d, va_d) if i == 0 else (evaluate(rows, c2, a2, "train"), evaluate(rows, c2, a2, "val"))
        lines.append("| %s%s | %s | %s | %s | %.1f %% | %s / %s | %s s / %s | [%s, %s] |" % (
            "**" if i == 0 else "", " AND ".join(L.text(a).split("] ", 1)[1] for a in a2), c2,
            L.rate(t2["k_2"], t2["n"]), L.rate(v2["k_2"], v2["n"]), 100 * (v2["base"] or 0),
            L.rate(v2["k_1.5"], v2["n"]).split(" [")[0], L.rate(v2["k_3"], v2["n"]).split(" [")[0],
            L.fmt(v2["t_2x_median"], "%.0f"), L.fmt(v2["drawdown_median"], "%+.2f"),
            L.fmt(v2["lift_ci"][0], "%+.3f"), L.fmt(v2["lift_ci"][1], "%+.3f")))
    L.write("E2_combinations.md", lines)
    with open(os.path.join(L.DERIVED, "E_kept.json"), "w") as fh:
        json.dump(kept, fh, indent=1, default=str)
    for fam, d in kept.items():
        print("%-18s %-5s p=%.3f TRAIN %s VAL %s base %.1f %%  %s" % (
            fam, d["cut"], d["p"], L.rate(d["train"]["k_2"], d["train"]["n"]), L.rate(d["val"]["k_2"], d["val"]["n"]),
            100 * d["val"]["base"], " AND ".join(L.text(tuple(a)) for a in d["atoms"])))


if __name__ == "__main__":
    main()
