#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Table 3: the share of tokens whose all-time high is already behind them by the
time they become visible.

The measurement: for each token, the timestamp of the pump.fun high
(`ath_market_cap` and its ts) is compared with the timestamp of detection, the
first moment the token exists for an outside observer (a `complete` token seen
by the detector at most 12 s after its creation). That is a lower bound on any
human buyer's latency, since a human sees the token much later.

Three thresholds, published together because they answer different questions:
    ATH <= detect_ts        : the peak is already behind when the token appears
    ATH < detect_ts + 60 s  : the peak is behind before one could decide
    ATH < detect_ts + 120 s : the same, with two minutes to react

Split by market-cap band at detection: the phenomenon concentrates on the tokens
that appear low, the ones that look like a bargain.

Limit: `o_ath_ts` comes from the pump.fun API, resolved to the second, and
`detect_ts` from the detector's local clock; a gap of a few seconds is possible.
Hence the three thresholds, and a conclusion that does not rest on the tightest.

Population: the clean B socle, healthy MC regime, 5k < mc < 300k, known high.

Usage: python3 code/t3_ath_avant_detection.py
Outputs: docs/tables/T3_ath_avant_detection.md, data/t3_ath_avant_detection.json
"""
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, dump_json, load_socle, write_table
from statlib import wilson

BANDS = [(5000, 20000), (20000, 30000), (30000, 40000), (40000, 50000),
         (50000, 65000), (65000, 85000), (85000, 120000), (120000, 300000)]


def main():
    d = load_socle()
    rows = [r for r in d["B"]
            if r.get("q_mc_regime_ok") and r.get("q_mc_plausible")
            and r.get("o_ath_true") and (r.get("detect_mc") or 0) > 0
            and r.get("o_ath_ts") and r.get("detect_ts")]
    ndays = len({r["day"] for r in rows})
    nclu = len({r["cluster_id"] for r in rows})
    print(f"n={len(rows)} tokens, {nclu} clusters, {ndays} jours")

    def bloc(sub):
        n = len(sub)
        k0 = sum(1 for r in sub if r["o_ath_ts"] <= r["detect_ts"])
        k60 = sum(1 for r in sub if r["o_ath_ts"] < r["detect_ts"] + 60)
        k120 = sum(1 for r in sub if r["o_ath_ts"] < r["detect_ts"] + 120)
        lo, hi = wilson(k60, n)
        delays = [(r["o_ath_ts"] - r["detect_ts"]) / 60.0 for r in sub]
        return {"n": n,
                "ath_avant_detection_pct": round(100 * k0 / n, 1),
                "ath_avant_60s_pct": round(100 * k60 / n, 1),
                "ath_avant_60s_ic95": [round(100 * lo, 1), round(100 * hi, 1)],
                "ath_avant_120s_pct": round(100 * k120 / n, 1),
                "delai_ath_median_min": round(st.median(delays), 1)}

    tab, out = [], {}
    for lo_, hi_ in BANDS:
        sub = [r for r in rows if lo_ <= r["detect_mc"] < hi_]
        if len(sub) < 5:
            continue
        b = bloc(sub)
        out[f"{lo_//1000}k-{hi_//1000}k"] = b
        tab.append([f"{lo_//1000}k-{hi_//1000}k", b["n"],
                    f"{b['ath_avant_detection_pct']:.1f}",
                    f"{b['ath_avant_60s_pct']:.1f}",
                    f"[{b['ath_avant_60s_ic95'][0]:.1f}, {b['ath_avant_60s_ic95'][1]:.1f}]",
                    f"{b['ath_avant_120s_pct']:.1f}",
                    f"{b['delai_ath_median_min']:.1f}"])

    sub20 = [r for r in rows if r["detect_mc"] < 20000]
    b20 = bloc(sub20)
    tot = bloc(rows)
    out["_sous_20k"] = b20
    out["_toutes_bandes"] = tot
    tab.append(["--- < 20k (aggregated)", b20["n"], f"{b20['ath_avant_detection_pct']:.1f}",
                f"{b20['ath_avant_60s_pct']:.1f}",
                f"[{b20['ath_avant_60s_ic95'][0]:.1f}, {b20['ath_avant_60s_ic95'][1]:.1f}]",
                f"{b20['ath_avant_120s_pct']:.1f}", f"{b20['delai_ath_median_min']:.1f}"])
    tab.append(["--- whole population", tot["n"], f"{tot['ath_avant_detection_pct']:.1f}",
                f"{tot['ath_avant_60s_pct']:.1f}",
                f"[{tot['ath_avant_60s_ic95'][0]:.1f}, {tot['ath_avant_60s_ic95'][1]:.1f}]",
                f"{tot['ath_avant_120s_pct']:.1f}", f"{tot['delai_ath_median_min']:.1f}"])

    txt = write_table(
        "T3_ath_avant_detection",
        ["MC band at detection", "n", "ATH already past %", "ATH < +60 s %",
         "95% CI %", "ATH < +120 s %", "median ATH delay (min)"],
        tab,
        ["",
         f"n = {len(rows)} tokens | {nclu} clusters | {ndays} UTC days | clean population B.",
         "`detect_ts` = first outside visibility (token `complete` seen <= 12 s "
         "after creation). A lower bound on a human buyer's latency.",
         "A negative median delay means that, within the band, the typical token "
         "peaked before it existed for the observer.",
         "Limit: `o_ath_ts` (pump.fun API) and `detect_ts` (local clock) can differ "
         "by a few seconds; the three thresholds are published for that reason.",
         "", "Regenerate: `python3 code/t3_ath_avant_detection.py`"])
    print(txt)
    dump_json({"n": len(rows), "n_clusters": nclu, "n_jours": ndays, "bandes": out},
              os.path.join(DATA, "t3_ath_avant_detection.json"))


if __name__ == "__main__":
    main()
