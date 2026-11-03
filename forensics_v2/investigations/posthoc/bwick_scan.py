"""Looks for the last card's mint among the bot's trades, by the part of it the screenshot shows. Output is private.

The card's price and posting time leave a few 40-minute windows. Within one, the bot's fee account lists every trade through it.

    python -m forensics_v2.investigations.posthoc.bwick_scan <credits per window> <unix start> [...]
"""

import json
import sys
from typing import Any

from ... import decode as D
from ...__main__ import client
from ...rpc import RpcError
from ..trades_2024 import PRIVATE, write_private
from ..trades_report import TOOL_FEE

PREFIX = "4V56nS"
SPAN_S = 40 * 60
OUT = "bwick_scan.json"


def mints_of(item: dict[str, Any]) -> set[str]:
    meta = item.get("meta") or {}
    return {b["mint"] for k in ("preTokenBalances", "postTokenBalances") for b in (meta.get(k) or [])}


def scan(c: Any, start: int, per_window: int) -> dict[str, Any]:
    token, pages, seen, hits, last = None, 0, 0, [], start
    while pages < per_window // 10:
        cfg: dict[str, Any] = {
            "transactionDetails": "full",
            "sortOrder": "asc",
            "limit": 100,
            "encoding": "json",
            "maxSupportedTransactionVersion": 1,
            "filters": {"tokenAccounts": "none", "status": "succeeded", "blockTime": {"gte": start, "lte": start + SPAN_S}},
        }
        if token:
            cfg["paginationToken"] = token
        r = c.call("getTransactionsForAddress", [TOOL_FEE, cfg], TOOL_FEE, credits=10)
        pages += 1
        for item in r.get("data") or []:
            seen += 1
            last = item.get("blockTime") or last
            for m in mints_of(item):
                if m.startswith(PREFIX):
                    d = D.decode(item)
                    hits.append(
                        {
                            "mint": m,
                            "sig": d.signature,
                            "payer": d.fee_payer,
                            "t": d.block_time,
                            "delta": d.lamport_delta.get(d.fee_payer),
                            "tok": D.traded_mints(d, d.fee_payer),
                        }
                    )
                    print("HIT", m, d.fee_payer, d.signature, d.block_time, flush=True)
        token = r.get("paginationToken")
        if not token:
            break
    return {"start": start, "pages": pages, "tx_seen": seen, "reached": last, "complete": token is None, "hits": hits}


def main() -> int:
    per_window = int(sys.argv[1])
    p = PRIVATE / OUT
    out = json.loads(p.read_text()) if p.exists() else {"windows": []}
    c = client((per_window + 30) * len(sys.argv[2:]))
    try:
        for s in map(int, sys.argv[2:]):
            w = scan(c, s, per_window)
            out["windows"].append(w)
            print({k: v for k, v in w.items() if k != "hits"}, "hits", len(w["hits"]), flush=True)
            write_private(OUT, json.dumps(out, indent=1))
            if w["hits"]:
                break
    except RpcError as e:  # credits or quota: keep what was read
        print("stopped", str(e)[:140])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
