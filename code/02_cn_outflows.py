#!/usr/bin/env python3
"""Cherche les SPLITS dans les sorties d'une adresse, sur une FENÊTRE DE DATES donnée.

On part de la SOURCE plutôt que des détenteurs : toutes les sorties de l'adresse sur la période
visée sont collectées, puis regroupées par montant quasi identique reçu dans un intervalle court.
Chaque groupe est un découpage — donc un ensemble de portefeuilles vraisemblablement contrôlés par
la même main.

POURQUOI LE FILTRE DE DATES EST ESSENTIEL
-----------------------------------------
Lire une signature coûte 1/1000e d'appel (elles arrivent par pages de 1000) ; lire une transaction
coûte un appel entier. Sur une adresse de service qui traite ~200 000 transactions par mois, tout
lire est hors de portée. On pagine donc les signatures — c'est rapide — en ne retenant que celles
de la fenêtre, et on ne lit en détail QUE celles-là.

USAGE
-----
    # explorer le débit d'une adresse, sans rien lire en détail
    python3 02_cn_outflows.py --addr <ADDR> --from 2024-10-01 --to 2025-02-28

    # collecter les sorties de la fenêtre et détecter les splits
    python3 02_cn_outflows.py --addr <ADDR> --from 2025-12-01 --to 2025-12-08 --collect

Client Helius unique : rpc_client.py (clés depuis $HELIUS_API_KEYS / .env, voir settings.py).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client  # noqa: E402
import settings  # noqa: E402
from splitlib import find_splits  # noqa: E402

LAMPORTS = 1_000_000_000

# Fenêtre de montants : en dessous on capte le bruit (dust, frais), au-dessus les transferts
# deviennent trop rares et hétérogènes pour former un découpage. Ce filtre local reste ici ;
# le regroupement (REL_TOL / WINDOW_S / MIN_CLUSTER) vit désormais dans splitlib.
MIN_SOL, MAX_SOL = 1.0, 20.0


def ts_of(date_str: str, end: bool = False) -> int:
    d = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=dt.UTC)
    if end:
        d += dt.timedelta(days=1)          # --to est inclusif sur la journée entière
    return int(d.timestamp())


def signatures_in_window(addr: str, t_from: int, t_to: int, max_pages: int) -> tuple:
    """Signatures de l'adresse comprises dans [t_from, t_to].

    L'API ne sait remonter que du présent vers le passé : on pagine en sautant ce qui est trop
    récent (sans le lire), on garde la fenêtre, et on s'arrête dès qu'on est passé sous t_from.
    """
    before, kept, scanned, per_month = None, [], 0, defaultdict(int)
    reached, oldest = False, None
    for page_i in range(max_pages):
        page = rpc_client.sigs(addr, 1000, before)
        if not page:
            break
        scanned += len(page)
        for s in page:
            t = s.get("blockTime")
            if not t:
                continue
            oldest = t if oldest is None else min(oldest, t)
            per_month[dt.datetime.fromtimestamp(t, dt.UTC).strftime("%Y-%m")] += 1
            if t_from <= t <= t_to:
                kept.append(s)
        before = page[-1]["signature"]
        if oldest is not None and oldest < t_from:
            reached = True
            break                                  # fenêtre entièrement dépassée
        if len(page) < 1000:
            break                                  # fin de l'historique
        if page_i % 20 == 19:
            print(f"  … {scanned} signatures parcourues, {len(kept)} dans la fenêtre "
                  f"(plus ancienne : {dt.datetime.fromtimestamp(oldest, dt.UTC):%Y-%m-%d})", flush=True)
        time.sleep(0.12)
    return kept, scanned, dict(sorted(per_month.items())), oldest, reached


def outflows_of_tx(tx: dict, addr: str) -> list:
    """Sorties de SOL depuis addr dans une transaction : [(destinataire, montant, ts)].

    On lit les deltas de solde plutôt que les transferts système : le financement est souvent
    obfusqué (fermeture d'un compte wrappé), auquel cas aucun transfert n'apparaît alors que les
    soldes bougent bien.
    """
    try:
        keys = [k["pubkey"] if isinstance(k, dict) else k
                for k in tx["transaction"]["message"]["accountKeys"]]
        pre, post = tx["meta"]["preBalances"], tx["meta"]["postBalances"]
        i = keys.index(addr)
    except Exception:
        return []
    if post[i] - pre[i] >= 0:
        return []                                   # ce n'est pas une sortie
    ts = tx.get("blockTime") or 0
    out = []
    for j, k in enumerate(keys):
        if j == i:
            continue
        d = (post[j] - pre[j]) / LAMPORTS
        if MIN_SOL <= d <= MAX_SOL:
            out.append((k, d, ts))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--addr", required=True)
    ap.add_argument("--from", dest="d_from", required=True, help="date de debut, AAAA-MM-JJ")
    ap.add_argument("--to", dest="d_to", required=True, help="date de fin incluse, AAAA-MM-JJ")
    ap.add_argument("--max-pages", type=int, default=2000)
    ap.add_argument("--collect", action="store_true",
                    help="lire les transactions de la fenetre et detecter les splits")
    ap.add_argument("--max-tx", type=int, default=5000, help="plafond de transactions lues")
    ap.add_argument("--out", default=os.path.join(settings.DATA, "split", "outflows.json"))
    a = ap.parse_args()

    t_from, t_to = ts_of(a.d_from), ts_of(a.d_to, end=True)
    print(f"Adresse {a.addr[:12]}…  fenetre {a.d_from} -> {a.d_to}", flush=True)

    kept, scanned, per_month, oldest, reached = signatures_in_window(
        a.addr, t_from, t_to, a.max_pages)

    print(f"\n{scanned} signatures parcourues, {len(kept)} dans la fenetre.")
    if oldest:
        print(f"Historique atteint : {dt.datetime.fromtimestamp(oldest, dt.UTC):%Y-%m-%d}")
    if not reached and oldest and oldest > t_from:
        print("⚠️  La fenetre n'a PAS ete entierement atteinte (plafond de pages). "
              "Augmenter --max-pages, ou la fenetre est anterieure a l'existence de l'adresse.")
    print("\nDebit par mois (sur ce qui a ete parcouru) :")
    for m, c in per_month.items():
        print(f"   {m} : {c:>7d}")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    meta = {"addr": a.addr, "from": a.d_from, "to": a.d_to, "n_scanned": scanned,
            "n_in_window": len(kept), "per_month": per_month,
            "oldest_reached": oldest, "window_fully_covered": reached}
    json.dump(meta, open(a.out.replace(".json", "_scan.json"), "w"), indent=1)

    if not a.collect:
        print(f"\n(mode exploration — relancer avec --collect pour lire les "
              f"{min(len(kept), a.max_tx)} transactions de la fenetre)")
        return

    rows, n = [], 0
    for s in kept[:a.max_tx]:
        tx = rpc_client.tx(s["signature"])
        n += 1
        if tx:
            rows.extend(outflows_of_tx(tx, a.addr))
        if n % 100 == 0:
            print(f"  {n}/{min(len(kept), a.max_tx)} transactions lues, {len(rows)} sorties", flush=True)
        time.sleep(0.1)

    # splitlib regroupe par portefeuille -> [(montant, ts)] : on convertit la liste plate des sorties.
    funding: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for w, amt, ts in rows:
        funding[w].append((amt, ts))
    clusters = find_splits(funding)
    json.dump({**meta, "n_tx_read": n, "n_outflows": len(rows),
               "n_clusters": len(clusters), "clusters": clusters},
              open(a.out, "w"), indent=1)

    print(f"\n=== {len(clusters)} splits detectes sur {len(rows)} sorties "
          f"({n} transactions lues) ===")
    for c in clusters[:15]:
        print(f"  {c['date']}  {c['amount_sol']:.9f} SOL x {c['n_wallets']} portefeuilles "
              f"(etales sur {c['span_seconds']}s)")
    if clusters:
        tot = len({w for c in clusters for w in c['wallets']})
        print(f"\n  {tot} portefeuilles distincts impliques dans un decoupage.")
        print("  ⚠️  Comparer a un temoin (meme methode sur une periode/adresse sans lien) "
              "avant toute conclusion.")


if __name__ == "__main__":
    main()
