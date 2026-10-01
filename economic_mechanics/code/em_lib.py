#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
em_lib.py -- the measures of analysis_plan.md from the frozen economic-mechanics table: groups from the
frozen coordination labels, architectures, funding, lifecycle, supply and exit measures, and the null
models. No price is read here (the price file is read by the price-impact section only).
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import random
import statistics
import sys
from collections import Counter
from typing import Any, Callable, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "post_detection_forensics", "code"))
import feat_30_build as FB  # noqa: E402

TABLE = os.path.join(STUDY, "derived", "em_table.jsonl.gz")
PRICE = os.path.join(STUDY, "derived", "em_price.jsonl.gz")
FREEZE = os.path.join(STUDY, "derived", "EM_FREEZE.json")
LABELS = os.path.join(ROOT, "coordination_detection", "derived", "C_results.json")
TABLES = os.path.join(STUDY, "tables")
N_PERM, SEED = 1000, 20261001
SPLITS = ("train", "val")
GROUPS = ("COORDINATED", "CONTROL", "STRICT CONTROL")


def load() -> list[dict[str, Any]]:
    doc = json.load(open(FREEZE))
    if hashlib.sha256(open(TABLE, "rb").read()).hexdigest() != doc["sha256_table"]:
        sys.exit("the economic-mechanics table differs from the frozen one")
    rows = [json.loads(x) for x in gzip.open(TABLE, "rt", encoding="utf8")]
    lab = json.load(open(LABELS))["labels"]
    for r in rows:
        d = lab[r["mint"]]
        r["group"] = {
            "COORDINATED": bool(d.get("MULTI-SIGNAL_COORDINATION")),
            "CONTROL": d.get("score", 0) <= 1,
            "STRICT CONTROL": bool(d.get("NO_SHARED_STRUCTURE")),
        }
    return rows


def load_prices() -> dict[str, dict[str, Any]]:
    doc = json.load(open(FREEZE))
    if hashlib.sha256(open(PRICE, "rb").read()).hexdigest() != doc["sha256_price"]:
        sys.exit("the price file differs from the frozen one")
    return {p["mint"]: p for p in (json.loads(x) for x in gzip.open(PRICE, "rt", encoding="utf8"))}


def write(name: str, lines: list[str]) -> None:
    os.makedirs(TABLES, exist_ok=True)
    with open(os.path.join(TABLES, name), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")


def dist(v: Sequence[Optional[float]], fmt: str = "%.3g") -> str:
    s = sorted(x for x in v if x is not None)
    if not s:
        return "n/a"

    def q(p: float) -> float:
        return s[int(p * (len(s) - 1))]

    return " / ".join(fmt % x for x in (q(0.5), q(0.25), q(0.75), q(0.9), s[0], s[-1])) + " (N %d)" % len(s)


def short(a: Optional[str]) -> str:
    return (a[:6] + "...") if a else "-"


# ----------------------------------------------------------------- funders --- #
def fkey(s: dict[str, Any], kind: str = "last", strict: bool = False) -> Optional[str]:
    """A shareable funder (never a known hub; with strict, never an unmeasured one); None when unknown."""
    f = s.get("last_funder") if kind == "last" else s.get("gen_funder")
    hub = s.get("last_funder_hub") if kind == "last" else s.get("gen_funder_hub")
    if f is None:
        return None
    if hub is True or (strict and hub is None):
        return "own:" + s["wallet"]
    return f


_hop_cache: dict[str, Any] = {}


def hop(addr: str) -> dict[str, Any]:
    if addr not in _hop_cache:
        _hop_cache[addr] = FB._hop(addr, False) or {}
    return _hop_cache[addr]


def deployer_sent_to(r: dict[str, Any]) -> set[str]:
    dep = r["creator"].get("wallet")
    out = set()
    for x in r["deployer_recent"]:
        d = x.get("d") or {}
        if dep and d.get(dep, 0) < 0 and not x.get("err"):
            out |= {k for k, v in d.items() if v > 0 and k != dep}
    return out


def architecture(r: dict[str, Any], kind: str = "last", strict: bool = False) -> dict[str, Any]:
    sn = r["snipers"]
    keys = [fkey(s, kind, strict) for s in sn]
    if any(k is None for k in keys):
        return {"primary": "UNRESOLVED", "flags": []}
    dep = r["creator"].get("wallet")
    by = Counter(k for k in keys if not k.startswith("own:"))
    multi = {f for f, c in by.items() if c >= 2}
    sent = deployer_sent_to(r)
    dep_funders = {r["creator"].get("gen_funder"), r["creator"].get("last_funder")} - {None}
    flags = []
    if dep and dep in multi:
        flags.append("C")

    def linked(f: str) -> bool:
        h = hop(f)
        return f in sent or (h.get("funding") or {}).get("funder") == dep or f in dep_funders

    if any(f != dep and linked(f) for f in multi):
        flags.append("A")
    srcs = Counter((hop(f).get("funding") or {}).get("funder") for f in by if not hop(f).get("hub_before_cursor"))
    srcs.pop(None, None)
    if len([f for f in multi if f != dep]) >= 2 or any(c >= 2 for c in srcs.values()):
        flags.append("D")
    if any(f != dep and not linked(f) for f in multi):
        flags.append("B")
    if not multi and dep not in by:
        flags.append("E")
    primary = next((a for a in ("C", "A", "D", "B", "E") if a in flags), "OTHER")
    return {"primary": primary, "flags": flags}


# ---------------------------------------------------------- per-launch measures #
def funding_measures(r: dict[str, Any]) -> dict[str, Any]:
    sn = r["snipers"]
    amts = [s.get("last_amount") for s in sn]
    bts = [s.get("last_bt") for s in sn]
    out: dict[str, Any] = {"n_snipers": len(sn), "n_funded": sum(1 for a in amts if a is not None)}
    if all(a is not None for a in amts):
        out["total_funded"] = sum(amts)
        m = statistics.mean(amts)
        out["amount_cv"] = statistics.pstdev(amts) / m if m > 0 else None
    if all(b is not None for b in bts):
        out["time_spread_s"] = max(bts) - min(bts)
        out["to_creation_s"] = statistics.median([r["t_create"] - b for b in bts])
        out["to_buy_s"] = statistics.median([s["bt"] - s["last_bt"] for s in sn])
        for lab, sec in (("lt_1min", 60), ("lt_10min", 600), ("lt_60min", 3600)):
            out["share_" + lab] = sum(1 for s in sn if s["bt"] - s["last_bt"] < sec) / len(sn)
    sigs = Counter(s.get("last_sig") for s in sn if s.get("last_sig"))
    out["max_snipers_one_funding_tx"] = max(sigs.values()) if sigs else None
    out["one_tx_for_2plus"] = (max(sigs.values()) >= 2) if sigs else None
    keys = [fkey(s) for s in sn]
    if all(k is not None for k in keys):
        c = Counter(k for k in keys if not k.startswith("own:"))
        out["shared_funder_2plus"] = bool(c) and max(c.values()) >= 2
    sent = deployer_sent_to(r)
    out["funder_funded_by_deployer"] = any(s.get("last_funder") in sent for s in sn)
    out["deployer_funds_sniper"] = any(s.get("last_funder") == r["creator"].get("wallet") for s in sn)
    return out


def sniper_lifecycle(r: dict[str, Any], s: dict[str, Any]) -> dict[str, Any]:
    ex = sorted(s["exits_full"], key=lambda x: (x["slot"], x["bt"] or 0))
    out: dict[str, Any] = {
        "received": s.get("last_amount"),
        "spent": s["ticket"],
        "spent_over_received": s["ticket"] / s["last_amount"] if s.get("last_amount") else None,
        "tok_bought": s["tok_bought"],
        "exited": bool(ex),
    }
    tok_out = sum(x["tok_out"] for x in ex)
    out["share_gone_30s"] = min(1.0, tok_out / s["tok_bought"]) if s["tok_bought"] else None
    out["sold_sol"] = sum(max(0.0, x["sol_in"] or 0) for x in ex if x["kind"] == "sell")
    out["n_sells"] = sum(1 for x in ex if x["kind"] == "sell")
    out["n_transfers"] = sum(1 for x in ex if x["kind"] == "transfer")
    if ex and s["bt"]:
        out["first_exit_s"] = (ex[0]["bt"] or s["bt"]) - s["bt"]
        out["first_exit_slots"] = ex[0]["slot"] - r["slot0"]
        cum, done = 0.0, None
        for x in ex:
            cum += x["tok_out"]
            if cum >= 0.99 * s["tok_bought"]:
                done = (x["bt"] or s["bt"]) - s["bt"]
                break
        out["complete_exit_s"] = done
        posts = [x["post_sol"] for x in ex if x["post_sol"] is not None]
        out["residual_sol"] = posts[-1] if posts else None
    out["recipients"] = sorted({o for x in ex if x["kind"] == "transfer" for o in x["recipients"]})
    return out


def returning_flows(r: dict[str, Any], s: dict[str, Any], next_funder: Optional[str]) -> Optional[dict[str, Any]]:
    """Where SOL goes between two launches of a returning sniper (complete records only)."""
    b = s.get("between")
    if not b or not b["complete"]:
        return None
    m = s["wallet"]
    sn_w = {x["wallet"] for x in r["snipers"]}
    out_to: list[str] = []
    for x in b["txs"]:
        d = x.get("d") or {}
        if x.get("err") or d.get(m, 0) >= -0.01:
            continue
        to = max((k for k in d if k != m), key=lambda k: d[k], default=None)
        if to is None or d.get(to, 0) <= 0:
            continue
        cls = (
            "first launch's funder"
            if to == s.get("last_funder")
            else "first launch's deployer"
            if to == r["creator"].get("wallet")
            else "another sniper of the launch"
            if to in sn_w
            else "next launch's funder"
            if to == next_funder
            else "another wallet"
        )
        out_to.append(cls)
    return {
        "outflows": out_to,
        "same_funder_next": next_funder is not None and next_funder == s.get("last_funder"),
        "next_funder": next_funder,
    }


def exit_sync(r: dict[str, Any], delays: Optional[list[Optional[int]]] = None) -> Optional[dict[str, Any]]:
    """Synchrony of first exits: delays in slots from the creation slot (None = no exit)."""
    if delays is None:
        delays = [min((x["slot"] for x in s["exits_full"]), default=None) for s in r["snipers"]]
        delays = [d - r["slot0"] if d is not None else None for d in delays]
    ex = [d for d in delays if d is not None]
    if len(ex) < 2:
        return None
    c = Counter(ex)
    return {"same_slot_share": sum(1 for d in ex if c[d] >= 2) / len(ex), "spread_slots": max(ex) - min(ex)}


# ------------------------------------------------------------------ nulls ---- #
def perm_test(obs: float, null: list[float], higher: bool = True) -> dict[str, Any]:
    null = sorted(null)
    n = len(null)
    p = (1 + sum(1 for x in null if (x >= obs if higher else x <= obs))) / (1 + n)
    mean = statistics.mean(null)
    return {
        "obs": obs,
        "null_mean": mean,
        "ci": [null[int(0.025 * (n - 1))], null[int(0.975 * (n - 1))]],
        "pct": sum(1 for x in null if x < obs) / n,
        "p": p,
        "effect": (obs / mean) if mean else None,
    }


def shuffled(rng: random.Random, v: list[Any]) -> list[Any]:
    v = list(v)
    rng.shuffle(v)
    return v


def null_funding(
    rr: list[dict[str, Any]],
    stat: Callable[[list[list[dict[str, Any]]]], float],
    fields: Sequence[str],
    n_perm: int = N_PERM,
) -> dict[str, Any]:
    """Funding attributes permuted among the sniper records of the subset, launches and sizes kept."""
    obs = stat([r["snipers"] for r in rr])
    attrs = [{k: s.get(k) for k in fields} for r in rr for s in r["snipers"]]
    rng = random.Random(SEED)
    null = []
    for _ in range(n_perm):
        a = shuffled(rng, attrs)
        i, groups = 0, []
        for r in rr:
            g = []
            for s in r["snipers"]:
                g.append({**s, **a[i]})
                i += 1
            groups.append(g)
        null.append(stat(groups))
    return perm_test(obs, null)


def co_pairs(groups: Sequence[Sequence[str]]) -> Counter:
    c: Counter = Counter()
    for g in groups:
        g = sorted(set(g))
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                c[(g[i], g[j])] += 1
    return c


def null_pairs(groups: list[list[str]], n_perm: int = N_PERM) -> dict[str, Any]:
    obs = float(sum(1 for v in co_pairs(groups).values() if v >= 2))
    edges = [(w, i) for i, g in enumerate(groups) for w in g]
    rng = random.Random(SEED)
    null = []
    for _ in range(n_perm):
        gs = [set(g) for g in groups]
        e = list(edges)
        for _ in range(3 * len(e)):
            a, b = rng.randrange(len(e)), rng.randrange(len(e))
            (w1, l1), (w2, l2) = e[a], e[b]
            if l1 == l2 or w1 == w2 or w2 in gs[l1] or w1 in gs[l2]:
                continue
            gs[l1].remove(w1)
            gs[l1].add(w2)
            gs[l2].remove(w2)
            gs[l2].add(w1)
            e[a], e[b] = (w2, l1), (w1, l2)
        null.append(float(sum(1 for v in co_pairs([sorted(g) for g in gs]).values() if v >= 2)))
    return perm_test(obs, null)


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


def clusters(
    rows: Sequence[dict[str, Any]], kind: str = "last", strict: bool = False, members: Optional[list[list[str]]] = None
) -> dict[str, str]:
    """Launch -> cluster id: wallets joined by a sniper pair in one launch, a non-hub funder-to-sniper
    relation, a deployer-to-funder relation or a common source (information at or before each launch)."""
    uf = UF()
    for i, r in enumerate(rows):
        sn = r["snipers"]
        ws = members[i] if members is not None else [s["wallet"] for s in sn]
        node = "L:" + r["mint"]
        for w in ws:
            uf.union(node, "W:" + w)
        if members is None:
            sent = deployer_sent_to(r)
            for s in sn:
                f = fkey(s, kind, strict)
                if f and not f.startswith("own:"):
                    uf.union("W:" + s["wallet"], "W:" + f)
                    src = (hop(f).get("funding") or {}).get("funder")
                    if src and not hop(f).get("hub_before_cursor"):
                        uf.union("W:" + f, "W:" + src)
                    if f in sent:
                        uf.union("W:" + f, "W:" + (r["creator"].get("wallet") or f))
    return {r["mint"]: uf.find("L:" + r["mint"]) for r in rows}


def summarize(groups: dict[str, list[str]]) -> dict[str, Any]:
    sizes = sorted((len(v) for v in groups.values()), reverse=True)
    return {
        "clusters": len(sizes),
        "multi_launch": sum(1 for x in sizes if x >= 2),
        "launches_in_multi": sum(x for x in sizes if x >= 2),
        "largest": sizes[0] if sizes else 0,
    }
