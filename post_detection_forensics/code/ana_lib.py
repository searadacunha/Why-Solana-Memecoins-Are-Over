#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ana_lib.py -- what every analysis script of analysis_plan.md shares.

Reads only the frozen analytic table and refuses to run if its sha256 differs
from derived/TABLE_FREEZE.json. Statistics: AUC and its Mann-Whitney p, Wilson,
Fisher, Benjamini-Hochberg, and cluster bootstraps (operator clusters resampled)
for differences of medians, of rates and of AUCs.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from typing import Any, Callable, Optional, Sequence

import feat_30_build as FB
import fml

pde = FB.pde
STUDY = FB.STUDY
TABLE = os.path.join(FB.DERIVED, "analytic_table.jsonl.gz")
FREEZE = os.path.join(FB.DERIVED, "TABLE_FREEZE.json")
TABLES = os.path.join(STUDY, "tables")
PRIMARY = "A_conf_2x_15m"
SEED = 20260929
B = 1000
SAFE = sorted(f for f in FB.FAMILY)                 # PRE_ENTRY, all SAFE after temporal_leakage_audit.md
FAM = FB.FAMILY


def load(path: str = TABLE, freeze: str = FREEZE) -> list[dict[str, Any]]:
    doc = json.load(open(freeze))
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if sha != doc["sha256"]:
        sys.exit("the analytic table differs from the frozen one (%s)" % freeze)
    with gzip.open(path, "rt", encoding="utf8") as fh:
        return [json.loads(x) for x in fh]


def xy(rows: Sequence[dict[str, Any]], split: str, label: str = PRIMARY, cut: str = "A"
       ) -> list[tuple[dict[str, Any], dict[str, Any], int]]:
    return [(r, r["f" + cut], r["y"][label]) for r in rows
            if r["split"] == split and r["y"].get(label) is not None]


def auc_p(a: float, n1: int, n0: int) -> float:
    se = math.sqrt((n1 + n0 + 1) / (12.0 * n1 * n0))
    return math.erfc(abs(a - 0.5) / se / math.sqrt(2))


def rate(k: int, n: int) -> str:
    return pde.rate_cell(k, n)


def q(v: Sequence[float], p: float) -> Optional[float]:
    v = sorted(x for x in v if x is not None)
    return v[int(p * (len(v) - 1))] if v else None


def _clusters(items: Sequence[tuple[str, Any]]) -> tuple[list[str], dict[str, list[Any]]]:
    by: dict[str, list[Any]] = defaultdict(list)
    for c, v in items:
        by[c].append(v)
    return sorted(by), by


def boot(items: Sequence[tuple[str, Any]], stat: Callable[[list[Any]], Optional[float]], b: int = B
         ) -> tuple[Optional[float], Optional[float]]:
    """95 % percentile CI of stat(items), resampling operator clusters."""
    keys, by = _clusters(items)
    if not keys:
        return None, None
    rng = random.Random(SEED)
    out = []
    for _ in range(b):
        sample = [v for _ in keys for v in by[keys[rng.randrange(len(keys))]]]
        s = stat(sample)
        if s is not None:
            out.append(s)
    if len(out) < b // 2:
        return None, None
    out.sort()
    return out[int(0.025 * (len(out) - 1))], out[int(0.975 * (len(out) - 1))]


def med_diff(sample: list[tuple[Optional[float], int]]) -> Optional[float]:
    w = [x for x, y in sample if y == 1 and x is not None]
    lo = [x for x, y in sample if y == 0 and x is not None]
    if not w or not lo:
        return None
    return q(w, 0.5) - q(lo, 0.5)


def auc_of(sample: list[tuple[float, int]]) -> Optional[float]:
    s = [a for a, _ in sample]
    y = [b for _, b in sample]
    return fml.roc_auc(s, y) if 0 < sum(y) < len(y) else None


def spearman(a: Sequence[float], b: Sequence[float]) -> float:
    """Rank correlation, ties at their mean rank; 0 below 3 pairs or with a constant side."""
    def ranks(v: Sequence[float]) -> list[float]:
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    if len(a) < 3:
        return 0.0
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else 0.0


def write(name: str, lines: list[str]) -> None:
    os.makedirs(TABLES, exist_ok=True)
    with open(os.path.join(TABLES, name), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")
