"""Who deployed the fleet's nine tokens, and did the fleet's money ever reach them? Kept as run; written after the report's first version.

    python -m forensics_v2.investigations.posthoc.nine_deployers <credits>
"""
import json
import sys
from collections import Counter
from pathlib import Path

from ...__main__ import client
from ...trace import history, sol_flows
from ..trade_context import read_mint

OUT = Path(__file__).resolve().parents[2] / "reports" / "nine_wallets"
d = json.loads((OUT / "group15_detail.json").read_text())
c = client(int(sys.argv[1]))
fleet = {r["wallet"] for r in d["credits"]}
rows, cache = [], {}
for tok in d["tokens"]:
    m = read_mint(c, tok["mint"], 10**12, cache)
    creator = m.get("creator")
    row = {"mint": tok["mint"], "creator": creator, "t_create": m.get("t_create"), "creator_is_fleet": creator in fleet, "first_events": len(m["events"])}
    if creator:
        h = history(c, creator, token_accounts="none", max_pages=2)
        flows, _ = sol_flows(h)
        row["creator_tx_read"] = len(h.txs)
        row["creator_receives_from_fleet_lamports"] = sum(f.lamports for f in flows if f.dst == creator and f.src in fleet)
        row["creator_sends_to_fleet_lamports"] = sum(f.lamports for f in flows if f.src == creator and f.dst in fleet)
        row["creator_first_funder"] = next((f.src for f in flows if f.dst == creator), None)
    rows.append(row)
res = {"tokens": rows, "distinct_creators": len({r["creator"] for r in rows}), "creators_seen_twice": [k for k, n in Counter(r["creator"] for r in rows).items() if n > 1],
       "net_calls": c.net_calls}
(OUT / "fleet_deployers.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps({k: v for k, v in res.items() if k != "tokens"}))
for r in rows:
    print(r["mint"][:8], (r["creator"] or "")[:8], r["creator_is_fleet"], r.get("creator_receives_from_fleet_lamports"), r.get("creator_sends_to_fleet_lamports"), (r.get("creator_first_funder") or "")[:8])
