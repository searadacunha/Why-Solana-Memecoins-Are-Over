"""Launch context of the author's curve trades, per docs/PLAN_trade_context.md. Private output, aggregated report.

    python -m forensics_v2.investigations.trade_context collect <credits>
    python -m forensics_v2.investigations.trade_context analyse
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from typing import Any, Optional

from .. import decode as D
from ..__main__ import client
from ..trace import history, sol_flows
from .gateway_bursts import wilson
from .trades_2024 import G2Y, OCT1, JAN1, POSTHOC, PRIVATE, utc, write_private

SEED = 20261102
BIG = 20_000_000 * 10**6
SUPPLY = 10**15
OUT = PRIVATE / "trade_context"  # figures about the author's own trades: nothing from here goes to a public file
WEEK = 7 * 86400


def sample() -> list[dict[str, Any]]:
    trips = json.loads((POSTHOC / "derived/trips.json").read_text())
    classes = json.loads((POSTHOC / "derived/classes.json").read_text())
    rows = []
    for t, c in zip(trips, classes):
        assert t["wallet"] == c["wallet"] and t["mint"] == c["mint"]
        if OCT1 <= t["t_open"] < JAN1 and t.get("entry_venue") == "pump":
            rows.append({**t, "class": c["class"]})
    rows.sort(key=lambda r: (r["t_open"], r["wallet"], r["mint"]))
    a = [r for r in rows if r["class"] == "P"]
    b = [r for r in rows if r.get("exit_venue") == "raydium" and r["closed"]]
    taken = {(r["wallet"], r["mint"], r["t_open"]) for r in a + b}
    rest = [r for r in rows if (r["wallet"], r["mint"], r["t_open"]) not in taken]
    c_rows = random.Random(SEED).sample(rest, min(200, len(rest)))
    out = []
    for name, group in (("A", a), ("B", b), ("C", c_rows)):
        out += [{"group": name, **r} for r in group]
    return out


def read_mint(c: Any, mint: str, t_entry: int, cache: dict[str, Any]) -> dict[str, Any]:
    """First 200 transactions of the mint: creation and every TradeEvent, in chain order."""
    if mint in cache:
        return cache[mint]
    h = history(c, mint, token_accounts="none", max_pages=2)
    order = {s["signature"]: (s["slot"], s.get("transactionIndex") or 0) for s in h.walk.signatures}
    events, creator, t_create = [], None, None
    for d in sorted(h.txs, key=lambda x: order.get(x.signature, (x.slot, 0))):
        if not d.ok:
            continue
        if creator is None and any(t.kind == "mint" and t.mint == mint for t in d.transfers):
            creator, t_create = d.fee_payer, d.block_time
        for e in d.trade_events:
            if e["mint"] == mint:
                events.append({"user": e["user"], "tok": e["tok"], "sol": e["sol"], "buy": e["buy"], "t": d.block_time,
                               "slot": d.slot, "idx": order.get(d.signature, (0, 0))[1], "rsol": e["rsol"], "sig": d.signature})
    r = {"creator": creator, "t_create": t_create, "events": events, "n_tx": len(h.txs), "stop": h.walk.stop,
         "last_t": h.txs[-1].block_time if h.txs else None}
    cache[mint] = r
    return r


def read_buyer(c: Any, wallet: str, cache: dict[str, Any]) -> dict[str, Any]:
    if wallet in cache:
        return cache[wallet]
    h = history(c, wallet, token_accounts="none", max_pages=1)
    flows, _ = sol_flows(h)
    credits_ = [{"lamports": f.lamports, "t": f.ts, "sig": f.signature, "evidence": f.evidence}
                for f in flows if f.dst == wallet and f.src == G2Y]
    first = h.txs[0] if h.txs else None
    r = {"first_t": first.block_time if first else None, "first_sig": first.signature if first else None,
         "first_is_gateway": bool(first and credits_ and credits_[0]["sig"] == first.signature),
         "gateway_credits": credits_[:5], "history_truncated": not h.walk.complete and len(h.txs) >= 100}
    cache[wallet] = r
    return r


def classify(trip: dict[str, Any], m: dict[str, Any], c: Any, buyers: dict[str, Any]) -> dict[str, Any]:
    t_open, wallet = trip["t_open"], trip["wallet"]
    ev = m["events"]
    mine = [e for e in ev if e["user"] == wallet and e["buy"] and (e["t"] or 0) >= t_open]
    covers = bool(mine) or (m["last_t"] or 0) >= t_open
    entry_t = mine[0]["t"] if mine else t_open
    entry_key = (mine[0]["slot"], mine[0]["idx"]) if mine else None
    before = []
    for e in ev:
        if not e["buy"] or e["tok"] < BIG or e["user"] == wallet:
            continue
        if entry_key and (e["slot"], e["idx"]) >= entry_key:
            continue
        if not entry_key and (e["t"] or 0) >= t_open:
            continue
        before.append(e)
    rank: dict[str, int] = {}
    for e in ev:
        if e["buy"] and e["user"] not in rank:
            rank[e["user"]] = len(rank) + 1
    s1 = s2 = None
    details = []
    seen = set()
    for e in before:
        if e["user"] in seen or len(seen) >= 8:
            continue
        seen.add(e["user"])
        b = read_buyer(c, e["user"], buyers)
        pre = [x for x in b["gateway_credits"] if (x["t"] or 0) <= (e["t"] or 0)]
        wk = [x for x in pre if (e["t"] or 0) - (x["t"] or 0) <= WEEK]
        is1 = bool(b["first_is_gateway"] and pre)
        is2 = bool(wk)
        details.append({"buyer": e["user"], "pct": round(e["tok"] * 100 / SUPPLY, 3), "t": e["t"], "s1": is1, "s2": is2,
                        "is_creator": e["user"] == m["creator"], "buy_sig": e["sig"],
                        "credit_sig": pre[0]["sig"] if pre else None, "credit_lamports": pre[0]["lamports"] if pre else None})
        if is1 and s1 is None:
            s1 = e["t"]
        if is2 and s2 is None:
            s2 = e["t"]
    my_first = mine[0] if mine else None
    return {"group": trip["group"], "wallet": wallet, "mint": trip["mint"], "t_open": t_open, "t_open_utc": utc(t_open),
            "class_frozen": trip["class"], "closed": trip["closed"], "realised_sol": trip["realised_sol"],
            "window_covers_entry": covers, "t_create": m["t_create"], "creator": m["creator"],
            "entry_delay_after_creation_s": (entry_t - m["t_create"]) if m["t_create"] and entry_t else None,
            "rank_among_buyers": rank.get(wallet),
            "first_buy_pct_supply": round(my_first["tok"] * 100 / SUPPLY, 4) if my_first else None,
            "curve_real_sol_after_entry": (my_first["rsol"] / 1e9) if my_first and my_first["rsol"] is not None else None,
            "S0": bool(before), "S1": s1 is not None, "S2": s2 is not None, "n_large_before": len({e["user"] for e in before}),
            "delay_after_S1_s": (entry_t - s1) if s1 and entry_t else None,
            "delay_after_S2_s": (entry_t - s2) if s2 and entry_t else None,
            "buyers_checked": details}


def collect(credits: int) -> int:
    smp = sample()
    c = client(credits)
    mints: dict[str, Any] = {}
    buyers: dict[str, Any] = {}
    out = []
    stopped: Optional[str] = None
    print("sample", len(smp), "mints", len({r["mint"] for r in smp}), flush=True)
    for i, t in enumerate(smp):
        try:
            m = read_mint(c, t["mint"], t["t_open"], mints)
            out.append(classify(t, m, c, buyers))
        except RuntimeError as e:
            stopped = str(e)[:140]
            print("stopped", stopped, flush=True)
            break
        if i % 25 == 0:
            print(i, "net", c.net_calls, flush=True)
            write_private("PATTERN_MATCHES.json", json.dumps({"stopped": stopped, "partial": True, "trips": out}, indent=1))
    write_private("PATTERN_MATCHES.json", json.dumps({"stopped": stopped, "partial": bool(stopped), "trips": out}, indent=1))
    print({"trips": len(out), "stopped": stopped, "net": c.net_calls, "buyers_read": len(buyers)})
    return 0


def control_sample(c: Any, n: int) -> list[dict[str, Any]]:
    """Ordinary buys at random moments of the period. Costs one reply per draw; nothing is stored but the checkpoint below."""
    from .trades_2024 import ledger
    own = set(ledger()["candidates"])
    rng = random.Random(20261103)
    ck = c.root / "intermediate" / "trade_context_controls.json"
    done: list[dict[str, Any]] = json.loads(ck.read_text()) if ck.exists() else []
    times = [rng.randrange(OCT1, JAN1) for _ in range(n)]
    for t in times[len(done):]:
        r = c.call("getTransactionsForAddress", [D.PUMP, {
            "transactionDetails": "full", "sortOrder": "asc", "limit": 20, "encoding": "json",
            "maxSupportedTransactionVersion": 1, "filters": {"tokenAccounts": "none", "status": "succeeded",
                                                             "blockTime": {"gte": t, "lte": t + 600}}}], D.PUMP, credits=10)
        pick = None
        for item in r.get("data") or []:
            d = D.decode(item)
            for e in d.trade_events:
                if e["buy"] and e["user"] not in own:
                    pick = {"group": "X", "wallet": e["user"], "mint": e["mint"], "t_open": d.block_time, "class": None,
                            "closed": False, "realised_sol": 0.0, "drawn_at": t}
                    break
            if pick:
                break
        done.append(pick or {"group": "X", "none_at": t})
        ck.parent.mkdir(parents=True, exist_ok=True)
        ck.write_text(json.dumps(done))
    return [x for x in done if "wallet" in x]


def collect_control(credits: int) -> int:
    c = client(credits)
    c.store_bodies = False  # the external disk stalls under other sessions: keep signatures and results, not the bodies
    smp = control_sample(c, 200)
    print("controls drawn", len(smp), "net", c.net_calls, flush=True)
    mints: dict[str, Any] = {}
    buyers: dict[str, Any] = {}
    out = []
    stopped = None
    for i, t in enumerate(smp):
        try:
            out.append(classify(t, read_mint(c, t["mint"], t["t_open"], mints), c, buyers))
        except RuntimeError as e:
            stopped = str(e)[:140]
            break
        if i % 25 == 0:
            print(i, "net", c.net_calls, flush=True)
    store = c.root / "intermediate" / "trade_context_group_x.json"
    store.write_text(json.dumps({"stopped": stopped, "trips": out}))
    print({"trips": len(out), "stopped": stopped, "net": c.net_calls})
    return 0


def _fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    from math import comb
    n, r1, k1 = a + b + c + d, a + b, a + c

    def pr(x: int) -> float:
        return comb(r1, x) * comb(n - r1, k1 - x) / comb(n, k1)
    p0 = pr(a)
    return min(1.0, sum(pr(x) for x in range(max(0, k1 - (n - r1)), min(r1, k1) + 1) if pr(x) <= p0 * (1 + 1e-9)))


def analyse_control() -> int:
    from .. import storage
    from .trades_2024 import PRIVATE
    x = json.loads((storage.data_root() / "intermediate" / "trade_context_group_x.json").read_text())
    c_rows = [r for r in json.loads((PRIVATE / "PATTERN_MATCHES.json").read_text())["trips"] if r["group"] == "C"]

    def seen(r: dict[str, Any]) -> bool:
        return bool(r["window_covers_entry"] and r["first_buy_pct_supply"] is not None)

    def band(r: dict[str, Any]) -> Optional[str]:
        v = r["curve_real_sol_after_entry"]
        return None if v is None else "under_5" if v < 5 else "5_to_20" if v < 20 else "20_to_85" if v < 85 else "over_85"

    def block(rows: list[dict[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {"n": len(rows)}
        for s in ("S0", "S1", "S2"):
            k = sum(1 for r in rows if r[s])
            out[s] = {"k": k, "share": k / len(rows) if rows else None, "wilson_95": wilson(k, len(rows))}
        out["median_first_buy_pct_supply"] = median([r["first_buy_pct_supply"] for r in rows])
        out["median_rank"] = median([r["rank_among_buyers"] for r in rows])
        out["median_entry_delay_s"] = median([r["entry_delay_after_creation_s"] for r in rows])
        out["median_curve_sol_after_entry"] = median([r["curve_real_sol_after_entry"] for r in rows])
        return out

    xs, cs = x["trips"], c_rows
    res: dict[str, Any] = {"stopped": x["stopped"], "amended_after_reading_groups_ABC": True,
                           "X_all": block(xs), "X_entry_seen": block([r for r in xs if seen(r)]),
                           "C_all": block(cs), "C_entry_seen": block([r for r in cs if seen(r)]), "by_curve_band_entry_seen": {}}
    for b in ("under_5", "5_to_20", "20_to_85"):
        res["by_curve_band_entry_seen"][b] = {
            "C": block([r for r in cs if seen(r) and band(r) == b]), "X": block([r for r in xs if seen(r) and band(r) == b])}
    a1, a0 = res["C_entry_seen"]["S1"]["k"], res["C_entry_seen"]["n"] - res["C_entry_seen"]["S1"]["k"]
    b1, b0 = res["X_entry_seen"]["S1"]["k"], res["X_entry_seen"]["n"] - res["X_entry_seen"]["S1"]["k"]
    res["fisher_S1_entry_seen_C_vs_X"] = {"table": [[a1, a0], [b1, b0]], "p_two_sided": _fisher_two_sided(a1, a0, b1, b0)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results_control.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=0))
    return 0


def median(v: list[float]) -> Optional[float]:
    v = sorted(x for x in v if x is not None)
    return (v[(len(v) - 1) // 2] + v[len(v) // 2]) / 2 if v else None


def analyse() -> int:
    from .trades_2024 import PRIVATE
    d = json.loads((PRIVATE / "PATTERN_MATCHES.json").read_text())
    rows = d["trips"]
    res: dict[str, Any] = {"partial": d["partial"], "n": len(rows), "groups": {}}
    for g in "ABC":
        # His own buy has to be seen: a late timestamp alone does not show the window reached his entry.
        for label, sel in (("all", lambda r: True),
                           ("entry_seen", lambda r: r["window_covers_entry"] and r["first_buy_pct_supply"] is not None)):
            xs = [r for r in rows if r["group"] == g and sel(r)]
            n = len(xs)
            entry = {"n": n}
            for s in ("S0", "S1", "S2"):
                k = sum(1 for r in xs if r[s])
                entry[s] = {"k": k, "share": k / n if n else None, "wilson_95": wilson(k, n)}
            entry["median_first_buy_pct_supply"] = median([r["first_buy_pct_supply"] for r in xs])
            entry["share_first_buy_at_most_1pct"] = (
                sum(1 for r in xs if r["first_buy_pct_supply"] is not None and r["first_buy_pct_supply"] <= 1.0)
                / max(1, sum(1 for r in xs if r["first_buy_pct_supply"] is not None)))
            entry["median_rank"] = median([r["rank_among_buyers"] for r in xs])
            entry["median_entry_delay_s"] = median([r["entry_delay_after_creation_s"] for r in xs])
            entry["median_curve_sol_after_entry"] = median([r["curve_real_sol_after_entry"] for r in xs])
            entry["median_delay_after_S1_s"] = median([r["delay_after_S1_s"] for r in xs])
            entry["median_delay_after_S2_s"] = median([r["delay_after_S2_s"] for r in xs])
            res["groups"].setdefault(g, {})[label] = entry
    assoc: dict[str, Any] = defaultdict(dict)
    c_closed = [r for r in rows if r["group"] == "C" and r["closed"]]
    for s in ("S0", "S1", "S2"):
        for flag in (True, False):
            xs = [r["realised_sol"] for r in c_closed if r[s] == flag]
            assoc[s][str(flag)] = {"n": len(xs), "sum_sol": round(sum(xs), 3), "median_sol": median(xs)}
    res["group_C_realised_by_signal_association_only"] = assoc
    res["signal_buyer_is_token_creator"] = sum(
        1 for r in rows for b in r["buyers_checked"] if b["is_creator"] and (b["s1"] or b["s2"]))
    res["checked_large_buyers"] = sum(len(r["buyers_checked"]) for r in rows)
    res["trips_with_more_large_buyers_than_checked"] = sum(1 for r in rows if r["n_large_before"] > len(r["buyers_checked"]))
    res["note_lower_bound"] = ("Only each buyer's first 100 transactions and up to 8 large buyers per trip are read: "
                               "S1 and S2 are lower bounds.")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=0))
    return 0


def main() -> int:
    if sys.argv[1] == "collect":
        return collect(int(sys.argv[2]))
    if sys.argv[1] == "collect_control":
        return collect_control(int(sys.argv[2]))
    if sys.argv[1] == "analyse_control":
        return analyse_control()
    return analyse()


if __name__ == "__main__":
    sys.exit(main())
