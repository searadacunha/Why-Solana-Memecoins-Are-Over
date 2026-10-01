#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Checks added after em_20_analysis.py, to classify every mechanism by the plan's rule (null p below 0.01 in
both splits, holding without the dominant operator and without the 10 most frequent sniper wallets):

- the robustness of exit-size similarity, proceeds back to the first funder and re-funding by the same funder,
  which em_20 tested on the full corpus only;
- fixed sniper-to-exit-wallet pairs: among the wallets receiving tokens from snipers in two launches or more,
  the share always fed by the same sniper; null: the sniper of each transfer reassigned among the subset's
  transferring snipers;
- the deployer funded by a non-hub wallet of its cluster's sniper network (snipers, their non-hub funders and
  sources, their token recipients), against the network of another cluster drawn at random. A first version
  of this count kept hubs in the network and read 81 %; hubs are excluded here.
Writes tables/K_extra.md.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from typing import Any

import em_20_analysis as A
import em_lib as E


def exit_pairs(rr: list[dict[str, Any]]) -> dict[str, Any]:
    ev = [(o, s["wallet"]) for r in rr for s in r["snipers"] for o in E.sniper_lifecycle(r, s)["recipients"]]

    def stat(ev: list[tuple[str, str]]) -> float:
        by: dict[str, list[str]] = defaultdict(list)
        for o, w in ev:
            by[o].append(w)
        m = [v for v in by.values() if len(v) >= 2]
        return sum(1 for v in m if len(set(v)) == 1) / len(m) if m else 0.0

    rng = random.Random(E.SEED)
    snip = [w for _, w in ev]
    null = [stat([(o, w) for (o, _), w in zip(ev, E.shuffled(rng, snip))]) for _ in range(E.N_PERM)]
    return E.perm_test(stat(ev), null)


def network(rr: list[dict[str, Any]]) -> set[str]:
    net: set[str] = set()
    for r in rr:
        for s in r["snipers"]:
            net.add(s["wallet"])
            for kind in ("last", "gen"):
                f = E.fkey(s, kind)
                if f and not f.startswith("own:"):
                    net.add(f)
                    h = E.hop(f)
                    src = (h.get("funding") or {}).get("funder")
                    if src and not h.get("hub_before_cursor"):
                        net.add(src)
            net |= set(E.sniper_lifecycle(r, s)["recipients"])
    return net


def dep_funders(r: dict[str, Any]) -> set[str]:
    c = r["creator"]
    return {
        f
        for f, h in ((c.get("gen_funder"), c.get("gen_funder_hub")), (c.get("last_funder"), c.get("last_funder_hub")))
        if f and h is not True
    }


def main() -> None:
    rows = sorted(E.load(), key=lambda z: z["t"])
    ret = A.returning(rows)
    top_op = {sp: Counter(r["cluster"] for r in rows if r["split"] == sp).most_common(1)[0][0] for sp in E.SPLITS}
    top10 = {w for w, _ in Counter(s["wallet"] for r in rows for s in r["snipers"]).most_common(10)}
    lines = [
        "# K. Checks added for the classification (%d permutations)" % E.N_PERM,
        "",
        "observed | null mean [95 %] | percentile | p | effect",
        "",
        "| subset | split | similar exit sizes (CV) | proceeds back to the first funder | re-funded by the same "
        "funder | fixed sniper-to-exit-wallet pairs |",
        "|---|---|---|---|---|---|",
    ]
    for sp in E.SPLITS:
        base = [r for r in rows if r["split"] == sp]
        for name, keep_r, keep_x in (
            ("all", lambda r: True, lambda x: True),
            (
                "without the dominant operator",
                lambda r, sp=sp: r["cluster"] != top_op[sp],
                lambda x, sp=sp: x["cluster"] != top_op[sp],
            ),
            (
                "without the 10 most frequent sniper wallets",
                lambda r: not ({s["wallet"] for s in r["snipers"]} & top10),
                lambda x: x["wallet"] not in top10,
            ),
        ):
            rr = [r for r in base if keep_r(r)]
            rt = [x for x in ret if x["split"] == sp and keep_x(x)]
            lines.append(
                "| %s | %s | %s | %s | %s | %s |"
                % (
                    name,
                    sp.upper(),
                    A.fmt_test(A.null_exit_size(rr)),
                    A.fmt_test(A.null_proceeds(rt)),
                    A.fmt_test(A.null_refund(rt)),
                    A.fmt_test(exit_pairs(rr)),
                )
            )
    cl = E.clusters(rows)
    grp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        grp[cl[r["mint"]]].append(r)
    multi = [rr for rr in grp.values() if len(rr) >= 2]
    nets = [network(rr) for rr in multi]
    lines += [
        "",
        "## The deployer funded by a non-hub wallet of its cluster's sniper network (multi-launch clusters)",
        "",
        "| split | launches | observed | null: another cluster's network |",
        "|---|---:|---|---|",
    ]
    for sp in E.SPLITS:
        obs = tot = 0
        for rr, net in zip(multi, nets):
            for r in rr:
                if r["split"] == sp:
                    tot += 1
                    obs += bool(dep_funders(r) & net)
        rng = random.Random(E.SEED)
        null = []
        for _ in range(E.N_PERM):
            n = 0
            for i, rr in enumerate(multi):
                for r in rr:
                    if r["split"] != sp:
                        continue
                    j = rng.randrange(len(multi) - 1)
                    j = j + 1 if j >= i else j
                    n += bool(dep_funders(r) & nets[j])
            null.append(float(n))
        t = E.perm_test(float(obs), null)
        lines.append(
            "| %s | %d | %d (%.0f %%) | %.1f [%.0f, %.0f], p %.4f |"
            % (sp.upper(), tot, obs, 100 * obs / tot, t["null_mean"], t["ci"][0], t["ci"][1], t["p"])
        )
    E.write("K_extra.md", lines)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
