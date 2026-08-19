#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tableau 2 : probabilite d'un x2 selon le prix d'entree.

Panneau A (principal), contrefactuel de prix. Le lot de tokens est fixe, seul
varie le parametre que l'acheteur ne choisit pas, le prix auquel il peut
entrer : x2(P) = part des tokens dont l'ATH pump.fun atteint au moins 2 x P,
soit la fonction de survie des ATH reparametree, x2(P) = P(ATH >= 2P), sans
degre de liberte, sans filtre et sans modele. Le prix P_90 tel que
x2(P_90) = 90 % vaut par construction le 10e percentile des ATH divise par 2.

Panneau B (controle), bandes de prix reellement observees. Meme mesure,
restreinte aux tokens effectivement detectes dans la bande. Le taux de x2 y est
quasi plat (42-58 % de 20k a 300k), ce qui bloque une lecture abusive du
panneau A : les tokens qui apparaissent bas sont aussi ceux dont l'ATH est bas.
Le panneau A porte sur le prix paye pour un token donne, pas sur une
superiorite des tokens achetes bas.

Trois avertissements, repris en pied de tableau :
 1. Borne superieure de la chance de doubler, pas un PnL : atteindre l'ATH
    n'est pas vendre a l'ATH. Le PnL executable est au tableau 1, negatif.
 2. mc est au denominateur : artefact de denominateur assume et mesure
    (elasticite log-log publiee).
 3. La colonne << x2 devant soi >> (panneau B) exige en plus que l'ATH survienne
    au moins 60 s apres la detection.

Population : socle B (fast-grad) propre, soit regime MC sain
(2026-06-27..2026-07-18), 5 000 < detect_mc < 300 000 et ATH connu.
Sensibilite sur B entier publiee.

Usage : python3 code/t2_x2_par_prix_entree.py
Sorties : docs/tables/T2a_x2_contrefactuel.md, docs/tables/T2b_x2_bandes.md,
          data/t2_x2_par_prix_entree.json
"""
import collections
import json
import math
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, dump_json, load_socle, wilson, write_table  # noqa: E402

PRIX = [16000, 20000, 23000, 25000, 30000, 40000, 47000, 50000,
        65000, 85000, 100000, 120000, 150000]
BANDS = [(5000, 20000), (20000, 30000), (30000, 40000), (40000, 50000),
         (50000, 65000), (65000, 85000), (85000, 100000), (100000, 120000),
         (120000, 300000)]


def clean_B(d):
    return [r for r in d["B"]
            if r.get("q_mc_regime_ok") and r.get("q_mc_plausible")
            and r.get("o_ath_true") and (r.get("detect_mc") or 0) > 0]


def elasticity(rows):
    """OLS de log10(ATH) sur log10(mc), demeanee par jour (methode du socle)."""
    byday = collections.defaultdict(list)
    for r in rows:
        byday[r["day"]].append(r)
    xs, ys = [], []
    for _, rr in byday.items():
        if len(rr) < 2:
            continue
        mx = st.mean([math.log10(r["detect_mc"]) for r in rr])
        my = st.mean([math.log10(r["o_ath_true"]) for r in rr])
        for r in rr:
            xs.append(math.log10(r["detect_mc"]) - mx)
            ys.append(math.log10(r["o_ath_true"]) - my)
    sxx = sum(x * x for x in xs)
    return (sum(x * y for x, y in zip(xs, ys)) / sxx) if sxx else None


def survie(rows, P, mult=2):
    k = sum(1 for r in rows if r["o_ath_true"] >= mult * P)
    return k, len(rows)


def main():
    d = load_socle()
    rows = clean_B(d)
    allB = [r for r in d["B"] if r.get("o_ath_true")]
    ndays = len({r["day"] for r in rows})
    nclu = len({r["cluster_id"] for r in rows})
    print(f"B propre : n={len(rows)} tokens, {nclu} clusters, {ndays} jours "
          f"| B entier avec ATH : n={len(allB)}")

    # ---------------- panneau A : contrefactuel de prix
    A, tabA = [], []
    for P in PRIX:
        k2, n = survie(rows, P, 2)
        k3, _ = survie(rows, P, 3)
        k5, _ = survie(rows, P, 5)
        ka, na = survie(allB, P, 2)
        lo, hi = wilson(k2, n)
        A.append({"prix_usd": P, "n": n, "x2_pct": round(100 * k2 / n, 1),
                  "x2_ic95": [round(100 * lo, 1), round(100 * hi, 1)],
                  "x3_pct": round(100 * k3 / n, 1),
                  "x5_pct": round(100 * k5 / n, 1),
                  "x2_pct_B_entier": round(100 * ka / na, 1)})
        tabA.append([f"{P:,}".replace(",", " "), n, f"{100*k2/n:.1f}",
                     f"[{100*lo:.1f}, {100*hi:.1f}]", f"{100*k3/n:.1f}",
                     f"{100*k5/n:.1f}", f"{100*ka/na:.1f}"])

    ath = sorted(r["o_ath_true"] for r in rows)
    p90 = ath[int(round(0.10 * len(ath)))] / 2.0
    ath_all = sorted(r["o_ath_true"] for r in allB)
    p90_all = ath_all[int(round(0.10 * len(ath_all)))] / 2.0
    el = elasticity(rows)

    write_table(
        "T2a_x2_contrefactuel",
        ["entry price USD", "n", "x2 %", "95% CI %", "x3 %", "x5 %",
         "x2 % (all of B, n={})".format(len(allB))],
        tabA,
        ["",
         f"n = {len(rows)} tokens | {nclu} clusters | {ndays} UTC days | clean population B.",
         "x2(P) = share of tokens whose pump.fun ATH >= 2 x P. Survival function "
         "of the ATHs: no free parameter.",
         f"**Entry price that yields a 90 % x2 rate: {p90:,.0f} USD** "
         f"(= 10th percentile of ATHs / 2; {p90_all:,.0f} USD on all of B)."
         .replace(",", " "),
         "An upper bound: reaching the ATH is not selling at the ATH.",
         "", "Regenerate: `python3 code/t2_x2_par_prix_entree.py`"])

    # ---------------- panneau B : bandes observees
    Bp, tabB = [], []
    for lo_, hi_ in BANDS:
        sub = [r for r in rows if lo_ <= r["detect_mc"] < hi_]
        if len(sub) < 5:
            continue
        n = len(sub)
        k2 = sum(1 for r in sub if r["o_ath_true"] >= 2 * r["detect_mc"])
        k2b = sum(1 for r in sub if r["o_ath_true"] >= 2 * r["detect_mc"]
                  and r.get("o_ath_ts") and r.get("detect_ts")
                  and r["o_ath_ts"] >= r["detect_ts"] + 60)
        lo95, hi95 = wilson(k2, n)
        rec = {"bande": f"{lo_//1000}k-{hi_//1000}k", "n": n,
               "x2_pct": round(100 * k2 / n, 1),
               "x2_ic95": [round(100 * lo95, 1), round(100 * hi95, 1)],
               "x2_devant_soi_pct": round(100 * k2b / n, 1),
               "mc_median": round(st.median([r["detect_mc"] for r in sub])),
               "ath_median": round(st.median([r["o_ath_true"] for r in sub]))}
        Bp.append(rec)
        tabB.append([rec["bande"], n, f"{rec['mc_median']:,}".replace(",", " "),
                     f"{rec['ath_median']:,}".replace(",", " "),
                     f"{rec['x2_pct']:.1f}",
                     f"[{rec['x2_ic95'][0]:.1f}, {rec['x2_ic95'][1]:.1f}]",
                     f"{rec['x2_devant_soi_pct']:.1f}"])

    write_table(
        "T2b_x2_bandes",
        ["detected MC band", "n", "median MC", "median ATH", "x2 %", "95% CI %",
         "x2 ahead %"],
        tabB,
        ["",
         f"n = {len(rows)} tokens | {nclu} clusters | {ndays} UTC days | clean population B.",
         "Here the denominator is the price actually observed at detection. The x2 "
         "rate is nearly flat: tokens that appear low also have a low ATH.",
         f"Elasticity log10(ATH) ~ log10(mc), demeaned by day: **b = {el:.3f}** "
         f"(n={len(rows)}). b < 1 => entering higher genuinely degrades the multiple.",
         "Limit (added on review): b is published without SE/CI; measurement error on "
         "the entry MC (errors-in-variables) pulls the slope below 1; and the nearly "
         "flat x2 rate of this panel is in tension with a causal reading. Mechanical "
         "decomposition: measured. Economic claim: indicative, NON ETABLI.",
         "`x2 ahead` = x2 and the ATH occurring >= 60 s after detection.",
         "", "Regenerate: `python3 code/t2_x2_par_prix_entree.py`"])

    dump_json({"n": len(rows), "n_clusters": nclu, "n_jours": ndays,
               "n_B_entier": len(allB),
               "elasticite_logath_logmc": el,
               "prix_pour_90pct_x2_usd": p90,
               "prix_pour_90pct_x2_usd_B_entier": p90_all,
               "panneau_A_contrefactuel": A, "panneau_B_bandes": Bp},
              os.path.join(DATA, "t2_x2_par_prix_entree.json"))

    print(open(os.path.join(os.path.dirname(DATA), "docs", "tables",
                            "T2a_x2_contrefactuel.md")).read())
    print(open(os.path.join(os.path.dirname(DATA), "docs", "tables",
                            "T2b_x2_bandes.md")).read())


if __name__ == "__main__":
    main()
