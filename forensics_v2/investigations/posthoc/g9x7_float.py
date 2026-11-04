"""Is the fleet's loop a treasury or a service's float? Reads the hub in fixed windows and counts where its SOL comes from and goes.

Written after the loop was found and before these windows were read. If most of what enters and leaves is the loop itself, that fits a
treasury. If most comes from and goes to wallets outside it, that fits a busy service, and the loop says little.

    python -m forensics_v2.investigations.posthoc.g9x7_float <credits>
"""
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

from ...__main__ import client
from ...trace import history, sol_flows
from .fleet_vs_gateway import OUT

HUB = "G9X7F4JzLzbSGMCndiBdWNi5YzZZakmtkdwq7xS3Q3FE"
RING = {"ERGbjcz9fs95YKvM6zXqvEaicK4VPPo2JwNV8beGKZM4", "AwzntLkaND9bq6CBrB4gAyUb41KBePj4TofdTeMXbKyL"}
DAYS = ["2024-11-21", "2024-11-28", "2024-12-05", "2024-12-12", "2024-12-14", "2024-12-16"]
LAMPORTS_MIN = 10_000_000


def main():
    c = client(int(sys.argv[1]))
    rows = []
    src_all, dst_all = Counter(), Counter()
    for day in DAYS:
        t0 = int(dt.datetime.fromisoformat(day + "T12:00:00+00:00").timestamp())
        h = history(c, HUB, t_from=t0, t_to=t0 + 3600, token_accounts="none", max_pages=1)
        flows, _ = sol_flows(h)
        inn = [f for f in flows if f.dst == HUB and f.lamports >= LAMPORTS_MIN]
        out = [f for f in flows if f.src == HUB and f.lamports >= LAMPORTS_MIN]
        src_all.update({f.src: f.lamports for f in inn})
        dst_all.update({f.dst: f.lamports for f in out})
        back = {f.src for f in inn} & {f.dst for f in out}
        rows.append({"day": day, "tx": len(h.txs), "span_s": (h.txs[-1].block_time - h.txs[0].block_time) if h.txs else 0, "in_sol": sum(f.lamports for f in inn) / 1e9,
                     "in_from_loop_sol": sum(f.lamports for f in inn if f.src in RING) / 1e9, "out_sol": sum(f.lamports for f in out) / 1e9,
                     "out_to_loop_sol": sum(f.lamports for f in out if f.dst in RING) / 1e9, "sources": len({f.src for f in inn}), "destinations": len({f.dst for f in out}),
                     "both_ways": len(back)})
        print(rows[-1], flush=True)
    total_in, total_out = sum(r["in_sol"] for r in rows), sum(r["out_sol"] for r in rows)
    res = {"hub": HUB, "windows": rows, "in_sol": round(total_in, 3), "out_sol": round(total_out, 3), "share_in_from_loop": round(sum(r["in_from_loop_sol"] for r in rows) / total_in, 4) if total_in else None,
           "share_out_to_loop": round(sum(r["out_to_loop_sol"] for r in rows) / total_out, 4) if total_out else None, "top_sources": [[a, round(v / 1e9, 3)] for a, v in src_all.most_common(5)],
           "top_destinations": [[a, round(v / 1e9, 3)] for a, v in dst_all.most_common(5)], "net_calls": c.net_calls}
    (Path(OUT) / "hub_float.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "windows"}))


if __name__ == "__main__":
    main()
