#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frz_55_candidate.py -- freeze the single pre-declared candidate SWARM + CHEAP ENTRY.

Reads NO outcome. Builds the candidate's firing vector from features only (swarm_10s >= 30 AND
p_entry_over_operator <= the DISCOVERY first-tercile boundary), writes derived/candidates.json and
derived/candidates_fire.npz in the format of val_60 / oos_70 / rob_80, the candidate freeze
(tables/CANDIDATE_SWARM_CHEAP_ENTRY_FREEZE.json: rule, thresholds, features, timestamp, hashes) and
SELECTION_FREEZE.json (the study's protocol freeze: same file list as mine_50 plus the candidate's
files). Refuses to run if a freeze already exists.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

import ap_data as D
import ap_lib as A
import ap_mine as M
from mine_50_selection import FROZEN_FILES

A_MIN = 30
CAND_MD = "tables/CANDIDATE_SWARM_CHEAP_ENTRY.md"
CAND_FREEZE = os.path.join(A.TABLES, "CANDIDATE_SWARM_CHEAP_ENTRY_FREEZE.json")
EXTRA = ["derived/feat_swarm.jsonl.gz", "code/feat_29_swarm.py", "code/frz_55_candidate.py", CAND_MD,
         "tables/CANDIDATE_SWARM_CHEAP_ENTRY_FREEZE.json"]


def main() -> None:
    if os.path.exists(A.SEL_FREEZE) or os.path.exists(CAND_FREEZE):
        sys.exit("a freeze already exists")
    mx = D.load_matrix()
    atoms = json.load(open(os.path.join(A.DERIVED, "atoms.json")))
    ref = np.array(atoms["ref_rows"])
    prem = mx["X"][:, mx["names"].index("p_entry_over_operator")].astype(float)
    b_thr = float(np.nanquantile(prem[ref], 1 / 3))
    sw = {r["mint"]: r["swarm_10s"] for r in A.jl(os.path.join(A.DERIVED, "feat_swarm.jsonl.gz"))}
    a = np.array([sw[m] for m in mx["mints"]], dtype=float)
    fire = (a >= A_MIN) & (~np.isnan(prem)) & (prem <= b_thr)
    cand = {"id": "SWARM_CHEAP", "target": "Y2", "kind": "prespecified", "rule": None, "depth": 2,
            "text": "swarm_10s >= %d AND p_entry_over_operator <= %.16g" % (A_MIN, b_thr),
            "families": ["TEMPO", "PRICE"],
            "atoms": [{"feat": "swarm_10s", "op": ">=", "thr": float(A_MIN), "q": None, "family": "TEMPO", "col": None},
                      {"feat": "p_entry_over_operator", "op": "<=", "thr": b_thr, "q": 1 / 3, "family": "PRICE",
                       "col": mx["names"].index("p_entry_over_operator")}],
            "disc": {"note": "not computed before the freeze (hypothesis born from DISCOVERY)"},
            "sel": {"note": "SELECTION not read"},
            "fires_by_block_all_alerts": {b: int(fire[mx["blocks"] == b].sum()) for b in A.BLOCKS}}
    A.write_json(os.path.join(A.DERIVED, "candidates.json"), {"cfg": M.CFG, "info": {"note": "single pre-declared candidate, PLAN section 11"},
                                                               "candidates": [cand]})
    np.savez_compressed(os.path.join(A.DERIVED, "candidates_fire.npz"), SWARM_CHEAP=fire)
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    A.write_json(CAND_FREEZE, {"frozen_at_utc": now, "rule": "IF swarm_10s >= 30 AND p_entry_over_operator <= B THEN SIGNAL",
                               "thresholds": {"A_min": A_MIN, "B_premium_max": b_thr, "B_definition": "first tercile of p_entry_over_operator over the 363 DISCOVERY reference rows (rob_80, 2026-10-05)"},
                               "features": {"swarm_10s": "distinct external buyer wallets with block time <= t_alert - 10 s (feat_29_swarm.py)",
                                            "p_entry_over_operator": "entry premium, forensics fA, cut alert - 1 s"},
                               "target": "Y2 (x2 confirmed within 1 h from the +5 s entry); Y3, Y5 descriptive",
                               "trade": "buy +5 s, TP x2 sold at the next read, time exit 1 h, trade.py costs, $500 primary",
                               "decision": "val_pass (PLAN 7) then Holm m=1 at 0.05; A / B / C as in the candidate file",
                               "fires_by_block_all_alerts": cand["fires_by_block_all_alerts"],
                               "sha256": {CAND_MD: A.sha256_file(os.path.join(A.STUDY, CAND_MD)),
                                          "derived/feat_swarm.jsonl.gz": A.sha256_file(os.path.join(A.DERIVED, "feat_swarm.jsonl.gz")),
                                          "code/feat_29_swarm.py": A.sha256_file(os.path.join(A.STUDY, "code/feat_29_swarm.py")),
                                          "derived/candidates.json": A.sha256_file(os.path.join(A.DERIVED, "candidates.json")),
                                          "derived/candidates_fire.npz": A.sha256_file(os.path.join(A.DERIVED, "candidates_fire.npz"))}})
    files = [f for f in FROZEN_FILES] + EXTRA
    missing = [f for f in files if not os.path.exists(os.path.join(A.STUDY, f))]
    if missing:
        sys.exit("cannot freeze, missing: %s" % missing)
    A.write_json(A.SEL_FREEZE, {"frozen_at_utc": now, "n_candidates": 1, "cfg": M.CFG, "note": "PLAN section 11: single pre-declared candidate",
                                "files": {f: A.sha256_file(os.path.join(A.STUDY, f)) for f in files}})
    A.registre("freeze", 1, "single pre-declared candidate SWARM + CHEAP ENTRY frozen (no outcome read)", n=0, declare=True,
               sortie="tables/CANDIDATE_SWARM_CHEAP_ENTRY_FREEZE.json")
    print("frozen:", cand["text"], "fires by block (all alerts):", cand["fires_by_block_all_alerts"])


if __name__ == "__main__":
    main()
