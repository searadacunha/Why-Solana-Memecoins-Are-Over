#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One row per alert: forensic features known before the entry, and the labels.

Two entries, two cut-offs, fixed before any model was fitted:
  A (primary)   entry at the alert. Features use transactions with a block time
                at least 1 s before the alert time, and wallets that appeared by
                then. A bot reading the chain had all of it before deciding.
  V (variant)   entry 30 s after the alert. Features may use everything up to
                alert + 29 s, including the wallets that first appeared in those
                30 s. Labels are then measured from the price at +30 s.

Every feature is declared once in FEATURES with its family, definition,
availability and causal status; feature_dictionary.md is generated from it.
Causal status UNKNOWN or POST_ENTRY never reaches a model.

Inputs: the frozen snapshot of post_detection_edge (alerts, prices, labels,
operator clusters, context features) and the on-chain caches of col_10 / col_20.
Output: derived/forensic_rows.jsonl.gz (+ derived/forensic_rows_test.jsonl.gz
when --test is given), and feature_dictionary.md.
"""
from __future__ import annotations

import gzip
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "post_detection_edge", "code"))
import pde  # noqa: E402
import fparse  # noqa: E402

WIN = os.path.join(STUDY, "data", "onchain_cache", "win")
WAL = os.path.join(STUDY, "data", "onchain_cache", "wal")
GEN = os.path.join(STUDY, "data", "onchain_cache", "genesis")
CORE_MIN_SOL = 5.0                          # the detector's ticket threshold, as col_20_wallets.roles
DERIVED = os.path.join(STUDY, "derived")   # never pde.DERIVED: that is the previous study's folder
T_VAL = pde.utc("2026-09-15 00:00:00")      # TRAIN before, VALIDATION from here to the snapshot


def write_rows(name: str, rows: list[dict[str, Any]]) -> None:
    os.makedirs(DERIVED, exist_ok=True)
    with open(os.path.join(DERIVED, name), "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
            for r in rows:
                gz.write((json.dumps(r, sort_keys=True) + "\n").encode("utf8"))


def read_rows(name: str) -> list[dict[str, Any]]:
    with gzip.open(os.path.join(DERIVED, name), "rt", encoding="utf8") as f:
        return [json.loads(line) for line in f]

# --------------------------------------------------------------------------- #
# the dictionary
# --------------------------------------------------------------------------- #
FEATURES: list[dict[str, str]] = []


def F(name: str, family: str, definition: str, availability: str = "alert - 1 s (A) / alert + 29 s (V)",
      source: str = "on-chain window", status: str = "PRE_ENTRY") -> str:
    FEATURES.append({"name": name, "family": family, "definition": definition, "availability": availability,
                     "source": source, "causal_status": status})
    return name


BUNDLE, WALLETS, HISTORY, FUNDING, MICRO, PRICE, CONTEXT = (
    "bundle", "wallets", "history", "funding", "micro", "price", "context")

# on-chain bundle (creation slot)
for nm, d in [("b_core_n", "wallets buying 5 SOL or more on the curve in the creation slot (the creator's "
                           "own first buy included when it is 5 SOL or more, as the detector counts it)"),
              ("b_core_sol", "SOL they put into the curve, at the venue"),
              ("b_core_supply", "share of the 1e9 supply they bought"),
              ("b_ticket_mean", "mean SOL per core wallet"), ("b_ticket_median", "median SOL per core wallet"),
              ("b_ticket_std", "standard deviation of the core tickets"), ("b_ticket_cv", "CV of the core tickets"),
              ("b_ticket_min", "smallest core ticket"), ("b_ticket_max", "largest core ticket"),
              ("b_ticket_range", "largest minus smallest ticket, over the mean"),
              ("b_ticket_q25", "first quartile of the tickets"), ("b_ticket_q75", "third quartile of the tickets"),
              ("b_hhi", "Herfindahl index of the tickets"), ("b_gini", "Gini coefficient of the tickets"),
              ("b_entropy", "Shannon entropy of the ticket shares, normalised by log(n)"),
              ("b_top1", "largest ticket share"), ("b_top2", "two largest tickets' share"),
              ("b_top3", "three largest tickets' share"),
              ("b_top_half", "share bought by the top half of the core wallets"),
              ("b_round_share", "share of core tickets within 0.05 SOL of a whole number of SOL"),
              ("b_core_tx_n", "distinct transactions carrying the core buys"),
              ("b_tx_per_wallet", "core transactions per core wallet (below 1 = several wallets per transaction)"),
              ("b_multi_buy", "core wallets buying more than once in the slot"),
              ("b_core_signers", "distinct fee payers of the core transactions"),
              ("b_core_tip_sol", "Jito tips paid in the core transactions, SOL"),
              ("b_core_prio_sol", "priority fees paid in the core transactions, SOL"),
              ("b_other_slot0_buyers", "other wallets buying on the curve in the creation slot"),
              ("b_other_slot0_sol", "SOL of those other creation-slot curve buys"),
              ("b_creator_buy_sol", "SOL of the creator's own first buy"),
              ("b_slot0_tx", "successful transactions on the mint in the creation slot"),
              ("b_slot0_failed", "failed transactions on the mint in the creation slot"),
              ("b_migrated_slot0", "1 if the curve migrated inside the creation slot"),
              ("b_slot0_pool_buy_sol", "SOL bought on the new pool inside the creation slot (the operator buying "
                                       "its own pool shows here)")]:
    F(nm, BUNDLE, d, availability="creation slot")

# micro-structure before the cut-off
for nm, d in [("m_tx", "successful transactions on the mint, creation to cut-off"),
              ("m_failed", "failed transactions on the mint"), ("m_fail_ratio", "failed / all"),
              ("m_buys", "external buys (not core, not creator)"), ("m_sells", "external sells"),
              ("m_buyers", "distinct external buyers"), ("m_sellers", "distinct external sellers"),
              ("m_buy_sol", "SOL of external buys"), ("m_sell_sol", "SOL of external sells"),
              ("m_buy_sell_ratio", "buy SOL / (buy + sell SOL)"), ("m_buy_median", "median external buy, SOL"),
              ("m_buy_max", "largest external buy, SOL"), ("m_sell_max", "largest external sell, SOL"),
              ("m_top_buyer_share", "largest external buyer's share of buy SOL"),
              ("m_ata", "token accounts opened by wallets that had not traded yet"),
              ("m_buyburn", "buy-and-burn transactions (a boost service)"),
              ("m_router_share", "share of trades sent through a router (Jupiter, OKX, ...)"),
              ("m_tip_share", "share of trades carrying a Jito tip"),
              ("m_prio_median", "median priority fee of trades, SOL"),
              ("m_rate", "external buys per second since creation"),
              ("m_accel", "external buys in the second half of the interval over the first half"),
              ("m_first1_sol", "SOL of the first external buy"), ("m_first3_sol", "SOL of the first 3 external buys"),
              ("m_first5_sol", "SOL of the first 5 external buys"),
              ("m_first10_sol", "SOL of the first 10 external buys"),
              ("m_t_first_buy", "seconds from creation to the first external buy"),
              ("m_buys_5s", "external buys within 5 s of creation (if before the cut-off)"),
              ("m_buys_10s", "external buys within 10 s of creation (if before the cut-off)"),
              ("m_core_exits", "core sells or transfers out before the cut-off"),
              ("m_core_exit_share", "share of the core's tokens already sold or moved out"),
              ("m_core_sell_sol", "SOL the core received from sells before the cut-off"),
              ("m_creator_sells", "creator sells before the cut-off")]:
    F(nm, MICRO, d)

F("p_entry_over_operator", "premium", "P0 over the core's average price (entry premium)",
  source="detector journal")
for nm, d in [("p_log_p0", "log10 of P0, the detector's spot price at the alert"),
              ("p_log_mc_usd", "log10 market cap at P0, USD"),
              ("p_pool_sol", "SOL in the pool at the last read before the cut-off (liquidity)"),
              ("p_pool_price_ratio", "pool price at the cut-off over the first pool price"),
              ("p_price_max_ratio", "highest pool price before the cut-off over the price at the cut-off"),
              ("p_velocity", "log10 pool price change per second before the cut-off"),
              ("p_reserve_vs_p0", "pool reserve price at the cut-off over P0 (consistency)"),
              ("p_curve_left_sol", "SOL left to buy before migration, if still on the curve")]:
    F(nm, PRICE, d, source="on-chain window + detector journal")

for role, rd in (("core", "core wallets"), ("creator", "the creator"), ("early", "external wallets active before "
                                                                               "the cut-off (first 25)")):
    for nm, d in [("fresh", "share with 3 or fewer earlier transactions"),
                  ("log_prior_n", "median log10(1 + earlier transactions), capped at 1 000"),
                  ("capped", "share with 1 000 or more earlier transactions (bots, hubs)"),
                  ("log_age_h", "median log10(1 + hours since the oldest earlier transaction seen)"),
                  ("active_days", "median distinct UTC days with activity in the earlier transactions seen"),
                  ("err_share", "median share of failed earlier transactions")]:
        F("w_%s_%s" % (role, nm), WALLETS, "%s: %s" % (rd, d), availability="each wallet's first transaction "
          "in the window", source="getSignaturesForAddress before that transaction")
for role, rd in (("core", "core wallets"), ("creator", "the creator"), ("early", "early external wallets")):
    for nm, d in [("tx_1h", "median earlier transactions in the hour before the alert"),
                  ("tx_24h", "median earlier transactions in the 24 h before the alert")]:
        F("h_%s_%s" % (role, nm), HISTORY, "%s: %s" % (rd, d), availability="before each wallet's first window "
          "transaction", source="getSignaturesForAddress")
for nm, d in [("h_core_last_in_age_h", "hours since the last SOL received by a core wallet (median, 5 latest txs)"),
              ("h_core_prior_buys", "pump-token buys in the core wallets' 5 latest earlier transactions (total)"),
              ("h_core_prior_sells", "pump-token sells in the same"),
              ("h_creator_prior_creates", "token creations in the creator's 20 latest earlier transactions"),
              ("h_creator_prior_buys", "pump-token buys in the same"),
              ("h_creator_prior_sells", "pump-token sells in the same"),
              ("h_creator_prev_alerts", "earlier alerts of the detector with the same creator"),
              ("h_sniper_reuse_max", "most earlier alerts in which one of the core wallets was a sniper"),
              ("h_config_prev", "earlier alerts with the same ticket configuration")]:
    F(nm, HISTORY, d, source="getTransaction of earlier transactions / detector journal")

for nm, d in [("g_core_funders", "distinct genesis funders of the core wallets"),
              ("g_core_common_ratio", "largest group of core wallets sharing a genesis funder, over the core"),
              ("g_creator_shares_core_funder", "1 if the creator's genesis funder funded a core wallet"),
              ("g_creator_funded_core", "1 if the creator directly funded a core wallet, or the reverse"),
              ("g_core_fund_cv", "CV of the SOL the core wallets received at genesis"),
              ("g_core_fund_sol", "median SOL a core wallet received at genesis"),
              ("g_core_fund_age_h", "median hours between a core wallet's genesis funding and the alert"),
              ("g_core_min_dist", "median, over core wallets, of the smallest funding-graph distance to another "
                                  "core wallet (3 hops up; 9 = not linked)"),
              ("g_core_creator_dist", "smallest funding-graph distance between the creator and a core wallet"),
              ("g_early_linked", "share of early wallets within distance 4 of a core wallet or the creator"),
              ("g_density", "share of linked pairs (distance <= 4) among core wallets and creator"),
              ("g_funder_prior_uses", "most earlier alerts whose core or creator had the same genesis funder as "
                                      "a core wallet here"),
              ("g_early_funders_shared", "early wallets sharing a genesis funder with each other, share")]:
    F(nm, FUNDING, d, availability="genesis funding of each wallet (before its first window transaction)",
      source="genesis transactions, walked 3 hops up")

for nm, d in [("c_hour", "hour of the alert, UTC"), ("c_dow", "weekday"),
              ("c_alerts_60m", "detector alerts in the previous hour"),
              ("c_candidates_60m", "detector candidates in the previous hour"),
              ]:
    F(nm, CONTEXT, d, source="detector journal")
F("c_actor_grouped", "actor", "1 if the core bought several wallets per transaction (grouped actor)",
  source="detector journal (creation block)")

for nm, d in [("f_n_funders", "distinct genesis funders of the core wallets"),
              ("f_funder_hhi", "Herfindahl index of core wallets per genesis funder"),
              ("f_funder_top1", "share of core wallets funded by the most frequent funder"),
              ("f_funder_top2", "share funded by the two most frequent funders"),
              ("f_funder_top3", "share funded by the three most frequent funders"),
              ("f_funded_sol_gini", "Gini of the SOL received at genesis, summed by funder"),
              ("f_bundle_share_top_funder", "share of the bundle SOL bought by wallets of the funder carrying the "
                                            "most bundle SOL"),
              ("f_same_funder_multi", "1 if one funder funded two or more core wallets"),
              ("f_hub_funded_share", "share of core wallets whose funder had more than 3 000 transactions before "
                                     "its earliest funding in the corpus (hub, measured causally)"),
              ("f_funder_log_hist", "median log10(1 + transactions of the core funders before their earliest "
                                    "funding in the corpus)"),
              ("f_fund_to_buy_h", "median hours from a core wallet's genesis funding to the creation slot"),
              ("f_fund_to_alert_h", "median hours from a core wallet's genesis funding to the alert"),
              ("f_indep_actors_strict", "core wallets grouped when they share a genesis funder or one funded the "
                                        "other: number of groups"),
              ("f_indep_actors_loose", "same, linking wallets within funding distance 4 (3 hops up, causal)"),
              ("f_indep_share", "independent actors (strict) over core wallets")]:
    F(nm, FUNDING, d, availability="genesis funding of each wallet; funders walked before their earliest funding",
      source="genesis transactions (col_20), genesis_hop cache")
for nm, d in [("e_prior_launches_median", "median, over early wallets, of earlier detector launches they traded "
                                          "in (block time before the cut-off)"),
              ("e_prior_launches_share", "share of early wallets that traded in at least one earlier detector "
                                         "launch"),
              ("e_prior_launches_max", "largest such count among early wallets")]:
    F(nm, HISTORY, d, availability="windows of earlier alerts, records before the cut-off",
      source="on-chain windows of earlier alerts")
F("p_time_since_creation_s", PRICE, "seconds from the creation block to the cut-off", source="on-chain window")
F("x_hub_flag", FUNDING, "funder walked as a hub (more than 3 000 transactions TODAY)", source="collection time",
  status="UNKNOWN")
F("x_mult_after", PRICE, "any price read after the entry", source="detector series", status="POST_ENTRY")

TRUNCATE = True
FAMILY = {f["name"]: f["family"] for f in FEATURES if f["causal_status"] == "PRE_ENTRY"}


# --------------------------------------------------------------------------- #
def med(xs: list[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def gini(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    tot = sum(s)
    if not n or not tot:
        return 0.0
    return sum((2 * (i + 1) - n - 1) * x for i, x in enumerate(s)) / (n * tot)


GEN_HOP = os.path.join(STUDY, "data", "onchain_cache", "genesis_hop")


def _hop(address: str, first: bool) -> Optional[dict[str, Any]]:
    p = os.path.join(GEN if first else GEN_HOP, address + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def lineage(address: str, depth: int = 3) -> list[str]:
    """Funders upward: hop 1 from the wallet's own genesis (history before its
    first window transaction), hops 2-3 from genesis_hop (each funder walked
    back from its earliest funding in the corpus). Stops at a funder that was
    already a hub then."""
    out, cur, first = [], address, True
    for _ in range(depth):
        g = _hop(cur, first)
        if not g or g.get("hub_before_cursor"):
            break
        fu = (g.get("funding") or {}).get("funder")
        if not fu:
            break
        out.append(fu)
        cur, first = fu, False
    return out


def distance(w1: str, w2: str, L: dict[str, list[str]]) -> int:
    """Edges on the funding tree between two wallets, through a common ancestor
    within 3 hops each; 1 if one funded the other; 9 if not linked."""
    a, b = [w1] + L.get(w1, []), [w2] + L.get(w2, [])
    best = 9
    for i, x in enumerate(a):
        if x in b:
            best = min(best, i + b.index(x))
    return best


def wallet_stats(entry: dict[str, Any], t_alert: float) -> dict[str, Any]:
    pr = entry["prior"]
    bts = [b for b in pr["bts"] if b]
    n = pr["n"]
    oldest = min(bts) if bts else None
    return {"n": n, "fresh": 1.0 if n <= 3 else 0.0, "capped": 1.0 if n >= 1000 else 0.0,
            "log_prior_n": math.log10(1 + n),
            "log_age_h": math.log10(1 + (t_alert - oldest) / 3600) if oldest else 0.0,
            "active_days": float(len({b // 86400 for b in bts})),
            "err_share": pr["n_err"] / n if n else 0.0,
            "tx_1h": float(sum(1 for b in bts if b >= t_alert - 3600)),
            "tx_24h": float(sum(1 for b in bts if b >= t_alert - 86400))}


# --------------------------------------------------------------------------- #
def features_for(a: dict[str, Any], w: dict[str, Any], wal: dict[str, Any], ctx: dict[str, Any],
                 cut: float, roles_ok: tuple[str, ...], funder_uses: dict[str, int],
                 partic: Optional[dict[str, list[tuple[float, str]]]] = None) -> dict[str, Any]:
    # Structural cut-off: the raw window is truncated BEFORE anything is parsed,
    # so no record, no migration, no pool read after the cut-off exists for the
    # features below (audit of 2026-09-29: p_curve_left_sol had used a migration
    # that happened after the alert). TRUNCATE is only switched off by the
    # leakage test, to show what an untruncated window would have leaked.
    if TRUNCATE:
        w = {**w, "sigs": [s for s in w["sigs"] if (s.get("bt") or 0) <= cut]}
    recs, facts = fparse.parse_window(w)
    t_alert = a["t"]
    slot0 = recs[0]["slot"]
    bt_of = {s["sig"]: s.get("bt") for s in w["sigs"]}
    create = [r for r in recs if r.get("kind") == "create"]
    t_create = create[0]["bt"] if create and create[0].get("bt") else t_alert - (a.get("age_alerte_s") or 12)
    pre = [r for r in recs if (r.get("bt") or 0) <= cut]
    wallets = {k: v for k, v in wal["wallets"].items() if v["role"] in roles_ok
               and (not TRUNCATE or (bt_of.get(v["cursor"]) or float("inf")) <= cut)}
    core = [k for k, v in wallets.items() if v["role"] == "core"]
    creator = next((k for k, v in wallets.items() if v["role"] == "creator"), None)
    early = [k for k, v in wallets.items() if v["role"] in ("early", "late")]
    f: dict[str, Any] = {}

    # bundle
    tick: dict[str, float] = defaultdict(float)
    core_txs, signers, tips, prios, buys_per = set(), set(), 0.0, 0.0, Counter()
    other_slot0, pool_slot0, creator_buy = defaultdict(float), 0.0, 0.0
    for r in recs:
        if r["slot"] != slot0 or r.get("err"):
            continue
        if r.get("kind") == "buy" and r.get("venue") == "curve" and r.get("leg_sol"):
            touched = False
            for o, sol in r["leg_sol"].items():
                # the SOL each wallet itself sent to the curve (fparse.leg_sol)
                if o in core:
                    tick[o] += sol
                    buys_per[o] += 1
                    touched = True
                else:
                    other_slot0[o] += sol
            if touched:
                core_txs.add(r["sig"])
                signers.add(r["signer"])
                tips += r.get("tip", 0) / 1e9
                prios += r.get("prio", 0) / 1e9
        elif r.get("kind") == "buy" and r.get("venue") == "pool":
            pool_slot0 += abs(r.get("v_sol") or 0)
        if r.get("kind") == "create":
            creator_buy += (r.get("leg_sol") or {}).get(r["signer"], 0.0)
            if creator_buy >= CORE_MIN_SOL:
                # the detector counts the creator's own first buy of 5 SOL or more as a
                # bundle ticket (11 alerts of the first 1 074 windows); the creator keeps
                # its own role for the wallet features
                tick[r["signer"]] += creator_buy
                buys_per[r["signer"]] += 1
                core_txs.add(r["sig"])
                signers.add(r["signer"])
                tips += r.get("tip", 0) / 1e9
                prios += r.get("prio", 0) / 1e9
    tk = sorted(tick.values(), reverse=True)
    s = sum(tk)
    n = len(tk)
    f["b_core_n"] = float(n)
    f["b_core_sol"] = s
    f["b_core_supply"] = None
    if n:
        sh = [x / s for x in tk]
        f.update({"b_ticket_mean": s / n, "b_ticket_median": statistics.median(tk),
                  "b_ticket_std": statistics.pstdev(tk), "b_ticket_cv": statistics.pstdev(tk) / (s / n),
                  "b_ticket_min": tk[-1], "b_ticket_max": tk[0], "b_ticket_range": (tk[0] - tk[-1]) / (s / n),
                  "b_ticket_q25": pde.quantile(tk, 0.25), "b_ticket_q75": pde.quantile(tk, 0.75),
                  "b_hhi": sum(x * x for x in sh), "b_gini": gini(tk),
                  "b_entropy": (-sum(x * math.log(x) for x in sh if x > 0) / math.log(n)) if n > 1 else 0.0,
                  "b_top1": sh[0], "b_top2": sum(sh[:2]), "b_top3": sum(sh[:3]),
                  "b_top_half": sum(sh[: max(1, n // 2)]),
                  "b_round_share": sum(1 for x in tk if abs(x - round(x)) < 0.05) / n,
                  "b_core_tx_n": float(len(core_txs)), "b_tx_per_wallet": len(core_txs) / n,
                  "b_multi_buy": float(sum(1 for v in buys_per.values() if v > 1)),
                  "b_core_signers": float(len(signers)), "b_core_tip_sol": tips, "b_core_prio_sol": prios})
    toks = 0.0
    for r in recs:
        if r["slot"] == slot0 and r.get("kind") == "buy" and r.get("venue") == "curve":
            toks += sum(v for o, v in (r.get("legs") or {}).items() if o in core and v > 0)
        elif r["slot"] == slot0 and r.get("kind") == "create" and creator_buy >= CORE_MIN_SOL:
            toks += max(0.0, (r.get("legs") or {}).get(r["signer"], 0.0))
    f["b_core_supply"] = toks / 1e9
    f["b_other_slot0_buyers"] = float(len(other_slot0))
    f["b_other_slot0_sol"] = sum(other_slot0.values())
    f["b_creator_buy_sol"] = creator_buy
    f["b_slot0_tx"] = float(sum(1 for r in recs if r["slot"] == slot0 and not r.get("err")))
    f["b_slot0_failed"] = float(sum(1 for r in recs if r["slot"] == slot0 and r.get("err")))
    f["b_migrated_slot0"] = 1.0 if facts["migration_slot"] == slot0 else 0.0
    f["b_slot0_pool_buy_sol"] = pool_slot0

    # micro-structure before the cut-off
    ext = set(core) | ({creator} if creator else set())
    trades = [r for r in pre if r.get("kind") in ("buy", "sell") and not r.get("err")]
    ebuys = [r for r in trades if r["kind"] == "buy" and r.get("trader") not in ext and r["slot"] != slot0]
    esells = [r for r in trades if r["kind"] == "sell" and r.get("trader") not in ext]
    bsol = [abs(r.get("v_sol") or 0) for r in ebuys]
    ssol = [abs(r.get("v_sol") or 0) for r in esells]
    dur = max(1.0, cut - t_create)
    f.update({"m_tx": float(sum(1 for r in pre if not r.get("err"))),
              "m_failed": float(sum(1 for r in pre if r.get("err"))),
              "m_buys": float(len(ebuys)), "m_sells": float(len(esells)),
              "m_buyers": float(len({r.get("trader") for r in ebuys})),
              "m_sellers": float(len({r.get("trader") for r in esells})),
              "m_buy_sol": sum(bsol), "m_sell_sol": sum(ssol),
              "m_buy_median": med(bsol), "m_buy_max": max(bsol) if bsol else 0.0,
              "m_sell_max": max(ssol) if ssol else 0.0,
              "m_ata": float(sum(1 for r in pre if r.get("kind") == "ata")),
              "m_buyburn": float(sum(1 for r in pre if r.get("kind") == "buyburn")),
              "m_rate": len(ebuys) / dur})
    f["m_fail_ratio"] = f["m_failed"] / max(1.0, f["m_failed"] + f["m_tx"])
    f["m_buy_sell_ratio"] = sum(bsol) / (sum(bsol) + sum(ssol)) if (bsol or ssol) and sum(bsol) + sum(ssol) else None
    by = defaultdict(float)
    for r, x in zip(ebuys, bsol):
        by[r.get("trader")] += x
    f["m_top_buyer_share"] = max(by.values()) / sum(by.values()) if by and sum(by.values()) else None
    f["m_router_share"] = sum(1 for r in trades if r.get("router")) / len(trades) if trades else None
    f["m_tip_share"] = sum(1 for r in trades if r.get("tip")) / len(trades) if trades else None
    f["m_prio_median"] = med([r.get("prio", 0) / 1e9 for r in trades])
    half = t_create + dur / 2
    b1 = sum(1 for r in ebuys if (r.get("bt") or 0) <= half)
    f["m_accel"] = (len(ebuys) - b1) / max(1, b1)
    for k in (1, 3, 5, 10):
        f["m_first%d_sol" % k] = sum(bsol[:k]) if len(bsol) >= k else None
    f["m_t_first_buy"] = (ebuys[0]["bt"] - t_create) if ebuys and ebuys[0].get("bt") else None
    for sec in (5, 10):
        f["m_buys_%ds" % sec] = (float(sum(1 for r in ebuys if (r.get("bt") or 0) <= t_create + sec))
                                 if t_create + sec <= cut else None)
    core_tok = sum(v for r in recs if r["slot"] == slot0 and r.get("kind") == "buy"
                   for o, v in (r.get("legs") or {}).items() if o in core and v > 0)
    out_tok, exits, core_sell_sol = 0.0, 0, 0.0
    for r in pre:
        legs = r.get("legs") or {}
        neg = {o: -v for o, v in legs.items() if o in core and v < 0}
        if neg:
            exits += 1
            out_tok += sum(neg.values())
            if r.get("kind") == "sell":
                core_sell_sol += abs(r.get("v_sol") or 0)
    f["m_core_exits"] = float(exits)
    f["m_core_exit_share"] = out_tok / core_tok if core_tok else None
    f["m_core_sell_sol"] = core_sell_sol
    f["m_creator_sells"] = float(sum(1 for r in trades if r["kind"] == "sell" and creator
                                     and (r.get("legs") or {}).get(creator, 0) < 0))

    # price before the cut-off
    pool_reads = [r for r in pre if r.get("pool_tok")]
    f["p_log_p0"] = math.log10(a["p0"])
    f["p_entry_over_operator"] = ctx.get("entry_over_operator")
    f["p_log_mc_usd"] = ctx.get("log10_mc_usd")
    if pool_reads:
        pr0 = pool_reads[0]["pool_sol"] / pool_reads[0]["pool_tok"]
        prl = pool_reads[-1]["pool_sol"] / pool_reads[-1]["pool_tok"]
        prices = [r["pool_sol"] / r["pool_tok"] for r in pool_reads]
        f["p_pool_sol"] = pool_reads[-1]["pool_sol"]
        f["p_pool_price_ratio"] = prl / pr0 if pr0 else None
        f["p_price_max_ratio"] = max(prices) / prl if prl else None
        span = (pool_reads[-1]["bt"] or 0) - (pool_reads[0]["bt"] or 0)
        f["p_velocity"] = math.log10(prl / pr0) / span if span > 0 and pr0 and prl else 0.0
        f["p_reserve_vs_p0"] = prl / a["p0"] if a.get("p0") else None
    else:
        f.update({"p_pool_sol": None, "p_pool_price_ratio": None, "p_price_max_ratio": None,
                  "p_velocity": None, "p_reserve_vs_p0": None})
    curve_reads = [r for r in pre if r.get("curve_lamports") is not None]
    f["p_curve_left_sol"] = (max(0.0, 85.0 - curve_reads[-1]["curve_lamports"])
                             if curve_reads and facts["migration_slot"] is None else 0.0)

    # wallets and history
    st = {k: wallet_stats(v, t_alert) for k, v in wallets.items()}
    for role, members in (("core", core), ("creator", [creator] if creator else []), ("early", early)):
        for nm in ("fresh", "log_prior_n", "capped", "log_age_h", "active_days", "err_share"):
            f["w_%s_%s" % (role, nm)] = med([st[m][nm] for m in members if m in st])
        for nm in ("tx_1h", "tx_24h"):
            f["h_%s_%s" % (role, nm)] = med([st[m][nm] for m in members if m in st])
    lasts, pb, ps = [], 0, 0
    for m in core:
        rc = wallets[m].get("recent") or []
        ins = [x["bt"] for x in rc if x.get("bt") and (x.get("d") or {}).get(m, 0) > 0]
        if ins:
            lasts.append((t_alert - max(ins)) / 3600)
        pb += sum(x.get("buys", 0) for x in rc)
        ps += sum(x.get("sells", 0) for x in rc)
    f["h_core_last_in_age_h"] = med(lasts)
    f["h_core_prior_buys"] = float(pb) if core else None
    f["h_core_prior_sells"] = float(ps) if core else None
    rc = (wallets.get(creator) or {}).get("recent") or [] if creator else []
    f["h_creator_prior_creates"] = float(sum(x.get("creates", 0) for x in rc)) if creator else None
    f["h_creator_prior_buys"] = float(sum(x.get("buys", 0) for x in rc)) if creator else None
    f["h_creator_prior_sells"] = float(sum(x.get("sells", 0) for x in rc)) if creator else None
    f["h_creator_prev_alerts"] = ctx.get("creator_prev")
    f["h_sniper_reuse_max"] = ctx.get("sniper_reuse_max")
    f["h_config_prev"] = ctx.get("config_prev")

    # funding graph
    L = {k: lineage(k) for k in wallets}
    gf = {k: (L[k][0] if L[k] else None) for k in wallets}
    cf = [gf[m] for m in core if gf.get(m)]
    f["g_core_funders"] = float(len(set(cf))) if core else None
    f["g_core_common_ratio"] = (max(Counter(cf).values()) / len(core)) if cf else None
    f["g_creator_shares_core_funder"] = (1.0 if creator and gf.get(creator) and gf[creator] in cf else 0.0) \
        if creator else None
    f["g_creator_funded_core"] = (1.0 if creator and any(gf.get(m) == creator or gf.get(creator) == m
                                                          for m in core) else 0.0) if creator else None
    amts = [((wallets[m].get("genesis") or {}).get("funding") or {}).get("received") for m in core]
    amts = [x for x in amts if x is not None and x > 0]
    f["g_core_fund_cv"] = statistics.pstdev(amts) / statistics.mean(amts) if len(amts) > 1 else None
    f["g_core_fund_sol"] = med(amts)
    ages = [(t_alert - ((wallets[m].get("genesis") or {}).get("funding") or {}).get("bt")) / 3600
            for m in core if ((wallets[m].get("genesis") or {}).get("funding") or {}).get("bt")]
    f["g_core_fund_age_h"] = med(ages)
    f["g_core_min_dist"] = med([float(min(distance(m, o, L) for o in core if o != m)) for m in core]) \
        if len(core) > 1 else None
    f["g_core_creator_dist"] = float(min(distance(creator, m, L) for m in core)) if creator and core else None
    anchors = core + ([creator] if creator else [])
    f["g_early_linked"] = (sum(1 for e in early if any(distance(e, x, L) <= 4 for x in anchors)) / len(early)
                           if early and anchors else None)
    pairs = [(x, y) for i, x in enumerate(anchors) for y in anchors[i + 1:]]
    f["g_density"] = sum(1 for x, y in pairs if distance(x, y, L) <= 4) / len(pairs) if pairs else None
    f["g_funder_prior_uses"] = float(max((funder_uses.get(x, 0) for x in set(cf)), default=0)) if core else None
    ef = [gf[e] for e in early if gf.get(e)]
    f["g_early_funders_shared"] = (sum(v for v in Counter(ef).values() if v > 1) / len(early)) if early else None

    # funding concentration, topology and timing of the core
    fund = {m: ((wallets[m].get("genesis") or {}).get("funding") or {}) for m in core}
    fu_of = {m: fund[m]["funder"] for m in core if fund[m].get("funder")}
    if fu_of:
        cnt = Counter(fu_of.values())
        shares = sorted((c / len(fu_of) for c in cnt.values()), reverse=True)
        f["f_n_funders"] = float(len(cnt))
        f["f_funder_hhi"] = sum(x * x for x in shares)
        f["f_funder_top1"], f["f_funder_top2"], f["f_funder_top3"] = shares[0], sum(shares[:2]), sum(shares[:3])
        by_sol: dict[str, float] = defaultdict(float)
        by_tick: dict[str, float] = defaultdict(float)
        for m, fu in fu_of.items():
            by_sol[fu] += fund[m].get("received") or 0.0
            by_tick[fu] += tick.get(m, 0.0)
        f["f_funded_sol_gini"] = gini(list(by_sol.values())) if len(by_sol) > 1 else 0.0
        f["f_bundle_share_top_funder"] = max(by_tick.values()) / s if s else None
        f["f_same_funder_multi"] = 1.0 if max(cnt.values()) >= 2 else 0.0
        hub, hist = [], []
        for fu in set(fu_of.values()):
            g = _hop(fu, False)
            if g is not None and ("hub_before_cursor" in g):
                hub.append(1.0 if g["hub_before_cursor"] else 0.0)
                n_hist = g.get("n_seen") if g["hub_before_cursor"] else g.get("n_before_cursor", 0)
                hist.append(math.log10(1 + (n_hist or 0)))
        hubs = {fu for fu in set(fu_of.values()) if (_hop(fu, False) or {}).get("hub_before_cursor")}
        f["f_hub_funded_share"] = (sum(1.0 for fu in fu_of.values() if fu in hubs) / len(fu_of)) if hub else None
        f["f_funder_log_hist"] = med(hist)
        bts = [fund[m].get("bt") for m in fu_of if fund[m].get("bt")]
        f["f_fund_to_buy_h"] = med([(t_create - b) / 3600 for b in bts])
        f["f_fund_to_alert_h"] = med([(t_alert - b) / 3600 for b in bts])
    parent = {m: m for m in core}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i, x in enumerate(core):
        for y in core[i + 1:]:
            if (fu_of.get(x) and fu_of.get(x) == fu_of.get(y)) or fu_of.get(x) == y or fu_of.get(y) == x:
                parent[find(x)] = find(y)
    strict = len({find(m) for m in core})
    for m in core:
        parent[m] = m
    for i, x in enumerate(core):
        for y in core[i + 1:]:
            if distance(x, y, L) <= 4:
                parent[find(x)] = find(y)
    f["f_indep_actors_strict"] = float(strict) if core else None
    f["f_indep_actors_loose"] = float(len({find(m) for m in core})) if core else None
    f["f_indep_share"] = strict / len(core) if core else None

    # early wallets' participation in earlier detector launches (causal)
    if partic is not None and early:
        counts = []
        for e in early:
            prev = {m for bt, m in partic.get(e, []) if bt < cut and m != a["mint"]}
            counts.append(len(prev))
        f["e_prior_launches_median"] = med([float(c) for c in counts])
        f["e_prior_launches_share"] = sum(1 for c in counts if c > 0) / len(counts)
        f["e_prior_launches_max"] = float(max(counts))
    f["p_time_since_creation_s"] = cut - t_create

    # context
    f["c_hour"] = float(ctx.get("hour_utc", 0))
    f["c_dow"] = float(ctx.get("dow", 0))
    f["c_alerts_60m"] = ctx.get("n_alerts_prev_60m")
    f["c_candidates_60m"] = ctx.get("n_candidates_prev_60m")
    f["c_actor_grouped"] = 1.0 if ctx.get("actor") == "grouped" else (0.0 if ctx.get("actor") else None)
    return {k: (None if (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else v)
            for k, v in f.items() if k in FAMILY}


LABEL_GRID = {  # name: (threshold, horizon s); fixed before any rate was computed
    "2x_5m": (2.0, 300), "2x_10m": (2.0, 600), "2x_15m": (2.0, 900), "2x_20m": (2.0, 1200), "2x_1h": (2.0, 3600),
    "1.5x_15m": (1.5, 900), "1.8x_15m": (1.8, 900), "2.2x_15m": (2.2, 900), "3x_15m": (3.0, 900),
}


def labels(pts: Optional[list[tuple[float, float]]], fine: bool) -> dict[str, Any]:
    """Labels from the price series, rules of post_detection_edge/code/pde.py.
    A_ = entry at P0 (the alert); V_ = entry at the first read at or after +30 s.
    'conf' = two consecutive reads at or above the threshold inside the window
    (the primary definition, A_conf_2x_15m); 'single' = one read. None = the
    window is not observed (censored or missing), never a miss."""
    out: dict[str, Any] = {}
    if not pts:
        return out

    def one(t_in: float, m_in: float, k: float, h: float) -> tuple[Optional[int], Optional[int], Optional[float]]:
        mx, ok = pde.window(pts, t_in, h, fine)
        if not ok:
            return None, None, None
        ins = [m / m_in for dt, m in pts if t_in < dt <= t_in + h]
        single = int(mx is not None and mx / m_in >= k)
        conf = int(any(x >= k and y >= k for x, y in zip(ins, ins[1:])))
        return single, conf, (mx / m_in if mx is not None else None)
    for name, (k, h) in LABEL_GRID.items():
        if h < pde.FINE_WINDOW and not fine:
            continue
        sgl, conf, mx = one(0.0, 1.0, k, h)
        out["A_single_" + name], out["A_conf_" + name] = sgl, conf
    for h in (900, 3600):
        _, _, mx = one(0.0, 1.0, 2.0, h)
        out["A_mfe_%ds" % h] = mx
    # time to the first confirmed 2x within 1 h (descriptive only)
    first = None
    for (d1, m1), (d2, m2) in zip(pts, pts[1:]):
        if 0 < d1 and d2 <= 3600 and m1 >= 2 and m2 >= 2:
            first = d2
            break
    out["A_t_conf_2x_s"] = first
    if fine:
        ent = pde.entry_point(pts, 30)
        if ent:
            for name in ("2x_15m", "2x_1h"):
                k, h = LABEL_GRID[name]
                sgl, conf, _ = one(ent[0], ent[1], k, h)
                out["V_single_" + name], out["V_conf_" + name] = sgl, conf
            out["V_entry_mult"] = ent[1]
    return out


def context(journal: list[dict[str, Any]], sol_usd: dict[int, float]) -> dict[str, dict[str, Any]]:
    """Context features of every alert, built strictly from journal lines older
    than the alert, with the definitions of post_detection_edge/code/build_10_dataset.py."""
    import bisect
    alerts = sorted((r for r in journal if r["genre"] == "alerte_lancement"), key=lambda r: r["t"])
    flux = sorted(r["t"] for r in journal if r["genre"] in ("alerte_lancement", "rejete"))
    retro = {r["mint"]: r.get("paquet_max") for r in journal if r["genre"] == "outil"}
    seen_c: Counter[str] = Counter()
    seen_w: Counter[str] = Counter()
    seen_k: Counter[str] = Counter()
    times: list[float] = []
    out = {}
    for a in alerts:
        t = a["t"]
        tk = a.get("tickets") or a["bloc"].get("tickets")
        ck = "+".join("%.2f" % x for x in sorted(tk, reverse=True)) if tk else None
        pm = a["bloc"].get("paquet_max") or retro.get(a["mint"])
        tm = __import__("time").gmtime(t)
        h = int(t) // 3600 * 3600 - 3600      # previous hour's close: known at the alert
        out[a["mint"]] = {
            "n_alerts_prev_60m": len(times) - bisect.bisect_left(times, t - 3600),
            "n_candidates_prev_60m": bisect.bisect_left(flux, t) - bisect.bisect_left(flux, t - 3600),
            "creator_prev": seen_c[a["createur"]] if a.get("createur") else 0,
            "sniper_reuse_max": max((seen_w[w] for w in a.get("snipers") or []), default=0),
            "config_prev": seen_k[ck] if ck else None,
            "actor": None if not pm else ("grouped" if pm >= 2 else "single"),
            "entry_over_operator": a.get("entree_sur_operateur"),
            "log10_mc_usd": math.log10(a["p0"] * 1e9 * sol_usd[h]) if h in sol_usd else None,
            "hour_utc": tm.tm_hour, "dow": tm.tm_wday}
        times.append(t)
        if a.get("createur"):
            seen_c[a["createur"]] += 1
        for w in a.get("snipers") or []:
            seen_w[w] += 1
        if ck:
            seen_k[ck] += 1
    return out


CUTS = {"A": -1.0, "A2": -2.0, "A5": -5.0, "V": 29.0}   # seconds relative to the alert, fixed in advance


def participation_index(alerts: list[dict[str, Any]]) -> dict[str, list[tuple[float, str]]]:
    """wallet -> [(block time, mint)] of every window record where it traded or
    signed. A wallet's count of earlier launches is then read strictly before
    each cut-off, so it never contains the future."""
    idx: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for a in alerts:
        wp = os.path.join(WIN, a["mint"] + ".json.gz")
        if not os.path.exists(wp):
            continue
        recs, _ = fparse.parse_window(json.load(gzip.open(wp, "rt")))
        for r in recs:
            if r.get("err") or not r.get("bt"):
                continue
            for x in {r.get("signer"), *((r.get("legs") or {}).keys())}:
                if x:
                    idx[x].append((r["bt"], a["mint"]))
    return idx


def build(alerts: list[dict[str, Any]], ctx_by_mint: dict[str, Any], clusters: dict[str, str], out_name: str,
          series: dict[str, list[tuple[float, float]]], split_name: Optional[str] = None) -> None:
    uses: dict[str, int] = defaultdict(int)
    partic = participation_index(alerts)
    out, skipped = [], Counter()
    for a in sorted(alerts, key=lambda r: r["t"]):
        wp, lp = os.path.join(WIN, a["mint"] + ".json.gz"), os.path.join(WAL, a["mint"] + ".json.gz")
        if not (os.path.exists(wp) and os.path.exists(lp)):
            skipped["no on-chain data"] += 1
            continue
        w = json.load(gzip.open(wp, "rt"))
        wal = json.load(gzip.open(lp, "rt"))
        ctx = ctx_by_mint.get(a["mint"], {})
        row: dict[str, Any] = {
            "alert_id": "%s@%d" % (a["mint"], int(a["t"])), "mint": a["mint"], "creation_slot": a["slot"],
            "detection_timestamp": a["t"], "utc": a["utc"], "t": a["t"], "p0": a["p0"],
            "actor_type": ctx.get("actor"), "split": split_name or ("train" if a["t"] < T_VAL else "val"),
            "cluster": clusters.get(a["mint"], a["mint"]), "fine": a["t"] >= pde.T_FINE}
        for key, off in CUTS.items():
            roles = ("core", "creator", "early", "late") if key == "V" else ("core", "creator", "early")
            row["f" + key] = features_for(a, w, wal, ctx, a["t"] + off, roles, uses, partic)
        # last slot read before the primary cut-off: the detector records no alert slot
        row["last_slot_before_cutoff"] = max(s_["slot"] for s_ in w["sigs"] if (s_.get("bt") or 0) <= a["t"] - 1)
        row["y"] = labels(series.get(a["mint"]), a["t"] >= pde.T_FINE)
        out.append(row)
        # causal funder reuse: updated only after this alert's features were built
        for k, v in wal["wallets"].items():
            if v["role"] in ("core", "creator"):
                for fu in lineage(k, 1):
                    uses[fu] += 1
    write_rows(out_name, out)
    print("%s: %d rows, skipped %s" % (out_name, len(out), dict(skipped)))


def dictionary() -> None:
    lines = ["# Feature dictionary", "",
             "Generated by `code/feat_30_build.py` from its FEATURES registry. Only PRE_ENTRY features reach a "
             "model. Cut-offs, relative to the alert time: A = -1 s (primary, entry at the alert), A2 = -2 s and "
             "A5 = -5 s (robustness), V = +29 s (entry at +30 s). The raw window is truncated at the cut-off before "
             "parsing.",
             "", "| feature_name | family | definition | timestamp_availability | source | available_before_entry "
             "| causal_status |", "|---|---|---|---|---|---|---|"]
    for f in FEATURES:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            f["name"], f["family"], f["definition"], f["availability"], f["source"],
            "true" if f["causal_status"] == "PRE_ENTRY" else "false", f["causal_status"]))
    lines += ["", "Counts: %s. PRE_ENTRY features: %d." % (dict(Counter(f["family"] for f in FEATURES
                                                                        if f["causal_status"] == "PRE_ENTRY")),
                                                          len(FAMILY))]
    with open(os.path.join(STUDY, "feature_dictionary.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")


def sol_usd_table(path: str) -> dict[int, float]:
    return {int(k): v for k, v in json.load(open(path))["close_by_hour"].items()}


def clusters_of(journal: list[dict[str, Any]]) -> dict[str, str]:
    """Operator clusters with the rules of post_detection_edge/code/build_10_dataset.py
    (shared sniper wallet, creator or ticket configuration), over every alert
    given. Grouping for inference only, never a feature."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a in (r for r in journal if r["genre"] == "alerte_lancement"):
        tk = a.get("tickets") or a["bloc"].get("tickets")
        keys = ["w:" + w for w in a.get("snipers") or []] + (["c:" + a["createur"]] if a.get("createur") else [])
        if tk:
            keys.append("k:" + "+".join("%.2f" % x for x in sorted(tk, reverse=True)))
        for k in keys:
            parent[find("a:" + a["mint"])] = find(k)
    return {r["mint"]: find("a:" + r["mint"]) for r in journal if r["genre"] == "alerte_lancement"}


def main_test() -> None:
    """TEST rows, from the second snapshot (code/snap_50_freeze_test.py)."""
    snap = os.path.join(STUDY, "data", "test_snapshot")
    with gzip.open(os.path.join(snap, "journal.jsonl.gz"), "rt", encoding="utf8") as fh:
        journal = [json.loads(x) for x in fh]
    series: dict[str, list[tuple[float, float]]] = defaultdict(list)
    with gzip.open(os.path.join(snap, "series.txt.gz"), "rt", encoding="utf8") as fh:
        for line in fh:
            m, dt, mult, _ = line.split()
            series[m].append((float(dt), float(mult)))
    for v in series.values():
        v.sort()
    test = set(json.load(open(os.path.join(snap, "test_alerts.json"))))
    sol = sol_usd_table(os.path.join(snap, "sol_usd_hourly.json"))
    ctx = context(journal, sol)
    alerts = [r for r in journal if r["genre"] == "alerte_lancement" and r["mint"] in test]
    build(alerts, ctx, clusters_of(journal), "forensic_rows_test.jsonl.gz", dict(series), split_name="test")


def main() -> None:
    if "--test" in sys.argv:
        main_test()
        return
    dictionary()
    journal = pde.load_journal()
    sol = sol_usd_table(os.path.join(pde.DATA, "sol_usd_hourly.json"))
    ctx = context(journal, sol)
    # operator clusters of the previous study, grouping only (never a feature)
    clusters = {r["mint"]: r["cluster"] for r in pde.read_rows("dataset_dev.jsonl.gz")}
    clusters.update({r["mint"]: r["cluster"] for r in pde.read_rows("dataset_test.sealed.jsonl.gz")})
    alerts = [r for r in journal if r["genre"] == "alerte_lancement"]
    build(alerts, ctx, clusters, "forensic_rows.jsonl.gz", pde.load_series())


if __name__ == "__main__":
    main()
