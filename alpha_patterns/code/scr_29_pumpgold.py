#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scr_29_pumpgold.py -- targeted DISCOVERY screen of the Pump-Gold features and of their
combinations with the existing families. DISCOVERY labels only; nothing is frozen or selected.

The matrix is extended IN MEMORY with the pg_* columns (new family WASH). Atoms are built with the
study's own rules; only pairs and triples that contain at least one pg_* atom are evaluated, with
the same DISCOVERY filters (support, Wilson, halves, parents, days, clusters, cluster cap). The same
screen is then run on DISCOVERY labels permuted at random (within DISCOVERY) as a noise benchmark.
Every count goes to the registry. Output: tables/pumpgold_screen.json.
"""
from __future__ import annotations

import json
import os
from collections import Counter

import numpy as np

import ap_data as D
import ap_lib as A
import ap_mine as M
from feat_27_pumpgold import DICT


def main() -> None:
    mx = D.load_matrix()
    lab = D.label_arrays("discovery", mx["mints"])
    rows_d = np.flatnonzero(lab["elig"])
    assert set(mx["blocks"][rows_d]) == {"DISC"}
    pg = {r["mint"]: r for r in A.jl(os.path.join(A.DERIVED, "feat_pumpgold.jsonl.gz"))}
    pnames = list(DICT)
    P = np.array([[np.nan if pg[m].get(k) is None else pg[m][k] for k in pnames] for m in mx["mints"]], dtype=np.float32)
    X = np.concatenate([mx["X"], P], axis=1)
    names = mx["names"] + pnames
    meta = dict(mx["meta"])
    for k in pnames:
        meta[k] = {"family": "WASH", "source": "pg"}
    excl = D.excluded_features()
    nomiss = D.no_missing_features() | set(pnames)      # no 'missing' atom for the new features either
    B, desc, ainfo = M.prepare_atoms(X, names, meta, rows_d, excl, nomiss)
    allowed, n_forb = M.allowed_pairs(X, desc, rows_d)
    is_pg = np.array([d["family"] == "WASH" for d in desc])
    allowed_pg = allowed & (is_pg[:, None] | is_pg[None, :])
    cfg = dict(M.CFG)
    cfg["TRIPLE_SEEDS"] = 100
    print("atoms %d (pg atoms %d), allowed pairs with a pg atom %d, forbidden copies %d" % (
        len(desc), int(is_pg.sum()), int(np.triu(allowed_pg, 1).sum()), n_forb))
    res = {"atoms": {"total": len(desc), "pg": int(is_pg.sum())}, "real": {}, "shuffled": {}}
    rng = np.random.default_rng(20261006)
    for tg in A.TARGETS:
        for mode in ("real", "shuffled"):
            y = lab["y"][tg].copy()
            if mode == "shuffled":
                y[rows_d] = rng.permutation(y[rows_d])
            disc = M.mine_disc(B, desc, y, rows_d, mx["days"], mx["clusters"], allowed_pg, cfg, allowed3=allowed)
            rules = [r for r in disc["rules"] if any(is_pg[a] for a in r["rule"])]
            ev = disc["evaluated"]
            ev["singles"] = int(is_pg.sum())
            A.registre("pumpgold_screen_" + mode, sum(ev.values()), "Pump-Gold atoms and pairs/triples on DISCOVERY, %s labels, %s" % (mode, tg),
                       {"target": tg, **ev, "passed": len(rules)}, n=int(len(rows_d)), declare=False,
                       donnees="reelles" if mode == "real" else "synthetiques")
            top = sorted(rules, key=lambda r: -r["lb"])[:15]
            fam = Counter()
            for r in rules:
                for a in r["rule"]:
                    if not is_pg[a]:
                        fam[desc[a]["family"]] += 1
            per_feat = Counter(desc[a]["feat"] for r in rules for a in r["rule"] if is_pg[a])
            res[mode][tg] = {"base": disc["base"], "evaluated": ev, "passed": len(rules),
                             "passed_by_depth": dict(Counter(len(r["rule"]) for r in rules)),
                             "partner_families": dict(fam), "pg_feature_uses": dict(per_feat.most_common()),
                             "top": [{"text": M.rule_text(r["rule"], desc), "n": r["n"], "prec": r["prec"], "lift": r["lift"],
                                      "lb": r["lb"], "clusters": r["clusters"], "days": r["days"]} for r in top]}
            print("%s %s: base %.3f evaluated %s passed %d %s" % (tg, mode, disc["base"], ev, len(rules), res[mode][tg]["passed_by_depth"]))
            for r in top[:5]:
                print("    n %3d prec %.2f lift %.2f cl %2d  %s" % (r["n"], r["prec"], r["lift"], r["clusters"], M.rule_text(r["rule"], desc)))
    A.write_json(os.path.join(A.TABLES, "pumpgold_screen.json"), res)


if __name__ == "__main__":
    main()
