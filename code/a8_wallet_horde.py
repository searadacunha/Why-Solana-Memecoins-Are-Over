#!/usr/bin/env python3
"""Disposable wallets, or a reusable fleet? — the question of what happens AFTER the trade.

Every other measurement in this repository looks upstream: who funded the buyer. This one looks the
other way, and it is the direction that turned out to matter.

TWO MODELS, DIFFERENT PREDICTIONS
- DISPOSABLE : the wallet receives, buys, sells, dies. Few transactions after the trade, and no
               outgoing payments to accounts that did not already exist.
- FLEET      : the wallet is kept, reactivated later, and used to FUND fresh wallets — which in
               turn fund others. That predicts outgoing payments to addresses whose FIRST activity
               is the payment itself: generations.

For each identified wallet this measures how long it stayed alive after its trade, how many
distinct addresses it went on to fund, and — the discriminating number — how many of those were
NEW at the moment of payment (first activity within an hour of receiving). A payment to an address
that is born on receipt is not a transfer between existing accounts; it is a wallet being created.

USAGE
    export HELIUS_API_KEYS=key1[,key2,...]
    python3 code/a8_wallet_horde.py
Needs the network. Its output, data/split/horde.json, is committed so the finding is checkable
without a key.
"""
from __future__ import annotations

import json, os, sys, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor

import rpc_client
import settings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "split", "all_buyers_g2y.json")
OUT = os.path.join(ROOT, "data", "split", "horde.json")
L = 1e9
MIN_SOL = 0.01


class Echec(Exception):
    pass


# Le transport Helius (JSON-RPC + transactions parsees) est delegue au client
# partage rpc_client : rotation de cles, cooldown apres un 429, reprises bornees,
# et surtout UNE seule regle d'erreur -- il LEVE HeliusError, il ne rend jamais
# [] ou None pour dire "echec". On conserve ici les fines enveloppes
# rpc()/parsed() qui retraduisent HeliusError en Echec, afin de ne rien changer
# aux appelants (naissance/etudie attrapent deja Echec). Les parametres ki/tries
# subsistent pour la compatibilite d'appel mais ne servent plus : rpc_client
# possede desormais la rotation et les reprises.
def rpc(method, params, ki=0, tries=8):
    try:
        return rpc_client.rpc(method, params)
    except rpc_client.HeliusError as e:
        raise Echec(f"{method}: {e}")


def parsed(addr, ki=0, before=None, tries=5):
    try:
        return rpc_client.enhanced(addr, limit=100, before=before)
    except rpc_client.HeliusError as e:
        raise Echec(f"parsed {addr[:10]}: {e}")


def naissance(addr, ki=0):
    """Premiere activite d'une adresse. None si hors de portee."""
    before, oldest = None, None
    for _ in range(6):
        try:
            page = rpc("getSignaturesForAddress", [addr, {"limit": 1000, "before": before}], ki=ki)
        except Echec:
            return None
        if not page:
            break
        o = min((s.get("blockTime") or 0) for s in page)
        oldest = o if oldest is None else min(oldest, o)
        if len(page) < 1000:
            return oldest
        before = page[-1]["signature"]
    return None


def etudie(args):
    idx, wallet, t_ref = args
    sorties, n_tx, before, dernier = {}, 0, None, None
    for _ in range(25):
        try:
            batch = parsed(wallet, ki=idx, before=before)
        except Echec:
            return wallet, {"statut": "illisible"}
        if not batch:
            break
        for tx in batch:
            n_tx += 1
            ts = tx.get("timestamp") or 0
            dernier = ts if dernier is None else max(dernier, ts)
            for t in (tx.get("nativeTransfers") or []):
                amt = (t.get("amount") or 0) / L
                if amt < MIN_SOL:
                    continue
                if t.get("fromUserAccount") == wallet and t.get("toUserAccount") != wallet:
                    d = t["toUserAccount"]
                    e = sorties.setdefault(d, {"sol": 0.0, "n": 0, "premier_ts": ts})
                    e["sol"] += amt
                    e["n"] += 1
                    e["premier_ts"] = min(e["premier_ts"], ts)
        if len(batch) < 100:
            break
        before = batch[-1].get("signature")
        time.sleep(0.05)

    # Une sortie vers une adresse NEUVE = generation suivante.
    neuves = {}
    for d, e in sorted(sorties.items(), key=lambda kv: -kv[1]["sol"])[:25]:
        nb = naissance(d, ki=idx)
        if nb is not None and abs(nb - e["premier_ts"]) <= 3600:
            neuves[d] = {"sol": round(e["sol"], 6), "n": e["n"],
                         "quand": dt.datetime.fromtimestamp(e["premier_ts"], dt.UTC)
                                  .strftime("%Y-%m-%d %H:%M")}
        time.sleep(0.03)

    return wallet, {"statut": "ok", "n_tx": n_tx,
                    "derniere_activite": dt.datetime.fromtimestamp(dernier, dt.UTC)
                                          .strftime("%Y-%m-%d") if dernier else None,
                    "jours_apres_le_trade": round((dernier - t_ref) / 86400, 1) if dernier else None,
                    "n_destinataires": len(sorties),
                    "n_destinataires_NEUFS": len(neuves),
                    "generation_suivante": neuves}


if not settings.helius_keys():
    sys.exit("Aucune cle Helius. export HELIUS_API_KEYS=cle1[,cle2] "
             "(ou .env a la racine).")

src = json.load(open(SRC))
cibles = []
for tok, v in src.items():
    if not v.get("mesurable"):
        continue
    t_ref = int(dt.datetime.strptime(v["creation"][:19], "%Y-%m-%dT%H:%M:%S")
                .replace(tzinfo=dt.UTC).timestamp())
    for w, r in (v.get("portefeuilles") or {}).items():
        if any(h["avant_token"] for h in (r.get("g2y") or [])):
            cibles.append((w, tok, t_ref))

uniq = {}
for w, tok, t in cibles:
    uniq.setdefault(w, (tok, t))
print(f"{len(uniq)} portefeuilles finances par le guichet avant leur token\n", flush=True)

res = {}
with ThreadPoolExecutor(max_workers=5) as ex:
    for w, r in ex.map(etudie, [(i, w, t) for i, (w, (tok, t)) in enumerate(uniq.items())]):
        res[w] = {**r, "token": uniq[w][0]}
        if r.get("statut") == "ok":
            print(f"  {w[:16]}… {uniq[w][0]:<11} tx={r['n_tx']:<5} "
                  f"actif +{r['jours_apres_le_trade']}j  "
                  f"finance {r['n_destinataires']} adresses dont "
                  f"{r['n_destinataires_NEUFS']} NEUVES", flush=True)

ok = [r for r in res.values() if r.get("statut") == "ok"]
avec_gen = [r for r in ok if r["n_destinataires_NEUFS"] > 0]
json.dump({"n_portefeuilles": len(res), "n_mesures": len(ok),
           "n_ayant_finance_des_adresses_neuves": len(avec_gen),
           "portefeuilles": res}, open(OUT, "w"), indent=1, ensure_ascii=False)
print(f"\n=== {len(avec_gen)}/{len(ok)} portefeuilles ont finance au moins une adresse NEUVE ===")
if ok:
    med = sorted(r["jours_apres_le_trade"] or 0 for r in ok)[len(ok) // 2]
    print(f"    duree de vie mediane apres le trade : {med} jours")
    print(f"    total adresses neuves engendrees    : "
          f"{sum(r['n_destinataires_NEUFS'] for r in ok)}")
print(f"-> {OUT}")
