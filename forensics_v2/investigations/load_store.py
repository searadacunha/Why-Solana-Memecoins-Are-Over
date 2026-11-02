"""Load the decoded 2024 perimeter into DuckDB, check the books, export Parquet.

The database names the author's wallets, so it stays on the data volume and the Parquet of his trades in private_trades/.
Needs duckdb: run with the venv in <data root>/tooling or any Python that has it.
"""
from __future__ import annotations

import json
import sys

from .. import storage
from .. import store as ST
from .trades_2024 import PRIVATE, load_all


def main() -> int:
    root = storage.data_root()
    (root / "duckdb").mkdir(parents=True, exist_ok=True)
    con = ST.connect(root / "duckdb" / "forensics.duckdb")
    all_txs = load_all()
    seen = set()
    batch = []
    for txs in all_txs.values():
        for d in txs:
            if d.signature not in seen:
                seen.add(d.signature)
                batch.append(d)
    con.execute("BEGIN")
    new = ST.ingest(con, batch)
    con.execute("COMMIT")
    again = ST.ingest(con, batch[:200])
    books = ST.reconcile(con)
    counts = ST.counts(con)
    ST.export_parquet(con, root / "parquet", ("transactions", "instructions", "balance_movements", "token_movements",
                                              "funding_edges", "swap_events", "unresolved_sol"))
    csv_path = PRIVATE / "TRADES_2024_2025.csv"
    pq = PRIVATE / "TRADES_2024_2025.parquet"
    con.execute("COPY (SELECT * FROM read_csv_auto('%s', sample_size=-1)) TO '%s' (FORMAT parquet)" % (csv_path, pq))
    pq.chmod(0o600)
    check = con.execute("SELECT count(*), sum(realised_lamports) FILTER (WHERE closed AND t_open_utc < '2025-01-01') "
                        "FROM read_parquet('%s')" % pq).fetchone()
    print(json.dumps({"new": new, "replayed_again_new": again, "books": books, "counts": {k: v for k, v in counts.items() if v},
                      "parquet_rows": check[0], "parquet_realised_q4_lamports": int(check[1])}, indent=0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
