#!/usr/bin/env python3
"""Recolte de mints pump.fun crees dans une fenetre de slots donnee.

Principe : dans une transaction de creation pump.fun, la KEYPAIR DU MINT SIGNE la
transaction. Un compte signataire dont l'adresse se termine par "pump" est donc un
mint pump.fun en train d'etre cree. On lit les blocs avec transactionDetails="accounts"
(leger : pas d'instructions, juste les cles de comptes + drapeaux signataire).

Aucune cle en dur : SOLANA_RPC_URL vient de l'environnement.
"""
from __future__ import annotations
import json, os, sys, time, urllib.request, datetime as dt
from concurrent.futures import ThreadPoolExecutor

RPC = os.environ.get("SOLANA_RPC_URL", "")
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"


def rpc(method, params, retries=5, timeout=60):
    if not RPC:
        sys.exit("SOLANA_RPC_URL non defini.")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params}).encode()
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(RPC, data=body, headers={
                "Content-Type": "application/json", "User-Agent": "harvest/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.load(r)
            if "result" in out:
                return out["result"]
            last = out.get("error")
            # slot saute / non disponible : inutile de reessayer
            if isinstance(last, dict) and last.get("code") in (-32007, -32009, -32004):
                return None
        except Exception as e:
            last = str(e)
        time.sleep(1.0 * (i + 1))
    return None


def slot_for_ts(target_ts, lo=1, hi=None):
    """Binary search slot -> blockTime. Renvoie le slot dont le temps <= target_ts."""
    if hi is None:
        hi = rpc("getSlot", [])
    best = None
    while lo < hi:
        mid = (lo + hi) // 2
        t = None
        # les slots sautes n'ont pas de blockTime : on decale
        for d in range(0, 60):
            t = rpc("getBlockTime", [mid + d])
            if t:
                mid = mid + d
                break
        if not t:
            hi = mid
            continue
        if t <= target_ts:
            best = (mid, t)
            lo = mid + 1
        else:
            hi = mid
    return best


def block_pump_mints(slot):
    """Renvoie [(mint, signature)] des mints pump.fun CREES dans ce bloc."""
    b = rpc("getBlock", [slot, {
        "encoding": "json", "transactionDetails": "accounts",
        "rewards": False, "maxSupportedTransactionVersion": 0}])
    if not b:
        return None  # bloc saute / indisponible
    out = []
    for tx in b.get("transactions", []):
        meta = tx.get("meta") or {}
        if meta.get("err"):
            continue
        keys = (tx.get("transaction") or {}).get("accountKeys") or []
        names = {k.get("pubkey") for k in keys}
        if PUMP_PROGRAM not in names:
            continue
        for k in keys:
            pk = k.get("pubkey", "")
            if k.get("signer") and pk.endswith("pump"):
                sigs = (tx.get("transaction") or {}).get("signatures") or []
                out.append((pk, sigs[0] if sigs else None))
    return out


def harvest(start_slot, n_slots, workers=12):
    slots = list(range(start_slot, start_slot + n_slots))
    found, skipped = [], 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for slot, res in zip(slots, ex.map(block_pump_mints, slots)):
            if res is None:
                skipped += 1
                continue
            for mint, sig in res:
                found.append({"mint": mint, "slot": slot, "sig": sig})
    return found, skipped, len(slots)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ts", type=int, help="timestamp unix cible")
    ap.add_argument("--slot", type=int)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.slot:
        s = a.slot
    else:
        r = slot_for_ts(a.ts)
        print("slot trouve:", r, dt.datetime.utcfromtimestamp(r[1]).isoformat(), file=sys.stderr)
        s = r[0]
    found, skipped, total = harvest(s, a.n)
    print(f"blocs={total} sautes={skipped} mints={len(found)}", file=sys.stderr)
    js = json.dumps({"start_slot": s, "n_slots": total, "skipped": skipped,
                     "mints": found}, indent=1)
    if a.out:
        open(a.out, "w").write(js)
    else:
        print(js)
