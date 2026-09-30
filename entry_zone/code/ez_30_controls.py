#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controls against false signals and the classification of analysis_plan.md, for the rules
ez_20_search.py kept (derived/E_kept.json): each family's best single condition and the
best combination.

Residual lift: on VALIDATION, mean(y - p) inside the rule minus outside, p from a TRAIN
model (boosting, 150 rounds) of the controls only; 95 % cluster-bootstrap CI. Control
sets: premium; actor; premium + actor; premium + actor + snipers + run-up since the alert.
The premium sets are not applied to price rules (market cap, premium, other price): the
rule is the premium there. Then: largest operator share, halves and weeks, the rule with
the largest buyer removed (SOL totals), VALIDATION without the dominant operator of the
selection and without the grouped launches. Writes tables/E3_controls.md and
derived/E_classified.json.
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import Counter, defaultdict
from typing import Any, Callable, Optional

import ez_lib as L

sys.path.insert(0, os.path.join(L.ROOT, "post_detection_forensics", "code"))
import fml

PRICE_FAMILIES = {"market cap", "premium", "other price"}
CONTROLS = {"premium": ["premium"], "actor": ["actor"], "premium + actor": ["premium", "actor"],
            "premium + actor + snipers + run-up": ["premium", "actor", "n_snipers", "mult_since_alert"]}
MIN_VAL = 30


def ctl_x(r: dict[str, Any], cut: str, names: list[str]) -> dict[str, Any]:
    f = r["f"][cut]
    x = {}
    for n in names:
        if n == "actor":
            x[n] = r["ctx"]["actor_grouped"]
        elif n == "premium":
            x[n] = f.get("premium") if f.get("premium") is not None else r["ctx"]["premium0"]
        else:
            x[n] = f.get(n)
    return x


def resid_lift(rows: list[dict[str, Any]], cut: str, pred: Callable[[dict[str, Any]], bool], names: list[str]
               ) -> tuple[Optional[float], Optional[float], Optional[float]]:
    tr, va = L.observed(rows, cut, "train"), L.observed(rows, cut, "val")
    prep = fml.Prep(names).fit([ctl_x(r, cut, names) for r in tr])
    m = fml.Boost(150).fit(prep.transform([ctl_x(r, cut, names) for r in tr]), [r["y"][cut][L.PRIMARY] for r in tr],
                           [prep.cuts[n] for n in names])
    p = m.score(prep.transform([ctl_x(r, cut, names) for r in va]))
    items = [(r["cluster"], (int(pred(r)), r["y"][cut][L.PRIMARY] - pi)) for r, pi in zip(va, p)]

    def stat(sample: list[tuple[int, float]]) -> Optional[float]:
        a = [d for g, d in sample if g]
        b = [d for g, d in sample if not g]
        return sum(a) / len(a) - sum(b) / len(b) if a and b else None
    est = stat([v for _, v in items])
    by: dict[str, list] = defaultdict(list)
    for c, v in items:
        by[c].append(v)
    keys = sorted(by)
    rng = random.Random(L.SEED)
    bs = []
    for _ in range(L.B):
        s = stat([v for _ in keys for v in by[keys[rng.randrange(len(keys))]]])
        if s is not None:
            bs.append(s)
    bs.sort()
    if len(bs) < L.B // 2:
        return est, None, None
    return est, bs[int(0.025 * (len(bs) - 1))], bs[int(0.975 * (len(bs) - 1))]


def holds_val(sel: list[dict[str, Any]], allr: list[dict[str, Any]], cut: str) -> tuple[bool, float, float]:
    k = sum(r["y"][cut][L.PRIMARY] for r in sel)
    base = sum(r["y"][cut][L.PRIMARY] for r in allr) / len(allr) if allr else 0.0
    lb = L.wilson_lb(k, len(sel))
    return (len(sel) > 0 and lb > base), lb, base


def main() -> None:
    rows = L.load()
    kept = json.load(open(os.path.join(L.DERIVED, "E_kept.json")))
    lines = ["# E3. Controls against false signals, and the classification", "",
             "VALIDATION holds = its Wilson 95 % lower bound is above the VALIDATION base at the cut-off.", ""]
    out: dict[str, Any] = {}
    for fam, d in kept.items():
        cut = d["cut"]
        atoms = [tuple(a) for a in d["atoms"]]

        def pred(r: dict[str, Any], atoms: list[tuple] = atoms, cut: str = cut) -> bool:
            return all(L.holds(r["f"][cut], a) for a in atoms)
        va = L.observed(rows, cut, "val")
        sel_v = [r for r in va if pred(r)]
        ok, lb, base = holds_val(sel_v, va, cut)
        rec: dict[str, Any] = {"family": fam, "cut": cut, "rule": " AND ".join(L.text(a) for a in atoms),
                               "p": d["p"], "val_n": len(sel_v), "val_k": sum(r["y"][cut][L.PRIMARY] for r in sel_v),
                               "val_base": base, "val_lb": lb, "val_holds": ok,
                               "train_n": d["train"]["n"], "train_k": d["train"]["k_2"]}
        lines += ["## %s: `%s`" % (fam, rec["rule"]), "",
                  "- TRAIN %s (base %.1f %%), permutation p %.3f." % (
                      L.rate(rec["train_k"], rec["train_n"]), 100 * d["train"]["base"], d["p"]),
                  "- VALIDATION %s, base %.1f %%, lower bound %.1f %%: %s." % (
                      L.rate(rec["val_k"], rec["val_n"]), 100 * base, 100 * lb, "holds" if ok else "does not hold")]
        winners = [r for r in sel_v if r["y"][cut][L.PRIMARY] == 1]
        dd = sorted(r["y"][cut]["drawdown"] for r in winners if r["y"][cut].get("drawdown") is not None)
        rec["val_drawdown_winners_median"] = dd[len(dd) // 2] if dd else None
        lines.append("- VALIDATION drawdown before the 2x, among the %d that reached it: median %s." % (
            len(winners), L.fmt(rec["val_drawdown_winners_median"], "%+.2f")))
        # residual lifts
        rec["resid"] = {}
        for name, names in CONTROLS.items():
            if fam in PRICE_FAMILIES and "premium" in names:
                continue
            if not sel_v or len(sel_v) == len(va):
                continue
            e, lo, hi = resid_lift(rows, cut, pred, names)
            rec["resid"][name] = [e, lo, hi]
            lines.append("- Lift beyond %s: %s pts [%s, %s]%s." % (
                name, L.fmt(None if e is None else 100 * e, "%+.1f"), L.fmt(None if lo is None else 100 * lo, "%+.1f"),
                L.fmt(None if hi is None else 100 * hi, "%+.1f"),
                "" if lo is not None and lo > 0 else " (the CI reaches 0: explained by it)"))
        # operators, periods, grouped launches, big wallets
        cc = Counter(r["cluster"] for r in sel_v)
        top, topn = cc.most_common(1)[0] if cc else (None, 0)
        rec["val_top_cluster_share"] = topn / len(sel_v) if sel_v else None
        rest = [r for r in va if r["cluster"] != top]
        ok2, lb2, base2 = holds_val([r for r in rest if pred(r)], rest, cut)
        single = [r for r in va if r["actor"] != "grouped"]
        ok3, lb3, base3 = holds_val([r for r in single if pred(r)], single, cut)
        rec["val_without_dominant"] = [ok2, lb2, base2, sum(1 for r in rest if pred(r))]
        rec["val_single_only"] = [ok3, lb3, base3, sum(1 for r in single if pred(r))]
        lines += ["- Largest operator: %d of the %d VALIDATION alerts (%.0f %%)." % (
                      topn, len(sel_v), 100 * (rec["val_top_cluster_share"] or 0)),
                  "- Without that operator: %s against %.1f %%: %s." % (
                      L.rate(sum(r["y"][cut][L.PRIMARY] for r in rest if pred(r)), rec["val_without_dominant"][3]),
                      100 * base2, "holds" if ok2 else "does not hold"),
                  "- Without the grouped launches: %s against %.1f %%: %s." % (
                      L.rate(sum(r["y"][cut][L.PRIMARY] for r in single if pred(r)), rec["val_single_only"][3]),
                      100 * base3, "holds" if ok3 else "does not hold")]
        half = sorted(r["t"] for r in va)[len(va) // 2]
        halves = []
        for lab, cond in (("first", lambda r: r["t"] < half), ("second", lambda r: r["t"] >= half)):
            s = [r for r in va if cond(r) and pred(r)]
            a = [r for r in va if cond(r)]
            rt = sum(r["y"][cut][L.PRIMARY] for r in s) / len(s) if s else None
            bs = sum(r["y"][cut][L.PRIMARY] for r in a) / len(a)
            halves.append(rt is not None and rt > bs)
            lines.append("- VALIDATION %s half: %s against %.1f %%." % (
                lab, L.rate(sum(r["y"][cut][L.PRIMARY] for r in s), len(s)), 100 * bs))
        rec["halves_above"] = halves
        for wk in sorted({int(r["t"] // (7 * 86400)) for r in va}):
            s = [r for r in va if int(r["t"] // (7 * 86400)) == wk and pred(r)]
            if s:
                lines.append("  - week from %s: %s." % (min(r["utc"][:10] for r in va if int(r["t"] // (7 * 86400))
                                                            == wk), L.rate(sum(r["y"][cut][L.PRIMARY] for r in s),
                                                                           len(s))))
        big = None
        if len(atoms) == 1 and atoms[0][1] in ("sol_total", "sol_early_total"):
            a = atoms[0]
            sub = "sol_max" if a[1] == "sol_total" else "sol_early_max"

            def pred_big(r: dict[str, Any]) -> bool:
                f = dict(r["f"][cut])
                if f.get(a[1]) is None or f.get(sub) is None:
                    return False
                f[a[1]] = f[a[1]] - f[sub]
                return L.holds(f, a)
            sb = [r for r in va if pred_big(r)]
            big = holds_val(sb, va, cut)[0]
            lines.append("- Same rule with the largest buyer removed: %s: %s." % (
                L.rate(sum(r["y"][cut][L.PRIMARY] for r in sb), len(sb)), "holds" if big else "does not hold"))
        rec["big_wallet_holds"] = big
        # classification, rules of analysis_plan.md, in this order
        pa = rec["resid"].get("premium + actor")
        if d["p"] >= 0.05:
            cls = "NO SIGNAL"
        elif not ok:
            cls = "TRAIN OVERFIT"
        elif (pa is not None and not (pa[1] is not None and pa[1] > 0)) or not ok2 or not ok3:
            cls = "PRICE/OPERATOR CONFOUNDED"
        elif len(sel_v) >= MIN_VAL and all(halves) and all(
                v[1] is not None and v[1] > 0 for v in rec["resid"].values()) and big is not False:
            cls = "PROMISING BUT UNCONFIRMED"
        elif len(sel_v) < MIN_VAL:
            cls = "TRAIN OVERFIT"            # VALIDATION holds on fewer than 30 alerts: not a confirmation
        else:
            cls = "PRICE/OPERATOR CONFOUNDED"
        rec["class"] = cls
        lines += ["", "**Classification: %s**" % cls, ""]
        out[fam] = rec
    L.write("E3_controls.md", lines)
    with open(os.path.join(L.DERIVED, "E_classified.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    for fam, r in out.items():
        print("%-18s %-26s VAL %s base %.1f %%  %s" % (fam, r["class"], L.rate(r["val_k"], r["val_n"]),
                                                     100 * r["val_base"], r["rule"][:90]))


if __name__ == "__main__":
    main()
