#!/usr/bin/env python3
"""A token's early buyers, then the search for a split in how they were funded.

An old token's main holders today say nothing about its launch: the supply has
changed hands since. So this walks back to the mint's first transactions to
identify who was there at the start, then looks at how those wallets were
funded.

If an operator split a sum through a swap service to feed N wallets, those
wallets received near-identical amounts within a short interval. That is the
signature being looked for.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client
import settings
from splitlib import find_splits

LAMPORTS = 1_000_000_000
# A wider incoming band here: the calibre of the time is not known. This local
# filter stays; the grouping (REL_TOL / WINDOW_S / MIN_CLUSTER) now lives in
# splitlib.
MIN_SOL, MAX_SOL = 0.5, 50.0


def oldest_signatures(addr: str, stop_ts: int, max_pages: int = 400) -> list:
    """Paginate until stop_ts is reached, oldest to newest. A pagination bounded
    too tightly never reaches creation on an active address and leads to a wrong
    conclusion, so an exhausted page budget raises instead of returning a
    partial history.
    """
    out, _ = rpc_client.walk_sigs(addr, until_ts=stop_ts, max_pages=max_pages)
    return sorted(out, key=lambda s: s.get("blockTime") or 0)


def early_buyers(mint: str, created_ts: int, n_early: int, window_h: int = 48) -> tuple:
    """The signers of the first transactions touching the mint."""
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
        except (KeyError, TypeError, StopIteration):
            continue
        if signer not in buyers:
            buyers[signer] = s.get("blockTime")
            order.append(signer)
        time.sleep(0.1)
    return order, t0


def all_signatures(addr: str, max_pages: int = 60) -> tuple:
    """Every signature of an address, oldest to newest.

    Do not bound this pagination too tightly: a wallet's initial funding sits in its
    first transactions, and a partial pagination returns only the most recent ones,
    which leads to wrongly concluding there was no funding. It stops when a page
    comes back incomplete, the sign that genesis has been reached, and it reports
    whether the cap was hit before that.
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
    """A wallet's notable incoming SOL, measured by balance delta.

    The first 40 transactions of its existence are read: that is where its funding
    is.
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
        except (KeyError, TypeError, ValueError, IndexError):
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
