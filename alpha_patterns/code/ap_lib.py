#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ap_lib.py -- definitions shared by every script of the exploratory alpha-pattern search.

EXPLORATORY study, separate from the frozen confirmatory work. Inputs are read only:
  W  = WSMO-signal-search worktree (frozen per-alert tables, price series, cost model code)
  PD = WSMO-pattern-discovery worktree (unfrozen feature table of an interrupted study)
Nothing under WSMO-bundle-outcomes is ever opened. No network, no .env.

The four time blocks, the labels and the stage guards live here once.
"""
from __future__ import annotations

import calendar
import gzip
import hashlib
import json
import math
import os
import sys
import time
from typing import Any, Iterable, Optional

import numpy as np

sys.dont_write_bytecode = True  # never write __pycache__ into the read-only worktrees

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
DERIVED = os.path.join(STUDY, "derived")
TABLES = os.path.join(STUDY, "tables")
REGISTRE = os.path.join(STUDY, "registre")
CONTROLES = os.path.join(STUDY, "controles")

CRYPTO = os.path.dirname(STUDY)
W = os.path.join(CRYPTO, "WSMO-signal-search")
PD = os.path.join(CRYPTO, "WSMO-pattern-discovery", "pattern_discovery")
SS = os.path.join(W, "signal_search")
FORBIDDEN = os.path.join(CRYPTO, "WSMO-bundle-outcomes")

ANALYTIC = os.path.join(W, "post_detection_forensics/derived/analytic_table.jsonl.gz")
EZ_TABLE = os.path.join(W, "entry_zone/derived/ez_table.jsonl.gz")
SC_TABLE = os.path.join(W, "sniper_capital/derived/sc_table.jsonl.gz")
CD_TABLE = os.path.join(W, "coordination_detection/derived/cd_table.jsonl.gz")
EM_TABLE = os.path.join(W, "economic_mechanics/derived/em_table.jsonl.gz")
KG_FEATS = os.path.join(W, "known_group_reentry/derived/kg_features.jsonl.gz")
PDE_DEV = os.path.join(W, "post_detection_edge/derived/dataset_dev.jsonl.gz")
PDE_TEST = os.path.join(W, "post_detection_edge/derived/dataset_test.sealed.jsonl.gz")
JOURNAL = os.path.join(W, "post_detection_edge/data/journal.jsonl.gz")
SERIES = os.path.join(W, "post_detection_edge/data/series.txt.gz")
PD_TABLE = os.path.join(PD, "derived/pd_table.jsonl.gz")
PD_FEATS = os.path.join(PD, "derived/pd_features.json")
SS_FEATS = {fam: os.path.join(SS, "derived", "feat_%s.jsonl.gz" % fam)
            for fam in ("bundle_sizing", "early_flow", "funding", "history", "slot0")}


def utc(s: str) -> float:
    return float(calendar.timegm(time.strptime(s, "%Y-%m-%d %H:%M:%S")))


# --- time blocks (fixed on alert counts only, before any outcome of this study) -------------- #
T_FINE = utc("2026-08-25 21:47:00")       # 5 s sampling starts; rows before it are not eligible (coarse labels)
T_DISC_END = utc("2026-09-07 00:00:00")   # DISCOVERY  : rule generation
T_SEL_END = utc("2026-09-15 00:00:00")    # SELECTION  : mechanical choice of the frozen candidates
T_VAL_END = utc("2026-09-22 00:00:00")    # VALIDATION : one read of the frozen list
T_SNAP = 1790680980.0                     # OOS ends at the snapshot (2026-09-29 11:23 UTC)
BLOCKS = ("DISC", "SEL", "VAL", "OOS")


def block_of(t: float) -> str:
    if t >= T_SNAP:
        raise ValueError("alert after the snapshot: forbidden (future confirmatory TEST)")
    if t < T_DISC_END:
        return "DISC"
    if t < T_SEL_END:
        return "SEL"
    return "VAL" if t < T_VAL_END else "OOS"


# --- labels and trades (fixed before any rate was computed) --------------------------------- #
LAT = 5.0                       # entry = first price read in [5, 15] s after the alert
MULTS = (2.0, 3.0, 5.0)
HORIZONS = (1800, 3600, 7200)   # 1 h is primary; 30 min and 2 h are robustness variants
PRIMARY_H = 3600
TARGETS = ("Y2", "Y3", "Y5")    # confirmed (two consecutive reads) k x the entry price within 1 h
COST = {"fee_per_leg": 0.01, "fixed_sol_per_tx": 0.005, "k_pool": 1.39e10, "k_curve": 30 * 1.073e9}
SIZES = (100, 500, 1000)
RESOLVE_1H = 3600 + 15 + 135 + 60   # a prior alert's 1 h outcome is known this long after its alert
# pre-declared trade attached to each target: buy at +5 s, take profit at k x (sold at the NEXT read,
# a polling bot), no stop, time exit at 1 h. Variants are sensitivities, never selected on.
STRAT_OF = {"Y2": "tp2_next", "Y3": "tp3_next", "Y5": "tp5_next"}


# --- stage guards ---------------------------------------------------------------------------- #
SEL_FREEZE = os.path.join(STUDY, "SELECTION_FREEZE.json")
VAL_DONE = os.path.join(STUDY, "VALIDATION_READ.json")
OOS_DONE = os.path.join(STUDY, "OOS_READ.json")
STAGE_BLOCKS = {"discovery": ("DISC",), "selection": ("DISC", "SEL"),
                "validation": ("DISC", "SEL", "VAL"), "oos": ("DISC", "SEL", "VAL", "OOS")}


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_freeze() -> dict[str, Any]:
    """The frozen candidate list and the code that reads the hold-out blocks must be unchanged."""
    if not os.path.exists(SEL_FREEZE):
        raise RuntimeError("SELECTION_FREEZE.json is missing: VALIDATION and OOS stay closed")
    fr = json.load(open(SEL_FREEZE))
    for rel, sha in fr["files"].items():
        if sha256_file(os.path.join(STUDY, rel)) != sha:
            raise RuntimeError("frozen file changed since the selection freeze: " + rel)
    return fr


def allowed_blocks(stage: str) -> tuple[str, ...]:
    if stage not in STAGE_BLOCKS:
        raise ValueError(stage)
    if stage in ("validation", "oos"):
        check_freeze()
    if stage == "oos" and not os.path.exists(VAL_DONE):
        raise RuntimeError("VALIDATION has not been read yet: OOS stays closed")
    return STAGE_BLOCKS[stage]


# --- io --------------------------------------------------------------------------------------- #
def jl(path: str) -> Iterable[dict[str, Any]]:
    if os.path.abspath(path).startswith(FORBIDDEN):
        raise RuntimeError("forbidden path: " + path)
    with gzip.open(path, "rt", encoding="utf8") as fh:
        for line in fh:
            yield json.loads(line)


def write_jl(path: str, rows: Iterable[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=6, mtime=0) as gz:
            for r in rows:
                gz.write((json.dumps(r, sort_keys=True) + "\n").encode("utf8"))


def write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8") as f:
        json.dump(obj, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def load_base() -> list[dict[str, Any]]:
    """One record per alert, chronological: mint, t, block, fine, cluster (inference only), p0."""
    out = []
    for r in jl(ANALYTIC):
        out.append({"mint": r["mint"], "t": r["t"], "utc": r["utc"], "fine": bool(r["fine"]),
                    "cluster": r["cluster"], "p0": r["p0"], "actor_type": r["actor_type"],
                    "block": block_of(r["t"])})
    out.sort(key=lambda r: (r["t"], r["mint"]))
    if len(out) != 1657 or len({r["mint"] for r in out}) != 1657:
        raise ValueError("base table is not the 1,657-alert snapshot")
    return out


def load_labels(stage: str) -> dict[str, dict[str, Any]]:
    """Labels of the blocks the stage may read; every other block is withheld."""
    blocks = allowed_blocks(stage)
    out = {}
    for r in jl(os.path.join(DERIVED, "labels.jsonl.gz")):
        if r["block"] in blocks:
            out[r["mint"]] = r
    return out


# --- statistics ------------------------------------------------------------------------------- #
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def wilson_lb_vec(k: np.ndarray, n: np.ndarray, z: float = 1.645) -> np.ndarray:
    """Vectorised one-sided Wilson lower bound (z = 1.645: 95 % one-sided)."""
    n = np.maximum(n.astype(float), 1e-9)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(np.maximum(p * (1 - p) / n + z * z / (4 * n * n), 0))
    return (c - h) / d


def cluster_boot(values_by_cluster: dict[str, list[tuple[int, float]]], stat, b: int = 2000,
                 seed: int = 20261005) -> tuple[Optional[float], Optional[float], float]:
    """Percentile CI and one-sided p (share of draws <= 0) of stat over cluster resamples.

    values_by_cluster = {cluster: [(in_rule 0/1, y), ...]}; stat(arr_in_rule, arr_y) -> float or nan.
    """
    keys = sorted(values_by_cluster)
    arrs = [np.array(values_by_cluster[k], dtype=float) for k in keys]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(b):
        pick = rng.integers(0, len(keys), len(keys))
        a = np.concatenate([arrs[i] for i in pick])
        v = stat(a[:, 0], a[:, 1])
        if v is not None and not math.isnan(v):
            out.append(v)
    if len(out) < b // 2:
        return (None, None, 1.0)
    o = np.sort(np.array(out))
    p = float((np.sum(o <= 0) + 1) / (len(o) + 1))
    return (float(o[int(0.025 * (len(o) - 1))]), float(o[int(0.975 * (len(o) - 1))]), p)


def holm(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * pvals[i]))
        adj[i] = run
    return adj


def bh(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    run = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        run = min(run, pvals[i] * m / rank)
        adj[i] = run
    return adj


def registre(stage: str, n_tests: int, what: str, extra: Optional[dict[str, Any]] = None, n: int = 0,
             donnees: str = "reelles", declare: bool = True, sortie: Optional[str] = None) -> None:
    """One chained registry line per batch of outcome-touching computations, in the format of the
    etude-gelee skill (code/registre.py, copied from the skill): n_comparaisons = rules or tests
    evaluated, donnees = reelles | synthetiques."""
    from registre import enregistrer
    enregistrer(STUDY, test="%s: %s" % (stage, what), declare=declare, n=int(n), agent="session principale",
                n_comparaisons=max(1, int(n_tests)), donnees=donnees, params=extra or {}, sortie=sortie)
