"""Names and metadata links of mints, from DAS. Usage: col_05_names.py <file with one mint per line>. Appends to evidence/token_names.jsonl."""
from __future__ import annotations

import json
import sys

from lib import OUT, client

path = OUT / "token_names.jsonl"
have = set()
if path.exists():
    have = {json.loads(x)["mint"] for x in open(path)}
todo = [x.strip() for x in open(sys.argv[1]) if x.strip() and x.strip() not in have]
c = client(run_limit=2000)
for i in range(0, len(todo), 500):
    batch = todo[i:i + 500]
    r = c.call("getAssetBatch", [batch], "batch", credits=10)
    if len(r) != len(batch):
        raise SystemExit("batch came back short: %d of %d" % (len(r), len(batch)))
    with open(path, "a") as f:
        for m, a in zip(batch, r):
            meta = ((a or {}).get("content") or {}).get("metadata") or {}
            f.write(json.dumps({"mint": m, "name": meta.get("name"), "symbol": meta.get("symbol"),
                                "json_uri": ((a or {}).get("content") or {}).get("json_uri"),
                                "permanent_delegate": ((a or {}).get("mint_extensions") or {}).get("permanent_delegate")}) + "\n")
    print(i + len(batch), "of", len(todo), "credits", c.budget.used(), flush=True)
