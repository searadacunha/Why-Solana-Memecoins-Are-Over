#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""desc_45_families.py -- descriptive tables per feature family and the follow-through of the move.

Usage: python3 desc_45_families.py selection   (DISCOVERY + SELECTION only, before the freeze)
       python3 desc_45_families.py oos         (all four blocks, after the OOS read; descriptive)
Per family and target: number of atoms, single atoms passing DISCOVERY, and the three single atoms
with the best worst-block lift lower bound on DISCOVERY and SELECTION (the selection score).
Follow-through: base rates of 2x / 3x / 5x, P(3x | 2x), P(5x | 3x), time to target, lowest multiple
before the target, MFE and MAE, per block the stage may read.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

import ap_data as D
import ap_lib as A
import ap_mine as M


def main() -> None:
    stage = sys.argv[1] if len(sys.argv) > 1 else "selection"
    if stage not in ("selection", "oos"):
        raise SystemExit("stage must be 'selection' (after the freeze) or 'oos' (after the OOS read)")
    if stage == "selection" and not os.path.exists(A.SEL_FREEZE):
        raise SystemExit("descriptive SELECTION reading is allowed only after SELECTION_FREEZE.json exists")
    if stage == "oos" and not os.path.exists(A.OOS_DONE):
        raise SystemExit("descriptive OOS reading is allowed only after OOS_READ.json exists")
    mx = D.load_matrix()
    lab = D.label_arrays(stage, mx["mints"])
    blocks, elig, ex = mx["blocks"], lab["elig"], lab["extra"]
    out: dict = {"stage": stage, "follow_through": {}, "families": {}}
    for b in A.STAGE_BLOCKS[stage]:
        rows = np.flatnonzero(elig & (blocks == b))
        y2, y3, y5 = (lab["y"][t][rows] for t in A.TARGETS)
        ft = {"n": int(len(rows)), "rate_2x": float(y2.mean()), "rate_3x": float(y3.mean()), "rate_5x": float(y5.mean()),
              "p_3x_given_2x": float(y3[y2 == 1].mean()) if y2.sum() else None,
              "p_5x_given_3x": float(y5[y3 == 1].mean()) if y3.sum() else None,
              "mfe_median": float(np.nanmedian(ex["mfe_3600"][rows])), "mfe_p90": float(np.nanquantile(ex["mfe_3600"][rows], 0.9)),
              "mae_median": float(np.nanmedian(ex["mae_3600"][rows]))}
        for k in A.MULTS:
            th = ex["t_hit_%gx" % k][rows]
            lo = ex["low_before_%gx" % k][rows]
            if (~np.isnan(th)).sum():
                ft["t_hit_%gx_median_s" % k] = float(np.nanmedian(th))
                ft["t_hit_%gx_p90_s" % k] = float(np.nanquantile(th, 0.9))
                ft["low_before_%gx_median" % k] = float(np.nanmedian(lo))
                ft["low_before_%gx_p10" % k] = float(np.nanquantile(lo, 0.1))
        for h in A.HORIZONS:
            for k in A.MULTS:
                v = ex["conf_%gx_%d" % (k, h)][np.flatnonzero(blocks == b)]
                ft["rate_%gx_%ds" % (k, h)] = float(np.nanmean(v)) if (~np.isnan(v)).sum() else None
        for s in ("tp2_next", "tp3_next", "tp5_next", "time60", "time300", "time900", "time3600"):
            ft["net_500_" + s] = float(np.nanmean(ex[s + ".net_500"][rows]))
        out["follow_through"][b] = ft
    # single atoms per family on DISCOVERY and SELECTION
    excl = D.excluded_features()
    r_d = np.flatnonzero(elig & (blocks == "DISC"))
    r_s = np.flatnonzero(elig & (blocks == "SEL"))
    B, desc, _ = M.prepare_atoms(mx["X"], mx["names"], mx["meta"], r_d, excl, D.no_missing_features())
    Kd, Ks = M.cluster_onehot(mx["clusters"][r_d]), M.cluster_onehot(mx["clusters"][r_s])
    cap = M.CFG["CAP"] or 1e9
    n_tests = 0
    for tg in A.TARGETS:
        yd, ys = lab["y"][tg][r_d].astype(np.float32), lab["y"][tg][r_s].astype(np.float32)
        Fd, Fs = B[:, r_d].astype(np.float32), B[:, r_s].astype(np.float32)
        nd, hd, pd_ = M.capped(Fd, yd, Kd, cap)
        ns, hs, ps = M.capped(Fs, ys, Ks, cap)
        bd = float(M.capped(np.ones((1, len(r_d)), dtype=np.float32), yd, Kd, cap)[2][0])
        bs = float(M.capped(np.ones((1, len(r_s)), dtype=np.float32), ys, Ks, cap)[2][0])
        score = np.minimum(A.wilson_lb_vec(hd, nd, z=1.2816) / bd, A.wilson_lb_vec(hs, ns, z=1.2816) / bs)
        raw_d = (Fd @ yd) / np.maximum(Fd.sum(1), 1)
        raw_s = (Fs @ ys) / np.maximum(Fs.sum(1), 1)
        n_tests += 2 * len(desc)
        for fam in sorted({d["family"] for d in desc}):
            idx = [i for i, d in enumerate(desc) if d["family"] == fam]
            best = sorted(idx, key=lambda i: -score[i])[:3]
            out["families"].setdefault(fam, {})[tg] = {
                "atoms": len(idx), "features": len({desc[i]["feat"] for i in idx}),
                "atoms_score_above_1": int(sum(1 for i in idx if score[i] > 1)),
                "best": [{"atom": M.rule_text((i,), desc), "score": float(score[i]),
                          "disc": "%d fires, %.1f %% (base %.1f %%)" % (Fd[i].sum(), 100 * raw_d[i], 100 * float(yd.mean())),
                          "sel": "%d fires, %.1f %% (base %.1f %%)" % (Fs[i].sum(), 100 * raw_s[i], 100 * float(ys.mean()))}
                         for i in best]}
    A.registre("descriptive_" + stage, n_tests, "single atoms scored per family on DISCOVERY and SELECTION (descriptive)",
               n=int(len(r_d) + len(r_s)), declare=False)
    A.write_json(os.path.join(A.TABLES, "families_%s.json" % stage), out)
    for b, ft in out["follow_through"].items():
        print(b, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in ft.items() if k in (
            "n", "rate_2x", "rate_3x", "rate_5x", "p_3x_given_2x", "p_5x_given_3x", "t_hit_2x_median_s", "low_before_2x_median", "net_500_tp2_next", "net_500_time60")})
    for fam, d in out["families"].items():
        for tg in A.TARGETS:
            x = d[tg]
            print("%-8s %s atoms %4d score>1 %3d | best %.2f %s | DISC %s | SEL %s" % (
                fam, tg, x["atoms"], x["atoms_score_above_1"], x["best"][0]["score"], x["best"][0]["atom"], x["best"][0]["disc"], x["best"][0]["sel"]))


if __name__ == "__main__":
    main()
