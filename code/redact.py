#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redact.py -- stable pseudonymisation of a small set of on-chain identifiers.

WHY THIS EXISTS
---------------
Solana addresses and mints are public data, and this dossier publishes them
unmasked on purpose: masking them would make every claim unverifiable. There
is one exception. A vanity address is *chosen* by whoever generated it, and a
handful of identifiers in this corpus were generated to carry a racial slur in
their first characters. Reproducing those strings in a public repository would
republish the slur, so they -- and only they -- are replaced by a stable
neutral label.

THE RULE (mechanical, applied once, auditable)
----------------------------------------------
An identifier is redacted iff its first 8 characters contain a term from a
hard-slur word list. The rule is applied by build_redactions.py, which takes
the word list as an external file: **the list is never committed**, and this
repository therefore contains neither the offending addresses nor the words
used to find them.

What IS committed is code/redactions.json: a map from
sha256(identifier) -> label. That is enough to
  * apply the substitution to any file (hash each candidate, look it up), and
  * let any third party who already holds an address confirm what it became,
    by hashing it themselves,
without the repository containing a single one of the strings.

Labels are of the form  RDCT-<first 10 hex of sha256>. They contain a hyphen,
so they can never be mistaken for a base58 address, and they are stable across
files: grouping, graph and ubiquity computations are unaffected -- a
substitution that is injective on identifiers leaves every count invariant.

Redacted identifiers are a rounding error in the corpus (24 of ~91 600
identifiers, none of them in the operator clusters that the dossier analyses).
"""
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
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


def _load():
    if not os.path.exists(MAP_PATH):
        return {}
    with open(MAP_PATH) as f:
        return json.load(f).get("map", {})


MAP = _load()


def h(s):
    return hashlib.sha256(s.encode()).hexdigest()


def label_of(s):
    """Return 'RDCT-xxxxxxxxxx' for a canonically redacted identifier."""
    return "RDCT-" + h(s)[:10]


def apply(s):
    """Identifier -> published form. Non-redacted identifiers pass through."""
    if not isinstance(s, str):
        return s
    return MAP.get(h(s), s)


def is_redacted(s):
    return isinstance(s, str) and bool(LABEL_RE.match(s))


def scrub_text(text):
    """Substitute inside arbitrary text (Markdown, logs, JSON as a string)."""
    if not MAP:
        return text
    return B58_RE.sub(lambda m: MAP.get(h(m.group(0)), m.group(0)), text)


def scrub(obj):
    """Recursively substitute inside a decoded JSON object, keys included."""
    if not MAP:
        return obj
    if isinstance(obj, str):
        return MAP.get(h(obj), obj)
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {scrub(k): scrub(v) for k, v in obj.items()}
    return obj


def stats():
    return {"n_redacted_identifiers": len(MAP), "map": MAP_PATH}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        for a in sys.argv[1:]:
            print("%s -> %s" % (a[:6] + "...", apply(a)))
    else:
        print(json.dumps(stats(), indent=1))
