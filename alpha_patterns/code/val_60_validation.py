#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""val_60_validation.py -- VALIDATION: one read of the frozen candidate list.

Pass rule (ap_mine.val_pass): >= 8 fires in >= 5 clusters on >= 3 days, precision above the block
base rate, one-sided p <= 0.10 where p = max(Fisher exact, cluster bootstrap counting the draws
without a fire against the rule, day-stratified CMH). No multiplicity correction here: this is the
replication screen; the correction is in the OOS. The read marker is written BEFORE any result.
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


def load_candidates():
    c = json.load(open(os.path.join(A.DERIVED, "candidates.json")))["candidates"]
    z = np.load(os.path.join(A.DERIVED, "candidates_fire.npz"))
    for x in c:
        x["fire"] = z[x["id"]]
    return c


def main() -> None:
    A.check_freeze()
    if os.path.exists(A.VAL_DONE):
        sys.exit("VALIDATION was already read once")
    mx = D.load_matrix()
    cands = load_candidates()
    A.write_json(A.VAL_DONE, {"read_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "status": "reading"})
    lab = D.label_arrays("validation", mx["mints"])
    nets = {tg: lab["extra"]["%s.net_500" % A.STRAT_OF[tg]] for tg in A.TARGETS}
    M.holdout(cands, "val", lab["y"], lab["elig"], mx["blocks"], "VAL", mx["clusters"], mx["days"], nets)
    for c in cands:
        c["val_pass"] = M.val_pass(c["val"])
    A.write_json(os.path.join(A.TABLES, "validation.json"),
                 [{k: v for k, v in c.items() if k != "fire"} for c in cands])
    A.write_json(A.VAL_DONE, {"read_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "status": "done",
                              "survivors": [c["id"] for c in cands if c["val_pass"]]})
    A.registre("validation", len(cands), "frozen candidates read once on VALIDATION",
               {"passed": [c["id"] for c in cands if c["val_pass"]]},
               n=int((lab["elig"] & (mx["blocks"] == "VAL")).sum()), sortie="tables/validation.json")
    for c in cands:
        v = c["val"]
        print("%-8s %s  VAL n %3d prec %s base %.3f lift %s p %.3f (F %.3f B %.3f D %.3f) clusters %d days %d net %s" % (
            c["id"], "PASS" if c["val_pass"] else "fail", v["n_fire"],
            "%.2f" % v["prec"] if v.get("prec") is not None else "n/a", v["base"],
            "%.2f" % v["lift"] if v.get("lift") else "n/a", v["p"], v.get("p_fisher", 1), v.get("p_boot", 1), v.get("p_day", 1),
            v["n_clusters_fire"], v["n_days_fire"],
            "%.2f" % v["net_mean"] if v.get("net_mean") is not None else "n/a"))


if __name__ == "__main__":
    main()
