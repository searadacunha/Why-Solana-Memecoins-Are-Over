"""Are the published nine inside the rebuilt fifteen? Each credit read twice, from two independent sources.

Source A: the raw transaction in this engine's cache, read only, no credit. Source B: the public Solana RPC, no key, no credit.
Published list: docs/PATTERN.md section 2.1. Historical collections: data/split/all_buyers_g2y.json, data/trace_h2w6/e6_courbe_acheteurs.json.

    python -m forensics_v2.investigations.posthoc.nine_reconcile
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ... import storage

G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"
AMOUNT = 2_976_815_600
SYSTEM = "11111111111111111111111111111111"
PUBLIC_RPC = "https://api.mainnet-beta.solana.com"
REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "forensics_v2/reports/nine_wallets"


def public_rpc(method: str, params: list[Any]) -> Any:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(8):
        req = urllib.request.Request(PUBLIC_RPC, data=body, headers={"Content-Type": "application/json", "User-Agent": "forensics-v2"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
            if "result" in d and d["result"] is not None:
                time.sleep(1.2)  # the public endpoint's own limit
                return d["result"]
        except OSError:
            pass
        time.sleep(4 * (attempt + 1))
    raise RuntimeError("public RPC did not answer %s" % method)


def read_credit(tx: dict[str, Any], wallet: str) -> dict[str, Any]:
    """What the raw transaction itself says, from its account keys, balances and first-level instructions."""
    msg = tx["transaction"]["message"]
    keys = list(msg["accountKeys"]) + tx["meta"].get("loadedAddresses", {}).get("writable", []) + tx["meta"].get("loadedAddresses", {}).get("readonly", [])
    pre, post = tx["meta"]["preBalances"], tx["meta"]["postBalances"]
    w, g = keys.index(wallet), keys.index(G2Y)
    transfers = []
    for pos, ins in enumerate(msg["instructions"]):
        if keys[ins["programIdIndex"]] != SYSTEM:
            continue
        raw = _b58decode(ins["data"])
        if len(raw) == 12 and int.from_bytes(raw[:4], "little") == 2:
            transfers.append({"position": pos, "from": keys[ins["accounts"][0]], "to": keys[ins["accounts"][1]],
                              "lamports": int.from_bytes(raw[4:], "little")})
    return {"signature": tx["transaction"]["signatures"][0], "slot": tx["slot"], "block_time": tx["blockTime"],
            "ok": tx["meta"]["err"] is None, "fee_payer": keys[0],
            "signers": keys[:msg["header"]["numRequiredSignatures"]],
            "wallet_pre": pre[w], "wallet_post": post[w], "gateway_delta": post[g] - pre[g], "fee": tx["meta"]["fee"], "system_transfers": transfers}


def _b58decode(s: str) -> bytes:
    alpha = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = 0
    for c in s:
        n = n * 58 + alpha.index(c)
    return n.to_bytes((n.bit_length() + 7) // 8, "big")


def main() -> int:
    published = re.findall(r"\| `(\w{32,44})` \| 2\.976815600 \| (\d\d:\d\d:\d\d) \|", (REPO / "docs/PATTERN.md").read_text())
    assert len(published) == 9, len(published)
    detail = json.loads((OUT / "group15_detail.json").read_text())
    assert len(detail["credits"]) == 15
    hist = json.loads((REPO / "data/split/all_buyers_g2y.json").read_text())["h2w6gm6jz"]
    e6 = json.loads((REPO / "data/trace_h2w6/e6_courbe_acheteurs.json").read_text())["rang_par_wallet"]
    db = sqlite3.connect("file:%s?mode=ro" % (storage.data_root() / "rpc_raw/tx.sqlite"), uri=True, timeout=120)
    rows = []
    for c in sorted(detail["credits"], key=lambda x: x["slot"]):
        w, sig = c["wallet"], c["sig"]
        hit = db.execute("SELECT body FROM tx WHERE sig = ?", (sig,)).fetchone()
        a = read_credit(json.loads(zlib.decompress(hit[0])), w) if hit else None
        b = read_credit(public_rpc("getTransaction", [sig, {"encoding": "json", "maxSupportedTransactionVersion": 1}]), w)
        sigs = public_rpc("getSignaturesForAddress", [w, {"limit": 1000}])
        direct = [t for t in b["system_transfers"] if t["from"] == G2Y and t["to"] == w]
        row = {"wallet": w, "in_published_nine": w in dict(published), "published_time": dict(published).get(w),
               "credit_signature": sig, "slot": b["slot"], "utc": datetime.fromtimestamp(b["block_time"], timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
               "funder": direct[0]["from"] if len(direct) == 1 else None, "fee_payer": b["fee_payer"], "signers": b["signers"],
               "lamports": direct[0]["lamports"] if len(direct) == 1 else None,
               "wallet_balance_before": b["wallet_pre"], "wallet_balance_after": b["wallet_post"], "instruction_position": direct[0]["position"] if direct else None,
               "other_system_transfers_in_tx": len(b["system_transfers"]) - len(direct),
               "transactions_of_wallet": len(sigs), "first_transaction_is_this_credit": len(sigs) < 1000 and sigs[-1]["signature"] == sig,
               "source_a_equals_source_b": a == b if a else None,
               "historical_curve_buyer_rank_e6": e6.get(w), "in_historical_portefeuilles": w in hist["portefeuilles"]}
        print(row["wallet"][:8], row["utc"], row["lamports"], row["funder"][:6], row["fee_payer"][:6], row["wallet_balance_before"], row["first_transaction_is_this_credit"], row["source_a_equals_source_b"], row["in_published_nine"], flush=True)
        rows.append(row)
    nine = [r for r in rows if r["in_published_nine"]]
    t = lambda r: datetime.strptime(r["utc"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()  # noqa: E731
    span15, span9 = t(rows[-1]) - t(rows[0]), t(nine[-1]) - t(nine[0])
    result = {
        "published": {"source": "docs/PATTERN.md 2.1, README Act I, docs/out/a9_g2y_prelaunch.json", "n": 9, "span_s": 343},
        "rebuilt": {"n": len(rows), "span_s": int(span15), "first": rows[0]["utc"], "last": rows[-1]["utc"]},
        "published_inside_rebuilt": sum(r["in_published_nine"] for r in rows), "published_times_match_chain": all(r["published_time"] == r["utc"][-8:] for r in nine),
        "published_span_recomputed_s": int(span9),
        "seconds_added_by_first_wallet": int(t(nine[0]) - t(rows[0])), "wallets_before_published_window": [r["wallet"] for r in rows if t(r) < t(nine[0])],
        "wallets_inside_published_window_not_published": [r["wallet"] for r in rows if not r["in_published_nine"] and t(nine[0]) <= t(r) <= t(nine[-1])],
        "all_exact_amount": all(r["lamports"] == AMOUNT for r in rows), "all_from_gateway": all(r["funder"] == G2Y for r in rows),
        "fee_payers": sorted({r["fee_payer"] for r in rows}), "signer_sets": sorted({"+".join(r["signers"]) for r in rows}),
        "all_first_transaction": all(r["first_transaction_is_this_credit"] for r in rows), "all_empty_before": all(r["wallet_balance_before"] == 0 for r in rows),
        "sources_agree": [r["source_a_equals_source_b"] for r in rows].count(True), "sources_absent_from_cache": [r["source_a_equals_source_b"] for r in rows].count(None),
        "six_in_historical_curve_buyers": sum(r["historical_curve_buyer_rank_e6"] is not None for r in rows if not r["in_published_nine"]),
        "six_in_historical_portefeuilles": sum(r["in_historical_portefeuilles"] for r in rows if not r["in_published_nine"]),
        "historical_counts": {k: hist[k] for k in ("n_acheteurs_distincts", "n_vierges", "n_illisibles", "n_vierges_finances_G2Y_avant_token")},
        "wallets": rows,
    }
    (OUT / "reconciliation.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "wallets"}, indent=1))
    assert result["published_inside_rebuilt"] == 9 and result["published_span_recomputed_s"] == 343
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
