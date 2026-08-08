#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La signature d'ouverture de courbe sur les gros tokens (ATH >= 500 k$).

Question : quand un token pump.fun atteint une capitalisation elevee, sa courbe
a-t-elle ete rachetee en bloc dans le slot de creation ?

Ce script ne fait AUCUN appel reseau : il recompte sur l'echantillon gele
data/v09_signature_gros_tokens.json (n = 70, fige le 2026-07-29). La collecte
on-chain qui l'a produit lit les premieres signatures de la bonding-curve PDA
de chaque mint et mesure le SOL engage dans les 30 premieres secondes.

Le script imprime aussi les deux controles qui limitent la portee du chiffre :
l'echantillon n'est pas aleatoire, et les tokens SANS la signature ont un ATH
median PLUS ELEVE que ceux qui l'ont.

  python3 code/f_signature_gros_tokens.py
"""

import json
import math
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "data", "v09_signature_gros_tokens.json")


def wilson(k, n, z=1.96):
    """IC95 de Wilson en pourcentage. L'intervalle est defini une seule fois
    dans statlib.wilson ; on ne fait ici que le passer en pourcentage."""
    from statlib import wilson as _wilson_frac
    lo, hi = _wilson_frac(k, n, z)
    if lo is None:
        return (0.0, 0.0)
    return (100 * lo, 100 * hi)


def main():
    with open(SRC, encoding="utf-8") as fh:
        doc = json.load(fh)
    rows = doc["tokens"]
    n = len(rows)

    avec = [r for r in rows if r["snipe_in_first_slot"]]
    sans = [r for r in rows if not r["snipe_in_first_slot"]]
    k = len(avec)
    lo, hi = wilson(k, n)

    print(f"Echantillon gele le {doc['gele_le']} : n = {n} tokens ATH >= 500 k$")
    print(f"ATH median de la population : {st.median([r['ath_usd'] for r in rows]):,.0f} $"
          .replace(",", " "))
    print()
    print(f"Courbe rachetee (>= 60 SOL) DANS LE SLOT DE CREATION : {k}/{n} = "
          f"{100*k/n:.1f} %  IC95 Wilson [{lo:.1f} ; {hi:.1f}]")

    # Le fait le plus net : les deux definitions coincident exactement.
    accord = sum(1 for r in rows if r["full_snipe"] == r["snipe_in_first_slot"])
    print(f"Accord 'rachat en 30 s' vs 'rachat dans le slot de creation' : {accord}/{n}")
    print("  -> quand la courbe est rachetee dans les 30 s, elle l'est entierement")
    print("     dans le slot de creation. Il n'y a pas de fenetre intermediaire.")
    print()

    sol = [r["sol_first_slot"] for r in avec]
    ach = [r["n_buyers_first_slot"] for r in avec]
    print(f"SOL engage dans le slot de creation : mediane {st.median(sol):.2f}"
          f"  (min {min(sol):.2f} / max {max(sol):.2f})")
    print(f"Acheteurs dans ce slot : mediane {st.median(ach):.0f}"
          f"  (min {min(ach)} / max {max(ach)})")
    print()

    print("--- CONTROLES QUI LIMITENT LA PORTEE DU CHIFFRE ---")
    print(f"1. Echantillonnage : {doc['definition']['echantillonnage']}")
    print("2. La signature ne 'fait' pas les gros tokens. Parmi ces memes 70 :")
    print(f"     ATH median AVEC signature ({len(avec)}) : "
          f"{st.median([r['ath_usd'] for r in avec]):,.0f} $".replace(",", " "))
    print(f"     ATH median SANS signature ({len(sans)}) : "
          f"{st.median([r['ath_usd'] for r in sans]):,.0f} $".replace(",", " "))
    print("   Les tokens SANS la signature montent PLUS HAUT. La signature decrit")
    print("   comment un lancement demarre, elle ne predit pas jusqu'ou il ira.")
    print("3. Population conditionnee sur le SUCCES (ATH >= 500 k$) : ce taux ne dit")
    print("   RIEN de la proportion de lancements snipes dans le flux general, ni de")
    print("   la probabilite qu'un lancement snipe reussisse. C'est P(signature|gros),")
    print("   pas P(gros|signature).")


if __name__ == "__main__":
    main()
