#!/usr/bin/env python3
"""Cartographie un hub de distribution : d'où vient l'argent, où il va, et qui le lui renvoie.

Lire l'historique d'un hub transaction par transaction est impraticable : ces adresses cumulent des
dizaines de milliers d'opérations, et toute pagination bornée échoue en silence en ne rendant que
les plus récentes. On utilise donc l'API de transactions *parsées* de Helius, qui renvoie les
transferts déjà décodés par paquets de cent, deux ordres de grandeur plus efficace.

Ce que le script mesure :
- les entrées : qui alimente le hub, pour combien, et quand pour la première fois ;
- les sorties : combien de portefeuilles distincts il finance, et avec quels montants ;
- les montants répétés : un même montant versé à plusieurs destinataires est la signature d'un
  découpage. On les classe par nombre de répétitions ;
- le recyclage : les adresses qui apparaissent à la fois en entrée et en sortie, c'est-à-dire les
  satellites qui renvoient des fonds au hub.

Usage:
    python3 06_hub_map.py --addr <ADDR> --pages 30

Client Helius unique (rpc_client.py, API enhanced) : les clés viennent de
l'environnement ($HELIUS_API_KEYS, ou .env non versionné, voir settings.py) et un
échec réseau lève au lieu de se déguiser en pagination vide
(docs/PITFALLS.md, règle n°2). Aucune clé n'est stockée dans ce dépôt.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, sys, time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client  # noqa: E402

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
                  f"(remonte a {dt.datetime.fromtimestamp(oldest, dt.UTC):%Y-%m-%d})", flush=True)
        time.sleep(0.2)

    recycl = sorted(set(inflow) & set(outflow),
                    key=lambda w: -(inflow[w]["sol"] + outflow[w]["sol"]))
    fmt = lambda t: dt.datetime.fromtimestamp(t, dt.UTC).strftime("%Y-%m-%d") if t else "?"

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
