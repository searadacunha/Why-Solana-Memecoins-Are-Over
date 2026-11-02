"""Where heavy data goes. Refuses to write if the external volume is not there.

The root comes from $FORENSICS_DATA_ROOT or ~/.config/forensics_v2/config.json, never a volume name
in the code. A root is valid only if it holds the marker file and sits on another device than the
home directory, so an unmounted disk cannot silently turn into writes on the internal disk.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

MARKER = ".forensics_v2_volume"
CONFIG = Path.home() / ".config" / "forensics_v2" / "config.json"
MIN_FREE_BYTES = 20 * 10**9
INTERNAL_MIN_FREE_BYTES = 13_500_000_000  # the floor of the machine's disk guard: never written past


class StorageError(RuntimeError):
    pass


def internal_quota() -> int:
    """Bytes the cache may use on the internal disk. 0 unless a quota is written in the config."""
    return json.loads(CONFIG.read_text()).get("internal_quota_bytes", 0) if CONFIG.exists() else 0


def data_root(allow_internal: bool = False) -> Path:
    raw = os.environ.get("FORENSICS_DATA_ROOT")
    if not raw and CONFIG.exists():
        raw = json.loads(CONFIG.read_text()).get("data_root")
    if not raw:
        raise StorageError("no data root: set FORENSICS_DATA_ROOT or data_root in %s" % CONFIG)
    root = Path(raw).expanduser()
    allow_internal = allow_internal or internal_quota() > 0
    if not (root / MARKER).is_file():
        raise StorageError("%s has no %s: volume disconnected or wrong path" % (root, MARKER))
    if not allow_internal and os.stat(root).st_dev == os.stat(Path.home()).st_dev:
        raise StorageError("%s is on the same device as the home directory" % root)
    on_internal = os.stat(root).st_dev == os.stat(Path.home()).st_dev
    free = shutil.disk_usage(root).free
    if free < (INTERNAL_MIN_FREE_BYTES if on_internal else MIN_FREE_BYTES):
        raise StorageError("%s has only %.1f GB free" % (root, free / 1e9))
    return root


def sub(name: str, allow_internal: bool = False) -> Path:
    p = data_root(allow_internal) / name
    p.mkdir(parents=True, exist_ok=True)
    return p
