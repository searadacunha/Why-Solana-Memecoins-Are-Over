#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mech_48_absorption.py -- does external demand absorb the team's inventory? (tables/TEAM_ABSORPTION_PREREG_2026-10-07.md)

Population: the 1,015 alerts before 2026-09-15 (DISCOVERY + SELECTION). Outcomes only through
ap_lib.load_labels('selection') (explanatory Y2, entry +5 s) and the price series filtered to these
mints (tradable Y2_T, entry at T). VALIDATION and OOS are never loaded. Features: derived/feat_absorption.jsonl.gz
(code/feat_48_absorption.py, no outcome). Teams: U groups of mech_47_team_rhythm.build().
Modes:
  check  structural controls K1 and K3 (no outcome)
  real   the pre-registered tests -> tables/team_absorption.json (report written by hand from it)
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import binomtest

import ap_lib as A
import mech_47_team_rhythm as R
from mech_40_break_the_loop import load_window

sys.path.insert(0, os.path.join(A.W, "post_detection_edge", "code"))
import pde  # noqa: E402
import trade  # noqa: E402
import lab_10_labels as L  # noqa: E402

PREREG = "tables/TEAM_ABSORPTION_PREREG_2026-10-07.md"
FEAT = os.path.join(A.DERIVED, "feat_absorption.jsonl.gz")
CUTS_EXPL = (-1, 2)                         # explanatory BH family: before the entry only (amendment 1.2)
CUTS_LATE = (4, 9, 19, 29)                  # explanatory, descriptive only (no q; M10 excluded)
T_DEC = {5: 2, 10: 7, 20: 17, 30: 27}       # decision time -> feature cut T - 3 (amendment 1.1)
LAT_CUT = {5: 4, 10: 9, 20: 19, 30: 29}     # sensitivity: cut T - 1
B_MAIN, B_SENS = 5000, 2000
RNG = np.random.default_rng(20261009)
MET = ["M1_ext_buyers", "M2_ext_buy_sol", "M3_ext_buy_sol_last10", "M4_ext_accel", "M5_team_sold_share",
       "M6_team_sell_sol", "M7_demand_over_inventory", "M8_absorption", "M9_recurrent_share", "M10_price_move"]
DEMAND = {"M1_ext_buyers", "M2_ext_buy_sol", "M3_ext_buy_sol_last10", "M4_ext_accel", "M7_demand_over_inventory", "M8_absorption"}
TESTS = [0]


def load():
    S = R.build()
    rows = {r["mint"]: r for r in A.jl(FEAT)}
    if set(rows) != set(S["mints"]):
        raise RuntimeError("feature table does not match the 1,015 alerts")
    F = [rows[m] for m in S["mints"]]
    return S, F


def metrics(S, F, series):
    """M[name][cut] arrays aligned on S['mints']."""
    n, t = S["n"], S["t"]
    cuts = sorted(set(CUTS_EXPL) | set(CUTS_LATE) | set(T_DEC.values()) | set(LAT_CUT.values()))
    M = {m: {} for m in MET}
    # recurrent external buyers: seen as pre-alert external buyers in >= 5 earlier launches (60 s visibility)
    order = S["order"]
    seen = Counter()
    vis = 0
    seen_at = [None] * n
    for i in order:
        while vis < n and t[order[vis]] + 60 <= t[i] - 1:
            seen.update(S["ext"][order[vis]].keys())
            vis += 1
        seen_at[i] = {w: seen[w] for c in cuts for w in F[i]["ext_buyer_sol_t%+d" % c]}
    for c in cuts:
        s = "_t%+d" % c
        g = lambda k: np.array([np.nan if F[i].get(k + s) is None else F[i][k + s] for i in range(n)], float)  # noqa: E731
        inv = np.array([F[i]["inventory_value_sol"] for i in range(n)], float)
        M["M1_ext_buyers"][c] = g("ext_buyers")
        M["M2_ext_buy_sol"][c] = g("ext_buy_sol")
        M["M3_ext_buy_sol_last10"][c] = g("ext_buy_sol_last10")
        M["M4_ext_accel"][c] = g("ext_buyers_last10") - g("ext_buyers_prev10")
        M["M5_team_sold_share"][c] = g("team_sold_share")
        M["M6_team_sell_sol"][c] = g("team_sell_sol")
        M["M7_demand_over_inventory"][c] = g("ext_buy_sol") / inv
        M["M8_absorption"][c] = g("ext_buy_sol") / (g("team_sell_sol") + g("ext_sell_sol") + 1.0)
        M.setdefault("S_M8_with_buyburn", {})[c] = (g("ext_buy_sol") + g("buyburn_sol")) / (g("team_sell_sol") + g("ext_sell_sol") + 1.0)
        M.setdefault("S_M7_with_buyburn", {})[c] = (g("ext_buy_sol") + g("buyburn_sol")) / inv
        M.setdefault("S_exit_wallets", {})[c] = g("exit_wallets")
        rs = []
        for i in range(n):
            ws = F[i]["ext_buyer_sol" + s]
            rs.append(np.nan if not ws else sum(1 for w in ws if seen_at[i].get(w, 0) >= 5) / len(ws))
        M["M9_recurrent_share"][c] = np.array(rs, float)
        if c < 0:
            M["M10_price_move"][c] = np.full(n, np.nan)
        else:
            pm = []
            for m in S["mints"]:
                pts = [p for p in series.get(m, []) if 0 < p[0] <= c]
                pm.append(pts[-1][1] if pts else 1.0)
            M["M10_price_move"][c] = np.array(pm, float)
    return M


def labels(S, series):
    """Explanatory Y2 (entry +5 s) and tradable Y2_T (entry at T) with the tp2_next trade at 500 $."""
    lab = A.load_labels("selection")
    if {r["block"] for r in lab.values()} - {"DISC", "SEL"}:
        raise RuntimeError("a VALIDATION / OOS label was loaded")
    n = S["n"]
    base = {b["mint"]: b for b in S["base"]}
    Y = {"Y2": np.full(n, np.nan)}
    NET = {}
    ENTRY = {}
    for T in T_DEC:
        Y["Y2_%d" % T] = np.full(n, np.nan)
        NET[T] = np.full(n, np.nan)
        ENTRY[T] = np.full(n, np.nan)
    mfe_path = {}
    for i, m in enumerate(S["mints"]):
        r = lab.get(m)
        if not r:
            continue
        if r.get("fine") and r.get("entry") and r.get("obs_3600"):
            Y["Y2"][i] = r["conf_2x_3600"]
        pts = series.get(m) or []
        if not (r.get("fine") and pts):
            continue
        for T in T_DEC:
            ent = pde.entry_point(pts, float(T))
            if ent is None:
                continue
            if ent[0] < T:
                raise RuntimeError("tradable entry before the decision time")
            pl = L.path_labels(pts, True, ent[0], ent[1])
            if not pl["obs_3600"]:
                continue
            Y["Y2_%d" % T][i] = pl["conf_2x_3600"]
            ENTRY[T][i] = ent[1]
            sim = trade.simulate(pts, True, float(T), 2.0, None, 3600, "next")
            if sim["status"] == "ok":
                NET[T][i] = trade.net_return(sim["gross"], sim["entry_mult"], base[m]["p0"], r["p0_source"], base[m]["t"], 500, A.COST)
        e5 = pde.entry_point(pts, 5.0)
        if e5 and not np.isnan(Y["Y2"][i]):
            mfe_path[i] = {h: (max([p[1] for p in pts if e5[0] < p[0] <= e5[0] + h] or [np.nan]) / e5[1]) for h in (10, 20, 30, 60, 120, 300)}
            mfe_path[i].update({"at_%d" % h: next((p[1] / e5[1] for p in pts if p[0] >= e5[0] + h), np.nan) for h in (10, 20, 30, 60, 120, 300)})
    ok5 = ~np.isnan(Y["Y2"]) & ~np.isnan(Y["Y2_5"])
    if not np.array_equal(Y["Y2"][ok5], Y["Y2_5"][ok5]) or ok5.sum() != (~np.isnan(Y["Y2"])).sum():
        raise RuntimeError("Y2_5 does not reproduce Y2")
    return Y, NET, ENTRY, mfe_path


def team_rows(S, y, min_elig=5, drop=None):
    U = S["U"]
    ie = np.flatnonzero(~np.isnan(y) & (np.ones(S["n"], bool) if drop is None else ~drop))
    ce = Counter(U[ie].tolist())
    return np.array([i for i in ie if ce[U[i]] >= min_elig])


def family(S, M, y_of, cuts_of, rows_of, B, rng, blocks=True, big=None):
    out = {}
    for m in MET:
        for key, c in cuts_of.items():
            x = M[m][c]
            if np.all(np.isnan(x)):
                continue
            y = y_of(key)
            rows = rows_of(key)
            r = R.within_auc(x, y, S["U"], rows, B, rng, big)
            TESTS[0] += 1
            if r is None:
                continue
            if blocks:
                for b in ("DISC", "SEL"):
                    rr = R.within_auc(x, y, S["U"], rows[S["blocks"][rows] == b], 0, rng)
                    r["auc_" + b] = rr["auc"] if rr else None
                    TESTS[0] += 1
                r["pooled_auc"] = R.pooled_auc(x, y, np.flatnonzero(~np.isnan(y)))
                r["same_sense"] = bool(r.get("auc_DISC") is not None and r.get("auc_SEL") is not None
                                       and np.sign(r["auc"] - 0.5) == np.sign(r["auc_DISC"] - 0.5) == np.sign(r["auc_SEL"] - 0.5))
            out["%s|%s" % (m, key)] = r
    if blocks:
        ks = [k for k in out if "p" in out[k]]
        q = A.bh([out[k]["p"] for k in ks])
        for k, qq in zip(ks, q):
            out[k]["q_bh"] = qq
            out[k]["passes"] = bool(qq <= 0.10 and out[k]["same_sense"])
    return out


def check() -> None:
    """K1 timestamps and K3 externality of the buyers, in SOL at each decision cut (no outcome)."""
    S, F = load()
    n = S["n"]
    k1 = Counter()
    for i, b in enumerate(S["base"]):
        w, recs, _ = load_window(b["mint"])
        recs = [r for r in recs if not r.get("err")]
        tc = F[i]["t_create"]
        bts = [r["bt"] for r in recs]
        k1["records"] += len(recs)
        k1["bt_before_create"] += sum(1 for x in bts if x < tc)
        k1["bt_after_window"] += sum(1 for x in bts if x > b["t"] + 30)
        srt = sorted(recs, key=lambda r: r["slot"])
        k1["slot_bt_inversions_gt1s"] += sum(1 for a, c in zip(srt, srt[1:]) if c["bt"] < a["bt"] - 1)
    funders = defaultdict(set)
    mset = set(S["mints"])
    for r in A.jl(A.CD_TABLE):
        if r["mint"] not in mset:
            continue
        for s in r["snipers"]:
            for k in ("last_funder", "gen_funder"):
                if s.get(k):
                    funders[r["mint"]].add(s[k])
    core_launch = defaultdict(set)
    for i in range(n):
        for w in S["core"][i]:
            core_launch[w].add(i)
    k3 = {}
    for c in sorted(set(T_DEC.values()) | {29}):
        tot = Counter()
        for i, b in enumerate(S["base"]):
            ext = F[i]["ext_buyer_sol_t%+d" % c]
            end = F[i]["ext_buyer_sol_t+29"]
            for w, sol in ext.items():
                tot["ext_sol"] += sol
                if w not in end:
                    tot["late_team_joiner_sol"] += sol
                if w in funders[b["mint"]]:
                    tot["sniper_funder_sol"] += sol
                js = core_launch.get(w, ())
                if any(S["U"][j] == S["U"][i] and j != i for j in js):
                    tot["same_team_sniper_sol"] += sol
                if any(S["U"][j] != S["U"][i] for j in js):
                    tot["other_team_sniper_sol"] += sol
        k3["cut_%+d" % c] = {k: float(v) for k, v in tot.items()}
        k3["cut_%+d" % c].update({"share_" + k: float(v / tot["ext_sol"]) for k, v in tot.items() if k != "ext_sol"})
    out = {"K1": dict(k1), "K3_sol_by_cut": k3}
    A.write_json(os.path.join(A.TABLES, "team_absorption_checks.json"), out)
    print(json.dumps(out, indent=1))


def slim(d):
    return {k: (v and {kk: v.get(kk) for kk in ("auc", "p", "n", "strata")}) for k, v in d.items()}


def real() -> None:
    S, F = load()
    n, U, blocks = S["n"], S["U"], S["blocks"]
    series_all = pde.load_series()
    series = {m: series_all.get(m, []) for m in S["mints"]}
    del series_all
    M = metrics(S, F, series)
    Y, NET, ENTRY, mfe_path = labels(S, series)
    TESTS[0] = 0
    big = max(Counter(U.tolist()).items(), key=lambda kv: kv[1])[0]
    nobig = U == big
    out = {"prereg_sha256": A.sha256_file(os.path.join(A.STUDY, PREREG)),
           "population": {"alerts": n, "largest_group": int(big),
                          **{k: {"eligible": int((~np.isnan(v)).sum()), "good": int(np.nansum(v)), "rate": float(np.nanmean(v)),
                                 "by_block": {b: [int(np.nansum(v[blocks == b])), int((~np.isnan(v[blocks == b])).sum())] for b in ("DISC", "SEL")},
                                 "within_rows": int(len(team_rows(S, v))), "within_teams": int(len(set(U[team_rows(S, v)].tolist())))}
                             for k, v in Y.items()}}}
    # ---------------- mechanism, descriptive (Y2 within-team rows), no test
    y = Y["Y2"]
    rows = team_rows(S, y)
    gi, bi = rows[y[rows] == 1], rows[y[rows] == 0]
    desc_keys = ["inventory_supply", "inventory_value_sol", "inventory_hhi", "exit_wallets_end", "first_transfer_from_create",
                 "first_team_sell_from_create", "first_team_sell_from_alert", "team_sold_share_c10", "team_sold_share_c20",
                 "team_sold_share_c30", "team_sold_share_c40", "age_alert"]
    desc = {}
    for k in desc_keys:
        v = np.array([np.nan if F[i].get(k) is None else F[i][k] for i in range(n)], float)
        desc[k] = {"good_median": float(np.nanmedian(v[gi])), "bad_median": float(np.nanmedian(v[bi])),
                   "good_n": int((~np.isnan(v[gi])).sum()), "bad_n": int((~np.isnan(v[bi])).sum())}
    timeline = {}
    for c in sorted(set(CUTS_EXPL) | set(CUTS_LATE) | set(T_DEC.values())):
        timeline[str(c)] = {m: {"good_median": float(np.nanmedian(M[m][c][gi])), "bad_median": float(np.nanmedian(M[m][c][bi]))} for m in MET}
    price = {}
    for h in (10, 20, 30, 60, 120, 300):
        for kind in ("max", "at"):
            key = h if kind == "max" else "at_%d" % h
            g = np.array([mfe_path[i][key] for i in gi if i in mfe_path], float)
            b_ = np.array([mfe_path[i][key] for i in bi if i in mfe_path], float)
            g, b_ = g[~np.isnan(g)], b_[~np.isnan(b_)]
            price["%s_%d" % (kind, h)] = {"good_median": float(np.median(g)), "bad_median": float(np.median(b_)), "good_n": int(len(g)), "bad_n": int(len(b_)),
                                          "good_share_ge2": float((g >= 2).mean()), "bad_share_ge2": float((b_ >= 2).mean()),
                                          "good_share_ge1_5": float((g >= 1.5).mean()), "bad_share_ge1_5": float((b_ >= 1.5).mean())}
    out["mechanism"] = {"descriptive": desc, "timeline_medians": timeline, "price_after_entry": price,
                        "rows": int(len(rows)), "good": int(len(gi)), "bad": int(len(bi))}
    s4 = sum(F[i]["team_end_sell_sol_by_t+4"] for i in range(n))
    s29 = sum(F[i]["team_end_sell_sol_by_t+29"] for i in range(n))
    out["K2_team_sell_sol_final_team"] = {"by_t+4": float(s4), "by_t+29": float(s29), "share_after_t+4": float(1 - s4 / s29),
                                          "launches_with_team_sell_by_t+29": int(sum(F[i]["first_team_sell_from_alert"] is not None for i in range(n)))}
    # ---------------- explanatory family (Y2), before the entry only
    out["explanatory"] = family(S, M, lambda k: Y["Y2"], {c: c for c in CUTS_EXPL}, lambda k: team_rows(S, Y["Y2"]), B_MAIN, RNG, big=big)
    late = {}
    for m in MET:
        if m == "M10_price_move":
            continue
        for c in CUTS_LATE:
            r = R.within_auc(M[m][c], y, U, rows, 0, RNG)
            TESTS[0] += 1
            late["%s|%d" % (m, c)] = r and {"auc": r["auc"], "n": r["n"], "pooled_auc": R.pooled_auc(M[m][c], y, np.flatnonzero(~np.isnan(y)))}
    out["explanatory_late_descriptive"] = late
    # equal-price tests: M2, M7, M8 at c = 29 within team x tercile of M10 at c = 29
    pm29 = M["M10_price_move"][29]
    qs = np.nanquantile(pm29[~np.isnan(y)], [1 / 3, 2 / 3])
    terc = np.where(pm29 <= qs[0], 0, np.where(pm29 <= qs[1], 1, 2))
    strata = U * 10 + terc
    eq = {}
    for m in ("M2_ext_buy_sol", "M7_demand_over_inventory", "M8_absorption"):
        r = R.within_auc(M[m][29], y, strata, rows, B_MAIN, RNG)
        TESTS[0] += 1
        for b in ("DISC", "SEL"):
            rr = R.within_auc(M[m][29], y, strata, rows[blocks[rows] == b], 0, RNG)
            r["auc_" + b] = rr["auc"] if rr else None
            TESTS[0] += 1
        r["same_sense"] = bool(r.get("auc_DISC") is not None and r.get("auc_SEL") is not None
                               and np.sign(r["auc"] - 0.5) == np.sign(r["auc_DISC"] - 0.5) == np.sign(r["auc_SEL"] - 0.5))
        eq[m] = r
    q = A.bh([eq[m]["p"] for m in eq])
    for m, qq in zip(eq, q):
        eq[m]["q_bh"] = qq
        eq[m]["passes"] = bool(qq <= 0.10 and eq[m]["same_sense"])
    out["equal_price"] = {"m10_terciles_at_29": qs.tolist(), **eq}
    # ---------------- tradable family (Y2_T, entry at T, features at T - 3)
    trad = family(S, M, lambda k: Y["Y2_%d" % k], T_DEC, lambda k: team_rows(S, Y["Y2_%d" % k]), B_MAIN, RNG, big=big)
    out["tradable"] = trad
    sens = {}
    sens["tradable_cut_T-1"] = slim(family(S, M, lambda k: Y["Y2_%d" % k], LAT_CUT, lambda k: team_rows(S, Y["Y2_%d" % k]), B_SENS, RNG, blocks=False))
    sens["tradable_without_largest_group"] = slim(family(S, M, lambda k: Y["Y2_%d" % k], T_DEC, lambda k: team_rows(S, Y["Y2_%d" % k], drop=nobig), B_SENS, RNG, blocks=False))
    sens["explanatory_without_largest_group"] = slim(family(S, M, lambda k: Y["Y2"], {c: c for c in CUTS_EXPL}, lambda k: team_rows(S, Y["Y2"], drop=nobig), B_SENS, RNG, blocks=False))
    sens["tradable_without_many_exit_wallets"] = slim(family(S, M, lambda k: Y["Y2_%d" % k], T_DEC,
                                                             lambda k: team_rows(S, Y["Y2_%d" % k], drop=(M["S_exit_wallets"][T_DEC[k]] > 10)), B_SENS, RNG, blocks=False))
    out["sensitivity"] = sens
    # ---------------- rules at c = T - 3 on all eligible launches of Y2_T
    disc = blocks == "DISC"
    rules = {}
    for T, c in T_DEC.items():
        yT, net = Y["Y2_%d" % T], NET[T]
        el = ~np.isnan(yT)
        thr3 = float(np.nanquantile(M["M3_ext_buy_sol_last10"][c][disc], 0.8))
        thr5 = float(np.nanmedian(M["M1_ext_buyers"][c][disc]))
        R_ = {"R1_absorption_ge1": M["M8_absorption"][c] >= 1,
              "R2_demand_inventory_ge0.25": M["M7_demand_over_inventory"][c] >= 0.25,
              "R3_velocity_ge_disc_p80": M["M3_ext_buy_sol_last10"][c] >= thr3,
              "R4_team_selling_price_holds": (M["M5_team_sold_share"][c] >= 0.05) & (M["M10_price_move"][c] >= 1.0),
              "R5_no_team_sell_strong_demand": (M["M5_team_sold_share"][c] == 0) & (M["M1_ext_buyers"][c] >= thr5),
              "S_R1_with_buyburn": M["S_M8_with_buyburn"][c] >= 1,
              "S_R2_with_buyburn": M["S_M7_with_buyburn"][c] >= 0.25}
        rules[str(T)] = {"cut": c, "base": {b: {"rate": float(np.nanmean(yT[el & (blocks == b)])), "n": int((el & (blocks == b)).sum()),
                                                "net_500_mean": float(np.nanmean(net[el & (blocks == b)]))} for b in ("DISC", "SEL")},
                         "thr_R3": thr3, "thr_R5": thr5}
        for nm, f in R_.items():
            rec = {}
            for b in ("DISC", "SEL", "ALL"):
                mk = el & f & ((blocks == b) if b != "ALL" else True)
                k_, n_ = int(np.nansum(yT[mk])), int(mk.sum())
                nv = net[mk]
                rec[b] = {"n": n_, "good": k_, "precision": (k_ / n_) if n_ else None, "ci": A.wilson(k_, n_) if n_ else None,
                          "net_500_mean": float(np.nanmean(nv)) if (~np.isnan(nv)).sum() else None, "net_n": int((~np.isnan(nv)).sum()),
                          "teams": int(len(set(U[mk].tolist())))}
                TESTS[0] += 1
            rec["meets_A"] = bool(not nm.startswith("S_") and all(rec[b]["n"] >= 15 and rec[b]["precision"] is not None and rec[b]["precision"] >= 0.458
                                                                  and rec[b]["net_500_mean"] is not None and rec[b]["net_500_mean"] > 0 for b in ("DISC", "SEL")))
            rules[str(T)][nm] = rec
    out["rules"] = rules
    # ---------------- GOOD vs BAD per team (Y2, >= 3 GOOD and >= 3 BAD): c = 29 (pre-registered) and c = 2 (descriptive)
    per = []
    keys29 = {"inventory_value_sol": np.array([F[i]["inventory_value_sol"] for i in range(n)], float), "M5": M["M5_team_sold_share"][29],
              "M1": M["M1_ext_buyers"][29], "M2": M["M2_ext_buy_sol"][29], "M7": M["M7_demand_over_inventory"][29], "M8": M["M8_absorption"][29]}
    keys2 = {"M1_c2": M["M1_ext_buyers"][2], "M7_c2": M["M7_demand_over_inventory"][2], "M8_c2": M["M8_absorption"][2], "M5_c2": M["M5_team_sold_share"][2]}
    for g, cnt in Counter(U[rows].tolist()).most_common():
        ii = rows[U[rows] == g]
        G_, B_ = ii[y[ii] == 1], ii[y[ii] == 0]
        if len(G_) >= 3 and len(B_) >= 3:
            per.append({"team": int(g), "good": int(len(G_)), "bad": int(len(B_)),
                        **{k: [float(np.nanmedian(v[G_])), float(np.nanmedian(v[B_]))] for k, v in {**keys29, **keys2}.items()}})
    sign = {}
    for k in keys29:
        wins = sum(1 for p in per if p[k][0] > p[k][1])
        ties = sum(1 for p in per if p[k][0] == p[k][1])
        m_ = len(per) - ties
        sign[k] = {"teams": len(per), "good_higher": wins, "ties": ties, "p_sign": float(binomtest(wins, m_, 0.5).pvalue) if m_ else None}
        TESTS[0] += 1
    out["per_team"] = {"teams": per, "sign_tests_c29": sign}
    out["n_tests_registered"] = TESTS[0]
    A.write_json(os.path.join(A.TABLES, "team_absorption.json"), out)
    A.registre("team_absorption", TESTS[0], "absorption of the team inventory by external demand, pre-registered tests on DISCOVERY + SELECTION (exploratory)",
               {"prereg": PREREG, "prereg_sha256": out["prereg_sha256"]}, n=int((~np.isnan(Y["Y2"])).sum()), declare=False, sortie="tables/team_absorption.json")
    print(json.dumps({"population": out["population"], "n_tests": TESTS[0]}, indent=1))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "check":
        check()
    elif mode == "real":
        real()
    else:
        raise SystemExit("usage: mech_48_absorption.py check|real")


if __name__ == "__main__":
    main()
