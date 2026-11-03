"""The author's trades as a ledger of every transaction: no trip cutting, exact chain values, private outputs only.

Reads the frozen study's raw cache, no network, and writes one row per (wallet, transaction) with what that wallet's accounts did:
native lamports, wrapped SOL, token-account rent, token changes, its transfers and venues. Every later figure is a sum over
these rows, so that it can be recomputed by anyone holding the private folder.

    python -m forensics_v2.investigations.trades_ledger extract
"""

from __future__ import annotations

import gzip
import json
import resource
import sys
from concurrent.futures import ProcessPoolExecutor
from typing import Any

from .. import decode as D
from .trades_2024 import CACHE, PRIVATE, ledger

DERIVED = PRIVATE / "derived"
ROWS = DERIVED / "txrows.jsonl.gz"
MAX_RSS_BYTES = 1_500_000_000  # machine has 17 GB shared with other sessions: stop rather than swap, see the project notes


def row_of(wallet: str, sig: str) -> dict[str, Any]:
    with open(CACHE / (sig + ".json")) as f:
        raw = json.load(f)["result"]
    d = D.decode(raw)
    n = d.owners.get(wallet)
    at = d.keys.index(wallet) if wallet in d.keys else None
    moves = []
    for t in d.transfers:
        if t.mint is None or t.kind == "wsol_lamports":
            if wallet in (t.src, t.dst) and t.kind != "wsol_lamports":
                moves.append({"k": t.kind, "src": t.src, "dst": t.dst, "n": t.amount})
        elif wallet in (t.src_owner, t.dst_owner):
            moves.append({"k": t.kind, "src": t.src_owner, "dst": t.dst_owner, "n": t.amount, "mint": t.mint})
    return {
        "w": wallet,
        "sig": sig,
        "slot": d.slot,
        "t": d.block_time,
        "ok": d.ok,
        "fee": d.fee,
        "payer": d.fee_payer,
        "signers": d.signers,
        "pre": raw["meta"]["preBalances"][at] if at is not None else None,
        "post": raw["meta"]["postBalances"][at] if at is not None else None,
        "native": d.lamport_delta.get(wallet, 0),
        "wsol": n.wsol if n else 0,
        "rent": n.rent if n else 0,
        "tok": D.traded_mints(d, wallet),
        "moves": moves,
        "edges": [[e.src, e.dst, e.lamports, e.basis] for e in d.edges if wallet in (e.src, e.dst)],
        "venues": d.venues,
        "programs": d.programs,
        "unresolved": d.unresolved_sol.get(wallet, 0),
        "conserved": d.conserved,
    }


def _wallet(job: tuple[str, list[str]]) -> list[dict[str, Any]]:
    return [row_of(job[0], s) for s in job[1]]


def extract() -> int:
    DERIVED.mkdir(mode=0o700, exist_ok=True)
    jobs = [(w, [r["sig"] for r in rows]) for w, rows in ledger()["ledger"].items()]
    n = 0
    with gzip.open(ROWS, "wt") as out, ProcessPoolExecutor(3) as ex:
        for rows in ex.map(_wallet, jobs):
            for r in rows:
                out.write(json.dumps(r, separators=(",", ":")) + "\n")
            n += len(rows)
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if rss > MAX_RSS_BYTES:
                raise SystemExit("memory limit reached: %d" % rss)
    ROWS.chmod(0o600)
    print("rows", n, "wallets", len(jobs))
    return 0


def token_meta() -> int:
    """Name and symbol of every mint traded, by DAS batches of 1,000: 10 credits a call, a handful of calls. Kept privately."""
    from ..__main__ import client

    mints = sorted({m for line in gzip.open(ROWS, "rt") for m in json.loads(line)["tok"]})
    c = client(100)
    out: dict[str, Any] = {}
    for i in range(0, len(mints), 1000):
        for a in c.call("getAssetBatch", {"ids": mints[i : i + 1000]}, "token_meta", credits=10):  # type: ignore[arg-type]
            if a:
                md = a.get("content", {}).get("metadata", {})
                out[a["id"]] = {
                    "symbol": md.get("symbol"),
                    "name": md.get("name"),
                    "decimals": a.get("token_info", {}).get("decimals"),
                    "supply": a.get("token_info", {}).get("supply"),
                }
    (DERIVED / "token_meta.json").write_text(json.dumps(out))
    print("mints", len(mints), "with metadata", len(out), "credits this run", c.budget.used() if hasattr(c, "budget") else "?")
    return 0


if __name__ == "__main__":
    raise SystemExit({"extract": extract, "token_meta": token_meta}[sys.argv[1]]())
