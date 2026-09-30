#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fml.py -- the four model families, their preprocessing and their metrics.

Standard library only, like the rest of the repository, which is why the trees
are histogram trees: every feature is cut once, on TRAIN, into at most 10 bins
at its deciles, and a split is searched over those cut points in one pass per
feature. Nothing here is fitted on anything but the rows it is given.

  Prep            median imputation, winsorising at the 1st / 99th percentile,
                  standardisation; all three computed on TRAIN and frozen.
  LogReg          ridge logistic regression, full-batch gradient descent with
                  Nesterov momentum on standardised inputs (convex, 400 steps).
  Tree            one CART classifier (Gini), depth 2 or 3, leaves >= 30.
  Forest          bagged Gini trees on bootstrap samples, sqrt(p) features per
                  split, depth <= 5, leaves >= 20.
  Boost           gradient boosting on the logistic loss, depth-2 Newton trees,
                  learning rate 0.05, row subsampling 0.8.
Metrics: ROC-AUC, PR-AUC (average precision), Brier score, expected calibration
error over 10 bins, precision / recall / F1 at a fixed threshold, and
precision at the top k % of scores.
"""
from __future__ import annotations

import math
import random
from typing import Any, Optional, Sequence


# ------------------------------------------------------------------ prep ---- #
class Prep:
    def __init__(self, names: list[str]) -> None:
        self.names = names
        self.med: dict[str, float] = {}
        self.lo: dict[str, float] = {}
        self.hi: dict[str, float] = {}
        self.mu: dict[str, float] = {}
        self.sd: dict[str, float] = {}
        self.cuts: dict[str, list[float]] = {}

    def fit(self, rows: Sequence[dict[str, Any]]) -> "Prep":
        for f in self.names:
            xs = sorted(float(r[f]) for r in rows if r.get(f) is not None)
            if not xs:
                self.med[f], self.lo[f], self.hi[f], self.mu[f], self.sd[f], self.cuts[f] = 0, 0, 0, 0, 1, []
                continue
            q = lambda p: xs[min(len(xs) - 1, int(p * (len(xs) - 1)))]  # noqa: E731
            self.med[f], self.lo[f], self.hi[f] = q(0.5), q(0.01), q(0.99)
            v = [min(self.hi[f], max(self.lo[f], float(r[f]) if r.get(f) is not None else self.med[f]))
                 for r in rows]
            self.mu[f] = sum(v) / len(v)
            self.sd[f] = (sum((x - self.mu[f]) ** 2 for x in v) / len(v)) ** 0.5 or 1.0
            self.cuts[f] = sorted({(q(k / 10) - self.mu[f]) / self.sd[f] for k in range(1, 10)})
        return self

    def transform(self, rows: Sequence[dict[str, Any]]) -> list[list[float]]:
        out = []
        for r in rows:
            x = []
            for f in self.names:
                v = r.get(f)
                v = self.med[f] if v is None else float(v)
                v = min(self.hi[f], max(self.lo[f], v))
                x.append((v - self.mu[f]) / self.sd[f])
            out.append(x)
        return out

    def state(self) -> dict[str, Any]:
        return {"names": self.names, "med": self.med, "lo": self.lo, "hi": self.hi, "mu": self.mu, "sd": self.sd,
                "cuts": self.cuts}

    @staticmethod
    def load(s: dict[str, Any]) -> "Prep":
        p = Prep(s["names"])
        p.med, p.lo, p.hi, p.mu, p.sd, p.cuts = s["med"], s["lo"], s["hi"], s["mu"], s["sd"], s["cuts"]
        return p


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, z))))


# ---------------------------------------------------------------- logreg ---- #
class LogReg:
    def __init__(self, lam: float) -> None:
        self.lam = lam
        self.w: list[float] = []

    def fit(self, X: list[list[float]], y: list[int], steps: int = 400) -> "LogReg":
        n, p = len(X), len(X[0])
        w = [0.0] * (p + 1)
        v = [0.0] * (p + 1)
        lr, mom = 0.5, 0.9
        for _ in range(steps):
            look = [w[j] + mom * v[j] for j in range(p + 1)]
            g = [0.0] * (p + 1)
            for x, t in zip(X, y):
                z = look[0] + sum(a * b for a, b in zip(look[1:], x))
                e = sigmoid(z) - t
                g[0] += e
                for j, xv in enumerate(x):
                    g[j + 1] += e * xv
            for j in range(p + 1):
                g[j] = g[j] / n + (self.lam / n * look[j] if j else 0.0)
                v[j] = mom * v[j] - lr * g[j]
                w[j] += v[j]
        self.w = w
        return self

    def score(self, X: list[list[float]]) -> list[float]:
        return [sigmoid(self.w[0] + sum(a * b for a, b in zip(self.w[1:], x))) for x in X]

    def state(self) -> dict[str, Any]:
        return {"type": "logreg", "lam": self.lam, "w": self.w}


# ---------------------------------------------------------- histogram trees -- #
def _bins(X: list[list[float]], cuts: list[list[float]]) -> list[list[int]]:
    """Column-major bin indices: B[j][i] = number of cut points below x[i][j]."""
    out = []
    for j, c in enumerate(cuts):
        col = []
        for x in X:
            v, b = x[j], 0
            while b < len(c) and v > c[b]:
                b += 1
            col.append(b)
        out.append(col)
    return out


def _gini_tree(B: list[list[int]], y: list[int], idx: list[int], cuts: list[list[float]], depth: int,
               min_leaf: int, feats_fn: Any) -> dict[str, Any]:
    k = sum(y[i] for i in idx)
    node: dict[str, Any] = {"n": len(idx), "p": (k + 1) / (len(idx) + 2)}
    if depth == 0 or len(idx) < 2 * min_leaf or k in (0, len(idx)):
        return node
    parent = len(idx) * (1 - (k / len(idx)) ** 2 - (1 - k / len(idx)) ** 2)
    best = None
    for j in feats_fn():
        nb = len(cuts[j]) + 1
        cnt, pos = [0] * nb, [0] * nb
        col = B[j]
        for i in idx:
            cnt[col[i]] += 1
            pos[col[i]] += y[i]
        nl = kl = 0
        for b in range(nb - 1):
            nl += cnt[b]
            kl += pos[b]
            nr, kr = len(idx) - nl, k - kl
            if nl < min_leaf or nr < min_leaf:
                continue
            g = nl * (1 - (kl / nl) ** 2 - (1 - kl / nl) ** 2) + nr * (1 - (kr / nr) ** 2 - (1 - kr / nr) ** 2)
            if g < parent - 1e-9 and (best is None or g < best[0]):
                best = (g, j, b)
    if best is None:
        return node
    _, j, b = best
    left = [i for i in idx if B[j][i] <= b]
    right = [i for i in idx if B[j][i] > b]
    node.update({"f": j, "t": cuts[j][b], "gain": parent - best[0],
                 "l": _gini_tree(B, y, left, cuts, depth - 1, min_leaf, feats_fn),
                 "r": _gini_tree(B, y, right, cuts, depth - 1, min_leaf, feats_fn)})
    return node


def _walk(node: dict[str, Any], x: list[float], key: str = "p") -> float:
    while "f" in node:
        node = node["l"] if x[node["f"]] <= node["t"] else node["r"]
    return node[key]


def _importance(node: dict[str, Any], acc: dict[int, float]) -> None:
    if "f" in node:
        acc[node["f"]] = acc.get(node["f"], 0.0) + node.get("gain", 0.0)
        _importance(node["l"], acc)
        _importance(node["r"], acc)


class Tree:
    def __init__(self, depth: int, min_leaf: int = 30) -> None:
        self.depth, self.min_leaf = depth, min_leaf
        self.root: dict[str, Any] = {}

    def fit(self, X: list[list[float]], y: list[int], cuts: list[list[float]]) -> "Tree":
        B = _bins(X, cuts)
        p = len(cuts)
        self.root = _gini_tree(B, y, list(range(len(X))), cuts, self.depth, self.min_leaf, lambda: range(p))
        return self

    def score(self, X: list[list[float]]) -> list[float]:
        return [_walk(self.root, x) for x in X]

    def importance(self) -> dict[int, float]:
        acc: dict[int, float] = {}
        _importance(self.root, acc)
        return acc

    def state(self) -> dict[str, Any]:
        return {"type": "tree", "depth": self.depth, "root": self.root}


class Forest:
    def __init__(self, n_trees: int, depth: int, min_leaf: int = 20, seed: int = 20260929) -> None:
        self.n_trees, self.depth, self.min_leaf, self.seed = n_trees, depth, min_leaf, seed
        self.trees: list[dict[str, Any]] = []

    def fit(self, X: list[list[float]], y: list[int], cuts: list[list[float]]) -> "Forest":
        rng = random.Random(self.seed)
        B = _bins(X, cuts)
        p = len(cuts)
        m = max(1, int(round(p ** 0.5)))
        self.trees = []
        for _ in range(self.n_trees):
            idx = [rng.randrange(len(X)) for _ in range(len(X))]
            self.trees.append(_gini_tree(B, y, idx, cuts, self.depth, self.min_leaf,
                                         lambda: rng.sample(range(p), m)))
        return self

    def score(self, X: list[list[float]]) -> list[float]:
        return [sum(_walk(t, x) for t in self.trees) / len(self.trees) for x in X]

    def importance(self) -> dict[int, float]:
        acc: dict[int, float] = {}
        for t in self.trees:
            _importance(t, acc)
        return acc

    def state(self) -> dict[str, Any]:
        return {"type": "forest", "depth": self.depth, "trees": self.trees}


def _newton_tree(B: list[list[int]], g: list[float], h: list[float], idx: list[int], cuts: list[list[float]],
                 depth: int, lam: float, min_leaf: int) -> dict[str, Any]:
    G = sum(g[i] for i in idx)
    H = sum(h[i] for i in idx)
    node: dict[str, Any] = {"v": -G / (H + lam), "n": len(idx)}
    if depth == 0 or len(idx) < 2 * min_leaf:
        return node
    base = G * G / (H + lam)
    best = None
    for j in range(len(cuts)):
        nb = len(cuts[j]) + 1
        gs, hs, cn = [0.0] * nb, [0.0] * nb, [0] * nb
        col = B[j]
        for i in idx:
            b = col[i]
            gs[b] += g[i]
            hs[b] += h[i]
            cn[b] += 1
        gl = hl = 0.0
        nl = 0
        for b in range(nb - 1):
            gl += gs[b]
            hl += hs[b]
            nl += cn[b]
            if nl < min_leaf or len(idx) - nl < min_leaf:
                continue
            gain = gl * gl / (hl + lam) + (G - gl) ** 2 / (H - hl + lam) - base
            if gain > 1e-9 and (best is None or gain > best[0]):
                best = (gain, j, b)
    if best is None:
        return node
    _, j, b = best
    left = [i for i in idx if B[j][i] <= b]
    right = [i for i in idx if B[j][i] > b]
    node.update({"f": j, "t": cuts[j][b], "gain": best[0],
                 "l": _newton_tree(B, g, h, left, cuts, depth - 1, lam, min_leaf),
                 "r": _newton_tree(B, g, h, right, cuts, depth - 1, lam, min_leaf)})
    return node


class Boost:
    def __init__(self, rounds: int, lr: float = 0.05, depth: int = 2, lam: float = 1.0, sub: float = 0.8,
                 min_leaf: int = 20, seed: int = 20260929) -> None:
        self.rounds, self.lr, self.depth, self.lam, self.sub, self.min_leaf, self.seed = (
            rounds, lr, depth, lam, sub, min_leaf, seed)
        self.base = 0.0
        self.trees: list[dict[str, Any]] = []

    def fit(self, X: list[list[float]], y: list[int], cuts: list[list[float]]) -> "Boost":
        rng = random.Random(self.seed)
        B = _bins(X, cuts)
        prior = (sum(y) + 1) / (len(y) + 2)
        self.base = math.log(prior / (1 - prior))
        f = [self.base] * len(X)
        self.trees = []
        for _ in range(self.rounds):
            p = [sigmoid(v) for v in f]
            g = [pi - yi for pi, yi in zip(p, y)]
            h = [max(1e-6, pi * (1 - pi)) for pi in p]
            idx = [i for i in range(len(X)) if rng.random() < self.sub]
            t = _newton_tree(B, g, h, idx, cuts, self.depth, self.lam, self.min_leaf)
            self.trees.append(t)
            for i, x in enumerate(X):
                f[i] += self.lr * _walk(t, x, "v")
        return self

    def score(self, X: list[list[float]]) -> list[float]:
        return [sigmoid(self.base + self.lr * sum(_walk(t, x, "v") for t in self.trees)) for x in X]

    def importance(self) -> dict[int, float]:
        acc: dict[int, float] = {}
        for t in self.trees:
            _importance(t, acc)
        return acc

    def state(self) -> dict[str, Any]:
        return {"type": "boost", "base": self.base, "lr": self.lr, "trees": self.trees}


def score_state(state: dict[str, Any], X: list[list[float]]) -> list[float]:
    """Score rows with a frozen model, from its saved state only."""
    t = state["type"]
    if t == "logreg":
        w = state["w"]
        return [sigmoid(w[0] + sum(a * b for a, b in zip(w[1:], x))) for x in X]
    if t == "tree":
        return [_walk(state["root"], x) for x in X]
    if t == "forest":
        return [sum(_walk(tr, x) for tr in state["trees"]) / len(state["trees"]) for x in X]
    if t == "boost":
        return [sigmoid(state["base"] + state["lr"] * sum(_walk(tr, x, "v") for tr in state["trees"])) for x in X]
    raise ValueError(t)


# --------------------------------------------------------------- metrics ---- #
def roc_auc(s: Sequence[float], y: Sequence[int]) -> Optional[float]:
    pairs = sorted(zip(s, y))
    n1 = sum(y)
    n0 = len(y) - n1
    if not n1 or not n0:
        return None
    rank_sum, i = 0.0, 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        r = (i + j) / 2 + 1
        rank_sum += r * sum(1 for k in range(i, j + 1) if pairs[k][1] == 1)
        i = j + 1
    return (rank_sum - n1 * (n1 + 1) / 2) / (n1 * n0)


def pr_auc(s: Sequence[float], y: Sequence[int]) -> Optional[float]:
    """Average precision (step interpolation)."""
    n1 = sum(y)
    if not n1:
        return None
    order = sorted(range(len(s)), key=lambda i: -s[i])
    tp, ap = 0, 0.0
    for k, i in enumerate(order, 1):
        if y[i]:
            tp += 1
            ap += tp / k
    return ap / n1


def brier(s: Sequence[float], y: Sequence[int]) -> float:
    return sum((a - b) ** 2 for a, b in zip(s, y)) / len(y)


def ece(s: Sequence[float], y: Sequence[int], bins: int = 10) -> tuple[float, list[tuple[float, float, int]]]:
    order = sorted(range(len(s)), key=lambda i: s[i])
    out, err = [], 0.0
    for b in range(bins):
        part = order[b * len(order) // bins:(b + 1) * len(order) // bins]
        if not part:
            continue
        ps = sum(s[i] for i in part) / len(part)
        ys = sum(y[i] for i in part) / len(part)
        out.append((ps, ys, len(part)))
        err += len(part) / len(s) * abs(ps - ys)
    return err, out


def top_k(s: Sequence[float], y: Sequence[int], frac: float) -> tuple[int, int]:
    """(hits, n) among the top `frac` of scores."""
    n = max(1, int(round(frac * len(s))))
    order = sorted(range(len(s)), key=lambda i: -s[i])[:n]
    return sum(y[i] for i in order), n


def at_threshold(s: Sequence[float], y: Sequence[int], thr: float) -> dict[str, Any]:
    tp = sum(1 for a, b in zip(s, y) if a >= thr and b)
    fp = sum(1 for a, b in zip(s, y) if a >= thr and not b)
    fn = sum(1 for a, b in zip(s, y) if a < thr and b)
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    f1 = 2 * prec * rec / (prec + rec) if prec and rec else None
    return {"tp": tp, "fp": fp, "fn": fn, "n_sel": tp + fp, "precision": prec, "recall": rec, "f1": f1}
