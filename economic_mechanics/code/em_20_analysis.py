#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The analysis of analysis_plan.md on the frozen economic-mechanics table: role graph and architectures,
funding, capital lifecycle, supply, exits, recurrence, clusters, null models (1,000 permutations),
robustness, roles, hypotheses, fingerprints; then, last and apart, the price impact. Groups come from
the frozen coordination labels; no price outcome defines anything.

Writes tables/B_roles.md, C_funding.md, D_lifecycle.md, E_supply.md, E2_price_impact.md, F_exits.md,
G_recurrence.md, H_nulls.md, I_robustness.md, J_roles_hypotheses.md and derived/M_results.json.
"""

from __future__ import annotations

import json
import math
import os
import random
import statistics
from collections import Counter, defaultdict
from typing import Any, Callable, Optional

import em_lib as E

P_INIT = 30.0 / 1.073e9  # pump.fun bonding curve: 30 SOL and 1.073e9 tokens of virtual reserves


def by_group(rows: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    return [(g, sp, [r for r in rows if r["split"] == sp and r["group"][g]]) for g in E.GROUPS for sp in E.SPLITS]


# --------------------------------------------------------------- mechanisms --- #
def m_shared(kind: str = "last", strict: bool = False) -> Callable[[list[list[dict[str, Any]]]], float]:
    def stat(groups: list[list[dict[str, Any]]]) -> float:
        n = 0
        for g in groups:
            keys = [E.fkey(s, kind, strict) for s in g]
            c = Counter(k for k in keys if k and not k.startswith("own:"))
            n += bool(c) and max(c.values()) >= 2
        return float(n)

    return stat


def m_one_tx(groups: list[list[dict[str, Any]]]) -> float:
    return float(
        sum(
            1
            for g in groups
            if max(Counter(s.get("last_sig") for s in g if s.get("last_sig")).values(), default=0) >= 2
        )
    )


def null_time_spread(rr: list[dict[str, Any]], n_perm: int = E.N_PERM) -> dict[str, Any]:
    known = [r for r in rr if all(s.get("last_bt") is not None and s.get("bt") for s in r["snipers"])]
    if not known:
        return {}
    dl = [[s["bt"] - s["last_bt"] for s in r["snipers"]] for r in known]
    obs = statistics.mean(max(d) - min(d) for d in dl)
    pool = [x for d in dl for x in d]
    rng = random.Random(E.SEED)
    null = []
    for _ in range(n_perm):
        p = E.shuffled(rng, pool)
        i, v = 0, []
        for d in dl:
            v.append(max(p[i : i + len(d)]) - min(p[i : i + len(d)]))
            i += len(d)
        null.append(statistics.mean(v))
    return E.perm_test(obs, null, higher=False)


def null_exit_sync(rr: list[dict[str, Any]], n_perm: int = E.N_PERM) -> dict[str, Any]:
    per = []
    for r in rr:
        d = [min((x["slot"] for x in s["exits_full"]), default=None) for s in r["snipers"]]
        d = [x - r["slot0"] for x in d if x is not None]
        if len(d) >= 2:
            per.append(d)
    if not per:
        return {}

    def share(d: list[int]) -> float:
        c = Counter(d)
        return sum(1 for x in d if c[x] >= 2) / len(d)

    obs = statistics.mean(share(d) for d in per)
    pool = [x for d in per for x in d]
    rng = random.Random(E.SEED)
    null = []
    for _ in range(n_perm):
        p = E.shuffled(rng, pool)
        i, v = 0, []
        for d in per:
            v.append(share(p[i : i + len(d)]))
            i += len(d)
        null.append(statistics.mean(v))
    return E.perm_test(obs, null)


def null_exit_size(rr: list[dict[str, Any]], n_perm: int = E.N_PERM) -> dict[str, Any]:
    per = []
    for r in rr:
        sh = [E.sniper_lifecycle(r, s)["share_gone_30s"] for s in r["snipers"] if s["exits_full"]]
        if len(sh) >= 2:
            per.append(sh)
    if not per:
        return {}

    def cv(v: list[float]) -> float:
        m = statistics.mean(v)
        return statistics.pstdev(v) / m if m > 0 else 0.0

    obs = statistics.mean(cv(v) for v in per)
    pool = [x for v in per for x in v]
    rng = random.Random(E.SEED)
    null = []
    for _ in range(n_perm):
        p = E.shuffled(rng, pool)
        i, vals = 0, []
        for v in per:
            vals.append(cv(p[i : i + len(v)]))
            i += len(v)
        null.append(statistics.mean(vals))
    return E.perm_test(obs, null, higher=False)


def null_consolidation(rr: list[dict[str, Any]], n_perm: int = E.N_PERM) -> dict[str, Any]:
    per = []
    for r in rr:
        rec = [tuple(E.sniper_lifecycle(r, s)["recipients"]) for s in r["snipers"]]
        if sum(1 for x in rec if x) >= 2:
            per.append(rec)
    if not per:
        return {}

    def common(rec: list[tuple]) -> bool:
        c = Counter(o for x in rec for o in set(x))
        return bool(c) and max(c.values()) >= 2

    obs = float(sum(1 for rec in per if common(rec)))
    pool = [x for rec in per for x in rec if x]
    rng = random.Random(E.SEED)
    null = []
    for _ in range(n_perm):
        p = E.shuffled(rng, pool)
        i, n = 0, 0
        for rec in per:
            k = sum(1 for x in rec if x)
            n += common(p[i : i + k])
            i += k
        null.append(float(n))
    return E.perm_test(obs, null)


def returning(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Returning snipers with complete flows between their two launches: destinations of SOL out, their
    first and next funders."""
    by_mint = {r["mint"]: r for r in rows}
    out = []
    for r in rows:
        for s in r["snipers"]:
            b = s.get("between")
            if not b or not b["complete"]:
                continue
            nr = by_mint.get(b["next_mint"])
            ns = next((x for x in nr["snipers"] if x["wallet"] == s["wallet"]), None) if nr else None
            dest = []
            for x in b["txs"]:
                d = x.get("d") or {}
                if x.get("err") or d.get(s["wallet"], 0) >= -0.01:
                    continue
                to = max((k for k in d if k != s["wallet"]), key=lambda k: d[k], default=None)
                if to and d.get(to, 0) > 0:
                    dest.append(to)
            out.append(
                {
                    "split": r["split"],
                    "group": r["group"],
                    "cluster": r["cluster"],
                    "wallet": s["wallet"],
                    "dest": dest,
                    "first_funder": s.get("last_funder"),
                    "deployer": r["creator"].get("wallet"),
                    "snipers": {x["wallet"] for x in r["snipers"]},
                    "next_funder": ns.get("last_funder") if ns else None,
                    "gap_s": b["next_t"] - r["t"],
                    "flows": E.returning_flows(r, s, ns.get("last_funder") if ns else None),
                }
            )
    return out


def null_proceeds(ret: list[dict[str, Any]], n_perm: int = E.N_PERM) -> dict[str, Any]:
    use = [x for x in ret if x["first_funder"] and x["dest"]]
    if not use:
        return {}
    obs = sum(1 for x in use if x["first_funder"] in x["dest"]) / len(use)
    funders = [x["first_funder"] for x in use]
    rng = random.Random(E.SEED)
    null = [sum(1 for x, f in zip(use, E.shuffled(rng, funders)) if f in x["dest"]) / len(use) for _ in range(n_perm)]
    return E.perm_test(obs, null)


def null_refund(ret: list[dict[str, Any]], n_perm: int = E.N_PERM) -> dict[str, Any]:
    use = [x for x in ret if x["first_funder"] and x["next_funder"]]
    if not use:
        return {}
    obs = sum(1 for x in use if x["first_funder"] == x["next_funder"]) / len(use)
    nxt = [x["next_funder"] for x in use]
    rng = random.Random(E.SEED)
    null = [
        sum(1 for x, f in zip(use, E.shuffled(rng, nxt)) if f == x["first_funder"]) / len(use) for _ in range(n_perm)
    ]
    return E.perm_test(obs, null)


def mechanisms(
    rr: list[dict[str, Any]], ret: list[dict[str, Any]], n_perm: int = E.N_PERM, only: Optional[set[str]] = None
) -> dict[str, dict[str, Any]]:
    tests: dict[str, Callable[[], dict[str, Any]]] = {
        "shared last funder": lambda: E.null_funding(rr, m_shared(), ("last_funder", "last_funder_hub"), n_perm),
        "one funding transaction for 2+ snipers": lambda: E.null_funding(rr, m_one_tx, ("last_sig",), n_perm),
        "funding-time synchrony (spread, s)": lambda: null_time_spread(rr, n_perm),
        "exits in one slot (share)": lambda: null_exit_sync(rr, n_perm),
        "similar exit sizes (CV)": lambda: null_exit_size(rr, n_perm),
        "tokens consolidated to one recipient": lambda: null_consolidation(rr, n_perm),
        "proceeds back to the first funder": lambda: null_proceeds(ret, n_perm),
        "returning sniper re-funded by the same funder": lambda: null_refund(ret, n_perm),
        "recurring sniper pairs": lambda: E.null_pairs([[s["wallet"] for s in r["snipers"]] for r in rr], n_perm),
    }
    return {k: f() for k, f in tests.items() if only is None or k in only}


def fmt_test(d: dict[str, Any]) -> str:
    if not d:
        return "n/a"
    return "%.4g | %.4g [%.4g, %.4g] | %.0f %% | %.4f | %s" % (
        d["obs"],
        d["null_mean"],
        d["ci"][0],
        d["ci"][1],
        100 * d["pct"],
        d["p"],
        "n/a" if d["effect"] is None else "x%.2f" % d["effect"],
    )


# --------------------------------------------------------------------- main --- #
def main() -> None:
    rows = E.load()
    E.require_hops(rows)
    E.check_prices()
    res: dict[str, Any] = {}
    arch = {r["mint"]: E.architecture(r) for r in rows}
    arch_g = {r["mint"]: E.architecture(r, "gen") for r in rows}
    arch_s = {r["mint"]: E.architecture(r, strict=True) for r in rows}
    # ---------------- B roles and architectures
    lines = [
        "# B. Role graph and architectures",
        "",
        "Primary architecture per launch (C deployer funds 2+ snipers; A a funder of 2+ snipers linked to the "
        "deployer; D several funders of 2+ snipers or a common source; B a common funder, no deployer link; E no "
        "common funding; UNRESOLVED a sniper's funder unknown). Flags can combine; the primary is the first of "
        "C, A, D, B, E.",
        "",
        "| group | split | launches | C | A | D | B | E | UNRESOLVED |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for g, sp, rr in by_group(rows):
        c = Counter(arch[r["mint"]]["primary"] for r in rr)
        lines.append(
            "| %s | %s | %d | %s |"
            % (
                g,
                sp.upper(),
                len(rr),
                " | ".join(
                    "%d (%.0f %%)" % (c[a], 100 * c[a] / max(1, len(rr)))
                    for a in ("C", "A", "D", "B", "E", "UNRESOLVED")
                ),
            )
        )
    lines += [
        "",
        "Sensitivity, all launches: last funders, genesis funders, known non-hub last funders only.",
        "",
        "| architecture | last funders | genesis funders | strict |",
        "|---|---:|---:|---:|",
    ]
    for a in ("C", "A", "D", "B", "E", "UNRESOLVED", "OTHER"):
        lines.append(
            "| %s | %d | %d | %d |"
            % (
                a,
                sum(1 for v in arch.values() if v["primary"] == a),
                sum(1 for v in arch_g.values() if v["primary"] == a),
                sum(1 for v in arch_s.values() if v["primary"] == a),
            )
        )
    lines += ["", "## Representative launches (the first TRAIN launch of each architecture; addresses shortened)", ""]
    for a in ("C", "A", "D", "B", "E"):
        r = next((x for x in rows if x["split"] == "train" and arch[x["mint"]]["primary"] == a), None)
        if not r:
            continue
        dep = r["creator"].get("wallet")
        lines += [
            "### %s, launch %s (%s), deployer %s" % (a, short(r["mint"]), r["utc"], E.short(dep)),
            "",
            "| sniper | ticket SOL | tokens | funded by | funding SOL | funding s before buy | funding tx | "
            "hub status | first exit | tokens gone by +30 s |",
            "|---|---:|---:|---|---:|---:|---|---|---|---:|",
        ]
        for s in r["snipers"]:
            lc = E.sniper_lifecycle(r, s)
            fb = s.get("last_funder")
            lines.append(
                "| %s | %.2f | %.3g | %s%s | %s | %s | %s | %s | %s | %s |"
                % (
                    E.short(s["wallet"]),
                    s["ticket"],
                    s["tok_bought"],
                    E.short(fb),
                    " (deployer)" if fb == dep else "",
                    "n/a" if s.get("last_amount") is None else "%.3f" % s["last_amount"],
                    "n/a" if s.get("last_bt") is None else "%d" % (s["bt"] - s["last_bt"]),
                    E.short(s.get("last_sig")),
                    {True: "hub", False: "non-hub", None: "unknown"}[s.get("last_funder_hub")],
                    "n/a"
                    if "first_exit_s" not in lc
                    else "%s after %d s" % ("transfer" if lc["n_transfers"] else "sell", lc["first_exit_s"]),
                    "n/a" if lc["share_gone_30s"] is None else "%.0f %%" % (100 * lc["share_gone_30s"]),
                )
            )
        lines.append("")
    E.write("B_roles.md", lines)
    res["architectures"] = Counter(v["primary"] for v in arch.values())
    # ---------------- C funding
    fm = {r["mint"]: E.funding_measures(r) for r in rows}
    keys = [
        "total_funded",
        "amount_cv",
        "time_spread_s",
        "to_creation_s",
        "to_buy_s",
        "share_lt_1min",
        "share_lt_10min",
        "share_lt_60min",
        "max_snipers_one_funding_tx",
    ]
    lines = ["# C. Funding mechanics (median / Q25 / Q75 / Q90 / min / max, N)", ""]
    for g, sp, rr in by_group(rows):
        lines += ["## %s, %s (%d launches)" % (g, sp.upper(), len(rr)), "", "| measure | distribution |", "|---|---|"]
        for k in keys:
            lines.append("| %s | %s |" % (k, E.dist([fm[r["mint"]].get(k) for r in rr])))
        for k in ("one_tx_for_2plus", "shared_funder_2plus", "funder_funded_by_deployer", "deployer_funds_sniper"):
            v = [fm[r["mint"]].get(k) for r in rr if fm[r["mint"]].get(k) is not None]
            lines.append("| %s | %d of %d (%.0f %%) |" % (k, sum(v), len(v), 100 * sum(v) / max(1, len(v))))
        amt = [s.get("last_amount") for r in rr for s in r["snipers"]]
        lines += ["| funding per sniper wallet (SOL) | %s |" % E.dist(amt), ""]
    E.write("C_funding.md", lines)
    # ---------------- D lifecycle
    ret = returning(rows)
    lines = [
        "# D. Capital lifecycle per sniper (up to alert + 30 s; then between two launches for returning snipers)",
        "",
    ]
    for g, sp, rr in by_group(rows):
        lc = [E.sniper_lifecycle(r, s) for r in rr for s in r["snipers"]]
        if not lc:
            continue
        lines += ["## %s, %s (%d snipers)" % (g, sp.upper(), len(lc)), "", "| measure | value |", "|---|---|"]
        for k in (
            "received",
            "spent",
            "spent_over_received",
            "share_gone_30s",
            "sold_sol",
            "first_exit_s",
            "complete_exit_s",
            "residual_sol",
        ):
            lines.append("| %s | %s |" % (k, E.dist([x.get(k) for x in lc])))
        ex = [x for x in lc if x["exited"]]
        lines += [
            "| exited by alert + 30 s | %d of %d (%.0f %%) |" % (len(ex), len(lc), 100 * len(ex) / len(lc)),
            "| exits by token transfer only / by sale only / both | %d / %d / %d |"
            % (
                sum(1 for x in ex if x["n_transfers"] and not x["n_sells"]),
                sum(1 for x in ex if x["n_sells"] and not x["n_transfers"]),
                sum(1 for x in ex if x["n_sells"] and x["n_transfers"]),
            ),
            "| complete exit by alert + 30 s | %d of %d exiting |"
            % (sum(1 for x in ex if x.get("complete_exit_s") is not None), len(ex)),
            "",
        ]
    lines += [
        "## Returning snipers: SOL sent out between two launches (complete records)",
        "",
        "| split | records | with an outflow | first launch's funder | its deployer | another sniper of it | "
        "next launch's funder | another wallet | re-funded by the same funder | gap between launches, h |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for sp in E.SPLITS:
        rr = [x for x in ret if x["split"] == sp]
        fl = [x["flows"] for x in rr if x["flows"]]
        w = [f for f in fl if f["outflows"]]
        cls = Counter(c for f in w for c in set(f["outflows"]))
        lines.append(
            "| %s | %d | %d | %s | %s | %s | %s | %s | %d of %d | %s |"
            % (
                sp.upper(),
                len(rr),
                len(w),
                *(
                    "%d (%.0f %%)" % (cls[c], 100 * cls[c] / max(1, len(w)))
                    for c in (
                        "first launch's funder",
                        "first launch's deployer",
                        "another sniper of the launch",
                        "next launch's funder",
                        "another wallet",
                    )
                ),
                sum(1 for x in rr if x["next_funder"] and x["next_funder"] == x["first_funder"]),
                sum(1 for x in rr if x["next_funder"] and x["first_funder"]),
                E.dist([x["gap_s"] / 3600 for x in rr]),
            )
        )
    E.write("D_lifecycle.md", lines)
    # ---------------- E supply
    lines = [
        "# E. Supply held by the group (creation slot)",
        "",
        "| group | split | group share of supply | largest "
        "sniper share | token HHI among snipers | group share of the slot's SOL | snipers in a multi-wallet "
        "transaction | tokens gone before the alert |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for g, sp, rr in by_group(rows):
        if not rr:
            continue
        sup, top, hh, sl, mt, pre = [], [], [], [], [], []
        for r in rr:
            tk = [s["tok_bought"] for s in r["snipers"]]
            sup.append(sum(tk) / 1e9)
            top.append(max(tk) / 1e9)
            hh.append(sum((x / sum(tk)) ** 2 for x in tk))
            tot = sum(r["slot0_sol"].values())
            sl.append(sum(r["slot0_sol"].get(s["wallet"], 0) for s in r["snipers"]) / tot if tot else None)
            per = Counter(g2 for s in r["snipers"] for g2 in s["sigs"])
            mt.append(sum(1 for s in r["snipers"] if any(per[x] >= 2 for x in s["sigs"])) / len(r["snipers"]))
            gone = sum(x["tok_out"] for s in r["snipers"] for x in s["exits_full"] if (x["bt"] or 0) <= r["t"] - 1)
            pre.append(gone / sum(tk))
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s |"
            % (g, sp.upper(), E.dist(sup), E.dist(top), E.dist(hh), E.dist(sl), E.dist(mt), E.dist(pre))
        )
    E.write("E_supply.md", lines)
    # ---------------- F exits
    lines = [
        "# F. Exit mechanics (first exits up to alert + 30 s; 60 s and 5 min after the buy are censored)",
        "",
        "| group | split | snipers | exit within 5 s / 10 s / 30 s of the buy | launches with 2+ exiting | "
        "same-slot share of first exits | spread of first exits (slots) |",
        "|---|---|---:|---|---:|---|---|",
    ]
    for g, sp, rr in by_group(rows):
        sn = [(r, s) for r in rr for s in r["snipers"]]
        if not sn:
            continue
        fe = [E.sniper_lifecycle(r, s).get("first_exit_s") for r, s in sn]
        sy = [E.exit_sync(r) for r in rr]
        sy = [x for x in sy if x]
        lines.append(
            "| %s | %s | %d | %s | %d | %s | %s |"
            % (
                g,
                sp.upper(),
                len(sn),
                " / ".join(
                    "%.0f %%" % (100 * sum(1 for x in fe if x is not None and x <= t) / len(sn)) for t in (5, 10, 30)
                ),
                len(sy),
                E.dist([x["same_slot_share"] for x in sy]),
                E.dist([x["spread_slots"] for x in sy]),
            )
        )
    E.write("F_exits.md", lines)
    # ---------------- G recurrence and clusters
    appear: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in sorted(rows, key=lambda z: z["t"]):
        for s in r["snipers"]:
            appear[s["wallet"]].append(r)
    fund_launch: dict[str, set] = defaultdict(set)
    dep_launch: Counter = Counter()
    fs_pairs: Counter = Counter()
    for r in rows:
        dep_launch[r["creator"].get("wallet")] += 1
        for s in r["snipers"]:
            f = E.fkey(s)
            if f and not f.startswith("own:"):
                fund_launch[f].add(r["mint"])
                fs_pairs[(f, s["wallet"])] += 1
    gaps = [(b["t"] - a["t"]) / 3600 for lst in appear.values() for a, b in zip(lst, lst[1:])]
    pairs = E.co_pairs([[s["wallet"] for s in r["snipers"]] for r in rows])
    rec_pairs = [p for p, v in pairs.items() if v >= 2]
    deps_per_pair = []
    for p in rec_pairs:
        ls = [r for r in appear[p[0]] if any(s["wallet"] == p[1] for s in r["snipers"])]
        deps_per_pair.append(len({r["creator"].get("wallet") for r in ls}))
    cl = E.clusters(sorted(rows, key=lambda z: z["t"]))
    groups: dict[str, list[str]] = defaultdict(list)
    for m, c in cl.items():
        groups[c].append(m)
    by_mint = {r["mint"]: r for r in rows}
    lines = [
        "# G. Recurrence across launches",
        "",
        "- Sniper wallets: %d; in 2 launches or more: %d; launches per recurring wallet %s."
        % (
            len(appear),
            sum(1 for v in appear.values() if len(v) >= 2),
            E.dist([len(v) for v in appear.values() if len(v) >= 2], "%.0f"),
        ),
        "- Hours between two launches of the same sniper: %s." % E.dist(gaps),
        "- Non-hub funders: %d; funding snipers in 2 launches or more: %d."
        % (len(fund_launch), sum(1 for v in fund_launch.values() if len(v) >= 2)),
        "- The same funder funding the same sniper in 2 launches or more: %d relations."
        % sum(1 for v in fs_pairs.values() if v >= 2),
        "- Deployers: %d; deploying 2 launches or more: %d."
        % (len(dep_launch), sum(1 for v in dep_launch.values() if v >= 2)),
        "- Recurring sniper pairs: %d; distinct deployers behind a recurring pair: %s."
        % (len(rec_pairs), E.dist(deps_per_pair, "%.0f")),
        "",
        "## Clusters (wallets joined by co-sniping, non-hub funding, deployer-to-funder transfers, common "
        "sources; information at or before each launch)",
        "",
    ]
    cs = sorted(groups.values(), key=len, reverse=True)
    multi = [c for c in cs if len(c) >= 2]
    lines += [
        "- Clusters holding a launch: %d; holding 2 launches or more: %d, with %d launches."
        % (len(cs), len(multi), sum(len(c) for c in multi)),
        "- Launches per multi-launch cluster: %s." % E.dist([len(c) for c in multi], "%.0f"),
        "- Multi-launch clusters with TRAIN and VALIDATION launches: %d."
        % sum(1 for c in multi if {by_mint[m]["split"] for m in c} == {"train", "val"}),
        "- Operator clusters of the previous studies spanned per multi-launch cluster: %s."
        % E.dist([len({by_mint[m]["cluster"] for m in c}) for c in multi], "%.0f"),
        "",
        "## Behavioral fingerprints of the clusters with 10 launches or more",
        "",
        "| cluster | launches TRAIN / VAL | dominant architecture | one-tx funding | funding s before buy | "
        "snipers | ticket SOL | supply share | exited by +30 s | exits by transfer | proceeds to first funder "
        "| days between launches | operator clusters |",
        "|---|---|---|---:|---|---:|---|---|---:|---:|---|---|---:|",
    ]
    retm = defaultdict(list)
    for x in ret:
        retm[x["wallet"]].append(x)
    fps = []
    for i, c in enumerate([c for c in multi if len(c) >= 10]):
        rr = sorted((by_mint[m] for m in c), key=lambda z: z["t"])
        ar = Counter(arch[r["mint"]]["primary"] for r in rr).most_common(1)[0]
        lc = [E.sniper_lifecycle(r, s) for r in rr for s in r["snipers"]]
        ex = [x for x in lc if x["exited"]]
        wl = {s["wallet"] for r in rr for s in r["snipers"]}
        rx = [x for w in wl for x in retm.get(w, []) if x["first_funder"] and x["dest"]]
        fm_c = [fm[r["mint"]] for r in rr]
        fps.append({"launches": len(rr), "arch": ar})
        lines.append(
            "| %d | %d / %d | %s (%.0f %%) | %.0f %% | %s | %s | %s | %s | %.0f %% | %.0f %% | %s | %s | %d |"
            % (
                i + 1,
                sum(1 for r in rr if r["split"] == "train"),
                sum(1 for r in rr if r["split"] == "val"),
                ar[0],
                100 * ar[1] / len(rr),
                100 * sum(1 for f in fm_c if f.get("one_tx_for_2plus")) / len(rr),
                E.dist([f.get("to_buy_s") for f in fm_c], "%.0f").split(" /")[0],
                E.dist([len(r["snipers"]) for r in rr], "%.0f").split(" /")[0],
                E.dist([s["ticket"] for r in rr for s in r["snipers"]], "%.1f").split(" /")[0],
                E.dist([sum(s["tok_bought"] for s in r["snipers"]) / 1e9 for r in rr], "%.3f").split(" /")[0],
                100 * len(ex) / max(1, len(lc)),
                100 * sum(1 for x in ex if x["n_transfers"]) / max(1, len(ex)),
                "%d of %d" % (sum(1 for x in rx if x["first_funder"] in x["dest"]), len(rx)) if rx else "n/a",
                E.dist([(b["t"] - a["t"]) / 86400 for a, b in zip(rr, rr[1:])], "%.2f").split(" /")[0],
                len({r["cluster"] for r in rr}),
            )
        )
    E.write("G_recurrence.md", lines)
    res["clusters"] = {"n": len(cs), "multi": len(multi), "fingerprints": len(fps)}
    # ---------------- H nulls
    mech = {
        (g, sp): mechanisms(rr, [x for x in ret if x["split"] == sp and x["group"][g]])
        for g, sp, rr in by_group(rows)
        if g == "COORDINATED"
    }
    allm = {
        sp: mechanisms([r for r in rows if r["split"] == sp], [x for x in ret if x["split"] == sp]) for sp in E.SPLITS
    }
    lines = [
        "# H. Null models (%d permutations): observed | null mean [95 %%] | percentile | p | effect" % E.N_PERM,
        "",
        "| mechanism | all launches, TRAIN | all launches, VALIDATION | coordinated, TRAIN | coordinated, VALIDATION |",
        "|---|---|---|---|---|",
    ]
    for k in allm["train"]:
        lines.append(
            "| %s | %s | %s | %s | %s |"
            % (
                k,
                fmt_test(allm["train"][k]),
                fmt_test(allm["val"][k]),
                fmt_test(mech[("COORDINATED", "train")][k]),
                fmt_test(mech[("COORDINATED", "val")][k]),
            )
        )
    E.write("H_nulls.md", lines)
    res["nulls"] = {sp: allm[sp] for sp in E.SPLITS}
    # ---------------- I robustness
    top_op = {sp: Counter(r["cluster"] for r in rows if r["split"] == sp).most_common(1)[0][0] for sp in E.SPLITS}
    wcount = Counter(s["wallet"] for r in rows for s in r["snipers"])
    top10 = {w for w, _ in wcount.most_common(10)}
    key_m = {
        "shared last funder",
        "one funding transaction for 2+ snipers",
        "funding-time synchrony (spread, s)",
        "exits in one slot (share)",
        "tokens consolidated to one recipient",
        "recurring sniper pairs",
    }
    subsets: list[tuple[str, str, list[dict[str, Any]]]] = []
    for sp in E.SPLITS:
        base = [r for r in rows if r["split"] == sp]
        subsets.append(("without the dominant operator", sp, [r for r in base if r["cluster"] != top_op[sp]]))
        strip = []
        for r in base:
            sn = [s for s in r["snipers"] if s["wallet"] not in top10]
            if len(sn) >= 2:
                strip.append({**r, "snipers": sn})
        subsets.append(("without the 10 most frequent sniper wallets", sp, strip))
    lines = [
        "# I. Robustness (p of each null, %d permutations)" % E.N_PERM,
        "",
        "| subset | split | launches | " + " | ".join(sorted(key_m)) + " |",
        "|---|---|---:|" + "---|" * len(key_m),
    ]
    rob: dict[str, Any] = {}
    for name, sp, rr in subsets:
        mt = mechanisms(rr, [x for x in ret if x["split"] == sp], E.N_PERM, key_m)
        rob[(name, sp).__str__()] = {k: v.get("p") for k, v in mt.items()}
        lines.append(
            "| %s | %s | %d | %s |"
            % (
                name,
                sp.upper(),
                len(rr),
                " | ".join(
                    "%.4f (x%.2f)" % (mt[k]["p"], mt[k]["effect"] or 0) if mt[k] else "n/a" for k in sorted(key_m)
                ),
            )
        )
    for name, kind, strict in (
        ("known non-hub last funders only", "last", True),
        ("genesis funders only", "gen", False),
    ):
        for sp in E.SPLITS:
            rr = [r for r in rows if r["split"] == sp]
            fields = ("last_funder", "last_funder_hub") if kind == "last" else ("gen_funder", "gen_funder_hub")
            t = E.null_funding(rr, m_shared(kind, strict), fields)
            rob[(name, sp).__str__()] = {"shared funder": t["p"]}
            lines.append(
                "| %s: shared funder | %s | %d | observed %d, null mean %.1f, p %.4f |"
                % (name, sp.upper(), len(rr), t["obs"], t["null_mean"], t["p"])
            )
    ops = [c for c, n in Counter(r["cluster"] for r in rows).most_common() if n >= 30]
    lines += [
        "",
        "## Inside the operators with 30 launches or more (both splits pooled)",
        "",
        "| operator | launches | shared last funder | one funding tx | funding synchrony | exits in one slot |",
        "|---|---:|---|---|---|---|",
    ]
    for i, c in enumerate(ops):
        rr = [r for r in rows if r["cluster"] == c]
        mt = mechanisms(
            rr,
            [],
            E.N_PERM,
            {
                "shared last funder",
                "one funding transaction for 2+ snipers",
                "funding-time synchrony (spread, s)",
                "exits in one slot (share)",
            },
        )
        lines.append(
            "| operator %d | %d | %s |"
            % (
                i + 1,
                len(rr),
                " | ".join(
                    ("%.4g vs %.3g, p %.3f" % (mt[k]["obs"], mt[k]["null_mean"], mt[k]["p"])) if mt.get(k) else "n/a"
                    for k in (
                        "shared last funder",
                        "one funding transaction for 2+ snipers",
                        "funding-time synchrony (spread, s)",
                        "exits in one slot (share)",
                    )
                ),
            )
        )
    E.write("I_robustness.md", lines)
    res["robustness"] = rob
    # ---------------- J roles and hypotheses (counts; interpretation in results.md)
    recips = Counter(o for r in rows for s in r["snipers"] for o in E.sniper_lifecycle(r, s)["recipients"])
    recip_launch = defaultdict(set)
    for r in rows:
        for s in r["snipers"]:
            for o in E.sniper_lifecycle(r, s)["recipients"]:
                recip_launch[o].add(r["mint"])
    coll_src = defaultdict(set)
    for x in ret:
        for d in set(x["dest"]):
            coll_src[d].add(x["wallet"])
    f_ops = defaultdict(set)
    for r in rows:
        for s in r["snipers"]:
            if s.get("last_funder"):
                f_ops[s["last_funder"]].add(r["cluster"])
    lines = [
        "# J. Behavioral roles (counts and the observation behind each)",
        "",
        "| role | wallets | observation |",
        "|---|---:|---|",
        "| deployer | %d | signed the creation transaction; %d deployed 2 launches or more |"
        % (len(dep_launch), sum(1 for v in dep_launch.values() if v >= 2)),
        "| upstream funder (non-hub) | %d | sent the last SOL to 2+ snipers of one launch: %d |"
        % (
            len(fund_launch),
            len(
                {
                    f
                    for r in rows
                    for f, c in Counter(E.fkey(s) for s in r["snipers"]).items()
                    if f and not f.startswith("own:") and c >= 2
                }
            ),
        ),
        "| sniper | %d | bought 5 SOL or more in the creation slot |" % len(appear),
        "| token recipient (exit wallet) | %d | received tokens from a sniper by transfer; from 2+ snipers of one "
        "launch: %d; in 2+ launches: %d |"
        % (
            len(recips),
            len(
                {
                    o
                    for r in rows
                    for o, c in Counter(
                        o2 for s in r["snipers"] for o2 in E.sniper_lifecycle(r, s)["recipients"]
                    ).items()
                    if c >= 2
                }
            ),
            sum(1 for v in recip_launch.values() if len(v) >= 2),
        ),
        "| collection wallet | %d | received SOL from 2+ returning snipers between launches |"
        % sum(1 for v in coll_src.values() if len(v) >= 2),
        "| funding service (cross-operator funder) | %d | last funder of snipers in 3+ operator clusters (of them "
        "known hubs: %d) |"
        % (
            sum(1 for v in f_ops.values() if len(v) >= 3),
            sum(
                1
                for f, v in f_ops.items()
                if len(v) >= 3
                and any(s.get("last_funder") == f and s.get("last_funder_hub") for r in rows for s in r["snipers"])
            ),
        ),
        "| recurring infrastructure wallet | %d | the same wallet in 5+ launches in one role (sniper, funder, "
        "recipient or deployer) |"
        % len(
            {w for w, v in appear.items() if len(v) >= 5}
            | {f for f, v in fund_launch.items() if len(v) >= 5}
            | {o for o, v in recip_launch.items() if len(v) >= 5}
            | {d for d, n in dep_launch.items() if d and n >= 5}
        ),
    ]
    E.write("J_roles_hypotheses.md", lines)
    # ---------------- price impact, last and apart
    prices = E.load_prices()
    lines = [
        "# E2. Price impact of the creation slot (descriptive; read after every group and role was fixed)",
        "",
        "Prices in SOL per token. The curve's initial price is %.3e. Inside the creation slot the order of "
        "transactions is unknown, so the group's part of the jump is approximated by its share of the slot's "
        "SOL; exact attribution is not possible." % P_INIT,
        "",
        "| group | split | jump over the creation slot (x) | P0 over initial (x) | share of the move to P0 done "
        "in the slot (log) | group share of the slot's SOL | max within 10 s / 30 s / 60 s / 5 min of the "
        "creation, over P0 |",
        "|---|---|---|---|---|---|---|",
    ]
    for g, sp, rr in by_group(rows):
        jump, p0x, frac, gs, mx = [], [], [], [], {10: [], 30: [], 60: [], 300: []}
        for r in rr:
            p = prices[r["mint"]]
            st = r["slot0_states"]
            pool = [x for x in st if x.get("pool_tok")]
            if pool:
                after = max(x["pool_sol"] / x["pool_tok"] for x in pool)
            else:
                cv = [x for x in st if x.get("curve_tok") is not None and x.get("curve_lamports") is not None]
                if not cv:
                    continue
                x = min(cv, key=lambda z: z["curve_tok"])
                after = (30.0 + x["curve_lamports"]) / (73e6 + x["curve_tok"])
            jump.append(after / P_INIT)
            if p["p0"]:
                p0x.append(p["p0"] / P_INIT)

                if p["p0"] > P_INIT and after > P_INIT:
                    frac.append(min(1.5, math.log(after / P_INIT) / math.log(p["p0"] / P_INIT)))
                reads = []
                for w in p["window"]:
                    if w.get("pool_tok"):
                        reads.append((w["bt"], w["pool_sol"] / w["pool_tok"]))
                    elif w.get("curve_tok") is not None and w.get("curve_lamports") is not None:
                        reads.append((w["bt"], (30.0 + w["curve_lamports"]) / (73e6 + w["curve_tok"])))
                reads += [(p["t"] + dt, m * p["p0"]) for dt, m in p["series"]]
                for sec in mx:
                    v = [pr for bt, pr in reads if bt is not None and bt <= p["t_create"] + sec]
                    if v:
                        mx[sec].append(max(v) / p["p0"])
            tot = sum(r["slot0_sol"].values())
            if tot:
                gs.append(sum(r["slot0_sol"].get(s["wallet"], 0) for s in r["snipers"]) / tot)
        if not rr:
            continue
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s |"
            % (
                g,
                sp.upper(),
                E.dist(jump),
                E.dist(p0x),
                E.dist(frac),
                E.dist(gs),
                " ; ".join(E.dist(mx[s]).split(" /")[0] for s in (10, 30, 60, 300)),
            )
        )
    E.write("E2_price_impact.md", lines)
    with open(os.path.join(E.STUDY, "derived", "M_results.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(open(os.path.join(E.TABLES, "H_nulls.md")).read())


def short(a: str) -> str:
    return a[:6] + "..."


if __name__ == "__main__":
    main()
