"""All transactions citing the mint inside a time window, written as one row per owner token change, in chain order.

Usage: col_04_mint_window.py <name> <utc start> <utc end> <max_pages> <run_credit_limit>
"""
from __future__ import annotations

import calendar
import json
import sys
import time

from lib import DATA, MINT, client, guard

from forensics_v2 import decode as D


def ts(s: str) -> int:
    return calendar.timegm(time.strptime(s, "%Y-%m-%d %H:%M:%S"))


def main() -> None:
    name, a, b, pages, limit = sys.argv[1], ts(sys.argv[2]), ts(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    c = client(run_limit=limit)
    out = DATA / "mint" / (name + ".jsonl")
    ck = DATA / "mint" / (name + ".ck.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    st = json.loads(ck.read_text()) if ck.exists() else {"next": None, "pages": 0, "done": False, "txs": 0, "ok": 0}
    cfg_base = {"transactionDetails": "full", "sortOrder": "asc", "limit": 100, "encoding": "json",
                "maxSupportedTransactionVersion": 1, "filters": {"blockTime": {"gte": a, "lte": b}, "status": "succeeded"}}
    run = 0
    while not st["done"] and run < pages:
        guard()
        cfg = dict(cfg_base)
        if st["next"]:
            cfg["paginationToken"] = st["next"]
        r = c.call("getTransactionsForAddress", [MINT, cfg], MINT, credits=10)
        data = r["data"]
        with open(out, "a") as f:
            for t in data:
                d = D.decode(t)
                st["txs"] += 1
                nets = {o: {"tok": n.tokens.get(MINT, 0), "sol": n.sol} for o, n in d.owners.items() if n.tokens.get(MINT)}
                if not nets:
                    continue
                st["ok"] += 1
                f.write(json.dumps({"sig": d.signature, "slot": d.slot, "idx": t.get("transactionIndex"), "ts": d.block_time,
                                    "signers": d.signers, "nets": nets, "venues": d.venues, "fee": d.fee,
                                    "transfers": [[x.src_owner, x.dst_owner, x.amount] for x in d.transfers
                                                  if x.kind == "spl" and x.mint == MINT]}) + "\n")
        st["next"], st["done"] = r["paginationToken"], r["paginationToken"] is None
        st["pages"] += 1
        run += 1
        ck.write_text(json.dumps(st))
    print(name, st["pages"], "pages", st["txs"], "txs", st["ok"], "with a token change", "done", st["done"],
          "run credits", c.budget.run_spent, "total", c.budget.used())


if __name__ == "__main__":
    main()
