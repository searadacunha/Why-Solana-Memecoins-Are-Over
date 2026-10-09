#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rep_90_report.py -- the ranked list of patterns with the verdict rules of PLAN.md section 10.

Frozen with the selection (check_freeze). Reads only what the earlier stages wrote (candidates,
validation, OOS, robustness, inventory, controls). Writes tables/TOP20.json and tables/TOP20.md.
The verdict is mechanical (ap_mine.tier + the exploitable criteria below); the economic-plausibility
note of each pattern can be completed by hand in tables/plausibility_notes.json ({id: {score, note}}).
"""
from __future__ import annotations

import json
import os

import ap_lib as A
import ap_mine as M

TIER = {"CANDIDAT EXPLOITABLE": 0, "OOS SURVIVOR": 1, "INTERESTING": 2, "REJECTED": 3}
OBS_RANK = ["T0", "ALERT: detector", "ALERT: on-chain", "HISTORY", "ALERT + RPC"]
LEAK_TEXT = {"SAFE": "FAIBLE (audité)", "SAFE_PRIOR_AUDIT": "FAIBLE (table gelée auditée par son étude)",
             "REVIEWED": "FAIBLE (re-dérivé par la revue)", "SAFE_WITH_CAVEAT": "MOYEN (réserve d'audit)",
             "NOT_AUDITED": "NON AUDITÉ", "LEAK": "ÉLEVÉ", "AMBIGUOUS": "ÉLEVÉ", "EXCLUDED_BY_PLAN": "ÉLEVÉ"}
LEAK_ORDER = ["SAFE", "SAFE_PRIOR_AUDIT", "REVIEWED", "SAFE_WITH_CAVEAT", "NOT_AUDITED", "LEAK", "AMBIGUOUS", "EXCLUDED_BY_PLAN"]


def pct(x, nd=1):
    return "n/a" if x is None else ("%." + str(nd) + "f %%") % (100 * x)


def num(x, nd=2):
    return "n/a" if x is None else ("%." + str(nd) + "f") % x


def cell(b):
    if not b or b.get("prec") is None:
        return "n/a"
    s = "%s (%d/%d), base %s, lift %s" % (pct(b["prec"]), b["hits"], b["n"], pct(b["base"]), num(b["lift"]))
    if b.get("mh_lift") is not None:
        s += ", MH %s" % num(b["mh_lift"])
    return s


def main() -> None:
    A.check_freeze()
    cands = {c["id"]: c for c in json.load(open(os.path.join(A.DERIVED, "candidates.json")))["candidates"]}
    val = {c["id"]: c for c in json.load(open(os.path.join(A.TABLES, "validation.json")))}
    oos = {c["id"]: c for c in json.load(open(os.path.join(A.TABLES, "oos.json")))}
    rob = {c["id"]: c for c in json.load(open(os.path.join(A.TABLES, "robustness.json")))["candidates"]}
    inv = {r["feature"]: r for r in json.load(open(os.path.join(A.TABLES, "FEATURE_INVENTORY.json")))}
    ctl = json.load(open(os.path.join(A.CONTROLES, "ctl_00_controls.json")))["summary"]
    null_interesting = ctl.get("NULL", {}).get("interesting_per_run")
    null_runs_interesting = ctl.get("NULL", {}).get("runs_with_interesting")
    null_runs = ctl.get("NULL", {}).get("runs")
    notes_p = os.path.join(A.TABLES, "plausibility_notes.json")
    notes = json.load(open(notes_p)) if os.path.exists(notes_p) else {}
    out = []
    for cid, c in cands.items():
        v, o, r = val[cid]["val"], oos[cid]["oos"], rob[cid]
        val_pass, oos_pass = val[cid]["val_pass"], oos[cid]["oos_pass"]
        feats = [a["feat"] for a in c.get("atoms", [])]
        statuses = [inv[f]["status"] for f in feats]
        leak = any(s in ("LEAK", "AMBIGUOUS", "EXCLUDED_BY_PLAN") for s in statuses)
        b = r["blocks"]
        h = r["hold"]
        verdict = M.tier(val_pass, oos_pass, o, h["lifts_val_oos"], h["p_day"], leak)
        eco = r["economics_hold"]
        k = {"Y2": 2, "Y3": 3, "Y5": 5}[c["target"]]
        main_net = eco["tp%d_next.net_500" % k]
        # exploitable criteria (PLAN section 10), computed only for OOS survivors
        crit = {}
        d_ex = (b["DISC"]["lift"] or 0) - 1
        o_ex = (b["OOS"]["lift"] or 0) - 1
        crit["degradation"] = bool(d_ex > 0 and o_ex >= 0.5 * d_ex) if c["kind"] == "rule" else bool(o_ex > 0)
        crit["thresholds"] = r.get("threshold_status") == "all_above_1"
        wt = r.get("without_top_cluster") or {}
        crit["clusters"] = bool(wt.get("mh_lift") and wt["mh_lift"] > 1 and r["clusters_firing_hold"] >= 5)
        lb = main_net.get("net_lb99") if (main_net.get("net_n") or 0) < 35 else (main_net.get("net_ci") or [None])[0]
        crit["net"] = bool(lb is not None and lb > 0 and (main_net.get("net_clusters") or 0) >= 5
                           and (eco["tp%d_next.net_100" % k].get("net_mean") or -1) > 0
                           and (eco["tp%d_next.net_500_k05" % k].get("net_mean") or -1) > 0)
        crit["frequency"] = r["frequency"]["fires_per_active_day"] >= 2
        crit["no_leak"] = not leak
        if verdict == "OOS SURVIVOR" and all(crit.values()):
            verdict = "CANDIDAT EXPLOITABLE"
        h_ex = (h["mh_lift_blocks"] or 0) - 1
        kept = (h_ex / d_ex) if d_ex > 0 else None
        if c["kind"] != "rule":
            overfit = "ÉLEVÉ (modèle ajusté sur 363 lignes)"
        elif kept is None or kept < 0.25:
            overfit = "ÉLEVÉ"
        elif kept < 0.6 or c["depth"] == 3:
            overfit = "MOYEN"
        else:
            overfit = "FAIBLE"
        obs = [inv[f]["observable_at"] for f in feats]
        latest = max(obs, key=lambda s: max(i for i, p in enumerate(OBS_RANK) if s.startswith(p))) if obs else "ALERT + RPC (toutes les features)"
        worst = max(statuses, key=LEAK_ORDER.index) if statuses else "NOT_AUDITED"
        leak_risk = LEAK_TEXT[worst] + (" : %s" % ", ".join("%s (%s)" % (f, s) for f, s in zip(feats, statuses) if s not in ("SAFE", "SAFE_PRIOR_AUDIT", "REVIEWED")) if worst not in ("SAFE", "SAFE_PRIOR_AUDIT", "REVIEWED") else "")
        if c["kind"] != "rule":
            leak_risk = "MOYEN (le modèle utilise toutes les features gardées, dont celles avec réserve ou non auditées)"
        n_h = h["n"]
        wl = A.wilson(h["hits"], n_h, z=1.2816)[0] if n_h else 0.0
        out.append({
            "id": cid, "target": c["target"], "kind": c["kind"], "definition": c["text"], "depth": c["depth"],
            "families": c["families"], "features": feats,
            "data_needed": sorted({"%s (%s)" % (inv[f]["source"], inv[f]["observable_at"].split(":")[0]) for f in feats}),
            "observable_at": latest,
            "occurrences_hold_all_alerts": r["frequency"]["fires_all_alerts"],
            "blocks": b, "hold": h,
            "validation": {"pass": val_pass, "p": v["p"], "p_fisher": v.get("p_fisher"), "p_boot": v.get("p_boot"), "p_day": v.get("p_day"),
                           "diff_ci": v.get("diff_ci"), "odds_ratio": v.get("odds_ratio"), "recall": v.get("recall"),
                           "clusters": v["n_clusters_fire"], "days": v["n_days_fire"]},
            "oos": {"pass": oos_pass, "confirmatory": o["confirmatory"], "p": o["p"], "p_holm": o.get("p_holm"), "p_day": o.get("p_day"),
                    "diff_ci": o.get("diff_ci"), "odds_ratio": o.get("odds_ratio"), "recall": o.get("recall"),
                    "clusters": o["n_clusters_fire"], "days": o["n_days_fire"]},
            "degradation": {"disc_lift": b["DISC"]["lift"], "sel_lift": b["SEL"]["lift"], "val_lift": b["VAL"]["lift"],
                            "oos_lift": b["OOS"]["lift"], "hold_mh_lift": h["mh_lift_blocks"], "share_of_disc_excess_kept_on_hold": kept},
            "thresholds": {"status": r.get("threshold_status"), "n_tested": r.get("threshold_n_tested"), "n_small": r.get("threshold_n_small"),
                           "n_not_testable": r.get("threshold_n_not_testable"), "min_mh_lift": r.get("threshold_min_mh_lift"),
                           "cutoffs": r.get("cutoffs")},
            "costs": {"net_500": main_net, "net_100": eco["tp%d_next.net_100" % k], "net_1000": eco["tp%d_next.net_1000" % k],
                      "net_500_k05": eco["tp%d_next.net_500_k05" % k], "net_500_k2": eco["tp%d_next.net_500_k2" % k],
                      "touch_500": eco["tp%d_touch.net_500" % k], "sl50_500": eco["tp%d_sl50_next.net_500" % k],
                      "time60_500": eco["time60.net_500"], "time300_500": eco["time300.net_500"],
                      "L15_500": eco.get("L15.tp_next.net_500"), "without_2_best": eco.get("tp_next.net_500_without_2_best"),
                      "net_500_VAL": r.get("net_500_VAL"), "net_500_OOS": r.get("net_500_OOS")},
            "frequency": r["frequency"], "path_hits": r.get("path_hits"), "mae_median_fires": r.get("mae_median_fires"),
            "labels": r["labels"], "weeks_above_base": r["weeks_above_base"],
            "clusters": {"firing_hold": r["clusters_firing_hold"], "days_firing_hold": r.get("days_firing_hold"),
                         "top_share": r.get("top_cluster_share_of_fires"), "without_top": r.get("without_top_cluster")},
            "liquid_only": r["liquid_only"], "premium_terciles": r["premium_terciles"],
            "overfit_risk": overfit, "leak_risk": leak_risk, "feature_statuses": dict(zip(feats, statuses)),
            "plausibility": notes.get(cid, {"score": None, "note": ""}),
            "criteria_exploitable": crit, "verdict": verdict, "_rank": (TIER[verdict], -wl / max(h["base"] or 1e-9, 1e-9)),
        })
    out.sort(key=lambda x: x["_rank"])
    for i, x in enumerate(out):
        x["rank"] = i + 1
        del x["_rank"]
    A.write_json(os.path.join(A.TABLES, "TOP20.json"), {"null_interesting_per_run": null_interesting,
                                                        "null_runs_with_interesting": null_runs_interesting,
                                                        "null_runs": null_runs, "patterns": out})

    L = ["Sous un monde nul (contrôles synthétiques, %s passages), la chaîne produit en moyenne %s candidat(s) INTERESTING par passage "
         "(au moins un dans %s passages sur %s) : ce statut est compatible avec le bruit pur." % (
             null_runs, num(null_interesting), null_runs_interesting, null_runs), "",
         "| # | id | cible | définition | DISC | SEL | VAL | OOS | net 500 $ (VAL+OOS) | verdict |", "|---|---|---|---|---|---|---|---|---|---|"]
    for x in out[:20]:
        n5 = x["costs"]["net_500"]
        L.append("| %d | %s | %s | `%s` | %s | %s | %s | %s | %s (n %s) | %s |" % (
            x["rank"], x["id"], x["target"], x["definition"],
            *["%s (%d), ×%s" % (pct(x["blocks"][b]["prec"], 0), x["blocks"][b]["n"], num(x["blocks"][b]["lift"])) for b in A.BLOCKS],
            pct(n5.get("net_mean")), n5.get("net_n"), x["verdict"]))
    L.append("")
    for x in out[:20]:
        c, n5 = x["costs"], x["costs"]["net_500"]
        th = x["thresholds"]
        L += ["### %d. %s : %s" % (x["rank"], x["id"], x["verdict"]), "",
              "1. Définition exacte : `%s` (cible %s, %d atome(s), familles %s)." % (x["definition"], x["target"], x["depth"], ", ".join(x["families"])),
              "2. Données nécessaires : %s." % ("; ".join(x["data_needed"]) or "toutes les features gardées"),
              "3. Observable : %s." % x["observable_at"],
              "4. Occurrences (lignes avec label) : DISC %d, SEL %d, VAL %d, OOS %d ; %d déclenchements sur toutes les alertes VAL + OOS." % (
                  *[x["blocks"][b]["n"] for b in A.BLOCKS], x["occurrences_hold_all_alerts"]),
              "5. Taux de base : " + ", ".join("%s %s" % (b, pct(x["blocks"][b]["base"])) for b in A.BLOCKS) + ".",
              "6. Lift : " + ", ".join("%s ×%s" % (b, num(x["blocks"][b]["lift"])) for b in A.BLOCKS) +
              " ; VAL + OOS stratifié par bloc ×%s (p stratifié par jour %s, descriptif)." % (num(x["hold"]["mh_lift_blocks"]), num(x["hold"]["p_day"], 3)),
              "7. Discovery : %s. Selection : %s." % (cell(x["blocks"]["DISC"]), cell(x["blocks"]["SEL"])),
              "8. Validation : %s ; p %s (Fisher %s, bootstrap de grappes %s, CMH par jour %s) ; %d grappes, %d jours ; écart règle moins reste IC 95 %% [%s, %s] ; odds ratio %s ; rappel %s ; %s." % (
                  cell(x["blocks"]["VAL"]), num(x["validation"]["p"], 3), num(x["validation"]["p_fisher"], 3), num(x["validation"]["p_boot"], 4),
                  num(x["validation"]["p_day"], 3), x["validation"]["clusters"], x["validation"]["days"],
                  *[pct(z) for z in (x["validation"]["diff_ci"] or [None, None])], num(x["validation"]["odds_ratio"]), pct(x["validation"]["recall"]),
                  "PASSE" if x["validation"]["pass"] else "échoue"),
              "9. OOS : %s ; p %s%s (CMH par jour %s) ; %d grappes, %d jours ; écart IC 95 %% [%s, %s] ; odds ratio %s ; rappel %s ; %s. Part de l'excès DISCOVERY conservée sur VAL + OOS : %s." % (
                  cell(x["blocks"]["OOS"]), num(x["oos"]["p"], 3),
                  (", Holm %s" % num(x["oos"]["p_holm"], 3)) if x["oos"]["p_holm"] is not None else "", num(x["oos"]["p_day"], 3),
                  x["oos"]["clusters"], x["oos"]["days"],
                  *[pct(z) for z in (x["oos"]["diff_ci"] or [None, None])], num(x["oos"]["odds_ratio"]), pct(x["oos"]["recall"]),
                  ("PASSE" if x["oos"]["pass"] else "échoue") if x["oos"]["confirmatory"] else "lecture descriptive (n'a pas passé VALIDATION)",
                  pct(x["degradation"]["share_of_disc_excess_kept_on_hold"], 0)),
              "10. Stabilité des seuils : %s (%s voisins testés, %s trop petits, %s non testables ; lift MH minimal des voisins testés %s). Coupures − 2 s / − 5 s : %s. Semaines au-dessus du taux de base : %s. Sans la grappe dominante : %s (%d grappes sur %d jours, la première pèse %s des déclenchements)." % (
                  {"all_above_1": "tous les voisins testés gardent un lift > 1", "fails": "au moins un voisin testé retombe à un lift ≤ 1",
                   "not_testable": "non mesurable (aucun voisin testable)"}.get(th["status"], str(th["status"])),
                  th["n_tested"], th["n_small"], th["n_not_testable"], num(th["min_mh_lift"]),
                  "non testables" if th["cutoffs"] == "not_testable" else "; ".join("%s MH %s (mêmes déclenchements %s)" % (kv, num(vv["mh_lift"]), pct(vv["same_fires_share"], 0)) for kv, vv in (th["cutoffs"] or {}).items()),
                  x["weeks_above_base"], cell(x["clusters"]["without_top"]),
                  x["clusters"]["firing_hold"], x["clusters"]["days_firing_hold"] or 0, pct(x["clusters"]["top_share"], 0)),
              "11. Coûts et rendement conditionnel (VAL + OOS, trade déclaré d'avance ; mesuré sur les blocs qui ont retenu la règle, donc biaisé vers le haut d'environ 9 à 14 points par trade d'après les contrôles) : net moyen %s à 500 $, IC 95 %% [%s, %s], borne basse 99 %% %s, %s de trades gagnants, n %s (%s censurés, %s grappes) ; %s à 100 $ ; %s à 1 000 $ ; K ×0,5 : %s ; sortie au toucher : %s ; stop − 50 %% : %s ; sortie à 60 s : %s ; entrée + 15 s : %s ; sans les 2 meilleurs trades : %s. Toutes alertes confondues : %s." % (
                  pct(n5.get("net_mean")), *[pct(z) for z in (n5.get("net_ci") or [None, None])], pct(n5.get("net_lb99")), pct(n5.get("net_win_share"), 0),
                  n5.get("net_n"), n5.get("net_censored"), n5.get("net_clusters"),
                  pct(c["net_100"].get("net_mean")), pct(c["net_1000"].get("net_mean")), pct(c["net_500_k05"].get("net_mean")),
                  pct(c["touch_500"].get("net_mean")), pct(c["sl50_500"].get("net_mean")), pct(c["time60_500"].get("net_mean")),
                  pct((c["L15_500"] or {}).get("net_mean")), pct(c["without_2_best"]), pct(n5.get("net_mean_all_alerts"))),
              "12. Fréquence : %.1f signaux par jour d'activité du détecteur (%s des alertes)." % (
                  x["frequency"]["fires_per_active_day"], pct(x["frequency"]["share"])),
              "13. Risque d'overfitting : %s." % x["overfit_risk"],
              "14. Risque de fuite : %s." % x["leak_risk"],
              "15. Plausibilité économique : %s. %s" % (
                  ("%s/5" % x["plausibility"]["score"]) if x["plausibility"].get("score") is not None else "non notée", x["plausibility"].get("note", "")),
              "16. Verdict : **%s**. Critères « exploitable » : %s." % (
                  x["verdict"], ", ".join("%s %s" % (k2, "oui" if v2 else "non") for k2, v2 in x["criteria_exploitable"].items())),
              ""]
        if x.get("path_hits"):
            p = x["path_hits"]
            L.insert(-1, "    Chemin des gagnants (VAL + OOS, n %d) : cible atteinte en %.0f s en médiane (90e centile %.0f s), creux médian avant la cible ×%.2f du prix d'entrée (10e centile ×%.2f)." % (
                p["n"], p["t_hit_median_s"], p["t_hit_p90_s"], p["low_before_median"], p["low_before_p10"]))
    with open(os.path.join(A.TABLES, "TOP20.md"), "w", encoding="utf8") as f:
        f.write("\n".join(L) + "\n")
    from collections import Counter
    print(dict(Counter(x["verdict"] for x in out)))
    for x in out[:20]:
        print("%2d %-8s %-22s hold MH x%s  net500 %s  %s" % (x["rank"], x["id"], x["verdict"], num(x["hold"]["mh_lift_blocks"]),
                                                            pct(x["costs"]["net_500"].get("net_mean")), x["definition"][:90]))


if __name__ == "__main__":
    main()
