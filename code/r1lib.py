#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r1lib.py -- the adapter for verifying "regime 1": fleets of fresh wallets
funded through dispatchers, before June 2026.

The robust client this module used to carry became rpc_client.py, the single
client of the repository: same key rotation, same 429 cooldown, same rule that
a failure RAISES and never returns a silently empty page. What is left here:
  - its own cache, data/cache_r1/, kept apart from data/cache/;
  - the atomic, pseudonymised write of the outputs (save);
  - the pump.fun constants the r1_* scripts use.

Keys are read from the environment, $HELIUS_API_KEYS or the uncommitted .env at
the repository root; see settings.py. Read-only.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

import rpc_client
import settings
from rpc_client import (  # noqa: F401  (re-exported for r1_* importers)
    HeliusError,
    STATS,
    block,
    enhanced,
    rpc,
    tx,
    walk_sigs,
)

DATA = settings.DATA
CACHE = settings.CACHE_R1
os.makedirs(CACHE, exist_ok=True)


def sig_page(addr: str, limit: int = 1000, before: Optional[str] = None) -> list[Any]:
    """One page of signatures. Raises if the call returns null (rpc_client.sigs)."""
    return rpc_client.sigs(addr, limit, before)


def cached(name: str, fn: Any) -> Any:
    """cache disque : data/cache_r1/<name>.json (ecriture atomique)."""
    return rpc_client.cached(name, fn, CACHE)


def save(name: str, obj: Any) -> str:
    """Atomic write, pseudonymised at write time (see redact.py)."""
    import redact
    p = os.path.join(DATA, name)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(redact.scrub(obj), f, indent=1)
    os.replace(tmp, p)
    sys.stderr.write("ecrit %s\n" % os.path.relpath(p, settings.ROOT))
    return p


# ---------------------------------------------------------------- pump.fun
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMP_AMM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
SYS_PROGRAM = "11111111111111111111111111111111"
LAMPORT = 1e-9
# Rent minimum of an empty system account, 0.00089088 SOL. Below it a wallet
# cannot even persist, let alone sign a buy.
RENT_MIN_SOL = 0.00089088
# Base fee of a Solana transaction: 5000 lamports.
TX_FEE_SOL = 0.000005
