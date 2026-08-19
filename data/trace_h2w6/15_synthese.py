#!/usr/bin/env python3
"""Synthese h2w6gm6jz : assemble les mesures des etapes 1 a 4bis en un seul fichier.

Ne mesure rien de neuf. Lit e1_buyers, e2_funding, e3_splits, e4b_origine_bailleurs et e8_fenetres
dans le repertoire courant, ecrit SYNTHESE_h2w6gm6jz.json. Calcule les denominateurs : aucun chiffre
de couverture n'est arrondi a l'avantage de la conclusion, le drapeau de genese est garde par
portefeuille, et le verdict reste borne a la portee effectivement couverte.
"""
from __future__ import annotations
import json, datetime as dt

D = "."
G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"

e1 = json.load(open(f"{D}/e1_buyers_h2w6gm6jz.json"))
e2 = json.load(open(f"{D}/e2_funding_h2w6gm6jz.json"))
e3 = json.load(open(f"{D}/e3_splits_h2w6gm6jz.json"))
e4b = json.load(open(f"{D}/e4b_origine_bailleurs.json"))
e8 = json.load(open(f"{D}/e8_fenetres_G9X7F4Jz.json"))

by_rank = {w["buy_rank"]: w for w in e2["wallets"]}

FLOTTES = [
    {"nom": "A", "bailleur": "G9X7F4JzLzbSGMCndiBdWNi5YzZZakmtkdwq7xS3Q3FE",
     "montant_recu_sol": 2.000000000, "calibre": "rond_SOL",
     "naissance_utc": ["2024-12-13 07:20:16", "2024-12-13 07:21:29"], "span_s": 73,
     "rangs": [11, 5, 9, 7, 6],
     "recharge": {"bailleur": "v6BFsgbJ5YaYZxEgapUXi5F2AoAZFDPaZdsspvfJBhq",
                  "utc": ["2024-12-13 12:24:54", "2024-12-13 12:25:37"],
                  "montants_sol": [1.70, 1.88, 1.44, 1.97, 3.00]},
     "achat_groupe": None},
    {"nom": "B", "bailleur": "AaZkwhkiDStDcgrU37XAj9fpNLrD8Erz5PNkdm4k5hjy",
     "montant_recu_sol": None, "calibre": "precis_swap",
     "montants_sol": [4.880451810, 4.895794919, 4.901747259],
     "naissance_utc": ["2024-12-12 13:21:08", "2024-12-12 13:25:09"], "span_s": 241,
     "rangs": [12, 14, 8],
     "achat_groupe": {"montant_sol": 1.512044279, "slot": 307237642,
                      "utc": "2024-12-13 14:50:41"}},
    {"nom": "C", "bailleur": "G9X7F4JzLzbSGMCndiBdWNi5YzZZakmtkdwq7xS3Q3FE",
     "montant_recu_sol": 1.000000000, "calibre": "rond_SOL",
     "naissance_utc": ["2024-12-03 15:49:28", "2024-12-03 16:12:16"], "span_s": 1368,
     "rangs": [24, 23, 22, 19],
     "achat_groupe": {"montant_sol": 0.563089281, "slot": 307237659,
                      "utc": "2024-12-13 14:50:48", "rangs": [19, 22, 24]}},
]
FLOTTES[0]["achat_groupe"] = {"note": "5 achats en 1 seconde (+6 s et +7 s apres la 1re tx de "
                                      "courbe), montants distincts",
                              "utc": "2024-12-13 14:50:40 / 14:50:41"}

TROISIEME = {"nom": "achat groupe D", "montant_sol": 2.070240160, "slot": 307237685,
             "utc": "2024-12-13 14:51:00", "rangs": [34, 35, 36],
             "note": "3 achats au lamport pres dans le MEME slot, mais les 3 portefeuilles sont des "
                     "bots anterieurs : genese non atteinte, financement de naissance non teste."}

n = len(e2["wallets"])
gen = [w for w in e2["wallets"] if w["genesis_reached"]]
res = {
    "token": "h2w6gm6jz", "mint": e1["mint"], "curve": e1["curve"],
    "creation_utc": e1["first_curve_tx_utc"],
    "courbe": {"n_signatures": e1["curve_signatures_total"],
               "genese_atteinte": e1["curve_genesis_reached"],
               "n_acheteurs_distincts_sur_toute_la_courbe": 183,
               "n_premiers_acheteurs_analyses": n},
    "couverture": {
        "n_portefeuilles": n,
        "n_genese_atteinte": len(gen),
        "n_genese_NON_atteinte": n - len(gen),
        "n_fenetre_prebuy_21j_couverte": e3["n_prebuy_reached"],
        "n_hyperactifs_non_mesurables": e3["n_hyperactifs_non_mesurables"],
        "portefeuilles_sans_genese": [w["wallet"] for w in e2["wallets"]
                                      if not w["genesis_reached"]],
        "regle": ("Un negatif ne vaut que sur la portee couverte. Pour les "
                  f"{n - len(gen)} portefeuilles sans genese, l'absence de financement de naissance "
                  "est un ECHEC DE MESURE, pas un resultat."),
    },
    "flottes_de_naissance": FLOTTES,
    "achat_groupe_sans_genese": TROISIEME,
    "decoupages": {"A_meme_transaction": e3["A_meme_transaction"],
                   "B_meme_montant_meme_moment": e3["B_meme_montant_meme_moment"],
                   "C_bailleurs_communs_PRIVES": e3["C_bailleurs_communs_PRIVES"],
                   "C_bailleurs_infrastructure": e3[
                       "C_bailleurs_communs_infrastructure_sans_valeur"]},
    "controle_taux_de_base": e8,
    "chaine_vers_G2Y": {
        "etabli": True,
        "maillons": [
            {"n": 1, "de": G2Y, "vers": "8RU58KBpKYz5QRwfmR1QaQ1U75xtvPbLbuLfTN4nqz6v",
             "montant_sol": 10.587826000, "utc": "2024-12-13 13:56:45",
             "signature": "5Yef1gQAUDb6yubfLKVR2VkHH9DSBRCAS559GHje4mPBqwXfmnesPTAtobXv5aamNXY5"
                          "GMvsJYrKVkyEoBk3iZjW",
             "note": "premiere transaction de la vie de 8RU58K ; genese atteinte, 22 signatures "
                     "au total dans toute son existence"},
            {"n": 2, "de": "8RU58KBpKYz5QRwfmR1QaQ1U75xtvPbLbuLfTN4nqz6v",
             "vers": "ApBXF9f1tgk8FTDbUonjTmGnWBCJRyedKKD26HP3Tp7X",
             "montant_sol": 10.587811100, "utc": "2024-12-13 14:04:15",
             "signature": "DzvXawfafGCVf3EeiPvAyrebUo78KNcwNvSYRfttr2o8dSwBxjZXPbDzAHnbzraTnR1n"
                          "F17KYsjp5iDsMYJZeV5",
             "note": "ApBXF9f1 est le CREATEUR du token ; ne a cet instant"},
            {"n": 3, "de": "ApBXF9f1tgk8FTDbUonjTmGnWBCJRyedKKD26HP3Tp7X", "vers": "mint + achat #1",
             "utc": "2024-12-13 14:50:34", "montant_sol": 1.332417321,
             "note": "creation du mint et premier achat, 46 min apres avoir recu les fonds"},
        ],
        "delai_G2Y_creation_minutes": 53.8,
        "reserve": ("Aboutir a G2Y est un fait de routage : tout capital entrant sur Solana franchit "
                    "une telle porte. Ce qui est probant ici n'est pas le passage par un service de "
                    "swap, c'est que le relais 8RU58K n'a servi qu'a CA (22 tx dans toute sa vie, "
                    "une entree, une sortie, puis 11 mois de silence) et que la chaine tient en "
                    "54 minutes."),
        "consequence_pour_l_enquete": ("G2Y etait DEJA EN SERVICE le 13 decembre 2024. La question "
                                       "ouverte du brief (« on ignore si elle etait deja en service "
                                       "fin 2024 ») est tranchee par le positif : oui.")},
    "profil_des_bailleurs": {
        "G9X7F4JzLzbSGMCndiBdWNi5YzZZakmtkdwq7xS3Q3FE": {
            "role": "SERVICE a fort debit, pas un distributeur dedie",
            "mesure_dec2024": {"tx_par_jour": 6674, "destinataires_distincts_en_11h": 759,
                               "payeurs_distincts_en_11h": 711,
                               "types": "100 % TRANSFER",
                               "montants_de_sortie_ronds": "1.0 SOL x10, 0.3 x9, 0.5 x6 …"},
            "consequence": ("« Meme bailleur » ne vaut donc RIEN seul pour cette adresse : c'est un "
                            "service a des centaines de clients par jour. Seul le controle de "
                            "fenetre (e8) porte l'argument."),
            "cadence_comparable_a_G2Y": ("~6 700 tx/jour ici contre ~6 600/jour pour G2Y "
                                         "(200 000/mois). Hypothese a tester, NON etablie : meme "
                                         "operateur, deux adresses. Les deux sont actives "
                                         "simultanement, donc ce n'est pas une simple rotation.")},
        "AaZkwhkiDStDcgrU37XAj9fpNLrD8Erz5PNkdm4k5hjy": {
            "role": "SERVICE (routeur de retraits), alimente par un echange et un service de swap",
            "mesure_dec2024": {"tx_par_jour": 1487, "destinataires_distincts_en_40h": 2005,
                               "payeurs_distincts_en_40h": 682,
                               "sorties": "toutes precises a la 9e decimale = sorties de conversion"},
            "payeurs_connus": ["5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9 (Binance) 1665 SOL",
                               "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w (service de swap) "
                               "600 SOL"],
            "lecture": ("Les 3 montants 4.880451810 / 4.895794919 / 4.901747259 SOL, ecartes de "
                        "0,43 %, livres en 4 minutes : signature de TROIS CONVERSIONS du meme "
                        "montant nominal a quelques minutes d'intervalle, le taux ayant bouge. "
                        "C'est un decoupage passe par un service de swap, pas un virement decoupe.")},
        "v6BFsgbJ5YaYZxEgapUXi5F2AoAZFDPaZdsspvfJBhq": {
            "role": "DECOUPEUR A USAGE UNIQUE — la piece maitresse",
            "genese_atteinte": True, "n_signatures_dans_toute_sa_vie": 24,
            "vie": ["2024-12-13 12:18:36 : recoit 15.000000000 SOL de "
                    "G2twzNaSnSnveK4Zys6usTNwG3pY8RruGaKvZycd7k2S",
                    "12:24:54 → 1.700000000 SOL a 3vzEogg… (acheteur #11)",
                    "12:25:06 → 1.880000000 SOL a 4bybJyL… (acheteur #5)",
                    "12:25:16 → 1.440000000 SOL a bgF2ueq… (acheteur #9)",
                    "12:25:27 → 1.970000000 SOL a DAss7Hi… (acheteur #7)",
                    "12:25:37 → 3.000000000 SOL a GLtrMWX… (acheteur #6)",
                    "12:26:25 → 5.000000000 SOL a AdoQbzXCMHiXba5Xz9iFj5FgnK6AYZTFa24J3iYhz2M9 "
                    "(6e destinataire, N'A PAS achete ce token)",
                    "puis silence jusqu'a une poussiere en avril 2025"],
            "total_sorti_sol": 14.99,
            "delai_dernier_versement_creation_token": "2 h 24 min",
            "lecture": ("15 SOL entres, 6 versements sortis en 92 secondes, 5 des 6 destinataires "
                        "achetent le token 2 h plus tard dans la meme seconde. C'est la signature "
                        "ODIN, en plus net : ODIN avait 4 x 3 SOL depuis un distributeur a 80 000 "
                        "transactions ; ici le decoupeur n'a existe que pour cette operation.")},
        "G2twzNaSnSnveK4Zys6usTNwG3pY8RruGaKvZycd7k2S": {
            "role": "distributeur prive en amont du decoupeur",
            "genese_atteinte": True, "n_signatures_totales": 63,
            "vie_utc": ["2024-12-02 20:15:54", "2025-05-06 06:21:18"],
            "entrees": "~10 petites adresses, montants precis a la 9e decimale (sorties de swap)",
            "sorties_rondes_sol": [21.0, 15.0, 11.0],
            "croisement_G2Y": "AUCUN sur son historique complet (genese atteinte)"},
    },
    "achats_groupes_au_lamport_pres": [
        {"montant_sol": 1.512044279, "slot": 307237642, "n": 3, "rangs": [8, 12, 14],
         "flotte": "B"},
        {"montant_sol": 0.563089281, "slot": 307237659, "n": 3, "rangs": [19, 22, 24],
         "flotte": "C"},
        {"montant_sol": 2.070240160, "slot": 307237685, "n": 3, "rangs": [34, 35, 36],
         "flotte": "aucune (genese non atteinte)"},
    ],
    "verdict": e3["verdict"],
}

json.dump(res, open(f"{D}/SYNTHESE_h2w6gm6jz.json", "w"), indent=1, ensure_ascii=False)
print("-> SYNTHESE_h2w6gm6jz.json")
print(f"couverture : genese {len(gen)}/{n} · prebuy {e3['n_prebuy_reached']}/{n}")
print(f"verdict : {res['verdict']}")
