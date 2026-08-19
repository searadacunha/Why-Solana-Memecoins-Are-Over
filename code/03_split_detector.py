#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Détecteur de split, la pièce centrale du dépôt.

Hypothèse testée : un opérateur qui veut faire passer N portefeuilles pour N acheteurs
indépendants doit d'abord les financer. S'il découpe une somme via un service de swap, les
portefeuilles reçoivent des montants quasi identiques dans une fenêtre temporelle courte. Un
montant précis à la neuvième décimale (ex. 1.393934883 SOL) répété sur plusieurs adresses ne
se produit pas par hasard : c'est la signature d'un découpage unique.

Le script fait deux choses. Pour un ensemble de portefeuilles (ex. les principaux détenteurs
d'un token), il collecte les entrées de SOL et les regroupe par quasi-égalité de montant et
proximité temporelle (splitlib). Il mesure ensuite le taux de faux positifs sur un groupe
témoin de portefeuilles sans lien : sans cette mesure, le nombre de splits ne veut rien dire,
des montants proches se produisent naturellement.

Outil exploratoire, hors du pipeline reproductible (absent de run_all.py). La mesure publiée
du signal de split est docs/SPLIT_PHASE1.md + a1_null_model.py / a2_recount.py.

Client Helius unique (rpc_client.py) : les clés viennent de l'environnement
($HELIUS_API_KEYS, ou .env non versionné, voir settings.py) et un échec réseau lève au lieu
de se déguiser en résultat vide (docs/PITFALLS.md, règle n°2).

Usage :
    python3 code/03_split_detector.py --mint <MINT> --top 30
    python3 code/03_split_detector.py --wallets w1,w2,w3
    python3 code/03_split_detector.py --mint <MINT> --control 40   # + groupe témoin
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client  # noqa: E402
import settings  # noqa: E402
from splitlib import MIN_CLUSTER, REL_TOL, WINDOW_S, find_splits  # noqa: E402

LAMPORTS = 1_000_000_000

# Fenêtre de montants retenue : en dessous, on capte le bruit (dust, frais) ;
# au-dessus, les transferts deviennent trop rares et hétérogènes pour former un split.
MIN_SOL, MAX_SOL = 1.0, 20.0

# getBlock sur un slot sauté renvoie une erreur JSON-RPC qui est une réponse
# légitime (« slot skipped »), pas une panne : on la tolère en None.
SKIPPED_SLOT_CODES = (-32007, -32009, -32004)


def top_holders(mint: str, n: int) -> list[str]:
    """Principaux détenteurs d'un token, via leurs comptes de token."""
    res = rpc_client.rpc("getTokenLargestAccounts", [mint]) or {}
    owners: list[str] = []
    for acc in (res.get("value") or [])[:n]:
        info = rpc_client.account_info(acc["address"], encoding="jsonParsed") or {}
        try:
            owners.append(info["data"]["parsed"]["info"]["owner"])
        except (KeyError, TypeError):
            continue
        time.sleep(0.15)
    return owners


def incoming_sol(wallet: str, max_pages: int = 3) -> list[tuple[float, int]]:
    """Entrées de SOL d'un portefeuille : [(montant_sol, timestamp)].

    On lit le delta de solde du portefeuille dans chaque transaction plutôt que les transferts
    système : le financement est souvent obfusqué (closeAccount d'un compte wrappé), auquel cas
    aucun transfert système n'apparaît alors que le solde augmente bien.
    """
    sigs: list[dict] = []
    before: Optional[str] = None
    for _ in range(max_pages):
        page = rpc_client.sigs(wallet, 1000, before)
        if not page:
            break
        sigs.extend(page)
        if len(page) < 1000:
            break
        before = page[-1]["signature"]
    out: list[tuple[float, int]] = []
    for s in sigs[-60:]:                     # les plus anciennes = le financement initial
        tx = rpc_client.tx(s["signature"])
        if not tx:
            continue
        try:
            keys = [k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"]]
            i = keys.index(wallet)
            delta = (tx["meta"]["postBalances"][i] - tx["meta"]["preBalances"][i]) / LAMPORTS
        except (KeyError, ValueError, TypeError):
            continue
        if MIN_SOL <= delta <= MAX_SOL:
            out.append((delta, tx.get("blockTime") or 0))
        time.sleep(0.12)
    return out


def collect(wallets: list[str], label: str) -> dict[str, list[tuple[float, int]]]:
    funding: dict[str, list[tuple[float, int]]] = {}
    for k, w in enumerate(wallets, 1):
        funding[w] = incoming_sol(w)
        print(f"  [{label}] {k}/{len(wallets)} {w[:12]}… {len(funding[w])} entrées", flush=True)
    return funding


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mint")
    ap.add_argument("--wallets")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--control", type=int, default=0,
                    help="taille du groupe témoin (portefeuilles sans lien) pour le taux de faux positifs")
    ap.add_argument("--out", default=os.path.join(settings.DATA, "split", "result.json"))
    a = ap.parse_args()

    if a.wallets:
        wallets = [w.strip() for w in a.wallets.split(",") if w.strip()]
    elif a.mint:
        wallets = top_holders(a.mint, a.top)
    else:
        sys.exit("Fournir --mint ou --wallets.")
    print(f"{len(wallets)} portefeuilles à analyser", flush=True)

    clusters = find_splits(collect(wallets, "cible"))
    result = {"mint": a.mint, "n_wallets": len(wallets), "clusters": clusters,
              "n_clusters": len(clusters),
              "wallets_in_cluster": len({w for c in clusters for w in c["wallets"]}),
              "params": {"min_sol": MIN_SOL, "max_sol": MAX_SOL, "rel_tol": REL_TOL,
                         "window_s": WINDOW_S, "min_cluster": MIN_CLUSTER}}

    # Groupe témoin : des portefeuilles pris au hasard parmi des transactions récentes non liées.
    # C'est lui qui donne le taux de faux positifs.
    if a.control:
        slot = rpc_client.rpc("getSlot", [])
        blk = rpc_client.rpc(
            "getBlock", [slot - 200, {"maxSupportedTransactionVersion": 0,
                                      "transactionDetails": "accounts", "rewards": False}],
            tolerate_codes=SKIPPED_SLOT_CODES) or {}
        pool: list[str] = []
        for tx in (blk.get("transactions") or []):
            for k in (tx.get("transaction", {}).get("accountKeys") or []):
                pk = k.get("pubkey") if isinstance(k, dict) else k
                if pk and pk not in wallets:
                    pool.append(pk)
        random.seed(0)
        ctrl = random.sample(pool, min(a.control, len(pool))) if pool else []
        if ctrl:
            cc = find_splits(collect(ctrl, "témoin"))
            result["control"] = {"n_wallets": len(ctrl), "n_clusters": len(cc),
                                 "wallets_in_cluster": len({w for c in cc for w in c["wallets"]})}

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(result, open(a.out, "w"), indent=1)

    print(f"\n=== {len(clusters)} splits détectés sur {len(wallets)} portefeuilles ===")
    for c in clusters[:10]:
        print(f"  {c['amount_sol']:.9f} SOL × {c['n_wallets']} portefeuilles "
              f"(étalés sur {c['span_seconds']}s)")
    if result.get("control"):
        k = result["control"]
        print(f"\n  GROUPE TÉMOIN : {k['n_clusters']} splits sur {k['n_wallets']} portefeuilles")
        print("  → l'écart entre cible et témoin est la seule mesure qui compte.")


if __name__ == "__main__":
    main()
