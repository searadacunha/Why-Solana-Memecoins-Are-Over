#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coverage audit of the sniper-capital study, before any analysis (the brief's sections 5 and 15).

One record per sniper and launch: the wallets that bought 5 SOL or more on the curve in the
creation slot (the detector's tickets, the creator's own buy included at 5 SOL or more). For
every variable of the brief, its status from the data already collected:
  OBSERVED  computed exactly from what is in the windows and wallet files;
  PARTIAL   only a bound is known (the history goes past what was fetched);
  MISSING   nothing usable.
No label is read. Then the cost of completing each variable, in RPC calls, deduplicated per
wallet. Writes coverage.md and derived/sc_coverage.json.

Sources, read only: post_detection_forensics/data/onchain_cache (windows: the buy transaction
itself, with the sniper's balance before and after; wallet files: the 1,000 signatures before
the buy, with their times only, the 5 most recent transactions with SOL deltas (20 for the
creator), the genesis funding when the history is shorter than 1,000 transactions, and the
funders' own genesis before their first funding in the corpus).
"""

from __future__ import annotations

import gzip
import json
import os
import sys
import time
from collections import Counter, defaultdict
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "post_detection_forensics", "code"))
import feat_30_build as FB  # noqa: E402
import fparse  # noqa: E402

pde = FB.pde
WINDOWS = {"1h": 3600, "6h": 6 * 3600, "24h": 86400, "7d": 7 * 86400}
CALLS_PER_S = 14.0  # measured on the collections of 2026-09-29 and 30, three keys
STATUSES = ("OBSERVED", "PARTIAL", "MISSING")


def system_inflow(t: dict[str, Any], wallet: str) -> float:
    """SOL sent to `wallet` by System transfers inside one transaction."""
    s = 0.0
    for ix in fparse._instructions(t):
        p = ix.get("parsed") or {} if ix.get("program") == "system" else {}
        info = p.get("info") or {}
        if (
            p.get("type") in ("transfer", "transferWithSeed")
            and info.get("destination") == wallet
            and info.get("source") != wallet
        ):
            s += int(info.get("lamports") or 0) / 1e9
    return s


def sniper_records(a: dict[str, Any]) -> list[dict[str, Any]]:
    w = json.load(gzip.open(os.path.join(FB.WIN, a["mint"] + ".json.gz"), "rt"))
    wal = json.load(gzip.open(os.path.join(FB.WAL, a["mint"] + ".json.gz"), "rt"))
    recs, _ = fparse.parse_window(w)
    slot0 = recs[0]["slot"]
    buys: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in recs:
        if r["slot"] == slot0 and not r.get("err") and r.get("venue") == "curve" and r.get("kind") in ("buy", "create"):
            for o, v in (r.get("leg_sol") or {}).items():
                if v > 0:
                    buys[o].append({"sig": r["sig"], "sol": v, "bt": r.get("bt"), "kind": r["kind"]})
    core = {k for k, v in wal["wallets"].items() if v["role"] == "core"}
    creator = next((k for k, v in wal["wallets"].items() if v["role"] == "creator"), None)
    snipers = [m for m in buys if m in core or (m == creator and sum(b["sol"] for b in buys[m]) >= FB.CORE_MIN_SOL)]
    out = []
    for m in snipers:
        bl = buys[m]
        ticket = sum(b["sol"] for b in bl)
        t_buy = min(b["bt"] for b in bl if b["bt"]) if any(b["bt"] for b in bl) else None
        pre, post, inflow, in_keys = [], [], 0.0, True
        for b in bl:
            t = w["txs"].get(b["sig"])
            keys = [k["pubkey"] for k in t["transaction"]["message"]["accountKeys"]] if t else []
            if m not in keys:
                in_keys = False
                continue
            i = keys.index(m)
            pre.append(t["meta"]["preBalances"][i] / 1e9)
            post.append(t["meta"]["postBalances"][i] / 1e9)
            inflow += system_inflow(t, m)
        v = wal["wallets"].get(m) or {}
        pr = v.get("prior") or {}
        n = pr.get("n", 0)
        k_fetch = 20 if v.get("role") == "creator" else 5
        rc = v.get("recent") or []
        g = (v.get("genesis") or {}).get("funding") or {}
        out.append(
            {
                "mint": a["mint"],
                "t": a["t"],
                "wallet": m,
                "role": v.get("role"),
                "ticket": ticket,
                "t_buy": t_buy,
                "pre": max(pre) if pre and in_keys else None,
                "post": min(post) if post and in_keys else None,
                "inflow_in_tx": inflow,
                "n_prior": n,
                "capped": n >= 1000,
                "bts": pr.get("bts") or [],
                "recent": rc,
                "recent_null": max(0, min(n, k_fetch) - len(rc)),
                "k_fetch": k_fetch,
                "genesis_bt": g.get("bt"),
                "genesis_funder": g.get("funder"),
                "genesis_received": g.get("received"),
            }
        )
    return out


def status(r: dict[str, Any]) -> dict[str, str]:
    """Status of every variable of the brief for one sniper record."""
    m, n, rc = r["wallet"], r["n_prior"], r["recent"]
    full = n <= len(rc)  # the whole history before the buy is in `recent`
    oldest = min((x["bt"] for x in rc if x.get("bt")), default=None)
    t = r["t_buy"] or r["t"]
    st: dict[str, str] = {}
    st["capital_before_buy"] = "OBSERVED" if r["pre"] is not None else "MISSING"
    st["capital_after_buy"] = "OBSERVED" if r["post"] is not None else "MISSING"
    st["ticket"] = "OBSERVED"
    for lab, h in WINDOWS.items():
        if full or (oldest is not None and oldest < t - h):
            st["funding_" + lab] = "OBSERVED"
        elif rc:
            st["funding_" + lab] = "PARTIAL"
        else:
            st["funding_" + lab] = "MISSING"
    fund = [x for x in rc if (x.get("d") or {}).get(m, 0) > 0 and not x.get("err") and x.get("signer") != m]
    st["time_since_last_funding"] = (
        "OBSERVED" if (fund or (full and r["genesis_bt"])) else ("PARTIAL" if rc else "MISSING")
    )
    st["balance_before_recent_funding"] = (
        "OBSERVED" if fund and r["pre"] is not None else ("PARTIAL" if rc else "MISSING")
    )
    st["sol_spent_history"] = "OBSERVED" if full else ("PARTIAL" if n < 1000 else "MISSING")
    st["n_history_tx"] = "OBSERVED" if n < 1000 else "PARTIAL"
    st["n_history_trades"] = "OBSERVED" if full else "MISSING"
    st["wallet_age"] = "OBSERVED" if (n < 1000 and r["genesis_bt"]) else "PARTIAL"
    gf = r["genesis_funder"]
    st["genesis_funder"] = "OBSERVED" if gf else "MISSING"
    hop = FB._hop(gf, False) if gf else None
    st["funder_of_funder"] = (
        "OBSERVED" if hop and ((hop.get("funding") or {}).get("funder") or hop.get("hub_before_cursor")) else "MISSING"
    )
    return st


def needed_calls(recs: list[dict[str, Any]], what: str) -> tuple[int, int, int]:
    """(getTransaction, getSignaturesForAddress, pairs left unknown even after: history past the page cap)
    to complete `what` for every non-OBSERVED record, transactions deduplicated per wallet by time."""
    per_wallet: dict[str, Counter] = defaultdict(Counter)
    pages = 0
    unknown = 0
    for r in recs:
        if status(r)[what] == "OBSERVED":
            continue
        t = r["t_buy"] or r["t"]
        if what.startswith("funding_") or what in ("time_since_last_funding", "balance_before_recent_funding"):
            h = WINDOWS.get(what.split("_", 1)[1], WINDOWS["24h"]) if what.startswith("funding_") else WINDOWS["24h"]
            need = Counter(b for b in r["bts"][r["k_fetch"] :] if b and b >= t - h)
            if r["capped"] and r["bts"] and min(b for b in r["bts"] if b) >= t - h:
                unknown += 1  # the 1,000 fetched signatures do not reach back that far
                pages += 1
        else:  # the whole history
            need = Counter(b for b in r["bts"][r["k_fetch"] :] if b)
            if r["capped"]:
                unknown += 1
                pages += 1
        cur = per_wallet[r["wallet"]]
        for b, c in need.items():
            cur[b] = max(cur[b], c)
    return sum(sum(c.values()) for c in per_wallet.values()), pages, unknown


def main() -> None:
    alerts = sorted((a for a in pde.load_journal() if a["genre"] == "alerte_lancement"), key=lambda a: a["t"])
    t_val = pde.utc("2026-09-15 00:00:00")
    recs: list[dict[str, Any]] = []
    for a in alerts:
        recs += sniper_records(a)
    sts = [status(r) for r in recs]
    variables = list(sts[0])
    split = ["train" if r["t"] < t_val else "val" for r in recs]
    lines = [
        "# Coverage of the sniper-capital variables, before any analysis",
        "",
        "One record per sniper and launch: %d records, %d distinct wallets, %d launches. Snipers = the "
        "detector's tickets (5 SOL or more on the curve in the creation slot, the creator's own buy included). "
        "No label was read to build this file."
        % (len(recs), len({r["wallet"] for r in recs}), len({r["mint"] for r in recs})),
        "",
        "## Per variable, sniper records",
        "",
        "| variable | OBSERVED | PARTIAL | MISSING | OBSERVED, TRAIN / VALIDATION |",
        "|---|---:|---:|---:|---|",
    ]
    out: dict[str, Any] = {"records": len(recs), "variables": {}}
    for v in variables:
        c = Counter(s[v] for s in sts)
        ct = Counter(s[v] for s, sp in zip(sts, split) if sp == "train")
        cv = Counter(s[v] for s, sp in zip(sts, split) if sp == "val")
        nt, nv = sum(ct.values()), sum(cv.values())
        lines.append(
            "| %s | %.1f %% | %.1f %% | %.1f %% | %.1f %% / %.1f %% |"
            % (v, *(100 * c[x] / len(sts) for x in STATUSES), 100 * ct["OBSERVED"] / nt, 100 * cv["OBSERVED"] / nv)
        )
        out["variables"][v] = {x: c[x] for x in STATUSES}
    # launch level: every sniper of the launch OBSERVED
    by_launch: dict[str, list[dict[str, str]]] = defaultdict(list)
    sp_of = {}
    for r, s, sp in zip(recs, sts, split):
        by_launch[r["mint"]].append(s)
        sp_of[r["mint"]] = sp
    lines += [
        "",
        "## Per variable, launches whose every sniper is OBSERVED",
        "",
        "| variable | all launches | TRAIN | VALIDATION |",
        "|---|---:|---:|---:|",
    ]
    nl = Counter(sp_of.values())
    for v in variables:
        ok = {m for m, ss in by_launch.items() if all(s[v] == "OBSERVED" for s in ss)}
        lines.append(
            "| %s | %d (%.0f %%) | %d | %d |"
            % (
                v,
                len(ok),
                100 * len(ok) / len(by_launch),
                sum(1 for m in ok if sp_of[m] == "train"),
                sum(1 for m in ok if sp_of[m] == "val"),
            )
        )
    # temporal bias
    lines += [
        "",
        "## Temporal bias: share of sniper records OBSERVED, by week",
        "",
        "| week from | records | capital before buy | funding 1h | funding 24h | funding 7d | whole history |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    wk: dict[int, list[dict[str, str]]] = defaultdict(list)
    wk_utc: dict[int, str] = {}
    for r, s in zip(recs, sts):
        k = int(r["t"] // (7 * 86400))
        wk[k].append(s)
        wk_utc[k] = min(wk_utc.get(k, "9"), time.strftime("%Y-%m-%d", time.gmtime(r["t"])))
    for k in sorted(wk):
        ss = wk[k]

        def sh(v: str) -> str:
            return "%.0f %%" % (100 * sum(1 for s in ss if s[v] == "OBSERVED") / len(ss))

        lines.append(
            "| %s | %d | %s | %s | %s | %s | %s |"
            % (
                wk_utc[k],
                len(ss),
                sh("capital_before_buy"),
                sh("funding_1h"),
                sh("funding_24h"),
                sh("funding_7d"),
                sh("sol_spent_history"),
            )
        )
    # who is missing: fresh against seasoned wallets
    lines += ["", "## Who is incomplete", ""]
    for lab, cond in (
        ("history of 5 transactions or fewer", lambda r: r["n_prior"] <= 5),
        ("6 to 99", lambda r: 5 < r["n_prior"] < 100),
        ("100 to 999", lambda r: 100 <= r["n_prior"] < 1000),
        ("1,000 or more (capped)", lambda r: r["n_prior"] >= 1000),
    ):
        sel = [(r, s) for r, s in zip(recs, sts) if cond(r)]
        lines.append(
            "- %s before the buy: %d records (%.0f %%), funding 24h OBSERVED for %.0f %% of them."
            % (
                lab,
                len(sel),
                100 * len(sel) / len(recs),
                100 * sum(1 for _, s in sel if s["funding_24h"] == "OBSERVED") / max(1, len(sel)),
            )
        )
    # reconstruction problems
    pre_below = sum(1 for r in recs if r["pre"] is not None and r["pre"] < r["ticket"])
    inflow = sum(1 for r in recs if r["inflow_in_tx"] > 0)
    nulls = sum(r["recent_null"] for r in recs)
    lines += [
        "",
        "## Transactions that could not be reconstructed, and traps",
        "",
        "- Earlier transactions returned null by the RPC and skipped by the collector: %d (out of %d asked)."
        % (nulls, sum(min(r["n_prior"], r["k_fetch"]) for r in recs)),
        "- Records whose balance before the buy is below the ticket: %d; records funded by a transfer inside "
        "the buy transaction itself: %d. For them the balance before the transaction is not the capital "
        "used; the transfer inside the transaction has to be added." % (pre_below, inflow),
        "- Wrapped SOL is not in the native balance; a sniper paying with it would look poorer than it is.",
    ]
    # costs
    lines += [
        "",
        "## Cost of completing each variable",
        "",
        "Calls deduplicated per wallet (a wallet sniping several launches shares its history). Time at %d "
        "calls per second (three keys, measured), on the Helius budget the live detector also uses." % CALLS_PER_S,
        "",
        "| variable | getTransaction | getSignaturesForAddress pages | records still unbounded | time |",
        "|---|---:|---:|---:|---:|",
    ]
    out["costs"] = {}
    for v in ("funding_1h", "funding_6h", "funding_24h", "funding_7d", "sol_spent_history", "n_history_trades"):
        tx, pages, unk = needed_calls(recs, v if v != "n_history_trades" else "sol_spent_history")
        hours = (tx + pages) / CALLS_PER_S / 3600
        out["costs"][v] = {"getTransaction": tx, "pages": pages, "unbounded": unk, "hours": hours}
        lines.append("| %s | %s | %s | %d | %.1f h |" % (v, format(tx, ","), format(pages, ","), unk, hours))
    lines += [
        "",
        '"Unbounded": the 1,000 signatures fetched before the buy do not reach back that far, so '
        "the count above is a floor and more pages are needed for those records.",
    ]
    os.makedirs(os.path.join(STUDY, "derived"), exist_ok=True)
    with open(os.path.join(STUDY, "coverage.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")
    out["pre_below_ticket"], out["inflow_in_tx"], out["null_recent"] = pre_below, inflow, nulls
    out["launches_by_split"] = dict(nl)
    with open(os.path.join(STUDY, "derived", "sc_coverage.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
