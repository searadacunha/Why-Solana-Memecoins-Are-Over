#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pumplib.py -- the shared library of the measurement series. Stdlib only (json,
gzip, math, bisect, statistics): no external dependency, no network, no key.

Conventions every measurement shares:

  t0             = `created`, the token's creation timestamp (UNIX seconds).
  swap           = {ts, side, trader, sol, tokens, price, src, progs[, sig]}
  executed price = sol / tokens, what the buyer actually paid, router fees
                   included in `sol`. The pool price in `price` is used as a
                   cross-check only: the two agree to the third decimal (m2).
  MC in SOL      = price * supply. pump.fun supply is constant at 1e9.
  launch MC      = 27.96 SOL, a constant of the pump.fun bonding curve (its
                   initial virtual reserve). That is where a token starts,
                   before any buy, and it is verifiable outside this repository.

The three evidence levels the outputs carry:
  [MESURE]      recomputed by the script from data/.
  [INFERE]      derived from measurements, and flagged as derived.
  [NON ETABLI]  a hypothesis, never quoted as a fact.
"""

import datetime as _dt
import gzip
import json
import os
import random
import statistics


def utc(ts, fmt="%Y-%m-%d"):
    """UNIX timestamp to a UTC string, defined here so that every measurement
    shares one definition of what a day is."""
    return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).strftime(fmt)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(HERE, "..", "data"))

# pump.fun curve constant: the market cap a token launches at, in SOL.
LAUNCH_MC_SOL = 27.96
PUMP_SUPPLY = 1e9


# ------------------------------------------------------------------- loading
def load_captures(path=None):
    """Load the capture corpus. Accepts .jsonl.gz or .jsonl."""
    if path is None:
        path = os.path.join(DATA, "floor_capture_public.jsonl.gz")
    op = gzip.open if path.endswith(".gz") else open
    out = []
    with op(path, "rt") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    out.sort(key=lambda d: (d["created"], d["mint"]))
    return out


def load_json(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def clean_swaps(d):
    """The usable swaps, sorted. One filter everywhere: sol > 0, tokens > 0,
    side in {buy, sell}. Adds the executed price as `p`."""
    out = []
    for s in d.get("swaps") or []:
        tok = s.get("tokens") or 0.0
        sol = s.get("sol") or 0.0
        if s.get("ts") is None or tok <= 0 or sol <= 0:
            continue
        if s.get("side") not in ("buy", "sell"):
            continue
        out.append({"ts": int(s["ts"]), "side": s["side"], "sol": float(sol),
                    "tokens": float(tok), "p": float(sol) / float(tok),
                    "price": s.get("price"), "src": s.get("src"),
                    "progs": s.get("progs") or [], "trader": s.get("trader")})
    out.sort(key=lambda x: x["ts"])
    return out


MIN_SOL_PRICE = 0.3   # smallest swap that counts towards a price
BUCKET = 30           # granularity of the price grid, in seconds


def robust_series(sw, bucket=BUCKET, min_sol=MIN_SOL_PRICE, t0=None):
    """The robust price series: per bucket of `bucket` seconds, the median
    executed price of the swaps worth at least `min_sol`.

    Why not simply max(price): a dust swap of 0.002 SOL carries an implicit
    price dominated by unit rounding, and produces outliers several orders of
    magnitude out. Measured, the raw maximum gives a market cap of 8.9e8 SOL,
    which is physically impossible. Taking the median per bucket over swaps of
    at least 0.3 SOL removes the artefact without picking anything by hand.

    This is the same definition the round-trip engine (M5) uses, so the two
    measurements share one notion of price rather than two.

    Returns [(bucket_start_ts, price), ...], sorted."""
    big = [s for s in sw if s["sol"] >= min_sol]
    if not big:
        return []
    base = big[0]["ts"] if t0 is None else t0
    buckets = {}
    for s in big:
        k = (s["ts"] - base) // bucket
        buckets.setdefault(k, []).append(s["p"])
    return [(base + k * bucket, statistics.median(v))
            for k, v in sorted(buckets.items())]


def clusters(caps, gap_s=1800):
    """Assign a temporal cluster id: two tokens created less than `gap_s`
    apart belong to the same cluster.

    This is the resampling unit. Tokens of one cluster share a market regime,
    so counting them as independent overstates the power of any test built
    on them."""
    cid, prev, out = 0, None, {}
    for d in sorted(caps, key=lambda x: x["created"]):
        c = d["created"]
        if prev is None or (c - prev) > gap_s:
            cid += 1
        prev = c
        out[d["mint"]] = cid
    return out


# ------------------------------------------------------------------ stats
# median / quantile / wilson are defined once in statlib.py and re-exported here
# so the m-series can keep calling P.median / P.wilson unchanged.
from statlib import median, quantile, wilson  # noqa: E402,F401


def bootstrap_median_ci(xs, n_boot=2000, seed=12345, alpha=0.05):
    """Bootstrap confidence interval of the median.

    Draw observations independently with replacement using a local seeded
    generator. Repeated runs are deterministic for a fixed seed and interpreter,
    without reading or changing the global random state. The former LCG's
    low bits forced balanced index classes for even sample sizes and could
    collapse the interval entirely; indexing its raw output modulo n was not
    a valid bootstrap.

    common.boot_ci_median_tokens uses different defaults, minimum sample size
    and percentile indices. Keep those procedures distinct."""
    xs = [x for x in xs if x is not None]
    if len(xs) < 3:
        return (None, None)
    n = len(xs)
    rng = random.Random(seed)
    meds = []
    for _ in range(n_boot):
        s = [xs[rng.randrange(n)] for _ in range(n)]
        s.sort()
        meds.append(s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2]))
    meds.sort()
    lo = meds[int(alpha / 2 * (n_boot - 1))]
    hi = meds[int((1 - alpha / 2) * (n_boot - 1))]
    return (lo, hi)


def cluster_bootstrap_mean_ci(values_by_cluster, n_boot=2000, seed=999, alpha=0.05):
    """Confidence interval obtained by resampling the clusters, not the
    tokens. Tokens of one cluster share a market regime, and treating them as
    independent would overstate the precision.

    The statistic resampled is the mean of the cluster means, the same one
    reported as the point estimate beside it. Draw len(keys) clusters
    independently with replacement using a local seeded generator, then give
    each drawn cluster mean equal weight. Averaging the pooled tokens instead
    would target a different, cluster-size-weighted statistic."""
    keys = sorted(values_by_cluster)
    if len(keys) < 3:
        return (None, None)
    cmeans = {k: sum(v) / len(v) for k, v in values_by_cluster.items() if v}
    keys = [k for k in keys if k in cmeans]
    rng = random.Random(seed)
    out = []
    for _ in range(n_boot):
        acc = [cmeans[keys[rng.randrange(len(keys))]] for _ in range(len(keys))]
        out.append(sum(acc) / len(acc))
    out.sort()
    return (out[int(alpha / 2 * (len(out) - 1))],
            out[int((1 - alpha / 2) * (len(out) - 1))])


# ------------------------------------------------------------------ printing
def head(title, level=None):
    bar = "=" * 78
    print(bar)
    print(title + ("   [%s]" % level if level else ""))
    print(bar)


def kv(label, value, unit="", n=None, note=""):
    s = "  %-52s %s%s" % (label, value, unit)
    if n is not None:
        s += "   (n=%s)" % n
    if note:
        s += "   %s" % note
    print(s)


def emit(obj, path):
    """Write the machine-readable result beside the printed text."""
    import redact
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(redact.scrub(obj), f, indent=1, sort_keys=True)
    print("\n  -> %s" % os.path.relpath(path, os.path.dirname(HERE)))
