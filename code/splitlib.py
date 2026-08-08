#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
splitlib.py -- the split-grouping core, shared by the phase-1 funding tools
(02_cn_outflows.py, 03_split_detector.py, 04_early_buyers_funding.py), which
each used to carry their own byte-for-byte copy of it.

A "split" is a single sum divided through a swap service into several fresh
wallets: they receive near-identical amounts within a short window. This groups
wallets by amount quasi-equality + temporal proximity and returns the clusters
of at least `min_cluster` distinct wallets. Stdlib only; no network, no state.

The adversarial null model a1_null_model.py deliberately keeps its OWN copy of
this logic so it stays runnable from published data alone and byte-stable under
run_all.py --strict; do not route a1 through this module.
"""
from __future__ import annotations

from typing import Any, Iterable

# Defaults shared by 02/03; 04 widens the amount band in its own incoming filter.
REL_TOL = 1e-4        # relative amount-equality tolerance (0.01 %)
WINDOW_S = 3600       # temporal window of one split
MIN_CLUSTER = 3       # minimum distinct wallets to call it a split


def find_splits(funding: dict[str, list[tuple[float, int]]],
                rel_tol: float = REL_TOL, window_s: int = WINDOW_S,
                min_cluster: int = MIN_CLUSTER) -> list[dict[str, Any]]:
    """Group wallets by a near-identical amount received in the same window.

    funding maps wallet -> [(amount_sol, ts), ...]. Returns one dict per
    detected split, richest-first, each carrying both `first_ts` and `date`
    fields so every historical caller finds the key it printed.
    """
    events = [(w, amt, ts) for w, lst in funding.items() for amt, ts in lst]
    events.sort(key=lambda e: e[1])
    clusters: list[dict[str, Any]] = []
    used: set[int] = set()
    for i, (w, amt, ts) in enumerate(events):
        if i in used:
            continue
        group = [(i, w, amt, ts)]
        for j in range(i + 1, len(events)):
            if j in used:
                continue
            w2, amt2, ts2 = events[j]
            if abs(amt2 - amt) > amt * rel_tol:
                break                          # sorted by amount: nothing else fits
            if w2 != w and abs(ts2 - ts) <= window_s:
                group.append((j, w2, amt2, ts2))
        wallets = {g[1] for g in group}
        if len(wallets) >= min_cluster:
            for g in group:
                used.add(g[0])
            times = [g[3] for g in group]
            import datetime as _dt
            clusters.append({
                "amount_sol": round(amt, 9),
                "n_wallets": len(wallets),
                "wallets": sorted(wallets),
                "span_seconds": max(times) - min(times),
                "first_ts": min(times),
                "date": _dt.datetime.fromtimestamp(
                    min(times), _dt.timezone.utc).strftime("%Y-%m-%d"),
            })
    return sorted(clusters, key=lambda c: -c["n_wallets"])
