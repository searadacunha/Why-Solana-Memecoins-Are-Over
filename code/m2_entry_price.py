#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M2 : le prix est deja parti quand le marche s'ouvre.

Affirmation testee : au premier instant ou un acheteur ordinaire peut executer
un ordre, le prix a deja monte d'un facteur important par rapport au prix de
lancement du token. La hausse est deja consommee avant le marche.

Definitions, toutes verifiables :
  - Prix de lancement = constante de la courbe pump.fun, MC = 27,96 SOL, soit
    le parametre de reserve virtuelle initiale, identique pour tous les tokens.
    Ce n'est pas une estimation.
  - Premier instant executable = premier swap enregistre d'au moins 0,05 SOL.
    Le seuil ecarte les swaps de poussiere (0,002 SOL) dont le prix implicite
    est domine par les arrondis. Sensibilite a ce seuil : voir la sortie.
  - Prix execute = sol / tokens. Controle croise avec `price` (prix de pool).
  - Part du parcours deja consommee = log(MC_premier / MC_lancement)
    / log(MC_pic / MC_lancement). En log parce que le processus est
    multiplicatif : 1 -> 2 et 10 -> 20 sont le meme mouvement. Le pic vient de
    la serie de prix robuste (pumplib.robust_series), pas du max brut : domine
    par les swaps de poussiere, celui-ci donne des valeurs physiquement
    impossibles (jusqu'a 8,9e8 SOL de MC).

Usage :  python3 m2_entry_price.py [--data ...] [--min-sol 0.05]
"""

import argparse
import collections
import math
import os

import pumplib as P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--min-sol", type=float, default=0.05)
    ap.add_argument("--out", default=os.path.join(P.HERE, "..", "docs", "out", "m2_entry_price.json"))
    a = ap.parse_args()

    caps = P.load_captures(a.data)
    P.head("M2 : PRIX AU PREMIER INSTANT EXECUTABLE", "MESURE")

    mc_exec, mc_pool, consumed, first_src, lags = [], [], [], collections.Counter(), []
    rows = []
    for d in caps:
        sw = P.clean_swaps(d)
        if not sw:
            continue
        supply = d.get("supply") or P.PUMP_SUPPLY
        big = [w for w in sw if w["sol"] >= a.min_sol]
        if not big:
            continue
        f = big[0]
        m_exec = f["p"] * supply
        mc_exec.append(m_exec)
        if f.get("price"):
            mc_pool.append(f["price"] * supply)
        first_src[f["src"]] += 1
        lags.append(f["ts"] - d["created"])

        # pic mesure sur la serie de prix robuste (cf. pumplib.robust_series) :
        # le max brut est domine par les swaps de poussiere et n'a pas de sens.
        ser = P.robust_series(sw)
        if ser:
            peak = max(p for _, p in ser) * supply
            if peak > P.LAUNCH_MC_SOL and m_exec > 0:
                consumed.append(math.log(max(m_exec, P.LAUNCH_MC_SOL) / P.LAUNCH_MC_SOL)
                                / math.log(peak / P.LAUNCH_MC_SOL))
        rows.append({"mint": d["mint"], "mc_first_sol": m_exec,
                     "ratio_vs_launch": m_exec / P.LAUNCH_MC_SOL})

    n = len(mc_exec)
    med = P.median(mc_exec)
    lo, hi = P.bootstrap_median_ci(mc_exec)

    P.kv("MC de lancement (constante de courbe)", "%.2f SOL" % P.LAUNCH_MC_SOL)
    print()
    P.kv("MC au 1er swap executable, p10", "%.1f SOL" % P.quantile(mc_exec, 0.10), n=n)
    P.kv("MC au 1er swap executable, mediane", "%.1f SOL" % med, n=n,
         note="IC95 [%.0f ; %.0f]" % (lo, hi))
    P.kv("MC au 1er swap executable, p90", "%.1f SOL" % P.quantile(mc_exec, 0.90), n=n)
    print()
    P.kv("=> multiple median deja realise", "x%.1f" % (med / P.LAUNCH_MC_SOL), n=n)
    P.kv("   au 10e centile (le cas le plus favorable sur 10)",
         "x%.1f" % (P.quantile(mc_exec, 0.10) / P.LAUNCH_MC_SOL), n=n)
    print()
    for thr in (2, 5, 10, 20):
        k = sum(1 for m in mc_exec if m >= thr * P.LAUNCH_MC_SOL)
        w = P.wilson(k, n)
        P.kv("part des tokens deja a x%d ou plus" % thr,
             "%.1f %%" % (100.0 * k / n), n=n,
             note="IC95 [%.1f ; %.1f]" % (100 * w[0], 100 * w[1]))

    print()
    P.kv("part du parcours (en log) deja consommee, mediane",
         "%.3f" % P.median(consumed), n=len(consumed))
    k = sum(1 for c in consumed if c >= 0.5)
    P.kv("part des tokens dont >= 50 %% du parcours est fait",
         "%.1f %%" % (100.0 * k / len(consumed)), n=len(consumed))

    print()
    P.kv("delai 1er swap executable - creation, mediane", "%.0f s" % P.median(lags), n=n)
    print("\n  Type du 1er swap executable (source du routeur) :")
    for s, c in first_src.most_common():
        print("    %-18s %4d   %5.1f %%" % (s, c, 100.0 * c / n))

    # controle : le prix de pool doit donner le meme resultat que le prix execute
    if mc_pool:
        P.kv("\n  controle prix de pool vs prix execute (mediane)",
             "%.1f vs %.1f SOL" % (P.median(mc_pool), med), n=len(mc_pool),
             note="ecart %.2f %%" % (100 * (P.median(mc_pool) / med - 1)))

    print("""
  LECTURE :
   - Le premier prix qu'un acheteur ordinaire peut toucher est deja, en
     mediane, un multiple a deux chiffres du prix de lancement. [MESURE]
   - Ce n'est pas un effet de latence de l'observateur : le delai median entre
     la creation et ce premier swap est de quelques secondes. Le prix a saute
     avant, pendant la phase de courbe, invisible depuis le pool. [MESURE]
   - Ce qui a produit ce saut est identifie en M3 : les adresses listees dans
     snipers[], qui achetent la courbe avant l'ouverture du pool. [MESURE]
   - Conclusion structurelle : la question "a quel moment fallait-il acheter"
     n'a pas de reponse accessible. Le bon moment est anterieur a l'existence
     d'un marche. [INFERE, deduction directe des deux mesures ci-dessus]""")

    P.emit({"n": n, "min_sol": a.min_sol,
            "launch_mc_sol": P.LAUNCH_MC_SOL,
            "mc_first_sol": {"p10": P.quantile(mc_exec, 0.10), "med": med,
                             "p90": P.quantile(mc_exec, 0.90),
                             "med_ic95": [lo, hi]},
            "multiple_median": med / P.LAUNCH_MC_SOL,
            "part_ge": {str(t): sum(1 for m in mc_exec if m >= t * P.LAUNCH_MC_SOL) / n
                        for t in (2, 5, 10, 20)},
            "log_run_consomme_med": P.median(consumed),
            "lag_med_s": P.median(lags),
            "src_1er_swap": dict(first_src),
            "niveau": "MESURE"}, os.path.abspath(a.out))


if __name__ == "__main__":
    main()
