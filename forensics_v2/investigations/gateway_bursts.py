"""Behaviour of same-amount gateway bursts, per docs/PLAN_gateway_bursts.md.

    python -m forensics_v2.investigations.gateway_bursts controls <credits>   # positive and negative controls
    python -m forensics_v2.investigations.gateway_bursts collect <credits>    # read the sampled members
    python -m forensics_v2.investigations.gateway_bursts analyse              # outcomes, null, intervals
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .. import decode as D
from ..__main__ import client
from ..trace import History, history, load_services, sol_flows
from .trades_2024 import STUDY

SEED = 20261102
MIN_SIZE, GAP_S, N_BURSTS, N_MEMBERS = 9, 600, 150, 12
H72, D7 = 72 * 3600, 7 * 86400
MIN_MEMBERS, SLOT_SPAN, MIN_DEST = 5, 10, 100_000_000
OUT = Path(__file__).resolve().parents[1] / "reports" / "gateway_bursts"


def bursts_of(payouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for p in payouts:
        by[p["lam"]].append(p)
    out = []
    for lam, rows in by.items():
        rows.sort(key=lambda r: (r["t"], r["sig"]))
        cur = [rows[0]]
        for r in rows[1:]:
            if r["t"] - cur[-1]["t"] <= GAP_S:
                cur.append(r)
            else:
                if len(cur) >= MIN_SIZE:
                    out.append({"lam": lam, "members": cur})
                cur = [r]
        if len(cur) >= MIN_SIZE:
            out.append({"lam": lam, "members": cur})
    out.sort(key=lambda b: (b["members"][0]["t"], b["lam"]))
    return out


def sample(bursts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    picked = random.Random(SEED).sample(range(len(bursts)), min(N_BURSTS, len(bursts)))
    return [{"lam": bursts[i]["lam"], "t0": bursts[i]["members"][0]["t"], "size": len(bursts[i]["members"]),
             "members": [{"wallet": m["to"], "t": m["t"], "sig": m["sig"]} for m in bursts[i]["members"][:N_MEMBERS]]}
            for i in sorted(picked)]


def behaviour(h: History, t_credit: int, services: set[str]) -> dict[str, Any]:
    """What one wallet did after its credit, from its first page of history."""
    buys = []
    for d in h.txs:
        if d.block_time is None or not d.ok or not 0 <= d.block_time - t_credit <= H72:
            continue
        for mint, tok in D.traded_mints(d, h.address).items():
            if tok > 0:
                buys.append({"mint": mint, "tok": tok, "slot": d.slot})
    flows, _ = sol_flows(h)
    dest = sorted({f.dst for f in flows if f.src == h.address and f.dst not in services and f.lamports >= MIN_DEST
                   and f.basis == "instruction" and f.ts is not None and 0 <= f.ts - t_credit <= D7})
    first = h.txs[0].signature if h.txs else None
    return {"buys": buys, "dest": dest, "first_sig": first, "n_tx": len(h.txs), "stop": h.walk.stop}


def outcomes(members: list[dict[str, Any]]) -> dict[str, bool]:
    by_mint: dict[str, set[str]] = defaultdict(set)
    by_size: dict[tuple[str, int], list[tuple[int, str]]] = defaultdict(list)
    by_dest: Counter[str] = Counter()
    for m in members:
        for b in m["buys"]:
            by_mint[b["mint"]].add(m["wallet"])
            by_size[(b["mint"], b["tok"])].append((b["slot"], m["wallet"]))
        for d in m["dest"]:
            by_dest[d] += 1
    o1 = False
    for rows in by_size.values():
        rows.sort()
        for i in range(len(rows)):
            window = {w for s, w in rows[i:] if s - rows[i][0] <= SLOT_SPAN}
            if len(window) >= MIN_MEMBERS:
                o1 = True
                break
        if o1:
            break
    return {"O1": o1, "O2": any(len(v) >= MIN_MEMBERS for v in by_mint.values()),
            "O3": any(v >= MIN_MEMBERS for v in by_dest.values())}


def read_member(c: Any, wallet: str, t: int, services: set[str]) -> dict[str, Any]:
    h = history(c, wallet, token_accounts="none", max_pages=1)
    return {"wallet": wallet, "t": t, **behaviour(h, t, services)}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def controls(credits: int) -> int:
    c = client(credits)
    services = set(load_services())
    group = json.loads((OUT.parent / "nine_wallets" / "group15.json").read_text())["group"]
    pos = []
    for w in group:
        h = history(c, w, token_accounts="none", max_pages=1)
        t = next(f.ts for f in sol_flows(h)[0] if f.dst == w)
        pos.append({"wallet": w, "t": t, **behaviour(h, t, services)})
    r = outcomes(pos)
    print("positive control, the 15 wallets of the published case:", r, "net", c.net_calls)
    (OUT / "controls.json").parent.mkdir(parents=True, exist_ok=True)
    (OUT / "controls.json").write_text(json.dumps({"positive": r}, indent=1))
    return 0 if all(r.values()) else 1


def collect(credits: int) -> int:
    payouts = json.loads((STUDY / "data/payouts.json").read_text())["payouts"]
    bursts = bursts_of(payouts)
    smp = sample(bursts)
    OUT.mkdir(parents=True, exist_ok=True)
    print("population bursts", len(bursts), "sampled", len(smp), "members", sum(len(b["members"]) for b in smp), flush=True)
    c = client(credits)
    services = set(load_services())
    results = []
    stopped = None
    for i, b in enumerate(smp):
        rows = []
        try:
            for m in b["members"]:
                rows.append(read_member(c, m["wallet"], m["t"], services) | {"credit_sig": m["sig"]})
        except RuntimeError as e:  # BudgetExhausted included: keep what was read, and say so
            stopped = str(e)[:120]
            break
        results.append({k: b[k] for k in ("lam", "t0", "size")} | {"members": rows})
        if i % 10 == 0:
            print(i, "net", c.net_calls, flush=True)
    meta = {"population_bursts": len(bursts), "population_members": sum(len(b["members"]) for b in bursts),
            "sampled": len(smp), "read": len(results), "stopped": stopped, "net_calls": c.net_calls}
    store = Path(c.root) / "intermediate" / "gateway_bursts.json"  # wallet level: stays off the repository
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_text(json.dumps({"meta": meta, "bursts": results}))
    print(meta)
    return 0


def analyse() -> int:
    from .. import storage
    d = json.loads((storage.data_root() / "intermediate" / "gateway_bursts.json").read_text())
    bursts = d["bursts"]
    names = ("O1", "O2", "O3")
    real = [outcomes(b["members"]) for b in bursts]
    counts = {o: sum(r[o] for r in real) for o in names}
    n = len(bursts)
    # null: member labels permuted inside a UTC day, sizes kept
    by_day: dict[int, list[int]] = defaultdict(list)
    for i, b in enumerate(bursts):
        by_day[b["t0"] // 86400].append(i)
    rng = random.Random(SEED)
    perms = 1000
    null = {o: [] for o in names}
    for _ in range(perms):
        tot = Counter()
        for idx in by_day.values():
            pool = [m for i in idx for m in bursts[i]["members"]]
            rng.shuffle(pool)
            pos = 0
            for i in idx:
                k = len(bursts[i]["members"])
                r = outcomes(pool[pos:pos + k])
                pos += k
                for o in names:
                    tot[o] += r[o]
        for o in names:
            null[o].append(tot[o])
    # bootstrap by day
    days = list(by_day)
    boot = {o: [] for o in names}
    for _ in range(2000):
        draw = [rng.choice(days) for _ in days]
        idx = [i for dd in draw for i in by_day[dd]]
        for o in names:
            boot[o].append(sum(real[i][o] for i in idx) / max(1, len(idx)))
    res: dict[str, Any] = {"meta": d["meta"], "n_bursts_read": n, "n_days": len(days), "alpha": 0.05 / 3, "outcomes": {}}
    for o in names:
        s = sorted(boot[o])
        nn = sorted(null[o])
        res["outcomes"][o] = {
            "bursts_meeting": counts[o], "share": counts[o] / n, "wilson_95": wilson(counts[o], n),
            "bootstrap_by_day_95": (s[int(0.025 * len(s))], s[int(0.975 * len(s))]),
            "null_mean": sum(nn) / perms, "null_p95": nn[int(0.95 * perms)],
            "p_permutation": (1 + sum(1 for x in nn if x >= counts[o])) / (perms + 1),
        }
    fresh = [i for i, b in enumerate(bursts)
             if sum(1 for m in b["members"] if m.get("first_sig") == m.get("credit_sig")) >= MIN_MEMBERS]
    res["secondary_bursts_with_5_fresh"] = {"n": len(fresh), **{o: sum(real[i][o] for i in fresh) for o in names}}
    res["member_history_stopped_at_first_page"] = sum(1 for b in bursts for m in b["members"] if m["stop"] == "max_pages")
    res["members_read"] = sum(len(b["members"]) for b in bursts)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=0))
    return 0


def main() -> int:
    cmd = sys.argv[1]
    if cmd == "controls":
        return controls(int(sys.argv[2]))
    if cmd == "collect":
        return collect(int(sys.argv[2]))
    return analyse()


if __name__ == "__main__":
    sys.exit(main())
