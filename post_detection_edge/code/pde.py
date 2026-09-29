#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pde.py -- the definitions every script of the post-detection study shares.

Everything that decides a number lives here once: the split dates, the
coverage rule that separates an observed failure from a censored window, the
targets, the price at a given latency, and the statistics. The constants below
were fixed before any outcome was computed; methodology.md records why each
one has the value it has.

Stdlib only, like the rest of the repository. Wilson, median and quantile are
imported from code/statlib.py rather than rewritten.
"""
from __future__ import annotations

import bisect
import calendar
import gzip
import json
import math
import os
import random
import sys
from collections import defaultdict
from typing import Any, Iterable, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
DATA = os.path.join(STUDY, "data")
DERIVED = os.path.join(STUDY, "derived")
TABLES = os.path.join(STUDY, "tables")
sys.path.insert(0, os.path.join(os.path.dirname(STUDY), "code"))
from statlib import median, quantile, wilson  # noqa: E402,F401  (re-exported)


def utc(s: str) -> float:
    """'YYYY-mm-dd HH:MM:SS' in UTC -> epoch seconds."""
    return float(calendar.timegm(__import__("time").strptime(s, "%Y-%m-%d %H:%M:%S")))


# --- splits (walk-forward, by alert time) ----------------------------------- #
# TRAIN ends at the T0 of the protocol pre-registered on 2026-08-29: every alert
# before it was mined by earlier campaigns. VALIDATION runs to 2026-09-15 00:00.
# TEST is everything after, up to the snapshot, and is sealed until LOCK.json.
T_TRAIN_END = utc("2026-08-29 18:36:00")
T_VAL_END = utc("2026-09-15 00:00:00")
# The detector sampled every 45 s until this restart, then every ~5 s for the
# first 180 s after each alert (45 s afterwards). Horizons under 180 s are only
# resolvable after it.
T_FINE = utc("2026-08-25 21:47:00")
FINE_WINDOW = 180.0


def split_of(t: float) -> str:
    if t < T_TRAIN_END:
        return "train"
    return "val" if t < T_VAL_END else "test"


# --- targets ---------------------------------------------------------------- #
HORIZONS = (10, 30, 60, 300, 900, 3600, 86400)
H_LABEL = {10: "10s", 30: "30s", 60: "60s", 300: "5m", 900: "15m", 3600: "1h", 86400: "24h"}
THRESHOLDS = (1.5, 2.0, 3.0, 5.0, 10.0)
LATENCIES = (0, 5, 10, 15, 20)
PRIMARY = (2.0, 3600)          # TARGET_2X at 1 h: chosen on coverage alone, see methodology.md

# Coverage rule. A window [entry, entry + H] is OBSERVED when no two consecutive
# observation instants inside it (the entry instant included) are further apart
# than G, and the series reaches H. G is set from the sampling regime, not from
# outcomes: 25 s inside the fine window (99th percentile of the gaps there is
# 23.9 s), 135 s elsewhere (three missed 45 s rounds; 99th percentile 51.2 s).
GAP_FINE = 25.0
GAP_COARSE = 135.0
LATENCY_TOL = 10.0             # an entry "at L seconds" needs a price in [L, L + 10]


def gap_limit(fine: bool, h: float) -> float:
    return GAP_FINE if (fine and h <= FINE_WINDOW) else GAP_COARSE


def load_series() -> dict[str, list[tuple[float, float]]]:
    """{mint: [(seconds since alert, multiple of p0), ...]} sorted by time."""
    s: dict[str, list[tuple[float, float]]] = defaultdict(list)
    with gzip.open(os.path.join(DATA, "series.txt.gz"), "rt", encoding="utf8") as f:
        for line in f:
            m, dt, mult, _ = line.split()
            s[m].append((float(dt), float(mult)))
    for v in s.values():
        v.sort()
    return dict(s)


def load_journal() -> list[dict[str, Any]]:
    with gzip.open(os.path.join(DATA, "journal.jsonl.gz"), "rt", encoding="utf8") as f:
        return [json.loads(line) for line in f]


def entry_point(pts: Sequence[tuple[float, float]], lat: float) -> Optional[tuple[float, float]]:
    """(dt, multiple) of the first price available at or after `lat` seconds.

    lat = 0 is P0 itself, read at the alert. For lat > 0 the first point in
    [lat, lat + LATENCY_TOL] is taken, never interpolated; None if there is none.
    """
    if lat == 0:
        return (0.0, 1.0)
    i = bisect.bisect_left(pts, (lat, -math.inf))
    if i < len(pts) and pts[i][0] <= lat + LATENCY_TOL:
        return pts[i]
    return None


def window(pts: Sequence[tuple[float, float]], t_in: float, h: float, fine: bool
           ) -> tuple[Optional[float], bool]:
    """(max multiple over (t_in, t_in + h], observed?) for one entry.

    The maximum is taken over the prices actually read, so it can only miss a
    peak that fell between two reads, never invent one. `observed` is the
    coverage rule above; it does not look at the prices.
    """
    g = gap_limit(fine, h)
    end = t_in + h
    i = bisect.bisect_right(pts, (t_in, math.inf))
    inside, prev, max_gap, reached = [], t_in, 0.0, False
    while i < len(pts):
        dt, m = pts[i]
        max_gap = max(max_gap, dt - prev)
        prev = dt
        if dt > end:
            reached = True
            break
        inside.append(m)
        i += 1
    if not reached and inside and end - prev <= g:
        reached = True
    mx = max(inside) if inside else None
    return mx, bool(inside) and reached and max_gap <= g


def outcome(mx: Optional[float], observed: bool, k: float) -> Optional[int]:
    """1 hit, 0 observed miss, None censored. A hit is a hit even in a window
    with a gap (the price was read); a miss needs the whole window observed.
    Complete-case estimates use only observed windows, hit or not."""
    if mx is not None and mx >= k:
        return 1
    return 0 if observed else None


# --- statistics -------------------------------------------------------------- #
def auc(scores: Sequence[float], y: Sequence[int]) -> Optional[float]:
    """Mann-Whitney AUC with average ranks for ties; None if a class is empty."""
    pairs = sorted(zip(scores, y))
    n1 = sum(y)
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return None
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = r
        i = j + 1
    r1 = sum(r for r, (_, yy) in zip(ranks, pairs) if yy == 1)
    return (r1 - n1 * (n1 + 1) / 2) / (n1 * n0)


def auc_p(a: float, n1: int, n0: int) -> float:
    """Two-sided normal-approximation p for an AUC (Hanley-McNeil null variance)."""
    se = math.sqrt((n1 + n0 + 1) / (12.0 * n1 * n0))
    z = abs(a - 0.5) / se
    return math.erfc(z / math.sqrt(2))


def fisher_greater(a: int, b: int, c: int, d: int) -> float:
    """One-sided Fisher exact p that group 1 (a hits of a+b) beats group 2 (c of c+d)."""
    n, r1, c1 = a + b + c + d, a + b, a + c

    def lc(nn: int, kk: int) -> float:
        return math.lgamma(nn + 1) - math.lgamma(kk + 1) - math.lgamma(nn - kk + 1)
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    tot = 0.0
    for x in range(a, hi + 1):
        if x < lo:
            continue
        tot += math.exp(lc(r1, x) + lc(n - r1, c1 - x) - lc(n, c1))
    return min(1.0, tot)


def bh(pvals: Sequence[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values, same order as the input."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    run = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        run = min(run, pvals[i] * m / rank)
        adj[i] = run
    return adj


def holm(pvals: Sequence[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * pvals[i]))
        adj[i] = run
    return adj


def cluster_boot_rate_diff(rows: Sequence[tuple[str, int, int]], b: int = 2000, seed: int = 20260929
                           ) -> tuple[Optional[float], Optional[float]]:
    """95 % percentile CI of P(y | signal) - P(y | not signal), resampling clusters.

    rows = (cluster id, in_signal 0/1, y 0/1). Clusters, not alerts, are drawn:
    two alerts of one operator are not two independent observations.
    """
    by: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for c, s, y in rows:
        by[c].append((s, y))
    keys = sorted(by)
    rng = random.Random(seed)
    out = []
    for _ in range(b):
        a1 = n1 = a0 = n0 = 0
        for _k in range(len(keys)):
            for s, y in by[keys[rng.randrange(len(keys))]]:
                if s:
                    n1 += 1
                    a1 += y
                else:
                    n0 += 1
                    a0 += y
        if n1 and n0:
            out.append(a1 / n1 - a0 / n0)
    if len(out) < b // 2:
        return (None, None)
    out.sort()
    return out[int(0.025 * (len(out) - 1))], out[int(0.975 * (len(out) - 1))]


def cluster_boot_mean(rows: Sequence[tuple[str, float]], b: int = 2000, seed: int = 20260929
                      ) -> tuple[Optional[float], Optional[float]]:
    """95 % percentile CI of a mean, resampling clusters."""
    by: dict[str, list[float]] = defaultdict(list)
    for c, x in rows:
        by[c].append(x)
    keys = sorted(by)
    if not keys:
        return (None, None)
    rng = random.Random(seed)
    out = []
    for _ in range(b):
        tot = n = 0.0
        for _k in range(len(keys)):
            v = by[keys[rng.randrange(len(keys))]]
            tot += sum(v)
            n += len(v)
        out.append(tot / n)
    out.sort()
    return out[int(0.025 * (b - 1))], out[int(0.975 * (b - 1))]


def pct(x: Optional[float], nd: int = 1) -> str:
    return "n/a" if x is None else ("%." + str(nd) + "f %%") % (100 * x)


def rate_cell(k: int, n: int) -> str:
    if n == 0:
        return "n/a (0)"
    lo, hi = wilson(k, n)
    return "%.1f %% (%d/%d) [%.1f-%.1f]" % (100 * k / n, k, n, 100 * lo, 100 * hi)


def write_table(name: str, text: str) -> str:
    os.makedirs(TABLES, exist_ok=True)
    p = os.path.join(TABLES, name)
    with open(p, "w", encoding="utf8") as f:
        f.write(text.rstrip() + "\n")
    return p


def read_rows(name: str) -> list[dict[str, Any]]:
    with gzip.open(os.path.join(DERIVED, name), "rt", encoding="utf8") as f:
        return [json.loads(line) for line in f]


def write_rows(name: str, rows: Iterable[dict[str, Any]]) -> None:
    os.makedirs(DERIVED, exist_ok=True)
    # mtime=0: the gzip header otherwise carries the write time, and the sha256
    # recorded in LOCK.json would change on every regeneration of identical rows
    with open(os.path.join(DERIVED, name), "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
            for r in rows:
                gz.write((json.dumps(r, sort_keys=True) + "\n").encode("utf8"))
