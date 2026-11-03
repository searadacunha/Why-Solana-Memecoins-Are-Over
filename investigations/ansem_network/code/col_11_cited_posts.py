"""Read every X post cited by the deployer's launches. Slow on purpose. Posts gone from X are recorded as unreadable."""
from __future__ import annotations

import json
import re
import time

from col_10_x_posts import STORE, fetch, known
from lib import OUT

have = known()
ids = []
for line in open(OUT / "token_metadata.jsonl"):
    m = re.search(r"(?:x|twitter)\.com/[^/]+/status/(\d{15,25})", json.loads(line).get("twitter") or "")
    if m and m.group(1) not in have:
        ids.append(m.group(1))
ids = list(dict.fromkeys(ids))
print("to read", len(ids), flush=True)
for i in ids:
    r = fetch(i)
    with open(STORE, "a") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    time.sleep(1.2)
print("done", flush=True)
