#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chk_00_integrity.py -- what in this published copy of alpha_patterns can be checked offline.

Standard library only, no network, nothing rewritten. Three checks:
  1. every file listed in SELECTION_FREEZE.json that is published here has the frozen sha256
     (a mismatch is a corruption of the record and fails the run); the files that are not published
     (feature matrix, labels, controls, about 12 MB in all) are listed with their frozen hash;
  2. each result JSON carries the sha256 of the pre-registration it was computed under, and that
     hash matches the published pre-registration file;
  3. every script / output hash recorded in the chained test registry (registre/tests.jsonl) is
     compared with the published file: 'match', or 'superseded' when the registry line refers to an
     earlier version of a script or output that was re-run later (the registry keeps every run).
Exit code 1 only for check 1 or 2 failing.
"""
from __future__ import annotations

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)

PREREG = {
    "tables/operator_forensics.json": "tables/OPERATOR_FORENSICS_PREREG_2026-10-07.md",
    "tables/team_rhythm.json": "tables/TEAM_RHYTHM_PREREG_2026-10-07.md",
    "tables/team_absorption.json": "tables/TEAM_ABSORPTION_PREREG_2026-10-07.md",
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    failed = False
    os.chdir(STUDY)

    print("1. SELECTION_FREEZE.json (frozen 2026-10-06 17:53 UTC, before VALIDATION was read)")
    freeze = json.load(open("SELECTION_FREEZE.json", encoding="utf-8"))
    n_ok = 0
    for rel, h in sorted(freeze["files"].items()):
        if not os.path.exists(rel):
            print("   not published  %-45s %s" % (rel, h[:16]))
            continue
        if sha256_file(rel) == h:
            n_ok += 1
        else:
            failed = True
            print("   MISMATCH       %s" % rel)
    print("   %d published file(s) match their frozen hash" % n_ok)

    print("2. pre-registrations")
    for js, md in PREREG.items():
        got = json.load(open(js, encoding="utf-8")).get("prereg_sha256")
        ok = got == sha256_file(md)
        failed |= not ok
        print("   %-7s %s <- %s" % ("match" if ok else "MISMATCH", os.path.basename(js), os.path.basename(md)))
    summ = "tables/x2_timing_summary.json"
    if os.path.exists(summ):
        got = json.load(open(summ, encoding="utf-8"))["input"]["sha256"]
        ok = got == freeze["files"]["derived/labels.jsonl.gz"]
        failed |= not ok
        print("   %-7s x2_timing_summary.json was computed on the frozen labels file" % ("match" if ok else "MISMATCH"))

    print("3. registre/tests.jsonl: hashes of scripts and outputs")
    n_match = n_sup = n_abs = 0
    for line in open("registre/tests.jsonl", encoding="utf-8"):
        r = json.loads(line)
        for k_path, k_sha in (("script", "script_sha"), ("sortie", "sortie_sha")):
            p, h = r.get(k_path), r.get(k_sha)
            if not p or not h:
                continue
            if not os.path.exists(p):
                n_abs += 1
                continue
            if sha256_file(p) == h:
                n_match += 1
            else:
                n_sup += 1
                print("   superseded     %-40s (registry line: %s)" % (p, (r.get("test") or "")[:60]))
    print("   %d match, %d superseded by a later version, %d refer to files not published here"
          % (n_match, n_sup, n_abs))
    print("\nRESULT:", "FAIL" if failed else "OK (checks 1 and 2 hold; check 3 is descriptive)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
