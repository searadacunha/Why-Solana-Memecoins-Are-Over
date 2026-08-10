#!/usr/bin/env python3
"""Premiers acheteurs d'un token, puis recherche d'un SPLIT dans leur financement.

DÉMARCHE
--------
Les principaux détenteurs *actuels* d'un token ancien ne disent rien de son lancement : la supply a
changé de mains depuis. On remonte donc aux PREMIÈRES transactions du mint pour identifier ceux qui
étaient là au début, puis on regarde comment ces portefeuilles ont été financés.

Si un opérateur a découpé une somme via un service de swap pour alimenter N portefeuilles, ceux-ci
ont reçu des montants quasi identiques dans un intervalle court. C'est cette signature qu'on cherche.

USAGE
-----
    python3 04_early_buyers_funding.py --mint <MINT> --created 2024-11-22 --n-early 40

Client Helius unique : rpc_client.py (clés depuis $HELIUS_API_KEYS / .env, voir settings.py).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client  # noqa: E402
import settings  # noqa: E402
from splitlib import find_splits  # noqa: E402

LAMPORTS = 1_000_000_000
# Bande d'entrées plus large ici : on ne connaît pas le calibre de l'époque. Ce filtre local
# reste ; le regroupement (REL_TOL / WINDOW_S / MIN_CLUSTER) vit désormais dans splitlib.
MIN_SOL, MAX_SOL = 0.5, 50.0


def oldest_signatures(addr: str, stop_ts: int, max_pages: int = 400) -> list:
    """Pagine jusqu'à atteindre stop_ts, du plus ancien au plus récent. Indispensable : une
    pagination bornée trop court ne remonte jamais à la création sur une adresse active, et fait
    conclure à tort — un budget de pages épuisé LÈVE donc au lieu de rendre un historique
    partiel."""
    out, _ = rpc_client.walk_sigs(addr, until_ts=stop_ts, max_pages=max_pages)
    return sorted(out, key=lambda s: s.get("blockTime") or 0)


def early_buyers(mint: str, created_ts: int, n_early: int, window_h: int = 48) -> tuple:
    """Signataires des premières transactions touchant le mint."""
    sigs = oldest_signatures(mint, created_ts - 3600)
    if not sigs:
        return [], None
    t0 = sigs[0].get("blockTime")
    print(f"  1re transaction du mint : {dt.datetime.fromtimestamp(t0, dt.UTC):%Y-%m-%d %H:%M} UTC")
    early = [s for s in sigs if (s.get("blockTime") or 0) <= t0 + window_h * 3600]
    buyers, order = {}, []
    for s in early:
        if len(order) >= n_early:
            break
        tx = rpc_client.tx(s["signature"])
        if not tx:
            continue
        try:
            keys = tx["transaction"]["message"]["accountKeys"]
            signer = next(k["pubkey"] for k in keys if k.get("signer"))
        except Exception:
            continue
        if signer not in buyers:
            buyers[signer] = s.get("blockTime")
            order.append(signer)
        time.sleep(0.1)
    return order, t0


def all_signatures(addr: str, max_pages: int = 60) -> tuple:
    """TOUTES les signatures d'une adresse, de la plus ancienne à la plus récente.

    ⚠️ Ne pas borner cette pagination trop court. Le financement initial d'un portefeuille se trouve
    dans ses PREMIÈRES transactions ; une pagination partielle ne rend que les plus récentes et fait
    conclure à tort à l'absence de financement. On s'arrête quand une page revient incomplète —
    signe qu'on a atteint la genèse — et on signale si le plafond a été touché avant.
    """
    out, before, complete = [], None, False
    for _ in range(max_pages):
        page = rpc_client.sigs(addr, 1000, before)
        if not page:
            complete = True
            break
        out.extend(page)
        if len(page) < 1000:
            complete = True
            break
        before = page[-1]["signature"]
        time.sleep(0.08)
    return sorted(out, key=lambda s: s.get("blockTime") or 0), complete


def funding_events(wallet: str) -> list:
    """Entrées de SOL notables d'un portefeuille, mesurées par delta de solde.

    On lit les 40 PREMIÈRES transactions de son existence : c'est là que se trouve son financement.
    """
    sigs, complete = all_signatures(wallet)
    if not complete:
        print(f"     ⚠️ {wallet[:12]}… genese NON atteinte (trop actif) — resultat non concluant",
              flush=True)
    out = []
    for s in sigs[:40]:
        tx = rpc_client.tx(s["signature"])
        if not tx:
            continue
        try:
            keys = [k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"]]
            i = keys.index(wallet)
            d = (tx["meta"]["postBalances"][i] - tx["meta"]["preBalances"][i]) / LAMPORTS
        except Exception:
            continue
        if MIN_SOL <= d <= MAX_SOL:
            out.append((d, tx.get("blockTime") or 0))
        time.sleep(0.08)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mint", required=True)
    ap.add_argument("--created", required=True, help="date de creation approx., AAAA-MM-JJ")
    ap.add_argument("--n-early", type=int, default=40)
    ap.add_argument("--out", default=os.path.join(settings.DATA, "split", "early_buyers.json"))
    a = ap.parse_args()

    created_ts = int(dt.datetime.strptime(a.created, "%Y-%m-%d")
                     .replace(tzinfo=dt.UTC).timestamp())
    print(f"Mint {a.mint[:16]}… — remontee jusqu'a {a.created}", flush=True)
    buyers, t0 = early_buyers(a.mint, created_ts, a.n_early)
    print(f"\n{len(buyers)} premiers signataires identifies", flush=True)

    funding = {}
    for k, w in enumerate(buyers, 1):
        funding[w] = funding_events(w)
        print(f"  [{k}/{len(buyers)}] {w[:14]}… {len(funding[w])} entrees", flush=True)

    clusters = find_splits(funding)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"mint": a.mint, "first_tx_ts": t0, "n_early_buyers": len(buyers),
               "n_clusters": len(clusters), "clusters": clusters,
               "funding": {w: [[round(x, 9), t] for x, t in v] for w, v in funding.items()}},
              open(a.out, "w"), indent=1)

    print(f"\n=== {len(clusters)} splits detectes parmi les premiers acheteurs ===")
    for c in clusters[:12]:
        print(f"  {c['date']}  {c['amount_sol']:.9f} SOL x {c['n_wallets']} portefeuilles "
              f"({c['span_seconds']}s)")
    if not clusters:
        print("  Aucun. Resultat NEGATIF a conserver tel quel : soit le financement etait different,")
        print("  soit la fenetre/les seuils ne conviennent pas. Ne pas forcer les parametres.")


if __name__ == "__main__":
    main()
