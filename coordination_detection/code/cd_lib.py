#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cd_lib.py -- the measures of analysis_plan.md, computed from one launch's raw relations, so that the
observed data and every permutation go through the same code. No price and no label of any kind.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
TABLE = os.path.join(STUDY, "derived", "cd_table.jsonl.gz")
FREEZE = os.path.join(STUDY, "derived", "CD_FREEZE.json")
TABLES = os.path.join(STUDY, "tables")
SLOT_S = 0.4


def load() -> list[dict[str, Any]]:
    doc = json.load(open(FREEZE))
    if hashlib.sha256(open(TABLE, "rb").read()).hexdigest() != doc["sha256"]:
        sys.exit("the coordination table differs from the frozen one")
    with gzip.open(TABLE, "rt", encoding="utf8") as fh:
        return [json.loads(x) for x in fh]


def write(name: str, lines: list[str]) -> None:
    os.makedirs(TABLES, exist_ok=True)
    with open(os.path.join(TABLES, name), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")


def gini(v: Sequence[float]) -> Optional[float]:
    v = sorted(x for x in v if x is not None)
    n, s = len(v), sum(v)
    if n < 2 or s <= 0:
        return None
    return sum((2 * (i + 1) - n - 1) * x for i, x in enumerate(v)) / (n * s)


def hhi(v: Sequence[float]) -> Optional[float]:
    s = sum(v)
    return sum((x / s) ** 2 for x in v) if s > 0 else None


# ------------------------------------------------------------ axis 1: funding #
def funder_key(s: dict[str, Any], kind: str, strict: bool = False) -> Optional[str]:
    """The sniper's funder of that kind if it may be shared: a known hub never is; with strict, a funder
    whose hub status was never measured is not either. A sniper with no shareable funder gets its own key."""
    f = s.get("gen_funder") if kind == "gen" else s.get("last_funder")
    hub = s.get("gen_funder_hub") if kind == "gen" else s.get("last_funder_hub")
    if f is None:
        return None
    if hub is True or (strict and hub is None):
        return "own:" + s["wallet"]
    return f


def funding(sn: list[dict[str, Any]], kind: str, strict: bool = False) -> dict[str, Any]:
    keys = [funder_key(s, kind, strict) for s in sn]
    out: dict[str, Any] = {}
    if any(k is None for k in keys):
        return {"observed": False}
    c = Counter(keys)
    shared = max(c.values())
    amt_key = "gen_received" if kind == "gen" else "last_amount"
    by: dict[str, float] = defaultdict(float)
    for s, k in zip(sn, keys):
        by[k] += max(0.0, s.get(amt_key) or 0.0)
    top = max(c, key=lambda k: (c[k], by[k]))
    out.update(
        {
            "observed": True,
            "n_funders": len(c),
            "shared": shared,
            "ratio": shared / len(sn),
            "sol_share_top": by[top] / sum(by.values()) if sum(by.values()) > 0 else None,
            "hhi": hhi(list(by.values())),
            "gini": gini(list(by.values())),
            "ge2": shared >= 2,
            "ge3": shared >= 3,
            "ge4": shared >= 4,
            "majority": shared > len(sn) / 2,
        }
    )
    if kind == "gen":
        src: dict[str, set] = defaultdict(set)
        for s, k in zip(sn, keys):
            if s.get("source") and not k.startswith("own:"):
                src[s["source"]].add(k)
        out["n_sources"] = len(src)
        out["max_funders_per_source"] = max((len(v) for v in src.values()), default=0)
        out["same_source_2_funders"] = out["max_funders_per_source"] >= 2
        out["depth"] = statistics.median([2 if s.get("source") else 1 for s in sn])
    return out


# ------------------------------------------------------- axis 2: synchrony --- #
def sync(
    r: dict[str, Any], sn: Optional[list[dict[str, Any]]] = None, early_slots: Optional[list[int]] = None
) -> dict[str, Any]:
    sn = sn if sn is not None else r["snipers"]
    per_tx: Counter = Counter(sig for s in sn for sig in s["sigs"])
    out: dict[str, Any] = {
        "max_per_tx": max(per_tx.values()) if per_tx else 0,
        "share_multi_tx": sum(1 for s in sn if any(per_tx[g] >= 2 for g in s["sigs"])) / len(sn),
    }
    ages = [s["bt"] - s["last_bt"] for s in sn if s.get("last_bt") is not None and s.get("bt") is not None]
    if len(ages) == len(sn):
        out["fund_spread_s"] = max(ages) - min(ages)
        m = statistics.mean(ages)
        out["fund_age_cv"] = statistics.pstdev(ages) / m if m > 0 else None
        out["fund_age_median"] = statistics.median(ages)
    if early_slots is None:
        early_slots = sorted(e["slot"] - r["slot0"] for e in r["early"] if e["pre_alert"])
    out["n_early_pre"] = len(early_slots)
    if early_slots:
        c = Counter(early_slots)
        out["early_same_slot_share"] = sum(1 for x in early_slots if c[x] >= 2) / len(early_slots)
        for sec in (1, 5, 10):
            out["early_within_%ds" % sec] = sum(1 for x in early_slots if x * SLOT_S <= sec)
        gaps = [b - a for a, b in zip(early_slots, early_slots[1:])]
        if len(gaps) >= 2:
            m, sd = statistics.mean(gaps), statistics.pstdev(gaps)
            out["early_burstiness"] = (sd - m) / (sd + m) if sd + m > 0 else None
            out["early_gap_cv"] = sd / m if m > 0 else None
    return out


# -------------------------------------------------------- axis 3: tickets ---- #
def tickets(tk: list[float]) -> dict[str, Any]:
    pairs = list(combinations(tk, 2))
    s = sorted(tk, reverse=True)
    tot = sum(tk)
    sh = [x / tot for x in tk] if tot > 0 else []
    med = statistics.median(tk)
    return {
        "identical_pairs": sum(1 for a, b in pairs if abs(a - b) < 0.001),
        "near_identical_pairs": sum(1 for a, b in pairs if abs(a - b) / max(a, b) < 0.01),
        "round": sum(1 for x in tk if abs(x - round(x)) < 0.01),
        "near5": sum(1 for x in tk if abs(x - 5) <= 0.5),
        "near10": sum(1 for x in tk if abs(x - 10) <= 0.5),
        "near20": sum(1 for x in tk if abs(x - 20) <= 0.5),
        "max_over_median": s[0] / med if med else None,
        "hhi": hhi(tk),
        "gini": gini(tk),
        "entropy": (-sum(p * math.log(p) for p in sh if p > 0) / math.log(len(tk))) if len(tk) > 1 else None,
        "top1": s[0] / tot if tot else None,
        "top2": sum(s[:2]) / tot if tot else None,
        "top3": sum(s[:3]) / tot if tot else None,
    }


# ---------------------------------------------------------- axis 4: graph ---- #
def graph(r: dict[str, Any], sn: Optional[list[dict[str, Any]]] = None, strict: bool = False) -> dict[str, Any]:
    sn = sn if sn is not None else r["snipers"]
    adj: dict[str, set] = defaultdict(set)

    def edge(a: Optional[str], b: Optional[str]) -> None:
        if a and b and a != b:
            adj[a].add(b)
            adj[b].add(a)

    for s in sn:
        adj[s["wallet"]]
        g = funder_key(s, "gen", strict)
        if g and not g.startswith("own:"):
            edge(s["wallet"], g)
            edge(g, s.get("source"))
        lf = funder_key(s, "last", strict)
        if lf and not lf.startswith("own:"):
            edge(s["wallet"], lf)
    c = r["creator"]
    dep = c.get("wallet")
    if dep:
        adj[dep]
        if c.get("gen_funder") and not c.get("gen_funder_hub"):
            edge(dep, c["gen_funder"])
            edge(c["gen_funder"], c.get("source"))
        if (
            c.get("last_funder")
            and c.get("last_funder_hub") is not True
            and not (strict and c.get("last_funder_hub") is None)
        ):
            edge(dep, c["last_funder"])
    snip = {s["wallet"] for s in sn}

    def comps(skip: Optional[str] = None) -> list[set]:
        seen, out = set(), []
        for v in adj:
            if v in seen or v == skip:
                continue
            stack, comp = [v], set()
            seen.add(v)
            while stack:
                x = stack.pop()
                comp.add(x)
                for y in adj[x]:
                    if y not in seen and y != skip:
                        seen.add(y)
                        stack.append(y)
            out.append(comp)
        return out

    cs = comps()
    with_sn = [len(x & snip) for x in cs if x & snip]
    nv = len(adj)
    ne = sum(len(v) for v in adj.values()) / 2
    non_sn = [v for v in adj if v not in snip]
    top = max(non_sn, key=lambda v: len(adj[v] & snip), default=None)
    pairs_via_top = 0
    if top:
        before = {v: i for i, x in enumerate(cs) for v in x}
        after = {v: i for i, x in enumerate(comps(top)) for v in x}
        pairs_via_top = sum(
            1 for a, b in combinations(sorted(snip), 2) if before[a] == before[b] and after.get(a) != after.get(b)
        )
    dist = None
    if dep:
        frontier, d, seen = {dep}, 0, {dep}
        while frontier and dist is None:
            if frontier & snip:
                dist = d
                break
            nxt = {y for x in frontier for y in adj[x]} - seen
            seen |= nxt
            frontier, d = nxt, d + 1
    funders_of = {v: len(adj[v] & snip) for v in non_sn}
    near_dep = set()
    if dep:
        near_dep = {dep} | adj[dep] | {y for x in adj[dep] for y in adj[x]}
    arch_a = any(k >= 2 and v in near_dep for v, k in funders_of.items())
    arch_b = False
    for v in non_sn:
        fs = [y for y in adj[v] if y not in snip and funders_of.get(y, 0) >= 1]
        if len(fs) >= 2 and sum(funders_of[y] for y in fs) >= 2:
            arch_b = True
    shared = any(k >= 2 for k in funders_of.values())
    independent = max(with_sn) == 1 if with_sn else True
    arch = "A" if arch_a else "B" if arch_b else "SHARED" if shared else "INDEPENDENT" if independent else "OTHER"
    dep_comp = next((x for x in cs if dep in x), set()) if dep else set()
    return {
        "n_components_with_sniper": len(with_sn),
        "largest_component_snipers": max(with_sn) if with_sn else 0,
        "largest_share": (max(with_sn) / len(sn)) if with_sn else 0.0,
        "density": ne / (nv * (nv - 1) / 2) if nv > 1 else 0.0,
        "max_degree_to_snipers": max(funders_of.values(), default=0),
        "pairs_only_via_top": pairs_via_top,
        "deployer_distance": dist,
        "snipers_with_deployer": len(dep_comp & snip),
        "architecture": arch,
    }


# ---------------------------------------------------------- axis 5: reuse ---- #
def reuse_causal(rows: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per launch, from earlier alerts only: sniper pairs already snipers together, snipers already seen
    as snipers, non-hub funders already seen funding snipers, a ticket (to 0.01 SOL) already seen."""
    seen_pair: Counter = Counter()
    seen_w: Counter = Counter()
    seen_f: Counter = Counter()
    seen_tk: Counter = Counter()
    out = {}
    for r in sorted(rows, key=lambda z: z["t"]):
        ws = sorted({s["wallet"] for s in r["snipers"]})
        prs = list(combinations(ws, 2))
        fs = {
            k
            for s in r["snipers"]
            for k in (funder_key(s, "gen"), funder_key(s, "last"))
            if k and not k.startswith("own:")
        }
        tks = {round(s["ticket"], 2) for s in r["snipers"]}
        out[r["mint"]] = {
            "pairs_seen_before": sum(1 for p in prs if seen_pair[p] > 0),
            "snipers_seen_before": sum(1 for w in ws if seen_w[w] > 0),
            "funders_seen_before": sum(1 for f in fs if seen_f[f] > 0),
            "tickets_seen_before": sum(1 for x in tks if seen_tk[x] > 0),
        }
        for p in prs:
            seen_pair[p] += 1
        for w in ws:
            seen_w[w] += 1
        for f in fs:
            seen_f[f] += 1
        for x in tks:
            seen_tk[x] += 1
    return out


def co_occurrence(groups: Sequence[Sequence[str]]) -> Counter:
    c: Counter = Counter()
    for g in groups:
        for p in combinations(sorted(set(g)), 2):
            c[p] += 1
    return c
