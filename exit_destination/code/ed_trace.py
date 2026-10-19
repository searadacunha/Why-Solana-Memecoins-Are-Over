#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ed_trace.py -- the reading rules of analysis_plan.md (sections 3 to 5), shared by the collection (online, through
Helius) and the build (offline, from the cache only), so that both follow the same paths.

- Fetch: signature pages and transactions, cached on disk; online it counts every call against the hard cap and
  raises on any failure; offline a missing item raises NotCollected.
- txflow: one transaction seen from one wallet, from balance changes and parsed System transfers only.
- Roles: who is known in the frozen tables, from when (a launch's roles are visible from its creation), and
  which addresses are hubs.
- wallet_listing, event_trace, prior_trace, read_node, Branch.step: the reading of an exit wallet, of an event
  window, of the history before the first receipt, and of each downstream wallet.
"""

from __future__ import annotations

import glob
import gzip
import hashlib
import json
import os
import sys
import threading
from collections import defaultdict
from typing import Any, Optional

import ed_lib as L
import em_lib as E

sys.path.insert(0, os.path.join(L.ROOT, "post_detection_forensics", "code"))
import fparse
import frpc
from rpc_client import HeliusError

TX_VERSION = 1  # Solana transaction version 1 exists on mainnet since mid-September 2026
WSOL = fparse.WSOL
VENUES = {fparse.PUMP, fparse.PUMPSWAP} | set(fparse.ROUTERS)
JITO = fparse.JITO_TIPS
ONCHAIN = os.path.join(L.ROOT, "post_detection_forensics", "data", "onchain_cache")
LAMPORTS = 1e9


class NotCollected(Exception):
    pass


class Budget(Exception):
    pass


def _atomic(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, threading.get_ident())
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


class Fetch:
    def __init__(self, online: bool) -> None:
        self.online = online
        self.lock = threading.Lock()
        self.state_path = os.path.join(L.CACHE, "budget.json")
        self.state = json.load(open(self.state_path)) if os.path.exists(self.state_path) else {"calls": 0, "fails": 0}
        self._win: dict[str, dict[str, Any]] = {}
        self.stopped: Optional[str] = None

    def save(self) -> None:
        if not self.online:
            return
        with self.lock:
            _atomic(self.state_path, json.dumps(self.state).encode())

    def _call(self, method: str, params: list[Any]) -> Any:
        if not self.online:
            raise NotCollected(method)
        with self.lock:
            if self.stopped:
                raise Budget(self.stopped)
            if self.state["calls"] >= L.CALL_CAP:
                self.stopped = "call cap %d reached" % L.CALL_CAP
                raise Budget(self.stopped)
            if self.state["calls"] >= 500 and self.state["fails"] > L.MAX_FAIL_SHARE * self.state["calls"]:
                self.stopped = "failure share above %.0f %%" % (100 * L.MAX_FAIL_SHARE)
                raise Budget(self.stopped)
            self.state["calls"] += 1
            if self.state["calls"] % 200 == 0:
                _atomic(self.state_path, json.dumps(self.state).encode())
        try:
            r = frpc.rpc(method, params)
        except HeliusError:
            with self.lock:
                self.state["fails"] += 1
            raise
        if r is None:
            with self.lock:
                self.state["fails"] += 1
            raise HeliusError("%s returned null" % method)
        return r

    def page(self, addr: str, before: Optional[str] = None, until: Optional[str] = None) -> list[dict[str, Any]]:
        """One page of up to 1,000 signatures, newest first: {sig, slot, bt, err}."""
        key = hashlib.sha1(("%s|%s|%s" % (addr, before, until)).encode()).hexdigest()[:16]
        path = os.path.join(L.CACHE, "sigs", addr[:2], "%s_%s.json" % (addr, key))
        if os.path.exists(path):
            return json.load(open(path))["page"]
        p: dict[str, Any] = {"limit": 1000}
        if before:
            p["before"] = before
        if until:
            p["until"] = until
        r = self._call("getSignaturesForAddress", [addr, p])
        out = [
            {"sig": e["signature"], "slot": e["slot"], "bt": e.get("blockTime"), "err": e.get("err") is not None}
            for e in r
        ]
        _atomic(path, json.dumps({"addr": addr, "before": before, "until": until, "page": out}).encode())
        return out

    def _from_window(self, sig: str, mint: Optional[str]) -> Optional[dict[str, Any]]:
        if not mint:
            return None
        if mint not in self._win:
            p = os.path.join(ONCHAIN, "win", mint + ".json.gz")
            self._win[mint] = json.load(gzip.open(p))["txs"] if os.path.exists(p) else {}
        return self._win[mint].get(sig)

    def tx(self, sig: str, mint: Optional[str] = None) -> dict[str, Any]:
        path = os.path.join(L.CACHE, "tx", sig[:2], sig + ".json.gz")
        if os.path.exists(path):
            return json.load(gzip.open(path))
        t = self._from_window(sig, mint)
        if t is not None:
            return t
        opts = {"encoding": "jsonParsed", "maxSupportedTransactionVersion": TX_VERSION}
        t = self._call("getTransaction", [sig, opts])
        _atomic(path, gzip.compress(json.dumps(t).encode(), mtime=0))
        return t


# ------------------------------------------------------------------ parsing --- #
def _instructions(t: dict[str, Any]) -> list[dict[str, Any]]:
    out = list(t["transaction"]["message"].get("instructions") or [])
    for g in t["meta"].get("innerInstructions") or []:
        out += g.get("instructions") or []
    return out


def txflow(t: dict[str, Any], w: str) -> dict[str, Any]:
    """One transaction from the point of view of wallet w (analysis_plan.md section 4)."""
    meta = t["meta"]
    acc = t["transaction"]["message"]["accountKeys"]
    keys = [k["pubkey"] for k in acc]
    signer = keys[0]
    fee = meta.get("fee") or 0
    rec: dict[str, Any] = {
        "sig": t["transaction"]["signatures"][0],
        "slot": t["slot"],
        "bt": t.get("blockTime"),
        "idx": t.get("transactionIndex"),
        "signer": signer,
        "err": meta.get("err") is not None,
        "signers": [k["pubkey"] for k in acc if k.get("signer")],
    }
    tok_accts = set()
    pre: dict[tuple[str, str], float] = defaultdict(float)
    post: dict[tuple[str, str], float] = defaultdict(float)
    for side, acc in (("preTokenBalances", pre), ("postTokenBalances", post)):
        for b in meta.get(side) or []:
            tok_accts.add(keys[b["accountIndex"]])
            acc[(b.get("owner") or "", b["mint"])] += float(b["uiTokenAmount"].get("uiAmount") or 0.0)
    delta = {k: post.get(k, 0.0) - pre.get(k, 0.0) for k in set(pre) | set(post)}
    lam = {k: meta["postBalances"][i] - meta["preBalances"][i] for i, k in enumerate(keys)}
    rec["dsol"] = (lam.get(w, 0) + (fee if signer == w else 0)) / LAMPORTS
    rec["dws"] = delta.get((w, WSOL), 0.0)
    rec["dtok"] = {m: round(v, 6) for (o, m), v in delta.items() if o == w and m != WSOL and abs(v) > 1e-9}
    rec["post_tok"] = {m: v for (o, m), v in post.items() if o == w and m != WSOL}
    rec["tok_to"] = {}
    for m, v in rec["dtok"].items():
        if v < 0:
            rec["tok_to"][m] = {o: round(d, 6) for (o, mm), d in delta.items() if mm == m and o != w and d > 1e-9}
    progs = {ix.get("programId") for ix in _instructions(t)}
    rec["venue"] = bool(progs & VENUES)
    venue_accts = set()
    for ix in _instructions(t):
        if ix.get("programId") in VENUES:
            venue_accts |= set(ix.get("accounts") or [])
    # Section 4 of the plan, by net balance changes: a SOL transfer out is a fall of the wallet's SOL (native plus
    # wrapped) in a transaction where its other token balances do not change; the recipient is the non-token
    # account with the largest lamport gain (the fee added back for the fee payer, Jito tip accounts excluded), or,
    # when the SOL stays wrapped, the owner with the largest wrapped-SOL gain. A first version took the destination
    # of the first System transfer instead: in a one-transaction sweep through a fresh address and wrapped SOL that
    # address is not where the SOL ends. Transfers made inside a trade are kept apart (trade_out), not followed.
    gain = {
        k: (v + (fee if k == signer else 0)) / LAMPORTS
        for k, v in lam.items()
        if k != w and k not in tok_accts and k not in JITO
    }
    loss = -(rec["dsol"] + rec["dws"])
    rec["out"], rec["inn"], rec["trade_out"] = [], [], []
    if not rec["dtok"] and loss >= 0.01:
        best = max((k for k in gain if gain[k] > 0), key=lambda k: (gain[k], k), default=None)
        if best is None:
            ws = {o: d for (o, m), d in delta.items() if m == WSOL and o != w and d > 1e-9}
            best = max(ws, key=lambda k: (ws[k], k), default=None)
            rec["out_gain"] = ws.get(best) if best else None
        else:
            rec["out_gain"] = gain[best]
        if best:
            rec["out"] = [[best, loss]]
    elif not rec["dtok"] and loss <= -0.01:
        src = min((k for k in gain if gain[k] < 0), key=lambda k: (gain[k], k), default=None)
        if src:
            rec["inn"] = [[src, -loss]]
    if rec["dtok"]:
        for ix in _instructions(t):
            p = ix.get("parsed") if ix.get("program") == "system" else None
            if not isinstance(p, dict) or p.get("type") not in ("transfer", "transferWithSeed"):
                continue
            info = p.get("info") or {}
            dst, lp = info.get("destination"), int(info.get("lamports") or 0)
            if info.get("source") == w and dst not in tok_accts and dst not in JITO and dst not in venue_accts:
                rec["trade_out"].append([dst, lp / LAMPORTS])
    return rec


def is_sale(f: dict[str, Any], mint: str) -> bool:
    return f["dtok"].get(mint, 0.0) < 0 and (f["venue"] or f["dsol"] + f["dws"] > 0)


def is_pump(m: str) -> bool:
    return m.endswith("pump")


# -------------------------------------------------------------------- roles --- #
class Roles:
    """Known wallets of the frozen tables with the time each role becomes visible, clusters and hubs."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        E.require_hops(rows)
        self.cl = E.clusters(rows)
        self.first: dict[str, float] = {}
        self.launches: dict[str, set[str]] = defaultdict(set)
        self.cluster_net: dict[str, dict[str, float]] = defaultdict(dict)
        self.dep_net: dict[str, dict[str, float]] = defaultdict(dict)
        self.deployers: dict[str, float] = {}
        self.hub: dict[str, Optional[bool]] = {}
        self.rows = {r["mint"]: r for r in rows}

        def see(addr: Optional[str], t: float, mint: str, net: Optional[dict[str, float]] = None) -> None:
            if not addr:
                return
            self.first[addr] = min(self.first.get(addr, t), t)
            self.launches[addr].add(mint)
            if net is not None:
                net[addr] = min(net.get(addr, t), t)

        for r in rows:
            t, m = r["t_create"], r["mint"]
            c = self.cl[m]
            cn, dn = self.cluster_net[c], self.dep_net[c]
            cr = r["creator"]
            dep = cr.get("wallet")
            see(dep, t, m, cn)
            see(dep, t, m, dn)
            if dep:
                self.deployers[dep] = min(self.deployers.get(dep, t), t)
            for k in ("gen_funder", "last_funder"):
                f, h = cr.get(k), cr.get(k + "_hub")
                self._hub(f, h)
                see(f, t, m, cn if h is not True else None)
                if h is not True:
                    see(f, t, m, dn)
            for s in r["snipers"]:
                see(s["wallet"], t, m, cn)
                for k in ("gen_funder", "last_funder"):
                    f, h = s.get(k), s.get(k + "_hub")
                    self._hub(f, h)
                    see(f, t, m, cn if h is not True else None)
                    if f and h is not True:
                        src = (E.hop(f).get("funding") or {}).get("funder")
                        if src and not E.hop(f).get("hub_before_cursor"):
                            see(src, t, m, cn)
                src = s.get("source")
                if isinstance(src, str):
                    see(src, t, m, cn)
                for x in s["exits_full"]:
                    if x["kind"] == "transfer":
                        for o in x["recipients"]:
                            see(o, t, m, cn)
        # hub status measured before the cursor only: the table fields and genesis_hop. The genesis/ cache counts
        # an address's whole history up to its collection date (later than the launches), so it is not used.
        for r in rows:
            for s in r["snipers"]:
                if s.get("n_prior") is not None and s["n_prior"] < 1000:
                    self._hub(s["wallet"], False)
        for p in glob.glob(os.path.join(ONCHAIN, "genesis_hop", "*.json")):
            d = json.load(open(p))
            if "hub_before_cursor" in d:
                self._hub(d["address"], d["hub_before_cursor"])

    def _hub(self, addr: Optional[str], h: Optional[bool]) -> None:
        if addr and h is not None:
            self.hub[addr] = bool(self.hub.get(addr)) or bool(h)

    def classify(self, addr: str, bt: float, ev: dict[str, Any], measured_hub: Optional[bool] = None) -> Optional[str]:
        """H1..H5 for a known or hub address at time bt for event ev; None for an unknown address."""
        if self.hub.get(addr) or measured_hub:
            return "H5"
        if addr in ev["funders"]:
            return "H1"
        c = ev["em_cluster"]
        if self.dep_net[c].get(addr, 1e18) <= bt:
            return "H3"
        if self.cluster_net[c].get(addr, 1e18) <= bt:
            return "H2"
        if self.first.get(addr, 1e18) <= bt:
            return "H4"
        return None

    def proceeds_cat(self, addr: str, bt: float, ev: dict[str, Any]) -> str:
        """Section 5 categories B-F for a direct destination of the exit wallet; H when unknown."""
        if self.hub.get(addr):
            return "F hub"
        if addr in ev["snipers"]:
            return "B sniper"
        if addr in ev["funders"]:
            return "C funder"
        if self.deployers.get(addr, 1e18) <= bt:
            return "E deployer"
        if self.first.get(addr, 1e18) <= bt:
            return "D known wallet"
        return "H unknown"

    def known(self, addr: str, bt: float) -> bool:
        return self.first.get(addr, 1e18) <= bt


# ---------------------------------------------------------------- readings --- #
def wallet_listing(F: Fetch, sel: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    """Stage A then B of section 3.1. Returns the listing (newest first) and its coverage."""
    w, cur, first = sel["wallet"], sel["cursor"], sel["first_receipt"]
    older: list[dict[str, Any]] = []
    before = cur["sig"]
    pages, reached_first, end = 0, False, False
    while pages < L.MAX_SIG_PAGES:
        p = F.page(w, before=before)
        pages += 1
        older += p
        sigs = [e["sig"] for e in older]
        if first["sig"] in sigs:
            n_before = len(older) - sigs.index(first["sig"]) - 1
        else:
            n_before = sum(1 for e in older if e["slot"] < first["slot"])
        reached_first = n_before >= 1 or first["sig"] in sigs
        if len(p) < 1000:
            end = True
            break
        if n_before >= L.PRIOR_TX:
            break
        before = p[-1]["sig"]
    out = {
        "wallet": w,
        "older": older,
        "older_pages": pages,
        "older_end": end,
        "reached_first": reached_first,
        "newer": [],
        "newer_complete": None,
    }
    if any(e["receipt"]["bt"] + L.WINDOW_S > cur["bt"] for e in events):
        b = None
        newer: list[dict[str, Any]] = []
        for _ in range(L.NEWEST_PAGES):
            p = F.page(w, before=b, until=cur["sig"])
            newer += p
            if len(p) < 1000:
                out["newer_complete"] = True
                break
            b = p[-1]["sig"]
        else:
            out["newer_complete"] = False
        out["newer"] = newer
    return out


def _combined(lst: dict[str, Any], cur: dict[str, Any]) -> list[dict[str, Any]]:
    """Newest first: the pages after the cursor (when complete), the cursor itself, the pages before it."""
    newer = lst["newer"] if lst["newer_complete"] else []
    mid = {"sig": cur["sig"], "slot": cur["slot"], "bt": cur["bt"], "err": False, "cursor": True}
    return newer + [mid] + lst["older"]


def event_trace(
    F: Fetch, ev: dict[str, Any], sel: dict[str, Any], lst: dict[str, Any], next_bt: Optional[float]
) -> dict[str, Any]:
    """Section 3.3: the event window read in time order with the early stop."""
    w, m, rc = ev["wallet"], ev["mint"], ev["receipt"]
    comb = _combined(lst, sel["cursor"])
    sigs = [e["sig"] for e in comb]
    out: dict[str, Any] = {"wallet": w, "mint": m, "receipt_listed": rc["sig"] in sigs}
    if rc["sig"] in sigs:
        after = comb[: sigs.index(rc["sig"])]
    else:
        after = [e for e in comb if e["slot"] > rc["slot"]]
    end_bt = rc["bt"] + L.WINDOW_S
    truncated = bool(lst["newer_complete"] is not True and end_bt > sel["cursor"]["bt"])
    oldest = lst["older"][-1]["slot"] if lst["older"] else sel["cursor"]["slot"]
    if not out["receipt_listed"] and not lst["older_end"] and oldest > rc["slot"]:
        out.update({"status": "history not reached", "reads": []})
        return out
    win = [e for e in reversed(after) if (e["bt"] or 0) < end_bt]
    if truncated:
        win = [e for e in win if (e["bt"] or 0) < sel["cursor"]["bt"]]
    ok = [e for e in win if not e["err"]]
    out.update({"n_window": len(win), "n_window_ok": len(ok), "truncated": truncated})
    held = max_held = float(ev["tokens"])
    sold_seen = False
    out_after_sale = False
    reads: list[dict[str, Any]] = []
    status = "window end"
    for e in ok:
        if len(reads) >= L.MAX_TX_EVENT:
            status = "cap"
            break
        f = txflow(F.tx(e["sig"], m), w)
        f["pooled"] = next_bt is not None and (f["bt"] or 0) >= next_bt
        reads.append(f)
        if m in f["post_tok"] or m in f["dtok"]:
            held = f["post_tok"].get(m, 0.0)
            max_held = max(max_held, held)
        if is_sale(f, m):
            sold_seen, out_after_sale = True, False
        elif sold_seen and any(v >= L.MIN_SOL for _, v in f["out"]):
            out_after_sale = True
        if held <= 0.01 * max_held and (out_after_sale or not sold_seen):
            status = "complete"
            break
    out.update({"status": status, "reads": reads, "max_held": max_held, "held_end": held})
    return out


def prior_trace(F: Fetch, sel: dict[str, Any], lst: dict[str, Any]) -> dict[str, Any]:
    """Section 3.2: the genesis funding and the transactions just before the first corpus receipt."""
    w, first = sel["wallet"], sel["first_receipt"]
    older = lst["older"]
    sigs = [e["sig"] for e in older]
    if first["sig"] in sigs:
        before = older[sigs.index(first["sig"]) + 1 :]
    else:
        before = [e for e in older if e["slot"] < first["slot"]]
    reads = [txflow(F.tx(e["sig"]), w) for e in [x for x in before if not x["err"]][: L.PRIOR_TX]]
    gen_p = os.path.join(ONCHAIN, "genesis", w + ".json")
    gen: dict[str, Any]
    if os.path.exists(gen_p):
        d = json.load(open(gen_p))
        gen = {
            "source": "cache",
            "hub": d.get("hub"),
            "funder": (d.get("funding") or {}).get("funder"),
            "bt": (d.get("funding") or {}).get("bt"),
            "received": (d.get("funding") or {}).get("received"),
        }
    else:
        chain = list(older)
        end = lst["older_end"]
        b = chain[-1]["sig"] if chain else sel["cursor"]["sig"]
        n_pages = 0
        while not end and n_pages < L.HUB_PAGES:
            p = F.page(w, before=b)
            n_pages += 1
            chain += p
            if len(p) < 1000:
                end = True
                break
            b = p[-1]["sig"]
        if not end:
            gen = {"source": "read", "hub": True, "funder": None, "n_seen": len(chain)}
        elif not chain:
            gen = {"source": "read", "hub": False, "funder": None, "empty": True}
        else:
            g = txflow(F.tx(chain[-1]["sig"]), w)
            src = max(g["inn"], key=lambda x: x[1])[0] if g["inn"] else None
            gen = {"source": "read", "hub": False, "funder": src, "bt": g["bt"], "received": g["dsol"]}
    return {"wallet": w, "reads": reads, "genesis": gen}


def read_node(F: Fetch, addr: str, inflow: dict[str, Any]) -> dict[str, Any]:
    """Section 3.4: an unknown downstream wallet at one inflow. Its signatures newest first until the inflow
    (at most HOP_PAGES pages), then back until HUB_N earlier ones or its first (at most HUB_PAGES more)."""
    chain: list[dict[str, Any]] = []
    b = None
    found = None
    end = False
    pages = 0
    while pages < L.HOP_PAGES:
        p = F.page(addr, before=b)
        pages += 1
        chain += p
        end = len(p) < 1000
        sigs = [e["sig"] for e in chain]
        if inflow["sig"] in sigs:
            found = sigs.index(inflow["sig"])
            break
        if end or (p and p[-1]["slot"] < inflow["slot"]):
            break
        b = p[-1]["sig"]
    listed = found is not None
    if found is None:
        if chain and chain[-1]["slot"] <= inflow["slot"]:
            found = next(i for i, e in enumerate(chain) if e["slot"] <= inflow["slot"]) - 1
        else:
            return {"status": "too active", "pages": pages}
    n_before = len(chain) - found - 1
    hub_pages = 0
    while not end and n_before < L.HUB_N and hub_pages < L.HUB_PAGES:
        p = F.page(addr, before=chain[-1]["sig"])
        hub_pages += 1
        chain += p
        n_before += len(p)
        end = len(p) < 1000
    hub = n_before >= L.HUB_N
    res: dict[str, Any] = {
        "status": "hub" if hub else "read",
        "n_before": n_before,
        "history_end": end,
        "hub": hub,
        "inflow_listed": listed,
    }
    if hub:
        return res
    after = [e for e in reversed(chain[: max(found, 0)]) if (e["bt"] or 0) < inflow["bt"] + L.WINDOW_S and not e["err"]]
    reads = [txflow(F.tx(e["sig"]), addr) for e in after[: L.HOP_TX]]
    outs = [(d, v, f["sig"], f["slot"], f["bt"]) for f in reads for d, v in f["out"] if v >= L.MIN_SOL]
    res.update({"n_after": len(after), "n_read": len(reads), "outs": outs})
    return res


class Branch:
    """One outgoing SOL transfer of the exit wallet, followed hop by hop (section 3.4)."""

    def __init__(
        self,
        ev: dict[str, Any],
        src: str,
        dst: str,
        sol: float,
        sig: str,
        slot: int,
        bt: float,
        after_sale: bool,
        pooled: bool,
    ) -> None:
        self.ev = ev
        self.path = [{"wallet": src}, {"wallet": dst, "sol": sol, "sig": sig, "slot": slot, "bt": bt}]
        self.after_sale, self.pooled = after_sale, pooled
        self.terminal: Optional[str] = None
        self.reason: Optional[str] = None
        self.side: list[dict[str, Any]] = []
        self.measured: dict[str, Any] = {}

    def hop(self) -> int:
        return len(self.path) - 1

    def step(self, F: Fetch, R: Roles) -> None:
        if self.terminal:
            return
        cur = self.path[-1]
        c = R.classify(cur["wallet"], cur["bt"], self.ev)
        if c:
            self.terminal, self.reason = c, "known"
            return
        if cur["wallet"] in {p["wallet"] for p in self.path[:-1]}:
            self.terminal, self.reason = "H6", "cycle"
            return
        if self.hop() >= L.MAX_HOPS:
            self.terminal, self.reason = "H6", "UNRESOLVED MULTI-HOP FLOW"
            return
        try:
            r = read_node(F, cur["wallet"], cur)
        except (Budget, NotCollected) as x:
            self.terminal, self.reason = "H6", "budget" if isinstance(x, Budget) or not F.online else "not collected"
            return
        except HeliusError as x:
            self.terminal, self.reason = "H6", "rpc failure: %s" % str(x)[:80]
            return
        self.measured[cur["wallet"]] = {k: r.get(k) for k in ("status", "n_before", "hub", "history_end")}
        if r["status"] == "too active":
            self.terminal, self.reason = "H6", "too active"
            return
        if r["hub"]:
            self.terminal, self.reason = "H5", "hub measured"
            return
        if not r["outs"]:
            self.terminal, self.reason = "H6", "retained by an unknown wallet"
            return
        best = max(r["outs"], key=lambda o: (o[1], -(o[4] or 0)))
        for o in r["outs"]:
            if o is not best:
                self.side.append(
                    {
                        "hop": self.hop() + 1,
                        "wallet": o[0],
                        "sol": o[1],
                        "sig": o[2],
                        "bt": o[4],
                        "class": R.classify(o[0], o[4] or 0, self.ev),
                    }
                )
        self.path.append({"wallet": best[0], "sol": best[1], "sig": best[2], "slot": best[3], "bt": best[4]})

    def doc(self) -> dict[str, Any]:
        return {
            "wallet": self.ev["wallet"],
            "mint": self.ev["mint"],
            "path": self.path,
            "terminal": self.terminal,
            "reason": self.reason,
            "after_sale": self.after_sale,
            "pooled": self.pooled,
            "side": self.side,
            "measured": self.measured,
        }
