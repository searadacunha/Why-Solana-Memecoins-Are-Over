#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pat_36_rank.py -- rankings of the pre-specified composite patterns (DISCOVERY-only results).

Reads tables/composite_patterns_results.json, writes tables/composite_patterns_ranking.md and
.json: the full table (RANK, PATTERN, FAMILY, N, DAYS, PRECISION / LIFT for x2 / x3 / x5, COVERAGE,
ROBUSTNESS, ECONOMIC_RATIONALE, NEW_INFORMATION, DISCOVERY_ONLY) and the per-category top 3.
Score (positive patterns) = cluster-capped lift on x2 x robustness share, with n >= 20 and at least
5 clusters; negative filters are scored on how far their precision sits below the base rate. A
pattern whose observed direction contradicts its pre-specified direction is kept with the flag
"direction inversée" and scored as observed (data-driven, said so).
"""
from __future__ import annotations

import json
import os

import ap_lib as A

CATS = ["TOP WASH", "TOP COORDINATION", "TOP FUNDING x COORDINATION", "TOP DIVERSITY x VOLUME", "TOP BUY-RUN",
        "TOP ORGANIC RELAY", "TOP CREATOR x WALLET HISTORY", "TOP BUNDLE x POST-BUNDLE", "TOP NEGATIVE FILTERS"]


def pct(x, nd=0):
    return "n/a" if x is None else ("%." + str(nd) + "f %%") % (100 * x)


def num(x, nd=2):
    return "n/a" if x is None else ("%." + str(nd) + "f") % x


def main() -> None:
    R = json.load(open(os.path.join(A.TABLES, "composite_patterns_results.json")))
    be = R["break_even"]
    rows = []
    for p in R["patterns"]:
        m2, m3, m5 = p["main"]["Y2"], p["main"]["Y3"], p["main"]["Y5"]
        lift2 = m2.get("lift")
        observed = None if lift2 is None or m2["n"] < 8 else ("positive" if lift2 > 1 else "negative")
        inverted = observed is not None and observed != ("positive" if p["direction"] == "positive" else "negative")
        rob = p["robustness"]
        # robustness recomputed in the OBSERVED direction when inverted
        if inverted:
            sign = 1 if observed == "positive" else -1
            checks = []
            for tg in ("Y2", "Y3"):
                for v in ("strict", "loose", "cut2"):
                    s_ = p["variants"][v][tg]
                    checks.append(s_["lift"] is not None and s_["n"] >= 8 and sign * (s_["lift"] - 1) > 0)
                for hl in ("half1", "half2"):
                    s_ = p["subperiods"]["halves"][hl][tg]
                    checks.append(s_["precision"] is not None and s_["n"] >= 5 and sign * (s_["precision"] - s_["base"]) > 0)
            rob = {"checks_passed": int(sum(checks)), "checks_total": len(checks), "coherent": bool(all(checks))}
        share = rob["checks_passed"] / max(rob["checks_total"], 1)
        cap2 = m2.get("capped_lift") or 0
        if observed == "positive":
            score = cap2 * share if (m2["n"] >= 20 and m2["clusters"] >= 5) else 0.0
        elif observed == "negative":
            score = (1 / max(cap2, 1e-6)) * share if (m2["n"] >= 20 and m2["clusters"] >= 5) else 0.0
        else:
            score = 0.0
        parts = p["new_information"]["parts"]
        ex_l = (parts.get("existing_only", {}).get("Y2") or {}).get("lift")
        pg_l = (parts.get("pg_only", {}).get("Y2") or {}).get("lift")
        jac = p["new_information"]["closest_existing_atom_jaccard"] or 0
        if lift2 is None:
            newinfo = "n/a"
        else:
            gain_pg = (lift2 - ex_l) if ex_l is not None else None
            newinfo = "lift complet %s ; sans pg %s ; pg seul %s ; Jaccard max avec un atome existant %.2f (%s)" % (
                num(lift2), num(ex_l), num(pg_l), jac, p["new_information"]["closest_existing_atom"])
            if jac >= 0.7:
                newinfo += " : REFORMULATION probable"
            elif gain_pg is not None and gain_pg <= 0.05:
                newinfo += " : le pg n'ajoute rien"
            elif gain_pg is not None:
                newinfo += " : gain pg +%.2f" % gain_pg
        cat = p["category"] if not inverted else ("TOP NEGATIVE FILTERS" if observed == "negative" else p["category"].replace("TOP NEGATIVE FILTERS", "TOP WASH"))
        rows.append({"id": p["id"], "family": p["family"], "category": cat, "source": p["source"], "direction_prespecified": p["direction"],
                     "direction_observed": observed, "inverted": inverted, "n": m2["n"], "days": m2["days"], "clusters": m2["clusters"],
                     "precision_x2": m2.get("precision"), "lift_x2": lift2, "capped_lift_x2": m2.get("capped_lift"), "lift_lb_x2": m2.get("lift_lb"),
                     "precision_x3": m3.get("precision"), "lift_x3": m3.get("lift"), "precision_x5": m5.get("precision"), "lift_x5": m5.get("lift"),
                     "successes_x2": m2["successes"], "failures_x2": m2["failures"], "successes_x3": m3["successes"], "failures_x3": m3["failures"],
                     "coverage": p["coverage"], "trades_per_day": p["expected_trades_per_active_day"],
                     "ev_500_x2": m2.get("ev_500"), "ev_100_x2": m2.get("ev_100"), "ev_500_x3": m3.get("ev_500"),
                     "break_even_x2": be["Y2"], "break_even_x3": be["Y3"],
                     "robustness": "%d/%d" % (rob["checks_passed"], rob["checks_total"]), "robust_share": share,
                     "variants": {v: {tg: (p["variants"][v][tg].get("lift"), p["variants"][v][tg]["n"]) for tg in ("Y2", "Y3")} for v in ("strict", "loose", "cut2")},
                     "halves": {hl: (p["subperiods"]["halves"][hl]["Y2"]["precision"], p["subperiods"]["halves"][hl]["Y2"]["n"]) for hl in ("half1", "half2")},
                     "weeks": p["subperiods"]["weeks"], "families": p["features_families"],
                     "conditions": " AND ".join("%s %s %s" % (c["feature"], {"ge": ">=", "gt": ">", "le": "<=", "lt": "<", "eq": "="}[c["cmp"]], "%.4g" % c["thr"]) for c in p["conditions"]),
                     "rationale": p["rationale"], "fragility": p["fragility"], "new_information": newinfo, "score": score})
    rows.sort(key=lambda r: -r["score"])
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    per_cat = {}
    for c in CATS:
        per_cat[c] = [r["id"] for r in rows if r["category"] == c and r["score"] > 0][:3]
    A.write_json(os.path.join(A.TABLES, "composite_patterns_ranking.json"), {"break_even": be, "per_category_top3": per_cat, "rows": rows})
    L = ["| RANK | PATTERN | FAMILY | N | DAYS | PRECISION_X2 | LIFT_X2 | PRECISION_X3 | LIFT_X3 | PRECISION_X5 | LIFT_X5 | COVERAGE | ROBUSTNESS | ECONOMIC_RATIONALE | NEW_INFORMATION | DISCOVERY_ONLY |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| %d | `%s`%s | %s | %d | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | oui |" % (
            r["rank"], r["id"], " (direction inversée)" if r["inverted"] else "", r["family"], r["n"], r["days"],
            pct(r["precision_x2"]), num(r["lift_x2"]), pct(r["precision_x3"]), num(r["lift_x3"]), pct(r["precision_x5"]), num(r["lift_x5"]),
            pct(r["coverage"], 1), r["robustness"], r["rationale"].replace("|", "/"), r["new_information"].replace("|", "/")))
    L += ["", "## Top 3 par catégorie (DISCOVERY seul, score = lift plafonné ×2 × part des vérifications cohérentes)", ""]
    for c in CATS:
        L.append("- **%s** : %s" % (c, ", ".join("`%s`" % x for x in per_cat[c]) or "aucun pattern avec n ≥ 20 et 5 grappes dans la direction observée"))
    with open(os.path.join(A.TABLES, "composite_patterns_ranking.md"), "w", encoding="utf8") as f:
        f.write("\n".join(L) + "\n")
    for r in rows[:15]:
        print("%2d %-36s %-26s n %3d x2 %s (lift %s, cap %s) x3 %s (lift %s) EV500 %s rob %s %s" % (
            r["rank"], r["id"], r["category"], r["n"], pct(r["precision_x2"]), num(r["lift_x2"]), num(r["capped_lift_x2"]),
            pct(r["precision_x3"]), num(r["lift_x3"]), pct(r["ev_500_x2"]), r["robustness"], "INV" if r["inverted"] else ""))


if __name__ == "__main__":
    main()
