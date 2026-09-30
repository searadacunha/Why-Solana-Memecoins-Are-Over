#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wallet histories and funding, strictly before each wallet's first appearance in
the launch window.

For every alert whose window is collected (col_10), the wallets that matter are:
  core      owners of the creation-slot bonding-curve buys of 5 SOL or more
            (identity-free, the definition of code/v05_creation_block.py);
  creator   the signer of the create transaction;
  early     the first 25 other wallets active before the alert (primary entry),
  late      and the first 25 new ones between the alert and +30 s (the variant).
For each (wallet, launch), with the wallet's first transaction of the window as
cursor, one page of getSignaturesForAddress returns up to 1 000 transactions
strictly EARLIER than that point: history available to a bot at the time,
nothing later. A wallet with fewer than 1 000 earlier transactions has reached
its genesis; its first transaction is then read to find who funded it (the
account whose SOL fell the most). Funders are walked up two more hops (hop 2,
hop 3), each strictly before the earliest transaction in which it funded a
wallet of the corpus (genesis_before), so that neither its hub status nor its
own funder depends on anything later; an address with more than 3 000
transactions before that point is recorded as a hub and not walked further. For the core wallets
and the creator, the most recent earlier transactions are also read (5 and 20)
to see what they were doing just before: last SOL received, prior token
trades, prior token creations.

Output (untracked, raw): data/onchain_cache/wal/<mint>.json.gz per alert and
data/onchain_cache/genesis/<address>.json per address. Resumable; every
failure raises for the alert, which is then absent rather than partial.

Usage:
    HELIUS_API_KEYS=k1,k2,k3 python3 post_detection_forensics/code/col_20_wallets.py [--alerts FILE] [--limit N]
"""
from __future__ import annotations

import gzip
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

import col_10_windows as C
import fparse
import frpc

R = C.R
CACHE = os.path.join(C.STUDY, "data", "onchain_cache")
WAL = os.path.join(CACHE, "wal")
GEN = os.path.join(CACHE, "genesis")
CORE_MIN_SOL = 5.0
N_EARLY = 25
LAST_CORE, LAST_CREATOR = 5, 20
HUB_PAGES = 3
GEN_HOP = os.path.join(CACHE, "genesis_hop")
PUMP_SUFFIX = "pump"


def roles(a: dict[str, Any], recs: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """[(wallet, role, cursor signature)] in order of first appearance."""
    slot0 = recs[0]["slot"] if recs else a["slot"]
    first: dict[str, str] = {}
    order: list[str] = []
    for r in recs:
        if r.get("err"):
            continue
        for w in [r.get("signer")] + list((r.get("legs") or {}).keys()):
            if w and w not in first:
                first[w] = r["sig"]
                order.append(w)
    core_sol: dict[str, float] = {}
    for r in recs:
        if r.get("kind") == "buy" and r.get("venue") == "curve" and r["slot"] == slot0:
            # SOL each wallet itself sent to the curve (fparse leg_sol), not a
            # pro-rata of tokens: the audit of 2026-09-29 found the pro-rata off
            # by up to 12.8 SOL in multi-wallet transactions
            for o, v in (r.get("leg_sol") or {}).items():
                core_sol[o] = core_sol.get(o, 0.0) + v
    core = [w for w in order if core_sol.get(w, 0.0) >= CORE_MIN_SOL]
    creators = [r["signer"] for r in recs if r.get("kind") == "create"]
    creator = creators[0] if creators else a.get("createur")
    out = [(w, "core", first[w]) for w in core]
    if creator and creator in first and creator not in core:
        out.append((creator, "creator", first[creator]))
    taken = set(core) | {creator}
    early, late = [], []
    for w in order:
        if w in taken or w in (fparse.bonding_curve_pda(a["mint"]),):
            continue
        rec_t = next(r["bt"] for r in recs if r["sig"] == first[w])
        if rec_t is not None and rec_t <= a["t"] - 1 and len(early) < N_EARLY:
            early.append(w)
        elif rec_t is not None and a["t"] - 1 < rec_t <= a["t"] + 29 and len(late) < N_EARLY:
            late.append(w)
    out += [(w, "early", first[w]) for w in early] + [(w, "late", first[w]) for w in late]
    return out


def prior(wallet: str, cursor: str) -> dict[str, Any]:
    page = frpc.sigs(wallet, 1000, cursor)
    bts = [s.get("blockTime") or 0 for s in page]
    return {"n": len(page), "genesis": len(page) < 1000,
            "oldest_sig": page[-1]["signature"] if page else None,
            "bts": bts, "n_err": sum(1 for s in page if s.get("err") is not None),
            "recent_sigs": [s["signature"] for s in page[:LAST_CREATOR]]}


def funding_of(address: str, first_sig: str) -> dict[str, Any]:
    """Who sent SOL to `address` in its first transaction."""
    t = C.call("getTransaction", [first_sig, {"encoding": "jsonParsed",
                                              "maxSupportedTransactionVersion": C.TX_VERSION}])
    if t is None:
        raise R.HeliusError("genesis tx null for %s" % address[:8])
    keys = [k["pubkey"] for k in t["transaction"]["message"]["accountKeys"]]
    meta = t["meta"]
    d = {k: (meta["postBalances"][i] - meta["preBalances"][i]) / 1e9 for i, k in enumerate(keys)}
    received = d.get(address, 0.0)
    senders = {k: -v for k, v in d.items() if v < 0 and k != address}
    funder = max(senders, key=lambda k: senders[k]) if senders else None
    return {"sig": first_sig, "bt": t.get("blockTime"), "received": received, "funder": funder,
            "funder_sent": senders.get(funder) if funder else None, "fee_payer": keys[0],
            "n_accounts": len(keys)}


def _dump(doc: dict[str, Any], p: str) -> None:
    with open(p + ".tmp", "w") as fh:
        json.dump(doc, fh)
    os.replace(p + ".tmp", p)


def genesis(address: str, first_sig: Optional[str] = None) -> dict[str, Any]:
    """Genesis facts of an address, cached (written atomically). first_sig when already known."""
    p = os.path.join(GEN, address + ".json")
    if os.path.exists(p):
        return json.load(open(p))
    if first_sig is None:
        before, n, oldest = None, 0, None
        for _ in range(HUB_PAGES):
            page = frpc.sigs(address, 1000, before)
            n += len(page)
            if not page:
                break
            oldest = page[-1]
            if len(page) < 1000:
                break
            before = page[-1]["signature"]
        else:
            doc = {"address": address, "hub": True, "n_seen": n}
            _dump(doc, p)
            return doc
        if oldest is None:
            doc = {"address": address, "empty": True}
            _dump(doc, p)
            return doc
        first_sig = oldest["signature"]
        doc = {"address": address, "hub": False, "n_total": n, "first_bt": oldest.get("blockTime")}
    else:
        doc = {"address": address, "hub": False}
    doc["funding"] = funding_of(address, first_sig)
    _dump(doc, p)
    return doc


def recent(sigs: list[str], k: int) -> list[dict[str, Any]]:
    """Compact view of the k most recent earlier transactions of a wallet."""
    out = []
    for s in sigs[:k]:
        t = C.call("getTransaction", [s, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": C.TX_VERSION}])
        if t is None:
            continue
        meta = t["meta"]
        keys = [x["pubkey"] for x in t["transaction"]["message"]["accountKeys"]]
        logs = meta.get("logMessages") or []
        names = [ln.split("Instruction: ", 1)[1].strip() for ln in logs if "Instruction: " in ln]
        mints = sorted({b.get("mint") for b in (meta.get("postTokenBalances") or [])
                        if b.get("mint", "").endswith(PUMP_SUFFIX)})
        out.append({"sig": s, "bt": t.get("blockTime"), "signer": keys[0], "err": meta.get("err") is not None,
                    "creates": sum(1 for n in names if n in ("CreateV2", "Create")),
                    "buys": sum(1 for n in names if n in ("Buy", "BuyExactQuoteIn", "BuyExactSolIn")),
                    "sells": sum(1 for n in names if n == "Sell"), "pump_mints": mints[:5],
                    "d": {k: round((meta["postBalances"][i] - meta["preBalances"][i]) / 1e9, 6)
                          for i, k in enumerate(keys) if meta["postBalances"][i] != meta["preBalances"][i]}})
    return out


def one(a: dict[str, Any]) -> tuple[str, int]:
    w = json.load(gzip.open(os.path.join(C.CACHE, a["mint"] + ".json.gz"), "rt"))
    recs, facts = fparse.parse_window(w)
    doc: dict[str, Any] = {"mint": a["mint"], "t_alert": a["t"], "facts": facts, "wallets": {}}
    bt_of = {r["sig"]: r.get("bt") for r in recs}
    for wal, role, cur in roles(a, recs):
        pr = prior(wal, cur)
        entry: dict[str, Any] = {"role": role, "cursor": cur, "first_bt": bt_of.get(cur),
                                 "prior": {k: v for k, v in pr.items() if k != "recent_sigs"}}
        if pr["genesis"] and pr["oldest_sig"]:
            entry["genesis"] = genesis(wal, pr["oldest_sig"])
        elif pr["n"] == 0:
            entry["genesis"] = {"address": wal, "first_in_window": True}
        if role in ("core", "creator"):
            entry["recent"] = recent(pr["recent_sigs"], LAST_CORE if role == "core" else LAST_CREATOR)
        doc["wallets"][wal] = entry
    p = os.path.join(WAL, a["mint"] + ".json.gz")
    with gzip.open(p + ".tmp", "wt", encoding="utf8") as f:
        json.dump(doc, f, separators=(",", ":"))
    os.replace(p + ".tmp", p)
    return a["mint"], len(doc["wallets"])


def genesis_before(address: str, cursor: str) -> dict[str, Any]:
    """Genesis of a funder as it could be seen BEFORE `cursor`, the earliest
    transaction in which this address funded a wallet of the corpus. Its hub
    status (more than HUB_PAGES x 1 000 earlier transactions) and its own funder
    therefore depend on nothing that happened after that funding, hence after
    any launch it is linked to. Cached in genesis_hop/, written atomically."""
    p = os.path.join(GEN_HOP, address + ".json")
    if os.path.exists(p):
        return json.load(open(p))
    before, n, oldest = cursor, 0, None
    for _ in range(HUB_PAGES):
        page = frpc.sigs(address, 1000, before)
        n += len(page)
        if not page:
            break
        oldest = page[-1]
        if len(page) < 1000:
            break
        before = page[-1]["signature"]
    else:
        doc = {"address": address, "cursor": cursor, "hub_before_cursor": True, "n_seen": n}
        _dump(doc, p)
        return doc
    if oldest is None:
        doc = {"address": address, "cursor": cursor, "empty_before_cursor": True}
        _dump(doc, p)
        return doc
    doc = {"address": address, "cursor": cursor, "hub_before_cursor": False, "n_before_cursor": n,
           "first_bt": oldest.get("blockTime"), "funding": funding_of(address, oldest["signature"])}
    _dump(doc, p)
    return doc


def _funding_records() -> list[dict[str, Any]]:
    out = []
    for d in (GEN, GEN_HOP):
        for f in os.listdir(d):
            if f.endswith(".json"):
                g = json.load(open(os.path.join(d, f)))
                if (g.get("funding") or {}).get("funder"):
                    out.append(g["funding"])
    return out


def hops() -> None:
    """Hop 2 and hop 3: each funder walked back from its earliest funding."""
    os.makedirs(GEN_HOP, exist_ok=True)
    done: set[str] = {f[:-5] for f in os.listdir(GEN_HOP) if f.endswith(".json")}
    for hop in (2, 3):
        earliest: dict[str, tuple[float, str]] = {}
        for fu in _funding_records():
            f, bt, sig = fu["funder"], fu.get("bt") or 0, fu["sig"]
            if f not in earliest or bt < earliest[f][0]:
                earliest[f] = (bt, sig)
        todo = sorted(f for f in earliest if f not in done)
        with ThreadPoolExecutor(max_workers=8) as ex:
            list(ex.map(lambda f: genesis_before(f, earliest[f][1]), todo))
        done |= set(todo)
        print("hop %d: %d funders walked" % (hop, len(todo)), flush=True)


def main() -> None:
    src = os.path.join(C.ROOT, "post_detection_edge", "data", "journal.jsonl.gz")
    if "--alerts" in sys.argv:
        src = sys.argv[sys.argv.index("--alerts") + 1]
    alerts = sorted(C.load_alerts(src), key=lambda r: r["t"])
    if "--only" in sys.argv:
        keep = set(json.load(open(sys.argv[sys.argv.index("--only") + 1])))
        alerts = [x for x in alerts if x["mint"] in keep]
    if "--limit" in sys.argv:
        alerts = alerts[: int(sys.argv[sys.argv.index("--limit") + 1])]
    os.makedirs(WAL, exist_ok=True)
    os.makedirs(GEN, exist_ok=True)
    os.makedirs(GEN_HOP, exist_ok=True)
    todo = [a for a in alerts if os.path.exists(os.path.join(C.CACHE, a["mint"] + ".json.gz"))
            and not os.path.exists(os.path.join(WAL, a["mint"] + ".json.gz"))]
    print("alerts %d, windows ready %d, to fetch %d" % (
        len(alerts), sum(1 for a in alerts if os.path.exists(os.path.join(C.CACHE, a["mint"] + ".json.gz"))),
        len(todo)), flush=True)
    t0, done, failed = time.time(), 0, []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(one, a): a for a in todo}
        for f in as_completed(futs):
            try:
                f.result()
                done += 1
            except Exception as e:  # noqa: BLE001  (counted; the alert stays absent)
                failed.append((futs[f]["mint"], str(e)[:120]))
            if (done + len(failed)) % 25 == 0 or done + len(failed) == len(todo):
                el = time.time() - t0
                print("%d/%d done, %d failed, %.0f s, rpc %d, 429s %d, retries %d" % (
                    done, len(todo), len(failed), el, frpc.STATS["rpc"], frpc.STATS["r429"], frpc.STATS["retry"]),
                    flush=True)
    for m, e in failed[:20]:
        print("FAILED %s %s" % (m, e), flush=True)
    if "--no-hops" not in sys.argv:
        hops()
    print("END done %d failed %d rpc %d" % (done, len(failed), frpc.STATS["rpc"]), flush=True)


if __name__ == "__main__":
    main()
