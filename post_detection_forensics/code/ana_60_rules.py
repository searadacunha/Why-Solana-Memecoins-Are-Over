#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 6 of analysis_plan.md: simple rules, TRAIN thresholds, VALIDATION check.

Conditions: every SAFE feature against its TRAIN deciles (<= and >). Rules: 1
to 3 conditions; pairs exhaustive, triples by beam over the 100 best pairs.
TRAIN support >= 40, TRAIN score = Wilson lower bound; duplicates on identical
TRAIN rows collapsed. The 50 best go to VALIDATION; the kept rule has the best
VALIDATION Wilson lower bound with VALIDATION N >= 40. Every rule at 60 / 70 /
80 % in TRAIN is counted with its pooled VALIDATION rate. The number of rules
evaluated is written. Output: tables/D6_rules.md, derived/D6_kept_rule.json.
"""
from __future__ import annotations

import json
import os
from typing import Any

import ana_lib as L

MIN_SUPPORT, MIN_VAL, BEAM, TOP = 40, 40, 100, 50


def main() -> None:
    rows = L.load()
    tr, va = L.xy(rows, "train"), L.xy(rows, "val")
    ybits = sum(1 << i for i, (_, _, y) in enumerate(tr) if y)
    atoms: list[tuple[str, str, float]] = []
    for f in L.SAFE:
        xs = [x.get(f) for _, x, _ in tr if x.get(f) is not None]
        if len(xs) < 50 or len(set(xs)) < 2:
            continue
        for t in sorted({L.q(xs, k / 10) for k in range(1, 10)}):
            atoms += [(f, "<=", t), (f, ">", t)]

    def holds(x: dict[str, Any], a: tuple[str, str, float]) -> bool:
        v = x.get(a[0])
        return v is not None and (v <= a[2] if a[1] == "<=" else v > a[2])
    am = [sum(1 << i for i, (_, x, _) in enumerate(tr) if holds(x, a)) for a in atoms]
    found: dict[int, dict[str, Any]] = {}
    n_eval = 0

    def consider(idx: tuple[int, ...], m: int) -> float:
        nonlocal n_eval
        n_eval += 1
        n = m.bit_count()
        if n < MIN_SUPPORT:
            return -1.0
        k = (m & ybits).bit_count()
        lb = L.pde.wilson(k, n)[0] or 0.0
        if m not in found or len(idx) < len(found[m]["idx"]):
            found[m] = {"idx": idx, "n": n, "k": k, "lb": lb}
        return lb
    for i in range(len(atoms)):
        consider((i,), am[i])
    pairs = []
    for i in range(len(atoms)):
        for j in range(i + 1, len(atoms)):
            if atoms[i][0] != atoms[j][0]:
                s = consider((i, j), am[i] & am[j])
                if s >= 0:
                    pairs.append((s, (i, j)))
    pairs.sort(reverse=True)
    for _, (i, j) in pairs[:BEAM]:
        for k in range(len(atoms)):
            if atoms[k][0] not in (atoms[i][0], atoms[j][0]):
                consider(tuple(sorted((i, j, k))), am[i] & am[j] & am[k])
    rules = sorted(found.values(), key=lambda d: (-d["lb"], -d["n"]))

    def val_of(d: dict[str, Any]) -> tuple[int, int]:
        sel = [y for _, x, y in va if all(holds(x, atoms[i]) for i in d["idx"])]
        return sum(sel), len(sel)

    def text(d: dict[str, Any]) -> str:
        return " AND ".join("%s %s %.4g" % atoms[i] for i in d["idx"])
    base_t = sum(y for _, _, y in tr) / len(tr)
    base_v = sum(y for _, _, y in va) / len(va)
    scored = []
    for d in rules[:TOP]:
        k, n = val_of(d)
        scored.append(((L.pde.wilson(k, n)[0] or 0.0) if n >= MIN_VAL else -1.0, k, n, d))
    scored.sort(key=lambda z: -z[0])
    lines = ["# D6. Simple rules (primary label)", "",
             "Atoms %d, rules evaluated %d, distinct rules with TRAIN support >= %d: %d. Base: TRAIN %.1f %%, "
             "VALIDATION %.1f %%." % (len(atoms), n_eval, MIN_SUPPORT, len(rules), 100 * base_t, 100 * base_v), "",
             "## Rules by TRAIN hit rate, and what VALIDATION gives them", "",
             "| TRAIN rate | rules | largest N | pooled TRAIN | pooled VALIDATION (alert-rule pairs) |",
             "|---|---:|---:|---|---|"]
    for lo, hi in ((0.8, 1.01), (0.7, 0.8), (0.6, 0.7)):
        grp = [d for d in rules if lo <= d["k"] / d["n"] < hi]
        vk = vn = 0
        for d in grp:
            k, n = val_of(d)
            vk, vn = vk + k, vn + n
        lines.append("| %d-%d %% | %d | %s | %s | %s |" % (
            100 * lo, min(100, 100 * hi), len(grp), max((d["n"] for d in grp), default="-"),
            L.rate(sum(d["k"] for d in grp), sum(d["n"] for d in grp)) if grp else "-", L.rate(vk, vn) if vn else "-"))
    lines += ["", "## The %d best TRAIN rules, re-measured in VALIDATION" % TOP, "",
              "| rule | TRAIN | VALIDATION | VAL Wilson lower bound |", "|---|---|---|---:|"]
    for s, k, n, d in scored[:25]:
        lines.append("| %s | %s | %s | %s |" % (text(d), L.rate(d["k"], d["n"]), L.rate(k, n),
                                                "%.3f" % s if s >= 0 else "VAL N < %d" % MIN_VAL))
    eligible = [z for z in scored if z[2] >= MIN_VAL]
    if eligible:
        s, k, n, d = eligible[0]
        kept: dict[str, Any] = {"rule": [list(atoms[i]) for i in d["idx"]], "text": text(d),
                                "train": [d["k"], d["n"]], "val": [k, n], "base_train": base_t, "base_val": base_v}
        lines += ["", "**Kept (best VALIDATION lower bound, VALIDATION N >= %d): `%s`**: TRAIN %s, VALIDATION %s "
                  "(base %.1f %%). VALIDATION chose it among %d rules, so its VALIDATION rate is optimistic." % (
                      MIN_VAL, text(d), L.rate(d["k"], d["n"]), L.rate(k, n), 100 * base_v, len(scored))]
    else:
        kept = {"rule": None, "text": None, "base_train": base_t, "base_val": base_v}
        lines += ["", "**No rule kept**: none of the %d best TRAIN rules has VALIDATION N >= %d." % (TOP, MIN_VAL)]
    L.write("D6_rules.md", lines)
    with open(os.path.join(L.FB.DERIVED, "D6_kept_rule.json"), "w") as fh:
        json.dump(kept, fh, indent=1)
    print("\n".join(lines[:12] + lines[-2:]))


if __name__ == "__main__":
    main()
