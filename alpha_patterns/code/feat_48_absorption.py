#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feat_48_absorption.py -- inventory, team liquidation and external demand per launch, at fixed cuts
(tables/TEAM_ABSORPTION_PREREG_2026-10-07.md, amendment 1). Features only: no outcome is read here.

Source: the raw window of every alert (creation -> alert + 30 s, every successful transaction of the
mint, parsed by post_detection_forensics/fparse.py through mech_40.load_window). Failed transactions
are not detailed by the collector (by design); they move no token.

Records (amendment 1.6): fparse's buy / sell (read from balances) are kept; a 'migrate' after slot 0
that also buys is a buy; buyburn (tokens burned, SOL into the pool) is kept apart; a transfer is any
record without a venue where one wallet loses >= 1e6 tokens and another gains >= 1e6 (a transfer typed
'create' by the instruction name included).
Per launch and per cut c (seconds relative to the alert; visible when bt <= t_alert + c):
  team T_c     snipers of the bundle + creator + every wallet that received >= 1e6 tokens (0.1 % of the
               supply) from a team wallet in a transfer visible at the cut (closure; dust ignored)
  inventory    tokens of the snipers from the slot-0 records (buy, create, migrate): validated against
               the detector's supply share; inventory_team adds the creator's slot-0 tokens (M5 base)
  team sells   sells by T_c wallets, slot 0 included
  external     buys AFTER the creation slot by wallets outside T_c (organic demand); sells by others
Cuts: -1 (pre-alert), 2, 7, 17, 27 (primary decision cuts for T = +5, +10, +20, +30 s: 3 s of margin for
the detector's 1-2 s lag), 4, 9, 19, 29 (T - 1, sensitivity and descriptive).
Output: derived/feat_absorption.jsonl.gz (one row per alert before 2026-09-15).
"""
from __future__ import annotations

import math
import os
from collections import Counter

import ap_lib as A
from mech_40_break_the_loop import load_window

CUTS = (-1, 2, 4, 7, 9, 17, 19, 27, 29)
MIN_TRANSFER = 1e6  # tokens (0.1 % of the supply): dust transfers (1 token to hundreds of wallets) are not exits
OUT = os.path.join(A.DERIVED, "feat_absorption.jsonl.gz")


def classify(r, slot0):
    """fparse's own buy / sell (read from balances) are kept; only its name-based types are corrected:
    a 'migrate' after the creation slot that also buys (venue, legs, tokens out of the venue) is a buy;
    any record without a venue where one wallet loses >= 1e6 tokens and another gains >= 1e6 is a
    transfer (a transfer typed 'create' by the instruction name included). The slot-0 creation and
    migration themselves are never trades."""
    k = r.get("kind")
    if r.get("err"):
        return None
    if k == "buyburn":
        return "buyburn"
    if k in ("buy", "sell"):
        return k
    if k == "migrate" and r["slot"] > slot0 and r.get("venue") and r.get("legs") and (r.get("v_tok") or 0) < 0:
        return "buy"
    if not r.get("venue") and r.get("legs"):
        lg = r["legs"]
        if any(v <= -MIN_TRANSFER for v in lg.values()) and any(v >= MIN_TRANSFER for v in lg.values()):
            return "transfer"
    return None


def buy_legs(r):
    """{buyer: SOL paid} for a buy (leg_sol when the record carries several receivers)."""
    if r.get("leg_sol"):
        return {w: float(v) for w, v in r["leg_sol"].items() if v and v > 0}
    return {r["trader"]: float(r["v_sol"])} if (r.get("v_sol") or 0) > 0 else {}


def launch(b, snipers, creator, slot0):
    t_a = b["t"]
    w, recs, facts = load_window(b["mint"])
    if abs(w["t_alert"] - t_a) > 0.01:
        raise RuntimeError("alert time mismatch " + b["mint"])
    recs = [r for r in recs if not r.get("err")]
    for r in recs:
        if r.get("bt") is None:
            raise RuntimeError("record without block time " + b["mint"])
        r["_k"] = classify(r, slot0)
    s0 = [r for r in recs if r["slot"] == slot0]
    if not s0:
        raise RuntimeError("no creation-slot record " + b["mint"])
    t_c = min(r["bt"] for r in s0)
    inv, inv_cr = Counter(), 0.0
    for r in s0:
        if r.get("kind") in ("buy", "migrate", "create"):
            for wl, tok in (r.get("legs") or {}).items():
                if tok > 0 and wl in snipers:
                    inv[wl] += tok
                elif tok > 0 and wl == creator:
                    inv_cr += tok
    I = float(sum(inv.values()))
    if I <= 0:
        raise RuntimeError("no sniper inventory " + b["mint"])
    I_team = I + inv_cr
    trans = sorted((r for r in recs if r["_k"] == "transfer"), key=lambda r: (r["slot"], r["bt"]))
    sells = [r for r in recs if r["_k"] == "sell"]
    buys_ext_window = [r for r in recs if r["_k"] == "buy" and r["slot"] > slot0]
    burns = [r for r in recs if r["_k"] == "buyburn" and r["slot"] > slot0]
    row = {"mint": b["mint"], "t": t_a, "t_create": t_c, "age_alert": t_a - t_c, "inventory_tok": I, "inventory_supply": I / 1e9,
           "inventory_team_tok": I_team, "inventory_hhi": sum((v / I) ** 2 for v in inv.values()), "snipers_n": len(snipers),
           "inventory_value_sol": I * float(b["p0"])}
    founders = set(snipers) | ({creator} if creator else set())

    def team_at(cutabs):
        team = set(founders)
        vis = [r for r in trans if r["bt"] <= cutabs]
        first_tr = None
        changed = True
        while changed:
            changed = False
            for r in vis:
                lg = r["legs"]
                if any(lg.get(x, 0) <= -MIN_TRANSFER for x in team):
                    for x, v in lg.items():
                        if v >= MIN_TRANSFER and x not in team:
                            team.add(x)
                            changed = True
                            first_tr = r["bt"] if first_tr is None else min(first_tr, r["bt"])
        return team, first_tr
    team_end, first_transfer = team_at(t_a + 29)
    row["exit_wallets_end"] = len(team_end - founders)
    row["first_transfer_from_create"] = (first_transfer - t_c) if first_transfer is not None else None
    se = [r for r in sells if r["bt"] <= t_a + 29 and r.get("trader") in team_end]
    row["first_team_sell_from_create"] = (min(r["bt"] for r in se) - t_c) if se else None
    row["first_team_sell_from_alert"] = (min(r["bt"] for r in se) - t_a) if se else None
    row["team_end_sell_sol_by_t+4"] = sum(-float(r["v_sol"]) for r in se if r["bt"] <= t_a + 4 and (r.get("v_sol") or 0) < 0)
    row["team_end_sell_sol_by_t+29"] = sum(-float(r["v_sol"]) for r in se if (r.get("v_sol") or 0) < 0)
    for h in (10, 20, 30, 40):  # descriptive horizons from the creation block
        cutabs = t_c + h
        if cutabs > t_a + 29:
            row["team_sold_share_c%d" % h] = None
            continue
        tm, _ = team_at(cutabs)
        row["team_sold_share_c%d" % h] = sum(float(r["v_tok"]) for r in sells if r["bt"] <= cutabs and r.get("trader") in tm and r["v_tok"] > 0) / I_team
    for c in CUTS:
        cutabs = t_a + c
        tm, _ = team_at(cutabs)
        vs = [r for r in sells if r["bt"] <= cutabs]
        vb = [r for r in buys_ext_window if r["bt"] <= cutabs]
        vbb = [r for r in burns if r["bt"] <= cutabs]
        if any(r["bt"] > cutabs for r in vs + vb + vbb):  # K4
            raise RuntimeError("record after the cut " + b["mint"])
        team_sell_tok = team_sell_sol = ext_sell_sol = 0.0
        team_sellers = set()
        for r in vs:
            tok, sol = max(float(r.get("v_tok") or 0), 0.0), max(-float(r.get("v_sol") or 0), 0.0)
            if r.get("trader") in tm:
                team_sell_tok += tok
                team_sell_sol += sol
                team_sellers.add(r["trader"])
            else:
                ext_sell_sol += sol
        buyers = Counter()
        last10, b_last10, b_prev10 = 0.0, set(), set()
        for r in vb:
            for wl, sol in buy_legs(r).items():
                if wl in tm:
                    continue
                buyers[wl] += sol
                if r["bt"] > cutabs - 10:
                    last10 += sol
                    b_last10.add(wl)
                elif r["bt"] > cutabs - 20:
                    b_prev10.add(wl)
        tot = sum(buyers.values())
        sfx = "_t%+d" % c
        row.update({"team_size" + sfx: len(tm), "exit_wallets" + sfx: len(tm - founders),
                    "team_sell_tok" + sfx: team_sell_tok, "team_sold_share" + sfx: team_sell_tok / I_team,
                    "team_sell_sol" + sfx: team_sell_sol, "team_sellers" + sfx: len(team_sellers),
                    "ext_buyers" + sfx: len(buyers), "ext_buy_sol" + sfx: tot, "ext_sell_sol" + sfx: ext_sell_sol,
                    "ext_buy_sol_last10" + sfx: last10, "ext_buyers_last10" + sfx: len(b_last10), "ext_buyers_prev10" + sfx: len(b_prev10),
                    "buyburn_sol" + sfx: sum(float(r.get("v_sol") or 0) for r in vbb), "buyburn_n" + sfx: len(vbb),
                    "ext_buy_hhi" + sfx: (sum((v / tot) ** 2 for v in buyers.values()) if tot > 0 else None),
                    "ext_buy_median_sol" + sfx: (sorted(buyers.values())[len(buyers) // 2] if buyers else None),
                    "ext_buyer_sol" + sfx: {wl: round(v, 9) for wl, v in sorted(buyers.items())}})
    first = {}
    for r in buys_ext_window:
        for wl in buy_legs(r):
            if wl not in team_end:
                first[wl] = min(first.get(wl, math.inf), r["bt"] - t_a)
    row["ext_first_buy_dt"] = first
    return row


def main() -> None:
    base = [b for b in A.load_base() if b["t"] < A.T_SEL_END]
    cd = {}
    for r in A.jl(A.CD_TABLE):
        # every bundle sniper (role core, or role creator when the creator is itself one of the snipers)
        cd[r["mint"]] = ({s["wallet"] for s in r["snipers"] if s.get("role") in ("core", "creator")}, (r.get("creator") or {}).get("wallet"), r["slot0"])
    rows = []
    for k, b in enumerate(base):
        sn, cr, slot0 = cd[b["mint"]]
        rows.append(launch(b, sn, cr, slot0))
        if k % 250 == 0:
            print(k, "launches")
    A.write_jl(OUT, rows)
    print("written", len(rows))


if __name__ == "__main__":
    main()
