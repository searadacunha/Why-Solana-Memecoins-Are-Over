"""Where could the last PnL card's trade be? Reads named wallets in a window and lists trips close to the card, whatever the token. Output is private.

The card's two dollar figures give the SOL price at the time, and that price is seen again after the ledger's last deposit. So a wallet that
first paid the deposit address later is missing from the perimeter.

    python -m forensics_v2.investigations.posthoc.bwick_search <credits> <t_from> <t_to> <wallet> [...]
"""

import json
import sys

from ...__main__ import client
from ...trace import history, sol_flows, trips
from ..trades_2024 import DEPOSIT, HOT, PRIVATE, write_private

INV, GOT, HELD = 0.254, 0.994, 821  # the card: invested, current gain, 13 m 41 s
OUT = "bwick_search.json"


def state() -> dict:
    p = PRIVATE / OUT
    return json.loads(p.read_text()) if p.exists() else {}


def wallets(credits: int, t_from: int, t_to: int, addrs: list[str]) -> int:
    """History of named wallets in a window, and every trip close to the card's figures, whatever its token."""
    c = client(credits)
    s = state()
    out = s.setdefault("wallets", {})
    for w in addrs:
        h = history(c, w, t_from, t_to, max_pages=max(1, credits // 10), token_accounts="balanceChanged")
        ts = trips(h.txs, w)
        close = [
            {
                "mint": t.mint,
                "invested": t.sol_out / 1e9,
                "gain": t.realised / 1e9,
                "held_s": (t.t_close or t.t_open) - t.t_open,
                "open": t.t_open,
                "closed": t.closed,
                "sigs": t.sigs,
            }
            for t in ts
            if abs(t.sol_out / 1e9 - INV) <= INV * 0.1 and abs(t.realised / 1e9 - GOT) <= GOT * 0.1
        ]
        fl = sol_flows(h)[0]
        out[w] = {
            "window": [t_from, t_to],
            "coverage": h.coverage(),
            "trips": len(ts),
            "close_to_card": close,
            "to_deposit_lamports": sum(f.lamports for f in fl if f.dst == DEPOSIT),
            "from_hot_lamports": sum(f.lamports for f in fl if f.src == HOT and f.dst == w),
            "funders": sorted({f.src for f in fl if f.dst == w and f.lamports >= 10_000_000}),
        }
        print(
            w[:8],
            h.coverage()["transactions_read"],
            h.walk.stop,
            "trips",
            len(ts),
            "close",
            close,
            "net",
            c.net_calls,
            flush=True,
        )
        write_private(OUT, json.dumps(s, indent=1))
    return 0


if __name__ == "__main__":
    a = sys.argv
    raise SystemExit(wallets(int(a[1]), int(a[2]), int(a[3]), a[4:]))
