#!/usr/bin/env python3
"""Recolte de mints pump.fun crees dans une fenetre de slots donnee.

Principe : dans une transaction de creation pump.fun, la KEYPAIR DU MINT SIGNE la
transaction. Un compte signataire dont l'adresse se termine par "pump" est donc un
mint pump.fun en train d'etre cree. On lit les blocs avec transactionDetails="accounts"
(leger : pas d'instructions, juste les cles de comptes + drapeaux signataire).

CLIENT
------
Client Helius unique (rpc_client.py) : les clés viennent de l'environnement
($HELIUS_API_KEYS, ou .env non versionné — voir settings.py) et **un échec réseau
LÈVE** au lieu de se déguiser en bloc sauté. Les slots sautés, eux, renvoient une
erreur JSON-RPC qui est une réponse légitime (« slot skipped »), tolérée en None
via tolerate_codes (docs/PITFALLS.md, règle n°2). Aucune clé n'est stockée ici.
"""
from __future__ import annotations
import datetime as dt, json, os, sys
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client  # noqa: E402

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

# getBlock / getBlockTime sur un slot saute renvoie une erreur JSON-RPC qui est une
# reponse legitime (« slot skipped »), pas une panne : on la tolere en None.
SKIPPED_SLOT_CODES = (-32007, -32009, -32004)


def slot_for_ts(target_ts: int, lo: int = 1,
                hi: Optional[int] = None) -> Optional[tuple[int, int]]:
    """Binary search slot -> blockTime. Renvoie le slot dont le temps <= target_ts."""
    if hi is None:
        hi = rpc_client.rpc("getSlot", [])
    best: Optional[tuple[int, int]] = None
    while lo < hi:
        mid = (lo + hi) // 2
        t = None
        # les slots sautes n'ont pas de blockTime : on decale
        for d in range(0, 60):
            t = rpc_client.rpc("getBlockTime", [mid + d],
                               tolerate_codes=SKIPPED_SLOT_CODES)
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


def block_pump_mints(slot: int) -> Optional[list[tuple[str, Optional[str]]]]:
    """Renvoie [(mint, signature)] des mints pump.fun CREES dans ce bloc."""
    b = rpc_client.rpc("getBlock", [slot, {
        "encoding": "json", "transactionDetails": "accounts",
        "rewards": False, "maxSupportedTransactionVersion": 0}],
        tolerate_codes=SKIPPED_SLOT_CODES)
    if not b:
        return None  # bloc saute / indisponible
    out: list[tuple[str, Optional[str]]] = []
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


def harvest(start_slot: int, n_slots: int,
            workers: int = 12) -> tuple[list[dict], int, int]:
    slots = list(range(start_slot, start_slot + n_slots))
    found: list[dict] = []
    skipped = 0
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
