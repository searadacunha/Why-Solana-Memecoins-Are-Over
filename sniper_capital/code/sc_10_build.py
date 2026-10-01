#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build and freeze the sniper-capital table (analysis_plan.md, "Sniper values", "Launch features").

Sniper records come from sc_00_coverage.sniper_records (windows and wallet files, read only); the
context and the labels from the frozen table of post_detection_forensics, after its sha256 check.
A launch feature is computed only when every sniper of the launch has the values it needs;
otherwise it is None, never zero. Writes derived/sc_table.jsonl.gz (one row per launch, with its
sniper values) and derived/SC_FREEZE.json (sha256, coverage per feature, no rate), then refuses to
run again.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import statistics
import sys
import time
from collections import Counter
from typing import Any, Callable, Optional

import sc_00_coverage as C

FB = C.FB
sys.path.insert(0, os.path.join(C.ROOT, "post_detection_forensics", "code"))
import ana_lib  # noqa: E402

DERIVED = os.path.join(C.STUDY, "derived")
TABLE = os.path.join(DERIVED, "sc_table.jsonl.gz")
FREEZE = os.path.join(DERIVED, "SC_FREEZE.json")
LABELS = ["A_conf_2x_15m", "A_conf_2x_5m", "A_conf_2x_1h", "A_conf_1.5x_15m", "A_conf_3x_15m", "A_mfe_3600s"]


def sniper_values(r: dict[str, Any]) -> dict[str, Any]:
    m = r["wallet"]
    cap = (r["pre"] + r["inflow_in_tx"]) if r["pre"] is not None else None
    v: dict[str, Any] = {
        "wallet": m,
        "role": r["role"],
        "ticket": r["ticket"],
        "capital": cap,
        "after": r["post"] if cap is not None else None,
        "n_prior": r["n_prior"],
    }
    v["a"] = r["ticket"] / cap if cap else None
    v["g"] = r["post"] / cap if cap and r["post"] is not None else None
    rc = r["recent"]
    fund = [x for x in rc if (x.get("d") or {}).get(m, 0) > 0 and not x.get("err") and x.get("signer") != m]
    last = max(fund, key=lambda x: x.get("bt") or 0) if fund else None
    t = r["t_buy"] or r["t"]
    if last and last.get("bt"):
        amt = last["d"][m]
        v["last_amount"] = amt
        v["last_age_s"] = max(0.0, t - last["bt"])
        v["last_sender"] = min(last["d"], key=lambda k: last["d"][k])
        v["ticket_over_last"] = r["ticket"] / amt if amt > 0 else None
        v["last_over_capital"] = amt / cap if cap else None
        after_funding = sum((x.get("d") or {}).get(m, 0) for x in rc if (x.get("bt") or 0) >= last["bt"])
        v["balance_before_last"] = max(0.0, r["pre"] - after_funding) if r["pre"] is not None else None
    gf = r["genesis_funder"] if r["n_prior"] < 1000 else None
    if gf:
        hop = FB._hop(gf, False) or {}
        v["gen_funder"] = gf
        v["gen_hub"] = 1.0 if hop.get("hub_before_cursor") else 0.0 if hop else None
        src = gf if hop.get("hub_before_cursor") else (hop.get("funding") or {}).get("funder")
        v["source"] = src
    return v


def agg(sn: list[dict[str, Any]], key: str, fn: Callable[[list[float]], Optional[float]]) -> Optional[float]:
    vals = [s.get(key) for s in sn]
    if not vals or any(x is None for x in vals):
        return None  # one sniper not OBSERVED: the launch value is not computed
    return fn(vals)


def q(p: float) -> Callable[[list[float]], float]:
    def f(v: list[float]) -> float:
        s = sorted(v)
        return s[int(p * (len(s) - 1))]

    return f


def share(cond: Callable[[float], bool]) -> Callable[[list[float]], float]:
    return lambda v: sum(1 for x in v if cond(x)) / len(v)


def count(cond: Callable[[float], bool]) -> Callable[[list[float]], float]:
    return lambda v: float(sum(1 for x in v if cond(x)))


def hhi(v: list[float]) -> Optional[float]:
    s = sum(v)
    return sum((x / s) ** 2 for x in v) if s > 0 else None


def launch_features(sn: list[dict[str, Any]]) -> dict[str, Any]:
    f: dict[str, Any] = {}
    med, mean = statistics.median, statistics.mean
    for k, fn in (("med", med), ("mean", mean), ("min", min), ("max", max), ("p25", q(0.25)), ("p75", q(0.75))):
        f["a_" + k] = agg(sn, "a", fn)
    f["a_total"] = (
        sum(s["ticket"] for s in sn) / sum(s["capital"] for s in sn) if all(s.get("capital") for s in sn) else None
    )
    for k, fn in (("med", med), ("mean", mean), ("min", min), ("max", max)):
        f["g_" + k] = agg(sn, "g", fn)
    for k, fn in (("med", med), ("min", min), ("max", max)):
        f["tl_" + k] = agg(sn, "ticket_over_last", fn)
        f["age_" + k] = agg(sn, "last_age_s", fn)
    f["age_share_lt_1h"] = agg(sn, "last_age_s", share(lambda x: x < 3600))
    f["age_share_lt_5min"] = agg(sn, "last_age_s", share(lambda x: x < 300))
    for k, fn in (("med", med), ("min", min), ("max", max), ("sum", sum), ("hhi", hhi)):
        f["amt_" + k] = agg(sn, "last_amount", fn)
    f["fit_share_90_100"] = agg(sn, "ticket_over_last", share(lambda x: 0.9 <= x <= 1.0))
    f["fit_n_90_100"] = agg(sn, "ticket_over_last", count(lambda x: 0.9 <= x <= 1.0))
    f["fit_share_above_1"] = agg(sn, "ticket_over_last", share(lambda x: x > 1.0))
    f["fc_med"] = agg(sn, "last_over_capital", med)
    for lab, cond in (
        ("lt10", lambda x: x < 0.10),
        ("ge25", lambda x: x >= 0.25),
        ("ge50", lambda x: x >= 0.50),
        ("ge75", lambda x: x >= 0.75),
        ("ge90", lambda x: x >= 0.90),
    ):
        f["n_a_" + lab] = agg(sn, "a", count(cond))
    f["share_a_ge50"] = agg(sn, "a", share(lambda x: x >= 0.5))
    # topology
    if all(s.get("gen_funder") for s in sn):
        c = Counter(s["gen_funder"] for s in sn)
        f["gen_n_funders"] = float(len(c))
        f["gen_max_share"] = max(c.values()) / len(sn)
        f["gen_same"] = 1.0 if max(c.values()) >= 2 else 0.0
        f["gen_share_hub"] = agg(sn, "gen_hub", mean)
        if all(s.get("source") for s in sn):
            srcs: dict[str, set] = {}
            for s in sn:
                srcs.setdefault(s["source"], set()).add(s["gen_funder"])
            f["src_n"] = float(len(srcs))
            f["src_max_funders"] = float(max(len(x) for x in srcs.values()))
    if all(s.get("last_sender") for s in sn):
        c = Counter(s["last_sender"] for s in sn)
        f["last_n_funders"] = float(len(c))
        f["last_max_share"] = max(c.values()) / len(sn)
        f["last_same"] = 1.0 if max(c.values()) >= 2 else 0.0
        ages = [s["last_age_s"] for s in sn]
        f["fund_time_spread_s"] = max(ages) - min(ages)
    # other aggregates
    f["sum_ticket"] = sum(s["ticket"] for s in sn)
    caps = [s.get("capital") for s in sn]
    if all(x is not None for x in caps):
        cs = sorted(caps, reverse=True)
        f["sum_capital"] = sum(cs)
        f["hhi_capital"] = hhi(cs)
        for k in (1, 2, 3):
            f["top%d_capital_share" % k] = sum(cs[:k]) / sum(cs) if sum(cs) > 0 else None
    f["hhi_ticket"] = hhi([s["ticket"] for s in sn])
    f["n_snipers_here"] = float(len(sn))
    return f


def main() -> None:
    if os.path.exists(FREEZE):
        sys.exit("the sniper-capital table is frozen (%s); it is not rebuilt" % FREEZE)
    base = {r["mint"]: r for r in ana_lib.load()}
    alerts = sorted((a for a in C.pde.load_journal() if a["genre"] == "alerte_lancement"), key=lambda a: a["t"])
    rows, cover = [], Counter()
    for a in alerts:
        b = base[a["mint"]]
        sn = [sniper_values(r) for r in C.sniper_records(a)]
        f = launch_features(sn)
        x = b["fA"]
        row = {
            "mint": a["mint"],
            "t": a["t"],
            "utc": a["utc"],
            "split": b["split"],
            "cluster": b["cluster"],
            "actor": b["actor_type"],
            "fine": b["fine"],
            "p0": b["p0"],
            "ctl": {
                "premium": x.get("p_entry_over_operator"),
                "actor": x.get("c_actor_grouped"),
                "snipers": x.get("b_core_n"),
                "log_mc": x.get("p_log_mc_usd"),
            },
            "f": f,
            "snipers": sn,
            "y": {k: b["y"].get(k) for k in LABELS},
        }
        rows.append(row)
        for k, v in f.items():
            cover[(k, b["split"])] += v is not None
    os.makedirs(DERIVED, exist_ok=True)
    with open(TABLE, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
            for r in rows:
                gz.write((json.dumps(r, sort_keys=True) + "\n").encode("utf8"))
    n = Counter(r["split"] for r in rows)
    feats = sorted({k for k, _ in cover})
    doc = {
        "frozen_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "sha256": hashlib.sha256(open(TABLE, "rb").read()).hexdigest(),
        "rows": len(rows),
        "rows_by_split": dict(n),
        "sniper_records": sum(len(r["snipers"]) for r in rows),
        "coverage": {k: {"train": cover[(k, "train")], "val": cover[(k, "val")]} for k in feats},
        "source_table_sha256": json.load(open(ana_lib.FREEZE))["sha256"],
        "note": "launches whose feature is computed (every sniper OBSERVED); no rate was computed",
    }
    with open(FREEZE, "w", encoding="utf8") as fh:
        json.dump(doc, fh, indent=1)
    os.chmod(TABLE, 0o444)
    os.chmod(FREEZE, 0o444)
    print(json.dumps({k: doc[k] for k in ("sha256", "rows", "rows_by_split", "sniper_records")}, indent=1))
    for k in feats:
        print("%-22s TRAIN %4d / %d   VAL %4d / %d" % (k, cover[(k, "train")], n["train"], cover[(k, "val")], n["val"]))


if __name__ == "__main__":
    main()
