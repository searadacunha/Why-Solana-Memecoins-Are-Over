"""
hlib.py — minimal Helius client used by every verification script of this dossier.

Read-only. No key is ever written to disk by these scripts: keys come from the
environment ($HELIUS_API_KEYS, or an untracked .env at the repo root -- see
settings.py) and are rotated round-robin on 429/5xx.

Two endpoints only:
  - JSON-RPC   https://mainnet.helius-rpc.com/?api-key=  (getSignaturesForAddress,
               getAccountInfo, getTransaction)
  - Enhanced   https://api.helius.xyz/v0/addresses/{a}/transactions (parsed
               nativeTransfers, 100/page)

Everything the dossier claims about upstream infrastructure is recomputable with
these two calls plus the local read-only files of pump_bundle_detector/.
"""
import json
import os
import time
import urllib.error
import urllib.request

import settings

CACHE = settings.CACHE
os.makedirs(CACHE, exist_ok=True)

KEYS = settings.helius_keys()
_i = [0]


def _next_key():
    global KEYS
    if not KEYS:
        KEYS = settings.require_helius()   # explicit message, no traceback
    k = KEYS[_i[0] % len(KEYS)]
    _i[0] += 1
    return k


def _get(url, payload=None, tries=6):
    last = None
    for t in range(tries):
        try:
            if payload is None:
                req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            else:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json", "User-Agent": "curl/8"},
                )
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = "HTTP %s" % e.code
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(1.2 * (t + 1))
                continue
            return {"_error": last}
        except Exception as e:  # noqa
            last = str(e)
            time.sleep(1.0 * (t + 1))
    return {"_error": last}


def rpc(method, params):
    url = "https://mainnet.helius-rpc.com/?api-key=" + _next_key()
    r = _get(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    return r.get("result") if isinstance(r, dict) else None


def sigs(addr, limit=1000, before=None):
    p = {"limit": limit}
    if before:
        p["before"] = before
    r = rpc("getSignaturesForAddress", [addr, p])
    return r or []


def account_info(addr):
    return rpc("getAccountInfo", [addr, {"encoding": "base64"}])


def enhanced(addr, limit=100, before=None, ttype=None):
    """Parsed transactions. before = signature."""
    url = "https://api.helius.xyz/v0/addresses/%s/transactions?api-key=%s&limit=%d" % (
        addr,
        _next_key(),
        limit,
    )
    if before:
        url += "&before=" + before
    if ttype:
        url += "&type=" + ttype
    r = _get(url)
    return r if isinstance(r, list) else []


def cached(name, fn):
    p = os.path.join(CACHE, name + ".json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    v = fn()
    with open(p, "w") as f:
        json.dump(v, f)
    return v


B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def is_b58_pubkey(s):
    if not (32 <= len(s) <= 44):
        return False
    n = 0
    for c in s:
        if c not in B58:
            return False
        n = n * 58 + B58.index(c)
    return len(n.to_bytes(32, "big")) == 32 if n < 2 ** 256 else False
