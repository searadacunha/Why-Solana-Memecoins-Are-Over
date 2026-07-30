#!/usr/bin/env python3
"""ETAPE 4bis — d'ou vient l'argent des BAILLEURS des premiers acheteurs de h2w6gm6jz ?

LE PROBLEME QUE CE SCRIPT RESOUD
--------------------------------
Le bailleur principal (G9X7F4Jz…) emet ~20 000 transactions par jour et est encore actif
aujourd'hui. `getSignaturesForAddress` ne remonte que du present vers le passe : remonter jusqu'a
decembre 2024 demanderait des milliers de pages. Une pagination bornee ne rendrait que 2026 et
ferait conclure a tort (piege nº1).

LA SOLUTION : ANCRAGE PAR SIGNATURE CONNUE.
Le parametre `before` de getSignaturesForAddress accepte une SIGNATURE. On connait deja, pour chaque
bailleur, la signature exacte du virement qu'il a fait a un premier acheteur en decembre 2024. On
pagine donc EN PARTANT DE CETTE SIGNATURE : on atterrit directement dans l'epoque utile, et chaque
page suivante recule dans le passe. Le plafond de pagination ne s'applique plus a l'intervalle
2024→2026, qui n'est pas parcouru.

Ce que le script rend explicitement pour chaque adresse :
  - `genesis_reached` : une page revenue incomplete AVANT l'ancre => on a vu sa naissance.
  - `oldest_seen_utc` : jusqu'ou on est remonte. Sans genese, un negatif est un ECHEC DE MESURE.
  - `calibre` de chaque entree : rond = versement delibere (distributeur) ;
    precis a la 9e decimale = sortie de conversion (service de swap).
  - toute apparition d'un TERMINAL connu (dont G2Y) parmi TOUTES les contreparties.

USAGE
    python3 13_origine_bailleurs.py --seeds 'ADDR:SIG,ADDR:SIG' --depth 3
"""
from __future__ import annotations
import argparse, json, os, time, datetime as dt
from collections import defaultdict
import lib_trace as L

MIN_INFLOW = 0.2
G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"


def roundness(x):
    lam = round(x * L.LAMPORTS)
    if lam % L.LAMPORTS == 0:
        return "rond_SOL"
    if lam % 100_000_000 == 0:
        return "rond_0.1"
    if lam % 10_000_000 == 0:
        return "rond_0.01"
    if lam % 1_000_000 == 0:
        return "rond_0.001"
    return "precis_swap"


def back_from(addr, anchor_sig, max_pages, label=""):
    """Pagine vers le PASSE en partant d'une signature d'ancrage datee.

    Rend (signatures triees du plus ancien au plus recent, genesis_reached, pages).
    genesis_reached=True uniquement si une page est revenue incomplete ou vide : on a alors vu la
    naissance de l'adresse. Sinon la mesure est bornee et doit etre declaree comme telle.
    """
    out, before, genesis, pages = [], anchor_sig, False, 0
    for _ in range(max_pages):
        pg = None
        for att in range(3):
            pg = L.rpc("getSignaturesForAddress", [addr, {"limit": 1000, "before": before}], tries=8)
            if pg is not None:
                break
            time.sleep(2.0 * (att + 1))
        if pg is None:
            print(f"      ⚠️ {label} pagination interrompue (reseau) — genese NON declaree",
                  flush=True)
            break
        pages += 1
        if not pg:
            genesis = True
            break
        out.extend(pg)
        if len(pg) < 1000:
            genesis = True
            break
        before = pg[-1]["signature"]
        oldest = min((s.get("blockTime") or 0) for s in pg if s.get("blockTime")) or 0
        if pages % 10 == 0:
            print(f"      … {label} {len(out)} sigs avant l'ancre, remonte a "
                  f"{L.utc(oldest)}", flush=True)
        time.sleep(0.05)
    return sorted(out, key=lambda s: (s.get("blockTime") or 0, s["signature"])), genesis, pages


def probe(addr, anchor_sig, head_tx, tail_tx, max_pages):
    sigs, genesis, pages = back_from(addr, anchor_sig, max_pages, addr[:8])
    node = {"addr": addr, "anchor_sig": anchor_sig, "known": L.KNOWN.get(addr),
            "n_sigs_before_anchor": len(sigs), "pages_paginated": pages,
            "genesis_reached": genesis, "pagination_capped": pages >= max_pages,
            "oldest_seen_utc": L.utc(sigs[0].get("blockTime")) if sigs else None,
            "newest_seen_utc": L.utc(sigs[-1].get("blockTime")) if sigs else None,
            "sources": [], "known_counterparties": [], "n_tx_inspected": 0,
            "measurement_failure": None if genesis else
            "genese non atteinte : un negatif sur cette adresse est un echec de mesure"}
    if not sigs:
        node["measurement_failure"] = "aucune signature avant l'ancre"
        return node

    picks = [s["signature"] for s in sigs[:head_tx]]            # la naissance
    for s in sigs[-tail_tx:]:                                   # juste avant le virement
        if s["signature"] not in picks:
            picks.append(s["signature"])
    txs = L.get_transactions(picks)
    node["n_tx_inspected"] = len(txs)
    node["n_tx_requested"] = len(picks)

    per_src = defaultdict(lambda: {"total": 0.0, "n": 0, "first": None, "last": None,
                                   "amounts": [], "calibres": set(), "sig": None})
    seen_known = {}
    for tx in txs.values():
        d = L.balance_deltas(tx)
        for k in d:
            if k in L.KNOWN and k != addr:
                seen_known.setdefault(k, {"label": L.KNOWN[k], "utc": L.utc(L.tx_ts(tx)),
                                          "delta_sol": round(d[k], 9),
                                          "signature": tx.get("signature")})
        gain = d.get(addr, 0.0)
        if gain < MIN_INFLOW:
            continue
        for k, dv in d.items():
            if k == addr or dv > -MIN_INFLOW or k in L.SYSTEM_ACCOUNTS:
                continue
            e = per_src[k]
            e["total"] += -dv
            e["n"] += 1
            e["amounts"].append(round(-dv, 9))
            e["calibres"].add(roundness(-dv))
            ts = L.tx_ts(tx)
            e["first"] = ts if e["first"] is None else min(e["first"], ts)
            e["last"] = ts if e["last"] is None else max(e["last"], ts)
            if e["sig"] is None or ts == e["first"]:
                e["sig"] = tx.get("signature")

    node["sources"] = [{"addr": s, "total_sol": round(v["total"], 6), "n": v["n"],
                        "first_utc": L.utc(v["first"]), "last_utc": L.utc(v["last"]),
                        "known": L.KNOWN.get(s), "calibres": sorted(v["calibres"]),
                        "amounts_sol": sorted(v["amounts"])[:12], "anchor_sig": v["sig"]}
                       for s, v in sorted(per_src.items(), key=lambda kv: -kv[1]["total"])[:15]]
    node["known_counterparties"] = [{"addr": k, **v} for k, v in seen_known.items()]
    return node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True, help="ADDR:SIG,ADDR:SIG …")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--head-tx", type=int, default=100)
    ap.add_argument("--tail-tx", type=int, default=100)
    ap.add_argument("--max-pages", type=int, default=120)
    ap.add_argument("--top", type=int, default=2)
    ap.add_argument("--out", default="e4b_origine_bailleurs.json")
    a = ap.parse_args()

    frontier = []
    for tok in a.seeds.split(","):
        tok = tok.strip()
        if not tok:
            continue
        addr, sig = tok.split(":")
        frontier.append((addr, sig))

    trace, seen = [], set()
    for level in range(a.depth):
        nxt = []
        for addr, sig in frontier:
            if addr in seen or addr in L.KNOWN:
                continue
            seen.add(addr)
            print(f"\n[niveau {level}] {addr}  (ancre {sig[:20]}…)", flush=True)
            node = probe(addr, sig, a.head_tx, a.tail_tx, a.max_pages)
            node["level"] = level
            trace.append(node)
            g = "ATTEINTE" if node["genesis_reached"] else "NON ATTEINTE"
            print(f"  {node['n_sigs_before_anchor']} sigs avant l'ancre, {node['pages_paginated']} "
                  f"pages, genese {g}, remonte a {node['oldest_seen_utc']}", flush=True)
            for s in node["sources"][:6]:
                tag = f"   <== {s['known']}" if s["known"] else ""
                print(f"    {s['total_sol']:>12.4f} SOL en {s['n']:>3d} fois "
                      f"[{','.join(s['calibres'])}]  {s['addr']}{tag}", flush=True)
            for k in node["known_counterparties"]:
                print(f"    ⇒ TERMINAL CONNU croise : {k['label']}  {k['addr']}", flush=True)
            for s in node["sources"][:a.top]:
                if s["addr"] not in L.KNOWN and s["addr"] not in seen and s["anchor_sig"]:
                    nxt.append((s["addr"], s["anchor_sig"]))
            json.dump({"trace": trace}, open(a.out, "w"), indent=1)
        frontier = nxt
        if not frontier:
            break

    hits = [(n["addr"], k) for n in trace for k in n["known_counterparties"]]
    g2y = [h for h in hits if h[1]["addr"] == G2Y]
    res = {"mint": "FNqJtYs7rsP1H9GXWTtc5VnDoL2GhXEUKhYN46EEpump", "token": "h2w6gm6jz",
           "n_nodes": len(trace),
           "n_genesis_reached": sum(1 for n in trace if n["genesis_reached"]),
           "noeuds_sans_genese": [n["addr"] for n in trace if not n["genesis_reached"]],
           "terminaux_rencontres": [{"noeud": h[0], **h[1]} for h in hits],
           "G2Y_rencontree": bool(g2y),
           "note": ("Aboutir a un terminal (echange, service de swap, pont) est un FAIT DE ROUTAGE, "
                    "pas une preuve d'implication du service. G2Y n'est mesuree active que de "
                    "decembre 2025 a avril 2026 ; son absence sur des chaines de decembre 2024 est "
                    "attendue et soutient l'hypothese d'une AUTRE adresse a l'epoque."),
           "trace": trace}
    json.dump(res, open(a.out, "w"), indent=1)
    print(f"\n=== {len(trace)} noeuds, genese atteinte pour {res['n_genesis_reached']} ===")
    print(f"  G2Y rencontree : {'OUI' if g2y else 'NON'}")
    for h in hits:
        print(f"  {h[0][:16]}… ⇒ {h[1]['label']} ({h[1]['utc']})")
    print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
