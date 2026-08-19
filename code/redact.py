#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redact.py -- stable pseudonymisation of a small set of on-chain identifiers.

Addresses and mints are public data and this dossier publishes them unmasked:
masking them would make the claims unverifiable. One exception is still in
force, a second was retired.

1. Slur-vanity identifiers (plain SHA-256). A vanity address is chosen by
   whoever generated it, and a handful in this corpus carry a racial slur in
   their first characters. Reproducing them would republish the slur, so they
   get a stable neutral label. The map is committed as sha256(id) -> label, so
   anyone already holding such an address can confirm what it became by hashing
   it. A plain hash is deliberate: it has to stay checkable by a third party.

2. Retired: the author's KYC'd exchange deposit address (salted HMAC-SHA256).
   Until 2026-08 it was redacted under a second scheme, keyed by
   HMAC-SHA256(salt, address) with an UNCOMMITTED salt, so it could not be
   confirmed by hashing candidates against the committed map (a plain sha256
   map would be an enumeration oracle). The address is published since
   (README.md, "Author") and the `map_hmac` block was dropped from
   code/redactions.json; its "history" field records the change. The machinery
   stays: re-adding a `map_hmac` entry re-redacts on every write path.

The rule: an identifier is redacted iff its first 8 characters contain a term
from a hard-slur word list. build_redactions.py applies it and reads that list
from an external file which is never committed, so the repo holds neither the
offending addresses nor the words used to find them.

Committed is code/redactions.json, "map" = sha256(id) -> label. Hashes only,
not one of the redacted strings. (A "map_hmac" block held the KYC address until
2026-08; the loader still reads it when present.)

Labels look like RDCT-<10 hex>. The hyphen makes them impossible to mistake for
base58, and the substitution is injective, so every count stays invariant.

43 redacted out of 212 201 scanned, all slur-vanity, none in the operator
clusters the dossier analyses.
"""
from __future__ import annotations

import functools
import hashlib
import hmac
import json
import os
import re
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAP_PATH = os.path.join(HERE, "redactions.json")

# Base58 alphabet (no 0, O, I, l). The look-around is NOT cosmetic: a Solana
# *signature* is 87-88 base58 characters, so a bare {32,44} pattern matches a
# 44-character window INSIDE a signature. Two failure modes follow, and both
# were observed before this was fixed:
#   - build_redactions flags such a window as an "identifier" (a slur can occur
#     by chance inside an 88-character random string), and
#   - scrub_text then rewrites that window, silently corrupting the signature
#     and making the transaction unverifiable on any explorer.
# Anchoring both ends to a non-base58 boundary makes a match a whole token.
B58_RE = re.compile(
    r"(?<![1-9A-HJ-NP-Za-km-z])[1-9A-HJ-NP-Za-km-z]{32,44}(?![1-9A-HJ-NP-Za-km-z])")
LABEL_RE = re.compile(r"^RDCT-[0-9a-f]{10}$")


def _load() -> tuple[dict[str, str], dict[str, str]]:
    if not os.path.exists(MAP_PATH):
        return {}, {}
    with open(MAP_PATH) as f:
        d = json.load(f)
    return d.get("map", {}), d.get("map_hmac", {})


MAP, MAP_HMAC = _load()


def _load_salt() -> Optional[bytes]:
    """The HMAC salt, from $REDACT_HMAC_SALT or redact_salt.txt (both
    git-ignored). None when absent -- a map_hmac entry then cannot be scrubbed
    or confirmed on this machine, but the slur set still is (it uses plain
    sha256), so a clone without the salt loses nothing it is allowed to have.
    map_hmac has no entry since 2026-08 (see the module docstring), so this
    is currently a no-op either way."""
    raw = os.environ.get("REDACT_HMAC_SALT")
    if not raw:
        p = os.path.join(ROOT, "redact_salt.txt")
        if os.path.exists(p):
            raw = open(p).read().strip()
    if not raw:
        return None
    try:
        return bytes.fromhex(raw)
    except ValueError:
        return raw.encode()


_SALT = _load_salt()


def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def hm(s: str) -> Optional[str]:
    """HMAC-SHA256(salt, s), or None when no salt is available."""
    if _SALT is None:
        return None
    return hmac.new(_SALT, s.encode(), hashlib.sha256).hexdigest()


def label_of(s: str) -> str:
    """Label for a plain-sha256 (slur-set) identifier."""
    return "RDCT-" + h(s)[:10]


@functools.lru_cache(maxsize=None)
def _label_for(s: str) -> Optional[str]:
    """The published label for an identifier under either scheme, or None.

    Memoised: scrubbing the corpus runs this over millions of base58 tokens,
    the same wallet appearing thousands of times, so a per-identifier cache
    turns the sha256 (+ HMAC, when a salt is loaded) into a one-off cost per
    distinct string. MAP / MAP_HMAC / the salt are fixed at import, so the
    cache is always valid for the life of the process."""
    lab = MAP.get(h(s))
    if lab is not None:
        return lab
    if MAP_HMAC:
        hx = hm(s)
        if hx is not None:
            return MAP_HMAC.get(hx)
    return None


def apply(s: Any) -> Any:
    """Identifier -> published form. Non-redacted identifiers pass through."""
    if not isinstance(s, str):
        return s
    return _label_for(s) or s


def is_redacted(s: Any) -> bool:
    return isinstance(s, str) and bool(LABEL_RE.match(s))


def scrub_text(text: str) -> str:
    """Substitute inside arbitrary text (Markdown, logs, JSON as a string)."""
    if not MAP and not MAP_HMAC:
        return text
    return B58_RE.sub(lambda m: _label_for(m.group(0)) or m.group(0), text)


def scrub(obj: Any) -> Any:
    """Recursively substitute inside a decoded JSON object, keys included."""
    if not MAP and not MAP_HMAC:
        return obj
    if isinstance(obj, str):
        return _label_for(obj) or obj
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {scrub(k): scrub(v) for k, v in obj.items()}
    return obj


def stats() -> dict[str, Any]:
    return {"n_redacted_identifiers": len(MAP) + len(MAP_HMAC),
            "n_plain": len(MAP), "n_hmac": len(MAP_HMAC),
            "salt_present": _SALT is not None, "map": MAP_PATH}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for a in sys.argv[1:]:
            print("%s -> %s" % (a[:6] + "...", apply(a)))
    else:
        print(json.dumps(stats(), indent=1))
