#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch, for every usable floor_capture capture, the HOURLY GeckoTerminal OHLCV
series of the token's pool (limit=1000 candles, which is 41 days).

Why re-fetch instead of reusing analysis_supervision/horizon.json: that file
marks 97 of 193 tokens "no_ohlcv", but a manual probe shows several of those
mints DO have candles (9f9k4eap has 50, J8QqdEur has 21). The original fetch
gave up after 4 attempts on HTTP 429, so its "no_ohlcv" conflates an absence of
volume with a network failure. Any statistic of the form "X % of tokens with no
volume" built on it would be false.

Call strategy, to spend as little quota as possible:
  1. try the pool recorded in the capture (`pool`) directly. Checked
     beforehand: over the 193 tokens of horizon.json, that pool is the same as
     the one GeckoTerminal designates in 188 cases out of 193.
  2. only if it returns NO candle at all, query /tokens/{mint}/pools and retry
     with the deepest pool.

The final statuses are kept distinct:
     ok           : hourly candles are present
     zero_bougie  : the pool or pools are known, but no candle is indexed
     pool_absent  : GeckoTerminal knows no pool for this mint
     echec_reseau : gave up, and it will be retried on the next run

Resumes on its own. Output: data/cout_acheteur/gt_raw.json
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, load_captures

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
GT = "https://api.geckoterminal.com/api/v2"
PACE = 2.2
OUTDIR = os.path.join(DATA, "cout_acheteur")
OUT = os.path.join(OUTDIR, "gt_raw.json")


def get(url, tries=6):
    for a in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                w = float(e.headers.get("Retry-After", 0) or 0) or min(10 * (a + 1), 60)
                time.sleep(w)
                continue
            if e.code == 404:
                return {"__404__": True}
            time.sleep(3 * (a + 1))
        except Exception:  # noqa: BLE001  (transport / decode ; la boucle rejoue)
            time.sleep(3 * (a + 1))
    return None


def ohlcv(pool):
    o = get(f"{GT}/networks/solana/pools/{pool}/ohlcv/hour?limit=1000")
    if o is None:
        return None
    lst = (o or {}).get("data", {}).get("attributes", {}).get("ohlcv_list") or []
    return sorted([[int(x[0]), float(x[1]), float(x[2]), float(x[3]),
                    float(x[4]), float(x[5])] for x in lst])


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    caps, rej, nfiles = load_captures(verbose=True)
    store = json.load(open(OUT)) if os.path.exists(OUT) else {}
    todo = [c for c in caps if store.get(c["mint"], {}).get("status") not in
            ("ok", "zero_bougie", "pool_absent")]
    print(f"{len(caps)} captures ; {len(todo)} a (re)traiter", flush=True)

    for i, c in enumerate(todo):
        mint = c["mint"]
        rec = {"mint": mint, "created": c["_created"], "pool_hint": c.get("pool"),
               "supply": c.get("supply"), "detect_mc": c.get("detect_mc"),
               "fetched_at": int(time.time())}
        cand = rec["pool_hint"]
        series, used, why = [], None, []
        if cand:
            series = ohlcv(cand)
            time.sleep(PACE)
            why.append(f"hint:{'None' if series is None else len(series)}")
            if series:
                used = cand
        if not series:
            p = get(f"{GT}/networks/solana/tokens/{mint}/pools")
            time.sleep(PACE)
            pools = []
            if p and not p.get("__404__"):
                for x in p.get("data", []):
                    a = x.get("attributes", {})
                    try:
                        res = float(a.get("reserve_in_usd") or 0)
                    except (TypeError, ValueError):
                        res = 0.0
                    pools.append({"address": a.get("address"), "reserve_usd": res})
            rec["pools"] = pools
            why.append(f"pools:{len(pools)}")
            if not pools:
                rec["status"] = "pool_absent" if p is not None else "echec_reseau"
                rec["trace"] = why
                store[mint] = rec
                _save(store, i, len(todo), mint, rec["status"])
                continue
            best = max(pools, key=lambda z: z["reserve_usd"])["address"]
            if best != cand:
                series = ohlcv(best)
                time.sleep(PACE)
                why.append(f"best:{'None' if series is None else len(series)}")
                if series:
                    used = best
        rec["trace"] = why
        if series is None:
            rec["status"] = "echec_reseau"
        else:
            rec["pool"] = used or cand
            rec["ohlcv"] = series
            rec["status"] = "ok" if series else "zero_bougie"
        store[mint] = rec
        _save(store, i, len(todo), mint, rec["status"])

    json.dump(store, open(OUT, "w"))
    print(Counter(v.get("status") for v in store.values()), flush=True)
    print("-> %s" % os.path.relpath(OUT, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _save(store, i, n, mint, status):
    print(f"  {i+1}/{n} {mint[:8]} {status}", flush=True)
    if (i + 1) % 5 == 0:
        json.dump(store, open(OUT, "w"))


if __name__ == "__main__":
    main()
