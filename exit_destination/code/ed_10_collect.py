#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The collection of analysis_plan.md section 3, and the same reading offline from the cache (ed_20_build.py calls
run() with an offline Fetch, so the build follows exactly the paths the collection read).

Order: wallets in a seeded shuffle; stage 1 the listing and the event windows of every wallet, stage 2 the
history before its first receipt, stage 3 the downstream hops breadth-first (hop 1 of every branch, then hop 2,
...). A budget stop therefore shortens the deepest hops evenly. Hard cap: ed_lib.CALL_CAP calls.

Usage (keys through the environment only, never printed):
    HELIUS_API_KEYS=$(cat post_detection_forensics/.helius_keys) FRPC_KEY_RPS=2 \
        python3 exit_destination/code/ed_10_collect.py [--threads 6]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

import ed_lib as L
import ed_trace as T
import em_lib as E
from rpc_client import HeliusError


def _guard(fn: Callable[[], Any], F: T.Fetch) -> tuple[Any, str | None]:
    try:
        return fn(), None
    except T.Budget as x:
        return None, "budget: %s" % x
    except T.NotCollected:
        return None, "budget: not collected"
    except HeliusError as x:
        return None, "rpc failure: %s" % str(x)[:120]


def run(F: T.Fetch, R: T.Roles, threads: int = 1, log: Callable[[str], None] = print) -> dict[str, Any]:
    doc = json.load(open(L.SELECTION))
    sel = {c["wallet"]: c for c in doc["selected"]}
    allev: dict[str, list[dict[str, Any]]] = {}
    for e in doc["events"]:
        allev.setdefault(e["wallet"], []).append(e)
    order = sorted(sel)
    random.Random(L.SEED).shuffle(order)
    t0 = time.time()

    def pool(fn: Callable[[Any], Any], items: list[Any]) -> list[Any]:
        if threads <= 1:
            return [fn(x) for x in items]
        with ThreadPoolExecutor(threads) as ex:
            return list(ex.map(fn, items))

    # stage 1: listing and event windows
    def stage1(w: str) -> dict[str, Any]:
        evs = allev[w]
        smp = [e for e in evs if e["sampled"]]
        lst, err = _guard(lambda: T.wallet_listing(F, sel[w], smp), F)
        out: dict[str, Any] = {"wallet": w, "listing_error": err, "events": []}
        if lst is None:
            for e in smp:
                out["events"].append({"wallet": w, "mint": e["mint"], "status": err, "reads": []})
            return out
        out["listing"] = {k: lst[k] for k in ("older_pages", "older_end", "reached_first", "newer_complete")}
        out["listing"]["n_older"], out["listing"]["n_newer"] = len(lst["older"]), len(lst["newer"])
        out["_lst"] = lst
        for e in smp:
            later = [x["receipt"]["bt"] for x in evs if x["receipt"]["slot"] > e["receipt"]["slot"]]
            nxt = min(later) if later else None
            tr, err = _guard(lambda e=e, nxt=nxt: T.event_trace(F, e, sel[w], lst, nxt), F)
            out["events"].append(tr if tr is not None else {"wallet": w, "mint": e["mint"], "status": err, "reads": []})
        return out

    s1 = pool(stage1, order)
    log("stage 1 done: %d wallets, %d calls, %.0f s" % (len(s1), F.state["calls"], time.time() - t0))
    F.save()

    # stage 2: before the first receipt
    def stage2(x: dict[str, Any]) -> dict[str, Any]:
        if "_lst" not in x:
            return {"wallet": x["wallet"], "error": x["listing_error"]}
        pr, err = _guard(lambda: T.prior_trace(F, sel[x["wallet"]], x["_lst"]), F)
        return pr if pr is not None else {"wallet": x["wallet"], "error": err}

    s2 = pool(stage2, s1)
    log("stage 2 done: %d calls, %.0f s" % (F.state["calls"], time.time() - t0))
    F.save()

    # stage 3: branches, breadth-first
    evmeta = {(e["wallet"], e["mint"]): e for e in doc["events"]}
    branches: list[T.Branch] = []
    for x in s1:
        for tr in x["events"]:
            ev = evmeta[(tr["wallet"], tr["mint"])]
            sold = False
            for f in tr.get("reads", []):
                if f["err"]:
                    continue
                if T.is_sale(f, tr["mint"]):
                    sold = True
                for dst, v in f["out"]:
                    if v >= L.MIN_SOL:
                        branches.append(T.Branch(ev, tr["wallet"], dst, v, f["sig"], f["slot"], f["bt"] or 0, sold,
                                                 f["pooled"]))
    for level in range(1, L.MAX_HOPS + 1):
        open_b = [b for b in branches if not b.terminal]
        pool(lambda b: b.step(F, R), open_b)
        log("stage 3 hop %d: %d open branches stepped, %d calls, %.0f s" % (
            level, len(open_b), F.state["calls"], time.time() - t0))
        F.save()
    for b in branches:
        if not b.terminal:
            b.terminal, b.reason = "H6", "UNRESOLVED MULTI-HOP FLOW"
    for x in s1:
        x.pop("_lst", None)
    return {"wallets": s1, "prior": s2, "branches": [b.doc() for b in branches], "calls": dict(F.state),
            "stopped": F.stopped}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=6)
    a = ap.parse_args()
    os.makedirs(L.CACHE, exist_ok=True)
    logp = os.path.join(L.CACHE, "collect.log")

    def log(msg: str) -> None:
        line = "%s %s" % (time.strftime("%H:%M:%S"), msg)
        print(line, flush=True)
        with open(logp, "a") as fh:
            fh.write(line + "\n")

    R = T.Roles(sorted(E.load(), key=lambda z: z["t"]))
    F = T.Fetch(online=True)
    log("start, calls so far %d, cap %d, %d threads" % (F.state["calls"], L.CALL_CAP, a.threads))
    out = run(F, R, a.threads, log)
    F.save()
    log("done: %s calls, %s failures, stopped: %s" % (out["calls"]["calls"], out["calls"]["fails"], out["stopped"]))


if __name__ == "__main__":
    main()
