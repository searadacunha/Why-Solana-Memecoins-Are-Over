#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hlib.py -- adapter kept for the scripts that import it (v1_probe_addresses.py,
v2_dispatcher_burst.py). The client itself now lives in rpc_client.py; this
module only re-exports it under the historical names and keeps the base58
pubkey check.

It used to be a second, weaker client that returned [] / None on failure, so a
quota-truncated page looked like an empty one. Every call now raises
HeliusError (see rpc_client.py).
"""
from __future__ import annotations

from typing import Any

import settings
from rpc_client import (  # noqa: F401  (re-exported for importers)
    HeliusError,
    account_info,
    cached as _cached,
    enhanced,
    rpc,
    sigs,
)

CACHE = settings.CACHE


def cached(name: str, fn: Any) -> Any:
    """Disk cache under data/cache/ (atomic write; see rpc_client.cached)."""
    return _cached(name, fn, settings.CACHE)


B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def is_b58_pubkey(s: str) -> bool:
    """True for a base58 string that decodes to a 32-byte Solana pubkey.

    The length window rejects the obvious non-keys; the final bound is the real
    test, since 32 bytes is exactly the integers below 2**256.
    """
    if not (32 <= len(s) <= 44):
        return False
    n = 0
    for c in s:
        if c not in B58:
            return False
        n = n * 58 + B58.index(c)
    return n < 2 ** 256
