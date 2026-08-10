#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rpc_client.py -- the single Helius client for this dossier.

Read-only. Stdlib only (urllib). Keys come from the environment
($HELIUS_API_KEYS, or an untracked .env at the repo root -- see settings.py)
and are rotated round-robin, with a per-key cooldown after a 429 so that
retrying a key that just reported its quota does not simply confirm it again.

    ONE error rule, applied everywhere:
        a call either returns its result or raises HeliusError.
        It NEVER returns None, [] or {} to mean "the call failed" -- a network
        outage or a quota hit must interrupt the measurement, not silently
        truncate it into a clean-looking zero (see docs/PITFALLS.md).

Before this module the repository carried a dozen ad-hoc clients with three
different error conventions: some raised, some returned an {"_error": ...}
dict, and hlib.py returned an empty list on failure -- indistinguishable from
a genuinely empty page, the exact trap that once produced a false "0 of 14".
hlib.py / lib_verif.py / r1lib.py are now thin adapters over this module and
keep only their own cache location and their non-network helpers.

Two endpoints:
  JSON-RPC   https://mainnet.helius-rpc.com/?api-key=  (getSignaturesForAddress,
             getTransaction, getBlock, getAccountInfo, ...)
  Enhanced   https://api.helius.xyz/v0/addresses/{a}/transactions  (parsed
             nativeTransfers, 100/page)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

import settings

RPC_URL = "https://mainnet.helius-rpc.com/?api-key="
ENHANCED_URL = "https://api.helius.xyz/v0/addresses/%s/transactions?api-key=%s&limit=%d"

# Live counters, useful when a deep walk is running and you want to know whether
# it is making progress or just retrying. Read-only for callers.
STATS: dict[str, int] = {"rpc": 0, "enh": 0, "retry": 0, "fail": 0}

_KEYS: list[str] = settings.helius_keys()
_i = [0]
_COOLDOWN: dict[str, float] = {}   # key -> earliest time it may be reused


class HeliusError(RuntimeError):
    """A network or RPC-level failure. Raised, never returned: a caller that
    does not catch it stops, which is the point."""


def _next_key() -> str:
    global _KEYS
    if not _KEYS:
        _KEYS = settings.require_helius()   # explicit message, no traceback
    k = _KEYS[_i[0] % len(_KEYS)]
    _i[0] += 1
    return k


def _available_key() -> str:
    """A key not currently in 429 cooldown. Retrying a key that just returned
    429 only confirms its quota, so a cooled key is skipped until it is due;
    if all keys are cooling, wait out the soonest (bounded)."""
    if not _KEYS:
        return _next_key()
    now = time.time()
    for _ in range(len(_KEYS) * 3):
        k = _next_key()
        if _COOLDOWN.get(k, 0.0) <= now:
            return k
    k = min(_KEYS, key=lambda x: _COOLDOWN.get(x, 0.0))
    wait = max(0.0, _COOLDOWN.get(k, 0.0) - now)
    if wait:
        time.sleep(min(wait, 20.0))
    return k


def _http(url: str, payload: Optional[dict[str, Any]] = None, tries: int = 8) -> Any:
    """Decoded JSON, or raise HeliusError. Retries 429/5xx and transport
    errors with a bounded backoff; a non-retryable HTTP status raises at once."""
    last: Optional[str] = None
    for t in range(tries):
        try:
            if payload is None:
                req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            else:
                req = urllib.request.Request(
                    url, data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json",
                             "User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = "HTTP %d" % e.code
            if e.code in (429, 500, 502, 503, 504):
                STATS["retry"] += 1
                time.sleep(min(8.0, 0.8 * (t + 1) ** 1.6))
                continue
            raise HeliusError(last)
        except Exception as e:  # noqa: BLE001  (transport: URLError, timeout, decode)
            last = repr(e)
            STATS["retry"] += 1
            time.sleep(min(8.0, 0.8 * (t + 1)))
    STATS["fail"] += 1
    raise HeliusError("gave up after %d tries: %s" % (tries, last))


def _http_rotating(build_url: Callable[[str], str],
                   payload: Optional[dict[str, Any]] = None, tries: int = 10) -> Any:
    """Like _http but tries a different key on each attempt, cooling a key that
    returns 429 so the rotation actually moves off it."""
    last: Optional[str] = None
    for t in range(tries):
        key = _available_key()
        try:
            return _http(build_url(key), payload, tries=1)
        except HeliusError as e:
            last = str(e)
            if "429" in last:
                _COOLDOWN[key] = time.time() + 6.0
                STATS["retry"] += 1
                time.sleep(0.25)
                continue
            if any(c in last for c in ("500", "502", "503", "504",
                                       "timed out", "URLError")):
                STATS["retry"] += 1
                time.sleep(min(6.0, 0.6 * (t + 1)))
                continue
            raise
    STATS["fail"] += 1
    raise HeliusError("gave up after %d tries (key rotation): %s" % (tries, last))


# --------------------------------------------------------------- JSON-RPC ----
def rpc(method: str, params: list[Any], tolerate_codes: tuple[int, ...] = ()) -> Any:
    """A JSON-RPC call. Returns result, or raises HeliusError on transport
    failure or a JSON-RPC `error` object.

    tolerate_codes lists JSON-RPC error codes that are a legitimate answer
    rather than a failure -- e.g. -32009 "slot skipped" for getBlock, or
    -32601/-32602 "method not found / invalid params" -- for which the call
    returns None instead of raising. This is the ONLY way None ever comes back
    from a failed-looking call, and the caller asked for it by name."""
    STATS["rpc"] += 1
    r = _http_rotating(lambda k: RPC_URL + k,
                       {"jsonrpc": "2.0", "id": 1, "method": method,
                        "params": params})
    if isinstance(r, dict) and r.get("error") is not None:
        err = r["error"]
        code = err.get("code") if isinstance(err, dict) else None
        if code in tolerate_codes:
            return None
        raise HeliusError("%s: %s" % (method, json.dumps(err)[:200]))
    return r.get("result") if isinstance(r, dict) else None


def sigs(addr: str, limit: int = 1000, before: Optional[str] = None) -> list[Any]:
    """One page of getSignaturesForAddress, oldest-last. Raises if the RPC
    returns null (a null is a failure here, not an empty page)."""
    p: dict[str, Any] = {"limit": limit}
    if before:
        p["before"] = before
    r: list[Any] = rpc("getSignaturesForAddress", [addr, p])
    if r is None:
        raise HeliusError("getSignaturesForAddress -> null")
    return r


def walk_sigs(addr: str, until_ts: Optional[int] = None, max_pages: int = 400,
              verbose: bool = False) -> tuple[list[Any], int]:
    """Full backward history (or down to until_ts, exclusive), newest to
    oldest. Raises if max_pages runs out before genesis or until_ts is
    reached -- no silent truncation."""
    out: list[Any] = []
    before: Optional[str] = None
    pages = 0
    while True:
        if pages >= max_pages:
            raise HeliusError(
                "walk_sigs %s: %d pages exhausted before genesis%s -- partial "
                "history refused" % (addr[:8], max_pages,
                                     "" if until_ts is None else " or until_ts"))
        page = sigs(addr, 1000, before)
        pages += 1
        if not page:
            break
        out += page
        before = page[-1]["signature"]
        oldest = page[-1].get("blockTime")
        if verbose and pages % 10 == 0:
            sys.stderr.write("  ..%s page %d n=%d oldest=%s\n"
                             % (addr[:6], pages, len(out), oldest))
        if len(page) < 1000:
            break
        if until_ts and oldest and oldest < until_ts:
            break
    return out, pages


def tx(sig: str) -> Any:
    return rpc("getTransaction", [sig, {"maxSupportedTransactionVersion": 0,
                                        "encoding": "jsonParsed"}])


def block(slot: int, sigs_only: bool = False) -> Any:
    cfg = {"maxSupportedTransactionVersion": 0, "rewards": False,
           "transactionDetails": "signatures" if sigs_only else "full",
           "encoding": "jsonParsed"}
    return rpc("getBlock", [slot, cfg])


def account_info(addr: str, encoding: str = "base64") -> Any:
    return rpc("getAccountInfo", [addr, {"encoding": encoding}])


# --------------------------------------------------------------- Enhanced ----
def enhanced(addr: str, limit: int = 100, before: Optional[str] = None,
             ttype: Optional[str] = None) -> list[Any]:
    """Parsed transactions for an address. `before` is a signature. Raises if
    the response is not a list (an error object is a failure, not zero txs)."""
    STATS["enh"] += 1
    suffix = ""
    if before:
        suffix += "&before=" + before
    if ttype:
        suffix += "&type=" + ttype
    r = _http_rotating(lambda k: (ENHANCED_URL % (addr, k, limit)) + suffix)
    if not isinstance(r, list):
        raise HeliusError("enhanced(%s) -> %s" % (addr[:6], str(r)[:200]))
    return r


# ------------------------------------------------------------------ cache ----
def cached(name: str, fn: Callable[[], Any],
           cache_dir: Optional[str] = None) -> Any:
    """Disk memoisation: cache_dir/<name>.json. The write is ATOMIC (a temp
    file renamed into place), so a crash mid-write cannot leave a truncated
    JSON that poisons the next run."""
    d = cache_dir or settings.CACHE
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name + ".json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    v = fn()
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(v, f)
    os.replace(tmp, p)
    return v
