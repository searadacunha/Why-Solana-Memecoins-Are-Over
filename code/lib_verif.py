#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lib_verif.py -- the common base of the on-chain verification scripts (v0*).

Read-only on its sources, and it writes nowhere outside data/.

The network client is rpc_client.py now, the repository's single client, which
RAISES on failure instead of returning an empty value. What is left here is the
local cache under data/cache/, the loaders for the local sources, and the few
helpers only the v0* scripts need.

Inputs:
  - capture corpus  : data/floor_capture_public.jsonl.gz (published), or
                      $PUMP_PRIVATE_ROOT/state/floor_capture/ when mounted.
  - feature socle   : data/dataset_socle.json (published).
  - creation-window geometry: a cache derived from Helius, not published
                      (5.5 MB, 913 files), and it needs $PUMP_PRIVATE_ROOT.
                      What derives from it IS published, under data/.
  - Helius          : keys read from the environment (see settings.py). No key
                      is ever written to data/ or into any output.
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import statistics as st
from typing import Any, Optional

import rpc_client
import settings

OUT = settings.ROOT
DATA = settings.DATA
CACHE = settings.CACHE
os.makedirs(CACHE, exist_ok=True)

SOCLE = settings.data("dataset_socle.json")


def _snipe_cache_dir() -> str:
    priv = settings.private_root(required=True)
    return os.path.join(priv, "analysis_forensic", "ident_age_stack", "cache")


# ---------------------------------------------------------------- Helius
def rpc(method: str, params: list[Any]) -> Any:
    """Helius JSON-RPC through the single client. It tolerates -32601 and
    -32602, a missing method and invalid parameters, by returning None as it
    always did. Every other failure raises HeliusError rather than disguising
    itself as an empty result.
    """
    return rpc_client.rpc(method, params, tolerate_codes=(-32601, -32602))


def cached(name: str, fn: Any) -> Any:
    """cache disque : data/cache/<name>.json (ecriture atomique)."""
    return rpc_client.cached(name, fn, CACHE)


def get_tx(sig: str) -> Any:
    return cached("tx_" + sig[:24], lambda: rpc(
        "getTransaction", [sig, {"encoding": "jsonParsed",
                                 "maxSupportedTransactionVersion": 0}]))


def get_sigs(addr: str, limit: int = 1000, before: Optional[str] = None) -> Any:
    p: dict[str, Any] = {"limit": limit}
    if before:
        p["before"] = before
    return rpc("getSignaturesForAddress", [addr, p])


def first_signature(addr: str) -> tuple[Optional[str], Optional[int], int, bool]:
    """Walk back to an address's oldest signature, paginating backwards.

    Returns (sig, blockTime, n_pages, censored). censored is True when the walk
    hit the page cap, so the signature returned is a lower bound on the
    address's age rather than its first.
    """
    CAP = 40           # 40 * 1000 = 40 000 signatures max
    before, last, n = None, None, 0
    while n < CAP:
        r = get_sigs(addr, 1000, before)
        n += 1
        if not r:
            break
        last = r[-1]
        if len(r) < 1000:
            return last["signature"], last.get("blockTime"), n, False
        before = last["signature"]
    return (last or {}).get("signature"), (last or {}).get("blockTime"), n, True


# ---------------------------------------------------------------- sources locales
def load_floor() -> dict[str, Any]:
    """Every non-empty capture, indexed by mint. Read-only.

    The published source by default, the raw corpus when $PUMP_PRIVATE_ROOT is
    mounted.
    """
    priv = settings.private_root()
    out: dict[str, Any] = {}
    if priv:
        for f in sorted(glob.glob(os.path.join(priv, "state", "floor_capture", "*.json"))):
            d = json.load(open(f))
            if d.get("swaps"):
                out[d["mint"]] = d
        return out
    with gzip.open(settings.PUBLIC_CORPUS, "rt") as fh:
        for line in fh:
            line = line.strip()
            if line:
                d = json.loads(line)
                out[d["mint"]] = d
    return out


def load_snipe() -> dict[str, Any]:
    """The snipe_*.json cache: the geometry of the creation window, up to +12 s.

    This is the one input of the dossier that is not published: 913 files
    derived from Helius, kept as they came so the API is not queried again on
    every run. What derives from them, data/v0*.json, IS published, so v03
    through v08 stay checkable without it.
    """
    d0 = _snipe_cache_dir()
    out: dict[str, Any] = {}
    for f in sorted(glob.glob(os.path.join(d0, "snipe_*.json"))):
        d = json.load(open(f))
        out[d["mint"]] = d
    if not out:
        raise SystemExit("cache snipe_*.json introuvable dans %s" % d0)
    return out


def load_socle() -> Any:
    return json.load(open(SOCLE))


def cv(x: list[Any]) -> float:
    if len(x) < 2:
        return 0.0
    m = st.mean(x)
    return (st.pstdev(x) / m) if m else 0.0


def save(name: str, obj: Any) -> None:
    """The single write point for the v0* outputs. Pseudonymisation happens
    HERE, so a re-run from the raw network cache, which still holds the
    original identifiers, cannot undo it.
    """
    import redact
    p = f"{DATA}/{name}"
    json.dump(redact.scrub(obj), open(p, "w"), indent=1, default=str)
    print(f"  -> {os.path.relpath(p, settings.ROOT)}")
