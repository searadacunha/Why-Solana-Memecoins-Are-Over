#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Level 3 and 4: models by ablation, fitted on TRAIN, chosen on VALIDATION, locked.

Feature sets (families from feature_dictionary.md, PRE_ENTRY only):
  A_bundle                  bundle
  B_bundle_wallets          bundle + wallets
  C_bundle_funding          bundle + funding
  D_bundle_funding_history  bundle + funding + wallets + history
  E_bundle_funding_micro    bundle + funding + micro-structure + price
  F_full                    every family, context included
  F_no_price / F_no_bundle / F_no_funding / F_no_history   F_full minus one block
  R_price_only              price alone, the reference an on-chain model has to beat
Two entries: A (at the alert) and V (at +30 s, with the first 30 s as features).
Target: 2x within 1 h of the entry, complete-case, for every model. The other
targets are only used to describe the locked headline model's ranking.

Per (feature set, entry), 11 configurations: ridge logistic (lambda 1, 10, 100,
1000), tree (depth 2, 3), forest (200 trees, depth 3, 5), boosting (50, 150,
300 rounds). Every configuration is fitted on TRAIN only; the one with the best
VALIDATION ROC-AUC is locked. The headline is F_full at entry A, declared
before any fit. The lock also freezes the thresholds used on TEST (VALIDATION
score quantiles), the decision rules of the verdict, and the trading
parameters.

Output: tables/T3_model_selection.md, tables/LOCK.json. TEST does not exist yet
when this runs: its alerts are posterior to the snapshot.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from multiprocessing import Pool
from typing import Any

import fml
from feat_30_build import DERIVED, FAMILY, STUDY, read_rows

SETS = {
    "A_bundle": {"bundle"},
    "B_bundle_wallets": {"bundle", "wallets"},
    "C_bundle_funding": {"bundle", "funding"},
    "D_bundle_funding_history": {"bundle", "funding", "wallets", "history"},
    "E_bundle_funding_micro": {"bundle", "funding", "micro", "price"},
    "F_full": {"bundle", "wallets", "history", "funding", "micro", "price", "context"},
    "F_no_price": {"bundle", "wallets", "history", "funding", "micro", "context"},
    "F_no_bundle": {"wallets", "history", "funding", "micro", "price", "context"},
    "F_no_funding": {"bundle", "wallets", "history", "micro", "price", "context"},
    "F_no_history": {"bundle", "funding", "micro", "price", "context"},
    "R_price_only": {"price"},
}
CONFIGS = ([("logreg", {"lam": x}) for x in (1.0, 10.0, 100.0, 1000.0)]
           + [("tree", {"depth": d}) for d in (2, 3)]
           + [("forest", {"depth": d}) for d in (3, 5)]
           + [("boost", {"rounds": r}) for r in (50, 150, 300)])
HEADLINE = ("F_full", "A")
TARGET = "2x_1h"
TOPS = (0.01, 0.05, 0.10, 0.20, 0.30, 0.50)
TABLES = os.path.join(STUDY, "tables")


def data(rows: list[dict[str, Any]], entry: str, names: list[str]) -> tuple[list, list]:
    X = [r["f" + entry] for r in rows if r["y"].get("%s_%s" % (entry, TARGET)) is not None]
    y = [r["y"]["%s_%s" % (entry, TARGET)] for r in rows if r["y"].get("%s_%s" % (entry, TARGET)) is not None]
    return X, y


def fit_one(kind: str, hp: dict[str, Any], Xt: list, yt: list, cuts: list) -> Any:
    if kind == "logreg":
        return fml.LogReg(hp["lam"]).fit(Xt, yt)
    if kind == "tree":
        return fml.Tree(hp["depth"]).fit(Xt, yt, cuts)
    if kind == "forest":
        return fml.Forest(200, hp["depth"]).fit(Xt, yt, cuts)
    return fml.Boost(hp["rounds"]).fit(Xt, yt, cuts)


def job(args: tuple[str, str]) -> dict[str, Any]:
    name, entry = args
    rows = read_rows("forensic_rows.jsonl.gz")
    tr = [r for r in rows if r["split"] == "train" and (entry == "A" or r["fine"])]
    va = [r for r in rows if r["split"] == "val" and (entry == "A" or r["fine"])]
    names = sorted(f for f, fam in FAMILY.items() if fam in SETS[name])
    Rt, yt = data(tr, entry, names)
    Rv, yv = data(va, entry, names)
    prep = fml.Prep(names).fit(Rt)
    Xt, Xv = prep.transform(Rt), prep.transform(Rv)
    cuts = [prep.cuts[f] for f in names]
    res = []
    best = None
    for kind, hp in CONFIGS:
        t0 = time.time()
        m = fit_one(kind, hp, Xt, yt, cuts)
        sv, st = m.score(Xv), m.score(Xt)
        auc_v, auc_t = fml.roc_auc(sv, yv), fml.roc_auc(st, yt)
        r = {"kind": kind, "hp": hp, "auc_train": auc_t, "auc_val": auc_v, "pr_val": fml.pr_auc(sv, yv),
             "brier_val": fml.brier(sv, yv), "secs": round(time.time() - t0, 1)}
        res.append(r)
        if best is None or (auc_v or 0) > (best[0]["auc_val"] or 0):
            best = (r, m, sv)
    r, m, sv = best
    thr = {str(k): sorted(sv)[max(0, int(round((1 - k) * len(sv))) - 1)] for k in TOPS}
    tops = {str(k): fml.top_k(sv, yv, k) for k in TOPS}
    return {"set": name, "entry": entry, "features": names, "n_train": len(yt), "n_val": len(yv),
            "base_train": sum(yt) / len(yt), "base_val": sum(yv) / len(yv), "configs": res, "chosen": r,
            "state": m.state(), "prep": prep.state(), "val_thresholds": thr, "val_tops": tops,
            "val_ece": fml.ece(sv, yv)[0]}


def main() -> None:
    if os.path.exists(os.path.join(TABLES, "LOCK.json")) and "--relock" not in sys.argv:
        sys.exit("tables/LOCK.json exists: the models are locked (a rerun would need --relock, before TEST only)")
    jobs = [(s, e) for e in ("A", "V") for s in SETS]
    with Pool(min(8, os.cpu_count() or 2)) as pool:
        out = pool.map(job, jobs)
    os.makedirs(TABLES, exist_ok=True)
    lines = ["# T3. Model selection on VALIDATION (TRAIN fit only)", "",
             "Target 2x within 1 h of the entry, complete-case. 11 configurations per feature set and entry; the "
             "best VALIDATION ROC-AUC is locked. Regenerate: `python3 post_detection_forensics/code/"
             "mod_40_select.py --relock` (only before the TEST exists).", "",
             "| feature set | entry | features | N train | N val | base val | chosen | AUC train | AUC val | "
             "PR-AUC val | Brier val | P(2x) top 10 % val | best logreg / tree / forest / boost AUC val |",
             "|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|"]
    for o in out:
        c = o["chosen"]
        by = {}
        for r in o["configs"]:
            by[r["kind"]] = max(by.get(r["kind"], 0), r["auc_val"] or 0)
        k, n = o["val_tops"]["0.1"]
        lines.append("| %s | %s | %d | %d | %d | %.1f %% | %s %s | %.3f | %.3f | %.3f | %.3f | %.1f %% (%d/%d) | "
                     "%.3f / %.3f / %.3f / %.3f |" % (
                         o["set"], o["entry"], len(o["features"]), o["n_train"], o["n_val"], 100 * o["base_val"],
                         c["kind"], json.dumps(c["hp"]), c["auc_train"], c["auc_val"], c["pr_val"], c["brier_val"],
                         100 * k / n, k, n, by["logreg"], by["tree"], by["forest"], by["boost"]))
    n_fits = sum(len(o["configs"]) for o in out)
    lines += ["", "Fits: %d (%d feature sets x 2 entries x %d configurations). Features per set: %s." % (
        n_fits, len(SETS), len(CONFIGS), {o["set"]: len(o["features"]) for o in out if o["entry"] == "A"})]
    with open(os.path.join(TABLES, "T3_model_selection.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")
    rows_sha = hashlib.sha256(open(os.path.join(DERIVED, "forensic_rows.jsonl.gz"), "rb").read()).hexdigest()
    lock = {
        "locked_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "train_val_rows_sha256": rows_sha,
        "target": TARGET, "headline": list(HEADLINE), "sets": {k: sorted(v) for k, v in SETS.items()},
        "n_fits": n_fits, "models": out,
        "test_population": "every detector alert after the snapshot T_SNAP 2026-09-29 11:23:00 UTC, frozen in a "
                           "separate snapshot, on-chain features collected with this commit's code",
        "decision_rules": {
            "predictive": "headline TEST ROC-AUC with a 95 % cluster-bootstrap CI above 0.5 and a label-permutation "
                          "p < 0.05",
            "strong": "headline TEST ROC-AUC >= 0.70 AND P(2x) in the top 10 % (fixed VALIDATION threshold) with a "
                      "Wilson lower bound at least 20 points above the TEST base rate",
            "on_chain": "F_no_price keeps a TEST ROC-AUC CI above 0.5 (otherwise the information is price, not "
                        "deep on-chain structure)",
            "tradable": "top 10 % (fixed threshold), hold to 2x for 1 h, +10 s, $500, on-chain reserve costs: mean "
                        "net return with a 95 % cluster CI above 0",
            "verdict": "ROBUST ON-CHAIN SIGNAL = predictive AND strong AND on_chain AND tradable; STATISTICAL "
                       "SIGNAL - NOT TRADABLE = predictive AND strong AND not tradable; WEAK ON-CHAIN SIGNAL = "
                       "predictive but not strong; NO ROBUST ON-CHAIN SEPARATION FOUND = not predictive; "
                       "INCONCLUSIVE = fewer than 300 TEST alerts with an observed 1 h window",
        },
        "trading": {"strategies": {"HOLD_1h": {"tp": 2.0, "sl": None, "timeout_s": 3600},
                                   "TP2_SL20_5m": {"tp": 2.0, "sl": 0.8, "timeout_s": 300},
                                   "HOLD_15m": {"tp": 2.0, "sl": None, "timeout_s": 900}},
                    "primary": "HOLD_1h", "tops": [0.01, 0.05, 0.10, 0.20], "sizes_usd": [100, 500, 1000],
                    "latencies_s": [0, 5, 10, 15, 20], "fee_per_leg": 0.01, "fixed_sol_per_tx": 0.005,
                    "depth": "the pool's SOL reserve read on chain before the cut-off; the exit reserve follows the "
                             "constant product, reserve x sqrt(price ratio)"},
    }
    with open(os.path.join(TABLES, "LOCK.json"), "w", encoding="utf8") as fh:
        json.dump(lock, fh)
        fh.write("\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
