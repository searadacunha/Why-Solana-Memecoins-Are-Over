#!/usr/bin/env python3
"""Etape 7 : rapport consolide. Taux de base par signature, bornes, couverture, rattrapage.

Lit t4_taux_de_base.json, plus t5_rattrapage_journal.json et t6_profil_bailleurs.json s'ils
existent. Ecrit t7_rapport_final.json a cote du script.

Ce qu'il ajoute a t4 :
1. Des bornes, pas seulement des points. "0 sur 9" n'est pas "zero" : la borne superieure exacte a
   95 % (Clopper-Pearson, cas 0 succes : 1 - 0.05^(1/n)) dit ce que l'echantillon permet d'exclure.
   Avec neuf temoins on ne peut pas exclure un taux de base de 28 % par token.
2. Le resultat du rattrapage de couverture (t5), qui distingue deux choses tres differentes : un
   portefeuille non remonte parce que le plafond etait bas, et un portefeuille structurellement hors
   d'atteinte de `getSignaturesForAddress`.
3. Le profil des bailleurs communs prives (t6), sans lequel la signature C n'est pas interpretable.
"""
from __future__ import annotations
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "t7_rapport_final.json")


def borne_sup_95_zero(n):
    """Borne superieure exacte a 95 % du taux, quand on a observe zero positif sur n essais."""
    return None if not n else round(1 - math.exp(math.log(0.05) / n), 4)


def ic_95(k, n):
    """Intervalle de confiance exact (Clopper-Pearson) par recherche binaire sur la loi binomiale."""
    if not n:
        return None
    def cdf_sup(p):        # P(X <= k-1 | p)  -> borne basse
        return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k))
    def cdf_inf(p):        # P(X <= k | p)    -> borne haute
        return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k+1))
    lo, hi = 0.0, 0.0
    if k > 0:
        a, b = 0.0, 1.0
        for _ in range(60):
            m = (a+b)/2
            if cdf_sup(m) > 0.975: a = m
            else: b = m
        lo = a
    a, b = 0.0, 1.0
    for _ in range(60):
        m = (a+b)/2
        if cdf_inf(m) > 0.025: a = m
        else: b = m
    hi = a
    return [round(lo, 4), round(hi, 4)]


def main():
    t4 = json.load(open(os.path.join(HERE, "t4_taux_de_base.json")))
    tokens, cibles = t4["tokens_temoins"], t4["cibles_meme_procedure"]
    nT, nW = len(tokens), t4["n_portefeuilles_temoins"]
    cov = t4["couverture"]

    kA = sum(1 for t in tokens if t["signature_A_n_clusters"])
    kB = sum(1 for t in tokens if t["signature_B_n_clusters"])
    kC = sum(1 for t in tokens if t["signature_C_n_bailleurs_prives"])

    prof = {}
    p6 = os.path.join(HERE, "t6_profil_bailleurs.json")
    if os.path.exists(p6):
        prof = {x["contexte"]: x for x in json.load(open(p6))}

    ratt, ratt_detail = None, []
    p5 = os.path.join(HERE, "t5_rattrapage_journal.json")
    if os.path.exists(p5):
        j = json.load(open(p5))
        ratt_detail = j
        ratt = {"n_portefeuilles_retentes": len(j),
                "n_recuperes": sum(1 for x in j if x["prebuy_reached_apres"]),
                "n_toujours_hors_atteinte": sum(1 for x in j if not x["prebuy_reached_apres"]),
                "pages_max_atteintes": max((x["pages"] for x in j), default=0),
                "signatures_max_lues": max((x["sigs"] for x in j), default=0)}

    res = {
        "objet": ("TAUX DE BASE du decoupage de financement chez les premiers acheteurs de tokens "
                  "pump.fun temoins de la meme periode (oct-dec 2024) que les cibles de l'auteur"),
        "procedure": t4["procedure"],
        "echantillon": {"n_tokens_temoins": nT, "n_premiers_acheteurs": nW,
                        "n_tokens_cibles_passes_par_la_meme_procedure": len(cibles),
                        "cibles_presentes": [c["label"] for c in cibles]},

        # ---- le resultat central -------------------------------------------------------------
        "taux_de_base_par_signature": {
            "A_meme_transaction": {
                "description": ("plusieurs premiers acheteurs finances dans UNE SEULE transaction "
                                "— la signature du cas ODIN, la seule indiscutable"),
                "par_token": f"{kA}/{nT}",
                "par_portefeuille_genese_atteinte":
                    f"{t4['taux_de_base_PAR_PORTEFEUILLE_genese_atteinte']['A']['n_positifs']}"
                    f"/{t4['taux_de_base_PAR_PORTEFEUILLE_genese_atteinte']['A']['n_portefeuilles']}",
                "borne_sup_95_par_token": borne_sup_95_zero(nT) if kA == 0 else None,
                "borne_sup_95_par_portefeuille_genese_atteinte":
                    borne_sup_95_zero(cov["n_genese_atteinte"]) if kA == 0 else None,
                "presente_sur_les_cibles": {c["label"]: c["signature_A_n_clusters"] for c in cibles},
            },
            "B_meme_montant_meme_moment": {
                "description": ("montants egaux a 1e-4 pres vers >= 3 portefeuilles distincts en "
                                "moins d'une heure"),
                "par_token": f"{kB}/{nT}",
                "par_portefeuille_prebuy_couvert":
                    f"{t4['taux_de_base_PAR_PORTEFEUILLE_fenetre_prebuy_couverte']['B']['n_positifs']}"
                    f"/{t4['taux_de_base_PAR_PORTEFEUILLE_fenetre_prebuy_couverte']['B']['n_portefeuilles']}",
                "borne_sup_95_par_token": borne_sup_95_zero(nT) if kB == 0 else None,
                "borne_sup_95_par_portefeuille_prebuy_couvert":
                    borne_sup_95_zero(cov["n_prebuy_atteinte"]) if kB == 0 else None,
                "presente_sur_les_cibles": {c["label"]: c["signature_B_n_clusters"] for c in cibles},
            },
            "C_bailleur_prive_commun": {
                "description": ("une source privee finance >= 2 des premiers acheteurs, montants "
                                "quelconques"),
                "par_token": f"{kC}/{nT}",
                "taux_point_par_token": round(kC / nT, 4),
                "IC95_par_token": ic_95(kC, nT),
                "par_portefeuille": f"{t4['taux_de_base_PAR_PORTEFEUILLE_tous']['C']['n_positifs']}/{nW}",
                "temoins_positifs": [t["label"] for t in tokens
                                     if t["signature_C_n_bailleurs_prives"]],
                "presente_sur_les_cibles": {c["label"]: c["signature_C_n_bailleurs_prives"]
                                            for c in cibles},
            },
        },

        # ---- ce que le detecteur declare, tel quel ---------------------------------------------
        "verdict_global_du_detecteur": {
            "temoins_DECOUPAGE_DETECTE":
                f"{sum(1 for t in tokens if t['verdict_detecteur'].startswith('DECOUPAGE'))}/{nT}",
            "cibles_DECOUPAGE_DETECTE":
                f"{sum(1 for c in cibles if c['verdict_detecteur'].startswith('DECOUPAGE'))}/{len(cibles)}",
            "lecture": ("Le verdict global du detecteur declare « DECOUPAGE DETECTE » des qu'UNE des "
                        "trois signatures est presente. Sur ce verdict global, un temoin sur neuf est "
                        "positif. Un verdict positif sur un token isole n'est donc PAS distinctif."),
        },

        "couverture": dict(cov, **{
            "part_genese_atteinte": round(cov["n_genese_atteinte"] / nW, 3),
            "part_prebuy_atteinte": round(cov["n_prebuy_atteinte"] / nW, 3)}),
        "rattrapage_de_couverture": ratt,
        "rattrapage_detail": ratt_detail,
        "profil_des_bailleurs_communs_prives": prof,

        "par_token_detail": [
            {"temoin": t["label"], "symbole": t["symbole"], "mint": t["mint"],
             "n_premiers_acheteurs": t["n_portefeuilles"],
             "A": t["signature_A_n_clusters"], "B": t["signature_B_n_clusters"],
             "C_prive": t["signature_C_n_bailleurs_prives"],
             "C_infra_sans_valeur": len(t["signature_C_infra_sans_valeur"]),
             "genese": f"{t['n_genese_atteinte']}/{t['n_portefeuilles']}",
             "prebuy": f"{t['n_prebuy_atteinte']}/{t['n_portefeuilles']}",
             "n_entrees_retenues": t["n_entrees_de_fonds_retenues"],
             "n_ecartees_produit_de_vente": t["n_rentrees_ecartees_produit_de_vente"],
             "verdict": t["verdict_detecteur"]}
            for t in tokens],
    }
    json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)

    S = res["taux_de_base_par_signature"]
    print("\n" + "=" * 96)
    print(f"TAUX DE BASE — {nT} temoins, {nW} premiers acheteurs")
    print("=" * 96)
    for k, v in S.items():
        print(f"\n{k}")
        print(f"   par token                : {v['par_token']}"
              + (f"   borne sup 95% : {v['borne_sup_95_par_token']:.1%}"
                 if v.get("borne_sup_95_par_token") else
                 f"   IC95 : {v.get('IC95_par_token')}"))
        cle = ("par_portefeuille_genese_atteinte" if "par_portefeuille_genese_atteinte" in v
               else "par_portefeuille_prebuy_couvert" if "par_portefeuille_prebuy_couvert" in v
               else "par_portefeuille")
        bs = v.get("borne_sup_95_par_portefeuille_genese_atteinte") or \
             v.get("borne_sup_95_par_portefeuille_prebuy_couvert")
        print(f"   par portefeuille         : {v[cle]}"
              + (f"   borne sup 95% : {bs:.1%}" if bs else ""))
        print(f"   sur les cibles           : {v['presente_sur_les_cibles']}")
    print(f"\nverdict global du detecteur : temoins "
          f"{res['verdict_global_du_detecteur']['temoins_DECOUPAGE_DETECTE']} · cibles "
          f"{res['verdict_global_du_detecteur']['cibles_DECOUPAGE_DETECTE']}")
    c = res["couverture"]
    print(f"couverture : genese {c['n_genese_atteinte']}/{nW} ({c['part_genese_atteinte']:.0%}) · "
          f"fenetre pre-achat {c['n_prebuy_atteinte']}/{nW} ({c['part_prebuy_atteinte']:.0%}) · "
          f"hyperactifs non mesurables {c['n_hyperactifs_non_mesurables']}")
    if ratt:
        print(f"rattrapage (plafond 900 pages) : {ratt['n_recuperes']}/"
              f"{ratt['n_portefeuilles_retentes']} recuperes, "
              f"{ratt['n_toujours_hors_atteinte']} STRUCTURELLEMENT hors d'atteinte "
              f"(jusqu'a {ratt['signatures_max_lues']:,} signatures lues)")
    print(f"\n  -> {OUT}")


if __name__ == "__main__":
    main()
