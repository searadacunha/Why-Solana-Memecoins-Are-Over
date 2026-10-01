#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The analysis of analysis_plan.md sections 6-7 on the frozen features (KG_FREEZE.json) and outcomes
(KG_OUTCOMES.json): group rates, models 1-3, matched comparison, depth, recency and stability, operator controls,
forward returns, trading, the decision rule. Writes tables/C_models.md ... J_decision.md and
derived/KG_results.json. TEST is not in the data.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from typing import Any, Callable, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "post_detection_edge", "code"))
import pde  # noqa: E402

D = os.path.join(STUDY, "derived")
TABLES = os.path.join(STUDY, "tables")
SPLITS = ("train", "val")
PRIMARY_Y = ("L5", "y_1.50_900")
PRIMARY_T = ("L5", "tp1.50_sl0.85")
STRATS = ("time10", "time30", "time60", "time300", "time900", "tp1.25_sl0.90", "tp1.50_sl0.85", "tp2.00_sl0.80")
LATS = ("L0", "L5", "L15", "L30")
L2 = 1.0
SEED = 20261001


def load() -> list[dict[str, Any]]:
    for f, key, meta in (
        ("kg_features.jsonl.gz", "sha256_features", "KG_FREEZE.json"),
        ("kg_outcomes.jsonl.gz", "sha256_outcomes", "KG_OUTCOMES.json"),
    ):
        if (
            hashlib.sha256(open(os.path.join(D, f), "rb").read()).hexdigest()
            != json.load(open(os.path.join(D, meta)))[key]
        ):
            sys.exit("%s differs from its frozen sha256" % f)
    fe = [json.loads(x) for x in gzip.open(os.path.join(D, "kg_features.jsonl.gz"), "rt")]
    oc = {o["mint"]: o for o in (json.loads(x) for x in gzip.open(os.path.join(D, "kg_outcomes.jsonl.gz"), "rt"))}
    for r in fe:
        r["o"] = oc[r["mint"]]
    return sorted(fe, key=lambda r: r["t"])


def y_of(r: dict[str, Any], lat: str = PRIMARY_Y[0], key: str = PRIMARY_Y[1]) -> Optional[int]:
    d = r["o"].get(lat)
    return None if d is None else d.get(key)


def trade_of(r: dict[str, Any], lat: str = PRIMARY_T[0], strat: str = PRIMARY_T[1]) -> Optional[dict[str, Any]]:
    d = r["o"].get(lat)
    if d is None:
        return None
    s = d["trades"][strat]
    return s if s["status"] == "ok" else None


def write(name: str, lines: list[str]) -> None:
    os.makedirs(TABLES, exist_ok=True)
    with open(os.path.join(TABLES, name), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")


def pct(x: Optional[float]) -> str:
    return "n/a" if x is None else "%.1f %%" % (100 * x)


def ci(t: tuple[Optional[float], Optional[float]]) -> str:
    return "n/a" if t[0] is None else "[%+.1f, %+.1f]" % (100 * t[0], 100 * t[1])


# ------------------------------------------------------------------ models --- #
def feats_base(r: dict[str, Any]) -> list[Optional[float]]:
    f = r["f"]
    eo = f.get("entry_over_operator")
    return [
        f.get("n_snipers"),
        math.log10(f["snipe_sol"]) if f.get("snipe_sol") else None,
        f.get("supply_part"),
        f.get("log10_mc_usd"),
        math.log10(eo) if eo and eo > 0 else None,
        1.0 if f.get("p0_source") == "pool" else 0.0,
        1.0 if (f.get("paquet_max") or 0) >= 2 else 0.0,
    ]


def feats_group(r: dict[str, Any]) -> list[Optional[float]]:
    return [
        1.0 if r["G1"] == "KNOWN" else 0.0,
        1.0 if r["G1"] == "PARTIAL" else 0.0,
        math.log1p(r["prior_group_launches"]),
        1.0 if r["G2"] else 0.0,
        1.0 if r["G4"] else 0.0,
    ]


def feats_full(r: dict[str, Any]) -> list[Optional[float]]:
    b, g = feats_base(r), feats_group(r)
    k = g[0]
    return b + g + [k * (b[1] if b[1] is not None else 0.0), k * (b[0] or 0.0)]


class Logit:
    def __init__(self, fn: Callable[[dict[str, Any]], list[Optional[float]]]) -> None:
        self.fn = fn

    def _x(self, r: dict[str, Any]) -> list[float]:
        v = self.fn(r)
        return [1.0] + [((self.med[i] if x is None else x) - self.mu[i]) / self.sd[i] for i, x in enumerate(v)]

    def fit(self, rows: list[dict[str, Any]], ys: list[int]) -> "Logit":
        raw = [self.fn(r) for r in rows]
        k = len(raw[0])
        self.med = [
            sorted(x[i] for x in raw if x[i] is not None)[len([x for x in raw if x[i] is not None]) // 2]
            for i in range(k)
        ]
        full = [[(self.med[i] if x[i] is None else x[i]) for i in range(k)] for x in raw]
        self.mu = [sum(x[i] for x in full) / len(full) for i in range(k)]
        self.sd = [max(1e-9, math.sqrt(sum((x[i] - self.mu[i]) ** 2 for x in full) / len(full))) for i in range(k)]
        X = [self._x(r) for r in rows]
        w = [0.0] * (k + 1)
        for _ in range(50):  # Newton steps, L2 on the slopes
            g = [0.0] * (k + 1)
            H = [[0.0] * (k + 1) for _ in range(k + 1)]
            for xi, yi in zip(X, ys):
                p = 1 / (1 + math.exp(-sum(a * b for a, b in zip(w, xi))))
                for a in range(k + 1):
                    g[a] += (p - yi) * xi[a]
                    for b in range(k + 1):
                        H[a][b] += p * (1 - p) * xi[a] * xi[b]
            for a in range(1, k + 1):
                g[a] += L2 * w[a]
                H[a][a] += L2
            step = solve(H, g)
            w = [a - b for a, b in zip(w, step)]
            if max(abs(s) for s in step) < 1e-8:
                break
        self.w = w
        return self

    def p(self, r: dict[str, Any]) -> float:
        z = sum(a * b for a, b in zip(self.w, self._x(r)))
        return 1 / (1 + math.exp(-max(-30, min(30, z))))


def solve(A: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda i: abs(M[i][c]))
        M[c], M[p] = M[p], M[c]
        for i in range(n):
            if i != c and M[c][c]:
                f = M[i][c] / M[c][c]
                for j in range(c, n + 1):
                    M[i][j] -= f * M[c][j]
    return [M[i][n] / M[i][i] if M[i][i] else 0.0 for i in range(n)]


def metrics(ps: list[float], ys: list[int]) -> dict[str, Any]:
    eps = 1e-12
    ll = -sum(y * math.log(max(p, eps)) + (1 - y) * math.log(max(1 - p, eps)) for p, y in zip(ps, ys)) / len(ys)
    brier = sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ys)
    order = sorted(range(len(ps)), key=lambda i: -ps[i])
    tp = 0
    ap = 0.0
    npos = sum(ys)
    for rank, i in enumerate(order, 1):
        if ys[i]:
            tp += 1
            ap += tp / rank
    cal = []
    q = sorted(range(len(ps)), key=lambda i: ps[i])
    for b in range(5):
        idx = q[b * len(q) // 5 : (b + 1) * len(q) // 5]
        cal.append((sum(ps[i] for i in idx) / len(idx), sum(ys[i] for i in idx) / len(idx), len(idx)))
    return {
        "auc": pde.auc(ps, ys),
        "pr_auc": ap / npos if npos else None,
        "brier": brier,
        "logloss": ll,
        "cal": cal,
        "n": len(ys),
        "pos": npos,
    }


# ------------------------------------------------------------------ trading --- #
def trading(rows: list[dict[str, Any]], lat: str, strat: str, size: str = "net_500") -> dict[str, Any]:
    tr = [(r, trade_of(r, lat, strat)) for r in rows]
    ok = [(r, s) for r, s in tr if s is not None and s.get(size) is not None]
    out: dict[str, Any] = {"eligible": len(rows), "trades": len(ok)}
    if not ok:
        return out
    net = [s[size] for _, s in ok]
    gross = [s["gross"] - 1 for _, s in ok]
    wins = [x for x in net if x > 0]
    losses = [x for x in net if x <= 0]
    eq, peak, mdd = 0.0, 0.0, 0.0
    for x in net:  # time order (rows are sorted by alert time)
        eq += x
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)

    def be(v: list[float]) -> Optional[float]:
        w = [x for x in v if x > 0]
        lo = [x for x in v if x <= 0]
        if not w or not lo:
            return None
        aw, al = sum(w) / len(w), sum(lo) / len(lo)
        return -al / (aw - al)

    span = max(r["t"] for r, _ in ok) - min(r["t"] for r, _ in ok)
    out.update(
        {
            "win": len(wins) / len(net),
            "mean": sum(net) / len(net),
            "median": pde.median(net),
            "gross": sum(gross) / len(gross),
            "fees": sum(s["fees_500"] for _, s in ok) / len(ok),
            "slippage": sum(s["slippage_500"] for _, s in ok) / len(ok),
            "mdd": mdd,
            "worst": min(net),
            "pf": (sum(wins) / -sum(losses)) if losses and sum(losses) < 0 else None,
            "hold": sum(s["dt"] for _, s in ok) / len(ok),
            "exposed": (sum(s["dt"] for _, s in ok) / span) if span > 0 else None,
            "be_gross": be(gross),
            "be_net": be(net),
            "ci": pde.cluster_boot_mean([(r["operator"], s[size]) for r, s in ok]),
        }
    )
    return out


def trow(name: str, t: dict[str, Any]) -> str:
    if not t.get("trades"):
        return "| %s | %d | 0 | | | | | | | | | | | | | |" % (name, t.get("eligible", 0))
    return (
        "| %s | %d | %d | %s | %+.1f %% %s | %+.1f %% | %+.1f %% | %+.1f %% | %+.1f %% | %.1f | %+.0f %% | %s | "
        "%.0f s | %s | %s / %s |"
        % (
            name,
            t["eligible"],
            t["trades"],
            pct(t["win"]),
            100 * t["mean"],
            ci(t["ci"]),
            100 * t["median"],
            100 * t["gross"],
            100 * t["fees"],
            100 * t["slippage"],
            t["mdd"],
            100 * t["worst"],
            "%.2f" % t["pf"] if t["pf"] else "n/a",
            t["hold"],
            pct(t["exposed"]),
            pct(t["be_gross"]),
            pct(t["be_net"]),
        )
    )


THEAD = [
    "| population | eligible | trades | win | mean net [cluster CI] | median net | gross | fees | slippage | "
    "max drawdown (sum of returns) | worst | profit factor | hold | time in a position | break-even win gross / net |",
    "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
]


# --------------------------------------------------------------- comparisons --- #
def rate_diff(
    rows: list[dict[str, Any]],
    a: Callable[[dict[str, Any]], bool],
    b: Callable[[dict[str, Any]], bool],
    yf: Callable[[dict[str, Any]], Optional[int]] = y_of,
) -> dict[str, Any]:
    ra = [(r["operator"], 1, yf(r)) for r in rows if a(r) and yf(r) is not None]
    rb = [(r["operator"], 0, yf(r)) for r in rows if b(r) and yf(r) is not None]
    if not ra or not rb:
        return {"na": len(ra), "nb": len(rb)}
    pa = sum(y for _, _, y in ra) / len(ra)
    pb = sum(y for _, _, y in rb) / len(rb)
    ka, kb = sum(y for _, _, y in ra), sum(y for _, _, y in rb)
    pg = pde.fisher_greater(ka, len(ra) - ka, kb, len(rb) - kb)
    pl = pde.fisher_greater(kb, len(rb) - kb, ka, len(ra) - ka)
    return {
        "pa": pa,
        "pb": pb,
        "na": len(ra),
        "nb": len(rb),
        "diff": pa - pb,
        "ci": pde.cluster_boot_rate_diff(ra + rb),
        "p2": min(1.0, 2 * min(pg, pl)),
    }


def dcell(d: dict[str, Any]) -> str:
    if "diff" not in d:
        return "n/a (N %d / %d)" % (d.get("na", 0), d.get("nb", 0))
    return "%s (N %d) vs %s (N %d): %+.1f pts %s, p %.3g" % (
        pct(d["pa"]),
        d["na"],
        pct(d["pb"]),
        d["nb"],
        100 * d["diff"],
        ci(d["ci"]),
        d["p2"],
    )


def mh_within(
    rows: list[dict[str, Any]], a: Callable[[dict[str, Any]], bool], b: Callable[[dict[str, Any]], bool]
) -> dict[str, Any]:
    """Mantel-Haenszel risk difference over operators holding both groups; cluster bootstrap over them."""
    by: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for r in rows:
        y = y_of(r)
        if y is None:
            continue
        if a(r):
            by[r["operator"]].append((1, y))
        elif b(r):
            by[r["operator"]].append((0, y))
    ops = [o for o, v in by.items() if any(s for s, _ in v) and any(not s for s, _ in v)]

    def est(keys: list[str]) -> Optional[float]:
        num = den = 0.0
        for o in keys:
            v = by[o]
            n1 = sum(1 for s, _ in v if s)
            n0 = len(v) - n1
            a1 = sum(y for s, y in v if s)
            a0 = sum(y for s, y in v if not s)
            w = n1 * n0 / (n1 + n0)
            num += w * (a1 / n1 - a0 / n0)
            den += w
        return num / den if den else None

    if not ops:
        return {"ops": 0}
    rng = random.Random(SEED)
    boots = sorted(x for x in (est([ops[rng.randrange(len(ops))] for _ in ops]) for _ in range(2000)) if x is not None)
    return {
        "ops": len(ops),
        "n": sum(len(by[o]) for o in ops),
        "diff": est(ops),
        "ci": (boots[int(0.025 * (len(boots) - 1))], boots[int(0.975 * (len(boots) - 1))]) if boots else (None, None),
    }


def matched(rows: list[dict[str, Any]], train: list[dict[str, Any]]) -> dict[str, Any]:
    keys = (
        ("n_snipers", lambda r: r["f"].get("n_snipers")),
        ("snipe_sol", lambda r: r["f"].get("snipe_sol")),
        ("supply_part", lambda r: r["f"].get("supply_part")),
        ("entry_over_operator", lambda r: r["f"].get("entry_over_operator")),
        ("mc", lambda r: r["f"].get("log10_mc_usd")),
    )
    cuts = []
    for _, g in keys:
        v = sorted(x for x in (g(r) for r in train) if x is not None)
        cuts.append((v[len(v) // 3], v[2 * len(v) // 3]))

    def cell(r: dict[str, Any]) -> tuple[Any, ...]:
        out = []
        for (_, g), (c1, c2) in zip(keys, cuts):
            x = g(r)
            out.append(None if x is None else (0 if x <= c1 else 1 if x <= c2 else 2))
        return tuple(out)

    by: dict[tuple[Any, ...], list[tuple[str, int, int]]] = defaultdict(list)
    for r in rows:
        y = y_of(r)
        if y is None or r["G1"] == "PARTIAL":
            continue
        by[cell(r)].append((r["operator"], 1 if r["G1"] == "KNOWN" else 0, y))
    strata = {k: v for k, v in by.items() if any(s for _, s, _ in v) and any(not s for _, s, _ in v)}

    def est(st: dict[tuple[Any, ...], list[tuple[str, int, int]]]) -> Optional[float]:
        num = den = 0.0
        for v in st.values():
            k1 = [y for _, s, y in v if s]
            k0 = [y for _, s, y in v if not s]
            if not k1 or not k0:
                continue
            num += len(k1) * (sum(k1) / len(k1) - sum(k0) / len(k0))
            den += len(k1)
        return num / den if den else None

    opsl = sorted({o for v in strata.values() for o, _, _ in v})
    rng = random.Random(SEED)
    boots = []
    for _ in range(2000):
        pick = Counter(opsl[rng.randrange(len(opsl))] for _ in opsl)
        st = {k: [x for x in v for _ in range(pick.get(x[0], 0))] for k, v in strata.items()}
        e = est(st)
        if e is not None:
            boots.append(e)
    boots.sort()
    return {
        "strata": len(strata),
        "known": sum(1 for v in strata.values() for _, s, _ in v if s),
        "unknown": sum(1 for v in strata.values() for _, s, _ in v if not s),
        "diff": est(strata),
        "ci": (boots[int(0.025 * (len(boots) - 1))], boots[int(0.975 * (len(boots) - 1))]) if boots else (None, None),
    }


# --------------------------------------------------------------------- main --- #
def main() -> None:
    rows = load()
    sp = {s: [r for r in rows if r["split"] == s] for s in SPLITS}
    res: dict[str, Any] = {}
    K = lambda r: r["G1"] == "KNOWN"  # noqa: E731
    U = lambda r: r["G1"] == "UNKNOWN"  # noqa: E731

    # B. recognition
    lines = [
        "# B. Group recognition at the alert (analysis_plan.md section 2)",
        "",
        "| split | alerts | G1 KNOWN | G1 PARTIAL | G1 UNKNOWN | G2 recurring funder | G3 strong | G4 exit structure |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in SPLITS:
        c = Counter(r["G1"] for r in sp[s])
        lines.append(
            "| %s | %d | %d | %d | %d | %d | %d | %d |"
            % (
                s.upper(),
                len(sp[s]),
                c["KNOWN"],
                c["PARTIAL"],
                c["UNKNOWN"],
                sum(r["G2"] for r in sp[s]),
                sum(r["G3"] for r in sp[s]),
                sum(r["G4"] for r in sp[s]),
            )
        )
    write("B_recognition.md", lines)

    # C. rates and models
    lines = [
        "# C. Known group against the baseline (primary target: +50 % within 15 min, entry +5 s)",
        "",
        "| split | KNOWN vs UNKNOWN (G1) | PARTIAL vs UNKNOWN | G2 | G3 | G4 |",
        "|---|---|---|---|---|---|",
    ]
    res["rates"] = {}
    for s in SPLITS:
        d = {
            "G1": rate_diff(sp[s], K, U),
            "G1_partial": rate_diff(sp[s], lambda r: r["G1"] == "PARTIAL", U),
            "G2": rate_diff(sp[s], lambda r: r["G2"], lambda r: not r["G2"]),
            "G3": rate_diff(sp[s], lambda r: r["G3"], lambda r: not r["G3"]),
            "G4": rate_diff(sp[s], lambda r: r["G4"], lambda r: not r["G4"]),
        }
        res["rates"][s] = d
        lines.append(
            "| %s | %s | %s | %s | %s | %s |"
            % (s.upper(), dcell(d["G1"]), dcell(d["G1_partial"]), dcell(d["G2"]), dcell(d["G3"]), dcell(d["G4"]))
        )
    pv = [res["rates"]["val"][g].get("p2", 1.0) for g in ("G1", "G2", "G3", "G4")]
    hol = pde.holm(pv)
    lines += [
        "",
        "Holm across G1-G4 on VALIDATION (two-sided Fisher, alert level): "
        + ", ".join("%s %.3g" % (g, h) for g, h in zip(("G1", "G2", "G3", "G4"), hol)),
    ]
    tr = [r for r in sp["train"] if y_of(r) is not None]
    va = [r for r in sp["val"] if y_of(r) is not None]
    models = {"Model 1 baseline": feats_base, "Model 2 group only": feats_group, "Model 3 baseline + group": feats_full}
    fitted = {}
    lines += [
        "",
        "## Models fitted on TRAIN, scored on VALIDATION (L2 = 1, no tuning)",
        "",
        "| model | AUC | PR-AUC | Brier | log loss | calibration (mean predicted / observed, 5 bins) |",
        "|---|---:|---:|---:|---:|---|",
    ]
    res["models"] = {}
    for name, fn in models.items():
        m = Logit(fn).fit(tr, [y_of(r) for r in tr])
        fitted[name] = m
        mt = metrics([m.p(r) for r in va], [y_of(r) for r in va])
        res["models"][name] = {k: v for k, v in mt.items() if k != "cal"}
        lines.append(
            "| %s | %.3f | %.3f | %.4f | %.4f | %s |"
            % (
                name,
                mt["auc"],
                mt["pr_auc"],
                mt["brier"],
                mt["logloss"],
                ", ".join("%.2f/%.2f" % (a, b) for a, b, _ in mt["cal"]),
            )
        )
    m1, m3 = fitted["Model 1 baseline"], fitted["Model 3 baseline + group"]

    def ll(p: float, y: int) -> float:
        return -(y * math.log(max(p, 1e-12)) + (1 - y) * math.log(max(1 - p, 1e-12)))

    dl = [(r["operator"], ll(m3.p(r), y_of(r)) - ll(m1.p(r), y_of(r))) for r in va]
    dci = pde.cluster_boot_mean(dl)
    res["delta_logloss"] = {"mean": sum(x for _, x in dl) / len(dl), "ci": dci}
    lines += [
        "",
        "Log loss, Model 3 minus Model 1, per VALIDATION alert: %+.4f [%+.4f, %+.4f] (cluster bootstrap; "
        "negative = the group adds information)." % (res["delta_logloss"]["mean"], dci[0], dci[1]),
        "Base rate of the primary target: TRAIN %s (N %d), VALIDATION %s (N %d)."
        % (pct(sum(y_of(r) for r in tr) / len(tr)), len(tr), pct(sum(y_of(r) for r in va) / len(va)), len(va)),
    ]
    write("C_models.md", lines)

    # D. matched
    lines = [
        "# D. Matched comparison: KNOWN vs UNKNOWN in strata of TRAIN tertiles of n_snipers, SOL, supply, "
        "premium and market cap",
        "",
        "| split | strata | KNOWN | UNKNOWN | weighted difference [cluster CI] |",
        "|---|---:|---:|---:|---|",
    ]
    res["matched"] = {}
    for s in SPLITS:
        m = matched(sp[s], sp["train"])
        res["matched"][s] = m
        lines.append(
            "| %s | %d | %d | %d | %s %s |"
            % (
                s.upper(),
                m["strata"],
                m["known"],
                m["unknown"],
                "%+.1f pts" % (100 * m["diff"]) if m["diff"] is not None else "n/a",
                ci(m["ci"]),
            )
        )
    write("D_matched.md", lines)

    # E. depth, recency, stability
    lines = ["# E. Recurrence depth, recency, stability (primary target; primary strategy, $500)", ""]
    res["E"] = {}
    for title, key, order in (
        ("depth (prior group launches)", "depth", ("0", "1", "2-5", ">5")),
        ("recency (since the latest group launch)", "recency", ("<5m", "5-15m", "15-30m", "30-60m", "1-6h", ">6h")),
        ("stability", "stability", ("weak", "medium", "strong")),
    ):
        lines += [
            "## " + title,
            "",
            "| bin | TRAIN rate | VALIDATION rate | TRAIN net mean (N) | VALIDATION net mean [cluster CI] (N) |",
            "|---|---|---|---|---|",
        ]
        for b in order:
            cells = []
            for s in SPLITS:
                xs = [r for r in sp[s] if r[key] == b]
                ys = [y_of(r) for r in xs if y_of(r) is not None]
                t = trading(xs, *PRIMARY_T)
                cells.append((pde.rate_cell(sum(ys), len(ys)), t))
                res["E"].setdefault(key, {}).setdefault(b, {})[s] = {
                    "rate": (sum(ys) / len(ys)) if ys else None,
                    "n": len(ys),
                    "net": t.get("mean"),
                    "trades": t.get("trades"),
                }
            lines.append(
                "| %s | %s | %s | %s | %s |"
                % (
                    b,
                    cells[0][0],
                    cells[1][0],
                    "%+.1f %% (%d)" % (100 * cells[0][1]["mean"], cells[0][1]["trades"])
                    if cells[0][1].get("trades")
                    else "n/a",
                    "%+.1f %% %s (%d)" % (100 * cells[1][1]["mean"], ci(cells[1][1]["ci"]), cells[1][1]["trades"])
                    if cells[1][1].get("trades")
                    else "n/a",
                )
            )
        lines.append("")
    write("E_recurrence.md", lines)

    # F. operator controls
    lines = [
        "# F. Operator robustness (G1 KNOWN vs UNKNOWN, primary target)",
        "",
        "| split | full | without the dominant operator | within operators (Mantel-Haenszel) | "
        "operator-level means (operators with both) | strict non-hub funder (G2) |",
        "|---|---|---|---|---|---|",
    ]
    res["F"] = {}
    for s in SPLITS:
        top = Counter(r["operator"] for r in sp[s]).most_common(1)[0][0]
        wo = [r for r in sp[s] if r["operator"] != top]
        mh = mh_within(sp[s], K, U)
        byop: dict[str, dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))
        for r in sp[s]:
            y = y_of(r)
            if y is not None and (K(r) or U(r)):
                byop[r["operator"]][1 if K(r) else 0].append(y)
        both = [(sum(v[1]) / len(v[1]), sum(v[0]) / len(v[0])) for v in byop.values() if v[1] and v[0]]
        opl = (
            (
                "%d operators: %s vs %s"
                % (len(both), pct(sum(a for a, _ in both) / len(both)), pct(sum(b for _, b in both) / len(both)))
            )
            if both
            else "none"
        )
        res["F"][s] = {
            "full": rate_diff(sp[s], K, U),
            "without_top": rate_diff(wo, K, U),
            "mh": mh,
            "op_level": both,
            "strict": rate_diff(sp[s], lambda r: r["G2_strict"], lambda r: not r["G2_strict"]),
            "top": top,
        }
        lines.append(
            "| %s | %s | %s | %s | %s | %s |"
            % (
                s.upper(),
                dcell(res["F"][s]["full"]),
                dcell(res["F"][s]["without_top"]),
                ("%+.1f pts %s, %d operators, N %d" % (100 * mh["diff"], ci(mh["ci"]), mh["ops"], mh["n"]))
                if mh.get("diff") is not None
                else "n/a",
                opl,
                dcell(res["F"][s]["strict"]),
            )
        )
    lines += [
        "",
        "## Leave one operator out (VALIDATION, the 10 largest operators)",
        "",
        "| operator left out | alerts | KNOWN vs UNKNOWN |",
        "|---|---:|---|",
    ]
    res["F"]["loo"] = []
    for op, n in Counter(r["operator"] for r in sp["val"]).most_common(10):
        d = rate_diff([r for r in sp["val"] if r["operator"] != op], K, U)
        res["F"]["loo"].append((op, n, d.get("diff")))
        lines.append("| %s | %d | %s |" % (op[:16], n, dcell(d)))
    write("F_operators.md", lines)

    # G. forward returns
    lines = [
        "# G. Forward returns by G1 status (VALIDATION; TRAIN in derived/KG_results.json)",
        "",
        "Median point return / median MFE / median MAE / N observed, from each entry.",
        "",
    ]
    hs = (("5s", 5), ("10s", 10), ("30s", 30), ("60s", 60), ("5m", 300), ("15m", 900), ("1h", 3600))
    res["G"] = {}
    for lat in LATS:
        lines += ["## Entry %s" % lat, "", "| horizon | KNOWN | PARTIAL | UNKNOWN |", "|---|---|---|---|"]
        for lab, h in hs:
            cells = []
            for g in ("KNOWN", "PARTIAL", "UNKNOWN"):
                v = [r["o"][lat]["h%d" % h] for r in sp["val"] if r["G1"] == g and r["o"].get(lat)]
                v = [x for x in v if x["obs"] and x["ret"] is not None]
                cells.append(
                    "%+.1f %% / %.2f / %.2f / %d"
                    % (
                        100 * (pde.median([x["ret"] for x in v]) - 1),
                        pde.median([x["mfe"] for x in v]),
                        pde.median([x["mae"] for x in v]),
                        len(v),
                    )
                    if v
                    else "n/a"
                )
                res["G"].setdefault(lat, {}).setdefault(lab, {})[g] = len(v)
            lines.append("| %s | %s |" % (lab, " | ".join(cells)))
        lines.append("")
    lines += [
        "## Binary targets, entry +5 s, VALIDATION: KNOWN vs UNKNOWN",
        "",
        "| target | 60 s | 5 min | 15 min | 1 h |",
        "|---|---|---|---|---|",
    ]
    for k in (1.10, 1.25, 1.50, 2.00):
        cells = []
        for h in (60, 300, 900, 3600):
            d = rate_diff(sp["val"], K, U, lambda r, k=k, h=h: y_of(r, "L5", "y_%.2f_%d" % (k, h)))
            cells.append(
                "%s vs %s, %+.1f pts" % (pct(d.get("pa")), pct(d.get("pb")), 100 * d["diff"]) if "diff" in d else "n/a"
            )
        lines.append("| +%d %% | %s |" % (round(100 * (k - 1)), " | ".join(cells)))
    write("G_returns.md", lines)

    # H. trading
    th = {}
    for name in ("Model 1 baseline", "Model 3 baseline + group"):
        sc = sorted(fitted[name].p(r) for r in sp["train"])
        th[name] = sc[int(0.8 * (len(sc) - 1))]
    pops = {
        "all alerts": lambda r: True,
        "G1 KNOWN": K,
        "G1 PARTIAL": lambda r: r["G1"] == "PARTIAL",
        "G1 UNKNOWN": U,
        "Model 1 top 20 %": lambda r: fitted["Model 1 baseline"].p(r) >= th["Model 1 baseline"],
        "Model 3 top 20 %": lambda r: fitted["Model 3 baseline + group"].p(r) >= th["Model 3 baseline + group"],
    }
    lines = [
        "# H. Trading simulation ($500, costs of the post-detection-edge model)",
        "",
        "Primary strategy: entry +5 s, target +50 %, stop -15 %, 15-minute timeout.",
        "",
    ]
    res["H"] = {}
    for s in SPLITS:
        lines += ["## %s, primary strategy" % s.upper(), ""] + THEAD
        for pn, f in pops.items():
            t = trading([r for r in sp[s] if f(r)], *PRIMARY_T)
            res["H"].setdefault(s, {}).setdefault(pn, {})["primary"] = {k: v for k, v in t.items()}
            lines.append(trow(pn, t))
        lines.append("")
    lines += [
        "## VALIDATION, every entry and strategy: mean net return (trades), G1 KNOWN | G1 UNKNOWN | all",
        "",
        "| entry | " + " | ".join(STRATS) + " |",
        "|---|" + "---|" * len(STRATS),
    ]
    for lat in LATS:
        cells = []
        for st in STRATS:
            vals = []
            for f in (K, U, lambda r: True):
                t = trading([r for r in sp["val"] if f(r)], lat, st)
                vals.append(("%+.0f %% (%d)" % (100 * t["mean"], t["trades"])) if t.get("trades") else "n/a")
                res["H"].setdefault("grid", {}).setdefault(lat, {}).setdefault(st, []).append(t.get("mean"))
            cells.append(" / ".join(vals))
        lines.append("| %s | %s |" % (lat, " | ".join(cells)))
    lines += [
        "",
        "## VALIDATION, every entry and strategy: mean GROSS return before any cost, KNOWN | UNKNOWN | all",
        "",
        "| entry | " + " | ".join(STRATS) + " |",
        "|---|" + "---|" * len(STRATS),
    ]
    for lat in LATS:
        cells = []
        for st in STRATS:
            vals = []
            for f in (K, U, lambda r: True):
                t = trading([r for r in sp["val"] if f(r)], lat, st)
                vals.append(("%+.0f %%" % (100 * t["gross"])) if t.get("trades") else "n/a")
                res["H"].setdefault("grid_gross", {}).setdefault(lat, {}).setdefault(st, []).append(t.get("gross"))
            cells.append(" / ".join(vals))
        lines.append("| %s | %s |" % (lat, " | ".join(cells)))
    lines += [
        "",
        "## VALIDATION, primary strategy: sizes, depth and fill sensitivity (G1 KNOWN | all alerts)",
        "",
        "| variant | KNOWN mean net | all alerts mean net |",
        "|---|---:|---:|",
    ]
    for lab, key, strat in (
        ("$100", "net_100", PRIMARY_T[1]),
        ("$500", "net_500", PRIMARY_T[1]),
        ("$1,000", "net_1000", PRIMARY_T[1]),
        ("$500, depth x0.5", "net_500_k05", PRIMARY_T[1]),
        ("$500, depth x2", "net_500_k2", PRIMARY_T[1]),
        ("$500, take-profit at the next read", "net_500", "tp1.50_sl0.85_next"),
    ):
        a = trading([r for r in sp["val"] if K(r)], "L5", strat, key)
        b = trading(sp["val"], "L5", strat, key)
        lines.append(
            "| %s | %s | %s |"
            % (
                lab,
                ("%+.1f %%" % (100 * a["mean"])) if a.get("trades") else "n/a",
                ("%+.1f %%" % (100 * b["mean"])) if b.get("trades") else "n/a",
            )
        )
    # upper bound, added after reading the grids: the best gross cell of the KNOWN grid at every size. If even it
    # loses after costs at $100, no cell of the grid can carry a trade. Selected on VALIDATION, so not a strategy.
    best = max(
        ((lat, st) for lat in LATS for st in STRATS),
        key=lambda c: (
            res["H"]["grid_gross"][c[0]][c[1]][0] if res["H"]["grid_gross"][c[0]][c[1]][0] is not None else -9
        ),
    )
    lines += [
        "",
        "## Upper bound: the best gross cell of the KNOWN grid (%s, %s), every size, VALIDATION" % best,
        "",
        "| size | trades | gross | mean net [cluster CI] |",
        "|---|---:|---:|---|",
    ]
    res["H"]["upper_bound"] = {"cell": best}
    for key in ("net_100", "net_500", "net_1000"):
        t = trading([r for r in sp["val"] if K(r)], best[0], best[1], key)
        res["H"]["upper_bound"][key] = {"gross": t.get("gross"), "net": t.get("mean"), "ci": t.get("ci")}
        lines.append(
            "| %s | %d | %+.1f %% | %+.1f %% %s |"
            % (key.replace("net_", "$"), t["trades"], 100 * t["gross"], 100 * t["mean"], ci(t["ci"]))
        )
    write("H_trading.md", lines)

    # I. out of sample and J. decision
    v1 = res["rates"]["val"]["G1"]
    t1 = res["rates"]["train"]["G1"]
    pk = res["H"]["val"]["G1 KNOWN"]["primary"]
    mhv = res["F"]["val"]["mh"]
    mv = res["matched"]["val"]
    pred_holds = (
        v1.get("ci", (None,))[0] is not None
        and v1["ci"][0] > 0
        and t1.get("diff", 0) > 0
        and mhv.get("ci", (None,))[0] is not None
        and mhv["ci"][0] > 0
    )
    ll_better = dci[1] is not None and dci[1] < 0

    def above0(d: dict[str, Any]) -> bool:
        return d.get("ci", (None,))[0] is not None and d["ci"][0] > 0

    # section 7 as written: NO INCREMENTAL SIGNAL when the VALIDATION difference contains zero (or has the wrong
    # sign) in full, after matching or within operators, and Model 3 does not lower Model 1's log loss. A first
    # version of this test left the matched comparison out; it is part of the rule's text.
    fails_somewhere = not (above0(v1) and above0(mv) and above0(mhv))
    if fails_somewhere and not ll_better:
        cls = "NO INCREMENTAL SIGNAL"
    elif pk.get("mean") is None or pk["mean"] <= 0:
        cls = "STATISTICAL SIGNAL, NOT TRADABLE"
    elif pk["ci"][0] is None or pk["ci"][0] <= 0 or not (mv.get("diff") or 0) > 0:
        cls = "POTENTIAL TRADING SIGNAL"
    else:
        cls = "ROBUST OUT-OF-SAMPLE TRADING SIGNAL"
    res["decision"] = {
        "class": cls,
        "predictive_holds": pred_holds,
        "logloss_better": ll_better,
        "fails_full_matched_or_within": fails_somewhere,
    }
    lines = [
        "# I-J. Out of sample and decision",
        "",
        "| | TRAIN | VALIDATION |",
        "|---|---|---|",
        "| G1 KNOWN vs UNKNOWN, primary target | %s | %s |" % (dcell(t1), dcell(v1)),
        "| within operators (Mantel-Haenszel) | %s | %s |"
        % tuple(
            ("%+.1f pts %s" % (100 * res["F"][s]["mh"]["diff"], ci(res["F"][s]["mh"]["ci"])))
            if res["F"][s]["mh"].get("diff") is not None
            else "n/a"
            for s in SPLITS
        ),
        "| matched | %s | %s |"
        % tuple(
            ("%+.1f pts %s" % (100 * res["matched"][s]["diff"], ci(res["matched"][s]["ci"])))
            if res["matched"][s]["diff"] is not None
            else "n/a"
            for s in SPLITS
        ),
        "| primary strategy on KNOWN, mean net | %s | %s |"
        % tuple(
            (
                "%+.1f %% %s (N %d)"
                % (
                    100 * res["H"][s]["G1 KNOWN"]["primary"]["mean"],
                    ci(res["H"][s]["G1 KNOWN"]["primary"]["ci"]),
                    res["H"][s]["G1 KNOWN"]["primary"]["trades"],
                )
            )
            if res["H"][s]["G1 KNOWN"]["primary"].get("trades")
            else "n/a"
            for s in SPLITS
        ),
        "",
        "Log loss, Model 3 minus Model 1, VALIDATION: %+.4f [%+.4f, %+.4f]."
        % (res["delta_logloss"]["mean"], dci[0], dci[1]),
        "",
        "**Decision (rule of analysis_plan.md section 7): %s**" % cls,
    ]
    write("J_decision.md", lines)
    with open(os.path.join(D, "KG_results.json"), "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True, default=str)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
