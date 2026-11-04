"""Cross-chain movements out of Solana, with what each level of proof rests on.

A bridge program in a transaction is a fact on chain. The message identity is a fact when its sequence and emitter are
found in that same transaction. The arrival is a fact only once the destination chain's own node shows the transaction,
successful. Whatever comes from an indexer alone stays INDEXER_REPORTED. A custodial swap, ChangeNOW for instance, leaves
no such link: nothing here can follow it.

    python -m forensics_v2.crosschain prove <signature>     # public endpoints, no key, no credit
    python -m forensics_v2.crosschain scan <dir of raw JSON transactions>
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from typing import Any, Optional

from . import decode as D

ONCHAIN = "ONCHAIN_VERIFIED"
INDEXER = "INDEXER_REPORTED"
NOT_FOUND = "NOT_FOUND"

# Program ids from each project's public documentation. Absence from this list is not absence of a bridge.
BRIDGE_PROGRAMS = {
    "worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth": "wormhole_core",
    "wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb": "wormhole_token_bridge",
    "src5qyZHqTqecJV4aY6Cb6zDZLMDzrDKKezs22MPHr4": "debridge_source",
    "dst5MGcFPoBeREFAA5E3tU5ij8m5uVYwkzkSAbsLbNo": "debridge_destination",
    "BLZRi6frs4X4DNLw56V4EXai1b6QVESN1BhHBTYM9VcY": "mayan_swift",
    "FC4eXxkyrMPTjiYUpp4EAnkmwMbQyZ6NDCh1kfLn6vsf": "mayan_forwarder",
    "BrdgN2RPzEMWF96ZbnnJaUtQDQx7VRXYaHHbYCBvceWB": "allbridge_core",
    "CCTPiPYPc6AsJuwueEnWgSgucamXDZwBd53dQ11YiKX3": "cctp_message_transmitter",
}
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
WORMHOLESCAN = "https://api.wormholescan.io/api/v1/operations?txHash=%s"
# Wormhole chain id -> a public node keeping old receipts: publicnode returned none for a 2024 transaction, drpc did.
EVM_RPC = {
    2: "https://eth.drpc.org",
    4: "https://bsc.drpc.org",
    5: "https://polygon.drpc.org",
    6: "https://avalanche.drpc.org",
    23: "https://arbitrum.drpc.org",
    24: "https://optimism.drpc.org",
    30: "https://base.drpc.org",
}
_SEQ = re.compile(r"Program log: Sequence: (\d+)")


def _http(url: str, body: Optional[dict[str, Any]] = None, tries: int = 6) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    last = ""
    for attempt in range(tries):
        req = urllib.request.Request(url, data, {"Content-Type": "application/json", "User-Agent": "forensics-v2"})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = type(e).__name__
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("no answer from %s: %s" % (url.split("?")[0], last))


def bridges_in(programs: list[str]) -> list[str]:
    return sorted(BRIDGE_PROGRAMS[p] for p in programs if p in BRIDGE_PROGRAMS)


def parse_vaa(raw: bytes) -> dict[str, Any]:
    """Header and body of a signed message, by the published layout. Guardian signatures are counted, not checked."""
    n = raw[5]
    body = raw[6 + 66 * n :]
    return {
        "version": raw[0],
        "guardian_set": int.from_bytes(raw[1:5], "big"),
        "signatures": n,
        "timestamp": int.from_bytes(body[:4], "big"),
        "emitter_chain": int.from_bytes(body[8:10], "big"),
        "emitter_hex": body[10:42].hex(),
        "sequence": int.from_bytes(body[42:50], "big"),
    }


def source_proof(tx: dict[str, Any], op: dict[str, Any]) -> dict[str, Any]:
    """Do the Solana transaction's own logs and accounts carry the message the indexer names?"""
    logs = tx["meta"].get("logMessages") or []
    seqs = [int(s) for line in logs for s in _SEQ.findall(line)]
    emitter_hex = (
        op["emitterAddress"]["hex"].lower().removeprefix("0x")
        if isinstance(op.get("emitterAddress"), dict)
        else str(op.get("emitterAddress")).lower()
    )
    keys = {D.b58decode(k).hex() for k in D.account_keys(tx)}
    ok_seq = int(op["sequence"]) in seqs
    ok_emitter = emitter_hex in keys
    return {
        "sequence_in_logs": ok_seq,
        "emitter_in_accounts": ok_emitter,
        "evidence": ONCHAIN if ok_seq and ok_emitter else INDEXER,
    }


def destination_proof(chain: Optional[int], tx_hash: Optional[str]) -> dict[str, Any]:
    if not tx_hash:
        return {"tx": None, "evidence": NOT_FOUND, "note": "no arrival known to the indexer"}
    rpc = EVM_RPC.get(chain or 0)
    if rpc is None:
        return {"tx": tx_hash, "evidence": INDEXER, "note": "no public node configured for chain %s" % chain}
    r = _http(rpc, {"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx_hash]}).get("result")
    if not r:
        return {
            "tx": tx_hash,
            "evidence": INDEXER,
            "note": "node returned no receipt, which an old transaction can also get from a pruned node",
        }
    return {
        "tx": tx_hash,
        "evidence": ONCHAIN if r["status"] == "0x1" else INDEXER,
        "status": r["status"],
        "block": int(r["blockNumber"], 16),
        "to": r["to"],
    }


def prove(signature: str, tx: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Every level of proof available for one Solana transaction, each with what it rests on."""
    if tx is None:
        reply = _http(
            SOLANA_RPC,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [signature, {"encoding": "json", "maxSupportedTransactionVersion": 1}],
            },
        )
        tx = reply.get("result")
        if tx is None:
            raise RuntimeError("transaction not returned by the public node: unknown, not absent")
    d = D.decode(tx)
    out: dict[str, Any] = {
        "signature": signature,
        "slot": d.slot,
        "block_time": d.block_time,
        "ok": d.ok,
        "fee_payer": d.fee_payer,
        "bridge_programs": bridges_in(d.programs),
        "bridge_evidence": ONCHAIN if bridges_in(d.programs) else NOT_FOUND,
        "messages": [],
    }
    if not any(b.startswith(("wormhole", "mayan")) for b in out["bridge_programs"]):
        return out
    for op in _http(WORMHOLESCAN % signature).get("operations") or []:
        std = op.get("content", {}).get("standarizedProperties", {})
        tgt = op.get("targetChain") or {}
        vaa = parse_vaa(base64.b64decode(op["vaa"]["raw"])) if op.get("vaa", {}).get("raw") else None
        out["messages"].append(
            {
                "id": op["id"],
                "apps": std.get("appIds"),
                "to_chain": std.get("toChain"),
                "to_address": std.get("toAddress"),
                "token_address": std.get("tokenAddress"),
                "amount": std.get("amount"),
                "indexer_evidence": INDEXER,
                "source": source_proof(tx, op),
                "vaa": vaa,
                "vaa_matches_id": bool(vaa)
                and "%d/%s/%d" % (vaa["emitter_chain"], vaa["emitter_hex"], vaa["sequence"]) == op["id"],
                "destination": destination_proof(tgt.get("chainId"), (tgt.get("transaction") or {}).get("txHash")),
            }
        )
    return out


def scan(folder: str) -> dict[str, Any]:
    """Program ids searched as text in each raw file, no JSON parsing: fast, one file in memory at a time."""
    hits: Counter[str] = Counter()
    sigs: dict[str, list[str]] = {}
    n = 0
    needles = list(BRIDGE_PROGRAMS)
    with os.scandir(folder) as it:
        for e in it:
            if not e.name.endswith(".json"):
                continue
            n += 1
            with open(e.path) as f:
                text = f.read()
            for p in needles:
                if p in text:
                    hits[BRIDGE_PROGRAMS[p]] += 1
                    sigs.setdefault(BRIDGE_PROGRAMS[p], []).append(e.name[:-5])
    return {"files_read": n, "hits": dict(hits), "signatures": sigs}


def main() -> int:
    if sys.argv[1] == "prove":
        print(json.dumps(prove(sys.argv[2]), indent=1))
    else:
        print(json.dumps(scan(sys.argv[2]), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
