#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r1lib.py — client Helius ROBUSTE pour la verification du "regime 1"
(financement de flottes de wallets vierges via dispatchers, avant juin 2026).

Difference avec hlib.py : hlib renvoie une liste vide aussi bien quand la page
est genuinement vide que quand l'appel a echoue (429 / 5xx). Une pagination
qui s'arrete sur une page vide y est donc indistinguable d'une pagination
tronquee par le quota. Toutes les mesures d'historique profond de ce dossier
passent par ici : `page()` distingue explicitement OK / VIDE / ERREUR et la
pagination ne s'arrete JAMAIS sur une erreur silencieuse (elle leve).

Cles : lues dans l'environnement ($HELIUS_API_KEYS, ou .env non versionne a la
racine du depot -- voir settings.py), rotation round-robin.
Aucune cle n'est ecrite dans data/ ni dans les sorties.

Lecture seule. Deux endpoints :
  RPC      getSignaturesForAddress / getTransaction / getBlock / getAccountInfo
  Enhanced /v0/addresses/{a}/transactions  (transferts natifs deja parses)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

import settings

HERE = settings.CODE
DATA = settings.DATA
CACHE = settings.CACHE_R1
os.makedirs(CACHE, exist_ok=True)

KEYS = settings.helius_keys()
_i = [0]
STATS = {"rpc": 0, "enh": 0, "retry": 0, "fail": 0}


def _k():
    global KEYS
    if not KEYS:
        KEYS = settings.require_helius()
    k = KEYS[_i[0] % len(KEYS)]
    _i[0] += 1
    return k


class HeliusError(RuntimeError):
    pass


_COOLDOWN = {}   # cle -> timestamp avant lequel on ne la reutilise pas


def _k_ok():
    """Cle disponible. Une cle qui vient de renvoyer 429 est mise au repos :
    reessayer la MEME cle immediatement ne fait que confirmer son quota."""
    now = time.time()
    for _ in range(len(KEYS) * 3):
        k = _k()
        if _COOLDOWN.get(k, 0) <= now:
            return k
    k = min(KEYS, key=lambda x: _COOLDOWN.get(x, 0))
    d = max(0.0, _COOLDOWN.get(k, 0) - now)
    if d:
        time.sleep(min(d, 20.0))
    return k


def _http_key(build_url, payload=None, tries=10):
    """Comme _http mais tourne les cles a chaque essai (build_url(cle))."""
    last = None
    for t in range(tries):
        key = _k_ok()
        try:
            return _http(build_url(key), payload, tries=1)
        except HeliusError as e:
            last = str(e)
            if "429" in last:
                _COOLDOWN[key] = time.time() + 6.0
                STATS["retry"] += 1
                time.sleep(0.25)
                continue
            if any(c in last for c in ("500", "502", "503", "504", "timed out", "URLError")):
                STATS["retry"] += 1
                time.sleep(min(6.0, 0.6 * (t + 1)))
                continue
            raise
    STATS["fail"] += 1
    raise HeliusError("abandon apres %d essais (rotation de cles): %s" % (tries, last))


def _http(url, payload=None, tries=8):
    """Renvoie l'objet decode, ou leve HeliusError. Ne renvoie JAMAIS None
    silencieusement : un quota atteint doit interrompre la mesure, pas la
    tronquer."""
    last = None
    for t in range(tries):
        try:
            if payload is None:
                req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            else:
                req = urllib.request.Request(
                    url, data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json", "User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = "HTTP %d" % e.code
            if e.code in (429, 500, 502, 503, 504):
                STATS["retry"] += 1
                time.sleep(min(8.0, 0.8 * (t + 1) ** 1.6))
                continue
            raise HeliusError(last)
        except Exception as e:  # noqa: BLE001
            last = repr(e)
            STATS["retry"] += 1
            time.sleep(min(8.0, 0.8 * (t + 1)))
    STATS["fail"] += 1
    raise HeliusError("abandon apres %d essais: %s" % (tries, last))


def rpc(method, params):
    STATS["rpc"] += 1
    r = _http_key(lambda k: "https://mainnet.helius-rpc.com/?api-key=" + k,
                  {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    if "error" in r:
        raise HeliusError("%s: %s" % (method, json.dumps(r["error"])[:200]))
    return r.get("result")


def sig_page(addr, limit=1000, before=None):
    p = {"limit": limit}
    if before:
        p["before"] = before
    r = rpc("getSignaturesForAddress", [addr, p])
    if r is None:
        raise HeliusError("getSignaturesForAddress -> null")
    return r


def walk_sigs(addr, until_ts=None, max_pages=400, verbose=True):
    """Historique COMPLET (ou jusqu'a until_ts, exclusif), du plus recent au
    plus ancien. Leve si le quota coupe -> pas de troncature muette."""
    out, before, pages = [], None, 0
    while pages < max_pages:
        page = sig_page(addr, 1000, before)
        pages += 1
        if not page:
            break
        out += page
        before = page[-1]["signature"]
        old = page[-1].get("blockTime")
        if verbose and pages % 10 == 0:
            sys.stderr.write("  ..%s page %d n=%d oldest=%s\n" % (addr[:6], pages, len(out), old))
        if len(page) < 1000:
            break
        if until_ts and old and old < until_ts:
            break
    return out, pages


def enhanced(addr, limit=100, before=None):
    STATS["enh"] += 1
    suf = ("&before=" + before) if before else ""
    r = _http_key(
        lambda k: "https://api.helius.xyz/v0/addresses/%s/transactions?api-key=%s&limit=%d%s"
        % (addr, k, limit, suf))
    if not isinstance(r, list):
        raise HeliusError("enhanced -> %s" % str(r)[:200])
    return r


def tx(sig):
    return rpc("getTransaction", [sig, {"maxSupportedTransactionVersion": 0,
                                        "encoding": "jsonParsed"}])


def block(slot, sigs_only=False):
    cfg = {"maxSupportedTransactionVersion": 0, "rewards": False,
           "transactionDetails": "signatures" if sigs_only else "full",
           "encoding": "jsonParsed"}
    return rpc("getBlock", [slot, cfg])


def cached(name, fn):
    p = os.path.join(CACHE, name + ".json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    v = fn()
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(v, f)
    os.replace(tmp, p)
    return v


def save(name, obj):
    """Ecriture atomique + pseudonymisation a l'ecriture (voir redact.py)."""
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
# minimum de rente d'un compte systeme vide (0.00089088 SOL) : en dessous, un
# wallet ne peut meme pas exister durablement, a fortiori signer un achat.
RENT_MIN_SOL = 0.00089088
# frais de base d'une transaction Solana : 5000 lamports.
TX_FEE_SOL = 0.000005
