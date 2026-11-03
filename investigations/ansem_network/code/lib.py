"""Shared setup: the forensics_v2 client with this investigation's own root, ceiling and output folders."""
from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import resource
import shutil
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent.parent
sys.path.insert(0, str(REPO))

from forensics_v2.keys import KeyPool  # noqa: E402
from forensics_v2.rpc import Budget, RpcClient  # noqa: E402

MINT = "9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump"
CREATION_SLOT = 426930467
CREATOR = "yHCxHBEaJW5tbndqC8JciSThr7U1cqLpdcsvHcx6PRe"
SECOND_BUYER = "9ryBR3SnxgGPhWsKvsfxuNHUCTt6tSpLe8wrKCShXLaq"

DATA = Path(os.environ.get("ANSEM_DATA_ROOT", str(Path.home() / ".local/state/ansem_network")))
COLD = Path("/Volumes/PHI-Data/ansem_network")  # APFS image: SQLite needs locks, the bare USB volume is FAT32
OUT = ROOT / "evidence"
CEILING = 150_000
QUOTA_BYTES = 1_500_000_000
MIN_FREE = 13_500_000_000
MAX_RSS = 1_500_000_000


def client(run_limit: int | None = None) -> RpcClient:
    pool = KeyPool.from_config(rps_per_key=8.0, rps_total=10.0)
    budget = Budget(DATA / "checkpoints" / "credits", CEILING, run_limit)
    return RpcClient(pool, DATA, budget, legacy_root=COLD if COLD.is_dir() else DATA, max_db_bytes=QUOTA_BYTES)


def guard() -> None:
    """Stop before memory turns into swap on the disk PolySentinel also needs."""
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS
    if rss > MAX_RSS:
        raise SystemExit("memory guard: RSS %.2f GB" % (rss / 1e9))
    if shutil.disk_usage(DATA).free < MIN_FREE:
        raise SystemExit("disk guard: under the 13.5 GB floor")


def utc(ts: int | None) -> str | None:
    return None if ts is None else dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def sol(lamports: int) -> float:
    return round(lamports / 1e9, 9)


def save_json(name: str, obj: Any) -> Path:
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, sort_keys=False, ensure_ascii=False) + "\n")
    return p


def save_gz(name: str, obj: Any) -> Path:
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 so a re-run writes the same bytes
    with open(p, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        gz.write(json.dumps(obj, sort_keys=True).encode())
    return p
