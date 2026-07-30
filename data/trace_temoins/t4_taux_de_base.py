#!/usr/bin/env python3
"""ETAPE 4 — LE TAUX DE BASE. Combien de temoins montrent aussi un « decoupage » ?

CE QUE CE SCRIPT NE FAIT PAS
----------------------------
Il ne recalcule rien et n'ajuste aucun seuil. Il lit les fichiers e3_splits_*.json produits par le
detecteur des cibles, recopie a l'identique, et compte. Tout reglage fait ici, apres avoir vu les
resultats, serait un seuil choisi pour obtenir la conclusion voulue.

TROIS TAUX SEPARES, PAS UN
--------------------------
Le detecteur rend trois signatures de force tres inegale (A meme transaction, B meme montant/meme
moment, C bailleur prive commun) et son verdict global declare « DECOUPAGE DETECTE » des que l'UNE
d'elles est presente. Agreger les trois en un seul taux de base masquerait l'essentiel : une
signature dont le taux de base est eleve ne vaut rien, meme si une autre reste a zero. On rend donc
un taux par signature.

DENOMINATEUR : LE PORTEFEUILLE, PAS LE TOKEN
--------------------------------------------
Cinq temoins sur neuf ont moins de dix premiers acheteurs (B&D en a deux). Compter par token
donnerait a un temoin a 2 acheteurs le meme poids qu'a un temoin a 40. On rend donc les deux
denominateurs, et le taux par portefeuille est celui qui compte.

COUVERTURE : UN NEGATIF NON COUVERT N'EST PAS UN NEGATIF
-------------------------------------------------------
Pour chaque portefeuille on rend `genesis_reached` (naissance vue) et `prebuy_window_reached`
(21 jours precedant le premier achat couverts). Le taux de base est calcule DEUX FOIS : sur tous les
portefeuilles, et sur le seul sous-ensemble effectivement couvert. Le second est le seul defendable.
"""
from __future__ import annotations
import glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
CIBLE_DIR = "data/trace_optimus"
OUT = os.path.join(HERE, "t4_taux_de_base.json")


def charge(d3, d2):
    """Un token : verdict du detecteur + couverture portefeuille par portefeuille."""
    wal = {w["wallet"]: w for w in d2["wallets"]}
    in_A = {w for c in d3["A_meme_transaction"] for w in c["wallets"]}
    in_B = {w for c in d3["B_meme_montant_meme_moment"] for w in c["wallets"]}
    in_C = {w for c in d3["C_bailleurs_communs_PRIVES"] for w in c["wallets"]}
    rows = []
    for w in d2["wallets"]:
        rows.append({
            "wallet": w["wallet"], "rang_achat": w.get("buy_rank"),
            "n_signatures": w.get("n_signatures_total"),
            "pages_paginees": w.get("pages_paginated"),
            "genese_atteinte": bool(w.get("genesis_reached")),
            "fenetre_prebuy_atteinte": bool(w.get("prebuy_window_reached")),
            "jours_prebuy_couverts": w.get("prebuy_window_days_covered"),
            "hyperactif_non_mesurable": bool(w.get("hyperactif_non_mesurable")),
            "pagination_plafonnee": bool(w.get("pagination_capped")),
            "n_entrees_de_fonds": len([f for f in w.get("inflows") or []
                                       if f.get("nature") != "produit_de_vente"]),
            "dans_signature_A": w["wallet"] in in_A,
            "dans_signature_B": w["wallet"] in in_B,
            "dans_signature_C_prive": w["wallet"] in in_C,
            "echec_de_mesure": w.get("measurement_failure"),
        })
    return {
        "label": d3["label"], "mint": d3["mint"],
        "n_portefeuilles": d3["n_wallets"],
        "n_entrees_de_fonds_retenues": d3["n_inflows_total"],
        "n_rentrees_ecartees_produit_de_vente": d3["n_rentrees_ecartees_produit_de_vente"],
        "signature_A_n_clusters": len(d3["A_meme_transaction"]),
        "signature_B_n_clusters": len(d3["B_meme_montant_meme_moment"]),
        "signature_C_n_bailleurs_prives": len(d3["C_bailleurs_communs_PRIVES"]),
        "signature_C_bailleurs_prives": [
            {"bailleur": c["funder"], "n_acheteurs": c["n_early_buyers_funded"],
             "montants_sol": c["amounts_sol"], "premier_utc": c["first_utc"],
             "portefeuilles": c["wallets"]}
            for c in d3["C_bailleurs_communs_PRIVES"]],
        "signature_C_infra_sans_valeur": [
            {"bailleur": c["funder"], "connu": c["known"],
             "n_acheteurs": c["n_early_buyers_funded"]}
            for c in d3["C_bailleurs_communs_infrastructure_sans_valeur"]],
        "verdict_detecteur": d3["verdict"],
        "n_genese_atteinte": d3["n_genesis_reached"],
        "n_genese_NON_atteinte": d3["n_genesis_NOT_reached"],
        "n_prebuy_atteinte": d3["n_prebuy_reached"],
        "n_prebuy_NON_atteinte": d3["n_prebuy_NOT_reached"],
        "n_hyperactifs_non_mesurables": d3["n_hyperactifs_non_mesurables"],
        "portefeuilles": rows,
    }


def taux(tokens, key, filtre=None):
    """Taux par portefeuille pour une signature donnee, sur le sous-ensemble `filtre`."""
    n = pos = 0
    for t in tokens:
        for w in t["portefeuilles"]:
            if filtre and not filtre(w):
                continue
            n += 1
            pos += 1 if w[key] else 0
    return {"n_portefeuilles": n, "n_positifs": pos,
            "taux": round(pos / n, 4) if n else None}


def main():
    liste = json.load(open(os.path.join(HERE, "t0_temoins.json")))["temoins"]
    tokens, manquants = [], []
    for t in liste:
        lab = t["label"]
        p3, p2 = os.path.join(HERE, f"e3_splits_{lab}.json"), \
                 os.path.join(HERE, f"e2_funding_{lab}.json")
        if not (os.path.exists(p3) and os.path.exists(p2)):
            manquants.append(lab)
            continue
        row = charge(json.load(open(p3)), json.load(open(p2)))
        row["symbole"] = t["symbole"]
        row["date_creation_utc"] = t["date_creation_utc"]
        row["fenetre_ancre"] = t["fenetre_ancre"]
        row["deja_mesure_pendant_les_cibles"] = lab in ("Calm", "faith")
        tokens.append(row)

    # La cible passee par cette meme procedure, pour la comparaison.
    cibles = []
    for p3 in sorted(glob.glob(os.path.join(CIBLE_DIR, "e3_splits_*.json"))):
        lab = os.path.basename(p3)[len("e3_splits_"):-len(".json")]
        p2 = os.path.join(CIBLE_DIR, f"e2_funding_{lab}.json")
        if lab in ("Calm", "faith", "DOGEFORMULA") or not os.path.exists(p2):
            continue
        cibles.append(charge(json.load(open(p3)), json.load(open(p2))))

    couvert_prebuy = lambda w: w["fenetre_prebuy_atteinte"]
    couvert_genese = lambda w: w["genese_atteinte"]

    res = {
        "objet": "Taux de base du DECOUPAGE chez les premiers acheteurs de tokens pump.fun temoins",
        "procedure": ("etape1/2/3 des cibles recopiees a l'identique (t1_/t2_/t3_). Aucun seuil "
                      "modifie : N_BUYERS=40, MAX_TX=260, MIN_INFLOW=0.05 SOL, PREBUY_DAYS=21, "
                      "MAX_PAGES=400, REL_TOL=1e-4, WINDOW_S=3600s, MIN_CLUSTER=3."),
        "temoins_manquants": manquants,
        "n_tokens_temoins": len(tokens),
        "n_portefeuilles_temoins": sum(t["n_portefeuilles"] for t in tokens),

        "taux_de_base_PAR_TOKEN": {
            "A_meme_transaction": f"{sum(1 for t in tokens if t['signature_A_n_clusters'])}/{len(tokens)}",
            "B_meme_montant_meme_moment": f"{sum(1 for t in tokens if t['signature_B_n_clusters'])}/{len(tokens)}",
            "C_bailleur_prive_commun": f"{sum(1 for t in tokens if t['signature_C_n_bailleurs_prives'])}/{len(tokens)}",
            "verdict_global_du_detecteur_DECOUPAGE_DETECTE":
                f"{sum(1 for t in tokens if t['verdict_detecteur'].startswith('DECOUPAGE'))}/{len(tokens)}",
        },
        "taux_de_base_PAR_PORTEFEUILLE_tous": {
            "A": taux(tokens, "dans_signature_A"),
            "B": taux(tokens, "dans_signature_B"),
            "C": taux(tokens, "dans_signature_C_prive"),
        },
        "taux_de_base_PAR_PORTEFEUILLE_fenetre_prebuy_couverte": {
            "A": taux(tokens, "dans_signature_A", couvert_prebuy),
            "B": taux(tokens, "dans_signature_B", couvert_prebuy),
            "C": taux(tokens, "dans_signature_C_prive", couvert_prebuy),
        },
        "taux_de_base_PAR_PORTEFEUILLE_genese_atteinte": {
            "A": taux(tokens, "dans_signature_A", couvert_genese),
            "B": taux(tokens, "dans_signature_B", couvert_genese),
            "C": taux(tokens, "dans_signature_C_prive", couvert_genese),
        },
        "couverture": {
            "n_genese_atteinte": sum(t["n_genese_atteinte"] for t in tokens),
            "n_genese_NON_atteinte": sum(t["n_genese_NON_atteinte"] for t in tokens),
            "n_prebuy_atteinte": sum(t["n_prebuy_atteinte"] for t in tokens),
            "n_prebuy_NON_atteinte": sum(t["n_prebuy_NON_atteinte"] for t in tokens),
            "n_hyperactifs_non_mesurables": sum(t["n_hyperactifs_non_mesurables"] for t in tokens),
        },
        "tokens_temoins": tokens,
        "cibles_meme_procedure": cibles,
    }

    # Qualification. Un taux de base de zero ne vaut que sur la couverture effectivement obtenue.
    cp = res["couverture"]
    res["qualification"] = (
        f"Couverture : genese atteinte pour {cp['n_genese_atteinte']}/"
        f"{res['n_portefeuilles_temoins']} portefeuilles temoins, fenetre pre-achat pour "
        f"{cp['n_prebuy_atteinte']}/{res['n_portefeuilles_temoins']}. "
        f"Le taux de base de la signature A (financement dans une meme transaction, la signature "
        f"ODIN) n'est mesure que sur les {cp['n_genese_atteinte']} portefeuilles dont la naissance a "
        f"ete vue ; sur les {cp['n_genese_NON_atteinte']} autres l'absence de A est un ECHEC DE "
        f"MESURE, pas un zero.")
    json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)

    print(f"\n{'='*104}\nTAUX DE BASE — {len(tokens)} tokens temoins, "
          f"{res['n_portefeuilles_temoins']} premiers acheteurs\n{'='*104}")
    print(f"{'temoin':<12}{'acht':>5}{'entrees':>8}{'ventes':>8}{'genese':>9}{'prebuy':>9}"
          f"{'  A':>4}{'  B':>4}{'  C':>4}  verdict du detecteur")
    for t in tokens + [None] + cibles:
        if t is None:
            print("-" * 104 + "\nCIBLE(S) passees par la MEME procedure, pour comparaison :")
            continue
        print(f"{t['label']:<12}{t['n_portefeuilles']:>5}{t['n_entrees_de_fonds_retenues']:>8}"
              f"{t['n_rentrees_ecartees_produit_de_vente']:>8}"
              f"{t['n_genese_atteinte']:>4}/{t['n_portefeuilles']:<4}"
              f"{t['n_prebuy_atteinte']:>4}/{t['n_portefeuilles']:<4}"
              f"{t['signature_A_n_clusters']:>4}{t['signature_B_n_clusters']:>4}"
              f"{t['signature_C_n_bailleurs_prives']:>4}  {t['verdict_detecteur'][:34]}")
    print()
    for nom, cle in [("tous les portefeuilles", "taux_de_base_PAR_PORTEFEUILLE_tous"),
                     ("fenetre pre-achat couverte",
                      "taux_de_base_PAR_PORTEFEUILLE_fenetre_prebuy_couverte"),
                     ("genese atteinte", "taux_de_base_PAR_PORTEFEUILLE_genese_atteinte")]:
        b = res[cle]
        print(f"  taux par portefeuille ({nom}) : "
              + " · ".join(f"{k} {v['n_positifs']}/{v['n_portefeuilles']}" for k, v in b.items()))
    print("\n  par token : " + " · ".join(f"{k} {v}" for k, v
                                          in res["taux_de_base_PAR_TOKEN"].items()))
    print("\n  " + res["qualification"])
    print(f"\n  -> {OUT}")


if __name__ == "__main__":
    main()
