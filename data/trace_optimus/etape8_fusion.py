#!/usr/bin/env python3
"""ETAPE 8 — fusion des mesures M2 (etape 2) et M1 rattrapee (etape 7).

Produit un fichier de financement au meme format que `e2_funding_OPTIMUS.json`, mais ou
`genesis_reached` reflete la pagination REELLEMENT poussee jusqu'a la naissance, et ou les entrees de
naissance des 16 portefeuilles rattrapes sont presentes. C'est ce fichier que l'etape 3 doit relire :
la signature de type ODIN (financement de naissance) devient alors TESTEE sur ces portefeuilles.

La deduplication se fait par signature : un portefeuille ne vivant que quelques jours avant l'achat a
ses transactions de naissance DANS la fenetre pre-achat, et elles seraient sinon comptees deux fois.

USAGE
    python3 etape8_fusion.py
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="OPTIMUS")
    a = ap.parse_args()
    E2 = os.path.join(HERE, f"e2_funding_{a.label}.json")
    E7 = os.path.join(HERE, f"e7_genese_M1_{a.label}.json")
    OUT = os.path.join(HERE, f"e8_funding_complet_{a.label}.json")
    d2 = json.load(open(E2))
    d7 = json.load(open(E7))
    by7 = {w["wallet"]: w for w in d7["wallets"]}

    wallets, n_added = [], 0
    for w in d2["wallets"]:
        r = by7.get(w["wallet"])
        w = dict(w)
        if r:
            w["genesis_reached"] = bool(r["genesis_reached"])
            w["genesis_recovered_at_etape7"] = bool(r["genesis_reached"])
            w["etape7_stop_reason"] = r["stop_reason"]
            w["etape7_pages_added"] = r["pages_added"]
            w["n_signatures_total"] = max(w["n_signatures_total"], r["n_signatures_total"])
            w["oldest_seen_ts"] = r["oldest_seen_ts"] or w.get("oldest_seen_ts")
            w["oldest_seen_utc"] = r["oldest_seen_utc"] or w.get("oldest_seen_utc")
            w["days_alive_before_first_buy"] = r["days_alive_before_first_buy"]
            if r["genesis_reached"]:
                have = {f.get("signature") for f in w["inflows"]}
                for f in r["M1_inflows"]:
                    if f.get("signature") not in have:
                        w["inflows"].append(f)
                        have.add(f.get("signature"))
                        n_added += 1
                w["inflows"].sort(key=lambda f: f["ts"])
                w["measurement_failure"] = None
            else:
                w["measurement_failure"] = f"genese non atteinte ({r['stop_reason']})"
        else:
            w["genesis_recovered_at_etape7"] = False
        wallets.append(w)

    n_g = sum(1 for w in wallets if w["genesis_reached"])
    n_p = sum(1 for w in wallets if w.get("prebuy_window_reached"))
    res = {"label": d2["label"], "mint": d2["mint"], "n_wallets": len(wallets),
           "n_genesis_reached": n_g, "n_genesis_NOT_reached": len(wallets) - n_g,
           "n_prebuy_window_reached": n_p, "n_prebuy_NOT_reached": len(wallets) - n_p,
           "n_inflows_M1_ajoutees_etape7": n_added,
           "wallets_without_genesis": [w["wallet"] for w in wallets if not w["genesis_reached"]],
           "wallets_without_prebuy": [w["wallet"] for w in wallets
                                      if not w.get("prebuy_window_reached")],
           "wallets": wallets}
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"geneses atteintes : {n_g}/{len(wallets)} · fenetres pre-achat : {n_p}/{len(wallets)} · "
          f"{n_added} entrees de naissance ajoutees -> {OUT}")
    for w in wallets:
        if not w["genesis_reached"]:
            print(f"  SANS GENESE : #{w['buy_rank']} {w['wallet']} "
                  f"({w['n_signatures_total']} sigs vues, remonte a {w['oldest_seen_utc']})")


if __name__ == "__main__":
    main()
