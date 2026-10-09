#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mine_40_discovery.py -- DISCOVERY: generate every rule mechanically, keep the ones that pass.

Reads the labels of the DISCOVERY block only (ap_lib.load_labels('discovery')). Every rule that
passes is written to registre/disc_rules_<target>.jsonl.gz; the number of rules evaluated goes to
the chained registry with the configuration. Atoms are outcome-free and saved for the later stages.
"""
from __future__ import annotations

import os
import sys
from collections import Counter

import numpy as np

import ap_data as D
import ap_lib as A
import ap_mine as M


def atoms_and_pairs(mx, elig, excl):
    ref = np.flatnonzero(elig & (mx["blocks"] == "DISC"))
    B, desc, ainfo = M.prepare_atoms(mx["X"], mx["names"], mx["meta"], ref, excl, D.no_missing_features())
    allowed, n_forb = M.allowed_pairs(mx["X"], desc, ref)
    ainfo["forbidden_copy_feature_pairs"] = n_forb
    ainfo["allowed_atom_pairs"] = int(np.triu(allowed, 1).sum())
    return ref, B, desc, allowed, ainfo


def main() -> None:
    if os.path.exists(A.SEL_FREEZE):
        sys.exit("the candidate list is frozen: DISCOVERY is not re-run")
    mx = D.load_matrix()
    lab = D.label_arrays("discovery", mx["mints"])
    excl = D.excluded_features()
    if (mx["blocks"][np.flatnonzero(lab["elig"])] != "DISC").any():
        raise RuntimeError("a non-DISCOVERY label reached the discovery stage")
    ref, B, desc, allowed, ainfo = atoms_and_pairs(mx, lab["elig"], excl)
    np.savez_compressed(os.path.join(A.DERIVED, "atoms_B.npz"), B=B)
    A.write_json(os.path.join(A.DERIVED, "atoms.json"), {"atoms": desc, "ref_rows": ref.tolist(),
                                                         "excluded_features": sorted(excl), "cfg": M.CFG, "info": ainfo})
    print("DISCOVERY eligible rows %d, atoms %d (features %d), %s" % (len(ref), len(desc), ainfo["n_features"], ainfo))
    summary = {"atoms": ainfo, "cfg": M.CFG}
    for tg in A.TARGETS:
        res = M.mine_disc(B, desc, lab["y"][tg], ref, mx["days"], mx["clusters"], allowed)
        ev = res["evaluated"]
        out = os.path.join(A.REGISTRE, "disc_rules_%s.jsonl.gz" % tg)
        A.write_jl(out, ({**r, "rule": list(r["rule"]), "text": M.rule_text(r["rule"], desc)} for r in res["rules"]))
        A.registre("discovery", sum(ev.values()), "rules evaluated on DISCOVERY for %s" % tg,
                   {"target": tg, **ev, "n_atoms": res["n_atoms"], "passed": len(res["rules"]),
                    "passed_by_depth": res["passed_by_depth"], "passed_before_spread": res["passed_before_spread"],
                    "base": res["base"], "base_eff": res["base_eff"], "cfg": M.CFG},
                   n=res["n"], sortie=os.path.relpath(out, A.STUDY))
        fam = Counter()
        for r in res["rules"]:
            for a in r["rule"]:
                fam[desc[a]["family"]] += 1
        summary[tg] = {"base": res["base"], "base_eff": res["base_eff"], "n": res["n"], "hits": int(round(res["base"] * res["n"])),
                       "evaluated": ev, "passed": len(res["rules"]), "passed_by_depth": res["passed_by_depth"],
                       "passed_before_spread": res["passed_before_spread"],
                       "atom_uses_by_family": dict(fam),
                       "rules_ge5_clusters": sum(1 for r in res["rules"] if r["clusters"] >= 5),
                       "rules_ge10_clusters": sum(1 for r in res["rules"] if r["clusters"] >= 10),
                       "rules_ge5_days": sum(1 for r in res["rules"] if r["days"] >= 5)}
        print("%s base %.3f (n %d): evaluated singles %d pairs %d triples %d -> passed %d by depth %s" % (
            tg, res["base"], res["n"], ev["singles"], ev["pairs"], ev["triples"], len(res["rules"]), res["passed_by_depth"]))
        for r in sorted(res["rules"], key=lambda r: -r["lb"])[:5]:
            print("    n %3d prec %.2f lift %.2f clusters %2d days %2d  %s" % (
                r["n"], r["prec"], r["lift"], r["clusters"], r["days"], M.rule_text(r["rule"], desc)))
    A.write_json(os.path.join(A.TABLES, "discovery_summary.json"), summary)


if __name__ == "__main__":
    main()
