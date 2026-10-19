#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The study table rebuilt offline from the cache with the collection's own reading (fn_10_collect.run with an
offline Fetch), frozen by sha256, then the integrity checks of analysis_plan.md section 8. Failures go to
derived/FN_INTEGRITY.json; nothing is repaired. An audit hook refuses any opening of a price file.
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

import fn_10_collect as C  # noqa: E402
import fn_trace as N  # noqa: E402
import ed_lib as L  # noqa: E402

TABLE = os.path.join(N.DERIVED, "fn_table.json.gz")
FREEZE = os.path.join(N.DERIVED, "FN_FREEZE.json")
INTEGRITY = os.path.join(N.DERIVED, "FN_INTEGRITY.json")
B58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def integrity(out: dict[str, Any]) -> dict[str, Any]:
    fails: dict[str, list[Any]] = defaultdict(list)
    for w, fl in out["reads"].items():
        s = [f["sig"] for f in fl]
        if len(s) != len(set(s)):
            fails["duplicate signature in a wallet's reads"].append(w)
        for f in fl:
            if (f["bt"] or 0) >= N.TEST_START:
                fails["transaction at or after TEST start read"].append(f["sig"])
            if f["out"] and f.get("out_gain") is not None and abs(f["out"][0][1] - f["out_gain"]) > 0.01:
                fails["recipient's gain differs from the wallet's SOL loss"].append(
                    (f["sig"], round(f["out"][0][1], 4), round(f["out_gain"], 4))
                )
            for d, _ in f["out"]:
                if not B58.match(d):
                    fails["malformed address"].append(d)
    seen: dict[tuple[str, str, str], int] = Counter()
    for x in out["ups"] + out["downs"]:
        p = x["path"]
        for n in p:
            if n["wallet"] and not B58.match(n["wallet"]):
                fails["malformed address"].append(n["wallet"])
            if n.get("bt") and n["bt"] >= N.TEST_START:
                fails["edge at or after TEST start"].append(n.get("sig"))
        bts = [n["bt"] for n in p[1:] if n.get("bt")]
        if x["direction"] == "up" and any(bts[i] < bts[i + 1] for i in range(len(bts) - 1)):
            fails["upstream path not going back in time"].append(x["primary"])
        if x["direction"] == "down" and any(bts[i] > bts[i + 1] for i in range(len(bts) - 1)):
            fails["downstream path not going forward in time"].append(x["primary"])
        for a, m in x["measured"].items():
            if m.get("status") == "hub" and x["terminal"] != "hub measured":
                fails["measured hub kept as a private wallet"].append(a)
        if x["direction"] == "down":
            seen[(p[1]["sig"], p[0]["wallet"], p[1]["wallet"])] += 1
    dup = [k for k, v in seen.items() if v >= 2]
    if dup:
        fails["one transfer starts two branches"].extend(dup)
    st: Counter = Counter()
    for p in out["primary"].values():
        st["upstream start: " + str((p.get("upstream_start") or {}).get("status")).split(":")[0]] += 1
        if "end" in p:
            st["end: " + str(p["end"].get("status")).split(":")[0]] += 1
        if "sample" in p:
            st["sample: " + str(p["sample"].get("status")).split(":")[0]] += 1
    for x in out["ups"]:
        st["upstream terminal: " + str(x["terminal"]).split(":")[0]] += 1
    for x in out["downs"]:
        st["downstream terminal: " + str(x["terminal"]).split(":")[0]] += 1
    return {
        "failures": {k: {"n": len(v), "examples": v[:5]} for k, v in fails.items()},
        "status": dict(st),
        "price_file_opened": False,
    }


def main() -> None:
    # Validate all collection metadata before replacing the frozen table.
    calls = json.load(open(os.path.join(L.CACHE, "budget.json")))
    done = [x for x in open(os.path.join(L.CACHE, "collect.log")) if "stopped: " in x]
    F = N.Fetch(online=False)
    out = C.run(F, 1, lambda m: None)
    out["stopped"] = done[-1].split("stopped: ", 1)[1].strip() if done else "collection log has no end line"
    raw = json.dumps(out, sort_keys=True, separators=(",", ":")).encode()
    packed = gzip.compress(raw, mtime=0)
    sha = hashlib.sha256(packed).hexdigest()
    if os.path.exists(FREEZE) and sha != json.load(open(FREEZE))["sha256_table"]:
        sys.exit("rebuilt funder table differs from the frozen one (check cache completeness); outputs left unchanged")
    commit = subprocess.run(
        ["git", "-C", N.ROOT, "log", "-1", "--format=%h", "--", "funder_network/analysis_plan.md"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    doc = {
        "sha256_table": sha,
        "protocol_commit": commit,
        "calls": calls,
        "probe_calls_included": N.PROBE_CALLS,
        "primary": len(out["primary"]),
        "ups": len(out["ups"]),
        "downs": len(out["downs"]),
        "reads": sum(len(v) for v in out["reads"].values()),
    }
    integ = integrity(out)
    with open(TABLE, "wb") as fh:
        fh.write(packed)
    json.dump(doc, open(FREEZE, "w"), indent=1, sort_keys=True)
    json.dump(integ, open(INTEGRITY, "w"), indent=1, sort_keys=True, default=str)
    print(json.dumps(doc, indent=1))
    print(json.dumps(integ, indent=1, default=str)[:5000])


if __name__ == "__main__":
    main()
