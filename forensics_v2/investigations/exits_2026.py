"""The 2026 groups' sales and exits through the new engine, against the frozen tables. Plan: docs/PLAN_exits_2026.md.

python -m forensics_v2.investigations.exits_2026 <credits>
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from .. import decode as D
from ..__main__ import client
from ..crosschain import bridges_in
from ..rpc import RpcError

SEED = 20261103
LIMIT = int(dt.datetime(2026, 9, 22, tzinfo=dt.timezone.utc).timestamp())
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "forensics_v2/reports/exits_2026"


def events() -> list[dict[str, Any]]:
    with gzip.open(REPO / "exit_destination/derived/ed_table.json.gz", "rt") as f:
        wallets = json.load(f)["wallets"]
    return [e for w in wallets for e in w["events"] if e["reads"] and max(r["bt"] for r in e["reads"]) < LIMIT]


def compare_read(read: dict[str, Any], d: D.Decoded, wallet: str) -> list[str]:
    """What the frozen parser recorded against this engine's reading of the raw transaction. Empty means they agree."""
    bad = []
    # The frozen table's dsol adds the fee back when the wallet signs (exit_destination/code/ed_trace.py:175). The first run of this
    # comparison missed that and disagreed on 292 of 427, each by exactly the fee: amendment in DECISIONS.md 17.
    native = d.lamport_delta.get(wallet, 0) + (d.fee if d.fee_payer == wallet else 0)
    n = d.owners.get(wallet)
    wsol = n.wsol if n else 0
    if abs((native + wsol) - round((read["dsol"] + read.get("dws", 0.0)) * 1e9)) > 2:
        bad.append("sol %d against %s" % (native + wsol, read["dsol"]))
    toks = D.traded_mints(d, wallet)
    for mint, ui in read["dtok"].items():
        dec = next((t.decimals for t in d.token_accounts.values() if t.mint == mint and t.decimals is not None), 6)
        if abs(toks.get(mint, 0) - round(ui * 10**dec)) > 1000:  # the table keeps floats, at most 3 raw units per 1e15
            bad.append("token %s %d against %s" % (mint[:8], toks.get(mint, 0), ui))
    for dst, sol in read.get("out", []):
        found = sum(e.lamports for e in d.edges if e.src == wallet and e.dst == dst)
        if abs(found - round(sol * 1e9)) > 2:
            bad.append("sweep to %s: %d against %s" % (dst[:8], found, sol))
    return bad


def main() -> int:
    c = client(int(sys.argv[1]))
    ev = events()
    rng = random.Random(SEED)
    done = sorted((e for e in ev if e["status"] == "complete"), key=lambda e: (e["wallet"], e["mint"]))
    capped = sorted((e for e in ev if e["status"] == "cap"), key=lambda e: (e["wallet"], e["mint"]))
    val, ext = rng.sample(done, 100), rng.sample(capped, 40)
    n, disagreements, n_tx = 0, [], 0
    for e in val:
        for r in e["reads"]:
            d = D.decode(c.tx(r["sig"]))
            n_tx += 1
            if r["err"] != (not d.ok):
                disagreements.append({"sig": r["sig"], "why": "ok flag"})
                continue
            bad = compare_read(r, d, e["wallet"]) if d.ok else []
            n += not bad
            if bad:
                disagreements.append({"sig": r["sig"], "wallet": e["wallet"], "why": bad})
    rows = []
    bridges: Counter[str] = Counter()
    stopped = None
    for e in ext:
        t0, t1 = min(r["bt"] for r in e["reads"]), LIMIT - 1
        try:
            raw, walk = c.history_txs(e["wallet"], t0, min(t1, t0 + 3 * 86400), "none", max_pages=3)
        except RpcError as x:  # credits or quota: keep what was read
            stopped = str(x)[:120]
            break
        sold = sol_in = sweep = 0
        dests: Counter[str] = Counter()
        for tx in raw:
            d = D.decode(tx)
            if not d.ok:
                continue
            bridges.update(bridges_in(d.programs))
            delta = D.traded_mints(d, e["wallet"]).get(e["mint"], 0)
            if delta < 0 and d.lamport_delta.get(e["wallet"], 0) > 0:
                sold += 1
                sol_in += d.lamport_delta[e["wallet"]]
            for ed in d.edges:
                if ed.src == e["wallet"] and not D.traded_mints(d, e["wallet"]):
                    sweep += ed.lamports
                    dests[ed.dst] += ed.lamports
        old_sales = [r for r in e["reads"] if r["dtok"].get(e["mint"], 0) < 0 and r["dsol"] > 0]
        old_dest = {o[0] for r in e["reads"] for o in r.get("out", [])}
        rows.append(
            {
                "wallet": e["wallet"],
                "mint": e["mint"],
                "pages_complete": walk.complete,
                "transactions": len(raw),
                "sales_new": sold,
                "sales_table": len(old_sales),
                "sol_from_sales_new": sol_in / 1e9,
                "sol_from_sales_table": sum(r["dsol"] for r in old_sales),
                "swept_sol_new": sweep / 1e9,
                "top_destination": dests.most_common(1)[0][0] if dests else None,
                "table_destinations": sorted(old_dest),
            }
        )
    same_dest = [r for r in rows if r["top_destination"] and r["table_destinations"]]
    res = {
        "seed": SEED,
        "first_run_before_fee_convention": {"agree": 135, "disagree": 292, "all_by_exactly_the_fee": True},
        "destination_matches_table": {
            "compared": len(same_dest),
            "same": sum(r["top_destination"] in r["table_destinations"] for r in same_dest),
            "new_where_table_had_none": sum(1 for r in rows if r["top_destination"] and not r["table_destinations"]),
        },
        "validation": {
            "events": len(val),
            "transactions": n_tx,
            "agree": n,
            "disagree": len(disagreements),
            "share": round(n / n_tx, 5) if n_tx else None,
            "passes_99": bool(n_tx) and n / n_tx >= 0.99,
            "disagreements": disagreements[:40],
        },
        "extension": {
            "events_read": len(rows),
            "stopped": stopped,
            "hidden_sales": sum(r["sales_new"] - r["sales_table"] for r in rows),
            "hidden_sol": round(sum(r["sol_from_sales_new"] - r["sol_from_sales_table"] for r in rows), 4),
            "sales_table": sum(r["sales_table"] for r in rows),
            "sol_table": round(sum(r["sol_from_sales_table"] for r in rows), 4),
            "bridge_transactions": dict(bridges),
            "rows": rows,
        },
        "net_calls": c.net_calls,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(res, indent=1) + "\n")
    print(
        json.dumps({k: v for k, v in res["validation"].items() if k != "disagreements"}),
        {k: v for k, v in res["extension"].items() if k != "rows"},
        res["net_calls"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
