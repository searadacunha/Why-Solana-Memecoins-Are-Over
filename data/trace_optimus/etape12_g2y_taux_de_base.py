#!/usr/bin/env python3
"""Etape 12 : le lien avec G2Y est-il specifique a la cible, ou banal ?

Lit un ou plusieurs e9_origine_*.json, ecrit e12_g2y_taux_de_base.json.

Question posee : « les portefeuilles qui achetent en premier un token pump.fun sont-ils
majoritairement finances, directement ou en quelques sauts, depuis un service de swap ? », G2Y
etant le service identifie.

Ce qui serait une faute : trouver une chaine G2Y -> intermediaire -> premier acheteur sur la cible
et s'arreter la. Tout capital qui entre sur Solana franchit une porte de conversion, et un service
qui traite ~200 000 transactions par mois apparait mecaniquement dans beaucoup de chaines. La seule
mesure qui informe est l'ecart entre la cible et des temoins mesures a la meme profondeur, avec le
meme code.

Deux qualites d'apparition, a ne jamais confondre :
- flux de valeur : le delta de solde de G2Y est non nul dans la transaction, G2Y a paye ou encaisse.
- mention a delta nul : G2Y n'est qu'un compte cite dans la transaction (route, compte de
  programme). Ce n'est pas un financement. La premiere version de l'etape 4 comptait les deux
  ensemble et a produit un faux lien G2Y sur le distributeur 9zqLjp, corrige ici.

Usage :
    python3 etape12_g2y_taux_de_base.py --origine e9_origine_OPTIMUS.json \
                                        --origine e9_origine_Calm.json
"""
from __future__ import annotations
import argparse, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"
CIBLES = {"OPTIMUS"}


def analyse(path):
    d = json.load(open(path))
    label = d.get("label", os.path.basename(path))
    tr = d["trace"]
    flux, mentions = [], []
    for n in tr:
        for k in n["known_counterparties"]:
            if k["addr"] != G2Y:
                continue
            rec = {"noeud": n["addr"], "niveau": n["level"], "utc": k["utc"],
                   "delta_G2Y_sol": k["delta_sol"], "signature": k["signature"],
                   "genese_du_noeud_atteinte": n["genesis_reached"]}
            (flux if abs(k["delta_sol"]) > 0 else mentions).append(rec)
    par_niveau = {}
    for n in tr:
        par_niveau.setdefault(n["level"], {"n": 0, "genese": 0})
        par_niveau[n["level"]]["n"] += 1
        par_niveau[n["level"]]["genese"] += 1 if n["genesis_reached"] else 0
    return {"label": label,
            "role": "cible" if label in CIBLES else "temoin",
            "n_bailleurs_prives_directs": d.get("n_bailleurs_prives_directs"),
            "n_noeuds_remontes": len(tr),
            "n_geneses_atteintes": sum(1 for n in tr if n["genesis_reached"]),
            "n_plafond_pagination": sum(1 for n in tr if not n["genesis_reached"]),
            "par_niveau": {str(k): v for k, v in sorted(par_niveau.items())},
            "n_G2Y_flux_de_valeur": len(flux),
            "n_G2Y_mentions_delta_nul": len(mentions),
            "G2Y_flux": flux, "G2Y_mentions": mentions,
            "terminaux_par_type_nb_noeuds": {k: len(v)
                                             for k, v in d["terminaux_par_type"].items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origine", action="append", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "e12_g2y_taux_de_base.json"))
    a = ap.parse_args()

    rows = [analyse(os.path.join(HERE, p)) for p in a.origine]
    cible = [r for r in rows if r["role"] == "cible"]
    tem = [r for r in rows if r["role"] == "temoin"]
    verdict = (
        "MESURE INSUFFISANTE : pas de temoin remonte a la meme profondeur." if not tem else
        "G2Y NON SPECIFIQUE A LA CIBLE : un flux de valeur G2Y apparait aussi dans la chaine de "
        "financement des premiers acheteurs des temoins, mesures avec le meme code et la meme "
        "profondeur. L'apparition de G2Y ne distingue donc pas la cible."
        if any(r["n_G2Y_flux_de_valeur"] > 0 for r in tem) and cible
        and cible[0]["n_G2Y_flux_de_valeur"] > 0 else
        "G2Y VU SUR LA CIBLE ET ABSENT DES TEMOINS a profondeur egale — ecart a confirmer sur "
        "davantage de temoins avant toute conclusion."
        if cible and cible[0]["n_G2Y_flux_de_valeur"] > 0 else
        "G2Y ABSENTE DES CHAINES DE LA CIBLE aux profondeurs mesurees.")
    res = {"question": "les premiers acheteurs sont-ils finances depuis G2Y en quelques sauts ?",
           "verdict": verdict,
           "avertissement": ("Aboutir a un service de conversion est un fait de routage. Un service "
                             "traitant ~200 000 transactions par mois apparait mecaniquement dans "
                             "de nombreuses chaines : seul l'ecart cible/temoins informe."),
           "tokens": rows}
    json.dump(res, open(a.out, "w"), indent=1)

    print(f"\n{'token':<14} {'role':<8} {'noeuds':>7} {'genese':>8} {'G2Y flux':>9} "
          f"{'G2Y mention':>12}")
    print("-" * 64)
    for r in sorted(rows, key=lambda r: r["role"] != "cible"):
        print(f"{r['label']:<14} {r['role']:<8} {r['n_noeuds_remontes']:>7} "
              f"{r['n_geneses_atteintes']:>3}/{r['n_noeuds_remontes']:<4} "
              f"{r['n_G2Y_flux_de_valeur']:>9} {r['n_G2Y_mentions_delta_nul']:>12}")
    for r in rows:
        for f in r["G2Y_flux"]:
            print(f"\n  {r['label']} — flux de valeur G2Y : {f['delta_G2Y_sol']:+.9f} SOL "
                  f"le {f['utc']}\n     vers/depuis {f['noeud']} (niveau {f['niveau']})"
                  f"\n     tx {f['signature']}")
    print(f"\n  VERDICT : {verdict}")
    print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
