#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Checks added after reading tables B to J, descriptive and marked post hoc in results.md:

1. the hubs (activity proxy, 3,000 transactions or more before the inflow): which ones receive or send the SOL,
   how many operators each touches. The plan never lets a hub join operators; this shows what that rule hides;
2. the same components if hubs were allowed to join (a sensitivity, not a finding);
3. every cross-operator link through a non-hub wallet, with its direction and relation;
4. the operators of each multi-operator component and the operators left alone.
Writes tables/K_posthoc.md and derived/FN_posthoc.json. No price is read.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from typing import Any

import fn_30_analysis as A
import fn_trace as N


def main() -> None:
    D = A.Data()
    out: dict[str, Any] = {}
    lines = ["# K. Post-hoc checks (descriptive, added after reading tables B to J)", ""]

    # 1. hubs
    hub_use: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"ops": set(), "prims": set(), "sol": 0.0, "dirs": set(), "measured": False}
    )
    for x in D.paths:
        for n in x["path"][1:]:
            a = n["wallet"]
            if a and D.is_hub(a):
                h = hub_use[a]
                h["ops"] |= D.ops[x["primary"]]
                h["prims"].add(x["primary"])
                h["sol"] += n.get("sol") or 0
                h["dirs"].add(x["direction"])
                h["measured"] |= x["terminal"] == "hub measured"
                break
    multi = {a: h for a, h in hub_use.items() if len(h["ops"]) >= 2}
    lines += [
        "## 1. Hubs reached (first hub on each path)",
        "",
        "%d distinct hubs; touched by two operators or more: %d; SOL reaching hubs %.0f, of which through hubs "
        "shared by two operators or more %.0f."
        % (len(hub_use), len(multi), sum(h["sol"] for h in hub_use.values()), sum(h["sol"] for h in multi.values())),
        "",
        "| hub | operators | primary wallets | direction | SOL on the edge into it | in the frozen tables |",
        "|---|---:|---:|---|---:|---|",
    ]
    for a, h in sorted(hub_use.items(), key=lambda kv: (-len(kv[1]["ops"]), -kv[1]["sol"]))[:20]:
        lines.append(
            "| %s | %d | %d | %s | %.0f | %s |"
            % (
                a[:10],
                len(h["ops"]),
                len(h["prims"]),
                "/".join(sorted(h["dirs"])),
                h["sol"],
                "yes" if a in D.ties else "no",
            )
        )
    out["hubs"] = {
        a: {"operators": sorted(h["ops"]), "primaries": len(h["prims"]), "sol": h["sol"], "dirs": sorted(h["dirs"])}
        for a, h in hub_use.items()
    }

    # 2. components if hubs could join
    inc_all = sorted(
        {
            (x["primary"], n["wallet"])
            for x in D.paths
            for n in x["path"][1:]
            if n["wallet"] and n["wallet"] != x["primary"]
        }
    )
    st_no = A.stats(D, A.incidence(D, D.paths), D.ops)
    st_h = A.stats(D, inc_all, D.ops)
    lines += [
        "",
        "## 2. Sensitivity: hubs allowed to join operators (not the plan's rule)",
        "",
        "Operator components without hubs (the plan): sizes %s. With hubs: sizes %s." % (st_no["sizes"], st_h["sizes"]),
    ]
    out["components_with_hubs"] = st_h["sizes"]
    loo_h = []
    for a in sorted(multi):
        st = A.stats(D, [(p, b) for p, b in inc_all if b != a], D.ops)
        loo_h.append((a, st["largest"]))
    worst = min(loo_h, key=lambda t: t[1]) if loo_h else None
    lines.append(
        "Leave one shared hub out: the largest component keeps %d to %d operators%s."
        % (
            min(g for _, g in loo_h) if loo_h else 0,
            max(g for _, g in loo_h) if loo_h else 0,
            " (smallest without %s)" % worst[0][:10] if worst else "",
        )
    )
    uf_h = A.UF()
    for p, o in D.ops.items():
        o = sorted(o)
        for i in range(1, len(o)):
            uf_h.union("O:" + o[0], "O:" + o[i])
    for p, a in inc_all:
        for o in D.ops[p]:
            uf_h.union("O:" + o, "W:" + a)
    comp_h: dict[str, set[str]] = defaultdict(set)
    for o in {o for v in D.ops.values() for o in v}:
        comp_h[uf_h.find("O:" + o)].add(o)
    big = max(comp_h.values(), key=len)
    lines.append(
        "Operators outside the largest component with hubs: %s."
        % ", ".join(sorted(o[:16] for v in comp_h.values() if v is not big for o in v))
    )
    out["hub_leave_one_out"] = loo_h
    # the informative variant: a hub joins only through a direct transfer it co-signed as recipient (hop 1,
    # downstream); a hub that funded a wallet signs its own outflow, which an exchange does too
    F0 = N.Fetch(online=False)
    cos = set()
    for x in D.tab["downs"]:
        a = x["path"][1]["wallet"]
        if not D.is_hub(a):
            continue
        acc = F0.tx(x["path"][1]["sig"])["transaction"]["message"]["accountKeys"]
        if a in [k["pubkey"] for k in acc if k.get("signer")]:
            cos.add((x["primary"], a))
    inc_cos = sorted(set(A.incidence(D, D.paths)) | cos)
    st_c = A.stats(D, inc_cos, D.ops)
    loo_c = [A.stats(D, [(p, b) for p, b in inc_cos if b != a], D.ops)["largest"] for a in sorted({b for _, b in cos})]
    lines.append(
        "Hubs joining only through a direct transfer they co-signed as recipient: %d such hubs, %d shared "
        "by two operators or more; components %s; leaving one of these hubs out keeps %d to %d operators "
        "in the largest."
        % (
            len({b for _, b in cos}),
            sum(1 for b in {b for _, b in cos} if len({o for p, bb in cos if bb == b for o in D.ops[p]}) >= 2),
            st_c["sizes"],
            min(loo_c) if loo_c else 0,
            max(loo_c) if loo_c else 0,
        )
    )
    out["components_cosigned_hubs"] = st_c["sizes"]

    # 3. cross-operator links through non-hub wallets
    links = []
    for a, opset in sorted(st_no["shared_wallets"].items()):
        xs = [x for x in D.paths if a in [n["wallet"] for n in x["path"][1:]]]
        for x in xs:
            i = [n["wallet"] for n in x["path"]].index(a)
            n = x["path"][i]
            links.append(
                {
                    "wallet": a,
                    "primary": x["primary"],
                    "operators": sorted(D.ops[x["primary"]]),
                    "direction": x["direction"],
                    "hop": i,
                    "sol": n.get("sol"),
                    "bt": n.get("bt"),
                    "edge": (
                        "%s funded %s" % (a[:8], x["path"][i - 1]["wallet"][:8])
                        if x["direction"] == "up"
                        else "%s sent to %s" % (x["path"][i - 1]["wallet"][:8], a[:8])
                    ),
                }
            )
    lines += [
        "",
        "## 3. Every edge touching a wallet shared by two operators (non-hub)",
        "",
        "| shared wallet | primary | operator | direction | hop | edge | SOL | week |",
        "|---|---|---|---|---:|---|---:|---|",
    ]
    for k in links:
        lines.append(
            "| %s | %s | %s | %s | %d | %s | %.1f | %s |"
            % (
                k["wallet"][:8],
                k["primary"][:8],
                "/".join(o[:12] for o in k["operators"]),
                k["direction"],
                k["hop"],
                k["edge"],
                k["sol"] or 0,
                A.week(k["bt"]) if k["bt"] else "-",
            )
        )
    out["links"] = links
    created = defaultdict(set)
    for x in D.tab["ups"]:
        if len(x["path"]) >= 2 and x["path"][1]["wallet"]:
            created[x["path"][1]["wallet"]].add(x["primary"])
    shared_creators = {a: ps for a, ps in created.items() if len({o for p in ps for o in D.ops[p]}) >= 2}
    lines += [
        "",
        "Wallets that created (genesis funding) primary wallets of two operators or more: "
        + (
            ", ".join(
                "%s (%d wallets: %s)" % (a[:8], len(ps), ", ".join(sorted({o[:12] for p in ps for o in D.ops[p]})))
                for a, ps in shared_creators.items()
            )
            or "none"
        )
        + ".",
    ]
    hubs_created = {a: ps for a, ps in created.items() if D.is_hub(a)}
    lines.append(
        "Primary wallets created by a hub: %d, by %d distinct hubs; hubs that created wallets of two "
        "operators or more: %d."
        % (
            sum(len(ps) for ps in hubs_created.values()),
            len(hubs_created),
            sum(1 for ps in hubs_created.values() if len({o for p in ps for o in D.ops[p]}) >= 2),
        )
    )

    # 4. component membership
    uf = A.UF()
    for p, o in D.ops.items():
        o = sorted(o)
        for i in range(1, len(o)):
            uf.union("O:" + o[0], "O:" + o[i])
    for p, a in A.incidence(D, D.paths):
        for o in D.ops[p]:
            uf.union("O:" + o, "W:" + a)
    comp: dict[str, set[str]] = defaultdict(set)
    for o in {o for s in D.ops.values() for o in s}:
        comp[uf.find("O:" + o)].add(o)
    lines += ["", "## 4. Operator components (plan's rule)", ""]
    for c in sorted(comp.values(), key=lambda v: -len(v)):
        sw = sum(len(p["sweeps"]) for w, p in D.pop.items() if D.ops[w] & c)
        lines.append(
            "- %d operator(s), %d sweeps in the exit sample: %s" % (len(c), sw, ", ".join(sorted(o[:16] for o in c)))
        )
    out["components"] = [sorted(c) for c in comp.values()]
    # 5. ordered sequences through bridge wallets: capital in from operator X, then out to a wallet of operator Y
    edges = []  # (src, dst, sol, bt, origin operators)
    for x in D.paths:
        p = x["path"]
        for i in range(1, len(p)):
            if not p[i]["wallet"] or not p[i].get("bt"):
                continue
            if x["direction"] == "down":
                edges.append(
                    (p[i - 1]["wallet"], p[i]["wallet"], p[i].get("sol") or 0, p[i]["bt"], D.ops[x["primary"]])
                )
            else:
                edges.append((p[i]["wallet"], p[i - 1]["wallet"], p[i].get("sol") or 0, p[i]["bt"], set()))
    edges = sorted(set((a, b, round(v, 6), t, tuple(sorted(o))) for a, b, v, t, o in edges), key=lambda e: e[3])
    bridges = sorted({w for w in st_no["shared_wallets"]} | {a for a in created if a in st_no["shared_wallets"]})
    seqs = []
    for w in bridges:
        ins = [e for e in edges if e[1] == w and e[4]]
        outs = [e for e in edges if e[0] == w and e[1] in D.pop]
        for i in ins:
            for o in outs:
                y = D.ops[o[1]]
                if o[3] > i[3] and not (set(i[4]) & y):
                    seqs.append(
                        {
                            "bridge": w,
                            "from_ops": list(i[4]),
                            "to_wallet": o[1],
                            "to_ops": sorted(y),
                            "in_sol": i[2],
                            "out_sol": o[2],
                            "delay_h": (o[3] - i[3]) / 3600,
                            "in_week": A.week(i[3]),
                            "out_week": A.week(o[3]),
                        }
                    )
    lines += [
        "",
        "## 5. Ordered sequences: SOL into a bridge wallet from one operator's path, then SOL out of it to a "
        "primary wallet of another operator",
        "",
        "| bridge | from operator | in SOL | to wallet | to operator | out SOL | delay (h) | weeks |",
        "|---|---|---:|---|---|---:|---:|---|",
    ]
    for q in seqs:
        lines.append(
            "| %s | %s | %.1f | %s | %s | %.1f | %.1f | %s -> %s |"
            % (
                q["bridge"][:8],
                "/".join(o[:12] for o in q["from_ops"]),
                q["in_sol"],
                q["to_wallet"][:8],
                "/".join(o[:12] for o in q["to_ops"]),
                q["out_sol"],
                q["delay_h"],
                q["in_week"],
                q["out_week"],
            )
        )
    if not seqs:
        lines.append("| none | | | | | | | |")
    out["sequences"] = seqs

    # 6. hubs that both receive SOL from primary wallets and created (genesis funding) primary wallets
    two_way = []
    for a, h in hub_use.items():
        made = created.get(a, set())
        recv = [x for x in D.tab["downs"] if a in [n["wallet"] for n in x["path"][1:]]]
        if made and recv:
            two_way.append(
                {
                    "hub": a,
                    "created": sorted(made),
                    "created_ops": sorted({o for p in made for o in D.ops[p]}),
                    "received_from_ops": sorted({o for x in recv for o in D.ops[x["primary"]]}),
                    "sol_in": sum(n.get("sol") or 0 for x in recv for n in x["path"][1:] if n["wallet"] == a),
                }
            )
    lines += [
        "",
        "## 6. Hubs that both receive SOL from primary wallets and created primary wallets",
        "",
        "| hub | primaries created | their operators | receives from operators | SOL in |",
        "|---|---:|---|---|---:|",
    ]
    for t in sorted(two_way, key=lambda t: -t["sol_in"]):
        lines.append(
            "| %s | %d | %s | %s | %.0f |"
            % (
                t["hub"][:10],
                len(t["created"]),
                ", ".join(o[:12] for o in t["created_ops"]),
                ", ".join(o[:12] for o in t["received_from_ops"]),
                t["sol_in"],
            )
        )
    out["two_way_hubs"] = two_way

    # 7. who signs the primary wallet's transfer into its first destination (cached transactions only)
    F = N.Fetch(online=False)
    sig_rows: Counter = Counter()
    for x in D.tab["downs"]:
        dst = x["path"][1]["wallet"]
        try:
            t = F.tx(x["path"][1]["sig"])
        except N.NotCollected:
            sig_rows[("not cached", "")] += 1
            continue
        acc = t["transaction"]["message"]["accountKeys"]
        sg = [k["pubkey"] for k in acc if k.get("signer")]
        kind = "hub" if D.is_hub(dst) else "population" if dst in D.pop else "other"
        sig_rows[
            (
                kind,
                "destination signs (fee payer)"
                if sg[0] == dst
                else "destination signs"
                if dst in sg
                else "destination does not sign",
            )
        ] += 1
    lines += [
        "",
        "## 7. Does the destination sign the transfer it receives? (first hop of every downstream branch)",
        "",
        "| destination | signature | transfers |",
        "|---|---|---:|",
    ]
    for (k, v), n in sorted(sig_rows.items()):
        lines.append("| %s | %s | %d |" % (k, v, n))
    out["destination_signs"] = {"%s / %s" % k: v for k, v in sig_rows.items()}
    A.write("K_posthoc.md", lines)
    with open(os.path.join(N.DERIVED, "FN_posthoc.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, default=str)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
