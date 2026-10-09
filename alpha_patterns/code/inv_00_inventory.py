#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inv_00_inventory.py -- inventory of every available feature and of when it is knowable.

For each column of the feature matrix: source table, family, earliest moment it is observable,
causal status after the blind audit (audit/causality_findings.json), calendar availability
(first and last alert with a value, share of non-missing values per block), number of distinct
values, and which earlier study already tested it. Writes the exclusion list used by the mining:
LEAK and AMBIGUOUS features are excluded, SAFE_WITH_CAVEAT ones are kept and annotated.
No outcome is read.
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter, defaultdict

import numpy as np

import ap_data as D
import ap_lib as A


# excluded by the plan (statistics review): five weeks of alerts cannot identify a weekday effect,
# and a day-of-week atom is tested on a handful of days, not on hundreds of alerts
PLAN_EXCLUDED = {k: "day-of-week / weekend indicator: five weeks cannot identify a weekday effect (plan, 2026-10-06)"
                 for k in ("c_dow", "lv_dow", "reg_weekend")}


def main() -> None:
    mx = D.load_matrix()
    X, names, meta, blocks, t = mx["X"], mx["names"], mx["meta"], mx["blocks"], mx["t"]
    aud = json.load(open(os.path.join(A.STUDY, "audit", "causality_findings.json")))
    flagged = {}
    for f in aud["flagged"]:
        flagged.setdefault(f["feature"], f)
    unknown = sorted(k for k in flagged if k not in names)
    bad = [k for k in unknown if flagged[k]["status"] in ("LEAK", "AMBIGUOUS")
           and not (k.startswith("miss__") and k[6:] in flagged and flagged[k[6:]]["status"] in ("LEAK", "AMBIGUOUS"))]
    if bad:
        raise RuntimeError("LEAK / AMBIGUOUS feature names absent from the matrix (misspelt?): %s" % bad)
    # audit coverage: the blind causality audit (workflow 1) read the signal_search and pd columns; the
    # frozen fA / ez / sc / kg tables were audited by their own studies; the leakage review of this
    # study re-derived the h1 wallet / creator / config / regime features; lv, x and the funder and
    # early-buyer h1 keys were not audited by anyone.
    def default_status(k, src):
        if src.startswith("ss_") or src == "pd":
            return "SAFE"
        if src in ("fA", "ez", "sc", "kg"):
            return "SAFE_PRIOR_AUDIT"
        if src == "h1":
            return "NOT_AUDITED" if (k.endswith("_f") or k.startswith("h1_e_")) else "REVIEWED"
        return "NOT_AUDITED"
    rows, excluded, no_missing = [], {}, set()
    for j, k in enumerate(names):
        x = X[:, j]
        ok = ~np.isnan(x)
        fl = flagged.get(k)
        status = fl["status"] if fl else default_status(k, meta[k]["source"])
        if fl and fl.get("decision"):
            status = fl["decision"]
        if k in PLAN_EXCLUDED:
            status, fl = "EXCLUDED_BY_PLAN", {"reason": PLAN_EXCLUDED[k]}
        if status in ("LEAK", "AMBIGUOUS", "EXCLUDED_BY_PLAN"):
            excluded[k] = fl["reason"]
        if status in ("SAFE_WITH_CAVEAT", "NOT_AUDITED"):
            no_missing.add(k)
        rows.append({
            "feature": k, "source": meta[k]["source"], "family": meta[k]["family"],
            "user_family": meta[k]["user_family"], "observable_at": meta[k]["observable_at"], "status": status,
            "note": (fl or {}).get("reason", ""),
            "first_utc": time.strftime("%Y-%m-%d", time.gmtime(t[ok].min())) if ok.any() else None,
            "last_utc": time.strftime("%Y-%m-%d", time.gmtime(t[ok].max())) if ok.any() else None,
            "coverage": {b: round(float(ok[blocks == b].mean()), 3) for b in A.BLOCKS},
            "n_distinct": int(len(np.unique(x[ok]))),
            "already_tested_by": meta[k]["already_tested_by"]})
    A.write_json(os.path.join(A.DERIVED, "feature_exclusions.json"),
                 {"excluded": sorted(excluded), "reasons": excluded, "flagged_not_in_matrix": unknown,
                  "no_missing_atom": sorted(no_missing - set(excluded))})
    A.write_json(os.path.join(A.TABLES, "FEATURE_INVENTORY.json"), rows)

    by_fam = defaultdict(list)
    for r in rows:
        by_fam[r["user_family"]].append(r)
    L = ["# Inventaire des features disponibles et de leur disponibilité temporelle", "",
         "Généré par `code/inv_00_inventory.py`. %d features sur les 1 657 alertes du snapshot "
         "(2026-08-21 17:35 → 2026-09-29 10:47 UTC). Aucune issue n'est lue ici." % len(rows), "",
         "## Résumé", "",
         "| famille | features | exclues (fuite ou ambiguë) | avec réserve | couverture médiane DISC / SEL / VAL / OOS |",
         "|---|---|---|---|---|"]
    for fam in sorted(by_fam):
        rr = by_fam[fam]
        med = [np.median([r["coverage"][b] for r in rr]) for b in A.BLOCKS]
        L.append("| %s | %d | %d | %d | %s |" % (
            fam, len(rr), sum(1 for r in rr if r["status"] in ("LEAK", "AMBIGUOUS")),
            sum(1 for r in rr if r["status"] == "SAFE_WITH_CAVEAT"), " / ".join("%.0f %%" % (100 * m) for m in med)))
    L += ["", "## Moment où la valeur devient observable", "", "| moment | features |", "|---|---|"]
    for k, v in sorted(Counter(r["observable_at"] for r in rows).items()):
        L.append("| %s | %d |" % (k, v))
    L += ["", "## Sources", "", "| source | features | table |", "|---|---|---|"]
    src_doc = {"fA": "post_detection_forensics analytic_table, coupure alerte − 1 s (gelée)",
               "ez": "entry_zone ez_table f['D'] (gelée)", "sc": "sniper_capital sc_table (gelée)",
               "kg": "known_group_reentry kg_features (gelée)", "lv": "détecteur en direct, post_detection_edge f (gelée)",
               "pd": "pattern_discovery pd_table (non gelée, auditée ici)", "h1": "cette étude, feat_20_history.py",
               "ss_bundle_sizing": "signal_search", "ss_early_flow": "signal_search", "ss_funding": "signal_search",
               "ss_history": "signal_search", "ss_slot0": "signal_search"}
    for k, v in sorted(Counter(r["source"] for r in rows).items()):
        L.append("| %s | %d | %s |" % (k, v, src_doc.get(k, "")))
    L += ["", "## Features exclues avant toute lecture de label", ""]
    if excluded:
        L += ["| feature | statut | raison |", "|---|---|---|"]
        for r in rows:
            if r["feature"] in excluded:
                L.append("| `%s` | %s | %s |" % (r["feature"], r["status"], r["note"].replace("|", "/")))
    else:
        L.append("Aucune.")
    L += ["", "## Statuts", "", "| statut | features | sens |", "|---|---|---|"]
    sens = {"SAFE": "audité à l'aveugle le 05/10 (signal_search, pattern_discovery), rien à signaler",
            "SAFE_WITH_CAVEAT": "audité, réserve notée ci-dessous ; pas d'atome « manquante »",
            "SAFE_PRIOR_AUDIT": "table gelée auditée par sa propre étude (forensics, entry_zone, sniper_capital, known_group)",
            "REVIEWED": "cette étude, re-dérivé indépendamment par la revue du 05/10",
            "NOT_AUDITED": "personne ne l'a audité (détecteur en direct, features dérivées, clés funder et early de l'historique) ; pas d'atome « manquante »",
            "LEAK": "exclue", "AMBIGUOUS": "exclue", "EXCLUDED_BY_PLAN": "exclue par le plan"}
    for k, v in sorted(Counter(r["status"] for r in rows).items()):
        L.append("| %s | %d | %s |" % (k, v, sens.get(k, "")))
    L += ["", "La cotation SOL/USD de `p_log_mc_usd`, `ez_log_mc_usd`, `ez_mc_usd` est la clôture de l'heure PRÉCÉDENTE "
          "(vérifié le 06/10 contre sol_usd_hourly.json, écart 2e-7) : causale, gardée. Les jumelles lv_ (heure courante) sont retirées.",
          "", "## Features gardées avec réserve", "", "| feature | réserve |", "|---|---|"]
    for r in rows:
        if r["status"] == "SAFE_WITH_CAVEAT":
            L.append("| `%s` | %s |" % (r["feature"], r["note"].replace("|", "/")))
    if aud.get("defects"):
        L += ["", "## Défauts relevés par l'audit", ""] + ["- " + d for d in aud["defects"]]
    L += ["", "## Détail par famille", ""]
    for fam in sorted(by_fam):
        L += ["### %s" % fam, "", "| feature | source | observable | statut | couverture D/S/V/O | valeurs distinctes | déjà testée par |",
              "|---|---|---|---|---|---|---|"]
        for r in by_fam[fam]:
            L.append("| `%s` | %s | %s | %s | %s | %d | %s |" % (
                r["feature"], r["source"], r["observable_at"].split(":")[0], r["status"],
                "/".join("%.0f" % (100 * r["coverage"][b]) for b in A.BLOCKS), r["n_distinct"],
                ", ".join(r["already_tested_by"]) or "-"))
        L.append("")
    with open(os.path.join(A.TABLES, "FEATURE_INVENTORY.md"), "w", encoding="utf8") as f:
        f.write("\n".join(L) + "\n")
    print("features %d, excluded %d, with caveat %d, flagged but absent from the matrix %d" % (
        len(rows), len(excluded), sum(1 for r in rows if r["status"] == "SAFE_WITH_CAVEAT"), len(unknown)))


if __name__ == "__main__":
    main()
