"""Copy the work area to the external volume. Adds only: nothing already there is overwritten or removed.

Transactions go row by row into the external database. Checkpoints, logs and intermediate results are copied when
absent or older. The copy is low priority work and can be stopped and run again at any time.
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
from pathlib import Path

from .. import storage


def main() -> int:
    cfg = storage.json.loads(storage.CONFIG.read_text())
    hot = Path(cfg["data_root"]).expanduser()
    cold = Path(cfg["cold_root"])
    if not (cold / storage.MARKER).is_file():
        print("external volume not mounted, nothing copied:", cold)
        return 1
    (cold / "rpc_raw").mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(hot / "rpc_raw" / "tx.sqlite", timeout=120)
    dst = sqlite3.connect(cold / "rpc_raw" / "tx.sqlite", timeout=300)
    dst.execute("PRAGMA journal_mode=WAL")
    dst.execute("CREATE TABLE IF NOT EXISTS tx(sig TEXT PRIMARY KEY, body BLOB NOT NULL) WITHOUT ROWID")
    n = 0
    cur = src.execute("SELECT sig, body FROM tx")
    while True:
        rows = cur.fetchmany(2000)
        if not rows:
            break
        dst.executemany("INSERT OR IGNORE INTO tx(sig, body) VALUES (?, ?)", rows)
        dst.commit()
        n += len(rows)
    copied = 0
    for name in ("checkpoints", "intermediate", "rpc_raw/provenance.jsonl"):
        p = hot / name
        for f in ([p] if p.is_file() else p.rglob("*") if p.exists() else []):
            if f.is_dir():
                continue
            t = cold / f.relative_to(hot)
            if not t.exists() or t.stat().st_mtime < f.stat().st_mtime:
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, t)
                copied += 1
    print({"transactions_offered": n, "files_copied": copied, "external_rows": dst.execute("SELECT count(*) FROM tx").fetchone()[0]})
    return 0


if __name__ == "__main__":
    sys.exit(main())
