#!/usr/bin/env python3
"""ETAPE 11 — cartographie COMPLETE d'un distributeur, et test de son lien avec G2Y.

POURQUOI CELUI-LA
-----------------
Le rattrapage des geneses (etape 7) a fait apparaitre un bailleur qui n'etait pas visible avant :
9zqLjpSvvvreWyhQBSPquwo7LTotH5eoJWhWLCm6qcde finance la NAISSANCE de deux des quarante premiers
acheteurs d'OPTIMUS, pour des montants RONDS (47.000000000 SOL le 2024-03-14 et 10.000000000 SOL le
2024-06-07). Un montant rond est un versement delibere : signature d'un distributeur intermediaire,
pas d'un service de swap (piege nº3).

Cette adresse est petite (~2 300 transactions) : sa genese est atteinte et son historique peut etre
lu INTEGRALEMENT. C'est donc le seul noeud de la chaine ou une conclusion negative aurait vraiment
valeur de negatif.

CE QUE LE SCRIPT MESURE
-----------------------
- toutes ses entrees et sorties de SOL, par delta de solde ;
- ses destinataires, avec les montants repetes (signature d'un decoupage systematique) ;
- toute apparition d'un terminal connu, G2Y en particulier, AVEC le delta de solde associe : une
  apparition a delta nul est une simple mention de compte dans une route, pas un flux de valeur.

USAGE
    python3 etape11_hub_distributeur.py --addr <ADRESSE> [--label nom]
"""
from __future__ import annotations
import argparse, json, os, sys, time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_trace as L
from etape7_genese_M1 import load_keys, rpc_with, get_transactions_with, log

G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"
MIN = 0.05


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addr", required=True)
    ap.add_argument("--label", default=None)
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--max-tx", type=int, default=3000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    keys = load_keys()
    key = keys[-1]
    url = f"https://mainnet.helius-rpc.com/?api-key={key}"
    label = a.label or a.addr[:8]
    out = a.out or os.path.join(HERE, f"e11_hub_{label}.json")

    sigs, before, genesis, pages = [], None, False, 0
    while pages < a.max_pages:
        pg = rpc_with(url, "getSignaturesForAddress", [a.addr, {"limit": 1000, "before": before}])
        if pg is None:
            break
        pages += 1
        if not pg:
            genesis = True
            break
        sigs.extend(pg)
        if len(pg) < 1000:
            genesis = True
            break
        before = pg[-1]["signature"]
    sigs.sort(key=lambda s: (s.get("blockTime") or 0))
    ok = [s for s in sigs if not s.get("err")]
    log(f"{label} : {len(sigs)} signatures ({len(ok)} reussies), genese "
        f"{'ATTEINTE' if genesis else 'NON ATTEINTE'}, {pages} pages")

    picks = [s["signature"] for s in ok][:a.max_tx]
    txs = get_transactions_with(key, picks)
    if "__error__" in txs:
        sys.exit(txs["__error__"])
    log(f"  {len(txs)}/{len(picks)} transactions parsees relues")

    ins = defaultdict(lambda: {"total": 0.0, "n": 0, "amounts": [], "first": None, "last": None})
    outs = defaultdict(lambda: {"total": 0.0, "n": 0, "amounts": [], "first": None, "last": None})
    known_hits, amount_counter = [], defaultdict(int)
    for tx in txs.values():
        d = L.balance_deltas(tx)
        ts = L.tx_ts(tx)
        mine = d.get(a.addr, 0.0)
        for k, dv in d.items():
            if k in L.KNOWN and k != a.addr:
                known_hits.append({"addr": k, "label": L.KNOWN[k], "utc": L.utc(ts),
                                   "delta_sol": round(dv, 9),
                                   "delta_hub_sol": round(mine, 9),
                                   "signature": tx.get("signature")})
        if mine >= MIN:                                        # le hub encaisse
            for k, dv in d.items():
                if k == a.addr or dv > -MIN or k in L.SYSTEM_ACCOUNTS:
                    continue
                e = ins[k]
                e["total"] += -dv; e["n"] += 1; e["amounts"].append(round(-dv, 9))
                e["first"] = ts if e["first"] is None else min(e["first"], ts)
                e["last"] = ts if e["last"] is None else max(e["last"], ts)
        elif mine <= -MIN:                                     # le hub verse
            for k, dv in d.items():
                if k == a.addr or dv < MIN or k in L.SYSTEM_ACCOUNTS:
                    continue
                e = outs[k]
                e["total"] += dv; e["n"] += 1; e["amounts"].append(round(dv, 9))
                e["first"] = ts if e["first"] is None else min(e["first"], ts)
                e["last"] = ts if e["last"] is None else max(e["last"], ts)
                amount_counter[round(dv, 9)] += 1

    def fmt(dd):
        return [{"addr": k, "total_sol": round(v["total"], 6), "n": v["n"],
                 "first_utc": L.utc(v["first"]), "last_utc": L.utc(v["last"]),
                 "known": L.KNOWN.get(k), "amounts_sol": sorted(v["amounts"])[:20]}
                for k, v in sorted(dd.items(), key=lambda kv: -kv[1]["total"])]

    rep = sorted(((amt, n) for amt, n in amount_counter.items() if n >= 2), key=lambda x: -x[1])
    g2y_flux = [h for h in known_hits if h["addr"] == G2Y and abs(h["delta_sol"]) > 0]
    g2y_mention = [h for h in known_hits if h["addr"] == G2Y and abs(h["delta_sol"]) == 0]

    res = {"addr": a.addr, "label": label,
           "n_signatures": len(sigs), "n_signatures_reussies": len(ok),
           "genesis_reached": genesis, "pages": pages,
           "n_tx_relues": len(txs), "n_tx_demandees": len(picks),
           "couverture": ("integrale" if genesis and len(picks) >= len(ok)
                          else "PARTIELLE — plafond atteint, les listes sont un minorant"),
           "premiere_tx_utc": L.utc(sigs[0].get("blockTime")) if sigs else None,
           "derniere_tx_utc": L.utc(sigs[-1].get("blockTime")) if sigs else None,
           "n_sources": len(ins), "n_destinataires": len(outs),
           "montants_de_sortie_repetes": [{"amount_sol": amt, "n": n} for amt, n in rep[:25]],
           "G2Y_flux_de_valeur": g2y_flux,
           "G2Y_simple_mention_delta_nul": len(g2y_mention),
           "terminaux_connus_croises": sorted({h["label"] for h in known_hits}),
           "entrees": fmt(ins), "sorties": fmt(outs),
           "toutes_contreparties": sorted(set(ins) | set(outs))}
    json.dump(res, open(out, "w"), indent=1)

    log(f"  {len(ins)} sources · {len(outs)} destinataires")
    log(f"  montants de sortie les plus repetes : "
        + ", ".join(f"{amt:.9f}x{n}" for amt, n in rep[:6]))
    log(f"  G2Y : {len(g2y_flux)} flux de valeur, {len(g2y_mention)} mentions a delta nul")
    log(f"  terminaux croises : {res['terminaux_connus_croises']}")
    log(f"  -> {out}")


if __name__ == "__main__":
    main()
