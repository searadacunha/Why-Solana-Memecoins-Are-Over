#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feat_27_pumpgold.py -- candidate features suggested by the Pump-Gold dataset concepts
(wash trading, economic diversity, flow, timing, artificial coordination), rebuilt at decision time.

Pump-Gold (Solid-Sea/pump-gold-dataset) publishes only whole-life aggregates per token: buy_count,
sell_count, unique_wallets, total_quote, avg_swap_size, pmin / pmax. Here the same concepts are
measured on the EXTERNAL trades of the pre-alert window only (creation -> alert - 1 s, block time
<= t - cut), external = trader outside the core snipers and the creator, slot-0 buys excluded
(the bundle itself is described by the b_* family). Source: the raw windows cached locally by
post_detection_forensics (every transaction creation -> alert + 30 s), parsed with its fparse.py;
records after the cut are dropped BEFORE any statistic. No outcome is read.

Usage: python3 feat_27_pumpgold.py [--cut 1|2]   (default 1: alert - 1 s; 2 = alert - 2 s variant)
"""
from __future__ import annotations

import gzip
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np

import ap_lib as A

sys.path.insert(0, os.path.join(A.W, "post_detection_forensics", "code"))
import fparse  # noqa: E402

WIN = os.path.join(A.CRYPTO, "Why-Solana-Memecoins-Are-Over", "post_detection_forensics", "data", "onchain_cache", "win")

DICT = {
    # wash-trading intensity
    "pg_tx_per_wallet": "external buys + sells per distinct external trader",
    "pg_buys_per_buyer": "external buys per distinct external buyer",
    "pg_repeat_buyer_sol_share": "share of external buy SOL from wallets with >= 2 buys",
    "pg_max_buys_one_wallet": "largest number of external buys by one wallet",
    "pg_roundtrip_wallets": "external wallets that both bought and sold before the cut",
    "pg_roundtrip_share": "round-trip wallets / distinct external buyers",
    "pg_roundtrip_sol_share": "SOL sold by round-trip wallets / external buy SOL",
    "pg_seller_buyer_overlap": "external sellers that had bought in the window / external sellers",
    "pg_sell_buy_count_ratio": "external sells / external buys",
    "pg_pingpong_10s": "buy followed by a sell of the same wallet within 10 s (count)",
    "pg_same_size_share": "share of external buys whose SOL size (1e-3) is repeated by another buy",
    "pg_modal_size_share": "share of external buys at the modal SOL size (1e-3)",
    "pg_size_cv": "coefficient of variation of external buy sizes",
    # economic diversity
    "pg_wallets_per_sol": "distinct external buyers per SOL of external buys",
    "pg_sol_per_buyer": "external buy SOL per distinct external buyer",
    "pg_buy_gini": "Gini of external buy SOL across buyer wallets",
    "pg_top5_buyer_share": "share of external buy SOL from the 5 largest buyers",
    "pg_small_buy_share": "share of external buys below 0.05 SOL",
    "pg_big_buy_sol_share": "share of external buy SOL from buys >= 1 SOL",
    "pg_ext_over_bundle": "external buy SOL / bundle SOL (core tickets)",
    "pg_apparent_per_wallet": "(external buy + sell SOL) per distinct external trader",
    # flow
    "pg_sell_pressure": "external sell SOL / external buy SOL",
    "pg_core_sell_over_ext_buy": "core sniper sell SOL before the cut / external buy SOL",
    "pg_sell_first": "1 if the first external trade after slot 0 is a sell",
    "pg_buy_run_max": "longest run of consecutive external buys without an external sell",
    # timing
    "pg_buy_slot_gap_cv": "coefficient of variation of the slot gaps between consecutive external buys",
    "pg_novelty_2nd_half": "share of second-half external buys made by wallets absent from the first half",
    "pg_size_shift": "median external buy size, second half over first half of the window",
    "pg_fresh_ata_share": "token accounts opened by first-time wallets / distinct external buyers",
    # artificial coordination
    "pg_sync_same_size_pairs": "pairs of external buys in the same slot by different wallets within 5 % in size",
    "pg_same_slot_max_buyers": "largest number of distinct external buyers in one slot",
    "pg_payer_mismatch_share": "share of external trades whose fee payer is not the trader",
    "pg_modal_prio_share": "share of external trades paying the modal priority fee",
    "pg_multisig_share": "share of external trades with >= 2 signatures",
    "pg_n_ext_trades": "number of external trades (coverage)",
}


def gini(v):
    v = np.sort(np.asarray(v, dtype=float))
    n = len(v)
    if n == 0 or v.sum() <= 0:
        return None
    return float((2 * np.sum((np.arange(1, n + 1)) * v) / (n * v.sum())) - (n + 1) / n)


def features(recs, slot0, core, creator, t_cut, bundle_sol):
    ext_set = set(core) | ({creator} if creator else set())
    pre = [r for r in recs if (r.get("bt") or 0) <= t_cut]
    trades = [r for r in pre if r.get("kind") in ("buy", "sell") and not r.get("err") and r.get("trader")]
    ebuys = [r for r in trades if r["kind"] == "buy" and r["trader"] not in ext_set and r["slot"] != slot0]
    esells = [r for r in trades if r["kind"] == "sell" and r["trader"] not in ext_set]
    core_sells = [r for r in trades if r["kind"] == "sell" and r["trader"] in core]
    ext = sorted(ebuys + esells, key=lambda r: (r["slot"], r.get("bt") or 0))
    f = {k: None for k in DICT}
    f["pg_n_ext_trades"] = float(len(ext))
    if not ebuys:
        return f
    bsol = np.array([abs(r.get("v_sol") or 0.0) for r in ebuys])
    ssol = np.array([abs(r.get("v_sol") or 0.0) for r in esells]) if esells else np.array([])
    buyers = Counter(r["trader"] for r in ebuys)
    sol_by = defaultdict(float)
    for r, x in zip(ebuys, bsol):
        sol_by[r["trader"]] += x
    sellers = {r["trader"] for r in esells}
    traders = set(buyers) | sellers
    tot_b = float(bsol.sum())
    f["pg_tx_per_wallet"] = len(ext) / len(traders)
    f["pg_buys_per_buyer"] = len(ebuys) / len(buyers)
    f["pg_repeat_buyer_sol_share"] = (sum(sol_by[w] for w, c in buyers.items() if c >= 2) / tot_b) if tot_b else None
    f["pg_max_buys_one_wallet"] = float(max(buyers.values()))
    rt = {w for w in sellers if w in buyers}
    f["pg_roundtrip_wallets"] = float(len(rt))
    f["pg_roundtrip_share"] = len(rt) / len(buyers)
    f["pg_roundtrip_sol_share"] = (sum(abs(r.get("v_sol") or 0.0) for r in esells if r["trader"] in rt) / tot_b) if tot_b else None
    f["pg_seller_buyer_overlap"] = (len(rt) / len(sellers)) if sellers else None
    f["pg_sell_buy_count_ratio"] = len(esells) / len(ebuys)
    last_buy = {}
    pp = 0
    for r in ext:
        if r["kind"] == "buy":
            last_buy[r["trader"]] = r.get("bt") or 0
        elif r["trader"] in last_buy and (r.get("bt") or 0) - last_buy[r["trader"]] <= 10:
            pp += 1
    f["pg_pingpong_10s"] = float(pp)
    sizes = Counter(round(float(x), 3) for x in bsol)
    f["pg_same_size_share"] = sum(c for c in sizes.values() if c >= 2) / len(ebuys)
    f["pg_modal_size_share"] = max(sizes.values()) / len(ebuys)
    f["pg_size_cv"] = float(bsol.std() / bsol.mean()) if bsol.mean() > 0 else None
    f["pg_wallets_per_sol"] = (len(buyers) / tot_b) if tot_b else None
    f["pg_sol_per_buyer"] = tot_b / len(buyers)
    f["pg_buy_gini"] = gini(list(sol_by.values()))
    top = sorted(sol_by.values(), reverse=True)[:5]
    f["pg_top5_buyer_share"] = (sum(top) / tot_b) if tot_b else None
    f["pg_small_buy_share"] = float((bsol < 0.05).mean())
    f["pg_big_buy_sol_share"] = (float(bsol[bsol >= 1.0].sum() / tot_b)) if tot_b else None
    f["pg_ext_over_bundle"] = (tot_b / bundle_sol) if bundle_sol else None
    f["pg_apparent_per_wallet"] = (tot_b + float(ssol.sum())) / len(traders)
    f["pg_sell_pressure"] = (float(ssol.sum()) / tot_b) if tot_b else None
    f["pg_core_sell_over_ext_buy"] = (sum(abs(r.get("v_sol") or 0.0) for r in core_sells) / tot_b) if tot_b else None
    after0 = [r for r in ext if r["slot"] != slot0]
    f["pg_sell_first"] = (1.0 if after0 and after0[0]["kind"] == "sell" else 0.0) if after0 else None
    run = best = 0
    for r in ext:
        run = run + 1 if r["kind"] == "buy" else 0
        best = max(best, run)
    f["pg_buy_run_max"] = float(best)
    slots = sorted(r["slot"] for r in ebuys)
    gaps = np.diff(slots).astype(float)
    f["pg_buy_slot_gap_cv"] = float(gaps.std() / gaps.mean()) if len(gaps) >= 5 and gaps.mean() > 0 else None
    bts = [r.get("bt") or 0 for r in ebuys]
    t0, t1 = min(bts), t_cut
    half = t0 + (t1 - t0) / 2
    first = [r for r in ebuys if (r.get("bt") or 0) <= half]
    second = [r for r in ebuys if (r.get("bt") or 0) > half]
    if second and first:
        seen1 = {r["trader"] for r in first}
        f["pg_novelty_2nd_half"] = sum(1 for r in second if r["trader"] not in seen1) / len(second)
        m1 = np.median([abs(r.get("v_sol") or 0.0) for r in first])
        m2 = np.median([abs(r.get("v_sol") or 0.0) for r in second])
        f["pg_size_shift"] = float(m2 / m1) if m1 > 0 else None
    n_ata = sum(1 for r in pre if r.get("kind") == "ata")
    f["pg_fresh_ata_share"] = n_ata / len(buyers)
    by_slot = defaultdict(list)
    for r, x in zip(ebuys, bsol):
        by_slot[r["slot"]].append((r["trader"], float(x)))
    pairs = 0
    for lst in by_slot.values():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b = lst[i], lst[j]
                if a[0] != b[0] and max(a[1], b[1]) > 0 and abs(a[1] - b[1]) / max(a[1], b[1]) <= 0.05:
                    pairs += 1
    f["pg_sync_same_size_pairs"] = float(pairs)
    f["pg_same_slot_max_buyers"] = float(max(len({w for w, _ in lst}) for lst in by_slot.values()))
    f["pg_payer_mismatch_share"] = sum(1 for r in ext if r.get("signer") != r["trader"]) / len(ext)
    prios = Counter(r.get("prio", 0) for r in ext)
    f["pg_modal_prio_share"] = max(prios.values()) / len(ext)
    f["pg_multisig_share"] = sum(1 for r in ext if (r.get("n_sig") or 1) >= 2) / len(ext)
    return f


def main() -> None:
    cut = 1
    if "--cut" in sys.argv:
        cut = int(sys.argv[sys.argv.index("--cut") + 1])
    base = A.load_base()
    cd = {}
    for r in A.jl(A.CD_TABLE):
        cd[r["mint"]] = {"core": [s["wallet"] for s in r["snipers"] if s.get("role") == "core"],
                         "creator": (r.get("creator") or {}).get("wallet"), "slot0": r["slot0"],
                         "bundle_sol": r["ctl"].get("sol_bundle")}
    rows, rep = [], Counter()
    t0 = time.time()
    for i, b in enumerate(base):
        m = b["mint"]
        p = os.path.join(WIN, m + ".json.gz")
        w = json.load(gzip.open(p, "rt"))
        if abs(w["t_alert"] - b["t"]) > 1e-3:
            raise ValueError("window t_alert differs from base t: " + m)
        recs, facts = fparse.parse_window(w)
        t_cut = b["t"] - cut
        if any((r.get("bt") or 0) > t_cut for r in recs):
            rep["windows_with_records_after_cut_dropped"] += 1
        f = features(recs, w["slot0"], cd[m]["core"], cd[m]["creator"], t_cut, cd[m]["bundle_sol"])
        rows.append({"mint": m, **{k: (None if (isinstance(v, float) and not math.isfinite(v)) else v) for k, v in f.items()}})
        if (i + 1) % 200 == 0:
            print("%d / %d windows, %.0f s" % (i + 1, len(base), time.time() - t0), flush=True)
    out = os.path.join(A.DERIVED, "feat_pumpgold%s.jsonl.gz" % ("" if cut == 1 else "_cut%d" % cut))
    A.write_jl(out, rows)
    if cut == 1:
        with open(os.path.join(A.DERIVED, "feat_pumpgold_dictionary.md"), "w", encoding="utf8") as fh:
            fh.write("# Pump-Gold inspired features (pre-alert window, external trades, cut alert - 1 s)\n\n| feature | definition | non-null |\n|---|---|---|\n")
            for k, d in DICT.items():
                fh.write("| `%s` | %s | %d |\n" % (k, d, sum(1 for r in rows if r.get(k) is not None)))
    print("written", out, "cut", cut, dict(rep))
    for k in DICT:
        print("%-28s non-null %4d" % (k, sum(1 for r in rows if r.get(k) is not None)))


if __name__ == "__main__":
    main()
