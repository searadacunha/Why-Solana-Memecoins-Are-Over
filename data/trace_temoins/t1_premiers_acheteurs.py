#!/usr/bin/env python3
"""Etape 1 : les premiers acheteurs reels d'un token pump.fun.

Les principaux detenteurs actuels d'un token de 2024 ne disent rien de son lancement, la supply a
change de mains cent fois depuis. On lit donc la courbe de bonding depuis sa premiere transaction.

Le compte `bonding_curve` du token concentre toutes les operations d'achat et de vente sur la
courbe. On pagine ses signatures jusqu'a la genese (page incomplete), on trie par ordre
chronologique, puis on classe les signataires par ordre de premier achat. Un achat = variation
positive du solde du token pour le signataire et variation negative de son solde SOL, ce qui
distingue les acheteurs des vendeurs et du createur.

Ecrit e1_buyers_<label>.json dans --outdir.

Pieges : si la genese de la courbe n'est pas atteinte, l'ordre des premiers acheteurs n'est pas
fiable, le script le signale. Sous 10 acheteurs distincts, on ne peut ni confirmer ni infirmer une
signature de decoupage.

Usage :
    python3 etape1_premiers_acheteurs.py --mint <MINT> --curve <BONDING_CURVE> --label OPTIMUS
"""
from __future__ import annotations
import argparse, json, os, sys
import lib_trace as L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mint", required=True)
    ap.add_argument("--curve", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--n-buyers", type=int, default=40, help="premiers acheteurs distincts retenus")
    ap.add_argument("--max-tx", type=int, default=260, help="tx de courbe inspectees depuis le debut")
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()

    print(f"[{a.label}] courbe {a.curve}", flush=True)
    sigs, genesis, pages = L.all_signatures(a.curve, label=a.label)
    print(f"  {len(sigs)} signatures sur la courbe, {pages} pages, "
          f"genese {'ATTEINTE' if genesis else 'NON ATTEINTE (plafond)'}", flush=True)
    if not sigs:
        sys.exit("aucune signature sur la courbe")
    if not genesis:
        print("  ⚠️ la genese de la courbe n'est pas atteinte : l'ordre des premiers acheteurs "
              "n'est PAS fiable.", flush=True)

    subset = [s["signature"] for s in sigs[:a.max_tx]]
    txs = L.get_transactions(subset, progress=lambda d, t: None)
    print(f"  {len(txs)}/{len(subset)} transactions de tete recuperees", flush=True)

    t0 = sigs[0].get("blockTime")
    events, buyers, order = [], {}, []
    for s in sigs[:a.max_tx]:
        tx = txs.get(s["signature"])
        if not tx or tx.get("transactionError"):
            continue
        signer = L.signer_of(tx)
        if not signer:
            continue
        ts = tx.get("timestamp") or 0
        dtok = L.token_delta(tx, signer, a.mint)
        dsol = L.balance_deltas(tx).get(signer, 0.0)
        kind = "achat" if dtok > 0 and dsol < 0 else ("vente" if dtok < 0 else "autre")
        events.append({"sig": s["signature"], "ts": ts, "utc": L.utc(ts), "signer": signer,
                       "kind": kind, "token_delta": round(dtok, 6), "sol_delta": round(dsol, 9),
                       "rank_tx": len(events) + 1})
        if kind == "achat" and signer not in buyers and len(order) < a.n_buyers:
            buyers[signer] = {"wallet": signer, "rank": len(order) + 1, "first_buy_ts": ts,
                              "first_buy_utc": L.utc(ts),
                              "seconds_after_first_curve_tx": ts - t0 if ts and t0 else None,
                              "sol_spent_first_buy": round(-dsol, 9),
                              "tokens_first_buy": round(dtok, 6),
                              "first_buy_sig": s["signature"]}
            order.append(signer)

    res = {"label": a.label, "mint": a.mint, "curve": a.curve,
           "curve_signatures_total": len(sigs), "curve_genesis_reached": genesis,
           "first_curve_tx_ts": t0, "first_curve_tx_utc": L.utc(t0),
           "n_curve_tx_inspected": len(events),
           "n_distinct_early_buyers": len(order),
           "buyers": [buyers[w] for w in order],
           "curve_events_head": events[:120]}
    os.makedirs(a.outdir, exist_ok=True)
    p = os.path.join(a.outdir, f"e1_buyers_{a.label}.json")
    json.dump(res, open(p, "w"), indent=1)

    print(f"\n  1re tx de courbe : {L.utc(t0)} UTC")
    warn = ("  ⚠️ MOINS DE 10 : ce token est trop pauvre en acheteurs pour confirmer OU infirmer"
            " une signature de decoupage") if len(order) < 10 else ""
    print(f"  {len(order)} acheteurs distincts precoces retenus{warn}")
    for b in [buyers[w] for w in order][:15]:
        print(f"    #{b['rank']:>2d}  +{b['seconds_after_first_curve_tx']:>5}s  "
              f"{b['sol_spent_first_buy']:>12.9f} SOL  {b['wallet']}")
    print(f"  -> {p}")


if __name__ == "__main__":
    main()
