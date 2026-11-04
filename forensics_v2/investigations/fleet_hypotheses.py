"""One operator, a coordinated group, or a shared service? Plan: docs/PLAN_fleet_hypotheses.md. Public addresses only.

python -m forensics_v2.investigations.fleet_hypotheses <burst sample json> <credits>
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from .. import decode as D
from ..__main__ import client
from ..trace import history, load_services, sol_flows

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "forensics_v2/reports/fleet_structure"
AWZ = "AwzntLkaND9bq6CBrB4gAyUb41KBePj4TofdTeMXbKyL"
ERG = "ERGbjcz9fs95YKvM6zXqvEaicK4VPPo2JwNV8beGKZM4"


def labels() -> dict[str, str]:
    """Public labels already in the repository, and this project's service list."""
    text = (ROOT / "data/trace_h2w6/lib_trace.py").read_text()
    out = {a: n for a, n in re.findall(r'"([1-9A-HJ-NP-Za-km-z]{32,44})":\s*"([^"]+)"', text)}
    out.update({a: v["name"] for a, v in load_services().items()})
    return out


def tool_of(c: Any, wallet: str) -> dict[str, Counter[str]]:
    """In this wallet's buys: programs, and accounts it paid under 5 % of what it spent in the same transaction."""
    h = history(c, wallet, token_accounts="none", max_pages=1)
    prog: Counter[str] = Counter()
    fee: Counter[str] = Counter()
    for d in h.txs:
        toks = D.traded_mints(d, wallet)
        if not d.ok or not toks or next(iter(toks.values())) <= 0:
            continue
        spent = -d.lamport_delta.get(wallet, 0)
        prog.update(d.programs)
        for t in d.transfers:
            if t.kind == "sol_transfer" and t.src == wallet and t.dst and 0 < t.amount < spent * 0.05:
                fee[t.dst] += 1
    return {"programs": prog, "fee_accounts": fee}


def path_of(c: Any, start: str, known: dict[str, str]) -> dict[str, Any]:
    h = history(c, start, token_accounts="none", max_pages=2)
    flows, _ = sol_flows(h)
    out: Counter[str] = Counter()
    for f in flows:
        if f.src == start and f.lamports >= 10_000_000:
            out[f.dst] += f.lamports
    top = out.most_common(3)
    second: dict[str, list[list[Any]]] = {}
    if top and top[0][0] not in known:
        h2 = history(c, top[0][0], token_accounts="none", max_pages=1)
        f2, _ = sol_flows(h2)
        o2: Counter[str] = Counter()
        for f in f2:
            if f.src == top[0][0] and f.lamports >= 10_000_000:
                o2[f.dst] += f.lamports
        second[top[0][0]] = [[a, round(v / 1e9, 3), known.get(a)] for a, v in o2.most_common(3)]
    return {
        "wallet": start,
        "tx_read": len(h.txs),
        "complete": h.walk.complete,
        "out_top": [[a, round(v / 1e9, 3), known.get(a)] for a, v in top],
        "second_hop": second,
    }


def main() -> int:
    bursts = json.loads(Path(sys.argv[1]).read_text())["bursts"]
    r = json.loads((OUT / "results.json").read_text())
    known = labels()
    c = client(int(sys.argv[2]))
    groups: list[dict[str, Any]] = []
    fleet = json.loads((ROOT / "forensics_v2/reports/nine_wallets/group15.json").read_text())["group"]
    for s in r["strict_bursts"]:
        members = sorted({m["wallet"] for m in bursts[s["i"]]["members"]})
        groups.append(
            {"name": "burst_%d_%s" % (s["i"], s["day"]), "members": members[:3], "dest": s["destinations_5_wallets"][:1]}
        )
    groups.append({"name": "published_fleet", "members": sorted(fleet)[:3], "dest": [ERG, AWZ]})
    res = []
    for g in groups:
        prog: Counter[str] = Counter()
        fee: Counter[str] = Counter()
        for w in g["members"]:
            t = tool_of(c, w)
            prog += t["programs"]
            fee += t["fee_accounts"]
        res.append(
            {
                "group": g["name"],
                "programs": prog.most_common(8),
                "fee_accounts": [[a, n, known.get(a)] for a, n in fee.most_common(6)],
                "paths": [path_of(c, d, known) for d in g["dest"]],
            }
        )
        print(g["name"], "net", c.net_calls, flush=True)
    sets = {}
    for g in res:
        s = set()
        for p in g["paths"]:
            s.add(p["wallet"])
            s.update(a for a, _, lab in p["out_top"] if not lab)
            for rows in p["second_hop"].values():
                s.update(a for a, _, lab in rows if not lab)
        sets[g["group"]] = s
    names = list(sets)
    joins = [
        {"a": x, "b": y, "shared": sorted(sets[x] & sets[y])}
        for i, x in enumerate(names)
        for y in names[i + 1 :]
        if sets[x] & sets[y]
    ]
    fee_groups: Counter[str] = Counter(a for g in res for a, _, _ in g["fee_accounts"])
    out = {
        "plan": "docs/PLAN_fleet_hypotheses.md",
        "groups": res,
        "joins": joins,
        "fee_accounts_in_2_or_more_groups": [[a, n, known.get(a)] for a, n in fee_groups.most_common() if n >= 2],
        "net_calls": c.net_calls,
    }
    (OUT / "hypotheses.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "groups"}, indent=0)[:1600])
    for g in res:
        print(
            g["group"],
            "fees",
            [(a[:8], n, lab) for a, n, lab in g["fee_accounts"]][:4],
            "prog",
            [p[:8] for p, _ in g["programs"]][:6],
        )
        for p in g["paths"]:
            print(
                "   ",
                p["wallet"][:8],
                p["tx_read"],
                p["complete"],
                [(a[:8], v, lab) for a, v, lab in p["out_top"]],
                {k[:8]: [(a[:8], v, lab) for a, v, lab in rows] for k, rows in p["second_hop"].items()},
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
