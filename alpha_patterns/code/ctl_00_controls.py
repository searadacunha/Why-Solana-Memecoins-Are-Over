#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ctl_00_controls.py -- what the whole chain can and cannot see, on synthetic outcomes.

Real features, real blocks, real clusters, real days, real eligibility; synthetic outcomes only
(no real label is read). Three nested targets with the DISCOVERY base rates of Y2 / Y3 / Y5.
Worlds:
  NULL        cluster-by-block random effect (logit sd 1) + noise: nothing persists across blocks.
  NULL_day04  same plus a calendar-day random effect (logit sd 0.4); NULL_day08: sd 0.8.
  NULL_hist   iid + day effect sd 0.8, and the h1_* history features REBUILT from the synthetic
              outcomes (feat_20_history.build), so the outcome -> history path is exercised.
  PLANTED_xB  NULL plus one planted rule (random allowed pair of real atoms, support band given)
              whose precision is B x the base rate of each target. B = 1.83 / 2.9 are the break-even
              lifts of Y2 / Y3; 2.2 and 3.0 are round values; support 8-15 %, or 5-8 % (_s5).
Every run goes through the full chain: DISCOVERY -> SELECTION -> VALIDATION -> OOS -> tier.
Reported per world: OOS survivors per run (false under NULL; in planted worlds split by the share
of their fires inside the planted set), INTERESTING tiers per run, and the planted rule's fate.
The configuration and base rates are those the WORKERS used (returned by them, checked equal).

Usage: python3 ctl_00_controls.py [n_null_seeds] [n_planted_seeds] [n_workers]
Environment overrides (design runs only; recorded in the output): AP_RANK, AP_CAP, AP_NMIN_DISC,
AP_NMIN_SEL, AP_TRIPLES, AP_BOOT, AP_TAG (output name), AP_SCENARIOS (comma list).
"""
from __future__ import annotations

import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

import ap_data as D
import ap_lib as A
import ap_mine as M
import feat_20_history as F20

BOOT_CTL = 20000
SCENARIOS = {
    "NULL": dict(sd_cluster=1.0, sd_day=0.0, boost=None),
    "NULL_day04": dict(sd_cluster=1.0, sd_day=0.4, boost=None),
    "NULL_day08": dict(sd_cluster=1.0, sd_day=0.8, boost=None),
    "NULL_hist": dict(sd_cluster=0.0, sd_day=0.8, boost=None, rebuild_history=True),
    "PLANTED_x1.6": dict(sd_cluster=1.0, sd_day=0.0, boost=1.6, support=(0.08, 0.15)),
    "PLANTED_x1.83": dict(sd_cluster=1.0, sd_day=0.0, boost=1.83, support=(0.08, 0.15)),
    "PLANTED_x2.2": dict(sd_cluster=1.0, sd_day=0.0, boost=2.2, support=(0.08, 0.15)),
    "PLANTED_x2.9": dict(sd_cluster=1.0, sd_day=0.0, boost=2.9, support=(0.08, 0.15)),
    "PLANTED_x3.0": dict(sd_cluster=1.0, sd_day=0.0, boost=3.0, support=(0.08, 0.15)),
    "PLANTED_x2.2_s5": dict(sd_cluster=1.0, sd_day=0.0, boost=2.2, support=(0.05, 0.08)),
    "PLANTED_x3.0_s5": dict(sd_cluster=1.0, sd_day=0.0, boost=3.0, support=(0.05, 0.08)),
}
_G: dict = {}


def init():
    for env, key, cast in (("AP_RANK", "RANK", str), ("AP_CAP", "CAP", float), ("AP_NMIN_DISC", "N_MIN_DISC", int),
                           ("AP_NMIN_SEL", "N_MIN_SEL", int), ("AP_TRIPLES", "TRIPLE_SEEDS", int), ("AP_BOOT", "BOOT", int)):
        if os.environ.get(env):
            M.CFG[key] = cast(os.environ[env])
    if "AP_BOOT" not in os.environ:
        M.CFG["BOOT"] = BOOT_CTL
    mx = D.load_matrix()
    excl = D.excluded_features()          # raises if missing: a control must use the real exclusions
    nomiss = D.no_missing_features()
    elig = D.elig_all(mx["mints"])
    ref = np.flatnonzero(elig & (mx["blocks"] == "DISC"))
    B, desc, ainfo = M.prepare_atoms(mx["X"], mx["names"], mx["meta"], ref, excl, nomiss)
    allowed, n_forb = M.allowed_pairs(mx["X"], desc, ref)
    p = os.path.join(A.TABLES, "discovery_summary.json")
    ds = json.load(open(p))
    bases = [ds[tg]["base"] for tg in A.TARGETS]
    base_rows = A.load_base()
    keys, _ = F20.load_keys(base_rows)
    h1_cols = [j for j, nme in enumerate(mx["names"]) if mx["meta"][nme]["source"] == "h1"]
    _G.update(mx=mx, excl=excl, nomiss=nomiss, elig=elig, ref=ref, B=B, desc=desc, allowed=allowed, bases=bases,
              bases_source=p, atoms_info=ainfo, n_forbidden_pairs=n_forb, base_rows=base_rows, keys=keys,
              h1_cols=h1_cols)


def sigmoid(z):
    return 1 / (1 + np.exp(-z))


def world(rng, spec):
    """Synthetic probabilities P[tg] and outcomes Y[tg] (NaN outside eligible rows), planted rule."""
    mx, elig, B, desc = _G["mx"], _G["elig"], _G["B"], _G["desc"]
    n = len(elig)
    keys = np.char.add(np.char.add(mx["clusters"].astype(str), "|"), mx["blocks"].astype(str))
    inv = np.unique(keys, return_inverse=True)[1]
    u = rng.normal(0, spec["sd_cluster"], inv.max() + 1)[inv] if spec["sd_cluster"] > 0 else np.zeros(n)
    if spec["sd_day"] > 0:
        dinv = np.unique(mx["days"], return_inverse=True)[1]
        u = u + rng.normal(0, spec["sd_day"], dinv.max() + 1)[dinv]
    z = rng.random(n)
    planted = None
    if spec["boost"] is not None:
        lo, hi = spec["support"]
        allowed = _G["allowed"]
        for _ in range(200000):
            a, b = rng.integers(0, len(desc), 2)
            if a == b or not allowed[a, b]:
                continue
            f = B[a] & B[b]
            sh = [f[elig & (mx["blocks"] == blk)].mean() for blk in A.BLOCKS]
            if lo <= f[elig].mean() <= hi and min(sh) >= 0.6 * lo:
                planted = {"rule": (int(min(a, b)), int(max(a, b))), "fire": f}
                break
        if planted is None:
            raise RuntimeError("no plantable pair found")
    P, Y = {}, {}
    for tg, base in zip(A.TARGETS, _G["bases"]):
        lo_, hi_ = -15.0, 15.0
        for _ in range(60):
            mid = (lo_ + hi_) / 2
            if sigmoid(mid + u[elig]).mean() < base:
                lo_ = mid
            else:
                hi_ = mid
        p = sigmoid((lo_ + hi_) / 2 + u)
        if planted is not None:
            p = np.where(planted["fire"], min(0.95, spec["boost"] * base), p)
        y = (z < p).astype(float)
        y[~elig] = np.nan
        P[tg], Y[tg] = p, y
    return P, Y, planted


def synthetic_outcomes(rng, Y):
    """Outcome records for feat_20_history.build from synthetic labels (MFE and net drawn from
    rough DISCOVERY shapes: they only need to be consistent with the labels)."""
    out = []
    elig = _G["elig"]
    for i in range(len(elig)):
        if not elig[i]:
            out.append(None)
            continue
        y = {k: int(Y[tg][i]) for k, tg in zip((2, 3, 5), A.TARGETS)}
        if y[5]:
            mfe = rng.uniform(5, 8)
        elif y[3]:
            mfe = rng.uniform(3, 5)
        elif y[2]:
            mfe = rng.uniform(2, 3)
        else:
            mfe = rng.uniform(0.3, 1.9)
        net = rng.normal(0.9, 0.3) if y[2] else rng.normal(-0.75, 0.2)
        out.append({"y": y, "lmfe": float(np.log(mfe)), "net": float(net)})
    return out


def one(args):
    name, seed = args
    if not _G:
        init()
    spec = SCENARIOS[name]
    mx = _G["mx"]
    rng = np.random.default_rng(1000 * seed + sum(ord(ch) for ch in name) % 997)
    P, Y, planted = world(rng, spec)
    X, B, desc, allowed = mx["X"], _G["B"], _G["desc"], _G["allowed"]
    if spec.get("rebuild_history"):
        feats = F20.build(_G["base_rows"], _G["keys"], synthetic_outcomes(rng, Y))
        X = X.copy()
        for j in _G["h1_cols"]:
            nme = mx["names"][j]
            X[:, j] = np.array([np.nan if r[nme] is None else r[nme] for r in feats], dtype=np.float32)
        B, desc, _ = M.prepare_atoms(X, mx["names"], mx["meta"], _G["ref"], _G["excl"], _G["nomiss"])
        allowed, _ = M.allowed_pairs(X, desc, _G["ref"])
    t0 = time.time()
    elig = _G["elig"]
    cands, info = M.build_candidates(X, mx["names"], _G["excl"], B, desc, allowed, Y, elig, mx["blocks"],
                                     mx["days"], mx["clusters"], with_composite=True)
    M.holdout(cands, "val", Y, elig, mx["blocks"], "VAL", mx["clusters"], mx["days"])
    for c in cands:
        c["val_pass"] = M.val_pass(c["val"])
    surv = [c for c in cands if c["val_pass"]]
    M.holdout(cands, "oos", Y, elig, mx["blocks"], "OOS", mx["clusters"], mx["days"])
    for c in cands:
        c["oos_pass"] = False
    for c, ok in zip(surv, M.oos_decide([c["oos"] for c in surv])):
        c["oos_pass"] = ok
    hold_rows = elig & ((mx["blocks"] == "VAL") | (mx["blocks"] == "OOS"))
    recs = []
    for c in cands:
        hs = M.hold_summary(c["fire"], Y[c["target"]], elig, mx["blocks"], mx["days"])
        c["tier"] = M.tier(c["val_pass"], c["oos_pass"], c["oos"], hs["hold"]["lifts_val_oos"], hs["hold"]["p_day"])
        f = c["fire"]
        inside = float((f & planted["fire"]).sum() / max(f.sum(), 1)) if planted is not None else None
        jac = float((f & planted["fire"]).sum() / max((f | planted["fire"]).sum(), 1)) if planted is not None else None
        tg = c["target"]
        tl = float(P[tg][hold_rows & f].mean() / P[tg][hold_rows].mean()) if (hold_rows & f).sum() else None
        recs.append({"id": c["id"], "kind": c["kind"], "depth": c["depth"], "families": c["families"],
                     "uses_history": any(x.startswith(("h1_", "tr_", "reg_", "kg_")) for x in c["text"].split()),
                     "val_pass": c["val_pass"], "oos_pass": c["oos_pass"], "tier": c["tier"],
                     "val_p": c["val"]["p"], "oos_p": c["oos"]["p"], "true_lift_hold": tl,
                     "inside_planted": inside, "jaccard_planted": jac})
    out = {"scenario": name, "seed": seed, "seconds": round(time.time() - t0, 1), "cfg": dict(M.CFG),
           "bases": _G["bases"], "n_candidates": len(cands), "n_val_pass": len(surv),
           "n_oos_pass": sum(1 for r in recs if r["oos_pass"]),
           "n_interesting": sum(1 for r in recs if r["tier"] == "INTERESTING"),
           "oos_pass_history": sum(1 for r in recs if r["oos_pass"] and r["uses_history"]),
           "disc_passed": {tg: info[tg]["disc_passed"] for tg in info},
           "sel_passed": {tg: info[tg]["sel_passed"] for tg in info},
           "candidates": recs}
    if planted is not None:
        out.update(planted_text=M.rule_text(planted["rule"], desc), planted_support=float(planted["fire"][elig].mean()),
                   planted_frozen=any(r["jaccard_planted"] >= 0.5 for r in recs),
                   planted_val=any(r["jaccard_planted"] >= 0.5 and r["val_pass"] for r in recs),
                   planted_oos=any(r["jaccard_planted"] >= 0.5 and r["oos_pass"] for r in recs),
                   signal_oos=any(r["inside_planted"] >= 0.5 and r["oos_pass"] for r in recs),
                   false_oos=sum(1 for r in recs if r["oos_pass"] and r["inside_planted"] < 0.2))
    else:
        out.update(false_oos=out["n_oos_pass"])
    return out


def main() -> None:
    n_null = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    n_pl = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    names = os.environ.get("AP_SCENARIOS", ",".join(SCENARIOS)).split(",")
    tag = os.environ.get("AP_TAG", "")
    out_path = os.path.join(A.CONTROLES, "ctl_00_controls%s.json" % (("_" + tag) if tag else ""))
    if os.path.exists(out_path):
        sys.exit("refusing to overwrite " + out_path)
    jobs = []
    for nme in names:
        n_seeds = n_null if nme == "NULL" else (max(n_null // 3, 12) if nme.startswith("NULL") else n_pl)
        jobs += [(nme, s) for s in range(n_seeds)]
    res = []
    with Pool(workers, initializer=init) as pool:
        for r in pool.imap_unordered(one, jobs):
            res.append(r)
            print(json.dumps({k: r[k] for k in ("scenario", "seed", "seconds", "n_candidates", "n_val_pass",
                                                "n_oos_pass", "n_interesting", "false_oos")}), flush=True)
    cfgs = {json.dumps(r["cfg"], sort_keys=True) for r in res}
    if len(cfgs) != 1 or len({json.dumps(r["bases"]) for r in res}) != 1:
        raise RuntimeError("workers did not share one configuration")
    summ = {}
    for nme in names:
        rr = [r for r in res if r["scenario"] == nme]
        if not rr:
            continue
        s = {"runs": len(rr), "runs_with_false_oos_survivor": sum(1 for r in rr if r["false_oos"] > 0),
             "false_oos_survivors_per_run": sum(r["false_oos"] for r in rr) / len(rr),
             "oos_survivors_per_run": sum(r["n_oos_pass"] for r in rr) / len(rr),
             "val_pass_per_run": sum(r["n_val_pass"] for r in rr) / len(rr),
             "interesting_per_run": sum(r["n_interesting"] for r in rr) / len(rr),
             "runs_with_interesting": sum(1 for r in rr if r["n_interesting"] > 0),
             "oos_survivors_using_history": sum(r["oos_pass_history"] for r in rr)}
        if rr[0].get("planted_text"):
            s.update(planted_frozen=sum(r["planted_frozen"] for r in rr), planted_val=sum(r["planted_val"] for r in rr),
                     planted_oos=sum(r["planted_oos"] for r in rr), signal_oos=sum(r["signal_oos"] for r in rr))
        summ[nme] = s
    A.write_json(out_path, {"boot_in_controls": res[0]["cfg"]["BOOT"], "cfg": res[0]["cfg"], "bases": res[0]["bases"],
                            "scenarios": {k: SCENARIOS[k] for k in names}, "summary": summ,
                            "runs": sorted(res, key=lambda r: (r["scenario"], r["seed"]))})
    A.registre("controls", sum(r["n_candidates"] for r in res), "synthetic controls, %d runs" % len(res),
               {"scenarios": names}, n=len(res), donnees="synthetiques", sortie=os.path.relpath(out_path, A.STUDY))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
