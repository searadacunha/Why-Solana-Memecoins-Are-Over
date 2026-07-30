#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
settings.py -- single source of truth for paths and credentials.

Every other script in code/ resolves its inputs and outputs through this
module. There is exactly one hard-coded path in the whole package -- the
location of this file -- and everything else is derived from it. Nothing here
depends on the machine the code was written on.

    repo/
      code/     <- this file
      data/     <- published inputs (see data/MANIFEST.json)
      docs/     <- generated tables and reports

Three classes of input, deliberately kept apart:

  PUBLIC      data/ , shipped with the repo, no credentials, no network.
              Everything a reader needs to re-derive the headline numbers.

  NETWORK     Helius RPC (Solana). Needed only by the on-chain verification
              scripts (v0*, v1_*, v2_*, r1_*). Keys come from the environment
              or from an untracked .env at the repo root -- NEVER from source.

  PRIVATE     the raw collector state (`pump_bundle_detector/`), which is not
              published: it contains ~170 MB of unreduced captures. Scripts
              that can optionally re-derive data/ from it read the path from
              $PUMP_PRIVATE_ROOT and degrade with an explicit message when it
              is absent. No published measurement requires it.
"""
import os

CODE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(CODE)
DATA = os.path.join(ROOT, "data")
DOCS = os.path.join(ROOT, "docs")
TABLES = os.path.join(DOCS, "tables")
OUT = os.path.join(DOCS, "out")

# Disk caches for network calls. Not published (see .gitignore): they are a
# byte-for-byte mirror of public chain data and weigh several hundred MB.
CACHE = os.path.join(DATA, "cache")
CACHE_R1 = os.path.join(DATA, "cache_r1")

PUBLIC_CORPUS = os.path.join(DATA, "floor_capture_public.jsonl.gz")
SAMPLE_CORPUS = os.path.join(DATA, "sample", "floor_capture_sample.jsonl")

for _d in (DATA, DOCS, TABLES, OUT):
    os.makedirs(_d, exist_ok=True)


def data(*parts):
    return os.path.join(DATA, *parts)


def docs(*parts):
    return os.path.join(DOCS, *parts)


# --------------------------------------------------------------- private ----
def private_root(required=False):
    """Root of the unpublished collector state, or None.

    Set it only if you hold the raw corpus:
        export PUMP_PRIVATE_ROOT=/path/to/pump_bundle_detector
    """
    p = os.environ.get("PUMP_PRIVATE_ROOT")
    if p:
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            return p
        raise SystemExit("PUMP_PRIVATE_ROOT points to a missing directory: %s" % p)
    if required:
        raise SystemExit(
            "this script needs the raw (unpublished) corpus.\n"
            "  export PUMP_PRIVATE_ROOT=/path/to/pump_bundle_detector\n"
            "Every measurement published in docs/ runs without it, from data/."
        )
    return None


# ---------------------------------------------------------------- keys ------
_ENV_NAMES = ("HELIUS_API_KEYS", "HELIUS_API_KEY", "HELIUS_KEY")


def _from_dotenv():
    """Read <repo>/.env if present. The file is git-ignored; .env.example
    documents its format. A key is never written back to disk by any script."""
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() in _ENV_NAMES:
                out.extend(v.strip().strip('"').strip("'")
                           for v in value.split(","))
    return [k for k in out if k]


def helius_keys():
    """All available Helius keys, de-duplicated, order preserved.

    Several keys are supported on purpose: the deep-history walks saturate a
    single key's rate limit, and the clients in hlib/r1lib rotate round-robin
    and fail over on 429/5xx. One key is enough for every script here, it is
    only slower.
    """
    raw = []
    for name in _ENV_NAMES:
        v = os.environ.get(name)
        if v:
            raw.extend(x.strip() for x in v.split(","))
    raw.extend(_from_dotenv())
    seen, out = set(), []
    for k in raw:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def require_helius():
    ks = helius_keys()
    if not ks:
        raise SystemExit(
            "no Helius API key found.\n"
            "  export HELIUS_API_KEYS=key1[,key2,...]\n"
            "or copy .env.example to .env and fill it in (the file is git-ignored).\n"
            "Free tier is enough; see code/README.md for the per-script call budget."
        )
    return ks


def redact_key(text):
    """Strip any known key from a string before it is printed or logged."""
    for k in helius_keys():
        if k:
            text = text.replace(k, "<HELIUS_KEY>")
    return text
