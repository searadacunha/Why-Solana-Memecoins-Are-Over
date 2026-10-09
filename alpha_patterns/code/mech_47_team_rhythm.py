#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mech_47_team_rhythm.py -- team rhythm and GOOD / BAD inside the same team
(tables/TEAM_RHYTHM_PREREG_2026-10-07.md).

Population: the 1,015 alerts before 2026-09-15 (DISCOVERY + SELECTION). Outcomes only through
ap_lib.load_labels('selection'): VALIDATION and OOS are never loaded. Teams = U groups of
mech_45_operators.py. Two modes:
  controls  synthetic outcomes only (real eligibility, teams, sessions, features), written first:
            controles/team_rhythm_controls.json
  real      the pre-registered tests: tables/team_rhythm.json (the report is written by hand from it)
Everything is registered (registre/tests.jsonl) as exploratory.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import rankdata

import ap_data as D
import ap_lib as A
import mech_45_operators as M

sys.path.insert(0, os.path.join(A.W, "post_detection_forensics", "code"))
import fparse  # noqa: E402,F401  (imported by mech_40.load_window)
from mech_40_break_the_loop import load_window  # noqa: E402

PREREG = "tables/TEAM_RHYTHM_PREREG_2026-10-07.md"
EXT_CACHE = os.path.join(A.DERIVED, "feat_team_rhythm_ext.jsonl.gz")
B_MAIN = 10000
B_SENS = 2000
SESSION_MIN = 90
RESOLVE_SEQ = 4020  # prereg section 3 (S5, S6): t_j + 4 020 s <= t_i - 1
B_CTL = 1000
B_CTL_BLOCK = 500
TESTS = [0]  # outcome-touching comparisons of the current run (registry count)
RNG = np.random.default_rng(20261008)

FEATS = [  # (name, family, source)
    ("n_snipers", "T0", "lv_n_snipers"), ("snipe_sol", "T0", "lv_snipe_sol"), ("ticket_median", "T0", "lv_ticket_median"),
    ("ticket_cv", "T0", "lv_ticket_cv"), ("supply_part", "T0", "lv_supply_part"), ("ntx", "T0", "lv_ntx"),
    ("grouped", "T0", "lv_paquet_max"), ("core_order_rho", "T0", "s0_core_order_rho"), ("creator_buy", "T0", "b_creator_buy_sol"),
    ("wallet_age", "T0", "w_core_log_age_h"), ("new_to_team_share", "T0", None), ("jaccard_prev", "T0", None),
    ("n_last_funders", "T0", None), ("shared_funder_prev", "T0", None), ("fund_to_buy_med_s", "T0", "cd_fund_to_buy_med_s"),
    ("fund_spread_s", "T0", "cd_fund_spread_s"), ("same_config_prev", "T0", None),
    ("log_gap_prev_min", "RY", None), ("rank_in_session", "RY", None), ("team_launches_60m", "RY", None),
    ("swarm_10s", "RE", None), ("swarm_5s", "RE", None), ("recurrent_bots_10s", "RE", None), ("other_team_snipers_buying", "RE", None),
    ("other_slot0_buyers", "RE", "b_other_slot0_buyers"), ("core_exit_share", "RE", "m_core_exit_share"),
    ("age_at_alert_s", "RE", "lv_age_alert_s"), ("entry_premium", "RE", "p_entry_over_operator"),
    ("market_rate_24h", "CX", None), ("alerts_60m", "CX", "lv_n_alerts_prev_60m"), ("candidates_60m", "CX", "lv_n_candidates_prev_60m"),
    ("other_team_launches_30m", "CX", None),
]
FNAMES = [f[0] for f in FEATS]


# ------------------------------------------------------------------------------------ helpers
def perm_matrix(y, strata, B, rng):
    """B permutations of y within strata."""
    n = len(y)
    order0 = np.argsort(strata, kind="stable")
    srank = np.unique(strata[order0], return_inverse=True)[1].astype(float)
    o = np.argsort(rng.random((B, n)) + srank[None, :], axis=1)
    Yp = np.empty((B, n))
    Yp[:, order0] = y[order0][o]
    return Yp


def p_two(obs, null, center=None):
    c = null.mean() if center is None else center
    return float((np.sum(np.abs(null - c) >= abs(obs - c) - 1e-12) + 1) / (len(null) + 1))


def p_upper(obs, null):
    return float((np.sum(null >= obs - 1e-12) + 1) / (len(null) + 1))


def within_auc(x, y, strata, rows, B, rng, big=None):
    """P(x_GOOD > x_BAD) over (GOOD, BAD) pairs of the same stratum; permutation inside strata.
    big: a stratum label whose share of the pairs is reported (pairs weigh n1 x n0 per stratum)."""
    ok = rows[~np.isnan(x[rows])]
    s, yy, xx = strata[ok], y[ok], x[ok]
    keep = np.zeros(len(ok), bool)
    r = np.zeros(len(ok))
    for g in np.unique(s):
        idx = np.flatnonzero(s == g)
        k = yy[idx].sum()
        if 0 < k < len(idx):
            keep[idx] = True
            r[idx] = rankdata(xx[idx])
    if keep.sum() < 4:
        return None
    s, yy, r = s[keep], yy[keep], r[keep]
    n1 = Counter(s[yy == 1].tolist())
    n0 = Counter(s[yy == 0].tolist())
    pairs = sum(n1[g] * n0[g] for g in n1)
    const = sum(n1[g] * (n1[g] + 1) / 2 for g in n1)
    obs = float((yy @ r - const) / pairs)
    res = {"auc": obs, "n": int(len(yy)), "good": int(yy.sum()), "strata": int(len(set(s.tolist()))), "pairs": int(pairs)}
    if big is not None:
        res["share_pairs_largest_group"] = float(n1.get(big, 0) * n0.get(big, 0) / pairs)
    if B:
        null = (perm_matrix(yy, s, B, rng) @ r - const) / pairs
        res["p"] = p_two(obs, null, 0.5)
    return res


def pooled_auc(x, y, rows):
    ok = rows[~np.isnan(x[rows])]
    yy = y[ok]
    if yy.sum() in (0, len(yy)):
        return None
    r = rankdata(x[ok])
    n1 = yy.sum()
    return float((r[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(yy) - n1)))


def cat_within(cat, y, team, rows, B, rng, per_team=True):
    """Categories against the outcome inside teams. Team rate p_g on the rows given (so a call on one
    block uses that block's team rates). per_team=True: sum over (team, category) cells of
    (O - E)^2 / (n p (1 - p)), the per-team Pearson chi2 summed over teams (prereg "chi2 somme sur les
    equipes"); per_team=False: pooled excess per category (CMH-like, directional), used for the binary
    present / absent and changed / same contrasts. Null: permutation of outcomes inside teams.
    Descriptive per-category excess is always pooled over teams."""
    ok = rows[~np.isnan(cat[rows])]
    tm, yy, cc = team[ok], y[ok], cat[ok].astype(int)
    pt = {g: yy[tm == g].mean() for g in np.unique(tm)}
    p = np.array([pt[g] for g in tm])
    inf = (p > 0) & (p < 1)
    ok, tm, yy, cc, p = ok[inf], tm[inf], yy[inf], cc[inf], p[inf]
    if len(ok) < 10:
        return None
    cell = np.unique(np.stack([tm, cc], 1), axis=0, return_inverse=True)[1].ravel() if per_team else np.unique(cc, return_inverse=True)[1]
    G = np.zeros((int(cell.max()) + 1, len(ok)))
    G[cell, np.arange(len(ok))] = 1
    V = G @ (p * (1 - p))
    E = G @ p
    good = V > 0

    def stat(Y):
        d = Y @ G.T - E
        return ((d[..., good] ** 2) / V[good]).sum(-1)
    obs = float(stat(yy[None, :])[0])
    res = {"stat": obs, "n": int(len(ok)), "teams": int(len(set(tm.tolist()))), "cells": int(good.sum()), "per_team": per_team, "categories": {}}
    u, ci = np.unique(cc, return_inverse=True)
    for k, c in enumerate(u):
        m = ci == k
        res["categories"][int(c)] = {"n": int(m.sum()), "good": int(yy[m].sum()), "rate": float(yy[m].mean()),
                                     "expected": float(p[m].mean()), "excess_pts": float((yy[m] - p[m]).mean() * 100)}
    if B:
        null = stat(perm_matrix(yy, tm, B, rng))
        res["p"] = p_upper(obs, null)
        res["null_mean"] = float(null.mean())
    return res


def cat_test(cat, y, team, rows, blocks, rng, per_team, B, B_block):
    """cat_within on ALL (B permutations) and on each block separately (team rates of that block).
    Same sense: per_team -> stat above its null mean in ALL, DISC and SEL; pooled -> the category with the
    largest |excess| in ALL (n >= 10) has an excess of the same sign in DISC and SEL."""
    r = cat_within(cat, y, team, rows, B, rng, per_team)
    if r is None:
        return None
    for b in ("DISC", "SEL"):
        rr = cat_within(cat, y, team, rows[blocks[rows] == b], B_block, rng, per_team)
        r["block_" + b] = None if rr is None else {"n": rr["n"], "stat_minus_null": rr["stat"] - rr["null_mean"], "p": rr["p"],
                                                   "excess_pts": {c: v["excess_pts"] for c, v in rr["categories"].items()},
                                                   "n_by_cat": {c: v["n"] for c, v in rr["categories"].items()}}
    bd, bs = r["block_DISC"], r["block_SEL"]
    if per_team:
        a = r["stat"] - r["null_mean"]
        r["same_sense"] = {"all": a, "disc": bd and bd["stat_minus_null"], "sel": bs and bs["stat_minus_null"],
                           "same": bool(bd and bs and a > 0 and bd["stat_minus_null"] > 0 and bs["stat_minus_null"] > 0)}
    else:
        cats = r["categories"]
        bigc = [c for c in cats if cats[c]["n"] >= 10] or list(cats)
        c = max(bigc, key=lambda c: abs(cats[c]["excess_pts"]))
        d = bd["excess_pts"].get(c) if bd else None
        s = bs["excess_pts"].get(c) if bs else None
        a = cats[c]["excess_pts"]
        r["same_sense"] = {"category": c, "all": a, "disc": d, "sel": s,
                           "same": bool(d is not None and s is not None and a != 0 and np.sign(a) == np.sign(d) == np.sign(s))}
    return r


def diff_within(cond_prev_idx, cur_idx, y, team, rows_all, B, rng, cond_fn, masks=None, min_cell=5):
    """P(G_cur | cond(prev outcomes)) - P(G_cur | not cond). cond_prev_idx: list of index arrays of the
    previous launches (most recent first); cond_fn(list of prev outcome arrays) -> 0/1 array.
    Null: permutation of all eligible outcomes inside teams (prev and cur move together). masks: {block:
    bool array over the tuples}; the block statistic and its null mean use the same permutations.
    Undefined (NaN) when the condition holds for fewer than min_cell tuples or for all but fewer."""
    pos = {i: k for k, i in enumerate(rows_all)}
    cur = np.array([pos[i] for i in cur_idx])
    prevs = [np.array([pos[i] for i in pi]) for pi in cond_prev_idx]
    yy = y[rows_all]

    def st(Y, m=None):
        c = cond_fn([Y[..., p] for p in prevs])
        b = Y[..., cur]
        if m is not None:
            c, b = c[..., m], b[..., m]
        n1, n0 = c.sum(-1), (1 - c).sum(-1)
        a1 = np.where(n1 >= min_cell, (c * b).sum(-1) / np.maximum(n1, 1), np.nan)
        a0 = np.where(n0 >= min_cell, ((1 - c) * b).sum(-1) / np.maximum(n0, 1), np.nan)
        return a1 - a0, a1, a0, n1
    d, a1, a0, nc = st(yy[None, :])
    res = {"diff": float(d[0]), "p_cond": float(a1[0]), "p_not": float(a0[0]), "n_cond": int(nc[0]), "n": int(len(cur))}
    if B:
        Yp = perm_matrix(yy, team[rows_all], B, rng)
        nd = st(Yp)[0]
        res["null_mean"] = float(np.nanmean(nd))
        res["p"] = p_two(float(d[0]), nd[~np.isnan(nd)]) if not np.isnan(d[0]) else None
        for b, m in (masks or {}).items():
            db, _, _, nb = st(yy[None, :], m)
            res["diff_" + b] = None if np.isnan(db[0]) else float(db[0])
            res["n_" + b] = int(m.sum())
            res["n_cond_" + b] = int(nb[0])
            ndb = st(Yp, m)[0]
            res["null_mean_" + b] = float(np.nanmean(ndb)) if (~np.isnan(ndb)).any() else None
    return res


def logloss(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


# ------------------------------------------------------------------------------------ data
def ext_buyers(base, cd):
    """External pre-alert buyers per launch {wallet: first dt}; cached (features only, no outcome)."""
    if os.path.exists(EXT_CACHE):
        rows = {r["mint"]: r["first_dt"] for r in A.jl(EXT_CACHE)}
        if all(b["mint"] in rows for b in base):
            return [rows[b["mint"]] for b in base]
    out, rows = [], []
    for b in base:
        core, cr, slot0 = cd[b["mint"]]
        _, recs, _ = load_window(b["mint"])
        ext = core | ({cr} if cr else set())
        first = {}
        for r in sorted((r for r in recs if r.get("kind") == "buy" and not r.get("err") and r.get("trader")
                         and r["trader"] not in ext and r["slot"] != slot0), key=lambda r: (r["slot"], r.get("bt") or 0)):
            if r.get("bt") is None:
                raise RuntimeError("buy without block time in " + b["mint"])
            first.setdefault(r["trader"], r["bt"] - b["t"])
        first = {w: v for w, v in first.items() if v <= -1}
        out.append(first)
        rows.append({"mint": b["mint"], "first_dt": first})
    A.write_jl(EXT_CACHE, rows)
    return out


def build():
    base = [b for b in A.load_base() if b["t"] < A.T_SEL_END]
    n = len(base)
    mints = [b["mint"] for b in base]
    t = np.array([b["t"] for b in base])
    blocks = np.array([b["block"] for b in base])
    day = (t // 86400).astype(int)
    keys, info = M.load_identity(base)
    U = M.components(n, keys, ["L1", "L3", "L5", "C"])
    L1 = M.components(n, keys, ["L1"])
    cdm = {}
    lastf = [set() for _ in range(n)]
    pos = {m: i for i, m in enumerate(mints)}
    for r in A.jl(A.CD_TABLE):
        if r["mint"] not in pos:
            continue
        i = pos[r["mint"]]
        core = [s for s in r["snipers"] if s["role"] == "core"]
        cdm[r["mint"]] = ({s["wallet"] for s in core}, (r.get("creator") or {}).get("wallet"), r["slot0"])
        lastf[i] = {s["last_funder"] for s in core if s.get("last_funder") and s.get("last_bt") is not None and s["last_bt"] < t[i] - 1}
    if len(cdm) != n:
        raise RuntimeError("cd_table does not cover every launch")
    core = [cdm[m][0] for m in mints]
    ext = ext_buyers(base, cdm)
    mx = D.load_matrix()
    mpos = {m: k for k, m in enumerate(mx["mints"])}
    rowsx = np.array([mpos[m] for m in mints])
    F = np.full((n, len(FEATS)), np.nan)
    for k, (nm, fam, src) in enumerate(FEATS):
        if src:
            F[:, k] = mx["X"][rowsx, mx["names"].index(src)].astype(float)
    F[:, FNAMES.index("grouped")] = np.where(np.isnan(F[:, FNAMES.index("grouped")]), np.nan, (F[:, FNAMES.index("grouped")] >= 2).astype(float))
    sw = {r["mint"]: r for r in A.jl(os.path.join(A.DERIVED, "feat_swarm.jsonl.gz")) if r["mint"] in pos}
    F[:, FNAMES.index("swarm_10s")] = [sw[m]["swarm_10s"] for m in mints]
    F[:, FNAMES.index("swarm_5s")] = [sw[m]["swarm_5s"] for m in mints]
    F[:, FNAMES.index("n_last_funders")] = [len(s) if s else np.nan for s in lastf]
    ref = np.array(json.load(open(os.path.join(A.DERIVED, "atoms.json")))["ref_rows"])
    premX = mx["X"][:, mx["names"].index("p_entry_over_operator")].astype(float)
    q = np.nanquantile(premX[ref], [1 / 3, 2 / 3])
    prem = F[:, FNAMES.index("entry_premium")]
    prem3 = np.where(np.isnan(prem), 3, np.where(prem <= q[0], 0, np.where(prem <= q[1], 1, 2)))
    del mx, premX
    order = np.argsort(t, kind="stable")
    # ---- team sequences (final U, descriptive identity)
    team_prev = {}
    seq = defaultdict(list)
    for i in order:
        team_prev[i] = list(seq[U[i]])
        seq[U[i]].append(i)

    def sessions_of(minutes):
        sid = np.zeros(n, int)
        rank = np.zeros(n, int)
        nxt = 0
        for g, ii in seq.items():
            for k, i in enumerate(ii):
                if k == 0 or t[i] - t[ii[k - 1]] > minutes * 60:
                    nxt += 1
                    rank[i] = 1
                else:
                    rank[i] = rank[ii[k - 1]] + 1
                sid[i] = nxt
        size = Counter(sid.tolist())
        ssize = np.array([size[s] for s in sid])
        rel = np.where(ssize >= 3, np.minimum(2, ((rank - 1) * 3) // np.maximum(ssize, 1)), -1)
        return sid, rank, ssize, rel
    sess = {m_: sessions_of(m_) for m_ in (60, SESSION_MIN, 180)}

    def team_rel(i, prev):
        """History-relative facts of launch i given its team's earlier launches (oldest first)."""
        out = {}
        if not prev:
            return {"new_to_team_share": np.nan, "jaccard_prev": np.nan, "shared_funder_prev": np.nan, "same_config_prev": np.nan,
                    "log_gap_prev_min": np.nan, "rank_in_session": 1, "team_launches_60m": 0, "prev": None}
        j = prev[-1]
        seen = set().union(*(core[k] for k in prev))
        out["new_to_team_share"] = len(core[i] - seen) / max(1, len(core[i]))
        out["jaccard_prev"] = len(core[i] & core[j]) / max(1, len(core[i] | core[j]))
        out["shared_funder_prev"] = float(bool(lastf[i] & lastf[j])) if lastf[i] and lastf[j] else np.nan
        out["same_config_prev"] = float(info[i]["config"] == info[j]["config"]) if info[i]["config"] and info[j]["config"] else np.nan
        out["log_gap_prev_min"] = math.log10(max(t[i] - t[j], 1) / 60)
        r = 1
        for k in range(len(prev) - 1, -1, -1):
            nxt_t = t[prev[k + 1]] if k + 1 < len(prev) else t[i]
            if nxt_t - t[prev[k]] > SESSION_MIN * 60:
                break
            r += 1
        out["rank_in_session"] = r
        out["team_launches_60m"] = sum(1 for k in prev if t[k] >= t[i] - 3600)
        out["prev"] = j
        return out
    for i in range(n):
        rel = team_rel(i, team_prev[i])
        for nm in ("new_to_team_share", "jaccard_prev", "shared_funder_prev", "same_config_prev", "log_gap_prev_min", "rank_in_session", "team_launches_60m"):
            F[i, FNAMES.index(nm)] = rel[nm]
    # ---- causal team histories (incremental union-find, 60 s visibility), as in mech_45
    hist = causal_hist(n, t, keys, ["L1", "L3", "L5", "C"])
    # ---- recurrent bots, other-team snipers, other-team launches (final U and causal versions)
    ext10 = [{w for w, v in e.items() if v <= -10} for e in ext]
    seen_ext = Counter()
    core_launches = defaultdict(list)
    vis = 0
    rb = np.zeros(n)
    ots = np.zeros(n)
    ots_c = np.zeros(n)
    otl = np.zeros(n)
    otl_c = np.zeros(n)
    for i in order:
        while vis < n and t[order[vis]] + 60 <= t[i] - 1:
            j = order[vis]
            seen_ext.update(ext[j].keys())
            for w in core[j]:
                core_launches[w].append(j)
            vis += 1
        rb[i] = sum(1 for w in ext10[i] if seen_ext[w] >= 5)
        hs = set(hist[i])
        ots[i] = sum(1 for w in ext[i] if any(U[j] != U[i] for j in core_launches.get(w, ())))
        ots_c[i] = sum(1 for w in ext[i] if any(j not in hs for j in core_launches.get(w, ())))
        rec = np.flatnonzero((t >= t[i] - 1800) & (t < t[i]))
        otl[i] = sum(1 for j in rec if U[j] != U[i])
        otl_c[i] = sum(1 for j in rec if j not in hs)
    F[:, FNAMES.index("recurrent_bots_10s")] = rb
    F[:, FNAMES.index("other_team_snipers_buying")] = ots
    F[:, FNAMES.index("other_team_launches_30m")] = otl
    # bots: the 10 most frequent external buyers at -10 s (frequency only, no outcome)
    freq = Counter(w for e in ext10 for w in e)
    top_bots = [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]
    return {"base": base, "n": n, "mints": mints, "t": t, "blocks": blocks, "day": day, "keys": keys, "info": info, "U": U, "L1": L1,
            "core": core, "lastf": lastf, "ext": ext, "ext10": ext10, "F": F, "prem3": prem3, "team_prev": team_prev, "seq": seq,
            "sess": sess, "hist": hist, "team_rel": team_rel, "ots_c": ots_c, "otl_c": otl_c, "top_bots": top_bots, "bot_freq": [freq[w] for w in top_bots],
            "order": order}


def causal_hist(n, t, keys, levels):
    order_t = np.argsort(t, kind="stable")
    uf = M.UF(n)
    members = {i: [i] for i in range(n)}
    key_first = {}
    visible = 0
    hist = [None] * n
    for i in order_t:
        while visible < n and t[order_t[visible]] + 60 <= t[i] - 1:
            j = order_t[visible]
            for lv in levels:
                for k in keys[j][lv]:
                    if k in key_first:
                        a, b = uf.find(key_first[k]), uf.find(j)
                        if a != b:
                            if len(members[a]) < len(members[b]):
                                a, b = b, a
                            members[a].extend(members[b])
                            del members[b]
                            uf.p[b] = a
                    else:
                        key_first[k] = j
            visible += 1
        roots = set()
        for lv in levels:
            for k in keys[i][lv]:
                if k in key_first and t[key_first[k]] + 60 <= t[i] - 1:
                    roots.add(uf.find(key_first[k]))
        hist[i] = sorted({j for r in roots for j in members[r]}, key=lambda j: t[j])
    return hist


def market_rate(t, y, elig):
    """p_m of mech_45: resolved eligible launches of the previous 24 h if >= 10, else cumulative if >= 30."""
    ie = np.flatnonzero(elig)
    rt, ry = t[ie], y[ie]
    pm = np.full(len(t), np.nan)
    for i in range(len(t)):
        ok = rt + A.RESOLVE_1H <= t[i] - 1
        rec = ok & (rt >= t[i] - 86400)
        if rec.sum() >= 10:
            pm[i] = ry[rec].mean()
        elif ok.sum() >= 30:
            pm[i] = ry[ok].mean()
    return pm


# ------------------------------------------------------------------------------------ test batteries
def population(S, elig, min_elig=5, ident="U", drop_largest=False):
    lab = S[ident]
    ie = np.flatnonzero(elig)
    ce = Counter(lab[ie].tolist())
    big = max(Counter(S["U"].tolist()).items(), key=lambda kv: kv[1])[0]
    return np.array([i for i in ie if ce[lab[i]] >= min_elig and not (drop_largest and S["U"][i] == big)])


def test4(S, F, y, rows, strata, B, rng, blocks=True, big=None):
    out = {}
    for k, nm in enumerate(FNAMES):
        x = F[:, k]
        r = within_auc(x, y, strata, rows, B, rng, big)
        TESTS[0] += 3 if blocks else 1
        if r is None:
            out[nm] = None
            continue
        if blocks:
            for b in ("DISC", "SEL"):
                rb = rows[S["blocks"][rows] == b]
                rr = within_auc(x, y, strata, rb, 0, rng)
                r["auc_" + b] = rr["auc"] if rr else None
                r["n_" + b] = rr["n"] if rr else 0
            r["pooled_auc"] = pooled_auc(x, y, rows)
            r["same_sense"] = bool(r.get("auc_DISC") is not None and r.get("auc_SEL") is not None
                                   and np.sign(r["auc"] - 0.5) == np.sign(r["auc_DISC"] - 0.5) == np.sign(r["auc_SEL"] - 0.5))
        out[nm] = r
    names = [nm for nm in FNAMES if out[nm] and "p" in out[nm]]
    if names:
        q = A.bh([out[nm]["p"] for nm in names])
        for nm, qq in zip(names, q):
            out[nm]["q_bh"] = qq
            out[nm]["passes"] = bool(qq <= 0.10 and out[nm].get("same_sense"))
    return out


def seq_index(S, elig, rows_set):
    """Previous-launch index arrays inside teams (final U), all launches in the condition eligible."""
    pairs, triples, quads, pairs_sess = [], [], [], []
    sid = S["sess"][SESSION_MIN][0]
    for g, ii in S["seq"].items():
        for k, i in enumerate(ii):
            if i not in rows_set:
                continue
            p = ii[max(0, k - 3):k][::-1]  # most recent first
            if len(p) >= 1 and p[0] in rows_set:
                pairs.append((i, p[0]))
                if sid[p[0]] == sid[i]:
                    pairs_sess.append((i, p[0]))
            if len(p) >= 2 and p[0] in rows_set and p[1] in rows_set:
                triples.append((i, p[0], p[1]))
            if len(p) >= 3 and all(x in rows_set for x in p[:3]):
                quads.append((i, p[0], p[1], p[2]))
    return pairs, pairs_sess, triples, quads


def resolved_index(S, elig, rows_set, k):
    """For each launch: its team's last k RESOLVED eligible launches (prereg: t_j + 4 020 s <= t_i - 1)."""
    t = S["t"]
    out = []
    for g, ii in S["seq"].items():
        for i in ii:
            if i not in rows_set:
                continue
            res = [j for j in ii if t[j] < t[i] and j in rows_set and t[j] + RESOLVE_SEQ <= t[i] - 1]
            if len(res) >= k:
                out.append(tuple([i] + res[::-1][:k]))
    return out


def seq_tests(S, elig, y, rows, B, rng):
    rows_set = set(rows.tolist())
    rows_all = np.array(sorted(rows_set))
    team = S["U"]
    pairs, pairs_sess, triples, quads = seq_index(S, elig, rows_set)
    r1 = resolved_index(S, elig, rows_set, 1)
    r2 = resolved_index(S, elig, rows_set, 2)
    blocks = S["blocks"]
    specs = {
        "S1_after_good_vs_bad": (pairs, lambda P: P[0]),
        "S2_after_good_vs_bad_same_session": (pairs_sess, lambda P: P[0]),
        "S3_after_two_bad": (triples, lambda P: (1 - P[0]) * (1 - P[1])),
        "S4_after_three_bad": (quads, lambda P: (1 - P[0]) * (1 - P[1]) * (1 - P[2])),
        "S5_last_resolved_good": (r1, lambda P: P[0]),
        "S6_last_two_resolved_bad": (r2, lambda P: (1 - P[0]) * (1 - P[1])),
    }
    out = {}
    for nm, (tup, fn) in specs.items():
        if len(tup) < 10:
            out[nm] = {"n": len(tup)}
            continue
        arr = np.array(tup)
        masks = {b: blocks[arr[:, 0]] == b for b in ("DISC", "SEL")}
        res = diff_within([arr[:, c] for c in range(1, arr.shape[1])], arr[:, 0], y, team, rows_all, B, rng, fn, masks)
        TESTS[0] += 3
        ex = [(res.get(k), res.get(m)) for k, m in (("diff", "null_mean"), ("diff_DISC", "null_mean_DISC"), ("diff_SEL", "null_mean_SEL"))]
        dev = [None if a is None or b is None or np.isnan(a) else a - b for a, b in ex]
        res["diff_minus_null"] = dev[0]
        res["diff_minus_null_DISC"], res["diff_minus_null_SEL"] = dev[1], dev[2]
        res["same_sense"] = bool(all(v is not None for v in dev) and dev[0] != 0 and np.sign(dev[0]) == np.sign(dev[1]) == np.sign(dev[2]))
        res["causal"] = nm in ("S5_last_resolved_good", "S6_last_two_resolved_bad")
        out[nm] = res
    return out


def runs_test(S, y, rows, B, rng):
    rows_set = set(rows.tolist())
    rows_all = np.array(sorted(rows_set))
    pos = {i: k for k, i in enumerate(rows_all)}
    adj = []
    for g, ii in S["seq"].items():
        e = [pos[i] for i in ii if i in rows_set]
        adj += list(zip(e[:-1], e[1:]))
    adj = np.array(adj)
    yy = y[rows_all]
    TESTS[0] += 1

    def st(Y):
        return (Y[..., adj[:, 0]] != Y[..., adj[:, 1]]).sum(-1)
    obs = float(st(yy[None, :])[0])
    null = st(perm_matrix(yy, S["U"][rows_all], B, rng)).astype(float)
    return {"changes": obs, "null_mean": float(null.mean()), "adjacent_pairs": int(len(adj)), "p": p_two(obs, null),
            "reading": "fewer changes than null = GOOD clustered in streaks; more = alternation"}


def family_23(S, F, y, elig, rows, rng, B, B_block):
    """Sections 2 and 3 of the prereg: rhythm categories, sequences, one BH over the 17 tests."""
    n, t, U, blocks = S["n"], S["t"], S["U"], S["blocks"]
    sid, rank, ssize, rel = S["sess"][SESSION_MIN]
    ie = np.flatnonzero(elig)
    hour = ((t // 3600) % 24).astype(int)
    g_ = F[:, FNAMES.index("log_gap_prev_min")]
    gapcat = np.where(np.isnan(g_), 0, np.where(10 ** g_ > 90, 1, np.where(10 ** g_ > 30, 2, np.where(10 ** g_ > 15, 3, 4)))).astype(float)
    rk = F[:, FNAMES.index("rank_in_session")]
    rcat = np.where(rk <= 1, 0, np.where(rk <= 3, 1, np.where(rk <= 6, 2, 3))).astype(float)
    relc = np.where(rel >= 0, rel, np.nan).astype(float)
    szc = np.where(ssize <= 1, 0, np.where(ssize <= 3, 1, np.where(ssize <= 9, 2, 3))).astype(float)
    tl = F[:, FNAMES.index("team_launches_60m")]
    tlc = np.where(tl == 0, 0, np.where(tl <= 2, 1, 2)).astype(float)
    rhythm, seqr = {}, {}
    specs = {"R1_hour_6h": (hour // 6, True), "R2_gap_since_previous": (gapcat, True), "R3_rank_in_session": (rcat, True),
             "R4_relative_third_of_session": (relc, False), "R5_session_size": (szc, False), "R6_team_launches_60m": (tlc, True)}
    labels_ = {"R1_hour_6h": ["00-06", "06-12", "12-18", "18-24"], "R2_gap_since_previous": ["first of team", "> 90 min (pause)", "30-90", "15-30", "< 15"],
               "R3_rank_in_session": ["1st", "2-3", "4-6", ">= 7"], "R4_relative_third_of_session": ["start", "middle", "end"],
               "R5_session_size": ["1", "2-3", "4-9", ">= 10"], "R6_team_launches_60m": ["0", "1-2", ">= 3"]}
    for nm, (cat, causal) in specs.items():
        r = cat_test(np.asarray(cat, float), y, U, rows, blocks, rng, True, B, B_block)
        TESTS[0] += 3
        if r:
            r.update({"causal": causal, "identity": "final U", "labels": labels_[nm]})
        rhythm[nm] = r
    r = cat_test((hour // 6).astype(float), y, np.zeros(n, int), ie, blocks, rng, True, B, B_block)
    TESTS[0] += 3
    r.update({"causal": True, "identity": "market", "labels": labels_["R1_hour_6h"]})
    rhythm["R1_hour_market"] = r
    seqr.update(seq_tests(S, elig, y, rows, B, rng))
    for nm, mod in (("S7_rank_mod3", 3), ("S8_rank_mod2", 2)):
        r = cat_test((rk % mod).astype(float), y, U, rows, blocks, rng, True, B, B_block)
        TESTS[0] += 3
        r.update({"causal": True, "identity": "final U"})
        seqr[nm] = r
    r9 = runs_test(S, y, rows, B, rng)
    for b in ("DISC", "SEL"):
        rb = runs_test(S, y, rows[blocks[rows] == b], B_block, rng)
        r9["changes_minus_null_" + b] = rb["changes"] - rb["null_mean"]
    a9 = r9["changes"] - r9["null_mean"]
    r9["same_sense"] = bool(a9 != 0 and np.sign(a9) == np.sign(r9["changes_minus_null_DISC"]) == np.sign(r9["changes_minus_null_SEL"]))
    r9["causal"] = False
    seqr["S9_runs"] = r9
    r10 = cat_test(sid.astype(float), y, U, rows, blocks, rng, True, B, B_block)
    TESTS[0] += 3
    r10 = {k: v for k, v in r10.items() if k != "categories"}
    for b in ("DISC", "SEL"):
        if r10.get("block_" + b):
            r10["block_" + b] = {k: v for k, v in r10["block_" + b].items() if k not in ("excess_pts", "n_by_cat")}
    r10["causal"] = False
    seqr["S10_session_overdispersion"] = r10
    names = [k for k in rhythm if rhythm[k] and rhythm[k].get("p") is not None]
    snames = [k for k in seqr if seqr[k] and seqr[k].get("p") is not None]
    q = A.bh([rhythm[k]["p"] for k in names] + [seqr[k]["p"] for k in snames])
    for k, qq in zip(names + snames, q):
        d = rhythm[k] if k in rhythm else seqr[k]
        ss = d.get("same_sense")
        d["q_bh_sections_2_3"] = qq
        d["passes"] = bool(qq <= 0.10 and (ss["same"] if isinstance(ss, dict) else bool(ss)))
    return rhythm, seqr, len(names) + len(snames)


def controls(S, elig):
    """Synthetic outcomes on the real teams, sessions, eligibility and variables (no real outcome).
    (a) null: team rates drawn at random, outcomes independent inside a team, 200 worlds;
    (b) planted feature: logit + 0.8 per within-team SD of snipe_sol, 50 worlds;
    (c) planted sequence: P(G) + k after a BAD (k = 0.05, 0.10, 0.15, 0.20), 50 worlds each.
    The real decision rules are applied: test 4 (BH over 32, same sense) and sections 2 + 3 (BH over 17,
    same sense). Permutations reduced (B_CTL, B_CTL_BLOCK)."""
    rng = np.random.default_rng(777)
    rows = population(S, elig)
    team = S["U"]
    teams = np.unique(team)
    F = S["F"].copy()
    out = {"population_rows": int(len(rows)), "B": B_CTL, "B_block": B_CTL_BLOCK, "null": [], "planted_feature": [], "planted_sequence": {}}
    k2 = FNAMES.index("snipe_sol")
    z = np.zeros(S["n"])
    for g in teams:
        ii = np.flatnonzero(team == g)
        x = F[ii, k2]
        z[ii] = (x - np.nanmean(x)) / (np.nanstd(x) + 1e-9) if len(ii) > 1 else 0
    t0 = time.time()

    def world(seed, beta=0.0, seq_bump=0.0):
        r = np.random.default_rng(seed)
        pt = {g: 1 / (1 + math.exp(-(math.log(0.275 / 0.725) + 0.6 * r.standard_normal()))) for g in teams}
        y = np.full(S["n"], np.nan)
        for g, ii in S["seq"].items():
            prev = None
            for i in ii:
                lp = math.log(pt[g] / (1 - pt[g])) + beta * z[i]
                p = 1 / (1 + math.exp(-lp)) + (seq_bump if prev == 0 else 0.0)
                yi = float(r.random() < min(max(p, 0.0), 1.0))
                if elig[i]:
                    y[i] = yi
                    prev = yi
                else:
                    prev = None
        return y

    def fam(y):
        rh, sq, _ = family_23(S, F, y, elig, rows, rng, B_CTL, B_CTL_BLOCK)
        d = {**rh, **sq}
        return {k: {"p": v.get("p"), "q": v.get("q_bh_sections_2_3"), "passes": bool(v.get("passes"))} for k, v in d.items() if v}
    TESTS[0] = 0
    for seed in range(200):
        y = world(1000 + seed)
        F[:, FNAMES.index("market_rate_24h")] = market_rate(S["t"], np.nan_to_num(y), elig)
        r4 = test4(S, F, y, rows, team, B_CTL, rng)
        f = fam(y)
        out["null"].append({"t4_passes": [nm for nm in FNAMES if r4[nm] and r4[nm].get("passes")],
                            "t4_min_q": min(r4[nm]["q_bh"] for nm in FNAMES if r4[nm] and "q_bh" in r4[nm]),
                            "f23_passes": [k for k, v in f.items() if v["passes"]], "S1_p": f["S1_after_good_vs_bad"]["p"]})
    for seed in range(50):
        y = world(5000 + seed, beta=0.8)
        F[:, FNAMES.index("market_rate_24h")] = market_rate(S["t"], np.nan_to_num(y), elig)
        r4 = test4(S, F, y, rows, team, B_CTL, rng)
        out["planted_feature"].append({"auc": r4["snipe_sol"]["auc"], "q": r4["snipe_sol"].get("q_bh"), "passes": bool(r4["snipe_sol"].get("passes")),
                                       "other_passes": [nm for nm in FNAMES if nm != "snipe_sol" and r4[nm] and r4[nm].get("passes")]})
    for bump in (0.05, 0.10, 0.15, 0.20):
        lst = []
        for seed in range(50):
            y = world(9000 + int(bump * 1000) + seed, seq_bump=bump)
            f = fam(y)
            s1 = f["S1_after_good_vs_bad"]
            lst.append({"S1_p": s1["p"], "S1_q": s1["q"], "S1_passes": s1["passes"], "other_passes": [k for k, v in f.items() if v["passes"] and k != "S1_after_good_vs_bad"]})
        out["planted_sequence"]["%.2f" % bump] = lst
    nl = out["null"]
    out["summary"] = {
        "null_worlds": len(nl),
        "null_t4_share_any_pass": float(np.mean([len(w["t4_passes"]) > 0 for w in nl])),
        "null_t4_mean_passes": float(np.mean([len(w["t4_passes"]) for w in nl])),
        "null_f23_share_any_pass": float(np.mean([len(w["f23_passes"]) > 0 for w in nl])),
        "null_f23_mean_passes": float(np.mean([len(w["f23_passes"]) for w in nl])),
        "null_S1_p_le_0.05": float(np.mean([w["S1_p"] is not None and w["S1_p"] <= 0.05 for w in nl])),
        "planted_feature_auc_mean": float(np.mean([w["auc"] for w in out["planted_feature"]])),
        "planted_feature_power_rule": float(np.mean([w["passes"] for w in out["planted_feature"]])),
        "planted_feature_other_passes_mean": float(np.mean([len(w["other_passes"]) for w in out["planted_feature"]])),
        "planted_sequence_power_rule": {k: float(np.mean([w["S1_passes"] for w in v])) for k, v in out["planted_sequence"].items()},
        "planted_sequence_power_p05": {k: float(np.mean([w["S1_p"] is not None and w["S1_p"] <= 0.05 for w in v])) for k, v in out["planted_sequence"].items()},
        "seconds": time.time() - t0}
    path = os.path.join(A.CONTROLES, "team_rhythm_controls.json")
    A.write_json(path, out)
    A.registre("team_rhythm_controls", TESTS[0], "team rhythm: synthetic worlds v2 after the blind pre-run audit (null 200, planted feature, planted sequences)",
               {"prereg": PREREG, "prereg_sha256": A.sha256_file(os.path.join(A.STUDY, PREREG))}, n=int(len(rows)),
               donnees="synthetiques", declare=False, sortie="controles/team_rhythm_controls.json")
    print(json.dumps(out["summary"], indent=1))


def real(S):
    rng = RNG
    n, t, blocks, day, U = S["n"], S["t"], S["blocks"], S["day"], S["U"]
    lab = A.load_labels("selection")
    if {r["block"] for r in lab.values()} - {"DISC", "SEL"}:
        raise RuntimeError("a VALIDATION / OOS label was loaded")
    elig = np.zeros(n, bool)
    Y = {tg: np.full(n, np.nan) for tg in ("Y2", "Y3")}
    for i, m in enumerate(S["mints"]):
        r = lab.get(m)
        if r and r.get("fine") and r.get("entry") and r.get("obs_3600"):
            elig[i] = True
            Y["Y2"][i] = r["conf_2x_3600"]
            Y["Y3"][i] = r["conf_3x_3600"]
    if elig.sum() != 612:
        raise RuntimeError("eligible rows %d != 612" % elig.sum())
    y = Y["Y2"]
    F = S["F"]
    pm = market_rate(t, np.nan_to_num(y), elig)
    F[:, FNAMES.index("market_rate_24h")] = pm
    TESTS[0] = 0
    out = {"prereg_sha256": A.sha256_file(os.path.join(A.STUDY, PREREG)),
           "population": {"alerts": n, "eligible": int(elig.sum()), "base_Y2": float(np.nanmean(y[elig])), "base_Y3": float(np.nanmean(Y["Y3"][elig]))}}
    rows = population(S, elig)
    big = max(Counter(U.tolist()).items(), key=lambda kv: kv[1])[0]
    out["population"].update({"within_rows": int(len(rows)), "within_teams": int(len(set(U[rows].tolist()))),
                              "within_rows_by_block": {b: int((blocks[rows] == b).sum()) for b in ("DISC", "SEL")},
                              "within_teams_mixed": int(sum(1 for g in set(U[rows].tolist()) if 0 < np.nansum(y[rows][U[rows] == g]) < (U[rows] == g).sum())),
                              "within_good": int(np.nansum(y[rows])), "largest_group": int(big), "largest_group_rows": int((U[rows] == big).sum())})

    # ---------------- 1. rhythm, descriptive (no outcome needed except the chronology strings)
    sid, rank, ssize, rel = S["sess"][SESSION_MIN]
    gaps_team, gaps_sess, cvs = [], [], []
    team_desc = []
    for g, ii in S["seq"].items():
        if len(ii) < 2:
            continue
        gaps_team += (np.diff(t[ii]) / 60).tolist()
        gs = [(t[b] - t[a]) / 60 for a, b in zip(ii[:-1], ii[1:]) if sid[a] == sid[b]]
        gaps_sess += gs
        if len(gs) >= 3:
            cvs.append(np.std(gs) / np.mean(gs))
        if len(ii) >= 10:
            ss = Counter(sid[ii].tolist())
            durs = [(t[[i for i in ii if sid[i] == s][-1]] - t[[i for i in ii if sid[i] == s][0]]) / 60 for s in ss]
            ee = [i for i in ii if elig[i]]
            hrs = Counter(((t[ii] // 3600) % 24).astype(int).tolist())
            team_desc.append({"team": int(g), "launches": len(ii), "eligible": len(ee), "good": int(np.nansum(y[ee])),
                              "first": time.strftime("%m-%d %H:%M", time.gmtime(t[ii[0]])), "last": time.strftime("%m-%d %H:%M", time.gmtime(t[ii[-1]])),
                              "sessions": len(ss), "session_sizes": sorted(ss.values(), reverse=True),
                              "session_minutes_median": float(np.median(durs)), "gap_in_session_median_min": float(np.median(gs)) if gs else None,
                              "gap_in_session_cv": float(np.std(gs) / np.mean(gs)) if len(gs) >= 3 else None,
                              "launches_per_hour_in_session": float(60 / np.median(gs)) if gs else None,
                              "hours_utc_top3": hrs.most_common(3),
                              "chronology_by_session": " | ".join("".join(("." if not elig[i] else ("3" if Y["Y3"][i] else "2" if y[i] else "F"))
                                                                          for i in ii if sid[i] == s) for s in sorted(ss))})
    md = np.diff(np.sort(t)) / 60
    hour = ((t // 3600) % 24).astype(int)
    out["rhythm_descriptive"] = {
        "gap_team_quantiles_min": dict(zip(("10", "25", "50", "75", "90"), np.quantile(gaps_team, [.1, .25, .5, .75, .9]).round(2).tolist())),
        "gap_team_n": len(gaps_team), "gap_team_share_lt10": float(np.mean(np.array(gaps_team) < 10)), "gap_market_share_lt10": float(np.mean(md < 10)),
        "gap_in_session_n": len(gaps_sess),
        "gap_in_session_quantiles_min": dict(zip(("5", "10", "25", "50", "75", "90", "95"), np.quantile(gaps_sess, [.05, .1, .25, .5, .75, .9, .95]).round(2).tolist())),
        "gap_in_session_cv_pooled": float(np.std(gaps_sess) / np.mean(gaps_sess)), "gap_in_session_cv_team_median": float(np.median(cvs)) if cvs else None,
        "teams_with_cv": len(cvs),
        "sessions": int(len(set(sid.tolist()))), "session_size_counts": dict(sorted(Counter(Counter(sid.tolist()).values()).items())),
        "launches_in_sessions_ge3": int(sum(v for v in Counter(sid.tolist()).values() if v >= 3)),
        "launches_by_hour_utc": dict(sorted(Counter(hour.tolist()).items())),
        "teams_ge10": sorted(team_desc, key=lambda d: -d["launches"])}

    # ---------------- 2 and 3. rhythm vs outcome, sequences (one BH over the 17 tests)
    rhythm, seqr, n_fam = family_23(S, F, y, elig, rows, rng, B_MAIN, B_SENS)
    for m_ in (60, 180):
        sid_, rank_, ssize_, rel_ = S["sess"][m_]
        rc_ = np.where(rank_ <= 1, 0, np.where(rank_ <= 3, 1, np.where(rank_ <= 6, 2, 3))).astype(float)
        rhythm["R3_rank_in_session_sens_%dmin" % m_] = cat_test(rc_, y, U, rows, blocks, rng, True, B_SENS, B_SENS)
        TESTS[0] += 3
    out["rhythm_vs_outcome"] = rhythm
    out["sequences"] = seqr
    out["family_23_tests"] = n_fam

    # ---------------- 4. GOOD vs BAD inside the same team
    t4 = test4(S, F, y, rows, U, B_MAIN, rng, big=big)
    out["within_team"] = t4
    tc = within_auc(t.astype(float), y, U, rows, B_MAIN, rng, big)
    TESTS[0] += 1
    out["within_team_time_negative_control"] = tc
    sens = {}

    def slim(d):
        return {nm: (r and {k: r.get(k) for k in ("auc", "p", "n", "strata", "share_pairs_largest_group")}) for nm, r in d.items()}
    sens["intra_session"] = slim(test4(S, F, y, rows, U * 100000 + sid, B_SENS, rng, blocks=False))
    rows_nl = population(S, elig, drop_largest=True)
    sens["without_largest_group"] = slim(test4(S, F, y, rows_nl, U, B_SENS, rng, blocks=False))
    rows_l1 = population(S, elig, ident="L1")
    sens["strata_L1_variables_U"] = slim(test4(S, F, y, rows_l1, S["L1"], B_SENS, rng, blocks=False))
    sens["target_Y3"] = slim(test4(S, F, Y["Y3"], rows, U, B_SENS, rng, blocks=False))
    out["within_team_sensitivity"] = sens
    prof_vars = ["snipe_sol", "ticket_cv", "jaccard_prev", "fund_to_buy_med_s", "log_gap_prev_min", "rank_in_session", "swarm_10s",
                 "recurrent_bots_10s", "other_team_snipers_buying", "entry_premium", "market_rate_24h"]
    prof = []
    ce = Counter(U[rows].tolist())
    for g, c in ce.most_common(8):
        ii = rows[U[rows] == g]
        gi, bi = ii[y[ii] == 1], ii[y[ii] == 0]
        prof.append({"team": int(g), "eligible": int(c), "good": int(len(gi)),
                     **{v: [float(np.nanmedian(F[gi, FNAMES.index(v)])) if len(gi) else None, float(np.nanmedian(F[bi, FNAMES.index(v)])) if len(bi) else None] for v in prof_vars}})
    out["team_profiles_good_vs_bad_medians"] = prof

    # ---------------- 5. configuration changes
    conf = {}
    prev = np.array([S["team_prev"][i][-1] if S["team_prev"][i] else -1 for i in range(n)])
    has = prev >= 0
    pv = np.where(has, prev, 0)
    nsn = F[:, FNAMES.index("n_snipers")]
    sol = F[:, FNAMES.index("snipe_sol")]
    fd = [frozenset(S["info"][i]["funders"]) for i in range(n)]
    chg = {"C1_config_changed": np.where(np.isnan(F[:, FNAMES.index("same_config_prev")]), np.nan, 1 - F[:, FNAMES.index("same_config_prev")]),
           "C1_wallets_changed_jaccard_lt_0.5": np.where(np.isnan(F[:, FNAMES.index("jaccard_prev")]), np.nan, (F[:, FNAMES.index("jaccard_prev")] < 0.5).astype(float)),
           "C1_dominant_funder_changed": np.array([float(fd[i] != fd[prev[i]]) if prev[i] >= 0 and fd[i] and fd[prev[i]] else np.nan for i in range(n)]),
           "C1_n_snipers_changed": np.where(has, (nsn != nsn[pv]).astype(float), np.nan),
           "C1_sol_changed_gt_5pct": np.where(has, (np.abs(sol - sol[pv]) / np.maximum(sol[pv], 1e-9) > 0.05).astype(float), np.nan)}
    for nm, c in chg.items():
        r = cat_test(c, y, U, rows, blocks, rng, False, B_MAIN, B_SENS)
        TESTS[0] += 3
        if r:
            cc = r["categories"]
            r["diff_changed_minus_same_pts"] = (cc[1]["rate"] - cc[0]["rate"]) * 100 if 1 in cc and 0 in cc else None
            r["excess_changed_pts"] = cc[1]["excess_pts"] if 1 in cc else None
        conf[nm] = r
    cfgs = sorted({str(S["info"][i]["config"]) for i in range(n) if S["info"][i]["config"]})
    cfg_code = {c: k for k, c in enumerate(cfgs)}
    wset = {c: k for k, c in enumerate(sorted({"|".join(sorted(S["core"][i])) for i in range(n)}))}
    fds = {c: k for k, c in enumerate(sorted({"|".join(S["info"][i]["funders"]) for i in range(n) if S["info"][i]["funders"]}))}
    for nm, cat in (("C2_between_configs", np.array([cfg_code[str(S["info"][i]["config"])] if S["info"][i]["config"] else np.nan for i in range(n)], float)),
                    ("C2_between_wallet_sets", np.array([wset["|".join(sorted(S["core"][i]))] for i in range(n)], float)),
                    ("C2_between_dominant_funders", np.array([fds["|".join(S["info"][i]["funders"])] if S["info"][i]["funders"] else np.nan for i in range(n)], float))):
        r = cat_test(cat, y, U, rows, blocks, rng, True, B_MAIN, B_SENS)
        TESTS[0] += 3
        r["categories_n"] = len(r["categories"])
        r["categories_with_ge3"] = sum(1 for v in r["categories"].values() if v["n"] >= 3)
        r["rows_without_category"] = int(np.isnan(cat[rows]).sum())
        r = {k: v for k, v in r.items() if k != "categories"}
        for b in ("DISC", "SEL"):
            if r.get("block_" + b):
                r["block_" + b] = {k: v for k, v in r["block_" + b].items() if k not in ("excess_pts", "n_by_cat")}
        conf[nm] = r
    names = [k for k in conf if conf[k] and conf[k].get("p") is not None]
    q = A.bh([conf[k]["p"] for k in names])
    for k, qq in zip(names, q):
        conf[k]["q_bh"] = qq
        ss = conf[k].get("same_sense")
        conf[k]["passes"] = bool(qq <= 0.10 and ss and ss["same"])
    out["configuration_changes"] = conf

    # ---------------- 6. prediction before the move (causal identity)
    out["prediction"] = predict(S, F, y, elig, pm, rng)

    # ---------------- 7. interaction between teams / environment
    inter = {}
    ie = np.flatnonzero(elig)
    for w in (3600, 1800):
        W = ((np.abs(t[ie][:, None] - t[ie][None, :]) <= w) & (U[ie][:, None] != U[ie][None, :])).astype(float)
        np.fill_diagonal(W, 0)
        has_o = W.sum(1) > 0
        W = W[has_o]
        yy, dd = y[ie], day[ie]
        idx_rows = np.flatnonzero(has_o)
        bl = blocks[ie][idx_rows]

        def corr(Yb, m=None):
            R = (Yb @ W.T) / W.sum(1)
            a = Yb[..., idx_rows]
            if m is not None:
                R, a = R[..., m], a[..., m]
            a = a - a.mean(-1, keepdims=True)
            R = R - R.mean(-1, keepdims=True)
            return (a * R).sum(-1) / np.sqrt((a * a).sum(-1) * (R * R).sum(-1))
        obs = float(corr(yy[None, :])[0])
        res = {"corr": obs, "n": int(has_o.sum()), "mean_others": float(W.sum(1).mean())}
        for nm, strata in (("within_day", dd), ("global", np.zeros(len(ie), int)), ("within_team_day", U[ie] * 100000 + dd)):
            Yp = perm_matrix(yy, strata, B_MAIN, rng)
            nl = corr(Yp)
            res["p_" + nm] = p_two(obs, nl)
            res["null_mean_" + nm] = float(nl.mean())
            TESTS[0] += 1
            if nm == "within_day":
                for b in ("DISC", "SEL"):
                    mb = bl == b
                    res["corr_" + b] = float(corr(yy[None, :], mb)[0])
                    res["null_mean_within_day_" + b] = float(corr(Yp, mb).mean())
                    TESTS[0] += 1
        R = (yy @ W.T) / W.sum(1)
        qs = np.quantile(R, [1 / 3, 2 / 3])
        yr = yy[idx_rows]
        res["rate_by_others_tercile"] = [float(yr[R <= qs[0]].mean()), float(yr[(R > qs[0]) & (R <= qs[1])].mean()), float(yr[R > qs[1]].mean())]
        res["n_by_others_tercile"] = [int((R <= qs[0]).sum()), int(((R > qs[0]) & (R <= qs[1])).sum()), int((R > qs[1]).sum())]
        res["others_tercile_cuts"] = qs.tolist()
        dev = [obs - res["null_mean_within_day"], res["corr_DISC"] - res["null_mean_within_day_DISC"], res["corr_SEL"] - res["null_mean_within_day_SEL"]]
        res["same_sense"] = bool(np.sign(dev[0]) == np.sign(dev[1]) == np.sign(dev[2]) and dev[0] != 0)
        inter["I1_contemporaneous_other_teams_%dmin" % (w // 60)] = res
    bots = {}
    for k, w in enumerate(S["top_bots"]):
        pres = np.array([1.0 if w in S["ext10"][i] else 0.0 for i in range(n)])
        r = cat_test(pres, y, U, rows, blocks, rng, False, B_MAIN, B_SENS)
        TESTS[0] += 3
        if r and 1 in r["categories"] and 0 in r["categories"]:
            r["diff_present_minus_absent_pts"] = (r["categories"][1]["rate"] - r["categories"][0]["rate"]) * 100
        bots["bot%02d" % (k + 1)] = {"wallet_prefix": w[:6], "launches_present_all": S["bot_freq"][k], **(r or {})}
    names = [k for k in bots if bots[k].get("p") is not None]
    q = A.bh([bots[k]["p"] for k in names] + [inter["I1_contemporaneous_other_teams_60min"]["p_within_day"]])
    for k, qq in zip(names + ["I1_contemporaneous_other_teams_60min"], q):
        d = bots[k] if k in bots else inter[k]
        ss = d.get("same_sense")
        d["q_bh_I1_I4"] = qq
        d["passes"] = bool(qq <= 0.10 and (ss["same"] if isinstance(ss, dict) else bool(ss)))
    inter["I4_top_bots"] = bots
    core_team = defaultdict(set)
    for i in range(n):
        for w in S["core"][i]:
            core_team[w].add(int(U[i]))
    pair = defaultdict(list)
    for i in range(n):
        others = {g for w in S["ext"][i] for g in core_team.get(w, ()) if g != U[i]}
        for g in others:
            pair[(int(U[i]), g)].append(i)
    rowsI3 = []
    for (a, b), ii in sorted(pair.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(ii) < 5 or len(rowsI3) >= 10:
            break
        ee = [i for i in ii if elig[i]]
        s_ii = set(ii)
        aa = [i for i in np.flatnonzero((U == a) & elig) if i not in s_ii]
        rowsI3.append({"team_A_launches": a, "team_B_snipers_buy": b, "cooccurrences": len(ii), "eligible": len(ee), "good": int(np.nansum(y[ee])),
                       "A_rate_without_B": float(np.nanmean(y[aa])) if aa else None, "A_n_without_B": len(aa)})
    inter["I3_team_pairs"] = rowsI3
    inter["I3_pairs_ge5"] = int(sum(1 for v in pair.values() if len(v) >= 5))
    inter["launches_with_other_team_sniper_buying"] = int(sum(1 for i in range(n) if any(g != U[i] for w in S["ext"][i] for g in core_team.get(w, ()))))
    out["interaction"] = inter

    # ---------------- 8. variance decomposition
    mixed = {}
    try:
        import warnings
        import pandas as pd
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
        df = pd.DataFrame({"y": y[ie], "team": U[ie].astype(str), "sess": (U[ie] * 100000 + sid[ie]).astype(str), "day": day[ie].astype(str),
                           "prem3": S["prem3"][ie].astype(str)})
        for nm, vc in (("team", {"team": "0 + C(team)"}), ("team+session", {"team": "0 + C(team)", "sess": "0 + C(sess)"}),
                       ("team+session+day", {"team": "0 + C(team)", "sess": "0 + C(sess)", "day": "0 + C(day)"}),
                       ("session+day", {"sess": "0 + C(sess)", "day": "0 + C(day)"}), ("day", {"day": "0 + C(day)"})):
            with warnings.catch_warnings(record=True) as wl:
                warnings.simplefilter("always")
                mdl = BinomialBayesMixedGLM.from_formula("y ~ C(prem3)", vc, df)
                r = mdl.fit_vb()
            mixed[nm] = {"vc_names": list(mdl.vcp_names), "sd_mean": [float(np.exp(x)) for x in r.vcp_mean],
                         "warnings": sorted({str(x.message)[:120] for x in wl})}
            TESTS[0] += 1
    except Exception as e:  # reported, not hidden
        mixed["error"] = repr(e)
    out["variance_decomposition"] = mixed
    out["n_tests_registered"] = TESTS[0]

    A.write_json(os.path.join(A.TABLES, "team_rhythm.json"), out)
    A.registre("team_rhythm", TESTS[0], "team rhythm and within-team GOOD/BAD, pre-registered tests on DISCOVERY + SELECTION (exploratory)",
               {"prereg": PREREG, "prereg_sha256": out["prereg_sha256"]}, n=int(elig.sum()), declare=False, sortie="tables/team_rhythm.json")
    print(json.dumps({"population": out["population"], "n_tests": TESTS[0]}, indent=1))


def predict(S, F, y, elig, pm, rng):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    n, t, blocks, U = S["n"], S["t"], S["blocks"], S["U"]
    hist = S["hist"]
    rows = np.array([i for i in range(n) if elig[i] and len(hist[i]) >= 3])
    t0_dev = ["n_snipers", "snipe_sol", "ticket_median", "ticket_cv", "supply_part", "ntx", "grouped", "core_order_rho", "creator_buy", "wallet_age",
              "n_last_funders", "fund_to_buy_med_s", "fund_spread_s"]
    t0_rel = ["new_to_team_share", "jaccard_prev", "shared_funder_prev", "same_config_prev"]
    ry = ["log_gap_prev_min", "rank_in_session", "team_launches_60m"]
    re_ = ["swarm_10s", "swarm_5s", "recurrent_bots_10s", "other_team_snipers_buying", "other_slot0_buyers", "core_exit_share", "age_at_alert_s", "entry_premium"]
    cx = ["market_rate_24h", "alerts_60m", "candidates_60m", "other_team_launches_30m"]
    X = {}
    for i in rows:
        h = hist[i]
        rel = S["team_rel"](i, h)
        v = {}
        for nm in t0_dev:
            k = FNAMES.index(nm)
            prevv = F[h, k]
            v[nm] = F[i, k] - np.nanmean(prevv) if (~np.isnan(prevv)).any() else np.nan
        for nm in t0_rel + ry:
            v[nm] = rel[nm]
        for nm in re_ + cx:
            v[nm] = F[i, FNAMES.index(nm)]
        v["other_team_snipers_buying"] = S["ots_c"][i]
        v["other_team_launches_30m"] = S["otl_c"][i]
        X[i] = v
    # M1: shrunk team history (as mech_45)
    pg = np.full(n, np.nan)
    for i in rows:
        rs = [j for j in hist[i] if elig[j] and t[j] + A.RESOLVE_1H <= t[i] - 1]
        if not np.isnan(pm[i]):
            pg[i] = (np.nansum(y[rs]) + 10 * pm[i]) / (len(rs) + 10)
    sets = {"M2_T0_RY": t0_dev + t0_rel + ry, "M3_RE": re_, "M4_all": t0_dev + t0_rel + ry + re_ + cx}
    res = {"rows": int(len(rows)), "rows_by_block": {b: int((blocks[rows] == b).sum()) for b in ("DISC", "SEL")},
           "good_by_block": {b: int(np.nansum(y[rows][blocks[rows] == b])) for b in ("DISC", "SEL")}}
    for tr, te in (("DISC", "SEL"), ("SEL", "DISC")):
        rtr, rte = rows[blocks[rows] == tr], rows[blocks[rows] == te]
        ok = rte[~np.isnan(pm[rte])]
        d = {"test_rows": int(len(rte)), "test_rows_with_market": int(len(ok))}
        preds = {"M0_market": pm, "M1_team_history": pg}
        for nm, cols in sets.items():
            Xtr = np.array([[X[i][c] for c in cols] for i in rtr], float)
            Xte = np.array([[X[i][c] for c in cols] for i in rte], float)
            med = np.nanmedian(Xtr, 0)
            med = np.where(np.isnan(med), 0, med)
            Xtr = np.where(np.isnan(Xtr), med, Xtr)
            Xte = np.where(np.isnan(Xte), med, Xte)
            mu, sd = Xtr.mean(0), Xtr.std(0)
            sd = np.where(sd > 0, sd, 1)
            import warnings
            with warnings.catch_warnings(record=True) as wl:
                warnings.simplefilter("always")
                clf = LogisticRegression(C=0.1, max_iter=2000).fit((Xtr - mu) / sd, y[rtr])
            d[nm + "_warnings"] = sorted({str(x.message)[:120] for x in wl})
            p = np.full(n, np.nan)
            p[rte] = clf.predict_proba((Xte - mu) / sd)[:, 1]
            preds[nm] = p
            d[nm + "_coef"] = dict(zip(cols, [round(float(c), 3) for c in clf.coef_[0]]))
        for nm, p in preds.items():
            mk = ok[~np.isnan(p[ok])]
            r = {"n": int(len(mk)), "auc": float(roc_auc_score(y[mk], p[mk])) if 0 < y[mk].sum() < len(mk) else None}
            dl = logloss(y[mk], pm[mk]) - logloss(y[mk], p[mk])
            r["logloss_gain_vs_market"] = float(dl.mean())
            r["logloss_gain_ci"] = M.boot_by_group(dl, U[mk]) if nm != "M0_market" else None
            wa = within_auc(p, y, U, mk, 2000, rng)
            TESTS[0] += 3
            r["within_team_auc"] = wa and {k: wa[k] for k in ("auc", "p", "n", "strata")}
            d[nm] = r
        res["train_%s_test_%s" % (tr, te)] = d
    for nm in ("M1_team_history", "M2_T0_RY", "M3_RE", "M4_all"):
        a, b = res["train_DISC_test_SEL"][nm], res["train_SEL_test_DISC"][nm]
        res[nm + "_announces"] = bool(a["logloss_gain_ci"] and b["logloss_gain_ci"] and a["logloss_gain_ci"][0] > 0 and b["logloss_gain_ci"][0] > 0)
    return res


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("controls", "real"):
        raise SystemExit("usage: mech_47_team_rhythm.py controls|real")
    S = build()
    if mode == "controls":
        lab = A.load_labels("selection")  # structural fields only: no outcome is read here
        elig = np.array([bool(lab.get(m) and lab[m].get("fine") and lab[m].get("entry") and lab[m].get("obs_3600")) for m in S["mints"]])
        if elig.sum() != 612:
            raise RuntimeError("eligible rows %d != 612" % elig.sum())
        del lab
        controls(S, elig)
    else:
        real(S)


if __name__ == "__main__":
    main()
