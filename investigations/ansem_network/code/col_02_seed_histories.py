"""Full histories of named wallets. Usage: col_02_seed_histories.py <max_pages> <run_credit_limit> <address>..."""
from __future__ import annotations

import json
import sys

from flows import collect
from lib import DATA, client, utc


def main() -> None:
    pages, limit, addrs = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3:]
    c = client(run_limit=limit)
    log = DATA / "coverage.jsonl"
    for a in addrs:
        cov = collect(c, a, max_pages=pages)
        with open(log, "a") as f:
            f.write(json.dumps(cov) + "\n")
        print(a[:10], "txs", cov["transactions_read"], "pages", cov["pages"], "stop", cov["walk_stop"], "first",
              utc(cov["first_observable_ts"]), "credits run", c.budget.run_spent, flush=True)
    print("keys", [k["exhausted"] for k in c.pool.status()], "total credits", c.budget.used())


if __name__ == "__main__":
    main()
