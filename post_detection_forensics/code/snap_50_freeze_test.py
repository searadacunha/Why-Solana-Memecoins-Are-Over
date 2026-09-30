#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Freeze the TEST population once: every alert after the first snapshot.

The first snapshot (post_detection_edge/data/, T_SNAP = 2026-09-29 11:23:00 UTC)
holds TRAIN and VALIDATION. The TEST of this study is made of alerts the
detector raised afterwards, which nobody has looked at. This script copies the
live journal and price series a second time, at T_SNAP2 = now (to the minute),
and keeps:
  journal  every line up to T_SNAP2, with the same reduction and redaction as
           the first snapshot (post_detection_edge/code/snap_00_freeze.py is
           reused, not rewritten): the context features of a TEST alert count
           what came before it, including before T_SNAP;
  series   the price reads of the TEST alerts only, cut at T_SNAP2;
  test     the TEST alerts: T_SNAP < alert time <= T_SNAP2 - 1 h, so that the
           1 h window of every one of them had time to happen.
SOL/USD hourly is re-fetched over the new window. The result is read-only and
the script refuses to run twice.

Usage:
    DETECTOR_DIR=/path/to/detector python3 post_detection_forensics/code/snap_50_freeze_test.py
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
OUT = os.path.join(STUDY, "data", "test_snapshot")
MANIFEST = os.path.join(OUT, "SNAPSHOT_TEST.json")
_spec = importlib.util.spec_from_file_location("snap00", os.path.join(ROOT, "post_detection_edge", "code",
                                                                      "snap_00_freeze.py"))
S0 = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(S0)  # type: ignore[union-attr]
T_SNAP = json.load(open(os.path.join(ROOT, "post_detection_edge", "data", "SNAPSHOT.json")))["t_snap"]
MATURITY = 3600.0


def sha256(p: str) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main() -> None:
    root = os.environ.get("DETECTOR_DIR")
    if not root:
        sys.exit("set DETECTOR_DIR")
    if os.path.exists(MANIFEST):
        sys.exit("TEST snapshot already frozen; it is immutable")
    os.makedirs(OUT, exist_ok=True)
    etat = os.path.join(root, "etat")
    t2 = float(int(time.time()) // 60 * 60)
    tmp = os.path.join(OUT, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    shutil.copyfile(os.path.join(etat, "journal.jsonl"), os.path.join(tmp, "journal.jsonl"))
    srcs = sorted(x for x in os.listdir(etat) if re.fullmatch(r"prix-\d{8}-\d{6}\.jsonl(\.gz)?", x))
    copies = []
    for x in [os.path.join(etat, s) for s in srcs] + [os.path.join(etat, "prix.jsonl")]:
        d = os.path.join(tmp, os.path.basename(x))
        shutil.copyfile(x, d)
        copies.append(d)
    rows, counts = S0.reduce_journal(os.path.join(tmp, "journal.jsonl"), t2)
    jpath = os.path.join(OUT, "journal.jsonl.gz")
    with gzip.open(jpath, "wt", encoding="utf8", compresslevel=9) as g:
        for r in rows:
            g.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    test = {r["mint"]: r["t"] for r in rows if r["genre"] == "alerte_lancement" and T_SNAP < r["t"] <= t2 - MATURITY}
    spath = os.path.join(OUT, "series.txt.gz")
    scounts = S0.reduce_series(copies, test, t2, spath)
    shutil.rmtree(tmp)
    # SOL/USD over the new window (same source as the first snapshot)
    start = int(T_SNAP) // 3600 * 3600 - 7 * 86400
    hours: dict[int, float] = {}
    t = start
    while t < t2:
        url = ("https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1h&startTime=%d&endTime=%d&limit=1000"
               % (t * 1000, int(t2) * 1000))
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                                    timeout=30) as r:
            page = json.loads(r.read())
        if not page:
            raise RuntimeError("no SOLUSDT klines from %d" % t)
        for k in page:
            hours[int(k[0]) // 1000] = float(k[4])
        t = int(page[-1][0]) // 1000 + 3600
    upath = os.path.join(OUT, "sol_usd_hourly.json")
    json.dump({"source": "Binance SOLUSDT 1h klines, close",
               "close_by_hour": {str(k): hours[k] for k in sorted(hours)}}, open(upath, "w"))
    alerts_path = os.path.join(OUT, "test_alerts.json")
    json.dump(sorted(test), open(alerts_path, "w"))
    man = {"t_snap_previous": T_SNAP, "t_snap_test": t2,
           "t_snap_test_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t2)),
           "test_rule": "T_SNAP < alert time <= T_SNAP_TEST - 3600 s",
           "n_test_alerts": len(test), "journal_rows_by_type": counts, "series": scounts,
           "files": {os.path.basename(p): sha256(p) for p in (jpath, spath, upath, alerts_path)}}
    json.dump(man, open(MANIFEST, "w"), indent=1)
    for p in (jpath, spath, upath, alerts_path, MANIFEST):
        os.chmod(p, 0o444)
    print(json.dumps({k: man[k] for k in ("t_snap_test_utc", "n_test_alerts", "series")}, indent=1))


if __name__ == "__main__":
    main()
