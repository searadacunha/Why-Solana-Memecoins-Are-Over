"""One statement that keeps apart realised results, conversions, capital leaving, open positions and funds reaching the exchange. Private, no network.

python -m forensics_v2.investigations.posthoc.bilan_v3
"""

import csv
import gzip
import json
from collections import defaultdict
from typing import Any

from ..trades_2024 import FEB3, JAN1, OCT1, PRIVATE, ledger, write_private
from ..trades_ledger import ROWS
from ..trades_report import classify

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
TRADING = ("buy", "sell", "token_other", "failed", "tip")


def conversion(rows: list[dict[str, Any]], wallet: str) -> dict[str, Any]:
    """A SOL to USDC trip with USDC transferred away: the share that left is capital at the trip's own rate, not a trading loss."""
    usdc_in = usdc_sold = usdc_out = sol_spent = sol_back = 0
    for r in sorted((x for x in rows if x["w"] == wallet and USDC in x["tok"]), key=lambda x: x["slot"]):
        if r["native"] < 0 and r["tok"][USDC] > 0:
            usdc_in += r["tok"][USDC]
            sol_spent += -r["native"]
        elif r["native"] > 0 and r["tok"][USDC] < 0:
            usdc_sold += -r["tok"][USDC]
            sol_back += r["native"]
        else:
            usdc_out += -r["tok"][USDC]
    assert usdc_in == usdc_sold + usdc_out, (usdc_in, usdc_sold, usdc_out)  # no USDC left unexplained
    left = sol_spent * usdc_out / usdc_in
    return {
        "wallet": wallet,
        "sol_spent_lamports": sol_spent,
        "sol_back_lamports": sol_back,
        "usdc_in_raw": usdc_in,
        "usdc_sold_raw": usdc_sold,
        "usdc_transferred_away_raw": usdc_out,
        "capital_left_lamports": round(left),
        "conversion_cost_lamports": sol_spent - sol_back - round(left),
    }


def main() -> int:
    with open(PRIVATE / "WALLETS_V2.csv") as f:
        level = {r["wallet"]: r["level"] for r in csv.DictReader(f)}
    perimeter = set(ledger()["candidates"])  # as in the capital statement of trades_report
    flows: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    per_wallet: dict[str, int] = defaultdict(int)
    usdc_rows: list[dict[str, Any]] = []
    period = {"oct_dec": (OCT1, JAN1), "jan_feb2": (JAN1, FEB3)}
    with gzip.open(ROWS, "rt") as f:
        for line in f:
            r = json.loads(line)
            if USDC in r["tok"]:
                usdc_rows.append(r)
            k = classify(r, perimeter)
            for p, (a, b) in period.items():
                if a <= r["t"] < b:
                    flows[level.get(r["w"], "OUTSIDE") + ":" + p][k] += r["native"]
                    if k in TRADING:
                        per_wallet[r["w"]] += r["native"]
    trips: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with open(PRIVATE / "TRADES_V2.csv") as f:
        for t in csv.DictReader(f):
            p = "oct_dec" if t["t_open_utc"] < "2025-01-01" else "jan_feb2"
            key = t["level"] + ":" + p
            if t["closed"] == "True":
                trips[key]["realised_closed"] += int(t["realised_lamports"])
                trips[key]["closed_n"] += 1
            else:
                trips[key]["open_n"] += 1
                trips[key]["open_bought"] += int(t["sol_in_lamports_bought_with"])
                trips[key]["open_sold"] += int(t["sol_got_back_lamports"])
    conv = conversion(usdc_rows, next(w for w in level if w.startswith("63KN4NbK")))
    res = {
        "flows": {k: dict(v) for k, v in flows.items()},
        "trips": {k: dict(v) for k, v in trips.items()},
        "conversion": conv,
        "per_wallet_trading": dict(per_wallet),
    }
    write_private("derived/bilan_v3.json", json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
