"""
v2_dispatcher_burst.py: geometry of a mass-funding burst.

For each address given, walks the whole signature history
(getSignaturesForAddress, paged backwards) and the whole parsed history
(Helius enhanced, paged backwards), then measures:

  n_sig_total        total signatures over the account's whole life
  life_s             last_ts - first_ts (seconds)
  n_recipients       distinct addresses that received SOL from this address
  burst_window_s     shortest window containing 90% of the outgoing transfers
  ticket_median_sol  median outgoing amount
  sol_out_total      total SOL sent
  first_ts/last_ts   epoch seconds of the first and last transfer

Recipient sets are written out so that any two dispatchers can be compared
(Jaccard) without re-fetching.

Usage: python3 v2_dispatcher_burst.py [address ...]
Default set = the addresses the May-2026 notes call "mass dispatchers".
Output: data/v2_burst_<addr8>.json and data/v2_burst_summary.json
"""
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hlib  # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

DEFAULT = [
    "4KHPw3QDsXe6HFJPNA4SiBi6Qe3mrziDFgyYToeEWGu4",
    "4NyVM3epZLVRnUbHp5H7NrSP53nMU2kLMymhHm6TyUwS",
    "C2xnFBhKJ4TCQAPnyistMq2j9mYRMR9NvMcwVm36sff5",
    "odinXyAgz4ZUKgzXX84Artjyu3LiiqsBMVYFQthHDb1",
]
MAX_PAGES = 120  # 12 000 parsed tx per address, hard stop


def all_sigs(addr, cap=60000):
    out, before = [], None
    while len(out) < cap:
        page = hlib.sigs(addr, 1000, before)
        if not page:
            break
        out += page
        before = page[-1]["signature"]
        if len(page) < 1000:
            break
    return out


def all_enhanced(addr):
    out, before = [], None
    for _ in range(MAX_PAGES):
        page = hlib.enhanced(addr, 100, before)
        if not page:
            break
        out += page
        before = page[-1]["signature"]
        if len(page) < 100:
            break
        time.sleep(0.05)
    return out


def shortest_window(ts, frac=0.90):
    """Shortest time window containing frac of the events."""
    if not ts:
        return None
    ts = sorted(ts)
    k = max(1, int(len(ts) * frac))
    return min(ts[i + k - 1] - ts[i] for i in range(0, len(ts) - k + 1))


def run(addr):
    s = all_sigs(addr)
    tx = all_enhanced(addr)
    outs = []  # (ts, to, sol)
    for t in tx:
        ts = t.get("timestamp")
        for nt in t.get("nativeTransfers") or []:
            if nt.get("fromUserAccount") == addr and (nt.get("amount") or 0) > 0:
                outs.append((ts, nt.get("toUserAccount"), (nt["amount"]) / 1e9))
    rec = {}
    for ts, to, sol in outs:
        r = rec.setdefault(to, {"n": 0, "sol": 0.0, "first_ts": ts})
        r["n"] += 1
        r["sol"] += sol
        r["first_ts"] = min(r["first_ts"], ts) if r["first_ts"] else ts
    sts = [x.get("blockTime") for x in s if x.get("blockTime")]
    amts = [o[2] for o in outs]
    d = {
        "address": addr,
        "n_sig_total": len(s),
        "sig_first_ts": min(sts) if sts else None,
        "sig_last_ts": max(sts) if sts else None,
        "life_s": (max(sts) - min(sts)) if sts else None,
        "n_parsed_tx": len(tx),
        "parsed_pages_capped": len(tx) >= MAX_PAGES * 100,
        "n_out_transfers": len(outs),
        "n_recipients": len(rec),
        "sol_out_total": round(sum(amts), 4),
        "ticket_median_sol": round(statistics.median(amts), 6) if amts else None,
        "ticket_min_sol": round(min(amts), 6) if amts else None,
        "ticket_max_sol": round(max(amts), 6) if amts else None,
        "out_first_ts": min(o[0] for o in outs) if outs else None,
        "out_last_ts": max(o[0] for o in outs) if outs else None,
        "burst_window_90pct_s": shortest_window([o[0] for o in outs]),
        "recipients_per_tx_mean": round(len(outs) / len(tx), 2) if tx else None,
    }
    with open(os.path.join(DATA, "v2_burst_%s.json" % addr[:8]), "w") as f:
        json.dump({"profile": d, "recipients": rec}, f)
    return d


def main():
    addrs = sys.argv[1:] or DEFAULT
    rows = []
    for a in addrs:
        d = run(a)
        rows.append(d)
        print(json.dumps(d, indent=1))
    with open(os.path.join(DATA, "v2_burst_summary.json"), "w") as f:
        json.dump(rows, f, indent=1)


if __name__ == "__main__":
    main()
