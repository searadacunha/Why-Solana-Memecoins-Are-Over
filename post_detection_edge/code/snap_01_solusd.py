#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hourly SOL/USD over the snapshot window, frozen next to it.

Same source and same keyless endpoint as code/expl_ledger.py (Binance SOLUSDT
klines), at hourly instead of daily resolution. The detector's prices are SOL
per token; this series is only used to express a position size in dollars
($100 / $500 / $1 000) and a market cap in dollars. A missing hour raises when
it is looked up; it never defaults to a neighbour silently.

Usage:
    python3 post_detection_edge/code/snap_01_solusd.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
OUT = os.path.join(DATA, "sol_usd_hourly.json")
URL = ("https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1h"
       "&startTime=%d&endTime=%d&limit=1000")


def main() -> None:
    if os.path.exists(OUT):
        sys.exit("already frozen: %s" % os.path.relpath(OUT, DATA))
    snap = json.load(open(os.path.join(DATA, "SNAPSHOT.json")))
    start = (int(snap["t_snap"]) - 45 * 86400) // 3600 * 3600
    end = int(snap["t_snap"])
    rows: dict[int, float] = {}
    t = start
    while t < end:
        req = urllib.request.Request(URL % (t * 1000, end * 1000), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            page = json.loads(r.read())
        if not page:
            raise RuntimeError("Binance returned no SOLUSDT hourly klines from %d" % t)
        for k in page:
            rows[int(k[0]) // 1000] = float(k[4])      # open time -> close
        t = int(page[-1][0]) // 1000 + 3600
    doc = {"source": "Binance SOLUSDT 1h klines, close, keyed on the hour's open time (UTC seconds)",
           "n": len(rows), "first": min(rows), "last": max(rows),
           "close_by_hour": {str(k): rows[k] for k in sorted(rows)}}
    with open(OUT, "w", encoding="utf8") as f:
        json.dump(doc, f, indent=0)
        f.write("\n")
    os.chmod(OUT, 0o444)
    print("%d hours, sha256 %s" % (len(rows), hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]))


if __name__ == "__main__":
    main()
