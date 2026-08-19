#!/usr/bin/env python3
"""Remonte l'origine d'un portefeuille distributeur, en contournant le plafond de pagination.

`getSignaturesForAddress` ne remonte que du présent vers le passé, mille signatures par appel. Sur un
distributeur qui cumule 80 000 transactions ou plus, atteindre sa genèse par pagination complète est
hors de portée, et une pagination bornée rend les transactions récentes en laissant croire, en
silence, qu'on a vu le début. Ce piège a produit quatre conclusions fausses en une journée.

On ne remonte donc pas l'historique entier, seulement les entrées de fonds significatives. Deux
stratégies complémentaires, on garde la meilleure :

1. `--strategy deep` : pagination profonde jusqu'à la genèse, avec plafond explicite. Le résultat dit
   toujours si la genèse a été atteinte, il n'y a pas de zéro silencieux.
2. `--strategy sample` : échantillonnage en profondeur. On saute des pages par grands bonds pour
   atteindre rapidement les zones anciennes, et on n'inspecte que les transactions où le solde du
   portefeuille augmente fortement (ses financements). Coût constant, quelle que soit l'activité.

À chaque niveau, on retient les sources majeures et on recommence, sur N générations.

Usage:
    python3 05_trace_origin.py --addr <ADDR> --depth 3 --strategy sample

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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client  # noqa: E402
import settings  # noqa: E402

LAMPORTS = 1_000_000_000
MIN_INFLOW_SOL = 1.0          # en dessous, c'est du bruit opérationnel

# Terminaux connus : au-delà, on est dans l'infrastructure publique (échange, pont, service de swap).
# Une chaîne qui aboutit ici est un fait de routage, pas une preuve d'implication du service.
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
    """Pagination continue. Rend (signatures triées, genese_atteinte)."""
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
                  f"{dt.datetime.fromtimestamp(old, dt.UTC):%Y-%m-%d}", flush=True)
        time.sleep(0.05)
    return sorted(out, key=lambda s: s.get("blockTime") or 0), False


def sampled_signatures(addr: str, max_pages: int, keep_per_page: int = 60) -> tuple:
    """Échantillonnage : on traverse l'historique par bonds, en gardant un extrait de chaque page.

    On ne cherche pas l'exhaustivité mais les zones anciennes, atteintes à coût constant.
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
                  f"{dt.datetime.fromtimestamp(old, dt.UTC):%Y-%m-%d}", flush=True)
        time.sleep(0.04)
    return sorted(out, key=lambda s: s.get("blockTime") or 0), False


def inflows(addr: str, sigs: list, max_tx: int) -> list:
    """Entrées de SOL notables : [(source, montant, ts, signature)].

    Mesure par delta de solde : le financement est souvent obfusqué (fermeture d'un compte wrappé),
    auquel cas aucun transfert système n'apparaît alors que les soldes bougent.
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
        except Exception:
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
            oldest = dt.datetime.fromtimestamp(sigs[0].get("blockTime") or 0, dt.UTC)
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
                                 "first": dt.datetime.fromtimestamp(v["first"], dt.UTC)
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
