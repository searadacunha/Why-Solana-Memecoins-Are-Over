#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temporal leakage audit of every feature, written to temporal_leakage_audit.md.

Three parts.
  1. Declared: for each PRE_ENTRY feature of the registry, the exact source,
     the time it reads, the cut-off it is held to, and a verdict SAFE / LEAK /
     AMBIGUOUS, from the rules below (one per family, overrides by name).
  2. Empirical, windows: every feature is computed twice on every collected
     window, once with the window truncated at the cut-off (the production
     path) and once untruncated with every wallet kept. A feature whose value
     changes reads something after the cut-off when it is allowed to: that is
     the leak the truncation now blocks. The production path is then checked
     for invariance: appending the post-cut-off records must not move it.
  3. Empirical, wallets: every wallet kept at a cut-off appeared in the window
     at or before it, and every earlier transaction in its history precedes
     that first appearance.
Nothing here writes outside this report.
"""
from __future__ import annotations

import gzip
import json
import os
from collections import Counter
from typing import Any

import col_20_wallets as W
import feat_30_build as FB
import fparse

RULES = {
    "bundle": ("creation-slot records of the window", "block time of the creation slot", "SAFE",
               "the creation slot precedes every cut-off (alert age >= 5.3 s)"),
    "micro": ("window records truncated at the cut-off", "block time <= cut-off", "SAFE", "truncated before parsing"),
    "price": ("window records truncated at the cut-off; P0 from the alert", "block time <= cut-off; P0 at the alert",
              "SAFE", "P0 is the entry price read at the alert, i.e. at T_ENTRY"),
    "premium": ("P0 and the core VWAP from the alert", "alert", "SAFE", "both known at T_ENTRY"),
    "actor": ("core purchases per transaction in the creation block", "creation slot", "SAFE",
              "for 112 early alerts the label was computed later by the detector, from the same creation block"),
    "wallets": ("getSignaturesForAddress before each wallet's first window transaction", "< first appearance <= "
                "cut-off", "SAFE", "wallets appearing after the cut-off are dropped"),
    "history": ("earlier transactions of each wallet / detector journal / earlier windows", "< first appearance, "
                "< alert, or < cut-off", "SAFE", "journal counts use earlier alerts only"),
    "funding": ("genesis funding (hop 1); funders walked before their earliest funding in the corpus (hops 2-3)",
                "genesis <= first appearance; earliest funding <= every launch it is linked to", "SAFE",
                "hub status and deeper hops no longer read today's history (fixed 2026-09-29)"),
    "context": ("detector journal", "lines before the alert", "SAFE", "SOL/USD: previous hour's close"),
}
OVERRIDES = {
    "p_curve_left_sol": ("SAFE", "was LEAK before 2026-09-29: used a migration after the alert (13 / 182 windows); "
                                 "now reads the truncated window only"),
    "p_log_mc_usd": ("SAFE", "was AMBIGUOUS: used the close of the alert's own hour (up to 59 min later); now the "
                             "previous hour"),
    "g_core_min_dist": ("SAFE", "was AMBIGUOUS: hops 2-3 depended on today's hub status; now causal"),
    "g_core_creator_dist": ("SAFE", "same as g_core_min_dist"),
    "g_early_linked": ("SAFE", "same as g_core_min_dist"),
    "g_density": ("SAFE", "same as g_core_min_dist"),
    "f_indep_actors_loose": ("SAFE", "uses the causal lineage"),
}


def skeleton_wal(a: dict[str, Any], recs: list[dict[str, Any]]) -> dict[str, Any]:
    """Wallet roles only (no RPC), for windows whose wallet stage is not collected."""
    return {"wallets": {w: {"role": r, "cursor": c, "prior": {"n": 0, "bts": [], "n_err": 0}}
                        for w, r, c in W.roles(a, recs)}}


def main() -> None:
    journal = FB.pde.load_journal()
    alerts = {r["mint"]: r for r in journal if r["genre"] == "alerte_lancement"}
    ctx = FB.context(journal, FB.sol_usd_table(os.path.join(FB.pde.DATA, "sol_usd_hourly.json")))
    changed: Counter[str] = Counter()
    not_invariant: Counter[str] = Counter()
    n = 0
    wal_checks = Counter()
    for f in sorted(os.listdir(FB.WIN)):
        if not f.endswith(".json.gz"):
            continue
        w = json.load(gzip.open(os.path.join(FB.WIN, f), "rt"))
        a = alerts[w["mint"]]
        recs, _ = fparse.parse_window(w)
        lp = os.path.join(FB.WAL, a["mint"] + ".json.gz")
        wal = json.load(gzip.open(lp, "rt")) if os.path.exists(lp) else skeleton_wal(a, recs)
        n += 1
        for key, off in FB.CUTS.items():
            cut = a["t"] + off
            roles = ("core", "creator", "early", "late") if key == "V" else ("core", "creator", "early")
            FB.TRUNCATE = True
            safe = FB.features_for(a, w, wal, ctx.get(a["mint"], {}), cut, roles, {}, None)
            # invariance: the production path given a window cut exactly at the cut-off
            w_cut = {**w, "sigs": [s for s in w["sigs"] if (s.get("bt") or 0) <= cut]}
            safe2 = FB.features_for(a, w_cut, wal, ctx.get(a["mint"], {}), cut, roles, {}, None)
            FB.TRUNCATE = False
            raw = FB.features_for(a, w, wal, ctx.get(a["mint"], {}), cut, roles, {}, None)
            FB.TRUNCATE = True
            for k in safe:
                if safe.get(k) != safe2.get(k):
                    not_invariant[k] += 1
                if safe.get(k) != raw.get(k):
                    changed[(key, k)] += 1
        # wallet checks at the primary cut-off
        bt_of = {s["sig"]: s.get("bt") for s in w["sigs"]}
        for x, v in wal["wallets"].items():
            fb = bt_of.get(v["cursor"])
            wal_checks["wallets"] += 1
            if v["role"] in ("core", "creator", "early") and fb is not None and fb > a["t"] - 1:
                wal_checks["kept wallet first seen after the primary cut-off"] += 1
            if fb is not None and any(b and b > fb for b in v["prior"].get("bts", [])):
                wal_checks["history transaction after the first appearance"] += 1
    reg = [x for x in FB.FEATURES]
    lines = ["# Temporal leakage audit", "",
             "Generated by `code/qa_10_leakage.py` on %d collected windows. "
             "Cut-offs relative to the alert: %s. "
             "No LEAK or AMBIGUOUS feature enters a model." % (n, FB.CUTS),
             "",
             "## 1. Declared, per feature", "",
             "| feature | family | exact source | time used | cut-off | verdict | note |",
             "|---|---|---|---|---|---|---|"]
    for x in reg:
        if x["causal_status"] != "PRE_ENTRY":
            lines.append("| %s | %s | %s | %s | - | %s | excluded from every model |" % (
                x["name"], x["family"], x["source"], x["availability"],
                "LEAK" if x["causal_status"] == "POST_ENTRY" else "AMBIGUOUS"))
            continue
        src, used, verdict, note = RULES[x["family"]]
        if x["name"] in OVERRIDES:
            verdict, note = OVERRIDES[x["name"]]
        lines.append("| %s | %s | %s | %s | alert - 1 s (A), -2 s, -5 s, +29 s (V) | %s | %s |" % (
            x["name"], x["family"], src, used, verdict, note))
    lines += ["", "## 2. Empirical: what an untruncated window would have leaked", "",
              "Windows where the feature's value differs between the untruncated computation and the production "
              "(truncated) one. These are the features that WOULD read post-cut-off data if the truncation were "
              "removed; with it, they cannot.", "", "| cut-off | feature | windows that differ |", "|---|---|---:|"]
    for (key, k), c in sorted(changed.items(), key=lambda z: (z[0][0], -z[1])):
        lines.append("| %s | %s | %d |" % (key, k, c))
    lines += ["", "Invariance of the production path (the same features on a window cut exactly at the cut-off): "
              "%s." % ("identical on every window and feature" if not not_invariant else
                       "DIFFERENCES: %s" % dict(not_invariant)), "",
              "## 3. Empirical: wallets", "", "%s." % dict(wal_checks), "",
              "Note on the previous study: post_detection_edge/code/build_10_dataset.py priced `log10_mc_usd` with "
              "the close of the alert's own hour (up to 59 min of SOL/USD look-ahead). It fed the H2 / H2b "
              "hypotheses and a univariate feature there; that study is frozen and is not modified."]
    with open(os.path.join(FB.STUDY, "temporal_leakage_audit.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[-12:]))
    print("changed features:", sorted({k for (_, k) in changed}))


if __name__ == "__main__":
    main()
