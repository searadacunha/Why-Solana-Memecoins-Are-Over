#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the analytic table once and freeze it (analysis_plan.md, "Data").

Runs the corrected feature builder over every alert of the first snapshot,
writes derived/analytic_table.jsonl.gz, and records its sha256, row counts,
on-chain coverage and the label counts per split (counts only, no rate) in
derived/TABLE_FREEZE.json. Refuses to run again once the freeze exists: the
table is not modified after screening starts.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import sys
import time
from collections import Counter

import ana_lib as L
import feat_30_build as FB


def main() -> None:
    if os.path.exists(L.FREEZE):
        sys.exit("the analytic table is frozen (%s); it is not rebuilt" % L.FREEZE)
    FB.main()                                  # writes derived/forensic_rows.jsonl.gz and the dictionary
    src = os.path.join(FB.DERIVED, "forensic_rows.jsonl.gz")
    shutil.copyfile(src, L.TABLE)
    with gzip.open(L.TABLE, "rt", encoding="utf8") as fh:
        rows = [json.loads(x) for x in fh]
    alerts = [r for r in FB.pde.load_journal() if r["genre"] == "alerte_lancement"]
    n_split = Counter(r["split"] for r in rows)
    n_all = Counter("train" if a["t"] < FB.T_VAL else "val" for a in alerts)
    obs = Counter(r["split"] for r in rows if r["y"].get(L.PRIMARY) is not None)
    doc = {"frozen_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
           "sha256": hashlib.sha256(open(L.TABLE, "rb").read()).hexdigest(),
           "rows": len(rows), "rows_by_split": dict(n_split), "alerts_by_split": dict(n_all),
           "onchain_coverage": len(rows) / len(alerts),
           "primary_label": L.PRIMARY, "primary_observed_by_split": dict(obs),
           "safe_features": len(L.SAFE), "cutoffs": FB.CUTS,
           "note": "counts only; no rate was computed before this freeze"}
    with open(L.FREEZE, "w", encoding="utf8") as fh:
        json.dump(doc, fh, indent=1)
    os.chmod(L.TABLE, 0o444)
    os.chmod(L.FREEZE, 0o444)
    print(json.dumps(doc, indent=1))


if __name__ == "__main__":
    main()
