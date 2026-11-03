"""A shared service or one economic network? Plan: docs/PLAN_network_links.md. Public addresses only.

python -m forensics_v2.investigations.network_links <burst sample json> <credits>
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .. import decode as D
from ..__main__ import client
from ..rpc import RpcError
from ..trace import Flow, history, sol_flows
from .fleet_hypotheses import OUT, labels
from .trade_context import read_buyer

G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"
SWEEP = "6aRTeY51oxJQd631spmMZnhRKLTw9WhGZiW6GHGpQSKp"
BURSTS = (140, 141, 142)
CONTROL_BURST = 138
DESTINATIONS = {
    "godTjnH7RZ3KAG6oEVTU7mH22TZR5oV4JKJheF9ZAjc": "D15CAtUpCVE6z7NeFhAKrYCUq7R9Xh98cypCFrV33HAi",
    "C7ZxQvvjwB3N466Ysp6dWiktBDDcLNLMhhoukQUjsTA2": "D15CAtUpCVE6z7NeFhAKrYCUq7R9Xh98cypCFrV33HAi",
    "FuDyM3MLFYgvSM8CL8VTjrfSaMhxzizn1xiuxpM3obZb": "GrmXv6qK672i9ToMtXoAiBqAFQD51m7TQm8P6MmRAc66",
    "godxpxo7vYWyLCwHiWnwJmKivibyvfbdekMeSXQQ6TK": "godTjnH7RZ3KAG6oEVTU7mH22TZR5oV4JKJheF9ZAjc",
    "5FaGXg95BA7Wb1nqj7unqoCBgquywFMnb2uy2dBG5hY": "godTjnH7RZ3KAG6oEVTU7mH22TZR5oV4JKJheF9ZAjc",
}
DAY_0128 = 1738022400  # 2025-01-28 00:00 UTC
SERVICE_SENDERS, PRIVATE_SENDERS, BUSY_PER_HOUR = 18, 5, 200


def label_wallet(flows: Iterable[Flow], times: list[int], wallet: str) -> dict[str, Any]:
    """The plan's rule. `times` are the block times of the transactions read, in chain order. 100 transactions is one window."""
    times = sorted(t for t in times if t)
    flows = sorted(flows, key=lambda f: f.ts or 0)
    per_window: list[int] = []
    received: Counter[str] = Counter()
    for i in range(0, max(len(times), 1), 100):
        lo, hi = (times[i], times[min(i + 99, len(times) - 1)]) if times else (0, 0)
        per_window.append(len({f.src for f in flows if f.dst == wallet and f.lamports >= 10_000_000 and lo <= (f.ts or 0) <= hi}))
    for f in flows:
        if f.dst == wallet and f.lamports >= 10_000_000:
            received[f.src] += f.lamports
    busiest = 0
    j = 0
    for i, t in enumerate(times):
        while t - times[j] > 3600:
            j += 1
        busiest = max(busiest, i - j + 1)
    total = sum(received.values())
    top5 = sum(v for _, v in received.most_common(5))
    full = len(times) >= 100
    if max(per_window, default=0) >= SERVICE_SENDERS or busiest > BUSY_PER_HOUR:
        label = "service-like"
    elif full and max(per_window, default=0) <= PRIVATE_SENDERS and total and top5 / total >= 0.8:
        label = "private-like"
    else:
        label = "undetermined"
    return {
        "label": label,
        "tx_read": len(times),
        "max_senders_per_100_tx": max(per_window, default=0),
        "busiest_hour_tx": busiest,
        "top5_share_of_sol_received": round(top5 / total, 3) if total else None,
    }


def read(c: Any, wallet: str, t_from: int | None = None, pages: int = 1) -> tuple[list[Flow], list[int]]:
    h = history(c, wallet, t_from=t_from, token_accounts="none", max_pages=pages)
    return sol_flows(h)[0], [d.block_time for d in h.txs if d.block_time]


def dest_summary(wallet: str, flows: list[Flow], times: list[int], known: dict[str, str]) -> dict[str, Any]:
    uniq = {f.signature + f.src + f.dst + str(f.lamports): f for f in flows}
    fl = list(uniq.values())
    out: Counter[str] = Counter()
    for f in fl:
        if f.src == wallet and f.lamports >= 10_000_000:
            out[f.dst] += f.lamports
    return {
        "wallet": wallet,
        "public_label": known.get(wallet),
        **label_wallet(fl, sorted(set(times)), wallet),
        "pays": [[a, round(v / 1e9, 3), known.get(a)] for a, v in out.most_common(8)],
        "to_gateway": [[f.ts, round(f.lamports / 1e9, 6), f.signature] for f in fl if f.src == wallet and f.dst == G2Y],
    }


def main() -> int:
    bursts = json.loads(Path(sys.argv[1]).read_text())["bursts"]
    known = {**labels(), "CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM": "pump.fun fee account"}
    c = client(int(sys.argv[2]))
    res: dict[str, Any] = {"plan": "docs/PLAN_network_links.md", "stopped": None}
    buyers: dict[str, Any] = {}
    try:
        # the three destinations and the next hops
        sweep_time: dict[str, int] = {}
        for sender in set(DESTINATIONS.values()):
            fl, _ = read(c, sender, pages=2)
            for d, s in DESTINATIONS.items():
                if s == sender and d not in sweep_time:
                    t = [f.ts for f in fl if f.src == sender and f.dst == d and f.ts]
                    if t:
                        sweep_time[d] = min(t)
        dests = []
        for d in DESTINATIONS:
            fl, ti = read(c, d)
            if d in sweep_time:
                f2, t2 = read(c, d, t_from=sweep_time[d] - 300)
                fl, ti = fl + f2, ti + t2
            dests.append(dest_summary(d, fl, ti, known))
            print(d[:8], dests[-1]["label"], "net", c.net_calls, flush=True)
        res["destinations"] = dests

        # joins, by the plan's rule: not service-like, not labelled, and on the path of another group
        hyp = json.loads((OUT / "hypotheses.json").read_text())
        paths: dict[str, set[str]] = {}
        for g in hyp["groups"]:
            on = set()
            for pa in g["paths"]:
                on.add(pa["wallet"])
                on.update(a for a, _, lab in pa["out_top"] if not lab)
                for hop in pa["second_hop"].values():
                    on.update(a for a, _, lab in hop if not lab)
            paths[g["group"]] = on
        res["joins"] = []
        for x in dests:
            if x["label"] == "service-like" or x["public_label"]:
                continue
            reach = {x["wallet"]} | {a for a, _, lab in x["pays"] if not lab}
            home = [g for g, on in paths.items() if x["wallet"] in on]
            for g, on in paths.items():
                if g not in home and reach & on:
                    res["joins"].append({"destination": x["wallet"], "from": home, "to": g, "via": sorted(reach & on)})

        # the joined bursts' sweep
        members = {i: sorted({m["wallet"] for m in bursts[i]["members"]}) for i in (*BURSTS, CONTROL_BURST)}
        in_bursts = {w for i in BURSTS for w in members[i]}
        fl, ti = read(c, SWEEP, pages=2)
        f2, t2 = read(c, SWEEP, t_from=DAY_0128, pages=3)
        s = dest_summary(SWEEP, fl + f2, ti + t2, known)
        senders: Counter[str] = Counter()
        for f in {x.signature + x.src: x for x in fl + f2}.values():
            if f.dst == SWEEP and f.lamports >= 100_000_000:
                senders[f.src] += f.lamports
        others = [a for a, _ in senders.most_common() if a not in in_bursts and a not in known][:30]
        rows = []
        for a in others:
            b = read_buyer(c, a, buyers)
            rows.append({"wallet": a, "sol_sent": round(senders[a] / 1e9, 3), "first_is_gateway": bool(b["first_is_gateway"])})
        gw = sum(r["first_is_gateway"] for r in rows)
        share = gw / len(rows) if rows else None
        reading = (
            "service or shared sweep"
            if s["label"] == "service-like" or (share is not None and share < 0.25)
            else "one network, beyond the 3 bursts"
            if share is not None and share >= 0.5
            else "UNRESOLVED"
        )
        res["sweep"] = {
            **s,
            "senders_at_least_0_1_sol": len(senders),
            "senders_in_the_3_bursts": sum(a in in_bursts for a in senders),
            "sol_from_the_3_bursts": round(sum(v for a, v in senders.items() if a in in_bursts) / 1e9, 3),
            "sol_from_others": round(sum(v for a, v in senders.items() if a not in in_bursts) / 1e9, 3),
            "other_senders_read": rows,
            "other_senders_gateway_funded": gw,
            "reading_from_the_plan": reading,
        }
        print("sweep", s["label"], reading, "net", c.net_calls, flush=True)
        # post hoc, not in the plan: the rule reads many senders as a service, and a wallet farm's treasury looks the same
        paid: Counter[str] = Counter()
        for f in {x.signature + x.dst: x for x in fl + f2}.values():
            if f.src == SWEEP and f.lamports >= 100_000_000:
                paid[f.dst] += f.lamports
        round_paid = sum(v % 100_000_000 == 0 for v in paid.values())
        res["sweep"]["posthoc"] = {
            "paid_at_least_0_1_sol": len(paid),
            "round_totals_among_them": round_paid,
            "other_senders_read_also_paid_by_it": sum(r["wallet"] in paid for r in rows),
            "of_other_senders_read": len(rows),
        }

        # purchases across the 3 bursts
        bought: dict[int, dict[str, set[int]]] = {}
        for i in (*BURSTS, CONTROL_BURST):
            bought[i] = {}
            for w in members[i] if i in BURSTS else members[i][:3]:
                h = history(c, w, token_accounts="none", max_pages=1)
                for d in h.txs:
                    tk = D.traded_mints(d, w)
                    if d.ok and d.block_time and tk and next(iter(tk.values())) > 0:
                        bought[i].setdefault(next(iter(tk)), set()).add(d.block_time // 3600)
        common = {}
        ids = list(bought)
        for x, a in enumerate(ids):
            for b in ids[x + 1 :]:
                same = [m for m in set(bought[a]) & set(bought[b]) if bought[a][m] & bought[b][m]]
                common["%d_%d" % (a, b)] = {
                    "mints_same_hour": len(same),
                    "of_a": len(bought[a]),
                    "of_b": len(bought[b]),
                    "examples": sorted(same)[:5],
                }
        res["purchases"] = {"members": {str(i): len(members[i]) for i in BURSTS}, "control_members_read": 3, "pairs": common}
    except RpcError as e:  # credits or quota: keep what was read
        res["stopped"] = str(e)[:140]
    res["net_calls"] = c.net_calls
    (OUT / "network_links.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k not in ("destinations", "sweep")}, indent=0)[:1800])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
