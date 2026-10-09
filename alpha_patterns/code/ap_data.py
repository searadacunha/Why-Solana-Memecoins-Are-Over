#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ap_data.py -- loaders of the feature matrix and of the stage-gated label arrays."""
from __future__ import annotations

import json
import os
from typing import Any

import numpy as np

import ap_lib as A


def load_matrix() -> dict[str, Any]:
    z = np.load(os.path.join(A.DERIVED, "X.npz"))
    c = json.load(open(os.path.join(A.DERIVED, "X_cols.json")))
    t = z["t"]
    return {"X": z["X"], "XA2": z["fA2"], "XA5": z["fA5"], "t": t, "names": c["names"], "meta": c["meta"],
            "mints": c["mints"], "blocks": np.array(c["blocks"]), "clusters": np.array(c["clusters"]),
            "days": (t // 86400).astype(int), "variant_columns": set(c["variant_columns"])}


def excluded_features() -> set[str]:
    p = os.path.join(A.DERIVED, "feature_exclusions.json")
    if not os.path.exists(p):
        raise RuntimeError("feature_exclusions.json is missing: run inv_00_inventory.py after the causality audit")
    return set(json.load(open(p))["excluded"])


def no_missing_features() -> set[str]:
    """Features whose 'is missing' atom is not generated (missingness is a snapshot artefact)."""
    return set(json.load(open(os.path.join(A.DERIVED, "feature_exclusions.json")))["no_missing_atom"])


def elig_all(mints: list[str]) -> np.ndarray:
    """Eligibility of every alert (fine regime, entry, observed 1 h window): structure, not outcome."""
    ok = {}
    for r in A.jl(os.path.join(A.DERIVED, "labels.jsonl.gz")):
        ok[r["mint"]] = bool(r.get("fine") and r.get("entry") and r.get("obs_3600"))
    return np.array([ok[m] for m in mints])


def label_arrays(stage: str, mints: list[str]) -> dict[str, Any]:
    """Arrays aligned on the matrix rows. Rows of blocks the stage may not read stay NaN / False."""
    lab = A.load_labels(stage)
    n = len(mints)
    elig = np.zeros(n, dtype=bool)
    y = {tg: np.full(n, np.nan) for tg in A.TARGETS}
    extra: dict[str, np.ndarray] = {}

    def col(name):
        if name not in extra:
            extra[name] = np.full(n, np.nan)
        return extra[name]

    for i, m in enumerate(mints):
        r = lab.get(m)
        # eligible = fine sampling regime (5 s reads), an entry at +5 s and an observed 1 h window
        if r is None or not r.get("fine") or not r.get("entry") or not r.get("obs_3600"):
            continue
        elig[i] = True
        for tg, k in zip(A.TARGETS, A.MULTS):
            y[tg][i] = r["conf_%gx_3600" % k]
        for k in A.MULTS:
            for h in A.HORIZONS:
                for kind in ("conf", "single"):
                    v = r.get("%s_%gx_%d" % (kind, k, h))
                    if v is not None:
                        col("%s_%gx_%d" % (kind, k, h))[i] = v
            if r.get("t_hit_%gx" % k) is not None:
                col("t_hit_%gx" % k)[i] = r["t_hit_%gx" % k]
                col("low_before_%gx" % k)[i] = r["low_before_%gx" % k]
        col("mfe_3600")[i] = r["mfe_3600"]
        col("mae_3600")[i] = r["mae_3600"]
        col("entry_mult")[i] = r["entry"]["mult"]
        for name, tr in r["trades"].items():
            if tr["status"] == "ok":
                for fld in ("net_100", "net_500", "net_1000", "net_500_k05", "net_500_k2", "gross", "dt"):
                    col("%s.%s" % (name, fld))[i] = tr[fld]
        l15 = r.get("L15")
        if l15 and l15["obs_3600"]:
            for k in A.MULTS:
                col("L15_conf_%gx" % k)[i] = l15["conf_%gx" % k]
            for name, tr in l15["trades"].items():
                if tr["status"] == "ok":
                    col("L15_%s.net_500" % name)[i] = tr["net_500"]
    return {"elig": elig, "y": y, "extra": extra}
