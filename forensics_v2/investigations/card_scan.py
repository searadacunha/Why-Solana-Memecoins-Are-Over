"""Find the trade behind a PnL card by scanning every owner that traded the card's mint.

A card shows invested SOL, gain and holding time. The wallet is whoever matches, if anyone does. A
match is a candidate, not an identity: several traders can fit, and the score only counts how many of
the three independent figures agree. Output is private (forensics_v2/private_trades/).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from .. import decode as D
from ..__main__ import client
from ..trace import history
from .trades_2024 import STUDY, write_private


def owner_trips(txs: list[D.Decoded], mint: str) -> dict[str, list[dict[str, Any]]]:
    """Trips of every owner of `mint` in these transactions, SOL including wrapped SOL and rent."""
    legs: dict[str, list[tuple[Optional[int], int, int, str, list[str]]]] = defaultdict(list)
    for d in txs:
        if not d.ok:
            continue
        for owner, n in d.owners.items():
            tok = n.tokens.get(mint, 0)
            if tok:
                sol = n.sol
                legs[owner].append((d.block_time, tok, sol, d.signature, d.venues))
    out: dict[str, list[dict[str, Any]]] = {}
    for owner, rows in legs.items():
        rows.sort(key=lambda r: r[0] or 0)
        trips: list[dict[str, Any]] = []
        cur: Optional[dict[str, Any]] = None
        hold = 0
        for t, tok, sol, sig, venues in rows:
            if tok > 0 and sol < 0 and cur is None:
                cur = {"t_open": t, "t_close": None, "sol_out": 0, "sol_in": 0, "bought": 0, "sigs": [], "venues": set()}
            hold += tok
            if cur is None:
                continue
            cur["sigs"].append(sig)
            cur["venues"].update(venues)
            if tok > 0 and sol < 0:
                cur["sol_out"] -= sol
                cur["bought"] += tok
            elif tok < 0 and sol > 0:
                cur["sol_in"] += sol
                cur["t_close"] = t
            if cur["bought"] and hold * 1000 <= cur["bought"]:
                trips.append(cur)
                cur, hold = None, 0
        if cur:
            trips.append(cur)
        out[owner] = trips
    return out


def _held_seconds(text: str) -> int:
    import re
    return sum(int(n) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u] for n, u in re.findall(r"(\d+)\s*([dhms])", text))


def score(trip: dict[str, Any], inv: float, gain: float, held: int) -> dict[str, Any]:
    sol_out, realised = trip["sol_out"] / 1e9, (trip["sol_in"] - trip["sol_out"]) / 1e9
    dur = (trip["t_close"] - trip["t_open"]) if trip["t_close"] else None
    hits = {
        "invested": abs(sol_out - inv) <= max(0.03 * inv, 0.02),
        "gain": abs(realised - gain) <= 0.05 * abs(gain),
        "held": dur is not None and abs(dur - held) <= max(0.10 * held, 120),
    }
    return {"hits": hits, "n": sum(hits.values()), "sol_out": sol_out, "realised": realised, "dur": dur}


def scan(c: Any, sym: str, mint: str, inv: float, gain: float, held_txt: str, max_pages: int) -> dict[str, Any]:
    # t_from=1 keeps a distinct checkpoint from the first run, whose pages sit in small files on a stalled disk.
    h = history(c, mint, t_from=1, token_accounts="none", max_pages=max_pages)
    trips = owner_trips(h.txs, mint)
    held = _held_seconds(held_txt)
    rows = []
    for owner, ts in trips.items():
        for t in ts:
            s = score(t, inv, gain, held)
            if s["n"] >= 2:
                rows.append({"wallet": owner, "score": s["n"], **s, "t_open": t["t_open"], "t_close": t["t_close"],
                             "first_sig": t["sigs"][0], "venues": sorted(t["venues"])})
    rows.sort(key=lambda r: -r["score"])
    return {"sym": sym, "mint": mint, "card": {"inv": inv, "gain": gain, "held": held_txt},
            "coverage": h.coverage(), "n_owners": len(trips), "candidates": rows[:12]}


TARGETS = {  # symbol -> mint, read from data/screens/TOKENS_CONSOLIDES.md, card figures from q1/captures_read.json
    "h2w6gm6jz": "FNqJtYs7rsP1H9GXWTtc5VnDoL2GhXEUKhYN46EEpump",
}


def main() -> int:
    credits = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    targets = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else TARGETS
    c = client(credits)
    cards = {x["sym"]: x for x in json.loads((STUDY / "q1/captures_read.json").read_text())["cards"]}
    results = []
    for sym, mint in targets.items():
        k = cards[sym]
        r = scan(c, sym, mint, k["inv_sol"], k["gain_sol"], k["held"], max_pages=250)
        results.append(r)
        print(sym, "owners", r["n_owners"], "txs", r["coverage"]["transactions_read"], r["coverage"]["walk_stop"],
              "candidates", [(x["wallet"][:6], x["score"], round(x["sol_out"], 3), round(x["realised"], 3), x["dur"])
                             for x in r["candidates"][:4]], "net", c.net_calls, flush=True)
        write_private("card_scan.json", json.dumps(results, indent=1, default=list))
    return 0


if __name__ == "__main__":
    sys.exit(main())
