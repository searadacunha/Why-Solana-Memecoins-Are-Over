#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inventory for the funder-network study, before any flow is read.

Population (frozen, exit_destination table sha256 c09b0e77...): the 62 distinct recipients of the 1,280 sweeps,
with the labels of that study: H1 funder (the launch's own non-hub funder in at least one sweep, 42), collector
(the recipient was not the launch's funder in at least one sweep, 20; 3 wallets carry both labels), and launch
funder classified as a hub by the activity rule (3). Operators are the frozen `cluster` labels.

What the corpus already holds for each wallet: sweeps received in the exit sample, sniper and deployer fundings
in the frozen tables, signature pages cached by the exit study.

--probe (online): one page of up to 1,000 signatures strictly before the wallet's last sweep in the sample, to
measure its activity in the study period (counts and timestamps only, no transaction is read). Cached under
funder_network/data/cache. This is the only use of the network before the protocol is frozen.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "exit_destination", "code"))
import ed_lib  # noqa: E402

ed_lib.CACHE = os.path.join(STUDY, "data", "cache")
import ed_30_analysis as A  # noqa: E402
import ed_trace as T  # noqa: E402

TEST_START = 1790680980  # 2026-09-29 11:23 UTC: the future TEST begins, nothing after it is read
OUT = os.path.join(STUDY, "derived", "inventory.json")


def population(D: A.Data) -> dict[str, dict[str, Any]]:
    def raw_funders(m: str) -> set[str]:
        return {s.get("last_funder") for s in D.byrow[m]["snipers"]} - {None}

    pop: dict[str, dict[str, Any]] = {}
    for e in D.obs:
        for b in e["branches"]:
            w = b["path"][1]["wallet"]
            p = pop.setdefault(w, {"wallet": w, "labels": set(), "sweeps": [], "operators": set(), "launches": set()})
            if b["terminal"] == "H1":
                p["labels"].add("H1 funder")
            if w not in raw_funders(e["mint"]):
                p["labels"].add("collector")
            elif b["terminal"] != "H1":
                p["labels"].add("launch funder classified hub")
            p["sweeps"].append(
                {
                    "sig": b["path"][1]["sig"],
                    "slot": b["path"][1]["slot"],
                    "bt": b["path"][1]["bt"],
                    "sol": b["path"][1]["sol"],
                    "mint": e["mint"],
                    "exit_wallet": e["wallet"],
                    "operator": e["cluster"],
                    "split": e["split"],
                }
            )
            p["operators"].add(e["cluster"])
            p["launches"].add(e["mint"])
    fund: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in D.rows:
        for s in r["snipers"]:
            if s.get("last_funder"):
                fund[s["last_funder"]].append(
                    {
                        "role": "sniper",
                        "mint": r["mint"],
                        "bt": s.get("last_bt"),
                        "operator": r["cluster"],
                        "sig": s.get("last_sig"),
                    }
                )
        cr = r["creator"]
        if cr.get("last_funder"):
            fund[cr["last_funder"]].append(
                {
                    "role": "deployer",
                    "mint": r["mint"],
                    "bt": cr.get("last_bt"),
                    "operator": r["cluster"],
                    "sig": cr.get("last_sig"),
                }
            )
    for w, p in pop.items():
        p["fundings"] = fund.get(w, [])
        p["sweeps"].sort(key=lambda x: x["slot"])
        p["labels"] = sorted(p["labels"])
        p["operators"] = sorted(p["operators"])
        p["launches"] = sorted(p["launches"])
    return pop


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    D = A.Data()
    pop = population(D)
    lab = defaultdict(int)
    for p in pop.values():
        lab[" + ".join(p["labels"])] += 1
    print("population %d wallets: %s" % (len(pop), dict(lab)))
    F = T.Fetch(online=a.probe)
    for w, p in sorted(pop.items()):
        last = max(p["sweeps"], key=lambda x: x["slot"])
        try:
            page = F.page(w, before=last["sig"])
        except T.NotCollected:
            page = None
        p["probe"] = None
        if page is not None:
            bts = [x["bt"] for x in page if x["bt"]]
            span = (max(bts) - min(bts)) if len(bts) >= 2 else None
            p["probe"] = {
                "n": len(page),
                "span_s": span,
                "end": len(page) < 1000,
                "rate_per_day": len(page) / (span / 86400) if span else None,
                "oldest_bt": min(bts) if bts else None,
            }
    F.save()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump({"test_start": TEST_START, "population": pop, "calls": F.state}, fh, indent=1, sort_keys=True)
    for w, p in sorted(pop.items(), key=lambda x: -len(x[1]["sweeps"])):
        pr = p["probe"] or {}
        print(
            "%s %-40s sweeps %3d fundings %3d ops %d probe n %s span %.2f d rate/day %s"
            % (
                w[:8],
                "+".join(p["labels"]),
                len(p["sweeps"]),
                len(p["fundings"]),
                len(p["operators"]),
                pr.get("n"),
                (pr.get("span_s") or 0) / 86400,
                "%.0f" % pr["rate_per_day"] if pr.get("rate_per_day") else "-",
            )
        )
    print("calls", F.state)


if __name__ == "__main__":
    main()
