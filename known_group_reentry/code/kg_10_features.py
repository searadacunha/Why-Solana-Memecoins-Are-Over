#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The feature table of analysis_plan.md sections 1-3, built chronologically: for each alert, only earlier alerts
whose window closed at least 60 s before it (t_j + 60 <= t_i) feed its group features. The current alert
contributes only what is known at its own alert: its snipers, their tickets, their pre-buy funders. Its exits,
its `between` record and anything after the alert are never read.

No price outcome is read: an audit hook refuses the price series and the price file, and the post-detection-edge
rows are stripped of their `targets` on load (only the live features `f`, P0 and the operator label are kept).
Writes derived/kg_features.jsonl.gz and derived/KG_FREEZE.json (sha256), then the integrity checks.
"""

from __future__ import annotations

import gzip
import hashlib
import itertools
import json
import os
import sys
from collections import defaultdict
from typing import Any

FORBIDDEN = ("series.txt", "em_price")


def _audit(event: str, args: tuple[Any, ...]) -> None:
    if event == "open" and args and isinstance(args[0], str) and any(f in args[0] for f in FORBIDDEN):
        raise RuntimeError("a price file was opened by the group builder: %s" % args[0])


sys.addaudithook(_audit)

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "economic_mechanics", "code"))
import em_lib as E  # noqa: E402

PDE = os.path.join(ROOT, "post_detection_edge", "derived")
OUT = os.path.join(STUDY, "derived", "kg_features.jsonl.gz")
FREEZE = os.path.join(STUDY, "derived", "KG_FREEZE.json")
T_VAL = 1789430400  # 2026-09-15 00:00 UTC
CLOSE = 60.0
BASE = (
    "n_snipers",
    "snipe_sol",
    "supply_part",
    "log10_mc_usd",
    "entry_over_operator",
    "p0_source",
    "paquet_max",
    "actor",
)


def live_rows() -> dict[str, dict[str, Any]]:
    out = {}
    for name in ("dataset_dev.jsonl.gz", "dataset_test.sealed.jsonl.gz"):
        for line in gzip.open(os.path.join(PDE, name), "rt", encoding="utf8"):
            r = json.loads(line)
            out[r["mint"]] = {
                "mint": r["mint"],
                "t": r["t"],
                "p0": r["p0"],
                "fine": r["fine"],
                "has_series": r["has_series"],
                "operator": r["cluster"],
                "f": {k: r["f"].get(k) for k in BASE},
            }
    return out


def depth_bin(n: int) -> str:
    return "0" if n == 0 else "1" if n == 1 else "2-5" if n <= 5 else ">5"


def recency_bin(s: float | None) -> str | None:
    if s is None:
        return None
    m = s / 60
    return (
        "<5m"
        if m < 5
        else "5-15m"
        if m < 15
        else "15-30m"
        if m < 30
        else "30-60m"
        if m < 60
        else "1-6h"
        if m < 360
        else ">6h"
    )


def main() -> None:
    rows = sorted(E.load(), key=lambda r: (r["t"], r["mint"]))
    live = live_rows()
    sn_launch: dict[str, list[tuple[float, str]]] = defaultdict(list)
    pair_launch: dict[tuple[str, str], list[tuple[float, str]]] = defaultdict(list)
    fund_launch: dict[str, list[tuple[float, str]]] = defaultdict(list)
    fund_launch_strict: dict[str, list[tuple[float, str]]] = defaultdict(list)
    exit_senders: dict[str, list[tuple[float, str]]] = defaultdict(list)
    added = 0
    out = []
    for r in rows:
        t = r["t"]
        while added < len(rows) and rows[added]["t"] + CLOSE <= t:  # history: windows closed before t
            j = rows[added]
            ws = sorted({s["wallet"] for s in j["snipers"]})
            for w in ws:
                sn_launch[w].append((j["t"], j["mint"]))
            for a, b in itertools.combinations(ws, 2):
                pair_launch[(a, b)].append((j["t"], j["mint"]))
            for s in j["snipers"]:
                f = s.get("last_funder")
                if f and s.get("last_funder_hub") is not True:
                    fund_launch[f].append((j["t"], j["mint"]))
                if f and s.get("last_funder_hub") is False:
                    fund_launch_strict[f].append((j["t"], j["mint"]))
                if any(x["kind"] == "transfer" for x in s["exits_full"]):
                    exit_senders[s["wallet"]].append((j["t"], j["mint"]))
            added += 1
        ws = sorted({s["wallet"] for s in r["snipers"]})
        group = {m: tt for (a, b) in itertools.combinations(ws, 2) for tt, m in pair_launch.get((a, b), [])}
        seen = [w for w in ws if sn_launch.get(w)]
        funders = defaultdict(set)
        funders_strict = defaultdict(set)
        for s in r["snipers"]:
            f = s.get("last_funder")
            if f and s.get("last_funder_hub") is not True:
                funders[f].add(s["wallet"])
            if f and s.get("last_funder_hub") is False:
                funders_strict[f].add(s["wallet"])
        rec_funder = any(len(v) >= 2 and fund_launch.get(f) for f, v in funders.items())
        rec_funder_strict = any(len(v) >= 2 and fund_launch_strict.get(f) for f, v in funders_strict.items())
        any_funder_seen = any(fund_launch.get(f) for f in funders)
        g1 = "KNOWN" if group else ("PARTIAL" if (seen or any_funder_seen) else "UNKNOWN")
        g3 = g1 == "KNOWN" and rec_funder
        stab = (
            "strong" if g3 else "medium" if g1 == "KNOWN" else "weak" if (len(seen) == 1 and not rec_funder) else None
        )
        last_group = max(group.values()) if group else None
        lv = live[r["mint"]]
        out.append(
            {
                "mint": r["mint"],
                "t": t,
                "split": "train" if t < T_VAL else "val",
                "operator": lv["operator"],
                "p0": lv["p0"],
                "fine": lv["fine"],
                "has_series": lv["has_series"],
                "f": lv["f"],
                "n_snipers_em": len(ws),
                "G1": g1,
                "G2": rec_funder,
                "G2_strict": rec_funder_strict,
                "G3": g3,
                "G4": any(exit_senders.get(w) for w in ws),
                "prior_group_launches": len(group),
                "depth": depth_bin(len(group)),
                "sniper_prior_max": max((len(sn_launch.get(w, [])) for w in ws), default=0),
                "snipers_seen": len(seen),
                "since_group_s": (t - last_group) if last_group else None,
                "recency": recency_bin((t - last_group) if last_group else None),
                "one_funder_2plus": any(len(v) >= 2 for v in funders.values()),
                "stability": stab,
                "history_latest_t": rows[added - 1]["t"] if added else None,
            }
        )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    raw = "".join(json.dumps(x, sort_keys=True) + "\n" for x in out).encode()
    with open(OUT, "wb") as fh:
        fh.write(gzip.compress(raw, mtime=0))
    # integrity
    fails = {}
    bad = [x["mint"] for x in out if x["history_latest_t"] is not None and x["history_latest_t"] + CLOSE > x["t"]]
    if bad:
        fails["history alert closer than 60 s to the decision"] = bad[:5]
    if len({x["mint"] for x in out}) != len(out):
        fails["duplicate mint"] = True
    split_n = {s: sum(1 for x in out if x["split"] == s) for s in ("train", "val")}
    if split_n != {"train": 1015, "val": 642}:
        fails["split counts"] = split_n
    doc = {
        "sha256_features": hashlib.sha256(open(OUT, "rb").read()).hexdigest(),
        "rows": len(out),
        "splits": split_n,
        "integrity_failures": fails,
    }
    json.dump(doc, open(FREEZE, "w"), indent=1, sort_keys=True)
    print(json.dumps(doc, indent=1))
    from collections import Counter

    for sp in ("train", "val"):
        xs = [x for x in out if x["split"] == sp]
        print(
            sp,
            "G1",
            dict(Counter(x["G1"] for x in xs)),
            "G2",
            sum(x["G2"] for x in xs),
            "G3",
            sum(x["G3"] for x in xs),
            "G4",
            sum(x["G4"] for x in xs),
            "depth",
            dict(Counter(x["depth"] for x in xs)),
        )


if __name__ == "__main__":
    main()
