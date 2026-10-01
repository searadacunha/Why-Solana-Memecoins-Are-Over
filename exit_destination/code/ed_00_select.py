#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The sample of recurring exit wallets, from the frozen tables only (analysis_plan.md, section 2), and what the
existing on-chain cache already says about their activity (used for the call estimate, never for selection).

Score: launches (capped at 10) + 3 if fed by two snipers or more + 3 if present in TRAIN and VALIDATION + 2 if
most of its events have a funder that funds snipers in two launches or more. Ranked by score, then events,
then address; no economic-mechanics cluster above a quarter of the sample. Sampled events: up to 5 per wallet,
evenly spaced over its events in time order, the last one excluded (its receipt is the listing cursor).
Writes derived/selection.json.
"""

from __future__ import annotations

import glob
import gzip
import json
import os
from collections import Counter
from typing import Any

import ed_lib as L
import em_lib as E


def activity(wallets: set[str]) -> dict[str, dict[str, Any]]:
    """The earlier signature pages read by the window collection for any of these wallets (role, count, span)."""
    out: dict[str, dict[str, Any]] = {}
    for p in glob.glob(os.path.join(L.ROOT, "post_detection_forensics", "data", "onchain_cache", "wal", "*.json.gz")):
        d = json.load(gzip.open(p))
        for w, e in d["wallets"].items():
            if w not in wallets or "prior" not in e:
                continue
            bts = [b for b in e["prior"]["bts"] if b]
            span = (max(bts) - min(bts)) if len(bts) >= 2 else None
            cur = out.get(w)
            if cur is None or e["first_bt"] > cur["first_bt"]:
                out[w] = {"role": e.get("role"), "first_bt": e["first_bt"], "n": e["prior"]["n"], "span_s": span}
    return out


def main() -> None:
    rows = sorted(E.load(), key=lambda z: z["t"])
    cl = E.clusters(rows)
    ev = L.events(rows)
    g = L.by_wallet(ev)
    rec = {w: v for w, v in g.items() if len({e["mint"] for e in v}) >= 2}
    fl = Counter()
    for r in rows:
        for f in {E.fkey(s) for s in r["snipers"]} - {None}:
            if not f.startswith("own:"):
                fl[f] += 1
    multi_f = {f for f, c in fl.items() if c >= 2}
    cand = []
    for w, v in rec.items():
        n = len({e["mint"] for e in v})
        sn = set().union(*(e["snipers"] for e in v))
        sp = {e["split"] for e in v}
        strong = sum(1 for e in v if e["funders"] & multi_f)
        score = min(n, 10) + 3 * (len(sn) >= 2) + 3 * (sp == set(L.SPLITS)) + 2 * (strong > len(v) / 2)
        cc = Counter(cl[e["mint"]] for e in v).most_common(1)[0][0]
        cand.append({"wallet": w, "score": score, "launches": n, "snipers": len(sn), "splits": sorted(sp),
                     "strong_funder": strong > len(v) / 2, "em_cluster": cc,
                     "operator": Counter(e["cluster"] for e in v).most_common(1)[0][0]})
    cand.sort(key=lambda c: (-c["score"], -c["launches"], c["wallet"]))
    cap = int(L.CLUSTER_CAP * L.TARGET_WALLETS)
    per: Counter = Counter()
    sel = []
    for c in cand:
        if len(sel) >= L.TARGET_WALLETS:
            break
        if per[c["em_cluster"]] >= cap:
            continue
        per[c["em_cluster"]] += 1
        sel.append(c)
    chosen = {c["wallet"] for c in sel}
    sev = [e for w in chosen for e in g[w]]
    sampled = set()
    for c in sel:
        es = g[c["wallet"]]
        c["cursor"] = es[-1]["receipt"]
        c["first_receipt"] = es[0]["receipt"]
        n = len(es) - 1
        k = min(L.EVENTS_PER_WALLET, n)
        idx = {round(i * (n - 1) / (k - 1)) for i in range(k)} if k > 1 else {0}
        sampled |= {(c["wallet"], es[i]["mint"]) for i in idx}
    act = activity(chosen)
    doc = {
        "rule": "analysis_plan.md section 2",
        "population": len(rec),
        "selected": sel,
        "events": [
            {"wallet": e["wallet"], "mint": e["mint"], "t": e["t"], "split": e["split"], "cluster": e["cluster"],
             "em_cluster": cl[e["mint"]], "snipers": sorted(e["snipers"]), "funders": sorted(e["funders"]),
             "tokens": e["tokens"], "receipt": e["receipt"], "sampled": (e["wallet"], e["mint"]) in sampled}
            for e in sorted(sev, key=lambda e: (e["wallet"], e["receipt"]["slot"]))
        ],
    }
    os.makedirs(L.DERIVED, exist_ok=True)
    with open(L.SELECTION, "w") as fh:
        json.dump(doc, fh, indent=0, sort_keys=True)
    print("population %d, selected %d, events %d" % (len(rec), len(sel), len(sev)))
    print("score range", sel[0]["score"], sel[-1]["score"], "| launches", Counter(min(c["launches"], 10) for c in sel))
    print("2+ snipers %d | TRAIN and VAL %d | strong funder %d" % (
        sum(c["snipers"] >= 2 for c in sel),
        sum(len(c["splits"]) == 2 for c in sel),
        sum(c["strong_funder"] for c in sel)))
    print("em clusters %d, largest %s | operators %d, largest %s" % (
        len(per), per.most_common(3), len({c["operator"] for c in sel}),
        Counter(c["operator"] for c in sel).most_common(3)))
    print("events by split", Counter(e["split"] for e in sev))
    print("sampled events %d, by split %s, wallets with k sampled %s" % (
        len(sampled), Counter(e["split"] for e in sev if (e["wallet"], e["mint"]) in sampled),
        sorted(Counter(Counter(w for w, _ in sampled).values()).items())))
    print("activity known for %d of %d selected wallets" % (len(act), len(sel)))
    if act:
        ns = sorted(a["n"] for a in act.values())
        print("earlier txs on one page (cap 1000): median %d, p75 %d, p90 %d, capped %d" % (
            ns[len(ns) // 2], ns[3 * len(ns) // 4], ns[9 * len(ns) // 10], sum(1 for x in ns if x >= 1000)))
        print("roles", Counter(a["role"] for a in act.values()))


if __name__ == "__main__":
    main()
