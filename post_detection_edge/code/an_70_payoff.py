#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Why a hit rate is not a return: the payoff of the locked signals on TEST.

Descriptive, written after the final test and selecting nothing: it reads
LOCK.json and final_test_summary.json and decomposes the trades of three
populations (every alert, the headline signal, and every signal that survived
TEST) into the share that reached the take-profit, the mean of those that
did not, and the break-even hit rate those two numbers imply:
    p* = -loss / (gain - loss)
It also prints the surviving signal by horizon, like the headline table of T4,
and the gross mean of every pre-declared strategy with its cluster CI.
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable

import pde
import trade
from an_30_univariate import label
from an_60_final_test import member_fn


def decompose(rows: list[dict[str, Any]], fn: Callable, S: dict, strat: dict[str, Any], lat: float,
              cost: dict[str, Any]) -> dict[str, Any]:
    win_g, lose_g, win_n, lose_n, gross_all = [], [], [], [], []
    for r in rows:
        if not fn(r):
            continue
        sim = trade.simulate(S.get(r["mint"]) or [], r["fine"], lat, strat["tp"], strat["sl"], strat["timeout_s"])
        if sim["status"] != "ok":
            continue
        net = trade.net_return(sim["gross"], sim["entry_mult"], r["p0"], r["f"]["p0_source"], r["t"], 500, cost)
        gross_all.append((r["cluster"], sim["gross"] - 1))
        if sim["reason"] == "tp":
            win_g.append(sim["gross"] - 1)
            win_n.append(net)
        else:
            lose_g.append(sim["gross"] - 1)
            lose_n.append(net)
    n = len(win_g) + len(lose_g)

    def be(w: list[float], lo: list[float]) -> str:
        if not w or not lo:
            return "n/a"
        g, loss = sum(w) / len(w), sum(lo) / len(lo)
        return "%.1f %%" % (100 * -loss / (g - loss)) if g > loss else "n/a"
    return {"n": n, "tp": len(win_g), "tp_rate": len(win_g) / n if n else None,
            "mean_nontp_gross": sum(lose_g) / len(lose_g) if lose_g else None,
            "mean_tp_net": sum(win_n) / len(win_n) if win_n else None,
            "mean_nontp_net": sum(lose_n) / len(lose_n) if lose_n else None,
            "breakeven_gross": be(win_g, lose_g), "breakeven_net": be(win_n, lose_n),
            "gross_ci": pde.cluster_boot_mean(gross_all),
            "gross_mean": sum(g for _, g in gross_all) / len(gross_all) if gross_all else None}


def main() -> None:
    lock = json.load(open(os.path.join(pde.TABLES, "LOCK.json")))
    summ = json.load(open(os.path.join(pde.DERIVED, "final_test_summary.json")))
    test = pde.read_rows("dataset_test.sealed.jsonl.gz")
    everything = pde.read_rows("dataset_dev.jsonl.gz") + test
    S = pde.load_series()
    cost = lock["cost_model"]
    strats = lock["strategies"]
    by_id = {s["id"]: s for s in lock["signals"]}
    survivors = [sid for sid, v in summ.items() if v["survives"]]
    fams = [("ALL ALERTS", lambda r: True)] + [(sid, member_fn(by_id[sid]))
                                              for sid in [lock["headline_signal"]] + survivors]
    out = ["# T8. Payoff decomposition on TEST (descriptive, after the lock)", "",
           "Per trade, entry at +10 s, $500 for the net column. 'break-even hit rate' = the take-profit share at "
           "which the mean of the take-profit trades and the mean of the others would net to zero. "
           "Regenerate: `python3 post_detection_edge/code/an_70_payoff.py`.", "",
           "| population | strategy | trades | TP reached | mean of non-TP trades, gross | break-even hit rate, "
           "gross | mean TP trade, net | mean non-TP trade, net | break-even hit rate, net | gross mean "
           "[cluster CI] |", "|---|---|---:|---|---:|---:|---:|---:|---:|---|"]
    for name, fn in fams:
        for sn in ("S1", "S2", "S3", "HOLD_5m", "HOLD_15m", "HOLD_1h"):
            d = decompose(test, fn, S, strats[sn], 10, cost)
            if not d["n"]:
                continue
            lo, hi = d["gross_ci"]
            out.append("| %s | %s | %d | %s | %+.1f %% | %s | %+.1f %% | %+.1f %% | %s | %+.1f %% [%+.1f, %+.1f] |" % (
                name, sn, d["n"], pde.rate_cell(d["tp"], d["n"]), 100 * (d["mean_nontp_gross"] or 0),
                d["breakeven_gross"], 100 * (d["mean_tp_net"] or 0), 100 * (d["mean_nontp_net"] or 0),
                d["breakeven_net"], 100 * d["gross_mean"], 100 * lo, 100 * hi))
    for sid in survivors:
        fn = member_fn(by_id[sid])
        out += ["", "## Surviving signal by horizon, TEST: %s (%s)" % (sid, by_id[sid]["text"]), "",
                "| Horizon | Baseline P2x | Signal P2x | N signal | 95 % CI (Wilson) | Signal P2x, all splits |",
                "|---|---|---|---:|---|---|"]
        for hh in pde.HORIZONS:
            b = [label(r, 2.0, hh) for r in test if label(r, 2.0, hh) is not None]
            sg = [label(r, 2.0, hh) for r in test if label(r, 2.0, hh) is not None and fn(r)]
            al_ = [label(r, 2.0, hh) for r in everything if label(r, 2.0, hh) is not None and fn(r)]
            lo_, hi_ = pde.wilson(sum(sg), len(sg))
            out.append("| %s | %s | %s | %d | %s | %s |" % (
                pde.H_LABEL[hh], pde.rate_cell(sum(b), len(b)) if b else "n/a",
                ("%.1f %%" % (100 * sum(sg) / len(sg))) if sg else "n/a", len(sg),
                "n/a" if lo_ is None else "[%.1f, %.1f]" % (100 * lo_, 100 * hi_),
                pde.rate_cell(sum(al_), len(al_)) if al_ else "n/a"))
        out += ["", "MFE from P0 on TEST (touched, not cashed), signal against every alert:", "",
                "| horizon | signal: median / mean / N | all alerts: median / mean / N |", "|---|---|---|"]
        for hh in (300, 900, 3600):
            key = "L0_%s" % pde.H_LABEL[hh]
            obs = [r for r in test if r["targets"][key]["status"] == "observed"]
            cells = []
            for grp in ([r for r in obs if fn(r)], obs):
                v = [r["targets"][key]["mfe"] for r in grp]
                cells.append("%.2f / %.2f / %d" % (pde.median(v), sum(v) / len(v), len(v)))
            out.append("| %s | %s |" % (pde.H_LABEL[hh], " | ".join(cells)))
        out += ["", "Same signal, other thresholds on TEST at 15 min and 1 h:", "",
                "| threshold | 15 min: signal / base | 1 h: signal / base |", "|---|---|---|"]
        for k in pde.THRESHOLDS:
            cells = []
            for hh in (900, 3600):
                b = [label(r, k, hh) for r in test if label(r, k, hh) is not None]
                sg = [label(r, k, hh) for r in test if label(r, k, hh) is not None and fn(r)]
                cells.append("%s / %s" % (pde.rate_cell(sum(sg), len(sg)), pde.pct(sum(b) / len(b))))
            out.append("| %gx | %s |" % (k, " | ".join(cells)))
    # entry latency, whole population: fine-sampled alerts only, so every
    # latency is measured on the same alerts
    fine = [r for r in everything if r["fine"]]
    out += ["", "## Entry latency, whole population (fine-sampled alerts, TRAIN + VALIDATION + TEST)", "",
            "Entry = the first spot read at or after +L s. 'entry vs P0' = median price paid relative to P0. "
            "MFE and hit rates from that entry, complete-case. +1 s and +3 s are not measurable: the reads "
            "are ~5 s apart.", "",
            "| entry | horizon | N observed | entry vs P0 (median) | median MC at entry, USD | MFE median | "
            "P(>=1.5x) | P(>=2x) | P(>=3x) | P(>=5x) | P(>=10x) |",
            "|---|---|---:|---:|---:|---:|---|---|---|---|---|"]
    for lat in pde.LATENCIES + (30, 60):
        for hh in (60, 900, 3600):
            key = "L%d_%s" % (lat, pde.H_LABEL[hh])
            if lat in pde.LATENCIES:
                obs = [(r, r["targets"][key]) for r in fine if r["targets"][key]["status"] == "observed"]
            else:
                # +30 s and +60 s were not built into the dataset: same functions, computed here
                obs = []
                for r in fine:
                    pts = S.get(r["mint"]) or []
                    ent = pde.entry_point(pts, lat) if pts else None
                    if ent is None:
                        continue
                    mx, ok = pde.window(pts, ent[0], hh, True)
                    if ok:
                        obs.append((r, {"entry_mult": ent[1], "mfe": mx / ent[1]}))
            if not obs:
                continue
            em = pde.median([t["entry_mult"] for _, t in obs])
            mc = pde.median([r["f"]["mc_usd"] * t["entry_mult"] for r, t in obs])
            cells = [pde.rate_cell(sum(1 for _, t in obs if t["mfe"] >= k), len(obs)) for k in pde.THRESHOLDS]
            out.append("| +%d s | %s | %d | %.3f | %.0f | %.2f | %s |" % (
                lat, pde.H_LABEL[hh], len(obs), em, mc, pde.median([t["mfe"] for _, t in obs]), " | ".join(cells)))
    pde.write_table("T8_payoff.md", "\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
