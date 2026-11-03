"""Metadata JSON of the deployer's launches. Public files on the launch tool's own host. Writes evidence/token_metadata.jsonl.

Only hosts already named in the token's own metadata pointer are read. A failure is recorded, never dropped.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from lib import OUT

names = [json.loads(x) for x in open(OUT / "token_names.jsonl")]
path = OUT / "token_metadata.jsonl"
have = {json.loads(x)["mint"] for x in open(path)} if path.exists() else set()
ok = bad = 0
with open(path, "a") as f:
    for n in names:
        if n["mint"] in have or not n.get("json_uri"):
            continue
        row = {"mint": n["mint"], "uri": n["json_uri"]}
        try:
            req = urllib.request.Request(n["json_uri"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read(200_000))
            row.update({k: d.get(k) for k in ("name", "symbol", "twitter", "website", "telegram", "createdOn", "description", "showName")})
            ok += 1
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            row["error"] = type(e).__name__
            bad += 1
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        time.sleep(0.25)
print("read", ok, "failed", bad)
