#!/usr/bin/env python3
"""Etape 2 : pour chaque source de financement des premiers acheteurs de h2w6gm6jz, qui est-elle,
combien de portefeuilles finance-t-elle, avec quels montants repetes, et d'ou vient son argent
(remontee vers un service de swap ou un echange).

Lit le JSON de l'etape 1, ecrit les generations de profils de sources vers --out.

La lecture passe par l'API de transactions parsees de Helius (100 tx par appel) : getTransaction
une par une est impraticable sur des adresses actives, et toute pagination bornee ne rend que le
present. Pour chaque adresse, la genese atteinte ou non est declaree explicitement.

Calibre des montants :
- montant rond (3.000000000) = versement delibere -> distributeur intermediaire
- montant a la 9e decimale (1.393934883) = sortie de conversion -> service de swap

Usage : python3 12_trace_sources.py --in h2w6_early_funding.json --gen 3
"""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.request, datetime as dt
from collections import defaultdict, Counter

KEY = os.environ.get("HELIUS_API_KEY", "")
ADDR_URL = "https://api.helius.xyz/v0/addresses/{addr}/transactions"

KNOWN = {
    "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t": "SERVICE DE SWAP (G2Y, cible de l'enquete)",
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "Binance (hot wallet)",
    "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6": "echange (hot wallet)",
    "2snHHreXbpJ7UwZxPe37gnUNf7Wx7wv6UKDSR2JckKuS": "pont (solveur)",
    "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w": "service de swap",
    "is6MTRHEgyFLNTfYcuV4QBWLjrZBfmhVNYR6ccgr8KV": "echange (hot wallet)",
    "HRS6JqXcFgWrWxaBPjhnThQiWmUMkE3GrYHWR86tbFqR": "distributeur ODIN (12 SOL -> 4x3 SOL)",
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P": "programme pump.fun",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": "programme (Raydium/ATA)",
    "TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM": "programme",
}
PROGRAMS = {"11111111111111111111111111111111", "ComputeBudget111111111111111111111111111111",
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}


def get_page(addr, before=None, tries=5):
    url = ADDR_URL.format(addr=addr) + f"?api-key={KEY}&limit=100"
    if before:
        url += f"&before={before}"
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                       "User-Agent": "trace-sources/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r), True
        except Exception:
            time.sleep(1.5 * (i + 1))
    return [], False


def scan(addr, max_pages=120):
    """Toutes les tx parsees d'une adresse jusqu'a page incomplete (= genese atteinte)."""
    txs, before, complete, pages, net_ok = [], None, False, 0, True
    while pages < max_pages:
        page, ok = get_page(addr, before)
        pages += 1
        if not ok:
            net_ok = False
            break
        if not page:
            complete = True
            break
        txs.extend(page)
        if len(page) < 100:
            complete = True
            break
        before = page[-1].get("signature")
        time.sleep(0.12)
    return txs, (complete and net_ok), pages


def profile(addr, targets):
    txs, complete, pages = scan(addr)
    inflow, outflow = defaultdict(lambda: [0.0, 0, None]), defaultdict(lambda: [0.0, 0, None])
    out_amts, in_amts = Counter(), Counter()
    ts_all = []
    for tx in txs:
        ts = tx.get("timestamp") or 0
        if ts:
            ts_all.append(ts)
        for t in (tx.get("nativeTransfers") or []):
            amt = (t.get("amount") or 0) / 1e9
            if amt < 0.02:
                continue
            src, dst = t.get("fromUserAccount"), t.get("toUserAccount")
            if dst == addr and src and src != addr:
                e = inflow[src]; e[0] += amt; e[1] += 1
                e[2] = ts if e[2] is None else min(e[2], ts)
                in_amts[round(amt, 9)] += 1
            elif src == addr and dst and dst != addr:
                e = outflow[dst]; e[0] += amt; e[1] += 1
                e[2] = ts if e[2] is None else min(e[2], ts)
                out_amts[round(amt, 9)] += 1
    fmt = lambda t: dt.datetime.fromtimestamp(t, dt.UTC).strftime("%Y-%m-%d %H:%M:%S") if t else None
    top_in = sorted(inflow.items(), key=lambda kv: -kv[1][0])[:25]
    return {
        "addr": addr, "known": KNOWN.get(addr),
        "n_tx_lues": len(txs), "pages": pages, "genese_atteinte": complete,
        "periode": [fmt(min(ts_all)) if ts_all else None, fmt(max(ts_all)) if ts_all else None],
        "n_sources": len(inflow), "n_destinataires": len(outflow),
        "finance_combien_de_nos_acheteurs": len(set(outflow) & set(targets)),
        "nos_acheteurs_finances": sorted(set(outflow) & set(targets)),
        "entrees_top": [{"from": s, "known": KNOWN.get(s), "sol": round(v[0], 6),
                         "n": v[1], "first_utc": fmt(v[2])} for s, v in top_in],
        "montants_sortie_repetes": [[a, c] for a, c in out_amts.most_common(15) if c >= 2],
        "montants_entree_repetes": [[a, c] for a, c in in_amts.most_common(10) if c >= 2],
        "recyclage": sorted(set(inflow) & set(outflow))[:30],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp",
                    default="data/trace_h2w6/h2w6_early_funding.json")
    ap.add_argument("--gen", type=int, default=2)
    ap.add_argument("--max-per-gen", type=int, default=14)
    ap.add_argument("--out", default="data/trace_h2w6/h2w6_sources_origin.json")
    a = ap.parse_args()
    if not KEY:
        sys.exit("HELIUS_API_KEY non defini.")

    d = json.load(open(a.inp))
    buyers = set(d["funding"])
    # sources classees par nombre de nos acheteurs finances
    cnt = Counter()
    for w, f in d["funding"].items():
        for ev in f["inflows"]:
            if ev["source"] and ev["source"] not in PROGRAMS:
                cnt[ev["source"]] += 1
    frontier = [s for s, _ in cnt.most_common(a.max_per_gen)]

    seen, gens = set(), []
    for g in range(1, a.gen + 1):
        rows, nxt = [], Counter()
        print(f"\n### GENERATION {g} — {len(frontier)} adresses", flush=True)
        for i, addr in enumerate(frontier, 1):
            if addr in seen or addr in PROGRAMS:
                continue
            seen.add(addr)
            p = profile(addr, buyers if g == 1 else set())
            rows.append(p)
            tag = p["known"] or ""
            print(f"  [{g}.{i}] {addr[:14]}… {p['n_tx_lues']:>6d} tx  genese={p['genese_atteinte']}"
                  f"  {p['n_sources']} sources / {p['n_destinataires']} dest.  {tag}", flush=True)
            for e in p["entrees_top"][:6]:
                if e["from"] not in seen:
                    nxt[e["from"]] += 1
                if KNOWN.get(e["from"]):
                    print(f"        <== {KNOWN[e['from']]}  {e['sol']:.3f} SOL  {e['first_utc']}",
                          flush=True)
        gens.append({"generation": g, "profils": rows})
        frontier = [s for s, _ in nxt.most_common(a.max_per_gen)]
        if not frontier:
            break

    json.dump({"mint": d["mint"], "genere_le": dt.datetime.now(dt.UTC).isoformat(),
               "generations": gens}, open(a.out, "w"), indent=1)
    print(f"\n  -> {a.out}")


if __name__ == "__main__":
    main()
