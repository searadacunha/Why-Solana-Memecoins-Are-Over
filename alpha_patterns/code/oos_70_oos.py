#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""oos_70_oos.py -- OOS: the final, separate block, read once.

Confirmatory part: only the VALIDATION survivors are tested, Holm over them at one-sided 0.05
(ap_mine.oos_decide), with >= 8 fires in >= 5 clusters on >= 3 days and precision above the OOS
base rate. Descriptive part: the same statistics for the candidates that failed VALIDATION,
flagged confirmatory = false; they can never become survivors. The read marker is written first.
"""
from __future__ import annotations

import json
import os
import sys
import time

import ap_data as D
import ap_lib as A
import ap_mine as M
from val_60_validation import load_candidates


def main() -> None:
    A.check_freeze()
    if not os.path.exists(A.VAL_DONE) or json.load(open(A.VAL_DONE)).get("status") != "done":
        sys.exit("VALIDATION has not been read")
    if os.path.exists(A.OOS_DONE):
        sys.exit("OOS was already read once")
    surv_ids = set(json.load(open(A.VAL_DONE))["survivors"])
    mx = D.load_matrix()
    cands = load_candidates()
    A.write_json(A.OOS_DONE, {"read_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "status": "reading"})
    lab = D.label_arrays("oos", mx["mints"])
    nets = {tg: lab["extra"]["%s.net_500" % A.STRAT_OF[tg]] for tg in A.TARGETS}
    M.holdout(cands, "oos", lab["y"], lab["elig"], mx["blocks"], "OOS", mx["clusters"], mx["days"], nets)
    surv = [c for c in cands if c["id"] in surv_ids]
    for c in cands:
        c["oos"]["confirmatory"] = c["id"] in surv_ids
        c["oos_pass"] = False
    for c, ok in zip(surv, M.oos_decide([c["oos"] for c in surv])):
        c["oos_pass"] = ok
    A.write_json(os.path.join(A.TABLES, "oos.json"), [{k: v for k, v in c.items() if k != "fire"} for c in cands])
    A.write_json(A.OOS_DONE, {"read_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "status": "done",
                              "survivors": [c["id"] for c in surv if c["oos_pass"]]})
    A.registre("oos", len(surv), "VALIDATION survivors tested once on OOS (Holm)",
               {"passed": [c["id"] for c in surv if c["oos_pass"]], "descriptive_reads": len(cands) - len(surv)},
               n=int((lab["elig"] & (mx["blocks"] == "OOS")).sum()), sortie="tables/oos.json")
    for c in cands:
        v = c["oos"]
        print("%-8s %s  OOS n %3d prec %s base %.3f lift %s p %.3f holm %s clusters %d days %d net %s" % (
            c["id"], "PASS" if c["oos_pass"] else ("conf-fail" if v["confirmatory"] else "descr."), v["n_fire"],
            "%.2f" % v["prec"] if v.get("prec") is not None else "n/a", v["base"],
            "%.2f" % v["lift"] if v.get("lift") else "n/a", v["p"],
            "%.3f" % v["p_holm"] if "p_holm" in v else "-", v["n_clusters_fire"], v["n_days_fire"],
            "%.2f" % v["net_mean"] if v.get("net_mean") is not None else "n/a"))


if __name__ == "__main__":
    main()
