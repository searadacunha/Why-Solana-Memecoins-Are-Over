"""Walk wallets in a stream. Usage: col_03_stream.py <pages_per_wallet> <run_credit_limit> <address>..."""
from __future__ import annotations

import json
import sys

from flows import stream
from lib import DATA, client, utc


def main() -> None:
    pages, limit, addrs = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3:]
    c = client(run_limit=limit)
    for a in addrs:
        token, done = None, 0
        old = DATA / "checkpoints" / "gtfa" / (a + "_start_end_balanceChanged.jsonl")
        if old.exists():  # continue where the first, in-memory walk stopped; its rows are already written
            with open(old) as f:
                for line in f:
                    token = json.loads(line)["next"]
                    done += 1
        r = stream(c, a, pages, start_token=token, pages_done=done)
        print(a[:10], "pages", r["pages"], "txs_this_walk", r["txs"], "done", r["done"], "until", utc(r["last_ts"]),
              "run credits", c.budget.run_spent, "total", c.budget.used(), flush=True)
    print("keys", [k["exhausted"] for k in c.pool.status()])


if __name__ == "__main__":
    main()
