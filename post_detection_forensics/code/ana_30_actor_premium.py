#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3 of analysis_plan.md: does the actor label carry information of its own,
once the entry premium is known, and do the on-chain features add anything?

Six ridge logistic models, fitted on TRAIN, penalty chosen on VALIDATION ROC-AUC:
  A actor | B premium | C actor + premium | D every on-chain feature without the
  actor | E every feature + actor | F every feature + actor + premium.
VALIDATION: ROC-AUC, PR-AUC, precision in the top 10 / 20 %, and cluster-bootstrap
CIs of the paired AUC differences. The overlap of actor and premium is counted.
"""
from __future__ import annotations

import json
import os
from typing import Any

import ana_lib as L
import fml

LAMS = (1.0, 10.0, 100.0, 1000.0)


def fit(names: list[str], tr: list, va: list) -> dict[str, Any]:
    prep = fml.Prep(names).fit([x for _, x, _ in tr])
    Xt, Xv = prep.transform([x for _, x, _ in tr]), prep.transform([x for _, x, _ in va])
    yt, yv = [y for _, _, y in tr], [y for _, _, y in va]
    best = None
    for lam in LAMS:
        m = fml.LogReg(lam).fit(Xt, yt)
        s = m.score(Xv)
        a = fml.roc_auc(s, yv)
        if best is None or a > best[0]:
            best = (a, lam, s)
    return {"auc": best[0], "lam": best[1], "s": best[2], "pr": fml.pr_auc(best[2], yv),
            "top10": fml.top_k(best[2], yv, 0.10), "top20": fml.top_k(best[2], yv, 0.20)}


def main() -> None:
    rows = L.load()
    tr, va = L.xy(rows, "train"), L.xy(rows, "val")
    onchain = [f for f in L.SAFE if L.FAM[f] not in ("actor", "premium")]
    sets = {"A actor": ["c_actor_grouped"], "B premium": ["p_entry_over_operator"],
            "C actor + premium": ["c_actor_grouped", "p_entry_over_operator"],
            "D on-chain without actor": [f for f in onchain],
            "E all + actor": onchain + ["c_actor_grouped"],
            "F all + actor + premium": onchain + ["c_actor_grouped", "p_entry_over_operator"]}
    res = {k: fit(v, tr, va) for k, v in sets.items()}
    yv = [y for _, _, y in va]
    cl = [r["cluster"] for r, _, _ in va]

    def diff_ci(a: str, b: str) -> tuple:
        items = [(c, (sa, sb, y)) for c, sa, sb, y in zip(cl, res[a]["s"], res[b]["s"], yv)]

        def stat(sample: list) -> Any:
            ys = [t[2] for t in sample]
            if not 0 < sum(ys) < len(ys):
                return None
            return fml.roc_auc([t[0] for t in sample], ys) - fml.roc_auc([t[1] for t in sample], ys)
        return L.boot(items, stat)
    # overlap of actor and premium, all splits
    band = {}
    for r in rows:
        x = r["fA"]
        if x.get("c_actor_grouped") is None or x.get("p_entry_over_operator") is None:
            continue
        key = ("grouped" if x["c_actor_grouped"] else "single",
               "< x4.5" if x["p_entry_over_operator"] < 4.5 else ">= x4.5")
        band[key] = band.get(key, 0) + 1
    base = sum(yv) / len(yv)
    lines = ["# D3. Actor or premium? (primary label, fitted on TRAIN, measured on VALIDATION)", "",
             "VALIDATION base %.1f %% (N %d). Ridge logistic, penalty chosen on VALIDATION among %s." % (
                 100 * base, len(yv), list(LAMS)), "",
             "| model | features | ROC-AUC | PR-AUC | top 10 % | top 20 % |", "|---|---:|---:|---:|---|---|"]
    for k, v in res.items():
        lines.append("| %s | %d | %.3f | %.3f | %s | %s |" % (k, len(sets[k]), v["auc"], v["pr"],
                                                              L.rate(*v["top10"]), L.rate(*v["top20"])))
    lines += ["", "Paired AUC differences on VALIDATION (95 % cluster-bootstrap CI):", ""]
    summary: dict[str, Any] = {"auc": {k: v["auc"] for k, v in res.items()}, "diff": {}}
    for a, b in (("C actor + premium", "B premium"), ("C actor + premium", "A actor"),
                 ("E all + actor", "D on-chain without actor"), ("F all + actor + premium", "C actor + premium"),
                 ("D on-chain without actor", "B premium")):
        lo, hi = diff_ci(a, b)
        summary["diff"]["%s - %s" % (a[0], b[0])] = [res[a]["auc"] - res[b]["auc"], lo, hi]
        lines.append("- %s minus %s: %+.3f [%s, %s]" % (a, b, res[a]["auc"] - res[b]["auc"],
                                                       "n/a" if lo is None else "%+.3f" % lo,
                                                       "n/a" if hi is None else "%+.3f" % hi))
    lines += ["", "Overlap of actor and premium (all alerts with both): %s. A cell with fewer than 20 alerts means "
              "the two cannot be separated in that region." % band]
    L.write("D3_actor_premium.md", lines)
    with open(os.path.join(L.FB.DERIVED, "D3_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
