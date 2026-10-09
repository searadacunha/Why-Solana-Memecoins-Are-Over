#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feat_29_swarm.py -- the swarm count A of the pre-registered rule SWARM + CHEAP ENTRY, for every
alert (features only, no outcome).

A = number of DISTINCT external wallets that bought the token with block time <= t_alert - 10 s.
  external = not a core sniper of the bundle, not the creator; buys of the creation slot excluded
  (they are the bundle); 'buy' as parsed by post_detection_forensics/fparse.py from the raw window.
Also written: the same count at t_alert - 11 s (robustness of the cut), and at t_alert - 5 s.
"""
from __future__ import annotations

import os

import ap_lib as A
from mech_40_break_the_loop import load_window


def main() -> None:
    base = A.load_base()
    cd = {}
    for r in A.jl(A.CD_TABLE):
        cd[r["mint"]] = (set(s["wallet"] for s in r["snipers"] if s.get("role") == "core"), (r.get("creator") or {}).get("wallet"), r["slot0"])
    rows = []
    for b in base:
        m = b["mint"]
        core, cr, slot0 = cd[m]
        w, recs, facts = load_window(m)
        ext = core | ({cr} if cr else set())
        first = {}
        for r in sorted((r for r in recs if r.get("kind") == "buy" and not r.get("err") and r.get("trader")
                         and r["trader"] not in ext and r["slot"] != slot0), key=lambda r: (r["slot"], r.get("bt") or 0)):
            first.setdefault(r["trader"], (r.get("bt") or 0) - b["t"])
        rows.append({"mint": m, "swarm_10s": sum(1 for v in first.values() if v <= -10),
                     "swarm_11s": sum(1 for v in first.values() if v <= -11),
                     "swarm_5s": sum(1 for v in first.values() if v <= -5)})
    A.write_jl(os.path.join(A.DERIVED, "feat_swarm.jsonl.gz"), rows)
    print("written", len(rows), "alerts")


if __name__ == "__main__":
    main()
