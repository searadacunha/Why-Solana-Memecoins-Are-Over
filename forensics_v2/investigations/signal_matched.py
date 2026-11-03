"""An independent control of the signal. Plan: docs/PLAN_signal_matched.md. Output is private.

python -m forensics_v2.investigations.signal_matched collect <credits>
python -m forensics_v2.investigations.signal_matched analyse
"""

from __future__ import annotations

import csv
import json
import random
import sys
from math import comb
from typing import Any, Optional

from .. import decode as D
from ..__main__ import client
from ..rpc import RpcError
from .trade_context import _fisher_two_sided, classify, read_buyer, read_mint
from .trades_2024 import CACHE, PRIVATE, ledger, write_private

SEED = 20261104
DEC1 = 1733011200
EXCHANGES = {
    "FWznbcNXWQuHTawe9RxvQ2LdCENssh12dsznf4RiouN5",
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9",
    "H8sMJSCQxfKiFTCfDR3DUMLPwcRbM61LGFJ8N4dK3WjS",
    "2AQdpHJ2JpcEgPiATUXjQxA8QmafFegfQwSLWSprPicm",
    "GJRs4FwHtemZ5ZE9x3FNvJ8TMwitKTh21yxdRPqn7npE",
}
OUT = "trade_context/matched_v2.json"


def curve_band(lamports: Optional[int]) -> Optional[str]:
    if lamports is None:
        return None
    sol = lamports / 1e9
    return "under_5" if sol < 5 else "5_to_20" if sol < 20 else "20_to_85" if sol < 85 else None


def age_band(seconds: Optional[int]) -> Optional[str]:
    if seconds is None or seconds < 0:
        return None
    return (
        "a_1m"
        if seconds < 60
        else "b_10m"
        if seconds < 600
        else "c_1h"
        if seconds < 3600
        else "d_1d"
        if seconds < 86400
        else "e_more"
    )


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact test on the discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2**n)


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, top = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        top = max(top, min(1.0, ps[i] * (len(ps) - rank)))
        out[i] = top
    return out


def fresh_sample() -> list[dict[str, Any]]:
    """Curve entries whose launch was never read, in a fixed order, then the plan's draw."""
    with open(PRIVATE / "TRADES_V2.csv") as f:
        rows = [
            r
            for r in csv.DictReader(f)
            if r["entry_venue"] == "pump" and r["t_open_utc"] < "2025-01-01" and r["pattern"] == "launch_not_read"
        ]
    t_open = {}
    with open(PRIVATE / "TRADE_EVIDENCE.jsonl") as f:
        for line in f:
            e = json.loads(line)
            if e["side"] == "buy":
                t_open[e["sig"]] = e["t_open"]
    rows = sorted(
        (r for r in rows if r["first_buy_sig"] in t_open), key=lambda r: (t_open[r["first_buy_sig"]], r["wallet"], r["mint"])
    )
    early = [r for r in rows if t_open[r["first_buy_sig"]] < DEC1]
    late = [r for r in rows if t_open[r["first_buy_sig"]] >= DEC1]
    rng = random.Random(SEED)
    picked = rng.sample(early, 40) + rng.sample(late, 20)
    return [
        {
            "group": "FRESH",
            "wallet": r["wallet"],
            "mint": r["mint"],
            "t_open": t_open[r["first_buy_sig"]],
            "class": r["class_frozen"],
            "closed": r["closed"] == "True",
            "realised_sol": int(r["realised_lamports"]) / 1e9,
            "first_buy_sig": r["first_buy_sig"],
            "period": "oct_nov" if t_open[r["first_buy_sig"]] < DEC1 else "dec",
        }
        for r in picked
    ]


def own_level(trip: dict[str, Any]) -> Optional[int]:
    """Curve level after the author's first buy, from its event in the raw transaction: no network."""
    with open(CACHE / (trip["first_buy_sig"] + ".json")) as f:
        d = D.decode(json.load(f)["result"])
    for e in d.trade_events:
        if e["buy"] and e["user"] == trip["wallet"] and e["mint"] == trip["mint"]:
            return e["rsol"]
    return None


def extras(read: dict[str, Any], c: Any, buyers: dict[str, Any]) -> dict[str, Any]:
    """S1 without creators, and the negative control: first transaction a direct credit from a labelled exchange hot wallet."""
    sx = False
    for b in read["buyers_checked"]:
        r = read_buyer(c, b["buyer"], buyers)
        sx = sx or bool(set(r.get("first_funders") or []) & EXCHANGES)
    return {
        "S1_no_creator": any(b["s1"] and not b["is_creator"] for b in read["buyers_checked"]),
        "S1_creator": any(b["s1"] and b["is_creator"] for b in read["buyers_checked"]),
        "Sx": sx,
    }


def find_control(
    c: Any,
    trip: dict[str, Any],
    cband: str,
    aband: str,
    own: set[str],
    own_mints: set[str],
    used: set[str],
    mints: dict[str, Any],
) -> Optional[dict[str, Any]]:
    tried = 0
    for page in range(3):
        start = trip["t_open"] + page * 1200
        r = c.call(
            "getTransactionsForAddress",
            [
                D.PUMP,
                {
                    "transactionDetails": "full",
                    "sortOrder": "asc",
                    "limit": 100,
                    "encoding": "json",
                    "maxSupportedTransactionVersion": 1,
                    "filters": {
                        "tokenAccounts": "none",
                        "status": "succeeded",
                        "blockTime": {"gte": start, "lte": trip["t_open"] + 3600},
                    },
                },
            ],
            D.PUMP,
            credits=10,
        )
        for item in r.get("data") or []:
            d = D.decode(item)
            for e in d.trade_events:
                if (
                    not e["buy"]
                    or e["user"] in own
                    or e["mint"] in own_mints
                    or e["mint"] in used
                    or curve_band(e["rsol"]) != cband
                ):
                    continue
                if tried >= 4:
                    return None
                tried += 1
                used.add(e["mint"])
                m = read_mint(c, e["mint"], d.block_time or 0, mints)
                if m["t_create"] and age_band((d.block_time or 0) - m["t_create"]) == aband:
                    return {
                        "group": "MATCH",
                        "wallet": e["user"],
                        "mint": e["mint"],
                        "t_open": d.block_time,
                        "class": None,
                        "closed": False,
                        "realised_sol": 0.0,
                        "buy_sig": d.signature,
                    }
    return None


def collect(credits: int) -> int:
    c = client(credits)
    c.store_bodies = False  # results and signatures are kept: bodies would only fill the work area
    path = PRIVATE / OUT
    state: dict[str, Any] = (
        json.loads(path.read_text()) if path.exists() else {"positive_control": [], "pairs": [], "dropped": []}
    )
    own = set(ledger()["candidates"])
    with open(PRIVATE / "TRADES_V2.csv") as f:
        own_mints = {r["mint"] for r in csv.DictReader(f)}
    mints: dict[str, Any] = {}
    buyers: dict[str, Any] = {}
    if not state["positive_control"]:
        known = [t for t in json.loads((PRIVATE / "PATTERN_MATCHES.json").read_text())["trips"] if t["group"] == "A" and t["S1"]][
            :2
        ]
        for t in known:
            again = classify({**t, "class": t.get("class_frozen")}, read_mint(c, t["mint"], t["t_open"], mints), c, buyers)
            state["positive_control"].append({"mint": t["mint"], "S1": again["S1"]})
        write_private(OUT, json.dumps(state, indent=1))
        if not all(x["S1"] for x in state["positive_control"]):
            print("positive control failed", state["positive_control"])
            return 1
    done = {(p["trip"]["wallet"], p["trip"]["mint"]) for p in state["pairs"]} | {
        (x["wallet"], x["mint"]) for x in state["dropped"]
    }
    used = {p["control"]["mint"] for p in state["pairs"]}
    stopped = None
    for t in fresh_sample():
        if (t["wallet"], t["mint"]) in done:
            continue
        try:
            m = read_mint(c, t["mint"], t["t_open"], mints)
            cband, aband = curve_band(own_level(t)), age_band(t["t_open"] - m["t_create"] if m["t_create"] else None)
            if cband is None or aband is None:
                state["dropped"].append(
                    {"wallet": t["wallet"], "mint": t["mint"], "why": "no curve level or age", "period": t["period"]}
                )
                continue
            pick = find_control(c, t, cband, aband, own, own_mints, used, mints)
            if pick is None:
                state["dropped"].append(
                    {
                        "wallet": t["wallet"],
                        "mint": t["mint"],
                        "why": "no match",
                        "period": t["period"],
                        "curve": cband,
                        "age": aband,
                    }
                )
                continue
            rt = classify(t, m, c, buyers)
            rc = classify(pick, read_mint(c, pick["mint"], pick["t_open"], mints), c, buyers)
            state["pairs"].append(
                {
                    "period": t["period"],
                    "curve": cband,
                    "age": aband,
                    "trip": {**rt, **extras(rt, c, buyers)},
                    "control": {**rc, **extras(rc, c, buyers), "buy_sig": pick["buy_sig"]},
                }
            )
        except RpcError as e:  # credits or quota: keep the finished pairs
            stopped = str(e)[:140]
            print("stopped", stopped, flush=True)
            break
        write_private(OUT, json.dumps(state, indent=1))
        print(len(state["pairs"]), "pairs", len(state["dropped"]), "dropped, net", c.net_calls, flush=True)
    state["stopped"] = stopped
    write_private(OUT, json.dumps(state, indent=1))
    print({"pairs": len(state["pairs"]), "dropped": len(state["dropped"]), "stopped": stopped, "net": c.net_calls})
    return 0


def paired(pairs: list[dict[str, Any]], key: str) -> dict[str, Any]:
    both = sum(p["trip"][key] and p["control"][key] for p in pairs)
    b = sum(p["trip"][key] and not p["control"][key] for p in pairs)
    c = sum(p["control"][key] and not p["trip"][key] for p in pairs)
    return {
        "n": len(pairs),
        "author": both + b,
        "control": both + c,
        "only_author": b,
        "only_control": c,
        "p": mcnemar_exact(b, c),
    }


def analyse() -> int:
    s = json.loads((PRIVATE / OUT).read_text())
    early = [p for p in s["pairs"] if p["period"] == "oct_nov"]
    late = [p for p in s["pairs"] if p["period"] == "dec"]
    t1 = paired(early, "S1")
    a, b = sum(p["trip"]["S1"] for p in early), len(early) - sum(p["trip"]["S1"] for p in early)
    x, y = sum(p["trip"]["S1"] for p in late), len(late) - sum(p["trip"]["S1"] for p in late)
    t2 = _fisher_two_sided(a, b, x, y)
    adj = holm([t1["p"], t2])
    res = {
        "plan": "docs/PLAN_signal_matched.md",
        "positive_control": s["positive_control"],
        "pairs": len(s["pairs"]),
        "dropped": s["dropped"],
        "stopped": s.get("stopped"),
        "T1_oct_nov_S1": {**t1, "p_holm": adj[0]},
        "T2_author_oct_nov_vs_dec": {"oct_nov": [a, len(early)], "dec": [x, len(late)], "p": t2, "p_holm": adj[1]},
        "dec_pairs_S1": paired(late, "S1"),
        "oct_nov_S1_no_creator": paired(early, "S1_no_creator"),
        "dec_S1_no_creator": paired(late, "S1_no_creator"),
        "oct_nov_S1_creator": paired(early, "S1_creator"),
        "oct_nov_Sx": paired(early, "Sx"),
        "dec_Sx": paired(late, "Sx"),
        "S2_oct_nov": paired(early, "S2"),
        "S2_dec": paired(late, "S2"),
    }
    write_private("trade_context/matched_v2_results.json", json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "dropped"}, indent=0))
    print("dropped", len(s["dropped"]))
    return 0


if __name__ == "__main__":
    sys.exit(collect(int(sys.argv[2])) if sys.argv[1] == "collect" else analyse())
