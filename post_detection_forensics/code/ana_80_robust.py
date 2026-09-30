#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steps 8, 9 and 10 of analysis_plan.md, on the two signals steps 6 and 7 kept:
the rule of D6 and the top 20 % (TRAIN threshold) of the gate model of D7
("screened": step 1 features passing BH in TRAIN, plus actor and premium).

8  Robustness on VALIDATION: the 7 pre-declared variants (window 10 / 20 min,
   threshold 1.8 / 2.2x, single read, cut-off -2 / -5 s), VALIDATION halves,
   the calendar months and the weeks, each with its split named.
9  Mechanics: Spearman of the signal with P0, premium, pool reserve, curve
   progress, actor and funding features; 2x2 overlap with actor and premium
   band; and (amendment of 2026-09-29) the signal's lift beyond a reference
   model of P0, premium and actor (boosting, 150 rounds, fitted on TRAIN):
   on VALIDATION, observed minus expected inside the signal minus the same
   outside it, cluster-bootstrap CI. A lift whose CI reaches 0 is explained
   by P0, premium and actor. The lift within premium tercile x P0 tercile x
   actor strata is reported beside it: a null control on synthetic data showed
   that coarse strata leave premium confounding inside each tercile.
10 Matched comparison: within strata of week x premium tercile x number of
   core wallets x bundle SOL (TRAIN medians), common funding (one funder for
   >= 2 core wallets) vs not; Mantel-Haenszel risk difference with a
   stratified bootstrap CI. The independent-actor count is not a stratum: it
   is built from shared funders, hence from the treatment itself.
"""
from __future__ import annotations

import json
import os
import random
from collections import defaultdict
from typing import Any, Callable, Optional

import ana_lib as L
import fml

VARIANTS = [("window 10 min", "A_conf_2x_10m", "A"), ("window 20 min", "A_conf_2x_20m", "A"),
            ("threshold 1.8x", "A_conf_1.8x_15m", "A"), ("threshold 2.2x", "A_conf_2.2x_15m", "A"),
            ("single read", "A_single_2x_15m", "A"), ("cut-off -2 s", L.PRIMARY, "A2"),
            ("cut-off -5 s", L.PRIMARY, "A5")]
Strata = dict[tuple, list[tuple[int, int]]]


def signals() -> dict[str, Callable[[dict[str, Any]], bool]]:
    rule = json.load(open(os.path.join(L.FB.DERIVED, "D6_kept_rule.json")))
    model = json.load(open(os.path.join(L.FB.DERIVED, "D7_gate_model.json")))
    prep = fml.Prep.load(model["prep"])

    def in_rule(x: dict[str, Any]) -> bool:
        for f, op, t in rule["rule"]:
            v = x.get(f)
            if v is None or not (v <= t if op == "<=" else v > t):
                return False
        return True

    def in_model(x: dict[str, Any]) -> bool:
        return fml.score_state(model["state"], prep.transform([x]))[0] >= model["train_thr20"]
    out = {"model 'screened' (%s), top 20 %% by the TRAIN threshold" % model["kind"]: in_model}
    if rule["rule"] is not None:
        out = {"rule: " + rule["text"]: in_rule, **out}
    return out


def mh(strata: Strata) -> Optional[float]:
    """Mantel-Haenszel risk difference, treated (1) minus untreated (0)."""
    num = den = 0.0
    for v in strata.values():
        t = [y for g, y in v if g]
        c = [y for g, y in v if not g]
        if not t or not c:
            continue
        w = len(t) * len(c) / (len(t) + len(c))
        num += w * (sum(t) / len(t) - sum(c) / len(c))
        den += w
    return num / den if den else None


def mh_ci(strata: Strata) -> tuple[Optional[float], Optional[float], Optional[float], int]:
    """Estimate, 95 % stratified-bootstrap CI, and the number of strata holding both groups."""
    rng = random.Random(L.SEED)
    bs = []
    for _ in range(L.B):
        e = mh({k: [v[rng.randrange(len(v))] for _ in v] for k, v in strata.items()})
        if e is not None:
            bs.append(e)
    bs.sort()
    usable = sum(1 for v in strata.values() if any(g for g, _ in v) and any(not g for g, _ in v))
    if not bs:
        return mh(strata), None, None, usable
    return mh(strata), bs[int(0.025 * (len(bs) - 1))], bs[int(0.975 * (len(bs) - 1))], usable


def pts(e: Optional[float]) -> str:
    return "n/a" if e is None else "%+.1f" % (100 * e)


def tercile(cuts: tuple[Optional[float], Optional[float]], v: Optional[float]) -> Optional[int]:
    if v is None or cuts[0] is None:
        return None
    return 0 if v <= cuts[0] else (1 if v <= cuts[1] else 2)


def main() -> None:
    rows = L.load()
    val = [r for r in rows if r["split"] == "val"]
    trx = [r["fA"] for r in rows if r["split"] == "train"]
    cut = {f: (L.q([x.get(f) for x in trx], 1 / 3), L.q([x.get(f) for x in trx], 2 / 3))
           for f in ("p_entry_over_operator", "p_log_p0")}
    med = {f: L.q([x.get(f) for x in trx], 0.5) for f in ("b_core_n", "b_core_sol")}
    # reference model of what P0, premium and actor alone predict (TRAIN fit, fixed configuration)
    ref_names = ["c_actor_grouped", "p_entry_over_operator", "p_log_p0"]
    tr = L.xy(rows, "train")
    rprep = fml.Prep(ref_names).fit([x for _, x, _ in tr])
    ref = fml.Boost(150).fit(rprep.transform([x for _, x, _ in tr]), [y for _, _, y in tr],
                             [rprep.cuts[f] for f in ref_names])
    lines = ["# D8. Robustness, mechanics and matched comparison", ""]
    summary: dict[str, Any] = {}
    for name, fn in signals().items():
        sm: dict[str, Any] = summary.setdefault(name, {"rho": {}, "small_2x2": []})
        lines += ["## %s" % name, "", "| variant | signal | base | holds (Wilson lower bound above base) |",
                  "|---|---|---|---|"]
        held = 0
        for vname, lab, cu in [("primary", L.PRIMARY, "A")] + VARIANTS:
            ys = [(fn(r["f" + cu]), r["y"][lab]) for r in val if r["y"].get(lab) is not None]
            k = sum(y for s, y in ys if s)
            n = sum(1 for s, _ in ys if s)
            base = sum(y for _, y in ys) / len(ys)
            ok = n > 0 and (L.pde.wilson(k, n)[0] or 0) > base
            held += ok and vname != "primary"
            if vname == "primary":
                sm["primary"] = {"k": k, "n": n, "base": base, "lb": L.pde.wilson(k, n)[0] if n else None}
            lines.append("| %s | %s | %.1f %% | %s |" % (vname, L.rate(k, n), 100 * base, "yes" if ok else "no"))
        lines += ["", "Variants held: %d of %d." % (held, len(VARIANTS))]
        sm["held"] = held
        sm["perf"] = {}
        for sp in ("train", "val"):
            sel = [r for r in rows if r["split"] == sp and r["y"].get(L.PRIMARY) is not None]
            ins = [r for r in sel if fn(r["fA"])]
            sm["perf"][sp] = {"k": sum(r["y"][L.PRIMARY] for r in ins), "n": len(ins),
                              "base": sum(r["y"][L.PRIMARY] for r in sel) / len(sel),
                              "period": [min(r["utc"][:10] for r in sel), max(r["utc"][:10] for r in sel)]}
        half = sorted(r["t"] for r in val)[len(val) // 2]
        for lab_, cond in (("VALIDATION first half", lambda r: r["t"] < half),
                           ("VALIDATION second half", lambda r: r["t"] >= half)):
            ys = [(fn(r["fA"]), r["y"][L.PRIMARY]) for r in val if cond(r) and r["y"].get(L.PRIMARY) is not None]
            lines.append("- %s: signal %s, base %.1f %%." % (lab_, L.rate(sum(y for s, y in ys if s),
                                                                         sum(1 for s, _ in ys if s)),
                                                            100 * sum(y for _, y in ys) / len(ys)))
        for month in ("08", "09"):
            for sp in ("train", "val"):
                ys = [(fn(r["fA"]), r["y"][L.PRIMARY]) for r in rows if r["utc"][5:7] == month and r["split"] == sp
                      and r["y"].get(L.PRIMARY) is not None]
                if ys:
                    lines.append("- month %s, %s rows: signal %s, base %.1f %%." % (
                        month, sp.upper(), L.rate(sum(y for s, y in ys if s), sum(1 for s, _ in ys if s)),
                        100 * sum(y for _, y in ys) / len(ys)))
        for wk in sorted({int(r["t"] // (7 * 86400)) for r in rows}):
            for sp in ("train", "val"):
                ys = [(fn(r["fA"]), r["y"][L.PRIMARY]) for r in rows if int(r["t"] // (7 * 86400)) == wk
                      and r["split"] == sp and r["y"].get(L.PRIMARY) is not None]
                if ys:
                    first = min(r["utc"][:10] for r in rows if int(r["t"] // (7 * 86400)) == wk)
                    lines.append("- week from %s, %s rows: signal %s, base %.1f %%." % (
                        first, sp.upper(), L.rate(sum(y for s, y in ys if s), sum(1 for s, _ in ys if s)),
                        100 * sum(y for _, y in ys) / len(ys)))
        # mechanics
        mem = [1.0 if fn(r["fA"]) else 0.0 for r in val]
        lines += ["", "Mechanics on VALIDATION (Spearman with the signal):", ""]
        for f in ("p_log_p0", "p_entry_over_operator", "p_pool_sol", "p_reserve_vs_p0", "p_curve_left_sol",
                  "b_core_supply", "c_actor_grouped", "f_same_funder_multi", "g_core_common_ratio", "b_core_n"):
            pairs = [(m_, r["fA"].get(f)) for m_, r in zip(mem, val) if r["fA"].get(f) is not None]
            rho = L.spearman([a for a, _ in pairs], [b for _, b in pairs]) if pairs else 0.0
            sm["rho"][f] = rho
            lines.append("- %s: %+.2f%s" % (f, rho, "  (NOT SEPARABLE, |rho| >= 0.8)" if abs(rho) >= 0.8 else ""))
        # 2x2 tables of the signal against the actor and against the premium band (x4.5, the D3 cut)
        for other, key in (("actor", lambda x: x.get("c_actor_grouped")),
                           ("premium", lambda x: None if x.get("p_entry_over_operator") is None
                            else float(x["p_entry_over_operator"] >= 4.5))):
            cells: dict[tuple[int, int], int] = defaultdict(int)
            for m_, r in zip(mem, val):
                v = key(r["fA"])
                if v is not None:
                    cells[(int(m_), int(v))] += 1
            tab = {c: cells.get(c, 0) for c in ((0, 0), (0, 1), (1, 0), (1, 1))}
            if min(tab.values()) < 20:
                sm["small_2x2"].append(other)
            lines.append("- 2x2 signal x %s (out/in x 0/1): %s%s" % (
                other, tab, "  (NOT SEPARABLE, a cell below 20)" if min(tab.values()) < 20 else ""))
        # lift of the signal once P0, premium and actor are held fixed
        st: Strata = defaultdict(list)
        for m_, r in zip(mem, val):
            x, y = r["fA"], r["y"].get(L.PRIMARY)
            key = (tercile(cut["p_entry_over_operator"], x.get("p_entry_over_operator")),
                   tercile(cut["p_log_p0"], x.get("p_log_p0")), x.get("c_actor_grouped"))
            if y is not None and None not in key:
                st[key].append((int(m_), y))
        e, lo, hi, usable = mh_ci(st)
        sm["mh_p0_premium_actor"] = [e, lo, hi]
        lines.append("- Lift within premium tercile x P0 tercile x actor (VALIDATION, %d strata with both groups, "
                     "reported only): %s pts [%s, %s]" % (usable, pts(e), pts(lo), pts(hi)))
        obs = [(m_, r) for m_, r in zip(mem, val) if r["y"].get(L.PRIMARY) is not None]
        pe = ref.score(rprep.transform([r["fA"] for _, r in obs]))
        items = [(r["cluster"], (int(m_), r["y"][L.PRIMARY] - p)) for (m_, r), p in zip(obs, pe)]

        def resid(sample: list[tuple[int, float]]) -> Optional[float]:
            a = [d for g, d in sample if g]
            b = [d for g, d in sample if not g]
            return sum(a) / len(a) - sum(b) / len(b) if a and b else None
        e = resid([v for _, v in items])
        lo, hi = L.boot(items, resid)
        sm["resid_lift"] = [e, lo, hi]
        lines += ["- Lift beyond the P0 + premium + actor model (observed minus expected, in minus out): "
                  "%s pts [%s, %s]%s" % (pts(e), pts(lo), pts(hi), "" if lo is not None and lo > 0 else
                                         "  (EXPLAINED by P0, premium, actor: the CI reaches 0)"), ""]
    # matched comparison
    t1, t2 = cut["p_entry_over_operator"]

    def stratum(r: dict[str, Any]) -> Optional[tuple]:
        x = r["fA"]
        key = (int(r["t"] // (7 * 86400)), tercile(cut["p_entry_over_operator"], x.get("p_entry_over_operator")),
               None if x.get("b_core_n") is None else x["b_core_n"] > med["b_core_n"],
               None if x.get("b_core_sol") is None else x["b_core_sol"] > med["b_core_sol"])
        return None if None in key else key
    lines += ["## Matched comparison: common funding within similar launches", "",
              "Strata: week x premium tercile (TRAIN cuts %.2f / %.2f) x core wallets above %.0f x bundle SOL above "
              "%.1f (TRAIN medians). Treated: one funder for >= 2 core wallets. Mantel-Haenszel risk difference, "
              "stratified bootstrap (%d)." % (t1, t2, med["b_core_n"], med["b_core_sol"], L.B), ""]
    for sp in ("train", "val"):
        st = defaultdict(list)
        for r in rows:
            k_ = stratum(r)
            if r["split"] != sp or r["y"].get(L.PRIMARY) is None or r["fA"].get("f_same_funder_multi") is None \
                    or k_ is None:
                continue
            st[k_].append((int(r["fA"]["f_same_funder_multi"] == 1), r["y"][L.PRIMARY]))
        e, lo, hi, usable = mh_ci(st)
        summary.setdefault("_matched", {})[sp] = [e, lo, hi]
        lines.append("- %s: %d strata with both groups; MH difference %s pts [%s, %s]." % (
            sp.upper(), usable, pts(e), pts(lo), pts(hi)))
    L.write("D8_robustness.md", lines)
    with open(os.path.join(L.FB.DERIVED, "D8_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
