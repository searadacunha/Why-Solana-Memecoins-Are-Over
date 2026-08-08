#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sanitize_data.py -- apply code/redactions.json to everything that gets
published, and refresh the checksums in data/MANIFEST.json.

Idempotent: running it twice changes nothing (the second pass finds no
identifier left to substitute). `--check` performs the scan without writing
and exits non-zero if anything remains -- that is the form used by
check_no_secrets.py and by any pre-publication hook.

Scope: data/ (published files only), docs/ and code/. The network caches
data/cache/ and data/cache_r1/ are NOT touched: they are byte-for-byte mirrors
of chain data, they weigh ~470 MB and they are git-ignored.

Usage:
    python3 code/sanitize_data.py [--check]
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import redact  # noqa: E402
import settings  # noqa: E402

SKIP_DIRS = {"cache", "cache_r1", "transition", "__pycache__", ".git"}
TEXT_EXT = {".json", ".jsonl", ".md", ".py", ".txt", ".log", ".csv"}


def iter_files():
    for base in (settings.DATA, settings.DOCS, settings.CODE):
        for root, dirs, names in os.walk(base):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for n in names:
                if n == "redactions.json":
                    continue
                ext = os.path.splitext(n)[1]
                if ext in TEXT_EXT or n.endswith(".jsonl.gz"):
                    yield os.path.join(root, n)


def process(path, write):
    """Returns the number of substitutions that were (or would be) applied."""
    gz = path.endswith(".gz")
    op = gzip.open if gz else open
    try:
        with op(path, "rt", encoding="utf-8", errors="strict") as f:
            src = f.read()
    except (UnicodeDecodeError, OSError):
        return 0
    dst = redact.scrub_text(src)
    if dst == src:
        return 0
    n = sum(1 for k in redact.MAP.values() if k in dst) or 1
    if write:
        tmp = path + ".tmp"
        if gz:
            with gzip.open(tmp, "wt", compresslevel=9, encoding="utf-8") as f:
                f.write(dst)
        else:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(dst)
        os.replace(tmp, path)
    return n


GLUED_RE = re.compile(r"[1-9A-HJ-NP-Za-km-z]RDCT-[0-9a-f]{10}"
                      r"|RDCT-[0-9a-f]{10}[1-9A-HJ-NP-Za-km-z]")


def glued(path):
    """A label welded to base58 characters means a substitution happened INSIDE
    a longer token -- typically an 87/88-character transaction signature that a
    non-anchored pattern chopped into a 44-character window. The signature is
    then silently unverifiable on any explorer. This invariant is checked on
    every run because the failure is invisible otherwise."""
    op = gzip.open if path.endswith(".gz") else open
    try:
        with op(path, "rt", encoding="utf-8", errors="ignore") as f:
            return GLUED_RE.search(f.read()) is not None
    except OSError:
        return False


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def refresh_manifest():
    p = os.path.join(settings.DATA, "MANIFEST.json")
    if not os.path.exists(p):
        return
    m = json.load(open(p))
    for name, rec in m.get("fichiers", {}).items():
        fp = os.path.join(settings.DATA, name)
        if os.path.exists(fp):
            rec["sha256"] = sha256(fp)
            rec["bytes"] = os.path.getsize(fp)
    tr = m.setdefault("transformations", [])
    note = ("aucune anonymisation d'adresse SAUF les identifiants a prefixe "
            "vanity injurieux, remplaces par une etiquette stable RDCT-* "
            "(voir code/redact.py)")
    tr = [t for t in tr if not t.startswith("aucune anonymisation")
          and not t.startswith("identifiants a prefixe")]
    tr.append(note)
    m["transformations"] = tr
    m["n_identifiants_redactes"] = (len(redact.MAP) + len(redact.MAP_HMAC))
    with open(p, "w") as f:
        json.dump(m, f, indent=1, sort_keys=True)
    print("MANIFEST.json refreshed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report only; exit 1 if a redacted identifier is still present")
    a = ap.parse_args()
    if not redact.MAP:
        sys.exit("code/redactions.json is missing or empty -- run build_redactions.py")

    total, touched, broken = 0, [], []
    for path in sorted(iter_files()):
        n = process(path, write=not a.check)
        if n:
            total += n
            touched.append(os.path.relpath(path, settings.ROOT))
        if glued(path):
            broken.append(os.path.relpath(path, settings.ROOT))

    if broken:
        print("FAIL: label welded inside a longer base58 token (corrupted "
              "signature) in %d file(s):" % len(broken))
        for b in broken:
            print("   ", b)
        sys.exit(2)

    if a.check:
        if touched:
            print("FAIL: %d file(s) still contain a redacted identifier:" % len(touched))
            for t in touched:
                print("   ", t)
            sys.exit(1)
        print("OK: no redacted identifier left in data/, docs/ or code/ "
              "(%d in the map)" % (len(redact.MAP) + len(redact.MAP_HMAC)))
        return

    for t in touched:
        print("  rewritten:", t)
    print("%d file(s) rewritten, %d identifiers in the map" % (len(touched), (len(redact.MAP) + len(redact.MAP_HMAC))))
    if touched:
        refresh_manifest()


if __name__ == "__main__":
    main()
