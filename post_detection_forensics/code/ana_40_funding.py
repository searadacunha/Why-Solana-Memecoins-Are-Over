#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 4 of analysis_plan.md: funding flows, per sniper and per launch.

Per core wallet (the snipers): its genesis funder, whether that funder was a hub
before its earliest funding in the corpus, the SOL received, hours from funding
to the creation slot and to the alert, how many core wallets of the same launch
share the funder, the share of the bundle bought by that funder's wallets, the
link to the deployer, and the funder's earlier uses in the corpus (causal: only
alerts before this one). Descriptive, winners vs losers, TRAIN and VALIDATION.
Per launch: the funding topology (one funder for the whole core / several /
deployer linked / hub linked) against the primary label, with Wilson CIs.
"""
from __future__ import annotations

import gzip
import json
import os
from collections import Counter, defaultdict

import ana_lib as L
import feat_30_build as FB


def main() -> None:
    rows = L.load()
    per: dict[str, list[dict]] = defaultdict(list)
    uses: Counter[str] = Counter()
    topo: dict[str, dict[str, list[int]]] = {"train": defaultdict(list), "val": defaultdict(list)}
    for r in sorted(rows, key=lambda z: z["t"]):
        doc = json.load(gzip.open(os.path.join(FB.WAL, r["mint"] + ".json.gz"), "rt"))
        core = [w for w, v in doc["wallets"].items() if v["role"] == "core"]
        creator = next((w for w, v in doc["wallets"].items() if v["role"] == "creator"), None)
        fu = {w: ((doc["wallets"][w].get("genesis") or {}).get("funding") or {}) for w in core}
        funder = {w: f.get("funder") for w, f in fu.items() if f.get("funder")}
        cfund = ((doc["wallets"].get(creator) or {}).get("genesis") or {}).get("funding", {}) if creator else {}
        cnt = Counter(funder.values())
        y = r["y"].get(L.PRIMARY)
        t_create = (r["t"] - 1) - (r["fA"].get("p_time_since_creation_s") or 0)
        launch = []
        for w in core:
            f = fu[w]
            g = FB._hop(f["funder"], False) if f.get("funder") else None
            launch.append({
                "y": y, "cluster": r["cluster"], "known": bool(f.get("funder")),
                "hub": (g or {}).get("hub_before_cursor"), "received": f.get("received"),
                "to_buy_h": (t_create - f["bt"]) / 3600 if f.get("bt") else None,
                "to_alert_h": (r["t"] - f["bt"]) / 3600 if f.get("bt") else None,
                "same_funder": cnt.get(f.get("funder"), 0) if f.get("funder") else None,
                "deployer_link": bool(f.get("funder") and creator
                                      and (f["funder"] == creator or f["funder"] == cfund.get("funder"))),
                "prior_uses": uses[f["funder"]] if f.get("funder") else None})
        per[r["split"]] += launch
        if y is not None:
            t = []
            if funder and len(cnt) == 1 and len(funder) == len(core):
                t.append("one funder for the whole core")
            elif funder and max(cnt.values()) >= 2:
                t.append("some core wallets share a funder")
            elif funder:
                t.append("every known funder distinct")
            else:
                t.append("no funder known")
            if any(v["deployer_link"] for v in launch):
                t.append("deployer linked to a core wallet")
            if any(v["hub"] for v in launch):
                t.append("a core wallet funded by a hub")
            for k in t:
                topo[r["split"]][k].append(y)
        for w in list(core) + ([creator] if creator else []):
            ff = ((doc["wallets"].get(w) or {}).get("genesis") or {}).get("funding", {})
            if ff.get("funder"):
                uses[ff["funder"]] += 1
    lines = ["# D4. Funding flows (primary label)", "", "## Per sniper (core wallet), winners vs losers", "",
             "| split | measure | winners: median (q25-q75) or share | losers | N win / lose |",
             "|---|---|---|---|---|"]
    for sp in ("train", "val"):
        P = [p for p in per[sp] if p["y"] is not None]
        for key, kind in (("known", "share"), ("hub", "share"), ("received", "num"), ("to_buy_h", "num"),
                          ("to_alert_h", "num"), ("same_funder", "num"), ("deployer_link", "share"),
                          ("prior_uses", "num")):
            w = [p[key] for p in P if p["y"] == 1 and p[key] is not None]
            lo = [p[key] for p in P if p["y"] == 0 and p[key] is not None]
            if kind == "share":
                cell = lambda v: "%.1f %%" % (100 * sum(1 for x in v if x) / len(v)) if v else "n/a"  # noqa: E731
            else:
                cell = lambda v: (  # noqa: E731
                    "%.3g (%.3g-%.3g)" % (L.q(v, .5), L.q(v, .25), L.q(v, .75))) if v else "n/a"
            lines.append("| %s | %s | %s | %s | %d / %d |" % (sp.upper(), key, cell(w), cell(lo), len(w), len(lo)))
    lines += ["", "## Per launch: funding topology", "", "| split | topology | P(2x confirmed, 15 min) |",
              "|---|---|---|"]
    for sp in ("train", "val"):
        for k, ys in sorted(topo[sp].items()):
            lines.append("| %s | %s | %s |" % (sp.upper(), k, L.rate(sum(ys), len(ys))))
    L.write("D4_funding.md", lines)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
