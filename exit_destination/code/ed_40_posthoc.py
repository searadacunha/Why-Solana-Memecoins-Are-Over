#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Checks added after reading the pre-registered tables, all descriptive and marked post hoc in results.md. They
answer what the pre-registered tests could not show on their own:

- the structure of every outgoing SOL transfer (signers, fee payer, the one-time address it passes through,
  the exit wallet's balance after it), the venue and fee payer of every sale, and the timing of the sweep;
- returns to the launch's own funder whatever its hub status (the plan classifies a funder with 3,000
  transactions or more as a hub, H5, never H1);
- the operator as unit: the pre-registered nulls permute among events of all operators, and inside an operator
  the behaviour is all or nothing, so the event-level p-values overstate the evidence;
- the recipients that are not the launch's funder and whether the frozen tables know them.
Writes tables/K_posthoc.md and derived/ED_posthoc.json. No price is read.
"""

from __future__ import annotations

import json
import os
import statistics
from collections import Counter, defaultdict
from typing import Any

import ed_30_analysis as A
import ed_lib as L
import ed_trace as T
import fparse


def main() -> None:
    D = A.Data()
    F = T.Fetch(False)
    out: dict[str, Any] = {}

    def raw_funders(m: str) -> set[str]:
        return {s.get("last_funder") for s in D.byrow[m]["snipers"]} - {None}

    br = [(e, b) for e in D.obs for b in e["branches"]]
    lines = ["# K. Post-hoc checks (descriptive, added after reading tables B to J)", ""]

    # 1. the sweep transactions
    comp: Counter = Counter()
    onetime: Counter = Counter()
    posts, d_rec, d_sale = [], [], []
    for e, b in br:
        t = F.tx(b["path"][1]["sig"])
        acc = t["transaction"]["message"]["accountKeys"]
        keys = [k["pubkey"] for k in acc]
        sg = [k["pubkey"] for k in acc if k.get("signer")]
        comp[(e["wallet"] in sg, keys[0] == b["path"][1]["wallet"], len(sg))] += 1
        sys_dst = None
        for ix in T._instructions(t):
            p = ix.get("parsed") if ix.get("program") == "system" else None
            if isinstance(p, dict) and p.get("type") == "transfer" and p["info"].get("source") == e["wallet"]:
                sys_dst = p["info"].get("destination")
                break
        if sys_dst and sys_dst != b["path"][1]["wallet"]:
            try:
                onetime["through an address with %d transaction(s) in its history" % len(F.page(sys_dst))] += 1
            except T.NotCollected:
                onetime["through an address whose history was not listed"] += 1
        else:
            onetime["System transfer straight to the recipient"] += 1
        posts.append(t["meta"]["postBalances"][keys.index(e["wallet"])] / 1e9)
        d_rec.append(b["bt"] - e["receipt"]["bt"])
        sales = [f["bt"] for f in e["reads"] if T.is_sale(f, e["mint"]) and f["bt"] <= b["bt"]]
        if sales:
            d_sale.append(b["bt"] - max(sales))
    lines += [
        "## 1. Every outgoing SOL transfer of 0.1 SOL or more (%d)" % len(br),
        "",
        "- signers: "
        + ", ".join(
            "exit wallet signs %s, recipient pays the fee %s, %d signers: %d" % (a, c, n, v)
            for (a, c, n), v in comp.most_common()
        ),
        "- route: " + ", ".join("%s: %d" % kv for kv in onetime.most_common()),
        "- exit wallet's SOL after the transfer: %s; below 0.001 SOL in %d"
        % (A.dist(posts, "%.4f"), sum(1 for p in posts if p < 0.001)),
        "- delay from the receipt of the tokens (s): %s" % A.dist(d_rec),
        "- delay after the last sale before it (s): %s" % A.dist(d_sale),
        "",
    ]
    out["sweeps"] = {
        "n": len(br),
        "composition": {str(k): v for k, v in comp.items()},
        "route": dict(onetime),
        "post_below_0.001": sum(1 for p in posts if p < 0.001),
        "delay_receipt_median": statistics.median(d_rec),
        "delay_last_sale_median": statistics.median(d_sale),
    }

    # 2. the sales
    ven: Counter = Counter()
    payer: Counter = Counter()
    for e in D.obs:
        for f in e["reads"]:
            if not T.is_sale(f, e["mint"]):
                continue
            progs = {ix.get("programId") for ix in T._instructions(F.tx(f["sig"], e["mint"]))}
            v = (
                "pump.fun curve"
                if fparse.PUMP in progs
                else "PumpSwap"
                if fparse.PUMPSWAP in progs
                else "router"
                if progs & set(fparse.ROUTERS)
                else "other program"
            )
            ven[v] += 1
            payer["exit wallet" if f["signer"] == e["wallet"] else "another wallet"] += 1
    lines += [
        "## 2. Sales by the exit wallets",
        "",
        "- venue: " + ", ".join("%s %d" % kv for kv in ven.most_common()),
        "- fee paid by: " + ", ".join("%s %d" % kv for kv in payer.most_common()),
        "",
    ]
    for st in ("complete", "cap"):
        ev = [e for e in D.obs if e["status"] == st]
        base = sum(e["base"] for e in ev)
        ns = sorted(sum(1 for f in e["reads"] if T.is_sale(f, e["mint"])) for e in ev)
        lines.append(
            "- reading %s: %d events, tokens not yet sold when it stopped %s, sales read per event "
            "(median) %d" % (st, len(ev), A.pct(sum(e["held"] for e in ev), base), ns[len(ns) // 2])
        )
    out["sales"] = {"venue": dict(ven), "payer": dict(payer)}

    # 3. returns to the launch's own funder, whatever its hub status
    raw = [(e, b) for e, b in br if b["path"][1]["wallet"] in raw_funders(e["mint"])]
    oth = [(e, b) for e, b in br if b["path"][1]["wallet"] not in raw_funders(e["mint"])]
    ev_b = [e for e in D.obs if e["branches"]]
    ev_raw = {(e["wallet"], e["mint"]) for e, _ in raw}
    lines += [
        "",
        "## 3. SOL sent straight to the launch's own funder, whatever its hub status",
        "",
        "| | branches | SOL | events |",
        "|---|---:|---:|---:|",
        "| to the launch's funder | %d (%s) | %.0f (%s) | %d of %d (%s) |"
        % (
            len(raw),
            A.pct(len(raw), len(br)),
            sum(b["sol"] for _, b in raw),
            A.pct(sum(b["sol"] for _, b in raw), sum(b["sol"] for _, b in br)),
            len(ev_raw),
            len(ev_b),
            A.pct(len(ev_raw), len(ev_b)),
        ),
        "| of which to a funder the plan classifies as a hub (H5) | %d | %.0f | |"
        % (sum(1 for _, b in raw if b["terminal"] == "H5"), sum(b["sol"] for _, b in raw if b["terminal"] == "H5")),
        "| elsewhere | %d | %.0f | |" % (len(oth), sum(b["sol"] for _, b in oth)),
        "",
    ]
    for sp, name in (("train", "TRAIN"), ("val", "VALIDATION")):
        n = sum(1 for e, _ in br if e["split"] == sp)
        lines.append(
            "- %s: %s of branches to the launch's funder" % (name, A.pct(sum(1 for e, _ in raw if e["split"] == sp), n))
        )
    out["raw_funder"] = {
        "branches": len(raw),
        "sol": sum(b["sol"] for _, b in raw),
        "events": len(ev_raw),
        "events_with_branch": len(ev_b),
        "hub_flagged": sum(1 for _, b in raw if b["terminal"] == "H5"),
        "elsewhere": len(oth),
        "elsewhere_sol": sum(b["sol"] for _, b in oth),
        "all_branches": len(br),
        "all_sol": sum(b["sol"] for _, b in br),
    }

    # 4. the operator as unit
    ops: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in D.obs:
        ops[e["cluster"]].append(e)
    lines += [
        "",
        "## 4. By operator (the unit the event-level nulls ignore)",
        "",
        "| operator | launches TRAIN / VAL | read events | transfers | to the launch's funder | recipients | "
        "events funding a later launch |",
        "|---|---|---:|---:|---:|---|---:|",
    ]
    rows = []
    for op, ev in sorted(ops.items(), key=lambda x: (-len(x[1]), x[0])):
        b2 = [(e, b) for e in ev for b in e["branches"]]
        if not b2:
            continue
        r = sum(1 for e, b in b2 if b["path"][1]["wallet"] in raw_funders(e["mint"]))
        rc = Counter(b["path"][1]["wallet"] for _, b in b2)
        rec = sum(1 for e in ev if e["branches"] and any(A.recycling(D, e, b, light=True) for b in e["branches"]))
        lt = len({e["mint"] for e in ev if e["split"] == "train"})
        lv = len({e["mint"] for e in ev if e["split"] == "val"})
        rows.append(
            {
                "operator": op,
                "train": lt,
                "val": lv,
                "events": len(ev),
                "transfers": len(b2),
                "to_funder": r / len(b2),
                "recipients": len(rc),
                "recycle": rec,
                "with_branch": sum(1 for e in ev if e["branches"]),
            }
        )
        lines.append(
            "| %s | %d / %d | %d | %d | %s | %d (%s) | %d of %d |"
            % (
                op[:16],
                lt,
                lv,
                len(ev),
                len(b2),
                A.pct(r, len(b2)),
                len(rc),
                ", ".join("%s %d" % (w[:6], n) for w, n in rc.most_common(2)),
                rec,
                sum(1 for e in ev if e["branches"]),
            )
        )
    hi = [x for x in rows if x["to_funder"] >= 0.8]
    lo = [x for x in rows if x["to_funder"] <= 0.2]
    lines += [
        "",
        "Operators with transfers: %d; sending 80 %% or more to the launch's funder: %d (TRAIN-only %d, "
        "VALIDATION-only %d, both %d); 20 %% or less: %d (TRAIN-only %d, VALIDATION-only %d, both %d); "
        "in between: %d."
        % (
            len(rows),
            len(hi),
            sum(1 for x in hi if x["val"] == 0),
            sum(1 for x in hi if x["train"] == 0),
            sum(1 for x in hi if x["train"] and x["val"]),
            len(lo),
            sum(1 for x in lo if x["val"] == 0),
            sum(1 for x in lo if x["train"] == 0),
            sum(1 for x in lo if x["train"] and x["val"]),
            len(rows) - len(hi) - len(lo),
        ),
        "Operators funding a later launch from the swept capital: %d of the %d returning to the funder, %d of "
        "the %d sending elsewhere."
        % (sum(1 for x in hi if x["recycle"]), len(hi), sum(1 for x in lo if x["recycle"]), len(lo)),
    ]
    per_launch = Counter(e["mint"] for e in D.obs)
    lines.append(
        "Read events per launch, median: TRAIN %s, VALIDATION %s; launches: TRAIN %d, VALIDATION %d."
        % (
            statistics.median([v for m, v in per_launch.items() if D.byrow[m]["split"] == "train"]),
            statistics.median([v for m, v in per_launch.items() if D.byrow[m]["split"] == "val"]),
            sum(1 for m in per_launch if D.byrow[m]["split"] == "train"),
            sum(1 for m in per_launch if D.byrow[m]["split"] == "val"),
        )
    )
    out["operators"] = rows

    # 5. recipients other than the launch's funder
    rw: dict[str, set[str]] = defaultdict(set)
    for e, b in br:
        rw[b["path"][1]["wallet"]].add(e["cluster"])
    coll = Counter(b["path"][1]["wallet"] for _, b in oth)
    lines += [
        "",
        "## 5. Recipients other than the launch's funder",
        "",
        "%d distinct wallets for %d transfers; known anywhere in the frozen tables (any role, any time): %d; "
        "measured or recorded hubs: %d; too active to reach the inflow in 3 pages: %d."
        % (
            len(coll),
            len(oth),
            sum(1 for w in coll if w in D.R.first),
            sum(
                1
                for w in coll
                if D.R.hub.get(w) or any(b["path"][-1]["wallet"] == w and b["terminal"] == "H5" for _, b in oth)
            ),
            len({b["path"][-1]["wallet"] for _, b in oth if b["reason"] == "too active"}),
        ),
        "Recipient wallets used by two operators or more: "
        + (", ".join("%s (%d operators)" % (w[:8], len(o)) for w, o in rw.items() if len(o) >= 2) or "none")
        + ".",
        "Distinct recipients over all %d transfers: %d; events whose transfers go to two recipients or more: %d."
        % (len(br), len(rw), sum(1 for e in D.obs if len({b["path"][1]["wallet"] for b in e["branches"]}) >= 2)),
    ]
    out["collectors"] = {
        "distinct": len(coll),
        "known": sum(1 for w in coll if w in D.R.first),
        "shared_recipients": {w: len(o) for w, o in rw.items() if len(o) >= 2},
        "distinct_recipients": len(rw),
    }
    # 6. fan-out: exit wallets per sniper per launch, whole frozen corpus
    fan = Counter(
        len({o for x in s["exits_full"] if x["kind"] == "transfer" for o in x["recipients"]})
        for r in D.rows
        for s in r["snipers"]
    )
    lines += [
        "",
        "## 6. Exit wallets fed by one sniper in one launch (whole frozen corpus)",
        "",
        ", ".join("%d: %d" % kv for kv in sorted(fan.items())),
    ]
    out["fan_out"] = dict(fan)

    # 7. which wallet carries the recycling link
    via: Counter = Counter()
    for e in D.obs:
        best = None
        for b in e["branches"]:
            r = A.recycling(D, e, b)
            if r and (best is None or r["t_fund"] < best["t_fund"]):
                best = r
        if best:
            via["the launch's own funder" if best["wallet"] in raw_funders(e["mint"]) else "another wallet"] += 1
    lines += [
        "",
        "## 7. Recycling links (section F) by the wallet that funds the later launch",
        "",
        ", ".join("%s %d" % kv for kv in via.most_common()),
    ]
    out["recycling_via"] = dict(via)
    A.write("K_posthoc.md", lines)
    with open(os.path.join(L.DERIVED, "ED_posthoc.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, default=str)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
