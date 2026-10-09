#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mech_40_break_the_loop.py -- mechanism autopsy of D1 (sync sizes + same slot + shared funder) on
DISCOVERY only. No mining: pre-specified decompositions, trajectories, events and a handful of
mechanically-justified rules. Nothing of SELECTION / VALIDATION / OOS is read.

Per eligible DISCOVERY launch, from the raw window (every transaction creation -> alert, parsed
with post_detection_forensics/fparse.py) and the wallet cache (genesis funder when the wallet's
history was fully read, number of earlier transactions):
  participants: core snipers, creator, external buyers / sellers before the cut (bt <= t - 1 s)
  per wallet: genesis funder (if known), prior transactions, recurrence (seen as an external buyer
  of an EARLIER alert), link (shares a genesis funder with another participant of this launch),
  independence (known funder shared with nobody, or history too long to read = old wallet)
  time bins relative to the alert: (-inf,-30], (-30,-20], (-20,-10], (-10,-5], (-5,-2], (-2,-1], (-1,0]
  events: first coordinated burst, independent arrivals after it, acceleration, second funder group
Groups: D1 fires / not; D1 and x2 / D1 and not x2 / D1 and x3. Decomposition of D1 into its three
components. Mechanism rules R1-R6 with fixed thresholds. Actor histories (causal, DISCOVERY only).
"""
from __future__ import annotations

import gzip
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

import ap_data as D
import ap_lib as A
import ap_mine as M

sys.path.insert(0, os.path.join(A.W, "post_detection_forensics", "code"))
import fparse  # noqa: E402

CACHE = os.path.join(A.CRYPTO, "Why-Solana-Memecoins-Are-Over", "post_detection_forensics", "data", "onchain_cache")
BINS = [(-1e9, -30), (-30, -20), (-20, -10), (-10, -5), (-5, -2), (-2, -1), (-1, 0)]
BIN_NAMES = ["<-30", "-30..-20", "-20..-10", "-10..-5", "-5..-2", "-2..-1", "-1..0 (post-cut)"]
SIM = 0.05          # same size = within 5 %
OLD = 1000          # history not fully read (>= 1000 transactions): old wallet, funder unknown


def load_window(mint):
    w = json.load(gzip.open(os.path.join(CACHE, "win", mint + ".json.gz"), "rt"))
    recs, facts = fparse.parse_window(w)
    return w, recs, facts


def load_wal(mint):
    w = json.load(gzip.open(os.path.join(CACHE, "wal", mint + ".json.gz"), "rt"))
    out = {}
    for a, v in w["wallets"].items():
        g = (v.get("genesis") or {}).get("funding") or {}
        out[a] = {"role": v.get("role"), "prior_n": (v.get("prior") or {}).get("n"), "first_bt": v.get("first_bt"),
                  "funder": g.get("funder"), "funder_bt": g.get("bt"), "hub": (v.get("genesis") or {}).get("hub")}
    return out


def launch_profile(b, cd, idx_early, out_hist, resolved_gate):
    """Everything about one launch's pre-alert sequence. Returns a dict (no outcome inside)."""
    t = b["t"]
    w, recs, facts = load_window(b["mint"])
    wal = load_wal(b["mint"])
    core = set(cd["core"])
    creator = cd["creator"]
    ext_set = core | ({creator} if creator else set())
    trades = [r for r in recs if r.get("kind") in ("buy", "sell") and not r.get("err") and r.get("trader")]
    ext = [r for r in trades if r["trader"] not in ext_set and not (r["kind"] == "buy" and r["slot"] == cd["slot0"])]
    for r in ext:
        r["dt"] = (r.get("bt") or 0) - t
    pre = [r for r in ext if r["dt"] <= -1]
    buyers_pre = [r for r in pre if r["kind"] == "buy"]
    # wallet attributes
    part = set(core) | ({creator} if creator else set()) | {r["trader"] for r in buyers_pre}
    funder = {a: (wal.get(a) or {}).get("funder") for a in part}
    fcount = Counter(f for f in funder.values() if f)
    core_funders = {funder[a] for a in core if funder.get(a)} | ({funder.get(creator)} if creator and funder.get(creator) else set())
    attrs = {}
    first_seen = {}
    for r in sorted(buyers_pre, key=lambda r: (r["slot"], r["dt"])):
        a = r["trader"]
        first_seen.setdefault(a, r["dt"])
    for a in {r["trader"] for r in buyers_pre}:
        v = wal.get(a) or {}
        f = funder.get(a)
        linked = bool(f and fcount[f] >= 2)
        link_core = bool(f and f in core_funders)
        old = (v.get("prior_n") or 0) >= OLD
        fresh = (v.get("prior_n") is not None and v["prior_n"] <= 2)
        recurrent = a in idx_early and any(tj < t - 1 for tj, _ in idx_early[a])
        prior = [(tj, m) for tj, m in idx_early.get(a, []) if tj + resolved_gate <= t - 1 and out_hist.get(m) is not None]
        attrs[a] = {"funder": f, "linked": linked, "link_core": link_core, "old": old, "fresh": fresh,
                    "independent": (not linked) and (f is not None or old), "unknown": (f is None and not old),
                    "recurrent": recurrent, "prior_n_launches": len([1 for tj, _ in idx_early.get(a, []) if tj < t - 1]),
                    "prior_resolved": len(prior), "prior_x2": (sum(out_hist[m]["y2"] for _, m in prior) / len(prior)) if prior else None,
                    "first_dt": first_seen[a], "prior_tx": v.get("prior_n")}
    # bins
    bins = []
    seen = set()
    cum_sol = 0.0
    for (lo, hi), name in zip(BINS, BIN_NAMES):
        rb = [r for r in ext if lo < r["dt"] <= hi]
        bb = [r for r in rb if r["kind"] == "buy"]
        sb = [r for r in rb if r["kind"] == "sell"]
        ws = {r["trader"] for r in bb}
        new = {a for a in ws if a not in seen}
        seen |= ws
        sizes = np.array([abs(r.get("v_sol") or 0.0) for r in bb])
        cum_sol += float(sizes.sum())
        # sync pairs inside the bin: same slot, different wallets, size within 5 %
        by_slot = defaultdict(list)
        for r, x in zip(bb, sizes):
            by_slot[r["slot"]].append((r["trader"], float(x)))
        sync = 0
        for lst in by_slot.values():
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    a_, b_ = lst[i], lst[j]
                    if a_[0] != b_[0] and max(a_[1], b_[1]) > 0 and abs(a_[1] - b_[1]) / max(a_[1], b_[1]) <= SIM:
                        sync += 1
        at = [attrs.get(a) for a in ws if attrs.get(a)]
        bins.append({"bin": name, "buys": len(bb), "sells": len(sb), "buy_sol": float(sizes.sum()), "cum_sol": cum_sol,
                     "active": len(ws), "new": len(new), "cum_wallets": len(seen),
                     "recurrent": sum(1 for a in at if a["recurrent"]), "linked": sum(1 for a in at if a["linked"]),
                     "independent": sum(1 for a in at if a["independent"]), "unknown": sum(1 for a in at if a["unknown"]),
                     "fresh": sum(1 for a in at if a["fresh"]),
                     "funders_known": len({a["funder"] for a in at if a["funder"]}),
                     "size_median": float(np.median(sizes)) if len(sizes) else None,
                     "size_cv": float(sizes.std() / sizes.mean()) if len(sizes) > 1 and sizes.mean() > 0 else None,
                     "sync_pairs": sync})
    # events (pre-cut only)
    seq = sorted(buyers_pre, key=lambda r: (r["slot"], r["dt"]))
    t_burst = None
    by_slot = defaultdict(list)
    for r in seq:
        by_slot[r["slot"]].append(r)
    for s in sorted(by_slot):
        lst = by_slot[s]
        sizes = [abs(r.get("v_sol") or 0.0) for r in lst]
        wallets = {r["trader"] for r in lst}
        sim = 0
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                if lst[i]["trader"] != lst[j]["trader"] and max(sizes[i], sizes[j]) > 0 and abs(sizes[i] - sizes[j]) / max(sizes[i], sizes[j]) <= SIM:
                    sim += 1
        linked_here = sum(1 for a in wallets if attrs[a]["linked"])
        if (len(wallets) >= 3 and sim >= 2) or linked_here >= 2:
            t_burst = lst[0]["dt"]
            break
    ev = {"t_burst": t_burst, "n_ext_buyers": len(attrs), "n_independent": sum(1 for a in attrs.values() if a["independent"]),
          "n_linked": sum(1 for a in attrs.values() if a["linked"]), "n_unknown": sum(1 for a in attrs.values() if a["unknown"]),
          "n_recurrent": sum(1 for a in attrs.values() if a["recurrent"]), "n_fresh": sum(1 for a in attrs.values() if a["fresh"]),
          "n_funder_groups": sum(1 for f, c in fcount.items() if c >= 2),
          "n_link_core": sum(1 for a in attrs.values() if a["link_core"]),
          "window_s": float(t - 1 - (seq[0]["dt"] + t)) if seq else None}
    if t_burst is not None:
        after = [a for a in attrs.values() if a["first_dt"] > t_burst]
        ev.update(indep_after_burst=sum(1 for a in after if a["independent"]), new_after_burst=len(after),
                  linked_after_burst=sum(1 for a in after if a["linked"]),
                  indep_before_burst=sum(1 for a in attrs.values() if a["first_dt"] <= t_burst and a["independent"]),
                  burst_position=(t_burst - seq[0]["dt"]) / max(1e-9, (-1 - seq[0]["dt"])) if seq else None)
    # independent arrivals over time: when does the count reach 5, 10
    ind_dts = sorted(a["first_dt"] for a in attrs.values() if a["independent"])
    ev["t_indep_5"] = ind_dts[4] if len(ind_dts) >= 5 else None
    ev["t_indep_10"] = ind_dts[9] if len(ind_dts) >= 10 else None
    all_dts = sorted(a["first_dt"] for a in attrs.values())
    ev["t_buyers_10"] = all_dts[9] if len(all_dts) >= 10 else None
    ev["t_buyers_20"] = all_dts[19] if len(all_dts) >= 20 else None
    # acceleration: buys in (-5,-1] over buys in (-10,-5]
    b_last = sum(1 for r in buyers_pre if -5 < r["dt"] <= -1)
    b_prev = sum(1 for r in buyers_pre if -10 < r["dt"] <= -5)
    ev["accel_buys"] = (b_last / b_prev) if b_prev else (None if b_last == 0 else float("inf"))
    i_last = sum(1 for a in attrs.values() if a["independent"] and -5 < a["first_dt"] <= -1)
    i_prev = sum(1 for a in attrs.values() if a["independent"] and -10 < a["first_dt"] <= -5)
    ev["indep_last5"], ev["indep_prev5"] = i_last, i_prev
    # second funder group appearance time
    fg_dts = {}
    for a, at in attrs.items():
        if at["linked"]:
            fg_dts.setdefault(at["funder"], []).append(at["first_dt"])
    second = sorted(sorted(v)[1] for v in fg_dts.values() if len(v) >= 2)
    ev["t_second_funder_group"] = second[1] if len(second) >= 2 else None
    ev["t_first_funder_group"] = second[0] if second else None
    # historically performing wallets present (causal)
    perf = [a for a in attrs.values() if a["prior_resolved"] >= 3 and a["prior_x2"] is not None and a["prior_x2"] >= 0.5]
    ev["n_perf_wallets"] = len(perf)
    ev["perf_first_dt"] = min(a["first_dt"] for a in perf) if perf else None
    return {"mint": b["mint"], "t": t, "bins": bins, "events": ev, "attrs": attrs,
            "funders": {f: c for f, c in fcount.items() if c >= 2}, "core_funders": sorted(core_funders)}


def rate(mask, y):
    n = int(mask.sum())
    return {"n": n, "successes": int(y[mask].sum()), "precision": float(y[mask].mean()) if n else None}


def main() -> None:
    mx = D.load_matrix()
    lab = D.label_arrays("discovery", mx["mints"])
    rows = np.flatnonzero(lab["elig"])
    assert set(mx["blocks"][rows]) == {"DISC"}
    base = {b["mint"]: b for b in A.load_base()}
    names = mx["names"]
    X = mx["X"].astype(float)
    cd = {}
    for r in A.jl(A.CD_TABLE):
        cd[r["mint"]] = {"core": [s["wallet"] for s in r["snipers"] if s.get("role") == "core"],
                         "creator": (r.get("creator") or {}).get("wallet"), "slot0": r["slot0"],
                         "early": [(x["wallet"], x["bt"]) for x in r["early"] if x.get("pre_alert")]}
    # chronological early-buyer index over ALL alerts (causal use: only tj < ti - 1 is read later)
    idx_early = defaultdict(list)
    for m, c in cd.items():
        for wal, bt in c["early"]:
            idx_early[wal].append((base[m]["t"], m))
    # outcome history for actor track records: DISCOVERY labels only (prior alerts of DISCOVERY rows are DISCOVERY rows)
    out_hist = {}
    for i in rows:
        out_hist[mx["mints"][i]] = {"y2": int(lab["y"]["Y2"][i]), "y3": int(lab["y"]["Y3"][i])}
    ex = lab["extra"]
    y2, y3, y5 = (lab["y"][tg] for tg in A.TARGETS)
    net2 = ex["tp2_next.net_500"]
    # D1 and its components on DISCOVERY rows (same thresholds as the pattern library)
    col = {k: X[:, names.index(k)] for k in ("pg_sync_same_size_pairs", "pg_same_slot_max_buyers", "g_early_funders_shared", "pg_same_size_share")}
    q65_size = float(np.nanquantile(col["pg_same_size_share"][rows], 0.65))
    AB = col["pg_sync_same_size_pairs"] >= 4
    Async = col["pg_same_slot_max_buyers"] >= 8
    Bsize = col["pg_same_size_share"] >= q65_size
    Cfund = col["g_early_funders_shared"] > 0
    D1 = AB & Async & Cfund
    combos = {"A_sync_alone": Async, "B_sizes_alone": Bsize, "C_funder_alone": Cfund, "AB_sync+sizes": Async & Bsize,
              "AC_sync+funder": Async & Cfund, "BC_sizes+funder": Bsize & Cfund, "ABC_sync+sizes+funder": Async & Bsize & Cfund,
              "sync_same_size_pairs>=4 (D1 atom)": AB, "D1 = pairs>=4 & slot>=8 & funder": D1, "none_of_the_three": ~Async & ~Bsize & ~Cfund}
    n_tests = 0
    decomposition = {}
    for k, m in combos.items():
        mm = np.zeros(len(X), dtype=bool)
        mm[rows] = m[rows]
        r2, r3, r5 = rate(mm[rows], y2[rows]), rate(mm[rows], y3[rows]), rate(mm[rows], y5[rows])
        decomposition[k] = {"n": r2["n"], "x2": r2["precision"], "x3": r3["precision"], "x5": r5["precision"],
                            "lift_x2": (r2["precision"] / y2[rows].mean()) if r2["precision"] is not None else None,
                            "lift_x3": (r3["precision"] / y3[rows].mean()) if r3["precision"] is not None else None,
                            "ev_500_x2": float(np.nanmean(net2[rows][mm[rows]])) if r2["n"] and (~np.isnan(net2[rows][mm[rows]])).sum() else None,
                            "clusters": int(len(set(mx["clusters"][rows][mm[rows]]))), "days": int(len(set(mx["days"][rows][mm[rows]])))}
        n_tests += 3
    # profiles of every eligible DISCOVERY launch
    profiles = {}
    for i in rows:
        m = mx["mints"][i]
        profiles[m] = launch_profile(base[m], cd[m], idx_early, out_hist, A.RESOLVE_1H)
    groups = {"D1": D1[rows], "nonD1": ~D1[rows], "D1_x2": D1[rows] & (y2[rows] == 1), "D1_fail": D1[rows] & (y2[rows] == 0),
              "D1_x3": D1[rows] & (y3[rows] == 1), "nonD1_x2": ~D1[rows] & (y2[rows] == 1), "nonD1_fail": ~D1[rows] & (y2[rows] == 0)}
    mints_rows = [mx["mints"][i] for i in rows]
    traj = {}
    for g, mask in groups.items():
        sel = [profiles[m] for m, ok in zip(mints_rows, mask) if ok]
        per_bin = []
        for bi, name in enumerate(BIN_NAMES):
            vals = defaultdict(list)
            for p in sel:
                for k, v in p["bins"][bi].items():
                    if k != "bin" and v is not None:
                        vals[k].append(v)
            per_bin.append({"bin": name, **{k: (float(np.mean(v)), float(np.median(v))) for k, v in vals.items()}})
        evs = defaultdict(list)
        for p in sel:
            for k, v in p["events"].items():
                if v is not None and not (isinstance(v, float) and not np.isfinite(v)):
                    evs[k].append(v)
        traj[g] = {"n": len(sel), "bins": per_bin,
                   "events": {k: {"n": len(v), "mean": float(np.mean(v)), "median": float(np.median(v))} for k, v in evs.items()},
                   "share_with_burst": float(np.mean([p["events"]["t_burst"] is not None for p in sel])) if sel else None,
                   "share_second_funder_group": float(np.mean([p["events"]["t_second_funder_group"] is not None for p in sel])) if sel else None,
                   "share_perf_wallet": float(np.mean([p["events"]["n_perf_wallets"] > 0 for p in sel])) if sel else None}
    # mechanism rules with fixed, mechanically justified thresholds
    def ev_of(p, k):
        return p["events"].get(k)
    rules = {
        "R1_burst_then_ge5_independent": lambda p: ev_of(p, "t_burst") is not None and (ev_of(p, "indep_after_burst") or 0) >= 5,
        "R1b_burst_then_lt5_independent": lambda p: ev_of(p, "t_burst") is not None and (ev_of(p, "indep_after_burst") or 0) < 5,
        "R2_burst_in_first_half_window": lambda p: ev_of(p, "t_burst") is not None and (ev_of(p, "burst_position") or 1) <= 0.5,
        "R2b_burst_in_second_half_window": lambda p: ev_of(p, "t_burst") is not None and (ev_of(p, "burst_position") or 0) > 0.5,
        "R3_independent_accelerate_last5s": lambda p: (ev_of(p, "indep_last5") or 0) >= 3 and (ev_of(p, "indep_last5") or 0) > (ev_of(p, "indep_prev5") or 0),
        "R4_second_funder_group_present": lambda p: ev_of(p, "t_second_funder_group") is not None,
        "R5_performing_wallet_present": lambda p: (ev_of(p, "n_perf_wallets") or 0) >= 1,
        "R6_ge10_independent_total": lambda p: (ev_of(p, "n_independent") or 0) >= 10,
        "R7_no_burst_at_all": lambda p: ev_of(p, "t_burst") is None,
        "R8_D1_and_ge5_independent_after_burst": lambda p: False,   # filled below
        "R9_linked_share_ge_half": lambda p: ev_of(p, "n_ext_buyers") and (ev_of(p, "n_linked") or 0) / ev_of(p, "n_ext_buyers") >= 0.5,
    }
    rule_eval = {}
    for k, fn in rules.items():
        mask = np.array([fn(profiles[m]) for m in mints_rows], dtype=bool)
        if k == "R8_D1_and_ge5_independent_after_burst":
            mask = D1[rows] & np.array([rules["R1_burst_then_ge5_independent"](profiles[m]) for m in mints_rows])
        r2, r3 = rate(mask, y2[rows]), rate(mask, y3[rows])
        rule_eval[k] = {"n": r2["n"], "x2": r2["precision"], "x3": r3["precision"],
                        "lift_x2": (r2["precision"] / y2[rows].mean()) if r2["precision"] is not None else None,
                        "lift_x3": (r3["precision"] / y3[rows].mean()) if r3["precision"] is not None else None,
                        "ev_500_x2": float(np.nanmean(net2[rows][mask])) if r2["n"] and (~np.isnan(net2[rows][mask])).sum() else None,
                        "clusters": int(len(set(mx["clusters"][rows][mask]))), "days": int(len(set(mx["days"][rows][mask]))),
                        "within_D1": rate(mask & D1[rows], y2[rows]), "outside_D1": rate(mask & ~D1[rows], y2[rows])}
        n_tests += 4
    # actors of the D1 launches
    actors = {"funders": {}, "wallets": []}
    d1_mints = [m for m, ok in zip(mints_rows, D1[rows]) if ok]
    funder_launches = defaultdict(list)
    for m in mints_rows:
        for f in profiles[m]["funders"]:
            funder_launches[f].append(m)
    for m in d1_mints:
        for f, c in profiles[m]["funders"].items():
            ls = funder_launches[f]
            actors["funders"][f] = {"wallets_in_this_launch": c, "disc_launches_funding_early_wallets": len(ls),
                                    "x2_rate_of_those": float(np.mean([out_hist[x]["y2"] for x in ls])),
                                    "is_core_funder_here": f in profiles[m]["core_funders"], "launch": m[:8]}
    wl = []
    for m in d1_mints:
        for a, at in profiles[m]["attrs"].items():
            if at["linked"] or at["recurrent"]:
                wl.append({"launch": m[:8], "wallet": a[:8], "linked": at["linked"], "recurrent": at["recurrent"],
                           "prior_launches": at["prior_n_launches"], "prior_resolved": at["prior_resolved"], "prior_x2": at["prior_x2"],
                           "first_dt": at["first_dt"], "prior_tx": at["prior_tx"], "fresh": at["fresh"]})
    actors["wallets_summary"] = {"n": len(wl), "linked": sum(1 for w in wl if w["linked"]), "recurrent": sum(1 for w in wl if w["recurrent"]),
                                 "fresh": sum(1 for w in wl if w["fresh"]),
                                 "median_prior_launches_recurrent": float(np.median([w["prior_launches"] for w in wl if w["recurrent"]])) if any(w["recurrent"] for w in wl) else None,
                                 "prior_x2_mean_recurrent_resolved": float(np.mean([w["prior_x2"] for w in wl if w["prior_x2"] is not None])) if any(w["prior_x2"] is not None for w in wl) else None}
    # funder reuse across launches among D1: same funder on >= 2 DISC launches
    reuse = {f: v for f, v in actors["funders"].items() if v["disc_launches_funding_early_wallets"] >= 2}
    actors["funders_reused"] = len(reuse)
    actors["funders_total"] = len(actors["funders"])
    # delay between first appearance of linked wallets and the hit, for D1 successes
    delays = []
    for i, m in zip(rows, mints_rows):
        if D1[i] and y2[i] == 1 and ex["t_hit_2x"][i] is not None and not np.isnan(ex["t_hit_2x"][i]):
            lk = [at["first_dt"] for at in profiles[m]["attrs"].values() if at["linked"]]
            if lk:
                delays.append(ex["t_hit_2x"][i] - min(lk))
    actors["delay_linked_first_to_2x_s"] = {"n": len(delays), "median": float(np.median(delays)) if delays else None}
    # per-launch D1 table
    d1_table = []
    for i, m in zip(rows, mints_rows):
        if D1[i]:
            e = profiles[m]["events"]
            d1_table.append({"mint": m[:10], "y2": int(y2[i]), "y3": int(y3[i]), "n_ext_buyers": e["n_ext_buyers"], "independent": e["n_independent"],
                             "linked": e["n_linked"], "unknown": e["n_unknown"], "recurrent": e["n_recurrent"], "fresh": e["n_fresh"],
                             "funder_groups": e["n_funder_groups"], "t_burst": e["t_burst"], "indep_after_burst": e.get("indep_after_burst"),
                             "burst_position": e.get("burst_position"), "accel_buys": e["accel_buys"], "second_group": e["t_second_funder_group"],
                             "perf_wallets": e["n_perf_wallets"], "window_s": e["window_s"], "cluster": mx["clusters"][i][:12],
                             "premium": float(X[i, names.index("p_entry_over_operator")]) if not np.isnan(X[i, names.index("p_entry_over_operator")]) else None})
    A.registre("mechanism_disc", n_tests, "D1 autopsy: decomposition, trajectories, mechanism rules on DISCOVERY (descriptive)",
               n=int(len(rows)), declare=False, sortie="tables/break_the_loop.json")
    A.write_json(os.path.join(A.TABLES, "break_the_loop.json"),
                 {"base_x2": float(y2[rows].mean()), "base_x3": float(y3[rows].mean()), "q65_same_size_share": q65_size,
                  "decomposition": decomposition, "trajectories": traj, "rules": rule_eval, "actors": actors, "d1_launches": d1_table,
                  "d1_variants_note": "strict/loose/cut2 lifts are in composite_patterns_results.json"})
    # console summary
    print("base x2 %.3f x3 %.3f" % (y2[rows].mean(), y3[rows].mean()))
    print("\n== decomposition")
    for k, v in decomposition.items():
        print("%-36s n %3d x2 %s (lift %s) x3 %s (lift %s) EV %s cl %d" % (k, v["n"], "%.2f" % v["x2"] if v["x2"] is not None else "n/a",
              "%.2f" % v["lift_x2"] if v["lift_x2"] else "n/a", "%.2f" % v["x3"] if v["x3"] is not None else "n/a",
              "%.2f" % v["lift_x3"] if v["lift_x3"] else "n/a", "%.2f" % v["ev_500_x2"] if v["ev_500_x2"] is not None else "n/a", v["clusters"]))
    print("\n== rules")
    for k, v in rule_eval.items():
        print("%-40s n %3d x2 %s (lift %s) x3 %s (lift %s) EV %s cl %d | inD1 %s outD1 %s" % (k, v["n"], "%.2f" % v["x2"] if v["x2"] is not None else "n/a",
              "%.2f" % v["lift_x2"] if v["lift_x2"] else "n/a", "%.2f" % v["x3"] if v["x3"] is not None else "n/a",
              "%.2f" % v["lift_x3"] if v["lift_x3"] else "n/a", "%.2f" % v["ev_500_x2"] if v["ev_500_x2"] is not None else "n/a", v["clusters"],
              "%d/%d" % (v["within_D1"]["successes"], v["within_D1"]["n"]), "%d/%d" % (v["outside_D1"]["successes"], v["outside_D1"]["n"])))
    print("\n== trajectories (mean per bin): group n | bin: buys/new/independent/linked/recurrent/sync")
    for g, tv in traj.items():
        print(g, tv["n"], "burst %.2f 2nd-group %.2f perf %.2f" % (tv["share_with_burst"] or 0, tv["share_second_funder_group"] or 0, tv["share_perf_wallet"] or 0))
        for pb in tv["bins"]:
            print("   %-16s buys %5.1f new %5.1f indep %4.1f linked %4.1f recur %4.1f sync %4.1f cumW %5.1f" % (
                pb["bin"], pb.get("buys", (0,))[0], pb.get("new", (0,))[0], pb.get("independent", (0,))[0], pb.get("linked", (0,))[0],
                pb.get("recurrent", (0,))[0], pb.get("sync_pairs", (0,))[0], pb.get("cum_wallets", (0,))[0]))
        print("   events:", {k: round(v["median"], 2) for k, v in tv["events"].items() if k in ("t_burst", "indep_after_burst", "new_after_burst", "n_independent", "n_linked", "n_recurrent", "n_funder_groups", "accel_buys", "t_indep_5", "burst_position")})
    print("\n== actors: funders", actors["funders_total"], "reused on >=2 DISC launches", actors["funders_reused"], actors["wallets_summary"], actors["delay_linked_first_to_2x_s"])


if __name__ == "__main__":
    main()
