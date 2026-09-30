#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
frpc.py -- a Helius JSON-RPC caller paced per key, for the long collections.

code/rpc_client.py rotates keys and cools a key for 6 s after any 429. On the
free tier that cooling, not the quota, became the bottleneck: measured on
2026-09-29, one key serves about 5 to 6 getTransaction per second before 429s,
and the 6 s pauses cut three keys to ~6 calls/s in total. Here each key has its
own pace, a little under that rate, and a 429 only delays that key by 1 s.

The error rule of rpc_client.py is kept unchanged: a call returns its result or
raises HeliusError (imported from rpc_client), never None, [] or {} for a
failure. The only None is a JSON-RPC error code the caller tolerates by name.
Keys come from $HELIUS_API_KEYS only.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "code"))
from rpc_client import HeliusError  # noqa: E402

URL = "https://mainnet.helius-rpc.com/?api-key="
KEY_RPS = float(os.environ.get("FRPC_KEY_RPS", "5.5"))   # measured ceiling ~6 per key
KEYS = [k.strip() for k in os.environ.get("HELIUS_API_KEYS", "").split(",") if k.strip()]
STATS: dict[str, int] = {"rpc": 0, "retry": 0, "r429": 0, "fail": 0}
_lock = threading.Lock()
_next = {k: 0.0 for k in KEYS}


def _take() -> str:
    """The key whose next free slot is earliest; reserve it and wait for it."""
    if not KEYS:
        raise HeliusError("HELIUS_API_KEYS is empty")
    with _lock:
        k = min(KEYS, key=lambda x: _next[x])
        now = time.time()
        t = max(now, _next[k])
        _next[k] = t + 1.0 / KEY_RPS
    if t > now:
        time.sleep(t - now)
    return k


def rpc(method: str, params: list[Any], tolerate: tuple[int, ...] = (), tries: int = 12,
        tries_429: int = 40) -> Any:
    """Other failures get `tries` attempts; 429s get `tries_429`, each followed by a
    wait that doubles (1, 2, 4 ... 30 s). On 2026-09-29 a 429 storm (the live
    detector saw it too) made single calls fail 12 times within about 4 s and cost
    342 windows; backing off yields the account's budget instead of burning it."""
    STATS["rpc"] += 1
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last: Optional[str] = None
    t = n429 = 0
    while t < tries and n429 < tries_429:
        k = _take()
        try:
            req = urllib.request.Request(URL + k, data=payload, headers={"Content-Type": "application/json",
                                                                          "User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = "HTTP %d" % e.code
            if e.code == 429:
                STATS["r429"] += 1
                n429 += 1
                wait = min(30.0, 2.0 ** (n429 - 1))
                with _lock:
                    _next[k] = max(_next[k], time.time() + 1.0)
                time.sleep(wait)
                continue
            if e.code in (500, 502, 503, 504):
                STATS["retry"] += 1
                t += 1
                time.sleep(min(6.0, 0.5 * t))
                continue
            raise HeliusError("%s: %s" % (method, last))
        except Exception as e:  # noqa: BLE001  (transport: URLError, timeout, decode)
            last = repr(e)[:120]
            STATS["retry"] += 1
            t += 1
            time.sleep(min(6.0, 0.5 * t))
            continue
        if isinstance(out, dict) and out.get("error") is not None:
            err = out["error"]
            code = err.get("code") if isinstance(err, dict) else None
            if code in tolerate:
                return None
            raise HeliusError("%s: %s" % (method, json.dumps(err)[:200]))
        return out.get("result") if isinstance(out, dict) else None
    STATS["fail"] += 1
    raise HeliusError("%s: gave up after %d failures and %d 429s: %s" % (method, t, n429, last))


def sigs(addr: str, limit: int = 1000, before: Optional[str] = None) -> list[Any]:
    p: dict[str, Any] = {"limit": limit}
    if before:
        p["before"] = before
    r = rpc("getSignaturesForAddress", [addr, p])
    if r is None:
        raise HeliusError("getSignaturesForAddress -> null")
    return r
