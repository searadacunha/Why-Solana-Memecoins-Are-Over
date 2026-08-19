#!/usr/bin/env python3
"""Etape 5 : cible contre temoins, le decoupage est-il specifique ou banal ?

Lit les e3_splits_*.json passes en argument et les e2_funding_*.json correspondants, ecrit
e5_synthese.json.

Des portefeuilles finances au meme moment pour des montants voisins arrivent naturellement sur
pump.fun : les acheteurs precoces sortent souvent du meme robot, du meme echange, de la meme
fenetre de retrait. Sans taux de faux positifs mesure sur des tokens temoins, un motif observe sur
la cible ne prouve rien.

Les temoins ont ete choisis a la seconde pres autour de la creation de la cible, sur des criteres
qui ne touchent ni au financement, ni a l'origine des portefeuilles, ni a G2Y. La comparaison est
donc licite.

Ce qui est compare :
- part des premiers acheteurs impliques dans un decoupage (meme transaction, ou meme montant/moment)
- part des premiers acheteurs partageant un bailleur commun
- nombre d'acheteurs precoces distincts (un token trop pauvre donne un faux negatif mecanique)
- couverture de la mesure : geneses et fenetres pre-achat atteintes

Usage :
    python3 etape5_synthese.py --splits e3_splits_OPTIMUS.json --splits e3_splits_faith.json ...
"""
from __future__ import annotations
import argparse, json

CIBLES = {"OPTIMUS"}
# ODIN sert de temoin positif : cas de decoupage deja etabli. Si le pipeline ne le retrouve pas,
# c'est le pipeline qui est en cause, et aucun resultat negatif sur les autres tokens ne vaut.
POSITIF = {"ODIN_POSITIF"}


def stats(path):
    d = json.load(open(path))
    f = json.load(open(path.replace("e3_splits_", "e2_funding_")))
    wallets = f["wallets"]
    n = len(wallets)
    in_split = set()
    for c in d["A_meme_transaction"]:
        in_split |= set(c["wallets"])
    for c in d["B_meme_montant_meme_moment"]:
        in_split |= set(c["wallets"])
    shared = set()
    for c in d["C_bailleurs_communs_PRIVES"]:
        shared |= set(c["wallets"])
    return {
        "label": d["label"], "mint": d["mint"],
        "role": ("cible" if d["label"] in CIBLES else
                 "temoin_positif" if d["label"] in POSITIF else "temoin"),
        "n_early_buyers": n,
        "trop_pauvre_pour_conclure": n < 10,
        "n_inflows": d["n_inflows_total"],
        "genesis_reached": f["n_genesis_reached"], "genesis_missing": f["n_genesis_NOT_reached"],
        "prebuy_reached": f["n_prebuy_window_reached"], "prebuy_missing": f["n_prebuy_NOT_reached"],
        "n_A_meme_tx": len(d["A_meme_transaction"]),
        "n_B_meme_montant": len(d["B_meme_montant_meme_moment"]),
        "n_C_bailleurs_prives": len(d["C_bailleurs_communs_PRIVES"]),
        "n_C_bailleurs_infra": len(d["C_bailleurs_communs_infrastructure_sans_valeur"]),
        "wallets_in_split": len(in_split),
        "pct_wallets_in_split": round(100.0 * len(in_split) / n, 1) if n else None,
        "wallets_sharing_funder": len(shared),
        "pct_wallets_sharing_funder": round(100.0 * len(shared) / n, 1) if n else None,
        "biggest_A_cluster": max((c["n_wallets"] for c in d["A_meme_transaction"]), default=0),
        "biggest_B_cluster": max((c["n_wallets"] for c in d["B_meme_montant_meme_moment"]), default=0),
        "verdict": d["verdict"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", action="append", required=True)
    ap.add_argument("--out", default="e5_synthese.json")
    a = ap.parse_args()

    rows = [stats(p) for p in a.splits]
    cible = [r for r in rows if r["role"] == "cible"]
    tem = [r for r in rows if r["role"] == "temoin"]
    usable = [r for r in tem if not r["trop_pauvre_pour_conclure"]]

    concl = {
        "n_temoins": len(tem), "n_temoins_exploitables": len(usable),
        "temoins_ecartes_trop_pauvres": [r["label"] for r in tem if r["trop_pauvre_pour_conclure"]],
        "temoins_avec_decoupage_A": sum(1 for r in usable if r["n_A_meme_tx"] > 0),
        "temoins_avec_decoupage_B": sum(1 for r in usable if r["n_B_meme_montant"] > 0),
        "temoins_avec_bailleur_prive_commun": sum(1 for r in usable if r["n_C_bailleurs_prives"] > 0),
        "pct_split_cible": cible[0]["pct_wallets_in_split"] if cible else None,
        "pct_split_temoins": ([r["pct_wallets_in_split"] for r in usable]),
    }
    json.dump({"comparaison": rows, "conclusion": concl}, open(a.out, "w"), indent=1)

    w = 13
    print(f"\n{'token':<{w}} {'role':<14} {'ach.':>4} {'gen':>7} {'preb':>7} "
          f"{'A':>3} {'B':>3} {'C':>3} {'%split':>7} {'%bailleur':>9}")
    print("-" * 78)
    for r in sorted(rows, key=lambda r: (r["role"] != "cible", r["role"] != "temoin_positif", r["label"])):
        print(f"{r['label']:<{w}} {r['role']:<14} {r['n_early_buyers']:>4} "
              f"{r['genesis_reached']}/{r['n_early_buyers']:<4} "
              f"{r['prebuy_reached']}/{r['n_early_buyers']:<4} "
              f"{r['n_A_meme_tx']:>3} {r['n_B_meme_montant']:>3} {r['n_C_bailleurs_prives']:>3} "
              f"{str(r['pct_wallets_in_split']):>7} {str(r['pct_wallets_sharing_funder']):>9}")
    print(f"\n  A = financements dans une meme transaction · B = meme montant/meme moment"
          f" · C = bailleur commun a >= 2 acheteurs")
    print(f"  temoins exploitables : {len(usable)}/{len(tem)}"
          f"  (ecartes, < 10 acheteurs : {concl['temoins_ecartes_trop_pauvres']})")
    print(f"  temoins presentant A : {concl['temoins_avec_decoupage_A']}/{len(usable)} · "
          f"B : {concl['temoins_avec_decoupage_B']}/{len(usable)} · "
          f"C : {concl['temoins_avec_bailleur_prive_commun']}/{len(usable)}")
    print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
