#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.py -- the primitives shared by the buyer-cost tables, T1 to T5.

Default source: data/floor_capture_public.jsonl.gz, published with the
repository. No network, no key, no absolute path. The unpublished raw corpus
(645 files, 171 MB) still works if $PUMP_PRIVATE_ROOT is set, and both reading
paths give the same tables (code/README.md, "Reproducibility"): the published
corpus is simply rounded, to 6 significant figures on `sol` and 8 on
`tokens` / `price`.

Unit conventions, and they have been verified:
  - captures: `price` and `sol / tokens`  = SOL per token.
  - captures: `detect_mc`                 = USD.
  - GeckoTerminal OHLCV: price            = USD per token.
Any ratio mixing the two without converting is wrong by a factor equal to the
price of SOL, about 73 USD over this window. See sol_usd().
"""
import bisect
import glob
import gzip
import json
import os
import statistics as st
from collections import defaultdict

import redact
import settings

ROOT = settings.ROOT
DATA = settings.DATA
DOCS = settings.DOCS

# Per-token feature socle, populations A / B / C, published under data/.
SOCLE = settings.data("dataset_socle.json")

# --- simulation parameters, identical to the reconciled canonical socle ------
MIN_SOL_PRICE = 0.3     # smallest swap that counts towards the robust price
DEPTH_MIN_SOL = 0.05    # smallest order that counts towards the book
POS_SOL = 0.5           # size of the simulated position
FEE_SIDE = 0.01         # fee per leg
SLIP_SIDE = 0.02        # adverse slippage per leg
FEE_IN = (1 + SLIP_SIDE) * (1 + FEE_SIDE)
FEE_OUT = (1 - SLIP_SIDE) * (1 - FEE_SIDE)
DRAG = 1 - FEE_OUT / FEE_IN          # = 5.8241 % over the round trip
MIN_USEFUL = 120        # shortest useful duration of a capture
CLUSTER_GAP = 1800      # 30 min: two launches further apart are two clusters


# --------------------------------------------------------------- captures ---
def _raw_captures():
    """Iterate the raw captures, with (n_source_files, n_empty_already_dropped).

    Two interchangeable sources:
      1. data/floor_capture_public.jsonl.gz            (default, published)
      2. $PUMP_PRIVATE_ROOT/state/floor_capture/*.json (raw corpus)

    The published corpus has already lost the 352 captures holding no swap at
    all. Their count is read back from data/MANIFEST.json so that the rejection
    tallies printed are the same whichever source was used.
    """
    priv = settings.private_root()
    if priv:
        capdir = os.path.join(priv, "state", "floor_capture")
        files = sorted(glob.glob(os.path.join(capdir, "*.json")))
        if not files:
            raise SystemExit("aucune capture dans %s" % capdir)
        def gen():
            for fp in files:
                try:
                    yield json.load(open(fp))
                except (OSError, ValueError):
                    yield None
        return gen(), len(files), 0

    path = settings.PUBLIC_CORPUS
    if not os.path.exists(path):
        raise SystemExit(
            "corpus absent : %s\n"
            "Il est publie avec le depot ; sinon le reconstruire avec\n"
            "  python3 code/make_public_data.py --private /chemin/pump_bundle_detector"
            % os.path.relpath(path, ROOT))
    n_src, n_empty = 0, 0
    mf = settings.data("MANIFEST.json")
    if os.path.exists(mf):
        m = json.load(open(mf))
        n_src = m.get("n_fichiers_source", 0)
        n_empty = m.get("n_captures_vides_ecartees", 0)

    def gen():
        with gzip.open(path, "rt") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
    return gen(), n_src, n_empty


def load_captures(verbose=False):
    """Load the usable captures.

    Filters, the union of what both socles reject (see merge.py X11): an empty
    capture; a swap span under 120 s; a last swap less than 120 s after
    `created`; no buy at all; no swap of 0.3 SOL or more.

    Returns (captures, rejections_by_reason, n_files).
    """
    stream, n_files, n_empty = _raw_captures()
    kept, rej = [], defaultdict(int)
    if n_empty:
        rej["capture_vide"] += n_empty
    for d in stream:
        if d is None:
            rej["json_illisible"] += 1
            continue
        raw = d.get("swaps") or []
        if not raw:
            rej["capture_vide"] += 1
            continue
        cl = []
        for s in raw:
            tok = s.get("tokens") or 0.0
            sol = s.get("sol") or 0.0
            ts = s.get("ts")
            if ts is None or tok <= 0 or sol <= 0:
                continue
            if s.get("side") not in ("buy", "sell"):
                continue
            cl.append({"ts": int(ts), "side": s["side"], "sol": float(sol),
                       "tokens": float(tok), "trader": s.get("trader"),
                       "p": float(sol) / float(tok)})
        if not cl:
            rej["aucun_swap_exploitable"] += 1
            continue
        cl.sort(key=lambda x: x["ts"])
        created = d.get("created") or cl[0]["ts"]
        if cl[-1]["ts"] - cl[0]["ts"] < MIN_USEFUL:
            rej["span_swaps_lt_2min"] += 1
            continue
        if cl[-1]["ts"] - created < MIN_USEFUL:
            rej["duree_depuis_created_lt_2min"] += 1
            continue
        if not any(x["side"] == "buy" for x in cl):
            rej["aucun_buy"] += 1
            continue
        if not any(x["sol"] >= MIN_SOL_PRICE for x in cl):
            rej["aucun_swap_ge_0.3sol"] += 1
            continue
        d["_sw"] = cl
        d["_created"] = created
        kept.append(d)
    kept.sort(key=lambda d: (d["_created"], d["mint"]))
    n_files = n_files or (len(kept) + sum(rej.values()))
    # Sort the keys: this rejection dict ends up printed in the published
    # tables, and its insertion order depended on which source was read.
    rej = dict(sorted(rej.items()))
    if verbose:
        print(f"fichiers={n_files}  exploitables={len(kept)}  rejets={rej}")
    return kept, rej, n_files


# The source name quoted in the tables' footnotes.
def source_label():
    return ("$PUMP_PRIVATE_ROOT/state/floor_capture/*.json"
            if settings.private_root() else "data/floor_capture_public.jsonl.gz")


def clusters(caps, gap=CLUSTER_GAP):
    """Number the captures into clusters, splitting on a gap of over 30 min
    between two `created` timestamps."""
    out, cid, prev = {}, 0, None
    for d in sorted(caps, key=lambda x: x["_created"]):
        if prev is not None and d["_created"] - prev > gap:
            cid += 1
        out[d["mint"]] = cid
        prev = d["_created"]
    return out


def robust_price(sw, t0, t1, min_sol=MIN_SOL_PRICE):
    """The robust price: median price of the swaps of at least min_sol over
    [t0, t1). Nothing is interpolated, None propagates."""
    p = [s["p"] for s in sw if t0 <= s["ts"] < t1 and s["sol"] >= min_sol]
    return st.median(p) if p else None


# --------------------------------------------------------------- SOL / USD --
_SOL = None


def sol_usd(ts=None):
    """The price of SOL in USD, hourly, from the Raydium SOL/USDC pool via
    GeckoTerminal.

    Reads data/sol_usd_hourly.json, which code/fetch_sol_usd.py produces.
    Called without an argument, returns (median, n, ts_min, ts_max).
    """
    global _SOL
    if _SOL is None:
        p = os.path.join(DATA, "sol_usd_hourly.json")
        if not os.path.exists(p):
            raise SystemExit("data/sol_usd_hourly.json absent : lancer code/fetch_sol_usd.py")
        j = json.load(open(p))
        _SOL = sorted((int(t), float(c)) for t, c in j["hourly_close"])
    if ts is None:
        v = [c for _, c in _SOL]
        return st.median(v), len(_SOL), _SOL[0][0], _SOL[-1][0]
    keys = [t for t, _ in _SOL]
    i = bisect.bisect_right(keys, ts) - 1
    i = max(0, min(i, len(_SOL) - 1))
    return _SOL[i][1]


# --------------------------------------------------------------- stats ------
def boot_ci_median_tokens(v, B=4000, seed=12345):
    """Percentile bootstrap 95 % interval of the median, resampling per TOKEN
    with random.Random.

    Two limits are accepted rather than hidden. Tokens of one cluster are
    treated as independent, so the interval is narrower than reality
    (METHODOLOGY 3.1, effective n around 5.5); and random.Random is not
    byte-identical across Python versions. The cross-version LCG engine is
    pumplib.bootstrap_median_ci, and the two are deliberately distinct: see the
    statlib.py header, merging them would change published numbers.

    Returns (lo, hi)."""
    import random
    if len(v) < 5:
        return (None, None)
    rnd = random.Random(seed)
    n = len(v)
    out = []
    for _ in range(B):
        out.append(st.median([v[rnd.randrange(n)] for _ in range(n)]))
    out.sort()
    return out[int(0.025 * B)], out[int(0.975 * B)]


def load_socle():
    return json.load(open(SOCLE))


def write_table(name, header, rows, notes=()):
    """Write a Markdown table to docs/tables/NAME.md, and return it."""
    d = os.path.join(DOCS, "tables")
    os.makedirs(d, exist_ok=True)
    w = [max(len(str(header[i])), *(len(str(r[i])) for r in rows)) if rows
         else len(str(header[i])) for i in range(len(header))]
    L = ["| " + " | ".join(str(header[i]).ljust(w[i]) for i in range(len(header))) + " |",
         "|" + "|".join("-" * (w[i] + 2) for i in range(len(header))) + "|"]
    for r in rows:
        L.append("| " + " | ".join(str(r[i]).ljust(w[i]) for i in range(len(header))) + " |")
    txt = "\n".join(L)
    if notes:
        txt += "\n\n" + "\n".join(notes)
    open(os.path.join(d, name + ".md"), "w").write(redact.scrub_text(txt) + "\n")
    return txt


def dump_json(obj, path, **kw):
    """The single point where a measurement is written as JSON.

    It goes through redact.scrub, so the pseudonymisation of the handful of
    identifiers carrying an abusive vanity prefix is applied AT WRITE TIME, not
    afterwards. A re-run from the raw network cache therefore cannot undo it.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    kw.setdefault("indent", 1)
    with open(path, "w") as f:
        json.dump(redact.scrub(obj), f, **kw)
    return path
