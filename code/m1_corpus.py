#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M1 : recensement du corpus.

Ce que le script etablit : la taille reelle du corpus, sa fenetre et ses
limites. Il vient en premier parce que toute affirmation du dossier se lit avec
ces n-la en tete.

Point d'honnetete central : le collecteur a produit 645 fichiers mais 352 sont
vides (aucun swap enregistre, pannes du fournisseur RPC, pas un phenomene de
marche). Le n exploitable est 293, soit 2,2x moins que le nombre de fichiers.
Tout chiffre annonce "sur 645 captures" serait faux.

Usage :  python3 m1_corpus.py [--data <chemin .jsonl[.gz]>]
"""

import argparse
import collections
import os

import pumplib as P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=os.path.join(P.HERE, "..", "docs", "out", "m1_corpus.json"))
    a = ap.parse_args()

    # Garde-fou : avec --data (jeu d'exemple), on n'ecrase pas l'artefact
    # publie. Un tableau du dossier ne doit pas pouvoir etre remplace en
    # silence par le resultat d'un echantillon de 20 tokens.
    if a.data and a.out == ap.get_default("out"):
        a.out = os.path.join(P.HERE, "..", "data", "sample",
                             os.path.basename(a.out))

    caps = P.load_captures(a.data)
    P.head("M1 : RECENSEMENT DU CORPUS", "MESURE")

    n = len(caps)
    with_snipers = sum(1 for d in caps if d.get("snipers"))
    swaps = {d["mint"]: P.clean_swaps(d) for d in caps}
    n_swaps = sum(len(v) for v in swaps.values())
    traders = set()
    for v in swaps.values():
        traders.update(w["trader"] for w in v if w["trader"])

    t_min = min(d["created"] for d in caps)
    t_max = max(d["created"] for d in caps)
    days = sorted({P.utc(d["created"]) for d in caps})
    cl = P.clusters(caps)
    per_len = sorted(len(v) for v in swaps.values())

    P.kv("tokens publies (captures non vides)", n)
    P.kv("tokens avec liste snipers[] non vide", with_snipers,
         note="%.1f %%" % (100.0 * with_snipers / n))
    P.kv("swaps exploitables au total", n_swaps)
    P.kv("swaps par token, mediane", per_len[len(per_len) // 2])
    P.kv("swaps par token, min / max", "%d / %d" % (per_len[0], per_len[-1]))
    P.kv("adresses distinctes vues en swap", len(traders))
    P.kv("fenetre de creation (UTC)", "%s -> %s" % (
        P.utc(t_min, "%Y-%m-%d %H:%M"), P.utc(t_max, "%Y-%m-%d %H:%M")))
    P.kv("etendue", "%.1f jours" % ((t_max - t_min) / 86400.0))
    P.kv("jours calendaires couverts", len(days))
    P.kv("grappes temporelles (gap 30 min)", len(set(cl.values())),
         note="unite de re-echantillonnage")

    print("\n  Tokens par jour :")
    per_day = collections.Counter(P.utc(d["created"]) for d in caps)
    for d_ in days:
        print("    %s  %3d" % (d_, per_day[d_]))

    print("""
  LIMITES A GARDER EN TETE, toutes mesurees :
   - Le corpus couvre 6,2 jours. Aucune conclusion de ce depot ne porte sur
     une autre epoque de marche. [MESURE]
   - Le collecteur n'observe pas tout le flux : il capte les tokens qu'il a
     detectes, pas la population complete des lancements. Le corpus
     sur-echantillonne donc les tokens qui ont bouge. Consequence sur le sens
     des resultats : elle joue contre la these du dossier (un echantillon
     enrichi en gagnants devrait rendre l'achat moins perdant qu'il ne l'est
     reellement). [INFERE]
   - Les swaps enregistres sont ceux du pool AMM. Les achats effectues sur la
     courbe de bonding avant graduation n'y figurent pas : ils sont dans
     snipers[]. C'est precisement ce que M2 et M3 exploitent. [MESURE]""")

    P.emit({
        "n_tokens": n, "n_avec_snipers": with_snipers, "n_swaps": n_swaps,
        "n_adresses_distinctes": len(traders),
        "fenetre_utc": [t_min, t_max], "jours": days,
        "n_grappes": len(set(cl.values())),
        "swaps_par_token": {"min": per_len[0], "med": per_len[len(per_len) // 2],
                            "max": per_len[-1]},
        "niveau": "MESURE",
    }, os.path.abspath(a.out))


if __name__ == "__main__":
    main()
