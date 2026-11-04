"""One whole day of gateway payouts, to measure a burst in its own day's traffic.

    python -m forensics_v2.investigations.gateway_day 2024-12-13 <amount_lamports> <credits>
Prints and writes aggregates only: forensics_v2/reports/nine_wallets/gateway_day_<date>.json.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

from .. import decode as D
from ..__main__ import client
from .gateway_bursts import GAP_S, MIN_SIZE, bursts_of

G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"
OUT = Path(__file__).resolve().parents[1] / "reports" / "nine_wallets"


def main() -> int:
    day, amount, credits = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    t0 = int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp())
    c = client(credits)
    raw, walk = c.history_txs(G2Y, t0, t0 + 86399, "none", max_pages=credits // 10)
    pays = []
    for tx in raw:
        d = D.decode(tx)
        for e in d.edges:
            if e.src == G2Y and e.lamports >= 10**9:
                pays.append({"sig": d.signature, "slot": d.slot, "t": d.block_time, "to": e.dst, "lam": e.lamports,
                             "evidence": e.evidence})
    bursts = bursts_of(pays)
    amt = [p for p in pays if p["lam"] == amount]
    group = set(json.loads((OUT / "group15.json").read_text())["group"])
    in_group = [p for p in amt if p["to"] in group]
    t_g = sorted(p["t"] for p in in_group)
    window = [p for p in pays if t_g and t_g[0] <= p["t"] <= t_g[-1]]
    window_amt = [p for p in window if p["lam"] == amount]
    res = {
        "day": day, "complete": walk.complete, "stop": walk.stop, "pages": walk.pages, "transactions": len(raw),
        "payouts_at_least_1_sol": len(pays), "distinct_amounts": len({p["lam"] for p in pays}),
        "payouts_at_this_amount": len(amt), "recipients_at_this_amount": len({p["to"] for p in amt}),
        "of_which_the_group": len(in_group), "group_seen_at_this_amount": len({p["to"] for p in in_group}),
        "group_first_utc": dt.datetime.fromtimestamp(t_g[0], dt.timezone.utc).isoformat() if t_g else None,
        "group_span_s": (t_g[-1] - t_g[0]) if t_g else None,
        "payouts_all_amounts_during_group_span": len(window),
        "payouts_this_amount_during_group_span": len(window_amt),
        "not_group_this_amount_during_group_span": len([p for p in window_amt if p["to"] not in group]),
        "bursts_rule": {"min_size": MIN_SIZE, "gap_s": GAP_S}, "bursts_that_day": len(bursts),
        "largest_bursts": sorted((len(b["members"]) for b in bursts), reverse=True)[:8],
        "burst_of_this_amount_sizes": [len(b["members"]) for b in bursts if b["lam"] == amount],
        "top_amounts": Counter(p["lam"] for p in pays).most_common(6),
        "net_calls": c.net_calls,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("gateway_day_%s.json" % day)).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
