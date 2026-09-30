#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The TEST of the forensic study, run once, on the models of tables/LOCK.json.

TEST = the detector's alerts after the first snapshot (code/snap_50_freeze_test.py),
never seen when the models were fitted, chosen and locked. Nothing is chosen
here: models, thresholds, strategies, costs and decision rules come from the lock.

Writes
  T4_test.md          every locked model: ROC-AUC [cluster CI], permutation p,
                      PR-AUC, Brier, calibration, precision / recall / F1, the
                      critical table (top 50 % ... top 1 %) and the ablation table
  T5_importance.md    the headline model's features: model importance,
                      permutation importance on VALIDATION and on TEST, direction
  T6_trading.md       top 1 / 5 / 10 / 20 %, three strategies, sizes, latencies
  T7_robustness.md    by week, by operator cluster, leave-one-cluster-out, ANSEM
--rehearse DIR runs everything with VALIDATION standing in for TEST, into DIR,
to debug the script without opening the TEST rows.
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
from typing import Any

import fml
from feat_30_build import DERIVED, FAMILY, STUDY, read_rows

EDGE = os.path.join(os.path.dirname(STUDY), "post_detection_edge")
sys.path.insert(0, os.path.join(EDGE, "code"))
import pde  # noqa: E402
import trade as edge_trade  # noqa: E402  (simulate() only: the exit rules of the previous study)

K_CURVE = 30 * 1.073e9
B = 1000
SEED = 20260929


def wilson(k: int, n: int) -> str:
    if not n:
        return "n/a"
    lo, hi = pde.wilson(k, n)
    return "[%.1f, %.1f]" % (100 * lo, 100 * hi)


def boot_auc(s: list[float], y: list[int], cl: list[str]) -> tuple[float, float]:
    by: dict[str, list[int]] = defaultdict(list)
    for i, c in enumerate(cl):
        by[c].append(i)
    keys = sorted(by)
    rng = random.Random(SEED)
    out = []
    for _ in range(B):
        idx = [i for _ in keys for i in by[keys[rng.randrange(len(keys))]]]
        a = fml.roc_auc([s[i] for i in idx], [y[i] for i in idx])
        if a is not None:
            out.append(a)
    out.sort()
    return out[int(0.025 * (len(out) - 1))], out[int(0.975 * (len(out) - 1))]


def perm_p(s: list[float], y: list[int], n: int = 2000) -> float:
    a0 = fml.roc_auc(s, y)
    rng = random.Random(SEED)
    yy = list(y)
    ge = 0
    for _ in range(n):
        rng.shuffle(yy)
        if (fml.roc_auc(s, yy) or 0.5) >= a0 - 1e-12:
            ge += 1
    return (ge + 1) / (n + 1)


def load_series(path: str) -> dict[str, list[tuple[float, float]]]:
    s: dict[str, list[tuple[float, float]]] = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf8") as fh:
        for line in fh:
            m, dt, mult, _ = line.split()
            s[m].append((float(dt), float(mult)))
    for v in s.values():
        v.sort()
    return dict(s)


def net_return(gross: float, entry_mult: float, p0: float, pool_sol: Any, t: float, size_usd: float,
               sol_usd: dict[int, float], fee: float, fixed: float) -> float:
    s = size_usd / sol_usd[int(t) // 3600 * 3600]
    p_in = p0 * entry_mult
    r_in = pool_sol * math.sqrt(entry_mult) if pool_sol else math.sqrt(K_CURVE * p_in)
    s_eff = s * (1 - fee)
    q = s_eff / (p_in * (1 + s_eff / r_in))
    p_out = p_in * gross
    r_out = r_in * math.sqrt(gross)
    v = q * p_out
    recv = v / (1 + v / r_out) * (1 - fee)
    return (recv - s - 2 * fixed) / s


def main() -> None:
    lock = json.load(open(os.path.join(STUDY, "tables", "LOCK.json")))
    sha = hashlib.sha256(open(os.path.join(DERIVED, "forensic_rows.jsonl.gz"), "rb").read()).hexdigest()
    if sha != lock["train_val_rows_sha256"]:
        sys.exit("TRAIN/VALIDATION rows differ from those the lock was computed on")
    rows = read_rows("forensic_rows.jsonl.gz")
    val = [r for r in rows if r["split"] == "val"]
    if "--rehearse" in sys.argv:
        outdir = sys.argv[sys.argv.index("--rehearse") + 1]
        test = val
        series = pde.load_series()
        sol_usd = {int(k): v for k, v in json.load(open(os.path.join(pde.DATA, "sol_usd_hourly.json")))
                   ["close_by_hour"].items()}
    else:
        outdir = os.path.join(STUDY, "tables")
        test = read_rows("forensic_rows_test.jsonl.gz")
        snap = os.path.join(STUDY, "data", "test_snapshot")
        series = load_series(os.path.join(snap, "series.txt.gz"))
        sol_usd = {int(k): v for k, v in json.load(open(os.path.join(snap, "sol_usd_hourly.json")))
                   ["close_by_hour"].items()}
    tr = lock["trading"]
    key = lambda e: "%s_%s" % (e, lock["target"])  # noqa: E731

    def scored(m: dict[str, Any], rs: list[dict[str, Any]]) -> tuple[list, list, list, list]:
        e = m["entry"]
        rr = [r for r in rs if r["y"].get(key(e)) is not None and (e == "A" or r["fine"])]
        X = fml.Prep.load(m["prep"]).transform([r["f" + e] for r in rr])
        return rr, fml.score_state(m["state"], X), [r["y"][key(e)] for r in rr], [r["cluster"] for r in rr]

    def trades(rr: list[dict[str, Any]], sel: list[bool], entry: str, strat: dict[str, Any], lat: float,
               size: float) -> dict[str, Any]:
        res = []
        for r, ok in zip(rr, sel):
            if not ok:
                continue
            pts = series.get(r["mint"]) or []
            sim = edge_trade.simulate(pts, r["fine"], (30 if entry == "V" else 0) + lat, strat["tp"], strat["sl"],
                                      strat["timeout_s"])
            net = None
            if sim["status"] == "ok":
                net = net_return(sim["gross"], sim["entry_mult"], 10 ** r["fA"]["p_log_p0"],
                                 r["f" + entry].get("p_pool_sol"), r["t"], size, sol_usd, tr["fee_per_leg"],
                                 tr["fixed_sol_per_tx"])
            res.append((r["cluster"], sim, net))
        return edge_trade.summarise(res)

    def fmt(s: dict[str, Any]) -> str:
        if not s.get("n_ok"):
            return "n/a (0)"
        lo, hi = s.get("net_ci", (None, None))
        return "gross %+.1f %%, net %+.1f %% [%s, %s] (n %d)" % (
            100 * s["gross_mean"], 100 * s["net_mean"], "n/a" if lo is None else "%+.1f" % (100 * lo),
            "n/a" if hi is None else "%+.1f" % (100 * hi), s["n_ok"])

    out = ["# T4. Final TEST of the locked forensic models", "",
           "Lock: `tables/LOCK.json`, locked %s UTC. TEST = %s. Target 2x within 1 h of the entry, complete-case. "
           "Cluster CI: operators resampled, %d draws. Permutation p: %d label shuffles. 'fixed' thresholds are the "
           "VALIDATION score quantiles frozen in the lock; 'rank' takes the top k %% of TEST itself." % (
               lock["locked_at_utc"], "VALIDATION standing in (REHEARSAL)" if test is val else
               "alerts after the first snapshot", B, 2000), ""]
    summary: dict[str, Any] = {}
    head = next(m for m in lock["models"] if [m["set"], m["entry"]] == lock["headline"])
    final_rows = []
    for m in lock["models"]:
        rr, s, y, cl = scored(m, test)
        if not rr or not sum(y) or sum(y) == len(y):
            continue
        base = sum(y) / len(y)
        auc = fml.roc_auc(s, y)
        ci = boot_auc(s, y, cl)
        pp = perm_p(s, y) if m is head or m["set"] in ("F_no_price", "R_price_only") else None
        thr10 = m["val_thresholds"]["0.1"]
        sel10 = [x >= thr10 for x in s]
        k10 = sum(yy for yy, ok in zip(y, sel10) if ok)
        n10 = sum(sel10)
        rk, rn = fml.top_k(s, y, 0.10)
        t10 = trades(rr, sel10, m["entry"], tr["strategies"]["HOLD_1h"], 10, 500)
        summary[m["set"] + "_" + m["entry"]] = {"auc": auc, "ci": ci, "perm_p": pp, "base": base, "n": len(y),
                                                "fixed10": [k10, n10], "rank10": [rk, rn],
                                                "pr_auc": fml.pr_auc(s, y), "brier": fml.brier(s, y),
                                                "ece": fml.ece(s, y)[0], "trade10": t10}
        final_rows.append((m, len(y), base, k10, n10, rk, rn, fml.pr_auc(s, y), t10, auc, ci))
    out += ["## Ablation (final table)", "",
            "| Model | entry | Features | N Test | P2X, top 10 % fixed | Baseline | Lift | PR-AUC | Precision@10 % "
            "(rank) | ROC-AUC [CI] | Net return, top 10 %, hold 1 h, +10 s, $500 |",
            "|---|---|---:|---:|---|---:|---:|---:|---|---|---|"]
    for m, n, base, k10, n10, rk, rn, pr, t10, auc, ci in final_rows:
        out.append("| %s | %s | %d | %d | %s | %.1f %% | %s | %.3f | %.1f %% (%d/%d) | %.3f [%.3f, %.3f] | %s |" % (
            m["set"], m["entry"], len(m["features"]), n,
            ("%.1f %% (%d/%d) %s" % (100 * k10 / n10, k10, n10, wilson(k10, n10))) if n10 else "n/a (0 selected)",
            100 * base, ("%+.1f pts" % (100 * (k10 / n10 - base))) if n10 else "n/a", pr, 100 * rk / rn, rk, rn,
            auc, ci[0], ci[1], fmt(t10)))

    # headline in detail
    rr, s, y, cl = scored(head, test)
    base = sum(y) / len(y)
    auc = fml.roc_auc(s, y)
    thr20 = head["val_thresholds"]["0.2"]
    at = fml.at_threshold(s, y, thr20)
    e, cal = fml.ece(s, y)
    out += ["", "## Headline model: %s, entry %s (%s %s)" % (head["set"], head["entry"], head["chosen"]["kind"],
                                                               json.dumps(head["chosen"]["hp"])), "",
            "N TEST %d, base P(2x) %.1f %%. ROC-AUC %.3f %s, permutation p %s. PR-AUC %.3f. Brier %.4f (base-rate "
            "Brier %.4f). ECE %.3f. At the VALIDATION top-20 %% threshold: precision %s, recall %s, F1 %s." % (
                len(y), 100 * base, auc, "[%.3f, %.3f]" % summary[head["set"] + "_" + head["entry"]]["ci"],
                "%.4f" % summary[head["set"] + "_" + head["entry"]]["perm_p"], fml.pr_auc(s, y), fml.brier(s, y),
                base * (1 - base), e, "n/a" if at["precision"] is None else "%.1f %%" % (100 * at["precision"]),
                "n/a" if at["recall"] is None else "%.1f %%" % (100 * at["recall"]),
                "n/a" if at["f1"] is None else "%.3f" % at["f1"]), "",
            "Calibration (deciles of score): %s." % "; ".join("%.2f->%.2f (n %d)" % c for c in cal), "",
            "### Critical table", "",
            "| Population | N (rank) | P(2X) (rank) | Lift | 95 % CI | coverage | N (fixed thr.) | P(2X) (fixed) |"
            " 95 % CI (fixed) |", "|---|---:|---:|---:|---|---:|---:|---:|---|",
            "| Tous | %d | %.1f %% | - | %s | 100 %% | - | - | - |" % (len(y), 100 * base, wilson(sum(y), len(y)))]
    for k in (0.5, 0.3, 0.2, 0.1, 0.05, 0.01):
        hk, nk = fml.top_k(s, y, k)
        thr = head["val_thresholds"][str(k)]
        fk = sum(yy for yy, x in zip(y, s) if x >= thr)
        fn = sum(1 for x in s if x >= thr)
        out.append("| Top %g %% | %d | %.1f %% | %+.1f pts | %s | %.1f %% | %d | %s | %s |" % (
            100 * k, nk, 100 * hk / nk, 100 * (hk / nk - base), wilson(hk, nk), 100 * nk / len(y), fn,
            ("%.1f %%" % (100 * fk / fn)) if fn else "n/a", wilson(fk, fn)))
    # other targets, same headline scores
    out += ["", "Same headline scores against the other targets (not refitted):", "",
            "| target | N | base | top 10 % (rank) | ROC-AUC |", "|---|---:|---:|---|---:|"]
    for t in ("A_1.5x_1h", "A_3x_1h", "A_5x_1h", "A_2x_15m", "A_2x_5m"):
        pairs = [(sc, r["y"].get(t)) for r, sc in zip(rr, s) if r["y"].get(t) is not None]
        if not pairs or not any(b for _, b in pairs):
            continue
        ss, yy = [a for a, _ in pairs], [b for _, b in pairs]
        hk, nk = fml.top_k(ss, yy, 0.1)
        out.append("| %s | %d | %.1f %% | %.1f %% (%d/%d) | %.3f |" % (t, len(yy), 100 * sum(yy) / len(yy),
                                                                   100 * hk / nk, hk, nk, fml.roc_auc(ss, yy)))
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "T4_test.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(out) + "\n")

    # importance
    names = head["features"]
    prep = fml.Prep.load(head["prep"])
    imp = Counter()
    st = head["state"]
    if st["type"] == "logreg":
        for j, w in enumerate(st["w"][1:]):
            imp[j] = abs(w)
    else:
        def walk(node: dict[str, Any]) -> None:
            if "f" in node:
                imp[node["f"]] += node.get("gain", 0.0)
                walk(node["l"])
                walk(node["r"])
        for t in ([st["root"]] if st["type"] == "tree" else st["trees"]):
            walk(t)

    def perm_imp(rs: list[dict[str, Any]]) -> dict[int, float]:
        rr_, s_, y_, _ = scored(head, rs)
        X = prep.transform([r["f" + head["entry"]] for r in rr_])
        a0 = fml.roc_auc(s_, y_) or 0.5
        rng = random.Random(SEED)
        out_: dict[int, float] = {}
        for j in range(len(names)):
            drops = []
            for _ in range(3):
                col = [x[j] for x in X]
                rng.shuffle(col)
                Xp = [x[:j] + [c] + x[j + 1:] for x, c in zip(X, col)]
                drops.append(a0 - (fml.roc_auc(fml.score_state(st, Xp), y_) or 0.5))
            out_[j] = sum(drops) / len(drops)
        return out_

    def direction(rs: list[dict[str, Any]]) -> dict[int, float]:
        rr_, s_, _, _ = scored(head, rs)
        X = prep.transform([r["f" + head["entry"]] for r in rr_])
        out_ = {}
        for j in range(len(names)):
            col = [x[j] for x in X]
            out_[j] = spearman(col, s_)
        return out_
    pv, pt = perm_imp(val), perm_imp(test)
    dv, dt = direction(val), direction(test)
    tot = sum(imp.values()) or 1.0
    order = sorted(range(len(names)), key=lambda j: -(pv.get(j, 0)))
    fam = FAMILY
    imp_lines = ["# T5. What the headline model uses (association, not causation)", "",
                 "Model importance: split gain share (trees) or |standardised coefficient| share (logistic). "
                 "Permutation importance: drop in ROC-AUC when the feature's column is shuffled (3 repeats). "
                 "Direction: sign of the Spearman correlation between the feature and the model score. Robust OOS: "
                 "positive permutation importance on TEST and the same direction as on VALIDATION.", "",
                 "| Feature | Category | Available at entry | Model importance | Perm. importance VAL | "
                 "Perm. importance TEST | Direction | Robust OOS |", "|---|---|---|---:|---:|---:|---|---|"]
    for j in order[:30]:
        robust = pt.get(j, 0) > 0.002 and (dv[j] > 0) == (dt[j] > 0)
        imp_lines.append("| %s | %s | true | %.3f | %+.4f | %+.4f | %s | %s |" % (
            names[j], fam.get(names[j], "?"), imp.get(j, 0.0) / tot, pv[j], pt[j],
            "higher -> higher score" if dv[j] > 0 else "higher -> lower score", "yes" if robust else "no"))
    with open(os.path.join(outdir, "T5_importance.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(imp_lines) + "\n")

    # trading grid for the headline
    tl = ["# T6. Trading the headline score on TEST", "",
          "Selection by the fixed VALIDATION thresholds. Entry at the first price read at or after the alert (+30 s "
          "for entry V) + latency. Costs: %.0f %% per leg, %.3f SOL per transaction, price impact from the pool's SOL "
          "reserve read on chain before the cut-off, constant product for the exit. Mean per trade [95 %% cluster "
          "CI]." % (100 * tr["fee_per_leg"], tr["fixed_sol_per_tx"]), ""]
    for sname, strat in tr["strategies"].items():
        tl += ["## %s (TP %gx, SL %s, %d s)" % (sname, strat["tp"], "-" if strat["sl"] is None else
                                               "%+.0f %%" % (100 * (strat["sl"] - 1)), strat["timeout_s"]), "",
               "| selection | latency | $100 | $500 | $1 000 |", "|---|---:|---|---|---|"]
        for k in tr["tops"] + [1.0]:
            thr = head["val_thresholds"][str(k)] if k < 1 else -1.0
            sel = [x >= thr for x in s]
            for lat in tr["latencies_s"]:
                if k < 1 and lat not in (0, 10, 20) and sname != tr["primary"]:
                    continue
                cells = [fmt(trades(rr, sel, head["entry"], strat, lat, sz)) for sz in tr["sizes_usd"]]
                tl.append("| %s | +%d s | %s |" % ("all alerts" if k == 1 else "top %g %%" % (100 * k), lat,
                                                    " | ".join(cells)))
        tl.append("")
    with open(os.path.join(outdir, "T6_trading.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(tl) + "\n")

    # robustness
    rb = ["# T7. Robustness of the headline model on TEST", ""]
    days = sorted({r["utc"][:10] for r in rr})
    half = days[len(days) // 2] if days else ""
    for lab, cond in (("first half of TEST (%s to before %s)" % (days[0] if days else "", half),
                       lambda r: r["utc"][:10] < half), ("second half", lambda r: r["utc"][:10] >= half)):
        idx = [i for i, r in enumerate(rr) if cond(r)]
        ss, yy = [s[i] for i in idx], [y[i] for i in idx]
        if ss and 0 < sum(yy) < len(yy):
            hk, nk = fml.top_k(ss, yy, 0.1)
            rb.append("- %s: N %d, base %.1f %%, ROC-AUC %.3f, top 10 %% %.1f %% (%d/%d)." % (
                lab, len(yy), 100 * sum(yy) / len(yy), fml.roc_auc(ss, yy), 100 * hk / nk, hk, nk))
    thr10 = head["val_thresholds"]["0.1"]
    sel = [i for i, x in enumerate(s) if x >= thr10]
    clc = Counter(cl[i] for i in sel)
    rb.append("- top 10 %% (fixed): %d alerts from %d operator clusters; the largest holds %d." % (
        len(sel), len(clc), max(clc.values()) if clc else 0))
    loo = []
    for c in clc:
        kept = [i for i in sel if cl[i] != c]
        if kept:
            loo.append(sum(y[i] for i in kept) / len(kept))
    if loo:
        rb.append("- leave-one-cluster-out P(2x) in the top 10 %%: %.1f %% to %.1f %% (%d clusters)." % (
            100 * min(loo), 100 * max(loo), len(loo)))
    rb.append("- ANSEM: created 2026-06-16, outside every window of this study and outside the detector's "
              "definition; with and without ANSEM are the same numbers.")
    with open(os.path.join(outdir, "T7_robustness.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(rb) + "\n")

    # verdict by the locked rules
    h = summary[head["set"] + "_" + head["entry"]]
    npr = summary.get("F_no_price_" + head["entry"], {})
    k10, n10 = h["fixed10"]
    predictive = h["ci"][0] > 0.5 and (h["perm_p"] or 1) < 0.05
    strong = h["auc"] >= 0.70 and n10 > 0 and pde.wilson(k10, n10)[0] >= h["base"] + 0.20
    on_chain = bool(npr) and npr["ci"][0] > 0.5
    lo_net = (h["trade10"].get("net_ci") or (None, None))[0]
    tradable = lo_net is not None and lo_net > 0
    n_obs = h["n"]
    if n_obs < 300:
        verdict = "INCONCLUSIVE"
    elif predictive and strong and on_chain and tradable:
        verdict = "ROBUST ON-CHAIN SIGNAL"
    elif predictive and strong:
        verdict = "STATISTICAL SIGNAL - NOT TRADABLE"
    elif predictive:
        verdict = "WEAK ON-CHAIN SIGNAL"
    else:
        verdict = "NO ROBUST ON-CHAIN SEPARATION FOUND"
    summary["_verdict"] = {"predictive": predictive, "strong": strong, "on_chain": on_chain, "tradable": tradable,
                           "n_observed": n_obs, "verdict": verdict}
    with open(os.path.join(outdir if test is val else DERIVED, "final_test_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1, default=str)
    print("\n".join(out))
    print("\nVERDICT (locked rules): %s  %s" % (verdict, summary["_verdict"]))


def spearman(a: list[float], b: list[float]) -> float:
    def ranks(v: list[float]) -> list[float]:
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    if n < 3:
        return 0.0
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else 0.0


if __name__ == "__main__":
    main()
