#!/usr/bin/env python3
"""Etape 4 : d'ou vient l'argent des bailleurs ? Remontee vers un service de swap.

Lit les adresses de --seeds, ecrit e4_origine_<label>.json.

Les bailleurs identifies a l'etape 3 ont eux-memes ete finances. On remonte de generation en
generation jusqu'a rencontrer un terminal connu (service de swap, echange, pont). G2Y
(G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t) est le terminal qui interesse l'enquete.

Deux precautions :
1. Aboutir a un terminal est un fait de routage, pas une preuve d'implication du service, tout
   capital entrant sur Solana franchit une telle porte.
2. G2Y n'est mesuree active que de decembre 2025 a avril 2026, OPTIMUS date d'octobre 2024. Si les
   chaines de 2024 n'aboutissent pas a G2Y, l'hypothese a tester est que le service operait alors
   depuis une autre adresse, ce n'est pas un echec.

Pour chaque adresse : pagination jusqu'a la genese (drapeau rendu), puis lecture des N plus
anciennes transactions et des N plus recentes avant la date du token. Entrees mesurees par delta de
solde. Toute apparition d'un terminal connu est signalee parmi toutes les contreparties vues, pas
seulement parmi les sources majeures.

Usage : python3 etape4_origine.py --seeds A,B,C --depth 2 --label OPTIMUS
"""
from __future__ import annotations
import argparse, json, os, time
from collections import defaultdict
import lib_trace as L

MIN_INFLOW = 0.2


def probe(addr, head_tx, max_pages, before_ts=None):
    """Analyse une adresse : pagination + entrees mesurees par delta de solde."""
    sigs, genesis, pages = L.all_signatures(addr, max_pages=max_pages, label=addr[:8])
    node = {"addr": addr, "n_signatures_total": len(sigs), "pages_paginated": pages,
            "genesis_reached": genesis, "known": L.KNOWN.get(addr),
            "oldest_seen_utc": L.utc(sigs[0].get("blockTime")) if sigs else None,
            "newest_seen_utc": L.utc(sigs[-1].get("blockTime")) if sigs else None,
            "sources": [], "known_counterparties": [], "n_tx_inspected": 0}
    if not sigs:
        return node

    # Les plus anciennes (la naissance) + celles qui precedent immediatement le token.
    picks = [s["signature"] for s in sigs[:head_tx]]
    if before_ts:
        pre = [s for s in sigs if (s.get("blockTime") or 0) <= before_ts]
        for s in pre[-head_tx:]:
            if s["signature"] not in picks:
                picks.append(s["signature"])
    txs = L.get_transactions(picks)
    node["n_tx_inspected"] = len(txs)

    per_src = defaultdict(lambda: {"total": 0.0, "n": 0, "first": None, "amounts": []})
    seen_known = {}
    for tx in txs.values():
        deltas = L.balance_deltas(tx)
        for k in deltas:
            if k in L.KNOWN and k != addr:
                seen_known.setdefault(k, {"label": L.KNOWN[k], "utc": L.utc(L.tx_ts(tx)),
                                          "signature": tx.get("signature"),
                                          "delta_sol": round(deltas[k], 9)})
        gain = deltas.get(addr, 0.0)
        if gain < MIN_INFLOW:
            continue
        for k, dv in deltas.items():
            if k == addr or dv > -MIN_INFLOW or k in L.SYSTEM_ACCOUNTS:
                continue
            e = per_src[k]
            e["total"] += -dv
            e["n"] += 1
            e["amounts"].append(round(-dv, 9))
            ts = L.tx_ts(tx)
            e["first"] = ts if e["first"] is None else min(e["first"], ts)

    node["sources"] = [{"addr": s, "total_sol": round(v["total"], 6), "n": v["n"],
                        "first_utc": L.utc(v["first"]), "known": L.KNOWN.get(s),
                        "amounts_sol": sorted(v["amounts"])[:12]}
                       for s, v in sorted(per_src.items(), key=lambda kv: -kv[1]["total"])[:12]]
    node["known_counterparties"] = [{"addr": k, **v} for k, v in seen_known.items()]
    return node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True, help="adresses separees par des virgules")
    ap.add_argument("--label", required=True)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--head-tx", type=int, default=100)
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--top", type=int, default=2, help="sources suivies par niveau")
    ap.add_argument("--before-ts", type=int, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    out = a.out or f"e4_origine_{a.label}.json"
    frontier = [s.strip() for s in a.seeds.split(",") if s.strip()]
    trace, seen = [], set()
    for level in range(a.depth):
        nxt = []
        for addr in frontier:
            if addr in seen or addr in L.KNOWN:
                continue
            seen.add(addr)
            print(f"\n[niveau {level}] {addr}", flush=True)
            node = probe(addr, a.head_tx, a.max_pages, a.before_ts)
            node["level"] = level
            trace.append(node)
            g = "ATTEINTE" if node["genesis_reached"] else "NON ATTEINTE (plafond)"
            print(f"  {node['n_signatures_total']} sigs, genese {g}, "
                  f"remonte a {node['oldest_seen_utc']}", flush=True)
            for s in node["sources"][:5]:
                tag = f"  <== {s['known']}" if s["known"] else ""
                print(f"    {s['total_sol']:>12.4f} SOL en {s['n']:>3d} fois  {s['addr']}{tag}",
                      flush=True)
            for k in node["known_counterparties"]:
                print(f"    ⇒ terminal connu croise : {k['label']}  {k['addr']}", flush=True)
            for s in node["sources"][:a.top]:
                if s["addr"] not in L.KNOWN and s["addr"] not in seen:
                    nxt.append(s["addr"])
            json.dump({"label": a.label, "trace": trace}, open(out, "w"), indent=1)
        frontier = nxt
        if not frontier:
            break

    hits = [(n["addr"], k) for n in trace for k in n["known_counterparties"]]
    g2y = [h for h in hits if h[1]["addr"] == "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"]
    res = {"label": a.label, "n_nodes": len(trace),
           "n_genesis_reached": sum(1 for n in trace if n["genesis_reached"]),
           "terminaux_rencontres": [{"noeud": h[0], **h[1]} for h in hits],
           "G2Y_rencontree": bool(g2y),
           "note": ("Aboutir a un terminal est un fait de routage, pas une preuve d'implication du "
                    "service. G2Y n'est mesuree active qu'a partir de decembre 2025 ; son absence "
                    "sur des chaines de 2024 est attendue et suggere une autre adresse a l'epoque."),
           "trace": trace}
    json.dump(res, open(out, "w"), indent=1)
    print(f"\n=== {len(trace)} noeuds, {res['n_genesis_reached']} avec genese atteinte ===")
    print(f"  G2Y rencontree : {'OUI' if g2y else 'NON'}")
    for h in hits:
        print(f"  {h[0][:16]}… ⇒ {h[1]['label']}")
    print(f"  -> {out}")


if __name__ == "__main__":
    main()
