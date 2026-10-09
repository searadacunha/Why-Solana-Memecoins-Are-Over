#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ap_mine.py -- mechanical rule generation, selection and hold-out evaluation.

One code path for the real run and for the synthetic controls. Nothing here knows which block it
is allowed to read: the caller passes row indices and a label vector that is NaN outside them.

Rule = conjunction of 1 to 3 atoms from DIFFERENT feature families, never two copies of one
measure (|Spearman| >= COPY_RHO on the DISCOVERY rows, features only).
Atom = feature <= threshold, feature > threshold (thresholds at fixed quantiles of the DISCOVERY
feature distribution, outcome-free) or feature missing (not for features whose missingness is a
documented artefact). A missing value never satisfies <= or >. Atoms with identical firing vectors
over ALL rows are de-duplicated (features only).

DISCOVERY pass (per target), all on DISCOVERY rows only:
  support >= N_MIN_DISC, one-sided 95 % Wilson lower bound of the precision above the base rate,
  precision above the base rate in both time halves (>= N_MIN_HALF fires each),
  for depth 2 and 3: precision >= IMPROVE x the best parent (every sub-rule), in float64,
  fires on >= MIN_DAYS distinct days and >= MIN_CLUSTERS distinct clusters,
  cluster cap (CAP): a cluster contributes at most CAP fires weighted by its own hit rate, and the
  capped lower bound must clear the capped base rate (capped support >= NEFF_MIN_DISC).
  Triple seeds = the TRIPLE_SEEDS best pairs AMONG the pairs that passed everything.
SELECTION (per target), on SELECTION rows only: support >= N_MIN_SEL (capped >= NEFF_MIN_SEL),
  precision above the base rate (raw and capped); rank by the WORSE of the two blocks' one-sided
  90 % Wilson lower bound of the capped precision over the capped base rate (RANK = min); greedy
  de-duplication (Jaccard >= JACCARD_MAX); keep the top K_PER_TARGET.
HOLD-OUT test of one rule on one block: p = max(Fisher exact, cluster bootstrap with the draws
  without a fire counted against the rule, day-stratified Cochran-Mantel-Haenszel). A pass needs
  >= N_MIN_HOLD fires in >= MIN_CLUSTERS clusters on >= MIN_DAYS_HOLD days.
RANK, CAP and the support minima were chosen on synthetic controls only (controles/), before any
SELECTION, VALIDATION or OOS label was read.
"""
from __future__ import annotations

import math
from typing import Any, Optional

import numpy as np
from scipy.stats import fisher_exact, norm, spearmanr

import ap_lib as A

CFG = {
    "QUANTS": (0.2, 0.35, 0.5, 0.65, 0.8),
    "N_MIN_DISC": 25, "N_MIN_HALF": 8, "IMPROVE": 1.10, "MIN_DAYS": 5, "MIN_CLUSTERS": 5,
    "ATOM_MAX_SHARE": 0.95, "TRIPLE_SEEDS": 300, "COPY_RHO": 0.97,
    "N_MIN_SEL": 12, "JACCARD_MAX": 0.5, "K_PER_TARGET": 10, "RANK": "min",
    "CAP": 3.0, "NEFF_MIN_DISC": 12, "NEFF_MIN_SEL": 8,
    "N_MIN_HOLD": 8, "MIN_DAYS_HOLD": 3, "P_VAL": 0.10, "ALPHA_OOS": 0.05, "BOOT": 100000,
}


# ------------------------------------------------------------------------------------ atoms
def prepare_atoms(X: np.ndarray, names: list[str], meta: dict[str, dict], ref_rows: np.ndarray,
                  excluded: set[str], no_missing: set[str] = frozenset(), cfg: dict = CFG
                  ) -> tuple[np.ndarray, list[dict[str, Any]], dict[str, int]]:
    """Boolean matrix (atoms x all rows), atom descriptions, counts. ref_rows = DISCOVERY rows:
    they place the thresholds and drive the support filter. De-duplication over all rows. No outcome."""
    n_ref = len(ref_rows)
    rows_out, desc, seen = [], [], {}
    lo, hi = cfg["N_MIN_DISC"], int(cfg["ATOM_MAX_SHARE"] * n_ref)
    info = {"support_rejected": 0, "duplicates_removed": 0, "missing_atoms": 0, "missing_atoms_skipped": 0}

    def add(vec, d):
        s = int(vec[ref_rows].sum())
        if s < lo or s > hi:
            info["support_rejected"] += 1
            return
        key = vec.tobytes()
        if key in seen:
            info["duplicates_removed"] += 1
            desc[seen[key]].setdefault("twins", []).append("%s %s %s" % (d["feat"], d["op"], d["thr"]))
            return
        seen[key] = len(desc)
        rows_out.append(vec)
        desc.append(d)
        if d["op"] == "missing":
            info["missing_atoms"] += 1

    for j, name in enumerate(names):
        if name in excluded:
            continue
        x = X[:, j].astype(np.float64)
        xr = x[ref_rows]
        ok = ~np.isnan(xr)
        if ok.sum() < 2 * lo:
            continue
        vals = np.unique(xr[ok])
        if len(vals) < 2:
            continue
        fam = meta[name]["family"]
        if len(vals) <= 6:
            thrs = [(None, float((a + b) / 2)) for a, b in zip(vals[:-1], vals[1:])]
        else:
            thrs, last = [], None
            for q in cfg["QUANTS"]:
                v = float(np.quantile(xr[ok], q))
                if v != last:
                    thrs.append((q, v))
                    last = v
        notnan = ~np.isnan(x)
        for q, thr in thrs:
            add(notnan & (x <= thr), {"feat": name, "op": "<=", "thr": thr, "q": q, "family": fam, "col": j})
            add(notnan & (x > thr), {"feat": name, "op": ">", "thr": thr, "q": q, "family": fam, "col": j})
        if name in no_missing:
            info["missing_atoms_skipped"] += 1
        else:
            add(~notnan, {"feat": name, "op": "missing", "thr": None, "q": None, "family": fam, "col": j})
    info["n_atoms"] = len(desc)
    info["n_features"] = len({d["feat"] for d in desc})
    return np.array(rows_out, dtype=bool), desc, info


def allowed_pairs(X: np.ndarray, desc: list[dict[str, Any]], ref_rows: np.ndarray, cfg: dict = CFG
                  ) -> tuple[np.ndarray, int]:
    """Atom pairs that may be combined: different families and not two copies of one measure
    (|Spearman| >= COPY_RHO over the DISCOVERY rows, features only). Returns the mask and the
    number of feature pairs that were forbidden as copies."""
    cols = sorted({d["col"] for d in desc})
    pos = {c: i for i, c in enumerate(cols)}
    import pandas as pd
    Xr = X[np.ix_(ref_rows, cols)].astype(np.float64)
    # pairwise over the rows where both features exist, at least 30 of them; otherwise not a copy
    rho = pd.DataFrame(Xr).corr(method="spearman", min_periods=30).to_numpy()
    rho = np.nan_to_num(rho, nan=0.0)
    copy = np.abs(rho) >= cfg["COPY_RHO"]
    fam_names = sorted({d["family"] for d in desc})
    fam = np.array([fam_names.index(d["family"]) for d in desc])
    ci = np.array([pos[d["col"]] for d in desc])
    cross = fam[:, None] != fam[None, :]
    same_feat = ci[:, None] == ci[None, :]
    copies = copy[np.ix_(ci, ci)] & ~same_feat
    n_forbidden = int(((copy & ~np.eye(len(cols), dtype=bool)).sum()) // 2)
    return cross & ~copies, n_forbidden


def rule_text(rule: tuple[int, ...], desc: list[dict[str, Any]]) -> str:
    parts = []
    for a in rule:
        d = desc[a]
        parts.append("%s is missing" % d["feat"] if d["op"] == "missing" else "%s %s %.6g" % (d["feat"], d["op"], d["thr"]))
    return " AND ".join(parts)


def fire_of(rule: tuple[int, ...], B: np.ndarray) -> np.ndarray:
    v = B[rule[0]].copy()
    for a in rule[1:]:
        v &= B[a]
    return v


def cluster_onehot(cl: np.ndarray) -> np.ndarray:
    ids = np.unique(cl, return_inverse=True)[1]
    K = np.zeros((ids.max() + 1, len(cl)), dtype=np.float32)
    K[ids, np.arange(len(cl))] = 1
    return K


def capped(F: np.ndarray, y: np.ndarray, K: np.ndarray, cap: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cluster-capped support, hits and precision of each rule (rows of F). A cluster contributes
    at most `cap` fires, with its own hit rate: one operator cannot carry a rule alone."""
    Fc = (F @ K.T).astype(np.float64)
    Hc = ((F * y) @ K.T).astype(np.float64)
    w = np.minimum(Fc, cap)
    ne = w.sum(1)
    he = (w * Hc / np.maximum(Fc, 1)).sum(1)
    return ne, he, he / np.maximum(ne, 1e-9)


# ------------------------------------------------------------------------------------ discovery
def mine_disc(B: np.ndarray, desc: list[dict[str, Any]], y: np.ndarray, rows: np.ndarray, days: np.ndarray,
              clusters: np.ndarray, allowed: np.ndarray, cfg: dict = CFG,
              allowed3: Optional[np.ndarray] = None) -> dict[str, Any]:
    """All DISCOVERY-passing rules of depth 1-3 for one target. rows = eligible DISCOVERY rows,
    chronological. Returns the rules with their DISCOVERY statistics and the number evaluated.
    allowed3 (optional): the pair mask used when a third atom extends a seed pair (targeted screens
    may restrict the pairs to a subset while keeping the usual mask for the third atom)."""
    if allowed3 is None:
        allowed3 = allowed
    Bd = B[:, rows].astype(np.float32)
    yd = y[rows].astype(np.float32)
    n = len(rows)
    h = n // 2
    base, base1, base2 = float(yd.mean()), float(yd[:h].mean()), float(yd[h:].mean())
    nmin, nhalf, imp = cfg["N_MIN_DISC"], cfg["N_MIN_HALF"], cfg["IMPROVE"]
    N = len(desc)
    evaluated = {"singles": 0, "pairs": 0, "triples": 0}
    day_ids = np.unique(days[rows], return_inverse=True)[1]
    D = np.zeros((day_ids.max() + 1, n), dtype=np.float32)
    D[day_ids, np.arange(n)] = 1
    K = cluster_onehot(clusters[rows])
    cap = cfg["CAP"]
    base_eff = float(capped(np.ones((1, n), dtype=np.float32), yd, K, cap)[2][0]) if cap else base
    Bb = B[:, rows]

    def passes(C, H, C1, H1, parent_prec=None):
        C, H, C1, H1 = (np.asarray(v, dtype=np.float64) for v in (C, H, C1, H1))
        C2, H2 = C - C1, H - H1
        with np.errstate(divide="ignore", invalid="ignore"):
            prec = H / np.maximum(C, 1)
            ok = (C >= nmin) & (A.wilson_lb_vec(H, C) > base) & (C1 >= nhalf) & (C2 >= nhalf) \
                & (H1 / np.maximum(C1, 1) > base1) & (H2 / np.maximum(C2, 1) > base2)
            if parent_prec is not None:
                ok &= prec >= imp * np.asarray(parent_prec, dtype=np.float64) - 1e-9
        return ok

    def spread_and_cap(rules):
        """Keep the rules that fire on enough days and clusters and clear the capped base rate."""
        kept = []
        for s in range(0, len(rules), 4096):
            chunk = rules[s: s + 4096]
            F = np.array([fire_of(r, Bb) for r, _, _ in chunk], dtype=np.float32)
            nd = ((F @ D.T) > 0).sum(1)
            nk = ((F @ K.T) > 0).sum(1)
            if cap:
                ne, he, pe = capped(F, yd, K, cap)
                lbe = A.wilson_lb_vec(he, ne)
            for q, ((r, cn, hn), a, b2) in enumerate(zip(chunk, nd, nk)):
                if a < cfg["MIN_DAYS"] or b2 < cfg["MIN_CLUSTERS"]:
                    continue
                rec = {"rule": r, "n": int(cn), "hits": int(hn), "prec": hn / cn, "lift": hn / cn / base,
                       "lb": float(A.wilson_lb_vec(np.array([hn]), np.array([cn]))[0]),
                       "days": int(a), "clusters": int(b2)}
                if cap:
                    if ne[q] < cfg["NEFF_MIN_DISC"] or lbe[q] <= base_eff:
                        continue
                    rec.update(n_eff=float(ne[q]), h_eff=float(he[q]), prec_eff=float(pe[q]))
                kept.append(rec)
        return kept

    # singles
    c = Bd.sum(1)
    hs = Bd @ yd
    c1 = Bd[:, :h].sum(1)
    h1 = Bd[:, :h] @ yd[:h]
    evaluated["singles"] = int((c >= nmin).sum())
    prec1 = (hs / np.maximum(c, 1)).astype(np.float64)
    singles = [((int(i),), float(c[i]), float(hs[i])) for i in np.flatnonzero(passes(c, hs, c1, h1))]

    # pairs (allowed = different families and not copies; upper triangle)
    C = Bd @ Bd.T
    H = (Bd * yd) @ Bd.T
    C1 = Bd[:, :h] @ Bd[:, :h].T
    H1 = (Bd[:, :h] * yd[:h]) @ Bd[:, :h].T
    upper = allowed & np.triu(np.ones((N, N), dtype=bool), 1)
    evaluated["pairs"] = int((upper & (C >= nmin)).sum())
    parent = np.maximum(prec1[:, None], prec1[None, :])
    ii, jj = np.nonzero(upper & passes(C, H, C1, H1, parent))
    pairs = [((int(a), int(b2)), float(C[a, b2]), float(H[a, b2])) for a, b2 in zip(ii, jj)]
    kept_singles = spread_and_cap(singles)
    kept_pairs = spread_and_cap(pairs)

    # triples: the best KEPT pairs extended by an atom of a third family, allowed with both
    kept_triples = []
    if kept_pairs:
        order = sorted(range(len(kept_pairs)), key=lambda q: (-kept_pairs[q]["lb"], kept_pairs[q]["rule"]))
        seen3 = set()
        trip = []
        prec_pair = (H / np.maximum(C, 1)).astype(np.float64)
        for q in order[: cfg["TRIPLE_SEEDS"]]:
            a, b2 = kept_pairs[q]["rule"]
            f = Bd[a] * Bd[b2]
            c3 = Bd @ f
            h3 = Bd @ (f * yd)
            c31 = Bd[:, :h] @ f[:h]
            h31 = Bd[:, :h] @ (f[:h] * yd[:h])
            third = allowed3[a] & allowed3[b2]
            evaluated["triples"] += int((third & (c3 >= nmin)).sum())
            par = np.maximum.reduce([np.full(N, prec_pair[a, b2]), prec_pair[a], prec_pair[b2], prec1,
                                     np.full(N, max(prec1[a], prec1[b2]))])
            for k in np.flatnonzero(third & passes(c3, h3, c31, h31, par)):
                rule = tuple(sorted((a, b2, int(k))))
                if rule not in seen3:
                    seen3.add(rule)
                    trip.append((rule, float(c3[k]), float(h3[k])))
        kept_triples = spread_and_cap(trip)
    kept = kept_singles + kept_pairs + kept_triples
    return {"rules": kept, "evaluated": evaluated, "base": base, "base_eff": base_eff, "n": n, "n_atoms": N,
            "passed_before_spread": {"singles": len(singles), "pairs": len(pairs)},
            "passed_by_depth": {1: len(kept_singles), 2: len(kept_pairs), 3: len(kept_triples)}}


# ------------------------------------------------------------------------------------ selection
def select(disc: dict[str, Any], B: np.ndarray, y: np.ndarray, rows_sel: np.ndarray, rows_dedup: np.ndarray,
           clusters: np.ndarray, cfg: dict = CFG) -> dict[str, Any]:
    if cfg["RANK"] not in ("sel", "pooled", "min"):
        raise ValueError("unknown RANK: %r" % cfg["RANK"])
    rules = disc["rules"]
    ys = y[rows_sel].astype(np.float32)
    base = float(ys.mean())
    cap = cfg["CAP"]
    K = cluster_onehot(clusters[rows_sel])
    base_s = float(capped(np.ones((1, len(rows_sel)), dtype=np.float32), ys, K, cap)[2][0]) if cap else base
    base_d = disc["base_eff"]
    Bs = B[:, rows_sel]
    cand = []
    for s in range(0, len(rules), 4096):
        chunk = rules[s: s + 4096]
        F = np.array([fire_of(r["rule"], Bs) for r in chunk], dtype=np.float32)
        ns = F.sum(1).astype(np.float64)
        hs = (F @ ys).astype(np.float64)
        if cap:
            es, gs, _ = capped(F, ys, K, cap)
            ed = np.array([r["n_eff"] for r in chunk])
            gd = np.array([r["h_eff"] for r in chunk])
            n_min = cfg["NEFF_MIN_SEL"]
        else:
            es, gs = ns, hs
            ed = np.array([r["n"] for r in chunk], dtype=float)
            gd = np.array([r["hits"] for r in chunk], dtype=float)
            n_min = cfg["N_MIN_SEL"]
        lb = A.wilson_lb_vec(gs, es, z=1.2816)
        lbd = A.wilson_lb_vec(gd, ed, z=1.2816)
        lbp = A.wilson_lb_vec(gd + gs, ed + es, z=1.2816)
        base_p = (base_d * disc["n"] + base_s * len(rows_sel)) / (disc["n"] + len(rows_sel))
        for q, r in enumerate(chunk):
            if ns[q] < cfg["N_MIN_SEL"] or es[q] < n_min or gs[q] / es[q] <= base_s or hs[q] / ns[q] <= base:
                continue
            if cfg["RANK"] == "sel":
                sc = lb[q] / base_s
            elif cfg["RANK"] == "pooled":
                sc = lbp[q] / base_p
            else:
                sc = min(lbd[q] / base_d, lb[q] / base_s)
            cand.append({**r, "sel_n": int(ns[q]), "sel_hits": int(hs[q]), "sel_prec": float(hs[q] / ns[q]),
                         "sel_lift": float(hs[q] / ns[q] / base) if base > 0 else None,
                         "sel_n_eff": float(es[q]), "sel_prec_eff": float(gs[q] / es[q]),
                         "sel_score": float(sc) if base > 0 else 0.0})
    cand.sort(key=lambda r: (-r["sel_score"], len(r["rule"]), -r["lb"], r["rule"]))
    Bd = B[:, rows_dedup]
    kept, fires = [], []
    for r in cand:
        f = fire_of(r["rule"], Bd)
        dup = False
        for g in fires:
            inter = int((f & g).sum())
            union = int((f | g).sum())
            if union and inter / union >= cfg["JACCARD_MAX"]:
                dup = True
                break
        if not dup:
            kept.append(r)
            fires.append(f)
            if len(kept) >= cfg["K_PER_TARGET"]:
                break
    return {"kept": kept, "n_passing_selection": len(cand), "n_from_discovery": len(rules), "base": base,
            "base_eff": base_s, "n": int(len(rows_sel))}


# ------------------------------------------------------------------------------------ composite
def composite(X: np.ndarray, cols_ok: np.ndarray, y: np.ndarray, rows_disc: np.ndarray, rows_sel_elig: np.ndarray,
              seed: int = 0) -> Optional[dict[str, Any]]:
    """Gradient-boosted trees of depth 3 (they model interactions), fit on DISCOVERY only. The rule
    is 'score >= the 85th percentile of the SELECTION scores'. Returned with its firing vector."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    yd = y[rows_disc]
    if yd.sum() < 10 or (1 - yd).sum() < 10:
        return None
    m = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150, min_samples_leaf=15,
                                       l2_regularization=1.0, random_state=seed)
    m.fit(X[np.ix_(rows_disc, cols_ok)], yd.astype(int))
    score = m.predict_proba(X[:, cols_ok])[:, 1]
    thr = float(np.quantile(score[rows_sel_elig], 0.85))
    return {"fire": score >= thr, "thr": thr, "score": score}


# ------------------------------------------------------------------------------------ tests
def strat_test(f: np.ndarray, y: np.ndarray, strata: np.ndarray) -> dict[str, Any]:
    """Cochran-Mantel-Haenszel one-sided test and Mantel-Haenszel rate ratio of P(y | rule) over
    P(y | rest), stratified (days, or blocks). Strata without both arms contribute nothing."""
    T = E = V = num = den = 0.0
    used = 0
    for s in np.unique(strata):
        m = strata == s
        fs, ys = f[m], y[m]
        n1, n0 = int(fs.sum()), int((~fs).sum())
        if n1 == 0 or n0 == 0:
            continue
        a, cc = float(ys[fs].sum()), float(ys[~fs].sum())
        Nk, m1 = n1 + n0, a + cc
        T += a
        E += n1 * m1 / Nk
        if Nk > 1:
            V += n1 * n0 * m1 * (Nk - m1) / (Nk * Nk * (Nk - 1))
        num += a * n0 / Nk
        den += cc * n1 / Nk
        used += 1
    if used == 0 or V <= 0:
        return {"p_cmh": 1.0, "mh_rr": None, "strata_used": used}
    z = (T - E) / math.sqrt(V)
    return {"p_cmh": float(norm.sf(z)), "mh_rr": (num / den if den > 0 else None), "strata_used": used, "z": float(z)}


def evaluate(fire: np.ndarray, y: np.ndarray, rows_elig: np.ndarray, rows_all: np.ndarray, clusters: np.ndarray,
             days: np.ndarray, net: Optional[np.ndarray] = None, cfg: dict = CFG, seed: int = 20261005
             ) -> dict[str, Any]:
    """Statistics of one rule on one block. p = max(Fisher, cluster bootstrap, day-stratified CMH)."""
    f = fire[rows_elig]
    yy = y[rows_elig]
    n, hits = int(f.sum()), int(yy[f].sum())
    n0, hits0 = int((~f).sum()), int(yy[~f].sum())
    base = float(yy.mean())
    out: dict[str, Any] = {"n_block": int(len(rows_elig)), "n_fire": n, "hits": hits, "base": base,
                           "fire_share_all_alerts": float(fire[rows_all].mean()),
                           "n_fire_all_alerts": int(fire[rows_all].sum()),
                           "n_clusters_fire": int(len(set(clusters[rows_elig][f]))),
                           "n_days_fire": int(len(set(days[rows_elig][f]))),
                           "n_days_block": int(len(set(days[rows_elig])))}
    if n == 0 or n0 == 0:
        out.update(prec=None, lift=None, p=1.0)
        return out
    prec, prec0 = hits / n, hits0 / n0
    lo, hi = A.wilson(hits, n)
    out.update(prec=prec, prec_ci=[lo, hi], prec_rest=prec0, lift=(prec / base if base > 0 else None),
               recall=(hits / (hits + hits0) if hits + hits0 else None),
               odds_ratio=((hits + 0.5) * (n0 - hits0 + 0.5)) / ((n - hits + 0.5) * (hits0 + 0.5)))
    p_f = float(fisher_exact([[hits, n - hits], [hits0, n0 - hits0]], alternative="greater")[1])
    # cluster bootstrap of precision(rule) - precision(rest); draws without a fire count AGAINST the rule
    cl = np.unique(clusters[rows_elig], return_inverse=True)[1]
    K = cl.max() + 1
    S = np.zeros((K, 4))
    np.add.at(S[:, 0], cl, f.astype(float))
    np.add.at(S[:, 1], cl, f * yy)
    np.add.at(S[:, 2], cl, (~f).astype(float))
    np.add.at(S[:, 3], cl, (~f) * yy)
    rng = np.random.default_rng(seed)
    boot = cfg["BOOT"]
    le0 = 0
    dsum = []
    for s in range(0, boot, 10000):
        m = min(10000, boot - s)
        T = S[rng.integers(0, K, size=(m, K))].sum(1)
        good = (T[:, 0] > 0) & (T[:, 2] > 0)
        d = T[good, 1] / T[good, 0] - T[good, 3] / T[good, 2]
        le0 += int((d <= 0).sum()) + int((~good).sum())
        dsum.append(d)
    d = np.sort(np.concatenate(dsum))
    p_b = float((le0 + 1) / (boot + 1))
    if len(d) >= boot // 2:
        lo_d, hi_d = float(d[int(0.025 * (len(d) - 1))]), float(d[int(0.975 * (len(d) - 1))])
    else:
        lo_d = hi_d = None
    st = strat_test(f, yy, days[rows_elig])
    out.update(diff=prec - prec0, diff_ci=[lo_d, hi_d], p_fisher=p_f, p_boot=p_b, p_boot_floor=bool(p_b <= 1.5 / (boot + 1)),
               p_day=st["p_cmh"], mh_rr_day=st["mh_rr"], days_used=st["strata_used"],
               p=max(p_f, p_b, st["p_cmh"]))
    if net is not None:
        out.update(net_stats(f, net[rows_elig], cl, cfg["BOOT"], seed + 1))
    return out


def net_stats(f: np.ndarray, nn: np.ndarray, cl: np.ndarray, boot: int, seed: int) -> dict[str, Any]:
    """Mean net return of the trades taken by a rule, with cluster-bootstrap bounds."""
    out: dict[str, Any] = {}
    m1 = f & ~np.isnan(nn)
    out["net_n"] = int(m1.sum())
    out["net_censored"] = int((f & np.isnan(nn)).sum())
    allm = ~np.isnan(nn)
    out["net_mean_all_alerts"] = float(nn[allm].mean()) if allm.sum() else None
    if m1.sum():
        v = nn[m1]
        out["net_mean"] = float(v.mean())
        out["net_median"] = float(np.median(v))
        out["net_win_share"] = float((v > 0).mean())
        c = np.unique(cl[m1], return_inverse=True)[1]
        K = c.max() + 1
        out["net_clusters"] = int(K)
        if K >= 5:
            S = np.zeros((K, 2))
            np.add.at(S[:, 0], c, v)
            np.add.at(S[:, 1], c, 1.0)
            rng = np.random.default_rng(seed)
            mm = []
            for s in range(0, boot, 10000):
                T = S[rng.integers(0, K, size=(min(10000, boot - s), K))].sum(1)
                mm.append(T[:, 0] / T[:, 1])
            mm = np.sort(np.concatenate(mm))
            out["net_ci"] = [float(mm[int(0.025 * (boot - 1))]), float(mm[int(0.975 * (boot - 1))])]
            out["net_lb99"] = float(mm[int(0.01 * (boot - 1))])
        else:
            out["net_ci"] = None
            out["net_lb99"] = None
    return out


def val_pass(ev: dict[str, Any], cfg: dict = CFG) -> bool:
    return bool(ev["n_fire"] >= cfg["N_MIN_HOLD"] and ev.get("prec") is not None and ev["prec"] > ev["base"]
                and ev["p"] <= cfg["P_VAL"] and ev["n_clusters_fire"] >= cfg["MIN_CLUSTERS"]
                and ev["n_days_fire"] >= cfg["MIN_DAYS_HOLD"])


def oos_decide(evs: list[dict[str, Any]], cfg: dict = CFG) -> list[bool]:
    """Holm over the VALIDATION survivors, one-sided alpha, plus support, cluster and day minima."""
    if not evs:
        return []
    adj = A.holm([e["p"] for e in evs])
    for e, a in zip(evs, adj):
        e["p_holm"] = a
    return [bool(e["n_fire"] >= cfg["N_MIN_HOLD"] and e.get("prec") is not None and e["prec"] > e["base"]
                 and a <= cfg["ALPHA_OOS"] and e["n_clusters_fire"] >= cfg["MIN_CLUSTERS"]
                 and e["n_days_fire"] >= cfg["MIN_DAYS_HOLD"]) for e, a in zip(evs, adj)]


def tier(val_pass_: bool, oos_pass_: bool, oos_ev: dict[str, Any], lifts: list[Optional[float]],
         hold_p: Optional[float], leak: bool = False) -> str:
    """Ordered decision list of PLAN.md section 10 (without the exploitable criteria)."""
    if leak:
        return "REJECTED"
    if val_pass_ and oos_pass_:
        return "OOS SURVIVOR"
    if val_pass_ and oos_ev.get("prec") is not None and oos_ev["prec"] > oos_ev["base"]:
        return "INTERESTING"
    if (not val_pass_) and all(x is not None and x > 1 for x in lifts) and hold_p is not None and hold_p <= 0.05:
        return "INTERESTING"
    return "REJECTED"


# ------------------------------------------------------------------------------------ chain (real run and controls)
def build_candidates(X: np.ndarray, names: list[str], excluded: set[str], B: np.ndarray, desc: list[dict[str, Any]],
                     allowed: np.ndarray, Y: dict[str, np.ndarray], elig: np.ndarray, blocks: np.ndarray,
                     days: np.ndarray, clusters: np.ndarray, with_composite: bool = True, cfg: dict = CFG,
                     keep_disc: Optional[dict[str, Any]] = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """DISCOVERY + SELECTION for every target. Y may hold labels of later blocks (controls); only
    DISCOVERY and SELECTION rows are ever indexed here."""
    r_disc = np.flatnonzero(elig & (blocks == "DISC"))
    r_sel = np.flatnonzero(elig & (blocks == "SEL"))
    r_dedup = np.flatnonzero((blocks == "DISC") | (blocks == "SEL"))
    cols_ok = np.array([j for j, nme in enumerate(names) if nme not in excluded])
    cands, info = [], {}
    for tg in Y:
        y = Y[tg]
        disc = mine_disc(B, desc, y, r_disc, days, clusters, allowed, cfg)
        if keep_disc is not None:
            keep_disc[tg] = disc
        sel = select(disc, B, y, r_sel, r_dedup, clusters, cfg)
        info[tg] = {"disc_base": disc["base"], "disc_n": disc["n"], "evaluated": disc["evaluated"],
                    "disc_passed": len(disc["rules"]), "disc_passed_by_depth": disc["passed_by_depth"],
                    "sel_base": sel["base"], "sel_n": sel["n"], "sel_passed": sel["n_passing_selection"],
                    "kept": len(sel["kept"])}
        for rank, r in enumerate(sel["kept"]):
            cands.append({"id": "%s_R%02d" % (tg, rank + 1), "target": tg, "kind": "rule", "rule": list(r["rule"]),
                          "text": rule_text(r["rule"], desc), "depth": len(r["rule"]),
                          "families": sorted({desc[a]["family"] for a in r["rule"]}),
                          "disc": {k: r[k] for k in ("n", "hits", "prec", "lift", "lb", "days", "clusters", "n_eff", "prec_eff") if k in r},
                          "sel": {"n": r["sel_n"], "hits": r["sel_hits"], "prec": r["sel_prec"], "lift": r["sel_lift"],
                                  "n_eff": r["sel_n_eff"], "prec_eff": r["sel_prec_eff"], "score": r["sel_score"]},
                          "fire": fire_of(r["rule"], B)})
        if with_composite:
            comp = composite(X, cols_ok, y, r_disc, r_sel)
            info[tg]["composite"] = "not fitted"
            if comp is not None:
                fs = comp["fire"][r_sel]
                ys = y[r_sel].astype(np.float32)
                n_, h_ = int(fs.sum()), int(ys[fs].sum())
                cap = cfg["CAP"]
                if cap:
                    Ks = cluster_onehot(clusters[r_sel])
                    ne, he, pe = capped(fs[None, :].astype(np.float32), ys, Ks, cap)
                    base_s = float(capped(np.ones((1, len(r_sel)), dtype=np.float32), ys, Ks, cap)[2][0])
                    okc = n_ >= cfg["N_MIN_SEL"] and h_ / max(n_, 1) > sel["base"] and ne[0] >= cfg["NEFF_MIN_SEL"] and pe[0] > base_s
                else:
                    okc = n_ >= cfg["N_MIN_SEL"] and h_ / max(n_, 1) > sel["base"]
                info[tg]["composite"] = {"sel_n": n_, "sel_hits": h_, "kept": bool(okc), "thr": comp["thr"]}
                if okc:
                    fd = comp["fire"][r_disc]
                    cands.append({"id": "%s_GBM" % tg, "target": tg, "kind": "composite", "rule": None, "depth": 0,
                                  "text": "gradient-boosted score (depth 3, fit on DISCOVERY) >= %.4f" % comp["thr"],
                                  "families": ["COMPOSITE"],
                                  "disc": {"n": int(fd.sum()), "hits": int(y[r_disc][fd].sum()),
                                           "prec": float(y[r_disc][fd].mean()) if fd.sum() else None,
                                           "note": "in-sample fit, not comparable"},
                                  "sel": {"n": n_, "hits": h_, "prec": h_ / max(n_, 1), "lift": h_ / max(n_, 1) / sel["base"]},
                                  "fire": comp["fire"]})
    return cands, info


def holdout(cands: list[dict[str, Any]], key: str, Y: dict[str, np.ndarray], elig: np.ndarray, blocks: np.ndarray,
            block: str, clusters: np.ndarray, days: np.ndarray, nets: Optional[dict[str, np.ndarray]] = None,
            cfg: dict = CFG) -> None:
    r_el = np.flatnonzero(elig & (blocks == block))
    r_all = np.flatnonzero(blocks == block)
    for c in cands:
        c[key] = evaluate(c["fire"], Y[c["target"]], r_el, r_all, clusters, days,
                          None if nets is None else nets[c["target"]], cfg)


def hold_summary(fire: np.ndarray, y: np.ndarray, elig: np.ndarray, blocks: np.ndarray, days: np.ndarray
                 ) -> dict[str, Any]:
    """Pooled VALIDATION + OOS reading of a rule: lift per block, block-stratified MH rate ratio,
    day-stratified CMH p. Descriptive (both blocks were read once already)."""
    out: dict[str, Any] = {"blocks": {}}
    lifts = []
    for b in A.BLOCKS:
        r = np.flatnonzero(elig & (blocks == b))
        f, yy = fire[r], y[r]
        n = int(f.sum())
        base = float(yy.mean()) if len(r) else None
        prec = float(yy[f].mean()) if n else None
        lift = (prec / base) if (prec is not None and base) else None
        out["blocks"][b] = {"n": n, "hits": int(yy[f].sum()) if n else 0, "prec": prec, "base": base, "lift": lift}
        if b in ("VAL", "OOS"):
            lifts.append(lift)
    hold = np.flatnonzero(elig & ((blocks == "VAL") | (blocks == "OOS")))
    f, yy = fire[hold], y[hold]
    st_block = strat_test(f, yy, blocks[hold])
    st_day = strat_test(f, yy, days[hold])
    out["hold"] = {"n": int(f.sum()), "hits": int(yy[f].sum()), "prec": float(yy[f].mean()) if f.sum() else None,
                   "base": float(yy.mean()), "mh_lift_blocks": st_block["mh_rr"], "p_day": st_day["p_cmh"],
                   "p_block": st_block["p_cmh"], "lifts_val_oos": lifts}
    return out
