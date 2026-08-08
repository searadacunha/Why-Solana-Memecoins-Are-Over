#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redact.py -- stable pseudonymisation of a small set of on-chain identifiers.

WHY THIS EXISTS
---------------
Solana addresses and mints are public data, and this dossier publishes them
unmasked on purpose: masking them would make every claim unverifiable. There
are two exceptions, redacted by two different schemes for two different reasons.

1. SLUR-VANITY IDENTIFIERS (plain SHA-256).
   A vanity address is *chosen* by whoever generated it, and a handful of
   identifiers in this corpus were generated to carry a racial slur in their
   first characters. Reproducing those strings would republish the slur, so
   they are replaced by a stable neutral label. The map is committed as
   sha256(identifier) -> label, which lets anyone who already holds such an
   address confirm what it became by hashing it -- decency, not secrecy, so
   public confirmability is a feature and a plain hash is the right tool.

2. THE AUTHOR'S KYC'D EXCHANGE DEPOSIT ADDRESS (salted HMAC-SHA256).
   This one is redacted for privacy, and a plain sha256 map would defeat the
   purpose: an analyst holding candidate deposit addresses (shortlisted from
   the published trade fingerprints) could hash each and match it against the
   committed map -- an enumeration oracle. It is therefore keyed by
   HMAC-SHA256(salt, address) under an UNCOMMITTED salt (env REDACT_HMAC_SALT,
   or redact_salt.txt at the repo root -- both git-ignored). The label is
   HMAC-derived too, so it leaks nothing about sha256(address). Only someone
   holding BOTH the address AND the salt can confirm the label; the oracle is
   closed. See docs/EXPLOITATION.md and code/redactions.json.

THE RULE FOR THE SLUR SET (mechanical, applied once, auditable)
---------------------------------------------------------------
An identifier is redacted iff its first 8 characters contain a term from a
hard-slur word list. The rule is applied by build_redactions.py, which takes
the word list as an external file: **the list is never committed**, and this
repository therefore contains neither the offending addresses nor the words
used to find them.

WHAT IS COMMITTED is code/redactions.json:
  * "map"      : sha256(identifier) -> label       (the slur set)
  * "map_hmac" : HMAC-SHA256(salt, identifier) -> label   (the KYC address)
Neither contains a single one of the redacted strings.

Labels are of the form  RDCT-<10 hex>. They contain a hyphen, so they can never
be mistaken for a base58 address, and they are stable across files: a
substitution injective on identifiers leaves every count invariant.

Redacted identifiers are a rounding error in the corpus: 44 of 212 201 scanned
(43 slur-vanity + 1 KYC deposit address), none of them in the operator clusters
the dossier analyses.
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
    git-ignored). None when absent -- the KYC address then cannot be scrubbed
    or confirmed on this machine, but the slur set still is (it uses plain
    sha256), so a clone without the salt loses nothing it is allowed to have."""
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
