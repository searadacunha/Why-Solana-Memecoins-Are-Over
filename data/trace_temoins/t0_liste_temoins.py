#!/usr/bin/env python3
"""Etape 0 : la liste des 9 temoins, recopiee telle quelle de cibles.json.

Aucun choix n'est fait ici. La selection est figee en amont (fenetre de +-200 slots
autour de trois ancres, exclusion de `complete` et de KOTH, 3 par fenetre) et ne
portait que sur la date de creation et la performance de marche. On la prend en bloc,
temoins pauvres en acheteurs compris : retirer B&D (2 acheteurs) apres avoir vu les
resultats serait un choix dependant du resultat, ce que le pre-enregistrement interdit.

Les etiquettes ASCII sont des noms de fichiers ; le mint reste la seule identite.
"""
from __future__ import annotations
import json, os

CIBLES = ("data/cibles/cibles.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "t0_temoins.json")

# Etiquette de fichier ASCII -> symbole reel. Le seul cas non ASCII est le temoin 3.
ASCII = {"₫øⒼё": "DONGOE"}


# Le schema de cibles.json a change depuis: 10_select_temoins.py ne produit plus
# `acheteurs_distincts` ni `analysable_financement`. On le dit au lieu de lever un
# KeyError nu. La correspondance avec les champs actuels n'est pas devinable, il
# faut la retrouver: t0_temoins.json committe garde les valeurs d'alors.
ATTENDUS = ("acheteurs_distincts", "analysable_financement")


def main():
    d = json.load(open(CIBLES))
    exemple = (d.get("temoins") or d.get("cibles") or [{}])[0]
    absents = [k for k in ATTENDUS if k not in exemple]
    if absents:
        raise SystemExit(
            "%s ne porte plus %s.\n"
            "  Ce script attend le schema d'avant la regeneration de cibles.json par\n"
            "  10_select_temoins.py. Les valeurs d'alors sont dans t0_temoins.json."
            % (CIBLES, " ni ".join(absents)))
    rows = []
    for t in d["temoins"]:
        sym = t["symbole"]
        rows.append({
            "label": ASCII.get(sym, sym.replace("&", "and").replace(" ", "_")),
            "symbole": sym,
            "mint": t["mint"],
            "bonding_curve": t["bonding_curve"],
            "date_creation_utc": t["date_creation_utc"],
            "fenetre_ancre": t["fenetre_ancre"],
            "acheteurs_distincts_attendus": t["acheteurs_distincts"],
            "analysable_financement": t["analysable_financement"],
            "gradue": t["gradue"],
            "king_of_the_hill": t["king_of_the_hill"],
            "tx_totales_bonding_curve": t["tx_totales_bonding_curve"],
        })
    cibles = [{"label": t["symbole"], "mint": t["mint"], "bonding_curve": t["bonding_curve"],
               "acheteurs_distincts": t["acheteurs_distincts"]} for t in d["cibles"]]
    json.dump({"temoins": rows, "cibles_pour_memoire": cibles}, open(OUT, "w"), indent=1,
              ensure_ascii=False)
    for r in rows:
        print(f"  {r['label']:<12} {r['mint']}  curve {r['bonding_curve']}  "
              f"{r['acheteurs_distincts_attendus']:>3d} acheteurs  ancre {r['fenetre_ancre']}")
    print(f"\n  {len(rows)} temoins -> {OUT}")


if __name__ == "__main__":
    main()
