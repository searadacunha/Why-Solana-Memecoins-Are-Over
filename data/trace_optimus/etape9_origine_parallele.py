#!/usr/bin/env python3
"""Etape 9 : d'ou vient l'argent des bailleurs des premiers acheteurs d'OPTIMUS ?

Lit e8_funding_complet_OPTIMUS.json, ecrit e9_origine_OPTIMUS.json.

Difference avec l'etape 4 : celle-ci remontait deux ou trois graines a la fois, en serie, avec une
pagination a 60 000 pages, et n'a jamais fini. Ici on remonte tous les bailleurs prives des 40
premiers acheteurs, en parallele sur les cles disponibles, avec des bornes declarees. Un noeud dont
la pagination bute sur le plafond est rendu avec `genesis_reached=false` : ses sources ne valent
alors que comme « au moins ceci », jamais comme « voici tout ».

Ce qu'on cherche :
1. G2Y (G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t) parmi les contreparties, a n'importe quel
   niveau. Precaution : G2Y n'est mesuree active que de decembre 2025 a avril 2026, OPTIMUS date
   d'octobre 2024. Son absence sur des chaines de 2024 est attendue et suggere une autre adresse a
   l'epoque, ce n'est pas un echec de l'hypothese.
2. Tout autre terminal connu (echange, service de swap, pont). Aboutir la est un fait de routage,
   pas une preuve d'implication du service.
3. Les bailleurs prives communs a plusieurs premiers acheteurs : ce sont eux qui portent la
   signature de coordination.

Usage :
    python3 etape9_origine_parallele.py [--depth 2] [--max-pages 60] [--workers 5]
"""
from __future__ import annotations
import argparse, json, os, sys, time, threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_trace as L
from etape7_genese_M1 import load_keys, rpc_with, get_transactions_with, log

G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"
MIN_INFLOW = 0.2
OPTIMUS_TS = 1728537864          # 2024-10-10 05:24:24 UTC, premiere tx de la courbe


def paginate(addr, url, max_pages):
    out, before, genesis, pages = [], None, False, 0
    while pages < max_pages:
        pg = rpc_with(url, "getSignaturesForAddress", [addr, {"limit": 1000, "before": before}])
        if pg is None:
            return sorted(out, key=lambda s: (s.get("blockTime") or 0)), False, pages, "erreur_reseau"
        pages += 1
        if not pg:
            genesis = True
            break
        out.extend(pg)
        if len(pg) < 1000:
            genesis = True
            break
        before = pg[-1]["signature"]
    reason = "GENESE" if genesis else "plafond_pages"
    return sorted(out, key=lambda s: (s.get("blockTime") or 0)), genesis, pages, reason


def probe(addr, key, head_tx, max_pages, level):
    url = f"https://mainnet.helius-rpc.com/?api-key={key}"
    sigs, genesis, pages, reason = paginate(addr, url, max_pages)
    node = {"addr": addr, "level": level, "known": L.KNOWN.get(addr),
            "n_signatures_seen": len(sigs), "pages_paginated": pages,
            "genesis_reached": genesis, "stop_reason": reason,
            "oldest_seen_utc": L.utc(sigs[0].get("blockTime")) if sigs else None,
            "newest_seen_utc": L.utc(sigs[-1].get("blockTime")) if sigs else None,
            "sources": [], "known_counterparties": [], "n_tx_inspected": 0,
            "portee": ("complete : toutes les transactions de l'adresse ont ete vues" if genesis
                       else f"PARTIELLE : plafond de pagination ({pages} pages). Les sources "
                            "listees sont un minorant, pas un inventaire.")}
    if not sigs:
        node["measurement_failure"] = "aucune signature"
        return node

    picks = [s["signature"] for s in sigs[:head_tx]]
    pre = [s for s in sigs if (s.get("blockTime") or 0) <= OPTIMUS_TS]
    for s in pre[-head_tx:]:
        if s["signature"] not in picks:
            picks.append(s["signature"])
    txs = get_transactions_with(key, picks)
    if "__error__" in txs:
        node["measurement_failure"] = txs["__error__"]
        return node
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
    log(f"  [n{level}] {addr[:14]}… {len(sigs):>6d} sigs · "
        f"{'genese OK' if genesis else 'PLAFOND'} · {len(node['sources'])} sources · "
        f"{len(node['known_counterparties'])} terminaux"
        + ("  ⇒⇒ G2Y" if any(k['addr'] == G2Y for k in node['known_counterparties']) else ""))
    return node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--funding", default=os.path.join(HERE, "e8_funding_complet_OPTIMUS.json"))
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--head-tx", type=int, default=100)
    ap.add_argument("--max-pages", type=int, default=60)
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(HERE, "e9_origine_OPTIMUS.json"))
    a = ap.parse_args()

    keys = load_keys()
    d = json.load(open(a.funding))

    # graines : tous les bailleurs prives (hors terminaux connus) des 40 premiers acheteurs
    seeds, funded_by = [], defaultdict(set)
    for w in d["wallets"]:
        for f in w["inflows"]:
            if f.get("nature") == "produit_de_vente":
                continue
            s = f.get("source")
            if not s or s in L.KNOWN or s in L.SYSTEM_ACCOUNTS:
                continue
            funded_by[s].add(w["wallet"])
            if s not in seeds:
                seeds.append(s)
    log(f"{len(seeds)} bailleurs prives directs a remonter, profondeur {a.depth}, "
        f"plafond {a.max_pages} pages/noeud, {len(keys)} cles")

    trace, seen, frontier = [], set(), seeds
    for level in range(a.depth):
        jobs = [(addr, keys[i % len(keys)]) for i, addr in enumerate(frontier)
                if addr not in seen and addr not in L.KNOWN]
        for addr, _ in jobs:
            seen.add(addr)
        if not jobs:
            break
        log(f"\n=== niveau {level} : {len(jobs)} adresses ===")
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            nodes = list(ex.map(lambda j: probe(j[0], j[1], a.head_tx, a.max_pages, level), jobs))
        trace.extend(nodes)
        json.dump({"label": d.get("label", "OPTIMUS"), "trace": trace}, open(a.out, "w"), indent=1)
        nxt = []
        for n in nodes:
            for s in n["sources"][:a.top]:
                if s["addr"] not in L.KNOWN and s["addr"] not in seen and s["addr"] not in nxt:
                    nxt.append(s["addr"])
        frontier = nxt

    hits = [{"noeud": n["addr"], "niveau": n["level"], **k}
            for n in trace for k in n["known_counterparties"]]
    g2y = [h for h in hits if h["addr"] == G2Y]
    par_terminal = defaultdict(set)
    for h in hits:
        par_terminal[h["label"]].add(h["noeud"])
    communs = sorted(({"funder": s, "n_early_buyers": len(ws), "wallets": sorted(ws)}
                      for s, ws in funded_by.items() if len(ws) >= 2),
                     key=lambda c: -c["n_early_buyers"])
    res = {"label": d.get("label", "OPTIMUS"), "mint": d["mint"],
           "n_bailleurs_prives_directs": len(seeds),
           "n_noeuds_remontes": len(trace),
           "n_geneses_atteintes": sum(1 for n in trace if n["genesis_reached"]),
           "n_plafond_pagination": sum(1 for n in trace if not n["genesis_reached"]),
           "noeuds_sans_genese": [{"addr": n["addr"], "niveau": n["level"],
                                   "sigs_vues": n["n_signatures_seen"],
                                   "remonte_a": n["oldest_seen_utc"]}
                                  for n in trace if not n["genesis_reached"]],
           "G2Y_rencontree": bool(g2y),
           "G2Y_occurrences": g2y,
           "terminaux_par_type": {k: sorted(v) for k, v in par_terminal.items()},
           "bailleurs_prives_communs_a_2_premiers_acheteurs_ou_plus": communs,
           "note": ("Aboutir a un terminal connu est un fait de routage, pas une preuve "
                    "d'implication du service. G2Y n'est mesuree active que de decembre 2025 a "
                    "avril 2026 ; son absence sur des chaines d'octobre 2024 est attendue."),
           "trace": trace}
    json.dump(res, open(a.out, "w"), indent=1)
    log(f"\n=== {len(trace)} noeuds, geneses atteintes {res['n_geneses_atteintes']}/{len(trace)} ===")
    log(f"  G2Y rencontree : {'OUI' if g2y else 'NON'}")
    for lab, nodes in sorted(par_terminal.items(), key=lambda kv: -len(kv[1])):
        log(f"  {lab}: {len(nodes)} noeud(s)")
    log(f"  bailleurs prives communs a >=2 premiers acheteurs : {len(communs)}")
    for c in communs[:10]:
        log(f"     {c['funder']}  {c['n_early_buyers']} acheteurs")
    log(f"  -> {a.out}")


if __name__ == "__main__":
    main()
