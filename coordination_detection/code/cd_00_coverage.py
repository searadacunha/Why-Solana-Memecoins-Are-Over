#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1 of the protocol: what the collected data cover for the coordination study, before any plan
or rate. Counts of OBSERVED / MISSING per variable, for the snipers, the creator and the early
buyers, and the cost of what is missing. No coordination measure and no label is computed here.

Sources, read only: post_detection_forensics/data/onchain_cache (windows from the creation slot to
alert + 30 s, wallet files) through sniper_capital/code/sc_00_coverage.sniper_records.
Writes coverage.md.
"""

from __future__ import annotations

import gzip
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "sniper_capital", "code"))
import sc_00_coverage as SC  # noqa: E402

FB, fparse, pde = SC.FB, SC.fparse, SC.pde


def main() -> None:
    alerts = sorted((a for a in pde.load_journal() if a["genre"] == "alerte_lancement"), key=lambda a: a["t"])
    c: Counter = Counter()
    for a in alerts:
        snipers = SC.sniper_records(a)
        wal = json.load(gzip.open(os.path.join(FB.WAL, a["mint"] + ".json.gz"), "rt"))
        w = json.load(gzip.open(os.path.join(FB.WIN, a["mint"] + ".json.gz"), "rt"))
        recs, _ = fparse.parse_window(w)
        c["launches"] += 1
        sn_w = {s["wallet"] for s in snipers}
        for s in snipers:
            c["snipers"] += 1
            c["sniper_buy_time"] += s["t_buy"] is not None
            gf = s["genesis_funder"] if s["n_prior"] < 1000 else None
            c["sniper_genesis_funder"] += bool(gf)
            hop = FB._hop(gf, False) if gf else None
            c["sniper_source"] += bool(
                hop and ((hop.get("funding") or {}).get("funder") or hop.get("hub_before_cursor"))
            )
            fund = [
                x
                for x in s["recent"]
                if (x.get("d") or {}).get(s["wallet"], 0) > 0 and not x.get("err") and x.get("signer") != s["wallet"]
            ]
            c["sniper_last_funder"] += bool(fund)
        cr = next((v for v in wal["wallets"].values() if v["role"] == "creator"), None)
        if cr:
            c["creator"] += 1
            g = (cr.get("genesis") or {}).get("funding") or {}
            c["creator_genesis_funder"] += bool(g.get("funder")) and cr["prior"]["n"] < 1000
            m = next(k for k, v in wal["wallets"].items() if v is cr)
            c["creator_last_funder"] += any(
                (x.get("d") or {}).get(m, 0) > 0 and not x.get("err") and x.get("signer") != m
                for x in cr.get("recent") or []
            )
        early = {k: v for k, v in wal["wallets"].items() if v["role"] == "early"}
        for k, v in early.items():
            c["early"] += 1
            g = (v.get("genesis") or {}).get("funding") or {}
            c["early_genesis_funder"] += bool(g.get("funder")) and v["prior"]["n"] < 1000
            c["early_capped"] += v["prior"]["n"] >= 1000
        exits = {
            o
            for r in recs
            for o, x in (r.get("legs") or {}).items()
            if o in sn_w and x < 0 and (r.get("bt") or 0) <= a["t"] + 30
        }
        c["sniper_exit_in_window"] += len(exits)
    lines = [
        "# Coverage of the coordination variables, before the plan",
        "",
        "%d launches, %d sniper records (the detector's tickets), %d early buyers (the first 25 buyers "
        "outside the bundle up to alert - 1 s). No coordination measure was computed for this file."
        % (c["launches"], c["snipers"], c["early"]),
        "",
        "| variable | OBSERVED | of |",
        "|---|---:|---:|",
    ]
    for k, of in (
        ("sniper_buy_time", "snipers"),
        ("sniper_genesis_funder", "snipers"),
        ("sniper_source", "snipers"),
        ("sniper_last_funder", "snipers"),
        ("creator_genesis_funder", "creator"),
        ("creator_last_funder", "creator"),
        ("early_genesis_funder", "early"),
    ):
        lines.append("| %s | %d (%.1f %%) | %d |" % (k, c[k], 100 * c[k] / c[of], c[of]))
    lines += [
        "| tickets, buy slots and times, wallet identities (snipers and early buyers) | 100 % | |",
        "| sniper exits (sell or transfer out) up to alert + 30 s | observed inside the window | |",
        "| anything after alert + 30 s | 0 | |",
        "",
        "## Missing, and what it would cost",
        "",
        "- Early buyers' funders: %.0f %% of them have 1,000 earlier transactions or more; their genesis needs "
        "their whole history, unbounded for seasoned bots. Not collectable at a known cost."
        % (100 * c["early_capped"] / c["early"]),
        "- Genesis funder of the snipers with 1,000 transactions or more (%.1f %%): unbounded as well; their "
        "last funder is OBSERVED for %.1f %% of all snipers."
        % (100 * (1 - c["sniper_genesis_funder"] / c["snipers"]), 100 * c["sniper_last_funder"] / c["snipers"]),
        "- Sells after alert + 30 s: one signature page per sniper after its buy, then its transactions up "
        "to the exit: at least %d calls (%d snipers x about 4), more for wallets active afterwards."
        % (4 * c["snipers"], c["snipers"]),
        "",
        "None of them is needed for the main question (coordination observable at the launch); the sells "
        "are a secondary, descriptive section. No collection is launched.",
    ]
    with open(os.path.join(STUDY, "coverage.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
