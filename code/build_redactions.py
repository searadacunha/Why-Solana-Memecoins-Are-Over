#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_redactions.py -- (re)build code/redactions.json.

Scans every identifier of the published corpus, flags those whose FIRST 8
characters contain a term of an external word list, and writes a map
    sha256(identifier) -> RDCT-<10 hex>
Neither the identifiers nor the word list are written to the output: the map
contains hashes only. See redact.py for the rationale.

The word list is intentionally NOT part of this repository. Supply your own:
    python3 code/build_redactions.py --wordlist /path/to/slurs.txt
    (one lowercase term per line, '#' comments allowed)

Why the first 8 characters only: a slur appearing in the middle of a base58
string is a coincidence -- with ~91 600 identifiers you expect a few by pure
chance -- whereas a slur in the leading characters is the signature of a
vanity grind, i.e. it was chosen. Anchoring the rule to the prefix keeps the
redaction set small (24 identifiers) and defensible.

Usage:
    python3 code/build_redactions.py --wordlist FILE [--head 8] [--dry-run]
"""
import argparse
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settings  # noqa: E402
from redact import label_of  # noqa: E402


def corpus_identifiers(path):
    """Every mint and every trader of the published capture corpus."""
    seen = set()
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("mint"):
                seen.add(d["mint"])
            for w in d.get("swaps") or []:
                if w.get("trader"):
                    seen.add(w["trader"])
    return seen


def json_identifiers(path):
    """Every base58-looking string of a derived JSON file."""
    from redact import B58_RE
    with open(path) as f:
        return set(B58_RE.findall(f.read()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wordlist", required=True,
                    help="external file, one lowercase term per line (not committed)")
    ap.add_argument("--head", type=int, default=8,
                    help="how many leading characters the rule looks at (default 8)")
    ap.add_argument("--scan", nargs="*", default=[],
                    help="extra files/directories to scan for identifiers. Point "
                         "this at the ORIGINAL sources (raw captures, network "
                         "cache): once data/ has been sanitised, the redacted "
                         "identifiers are gone from it and cannot be re-derived.")
    ap.add_argument("--replace", action="store_true",
                    help="rebuild the map from scratch. Default is to MERGE: a "
                         "label, once published, must keep its meaning, so "
                         "entries are only ever added.")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    words = []
    with open(a.wordlist) as f:
        for line in f:
            line = line.strip().lower()
            if line and not line.startswith("#"):
                words.append(line)
    if not words:
        sys.exit("empty word list")

    ids = corpus_identifiers(settings.PUBLIC_CORPUS)
    for name in sorted(os.listdir(settings.DATA)):
        if name.endswith(".json") and name != "MANIFEST.json":
            ids |= json_identifiers(os.path.join(settings.DATA, name))
    for target in a.scan:
        target = os.path.expanduser(target)
        if os.path.isdir(target):
            for root, _dirs, names in os.walk(target):
                for n in names:
                    if n.endswith(".json"):
                        ids |= json_identifiers(os.path.join(root, n))
        elif target.endswith(".jsonl") or target.endswith(".jsonl.gz"):
            ids |= corpus_identifiers(target)
        elif os.path.isfile(target):
            ids |= json_identifiers(target)

    flagged = sorted(s for s in ids
                     if any(w in s[:a.head].lower() for w in words))

    new_map = {hashlib.sha256(s.encode()).hexdigest(): label_of(s) for s in flagged}
    if not a.replace:
        # A published label must never change meaning: entries are only added.
        from redact import MAP as OLD
        merged = dict(OLD)
        merged.update(new_map)
        new_map = merged

    out = {
        "rule": ("identifier redacted iff its first %d characters contain a term "
                 "of an external hard-slur word list; see code/redact.py" % a.head),
        "label_format": "RDCT-<first 10 hex chars of sha256(identifier)>",
        "n_scanned": len(ids),
        "n_redacted": len(new_map),
        "map": new_map,
    }
    print("scanned %d identifiers, %d redacted (%.4f %%)"
          % (len(ids), len(flagged), 100.0 * len(flagged) / max(1, len(ids))))
    if a.dry_run:
        return
    dst = os.path.join(settings.CODE, "redactions.json")
    with open(dst, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("-> %s (hashes only, no identifier and no word is stored)" % dst)


if __name__ == "__main__":
    main()
