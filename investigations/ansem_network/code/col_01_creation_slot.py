"""Rebuild the creation slot of ANSEM from the raw block.

Reads the whole block once so that transaction order is the chain's and tips sent in a separate
transaction of the same slot are seen. Writes the raw transactions that matter, gzipped, and a table.
"""
from __future__ import annotations

import struct
import sys

from lib import CREATION_SLOT, MINT, client, save_gz, save_json, sol, utc

from forensics_v2 import decode as D

COMPUTE_BUDGET = "ComputeBudget111111111111111111111111111111"


def compute_budget(tx: dict) -> dict:
    keys = D.account_keys(tx)
    out: dict = {}
    for ix in tx["transaction"]["message"]["instructions"]:
        if keys[ix["programIdIndex"]] != COMPUTE_BUDGET:
            continue
        raw = D.b58decode(ix.get("data") or "")
        if raw[:1] == b"\x02":
            out["unit_limit"] = struct.unpack_from("<I", raw, 1)[0]
        elif raw[:1] == b"\x03":
            out["unit_price"] = struct.unpack_from("<Q", raw, 1)[0]
    return out


def row(i: int, tx: dict) -> dict:
    d = D.decode(tx)
    m = tx["meta"]
    lookups = tx["transaction"]["message"].get("addressTableLookups") or []
    tips = [(t.src, t.dst, t.amount) for t in d.transfers if t.dst in D.JITO_TIP]
    return {
        "index_in_block": i,
        "signature": d.signature,
        "ok": d.ok,
        "err": m.get("err"),
        "fee_payer": d.fee_payer,
        "signers": d.signers,
        "fee_lamports": d.fee,
        "programs": d.programs,
        "version": tx.get("version"),
        "compute_budget": compute_budget(tx),
        "lookup_tables": [x["accountKey"] for x in lookups],
        "jito_tips": [{"src": s, "dst": t, "sol": sol(a)} for s, t, a in tips],
        "trades": [{**e, "sol_ui": sol(e["sol"]), "tok_ui": e["tok"] / 1e6} for e in d.trade_events],
        "owner_nets": {o: {"sol_change": sol(n.sol), "tokens": {k: v / 1e6 for k, v in n.tokens.items() if k == MINT}}
                       for o, n in d.owners.items()},
        "mint_ops": [{"kind": t.kind, "dst": t.dst, "dst_owner": t.dst_owner, "amount": t.amount / 1e6}
                     for t in d.transfers if t.kind in ("mint", "burn") and t.mint == MINT],
    }


def main() -> None:
    c = client(run_limit=50)
    block = c.call("getBlock", [CREATION_SLOT, {"encoding": "json", "transactionDetails": "full", "rewards": False,
                                                "maxSupportedTransactionVersion": 1}], str(CREATION_SLOT))
    if block is None:
        raise SystemExit("block not returned")
    txs = block["transactions"]
    touching = []
    for i, tx in enumerate(txs):
        tx = {**tx, "slot": CREATION_SLOT, "blockTime": block["blockTime"]}
        keys = D.account_keys(tx)
        if MINT in keys:
            touching.append((i, tx))
    if not touching:
        raise SystemExit("no transaction of the block cites the mint: wrong slot or a bad reply")

    rows = [row(i, tx) for i, tx in touching]
    signers = {s for r in rows for s in r["signers"]}
    # Same signers in the same slot, without the mint: separate tip or funding transactions.
    side = []
    for i, tx in enumerate(txs):
        tx = {**tx, "slot": CREATION_SLOT, "blockTime": block["blockTime"]}
        keys = D.account_keys(tx)
        header = tx["transaction"]["message"]["header"]
        sg = keys[:header["numRequiredSignatures"]]
        if MINT not in keys and signers & set(sg):
            side.append((i, tx))
    side_rows = [row(i, tx) for i, tx in side]

    save_gz("raw/creation_slot_txs.json.gz", [tx for _, tx in touching + side])
    table = {
        "slot": CREATION_SLOT,
        "block_time": block["blockTime"],
        "block_time_utc": utc(block["blockTime"]),
        "block_hash": block.get("blockhash"),
        "parent_slot": block.get("parentSlot"),
        "transactions_in_block": len(txs),
        "touching_mint": len(rows),
        "touching_mint_ok": sum(r["ok"] for r in rows),
        "touching_mint_failed": sum(not r["ok"] for r in rows),
        "rows": rows,
        "same_signer_other_tx": side_rows,
    }
    save_json("creation_slot.json", table)
    print("block txs", len(txs), "touching mint", len(rows), "ok", table["touching_mint_ok"], "side", len(side_rows))
    print("credits this run", c.budget.run_spent, "keys", c.pool.status())
    for r in rows:
        tr = [(e["user"][:8], "BUY" if e["buy"] else "SELL", e["sol_ui"], e["tok_ui"]) for e in r["trades"]]
        print(r["index_in_block"], r["signature"][:12], "ok" if r["ok"] else "FAIL", "signers",
              [s[:8] for s in r["signers"]], r["compute_budget"], "tips", [t["sol"] for t in r["jito_tips"]], tr,
              [(m["kind"], m["dst_owner"][:8] if m["dst_owner"] else None, m["amount"]) for m in r["mint_ops"]])


if __name__ == "__main__":
    sys.exit(main())
