#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2 of analysis_plan.md: combined structures, every pair of SAFE features.

Both features are split at their TRAIN median. In TRAIN the best of the four
cells (at least 30 alerts) is set against the rest with a one-sided Fisher p,
multiplied by 4 for the choice of cell; Benjamini-Hochberg across every pair.
The very same cell is then re-measured in VALIDATION. The pairs the owner named
are flagged and reported whatever they give.
"""
from __future__ import annotations

import ana_lib as L

NAMED = [("b_core_n", "b_hhi"), ("b_core_n", "f_hub_funded_share"),
         ("w_creator_log_age_h", "g_creator_shares_core_funder"), ("g_core_common_ratio", "b_core_tx_n"),
         ("b_hhi", "b_ticket_median"), ("f_indep_actors_strict", "b_ticket_cv"),
         ("w_early_log_prior_n", "f_funder_top1"), ("m_core_exit_share", "b_top1"),
         ("p_entry_over_operator", "f_funder_top1")]


def main() -> None:
    rows = L.load()
    tr, va = L.xy(rows, "train"), L.xy(rows, "val")
    med = {f: L.q([x.get(f) for _, x, _ in tr], 0.5) for f in L.SAFE}
    feats = [f for f in L.SAFE if med[f] is not None
             and len({x.get(f) for _, x, _ in tr if x.get(f) is not None}) > 1]
    named = {tuple(sorted(p)) for p in NAMED}
    base_t = sum(y for _, _, y in tr) / len(tr)
    base_v = sum(y for _, _, y in va) / len(va)
    res = []
    for i, a in enumerate(feats):
        for b in feats[i + 1:]:
            cells: dict[tuple[bool, bool], list[int]] = {}
            for _, x, y in tr:
                if x.get(a) is None or x.get(b) is None:
                    continue
                cells.setdefault((x[a] > med[a], x[b] > med[b]), []).append(y)
            tot_k = sum(sum(v) for v in cells.values())
            tot_n = sum(len(v) for v in cells.values())
            best = None
            for c, ys in cells.items():
                if len(ys) < 30:
                    continue
                if best is None or sum(ys) / len(ys) > best[1]:
                    best = (c, sum(ys) / len(ys), sum(ys), len(ys))
            if best is None:
                continue
            c, _, k, n = best
            p = min(1.0, 4 * L.pde.fisher_greater(k, n - k, tot_k - k, (tot_n - n) - (tot_k - k)))
            vy = [y for _, x, y in va if x.get(a) is not None and x.get(b) is not None
                  and (x[a] > med[a], x[b] > med[b]) == c]
            res.append({"a": a, "b": b, "cell": c, "k": k, "n": n, "p": p, "vk": sum(vy), "vn": len(vy),
                        "named": tuple(sorted((a, b))) in named})
    adj = L.pde.bh([r["p"] for r in res])
    for r, qv in zip(res, adj):
        r["q"] = qv
    res.sort(key=lambda r: r["q"])

    def cell(r: dict) -> str:
        return "%s %s med, %s %s med" % (r["a"], ">" if r["cell"][0] else "<=", r["b"], ">" if r["cell"][1] else "<=")
    sig = [r for r in res if r["q"] < 0.05]
    rep = [r for r in sig if r["vn"] >= 30 and L.pde.wilson(r["vk"], r["vn"])[0] > base_v]
    lines = ["# D2. Pairs of features, systematic screen (primary label)", "",
             "%d features, %d pairs tested. Base: TRAIN %.1f %%, VALIDATION %.1f %%. Passing BH (q < 0.05) in TRAIN: "
             "%d. Of those, VALIDATION rate with a Wilson lower bound above the VALIDATION base (N >= 30): %d." % (
                 len(feats), len(res), 100 * base_t, 100 * base_v, len(sig), len(rep)), "",
             "## Best TRAIN pairs (by q)", "", "| best cell | TRAIN | q (BH) | VALIDATION |", "|---|---|---:|---|"]
    for r in res[:30]:
        lines.append("| %s | %s | %.2g | %s |" % (cell(r), L.rate(r["k"], r["n"]), r["q"], L.rate(r["vk"], r["vn"])))
    lines += ["", "## The pairs named in the plan", "", "| pair (best cell) | TRAIN | q (BH) | VALIDATION |",
              "|---|---|---:|---|"]
    for r in res:
        if r["named"]:
            lines.append("| %s | %s | %.2g | %s |" % (cell(r), L.rate(r["k"], r["n"]), r["q"],
                                                   L.rate(r["vk"], r["vn"])))
    L.write("D2_pairs.md", lines)
    print("\n".join(lines[:4]))


if __name__ == "__main__":
    main()
