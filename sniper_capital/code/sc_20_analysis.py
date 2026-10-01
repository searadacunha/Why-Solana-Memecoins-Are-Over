#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The analysis of analysis_plan.md on the frozen sniper-capital table.

S1  descriptive: winners against losers, every launch feature and the main sniper values, TRAIN and
    VALIDATION apart: N, median, p25, p75, ROC-AUC as the effect size.
S2  the central test of ticket / capital (a_med).
S3  threshold rules per family (TRAIN choice, 200 permutations, VALIDATION once), then every
    control of the plan for each family's best, and the classification.
Every rule and every control is evaluated on the launches where its variable is OBSERVED, with the
base rate of that population. Writes tables/S1_descriptive.md, S2_central.md, S3_rules.md and
derived/S_kept.json.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import random
import statistics
import sys
from collections import Counter, defaultdict
from typing import Any, Callable, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "post_detection_edge", "code"))
sys.path.insert(0, os.path.join(ROOT, "post_detection_forensics", "code"))
import fml  # noqa: E402
import pde  # noqa: E402

TABLE = os.path.join(STUDY, "derived", "sc_table.jsonl.gz")
FREEZE = os.path.join(STUDY, "derived", "SC_FREEZE.json")
TABLES = os.path.join(STUDY, "tables")
Y = "A_conf_2x_15m"
MIN_N, N_PERM, SEED, B = 40, 200, 20261001, 1000
FAMILIES = {
    "1 ticket / capital": ["a_med", "a_mean", "a_min", "a_max", "a_p25", "a_p75", "a_total"],
    "2 capital after / before": ["g_med", "g_mean", "g_min", "g_max"],
    "3 ticket / last funding": ["tl_med", "tl_min", "tl_max"],
    "4 time since last funding": ["age_med", "age_min", "age_max", "age_share_lt_1h", "age_share_lt_5min"],
    "5 last funding amount": ["amt_med", "amt_min", "amt_max", "amt_sum", "amt_hhi", "fc_med"],
    "6 funding about the ticket": ["fit_share_90_100", "fit_n_90_100", "fit_share_above_1"],
    "7 snipers by fraction risked": ["n_a_lt10", "n_a_ge25", "n_a_ge50", "n_a_ge75", "n_a_ge90", "share_a_ge50"],
    "8 topology": [
        "gen_n_funders",
        "gen_max_share",
        "gen_same",
        "gen_share_hub",
        "src_n",
        "src_max_funders",
        "last_n_funders",
        "last_max_share",
        "last_same",
        "fund_time_spread_s",
    ],
    "9 other aggregates": [
        "sum_ticket",
        "sum_capital",
        "hhi_capital",
        "hhi_ticket",
        "top1_capital_share",
        "top2_capital_share",
        "top3_capital_share",
        "n_snipers_here",
    ],
}
RATIO_EDGES = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90]
FC_EDGES = [0.10, 0.25, 0.50, 0.75, 1.0]
AGE_EDGES = [60, 300, 1800, 3600, 21600, 86400]
COUNT_VARS = {
    "n_a_lt10",
    "n_a_ge25",
    "n_a_ge50",
    "n_a_ge75",
    "n_a_ge90",
    "fit_n_90_100",
    "gen_n_funders",
    "src_n",
    "src_max_funders",
    "last_n_funders",
    "n_snipers_here",
}
CONTROLS = {
    "premium": ["premium"],
    "actor": ["actor"],
    "snipers": ["snipers"],
    "premium + actor + snipers": ["premium", "actor", "snipers"],
}


# ------------------------------------------------------------------ data ---- #
def load() -> list[dict[str, Any]]:
    doc = json.load(open(FREEZE))
    if hashlib.sha256(open(TABLE, "rb").read()).hexdigest() != doc["sha256"]:
        sys.exit("the sniper-capital table differs from the frozen one")
    with gzip.open(TABLE, "rt", encoding="utf8") as fh:
        return [json.loads(x) for x in fh]


def pop(rows: Sequence[dict[str, Any]], split: str, vs: Sequence[str]) -> list[dict[str, Any]]:
    """Launches of the split with an observed label and every variable in vs OBSERVED."""
    return [
        r
        for r in rows
        if r["split"] == split and r["y"].get(Y) is not None and all(r["f"].get(v) is not None for v in vs)
    ]


def q(v: Sequence[Optional[float]], p: float) -> Optional[float]:
    s = sorted(x for x in v if x is not None)
    return s[int(p * (len(s) - 1))] if s else None


def rate(k: int, n: int) -> str:
    return pde.rate_cell(k, n)


def lb(k: int, n: int) -> float:
    return (pde.wilson(k, n)[0] or 0.0) if n else 0.0


def fmt(x: Optional[float], p: str = "%.3f") -> str:
    return "n/a" if x is None else p % x


def write(name: str, lines: list[str]) -> None:
    os.makedirs(TABLES, exist_ok=True)
    with open(os.path.join(TABLES, name), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")


# ----------------------------------------------------------------- atoms ---- #
def holds(f: dict[str, Any], a: tuple) -> bool:
    v, op, x, z = a
    w = f.get(v)
    if w is None:
        return False
    return {
        "le": lambda: w <= x,
        "gt": lambda: w > x,
        "in": lambda: x < w <= z,
        "ge": lambda: w >= x,
        "lt": lambda: w < x,
        "zone": lambda: x <= w < z,
    }[op]()


def text(a: tuple) -> str:
    v, op, x, z = a
    return {
        "le": lambda: "%s <= %.4g" % (v, x),
        "gt": lambda: "%s > %.4g" % (v, x),
        "in": lambda: "%.4g < %s <= %.4g" % (x, v, z),
        "ge": lambda: "%s >= %.4g" % (v, x),
        "lt": lambda: "%s < %.4g" % (v, x),
        "zone": lambda: "%.4g <= %s < %.4g" % (x, v, z),
    }[op]()


def atoms_for(v: str, tr: Sequence[dict[str, Any]]) -> list[tuple]:
    xs = [r["f"][v] for r in tr]
    if len(xs) < MIN_N or len(set(xs)) < 2:
        return []
    qs = sorted({q(xs, k / 10) for k in range(1, 10)})
    out = [(v, "le", t, None) for t in qs] + [(v, "gt", t, None) for t in qs]
    out += [(v, "in", a, b) for i, a in enumerate(qs) for b in qs[i + 1 :]]
    edges = (
        RATIO_EDGES
        if v.startswith(("a_", "tl_"))
        else FC_EDGES
        if v == "fc_med"
        else AGE_EDGES
        if v.startswith("age_") and not v.startswith("age_share")
        else None
    )
    if edges:
        bounds = [0.0] + edges + [float("inf")]
        out += [(v, "zone", a, b) for a, b in zip(bounds, bounds[1:])]
        out += [(v, "lt", e, None) for e in edges] + [(v, "ge", e, None) for e in edges]
    if v in COUNT_VARS:
        out += [(v, "ge", g, None) for g in (1, 2, 3, 4, 5)] + [(v, "lt", 1, None)]
    return sorted(set(out), key=lambda a: (a[1], a[2], a[3] if a[3] is not None else 0))


# ---------------------------------------------------------- reference models #
def ctl_x(r: dict[str, Any], names: Sequence[str]) -> dict[str, Any]:
    return {n: r["ctl"].get(n) for n in names}


def fit_ref(tr: Sequence[dict[str, Any]], names: list[str]) -> Callable[[Sequence[dict[str, Any]]], list[float]]:
    prep = fml.Prep(names).fit([ctl_x(r, names) for r in tr])
    m = fml.Boost(150).fit(
        prep.transform([ctl_x(r, names) for r in tr]), [r["y"][Y] for r in tr], [prep.cuts[n] for n in names]
    )
    return lambda rows: m.score(prep.transform([ctl_x(r, names) for r in rows]))


def cluster_boot(
    items: Sequence[tuple[str, Any]], stat: Callable[[list[Any]], Optional[float]]
) -> tuple[Optional[float], Optional[float]]:
    by: dict[str, list[Any]] = defaultdict(list)
    for c, v in items:
        by[c].append(v)
    keys = sorted(by)
    rng = random.Random(SEED)
    out = []
    for _ in range(B):
        s = stat([v for _ in keys for v in by[keys[rng.randrange(len(keys))]]])
        if s is not None:
            out.append(s)
    if len(out) < B // 2:
        return None, None
    out.sort()
    return out[int(0.025 * (len(out) - 1))], out[int(0.975 * (len(out) - 1))]


def resid_lift(
    tr: Sequence[dict[str, Any]], va: Sequence[dict[str, Any]], pred: Callable[[dict[str, Any]], bool], names: list[str]
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    p = fit_ref(tr, names)(va)
    items = [(r["cluster"], (int(pred(r)), r["y"][Y] - pi)) for r, pi in zip(va, p)]

    def stat(s: list[tuple[int, float]]) -> Optional[float]:
        a = [d for g, d in s if g]
        b = [d for g, d in s if not g]
        return sum(a) / len(a) - sum(b) / len(b) if a and b else None

    return (stat([v for _, v in items]), *cluster_boot(items, stat))


def mh(strata: dict[Any, list[tuple[int, int]]], odds: bool = False) -> Optional[float]:
    num = den = 0.0
    for v in strata.values():
        t = [y for g, y in v if g]
        c = [y for g, y in v if not g]
        if not t or not c:
            continue
        n = len(t) + len(c)
        if odds:
            a, b = sum(t), len(t) - sum(t)
            cc, d = sum(c), len(c) - sum(c)
            num += a * d / n
            den += b * cc / n
        else:
            w = len(t) * len(c) / n
            num += w * (sum(t) / len(t) - sum(c) / len(c))
            den += w
    return num / den if den else None


def mh_ci(
    strata: dict[Any, list[tuple[int, int]]], odds: bool = False
) -> tuple[Optional[float], Optional[float], Optional[float], int]:
    rng = random.Random(SEED)
    bs = []
    for _ in range(B):
        e = mh({k: [v[rng.randrange(len(v))] for _ in v] for k, v in strata.items()}, odds)
        if e is not None:
            bs.append(e)
    bs.sort()
    usable = sum(1 for v in strata.values() if any(g for g, _ in v) and any(not g for g, _ in v))
    if len(bs) < B // 2:
        return mh(strata, odds), None, None, usable
    return mh(strata, odds), bs[int(0.025 * (len(bs) - 1))], bs[int(0.975 * (len(bs) - 1))], usable


def tercile(cuts: tuple[Optional[float], Optional[float]], x: Optional[float]) -> Optional[int]:
    if x is None or cuts[0] is None:
        return None
    return 0 if x <= cuts[0] else (1 if x <= cuts[1] else 2)


# --------------------------------------------------------------------- S1 --- #
def s1(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "# S1. Winners against losers (confirmed 2x within 15 min of the alert)",
        "",
        "Launch features: only launches where the feature is OBSERVED (every sniper). ROC-AUC: above 0.5 when "
        "winners have the higher value. TRAIN and VALIDATION apart, never pooled.",
        "",
        "| feature | split | N win / lose | median win | p25-p75 win | median lose | p25-p75 lose | ROC-AUC |",
        "|---|---|---|---:|---|---:|---|---:|",
    ]
    for fam, vs in FAMILIES.items():
        for v in vs:
            for sp in ("train", "val"):
                p = pop(rows, sp, [v])
                w = [r["f"][v] for r in p if r["y"][Y] == 1]
                lo = [r["f"][v] for r in p if r["y"][Y] == 0]
                if not w or not lo:
                    continue
                a = pde.auc([r["f"][v] for r in p], [r["y"][Y] for r in p])
                lines.append(
                    "| %s | %s | %d / %d | %.4g | %.4g-%.4g | %.4g | %.4g-%.4g | %s |"
                    % (
                        v,
                        sp.upper(),
                        len(w),
                        len(lo),
                        statistics.median(w),
                        q(w, 0.25),
                        q(w, 0.75),
                        statistics.median(lo),
                        q(lo, 0.25),
                        q(lo, 0.75),
                        fmt(a),
                    )
                )
    lines += [
        "",
        "## Sniper values (one row per sniper; launches counted once per sniper)",
        "",
        "| value | split | N snipers of winners / losers | median win | p25-p75 win | median lose | p25-p75 lose |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for key in ("capital", "ticket", "a", "g", "last_amount", "last_age_s", "ticket_over_last", "n_prior"):
        for sp in ("train", "val"):
            w = [
                s[key]
                for r in rows
                if r["split"] == sp and r["y"].get(Y) == 1
                for s in r["snipers"]
                if s.get(key) is not None
            ]
            lo = [
                s[key]
                for r in rows
                if r["split"] == sp and r["y"].get(Y) == 0
                for s in r["snipers"]
                if s.get(key) is not None
            ]
            if w and lo:
                lines.append(
                    "| %s | %s | %d / %d | %.4g | %.4g-%.4g | %.4g | %.4g-%.4g |"
                    % (
                        key,
                        sp.upper(),
                        len(w),
                        len(lo),
                        statistics.median(w),
                        q(w, 0.25),
                        q(w, 0.75),
                        statistics.median(lo),
                        q(lo, 0.25),
                        q(lo, 0.75),
                    )
                )
    return lines


# --------------------------------------------------------------------- S2 --- #
def s2(rows: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    v = "a_med"
    tr, va = pop(rows, "train", [v]), pop(rows, "val", [v])
    out: dict[str, Any] = {}
    a_tr = pde.auc([r["f"][v] for r in tr], [r["y"][Y] for r in tr])
    a_va = pde.auc([r["f"][v] for r in va], [r["y"][Y] for r in va])
    sign = 1 if (a_tr or 0.5) >= 0.5 else -1
    out["auc"] = [a_tr, a_va, sign]
    lines = [
        "# S2. The central test: does ticket / capital add anything?",
        "",
        "`a_med` = the launch median of ticket / capital before the buy. N: TRAIN %d, VALIDATION %d (every "
        "sniper OBSERVED for all of them)." % (len(tr), len(va)),
        "",
        "- ROC-AUC, oriented on TRAIN (%s): TRAIN %s, VALIDATION %s."
        % (
            "higher a_med, more 2x" if sign > 0 else "lower a_med, more 2x",
            fmt(a_tr if sign > 0 else 1 - a_tr),
            fmt(None if a_va is None else (a_va if sign > 0 else 1 - a_va)),
        ),
    ]
    base_names = ["premium", "actor", "snipers"]

    def model(names: list[str], with_a: bool) -> list[float]:
        def x(r: dict[str, Any]) -> dict[str, Any]:
            d = ctl_x(r, names)
            if with_a:
                d["a_med"] = r["f"]["a_med"]
            return d

        allnames = names + (["a_med"] if with_a else [])
        prep = fml.Prep(allnames).fit([x(r) for r in tr])
        m = fml.Boost(150).fit(
            prep.transform([x(r) for r in tr]), [r["y"][Y] for r in tr], [prep.cuts[n] for n in allnames]
        )
        return m.score(prep.transform([x(r) for r in va]))

    s_with, s_without = model(base_names, True), model(base_names, False)
    items = [(r["cluster"], (a, b, r["y"][Y])) for r, a, b in zip(va, s_with, s_without)]

    def dstat(s: list[tuple[float, float, int]]) -> Optional[float]:
        ys = [t[2] for t in s]
        if not 0 < sum(ys) < len(ys):
            return None
        return fml.roc_auc([t[0] for t in s], ys) - fml.roc_auc([t[1] for t in s], ys)

    d = dstat([x for _, x in items])
    lo, hi = cluster_boot(items, dstat)
    out["gain"] = [d, lo, hi]
    lines.append(
        "- VALIDATION ROC-AUC of premium + actor + snipers + a_med minus premium + actor + snipers (TRAIN "
        "boosting): %s [%s, %s]." % (fmt(d, "%+.3f"), fmt(lo, "%+.3f"), fmt(hi, "%+.3f"))
    )
    # matched
    med_a = q([r["f"][v] for r in tr], 0.5)
    pc = (q([r["ctl"]["premium"] for r in tr], 1 / 3), q([r["ctl"]["premium"] for r in tr], 2 / 3))
    lines += [
        "",
        "## Matched comparison: a_med above its TRAIN median (%.3f) against below, within week x premium "
        "tercile x actor x snipers (4 or 5+)" % med_a,
        "",
    ]
    out["matched"] = {}
    for lab, sel in (
        ("all launches", lambda r: True),
        ("without the dominant operator", None),
        ("single-operator launches only", lambda r: r["actor"] != "grouped"),
    ):
        for sp, rr in (("TRAIN", tr), ("VALIDATION", va)):
            if sel is None:
                top = Counter(r["cluster"] for r in rr).most_common(1)[0][0]
                use = [r for r in rr if r["cluster"] != top]
            else:
                use = [r for r in rr if sel(r)]
            st: dict[Any, list[tuple[int, int]]] = defaultdict(list)
            for r in use:
                key = (
                    int(r["t"] // (7 * 86400)),
                    tercile(pc, r["ctl"]["premium"]),
                    r["ctl"]["actor"],
                    (r["ctl"]["snipers"] or 0) >= 5,
                )
                if None not in key:
                    st[key].append((int(r["f"][v] > med_a), r["y"][Y]))
            e, l2, h2, us = mh_ci(st)
            out["matched"][(lab, sp).__str__()] = [e, l2, h2, us]
            lines.append(
                "- %s, %s (%d launches, %d strata with both groups): %s pts [%s, %s]."
                % (
                    lab,
                    sp,
                    len(use),
                    us,
                    fmt(None if e is None else 100 * e, "%+.1f"),
                    fmt(None if l2 is None else 100 * l2, "%+.1f"),
                    fmt(None if h2 is None else 100 * h2, "%+.1f"),
                )
            )
    return lines, out


# --------------------------------------------------------------------- S3 --- #
def search_family(rows: list[dict[str, Any]], vs: list[str]) -> tuple[list[tuple], list[float]]:
    res = []
    null = [-1.0] * N_PERM
    for v in vs:
        tr = pop(rows, "train", [v])
        if len(tr) < MIN_N:
            continue
        ys = [r["y"][Y] for r in tr]
        base = sum(ys) / len(ys)
        ybits = sum(1 << i for i, y in enumerate(ys) if y == 1)
        perms = []
        for p in range(N_PERM):
            yy = list(ys)
            random.Random(SEED + p).shuffle(yy)
            perms.append(sum(1 << i for i, y in enumerate(yy) if y == 1))
        for a in atoms_for(v, tr):
            m = sum(1 << i for i, r in enumerate(tr) if holds(r["f"], a))
            n = m.bit_count()
            if n < MIN_N or n == len(tr):
                continue
            k = (m & ybits).bit_count()
            res.append((lb(k, n) - base, n, k, a, base, len(tr)))
            for p in range(N_PERM):
                kp = (m & perms[p]).bit_count()
                if kp > (null[p] + base) * n:
                    null[p] = max(null[p], lb(kp, n) - base)
    res.sort(key=lambda z: (-z[0], -z[1]))
    return res, null


def evaluate(rows: list[dict[str, Any]], a: tuple) -> dict[str, Any]:
    v = a[0]
    tr, va = pop(rows, "train", [v]), pop(rows, "val", [v])
    pred = lambda r: holds(r["f"], a)  # noqa: E731
    d: dict[str, Any] = {
        "rule": text(a),
        "var": v,
        "n_labeled": {
            "train": len([r for r in rows if r["split"] == "train" and r["y"].get(Y) is not None]),
            "val": len([r for r in rows if r["split"] == "val" and r["y"].get(Y) is not None]),
        },
    }
    for sp, rr in (("train", tr), ("val", va)):
        sel = [r for r in rr if pred(r)]
        k = sum(r["y"][Y] for r in sel)
        base = sum(r["y"][Y] for r in rr) / len(rr)
        d[sp] = {
            "N_pop": len(rr),
            "n": len(sel),
            "k": k,
            "base": base,
            "lb": lb(k, len(sel)),
            "rates": {
                lab: (sum(1 for r in sel if r["y"].get(lab) == 1), sum(1 for r in sel if r["y"].get(lab) is not None))
                for lab in ("A_conf_2x_5m", "A_conf_2x_1h", "A_conf_1.5x_15m", "A_conf_3x_15m")
            },
        }
    d["val_holds"] = d["val"]["n"] > 0 and d["val"]["lb"] > d["val"]["base"]
    # controls
    d["resid"] = {name: resid_lift(tr, va, pred, names) for name, names in CONTROLS.items()}
    sel = [r for r in va if pred(r)]
    cc = Counter(r["cluster"] for r in sel)
    top, topn = cc.most_common(1)[0] if cc else (None, 0)
    d["top_cluster_share"] = topn / len(sel) if sel else None

    def holds_in(rr: list[dict[str, Any]]) -> tuple[bool, int, int, float]:
        s = [r for r in rr if pred(r)]
        k = sum(r["y"][Y] for r in s)
        base = sum(r["y"][Y] for r in rr) / len(rr) if rr else 0.0
        return (len(s) > 0 and lb(k, len(s)) > base), k, len(s), base

    d["without_dominant"] = holds_in([r for r in va if r["cluster"] != top])
    d["single_only"] = holds_in([r for r in va if r["actor"] != "grouped"])
    half = sorted(r["t"] for r in va)[len(va) // 2]
    d["halves"] = [holds_in([r for r in va if (r["t"] < half) == first]) for first in (True, False)]
    d["halves_above"] = [h[2] > 0 and h[1] / h[2] > h[3] for h in d["halves"]]
    # logistic models: signal, + premium, + operator, + both; against the same without the signal
    d["models"] = {}
    for lab, names in (
        ("signal alone", []),
        ("+ premium", ["premium"]),
        ("+ operator", ["actor"]),
        ("+ premium + operator", ["premium", "actor"]),
    ):

        def x(r: dict[str, Any], names: list[str] = names, with_s: bool = True) -> dict[str, Any]:
            z = ctl_x(r, names)
            if with_s:
                z["signal"] = 1.0 if pred(r) else 0.0
            return z

        sc = {}
        for with_s in (True, False):
            nm = names + (["signal"] if with_s else [])
            if not nm:
                sc[with_s] = [0.0] * len(va)
                continue
            prep = fml.Prep(nm).fit([x(r, names, with_s) for r in tr])
            m = fml.LogReg(1.0).fit(prep.transform([x(r, names, with_s) for r in tr]), [r["y"][Y] for r in tr])
            sc[with_s] = m.score(prep.transform([x(r, names, with_s) for r in va]))
        yv = [r["y"][Y] for r in va]
        items = [(r["cluster"], (s1_, s0_, y)) for r, s1_, s0_, y in zip(va, sc[True], sc[False], yv)]

        def dstat(s: list[tuple[float, float, int]]) -> Optional[float]:
            ys = [t[2] for t in s]
            if not 0 < sum(ys) < len(ys):
                return None
            a0 = fml.roc_auc([t[1] for t in s], ys) if len(set(t[1] for t in s)) > 1 else 0.5
            return fml.roc_auc([t[0] for t in s], ys) - a0

        auc1 = fml.roc_auc(sc[True], yv)
        d["models"][lab] = {
            "auc": auc1,
            "pr_auc": fml.pr_auc(sc[True], yv),
            "gain": dstat([z for _, z in items]),
            "gain_ci": cluster_boot(items, dstat),
        }
    pc = (q([r["ctl"]["premium"] for r in tr], 1 / 3), q([r["ctl"]["premium"] for r in tr], 2 / 3))
    st: dict[Any, list[tuple[int, int]]] = defaultdict(list)
    for r in va:
        key = (tercile(pc, r["ctl"]["premium"]), r["ctl"]["actor"])
        if None not in key:
            st[key].append((int(pred(r)), r["y"][Y]))
    d["mh_or"] = mh_ci(st, odds=True)
    return d


def classify(d: dict[str, Any], p: float, coverage: float) -> str:
    pa = d["resid"]["premium + actor + snipers"]
    if coverage < 0.5 or d["val"]["n"] < 30:
        return "INSUFFICIENT DATA"
    if p >= 0.05:
        return "NO SIGNAL"
    if not d["val_holds"]:
        return "TRAIN OVERFIT"
    if not (pa[1] is not None and pa[1] > 0) or not d["without_dominant"][0] or not d["single_only"][0]:
        return "PRICE/OPERATOR CONFOUNDED"
    if all(d["halves_above"]):
        return "PROMISING BUT UNCONFIRMED"
    return "PRICE/OPERATOR CONFOUNDED"


def s3(rows: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    n_lab = {sp: sum(1 for r in rows if r["split"] == sp and r["y"].get(Y) is not None) for sp in ("train", "val")}
    lines = [
        "# S3. Threshold rules per family (TRAIN choice, VALIDATION once) and their controls",
        "",
        "Metric: Wilson 95 %% lower bound of the TRAIN rate minus the TRAIN base of the launches where the "
        "variable is OBSERVED, at least %d launches. Labeled launches: TRAIN %d, VALIDATION %d."
        % (MIN_N, n_lab["train"], n_lab["val"]),
        "",
    ]
    kept: dict[str, Any] = {}
    for fam, vs in FAMILIES.items():
        res, null = search_family(rows, vs)
        if not res:
            continue
        s, n, k, a, base, npop = res[0]
        p = sum(1 for x in null if x >= s) / N_PERM
        d = evaluate(rows, a)
        cov = min(len(pop(rows, "val", [v])) / n_lab["val"] for v in [a[0]])
        cls = classify(d, p, cov)
        d.update({"family": fam, "metric": s, "p": p, "class": cls, "n_rules": len(res)})
        kept[fam] = d
        t, v_ = d["train"], d["val"]
        lines += [
            "## %s: `%s`" % (fam, d["rule"]),
            "",
            "- Rules evaluated: %d. TRAIN metric %+.3f, permutation p %.3f (null best: median %+.3f, 95th "
            "%+.3f)." % (len(res), s, p, sorted(null)[N_PERM // 2], sorted(null)[int(0.95 * N_PERM)]),
            "- Coverage: %s OBSERVED on %d of %d TRAIN and %d of %d VALIDATION labeled launches."
            % (a[0], t["N_pop"], n_lab["train"], v_["N_pop"], n_lab["val"]),
            "- TRAIN %s against a base of %.1f %%; VALIDATION %s against %.1f %%, lower bound %.1f %%: %s."
            % (
                rate(t["k"], t["n"]),
                100 * t["base"],
                rate(v_["k"], v_["n"]),
                100 * v_["base"],
                100 * v_["lb"],
                "holds" if d["val_holds"] else "does not hold",
            ),
            "- Other labels, VALIDATION selection: 2x 5 min %s, 2x 1 h %s, 1.5x 15 min %s, 3x 15 min %s."
            % tuple(
                rate(*v_["rates"][lab]).split(" [")[0]
                for lab in ("A_conf_2x_5m", "A_conf_2x_1h", "A_conf_1.5x_15m", "A_conf_3x_15m")
            ),
        ]
        for name, (e, lo, hi) in d["resid"].items():
            lines.append(
                "- Lift beyond %s: %s pts [%s, %s]%s."
                % (
                    name,
                    fmt(None if e is None else 100 * e, "%+.1f"),
                    fmt(None if lo is None else 100 * lo, "%+.1f"),
                    fmt(None if hi is None else 100 * hi, "%+.1f"),
                    "" if lo is not None and lo > 0 else " (CI reaches 0)",
                )
            )
        wd, so = d["without_dominant"], d["single_only"]
        lines += [
            "- Largest operator: %.0f %% of the VALIDATION selection. Without it: %s against %.1f %% (%s). "
            "Single-operator launches only: %s against %.1f %% (%s)."
            % (
                100 * (d["top_cluster_share"] or 0),
                rate(wd[1], wd[2]),
                100 * wd[3],
                "holds" if wd[0] else "does not hold",
                rate(so[1], so[2]),
                100 * so[3],
                "holds" if so[0] else "does not hold",
            ),
            "- VALIDATION halves: %s against %.1f %%; %s against %.1f %%."
            % (
                rate(d["halves"][0][1], d["halves"][0][2]),
                100 * d["halves"][0][3],
                rate(d["halves"][1][1], d["halves"][1][2]),
                100 * d["halves"][1][3],
            ),
        ]
        for lab, m in d["models"].items():
            lines.append(
                "- Logistic, %s: VALIDATION ROC-AUC %s, PR-AUC %s, gain from the signal %s [%s, %s]."
                % (
                    lab,
                    fmt(m["auc"]),
                    fmt(m["pr_auc"]),
                    fmt(m["gain"], "%+.3f"),
                    fmt(m["gain_ci"][0], "%+.3f"),
                    fmt(m["gain_ci"][1], "%+.3f"),
                )
            )
        o = d["mh_or"]
        lines += [
            "- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: %s [%s, %s] "
            "(%d strata with both groups)." % (fmt(o[0], "%.2f"), fmt(o[1], "%.2f"), fmt(o[2], "%.2f"), o[3]),
            "",
            "**Classification: %s**" % cls,
            "",
        ]
    return lines, kept


def main() -> None:
    rows = load()
    write("S1_descriptive.md", s1(rows))
    l2, central = s2(rows)
    write("S2_central.md", l2)
    l3, kept = s3(rows)
    write("S3_rules.md", l3)
    with open(os.path.join(STUDY, "derived", "S_kept.json"), "w") as fh:
        json.dump({"central": central, "rules": kept}, fh, indent=1, default=str)
    print("\n".join(l2))
    for fam, d in kept.items():
        print(
            "%-30s %-26s p %.3f TRAIN %s VAL %s base %.1f %%  %s"
            % (
                fam,
                d["class"],
                d["p"],
                rate(d["train"]["k"], d["train"]["n"]).split(" [")[0],
                rate(d["val"]["k"], d["val"]["n"]),
                100 * d["val"]["base"],
                d["rule"],
            )
        )


if __name__ == "__main__":
    main()
