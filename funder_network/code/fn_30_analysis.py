#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The analysis of analysis_plan.md sections 4 to 7 on the frozen study table (derived/fn_table.json.gz): destination
classes A-G, the funder -> destination map, cross-operator convergence (capital transfer, shared infrastructure and
common terminal kept apart), components, recycling, deployer relationships, terminal distributions, nulls A-D
(operator structure kept), robustness and time. No price is read (an audit hook refuses any price file).

Writes tables/B_map.md ... J_hypotheses.md and derived/FN_results.json.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import os
import random
import statistics
import sys
from collections import Counter, defaultdict
from typing import Any, Optional


def _no_price(event: str, args: tuple[Any, ...]) -> None:
    if event == "open" and args and isinstance(args[0], str) and "em_price" in args[0]:
        raise RuntimeError("a price file was opened: %s" % args[0])


sys.addaudithook(_no_price)

import fn_trace as N  # noqa: E402
import ed_lib as L  # noqa: E402
import ed_trace as T  # noqa: E402
import em_lib as E  # noqa: E402

TABLE = os.path.join(N.DERIVED, "fn_table.json.gz")
FREEZE = os.path.join(N.DERIVED, "FN_FREEZE.json")
INVENTORY = os.path.join(N.DERIVED, "inventory.json")
EXIT_TABLE = os.path.join(N.ROOT, "exit_destination", "derived", "ed_table.json.gz")
CLASSES = (
    "A known hub",
    "D deployer network",
    "E cross-operator network",
    "C operator-associated",
    "B other operator",
    "F new / unknown, keeps the SOL",
    "G unresolved",
)
INF = 1e18


def week(bt: float) -> str:
    y, w, _ = dt.datetime.fromtimestamp(bt, dt.timezone.utc).isocalendar()
    return "%d-W%02d" % (y, w)


def pct(a: float, b: float) -> str:
    return "%.0f %%" % (100 * a / b) if b else "n/a"


def fmt(d: dict[str, Any]) -> str:
    if not d:
        return "n/a"
    return "%.3g | %.3g [%.3g, %.3g] | %.0f %% | %.4f | %s" % (
        d["obs"],
        d["null_mean"],
        d["ci"][0],
        d["ci"][1],
        100 * d["pct"],
        d["p"],
        "n/a" if d["effect"] is None else "x%.2f" % d["effect"],
    )


def write(name: str, lines: list[str]) -> None:
    os.makedirs(N.TABLES, exist_ok=True)
    with open(os.path.join(N.TABLES, name), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")


class UF:
    def __init__(self) -> None:
        self.p: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: str, b: str) -> None:
        self.p[self.find(a)] = self.find(b)


class Data:
    def __init__(self) -> None:
        fz = json.load(open(FREEZE))
        if hashlib.sha256(open(TABLE, "rb").read()).hexdigest() != fz["sha256_table"]:
            sys.exit("the study table differs from the frozen one")
        self.tab = json.load(gzip.open(TABLE))
        self.pop = json.load(open(INVENTORY))["population"]
        self.rows = sorted(E.load(), key=lambda z: z["t"])
        self.byrow = {r["mint"]: r for r in self.rows}
        self.R = T.Roles(self.rows)
        self.prim = self.tab["primary"]
        self.ops = {w: set(p["operators"]) for w, p in self.pop.items()}
        self.split = {w: {x["split"] for x in p["sweeps"]} for w, p in self.pop.items()}
        # hubs: frozen fields and genesis_hop, the exit study's measures, this study's measures
        self.hubs = {a for a, h in self.R.hub.items() if h}
        for b in json.load(gzip.open(EXIT_TABLE))["branches"]:
            self.hubs |= {a for a, m in b["measured"].items() if m.get("hub")}
        self.nonhub = {a for a, h in self.R.hub.items() if h is False}
        # overlapping sample anchors read some transactions twice (FN_INTEGRITY.json): every transfer counts once,
        # the first branch it starts is kept and the number dropped is reported
        seen, keep = set(), []
        for x in self.tab["downs"]:
            k = (x["path"][1]["sig"], x["path"][0]["wallet"], x["path"][1]["wallet"])
            if k not in seen:
                seen.add(k)
                keep.append(x)
        self.dropped_duplicates = len(self.tab["downs"]) - len(keep)
        self.tab["downs"] = keep
        self.paths = self.tab["ups"] + self.tab["downs"]
        for x in self.paths:
            for a, m in x["measured"].items():
                if m.get("status") == "hub":
                    self.hubs.add(a)
                elif m.get("status") == "read":
                    self.nonhub.add(a)
            if x["terminal"] == "hub measured":
                self.hubs.add(x["path"][-1]["wallet"])
        # operator ties (frozen) and deployer network, with the time each becomes visible
        self.ties: dict[str, dict[str, float]] = defaultdict(dict)
        self.dep: dict[str, float] = {}
        self.nlaunch: dict[str, set[str]] = defaultdict(set)

        def tie(a: Optional[str], op: str, t: float, mint: str) -> None:
            if a:
                self.ties[a][op] = min(self.ties[a].get(op, INF), t)
                self.nlaunch[a].add(mint)

        for r in self.rows:
            op, t, m = r["cluster"], r["t_create"], r["mint"]
            cr = r["creator"]
            tie(cr.get("wallet"), op, t, m)
            if cr.get("wallet"):
                self.dep[cr["wallet"]] = min(self.dep.get(cr["wallet"], INF), t)
            for k in ("gen_funder", "last_funder"):
                if cr.get(k) and cr.get(k + "_hub") is not True:
                    tie(cr[k], op, t, m)
                    self.dep[cr[k]] = min(self.dep.get(cr[k], INF), t)
            for s in r["snipers"]:
                tie(s["wallet"], op, t, m)
                for k in ("gen_funder", "last_funder"):
                    if s.get(k) and s.get(k + "_hub") is not True:
                        tie(s[k], op, t, m)
                if isinstance(s.get("source"), str):
                    tie(s["source"], op, t, m)
                for x in s["exits_full"]:
                    if x["kind"] == "transfer":
                        for o in x["recipients"]:
                            tie(o, op, t, m)
        for w, p in self.pop.items():
            t0 = min([x["bt"] for x in p["sweeps"]] + [x["bt"] for x in p["fundings"] if x["bt"]])
            for op in p["operators"]:
                self.ties[w][op] = min(self.ties[w].get(op, INF), t0)
        # frozen funding events, for recycling
        self.fund: dict[str, list[tuple[float, str, str]]] = defaultdict(list)
        for r in self.rows:
            for s in r["snipers"]:
                if s.get("last_funder") and s.get("last_bt"):
                    self.fund[s["last_funder"]].append((s["last_bt"], r["mint"], "sniper"))
            cr = r["creator"]
            if cr.get("last_funder") and cr.get("last_bt"):
                self.fund[cr["last_funder"]].append((cr["last_bt"], r["mint"], "deployer"))
        for v in self.fund.values():
            v.sort()
        self.reach = self._reach(self.paths)
        self.snipers: dict[str, set[str]] = defaultdict(set)
        self.exits: dict[str, set[str]] = defaultdict(set)
        for r in self.rows:
            for s in r["snipers"]:
                self.snipers[s["wallet"]].add(r["cluster"])
                for x in s["exits_full"]:
                    if x["kind"] == "transfer":
                        for o in x["recipients"]:
                            self.exits[o].add(r["cluster"])

    def role(self, a: str, src_ops: set[str]) -> str:
        """Role of a direct destination of a primary wallet (section 5, recycling)."""
        if self.is_hub(a):
            return "known hub"
        if a in self.snipers:
            return "sniper, same operator" if self.snipers[a] & src_ops else "sniper, another operator"
        if a in self.dep:
            return "deployer network"
        if a in self.pop:
            if self.ops[a] & src_ops:
                return "another funder or collector, same operator"
            return "another funder or collector, another operator"
        if a in self.exits:
            return "exit wallet"
        if a in self.ties:
            return "other known wallet"
        return "previously unseen wallet"

    def is_hub(self, a: str) -> bool:
        return a in self.hubs

    def ops_at(self, a: str, bt: float) -> set[str]:
        return {o for o, t in self.ties.get(a, {}).items() if t <= bt}

    def _reach(self, paths: list[dict[str, Any]]) -> dict[str, set[str]]:
        out: dict[str, set[str]] = defaultdict(set)
        for x in paths:
            for n in x["path"][1:]:
                if n["wallet"]:
                    out[n["wallet"]] |= self.ops[x["primary"]]
        return out

    def classify(self, x: dict[str, Any]) -> str:
        """Section 4, for the terminal of a path."""
        t = x["terminal"] or ""
        last = x["path"][-1]
        a, bt = last["wallet"], last.get("bt") or 0
        if t in ("hub", "hub measured") or (a and self.is_hub(a)):
            return "A known hub"
        if t == "retained":
            return "F new / unknown, keeps the SOL"
        if t not in ("known", "population"):
            return "G unresolved"
        if self.dep.get(a, INF) <= bt:
            return "D deployer network"
        ops = self.ops_at(a, bt) | self.reach.get(a, set())
        if len(ops) >= 2:
            return "E cross-operator network"
        if ops and ops <= self.ops[x["primary"]]:
            return "C operator-associated"
        return "B other operator"


# ---------------------------------------------------------------- the graph --- #
def incidence(D: Data, paths: list[dict[str, Any]], strict: bool = False) -> list[tuple[str, str]]:
    """(primary, wallet) for every non-hub wallet on a path (strict: only wallets with a measured non-hub
    status)."""
    out = set()
    for x in paths:
        for n in x["path"][1:]:
            a = n["wallet"]
            if not a or D.is_hub(a) or a == x["primary"]:
                continue
            if strict and a not in D.nonhub and a not in D.pop:
                continue
            out.add((x["primary"], a))
    return sorted(out)


def stats(D: Data, inc: list[tuple[str, str]], ops: dict[str, set[str]]) -> dict[str, Any]:
    """Wallets tied to two operators or more through the primaries, and operator components."""
    by: dict[str, set[str]] = defaultdict(set)
    for p, a in inc:
        by[a] |= ops.get(p, set())
    shared = {a: o for a, o in by.items() if len(o) >= 2}
    uf = UF()
    for p, o in ops.items():
        o = sorted(o)
        for i in range(1, len(o)):
            uf.union("O:" + o[0], "O:" + o[i])
    for p, a in inc:
        for o in ops.get(p, set()):
            uf.union("O:" + o, "W:" + a)
    for a in D.pop:  # a primary wallet reached by another primary's path joins both operators
        if a in by:
            for o in ops.get(a, set()):
                uf.union("O:" + o, "W:" + a)
    comp: dict[str, set[str]] = defaultdict(set)
    for o in {o for s in ops.values() for o in s}:
        comp[uf.find("O:" + o)].add(o)
    sizes = sorted((len(v) for v in comp.values()), reverse=True)
    return {
        "shared": len(shared),
        "shared_wallets": shared,
        "largest": sizes[0] if sizes else 0,
        "components": len(sizes),
        "sizes": sizes,
    }


def null_swaps(
    D: Data,
    inc: list[tuple[str, str]],
    ops: dict[str, set[str]],
    key: str,
    cross_only: bool = False,
    n_perm: int = L.N_PERM,
) -> dict[str, Any]:
    obs = stats(D, inc, ops)[key]
    rng = random.Random(L.SEED)
    null = []
    for _ in range(n_perm):
        e = list(inc)
        have = set(e)
        for _ in range(3 * len(e)):
            i, j = rng.randrange(len(e)), rng.randrange(len(e))
            (p1, a1), (p2, a2) = e[i], e[j]
            if p1 == p2 or a1 == a2 or (p1, a2) in have or (p2, a1) in have:
                continue
            if cross_only and ops.get(p1) == ops.get(p2):
                continue
            have -= {(p1, a1), (p2, a2)}
            have |= {(p1, a2), (p2, a1)}
            e[i], e[j] = (p1, a2), (p2, a1)
        null.append(float(stats(D, e, ops)[key]))
    return E.perm_test(float(obs), null)


def null_labels(
    D: Data, inc: list[tuple[str, str]], ops: dict[str, set[str]], key: str, n_perm: int = L.N_PERM
) -> dict[str, Any]:
    obs = stats(D, inc, ops)[key]
    rng = random.Random(L.SEED)
    prims = sorted(ops)
    null = []
    for _ in range(n_perm):
        lab = E.shuffled(rng, [ops[p] for p in prims])
        null.append(float(stats(D, inc, dict(zip(prims, lab)))[key]))
    return E.perm_test(float(obs), null)


# -------------------------------------------------------------- recycling --- #
def recycle(D: Data, x: dict[str, Any]) -> Optional[dict[str, Any]]:
    if x["direction"] != "down":
        return None
    best = None
    for n in x["path"][1:]:
        for t, mint, role in D.fund.get(n["wallet"], []):
            if t <= (n.get("bt") or 0):
                continue
            if best is None or t < best["t"]:
                best = {"wallet": n["wallet"], "t": t, "mint": mint, "role": role}
            break
    if not best:
        return None
    r = D.byrow[best["mint"]]
    src_ops = D.ops[x["primary"]]
    best["delay_s"] = best["t"] - x["path"][1]["bt"]
    best["sol"] = x["path"][1]["sol"]
    best["operator"] = r["cluster"]
    best["same_operator"] = r["cluster"] in src_ops
    best["to_population"] = best["wallet"] in D.pop
    best["kind"] = (
        "deployer funding"
        if best["role"] == "deployer"
        else "same operator's snipers"
        if best["same_operator"]
        else "another operator's snipers"
    )
    return best


def null_recycle(D: Data, links: list[dict[str, Any]], srcs: list[set[str]], n_perm: int = L.N_PERM) -> dict[str, Any]:
    obs = sum(1 for k in links if k["same_operator"]) / len(links) if links else 0.0
    ev_by_week: dict[str, list[str]] = defaultdict(list)
    for v in D.fund.values():
        for t, mint, _ in v:
            ev_by_week[week(t)].append(D.byrow[mint]["cluster"])
    rng = random.Random(L.SEED)
    null = []
    for _ in range(n_perm):
        n = 0
        for k, s in zip(links, srcs):
            pool = ev_by_week[week(k["t"])]
            n += pool[rng.randrange(len(pool))] in s
        null.append(n / len(links) if links else 0.0)
    return E.perm_test(obs, null)


# --------------------------------------------------------------- sections --- #
def section_b(D: Data) -> dict[str, Any]:
    prim = D.prim
    lines = [
        "# B. Funder -> destination map",
        "",
        "Primary wallets: %d (%d short-lived, %d very active). Upstream chains %d, downstream branches %d."
        % (
            len(prim),
            sum(p["kind"] == "short-lived" for p in prim.values()),
            sum(p["kind"] == "very active" for p in prim.values()),
            len(D.tab["ups"]),
            len(D.tab["downs"]),
        ),
        "",
        "## Upstream: who funded the primary wallets (terminal class of each chain)",
        "",
        "| class | chains | operators | hops to terminal (median) |",
        "|---|---:|---:|---:|",
    ]
    out: dict[str, Any] = {}
    for direction, title in (("up", None), ("down", "## Downstream: where their outgoing SOL goes")):
        xs = [x for x in D.paths if x["direction"] == direction]
        if title:
            lines += [
                "",
                title,
                "",
                "| class | branches | SOL | operators | hops to terminal (median) |",
                "|---|---:|---:|---:|---:|",
            ]
        c = Counter(D.classify(x) for x in xs)
        out[direction] = {}
        for k in CLASSES:
            sub = [x for x in xs if D.classify(x) == k]
            if not sub:
                continue
            opsn = len({o for x in sub for o in D.ops[x["primary"]]})
            hops = statistics.median([len(x["path"]) - 1 for x in sub])
            if direction == "up":
                lines.append("| %s | %d | %d | %g |" % (k, c[k], opsn, hops))
            else:
                lines.append(
                    "| %s | %d | %.1f | %d | %g |" % (k, c[k], sum(x["path"][1]["sol"] for x in sub), opsn, hops)
                )
            out[direction][k] = {"n": c[k], "sol": sum((x["path"][1].get("sol") or 0) for x in sub), "operators": opsn}
        reasons = Counter(x["terminal"] for x in xs if D.classify(x) == "G unresolved")
        lines.append("")
        lines.append(
            "Unresolved (%s): %s" % (direction, ", ".join("%s %d" % kv for kv in reasons.most_common()) or "none")
        )
    st = Counter(str((p.get("upstream_start") or {}).get("status")).split(":")[0] for p in prim.values())
    en = Counter(
        str((p.get("end") or {}).get("status")).split(":")[0] for p in prim.values() if p["kind"] == "short-lived"
    )
    lines += [
        "",
        "Upstream starts: " + ", ".join("%s %d" % kv for kv in st.most_common()),
        "Ends of the short-lived wallets: " + ", ".join("%s %d" % kv for kv in en.most_common()),
    ]
    ends = [p["end"] for p in prim.values() if p["kind"] == "short-lived" and p.get("end", {}).get("status") == "read"]
    if ends:
        lines.append(
            "Short-lived wallets: transactions after their last sweep and before TEST start, median %s; "
            "still active after TEST start: %d."
            % (statistics.median([e["n_after_last_sweep"] for e in ends]), sum(1 for e in ends if e.get("after_test")))
        )
    cls = Counter()
    for w, fl in D.tab["reads"].items():
        for f in fl:
            if f.get("origin") == "sample":
                cls[f["class"]] += 1
    lines += [
        "",
        "## Very active wallets: the sampled transactions",
        "",
        ", ".join("%s %d" % kv for kv in cls.most_common()) or "none",
    ]
    out["sample"] = dict(cls)
    write("B_map.md", lines)
    return out


def section_c(D: Data) -> dict[str, Any]:
    inc = incidence(D, D.paths)
    st = stats(D, inc, D.ops)
    lines = [
        "# C. Cross-operator convergence",
        "",
        "Non-hub wallets reached on any path (upstream or downstream, any hop): %d; reached from one operator "
        "only %d, from two %d, from three or more %d."
        % (
            len({a for _, a in inc}),
            sum(1 for a in {a for _, a in inc} if len(D.reach[a]) == 1),
            sum(1 for a in {a for _, a in inc} if len(D.reach[a]) == 2),
            sum(1 for a in {a for _, a in inc} if len(D.reach[a]) >= 3),
        ),
        "",
        "| destination | operators | primary wallets | launches (frozen) | SOL on paths | first | last | role | "
        "relation |",
        "|---|---:|---:|---:|---:|---|---|---|---|",
    ]
    rows = []
    for a, opset in sorted(st["shared_wallets"].items(), key=lambda kv: (-len(kv[1]), kv[0])):
        xs = [x for x in D.paths if a in [n["wallet"] for n in x["path"][1:]]]
        sol = sum((n.get("sol") or 0) for x in xs for n in x["path"][1:] if n["wallet"] == a)
        bts = [n["bt"] for x in xs for n in x["path"][1:] if n["wallet"] == a and n.get("bt")]
        dirs = {x["direction"] for x in xs}
        term = all(x["path"][-1]["wallet"] == a for x in xs)
        rel = (
            "common upstream source"
            if dirs == {"up"}
            else "common terminal"
            if term and dirs == {"down"}
            else "shared intermediary or mixed"
        )
        role = (
            "population"
            if a in D.pop
            else "deployer network"
            if a in D.dep
            else "frozen, %d operators" % len(D.ties.get(a, {}))
            if a in D.ties
            else "unseen"
        )
        rows.append(
            {
                "wallet": a,
                "operators": sorted(opset),
                "primaries": len({x["primary"] for x in xs}),
                "launches": len(D.nlaunch.get(a, ())),
                "sol": sol,
                "first": min(bts) if bts else None,
                "last": max(bts) if bts else None,
                "relation": rel,
                "role": role,
            }
        )
        lines.append(
            "| %s | %d | %d | %d | %.1f | %s | %s | %s | %s |"
            % (
                a[:10],
                len(opset),
                len({x["primary"] for x in xs}),
                len(D.nlaunch.get(a, ())),
                sol,
                week(min(bts)) if bts else "-",
                week(max(bts)) if bts else "-",
                role,
                rel,
            )
        )
    # capital transfers between operators: a path from one operator's primary ending at another operator's wallet
    transfers = []
    for x in D.paths:
        last = x["path"][-1]
        a = last["wallet"]
        if x["terminal"] not in ("known", "population") or not a:
            continue
        tgt = D.ops_at(a, last.get("bt") or 0)
        src = D.ops[x["primary"]]
        if tgt and not (tgt & src):
            transfers.append(
                {
                    "direction": x["direction"],
                    "from_ops": sorted(src),
                    "to_ops": sorted(tgt),
                    "wallet": a,
                    "sol": x["path"][1].get("sol"),
                    "hops": len(x["path"]) - 1,
                    "primary": x["primary"],
                }
            )
    lines += [
        "",
        "Capital transfers between operators (a path from one operator's primary wallet ending at a wallet "
        "tied only to other operators, upstream paths read as flowing into the primary): %d." % len(transfers),
    ]
    for t in transfers[:20]:
        lines.append(
            "- %s %s: %s %s %s (%s hops, %.2f SOL)"
            % (
                t["direction"],
                t["primary"][:8],
                "/".join(o[:12] for o in t["from_ops"]),
                "<-" if t["direction"] == "up" else "->",
                "/".join(o[:12] for o in t["to_ops"]),
                t["hops"],
                t["sol"] or 0,
            )
        )
    multi = {w: o for w, o in D.ops.items() if len(o) >= 2}
    lines += [
        "",
        "Shared infrastructure already in the frozen data: primary wallets serving two operators or more: "
        + (", ".join("%s (%s)" % (w[:8], ", ".join(sorted(o))) for w, o in multi.items()) or "none")
        + ".",
        "",
        "Operator components (operators joined by a shared non-hub wallet, a path into another operator's "
        "wallet, or a primary wallet serving both): %d components, sizes %s; operators in the largest: %d of %d."
        % (st["components"], st["sizes"], st["largest"], len({o for s in D.ops.values() for o in s})),
    ]
    write("C_convergence.md", lines)
    return {
        "stats": {k: v for k, v in st.items() if k != "shared_wallets"},
        "shared": rows,
        "transfers": transfers,
        "multi_operator_primaries": {w: sorted(o) for w, o in multi.items()},
    }


def section_d(D: Data) -> dict[str, Any]:
    inc = incidence(D, D.paths)
    uf = UF()
    for p, a in inc:
        uf.union("P:" + p, "W:" + a)
    for a in D.pop:
        if a in D.reach:
            uf.union("P:" + a, "W:" + a)
    comps: dict[str, list[str]] = defaultdict(list)
    for p in D.prim:
        comps[uf.find("P:" + p)].append(p)
    lines = [
        "# D. Network components (primary wallets joined by shared non-hub wallets)",
        "",
        "| component | primary wallets | operators | launches | downstream wallets | SOL on downstream paths | "
        "architecture |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    out = []
    for i, (c, ps) in enumerate(sorted(comps.items(), key=lambda kv: (-len(kv[1]), kv[0]))):
        opsn = {o for p in ps for o in D.ops[p]}
        launches = {x["mint"] for p in ps for x in D.pop[p]["sweeps"]}
        downs = [x for x in D.tab["downs"] if x["primary"] in ps]
        dw = {n["wallet"] for x in downs for n in x["path"][1:]}
        arch = Counter(D.classify(x) for x in downs).most_common(2)
        out.append(
            {
                "primaries": sorted(ps),
                "operators": sorted(opsn),
                "launches": len(launches),
                "downstream_wallets": len(dw),
                "sol": sum(x["path"][1]["sol"] for x in downs),
                "architecture": arch,
            }
        )
        if len(ps) >= 2 or i < 15:
            lines.append(
                "| %d | %d | %d | %d | %d | %.1f | %s |"
                % (
                    i + 1,
                    len(ps),
                    len(opsn),
                    len(launches),
                    len(dw),
                    sum(x["path"][1]["sol"] for x in downs),
                    ", ".join("%s %d" % kv for kv in arch) or "-",
                )
            )
    lines += [
        "",
        "Components: %d; with two primary wallets or more: %d; spanning two operators or more: %d."
        % (len(out), sum(1 for c in out if len(c["primaries"]) >= 2), sum(1 for c in out if len(c["operators"]) >= 2)),
    ]
    write("D_components.md", lines)
    return {"components": out}


def section_e(D: Data) -> dict[str, Any]:
    links, srcs = [], []
    for x in D.tab["downs"]:
        r = recycle(D, x)
        if r:
            links.append(dict(r, primary=x["primary"]))
            srcs.append(D.ops[x["primary"]])
    lines = [
        "# E. Capital recycling",
        "",
        "## Direct destinations of the primary wallets' outgoing SOL",
        "",
        "| destination | transfers | SOL | primary wallets | operators |",
        "|---|---:|---:|---:|---:|",
    ]
    dr: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in D.tab["downs"]:
        dr[D.role(x["path"][1]["wallet"], D.ops[x["primary"]])].append(x)
    for k, xs in sorted(dr.items(), key=lambda kv: -len(kv[1])):
        lines.append(
            "| %s | %d | %.1f | %d | %d |"
            % (
                k,
                len(xs),
                sum(x["path"][1]["sol"] for x in xs),
                len({x["primary"] for x in xs}),
                len({o for x in xs for o in D.ops[x["primary"]]}),
            )
        )
    lines += [
        "",
        "## Indirect: a wallet on a downstream path that later funds a frozen launch",
        "",
        "Downstream branches %d; reaching a wallet that later funds a sniper or deployer: %d."
        % (len(D.tab["downs"]), len(links)),
    ]
    c = Counter(k["kind"] for k in links)
    lines += ["", "| relation | links | SOL | delay median (min) | repeated pairs |", "|---|---:|---:|---:|---:|"]
    for k, n in c.most_common():
        sub = [x for x in links if x["kind"] == k]
        rep = Counter((x["primary"], x["wallet"]) for x in sub)
        lines.append(
            "| %s | %d | %.1f | %.0f | %d |"
            % (
                k,
                n,
                sum(x["sol"] or 0 for x in sub),
                statistics.median([x["delay_s"] / 60 for x in sub]),
                sum(1 for v in rep.values() if v >= 2),
            )
        )
    lines.append("")
    lines.append(
        "Recycling into a population wallet (another funder or collector of the 62): %d."
        % sum(1 for k in links if k["to_population"])
    )
    cross = [k for k in links if not k["same_operator"]]
    for k in cross[:10]:
        lines.append(
            "- %s -> %s funds %s of %s (%s), %.0f min later"
            % (k["primary"][:8], k["wallet"][:8], k["role"], k["mint"][:8], k["operator"][:14], k["delay_s"] / 60)
        )
    t = null_recycle(D, links, srcs) if links else {}
    lines += [
        "",
        "Null D (recipient launches drawn from the frozen funding events of the same ISO week): share to "
        "the same operator %s" % fmt(t),
    ]
    write("E_recycling.md", lines)
    return {
        "links": len(links),
        "kinds": dict(c),
        "null": t,
        "cross": cross,
        "direct": {k: {"n": len(v), "sol": sum(x["path"][1]["sol"] for x in v)} for k, v in dr.items()},
    }


def section_f(D: Data) -> dict[str, Any]:
    rows = []
    for x in D.paths:
        for i, n in enumerate(x["path"][1:], start=1):
            a = n["wallet"]
            if a and D.dep.get(a, INF) <= (n.get("bt") or 0) and not D.is_hub(a):
                own = bool(D.ops_at(a, n.get("bt") or 0) & D.ops[x["primary"]])
                rows.append(
                    {
                        "primary": x["primary"],
                        "direction": x["direction"],
                        "hop": i,
                        "wallet": a,
                        "own_operator": own,
                        "strict": a in D.nonhub,
                    }
                )
                break
    lines = ["# F. Deployer relationships (strict non-hub)", "", "| | paths | primary wallets |", "|---|---:|---:|"]
    for name, f in (
        ("direct (hop 1)", lambda r: r["hop"] == 1),
        ("indirect (hops 2-5)", lambda r: r["hop"] >= 2),
        ("own operator's deployer network", lambda r: r["own_operator"]),
        ("another operator's deployer network", lambda r: not r["own_operator"]),
        ("measured non-hub status", lambda r: r["strict"]),
    ):
        sub = [r for r in rows if f(r)]
        lines.append("| %s | %d | %d |" % (name, len(sub), len({r["primary"] for r in sub})))
    lines += ["", "By direction: " + ", ".join("%s %d" % kv for kv in Counter(r["direction"] for r in rows).items())]
    write("F_deployer.md", lines)
    return {"rows": rows}


def section_g(D: Data) -> dict[str, Any]:
    lines = [
        "# G. Terminal destinations (downstream, share of SOL by class)",
        "",
        "| level | unit | SOL | " + " | ".join(k.split(" ")[0] for k in CLASSES) + " |",
        "|---|---|---:|" + "---:|" * len(CLASSES),
    ]
    out: dict[str, Any] = {"primary": {}, "operator": {}}

    def row(level: str, unit: str, xs: list[dict[str, Any]]) -> dict[str, float]:
        tot = sum(x["path"][1]["sol"] for x in xs)
        d = {k: sum(x["path"][1]["sol"] for x in xs if D.classify(x) == k) / tot if tot else 0.0 for k in CLASSES}
        lines.append(
            "| %s | %s | %.1f | %s |" % (level, unit, tot, " | ".join("%.0f %%" % (100 * d[k]) for k in CLASSES))
        )
        return d

    downs = D.tab["downs"]
    row("all", "all", downs)
    by_op: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in downs:
        for o in D.ops[x["primary"]]:
            by_op[o].append(x)
    for o, xs in sorted(by_op.items(), key=lambda kv: -len(kv[1])):
        out["operator"][o] = row("operator", o[:16], xs)
    binary = sum(1 for d in out["operator"].values() if max(d.values()) >= 0.99)
    lines += [
        "",
        "Operators whose downstream SOL goes entirely (99 %% or more) to one class: %d of %d."
        % (binary, len(out["operator"])),
    ]
    by_p: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in downs:
        by_p[x["primary"]].append(x)
    for p, xs in sorted(by_p.items(), key=lambda kv: -len(kv[1])):
        out["primary"][p] = row("primary", p[:10], xs)
    write("G_terminals.md", lines)
    out["binary_operators"] = binary
    return out


def subsets(D: Data) -> list[tuple[str, list[dict[str, Any]], dict[str, set[str]], bool]]:
    opc = Counter(o for s in D.ops.values() for o in s)
    top = opc.most_common(1)[0][0]
    top10 = {
        w for w, _ in sorted(((w, len(p["sweeps"])) for w, p in D.pop.items()), key=lambda kv: (-kv[1], kv[0]))[:10]
    }

    def keep(ws: set[str]) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
        return [x for x in D.paths if x["primary"] in ws], {w: o for w, o in D.ops.items() if w in ws}

    allw = set(D.pop)
    out = [
        ("full", *keep(allw), False),
        ("without the dominant operator (%s)" % top[:14], *keep({w for w in allw if top not in D.ops[w]}), False),
        ("without the 10 primary wallets with the most sweeps", *keep(allw - top10), False),
        (
            "known non-hub (paths through a hub removed)",
            [x for x in D.paths if not any(D.is_hub(n["wallet"]) for n in x["path"][1:] if n["wallet"])],
            D.ops,
            False,
        ),
        ("strict non-hub", D.paths, D.ops, True),
        ("TRAIN", *keep({w for w in allw if "train" in D.split[w]}), False),
        ("VALIDATION", *keep({w for w in allw if "val" in D.split[w]}), False),
    ]
    return out


def section_h(D: Data) -> dict[str, Any]:
    lines = [
        "# H. Nulls and robustness (%d permutations)" % L.N_PERM,
        "",
        "Each test: observed | null mean [95 %] | percentile | p | effect.",
        "",
        "| subset | primary wallets | shared non-hub wallets (2+ operators) | operators in the largest component | "
        "null A (swaps): shared | null B (labels): shared | null C (cross-operator swaps): shared | null A: largest |",
        "|---|---:|---:|---:|---|---|---|---|",
    ]
    res = {}
    for name, paths, ops, strict in subsets(D):
        inc = incidence(D, paths, strict)
        st = stats(D, inc, ops)
        tests = {
            "A_shared": null_swaps(D, inc, ops, "shared") if inc else {},
            "B_shared": null_labels(D, inc, ops, "shared") if inc else {},
            "C_shared": null_swaps(D, inc, ops, "shared", cross_only=True) if inc else {},
            "A_largest": null_swaps(D, inc, ops, "largest") if inc else {},
        }
        res[name] = {"n": len(ops), "shared": st["shared"], "largest": st["largest"], "tests": tests}
        lines.append(
            "| %s | %d | %d | %d | %s | %s | %s | %s |"
            % (
                name,
                len(ops),
                st["shared"],
                st["largest"],
                fmt(tests["A_shared"]),
                fmt(tests["B_shared"]),
                fmt(tests["C_shared"]),
                fmt(tests["A_largest"]),
            )
        )
    # leave one wallet out
    inc = incidence(D, D.paths)
    base = stats(D, inc, D.ops)
    loo = []
    for a in sorted(base["shared_wallets"]):
        st = stats(D, [(p, b) for p, b in inc if b != a], D.ops)
        loo.append((a, st["shared"], st["largest"]))
    lines += [
        "",
        "Leave one shared wallet out (full sample: %d shared, largest component %d operators): %s"
        % (
            base["shared"],
            base["largest"],
            "; ".join("without %s: %d shared, largest %d" % (a[:8], s, g) for a, s, g in loo) or "no shared wallet",
        ),
    ]
    # time
    wk = defaultdict(set)
    for x in D.paths:
        for n in x["path"][1:]:
            if n["wallet"] in base["shared_wallets"] and n.get("bt"):
                wk[n["wallet"]].add(week(n["bt"]))
    lines += ["", "## Time: ISO weeks in which each shared wallet appears on a path", ""] + [
        "- %s: %s" % (a[:10], ", ".join(sorted(w))) for a, w in sorted(wk.items())
    ]
    write("H_nulls_robustness.md", lines)
    return {"subsets": res, "leave_one_out": loo, "weeks": {a: sorted(w) for a, w in wk.items()}}


def section_i(D: Data, comps: list[dict[str, Any]]) -> None:
    lines = [
        "# I. Behavioural network fingerprints (components with two primary wallets or more, or two operators)",
        "",
        "No intent and no owner are attached to a component.",
        "",
    ]
    for i, c in enumerate(comps):
        if len(c["primaries"]) < 2 and len(c["operators"]) < 2:
            continue
        ps = c["primaries"]
        ups = [x for x in D.tab["ups"] if x["primary"] in ps]
        downs = [x for x in D.tab["downs"] if x["primary"] in ps]
        sw = [s for p in ps for s in D.pop[p]["sweeps"]]
        weeks = sorted({week(s["bt"]) for s in sw})
        rec = sum(1 for x in downs if recycle(D, x))
        lines += [
            "## Component %d" % (i + 1),
            "",
            "- operators: %s" % ", ".join(o[:16] for o in c["operators"]),
            "- primary wallets: %d (%s)" % (len(ps), ", ".join("%s %s" % (p[:8], D.prim[p]["kind"]) for p in ps[:8])),
            "- upstream sources: %s" % ", ".join("%s %d" % kv for kv in Counter(D.classify(x) for x in ups).items()),
            "- downstream terminals: %s"
            % ", ".join("%s %d" % kv for kv in Counter(D.classify(x) for x in downs).items()),
            "- recurring wallets on its paths: %d"
            % sum(
                1
                for a, o in D.reach.items()
                if a not in D.pop
                and any(a in [n["wallet"] for n in x["path"][1:]] for x in ups + downs)
                and len(D.nlaunch.get(a, ())) >= 2
            ),
            "- capital recycled into a later launch: %d of %d branches" % (rec, len(downs)),
            "- sweeps received: %d, ISO weeks active: %s" % (len(sw), ", ".join(weeks)),
            "",
        ]
    write("I_fingerprint.md", lines)


def section_j(D: Data, s: dict[str, Any]) -> None:
    c = s["C"]["stats"]
    lines = [
        "# J. Hypothesis comparison",
        "",
        "| observation | value | H1 one common network | H2 common execution infrastructure | H3 separate "
        "operator networks | H4 independent traders |",
        "|---|---|---|---|---|---|",
        "| non-hub wallets reached from two operators or more | %d | expected, many | expected at the tool's "
        "wallets | few or none | none |" % c["shared"],
        "| operators in the largest component | %d of %d | most | most, through the tool | small "
        "components | single operators |" % (c["largest"], len({o for v in D.ops.values() for o in v})),
        "| capital transfers between operators | %d | expected | not required | none | none |"
        % len(s["C"]["transfers"]),
        "| primary wallets serving two operators (frozen) | %d | expected | expected | none | none |"
        % len(s["C"]["multi_operator_primaries"]),
        "| recycling into another operator's launches | %d of %d links | expected | possible (service funds "
        "clients) | none | none |" % (s["E"]["kinds"].get("another operator's snipers", 0), s["E"]["links"]),
        "| operators whose downstream SOL goes to one class only | %d of %d | - | - | expected | - |"
        % (s["G"]["binary_operators"], len(s["G"]["operator"])),
    ]
    write("J_hypotheses.md", lines)


def main() -> None:
    D = Data()
    s: dict[str, Any] = {
        "coverage": {
            "calls": D.tab["calls"],
            "stopped": D.tab["stopped"],
            "primary": len(D.prim),
            "ups": len(D.tab["ups"]),
            "downs": len(D.tab["downs"]),
            "dropped_duplicate_branches": D.dropped_duplicates,
        }
    }
    s["B"] = section_b(D)
    s["C"] = section_c(D)
    s["D"] = section_d(D)
    s["E"] = section_e(D)
    s["F"] = section_f(D)
    s["G"] = section_g(D)
    s["H"] = section_h(D)
    section_i(D, s["D"]["components"])
    section_j(D, s)
    with open(os.path.join(N.DERIVED, "FN_results.json"), "w") as fh:
        json.dump(s, fh, indent=1, sort_keys=True, default=str)
    print(json.dumps({k: s[k] for k in ("coverage",)}, indent=1, default=str))
    print("C", json.dumps(s["C"]["stats"], default=str))
    print("E", s["E"]["links"], s["E"]["kinds"])


if __name__ == "__main__":
    main()
