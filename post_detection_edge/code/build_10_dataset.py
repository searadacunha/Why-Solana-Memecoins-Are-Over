#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One row per alert: the features known at T_DETECT, the targets after it.

Unit of analysis: one launch alert, i.e. one potential buy decision. Features
are read from the alert record itself (the creation block as the detector
decoded it, p0, the time), plus a few context counts built strictly from
journal lines older than the alert. Targets are built from the frozen price
series with the coverage rule of pde.py. Nothing that happens after the alert
enters a feature: no multiple, no palier, no 8-minute verdict, no closure.

Outputs
  derived/dataset_dev.jsonl.gz          TRAIN + VALIDATION rows
  derived/dataset_test.sealed.jsonl.gz  TEST rows; no script reads it before
                                        tables/LOCK.json exists
  tables/T0_population.md               counts and coverage, no outcome
This script prints coverage counts only, never a hit rate.
"""
from __future__ import annotations

import bisect
import json
import math
import os
import statistics
from collections import Counter, defaultdict
from typing import Any, Optional

import pde

SOLUSD = {int(k): v for k, v in json.load(open(os.path.join(pde.DATA, "sol_usd_hourly.json")))
          ["close_by_hour"].items()}


def sol_usd(t: float) -> float:
    h = int(t) // 3600 * 3600
    if h not in SOLUSD:
        raise KeyError("no SOL/USD close for hour %d" % h)
    return SOLUSD[h]


def config_key(tickets: Optional[list[float]]) -> Optional[str]:
    return "+".join("%.2f" % x for x in sorted(tickets, reverse=True)) if tickets else None


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


def features(a: dict[str, Any], paquet: Optional[int], ctx: dict[str, Any]) -> dict[str, Any]:
    b = a["bloc"]
    tk = a.get("tickets") or b.get("tickets")
    f: dict[str, Any] = {
        "n_snipers": b.get("n_snipers"), "snipe_sol": b.get("sol"), "supply_part": b.get("part"),
        "ticket_cv": b.get("cv"), "core_cv": b.get("cv_noyau"), "ticket_median": b.get("ticket_median"),
        "n_buyers": b.get("n_acheteurs"), "ntx": b.get("ntx"), "nko": b.get("nko"),
        "complete_at_block": b.get("complete_au_bloc"), "amorce": b.get("amorce"),
        "paquet_max": paquet,
        "actor": None if not paquet else ("grouped" if paquet >= 2 else "single"),
        "p0_source": a.get("source"), "age_alert_s": a.get("age_alerte_s"),
        "entry_over_operator": a.get("entree_sur_operateur"),
    }
    f["extra_buyers"] = (f["n_buyers"] - f["n_snipers"]) if f["n_buyers"] is not None else None
    f["sol_per_sniper"] = f["snipe_sol"] / f["n_snipers"] if f["n_snipers"] else None
    f["fail_ratio"] = f["nko"] / f["ntx"] if f["ntx"] else None
    if tk:
        s = sum(tk)
        f["ticket_mean"] = s / len(tk)
        f["ticket_std"] = statistics.pstdev(tk)
        f["ticket_min"], f["ticket_max"] = min(tk), max(tk)
        f["max_share"] = max(tk) / s
        f["hhi"] = sum((x / s) ** 2 for x in tk)
        f["ticket_range_rel"] = (max(tk) - min(tk)) / f["ticket_mean"]
        f["round_share"] = sum(1 for x in tk if abs(x - round(x)) < 0.01) / len(tk)
    else:
        for k in ("ticket_mean", "ticket_std", "ticket_min", "ticket_max", "max_share", "hhi",
                  "ticket_range_rel", "round_share"):
            f[k] = None
    p0, vw = a["p0"], b.get("vwap_operateur")
    f["log10_p0"] = math.log10(p0)
    f["log10_vwap_op"] = math.log10(vw) if vw else None
    f["mc_usd"] = p0 * 1e9 * sol_usd(a["t"])
    f["log10_mc_usd"] = math.log10(f["mc_usd"])
    tm = __import__("time").gmtime(a["t"])
    f["hour_utc"], f["dow"] = tm.tm_hour, tm.tm_wday
    f.update(ctx)
    return f


def main() -> None:
    journal = pde.load_journal()
    series = pde.load_series()
    alerts = sorted((r for r in journal if r["genre"] == "alerte_lancement"), key=lambda r: r["t"])
    retro = {r["mint"]: r.get("paquet_max") for r in journal if r["genre"] == "outil"}
    flux = sorted(r["t"] for r in journal if r["genre"] in ("alerte_lancement", "rejete"))

    # operator clusters: alerts linked by a shared sniper wallet, the same
    # creator, or the same ticket configuration. Grouping only, never a feature.
    uf = UF()
    for a in alerts:
        keys = ["w:" + w for w in a.get("snipers") or []]
        if a.get("createur"):
            keys.append("c:" + a["createur"])
        ck = config_key(a.get("tickets") or a["bloc"].get("tickets"))
        if ck:
            keys.append("k:" + ck)
        for k in keys:
            uf.union("a:" + a["mint"], k)

    seen_creator: Counter[str] = Counter()
    seen_wallet: Counter[str] = Counter()
    seen_config: Counter[str] = Counter()
    alert_times: list[float] = []
    dev, test = [], []
    for a in alerts:
        t = a["t"]
        tk = a.get("tickets") or a["bloc"].get("tickets")
        ck = config_key(tk)
        ctx = {
            "n_alerts_prev_60m": len(alert_times) - bisect.bisect_left(alert_times, t - 3600),
            "n_candidates_prev_60m": bisect.bisect_left(flux, t) - bisect.bisect_left(flux, t - 3600),
            "creator_prev": seen_creator[a.get("createur") or ""] if a.get("createur") else 0,
            "sniper_reuse_max": max((seen_wallet[w] for w in a.get("snipers") or []), default=0),
            "config_prev": seen_config[ck] if ck else None,
        }
        paquet = a["bloc"].get("paquet_max") or retro.get(a["mint"])
        row: dict[str, Any] = {
            "mint": a["mint"], "t": t, "utc": a["utc"], "split": pde.split_of(t),
            "cluster": uf.find("a:" + a["mint"]), "creator": a.get("createur"),
            "snipers": a.get("snipers") or [], "config": ck, "sym": a.get("sym"),
            "p0": a["p0"], "fine": t >= pde.T_FINE,
            "f": features(a, paquet, ctx),
        }
        pts = series.get(a["mint"])
        row["has_series"] = bool(pts)
        tg: dict[str, Any] = {}
        for lat in pde.LATENCIES:
            ent = pde.entry_point(pts, lat) if pts else None
            for h in pde.HORIZONS:
                key = "L%d_%s" % (lat, pde.H_LABEL[h])
                if not pts:
                    tg[key] = {"status": "missing_no_series"}
                    continue
                if h < pde.FINE_WINDOW and not row["fine"]:
                    tg[key] = {"status": "missing_resolution"}
                    continue
                if lat and not row["fine"]:
                    tg[key] = {"status": "missing_resolution"}
                    continue
                if ent is None:
                    tg[key] = {"status": "missing_no_entry_price"}
                    continue
                mx, obs = pde.window(pts, ent[0], h, row["fine"])
                mfe = None if mx is None else mx / ent[1]
                tg[key] = {"status": "observed" if obs else "censored", "mfe": mfe,
                           "entry_mult": ent[1], "entry_dt": ent[0]}
        row["targets"] = tg
        (test if row["split"] == "test" else dev).append(row)
        # context is updated only after the row is built: strictly causal
        alert_times.append(t)
        if a.get("createur"):
            seen_creator[a["createur"]] += 1
        for w in a.get("snipers") or []:
            seen_wallet[w] += 1
        if ck:
            seen_config[ck] += 1

    pde.write_rows("dataset_dev.jsonl.gz", dev)
    pde.write_rows("dataset_test.sealed.jsonl.gz", test)

    # population and coverage table, outcome-free
    rows = dev + test
    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_split[r["split"]].append(r)
    snap = json.load(open(os.path.join(pde.DATA, "SNAPSHOT.json")))
    out = ["# T0. Population and coverage (no outcome in this table)", "",
           "Snapshot `data/SNAPSHOT.json`, T_SNAP = %s UTC. Regenerate: "
           "`python3 post_detection_edge/code/build_10_dataset.py`." % snap["t_snap_utc"], "",
           "| split | window (UTC) | alerts | with price series | fine sampling (5 s) | operator clusters |",
           "|---|---|---:|---:|---:|---:|"]
    for sp in ("train", "val", "test"):
        rr = by_split[sp]
        out.append("| %s | %s -> %s | %d | %d | %d | %d |" % (
            sp.upper(), rr[0]["utc"][:16], rr[-1]["utc"][:16], len(rr), sum(r["has_series"] for r in rr),
            sum(r["fine"] for r in rr), len({r["cluster"] for r in rr})))
    out.append("| all | %s -> %s | %d | %d | %d | %d |" % (
        rows[0]["utc"][:16], rows[-1]["utc"][:16], len(rows), sum(r["has_series"] for r in rows),
        sum(r["fine"] for r in rows), len({r["cluster"] for r in rows})))
    out += ["", "## Coverage of the entry-at-P0 window, by horizon", "",
            "`observed` = the whole window is covered by reads (pde.window); `censored` = a detector "
            "outage or the end of the follow-up cuts it; `missing` = no series, or a horizon shorter "
            "than the 45 s sampling of the alerts before 2026-08-25 21:47 UTC.", "",
            "| horizon | split | observed | censored | missing |", "|---|---|---:|---:|---:|"]
    for h in pde.HORIZONS:
        for sp in ("train", "val", "test"):
            c = Counter(r["targets"]["L0_%s" % pde.H_LABEL[h]]["status"] for r in by_split[sp])
            out.append("| %s | %s | %d | %d | %d |" % (
                pde.H_LABEL[h], sp, c["observed"], c["censored"],
                sum(v for k, v in c.items() if k.startswith("missing"))))
    cl = Counter(r["cluster"] for r in rows)
    sizes = sorted(cl.values(), reverse=True)
    out += ["", "Operator clusters (shared sniper wallet, creator or ticket configuration): %d clusters; "
            "largest %s; %d singletons." % (len(cl), ", ".join(map(str, sizes[:8])), sizes.count(1)),
            "", "Actor label: %s." % dict(Counter(r["f"]["actor"] for r in rows))]
    pde.write_table("T0_population.md", "\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
