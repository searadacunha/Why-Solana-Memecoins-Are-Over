#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The final TEST, run once, on the signals frozen in tables/LOCK.json.

Nothing is chosen here. Every signal, threshold, target, strategy, cost
parameter and decision rule is read from LOCK.json, which was committed before
this script first read the TEST rows. The script checks that the datasets are
the ones the lock was computed on, then measures:

  T4  per signal: TRAIN / VALIDATION / TEST rates, lift, one-sided Fisher with
      Holm across the locked family, cluster-bootstrap CI, trading result
      after costs, and the verdict the lock's decision rules produce;
      the headline signal by horizon; the high-hit-rate TRAIN rules on TEST
      (descriptive, after the lock).
  T6  trading: every strategy x latency x size x depth assumption, on TEST,
      for every locked signal and for "buy every alert".
  T7  robustness of the headline signal and of any survivor: by period, by
      operator cluster, leave-one-cluster-out, thresholds +/- 5 and 10 %
      (descriptive), and the ANSEM status.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from collections import Counter
from typing import Any, Callable

import pde
import trade
import an_20_baseline
from an_30_univariate import label, value
from an_40_signals import (TARGETS, atom_true, build_atoms, design, in_leaf, rule_text, search_rules)

LOCK_PATH = os.path.join(pde.TABLES, "LOCK.json")


def member_fn(sig: dict[str, Any]) -> Callable[[dict[str, Any]], bool]:
    kind = sig["kind"]
    if kind == "rule":
        rule = tuple(tuple(a) for a in sig["rule"])
        return lambda r: all(atom_true(r, a) for a in rule)
    if kind in ("logistic", "tree_leaf"):
        def x_of(r: dict[str, Any]) -> list[float]:
            return design([r], sig["median"], sig["mean"], sig["sd"])[0]
        if kind == "logistic":
            return lambda r: sum(b * v for b, v in zip(sig["beta"], x_of(r))) >= sig["cut"]
        path = tuple(tuple(p) for p in sig["path"])
        return lambda r: in_leaf(x_of(r), path)
    return {
        "H1_actor_grouped": lambda r: value(r, "actor") == "grouped",
        "H2_mc_below_60k": lambda r: r["f"]["mc_usd"] < 60000,
        "H2b_mc_40k_60k": lambda r: 40000 <= r["f"]["mc_usd"] < 60000,
    }[sig["id"]]


def split_stats(rows: list[dict[str, Any]], fn: Callable, k: float, h: int) -> dict[str, Any]:
    obs = [(r, label(r, k, h)) for r in rows if label(r, k, h) is not None]
    s = [(r, y) for r, y in obs if fn(r)]
    o = [(r, y) for r, y in obs if not fn(r)]
    return {"n": len(s), "k": sum(y for _, y in s), "base_n": len(obs), "base_k": sum(y for _, y in obs),
            "rest_n": len(o), "rest_k": sum(y for _, y in o),
            "boot": [(r["cluster"], 1 if fn(r) else 0, y) for r, y in obs]}


def trades(rows: list[dict[str, Any]], fn: Callable, S: dict, strat: dict[str, Any], lat: float, size: float,
           cost: dict[str, Any], k_scale: float = 1.0, exit_mode: str = "touch") -> dict[str, Any]:
    res = []
    for r in rows:
        if not fn(r):
            continue
        sim = trade.simulate(S.get(r["mint"]) or [], r["fine"], lat, strat["tp"], strat["sl"], strat["timeout_s"],
                             exit_mode)
        net = (trade.net_return(sim["gross"], sim["entry_mult"], r["p0"], r["f"]["p0_source"], r["t"], size, cost,
                                k_scale) if sim["status"] == "ok" else None)
        res.append((r["cluster"], sim, net))
    return trade.summarise(res)


def fmt_tr(s: dict[str, Any]) -> str:
    if not s.get("n_ok"):
        return "n/a (0 trades)"
    lo, hi = s.get("net_ci", (None, None))
    return "gross %+.1f %%, net %+.1f %% [%s, %s], win %.0f %% (n %d, cens. %d)" % (
        100 * s["gross_mean"], 100 * s["net_mean"], "n/a" if lo is None else "%+.1f" % (100 * lo),
        "n/a" if hi is None else "%+.1f" % (100 * hi), 100 * s["net_win"], s["n_ok"], s["n_censored"])


def main() -> None:
    if not os.path.exists(LOCK_PATH):
        sys.exit("no tables/LOCK.json: the TEST stays sealed")
    lock = json.load(open(LOCK_PATH))
    for name, key in (("dataset_dev.jsonl.gz", "dataset_dev_sha256"),
                      ("dataset_test.sealed.jsonl.gz", "dataset_test_sha256")):
        sha = hashlib.sha256(open(os.path.join(pde.DERIVED, name), "rb").read()).hexdigest()
        if sha != lock[key]:
            sys.exit("%s differs from the dataset the lock was computed on" % name)
    dev = pde.read_rows("dataset_dev.jsonl.gz")
    train = [r for r in dev if r["split"] == "train"]
    val = [r for r in dev if r["split"] == "val"]
    if "--rehearse" in sys.argv:
        # exercise every code path with VALIDATION standing in for TEST, without
        # opening the sealed file; tables go to --rehearse's directory
        test = val
        pde.TABLES = sys.argv[sys.argv.index("--rehearse") + 1]
    else:
        test = pde.read_rows("dataset_test.sealed.jsonl.gz")
    everything = dev + test
    S = pde.load_series()
    cost = lock["cost_model"]
    strats = lock["strategies"]
    prim = cost["primary"]
    sigs = lock["signals"]
    all_fn: Callable[[dict[str, Any]], bool] = lambda r: True  # noqa: E731

    # --- baselines on TEST and on everything ----------------------------------- #
    txt = ["# T1b. Base rates on TEST and on the whole population (computed after the lock)", ""]
    for lab_, rows in (("TEST", test), ("ALL (TRAIN + VALIDATION + TEST)", everything)):
        tab, _ = an_20_baseline.baseline(rows)
        txt += ["## %s (%d alerts)" % (lab_, len(rows)), ""] + tab + [""]
    pde.write_table("T1_baseline_test_and_all.md", "\n".join(txt))

    # --- per-signal statistics ------------------------------------------------ #
    stats = []
    for sig in sigs:
        fn = member_fn(sig)
        k, h = sig["target"]
        st = {sp: split_stats(rows, fn, k, h) for sp, rows in (("train", train), ("val", val), ("test", test))}
        t = st["test"]
        p = pde.fisher_greater(t["k"], t["n"] - t["k"], t["rest_k"], t["rest_n"] - t["rest_k"]) if t["n"] else 1.0
        ci = pde.cluster_boot_rate_diff(t["boot"]) if t["n"] else (None, None)
        strat = strats[strats["primary_for_target"][str(h)]]
        tr = trades(test, fn, S, strat, prim["latency_s"], prim["size_usd"], cost)
        stats.append({"sig": sig, "fn": fn, "st": st, "p": p, "ci": ci, "trade": tr,
                      "strategy": strats["primary_for_target"][str(h)]})
    adj = pde.holm([s["p"] for s in stats])
    for s, a in zip(stats, adj):
        t = s["st"]["test"]
        s["p_holm"] = a
        s["survives"] = (t["n"] >= 30 and a < 0.05 and s["ci"][0] is not None and s["ci"][0] > 0)
        lo_net = (s["trade"].get("net_ci") or (None, None))[0]
        s["edge"] = s["survives"] and lo_net is not None and lo_net > 0
        tr_ = s["st"]["train"]
        tr_lift = tr_["k"] / tr_["n"] - tr_["base_k"] / tr_["base_n"]
        if s["edge"]:
            s["verdict"] = "EDGE"
        elif s["survives"]:
            s["verdict"] = "STATISTICAL SIGNAL, NO TRADABLE EDGE"
        elif tr_lift >= 0.10:
            s["verdict"] = "OVERFIT (TRAIN +%.0f pts, not confirmed on TEST)" % (100 * tr_lift)
        else:
            s["verdict"] = "NO POSITIVE EFFECT"

    def rate(d: dict[str, Any]) -> str:
        return pde.rate_cell(d["k"], d["n"])

    out = ["# T4. Final TEST of the locked signals", "",
           "Lock: `tables/LOCK.json`, locked %s UTC, before the first read of TEST. Rates: complete-case "
           "(observed windows), entry at P0, a spot price. Holm across the %d locked signals. Cluster CI: "
           "operators (shared sniper wallet, creator or ticket configuration) resampled, 2 000 draws. "
           "'After costs': the signal's primary strategy on TEST (hold to 2x or timeout at the target horizon), "
           "entry at +%d s, $%d, estimated fees and price impact (trade.py): mean net return per trade "
           "[cluster 95 %% CI]. Regenerate: `python3 post_detection_edge/code/an_60_final_test.py`."
           % (lock["locked_at_utc"], len(sigs), prim["latency_s"], prim["size_usd"]), "",
           "| Signal | target | N train | P2x train | N val | P2x val | N test | P2x test | base TEST | "
           "Lift vs base | signal - rest [cluster CI] | Holm p | After costs | Verdict |",
           "|---|---|---:|---|---:|---|---:|---|---|---:|---|---:|---|---|"]
    for s in stats:
        st = s["st"]
        t = st["test"]
        lift = (t["k"] / t["n"] - t["base_k"] / t["base_n"]) if t["n"] else None
        diff = (t["k"] / t["n"] - t["rest_k"] / t["rest_n"]) if t["n"] and t["rest_n"] else None
        lo, hi = s["ci"]
        tr = s["trade"]
        after = ("%+.1f %% [%+.1f, %+.1f]" % (100 * tr["net_mean"], 100 * tr["net_ci"][0], 100 * tr["net_ci"][1])
                 if tr.get("net_ci") and tr["net_ci"][0] is not None else "n/a")
        out.append("| %s: %s | %gx@%s | %d | %s | %d | %s | %d | %s | %s | %s | %s [%s, %s] | %.3f | %s | %s |" % (
            s["sig"]["id"], s["sig"]["text"], s["sig"]["target"][0], pde.H_LABEL[s["sig"]["target"][1]],
            st["train"]["n"], rate(st["train"]), st["val"]["n"], rate(st["val"]), t["n"], rate(t),
            pde.rate_cell(t["base_k"], t["base_n"]), "n/a" if lift is None else "%+.1f pts" % (100 * lift),
            "n/a" if diff is None else "%+.1f pts" % (100 * diff), "n/a" if lo is None else "%+.1f" % (100 * lo),
            "n/a" if hi is None else "%+.1f" % (100 * hi), s["p_holm"], after, s["verdict"]))
    surv = [s for s in stats if s["survives"]]
    out += ["", "Signals that survive TEST under the locked rule: %d of %d. EDGE: %d." % (
        len(surv), len(stats), sum(1 for s in stats if s["edge"]))]
    for s in stats:
        lo_w = pde.wilson(s["st"]["test"]["k"], s["st"]["test"]["n"])[0]
        s["wilson_lo"] = lo_w

    # headline signal by horizon, on TEST
    head = next(s for s in stats if s["sig"]["id"] == lock["headline_signal"])
    out += ["", "## Headline signal by horizon, TEST: `%s`" % head["sig"]["text"], "",
            "| Horizon | Baseline P2x | Signal P2x | N signal | 95 % CI (Wilson) | Signal P2x, all splits |",
            "|---|---|---|---:|---|---|"]
    for hh in pde.HORIZONS:
        b = [label(r, 2.0, hh) for r in test if label(r, 2.0, hh) is not None]
        sg = [label(r, 2.0, hh) for r in test if label(r, 2.0, hh) is not None and head["fn"](r)]
        al_ = [label(r, 2.0, hh) for r in everything if label(r, 2.0, hh) is not None and head["fn"](r)]
        lo_, hi_ = pde.wilson(sum(sg), len(sg))
        out.append("| %s | %s | %s | %d | %s | %s |" % (
            pde.H_LABEL[hh], pde.rate_cell(sum(b), len(b)) if b else "n/a (0 observed)",
            ("%.1f %%" % (100 * sum(sg) / len(sg))) if sg else "n/a", len(sg),
            "n/a" if lo_ is None else "[%.1f, %.1f]" % (100 * lo_, 100 * hi_),
            pde.rate_cell(sum(al_), len(al_)) if al_ else "n/a"))

    # high hit-rate TRAIN rules, measured on TEST after the lock (descriptive)
    out += ["", "## TRAIN rules with a high hit rate, measured on TEST after the lock (descriptive)", "",
            "Re-run of the deterministic TRAIN search of an_40. Pooled rates count alert-rule pairs, so an "
            "alert selected by many rules counts many times.", "",
            "| target | TRAIN rate band | rules | pooled TRAIN | pooled VAL | pooled TEST | base TEST |",
            "|---|---|---:|---|---|---|---|"]
    for k, hh in TARGETS:
        tr_rows = [r for r in train if label(r, k, hh) is not None]
        ytr = [label(r, k, hh) for r in tr_rows]
        rules = search_rules(tr_rows, ytr, build_atoms(tr_rows))
        va_obs = [(r, label(r, k, hh)) for r in val if label(r, k, hh) is not None]
        te_obs = [(r, label(r, k, hh)) for r in test if label(r, k, hh) is not None]
        base = pde.rate_cell(sum(y for _, y in te_obs), len(te_obs))
        for lo_b, hi_b in ((0.8, 1.01), (0.7, 0.8), (0.6, 0.7)):
            grp = [d for d in rules if lo_b <= d["rate"] < hi_b]
            if not grp:
                out.append("| %gx@%s | %d-%d %% | 0 | - | - | - | %s |" % (k, pde.H_LABEL[hh], 100 * lo_b,
                                                                       min(100, 100 * hi_b), base))
                continue
            vk = vn = tk = tn = 0
            for d in grp:
                for r, y in va_obs:
                    if all(atom_true(r, a) for a in d["rule"]):
                        vn += 1
                        vk += y
                for r, y in te_obs:
                    if all(atom_true(r, a) for a in d["rule"]):
                        tn += 1
                        tk += y
            out.append("| %gx@%s | %d-%d %% | %d | %s | %s | %s | %s |" % (
                k, pde.H_LABEL[hh], 100 * lo_b, min(100, 100 * hi_b), len(grp),
                pde.rate_cell(sum(d["k"] for d in grp), sum(d["n"] for d in grp)),
                pde.rate_cell(vk, vn), pde.rate_cell(tk, tn), base))
            if lo_b == 0.8:
                for d in grp:
                    a = [y for r, y in te_obs if all(atom_true(r, x) for x in d["rule"])]
                    b = [y for r, y in va_obs if all(atom_true(r, x) for x in d["rule"])]
                    out.append("|  | `%s` | 1 | %s | %s | %s | |" % (
                        rule_text(d["rule"]), pde.rate_cell(d["k"], d["n"]), pde.rate_cell(sum(b), len(b)),
                        pde.rate_cell(sum(a), len(a))))
    pde.write_table("T4_final_test.md", "\n".join(out))

    # --- trading ------------------------------------------------------------- #
    tt = ["# T6. Trading on TEST: strategies, latency, size, depth", "",
          "Entry at the first spot read at or after the latency (L = 0 is P0). Exits as in trade.py. 'gross' = "
          "spot multiple - 1, no cost at all; 'net' = estimated fees ($ per tx, %.0f %% per leg) and constant-"
          "product impact from a depth derived from the price (K = %.3g for the pool). A trade counts only if "
          "its whole holding window is observed. Mean per trade, [95 %% cluster CI of the net mean]."
          % (100 * cost["fee_per_leg"], cost["k_pool"]), ""]
    fam = [("ALL ALERTS", all_fn)] + [(s["sig"]["id"], s["fn"]) for s in stats]
    for name, fn in fam:
        tt += ["## %s" % name, "", "| strategy | L=0 | L=5 | L=10 | L=15 | L=20 |", "|---|---|---|---|---|---|"]
        for sn in ("S1", "S2", "S3", "HOLD_5m", "HOLD_15m", "HOLD_1h"):
            cells = [fmt_tr(trades(test, fn, S, strats[sn], lat, prim["size_usd"], cost)) for lat in pde.LATENCIES]
            st_ = strats[sn]
            tt.append("| %s (TP %gx, SL %s, %ds) | %s |" % (sn, st_["tp"], "-" if st_["sl"] is None else
                                                             "%+.0f %%" % (100 * (st_["sl"] - 1)), st_["timeout_s"],
                                                             " | ".join(cells)))
        tt.append("")
    tt += ["## Size, depth and exit-fill sensitivity (primary strategy of each signal, L = 10 s)", "",
           "| signal | $100 | $500 | $1 000 | $500, K x0.5 | $500, K x2 | $500, exit at next read |",
           "|---|---|---|---|---|---|---|"]
    for name, fn in fam:
        if name == "ALL ALERTS":
            sn = "HOLD_1h"
        else:
            sn = next(s["strategy"] for s in stats if s["sig"]["id"] == name)
        st_ = strats[sn]
        cells = [fmt_tr(trades(test, fn, S, st_, 10, sz, cost)) for sz in cost["sizes_usd"]]
        cells += [fmt_tr(trades(test, fn, S, st_, 10, 500, cost, ks)) for ks in cost["k_sensitivity"]]
        cells.append(fmt_tr(trades(test, fn, S, st_, 10, 500, cost, 1.0, "next")))
        tt.append("| %s (%s) | %s |" % (name, sn, " | ".join(cells)))
    pde.write_table("T6_trading.md", "\n".join(tt))

    # --- robustness ---------------------------------------------------------- #
    rb = ["# T7. Robustness of the headline signal and of any survivor", ""]
    targets_rb = [head] + [s for s in surv if s is not head]
    for s in targets_rb:
        k, hh = s["sig"]["target"]
        fn = s["fn"]
        rb += ["## %s: `%s` (%gx@%s)" % (s["sig"]["id"], s["sig"]["text"], k, pde.H_LABEL[hh]), ""]
        rb += ["### By period", "", "| period | signal | rest | base |", "|---|---|---|---|"]
        periods = [("TRAIN 21-29 Aug", train), ("VALIDATION 30 Aug-14 Sep", val), ("TEST 15-29 Sep", test),
                   ("August (all splits)", [r for r in everything if r["utc"][5:7] == "08"]),
                   ("September (all splits)", [r for r in everything if r["utc"][5:7] == "09"])]
        for pn, rows in periods:
            d = split_stats(rows, fn, k, hh)
            rb.append("| %s | %s | %s | %s |" % (pn, pde.rate_cell(d["k"], d["n"]),
                                                 pde.rate_cell(d["rest_k"], d["rest_n"]),
                                                 pde.rate_cell(d["base_k"], d["base_n"])))
        rb.append("| June, July | no data: the detector started on 2026-08-21 | | |")
        te = [(r, label(r, k, hh)) for r in test if label(r, k, hh) is not None and fn(r)]
        cl = Counter(r["cluster"] for r, _ in te)
        base_t = split_stats(test, fn, k, hh)
        rb += ["", "### By operator cluster (TEST)", "",
               "%d signal alerts with an observed window, from %d clusters; the largest cluster holds %d (%.0f %%). "
               "Hits by cluster: %s." % (len(te), len(cl), max(cl.values()) if cl else 0,
                                         100 * max(cl.values()) / len(te) if te else 0,
                                         ", ".join("%d/%d" % (sum(y for r, y in te if r["cluster"] == c), n)
                                                   for c, n in cl.most_common(8))), ""]
        loo = []
        for c in cl:
            kept = [(r, y) for r, y in te if r["cluster"] != c]
            if kept:
                loo.append(sum(y for _, y in kept) / len(kept))
        if loo:
            rb.append("Leave-one-cluster-out signal rate on TEST: min %.1f %%, max %.1f %% over %d clusters removed "
                      "one at a time (base TEST %.1f %%)." % (100 * min(loo), 100 * max(loo), len(loo),
                                                                100 * base_t["base_k"] / base_t["base_n"]))
            big = cl.most_common(1)[0][0]
            kept = [(r, y) for r, y in te if r["cluster"] != big]
            rb.append("Without the largest cluster: %s." % pde.rate_cell(sum(y for _, y in kept), len(kept)))
        if s["sig"]["kind"] == "rule":
            rb += ["", "### Threshold stability on TEST (descriptive, after the lock)", "",
                   "| condition varied | -10 % | -5 % | locked | +5 % | +10 % |", "|---|---|---|---|---|---|"]
            rule = [tuple(a) for a in s["sig"]["rule"]]
            for i, a in enumerate(rule):
                if a[1] == "==":
                    continue
                cells = []
                for dlt in (-0.10, -0.05, 0.0, 0.05, 0.10):
                    v = a[2]
                    nv = math.log10(10 ** v * (1 + dlt)) if a[0].startswith("log10_") else v * (1 + dlt)
                    rr = tuple(rule[:i] + [(a[0], a[1], nv)] + rule[i + 1:])
                    sel = [y for r, y in ((r, label(r, k, hh)) for r in test) if y is not None
                           and all(atom_true(r, x) for x in rr)]
                    cells.append(pde.rate_cell(sum(sel), len(sel)))
                rb.append("| %s | %s |" % (rule_text((a,)), " | ".join(cells)))
        rb.append("")
    rb += ["## ANSEM", "",
           "Mint 9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump, created 2026-06-16 21:05:48 UTC. Not in the "
           "snapshot: the detector started on 2026-08-21, and its creation block (two buyers, one of them "
           "~84.7 SOL) fails the detector's definition (at least 4 snipers of >= 5 SOL). With ANSEM and "
           "without ANSEM are therefore the same numbers. It is not injected into any split."]
    pde.write_table("T7_robustness.md", "\n".join(rb))

    summary = {s["sig"]["id"]: {"train": [s["st"]["train"]["k"], s["st"]["train"]["n"]],
                                "val": [s["st"]["val"]["k"], s["st"]["val"]["n"]],
                                "test": [s["st"]["test"]["k"], s["st"]["test"]["n"]],
                                "test_base": [s["st"]["test"]["base_k"], s["st"]["test"]["base_n"]],
                                "holm_p": s["p_holm"], "ci_diff": s["ci"], "survives": s["survives"],
                                "edge": s["edge"], "verdict": s["verdict"], "wilson_lo_test": s["wilson_lo"],
                                "trade": {k_: v for k_, v in s["trade"].items()}} for s in stats}
    with open(os.path.join(pde.DERIVED, "final_test_summary.json"), "w", encoding="utf8") as fh:
        json.dump(summary, fh, indent=1, default=str)
    print("\n".join(out))


if __name__ == "__main__":
    main()
