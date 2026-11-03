"""Does the signal survive a match on the token's popularity? Plan: docs/PLAN_signal_popularity.md. Output is private.

python -m forensics_v2.investigations.signal_popularity collect <credits>
python -m forensics_v2.investigations.signal_popularity analyse
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path
from typing import Any, Optional

from .. import decode as D
from .. import storage
from ..__main__ import client
from ..rpc import RpcError
from .signal_matched import DEC1, age_band, curve_band, extras, mcnemar_exact, own_level, paired, unread_curve_trips
from .trade_context import classify, read_mint
from .trades_2024 import PRIVATE, ledger, write_private

SEED = 20261105
N_TRIPS = 40
MAX_CANDIDATES = 8
MAX_PAGES = 4
OUT = "trade_context/popularity.json"
OLD = "trade_context/matched_v2.json"
PATTERN = "PATTERN_MATCHES.json"


def t200_band(n_tx: int, stop: Optional[str], seconds: Optional[int]) -> Optional[str]:
    """Time from a mint's first transaction to its 200th. A history that ends first is its own band."""
    if stop == "genesis" and n_tx < 200:
        return "under_200"
    if n_tx < 200 or seconds is None or seconds < 0:
        return None
    return "a_1m" if seconds < 60 else "b_10m" if seconds < 600 else "c_1h" if seconds < 3600 else "d_more"


def mint_band(m: dict[str, Any]) -> Optional[str]:
    start = m["t_create"]
    return t200_band(m["n_tx"], m["stop"], (m["last_t"] - start) if m["last_t"] and start else None)


def mints_read() -> set[str]:
    """Every token whose launch any earlier group of this work read, so that the new sample has none, as the plan asks."""
    seen = {t["mint"] for t in json.loads((PRIVATE / PATTERN).read_text())["trips"]}
    old = json.loads((PRIVATE / OLD).read_text())
    for p in old["pairs"]:
        seen |= {p["trip"]["mint"], p["control"]["mint"]}
    seen |= {x["mint"] for x in old["dropped"]}
    cfg = json.loads(storage.CONFIG.read_text())
    for r in (cfg["cold_root"], cfg["data_root"]):
        f = Path(r) / "intermediate/trade_context_group_x.json"
        if f.exists():
            seen |= {t["mint"] for t in json.loads(f.read_text())["trips"]}
            break
    else:
        raise SystemExit("group X's list not found: the new sample could hold a token already read")
    return seen


def sample() -> list[dict[str, Any]]:
    rows, t_open = unread_curve_trips()
    with open(PRIVATE / "WALLETS_V2.csv") as f:
        level = {r["wallet"]: r["level"] for r in csv.DictReader(f)}
    read = mints_read()
    pool = [
        r
        for r in rows
        if t_open[r["first_buy_sig"]] < DEC1 and level.get(r["wallet"]) in ("CERTAIN", "PROBABLE") and r["mint"] not in read
    ]
    picked = random.Random(SEED).sample(pool, N_TRIPS)
    print("pool", len(pool), flush=True)
    return [
        {
            "group": "FRESH2",
            "wallet": r["wallet"],
            "mint": r["mint"],
            "t_open": t_open[r["first_buy_sig"]],
            "class": r["class_frozen"],
            "closed": r["closed"] == "True",
            "realised_sol": int(r["realised_lamports"]) / 1e9,
            "first_buy_sig": r["first_buy_sig"],
            "period": "oct_nov",
        }
        for r in picked
    ]


def find_control(
    c: Any,
    trip: dict[str, Any],
    cband: str,
    aband: str,
    pband: str,
    own: set[str],
    own_mints: set[str],
    used: set[str],
    mints: dict[str, Any],
) -> Optional[dict[str, Any]]:
    tried = 0
    for page in range(MAX_PAGES):
        start = trip["t_open"] + page * 900
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
                if tried >= MAX_CANDIDATES:
                    return None
                tried += 1
                used.add(e["mint"])
                m = read_mint(c, e["mint"], d.block_time or 0, mints)
                if m["t_create"] and age_band((d.block_time or 0) - m["t_create"]) == aband and mint_band(m) == pband:
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
    c.store_bodies = False
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
        known = [t for t in json.loads((PRIVATE / PATTERN).read_text())["trips"] if t["group"] == "A" and t["S1"]][:2]
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
    for t in sample():
        if (t["wallet"], t["mint"]) in done:
            continue
        try:
            m = read_mint(c, t["mint"], t["t_open"], mints)
            cband, aband, pband = (
                curve_band(own_level(t)),
                age_band(t["t_open"] - m["t_create"] if m["t_create"] else None),
                mint_band(m),
            )
            if cband is None or aband is None or pband is None:
                state["dropped"].append(
                    {"wallet": t["wallet"], "mint": t["mint"], "why": "no curve level, age or T200", "period": t["period"]}
                )
                continue
            pick = find_control(c, t, cband, aband, pband, own, own_mints, used, mints)
            if pick is None:
                state["dropped"].append(
                    {
                        "wallet": t["wallet"],
                        "mint": t["mint"],
                        "why": "no match",
                        "period": t["period"],
                        "curve": cband,
                        "age": aband,
                        "t200": pband,
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
                    "t200": pband,
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


def checkpoint_band(mint: str) -> Optional[str]:
    """T200 band of an old pair's mint, from the pages already saved: no network."""
    cfg = json.loads(storage.CONFIG.read_text())
    for root in (cfg["data_root"], cfg["cold_root"]):
        f = Path(root) / "checkpoints/gtfa" / ("%s_start_end_none.jsonl" % mint)
        if not f.exists():
            continue
        sigs, ended = [], False
        with open(f) as fh:
            for line in fh:
                r = json.loads(line)
                sigs += r["sigs"]
                ended = r["next"] is None
        ts = [s["blockTime"] for s in sigs if s.get("blockTime")]
        if not ts:
            return None
        return t200_band(len(sigs), "genesis" if ended else "max_pages", ts[-1] - ts[0])
    return None


def perimeter_signal_only(side: dict[str, Any], own: set[str]) -> bool:
    return side["S1"] and not any(b["s1"] and b["buyer"] not in own for b in side["buyers_checked"])


def analyse() -> int:
    own = set(ledger()["candidates"])
    with open(PRIVATE / "WALLETS_V2.csv") as f:
        level = {r["wallet"]: r["level"] for r in csv.DictReader(f)}
    old = json.loads((PRIVATE / OLD).read_text())
    early = [p for p in old["pairs"] if p["period"] == "oct_nov"]
    read_before = {t["mint"] for t in json.loads((PRIVATE / PATTERN).read_text())["trips"]}
    for p in early:
        p["t200"] = [checkpoint_band(p["trip"]["mint"]), checkpoint_band(p["control"]["mint"])]
        p["ne"] = level.get(p["trip"]["wallet"]) == "NOT_ESTABLISHED"
        p["read_before"] = p["trip"]["mint"] in read_before
        p["perimeter_only"] = perimeter_signal_only(p["trip"], own)

    def recount(pairs: list[dict[str, Any]], drop_perimeter: bool = False) -> dict[str, Any]:
        def s1(p: dict[str, Any], k: str) -> bool:
            return p[k]["S1"] and not (drop_perimeter and k == "trip" and p["perimeter_only"])

        b = sum(s1(p, "trip") and not s1(p, "control") for p in pairs)
        c = sum(s1(p, "control") and not s1(p, "trip") for p in pairs)
        return {
            "n": len(pairs),
            "trips": sum(s1(p, "trip") for p in pairs),
            "controls": sum(s1(p, "control") for p in pairs),
            "p_uncorrected": mcnemar_exact(b, c),
        }

    same = [p for p in early if p["t200"][0] and p["t200"][0] == p["t200"][1]]
    by_band: dict[str, dict[str, int]] = {}
    for p in early:
        for side, band in (("trip", p["t200"][0]), ("control", p["t200"][1])):
            e = by_band.setdefault("%s:%s" % (side, band), {"n": 0, "S1": 0})
            e["n"] += 1
            e["S1"] += p[side]["S1"]
    keep = [p for p in early if not p["ne"] and not p["read_before"]]
    part1 = {
        "status": "exploratory, same observations as T1, never a confirmation",
        "band_known": sum(bool(p["t200"][0] and p["t200"][1]) for p in early),
        "by_band": by_band,
        "n_large_before_mean": {k: sum(p[k]["n_large_before"] for p in early) / len(early) for k in ("trip", "control")},
        "buyers_checked_mean": {k: sum(len(p[k]["buyers_checked"]) for p in early) / len(early) for k in ("trip", "control")},
        "all_pairs": recount(early),
        "same_t200_band": recount(same),
        "without_not_established": recount([p for p in early if not p["ne"]]),
        "without_tokens_read_before": recount([p for p in early if not p["read_before"]]),
        "without_perimeter_signal": recount(early, True),
        "all_filters": recount([p for p in keep if p["t200"][0] and p["t200"][0] == p["t200"][1]], True),
        "deviating_pairs": [
            {"mint": p["trip"]["mint"], "wallet": p["trip"]["wallet"], "S1": p["trip"]["S1"], "control_S1": p["control"]["S1"]}
            for p in early
            if p["read_before"]
        ],
        "perimeter_only_pairs": [
            {"mint": p["trip"]["mint"], "wallet": p["trip"]["wallet"]} for p in early if p["perimeter_only"]
        ],
    }
    res: dict[str, Any] = {"plan": "docs/PLAN_signal_popularity.md", "part1": part1}
    path = PRIVATE / OUT
    if path.exists():
        s = json.loads(path.read_text())
        pairs = s["pairs"]
        t = paired(pairs, "S1")
        x = paired(pairs, "Sx")
        gap, gapx = t["author"] - t["control"], x["author"] - x["control"]
        reading = (
            "not confirmed"
            if not (t["p"] < 0.05 and gap > 0)
            else "confirmed once popularity is matched"
            if abs(gapx) < gap / 2
            else "not specific to the gateway"
        )
        res["part2"] = {
            "positive_control": s["positive_control"],
            "pairs": len(pairs),
            "dropped": len(s["dropped"]),
            "dropped_why": [d["why"] for d in s["dropped"]],
            "stopped": s.get("stopped"),
            "T1b": t,
            "Sx": x,
            "S1_no_creator": paired(pairs, "S1_no_creator"),
            "S1_creator": paired(pairs, "S1_creator"),
            "perimeter_only_on_trips": sum(perimeter_signal_only(p["trip"], own) for p in pairs),
            "window_covers_entry": {k: sum(p[k]["window_covers_entry"] for p in pairs) for k in ("trip", "control")},
            "reading_from_the_plan": reading,
        }
    write_private("trade_context/popularity_results.json", json.dumps(res, indent=1))
    print(json.dumps(res, indent=0))
    return 0


if __name__ == "__main__":
    raise SystemExit(collect(int(sys.argv[2])) if sys.argv[1] == "collect" else analyse())
