#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The collection of analysis_plan.md section 3 (scope B), and the same reading offline from the cache: the build
(fn_20_build.py) calls run() with an offline Fetch, so it follows exactly the paths the collection read.

Order: upstream starts (genesis of every primary wallet that has one in reach), the ends of the short-lived
wallets, the samples of the very active ones, then every upstream chain and downstream branch breadth-first.
Hard cap 6,000 calls on top of the 62 of the probe.

Usage (keys through the environment only, never printed):
    HELIUS_API_KEYS=$(cat post_detection_forensics/.helius_keys) FRPC_KEY_RPS=2 \
        python3 funder_network/code/fn_10_collect.py [--threads 6]
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

import fn_trace as N
import ed_lib as L
import ed_trace as T
import em_lib as E

INVENTORY = os.path.join(N.DERIVED, "inventory.json")
EXIT_TABLE = os.path.join(N.ROOT, "exit_destination", "derived", "ed_table.json.gz")


def setup() -> tuple[dict[str, Any], T.Roles, N.Known]:
    inv = json.load(open(INVENTORY))
    pop = inv["population"]
    R = T.Roles(sorted(E.load(), key=lambda z: z["t"]))
    hubs = set()
    for b in json.load(gzip.open(EXIT_TABLE))["branches"]:
        for a, m in b["measured"].items():
            if m.get("hub"):
                hubs.add(a)
    pop_first = {}
    for w, p in pop.items():
        ts = [x["bt"] for x in p["sweeps"]] + [x["bt"] for x in p["fundings"] if x["bt"]]
        pop_first[w] = min(ts)
    return pop, R, N.Known(R, pop_first, hubs)


def classify_sample(f: dict[str, Any], w: str, R: T.Roles) -> str:
    if f["err"]:
        return "failed"
    if f["dtok"]:
        return "trade or token movement"
    if f["out"]:
        d = f["out"][0][0]
        return (
            "sniper funding"
            if d in R.launches and any(d == s["wallet"] for m in R.launches[d] for s in R.rows[m]["snipers"])
            else "other SOL out"
        )
    if f["inn"]:
        return "sweep received" if f["signer"] == w and len(f.get("signers") or []) == 4 else "other SOL in"
    return "other"


def run(F: N.Fetch, threads: int = 1, log: Callable[[str], None] = print) -> dict[str, Any]:
    pop, R, K = setup()
    short = sorted(w for w, p in pop.items() if p["probe"]["end"])
    active = sorted(w for w, p in pop.items() if not p["probe"]["end"])
    rng = random.Random(L.SEED)
    rng.shuffle(short)
    rng.shuffle(active)
    t0 = time.time()

    def pool(fn: Callable[[Any], Any], items: list[Any]) -> list[Any]:
        if threads <= 1:
            return [fn(x) for x in items]
        with ThreadPoolExecutor(threads) as ex:
            return list(ex.map(fn, items))

    prim: dict[str, dict[str, Any]] = {
        w: {
            "wallet": w,
            "kind": "short-lived" if w in short else "very active",
            "labels": pop[w]["labels"],
            "operators": pop[w]["operators"],
        }
        for w in pop
    }
    ups: list[N.Up] = []
    downs: list[N.Down] = []
    reads: dict[str, list[dict[str, Any]]] = {}

    # 1. upstream starts
    def up_start(w: str) -> tuple[str, Any, Any]:
        sw = sorted(pop[w]["sweeps"], key=lambda x: x["slot"])
        if w in short:

            def g() -> Any:
                page = F.page(w, before=sw[-1]["sig"])
                if not page:
                    return {"status": "empty"}
                o = page[-1]
                src, got = N.funder_of(F.tx(o["sig"]), w)
                return {
                    "status": "read",
                    "n_before": len(page),
                    "genesis_sig": o["sig"],
                    "genesis_bt": o["bt"],
                    "genesis_slot": o["slot"],
                    "funder": src,
                    "received": got,
                }
        else:

            def g() -> Any:
                return N.upstream_step(F, w, sw[0]["sig"])

        r, err = N.guard(g)
        return w, r, err

    for w, r, err in pool(up_start, short + active):
        prim[w]["upstream_start"] = r if r is not None else {"status": err}
        if r and r.get("status") == "read":
            ups.append(
                N.Up(w, r.get("funder"), r["genesis_sig"], r["genesis_bt"] or 0, r["genesis_slot"], r["received"])
            )
    log("upstream starts: %d chains, %d calls, %.0f s" % (len(ups), F.state["calls"], time.time() - t0))

    # 2. ends of the short-lived wallets
    def end(w: str) -> tuple[str, Any, Any]:
        last = max(pop[w]["sweeps"], key=lambda x: x["slot"])

        def g() -> Any:
            chain: list[dict[str, Any]] = []
            b = None
            pre = []
            for _ in range(N.END_PAGES):
                p = F.page(w, before=b)
                chain += p
                pre = [e for e in chain if (e["bt"] or 0) < N.TEST_START]
                if pre or len(p) < 1000:
                    break
                b = p[-1]["sig"]
            if not pre:
                return {"status": "active beyond the TEST boundary", "n_listed": len(chain)}
            cand = [e for e in pre if e["slot"] > last["slot"] and not e["err"]][: N.END_TX]
            fl = [T.txflow(F.tx(e["sig"]), w) for e in reversed(cand)]
            return {
                "status": "read",
                "n_listed": len(chain),
                "n_after_last_sweep": sum(1 for e in pre if e["slot"] > last["slot"]),
                "reads": fl,
                "last_pre_test_bt": pre[0]["bt"],
                "after_test": len(chain) - len(pre),
            }

        r, err = N.guard(g)
        return w, r, err

    for w, r, err in pool(end, short):
        prim[w]["end"] = {k: v for k, v in (r or {"status": err}).items() if k != "reads"}
        if r and r.get("reads"):
            reads.setdefault(w, []).extend(dict(f, origin="end") for f in r["reads"])
            for f in r["reads"]:
                for d, v in f["out"]:
                    if v >= N.MIN_SOL and not f["err"]:
                        downs.append(N.Down(w, "end", d, v, f["sig"], f["slot"], f["bt"] or 0))
    log("short-lived ends: %d calls, %.0f s" % (F.state["calls"], time.time() - t0))

    # 3. samples of the very active wallets
    def sample(w: str) -> tuple[str, Any, Any]:
        sw = sorted(pop[w]["sweeps"], key=lambda x: x["slot"])
        anchors = []
        for x in (sw[0], sw[len(sw) // 2], sw[-1]):
            if x["sig"] not in [a["sig"] for a in anchors]:
                anchors.append(x)

        def g() -> Any:
            out = []
            for a in anchors:
                p = F.page(w, before=a["sig"], limit=N.SAMPLE_TX)
                for e in reversed(p):
                    if e["err"] or (e["bt"] or 0) >= N.TEST_START:
                        continue
                    f = T.txflow(F.tx(e["sig"]), w)
                    f["anchor"] = a["sig"]
                    f["class"] = classify_sample(f, w, R)
                    out.append(f)
            return {"status": "read", "anchors": len(anchors), "reads": out}

        r, err = N.guard(g)
        return w, r, err

    for w, r, err in pool(sample, active):
        prim[w]["sample"] = {
            "status": (r or {}).get("status", err),
            "anchors": (r or {}).get("anchors"),
            "n": len((r or {}).get("reads", [])),
        }
        if r and r.get("reads"):
            reads.setdefault(w, []).extend(dict(f, origin="sample") for f in r["reads"])
            for f in r["reads"]:
                for d, v in f["out"]:
                    if v >= N.MIN_SOL and not f["err"]:
                        downs.append(N.Down(w, "sample", d, v, f["sig"], f["slot"], f["bt"] or 0))
    log("very active samples: %d calls, %.0f s" % (F.state["calls"], time.time() - t0))
    F.save()

    # 4. chains and branches, breadth-first
    for level in range(1, N.MAX_HOPS + 1):
        open_items = [x for x in ups + downs if not x.terminal]
        pool(lambda x: x.step(F, K), open_items)
        log("hop %d: %d open stepped, %d calls, %.0f s" % (level, len(open_items), F.state["calls"], time.time() - t0))
        F.save()
    for x in ups + downs:
        if not x.terminal:
            x.terminal = "UNRESOLVED >5 HOPS"
    return {
        "primary": prim,
        "ups": [u.doc() for u in ups],
        "downs": [d.doc() for d in downs],
        "reads": reads,
        "calls": dict(F.state),
        "stopped": F.stopped,
    }


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

    F = N.Fetch(online=True)
    log("start, calls so far %d, cap %d, %d threads" % (F.state["calls"], L.CALL_CAP, a.threads))
    out = run(F, a.threads, log)
    F.save()
    log("done: %s calls, %s failures, stopped: %s" % (out["calls"]["calls"], out["calls"]["fails"], out["stopped"]))


if __name__ == "__main__":
    main()
