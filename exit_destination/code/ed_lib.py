#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ed_lib.py -- exit-wallet events from the frozen economic-mechanics table, and the shared constants of the
exit-destination study. No price is read here.

An event is one exit wallet in one launch: an owner that received the launch's tokens from one of its
snipers by a transfer (exits_full, kind "transfer", up to alert + 30 s). The receipt is the earliest such
transfer to that owner in the launch.
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "economic_mechanics", "code"))
import em_lib as E  # noqa: E402

DERIVED = os.path.join(STUDY, "derived")
TABLES = os.path.join(STUDY, "tables")
CACHE = os.path.join(STUDY, "data", "cache")
SELECTION = os.path.join(DERIVED, "selection.json")
N_PERM, SEED = E.N_PERM, E.SEED
SPLITS = E.SPLITS

# fixed by analysis_plan.md before any collection
TARGET_WALLETS = 300
CLUSTER_CAP = 0.25
EVENTS_PER_WALLET = 5
WINDOW_S = 2 * 3600
MAX_TX_EVENT = 10
PRIOR_TX = 5
MIN_SOL = 0.1
MAX_HOPS = 5
HOP_TX = 5
HOP_PAGES = 3
HUB_PAGES = 3
HUB_N = 3000
MAX_SIG_PAGES = 10
NEWEST_PAGES = 3
KEY_RPS = 2.0
MAX_FAIL_SHARE = 0.02
CALL_CAP = 18000


def events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One record per (exit wallet, launch), the snipers of the launch excluded as recipients."""
    out = []
    for r in rows:
        sn = {s["wallet"] for s in r["snipers"]}
        got: dict[str, dict[str, Any]] = {}
        for s in r["snipers"]:
            for x in s["exits_full"]:
                if x["kind"] != "transfer":
                    continue
                for o, tok in x["recipients"].items():
                    if o in sn or tok <= 0:
                        continue
                    e = got.setdefault(
                        o,
                        {
                            "wallet": o,
                            "mint": r["mint"],
                            "t": r["t"],
                            "split": r["split"],
                            "cluster": r["cluster"],
                            "snipers": set(),
                            "funders": set(),
                            "tokens": 0.0,
                            "receipt": None,
                        },
                    )
                    e["snipers"].add(s["wallet"])
                    f = E.fkey(s)
                    if f and not f.startswith("own:"):
                        e["funders"].add(f)
                    e["tokens"] += tok
                    k = (x["slot"], x["bt"] or 0, x["sig"])
                    if e["receipt"] is None or k < (e["receipt"]["slot"], e["receipt"]["bt"] or 0, e["receipt"]["sig"]):
                        e["receipt"] = {"sig": x["sig"], "slot": x["slot"], "bt": x["bt"]}
        out += got.values()
    return out


def by_wallet(ev: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    g: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in ev:
        g[e["wallet"]].append(e)
    for v in g.values():
        v.sort(key=lambda e: (e["receipt"]["slot"], e["receipt"]["sig"]))
    return g
