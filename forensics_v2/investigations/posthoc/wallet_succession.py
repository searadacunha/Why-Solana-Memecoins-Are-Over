"""Do the author's wallets take over from one another? Post hoc: the idea came from a first look at the dates. Output is private, no network.

Lists each wallet's first and last trade, the money between one wallet's last deposit and the next one's first credit, and how often a block of
wallets not established would fit between two reference wallets if it were placed at random. Exploratory, never a test of the rule in
docs/PLAN_attribution_2024.md, and it changes no level.

    python -m forensics_v2.investigations.posthoc.wallet_succession
"""

import csv
import json
from typing import Any

from ..same_operator import events, own_rows
from ..trades_2024 import DEPOSIT, HOT, PRIVATE, write_private

MIN_TRADES = 5


def intervals(ev_by: dict[str, list[dict[str, Any]]], level: dict[str, str]) -> list[dict[str, Any]]:
    out = []
    for w, ev in ev_by.items():
        if len(ev) >= MIN_TRADES:
            ts = [e["t"] for e in ev]
            out.append({"wallet": w, "level": level.get(w), "first": min(ts), "last": max(ts), "trades": len(ev)})
    return sorted(out, key=lambda r: r["first"])


def gaps(first: int, last: int, ref: list[dict[str, Any]]) -> tuple[int | None, int | None, int]:
    """Time since the latest reference wallet stopped, time until the next one starts, reference wallets running meanwhile."""
    before = [first - r["last"] for r in ref if r["last"] <= first]
    after = [r["first"] - last for r in ref if r["first"] >= last]
    overlap = sum(1 for r in ref if r["first"] < last and r["last"] > first)
    return min(before) if before else None, min(after) if after else None, overlap


def placed_at_random(first: int, last: int, ref: list[dict[str, Any]], step: int = 60) -> dict[str, Any]:
    """Share of positions of the same duration, on a one-minute grid, that fit at least as tightly, with no more wallets running."""
    b0, a0, o0 = gaps(first, last, ref)
    t0, t1 = min(r["first"] for r in ref), max(r["last"] for r in ref)
    span = last - first
    n = hits = 0
    for start in range(t0, t1 - span, step):
        b, a, o = gaps(start, start + span, ref)
        n += 1
        if b is not None and a is not None and b0 is not None and a0 is not None and b <= b0 and a <= a0 and o <= o0:
            hits += 1
    return {
        "gap_before_s": b0,
        "gap_after_s": a0,
        "running_meanwhile": o0,
        "positions": n,
        "as_tight": hits,
        "share": hits / n if n else None,
    }


def capital(rows: dict[str, list[dict[str, Any]]], order: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """For each wallet: its first credits and its last deposit, with signatures."""
    out = []
    for r in order:
        w = r["wallet"]
        credits, deposits = [], []
        for x in sorted(rows[w], key=lambda x: (x["slot"], x["t"])):
            for s, d, n, _ in x["edges"]:
                if d == w and n >= 10_000_000 and len(credits) < 3:
                    credits.append({"t": x["t"], "from": s, "sol": n / 1e9, "sig": x["sig"], "hot": s == HOT})
                if s == w and d == DEPOSIT and n >= 10_000_000:
                    deposits.append({"t": x["t"], "sol": n / 1e9, "sig": x["sig"]})
        out.append({**r, "first_credits": credits, "last_deposits": deposits[-2:]})
    return out


def main() -> int:
    with open(PRIVATE / "WALLETS_V2.csv") as f:
        level = {r["wallet"]: r["level"] for r in csv.DictReader(f)}
    rows = own_rows()
    ev_by = {w: events(rs) for w, rs in rows.items()}
    order = intervals(ev_by, level)
    ref = [r for r in order if r["level"] in ("CERTAIN", "PROBABLE")]
    assert gaps(10, 20, [{"first": 0, "last": 5}, {"first": 30, "last": 40}]) == (5, 10, 0)

    def block(prefixes: tuple[str, ...]) -> dict[str, Any]:
        ws = [r for r in order if r["wallet"].startswith(prefixes)]
        first, last = min(r["first"] for r in ws), max(r["last"] for r in ws)
        return {"wallets": [r["wallet"] for r in ws], "first": first, "last": last, **placed_at_random(first, last, ref)}

    groups = json.loads((PRIVATE / "same_operator/blocks.json").read_text())  # private: which wallets share a relay
    grouped = {w for ws in groups.values() for w in ws}
    ne = [r for r in order if r["level"] == "NOT_ESTABLISHED" and r["wallet"][:8] not in grouped]
    res = {
        "status": "exploratory, post hoc: the idea came from a first look at these dates",
        "reference_wallets": len(ref),
        "blocks": {
            **{name: block(tuple(ws)) for name, ws in groups.items()},
            **{r["wallet"][:8]: block((r["wallet"][:8],)) for r in ne},
        },
        # the same reading on each reference wallet against the others: the base rate of fitting tightly
        "reference_against_others": {
            r["wallet"][:8]: placed_at_random(r["first"], r["last"], [x for x in ref if x["wallet"] != r["wallet"]]) for r in ref
        },
        "capital": capital(rows, order),
    }
    write_private("same_operator/succession.json", json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
