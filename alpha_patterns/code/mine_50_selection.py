#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mine_50_selection.py -- SELECTION: mechanical choice of the candidates, then the freeze.

Reads DISCOVERY and SELECTION labels only. Re-runs the deterministic DISCOVERY mining with the
same code and configuration (its counts are registered again, from this run), ranks the passing
rules on the SELECTION block, de-duplicates, keeps K per target plus one gradient-boosted composite
per target, and writes the frozen list with every candidate's firing vector (features only for the
later blocks). SELECTION_FREEZE.json records the sha256 of the list, the data, the control report,
the inventory and the code that reads the hold-out blocks and assigns the verdicts. After it exists
this script refuses to run again.
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np

import ap_data as D
import ap_lib as A
import ap_mine as M
from mine_40_discovery import atoms_and_pairs

FROZEN_FILES = ["PLAN.md", "derived/candidates.json", "derived/candidates_fire.npz", "derived/atoms.json",
                "derived/labels.jsonl.gz", "derived/X.npz", "derived/X_cols.json", "derived/feature_exclusions.json",
                "tables/FEATURE_INVENTORY.json", "tables/discovery_summary.json", "controles/ctl_00_controls.json",
                "code/ap_lib.py", "code/ap_mine.py", "code/ap_data.py", "code/registre.py",
                "code/val_60_validation.py", "code/oos_70_oos.py", "code/rob_80_robustness.py",
                "code/rep_90_report.py", "code/desc_45_families.py"]


def main() -> None:
    if os.path.exists(A.SEL_FREEZE):
        sys.exit("SELECTION_FREEZE.json already exists: the candidate list is frozen")
    missing = [f for f in FROZEN_FILES if not os.path.exists(os.path.join(A.STUDY, f))
               and f not in ("derived/candidates.json", "derived/candidates_fire.npz", "derived/atoms.json")]
    if missing:
        sys.exit("cannot freeze, missing files: %s (nothing was read)" % missing)
    mx = D.load_matrix()
    lab = D.label_arrays("selection", mx["mints"])
    if set(mx["blocks"][np.flatnonzero(lab["elig"])]) - {"DISC", "SEL"}:
        raise RuntimeError("a hold-out label reached the selection stage")
    excl = D.excluded_features()
    ref, B, desc, allowed, ainfo = atoms_and_pairs(mx, lab["elig"], excl)
    keep = {}
    cands, info = M.build_candidates(mx["X"], mx["names"], excl, B, desc, allowed, lab["y"], lab["elig"], mx["blocks"],
                                     mx["days"], mx["clusters"], with_composite=True, keep_disc=keep)
    A.write_json(os.path.join(A.DERIVED, "atoms.json"), {"atoms": desc, "ref_rows": ref.tolist(),
                                                         "excluded_features": sorted(excl), "cfg": M.CFG, "info": ainfo})
    fires = {c["id"]: c["fire"] for c in cands}
    out = []
    for c in cands:
        d = {k: v for k, v in c.items() if k != "fire"}
        if c["rule"] is not None:
            d["atoms"] = [desc[a] for a in c["rule"]]
        out.append(d)
    A.write_json(os.path.join(A.DERIVED, "candidates.json"), {"cfg": M.CFG, "atoms_info": ainfo, "info": info, "candidates": out})
    np.savez_compressed(os.path.join(A.DERIVED, "candidates_fire.npz"), **fires)
    for tg in info:
        ev = info[tg]["evaluated"]
        A.registre("selection", sum(ev.values()), "DISCOVERY re-mined and scored on SELECTION for %s" % tg,
                   {k: v for k, v in info[tg].items()}, n=info[tg]["disc_n"] + info[tg]["sel_n"],
                   sortie="derived/candidates.json")
        print(tg, {k: v for k, v in info[tg].items() if k != "evaluated"})
    for c in out:
        print("%-8s d%d  DISC %3d %.2f (x%.2f) | SEL %3d %.2f (x%.2f)  %s" % (
            c["id"], c["depth"], c["disc"]["n"], c["disc"]["prec"] or 0, c["disc"].get("lift") or 0,
            c["sel"]["n"], c["sel"]["prec"], c["sel"]["lift"], c["text"]))
    A.write_json(A.SEL_FREEZE, {"frozen_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                                "n_candidates": len(out), "cfg": M.CFG,
                                "files": {f: A.sha256_file(os.path.join(A.STUDY, f)) for f in FROZEN_FILES}})
    print("frozen: %d candidates" % len(out))


if __name__ == "__main__":
    main()
