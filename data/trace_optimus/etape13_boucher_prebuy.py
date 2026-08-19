#!/usr/bin/env python3
"""Etape 13 : combler la derniere fenetre pre-achat manquante.

Lit le cache complet de l'etape 7 (cache_sigs_full/) et met a jour e2_funding_OPTIMUS.json sur
place.

nya666pQkP3PzWxi7JngU3rRMHuc7zbLK8c8wxQ4qpT (28e acheteur d'OPTIMUS) est le seul portefeuille dont
la mesure M2 restait vide : a l'etape 2 la pagination avait ete abandonnee (~4 000 signatures/jour,
projection a plus de 2 700 pages). L'etape 7 a atteint sa genese apres 2 332 569 signatures. Le
cache complet etant sur disque, la fenetre pre-achat se lit sans appel de pagination
supplementaire, il ne reste qu'a relire les transactions de la fenetre.

Sans cette etape la couverture restait a 39/40 fenetres pre-achat et tout negatif devait etre traite
comme partiel. Avec elle la couverture est complete et un negatif devient interpretable.

Usage :
    python3 etape13_boucher_prebuy.py
"""
from __future__ import annotations
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_trace as L
from etape2_financement import inflows_from, MIN_INFLOW, PREBUY_DAYS, PREBUY_MAX_TX
from etape7_genese_M1 import load_keys, get_transactions_with, log

W = "nya666pQkP3PzWxi7JngU3rRMHuc7zbLK8c8wxQ4qpT"
E2 = os.path.join(HERE, "e2_funding_OPTIMUS.json")
CACHE = os.path.join(HERE, "cache_sigs_full", f"{W}.json")


def main():
    keys = load_keys()
    d = json.load(open(E2))
    tgt = next(w for w in d["wallets"] if w["wallet"] == W)
    first_buy_ts = tgt["first_buy_ts"]
    start = first_buy_ts - PREBUY_DAYS * 86400

    if not os.path.exists(CACHE):
        raise SystemExit(
            "%s absent.\n"
            "  cache_sigs_full/ est un miroir de signatures git-ignore, il n'existe\n"
            "  pas dans un clone. Rejouer la collecte amont pour le reconstituer."
            % CACHE)
    c = json.load(open(CACHE))
    if not c.get("genesis"):
        sys.exit("le cache complet n'a pas la genese : ne pas conclure sur ce portefeuille")
    sigs = c["sigs"]
    win = [s for s in sigs if start <= (s.get("blockTime") or 0) <= first_buy_ts]
    log(f"{W[:12]} : {len(sigs)} signatures en cache (genese atteinte), "
        f"{len(win)} dans la fenetre pre-achat {L.utc(start)} -> {L.utc(first_buy_ts)}")

    picks = [s["signature"] for s in win[:PREBUY_MAX_TX]]
    txs = get_transactions_with(keys[0], picks)
    if "__error__" in txs:
        sys.exit(txs["__error__"])
    inflows = []
    for sig in picks:
        inflows.extend(inflows_from(txs, [sig], W, MIN_INFLOW, "M2_prebuy"))
    inflows.sort(key=lambda f: f["ts"])
    log(f"  {len(txs)}/{len(picks)} transactions relues · {len(inflows)} entrees de fonds")
    for f in inflows[:10]:
        log(f"    {f['utc']} +{f['amount_sol']:.9f} SOL [{f['calibre']}] "
            f"{f['nature']} src={str(f['source'])[:44]} {f.get('source_known') or ''}")

    # On ecrit dans le fichier de l'etape 2 : la fenetre est desormais couverte et les entrees
    # trouvees doivent entrer dans la detection de decoupage comme celles des 39 autres.
    have = {x.get("signature") for x in tgt["inflows"]}
    tgt["inflows"].extend([f for f in inflows if f.get("signature") not in have])
    tgt["inflows"].sort(key=lambda f: f["ts"])
    tgt["prebuy_window_reached"] = True
    tgt["hyperactif_non_mesurable"] = False
    tgt["n_tx_in_prebuy_window"] = len(win)
    tgt["n_signatures_total"] = len(sigs)
    tgt["prebuy_window_days_covered"] = float(PREBUY_DAYS)
    tgt["measurement_failure"] = None
    tgt["note_etape13"] = ("fenetre pre-achat lue depuis le cache complet de l'etape 7 "
                           f"({len(sigs)} signatures, genese atteinte)")
    n_p = sum(1 for w in d["wallets"] if w.get("prebuy_window_reached"))
    d["n_prebuy_window_reached"] = n_p
    d["n_prebuy_NOT_reached"] = len(d["wallets"]) - n_p
    d["wallets_without_prebuy"] = [w["wallet"] for w in d["wallets"]
                                   if not w.get("prebuy_window_reached")]
    json.dump(d, open(E2, "w"), indent=1)
    log(f"  fenetres pre-achat couvertes : {n_p}/{len(d['wallets'])} -> {E2}")


if __name__ == "__main__":
    main()
