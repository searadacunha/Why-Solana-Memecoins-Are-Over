#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch the hourly series of the price of SOL in USD, from GeckoTerminal's
Raydium SOL/USDC pool 58oQChx4. Needed because the floor_capture swaps are
denominated in SOL per token while GeckoTerminal returns USD per token.

Output: data/sol_usd_hourly.json
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA

POOL = "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"   # Raydium SOL/USDC
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def get(url, tries=6):
    for a in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After", 0) or 10 * (a + 1)))
                continue
            if e.code == 404:
                return None
            time.sleep(3 * (a + 1))
        except Exception:  # noqa: BLE001  (transport / decode ; la boucle rejoue)
            time.sleep(3 * (a + 1))
    return None


def main():
    d = get(f"https://api.geckoterminal.com/api/v2/networks/solana/pools/"
            f"{POOL}/ohlcv/hour?limit=1000")
    lst = (d or {}).get("data", {}).get("attributes", {}).get("ohlcv_list") or []
    if not lst:
        raise SystemExit("echec de recuperation SOL/USDC")
    hourly = sorted([[int(x[0]), float(x[4])] for x in lst])
    out = {"source": "geckoterminal ohlcv/hour",
           "pool": POOL, "pair": "SOL/USDC (Raydium)",
           "n": len(hourly), "ts_min": hourly[0][0], "ts_max": hourly[-1][0],
           "fetched_at": int(time.time()),
           "hourly_close": hourly}
    p = os.path.join(DATA, "sol_usd_hourly.json")
    json.dump(out, open(p, "w"))
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("%d bougies horaires -> %s" % (len(hourly), os.path.relpath(p, root)))
    print(f"  min {min(c for _, c in hourly):.2f} USD   "
          f"max {max(c for _, c in hourly):.2f} USD")


if __name__ == "__main__":
    main()
