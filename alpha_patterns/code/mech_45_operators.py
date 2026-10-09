#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mech_45_operators.py -- forensics of the bundle operators (tables/OPERATOR_FORENSICS_PREREG_2026-10-07.md).

Population: the 1,015 alerts before 2026-09-15 (DISCOVERY + SELECTION). Outcomes from
ap_data.label_arrays('selection'): VALIDATION and OOS are never loaded; their alerts are dropped
from every feature table on reading. Pre-registered tests only; all registered as exploratory.
Output: tables/operator_forensics.json (the report is written by hand from it).
"""
from __future__ import annotations

import json
import math
import os
import time
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import fisher_exact, spearmanr

import ap_data as D
import ap_lib as A

B_PERM = 10000
RNG = np.random.default_rng(20261007)
PREREG = "tables/OPERATOR_FORENSICS_PREREG_2026-10-07.md"
BE = {"Y2": 0.458, "Y3": 0.328}


# ------------------------------------------------------------------------------------ identity
def config_key(tickets):
    return "+".join("%.2f" % x for x in sorted(tickets, reverse=True)) if tickets else None


class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[max(a, b)] = min(a, b)


def load_identity(base):
    """Per launch (index in base): key sets per level. Pre-alert facts only."""
    idx = {b["mint"]: i for i, b in enumerate(base)}
    t = np.array([b["t"] for b in base])
    first_gen_t = {}
    cd = {}
    for r in A.jl(A.CD_TABLE):
        if r["mint"] not in idx:
            continue
        cd[r["mint"]] = r
        for s in r["snipers"] + [r["creator"]]:
            g = s.get("gen_funder")
            if g:
                first_gen_t[g] = min(first_gen_t.get(g, math.inf), r["t"])
    jr = {}
    for r in A.jl(A.JOURNAL):
        if r.get("genre") == "alerte_lancement" and r["mint"] in idx:
            jr[r["mint"]] = r
    keys = [dict() for _ in base]
    info = [dict() for _ in base]
    for m, i in idx.items():
        r, j, ti = cd[m], jr[m], t[i]
        core = [s for s in r["snipers"] if s["role"] == "core"]
        w = {s["wallet"] for s in core}
        wf = {(s["wallet"], s.get("last_funder")) for s in core if s.get("last_funder") and s.get("last_bt") is not None and s["last_bt"] < ti - 1}
        cnt = Counter()
        for s in core:
            cand = set()
            for fk, bk, hk in (("last_funder", "last_bt", "last_funder_hub"), ("gen_funder", "gen_bt", "gen_funder_hub")):
                fu = s.get(fk)
                if not fu or s.get(bk) is None or s[bk] >= ti - 1:
                    continue
                h = s.get(hk)
                if h is True and not first_gen_t.get(fu, math.inf) <= ti:
                    h = None
                if h is not True:
                    cand.add(fu)
            for fu in cand:
                cnt[fu] += 1
        mx = max(cnt.values(), default=0)
        f = {fu for fu, v in cnt.items() if v == mx} if mx >= 2 else set()
        src = Counter(s.get("source") for s in core if s.get("source"))
        tk = j.get("tickets") or j["bloc"].get("tickets")
        ck = config_key(tk)
        nsn = j["bloc"].get("n_snipers")
        tmed = j["bloc"].get("ticket_median")
        grouped = (j["bloc"].get("paquet_max") or 1) >= 2
        coarse = "n%s|t%d|%s" % (nsn, round(tmed) if tmed else -1, "G" if grouped else "S")
        cr = j.get("createur") or (r.get("creator") or {}).get("wallet")
        keys[i] = {"L1": {"w:" + x for x in w}, "L2": {"wf:%s|%s" % x for x in wf}, "L3": {"f:" + x for x in f},
                   "L5": {"k:" + ck} if ck else set(), "C": {"c:" + cr} if cr else set(),
                   "L3b": {"s:" + x for x, c in src.items() if c >= 2}, "L5b": {"b:" + coarse}}
        info[i] = {"wallets": sorted(w), "tickets": tk, "config": ck, "creator": cr, "n_snipers": nsn, "ticket_median": tmed,
                   "grouped": grouped, "funders": sorted(f), "age": j.get("age_alerte_s"), "premium": j.get("entree_sur_operateur")}
    return keys, info


def components(n, keys, levels, pair_min=None):
    """Connected components of launches linked by shared keys of the given levels. pair_min=2 for L4
    (>= 2 shared sniper wallets)."""
    uf = UF(n)
    if pair_min:
        inc = defaultdict(list)
        for i in range(n):
            for k in keys[i]["L1"]:
                inc[k].append(i)
        shared = Counter()
        for lst in inc.values():
            for a in range(len(lst)):
                for b in range(a + 1, len(lst)):
                    shared[(lst[a], lst[b])] += 1
        for (a, b), c in shared.items():
            if c >= pair_min:
                uf.union(a, b)
    else:
        first = {}
        for i in range(n):
            for lv in levels:
                for k in keys[i][lv]:
                    if k in first:
                        uf.union(first[k], i)
                    else:
                        first[k] = i
    return np.array([uf.find(i) for i in range(n)])


# ------------------------------------------------------------------------------------ permutation helpers
def perm_matrix(y, strata, B):
    """B permutations of y within strata (vectorised)."""
    n = len(y)
    order0 = np.argsort(strata, kind="stable")
    srank = np.unique(strata[order0], return_inverse=True)[1].astype(float)
    R = RNG.random((B, n)) + srank[None, :]
    o = np.argsort(R, axis=1)
    ys = y[order0][o]
    Yp = np.empty((B, n))
    Yp[:, order0] = ys
    return Yp


def chi2_groups(Y, G, p):
    """Pearson chi2 groups x outcome for each row of Y (outcome vectors). G = one-hot groups x n."""
    k = Y @ G.T
    nn = G.sum(1)
    return (((k - nn * p) ** 2) / (nn * p * (1 - p))).sum(-1)


def onehot(labels):
    u, inv = np.unique(labels, return_inverse=True)
    G = np.zeros((len(u), len(labels)))
    G[inv, np.arange(len(labels))] = 1
    return G, u


def wilson(k, n, z=1.96):
    return A.wilson(int(k), int(n), z)


def logloss(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot_by_group(vals, grp, B=5000):
    keys = np.unique(grp)
    sums = np.array([vals[grp == k].sum() for k in keys])
    cnts = np.array([(grp == k).sum() for k in keys])
    pick = RNG.integers(0, len(keys), size=(B, len(keys)))
    m = sums[pick].sum(1) / cnts[pick].sum(1)
    m.sort()
    return float(m[int(0.025 * (B - 1))]), float(m[int(0.975 * (B - 1))])


def auc(x, y):
    ok = ~np.isnan(x)
    x, y = x[ok], y[ok]
    if y.sum() == 0 or y.sum() == len(y):
        return None
    from scipy.stats import rankdata
    r = rankdata(x)
    n1 = y.sum()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1)))


# ------------------------------------------------------------------------------------ main
def main() -> None:
    base = [b for b in A.load_base() if b["t"] < A.T_SEL_END]
    n = len(base)
    mints = [b["mint"] for b in base]
    t = np.array([b["t"] for b in base])
    blocks = np.array([b["block"] for b in base])
    day = (t // 86400).astype(int)
    week = ((t - A.utc("2026-08-24 00:00:00")) // (7 * 86400)).astype(int)
    lab = A.load_labels("selection")
    if {r["block"] for r in lab.values()} - {"DISC", "SEL"}:
        raise RuntimeError("a VALIDATION / OOS label was loaded")
    elig = np.zeros(n, bool)
    Y = {tg: np.full(n, np.nan) for tg in ("Y2", "Y3", "Y5")}
    mfe = np.full(n, np.nan)
    net = np.full(n, np.nan)
    for i, m in enumerate(mints):
        r = lab.get(m)
        if r and r.get("fine") and r.get("entry") and r.get("obs_3600"):
            elig[i] = True
            for tg, k in zip(("Y2", "Y3", "Y5"), (2, 3, 5)):
                Y[tg][i] = r["conf_%gx_3600" % k]
            mfe[i] = r["mfe_3600"]
            tr = r["trades"]["tp2_next"]
            if tr["status"] == "ok":
                net[i] = tr["net_500"]
    # premium tercile (rob_80 definition: DISCOVERY reference rows of atoms.json)
    mx = D.load_matrix()
    pos = {m: k for k, m in enumerate(mx["mints"])}
    ref = np.array(json.load(open(os.path.join(A.DERIVED, "atoms.json")))["ref_rows"])
    premX = mx["X"][:, mx["names"].index("p_entry_over_operator")].astype(float)
    q = np.nanquantile(premX[ref], [1 / 3, 2 / 3])
    prem = np.array([premX[pos[m]] for m in mints])
    prem3 = np.where(np.isnan(prem), 3, np.where(prem <= q[0], 0, np.where(prem <= q[1], 1, 2)))
    sw = {r["mint"]: r for r in A.jl(os.path.join(A.DERIVED, "feat_swarm.jsonl.gz")) if r["mint"] in pos and mx["blocks"][pos[r["mint"]]] in ("DISC", "SEL")}
    swarm10 = np.array([sw[m]["swarm_10s"] for m in mints], float)
    swarm5 = np.array([sw[m]["swarm_5s"] for m in mints], float)
    del mx, premX
    keys, info = load_identity(base)
    out = {"population": {"alerts": n, "by_block": dict(Counter(blocks.tolist())), "eligible": int(elig.sum()),
                          "eligible_by_block": {b: int((elig & (blocks == b)).sum()) for b in ("DISC", "SEL")},
                          "base": {tg: float(np.nanmean(Y[tg][elig])) for tg in Y},
                          "base_by_block": {b: {tg: float(np.nanmean(Y[tg][elig & (blocks == b)])) for tg in Y} for b in ("DISC", "SEL")}},
           "prereg_sha256": A.sha256_file(os.path.join(A.STUDY, PREREG))}
    n_tests = 0

    # ---------------- 1. groupings and their defensibility
    grp = {"L1": components(n, keys, ["L1"]), "L2": components(n, keys, ["L2"]), "L3": components(n, keys, ["L3"]),
           "L4": components(n, keys, [], pair_min=2), "L5": components(n, keys, ["L5"]),
           "U": components(n, keys, ["L1", "L3", "L5", "C"]), "L3b": components(n, keys, ["L3b"]), "L5b": components(n, keys, ["L5b"])}
    from sklearn.metrics import adjusted_rand_score
    gstats = {}
    for g, lab_ in grp.items():
        c = Counter(lab_.tolist())
        sizes = np.array(sorted(c.values(), reverse=True))
        ce = Counter(lab_[elig].tolist())
        gstats[g] = {"groups": len(c), "singletons": int((sizes == 1).sum()), "largest": int(sizes[0]),
                     "largest_share": float(sizes[0] / n), "launches_in_groups_ge5": int(sizes[sizes >= 5].sum()),
                     "groups_ge": {m: int(sum(1 for v in ce.values() if v >= m)) for m in (5, 10, 20, 30, 50)},
                     "eligible_in_groups_ge": {m: int(sum(v for v in ce.values() if v >= m)) for m in (5, 10, 20, 30, 50)}}
    ari = {"%s~%s" % (a, b): float(adjusted_rand_score(grp[a], grp[b])) for a in grp for b in grp if a < b}
    # corroboration: among launch pairs sharing key type X, share also sharing Y (vs same-week pairs)
    import scipy.sparse as sp
    inc = {}
    for lv in ("L1", "L3", "L5", "C", "L3b"):
        allk = sorted({k for i in range(n) for k in keys[i][lv]})
        kid = {k: j for j, k in enumerate(allk)}
        rows_, cols_ = [], []
        for i in range(n):
            for k in keys[i][lv]:
                rows_.append(i)
                cols_.append(kid[k])
        M = sp.csr_matrix((np.ones(len(rows_)), (rows_, cols_)), shape=(n, max(1, len(allk))))
        S = (M @ M.T).toarray()
        np.fill_diagonal(S, 0)
        inc[lv] = S
    iu = np.triu_indices(n, 1)
    sameweek = (np.abs(t[:, None] - t[None, :]) <= 7 * 86400)[iu]
    corr = {}
    shares = {lv: inc[lv][iu] > 0 for lv in inc}
    shares["L4"] = inc["L1"][iu] >= 2
    for x in shares:
        corr[x] = {"pairs": int(shares[x].sum())}
        for y in shares:
            if x == y:
                continue
            a = shares[x]
            corr[x]["also_" + y] = float(shares[y][a].mean()) if a.sum() else None
            corr[x]["sameweek_baseline_" + y] = float(shares[y][sameweek & ~a].mean())
    out["groupings"] = {"stats": gstats, "ari": ari, "corroboration": corr}

    # ---------------- 2. group descriptions (U, L5, L1) and chronologies
    def describe(g, min_launches=5):
        res = []
        lab_ = grp[g]
        for gid, cnt in Counter(lab_.tolist()).most_common():
            if cnt < min_launches:
                break
            ii = np.flatnonzero(lab_ == gid)
            ii = ii[np.argsort(t[ii])]
            ws = Counter(w for i in ii for w in info[i]["wallets"])
            ee = ii[elig[ii]]
            seq = "".join(("." if not elig[i] else ("5" if Y["Y5"][i] else "3" if Y["Y3"][i] else "2" if Y["Y2"][i] else "F")) for i in ii)
            jac = []
            for a, b in zip(ii[:-1], ii[1:]):
                wa, wb = set(info[a]["wallets"]), set(info[b]["wallets"])
                jac.append(len(wa & wb) / max(1, len(wa | wb)))
            res.append({"group": int(gid), "launches": int(cnt), "eligible": int(len(ee)),
                        "first": time.strftime("%m-%d %H:%M", time.gmtime(t[ii[0]])), "last": time.strftime("%m-%d %H:%M", time.gmtime(t[ii[-1]])),
                        "active_days": int(len(set(day[ii]))), "launches_per_active_day": float(cnt / len(set(day[ii]))),
                        "wallets": len(ws), "wallets_recurrent": int(sum(1 for v in ws.values() if v >= 2)),
                        "wallet_max_uses": int(max(ws.values())) if ws else 0,
                        "consecutive_jaccard_median": float(np.median(jac)) if jac else None,
                        "funders": len({f for i in ii for f in info[i]["funders"]}), "creators": len({info[i]["creator"] for i in ii}),
                        "configs": len({info[i]["config"] for i in ii}), "top_config": Counter(info[i]["config"] for i in ii).most_common(1)[0],
                        "n_snipers": dict(Counter(info[i]["n_snipers"] for i in ii)), "grouped_share": float(np.mean([info[i]["grouped"] for i in ii])),
                        "ticket_median": float(np.median([info[i]["ticket_median"] for i in ii if info[i]["ticket_median"]])),
                        "age_median": float(np.median([info[i]["age"] for i in ii if info[i]["age"] is not None])) if any(info[i]["age"] is not None for i in ii) else None,
                        "premium_median": float(np.nanmedian(prem[ii])), "swarm10_median": float(np.median(swarm10[ii])), "swarm5_median": float(np.median(swarm5[ii])),
                        "x2": int(np.nansum(Y["Y2"][ee])), "x3": int(np.nansum(Y["Y3"][ee])), "x5": int(np.nansum(Y["Y5"][ee])),
                        "rate_x2": float(np.nanmean(Y["Y2"][ee])) if len(ee) else None, "ci_x2": wilson(np.nansum(Y["Y2"][ee]), len(ee)) if len(ee) else None,
                        "rate_x3": float(np.nanmean(Y["Y3"][ee])) if len(ee) else None, "ci_x3": wilson(np.nansum(Y["Y3"][ee]), len(ee)) if len(ee) else None,
                        "rate_x5": float(np.nanmean(Y["Y5"][ee])) if len(ee) else None,
                        "eligible_disc": int((elig[ii] & (blocks[ii] == "DISC")).sum()), "eligible_sel": int((elig[ii] & (blocks[ii] == "SEL")).sum()),
                        "rate_x2_disc": float(np.nanmean(Y["Y2"][ii[elig[ii] & (blocks[ii] == "DISC")]])) if (elig[ii] & (blocks[ii] == "DISC")).sum() else None,
                        "rate_x2_sel": float(np.nanmean(Y["Y2"][ii[elig[ii] & (blocks[ii] == "SEL")]])) if (elig[ii] & (blocks[ii] == "SEL")).sum() else None,
                        "sequence": seq})
        return res
    out["groups"] = {g: describe(g) for g in ("U", "L5", "L1", "L3", "L4")}
    n_tests += sum(len(v) for v in out["groups"].values())

    # ---------------- 3. heterogeneity between groups
    het = {}
    ie = np.flatnonzero(elig)
    for g in ("L1", "L3", "L4", "L5", "U"):
        het[g] = {}
        for tg in ("Y2", "Y3"):
            het[g][tg] = {}
            for m in (5, 10, 20, 30, 50):
                ce = Counter(grp[g][ie].tolist())
                keep = np.array([ce[x] >= m for x in grp[g][ie]])
                rr = ie[keep]
                if len(set(grp[g][rr])) < 2:
                    het[g][tg][m] = {"groups": len(set(grp[g][rr])), "launches": int(len(rr))}
                    continue
                y = Y[tg][rr]
                p = y.mean()
                G, _ = onehot(grp[g][rr])
                obs = float(chi2_groups(y[None, :], G, p)[0])
                res = {"groups": int(G.shape[0]), "launches": int(len(rr)), "chi2": obs, "df": int(G.shape[0] - 1)}
                for nm, strata in (("global", np.zeros(len(rr), int)), ("within_day", day[rr]), ("within_day_premium", day[rr] * 10 + prem3[rr])):
                    Yp = perm_matrix(y, strata, B_PERM)
                    null = chi2_groups(Yp, G, p)
                    res["p_" + nm] = float((np.sum(null >= obs) + 1) / (B_PERM + 1))
                    res["null_mean_" + nm] = float(null.mean())
                    n_tests += 1
                rates = (G @ y) / G.sum(1)
                ng = G.sum(1)
                res["between_sd_raw"] = float(rates.std())
                res["between_sd_true_mom"] = float(math.sqrt(max(0.0, rates.var() - np.mean(p * (1 - p) / ng))))
                res["groups_ci_excluding_base"] = int(sum(1 for k, nn_ in zip(G @ y, ng) if not (wilson(k, nn_)[0] <= p <= wilson(k, nn_)[1])))
                Yp = perm_matrix(y, np.zeros(len(rr), int), 2000)
                kk = Yp @ G.T
                excl = []
                for row in kk:
                    excl.append(sum(1 for k, nn_ in zip(row, ng) if not (wilson(k, nn_)[0] <= p <= wilson(k, nn_)[1])))
                res["groups_ci_excluding_base_null_mean"] = float(np.mean(excl))
                het[g][tg][m] = res
    out["heterogeneity"] = het

    # ---------------- 4. sequences within groups
    seqres = {}
    for g in ("U", "L5", "L1"):
        ce = Counter(grp[g][ie].tolist())
        gids = [x for x, c in ce.items() if c >= 10]
        rr = np.array([i for i in ie[np.argsort(t[ie])] if grp[g][i] in gids])
        prevs, nexts, p2a, p2b, p2c = [], [], [], [], []
        pos_in = {i: k for k, i in enumerate(rr)}
        for gid in gids:
            ii = [i for i in rr if grp[g][i] == gid]
            for a, b in zip(ii[:-1], ii[1:]):
                prevs.append(pos_in[a])
                nexts.append(pos_in[b])
            for a, b, c in zip(ii[:-2], ii[1:-1], ii[2:]):
                p2a.append(pos_in[a])
                p2b.append(pos_in[b])
                p2c.append(pos_in[c])
        prevs, nexts, p2a, p2b, p2c = map(np.array, (prevs, nexts, p2a, p2b, p2c))
        seqres[g] = {"groups": len(gids), "launches": int(len(rr))}
        for tg in ("Y2", "Y3"):
            y = Y[tg][rr]

            def st(Ym):
                a, b = Ym[:, prevs], Ym[:, nexts]
                pss = (a * b).sum(1) / np.maximum(a.sum(1), 1)
                psf = ((1 - a) * b).sum(1) / np.maximum((1 - a).sum(1), 1)
                ff = (1 - Ym[:, p2a]) * (1 - Ym[:, p2b])
                pff = (ff * Ym[:, p2c]).sum(1) / np.maximum(ff.sum(1), 1)
                pnot = ((1 - ff) * Ym[:, p2c]).sum(1) / np.maximum((1 - ff).sum(1), 1)
                return pss, psf, pff, pnot
            o = [float(v[0]) for v in st(y[None, :])]
            Yp = perm_matrix(y, grp[g][rr], B_PERM)
            nl = st(Yp)
            d_obs, d_null = o[0] - o[1], nl[0] - nl[1]
            f_obs, f_null = o[2] - o[3], nl[2] - nl[3]
            seqres[g][tg] = {"P_S_after_S": o[0], "P_S_after_F": o[1], "P_S_after_FF": o[2], "P_S_not_after_FF": o[3],
                             "pairs": int(len(prevs)), "triples": int(len(p2a)),
                             "p_two_sided_S_vs_F": float((np.sum(np.abs(d_null - d_null.mean()) >= abs(d_obs - d_null.mean())) + 1) / (B_PERM + 1)),
                             "null_mean_diff": float(d_null.mean()),
                             "p_FF_greater": float((np.sum(f_null >= f_obs) + 1) / (B_PERM + 1)), "null_mean_FF_diff": float(f_null.mean())}
            n_tests += 2
    # market serial dependence: previous launch of any group, same day
    order = ie[np.argsort(t[ie])]
    mkt = {}
    for tg in ("Y2", "Y3"):
        y = Y[tg][order]
        a, b = y[:-1], y[1:]
        mkt[tg] = {"P_S_after_S": float((a * b).sum() / a.sum()), "P_S_after_F": float(((1 - a) * b).sum() / (1 - a).sum())}
    seqres["market_previous_launch"] = mkt
    out["sequences"] = seqres

    # ---------------- 5. regimes (weekly heterogeneity within big groups vs market)
    reg = {}
    for g in ("U", "L5"):
        ce = Counter(grp[g][ie].tolist())
        gids = [x for x, c in ce.items() if c >= 20]
        reg[g] = {"groups": len(gids), "per_group": []}
        for tg in ("Y2", "Y3"):
            tot_obs, tot_null = 0.0, np.zeros(B_PERM)
            for gid in gids:
                ii = ie[grp[g][ie] == gid]
                y = Y[tg][ii]
                if y.mean() in (0.0, 1.0) or len(set(week[ii])) < 2:
                    continue
                G, wks = onehot(week[ii])
                obs = float(chi2_groups(y[None, :], G, y.mean())[0])
                nl = chi2_groups(perm_matrix(y, np.zeros(len(ii), int), B_PERM), G, y.mean())
                tot_obs += obs
                tot_null += nl
                if tg == "Y2":
                    reg[g]["per_group"].append({"group": int(gid), "weeks": {int(w): [int(y[week[ii] == w].sum()), int((week[ii] == w).sum())] for w in wks},
                                                "p": float((np.sum(nl >= obs) + 1) / (B_PERM + 1))})
                n_tests += 1
            reg[g][tg] = {"chi2_sum": tot_obs, "p": float((np.sum(tot_null >= tot_obs) + 1) / (B_PERM + 1))}
    for tg in ("Y2", "Y3"):
        y = Y[tg][ie]
        G, wks = onehot(week[ie])
        obs = float(chi2_groups(y[None, :], G, y.mean())[0])
        nl = chi2_groups(perm_matrix(y, np.zeros(len(ie), int), B_PERM), G, y.mean())
        reg.setdefault("market", {})[tg] = {"weeks": {int(w): [int(y[week[ie] == w].sum()), int((week[ie] == w).sum())] for w in wks},
                                            "chi2": obs, "p": float((np.sum(nl >= obs) + 1) / (B_PERM + 1))}
    out["regimes"] = reg

    # ---------------- 6. history -> next launch (causal, incremental union-find)
    def causal(levels):
        order_t = np.argsort(t, kind="stable")
        uf = UF(n)
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
    pred = {}
    # market prediction (causal): resolved eligible launches over the previous 24 h if >= 10, else cumulative
    res_t = t[ie]
    res_y = {tg: Y[tg][ie] for tg in ("Y2", "Y3")}
    pm = {tg: np.full(n, np.nan) for tg in ("Y2", "Y3")}
    for i in range(n):
        ok = res_t + A.RESOLVE_1H <= t[i] - 1
        rec = ok & (res_t >= t[i] - 86400)
        for tg in ("Y2", "Y3"):
            if rec.sum() >= 10:
                pm[tg][i] = res_y[tg][rec].mean()
            elif ok.sum() >= 30:
                pm[tg][i] = res_y[tg][ok].mean()
    finalU = grp["U"]
    for name, lv in (("U", ["L1", "L3", "L5", "C"]), ("L1", ["L1"]), ("L5", ["L5"])):
        hist = causal(lv)
        F = {k: np.full(n, np.nan) for k in ("n_prev", "rate_prev", "last5", "last10", "succ_last10", "days_since_success", "group_24h", "rate_prev_x3")}
        pg = {tg: np.full(n, np.nan) for tg in ("Y2", "Y3")}
        for i in range(n):
            hh = hist[i]
            F["group_24h"][i] = sum(1 for j in hh if t[j] >= t[i] - 86400)
            rs = [j for j in hh if elig[j] and t[j] + A.RESOLVE_1H <= t[i] - 1]
            F["n_prev"][i] = len(rs)
            if rs:
                y2 = Y["Y2"][rs]
                F["rate_prev"][i] = y2.mean()
                F["rate_prev_x3"][i] = Y["Y3"][rs].mean()
                F["last5"][i] = y2[-5:].mean()
                F["last10"][i] = y2[-10:].mean()
                F["succ_last10"][i] = y2[-10:].sum()
                sj = [j for j in rs if Y["Y2"][j] == 1]
                F["days_since_success"][i] = (t[i] - t[sj[-1]]) / 86400 if sj else np.nan
                for tg, rp in (("Y2", y2.sum()), ("Y3", Y["Y3"][rs].sum())):
                    if not np.isnan(pm[tg][i]):
                        pg[tg][i] = (rp + 10 * pm[tg][i]) / (len(rs) + 10)
        P = {"coverage": {b: {m_: int((elig & (blocks == b) & (F["n_prev"] >= m_)).sum()) for m_ in (1, 5, 10, 20)} for b in ("DISC", "SEL")}}
        for bl in ("DISC", "SEL", "ALL"):
            inb = elig & ((blocks == bl) if bl != "ALL" else True)
            P[bl] = {}
            for tg in ("Y2", "Y3"):
                y = Y[tg]
                for m_ in (1, 5, 10):
                    mk = inb & (F["n_prev"] >= m_) & ~np.isnan(pg[tg]) & ~np.isnan(pm[tg])
                    if mk.sum() < 10:
                        continue
                    dl = logloss(y[mk], pm[tg][mk]) - logloss(y[mk], pg[tg][mk])
                    db = (y[mk] - pm[tg][mk]) ** 2 - (y[mk] - pg[tg][mk]) ** 2
                    P[bl]["%s_nprev%d" % (tg, m_)] = {"n": int(mk.sum()), "groups": int(len(set(finalU[mk]))),
                                                      "logloss_market": float(logloss(y[mk], pm[tg][mk]).mean()), "logloss_group": float(logloss(y[mk], pg[tg][mk]).mean()),
                                                      "logloss_gain": float(dl.mean()), "logloss_gain_ci": boot_by_group(dl, finalU[mk]),
                                                      "brier_gain": float(db.mean()), "brier_gain_ci": boot_by_group(db, finalU[mk])}
                    n_tests += 2
                mk = inb & (F["n_prev"] >= 5)
                P[bl]["%s_auc_nprev5" % tg] = {"n": int(mk.sum()), **{k: auc(F[k][mk] if k != "days_since_success" else -F[k][mk], y[mk])
                                                                   for k in ("rate_prev", "last5", "last10", "succ_last10", "days_since_success", "group_24h", "n_prev", "rate_prev_x3")}}
                n_tests += 8
                # HIGH-CONFIDENCE rules
                rp = F["rate_prev"] if tg == "Y2" else F["rate_prev_x3"]
                lb = np.array([A.wilson(int(round(rp[i] * F["n_prev"][i])), int(F["n_prev"][i]), 1.2816)[0] if F["n_prev"][i] >= 10 else np.nan for i in range(n)])
                hc1 = inb & (F["n_prev"] >= 10) & (lb > pm[tg])
                hc2 = inb & (F["n_prev"] >= 10) & (rp >= BE[tg])
                other = inb & (F["n_prev"] >= 10)
                for nm, hc in (("HC1", hc1), ("HC2", hc2)):
                    rest = other & ~hc
                    k1, n1, k0, n0 = int(np.nansum(y[hc])), int(hc.sum()), int(np.nansum(y[rest])), int(rest.sum())
                    rec = {"n": n1, "successes": k1, "rate": (k1 / n1) if n1 else None, "ci": wilson(k1, n1) if n1 else None,
                           "rest_n": n0, "rest_rate": (k0 / n0) if n0 else None, "block_base": float(np.nanmean(y[inb])),
                           "groups": int(len(set(finalU[hc]))), "days": int(len(set(day[hc])))}
                    if n1 and n0:
                        rec["p_fisher"] = float(fisher_exact([[k1, n1 - k1], [k0, n0 - k0]], alternative="greater")[1])
                    if tg == "Y2" and n1:
                        v = net[hc]
                        rec["ev_500"] = float(np.nanmean(v)) if (~np.isnan(v)).sum() else None
                    P[bl]["%s_%s" % (tg, nm)] = rec
                    n_tests += 1
        # calibration bins of the group prediction (Y2, n_prev >= 5)
        mk = elig & (F["n_prev"] >= 5) & ~np.isnan(pg["Y2"])
        bins = [(0, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 1.01)]
        P["calibration_Y2"] = {"%.1f-%.1f" % b: {bl: (lambda mm: {"n": int(mm.sum()), "rate": float(np.nanmean(Y["Y2"][mm])) if mm.sum() else None})(
            mk & (blocks == bl) & (F["rate_prev"] >= b[0]) & (F["rate_prev"] < b[1])) for bl in ("DISC", "SEL")} for b in bins}
        pred[name] = P
    out["history_prediction"] = pred

    # ---------------- 7. portfolio (U groups >= 10 eligible)
    port = []
    ce = Counter(grp["U"][ie].tolist())
    for gid, c in ce.most_common():
        if c < 10:
            break
        ii = ie[grp["U"][ie] == gid]
        ii = ii[np.argsort(t[ii])]
        mf = mfe[ii]
        v = net[ii]
        v = v[~np.isnan(v)]
        cum = np.cumsum(v)
        dd = float(np.max(np.maximum.accumulate(np.concatenate([[0], cum])) - np.concatenate([[0], cum])))

        def streak(arr, cond):
            best = cur = 0
            for x in arr:
                cur = cur + 1 if cond(x) else 0
                best = max(best, cur)
            return best
        port.append({"group": int(gid), "eligible": int(c), "mfe_median": float(np.median(mf)), "mfe_mean": float(np.mean(mf)), "mfe_best": float(np.max(mf)),
                     "mfe_bins": {"<1.5": int((mf < 1.5).sum()), "1.5-2": int(((mf >= 1.5) & (mf < 2)).sum()), "2-3": int(((mf >= 2) & (mf < 3)).sum()),
                                  "3-5": int(((mf >= 3) & (mf < 5)).sum()), "5-10": int(((mf >= 5) & (mf < 10)).sum()), ">=10": int((mf >= 10).sum())},
                     "follower_net_mean": float(v.mean()) if len(v) else None, "follower_net_cum": float(cum[-1]) if len(v) else None,
                     "follower_max_drawdown": dd, "max_losing_streak": streak(v, lambda x: x < 0), "max_winning_streak": streak(v, lambda x: x > 0)})
    out["portfolio"] = port

    # ---------------- 8. operator vs launch: mixed model
    mixed = {}
    try:
        import pandas as pd
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
        df = pd.DataFrame({"y": Y["Y2"][ie], "grp": grp["U"][ie].astype(str), "day": day[ie].astype(str), "prem3": prem3[ie].astype(str)})
        for nm, vc in (("group+day", {"grp": "0 + C(grp)", "day": "0 + C(day)"}), ("group", {"grp": "0 + C(grp)"}), ("day", {"day": "0 + C(day)"})):
            mdl = BinomialBayesMixedGLM.from_formula("y ~ C(prem3)", vc, df)
            r = mdl.fit_vb()
            mixed[nm] = {"vc_names": list(mdl.vcp_names), "sd_mean": [float(np.exp(x)) for x in r.vcp_mean],
                         "fe": dict(zip(mdl.exog_names, [float(x) for x in r.fe_mean]))}
        n_tests += 3
    except Exception as e:  # reported, not hidden
        mixed["error"] = repr(e)
    out["mixed_model"] = mixed

    # ---------------- 9. presence before the move: group rate vs median swarm (U groups >= 10)
    rates, swm, ages = [], [], []
    for gid, c in ce.items():
        if c >= 10:
            ii = np.flatnonzero(grp["U"] == gid)
            ee = ii[elig[ii]]
            rates.append(np.nanmean(Y["Y2"][ee]))
            swm.append(np.median(swarm10[ii]))
            ages.append(np.median([info[i]["age"] for i in ii if info[i]["age"] is not None]))
    out["presence"] = {"groups": len(rates), "spearman_rate_vs_swarm10": float(spearmanr(rates, swm).correlation) if len(rates) > 2 else None,
                       "spearman_rate_vs_age": float(spearmanr(rates, ages).correlation) if len(rates) > 2 else None}
    A.registre("operator_forensics", n_tests, "bundle operator forensics, pre-registered tests on DISCOVERY + SELECTION (exploratory)",
               {"prereg": PREREG, "prereg_sha256": out["prereg_sha256"]}, n=int(elig.sum()), declare=False, sortie="tables/operator_forensics.json")
    A.write_json(os.path.join(A.TABLES, "operator_forensics.json"), out)
    print(json.dumps({"population": out["population"], "groupings": out["groupings"]["stats"]}, indent=1))


if __name__ == "__main__":
    main()
