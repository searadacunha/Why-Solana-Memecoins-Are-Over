#!/usr/bin/env python3
"""Trace a distributor wallet's origin, working around the pagination cap.

`getSignaturesForAddress` only walks from the present backwards, a thousand
signatures per call. On a distributor accumulating 80 000 transactions or more,
reaching its genesis by full pagination is out of reach, and a bounded
pagination returns the recent transactions while silently suggesting the
beginning has been seen. That trap produced four false conclusions in one day.

So the whole history is not walked, only the significant incoming funds. Two
complementary strategies, and the better result is kept:

1. `--strategy deep`: deep pagination to genesis, with an explicit cap. The
   result always says whether genesis was reached; there is no silent zero.
2. `--strategy sample`: sampling in depth. Pages are skipped in large jumps to
   reach the old regions quickly, and only the transactions where the wallet's
   balance rises sharply, its fundings, are inspected. Constant cost, whatever
   the level of activity.

At each level the major sources are kept and the walk starts again, over N
generations.

Usage:
    python3 05_trace_origin.py --addr <ADDR> --depth 3 --strategy sample

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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client
import settings

LAMPORTS = 1_000_000_000
MIN_INFLOW_SOL = 1.0          # en dessous, c'est du bruit opérationnel

# Known terminals: past these, one is in public infrastructure, an exchange, a
# bridge, a swap service. A chain ending here is a fact about routing, not
# evidence that the service was involved.
KNOWN = {
    "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t": "service de swap (G2Y)",
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "echange (hot wallet)",
    "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6": "echange (hot wallet)",
    "2snHHreXbpJ7UwZxPe37gnUNf7Wx7wv6UKDSR2JckKuS": "pont (solveur)",
    "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w": "service de swap",
    "is6MTRHEgyFLNTfYcuV4QBWLjrZBfmhVNYR6ccgr8KV": "echange (hot wallet)",
}
SYSTEM = {"11111111111111111111111111111111",
          "ComputeBudget111111111111111111111111111111",
          "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}


def page(addr: str, before: Optional[str] = None) -> list:
    return rpc_client.sigs(addr, 1000, before)


def deep_signatures(addr: str, max_pages: int) -> tuple:
    """Continuous pagination. Returns (sorted signatures, genesis_reached)."""
    out, before = [], None
    for i in range(max_pages):
        pg = page(addr, before)
        if not pg:
            return sorted(out, key=lambda s: s.get("blockTime") or 0), True
        out.extend(pg)
        if len(pg) < 1000:
            return sorted(out, key=lambda s: s.get("blockTime") or 0), True
        before = pg[-1]["signature"]
        if i % 20 == 19:
            old = min((s.get("blockTime") or 0) for s in pg)
            print(f"    … {len(out)} sigs, plus ancienne "
                  f"{dt.datetime.fromtimestamp(old, dt.timezone.utc):%Y-%m-%d}", flush=True)
        time.sleep(0.05)
    return sorted(out, key=lambda s: s.get("blockTime") or 0), False


def sampled_signatures(addr: str, max_pages: int, keep_per_page: int = 60) -> tuple:
    """Sampling: cross the history in jumps, keeping an excerpt of each page.

    Exhaustiveness is not the goal; the old regions are, reached at constant cost.
    """
    out, before = [], None
    for i in range(max_pages):
        pg = page(addr, before)
        if not pg:
            break
        step = max(1, len(pg) // keep_per_page)
        out.extend(pg[::step])
        if len(pg) < 1000:
            break
        before = pg[-1]["signature"]
        if i % 25 == 24:
            old = min((s.get("blockTime") or 0) for s in pg)
            print(f"    … page {i+1}, remonte a "
                  f"{dt.datetime.fromtimestamp(old, dt.timezone.utc):%Y-%m-%d}", flush=True)
        time.sleep(0.04)
    return sorted(out, key=lambda s: s.get("blockTime") or 0), False


def inflows(addr: str, sigs: list, max_tx: int) -> list:
    """Notable incoming SOL: [(source, amount, ts, signature)].

    Measured by balance delta: funding is often obfuscated, by closing a wrapped
    account, in which case no system transfer appears at all while the balances
    do move.
    """
    found, n = [], 0
    for s in sigs[:max_tx]:
        tx = rpc_client.tx(s["signature"])
        n += 1
        if not tx:
            continue
        try:
            keys = [k["pubkey"] if isinstance(k, dict) else k
                    for k in tx["transaction"]["message"]["accountKeys"]]
            pre, post = tx["meta"]["preBalances"], tx["meta"]["postBalances"]
            i = keys.index(addr)
        except (KeyError, TypeError, ValueError, IndexError):
            continue
        gain = (post[i] - pre[i]) / LAMPORTS
        if gain < MIN_INFLOW_SOL:
            continue
        for j, k in enumerate(keys):
            if j == i or k in SYSTEM:
                continue
            d = (post[j] - pre[j]) / LAMPORTS
            if d <= -MIN_INFLOW_SOL:
                found.append((k, -d, tx.get("blockTime") or 0, s["signature"]))
        if n % 150 == 0:
            print(f"    {n} tx inspectees, {len(found)} entrees", flush=True)
        time.sleep(0.05)
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--addr", required=True)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--strategy", choices=["deep", "sample"], default="sample")
    ap.add_argument("--max-pages", type=int, default=150)
    ap.add_argument("--max-tx", type=int, default=600)
    ap.add_argument("--top", type=int, default=3, help="sources majeures suivies par niveau")
    ap.add_argument("--out", default=os.path.join(settings.DATA, "split", "origin_trace.json"))
    a = ap.parse_args()

    trace, frontier, seen = [], [a.addr], set()
    for level in range(a.depth):
        nxt = []
        for addr in frontier:
            if addr in seen or addr in KNOWN:
                continue
            seen.add(addr)
            print(f"\n[niveau {level}] {addr}", flush=True)
            sigs, complete = (deep_signatures(addr, a.max_pages) if a.strategy == "deep"
                              else sampled_signatures(addr, a.max_pages))
            if not sigs:
                trace.append({"level": level, "addr": addr, "status": "aucune signature"})
                continue
            oldest = dt.datetime.fromtimestamp(sigs[0].get("blockTime") or 0, dt.timezone.utc)
            print(f"  {len(sigs)} signatures retenues | remonte a {oldest:%Y-%m-%d} | "
                  f"genese {'ATTEINTE' if complete else 'NON atteinte (echantillon)'}", flush=True)

            ins = inflows(addr, sigs, a.max_tx)
            per_src = defaultdict(lambda: {"total": 0.0, "n": 0, "first": None})
            for src, amt, ts, _ in ins:
                e = per_src[src]
                e["total"] += amt
                e["n"] += 1
                e["first"] = ts if e["first"] is None else min(e["first"], ts)
            ranked = sorted(per_src.items(), key=lambda kv: -kv[1]["total"])

            node = {"level": level, "addr": addr, "n_sigs": len(sigs),
                    "genesis_reached": complete,
                    "oldest_seen": oldest.strftime("%Y-%m-%d"),
                    "n_inflows": len(ins),
                    "sources": [{"addr": s, "total_sol": round(v["total"], 4), "n": v["n"],
                                 "first": dt.datetime.fromtimestamp(v["first"], dt.timezone.utc)
                                            .strftime("%Y-%m-%d") if v["first"] else None,
                                 "known": KNOWN.get(s)} for s, v in ranked[:8]]}
            trace.append(node)

            print(f"  {len(ranked)} sources distinctes. Principales :")
            for s, v in ranked[:5]:
                tag = f"  <== {KNOWN[s]}" if s in KNOWN else ""
                print(f"     {v['total']:>10.2f} SOL en {v['n']:>3d} fois  {s}{tag}")
            for s, _ in ranked[:a.top]:
                if s not in KNOWN and s not in seen:
                    nxt.append(s)
        frontier = nxt
        if not frontier:
            break

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"root": a.addr, "strategy": a.strategy, "trace": trace}, open(a.out, "w"), indent=1)

    print("\n=== SYNTHESE ===")
    for n in trace:
        if n.get("status"):
            continue
        hits = [s for s in n["sources"] if s.get("known")]
        flag = "" if n["genesis_reached"] else "  (genese non atteinte — origine incertaine)"
        print(f"  niveau {n['level']} · {n['addr'][:16]}… remonte a {n['oldest_seen']}{flag}")
        for h in hits:
            print(f"      → aboutit a : {h['known']}  ({h['total_sol']} SOL)")
    print("\n  Note : aboutir a un service connu est un FAIT DE ROUTAGE, pas une preuve")
    print("  d'implication de ce service. Tout capital entrant sur Solana passe par une telle porte.")


if __name__ == "__main__":
    main()
