"""Helius keys: where they come from, without ever holding a copy or printing one.

~/.config/forensics_v2/helius_sources.json lists source files and the fingerprints allowed for this
work (sha256 prefix, not reversible). Values are read from those files at run time only, so there is
no new copy of any secret. Keys used by live services are simply not on the allow list.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Optional

SOURCES = Path.home() / ".config" / "forensics_v2" / "helius_sources.json"
_UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def fingerprint(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:8]


def redact(text: str) -> str:
    """Remove anything shaped like a key from a string on its way to a log or an exception."""
    return _UUID.sub("<key>", text)


def keys_in_file(path: str, bare: bool) -> list[str]:
    """Helius lines only, so that other credentials in the same file are never touched."""
    out: list[str] = []
    with open(os.path.expanduser(path), errors="ignore") as f:
        for line in f:
            s = line.strip()
            if s.startswith("#") or not (bare or "helius" in s.lower()):
                continue
            out.extend(_UUID.findall(s))
    return out


class _Key:
    __slots__ = ("value", "fp", "next_at", "cooldown_until", "exhausted")

    def __init__(self, value: str):
        self.value = value
        self.fp = fingerprint(value)
        self.next_at = 0.0
        self.cooldown_until = 0.0
        self.exhausted = False

    def __repr__(self) -> str:
        return "<key %s>" % self.fp


class KeyPool:
    """Hands out one key per request at no more than `rps_per_key`, and `rps_total` overall.

    Defaults stay below the free plan's documented 10 requests per second. A 429 cools that key;
    "max usage reached" retires it for the run rather than hammering a spent quota.
    """

    def __init__(self, keys: list[str], rps_per_key: float = 8.0, rps_total: float = 10.0):
        if not keys:
            raise ValueError("no Helius key available")
        self._keys = [_Key(k) for k in dict.fromkeys(keys)]
        self._gap = 1.0 / rps_per_key
        self._total_gap = 1.0 / rps_total
        self._total_next = 0.0
        self._lock = threading.Lock()
        self._i = 0

    def __repr__(self) -> str:
        return "KeyPool(%d keys)" % len(self._keys)

    @classmethod
    def from_config(cls, path: Optional[Path] = None, **kw: float) -> "KeyPool":
        cfg = json.loads((path or SOURCES).read_text())
        allowed = set(cfg["pool_fingerprints"])
        found: list[str] = []
        for src in cfg["sources"]:
            found += [k for k in keys_in_file(src["path"], src.get("bare", False)) if fingerprint(k) in allowed]
        return cls(found, **kw)

    def acquire(self) -> _Key:
        """Block until a key may be used, or raise if every key is spent."""
        while True:
            with self._lock:
                live = [k for k in self._keys if not k.exhausted]
                if not live:
                    raise RuntimeError("every Helius key in the pool reports max usage")
                now = time.monotonic()
                for _ in range(len(self._keys)):
                    k = self._keys[self._i % len(self._keys)]
                    self._i += 1
                    if not k.exhausted and k.cooldown_until <= now and k.next_at <= now and self._total_next <= now:
                        k.next_at = now + self._gap
                        self._total_next = now + self._total_gap
                        return k
                wake = min(max(k.next_at, k.cooldown_until, self._total_next) for k in live) - now
            time.sleep(min(max(wake, 0.005), 2.0))

    def cool(self, key: _Key, seconds: float) -> None:
        with self._lock:
            key.cooldown_until = max(key.cooldown_until, time.monotonic() + seconds)

    def retire(self, key: _Key) -> None:
        with self._lock:
            key.exhausted = True

    def status(self) -> list[dict[str, object]]:
        return [{"fp": k.fp, "exhausted": k.exhausted} for k in self._keys]
