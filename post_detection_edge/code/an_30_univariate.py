#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Univariate screen: every feature known at T_DETECT, alone, in TRAIN; then the
same statistic, unchanged, in VALIDATION.

Primary target: TARGET_2X at 1 h, entry at P0, complete-case (observed windows).
Per feature:
  continuous  AUC (Mann-Whitney), normal-approximation p, and a label
              permutation p (2 000 draws); quartiles with cut points taken in
              TRAIN only; the best TRAIN quartile against the rest, with a
              permutation p for "best of four bins" (the maximum, since that is
              what was selected).
  categorical rate per level, best level against the rest, same permutation.
Then the VALIDATION rate of the very bins TRAIN picked.

Secondary grid: AUC of every feature on every (threshold, horizon) cell with at
least 5 TRAIN positives, Benjamini-Hochberg across the whole grid, and the
VALIDATION AUC of the same cells. The number of tests is counted and written.

TEST is not read.
"""
from __future__ import annotations

import json
import os
import random
from typing import Any, Optional

import pde

CONTINUOUS = [
    "n_snipers", "snipe_sol", "supply_part", "ticket_mean", "ticket_median", "ticket_std", "ticket_cv", "core_cv",
    "ticket_min", "ticket_max", "max_share", "hhi", "ticket_range_rel", "round_share", "sol_per_sniper",
    "n_buyers", "extra_buyers", "ntx", "nko", "fail_ratio", "amorce", "paquet_max",
    "log10_p0", "log10_mc_usd", "log10_vwap_op", "entry_over_operator", "age_alert_s",
    "n_alerts_prev_60m", "n_candidates_prev_60m", "creator_prev", "sniper_reuse_max", "config_prev",
]
CATEGORICAL = ["actor", "complete_at_block", "p0_source", "hour_bin", "dow"]
N_PERM = 2000
SEED = 20260929


def value(r: dict[str, Any], f: str) -> Any:
    if f == "hour_bin":
        return "%02d-%02dh" % (r["f"]["hour_utc"] // 4 * 4, r["f"]["hour_utc"] // 4 * 4 + 4)
    return r["f"].get(f)


def label(r: dict[str, Any], k: float, h: int, lat: int = 0) -> Optional[int]:
    t = r["targets"]["L%d_%s" % (lat, pde.H_LABEL[h])]
    if t["status"] != "observed":
        return None
    return 1 if t["mfe"] >= k else 0


def cuts(xs: list[float]) -> list[float]:
    return [pde.quantile(xs, q) for q in (0.25, 0.5, 0.75)]


def binof(x: float, c: list[float]) -> int:
    return sum(1 for v in c if x > v)


def best_bin_stat(bins: list[Any], y: list[int], levels: list[Any]) -> tuple[Any, float]:
    best, br = None, -1.0
    for lv in levels:
        idx = [i for i, b in enumerate(bins) if b == lv]
        if len(idx) < 10:
            continue
        r = sum(y[i] for i in idx) / len(idx)
        if r > br:
            best, br = lv, r
    return best, br


def main() -> None:
    dev = pde.read_rows("dataset_dev.jsonl.gz")
    train = [r for r in dev if r["split"] == "train"]
    val = [r for r in dev if r["split"] == "val"]
    k0, h0 = pde.PRIMARY
    rng = random.Random(SEED)
    n_tests = 0
    lines = ["# T2. Univariate screen, TRAIN then VALIDATION, target P(>=2x within 1 h), entry at P0", "",
             "TRAIN picks every cut point and every 'best bin'; VALIDATION only re-measures them. "
             "AUC > 0.5: higher values go with more doublings. perm p: %d label permutations, alert level "
             "(clusters ignored, so optimistic). 'best-of-bins perm p' tests the maximum over bins, the "
             "statistic actually selected. Regenerate: `python3 post_detection_edge/code/an_30_univariate.py`."
             % N_PERM, "",
             "| feature | N train | AUC train | p (normal) | perm p | TRAIN quartile cuts | rate by bin, TRAIN "
             "| best bin | best-of-bins perm p | N val | AUC val | rate by bin, VAL | best-bin rate VAL "
             "(VAL base) |",
             "|---|---:|---:|---:|---:|---|---|---|---:|---:|---:|---|---|"]
    summary: list[dict[str, Any]] = []
    tr_lab = [(r, label(r, k0, h0)) for r in train]
    va_lab = [(r, label(r, k0, h0)) for r in val]
    base_val = sum(y for _, y in va_lab if y is not None) / sum(1 for _, y in va_lab if y is not None)
    for f in CONTINUOUS + CATEGORICAL:
        tr = [(value(r, f), y) for r, y in tr_lab if y is not None and value(r, f) is not None]
        va = [(value(r, f), y) for r, y in va_lab if y is not None and value(r, f) is not None]
        if len(tr) < 30:
            lines.append("| %s | %d | too few non-missing TRAIN rows | | | | | | | | | | |" % (f, len(tr)))
            continue
        y = [b for _, b in tr]
        if f in CONTINUOUS:
            xs = [float(a) for a, _ in tr]
            a_tr = pde.auc(xs, y)
            n1 = sum(y)
            p_norm = pde.auc_p(a_tr, n1, len(y) - n1) if a_tr is not None else None
            n_tests += 1
            # permutation p of |AUC - 0.5|
            ge = 0
            yy = list(y)
            for _ in range(N_PERM):
                rng.shuffle(yy)
                ap = pde.auc(xs, yy)
                if ap is not None and abs(ap - 0.5) >= abs(a_tr - 0.5) - 1e-12:
                    ge += 1
            p_perm = (ge + 1) / (N_PERM + 1)
            c = cuts(xs)
            if len(set(c)) < 3:
                # a near-constant feature: bin on distinct values instead
                c = sorted(set(c))
            bins = [binof(x, c) for x in xs]
            levels = sorted(set(bins))
            cut_txt = ", ".join("%.4g" % v for v in c)
        else:
            a_tr, p_norm, p_perm = None, None, None
            bins = [a for a, _ in tr]
            levels = sorted(set(bins), key=str)
            c = []
            cut_txt = "levels"
        best, br = best_bin_stat(bins, y, levels)
        ge = 0
        yy = list(y)
        for _ in range(N_PERM):
            rng.shuffle(yy)
            _, bp = best_bin_stat(bins, yy, levels)
            if bp >= br - 1e-12:
                ge += 1
        p_best = (ge + 1) / (N_PERM + 1)
        n_tests += 1
        rate_tr = "; ".join("%s:%d/%d" % (lv, sum(y[i] for i, b in enumerate(bins) if b == lv),
                                          sum(1 for b in bins if b == lv)) for lv in levels)
        if f in CONTINUOUS:
            vb = [binof(float(a), c) for a, _ in va]
        else:
            vb = [a for a, _ in va]
        vy = [b for _, b in va]
        a_va = pde.auc([float(a) for a, _ in va], vy) if f in CONTINUOUS and va else None
        rate_va = "; ".join("%s:%d/%d" % (lv, sum(vy[i] for i, b in enumerate(vb) if b == lv),
                                          sum(1 for b in vb if b == lv)) for lv in levels)
        vi = [i for i, b in enumerate(vb) if b == best]
        best_va = pde.rate_cell(sum(vy[i] for i in vi), len(vi))
        lines.append("| %s | %d | %s | %s | %s | %s | %s | %s (%.1f %%) | %.4f | %d | %s | %s | %s (%.1f %%) |" % (
            f, len(tr), "n/a" if a_tr is None else "%.3f" % a_tr, "n/a" if p_norm is None else "%.4f" % p_norm,
            "n/a" if p_perm is None else "%.4f" % p_perm, cut_txt, rate_tr, best, 100 * br, p_best, len(va),
            "n/a" if a_va is None else "%.3f" % a_va, rate_va, best_va, 100 * base_val))
        summary.append({"feature": f, "auc_train": a_tr, "p_perm": p_perm, "auc_val": a_va, "best_bin": best,
                        "best_rate_train": br, "p_best": p_best,
                        "best_rate_val": (sum(vy[i] for i in vi) / len(vi)) if vi else None, "n_val_bin": len(vi)})

    # BH over the primary screen
    ps = [s["p_best"] for s in summary]
    adj = pde.bh(ps)
    lines += ["", "Benjamini-Hochberg on the %d 'best-of-bins' p-values of the primary screen: %d below 0.05 "
              "(%s)." % (len(ps), sum(1 for a in adj if a < 0.05),
                         ", ".join("%s q=%.3f" % (s["feature"], a) for s, a in zip(summary, adj) if a < 0.10)
                         or "none below 0.10")]

    # secondary grid: every threshold x horizon
    grid = ["", "## Secondary grid: AUC by threshold and horizon (TRAIN, then VALIDATION)", "",
            "Cells with fewer than 5 TRAIN positives are skipped. BH across the whole grid.", ""]
    cells: list[tuple[str, str, float, float, Optional[float]]] = []
    for h in pde.HORIZONS:
        for k in pde.THRESHOLDS:
            ty = [(r, label(r, k, h)) for r in train]
            if sum(1 for _, y in ty if y) < 5:
                continue
            vy_ = [(r, label(r, k, h)) for r in val]
            for f in CONTINUOUS:
                tr = [(float(value(r, f)), y) for r, y in ty if y is not None and value(r, f) is not None]
                if len(tr) < 30 or len({b for _, b in tr}) < 2:
                    continue
                a = pde.auc([x for x, _ in tr], [b for _, b in tr])
                if a is None:
                    continue
                n1 = sum(b for _, b in tr)
                p = pde.auc_p(a, n1, len(tr) - n1)
                va = [(float(value(r, f)), y) for r, y in vy_ if y is not None and value(r, f) is not None]
                av = pde.auc([x for x, _ in va], [b for _, b in va]) if va else None
                cells.append(("%gx@%s" % (k, pde.H_LABEL[h]), f, a, p, av))
                n_tests += 1
    adj = pde.bh([c[3] for c in cells])
    sig = [(c, q) for c, q in zip(cells, adj) if q < 0.05]
    grid.append("Grid: %d (feature, target) AUC tests. Significant after BH at q < 0.05 in TRAIN: %d." % (
        len(cells), len(sig)))
    if sig:
        grid += ["", "| target | feature | AUC train | q (BH) | AUC val | same direction in VAL |",
                 "|---|---|---:|---:|---:|---|"]
        for (tgt, f, a, p, av), q in sorted(sig, key=lambda z: z[1]):
            same = "n/a" if av is None else ("yes" if (a - 0.5) * (av - 0.5) > 0 else "NO")
            grid.append("| %s | %s | %.3f | %.4f | %s | %s |" % (tgt, f, a, q, "n/a" if av is None else
                                                               "%.3f" % av, same))
    lines += grid
    lines += ["", "Tests run by this script: %d." % n_tests]
    pde.write_table("T2_univariate.md", "\n".join(lines))
    os.makedirs(pde.DERIVED, exist_ok=True)
    with open(os.path.join(pde.DERIVED, "univariate_summary.json"), "w", encoding="utf8") as fh:
        json.dump({"n_tests": n_tests, "primary": summary}, fh, indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
