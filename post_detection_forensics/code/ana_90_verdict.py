#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The verdict rules of analysis_plan.md, applied as written to the outputs of
steps 3, 7 and 8 (derived/D3_summary.json, D7_summary.json, D8_summary.json)
and to the freeze record. No threshold here is chosen after the results: every number
below is the plan's.

INCONCLUSIVE        on-chain coverage < 80 % or < 300 VALIDATION alerts with
                    an observed primary label
independent info    step 7 "screened" minus step 7 "actor + premium" (same
                    model grid), VALIDATION ROC-AUC, cluster-bootstrap CI low
                    > 0 (amendment of 2026-09-29: step 3's ridge F minus C and
                    step 7's "all" minus "actor + premium" are reported, not
                    used; positive controls on synthetic data showed both
                    missing planted on-chain effects the screened model finds)
subgroup            a kept signal with VALIDATION N >= 50, rate >= base + 15
                    points, Wilson lower bound > base, >= 6 of 7 variants held,
                    |Spearman| < 0.8 with P0, premium and actor, no 2x2 cell
                    below 20 against actor or premium band, and (amendment of
                    2026-09-29) a lift beyond the TRAIN model of P0, premium
                    and actor whose CI stays above 0
PROMISING ...       independent info AND a subgroup
WEAK ...            independent info, no subgroup
NO ROBUST ...       no independent info
ROBUST ON-CHAIN SIGNAL is not reachable without the future TEST.
"""
from __future__ import annotations

import json
import os

import ana_lib as L

MIN_COVERAGE, MIN_VAL_OBS, MIN_N, MIN_LIFT, MIN_HELD, MAX_RHO, MIN_CELL = 0.80, 300, 50, 0.15, 6, 0.8, 20
MECHANICAL = ("p_log_p0", "p_entry_over_operator", "c_actor_grouped")


def main() -> None:
    L.load()                                   # refuses to run on a table that is not the frozen one
    fr = json.load(open(L.FREEZE))
    d3 = json.load(open(os.path.join(L.FB.DERIVED, "D3_summary.json")))
    d7 = json.load(open(os.path.join(L.FB.DERIVED, "D7_summary.json")))
    d8 = json.load(open(os.path.join(L.FB.DERIVED, "D8_summary.json")))
    cov = fr["onchain_coverage"]
    vobs = fr["primary_observed_by_split"].get("val", 0)
    est, lo, hi = d7["gate"]
    eb, lb_, hb = d7["beside"]
    indep = lo is not None and lo > 0
    e3, l3, h3 = d3["diff"]["F - C"]
    lines = ["# D9. Verdict, rules of analysis_plan.md applied as written", "",
             "- On-chain coverage: %.1f %% (minimum %.0f %%)." % (100 * cov, 100 * MIN_COVERAGE),
             "- VALIDATION alerts with an observed primary label: %d (minimum %d)." % (vobs, MIN_VAL_OBS),
             "- Step 7 'screened' minus 'actor + premium', VALIDATION ROC-AUC: %+.3f [%s, %s], independent "
             "on-chain information: %s. Screened features: %s." % (
                 est, "n/a" if lo is None else "%+.3f" % lo, "n/a" if hi is None else "%+.3f" % hi,
                 "yes" if indep else "no", ", ".join(d7["screened_names"])),
             "- Reported, not used: step 7 'all' minus 'actor + premium', %+.3f [%s, %s]." % (
                 eb, "n/a" if lb_ is None else "%+.3f" % lb_, "n/a" if hb is None else "%+.3f" % hb),
             "- Reported, not used: step 3 ridge F minus C, %+.3f [%s, %s]." % (
                 e3, "n/a" if l3 is None else "%+.3f" % l3, "n/a" if h3 is None else "%+.3f" % h3), ""]
    passing = []
    for name, s in d8.items():
        if name.startswith("_"):
            continue
        p = s["primary"]
        rlo = s["resid_lift"][1]
        rate = p["k"] / p["n"] if p["n"] else 0.0
        checks = {"VALIDATION N >= %d" % MIN_N: p["n"] >= MIN_N,
                  "rate >= base + %d points" % (100 * MIN_LIFT): rate >= p["base"] + MIN_LIFT,
                  "Wilson lower bound > base": (p["lb"] or 0) > p["base"],
                  ">= %d of 7 variants held" % MIN_HELD: s["held"] >= MIN_HELD,
                  "|Spearman| < %.1f with P0, premium, actor" % MAX_RHO:
                      all(abs(s["rho"].get(f, 0.0)) < MAX_RHO for f in MECHANICAL),
                  "no 2x2 cell below %d against actor or premium" % MIN_CELL: not s["small_2x2"],
                  "lift beyond the P0 + premium + actor model, CI above 0": rlo is not None and rlo > 0}
        ok = all(checks.values())
        passing += [name] if ok else []
        lines += ["## %s" % name, "", "VALIDATION %s, base %.1f %%, variants held %d of 7." % (
            L.rate(p["k"], p["n"]), 100 * p["base"], s["held"]), ""]
        lines += ["- %s: %s" % (k, "pass" if v else "FAIL") for k, v in checks.items()]
        lines.append("")
    lines += ["## Historical performance of the kept signals (primary label)", "",
              "| signal | status | period | N selected | base | 2x rate [Wilson 95 %] | lift |",
              "|---|---|---|---:|---:|---|---|"]
    for name, s in d8.items():
        if name.startswith("_"):
            continue
        for sp, status in (("train", "TRAIN (in-sample: chosen or fitted here)"),
                           ("val", "VALIDATION (used to choose among candidates)")):
            q = s["perf"][sp]
            r_ = q["k"] / q["n"] if q["n"] else None
            lines.append("| %s | %s | %s to %s | %d | %.1f %% | %s | %s |" % (
                name, status, q["period"][0], q["period"][1], q["n"], 100 * q["base"], L.rate(q["k"], q["n"]),
                "n/a" if r_ is None else "%+.1f pts, x%.2f" % (100 * (r_ - q["base"]), r_ / q["base"])))
    lines += ["", "No TEST row: the future TEST is a separate question and is not touched here.", ""]
    if cov < MIN_COVERAGE or vobs < MIN_VAL_OBS:
        verdict = "INCONCLUSIVE"
    elif indep and passing:
        verdict = "PROMISING HISTORICAL SIGNAL - NOT YET PROVEN OOS"
    elif indep:
        verdict = "WEAK ON-CHAIN SIGNAL"
    else:
        verdict = "NO ROBUST ON-CHAIN SEPARATION FOUND"
    lines += ["**Verdict: %s**" % verdict, "",
              "ROBUST ON-CHAIN SIGNAL needs the future TEST and is not reachable here. Nothing in this verdict "
              "accounts for costs, slippage or execution prices."]
    L.write("D9_verdict.md", lines)
    with open(os.path.join(L.FB.DERIVED, "D9_verdict.json"), "w") as fh:
        json.dump({"verdict": verdict, "independent": indep, "passing": passing, "coverage": cov,
                   "val_observed": vobs}, fh, indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
