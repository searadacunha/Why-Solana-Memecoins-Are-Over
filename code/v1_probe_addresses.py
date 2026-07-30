"""
v1_probe_addresses.py — existence and activity profile of every address the
dossier is tempted to cite as "upstream infrastructure".

For each address, MEASURED on-chain (Helius):
  exists        : getAccountInfo != null OR at least 1 signature
  owner         : account owner program (11111... = plain system wallet)
  lamports      : current balance
  sigs_p1       : signatures returned on the first page (cap 1000)
  span_p1_s     : wall-clock span covered by that first page, in seconds
  tx_per_day_p1 : sigs_p1 / span_p1 extrapolated  (only meaningful if saturated)
  newest_ts     : block time of the most recent signature
  payers/payees : distinct counterparties over the last 100 parsed transactions
                  (fan-in / fan-out shape — an exchange hot wallet has hundreds
                  of both and never stops; a burner dispatcher does not)

Output: data/v1_addresses.json + a printed table.
Usage: python3 v1_probe_addresses.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hlib  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "v1_addresses.json")

# claim = the note that cites the address; nothing here is assumed true.
TARGETS = {
    # --- mass dispatchers claimed in the May 2026 investigation notes
    "C2xnFBhKJ4TCQAPnyistMq2j9mYRMR9NvMcwVm36sff5": "note C2xn: 2000+ wallets funded in ~4 min (15/05/2026)",
    "Mihso7kXXNPb7GUZ71H7MedYrpW88MTQFdLKrtAnDvj": "note price_movers: root operator OX, funds 2 dispatchers",
    "4KHPw3QDsXe6HFJPNA4SiBi6Qe3mrziDFgyYToeEWGu4": "note price_movers: dispatcher A (194 wallets / 7 s)",
    "4NyVM3epZLVRnUbHp5H7NrSP53nMU2kLMymhHm6TyUwS": "note price_movers: dispatcher B (194 wallets / 7 s)",
    "odinXyAgz4ZUKgzXX84Artjyu3LiiqsBMVYFQthHDb1": "note odinx: dispatcher L1 (vanity odinX)",
    "odinKoMSVpxrJUZDNQotqk8GejBmfg5YCPehjy5wQFq": "note odinx: dispatcher L2 (vanity odinK)",
    "oDinBoTPS3Pz5gBv3FSTkPZXTyN3v7bZo6A2b3dooNP": "note odinx: dispatcher L3 (vanity oDinBoT)",
    "9obNtb5GyUegcs3a1CbBkLuc5hEWynWfJC6gjz5uWQkE": "note odinx: terminal funder",
    # --- claimed cash-out convergence chain
    "ExsX51TQbabuHnup9bVkH84tZda1mrPAYQPXHcWPv7Cy": "note consolidation: L1 cash-out hub (19/19 snipers)",
    "6x9ARWcPTKDWPN8xSYS3WYQ7o5vLBnELtuF9o2gSy44X": "note consolidation: L2 hub",
    "is6MTRHEgyFLNTfYcuV4QBWLjrZBfmhVNYR6ccgr8KV": "note consolidation: L3 hub / also tagged OKX Hot Wallet 1",
    "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6": "note consolidation: KuCoin 2 capital entry",
    # --- shared genesis funders found by the 29/07 memecoin forensic
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "forensic: shared genesis, 6-7 fleets, tagged Binance 2 / HUB DBR",
    "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w": "forensic: shared genesis, tagged Gate.io hot",
    "iGdFcQoyR2MwbXMHQskhmNsqddZ6rinsipHc4TNSdwu": "forensic: shared genesis, tagged HUB DBR",
    "BY4StcU9Y2BpgH8quZzorg31EGE4L1rjomN8FNsCBEcx": "forensic: shared genesis, 3 fleets",
    "H3Kv11CBrCR6qbHTLbzAMUgmZyVAaFmxnWHmnsyrZ8cs": "forensic: only inter-quad bridge (F002 and F003), undecided",
}


def retry(fn, ok, n=5):
    """Helius free tier drops calls under load; a null answer is not evidence."""
    v = None
    for _ in range(n):
        v = fn()
        if ok(v):
            return v
        time.sleep(1.5)
    return v


def profile(addr):
    d = {"address": addr, "claim": TARGETS[addr], "b58_valid": hlib.is_b58_pubkey(addr)}
    if not d["b58_valid"]:
        d["exists"] = False
        d["note"] = "not a valid base58 32-byte pubkey -> transcription error in the source note"
        return d
    ai = retry(lambda: hlib.account_info(addr), lambda v: isinstance(v, dict) and v.get("value"))
    val = ai.get("value") if isinstance(ai, dict) else None
    d["lamports"] = val.get("lamports") if val else 0
    d["owner"] = val.get("owner") if val else None
    d["executable"] = val.get("executable") if val else None
    s = retry(lambda: hlib.sigs(addr, 1000), lambda v: len(v) > 0)
    d["sigs_p1"] = len(s)
    d["saturated_1000"] = len(s) >= 1000
    ts = [x.get("blockTime") for x in s if x.get("blockTime")]
    if ts:
        d["newest_ts"] = max(ts)
        d["oldest_ts_p1"] = min(ts)
        d["span_p1_s"] = max(ts) - min(ts)
        d["tx_per_day_p1"] = round(len(s) / max(1, (max(ts) - min(ts))) * 86400, 1)
    d["exists"] = bool(val) or len(s) > 0
    tx = retry(lambda: hlib.enhanced(addr, 100), lambda v: len(v) > 0)
    payers, payees, sol_out = set(), set(), 0.0
    for t in tx:
        for nt in t.get("nativeTransfers") or []:
            if nt.get("fromUserAccount") == addr:
                payees.add(nt.get("toUserAccount"))
                sol_out += (nt.get("amount") or 0) / 1e9
            elif nt.get("toUserAccount") == addr:
                payers.add(nt.get("fromUserAccount"))
        for tt in t.get("tokenTransfers") or []:
            if tt.get("fromUserAccount") == addr:
                payees.add(tt.get("toUserAccount"))
            elif tt.get("toUserAccount") == addr:
                payers.add(tt.get("fromUserAccount"))
    d["enh_n"] = len(tx)
    d["distinct_payees_100tx"] = len(payees)
    d["distinct_payers_100tx"] = len(payers)
    d["sol_out_100tx"] = round(sol_out, 3)
    return d


def main():
    out = []
    for a in TARGETS:
        p = profile(a)
        out.append(p)
        print(
            "%-46s exists=%-5s sigs_p1=%-5s span_s=%-8s payees=%-4s payers=%-4s solout=%s"
            % (
                a[:44],
                p.get("exists"),
                p.get("sigs_p1"),
                p.get("span_p1_s"),
                p.get("distinct_payees_100tx"),
                p.get("distinct_payers_100tx"),
                p.get("sol_out_100tx"),
            )
        )
        time.sleep(0.15)
    with open(OUT, "w") as f:
        json.dump({"generated_ts": int(time.time()), "rows": out}, f, indent=1)
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
