"""Multi-hop funding and destination tracing for one wallet.

Every edge points to a signature. A branch that stops says why. "First observable activity" is only
called first activity when the signature walk reached genesis, and a walk that hit its cap is
reported as truncated rather than as a complete history. Connected wallets stay separate nodes:
nothing here merges them into one economic entity.
"""
from __future__ import annotations

import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from . import decode as D
from .rpc import BudgetExhausted, RpcClient, SigWalk, TxNotFound

SERVICES_FILE = Path(__file__).with_name("service_attributions.json")


def load_services(path: Path = SERVICES_FILE) -> dict[str, dict[str, str]]:
    return {e["address"]: e for e in json.loads(path.read_text())["entries"]}


@dataclass
class History:
    address: str
    walk: SigWalk
    txs: list[D.Decoded]
    missing: list[str] = field(default_factory=list)
    token_accounts: str = "balanceChanged"

    @property
    def complete(self) -> bool:
        return self.walk.complete and not self.missing and self.token_accounts != "none"

    def coverage(self) -> dict[str, Any]:
        first = self.walk.first_observable()
        return {"transactions_read": len(self.walk.signatures), "pages": self.walk.pages, "walk_stop": self.walk.stop,
                "reached_genesis": self.walk.stop == "genesis", "transactions_decoded": len(self.txs),
                "transactions_missing": len(self.missing), "token_account_inflows": self.token_accounts,
                "first_observable_ts": first.get("blockTime") if first else None,
                "first_observable_is_first_activity": self.walk.stop == "genesis" and first is not None}


def read_many(client: RpcClient, sigs: Iterable[str], workers: int = 8) -> tuple[dict[str, D.Decoded], list[str]]:
    """Decode many signatures. A null answer is listed as missing; an outage raises."""
    out: dict[str, D.Decoded] = {}
    missing: list[str] = []

    def one(s: str) -> None:
        try:
            out[s] = D.decode(client.tx(s))
        except TxNotFound:
            missing.append(s)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(one, sigs))  # list() so that the first exception propagates
    return out, missing


def history(client: RpcClient, addr: str, t_from: Optional[int] = None, t_to: Optional[int] = None,
            max_pages: int = 20, token_accounts: str = "balanceChanged") -> History:
    """Decoded history of a wallet in exact chain order, with its coverage.

    Signatures of the owner miss SPL inflows to an account that already exists, because such a
    transfer does not cite the owner. balanceChanged asks for those too; "none" leaves them out,
    which the coverage then states.
    """
    raw, walk = client.history_txs(addr, t_from, t_to, token_accounts, max_pages)
    return History(addr, walk, [D.decode(t) for t in raw], [], token_accounts)


@dataclass(frozen=True)
class Flow:
    src: str
    dst: str
    lamports: int
    signature: str
    slot: int
    ts: Optional[int]
    evidence: str
    basis: str
    path: Optional[str]


def sol_flows(h: History) -> tuple[list[Flow], list[dict[str, Any]]]:
    """SOL edges touching this wallet, and the SOL no edge explains.

    A transaction where the wallet's tokens change is a trade: its leg with the pool or curve is a
    position event, not funding. Only a direct instruction to or from another party survives there.
    """
    flows: list[Flow] = []
    unresolved: list[dict[str, Any]] = []
    for d in h.txs:
        if not d.ok:
            continue
        trading = bool(D.traded_mints(d, h.address))
        venues = D.trade_counterparties(d, h.address) if trading else set()
        for e in d.edges:
            if h.address not in (e.src, e.dst) or (trading and e.basis != "instruction"):
                continue
            if (e.dst if e.src == h.address else e.src) in venues:
                continue  # a buy's payment to the bonding curve is a trade, not a shared destination
            flows.append(Flow(e.src, e.dst, e.lamports, d.signature, d.slot, d.block_time,
                              e.evidence, e.basis, e.path))
        if h.address in d.unresolved_sol and not trading:
            unresolved.append({"signature": d.signature, "lamports": d.unresolved_sol[h.address],
                               "evidence": D.UNRESOLVED})
    return flows, unresolved


@dataclass
class Trip:
    wallet: str
    mint: str
    t_open: int
    sig_open: str
    sol_out: int = 0
    sol_in: int = 0
    bought: int = 0
    sold: int = 0
    n_buys: int = 0
    n_sells: int = 0
    t_close: Optional[int] = None
    closed: bool = False
    venues: set[str] = field(default_factory=set)
    sigs: list[str] = field(default_factory=list)

    @property
    def realised(self) -> int:
        return self.sol_in - self.sol_out


def trips(txs: Iterable[D.Decoded], wallet: str) -> list[Trip]:
    """Round trips of a wallet. A trip opens on a buy from flat and closes when its tokens are gone.

    SOL of a leg is the wallet's own lamport change, so all costs are inside. Same convention as
    the frozen 2024 study, so that its totals can be checked by a separate implementation.
    Wrapped SOL is deliberately not added here, for that comparison to stay exact.
    """
    legs: dict[str, list[tuple[str, D.Decoded, int, int]]] = defaultdict(list)
    for d in txs:
        tok = D.traded_mints(d, wallet)
        if not tok:
            continue
        sol = d.lamport_delta.get(wallet, 0)
        share = int(sol / len(tok))  # multi-mint transactions are rare; an equal split, stated
        for mint, dt in tok.items():
            side = "buy" if dt > 0 and share < 0 else "sell" if dt < 0 and share > 0 else "other"
            legs[mint].append((side, d, dt, share))
    out: list[Trip] = []
    for mint, rows in legs.items():
        rows.sort(key=lambda r: r[1].block_time or 0)
        cur: Optional[Trip] = None
        hold = 0
        for side, d, dt, share in rows:
            if side == "buy" and cur is None:
                cur = Trip(wallet, mint, d.block_time or 0, d.signature)
            hold += dt
            if cur is None:
                continue
            cur.sigs.append(d.signature)
            cur.venues.update(d.venues)
            if side == "buy":
                cur.sol_out -= share
                cur.bought += dt
                cur.n_buys += 1
            elif side == "sell":
                cur.sol_in += share
                cur.sold -= dt
                cur.n_sells += 1
                cur.t_close = d.block_time
            if cur.bought and hold * 1000 <= cur.bought:
                cur.closed = True
                out.append(cur)
                cur, hold = None, 0
        if cur:
            out.append(cur)
    return out


@dataclass
class Graph:
    seed: str
    direction: str
    hops: int
    min_lamports: int
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    stops: list[dict[str, Any]] = field(default_factory=list)
    budget_hit: bool = False


def trace(client: RpcClient, seed: str, direction: str = "both", hops: int = 2, min_lamports: int = 10_000_000,
          max_branches: int = 8, max_pages: int = 20, services: Optional[dict[str, dict[str, str]]] = None,
          t_from: Optional[int] = None, t_to: Optional[int] = None) -> Graph:
    """Breadth-first from `seed`. Stops at a service, a truncated history, or the hop limit, and says so."""
    services = load_services() if services is None else services
    g = Graph(seed, direction, hops, min_lamports)
    frontier = [(seed, 0, d) for d in (("back", "forward") if direction == "both" else (direction,))]
    expanded: set[tuple[str, str]] = set()
    seen_edges: set[tuple[str, str, str, str, Optional[str]]] = set()
    while frontier:
        addr, depth, way = frontier.pop(0)
        if (addr, way) in expanded:
            continue
        expanded.add((addr, way))
        if addr in services:
            g.nodes.setdefault(addr, {}).update(role="service", service=services[addr]["name"])
            g.stops.append({"address": addr, "direction": way, "reason": "service_boundary",
                            "note": "a custodial service's internal ledger is not on chain: the path ends here"})
            continue
        try:
            h = history(client, addr, t_from=t_from, t_to=t_to, max_pages=max_pages)
        except BudgetExhausted:
            g.budget_hit = True
            g.stops.append({"address": addr, "direction": way, "reason": "credit_budget"})
            continue
        flows, unresolved = sol_flows(h)
        node = g.nodes.setdefault(addr, {})
        node.update(coverage=h.coverage(), n_unresolved_sol=len(unresolved),
                    unresolved_lamports=sum(u["lamports"] for u in unresolved))
        node.setdefault("role", "seed" if addr == seed else "wallet")
        if not h.walk.complete:
            g.stops.append({"address": addr, "direction": way, "reason": "history_truncated",
                            "note": "signature walk capped: edges below are a lower bound"})
        for f in flows:
            key = (f.signature, f.src, f.dst, f.basis, f.path)
            if f.lamports >= min_lamports and key not in seen_edges:
                seen_edges.add(key)
                g.edges.append({"src": f.src, "dst": f.dst, "lamports": f.lamports, "signature": f.signature,
                                "slot": f.slot, "ts": f.ts, "evidence": f.evidence, "basis": f.basis,
                                "instruction": f.path})
        if depth >= hops or not h.walk.complete:
            if depth >= hops:
                g.stops.append({"address": addr, "direction": way, "reason": "hop_limit"})
            continue
        side = [f for f in flows if (f.dst == addr if way == "back" else f.src == addr) and f.lamports >= min_lamports]
        totals: dict[str, int] = defaultdict(int)
        for f in side:
            totals[f.src if way == "back" else f.dst] += f.lamports
        ranked = sorted(totals.items(), key=lambda x: (-x[1], x[0]))
        if len(ranked) > max_branches:
            g.stops.append({"address": addr, "direction": way, "reason": "branches_pruned",
                            "kept": max_branches, "dropped": len(ranked) - max_branches,
                            "lamports_dropped": sum(v for _, v in ranked[max_branches:])})
        for other, _ in ranked[:max_branches]:
            frontier.append((other, depth + 1, way))
    return g


def findings(g: Graph) -> dict[str, Any]:
    """Structure of the graph: facts about edges, never a statement about who controls what."""
    inc: dict[str, set[str]] = defaultdict(set)
    out: dict[str, set[str]] = defaultdict(set)
    for e in g.edges:
        inc[e["dst"]].add(e["src"])
        out[e["src"]].add(e["dst"])
    pairs = {(e["src"], e["dst"]) for e in g.edges}
    return {
        "shared_sources": sorted(a for a, b in out.items() if len(b) >= 2),
        "shared_destinations": sorted(a for a, b in inc.items() if len(b) >= 2),
        "fan_outs": sorted(((a, len(b)) for a, b in out.items() if len(b) >= 5), key=lambda x: -x[1]),
        "returns": sorted({tuple(sorted(p)) for p in pairs if (p[1], p[0]) in pairs}),
        "evidence_counts": {lvl: sum(1 for e in g.edges if e["evidence"] == lvl) for lvl in D.EVIDENCE_LEVELS
                            if any(e["evidence"] == lvl for e in g.edges)},
    }


def _sol(x: int) -> str:
    return "%.9f" % (x / 1e9)  # display only; stored values stay integers


def render(g: Graph) -> str:
    f = findings(g)
    cov = g.nodes.get(g.seed, {}).get("coverage", {})
    lines = ["# Trace of %s" % g.seed, "", "Direction %s, %d hops, edges of at least %s SOL." %
             (g.direction, g.hops, _sol(g.min_lamports)), "",
             "## Coverage of the seed", ""]
    lines += ["- %s: %s" % (k, cov.get(k)) for k in sorted(cov)]
    if g.budget_hit:
        lines += ["", "**Stopped by the credit budget: this report is partial.**"]
    lines += ["", "## Edges (%d)" % len(g.edges), "", "| from | to | SOL | UTC ts | evidence | basis | signature |",
              "|---|---|---:|---:|---|---|---|"]
    for e in sorted(g.edges, key=lambda x: (x["slot"], x["signature"])):
        lines.append("| `%s` | `%s` | %s | %s | %s | %s | `%s` |" % (e["src"], e["dst"], _sol(e["lamports"]), e["ts"],
                                                                     e["evidence"], e["basis"], e["signature"]))
    lines += ["", "## Where the paths stop (%d)" % len(g.stops), ""]
    lines += ["- `%s` (%s): %s%s" % (s["address"], s["direction"], s["reason"],
                                     " : " + s["note"] if s.get("note") else "") for s in g.stops]
    lines += ["", "## Structure", "", "```json", json.dumps(f, indent=1), "```", "",
              "A shared counterparty or a return is a fact about transactions. It does not show that two wallets "
              "have the same owner."]
    return "\n".join(lines) + "\n"
