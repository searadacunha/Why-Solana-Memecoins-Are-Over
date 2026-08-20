#!/usr/bin/env python3
"""Find the SPLITS in one address's outflows, over a given DATE WINDOW.

This starts from the SOURCE rather than from the holders: every outflow of the
address over the period is collected, then grouped by near-identical amounts
received within a short interval. Each group is a split, so a set of wallets
plausibly under one hand.

WHY THE DATE FILTER IS ESSENTIAL
--------------------------------
Reading a signature costs a thousandth of a call, since they arrive in pages of
1000; reading a transaction costs a whole call. On a service address handling
some 200 000 transactions a month, reading everything is out of reach. So the
signatures are paginated, which is fast, keeping only those inside the window,
and ONLY those are read in detail.

USAGE
-----
    # explore an address's throughput, without reading anything in detail
    python3 02_cn_outflows.py --addr <ADDR> --from 2024-10-01 --to 2025-02-28

    # collect the window's outflows and detect the splits
    python3 02_cn_outflows.py --addr <ADDR> --from 2025-12-01 --to 2025-12-08 --collect

One Helius client: rpc_client.py, keys from $HELIUS_API_KEYS or .env, see
settings.py.
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
import rpc_client
import settings
from splitlib import find_splits

LAMPORTS = 1_000_000_000

# Amount window: below it, noise is caught (dust, fees); above it, transfers
# become too rare and too heterogeneous to form a split. This local filter stays
# here; the grouping (REL_TOL / WINDOW_S / MIN_CLUSTER) now lives in splitlib.
MIN_SOL, MAX_SOL = 1.0, 20.0


def ts_of(date_str: str, end: bool = False) -> int:
    d = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=dt.UTC)
    if end:
        d += dt.timedelta(days=1)          # --to est inclusif sur la journée entière
    return int(d.timestamp())


def signatures_in_window(addr: str, t_from: int, t_to: int, max_pages: int) -> tuple:
    """The address's signatures falling inside [t_from, t_to].

    The API can only walk from the present backwards, so pagination skips what is
    too recent without reading it, keeps the window, and stops as soon as it has
    dropped below t_from.
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
    """SOL leaving addr in one transaction: [(recipient, amount, ts)].

    Balance deltas are read rather than system transfers: funding is often
    obfuscated, by closing a wrapped account, in which case no transfer appears at
    all while the balances do move.
    """
    try:
        keys = [k["pubkey"] if isinstance(k, dict) else k
                for k in tx["transaction"]["message"]["accountKeys"]]
        pre, post = tx["meta"]["preBalances"], tx["meta"]["postBalances"]
        i = keys.index(addr)
    # ValueError: addr is not in this transaction, the normal case. The others
    # mean a field is missing, which this filter would pass off as "no outflow".
    except (KeyError, TypeError, ValueError, IndexError):
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

    # splitlib groups by wallet -> [(amount, ts)], so the flat outflow list is converted.
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
