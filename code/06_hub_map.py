#!/usr/bin/env python3
"""Map a distribution hub: where the money comes from, where it goes, and who
sends it back.

Reading a hub's history transaction by transaction is impractical: these
addresses accumulate tens of thousands of operations, and any bounded pagination
fails silently by returning only the most recent ones. So this uses Helius's
parsed-transaction API, which returns the transfers already decoded in batches
of a hundred, two orders of magnitude more efficient.

What the script measures:
- inflows: who feeds the hub, for how much, and when for the first time;
- outflows: how many distinct wallets it funds, and with what amounts;
- repeated amounts: one amount paid to several recipients is the signature of a
  split, and they are ranked by how often they repeat;
- recycling: the addresses appearing both in and out, that is, the satellites
  that send funds back to the hub.

Usage:
    python3 06_hub_map.py --addr <ADDR> --pages 30

One Helius client (rpc_client.py, the enhanced API): the keys come from the
environment, $HELIUS_API_KEYS or the uncommitted .env, see settings.py, and a
network failure raises instead of disguising itself as an empty pagination
(docs/PITFALLS.md, rule 2). No key is stored in this repository.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, sys, time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client

MIN_SOL = 0.5

KNOWN = {
    "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t": "service de swap (G2Y)",
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "echange (hot wallet)",
    "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6": "echange (hot wallet)",
    "2snHHreXbpJ7UwZxPe37gnUNf7Wx7wv6UKDSR2JckKuS": "pont (solveur)",
    "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w": "service de swap",
    "is6MTRHEgyFLNTfYcuV4QBWLjrZBfmhVNYR6ccgr8KV": "echange (hot wallet)",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--addr", required=True)
    ap.add_argument("--pages", type=int, default=30)
    ap.add_argument("--out", default="../data/split/hub_map.json")
    a = ap.parse_args()

    inflow: dict[str, dict] = defaultdict(lambda: {"sol": 0.0, "n": 0, "first": None, "last": None})
    outflow: dict[str, dict] = defaultdict(lambda: {"sol": 0.0, "n": 0, "first": None})
    out_amounts: Counter = Counter()
    before, n_tx, oldest, newest = None, 0, None, None

    for p in range(a.pages):
        batch = rpc_client.enhanced(a.addr, 100, before)
        if not batch:
            break
        for tx in batch:
            n_tx += 1
            ts = tx.get("timestamp") or 0
            if ts:
                oldest = ts if oldest is None else min(oldest, ts)
                newest = ts if newest is None else max(newest, ts)
            for t in (tx.get("nativeTransfers") or []):
                amt = (t.get("amount") or 0) / 1e9
                if amt < MIN_SOL:
                    continue
                src, dst = t.get("fromUserAccount"), t.get("toUserAccount")
                if dst == a.addr and src and src != a.addr:
                    e = inflow[src]
                    e["sol"] += amt; e["n"] += 1
                    e["first"] = ts if e["first"] is None else min(e["first"], ts)
                    e["last"] = ts if e["last"] is None else max(e["last"], ts)
                elif src == a.addr and dst and dst != a.addr:
                    e = outflow[dst]
                    e["sol"] += amt; e["n"] += 1
                    e["first"] = ts if e["first"] is None else min(e["first"], ts)
                    out_amounts[round(amt, 6)] += 1
        before = batch[-1].get("signature")
        if p % 5 == 4:
            print(f"  … {n_tx} transactions, {len(inflow)} sources, {len(outflow)} destinataires "
                  f"(remonte a {dt.datetime.fromtimestamp(oldest, dt.timezone.utc):%Y-%m-%d})", flush=True)
        time.sleep(0.2)

    recycl = sorted(set(inflow) & set(outflow),
                    key=lambda w: -(inflow[w]["sol"] + outflow[w]["sol"]))
    def fmt(t):
        return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d") if t else "?"

    print(f"\n=== HUB {a.addr} ===")
    print(f"  {n_tx} transactions lues, du {fmt(oldest)} au {fmt(newest)}")
    print(f"  {len(inflow)} sources · {len(outflow)} destinataires · {len(recycl)} en recyclage\n")

    print("  ENTREES principales :")
    for s, v in sorted(inflow.items(), key=lambda kv: -kv[1]["sol"])[:10]:
        tag = f"  <== {KNOWN[s]}" if s in KNOWN else ""
        print(f"    {v['sol']:>10.2f} SOL en {v['n']:>3d} fois  depuis {fmt(v['first'])}  {s}{tag}")

    print("\n  MONTANTS DE SORTIE LES PLUS REPETES (signature de decoupage) :")
    for amt, c in out_amounts.most_common(12):
        if c >= 2:
            print(f"    {amt:>12.6f} SOL  x{c}")

    print(f"\n  RECYCLAGE — adresses qui recoivent PUIS renvoient ({len(recycl)}) :")
    for w in recycl[:10]:
        print(f"    {w}  recu {outflow[w]['sol']:.2f} / renvoye {inflow[w]['sol']:.2f} SOL")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({"addr": a.addr, "n_tx": n_tx, "oldest": oldest, "newest": newest,
               "inflow": {k: v for k, v in sorted(inflow.items(), key=lambda kv: -kv[1]["sol"])[:60]},
               "outflow_count": len(outflow),
               "repeated_amounts": [[k, v] for k, v in out_amounts.most_common(40) if v >= 2],
               "recycling": recycl[:60]}, open(a.out, "w"), indent=1)
    print(f"\n  -> {a.out}")


if __name__ == "__main__":
    main()
