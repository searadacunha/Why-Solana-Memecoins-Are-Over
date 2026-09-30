#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect, for every alert, every transaction on the mint from the creation slot
to the alert + 30 s.

This is the raw material of every pre-entry feature: the bundle itself, the
other buyers of the creation slot, the migration, the first pool trades, the
accounts bots open to get ready, the snipers' own exits before the alert. The
window ends 30 s after the alert because the pre-declared variant enters there;
the primary model only reads what happened before the alert.

How the window is read, and why this way
  getSignaturesForAddress pages from the newest transaction down. For a token
  that kept trading, "newest" is weeks after the window, so the walk starts
  from a cursor: the first signature of a block whose time is at or after the
  window's end (the same technique as the detector's analysis code). From
  there it pages down until it passes below the creation slot. Every
  successful signature of the window is then fetched with getTransaction
  (jsonParsed). Failed signatures are kept as signatures only.
  Inside one slot, the RPC gives no transaction index, so the order of the
  transactions of a slot is unknown and nothing downstream relies on it.

Output: data/onchain_cache/win/<mint>.json.gz (untracked, raw), one per alert,
written atomically. A rerun only fetches what is missing. Every failure
raises: a window is either complete or absent, never partial.

Usage:
    HELIUS_API_KEYS=k1,k2,k3 python3 post_detection_forensics/code/col_10_windows.py [--alerts FILE] [--limit N]
"""
from __future__ import annotations

import gzip
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "code"))
import rpc_client as R  # noqa: E402  (HeliusError, STATS kept for the log)
import frpc  # noqa: E402

CACHE = os.path.join(STUDY, "data", "onchain_cache", "win")
POST_WINDOW = 30.0          # seconds after the alert (the +30 s entry variant)
# Solana transaction version 1 appeared on mainnet in mid-September 2026; a request
# capped at 0 fails with -32015 on any window or block holding one (542 windows
# lost on 2026-09-29, nearly all alerts from 2026-09-15 on). Legacy and v0 come
# back unchanged under this cap.
TX_VERSION = 1
SLOT_S = 0.4                # nominal slot time, only used to guess where to look




def call(method: str, params: list[Any], tolerate: tuple[int, ...] = ()) -> Any:
    """Paced per key by frpc (see its header for why not rpc_client here)."""
    return frpc.rpc(method, params, tolerate)


def cursor(slot0: int, t_create: float, w_end: float) -> dict[str, Any]:
    """First signature of the first block at or after w_end."""
    slot = slot0 + max(1, int((w_end - t_create) / SLOT_S))
    seen_before = False
    for _ in range(400):
        b = call("getBlock", [slot, {"transactionDetails": "signatures", "rewards": False,
                                     "maxSupportedTransactionVersion": TX_VERSION}], tolerate=(-32007, -32009))
        if b is None or not b.get("signatures"):
            slot += 1
            continue
        bt = b.get("blockTime") or 0
        if bt < w_end:
            seen_before = True
            slot += max(1, int((w_end - bt) / SLOT_S))
            continue
        if not seen_before and bt > w_end + 3:
            # landed too late: step back until a block before w_end is found
            slot -= max(1, int((bt - w_end) / SLOT_S) + 2)
            continue
        return {"slot": slot, "blockTime": bt, "signature": b["signatures"][0]}
    raise R.HeliusError("no cursor block found after slot %d" % slot0)


def window(a: dict[str, Any]) -> dict[str, Any]:
    mint, slot0 = a["mint"], a["slot"]
    t_alert = a["t"]
    t_create = t_alert - (a.get("age_alerte_s") or 12.0)
    w_end = t_alert + POST_WINDOW
    cur = cursor(slot0, t_create, w_end)
    before, sigs, pages, reached = cur["signature"], [], 0, False
    while True:
        page = frpc.sigs(mint, 1000, before)
        pages += 1
        sigs += page
        if not page or len(page) < 1000 or page[-1]["slot"] < slot0:
            reached = True
            break
        if pages >= 50:
            break
        before = page[-1]["signature"]
    if not reached:
        raise R.HeliusError("%s: 50 pages without reaching the creation slot" % mint[:8])
    win = [{"sig": s["signature"], "slot": s["slot"], "bt": s.get("blockTime"), "err": s.get("err") is not None}
           for s in sigs if s["slot"] >= slot0 and (s.get("blockTime") or 0) <= w_end]
    txs = {}
    for s in win:
        if s["err"]:
            continue
        t = call("getTransaction", [s["sig"], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": TX_VERSION}])
        if t is None:
            raise R.HeliusError("getTransaction returned null for %s" % s["sig"][:12])
        txs[s["sig"]] = t
    if not any(s["slot"] == slot0 for s in win):
        raise R.HeliusError("%s: no transaction in the creation slot" % mint[:8])
    return {"mint": mint, "slot0": slot0, "t_alert": t_alert, "t_create_est": t_create, "w_end": w_end,
            "cursor": cur, "pages": pages, "reached_slot0": reached, "sigs": win, "txs": txs,
            "collected_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}


def path(mint: str) -> str:
    return os.path.join(CACHE, mint + ".json.gz")


def save(doc: dict[str, Any]) -> None:
    p = path(doc["mint"])
    tmp = p + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf8") as f:
        json.dump(doc, f, separators=(",", ":"))
    os.replace(tmp, p)


def load_alerts(src: str) -> list[dict[str, Any]]:
    with gzip.open(src, "rt", encoding="utf8") as f:
        return [r for r in (json.loads(x) for x in f) if r["genre"] == "alerte_lancement"]


def main() -> None:
    src = os.path.join(ROOT, "post_detection_edge", "data", "journal.jsonl.gz")
    if "--alerts" in sys.argv:
        src = sys.argv[sys.argv.index("--alerts") + 1]
    alerts = sorted(load_alerts(src), key=lambda r: r["t"])
    if "--only" in sys.argv:
        keep = set(json.load(open(sys.argv[sys.argv.index("--only") + 1])))
        alerts = [x for x in alerts if x["mint"] in keep]
    if "--limit" in sys.argv:
        alerts = alerts[: int(sys.argv[sys.argv.index("--limit") + 1])]
    os.makedirs(CACHE, exist_ok=True)
    todo = [a for a in alerts if not os.path.exists(path(a["mint"]))]
    print("alerts %d, cached %d, to fetch %d" % (len(alerts), len(alerts) - len(todo), len(todo)), flush=True)
    t0, done, failed = time.time(), 0, []

    def one(a: dict[str, Any]) -> tuple[str, int]:
        doc = window(a)
        save(doc)
        return a["mint"], len(doc["txs"])

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(one, a): a for a in todo}
        for f in as_completed(futs):
            try:
                _, n = f.result()
                done += 1
            except Exception as e:  # noqa: BLE001  (logged and counted; the window stays absent)
                failed.append((futs[f]["mint"], str(e)[:120]))
            if (done + len(failed)) % 25 == 0 or done + len(failed) == len(todo):
                el = time.time() - t0
                print("%d/%d done, %d failed, %.0f s, rpc %d, 429s %d, retries %d, %.1f calls/s" % (
                    done, len(todo), len(failed), el, frpc.STATS["rpc"], frpc.STATS["r429"], frpc.STATS["retry"],
                    frpc.STATS["rpc"] / max(el, 1)), flush=True)
    for m, e in failed[:20]:
        print("FAILED %s %s" % (m, e), flush=True)
    print("END done %d failed %d rpc %d" % (done, len(failed), frpc.STATS["rpc"]), flush=True)


if __name__ == "__main__":
    main()
