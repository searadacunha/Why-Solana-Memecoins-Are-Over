#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 7 of analysis_plan.md: four model types on each feature set.

Feature sets: bundle, funding, wallets + history, micro, actor, actor +
premium, price + micro (premium included), all, and "screened": the features
that pass BH in TRAIN at step 1 (derived/D1_summary.json), plus actor and
premium. Types and grids: ridge logistic (lambda 1, 10, 100, 1000), tree
(depth 2, 3), forest (200 trees, depth 3, 5), boosting (50, 150, 300 rounds).
Fit on TRAIN, the configuration with the best VALIDATION ROC-AUC is kept per
set. VALIDATION: ROC-AUC, PR-AUC, Brier, calibration error, precision / recall
/ F1 at the TRAIN top-20 % score threshold, and precision in the top 5 / 10 /
20 / 30 % (the main metric).

The gate of the verdict (amendment of 2026-09-29 in analysis_plan.md) is
"screened" minus "actor + premium", paired VALIDATION ROC-AUC difference with a
cluster-bootstrap CI; "all" minus "actor + premium" is reported beside it. The
"screened" model is the one step 8 re-measures.
"""
from __future__ import annotations

import json
import os
from multiprocessing import Pool
from typing import Any

import ana_lib as L
import fml

SETS = {"bundle": {"bundle"}, "funding": {"funding"}, "wallets + history": {"wallets", "history"},
        "micro": {"micro"}, "actor": {"actor"}, "actor + premium": {"actor", "premium"},
        "price + micro": {"price", "premium", "micro"},
        "all": {"bundle", "funding", "wallets", "history", "micro", "price", "premium", "actor", "context"},
        "screened": None}
CONFIGS = ([("logreg", x) for x in (1.0, 10.0, 100.0, 1000.0)] + [("tree", d) for d in (2, 3)]
           + [("forest", d) for d in (3, 5)] + [("boost", r) for r in (50, 150, 300)])
GATE, BESIDE, REF = "screened", "all", "actor + premium"


def names_of(name: str) -> list[str]:
    if SETS[name] is not None:
        return [f for f in L.SAFE if L.FAM[f] in SETS[name]]
    bh = json.load(open(os.path.join(L.FB.DERIVED, "D1_summary.json")))["bh_train"]
    return sorted({f for f in bh if L.FAM[f] not in ("actor", "premium")}) + ["c_actor_grouped",
                                                                             "p_entry_over_operator"]


def job(name: str) -> dict[str, Any]:
    rows = L.load()
    tr, va = L.xy(rows, "train"), L.xy(rows, "val")
    names = names_of(name)
    prep = fml.Prep(names).fit([x for _, x, _ in tr])
    Xt, Xv = prep.transform([x for _, x, _ in tr]), prep.transform([x for _, x, _ in va])
    yt, yv = [y for _, _, y in tr], [y for _, _, y in va]
    cuts = [prep.cuts[f] for f in names]
    best = None
    for kind, hp in CONFIGS:
        if kind == "logreg":
            m = fml.LogReg(hp).fit(Xt, yt)
        elif kind == "tree":
            m = fml.Tree(hp).fit(Xt, yt, cuts)
        elif kind == "forest":
            m = fml.Forest(200, hp).fit(Xt, yt, cuts)
        else:
            m = fml.Boost(hp).fit(Xt, yt, cuts)
        sv = m.score(Xv)
        a = fml.roc_auc(sv, yv)
        if best is None or (a or 0) > best[0]:
            best = (a, kind, hp, m, sv)
    a, kind, hp, m, sv = best
    st = m.score(Xt)
    thr = sorted(st)[int(0.8 * (len(st) - 1))]
    return {"set": name, "names": names, "kind": kind, "hp": hp, "auc": a, "pr": fml.pr_auc(sv, yv),
            "brier": fml.brier(sv, yv), "ece": fml.ece(sv, yv)[0], "at": fml.at_threshold(sv, yv, thr),
            "tops": {str(k): fml.top_k(sv, yv, k) for k in (0.05, 0.10, 0.20, 0.30)},
            "val_scores": sv, "train_thr20": thr, "state": m.state(), "prep": prep.state()}


def gate(rows: list[dict[str, Any]], a: dict[str, Any], b: dict[str, Any]) -> list[Any]:
    """a minus b, VALIDATION ROC-AUC, 95 % CI resampling operator clusters."""
    va = L.xy(rows, "val")
    items = [(r["cluster"], (sa, sb, y)) for (r, _, y), sa, sb in zip(va, a["val_scores"], b["val_scores"])]

    def stat(sample: list) -> Any:
        ys = [t[2] for t in sample]
        if not 0 < sum(ys) < len(ys):
            return None
        return fml.roc_auc([t[0] for t in sample], ys) - fml.roc_auc([t[1] for t in sample], ys)
    lo, hi = L.boot(items, stat)
    return [a["auc"] - b["auc"], lo, hi]


def main() -> None:
    with Pool(min(len(SETS), os.cpu_count() or 2)) as pool:
        out = pool.map(job, list(SETS))
    rows = L.load()
    yv = [y for _, _, y in L.xy(rows, "val")]
    base = sum(yv) / len(yv)
    by = {o["set"]: o for o in out}
    lines = ["# D7. Models by feature set (primary label, TRAIN fit, VALIDATION choice and measure)", "",
             "VALIDATION base %.1f %% (N %d). %d configurations per set, %d fits. 'screened' = the step 1 "
             "features passing BH in TRAIN, plus actor and premium: %s." % (
                 100 * base, len(yv), len(CONFIGS), len(CONFIGS) * len(SETS), ", ".join(by[GATE]["names"])), "",
             "| feature set | features | kept | ROC-AUC | PR-AUC | Brier | ECE | precision / recall / F1 at TRAIN "
             "top 20 % | P@5 % | P@10 % | P@20 % | P@30 % |", "|---|---:|---|---:|---:|---:|---:|---|---|---|---|---|"]
    for o in out:
        at = o["at"]
        lines.append("| %s | %d | %s %s | %.3f | %.3f | %.4f | %.3f | %s / %s / %s | %s |" % (
            o["set"], len(o["names"]), o["kind"], o["hp"], o["auc"], o["pr"], o["brier"], o["ece"],
            "n/a" if at["precision"] is None else "%.1f %%" % (100 * at["precision"]),
            "n/a" if at["recall"] is None else "%.1f %%" % (100 * at["recall"]),
            "n/a" if at["f1"] is None else "%.3f" % at["f1"],
            " | ".join(L.rate(*o["tops"][k]) for k in ("0.05", "0.1", "0.2", "0.3"))))
    g = {s: gate(rows, by[s], by[REF]) for s in (GATE, BESIDE)}
    lines.append("")
    for s, (e, lo, hi) in g.items():
        lines.append("- %s '%s' minus '%s', VALIDATION ROC-AUC %+.3f [%s, %s] (95 %% cluster bootstrap)." % (
            "Gate:" if s == GATE else "Beside the gate:", s, REF, e, "n/a" if lo is None else "%+.3f" % lo,
            "n/a" if hi is None else "%+.3f" % hi))
    L.write("D7_models.md", lines)
    with open(os.path.join(L.FB.DERIVED, "D7_summary.json"), "w") as fh:
        json.dump({"gate": g[GATE], "beside": g[BESIDE], "screened_names": by[GATE]["names"],
                   "auc": {o["set"]: o["auc"] for o in out},
                   "kept": {o["set"]: [o["kind"], o["hp"]] for o in out}}, fh, indent=1)
    keep = by[GATE]
    with open(os.path.join(L.FB.DERIVED, "D7_gate_model.json"), "w") as fh:
        json.dump({k: keep[k] for k in ("kind", "hp", "state", "prep", "train_thr20", "auc", "names")}, fh)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
