#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The study table, rebuilt offline from the cache with the collection's own reading (ed_10_collect.run with an
offline Fetch), frozen by sha256, then the integrity checks of analysis_plan.md section 9. Failures are written
to derived/ED_INTEGRITY.json and printed; nothing is repaired.

An audit hook refuses any opening of a price file during the build.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from typing import Any


def _no_price(event: str, args: tuple[Any, ...]) -> None:
    if event == "open" and args and isinstance(args[0], str) and "em_price" in args[0]:
        raise RuntimeError("a price file was opened: %s" % args[0])


sys.addaudithook(_no_price)

import ed_10_collect as C  # noqa: E402
import ed_lib as L  # noqa: E402
import ed_trace as T  # noqa: E402
import em_lib as E  # noqa: E402

TABLE = os.path.join(L.DERIVED, "ed_table.json.gz")
FREEZE = os.path.join(L.DERIVED, "ED_FREEZE.json")
INTEGRITY = os.path.join(L.DERIVED, "ED_INTEGRITY.json")
B58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def integrity(out: dict[str, Any], R: T.Roles, sel: dict[str, Any]) -> dict[str, Any]:
    fails: dict[str, list[Any]] = defaultdict(list)
    evmeta = {(e["wallet"], e["mint"]): e for e in sel["events"]}
    # signatures unique inside each event window and each wallet's listing
    for w in out["wallets"]:
        for tr in w["events"]:
            s = [f["sig"] for f in tr.get("reads", [])]
            if len(s) != len(set(s)):
                fails["duplicate signature in an event window"].append((tr["wallet"], tr["mint"]))
    # addresses and mints well formed
    for w in out["wallets"]:
        for tr in w["events"]:
            for a in (tr["wallet"], tr["mint"]):
                if not B58.match(a):
                    fails["malformed address or mint"].append(a)
            for f in tr.get("reads", []):
                for d, _ in f["out"]:
                    if not B58.match(d):
                        fails["malformed address or mint"].append(d)
    for b in out["branches"]:
        for p in b["path"]:
            if not B58.match(p["wallet"]):
                fails["malformed address or mint"].append(p["wallet"])
    # token amounts: the tracked balance never negative and consistent with the summed changes
    for w in out["wallets"]:
        for tr in w["events"]:
            m = tr["mint"]
            for f in tr.get("reads", []):
                if any(v < -1e-6 for v in f["post_tok"].values()):
                    fails["negative token balance"].append(f["sig"])
            if tr.get("reads") and "held_end" in tr:
                ch = sum(f["dtok"].get(m, 0.0) for f in tr["reads"])
                start = evmeta[(tr["wallet"], m)]["tokens"]
                if tr["held_end"] > 0 and abs(start + ch - tr["held_end"]) > max(1.0, 0.01 * tr["max_held"]):
                    fails["token balance differs from receipt plus changes (receipts of several snipers)"].append(
                        (tr["wallet"], m, round(start + ch), round(tr["held_end"]))
                    )
    # SOL: the recipient's gain matches the wallet's loss (a gap means several recipients in one transaction)
    for w in out["wallets"]:
        for tr in w["events"]:
            for f in tr.get("reads", []):
                if f["out"] and f.get("out_gain") is not None and abs(f["out"][0][1] - f["out_gain"]) > 0.01:
                    fails["recipient's gain differs from the wallet's SOL loss"].append(
                        (f["sig"], round(f["out"][0][1], 4), round(f["out_gain"], 4))
                    )
    # times in order along each path; one transfer never in two branches of one event; transfers shared by events
    seen: dict[tuple[str, str, str], set[tuple[str, str]]] = defaultdict(set)
    for b in out["branches"]:
        bts = [p["bt"] for p in b["path"][1:]]
        if any(bts[i] > bts[i + 1] for i in range(len(bts) - 1)):
            fails["times out of order along a path"].append((b["wallet"], b["mint"]))
        first = b["path"][1]
        seen[(first["sig"], b["path"][0]["wallet"], first["wallet"])].add((b["wallet"], b["mint"]))
    shared = [k for k, v in seen.items() if len(v) >= 2]
    if shared:
        fails["one transfer attributed to several events (pooled windows)"].extend(shared)
    per_ev = Counter((b["wallet"], b["mint"], b["path"][1]["sig"], b["path"][1]["wallet"]) for b in out["branches"])
    dup = [k for k, v in per_ev.items() if v >= 2]
    if dup:
        fails["one transfer counted twice in one event"].extend(dup)
    # hubs: no measured hub kept as a private wallet, no terminal H1-H4 on a known hub
    for b in out["branches"]:
        for a, m in b["measured"].items():
            if m.get("hub") and b["terminal"] != "H5":
                fails["measured hub not terminal H5"].append((b["wallet"], b["mint"], a))
        last = b["path"][-1]["wallet"]
        if b["terminal"] in ("H1", "H2", "H3", "H4") and R.hub.get(last):
            fails["known hub classified as a private terminal"].append(last)
    # roles visible at the flow's time
    for b in out["branches"]:
        if b["terminal"] in ("H2", "H3", "H4"):
            last = b["path"][-1]
            if R.first.get(last["wallet"], 1e18) > last["bt"]:
                fails["role used before it is visible"].append((b["wallet"], b["mint"], last["wallet"]))
    # no transaction after an event's window
    for w in out["wallets"]:
        for tr in w["events"]:
            rc = evmeta[(tr["wallet"], tr["mint"])]["receipt"]
            for f in tr.get("reads", []):
                if (f["bt"] or 0) >= rc["bt"] + L.WINDOW_S or (f["bt"] or 0) < rc["bt"]:
                    fails["transaction outside the event window"].append(f["sig"])
    for b in out["branches"]:
        for i in range(1, len(b["path"]) - 1):
            a, c = b["path"][i], b["path"][i + 1]
            if (c["bt"] or 0) >= (a["bt"] or 0) + L.WINDOW_S:
                fails["hop outside the 2 h window"].append((b["wallet"], b["mint"], i))
    # failures of collection
    st = Counter()
    for w in out["wallets"]:
        if w.get("listing_error"):
            st["listing: " + w["listing_error"].split(":")[0]] += 1
        for tr in w["events"]:
            st["event: " + str(tr.get("status")).split(":")[0]] += 1
    for p in out["prior"]:
        if p.get("error"):
            st["prior: " + p["error"].split(":")[0]] += 1
    for b in out["branches"]:
        st["branch: " + str(b["reason"]).split(":")[0]] += 1
    return {
        "failures": {k: {"n": len(v), "examples": v[:5]} for k, v in fails.items()},
        "status": dict(st),
        "price_file_opened": False,
    }


def main() -> None:
    rows = sorted(E.load(), key=lambda z: z["t"])
    R = T.Roles(rows)
    F = T.Fetch(online=False)
    out = C.run(F, R, 1, lambda m: None)
    sel = json.load(open(L.SELECTION))
    done = [x for x in open(os.path.join(L.CACHE, "collect.log")) if "stopped: " in x]
    out["stopped"] = done[-1].split("stopped: ", 1)[1].strip() if done else "collection log has no end line"
    raw = json.dumps(out, sort_keys=True, separators=(",", ":")).encode()
    with open(TABLE, "wb") as fh:
        fh.write(gzip.compress(raw, mtime=0))
    sha = hashlib.sha256(open(TABLE, "rb").read()).hexdigest()
    commit = subprocess.run(
        ["git", "-C", L.ROOT, "log", "-1", "--format=%h", "--", "exit_destination/analysis_plan.md"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    calls = json.load(open(os.path.join(L.CACHE, "budget.json")))
    doc = {
        "sha256_table": sha,
        "protocol_commit": commit,
        "calls": calls,
        "smoke_test_calls_not_in_counter": 11,
        "wallets": len(out["wallets"]),
        "events": sum(len(w["events"]) for w in out["wallets"]),
        "branches": len(out["branches"]),
        "sha256_selection": hashlib.sha256(open(L.SELECTION, "rb").read()).hexdigest(),
    }
    json.dump(doc, open(FREEZE, "w"), indent=1, sort_keys=True)
    integ = integrity(out, R, sel)
    json.dump(integ, open(INTEGRITY, "w"), indent=1, sort_keys=True, default=str)
    print(json.dumps(doc, indent=1))
    print(json.dumps(integ, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
