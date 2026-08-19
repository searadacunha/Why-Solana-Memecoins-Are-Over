#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
statlib.py -- the small pure statistics shared across the dossier, defined once.

Only the genuinely identical helpers live here: the Wilson interval and the
None-filtering median / quantile, which previously existed in four and three
near-copies respectively (common.py, pumplib.py, lib_verif.py,
09_bundle_snipe.py, f_signature_gros_tokens.py).

Not here: the bootstrap and cluster-bootstrap CIs. They are not duplicates,
they differ by construction (cross-version LCG in pumplib vs random.Random in
common/t1, different seeds, B and estimators), and merging them would change
published numbers. They stay with the module that owns their procedure.

Stdlib only.
"""
from __future__ import annotations

import statistics
from typing import Optional, Sequence


def wilson(k: int, n: int, z: float = 1.96) -> tuple[Optional[float], Optional[float]]:
    """Wilson 95 % interval for a proportion, clamped to [0, 1].

    Preferred over the normal interval as the proportion approaches 0 or 1,
    which is the case throughout this repository. Returns (None, None) for
    n == 0. The result is a fraction in [0, 1]; callers that report a percentage
    multiply by 100 at the call site.

    The arithmetic (each term divided by d separately, `** 0.5`, clamped) is
    kept bit-for-bit identical to the historical common.wilson so every
    offline table it feeds reproduces byte for byte under run_all.py --strict.
    """
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def median(xs: Sequence[Optional[float]]) -> Optional[float]:
    """Median, ignoring None; None if the sequence is empty after filtering."""
    vals = [x for x in xs if x is not None]
    return statistics.median(vals) if vals else None


def quantile(xs: Sequence[Optional[float]], q: float) -> Optional[float]:
    """Nearest-rank quantile, ignoring None; None if empty after filtering.

    Index formula identical to the historical pumplib.quantile / common.q so
    the value every offline table already prints is reproduced byte for byte.
    """
    vals = sorted(x for x in xs if x is not None)
    if not vals:
        return None
    i = min(len(vals) - 1, max(0, int(round(q * (len(vals) - 1)))))
    return vals[i]
