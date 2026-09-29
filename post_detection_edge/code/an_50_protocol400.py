#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The protocol pre-registered on 2026-08-29 18:36 UTC, evaluated as written.

Source: data/protocol400_caches/PROTOCOLE_400.md, copied into the snapshot.
Nothing is re-specified here. Success, failure, populations, sizes and
verdicts follow the protocol file and the detector's own evaluation code
(analyse/protocole_400.py, elimination_precoce.x2_confirme,
backtest_x2.trade, financeurs.lignee), re-implemented line for line on the
frozen snapshot, with "now" = T_SNAP. Its caches stopped being collected on
2026-08-31, so a hypothesis whose data was never collected is reported as not
evaluable, never as negative.

Two readings are printed where they differ:
  registered   the first N decided test alerts, N = the registered size,
               in alert order, and only alerts whose inputs were collected;
  as coded     what protocole_400.py prints: every decided alert, and a
               missing lineage counted as "no dead hub" (a deviation from the
               protocol text, shown for transparency only).
Nothing from this script feeds the signal search or the lock.
"""
from __future__ import annotations

import json
import math
import os
from typing import Any, Callable, Optional

import pde

CACHES = os.path.join(pde.DATA, "protocol400_caches")
DEAD = ("4kwMyUNQVYkKrUU9Zatf8cQsWbBy2tvGgtX4YWQX6gQb", "B1pCmsG1EjDKXibCezG2maQdYbHKXkuR19EQBEKPNxcX")
FINE = 180.0


def x2_confirmed(pts: list[tuple[float, float]]) -> Optional[float]:
    for i, (dt, m) in enumerate(pts):
        if m < 2.0:
            continue
        if dt > FINE:
            return dt
        if i + 1 < len(pts) and pts[i + 1][1] >= 2.0:
            return pts[i + 1][0]
    return None


def trade(pts: list[tuple[float, float]]) -> float:
    for i, (dt, m) in enumerate(pts):
        if m >= 2.0 and i + 1 < len(pts) and pts[i + 1][1] >= 2.0:
            return pts[i + 1][1]
        if m >= 2.0 and dt > 180:
            return m
    return pts[-1][1]


def lineage(W: dict[str, Any], w: str) -> list[str]:
    out, cur = [], w
    for _ in range(3):
        f = (W.get(cur) or {}).get("financeur")
        if not f:
            break
        out.append(f)
        cur = f
    return out


def fisher2(a: int, b: int, c: int, d: int) -> float:
    n, r1, c1 = a + b + c + d, a + b, a + c

    def lc(nn: int, kk: int) -> float:
        return math.lgamma(nn + 1) - math.lgamma(kk + 1) - math.lgamma(nn - kk + 1)

    def p(x: int) -> float:
        return math.exp(lc(r1, x) + lc(n - r1, c1 - x) - lc(n, c1))
    p0 = p(a)
    return min(1.0, sum(p(x) for x in range(max(0, r1 + c1 - n), min(r1, c1) + 1) if p(x) <= p0 * (1 + 1e-9)))


def main() -> None:
    snap = json.load(open(os.path.join(pde.DATA, "SNAPSHOT.json")))
    now = snap["t_snap"]
    journal = pde.load_journal()
    S = pde.load_series()
    retro = {r["mint"]: r.get("paquet_max") for r in journal if r["genre"] == "outil"}
    W = json.load(open(os.path.join(CACHES, "financeurs_cache.json")))["wallets"]
    n60 = json.load(open(os.path.join(CACHES, "protocole_400_n60.json")))
    cp = json.load(open(os.path.join(CACHES, "protocole_400_copies.json")))
    al = []
    for r in journal:
        if r["genre"] == "alerte_lancement" and r["t"] > pde.T_TRAIN_END:
            pm = r["bloc"].get("paquet_max") or retro.get(r["mint"])
            r["outil"] = None if not pm else ("groupe" if pm >= 2 else "unitaire")
            al.append(r)

    def issue(d: dict[str, Any]) -> Optional[bool]:
        if x2_confirmed(S.get(d["mint"]) or []) is not None:
            return True
        return False if now - d["t"] >= 86400 else None

    def wallets(d: dict[str, Any]) -> list[str]:
        return [w for w in (d.get("snipers") or []) + ([d["createur"]] if d.get("createur") else []) if w]

    def hubs(d: dict[str, Any]) -> set[str]:
        return {f for w in wallets(d) for f in lineage(W, w)}

    def collected(d: dict[str, Any]) -> bool:
        return all(w in W for w in wallets(d))

    tr = [(d, issue(d)) for d in al]
    dec = [(d, y) for d, y in tr if y is not None]
    out = ["# T5. Pre-registered protocol of 2026-08-29 (\"400\"), evaluated on the snapshot", "",
           "Protocol text: `data/protocol400_caches/PROTOCOLE_400.md` (unchanged). T0 = 2026-08-29 18:36 UTC; "
           "now = T_SNAP = %s UTC. Success = x2 CONFIRMED in the series (two consecutive reads >= 2 inside "
           "180 s, one read after); failure = no confirmed x2 and age >= 24 h. The detector's outages are not "
           "corrected for (the protocol does not), so success is a lower bound. Regenerate: "
           "`python3 post_detection_edge/code/an_50_protocol400.py`." % snap["t_snap_utc"], "",
           "Test alerts after T0: %d; decided: %d (confirmed x2: %d)." % (
               len(al), len(dec), sum(1 for _, y in dec if y)), "",
           "| hypothesis | registered size | reading | n | x2 | rate [Wilson] | verdict |",
           "|---|---:|---|---:|---:|---|---|"]

    def row(name: str, size: int, reading: str, pop: list[tuple[dict[str, Any], bool]],
            verdict: Callable[[int, int, list], str]) -> None:
        n = len(pop)
        k = sum(1 for _, y in pop if y)
        v = verdict(k, n, pop) if n >= size else "NOT EVALUABLE: %d of %d required" % (n, size)
        out.append("| %s | %d | %s | %d | %d | %s | %s |" % (name, size, reading, n, k,
                                                            pde.rate_cell(k, n) if n else "-", v))

    def v1(k: int, n: int, pop: list) -> str:
        lo, _ = pde.wilson(k, n)
        rend = sum(trade(S[d["mint"]]) * 0.97 - 1 for d, _ in pop) / n
        verdict = ("CONFIRMED" if lo > 0.40 and rend > 0
                   else ("RETRACTED" if k / n < 0.45 else "INCONCLUSIVE"))
        return "%s (protocol backtest %+.1f %%)" % (verdict, 100 * rend)

    c1_reg = [(d, y) for d, y in dec if d["outil"] == "groupe" and collected(d) and not (hubs(d) & set(DEAD))]
    c1_all = [(d, y) for d, y in dec if d["outil"] == "groupe" and not (hubs(d) & set(DEAD))]
    row("C1 grouped actor outside lineage 4kwM", 40, "registered", c1_reg[:40], v1)
    if len(c1_reg) < 40:
        row("C1 grouped actor outside lineage 4kwM", 80, "registered (extension)", c1_reg[:80], v1)
    row("C1 grouped actor outside lineage 4kwM", 40, "as coded", c1_all, v1)
    c1b = [(d, y) for d, y in dec if collected(d) and (hubs(d) & set(DEAD))][:10]
    row("C1b lineage 4kwM (elimination)", 10, "registered", c1b,
        lambda k, n, pop: "CONFIRMED (0 x2)" if k == 0 else "RETRACTED")
    c2 = [(d, y) for d, y in dec if cp.get(d["mint"])]
    row("C2 copied name", 15, "registered", c2,
        lambda k, n, pop: ("CONFIRMED" if pde.wilson(k, n)[0] > 0.40
                           else ("RETRACTED" if k / n < 0.45 else "INCONCLUSIVE")))

    def v3(k: int, n: int, pop: list) -> str:
        lo_ = [(d, y) for d, y in pop if n60[d["mint"]]["n60"] <= 100]
        hi_ = [(d, y) for d, y in pop if n60[d["mint"]]["n60"] > 100]
        a = sum(1 for _, y in lo_ if y)
        c = sum(1 for _, y in hi_ if y)
        p = fisher2(a, len(lo_) - a, c, len(hi_) - c)
        ok = p < 0.05 and lo_ and hi_ and a / len(lo_) > c / len(hi_)
        return "%s (n60<=100: %d/%d, n60>100: %d/%d, Fisher p = %.3f)" % (
            "CONFIRMED" if ok else "RETRACTED", a, len(lo_), c, len(hi_), p)
    c3 = [(d, y) for d, y in c1_all if (n60.get(d["mint"]) or {}).get("atteint")]
    row("C3 low pool density at 60 s (within C1)", 30, "registered", c3[:30], v3)

    c4 = []
    for d in al:
        pts = S.get(d["mint"]) or []
        t2 = x2_confirmed(pts)
        if t2 is not None and t2 <= 900:
            continue
        m = [mm for dt, mm in pts if dt <= 900]
        if not m or now - d["t"] < 900:
            continue
        if m[-1] <= 0.5:
            y = issue(d)
            if y is not None:
                c4.append((d, y))

    def v4(k: int, n: int, pop: list) -> str:
        return "CONFIRMED (0 false negative)" if k == 0 else ("RETRACTED" if k >= 2 else "INCONCLUSIVE")
    row("C4 second verdict at 15 min, x0.50 (x2 afterwards = false negative)", 60, "registered", c4[:60], v4)
    if c4[:60] and sum(1 for _, y in c4[:60] if y) == 1:
        row("C4 second verdict at 15 min", 100, "registered (extension)", c4[:100], v4)
    row("C4 second verdict at 15 min", 60, "as coded (all decided)", c4, v4)
    out.append("| C6 core exit destination | 30 | registered | 0 | 0 | - | NOT EVALUABLE: exit caches never "
               "collected after T0 |")
    out += ["", "Collection state in the snapshot: funding lineage for %d post-T0 alerts (last on 2026-08-31), "
            "copied-name checks for %d, pool density n60 for %d, core-exit data for 0. The daily `--collecte` "
            "stopped on 2026-08-31." % (sum(1 for d in al if collected(d) and d["outil"] == "groupe"),
                                        sum(1 for d in al if d["mint"] in cp), len(n60))]
    pde.write_table("T5_protocol400.md", "\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
