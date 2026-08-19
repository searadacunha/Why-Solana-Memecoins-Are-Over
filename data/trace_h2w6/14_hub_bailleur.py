#!/usr/bin/env python3
"""Que fait le bailleur ? Cartographie ancree dans le temps, via l'API parsee de Helius.

Qu'un bailleur ait finance 9 des 40 premiers acheteurs ne dit pas ce qu'il est. Deux lectures
restent ouvertes :
  (a) distributeur dedie : il n'alimente qu'une petite flotte, avec des montants repetes ;
  (b) service (routeur de bot, depot d'echange) : il alimente des milliers d'adresses sans lien
      entre elles, et croiser 9 de ses clients parmi 40 acheteurs ne prouve rien.
Seule la distribution de ses sorties tranche, mesuree sur une fenetre ancree dans l'epoque du token
et non sur son activite d'aujourd'hui.

`GET /v0/addresses/{addr}/transactions` rend 100 transactions parsees par appel et accepte
`before=<signature>`. On part de la signature datee du virement de decembre 2024 pour atterrir dans
l'epoque utile sans traverser les millions de transactions de 2025-2026 (piege nº1). Mesure par
delta de solde (`accountData[].nativeBalanceChange`), jamais par les seuls transferts.

Ecrit le profil du hub en JSON vers --out (defaut e5_hub_<label>.json).

Usage : python3 14_hub_bailleur.py --addr <ADDR> --anchor <SIG> --pages 40 --label G9X7F4Jz
"""
from __future__ import annotations
import argparse, json, time
from collections import Counter, defaultdict
import lib_trace as L

MIN = 0.05


def roundness(x):
    lam = round(x * L.LAMPORTS)
    for m, n in ((L.LAMPORTS, "rond_SOL"), (100_000_000, "rond_0.1"),
                 (10_000_000, "rond_0.01"), (1_000_000, "rond_0.001")):
        if lam % m == 0:
            return n
    return "precis_swap"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addr", required=True)
    ap.add_argument("--anchor", required=True, help="signature d'ancrage (epoque visee)")
    ap.add_argument("--pages", type=int, default=40, help="100 tx par page, vers le PASSE")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"e5_hub_{a.label}.json"

    before, seen, n_tx = a.anchor, set(), 0
    outs = defaultdict(lambda: {"total": 0.0, "n": 0, "amounts": []})
    ins = defaultdict(lambda: {"total": 0.0, "n": 0, "amounts": []})
    types = Counter()
    tmin, tmax, pages = None, None, 0
    for _ in range(a.pages):
        batch = L.helius_parsed(a.addr, before=before, limit=100)
        if not batch:
            break
        pages += 1
        for tx in batch:
            sig = tx.get("signature")
            if not sig or sig in seen:
                continue
            seen.add(sig)
            n_tx += 1
            ts = L.tx_ts(tx)
            if ts:
                tmin = ts if tmin is None else min(tmin, ts)
                tmax = ts if tmax is None else max(tmax, ts)
            types[f"{tx.get('type')}/{tx.get('source')}"] += 1
            d = L.balance_deltas(tx)
            if d.get(a.addr, 0.0) < 0:                       # le hub paie
                for k, dv in d.items():
                    if k == a.addr or dv < MIN or k in L.SYSTEM_ACCOUNTS:
                        continue
                    e = outs[k]; e["total"] += dv; e["n"] += 1; e["amounts"].append(round(dv, 9))
            if d.get(a.addr, 0.0) > 0:                       # le hub encaisse
                for k, dv in d.items():
                    if k == a.addr or dv > -MIN or k in L.SYSTEM_ACCOUNTS:
                        continue
                    e = ins[k]; e["total"] += -dv; e["n"] += 1; e["amounts"].append(round(-dv, 9))
        before = batch[-1].get("signature")
        time.sleep(0.08)

    amt_out = Counter()
    for v in outs.values():
        for x in v["amounts"]:
            amt_out[round(x, 9)] += 1

    span_h = (tmax - tmin) / 3600.0 if tmin and tmax else 0.0
    res = {"label": a.label, "addr": a.addr, "anchor": a.anchor,
           "n_tx_lues": n_tx, "pages": pages,
           "fenetre_utc": [L.utc(tmin), L.utc(tmax)],
           "duree_heures": round(span_h, 2),
           "tx_par_jour_estime": round(n_tx / (span_h / 24), 0) if span_h > 0 else None,
           "n_destinataires_distincts": len(outs),
           "n_payeurs_distincts": len(ins),
           "montants_de_sortie_les_plus_repetes": [
               {"montant_sol": m, "n": n, "calibre": roundness(m)}
               for m, n in amt_out.most_common(15)],
           "top_destinataires": [{"addr": k, "total_sol": round(v["total"], 6), "n": v["n"],
                                  "amounts_sol": sorted(v["amounts"])[:8]}
                                 for k, v in sorted(outs.items(),
                                                    key=lambda kv: -kv[1]["total"])[:15]],
           "top_payeurs": [{"addr": k, "total_sol": round(v["total"], 6), "n": v["n"],
                            "known": L.KNOWN.get(k), "calibres": sorted({roundness(x)
                                                                         for x in v["amounts"]}),
                            "amounts_sol": sorted(v["amounts"])[:8]}
                           for k, v in sorted(ins.items(), key=lambda kv: -kv[1]["total"])[:15]],
           "types_de_tx": types.most_common(15),
           "terminaux_connus_croises": sorted({k: L.KNOWN[k] for k in
                                               list(outs) + list(ins) if k in L.KNOWN}.items())}
    json.dump(res, open(out, "w"), indent=1)

    print(f"\n=== {a.label} — {n_tx} tx lues sur {res['fenetre_utc'][0]} → "
          f"{res['fenetre_utc'][1]} ({res['duree_heures']} h) ===")
    print(f"  cadence estimee : {res['tx_par_jour_estime']} tx/jour")
    print(f"  destinataires distincts : {len(outs)} · payeurs distincts : {len(ins)}")
    print("  montants de sortie les plus repetes :")
    for m in res["montants_de_sortie_les_plus_repetes"][:10]:
        print(f"    {m['montant_sol']:>14.9f} SOL x{m['n']:<4d} [{m['calibre']}]")
    print("  principaux payeurs :")
    for p in res["top_payeurs"][:8]:
        tag = f"  <== {p['known']}" if p["known"] else ""
        print(f"    {p['total_sol']:>12.4f} SOL en {p['n']:>3d} fois "
              f"[{','.join(p['calibres'])}]  {p['addr']}{tag}")
    print(f"  types : {res['types_de_tx'][:6]}")
    for k, v in res["terminaux_connus_croises"]:
        print(f"  ⇒ TERMINAL CONNU : {v}  {k}")
    print(f"  -> {out}")


if __name__ == "__main__":
    main()
