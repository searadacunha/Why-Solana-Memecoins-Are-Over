#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multivariate search in TRAIN, selection in VALIDATION, then LOCK.

Three targets, fixed before this script ran: >=2x within 5 min, 15 min and
1 h, entry at P0, complete-case. 1 h is the primary target (longest horizon
with >= 75 % coverage); 5 and 15 min are where the univariate screen found
effects that replicated in VALIDATION.

Per target:
  rules     conjunctions of 1 to 3 conditions. Atoms: every continuous feature
            against its TRAIN deciles (<= and >), every categorical level.
            Pairs exhaustive, triples by beam (100 best pairs). Minimum support
            20 TRAIN rows. TRAIN score: Wilson lower bound. Duplicates (same
            TRAIN rows) collapsed. The 50 best TRAIN rules go to VALIDATION;
            the one with the best VALIDATION Wilson lower bound (VAL n >= 30)
            is locked.
  logistic  ridge logistic regression on standardised features (TRAIN
            medians impute missing values), penalty chosen on VALIDATION AUC;
            signal = score above the TRAIN 80th percentile.
  tree      CART, depth 2 or 3 chosen on VALIDATION AUC, leaves >= 20; signal
            = the leaf with the highest TRAIN rate.
Plus three hypotheses specified before this study (not searched here):
  H1 actor == grouped (earlier campaigns: a tail effect at x5),
  H2 market cap at P0 < 60 000 USD, H2b 40 000 <= market cap < 60 000 USD
  (the owner's earlier stratification), all on the primary target.

Every rule, model and threshold evaluated is counted. TEST is not read. The
script ends by writing tables/LOCK.json: the locked signals, the decision
criteria for TEST, the trading and cost parameters. an_60_final_test.py refuses
to run without it.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from typing import Any, Callable, Optional

import pde
from an_30_univariate import CATEGORICAL, CONTINUOUS, label, value

TARGETS = [(2.0, 300), (2.0, 900), (2.0, 3600)]
MIN_SUPPORT = 20
BEAM = 100
TOP_TO_VAL = 50
MIN_VAL_N = 30
LAMBDAS = (0.1, 1.0, 10.0, 100.0)
BUDGET: dict[str, int] = {"atoms": 0, "rules_evaluated": 0, "models_fitted": 0, "thresholds": 0}

Atom = tuple[str, str, Any]      # (feature, op, value) with op in {"<=", ">", "=="}


def atom_true(r: dict[str, Any], a: Atom) -> bool:
    v = value(r, a[0])
    if v is None:
        return False
    if a[1] == "==":
        return v == a[2]
    return float(v) <= a[2] if a[1] == "<=" else float(v) > a[2]


def rule_true(r: dict[str, Any], rule: tuple[Atom, ...]) -> bool:
    return all(atom_true(r, a) for a in rule)


def rule_text(rule: tuple[Atom, ...]) -> str:
    def one(a: Atom) -> str:
        v = a[2]
        if a[0] == "log10_mc_usd" and a[1] != "==":
            return "mc_usd %s %.0f" % (a[1], 10 ** v)
        if a[0] == "log10_p0" and a[1] != "==":
            return "p0 %s %.4g SOL" % (a[1], 10 ** v)
        return "%s %s %s" % (a[0], a[1], ("%.4g" % v) if isinstance(v, float) else v)
    return " AND ".join(one(a) for a in rule)


def lb(k: int, n: int) -> float:
    return pde.wilson(k, n)[0] or 0.0


def build_atoms(train: list[dict[str, Any]]) -> list[Atom]:
    atoms: list[Atom] = []
    for f in CONTINUOUS:
        xs = [float(value(r, f)) for r in train if value(r, f) is not None]
        if len(xs) < 30:
            continue
        th = sorted({pde.quantile(xs, q / 10) for q in range(1, 10)})
        for t in th:
            atoms += [(f, "<=", t), (f, ">", t)]
    for f in CATEGORICAL:
        for lv in sorted({value(r, f) for r in train if value(r, f) is not None}, key=str):
            atoms.append((f, "==", lv))
    return atoms


def mask(rows: list[dict[str, Any]], a: Atom) -> int:
    m = 0
    for i, r in enumerate(rows):
        if atom_true(r, a):
            m |= 1 << i
    return m


def search_rules(train: list[dict[str, Any]], y: list[int], atoms: list[Atom]) -> list[dict[str, Any]]:
    ybits = sum(1 << i for i, b in enumerate(y) if b)
    am = [mask(train, a) for a in atoms]
    found: dict[int, dict[str, Any]] = {}

    def consider(rule: tuple[int, ...], m: int) -> Optional[float]:
        BUDGET["rules_evaluated"] += 1
        n = m.bit_count()
        if n < MIN_SUPPORT:
            return None
        k = (m & ybits).bit_count()
        s = lb(k, n)
        old = found.get(m)
        if old is None or len(rule) < len(old["idx"]):
            found[m] = {"idx": rule, "n": n, "k": k, "lb": s}
        return s

    for i in range(len(atoms)):
        consider((i,), am[i])
    pairs = []
    for i in range(len(atoms)):
        for j in range(i + 1, len(atoms)):
            if atoms[i][0] == atoms[j][0]:
                continue
            m = am[i] & am[j]
            s = consider((i, j), m)
            if s is not None:
                pairs.append((s, (i, j), m))
    pairs.sort(key=lambda z: -z[0])
    for _, (i, j), m in pairs[:BEAM]:
        for q in range(len(atoms)):
            if atoms[q][0] in (atoms[i][0], atoms[j][0]):
                continue
            consider(tuple(sorted((i, j, q))), m & am[q])
    out = []
    for m, d in found.items():
        d["rule"] = tuple(atoms[i] for i in d["idx"])
        d["rate"] = d["k"] / d["n"]
        out.append(d)
    out.sort(key=lambda d: (-d["lb"], -d["n"]))
    return out


# --- ridge logistic regression and a small CART, stdlib -------------------- #
LOGIT_FEATURES = [f for f in CONTINUOUS if f not in ("amorce",)]


def design(rows: list[dict[str, Any]], med: dict[str, float], mu: dict[str, float], sd: dict[str, float]
           ) -> list[list[float]]:
    X = []
    for r in rows:
        x = [1.0]
        for f in LOGIT_FEATURES:
            v = value(r, f)
            v = med[f] if v is None else float(v)
            x.append((v - mu[f]) / sd[f])
        x.append(1.0 if value(r, "actor") == "grouped" else 0.0)
        x.append(1.0 if value(r, "complete_at_block") else 0.0)
        x.append(1.0 if value(r, "p0_source") == "pool" else 0.0)
        x.append(1.0 if r["f"].get("ticket_mean") is None else 0.0)
        X.append(x)
    return X


def solve(A: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        piv = M[c][c]
        if abs(piv) < 1e-12:
            continue
        for r in range(n):
            if r != c and M[r][c]:
                fct = M[r][c] / piv
                for k in range(c, n + 1):
                    M[r][k] -= fct * M[c][k]
    return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]


def fit_logit(X: list[list[float]], y: list[int], lam: float) -> list[float]:
    BUDGET["models_fitted"] += 1
    p = len(X[0])
    beta = [0.0] * p
    for _ in range(50):
        g = [0.0] * p
        H = [[0.0] * p for _ in range(p)]
        for x, t in zip(X, y):
            z = sum(b * v for b, v in zip(beta, x))
            mu = 1 / (1 + math.exp(-max(-35, min(35, z))))
            w = mu * (1 - mu)
            for i in range(p):
                g[i] += (t - mu) * x[i]
                xi = w * x[i]
                for j in range(i, p):
                    H[i][j] += xi * x[j]
        for i in range(p):
            for j in range(i):
                H[i][j] = H[j][i]
            if i:
                g[i] -= lam * beta[i]
                H[i][i] += lam
        step = solve(H, g)
        beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-7:
            break
    return beta


def score(beta: list[float], X: list[list[float]]) -> list[float]:
    return [sum(b * v for b, v in zip(beta, x)) for x in X]


def gini_split(X: list[list[float]], y: list[int], idx: list[int]) -> Optional[tuple[int, float]]:
    best, bg = None, None
    n = len(idx)
    k = sum(y[i] for i in idx)
    parent = 1 - (k / n) ** 2 - (1 - k / n) ** 2
    for j in range(1, len(X[0])):
        vals = sorted({X[i][j] for i in idx})
        if len(vals) < 2:
            continue
        cand = [vals[int(q * (len(vals) - 1) / 10)] for q in range(1, 10)]
        for t in sorted(set(cand)):
            BUDGET["thresholds"] += 1
            L = [i for i in idx if X[i][j] <= t]
            if len(L) < MIN_SUPPORT or n - len(L) < MIN_SUPPORT:
                continue
            kl = sum(y[i] for i in L)
            kr = k - kl
            nl, nr = len(L), n - len(L)
            g = (nl * (1 - (kl / nl) ** 2 - (1 - kl / nl) ** 2) + nr * (1 - (kr / nr) ** 2 - (1 - kr / nr) ** 2)) / n
            if g < parent - 1e-9 and (bg is None or g < bg):
                best, bg = (j, t), g
    return best


def grow(X: list[list[float]], y: list[int], idx: list[int], depth: int, path: tuple = ()) -> list[dict[str, Any]]:
    sp = gini_split(X, y, idx) if depth > 0 else None
    if sp is None:
        return [{"path": path, "n": len(idx), "k": sum(y[i] for i in idx)}]
    j, t = sp
    L = [i for i in idx if X[i][j] <= t]
    R = [i for i in idx if X[i][j] > t]
    return grow(X, y, L, depth - 1, path + ((j, "<=", t),)) + grow(X, y, R, depth - 1, path + ((j, ">", t),))


def in_leaf(x: list[float], path: tuple) -> bool:
    return all((x[j] <= t) if op == "<=" else (x[j] > t) for j, op, t in path)


def colname(j: int) -> str:
    extra = ["actor==grouped", "complete_at_block", "p0_source==pool", "tickets_missing"]
    return "intercept" if j == 0 else (LOGIT_FEATURES[j - 1] if j <= len(LOGIT_FEATURES)
                                       else extra[j - 1 - len(LOGIT_FEATURES)])


def main() -> None:
    dev = pde.read_rows("dataset_dev.jsonl.gz")
    train = [r for r in dev if r["split"] == "train"]
    val = [r for r in dev if r["split"] == "val"]
    locked: list[dict[str, Any]] = []
    doc = ["# T3. Signal search in TRAIN, selection in VALIDATION (TEST sealed)", "",
           "Regenerate: `python3 post_detection_edge/code/an_40_signals.py`. Rates are complete-case "
           "(observed windows), entry at P0 (spot). Wilson 95 % intervals. A rule's N is the number of "
           "alerts it selects with an observed window.", ""]
    for k, h in TARGETS:
        tag = "%gx@%s" % (k, pde.H_LABEL[h])
        tr = [r for r in train if label(r, k, h) is not None]
        va = [r for r in val if label(r, k, h) is not None]
        ytr = [label(r, k, h) for r in tr]
        yva = [label(r, k, h) for r in va]
        base_tr, base_va = sum(ytr) / len(ytr), sum(yva) / len(yva)
        atoms = build_atoms(tr)
        BUDGET["atoms"] += len(atoms)
        before = BUDGET["rules_evaluated"]
        rules = search_rules(tr, ytr, atoms)
        n_eval = BUDGET["rules_evaluated"] - before
        doc += ["## Target %s" % tag, "",
                "Base rate: TRAIN %s, VALIDATION %s." % (pde.rate_cell(sum(ytr), len(ytr)),
                                                           pde.rate_cell(sum(yva), len(yva))),
                "Rule search: %d atoms, %d rules evaluated, %d distinct rules with TRAIN support >= %d."
                % (len(atoms), n_eval, len(rules), MIN_SUPPORT), ""]

        def val_of(rule: tuple[Atom, ...]) -> tuple[int, int]:
            sel = [yy for r, yy in zip(va, yva) if rule_true(r, rule)]
            return sum(sel), len(sel)

        # RULES WITH HIGH >=2X HIT RATE (TRAIN), with their VALIDATION rate
        doc += ["### Rules with a high TRAIN hit rate", "",
                "| TRAIN rate | rules | of which N >= 40 | median N | best VAL rate among them (N) | "
                "VAL rate pooled over all of them |", "|---|---:|---:|---:|---|---|"]
        for lo_, hi_ in ((0.9, 1.01), (0.8, 0.9), (0.7, 0.8), (0.6, 0.7)):
            grp = [d for d in rules if lo_ <= d["rate"] < hi_]
            if not grp:
                doc.append("| %d-%d %% | 0 | 0 | - | - | - |" % (100 * lo_, min(100, 100 * hi_)))
                continue
            vv = [(val_of(d["rule"]), d) for d in grp]
            best = max(vv, key=lambda z: (z[0][0] / z[0][1]) if z[0][1] >= MIN_VAL_N else -1)
            pk = sum(a for (a, n), _ in vv)
            pn = sum(n for (a, n), _ in vv)
            doc.append("| >= %d %% | %d | %d | %d | %s | %s |" % (
                100 * lo_, len(grp), sum(1 for d in grp if d["n"] >= 40), int(pde.median([d["n"] for d in grp])),
                ("%.1f %% (%d)" % (100 * best[0][0] / best[0][1], best[0][1])) if best[0][1] >= MIN_VAL_N
                else "none with VAL N >= %d" % MIN_VAL_N,
                pde.rate_cell(pk, pn) + " (alert-rule pairs, overlapping)"))
        doc += ["", "Largest-N rules at >= 60 %% in TRAIN (the full list is in derived/rules_%s.json):" % tag, "",
                "| rule | N train | TP | FP | TRAIN rate | N val | VAL rate | TEST rate |",
                "|---|---:|---:|---:|---|---:|---|---|"]
        hi_rules = sorted([d for d in rules if d["rate"] >= 0.6], key=lambda d: -d["n"])[:15]
        for d in hi_rules:
            vk, vn = val_of(d["rule"])
            doc.append("| %s | %d | %d | %d | %.1f %% | %d | %s | sealed |" % (
                rule_text(d["rule"]), d["n"], d["k"], d["n"] - d["k"], 100 * d["rate"], vn, pde.rate_cell(vk, vn)))

        # selection on VALIDATION
        top = rules[:TOP_TO_VAL]
        scored = []
        for d in top:
            vk, vn = val_of(d["rule"])
            scored.append((lb(vk, vn) if vn >= MIN_VAL_N else -1.0, vk, vn, d))
        scored.sort(key=lambda z: -z[0])
        doc += ["", "### The %d best TRAIN rules (Wilson lower bound), re-measured in VALIDATION" % TOP_TO_VAL, "",
                "| # | rule | N train | TRAIN rate | N val | VAL rate | VAL lower bound |",
                "|---:|---|---:|---|---:|---|---:|"]
        for i, (s, vk, vn, d) in enumerate(scored[:20], 1):
            doc.append("| %d | %s | %d | %s | %d | %s | %s |" % (
                i, rule_text(d["rule"]), d["n"], pde.rate_cell(d["k"], d["n"]), vn, pde.rate_cell(vk, vn),
                "%.3f" % s if s >= 0 else "VAL N < %d" % MIN_VAL_N))
        s0, vk, vn, d = scored[0]
        locked.append({"id": "R_%s" % tag, "kind": "rule", "target": [k, h],
                       "rule": [list(a) for a in d["rule"]], "text": rule_text(d["rule"]),
                       "train": [d["k"], d["n"]], "val": [vk, vn],
                       "base_train": base_tr, "base_val": base_va})
        doc += ["", "**Locked for TEST: `%s`** (TRAIN %s, VALIDATION %s)." % (
            rule_text(d["rule"]), pde.rate_cell(d["k"], d["n"]), pde.rate_cell(vk, vn)), ""]
        with open(os.path.join(pde.DERIVED, "rules_%s.json" % tag.replace("@", "_")), "w", encoding="utf8") as fh:
            json.dump([{"rule": rule_text(x["rule"]), "n": x["n"], "k": x["k"]} for x in rules], fh)

        # logistic regression
        med, mu, sd = {}, {}, {}
        for f in LOGIT_FEATURES:
            xs = [float(value(r, f)) for r in tr if value(r, f) is not None]
            med[f] = pde.median(xs) if xs else 0.0
            full = [float(value(r, f)) if value(r, f) is not None else med[f] for r in tr]
            mu[f] = sum(full) / len(full)
            sd[f] = (sum((v - mu[f]) ** 2 for v in full) / len(full)) ** 0.5 or 1.0
        Xtr, Xva = design(tr, med, mu, sd), design(va, med, mu, sd)
        fits = []
        for lam in LAMBDAS:
            beta = fit_logit(Xtr, ytr, lam)
            fits.append((pde.auc(score(beta, Xva), yva), lam, beta))
        a_va, lam, beta = max(fits, key=lambda z: z[0] or 0)
        s_tr = score(beta, Xtr)
        cut = pde.quantile(s_tr, 0.8)
        sel_tr = [yy for s, yy in zip(s_tr, ytr) if s >= cut]
        sel_va = [yy for s, yy in zip(score(beta, Xva), yva) if s >= cut]
        top_coef = sorted(range(1, len(beta)), key=lambda j: -abs(beta[j]))[:6]
        doc += ["### Ridge logistic regression", "",
                "Penalty chosen on VALIDATION AUC among %s: lambda = %g. AUC TRAIN %.3f, VALIDATION %.3f. "
                "Largest standardised coefficients: %s." % (
                    list(LAMBDAS), lam, pde.auc(s_tr, ytr), a_va,
                    ", ".join("%s %+.2f" % (colname(j), beta[j]) for j in top_coef)),
                "Signal = score >= TRAIN 80th percentile: TRAIN %s, VALIDATION %s." % (
                    pde.rate_cell(sum(sel_tr), len(sel_tr)), pde.rate_cell(sum(sel_va), len(sel_va))), ""]
        locked.append({"id": "L_%s" % tag, "kind": "logistic", "target": [k, h], "lambda": lam, "beta": beta,
                       "cut": cut, "features": LOGIT_FEATURES, "median": med, "mean": mu, "sd": sd,
                       "text": "ridge logistic score >= TRAIN 80th percentile",
                       "train": [sum(sel_tr), len(sel_tr)], "val": [sum(sel_va), len(sel_va)],
                       "base_train": base_tr, "base_val": base_va})

        # small CART
        trees = []
        for depth in (2, 3):
            BUDGET["models_fitted"] += 1
            leaves = grow(Xtr, ytr, list(range(len(Xtr))), depth)
            rate = {lf["path"]: lf["k"] / lf["n"] for lf in leaves}

            def pred(x: list[float], _leaves: list[dict[str, Any]] = leaves, _rate: dict = rate) -> float:
                for lf in _leaves:
                    if in_leaf(x, lf["path"]):
                        return _rate[lf["path"]]
                return 0.0
            trees.append((pde.auc([pred(x) for x in Xva], yva) or 0.0, depth, leaves))
        a_t, depth, leaves = max(trees, key=lambda z: z[0])
        best_leaf = max(leaves, key=lambda lf: (lf["k"] / lf["n"], lf["n"]))
        vsel = [yy for x, yy in zip(Xva, yva) if in_leaf(x, best_leaf["path"])]
        path_txt = " AND ".join("%s %s %.3g (standardised)" % (colname(j), op, t) for j, op, t in best_leaf["path"])
        doc += ["### Shallow tree", "",
                "Depth chosen on VALIDATION AUC: %d (AUC VALIDATION %.3f). Best TRAIN leaf: `%s`: TRAIN %s, "
                "VALIDATION %s." % (depth, a_t, path_txt or "(root)", pde.rate_cell(best_leaf["k"], best_leaf["n"]),
                                    pde.rate_cell(sum(vsel), len(vsel))), ""]
        locked.append({"id": "T_%s" % tag, "kind": "tree_leaf", "target": [k, h], "path": best_leaf["path"],
                       "features": LOGIT_FEATURES, "median": med, "mean": mu, "sd": sd, "text": path_txt,
                       "train": [best_leaf["k"], best_leaf["n"]], "val": [sum(vsel), len(vsel)],
                       "base_train": base_tr, "base_val": base_va})

    # hypotheses specified before this study, primary target only
    k, h = pde.PRIMARY
    hyp: list[tuple[str, str, Callable[[dict[str, Any]], bool]]] = [
        ("H1_actor_grouped", "actor == grouped (paquet_max >= 2)", lambda r: value(r, "actor") == "grouped"),
        ("H2_mc_below_60k", "market cap at P0 < 60 000 USD", lambda r: r["f"]["mc_usd"] < 60000),
        ("H2b_mc_40k_60k", "40 000 <= market cap at P0 < 60 000 USD", lambda r: 40000 <= r["f"]["mc_usd"] < 60000),
    ]
    doc += ["## Hypotheses specified before this study (target 2x@1h)", "",
            "| hypothesis | TRAIN signal | TRAIN rest | VALIDATION signal | VALIDATION rest |", "|---|---|---|---|---|"]
    for hid, txt, fn in hyp:
        cells = []
        base = {}
        for sp, rows in (("train", train), ("val", val)):
            obs = [(r, label(r, k, h)) for r in rows if label(r, k, h) is not None]
            s = [y for r, y in obs if fn(r)]
            o = [y for r, y in obs if not fn(r)]
            base[sp] = sum(y for _, y in obs) / len(obs)
            cells += [pde.rate_cell(sum(s), len(s)), pde.rate_cell(sum(o), len(o))]
            if sp == "train":
                trk = [sum(s), len(s)]
            else:
                vak = [sum(s), len(s)]
        doc.append("| %s: %s | %s |" % (hid, txt, " | ".join(cells)))
        locked.append({"id": hid, "kind": "hypothesis", "target": [k, h], "text": txt,
                       "train": trk, "val": vak, "base_train": base["train"], "base_val": base["val"]})

    doc += ["", "## Search budget", "",
            "Atoms (conditions) built: %d. Rules evaluated: %d. Models fitted (logistic + trees): %d. Tree "
            "thresholds scanned: %d. Univariate screen (an_30): see derived/univariate_summary.json. Locked "
            "signals: %d." % (BUDGET["atoms"], BUDGET["rules_evaluated"], BUDGET["models_fitted"],
                              BUDGET["thresholds"], len(locked))]
    pde.write_table("T3_signal_search.md", "\n".join(doc))

    dev_sha = hashlib.sha256(open(os.path.join(pde.DERIVED, "dataset_dev.jsonl.gz"), "rb").read()).hexdigest()
    test_sha = hashlib.sha256(open(os.path.join(pde.DERIVED, "dataset_test.sealed.jsonl.gz"), "rb").read()).hexdigest()
    lock = {
        "locked_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "dataset_dev_sha256": dev_sha, "dataset_test_sha256": test_sha,
        "search_budget": BUDGET,
        "signals": locked,
        "headline_signal": "R_2x@1h",
        "robustness_for": "the headline signal, plus every signal that survives TEST",
        "decision_rules": {
            "statistical_survival": "on TEST, all of: N(signal, observed) >= 30; one-sided Fisher p (signal "
                                    "vs rest of TEST) < 0.05 after Holm across all locked signals; 95 % "
                                    "cluster-bootstrap CI of (P(signal) - P(rest)) above 0",
            "high_probability": "reported, not a criterion: Wilson lower bound of P(2x | signal) on TEST "
                                "against 0.6 and 0.8",
            "edge": "a surviving signal is an EDGE only if its primary strategy, entry at 10 s latency, "
                    "$500, estimated costs, has a mean net return on TEST whose 95 % cluster-bootstrap CI "
                    "is above 0; otherwise STATISTICAL SIGNAL, NO TRADABLE EDGE",
        },
        "strategies": {
            "S1": {"tp": 1.5, "sl": 0.8, "timeout_s": 300},
            "S2": {"tp": 2.0, "sl": 0.8, "timeout_s": 300},
            "S3": {"tp": 3.0, "sl": 0.8, "timeout_s": 300},
            "HOLD_5m": {"tp": 2.0, "sl": None, "timeout_s": 300},
            "HOLD_15m": {"tp": 2.0, "sl": None, "timeout_s": 900},
            "HOLD_1h": {"tp": 2.0, "sl": None, "timeout_s": 3600},
            "primary_for_target": {"300": "HOLD_5m", "900": "HOLD_15m", "3600": "HOLD_1h"},
        },
        "cost_model": {
            "fee_per_leg": 0.01, "fixed_sol_per_tx": 0.005,
            "k_pool": 1.39e10, "k_curve": 30 * 1.073e9, "k_sensitivity": [0.5, 2.0],
            "sizes_usd": [100, 500, 1000], "latencies_s": list(pde.LATENCIES),
            "primary": {"size_usd": 500, "latency_s": 10, "exit_mode": "touch"},
            "exit_mode_sensitivity": "next",
        },
    }
    path = os.path.join(pde.TABLES, "LOCK.json")
    print("\n".join(doc))
    if os.path.exists(path):
        # The lock is written once. A rerun (a clone, a reviewer) recomputes it
        # and checks that it would have locked the same thing; it never
        # replaces the committed file, whose timestamp is the evidence.
        old = json.load(open(path))
        same = all(json.dumps(old[k], sort_keys=True) == json.dumps(json.loads(json.dumps(lock[k])), sort_keys=True)
                   for k in lock if k != "locked_at_utc")
        print("\nLOCK.json exists (locked %s UTC): recomputed lock %s." % (
            old["locked_at_utc"], "IDENTICAL" if same else "DIFFERENT, the committed lock is kept"))
        if not same:
            raise SystemExit(1)
        return
    with open(path, "w", encoding="utf8") as fh:
        json.dump(lock, fh, indent=1)
        fh.write("\n")
    print("\nLOCK written: %d signals" % len(locked))


if __name__ == "__main__":
    main()
