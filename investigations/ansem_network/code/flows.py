"""One wallet's decoded history turned into rows: SOL flows, token transfers, trades, created mints.

Rows are written to one JSONL per wallet in the work area and read back through DuckDB, never kept in a dict.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from lib import DATA, guard

from forensics_v2 import decode as D
from forensics_v2 import trace as T
from forensics_v2.rpc import RpcClient

ROWS = DATA / "rows"
PUMP_SUPPLY_RAW = 1_000_000_000_000_000


def rows_of(addr: str, d: D.Decoded) -> Iterator[dict[str, Any]]:
    base = {"wallet": addr, "sig": d.signature, "slot": d.slot, "ts": d.block_time}
    if not d.ok:
        return
    for t in d.transfers:
        if t.kind == "mint" and t.amount == PUMP_SUPPLY_RAW and D.PUMP in d.programs:
            yield {**base, "kind": "create", "mint": t.mint, "creator": d.fee_payer, "signers": d.signers}
    for t in d.transfers:
        if t.kind != "spl" or t.mint in (None, D.WSOL):
            continue
        if addr in (t.src_owner, t.dst_owner):
            yield {**base, "kind": "token_transfer", "mint": t.mint, "src": t.src_owner, "dst": t.dst_owner,
                   "raw": t.amount, "signers": d.signers}
    net = d.owners.get(addr)
    traded = D.traded_mints(d, addr)
    if traded and net:
        yield {**base, "kind": "trade", "mints": traded, "sol": net.sol, "native": net.native, "fee": d.fee,
               "venues": d.venues, "fee_payer": d.fee_payer}


def sol_rows(h: T.History) -> Iterator[dict[str, Any]]:
    flows, unresolved = T.sol_flows(h)
    for f in flows:
        yield {"wallet": h.address, "sig": f.signature, "slot": f.slot, "ts": f.ts, "kind": "sol", "src": f.src,
               "dst": f.dst, "lamports": f.lamports, "evidence": f.evidence, "basis": f.basis}
    for u in unresolved:
        yield {"wallet": h.address, "sig": u["signature"], "kind": "sol_unresolved", "lamports": u["lamports"]}


def collect(c: RpcClient, addr: str, max_pages: int = 100, t_from: int | None = None,
            t_to: int | None = None) -> dict[str, Any]:
    """Writes the wallet's rows and returns its coverage. Raises on an outage: nothing is written as empty."""
    guard()
    h = T.history(c, addr, t_from=t_from, t_to=t_to, max_pages=max_pages)
    ROWS.mkdir(parents=True, exist_ok=True)
    suffix = "" if t_from is None and t_to is None else "_%s_%s" % (t_from, t_to)
    path: Path = ROWS / (addr + suffix + ".jsonl")
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        for d in h.txs:
            for r in rows_of(addr, d):
                f.write(json.dumps(r) + "\n")
        for r in sol_rows(h):
            f.write(json.dumps(r) + "\n")
    tmp.replace(path)
    return {"address": addr, **h.coverage(), "complete": h.walk.complete}


def stream(c: RpcClient, addr: str, max_pages: int, t_from: int | None = None, t_to: int | None = None,
           start_token: str | None = None, pages_done: int = 0) -> dict[str, Any]:
    """Same rows as collect(), one page in memory at a time, bodies not stored. Resumable from a saved token.

    Rows are appended before the token is saved, so a crash can only duplicate rows: readers use DISTINCT.
    """
    tag = "%s_%s_%s" % (addr, t_from or "start", t_to or "end")
    ck = DATA / "checkpoints" / "stream" / (tag + ".json")
    ck.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads(ck.read_text()) if ck.exists() else {"next": start_token, "pages": pages_done, "done": False,
                                                            "txs": 0, "first_ts": None, "last_ts": None}
    ROWS.mkdir(parents=True, exist_ok=True)
    path = ROWS / (addr + ("" if t_from is None and t_to is None else "_%s_%s" % (t_from, t_to)) + ".jsonl")
    filters: dict[str, Any] = {"tokenAccounts": "balanceChanged"}
    window = {k: v for k, v in (("gte", t_from), ("lte", t_to)) if v is not None}
    if window:
        filters["blockTime"] = window
    run = 0
    while not state["done"] and run < max_pages:
        guard()
        cfg: dict[str, Any] = {"transactionDetails": "full", "sortOrder": "asc", "limit": 100, "filters": filters,
                               "encoding": "json", "maxSupportedTransactionVersion": 1}
        if state["next"]:
            cfg["paginationToken"] = state["next"]
        r = c.call("getTransactionsForAddress", [addr, cfg], addr, credits=10)
        for _ in range(2):  # an empty ending page is only believed after asking again
            if not (isinstance(r, dict) and r.get("data") == [] and r.get("paginationToken") is None):
                break
            r = c.call("getTransactionsForAddress", [addr, cfg], addr, credits=10)
        data = r.get("data") if isinstance(r, dict) else None
        if not isinstance(data, list) or "paginationToken" not in r:
            raise RuntimeError("getTransactionsForAddress: malformed reply for " + addr)
        decoded = [D.decode(t) for t in data]
        walk = T.SigWalk(addr, [], False, "page", 1)
        with open(path, "a") as f:
            for d in decoded:
                for row in rows_of(addr, d):
                    f.write(json.dumps(row) + "\n")
            for row in sol_rows(T.History(addr, walk, decoded)):
                f.write(json.dumps(row) + "\n")
        if decoded:
            state["first_ts"] = state["first_ts"] or decoded[0].block_time
            state["last_ts"] = decoded[-1].block_time
        state["txs"] += len(decoded)
        state["pages"] += 1
        state["next"] = r["paginationToken"]
        state["done"] = r["paginationToken"] is None
        run += 1
        tmp = ck.with_suffix(".tmp")
        tmp.write_text(json.dumps(state))
        tmp.replace(ck)
    return {"address": addr, **state, "complete": state["done"]}
