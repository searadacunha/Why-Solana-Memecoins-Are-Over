"""Re-derive every checked claim of the ledger from the saved raw transactions and X posts. No network. Exit 1 on any failure."""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))

from forensics_v2 import decode as D  # noqa: E402

JITO = D.JITO_TIP
PFEE = "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ"
APPROX = 1_000_000  # lamports: stated amounts rounded to the digits the claim shows


def fee_shares(t: dict, keys: list[str]) -> list[list]:
    out = []
    for ix in t["transaction"]["message"]["instructions"]:
        if keys[ix["programIdIndex"]] != PFEE:
            continue
        raw = D.b58decode(ix.get("data") or "")
        if raw[:8].hex() not in ("bd0d8863bba4ed23", "6ffb31064e4e6a12"):
            continue
        n = int.from_bytes(raw[8:12], "little")
        for i in range(n):
            out.append([D.b58encode(raw[12 + i * 34:44 + i * 34]), int.from_bytes(raw[44 + i * 34:46 + i * 34], "little")])
    return out


def check(t: dict, what: str, arg, index_of: dict[str, int]) -> str | None:
    d = D.decode(t)
    if what == "time":
        return None if d.block_time == arg else "time %s, expected %s" % (d.block_time, arg)
    if what == "slot":
        return None if d.slot == arg else "slot %s" % d.slot
    if what == "signer":
        return None if arg in d.signers else "%s did not sign" % arg[:8]
    if what == "not_signer":
        return None if arg not in d.signers else "%s signed" % arg[:8]
    if what == "failed":
        return None if not d.ok else "transaction succeeded"
    if what == "fee_share":
        return None if arg in fee_shares(t, d.keys) else "shares %s" % fee_shares(t, d.keys)
    if what == "trade_sol":
        return None if any(e["sol"] == arg for e in d.trade_events) else "trade events %s" % [e["sol"] for e in d.trade_events]
    if what == "no_jito_tip":
        return None if not any(x.dst in JITO for x in d.transfers) else "a Jito tip is present"
    if what == "index":
        return None if index_of.get(d.signature) == arg else "index %s" % index_of.get(d.signature)
    if what == "owner_sol":
        n = d.owners.get(arg[0])
        if n is None:
            return "owner absent"
        tol = APPROX if len(arg) > 2 else 0
        return None if abs(n.sol - arg[1]) <= tol else "SOL %s, expected %s" % (n.sol, arg[1])
    if what == "owner_sol_gain":
        n = d.owners.get(arg)
        return None if n and n.sol > 0 else "no SOL gain for %s" % arg[:8]
    if what == "owner_token":
        n = d.owners.get(arg[0])
        got = n.tokens.get(arg[1]) if n else None
        return None if got == arg[2] else "tokens %s, expected %s" % (got, arg[2])
    if what == "owner_token_any":
        n = d.owners.get(arg[0])
        return None if n and arg[1] in n.tokens.values() else "no token change of %s" % arg[1]
    return "unknown check " + what


def main() -> int:
    ev = ROOT / "evidence"
    with gzip.open(ev / "raw" / "key_txs.json.gz", "rt") as f:
        raw = json.load(f)
    with open(ev / "x_posts.jsonl") as f:
        posts = {}
        for line in f:
            r = json.loads(line)
            posts[r["id"]] = r
    with open(ev / "creation_slot.json") as f:
        cs = json.load(f)
    index_of = {r["signature"]: r["index_in_block"] for r in cs["rows"]}
    bad = n = 0
    for e in json.load(open(ev / "ledger.json")):
        for c in e["checks"]:
            n += 1
            err = check(raw[c["sig"]], c["check"], c["arg"], index_of)
            if err:
                bad += 1
                print("FAIL", e["id"], c["check"], c["sig"][:14], err)
        for p in e["posts"]:
            n += 1
            r = posts.get(p["id"])
            if not r or not r.get("readable") or p["contains"].lower() not in r["text"].lower():
                bad += 1
                print("FAIL", e["id"], "post", p["id"], "text does not contain:", p["contains"])
            elif ((int(p["id"]) >> 22) + 1288834974657) // 1000 and r["created_at"][:19].replace("T", " ") != r["id_time_utc"]:
                bad += 1
                print("FAIL", e["id"], "post time", p["id"], r["created_at"], r["id_time_utc"])
    print("checks", n, "failed", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
