"""Do the wallets not established behave like the author's other wallets? Plan: docs/PLAN_same_operator.md. Output is private.

python -m forensics_v2.investigations.same_operator controls <credits>
python -m forensics_v2.investigations.same_operator analyse
"""

from __future__ import annotations

import bisect
import csv
import gzip
import json
import math
import random
import sys
from collections import Counter, defaultdict
from typing import Any, Iterable, Optional

from .. import decode as D
from ..decode import JITO_TIP
from ..rpc import RpcError
from .trades_2024 import DEPOSIT, G2Y, HOT, PRIVATE, ledger, write_private
from .trades_ledger import ROWS, row_from_raw
from .trades_report import PUMP_FEE, TOOL_FEE

SEED = 20261105
T_FROM, T_TO = 1726358400, 1738281600  # 2024-09-15, 2025-01-31
N_CONTROLS = 30
WINDOW_S = 24 * 3600
BIN_S = 600
MIN_TRADES = 10
OUT_CONTROLS = "same_operator/controls.jsonl"
OUT_RESULTS = "same_operator/results.json"


def events(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Trades through the bot, each with the tip paid in the wallet's own transactions of that slot and its fee above the base."""
    rows = list(rows)
    tips: Counter[tuple[str, int]] = Counter()
    for r in rows:
        if r["ok"]:
            tips[(r["w"], r["slot"])] += sum(
                m["n"] for m in r["moves"] if m["k"] == "sol_transfer" and m["src"] == r["w"] and m["dst"] in JITO_TIP
            )
    out = []
    for r in rows:
        if not r["ok"] or not r["tok"] or not any(m["k"] == "sol_transfer" and m["dst"] == TOOL_FEE for m in r["moves"]):
            continue
        out.append(
            {
                "w": r["w"],
                "t": r["t"],
                "side": "buy" if any(v > 0 for v in r["tok"].values()) else "sell",
                "tip": tips[(r["w"], r["slot"])],
                "prio": r["fee"] - 5000 * len(r["signers"]),
            }
        )
    return out


class Reference:
    """The reference wallets' trades, without the wallet measured."""

    def __init__(self, ev: Iterable[dict[str, Any]]):
        self.by_side: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.bins: Counter[int] = Counter()
        self.by_wallet_bins: dict[str, Counter[int]] = defaultdict(Counter)
        for e in ev:
            self.by_side[e["side"]].append(e)
            self.bins[e["t"] // BIN_S] += 1
            self.by_wallet_bins[e["w"]][e["t"] // BIN_S] += 1
        for v in self.by_side.values():
            v.sort(key=lambda e: e["t"])
        self.times = {k: [e["t"] for e in v] for k, v in self.by_side.items()}

    def nearest(self, e: dict[str, Any]) -> Optional[dict[str, Any]]:
        best = None
        side = self.by_side.get(e["side"], [])
        i = bisect.bisect_left(self.times.get(e["side"], []), e["t"])
        j, k = i - 1, i
        # shortcut: skips the wallet itself by walking outwards, slow only if a wallet holds a long run of the reference
        while j >= 0 or k < len(side):
            a = side[j] if j >= 0 else None
            b = side[k] if k < len(side) else None
            pick = a if b is None or (a is not None and e["t"] - a["t"] <= b["t"] - e["t"]) else b
            if abs(pick["t"] - e["t"]) > WINDOW_S:
                return best
            if pick["w"] != e["w"]:
                return pick
            if pick is a:
                j -= 1
            else:
                k += 1
        return best

    def active(self, b: int, leave_out: str) -> bool:
        return self.bins[b] > self.by_wallet_bins[leave_out][b] if leave_out in self.by_wallet_bins else self.bins[b] > 0


def measure(ev: list[dict[str, Any]], ref: Reference) -> dict[str, Any]:
    tip = prio = n = 0
    for e in ev:
        o = ref.nearest(e)
        if o is None:
            continue
        n += 1
        tip += e["tip"] == o["tip"]
        prio += e["prio"] == o["prio"]
    wallet = ev[0]["w"] if ev else ""
    bins = {e["t"] // BIN_S for e in ev}
    shared = sum(ref.active(b, wallet) for b in bins)
    return {
        "trades": len(ev),
        "comparable": n,
        "M1_tip": tip / n if n else None,
        "M1_prio": prio / n if n else None,
        "bins": len(bins),
        "M2": shared / len(bins) if bins else None,
    }


def percentile(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[max(0, math.ceil(q * len(s)) - 1)]


def control_moments() -> list[int]:
    rng = random.Random(SEED)
    return sorted(rng.randrange(T_FROM, T_TO) for _ in range(N_CONTROLS))


def collect_controls(credits: int) -> int:
    from ..__main__ import client

    c = client(credits)
    c.store_bodies = False
    own = set(ledger()["candidates"])
    own |= {r["wallet"] for r in json.loads((PRIVATE / "derived/outside_wallets_read.json").read_text())}
    own |= {
        r["wallet"]
        for r in json.loads((PRIVATE / "WALLET_CANDIDATES_EXPANDED.json").read_text())["rows"]
        if isinstance(r, dict) and "wallet" in r
    }
    path = PRIVATE / OUT_CONTROLS
    path.parent.mkdir(mode=0o700, exist_ok=True)
    state = [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    done = {s["moment"] for s in state}
    used = {s["wallet"] for s in state if s["wallet"]}
    stop = None
    for moment in control_moments():
        if moment in done:
            continue
        try:
            r = c.call(
                "getTransactionsForAddress",
                [
                    TOOL_FEE,
                    {
                        "transactionDetails": "full",
                        "sortOrder": "asc",
                        "limit": 100,
                        "encoding": "json",
                        "maxSupportedTransactionVersion": 1,
                        "filters": {
                            "tokenAccounts": "none",
                            "status": "succeeded",
                            "blockTime": {"gte": moment, "lte": moment + 3600},
                        },
                    },
                ],
                TOOL_FEE,
                credits=10,
            )
            wallet = None
            for item in r.get("data") or []:
                d = D.decode(item)
                if d.fee_payer in own or d.fee_payer in used or not D.traded_mints(d, d.fee_payer):
                    continue
                wallet = d.fee_payer
                break
            rows: list[dict[str, Any]] = []
            walk_stop = None
            if wallet:
                raw, walk = c.history_txs(wallet, moment - 3 * 86400, moment + 7 * 86400, "none", 3)
                walk_stop = walk.stop
                rows = [row_from_raw(wallet, x["transaction"]["signatures"][0], x) for x in raw]
                used.add(wallet)
        except RpcError as e:  # credits or quota: keep what was read, as the plan says
            stop = str(e)[:140]
            print("stopped", stop, flush=True)
            break
        with open(path, "a") as f:
            f.write(
                json.dumps({"moment": moment, "wallet": wallet, "walk_stop": walk_stop, "rows": rows}, separators=(",", ":"))
                + "\n"
            )
        print(moment, wallet, len(rows), "net", c.net_calls, flush=True)
    print({"controls": len(used), "stopped": stop, "net": c.net_calls})
    return 0


def own_rows() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with gzip.open(ROWS, "rt") as f:
        for line in f:
            r = json.loads(line)
            out[r["w"]].append(r)
    return out


def shared_links(level: dict[str, str]) -> dict[str, Any]:
    """Funders and destinations shared by a wallet not established and a reference wallet, services left out. No test."""
    skip = (
        {HOT, DEPOSIT, G2Y, TOOL_FEE, PUMP_FEE} | set(JITO_TIP) | {w for w, v in level.items() if v == "EXCLUDED_INFRASTRUCTURE"}
    )
    funded: dict[str, set[str]] = defaultdict(set)
    paid: dict[str, set[str]] = defaultdict(set)
    amounts: Counter[tuple[str, str]] = Counter()
    for name in ("INTERNAL.csv", "EXTERNAL.csv"):
        with open(PRIVATE / name) as f:
            for r in csv.DictReader(f):
                if int(r["lamports"]) < 10_000_000:
                    continue
                amounts[(r["from"], r["to"])] += int(r["lamports"])
                if r["to"] in level and r["from"] not in skip:
                    funded[r["from"]].add(r["to"])
                if r["from"] in level and r["to"] not in skip:
                    paid[r["to"]].add(r["from"])

    def rows(m: dict[str, set[str]], funder: bool) -> list[dict[str, Any]]:
        res = []
        for a, ws in m.items():
            ne = [w for w in ws if level[w] == "NOT_ESTABLISHED"]
            cp = [w for w in ws if level[w] in ("CERTAIN", "PROBABLE")]
            if ne and cp:
                res.append(
                    {
                        "via": a,
                        "via_level": level.get(a, "OUTSIDE"),
                        "not_established": ne,
                        "certain_or_probable": cp,
                        "sol": {w: round(amounts[(a, w) if funder else (w, a)] / 1e9, 3) for w in ne + cp},
                    }
                )
        return res

    return {"shared_funders": rows(funded, True), "shared_destinations": rows(paid, False)}


def timeline(ev_by_wallet: dict[str, list[dict[str, Any]]], level: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for w, ev in ev_by_wallet.items():
        if ev:
            rows.append(
                {
                    "wallet": w,
                    "level": level.get(w),
                    "first": min(e["t"] for e in ev),
                    "last": max(e["t"] for e in ev),
                    "trades": len(ev),
                }
            )
    return sorted(rows, key=lambda r: r["first"])


def analyse() -> int:
    with open(PRIVATE / "WALLETS_V2.csv") as f:
        level = {r["wallet"]: r["level"] for r in csv.DictReader(f)}
    rows = own_rows()
    ev_by = {w: events(rs) for w, rs in rows.items()}
    ref_wallets = [w for w, v in level.items() if v in ("CERTAIN", "PROBABLE")]
    ref = Reference(e for w in ref_wallets for e in ev_by.get(w, []))

    negatives = {}
    for line in (PRIVATE / OUT_CONTROLS).read_text().splitlines():
        s = json.loads(line)
        if s["wallet"]:
            negatives[s["wallet"]] = measure(events(s["rows"]), ref)
    usable = {w: m for w, m in negatives.items() if m["comparable"] >= MIN_TRADES}
    limits = {}
    if usable:
        for k in ("M1_tip", "M1_prio"):
            limits[k] = percentile([m[k] for m in usable.values()], 0.95)
        limits["M2"] = percentile([m["M2"] for m in usable.values()], 0.05)

    def beats(m: dict[str, Any], k: str) -> bool:
        if k == "M2":
            return m[k] is not None and m[k] < limits[k]
        return m[k] is not None and m[k] > limits[k]

    wallets = {w: measure(ev_by.get(w, []), ref) for w in level if ev_by.get(w)}
    certain = [w for w, v in level.items() if v == "CERTAIN"]
    qualifying = []
    positive = {}
    for k in ("M1_tip", "M1_prio", "M2"):
        ok = [w for w in certain if w in wallets and wallets[w]["comparable"] >= MIN_TRADES and limits and beats(wallets[w], k)]
        positive[k] = {
            "beat": len(ok),
            "enough": sum(1 for w in certain if w in wallets and wallets[w]["comparable"] >= MIN_TRADES),
        }
        if len(ok) >= 6:
            qualifying.append(k)

    def verdict(m: dict[str, Any]) -> str:
        if m["comparable"] < MIN_TRADES:
            return "insufficient"
        return "matches" if all(beats(m, k) for k in qualifying) else "does not match"

    table = []
    for w, m in wallets.items():
        if level[w] == "EXCLUDED_INFRASTRUCTURE":
            continue
        table.append({"wallet": w, "level": level[w], **m, "verdict": verdict(m) if qualifying else "test cannot tell"})
    res = {
        "plan": "docs/PLAN_same_operator.md",
        "negative_controls_read": len(negatives),
        "negative_controls_usable": len(usable),
        "limits_from_negatives": limits,
        "positive_control": positive,
        "qualifying_measures": qualifying,
        "wallets": sorted(table, key=lambda r: (r["level"], -r["trades"])),
        "negatives": negatives,
        "timeline": timeline({w: ev_by.get(w, []) for w in level}, level),
        **shared_links(level),
    }
    write_private(OUT_RESULTS, json.dumps(res, indent=1))
    print(
        json.dumps(
            {
                k: res[k]
                for k in (
                    "negative_controls_read",
                    "negative_controls_usable",
                    "limits_from_negatives",
                    "positive_control",
                    "qualifying_measures",
                )
            },
            indent=0,
        )
    )
    return 0


if __name__ == "__main__":
    a = sys.argv
    raise SystemExit(collect_controls(int(a[2])) if a[1] == "controls" else analyse())
