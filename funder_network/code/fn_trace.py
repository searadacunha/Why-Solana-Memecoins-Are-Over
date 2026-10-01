#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fn_trace.py -- the reading rules of analysis_plan.md section 3, shared by the collection (online) and the build
(offline, from the cache only), so both follow the same paths. Built on exit_destination's ed_trace (Fetch,
txflow, Roles) with this study's cache, the TEST boundary and a 7-day hop window.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "exit_destination", "code"))
import ed_lib  # noqa: E402

EXIT_CACHE = ed_lib.CACHE
ed_lib.CACHE = os.path.join(STUDY, "data", "cache")
PROBE_CALLS = 62
ed_lib.CALL_CAP = 6000 + PROBE_CALLS
import ed_trace as T  # noqa: E402
from rpc_client import HeliusError  # noqa: E402

TEST_START = 1790680980  # 2026-09-29 11:23 UTC
HOP_WINDOW = 7 * 86400
UP_PAGES = 3
HUB_N = 3000
MAX_HOPS = 5
MIN_SOL = 0.1
END_PAGES = 3
END_TX = 10
SAMPLE_TX = 10
HOP_TX = 5
NotCollected, Budget = T.NotCollected, T.Budget
DERIVED = os.path.join(STUDY, "derived")
TABLES = os.path.join(STUDY, "tables")


class Fetch(T.Fetch):
    """This study's cache first, then the exit study's cache read-only, then the network."""

    def page(
        self, addr: str, before: Optional[str] = None, until: Optional[str] = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        if limit == 1000:
            for base in (ed_lib.CACHE, EXIT_CACHE):
                key = hashlib.sha1(("%s|%s|%s" % (addr, before, until)).encode()).hexdigest()[:16]
                p = os.path.join(base, "sigs", addr[:2], "%s_%s.json" % (addr, key))
                if os.path.exists(p):
                    return json.load(open(p))["page"]
            return super().page(addr, before, until)
        key = hashlib.sha1(("%s|%s|%s|%d" % (addr, before, until, limit)).encode()).hexdigest()[:16]
        path = os.path.join(ed_lib.CACHE, "sigs", addr[:2], "%s_%s.json" % (addr, key))
        if os.path.exists(path):
            return json.load(open(path))["page"]
        p: dict[str, Any] = {"limit": limit}
        if before:
            p["before"] = before
        if until:
            p["until"] = until
        r = self._call("getSignaturesForAddress", [addr, p])
        out = [
            {"sig": e["signature"], "slot": e["slot"], "bt": e.get("blockTime"), "err": e.get("err") is not None}
            for e in r
        ]
        T._atomic(
            path, json.dumps({"addr": addr, "before": before, "until": until, "limit": limit, "page": out}).encode()
        )
        return out

    def tx(self, sig: str, mint: Optional[str] = None) -> dict[str, Any]:
        p = os.path.join(EXIT_CACHE, "tx", sig[:2], sig + ".json.gz")
        if not os.path.exists(os.path.join(ed_lib.CACHE, "tx", sig[:2], sig + ".json.gz")) and os.path.exists(p):
            return json.load(gzip.open(p))
        return super().tx(sig, mint)


def guard(fn: Any) -> tuple[Any, Optional[str]]:
    try:
        return fn(), None
    except Budget as x:
        return None, "budget: %s" % x
    except NotCollected:
        return None, "budget: not collected"
    except HeliusError as x:
        return None, "rpc failure: %s" % str(x)[:100]


def funder_of(t: dict[str, Any], w: str) -> tuple[Optional[str], float]:
    """The account with the largest SOL loss in a transaction where w gains SOL (fee added back)."""
    meta = t["meta"]
    keys = [k["pubkey"] for k in t["transaction"]["message"]["accountKeys"]]
    fee = meta.get("fee") or 0
    d = {
        k: (meta["postBalances"][i] - meta["preBalances"][i] + (fee if i == 0 else 0)) / 1e9 for i, k in enumerate(keys)
    }
    got = d.get(w, 0.0)
    losers = {k: -v for k, v in d.items() if k != w and v < 0}
    if not losers:
        return None, got
    return max(losers, key=lambda k: (losers[k], k)), got


def history_before(F: Fetch, addr: str, before: str) -> tuple[list[dict[str, Any]], bool]:
    """Signatures strictly before `before`, up to UP_PAGES pages: (entries, history_end)."""
    chain: list[dict[str, Any]] = []
    b = before
    for _ in range(UP_PAGES):
        p = F.page(addr, before=b)
        chain += p
        if len(p) < 1000:
            return chain, True
        b = p[-1]["sig"]
    return chain, False


def upstream_step(F: Fetch, addr: str, before: str) -> dict[str, Any]:
    """Who funded `addr`, read strictly before the signature `before` (section 3.1)."""
    chain, end = history_before(F, addr, before)
    if not end:
        return {"status": "hub", "n_before": len(chain)}
    if not chain:
        return {"status": "empty"}
    g = chain[-1]
    t = F.tx(g["sig"])
    src, got = funder_of(t, addr)
    return {
        "status": "read",
        "n_before": len(chain),
        "genesis_sig": g["sig"],
        "genesis_bt": g["bt"],
        "genesis_slot": g["slot"],
        "funder": src,
        "received": got,
    }


def read_node(F: Fetch, addr: str, inflow: dict[str, Any]) -> dict[str, Any]:
    """A downstream wallet at one inflow: newest-first pages until the inflow (at most 3), its hub status, its
    first HOP_TX successful transactions within 7 days after the inflow and before TEST start."""
    chain: list[dict[str, Any]] = []
    b = None
    found = None
    end = False
    for _ in range(3):
        p = F.page(addr, before=b)
        chain += p
        end = len(p) < 1000
        sigs = [e["sig"] for e in chain]
        if inflow["sig"] in sigs:
            found = sigs.index(inflow["sig"])
            break
        if end or (p and p[-1]["slot"] < inflow["slot"]):
            break
        b = p[-1]["sig"]
    if found is None:
        if chain and chain[-1]["slot"] <= inflow["slot"]:
            found = next(i for i, e in enumerate(chain) if e["slot"] <= inflow["slot"]) - 1
        else:
            return {"status": "too active"}
    n_before = len(chain) - found - 1
    hp = 0
    while not end and n_before < HUB_N and hp < 3:
        p = F.page(addr, before=chain[-1]["sig"])
        hp += 1
        chain += p
        n_before += len(p)
        end = len(p) < 1000
    if n_before >= HUB_N:
        return {"status": "hub", "n_before": n_before}
    lim = min(inflow["bt"] + HOP_WINDOW, TEST_START)
    after = [e for e in reversed(chain[: max(found, 0)]) if (e["bt"] or 0) < lim and not e["err"]]
    reads = [T.txflow(F.tx(e["sig"]), addr) for e in after[:HOP_TX]]
    outs = [(d, v, f["sig"], f["slot"], f["bt"]) for f in reads for d, v in f["out"] if v >= MIN_SOL]
    return {"status": "read", "n_before": n_before, "n_after": len(after), "reads": reads, "outs": outs}


class Known:
    """Terminal test of section 4 at collection time: a hub, a frozen role visible by then, or a population
    wallet visible by then."""

    def __init__(self, R: T.Roles, pop_first: dict[str, float], hubs: set[str]) -> None:
        self.R, self.pop_first, self.hubs = R, pop_first, hubs

    def terminal(self, addr: str, bt: float) -> Optional[str]:
        if self.R.hub.get(addr) or addr in self.hubs:
            return "hub"
        if self.pop_first.get(addr, 1e18) <= bt:
            return "population"
        if self.R.first.get(addr, 1e18) <= bt:
            return "known"
        return None


class Up:
    """An upstream chain from a primary wallet (section 3.1/3.3)."""

    def __init__(self, primary: str, funder: Optional[str], sig: str, bt: float, slot: int, sol: float) -> None:
        self.primary = primary
        self.path = [{"wallet": primary}, {"wallet": funder, "sig": sig, "bt": bt, "slot": slot, "sol": sol}]
        self.terminal: Optional[str] = None if funder else "unresolved: no funder in the genesis transaction"
        self.measured: dict[str, Any] = {}

    def step(self, F: Fetch, K: Known) -> None:
        if self.terminal:
            return
        cur = self.path[-1]
        k = K.terminal(cur["wallet"], cur["bt"] or 0)
        if k:
            self.terminal = k
            return
        if cur["wallet"] in {p["wallet"] for p in self.path[:-1]}:
            self.terminal = "circular flow"
            return
        if len(self.path) - 1 >= MAX_HOPS:
            self.terminal = "UNRESOLVED >5 HOPS"
            return
        r, err = guard(lambda: upstream_step(F, cur["wallet"], cur["sig"]))
        if r is None:
            self.terminal = "unresolved: " + str(err)
            return
        self.measured[cur["wallet"]] = {k2: r.get(k2) for k2 in ("status", "n_before")}
        if r["status"] == "hub":
            self.terminal = "hub measured"
            return
        if r["status"] == "empty" or not r.get("funder"):
            self.terminal = "unresolved: no funder found"
            return
        self.path.append(
            {
                "wallet": r["funder"],
                "sig": r["genesis_sig"],
                "bt": r["genesis_bt"],
                "slot": r["genesis_slot"],
                "sol": r["received"],
            }
        )

    def doc(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "direction": "up",
            "path": self.path,
            "terminal": self.terminal,
            "measured": self.measured,
        }


class Down:
    """A downstream branch from a primary wallet's outgoing movement (section 3, downstream branches)."""

    def __init__(self, primary: str, origin: str, dst: str, sol: float, sig: str, slot: int, bt: float) -> None:
        self.primary, self.origin = primary, origin
        self.path = [{"wallet": primary}, {"wallet": dst, "sol": sol, "sig": sig, "slot": slot, "bt": bt}]
        self.terminal: Optional[str] = None
        self.side: list[dict[str, Any]] = []
        self.measured: dict[str, Any] = {}

    def step(self, F: Fetch, K: Known) -> None:
        if self.terminal:
            return
        cur = self.path[-1]
        k = K.terminal(cur["wallet"], cur["bt"] or 0)
        if k:
            self.terminal = k
            return
        if cur["wallet"] in {p["wallet"] for p in self.path[:-1]}:
            self.terminal = "circular flow"
            return
        if len(self.path) - 1 >= MAX_HOPS:
            self.terminal = "UNRESOLVED >5 HOPS"
            return
        r, err = guard(lambda: read_node(F, cur["wallet"], cur))
        if r is None:
            self.terminal = "unresolved: " + str(err)
            return
        self.measured[cur["wallet"]] = {k2: r.get(k2) for k2 in ("status", "n_before", "n_after")}
        if r["status"] == "too active":
            self.terminal = "unresolved: too active"
            return
        if r["status"] == "hub":
            self.terminal = "hub measured"
            return
        if not r["outs"]:
            self.terminal = "retained"
            return
        best = max(r["outs"], key=lambda o: (o[1], -(o[4] or 0)))
        for o in r["outs"]:
            if o is not best:
                self.side.append({"hop": len(self.path), "wallet": o[0], "sol": o[1], "sig": o[2], "bt": o[4]})
        self.path.append({"wallet": best[0], "sol": best[1], "sig": best[2], "slot": best[3], "bt": best[4]})

    def doc(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "direction": "down",
            "origin": self.origin,
            "path": self.path,
            "terminal": self.terminal,
            "side": self.side,
            "measured": self.measured,
        }
