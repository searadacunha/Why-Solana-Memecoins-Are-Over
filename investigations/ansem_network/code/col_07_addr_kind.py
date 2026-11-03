"""Cheap identity of an address: owning program, balance, recent activity. Usage: col_07_addr_kind.py <addr>...

Appends to evidence/address_kinds.jsonl. A program-owned account is a pool, vault or PDA, not a person's wallet.
"""
from __future__ import annotations

import json
import sys
import time

from lib import OUT, client

c = client(run_limit=len(sys.argv) * 3 + 10)
out = OUT / "address_kinds.jsonl"
for a in sys.argv[1:]:
    info = c.call("getAccountInfo", [a, {"encoding": "base64", "dataSlice": {"offset": 0, "length": 0}}], a)["value"]
    sigs = c.call("getSignaturesForAddress", [a, {"limit": 1000}], a)
    span = (sigs[0]["blockTime"] - sigs[-1]["blockTime"]) if len(sigs) > 1 else None
    row = {"address": a, "exists": bool(info), "owner": info and info["owner"], "lamports": info and info["lamports"],
           "executable": info and info["executable"], "recent_sigs": len(sigs),
           "seconds_for_last_1000": span if len(sigs) == 1000 else None, "read_at_unix": int(time.time())}
    with open(out, "a") as f:
        f.write(json.dumps(row) + "\n")
    print(a[:12], "owner", (row["owner"] or "")[:12], "SOL", round((row["lamports"] or 0) / 1e9, 2), "sigs", len(sigs), "s/1000", row["seconds_for_last_1000"], flush=True)
print("total", c.budget.used())
