#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feat_30_table.py -- one feature matrix for the 1,657 alerts, every column cut at the alert.

Sources (read only), all keyed by mint:
  fA   forensics analytic table, cut-off alert - 1 s (144)          + fA2 / fA5 variants
  ez   entry_zone f['D'] (alert cut-off)                             prefix ez_
  sc   sniper_capital launch features                                prefix sc_
  kg   known_group_reentry chronological group features              prefix kg_
  lv   detector live path (post_detection_edge f), SOL/USD look-ahead columns dropped   prefix lv_
  ss   signal_search families bundle_sizing / early_flow / funding / history / slot0
  pd   pattern_discovery non-fA, non-sc columns (cd_, dep_, fp_, fpc_, nb_)
  h1   this study's 1 h causal track records (feat_20_history.py)
No outcome is read here. Hindsight ids (cluster, operator) are never features.
"""
from __future__ import annotations

import json
import os
import re

import numpy as np

import ap_lib as A

LV_DROP = {"log10_mc_usd", "mc_usd"}          # SOL/USD close of the alert's own hour (look-ahead)
PD_KEEP = re.compile(r"^(cd_|dep_|fp_|fpc_|nb_)")
DEPTH = {"0": 0.0, "1": 1.0, "2-5": 2.0, ">5": 3.0}
STABILITY = {None: None, "weak": 0.0, "medium": 1.0, "strong": 2.0}

# mining families: an interaction must combine atoms of different families
PG_KEEP = ["pg_buys_per_buyer", "pg_repeat_buyer_sol_share", "pg_max_buys_one_wallet", "pg_roundtrip_sol_share",
           "pg_seller_buyer_overlap", "pg_same_size_share", "pg_modal_size_share", "pg_size_cv", "pg_buy_gini",
           "pg_buy_run_max", "pg_novelty_2nd_half", "pg_size_shift", "pg_sync_same_size_pairs", "pg_same_slot_max_buyers",
           "pg_payer_mismatch_share", "pg_modal_prio_share", "pg_multisig_share"]   # the 17 genuinely new (audit 06/10)

FAMILY_RULES = [
    ("WASH", r"^pg_(buys_per_buyer|repeat_buyer_sol_share|max_buys_one_wallet|roundtrip_sol_share|seller_buyer_overlap|"
             r"same_size_share|modal_size_share|modal_prio_share)$"),
    ("XFLOW", r"^pg_(size_cv|buy_gini|buy_run_max|novelty_2nd_half|size_shift|sync_same_size_pairs|same_slot_max_buyers|"
              r"payer_mismatch_share|multisig_share)$"),
    ("COORD", r"^x_motif_.*$"),
    ("BUNDLE", r"^(x_tip_over_bundle|x_prio_over_bundle)$"),
    ("FUND", r"^x_tl_spread$"),
    ("TEMPO", r"^(x_burst_pre|x_pre_slot_peak_share)$"),
    ("EXIT", r"^(m_core_exits|m_core_exit_share|m_core_sell_sol|m_creator_sells|m_sells|m_sellers|m_sell_sol|m_sell_max|"
             r"ef_bundle_moved_share|ef_bundle_sold_share|ef_first_exit_delay_s|ef_recipients_per_mover|"
             r"ef_nb_sol_after_exit_share|first_tp_sell_dslot_log)$"),
    ("TEMPO", r"^(p_time_since_creation_s|ef_px_.*|first_tp_buy_dslot)$"),
    ("PRICE", r"^(p_.*|ez_(log_mc_usd|log_price|mc_usd|premium|pool_sol|curve_left_sol|mult_since_alert)|"
              r"lv_(log10_p0|log10_vwap_op|entry_over_operator)|bs_bundle_over_pool)$"),
    ("CREATOR", r"^(w_creator_.*|h_creator_.*|g_creator_.*|b_creator_buy_sol|dep_.*|fu_creator_link|cd_creator_.*|"
                r"bs_creator_over_bundle|lv_creator_prev|h1_.*_c)$"),
    ("CLUSTER", r"^(kg_.*|h1_(npri|nres|ex\d|mfe|best|last2|net|since|n24)_(any|k|f)|tr_.*_(any|k|f)(_strict)?|"
                r"h_config_prev|lv_config_prev|g_funder_prior_uses|fu_funder_prior_alerts|fu_funder_since_prev_s|fpc_.*)$"),
    ("ACTOR", r"^(w_core_.*|w_early_.*|h_core_.*|h_early_.*|e_prior_.*|h_sniper_reuse_max|lv_sniper_reuse_max|"
              r"tr_.*_w|h1_.*_w|h1_e_.*|nb_d_.*|bs_nprior_spread)$"),
    ("COORD", r"^(fu_same_tx_funding|fu_fund_spread_s|fu_lead_s|sc_fund_time_spread_s|cd_fund_spread_s|cd_fund_to_buy_.*|"
              r"f_fund_to_buy_h|f_fund_to_alert_h|s0_core_interleave_log|s0_core_order_rho|s0_create_idx_log|fp_idx_.*|"
              r"fp_core_first_rank|fp_create_before_core|fp_create_gap|fp_foreign_create_to_core|b_core_signers|b_multi_buy)$"),
    ("FUND", r"^(g_.*|f_.*|ez_fu_.*|ez_cap_.*|sc_.*|fu_.*|cd_.*|bs_a_med|bs_after_min_log|bs_prefund_dry_share|bs_capital_spread)$"),
    ("TEMPO", r"^(m_.*|ef_.*|c_hour|c_dow|c_alerts_60m|c_candidates_60m|reg_.*|h1_reg.*|"
              r"lv_(hour_utc|dow|n_alerts_prev_60m|n_candidates_prev_60m|age_alert_s)|"
              r"ez_(buys_5s|buys_10s|n_buyers|n_early|t_first_outside|t_since_creation|sol_early_.*|sol_outside))$"),
    ("BUNDLE", r"^(b_.*|bs_.*|s0_.*|sk_.*|fp_.*|lv_.*|ez_.*|c_actor_grouped)$"),
]
FAMILY_RULES = [(f, re.compile(p)) for f, p in FAMILY_RULES]
# user families (A-H) for reporting
USER_FAMILY = {"WASH": "W wash trading of the external buyers (Pump-Gold concepts)",
               "XFLOW": "X diversity, flow and coordination of the external buyers (Pump-Gold concepts)",
               "FUND": "A funding graph", "COORD": "B coordination", "BUNDLE": "C bundles / MEV", "ACTOR": "D early actors",
               "CLUSTER": "E clusters", "CREATOR": "F creator / deployer", "TEMPO": "G temporal behaviour",
               "EXIT": "H exit (pre-alert)", "PRICE": "price / premium (known confounder)"}


def family_of(name: str) -> str:
    for fam, rx in FAMILY_RULES:
        if rx.match(name):
            return fam
    raise ValueError("no family for feature " + name)


def obs_of(name: str, src: str, pd_class: dict[str, str]) -> str:
    """Earliest moment the value is knowable live (refined by the causality audit in the inventory)."""
    if name.startswith("pg_"):
        return "ALERT: on-chain window creation -> alert - 1 s"
    if name.startswith("x_motif_"):
        return "ALERT + RPC: wallet / funder lookups (about 1-3 s live)"
    if name in ("x_tip_over_bundle", "x_prio_over_bundle"):
        return "T0: creation slot content"
    if src in ("h1", "kg") or name.startswith(("tr_", "reg_", "fpc_")) or name in (
            "h_config_prev", "h_sniper_reuse_max", "h_creator_prev_alerts", "g_funder_prior_uses", "fu_funder_prior_alerts",
            "fu_funder_since_prev_s", "e_prior_launches_median", "e_prior_launches_share", "e_prior_launches_max",
            "lv_config_prev", "lv_sniper_reuse_max", "lv_creator_prev"):
        return "HISTORY: earlier alerts (outcomes only once resolved)"
    if src == "lv":
        return "ALERT: detector live path, no extra call"
    if pd_class.get(name) == "T0" and name.startswith(("b_", "fp_", "c_")):
        return "T0: creation slot content"
    if name.startswith(("s0_", "sk_", "b_")):
        return "T0: creation slot content"
    if name.startswith(("g_", "f_", "w_", "h_", "sc_", "cd_", "fu_", "dep_", "ez_fu_", "ez_cap_", "nb_", "bs_")):
        return "ALERT + RPC: wallet / funder lookups (about 1-3 s live)"
    return "ALERT: on-chain window creation -> alert - 1 s"


def num(v):
    if v is None:
        return np.nan
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v) if np.isfinite(v) else np.nan
    raise TypeError(repr(v))


def main() -> None:
    base = A.load_base()
    idx = {b["mint"]: i for i, b in enumerate(base)}
    n = len(base)
    cols: dict[str, np.ndarray] = {}
    meta: dict[str, dict] = {}
    pd_meta = json.load(open(A.PD_FEATS))
    pd_class = {k: v["classe"] for k, v in pd_meta.items()}
    variants = {"fA2": {}, "fA5": {}}

    def put(name, src, mint, v):
        if name not in cols:
            cols[name] = np.full(n, np.nan, dtype=np.float64)
            meta[name] = {"source": src}
        elif meta[name]["source"] != src:
            raise ValueError("column defined by two sources: " + name)
        cols[name][idx[mint]] = num(v)

    for r in A.jl(A.ANALYTIC):
        for k, v in r["fA"].items():
            put(k, "fA", r["mint"], v)
        for var in ("fA2", "fA5"):
            for k, v in r[var].items():
                variants[var].setdefault(k, np.full(n, np.nan))[idx[r["mint"]]] = num(v)
    for r in A.jl(A.EZ_TABLE):
        for k, v in r["f"]["D"].items():
            put("ez_" + k, "ez", r["mint"], v)
    for r in A.jl(A.SC_TABLE):
        for k, v in r["f"].items():
            put("sc_" + k, "sc", r["mint"], v)
    for r in A.jl(A.KG_FEATS):
        m = r["mint"]
        put("kg_known", "kg", m, r["G1"] == "KNOWN")
        put("kg_partial", "kg", m, r["G1"] == "PARTIAL")
        for k in ("G2", "G2_strict", "G3", "G4", "one_funder_2plus", "prior_group_launches", "sniper_prior_max",
                  "snipers_seen", "since_group_s", "n_snipers_em"):
            put("kg_" + k, "kg", m, r[k])
        put("kg_depth", "kg", m, DEPTH[r["depth"]])
        # recency is a binned copy of since_group_s (kept numeric above); stability is ordinal
        put("kg_stability", "kg", m, STABILITY[r["stability"]])
    for path in (A.PDE_DEV, A.PDE_TEST):
        for r in A.jl(path):
            m = r["mint"]
            for k, v in r["f"].items():
                if k in LV_DROP:
                    continue
                if k == "actor":
                    put("lv_actor_grouped", "lv", m, None if v is None else (v == "grouped"))
                elif k == "p0_source":
                    put("lv_src_pool", "lv", m, v == "pool")
                else:
                    put("lv_" + k, "lv", m, v)
    for fam, path in A.SS_FEATS.items():
        for r in A.jl(path):
            for k, v in r.items():
                if k == "mint" or (k in cols and meta[k]["source"] == "fA"):
                    continue   # b_other_slot0_sol / b_core_tip_sol are copies of fA
                put(k, "ss_" + fam, r["mint"], v)
    for r in A.jl(A.PD_TABLE):
        for k, v in r["x"].items():
            if PD_KEEP.match(k):
                put(k, "pd", r["mint"], v)
    for r in A.jl(os.path.join(A.DERIVED, "feat_history1h.jsonl.gz")):
        for k, v in r.items():
            if k != "mint":
                put(k, "h1", r["mint"], v)

    for r in A.jl(os.path.join(A.DERIVED, "feat_derived.jsonl.gz")):
        for k, v in r.items():
            if k != "mint":
                put(k, "x", r["mint"], v)
    # Pump-Gold inspired features (external pre-alert trades), cut alert - 1 s; the alert - 2 s rebuild
    # feeds both variant blocks (there is no - 5 s rebuild: fA5 holds the - 2 s values for them)
    for r in A.jl(os.path.join(A.DERIVED, "feat_pumpgold.jsonl.gz")):
        for k in PG_KEEP:
            put(k, "pg", r["mint"], r.get(k))
    for r in A.jl(os.path.join(A.DERIVED, "feat_pumpgold_cut2.jsonl.gz")):
        for k in PG_KEEP:
            for var in ("fA2", "fA5"):
                variants[var].setdefault(k, np.full(n, np.nan))[idx[r["mint"]]] = num(r.get(k))
    # ratios suggested by the external-repo audit, from columns already cut at the creation slot
    with np.errstate(divide="ignore", invalid="ignore"):
        for name, num_, den in (("x_tip_over_bundle", "b_core_tip_sol", "b_core_sol"),
                                ("x_prio_over_bundle", "b_core_prio_sol", "b_core_sol")):
            v = cols[num_] / cols[den]
            cols[name] = np.where(np.isfinite(v), v, np.nan)
            meta[name] = {"source": "x"}
        cols["x_tl_spread"] = cols["sc_tl_max"] - cols["sc_tl_min"]
        meta["x_tl_spread"] = {"source": "x"}
    # causality audit, defect: with no resolved prior the shrunk excess of signal_search is 0 or a
    # float residue of about 3e-17 of random sign. "No history" must be missing, not a value.
    n_cleaned = 0
    for k in list(cols):
        if meta[k]["source"] == "ss_history" and (k.startswith("tr_ex_") or k in ("tr_mfe_any", "tr_ye1_any")):
            z = np.abs(cols[k]) < 1e-9
            n_cleaned += int(z.sum())
            cols[k][z] = np.nan
    print("zero-history residues set to missing:", n_cleaned)

    names = sorted(cols)
    for k in names:
        meta[k]["family"] = family_of(k)
        meta[k]["user_family"] = USER_FAMILY[meta[k]["family"]]
        meta[k]["observable_at"] = obs_of(k, meta[k]["source"], pd_class)
        meta[k]["already_tested_by"] = pd_meta.get(k, {}).get("deja_teste_par", [])
    X = np.column_stack([cols[k] for k in names]).astype(np.float32)
    np.savez_compressed(os.path.join(A.DERIVED, "X.npz"), X=X,
                        t=np.array([b["t"] for b in base]),
                        **{var: np.column_stack([variants[var].get(k, cols[k]) for k in names]).astype(np.float32)
                           for var in variants})
    A.write_json(os.path.join(A.DERIVED, "X_cols.json"),
                 {"mints": [b["mint"] for b in base], "blocks": [b["block"] for b in base],
                  "clusters": [b["cluster"] for b in base], "names": names, "meta": meta,
                  "variant_columns": sorted(variants["fA2"])})
    from collections import Counter
    print("rows", n, "columns", len(names))
    print("by source", dict(Counter(meta[k]["source"] for k in names)))
    print("by family", dict(Counter(meta[k]["family"] for k in names)))


if __name__ == "__main__":
    main()
