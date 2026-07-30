#!/usr/bin/env python3
"""ETAPE 10 — synthese finale OPTIMUS, avec couverture de mesure declaree.

Elle remplace l'etape 5 sur un seul point, mais decisif : elle accepte des paires
(financement, decoupage) explicites, ce qui permet de comparer la cible et les temoins sur des
mesures de MEME PROFONDEUR. Comparer une cible dont les geneses ont ete rattrapees a des temoins dont
elles ne l'ont pas ete fabriquerait un ecart artificiel — la cible aurait simplement ete mieux
mesuree. La colonne `gen` doit donc etre lue avant toute autre.

Le temoin POSITIF (ODIN) valide le detecteur : s'il ne ressort pas, aucun negatif ne vaut.

USAGE
    python3 etape10_synthese.py --pair OPTIMUS:e8_funding_complet_OPTIMUS.json:e8_splits_OPTIMUS.json \
                                --pair Calm:...:... [--out e10_synthese.json]
"""
from __future__ import annotations
import argparse, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
CIBLES = {"OPTIMUS"}
POSITIF = {"ODIN_POSITIF"}


def stats(label, fpath, spath):
    f = json.load(open(fpath))
    d = json.load(open(spath))
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
    n_g = sum(1 for w in wallets if w["genesis_reached"])
    n_p = sum(1 for w in wallets if w.get("prebuy_window_reached"))
    return {"label": label, "mint": d["mint"],
            "role": ("cible" if label in CIBLES else
                     "temoin_positif" if label in POSITIF else "temoin"),
            "n_early_buyers": n, "trop_pauvre_pour_conclure": n < 10,
            "n_inflows": d["n_inflows_total"],
            "genesis_reached": n_g, "genesis_missing": n - n_g,
            "pct_genesis": round(100.0 * n_g / n, 1) if n else None,
            "prebuy_reached": n_p, "prebuy_missing": n - n_p,
            "n_A_meme_tx": len(d["A_meme_transaction"]),
            "n_B_meme_montant": len(d["B_meme_montant_meme_moment"]),
            "n_C_bailleurs_prives": len(d["C_bailleurs_communs_PRIVES"]),
            "n_C_bailleurs_infra": len(d["C_bailleurs_communs_infrastructure_sans_valeur"]),
            "wallets_in_split": len(in_split),
            "pct_wallets_in_split": round(100.0 * len(in_split) / n, 1) if n else None,
            "wallets_sharing_funder": len(shared),
            "pct_wallets_sharing_funder": round(100.0 * len(shared) / n, 1) if n else None,
            "biggest_A_cluster": max((c["n_wallets"] for c in d["A_meme_transaction"]), default=0),
            "biggest_B_cluster": max((c["n_wallets"] for c in d["B_meme_montant_meme_moment"]),
                                     default=0),
            "C_bailleurs_prives": d["C_bailleurs_communs_PRIVES"],
            "verdict": d["verdict"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", action="append", required=True,
                    help="label:fichier_financement:fichier_decoupage")
    ap.add_argument("--out", default=os.path.join(HERE, "e10_synthese.json"))
    a = ap.parse_args()

    rows = []
    for p in a.pair:
        label, fpath, spath = p.split(":", 2)
        rows.append(stats(label, os.path.join(HERE, fpath), os.path.join(HERE, spath)))

    cible = [r for r in rows if r["role"] == "cible"]
    pos = [r for r in rows if r["role"] == "temoin_positif"]
    tem = [r for r in rows if r["role"] == "temoin"]
    usable = [r for r in tem if not r["trop_pauvre_pour_conclure"]]

    # Le detecteur est-il valide ? Le temoin positif doit ressortir en A (meme transaction).
    detecteur_valide = bool(pos and pos[0]["n_A_meme_tx"] > 0)
    concl = {
        "detecteur_valide_par_temoin_positif": detecteur_valide,
        "n_temoins": len(tem), "n_temoins_exploitables": len(usable),
        "temoins_ecartes_trop_pauvres": [r["label"] for r in tem
                                         if r["trop_pauvre_pour_conclure"]],
        "temoins_avec_A": sum(1 for r in usable if r["n_A_meme_tx"] > 0),
        "temoins_avec_B": sum(1 for r in usable if r["n_B_meme_montant"] > 0),
        "temoins_avec_C_prive": sum(1 for r in usable if r["n_C_bailleurs_prives"] > 0),
        "cible_A": cible[0]["n_A_meme_tx"] if cible else None,
        "cible_B": cible[0]["n_B_meme_montant"] if cible else None,
        "cible_C_prive": cible[0]["n_C_bailleurs_prives"] if cible else None,
        "portefeuilles_temoins_total": sum(r["n_early_buyers"] for r in tem),
        "comparabilite_profondeur": {r["label"]: f"{r['genesis_reached']}/{r['n_early_buyers']}"
                                     for r in rows},
    }
    json.dump({"comparaison": rows, "conclusion": concl}, open(a.out, "w"), indent=1)

    w = 14
    print(f"\n{'token':<{w}} {'role':<15} {'ach.':>4} {'gen':>8} {'preb':>8} "
          f"{'A':>3} {'B':>3} {'C':>3} {'%split':>7} {'%bailleur':>9}")
    print("-" * 84)
    order = {"cible": 0, "temoin_positif": 1, "temoin": 2}
    for r in sorted(rows, key=lambda r: (order[r["role"]], r["label"])):
        print(f"{r['label']:<{w}} {r['role']:<15} {r['n_early_buyers']:>4} "
              f"{r['genesis_reached']}/{r['n_early_buyers']:<5} "
              f"{r['prebuy_reached']}/{r['n_early_buyers']:<5} "
              f"{r['n_A_meme_tx']:>3} {r['n_B_meme_montant']:>3} {r['n_C_bailleurs_prives']:>3} "
              f"{str(r['pct_wallets_in_split']):>7} {str(r['pct_wallets_sharing_funder']):>9}")
    print("\n  A = financements dans une MEME transaction · B = meme montant/meme moment "
          "· C = bailleur PRIVE commun a >= 2 acheteurs")
    print(f"  detecteur valide par le temoin positif ODIN : "
          f"{'OUI' if detecteur_valide else 'NON — aucun negatif ne vaut'}")
    print(f"  temoins exploitables : {len(usable)}/{len(tem)} "
          f"(ecartes < 10 acheteurs : {concl['temoins_ecartes_trop_pauvres']})")
    print(f"  temoins presentant A : {concl['temoins_avec_A']}/{len(usable)} · "
          f"B : {concl['temoins_avec_B']}/{len(usable)} · "
          f"C prive : {concl['temoins_avec_C_prive']}/{len(usable)}")
    print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
