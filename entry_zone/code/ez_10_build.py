#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build and freeze the entry-zone table (analysis_plan.md, "Data", "Cut-offs", "Labels",
"Features"). One row per alert of the first snapshot, TRAIN and VALIDATION only.

Reads, never writes: the frozen table of post_detection_forensics (context: split,
cluster, actor, premium and market cap at the alert), its on-chain windows and wallet
files, and the detector's price series. Writes derived/ez_table.jsonl.gz and
derived/EZ_FREEZE.json (sha256, coverage per cut-off, label counts only), then
refuses to run again.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "post_detection_forensics", "code"))
import ana_lib  # noqa: E402  (loads the phase-3 frozen table after checking its sha256)
import feat_30_build as FB  # noqa: E402
import fparse  # noqa: E402

pde = FB.pde
DERIVED = os.path.join(STUDY, "derived")
TABLE = os.path.join(DERIVED, "ez_table.jsonl.gz")
FREEZE = os.path.join(DERIVED, "EZ_FREEZE.json")

# cut-off name: (seconds after the alert for the entry, trade cut relative to the alert or "slot0",
#                price cut relative to the alert or None, entry tolerance in s)
CUTS: dict[str, tuple[float, Any, Optional[float], float]] = {
    "T0": (0.0, "slot0", None, 10.0), "D": (0.0, -1.0, 0.0, 10.0),
    "P5": (5.0, 4.0, 4.0, 10.0), "P10": (10.0, 9.0, 9.0, 10.0), "P20": (20.0, 19.0, 19.0, 10.0),
    "P30": (30.0, 29.0, 29.0, 10.0), "P60": (60.0, 29.0, 59.0, 10.0), "P120": (120.0, 29.0, 119.0, 10.0),
    "P300": (300.0, 29.0, 299.0, 46.0)}
HORIZON = 900.0
WINDOWS = {"1h": 3600, "6h": 6 * 3600, "24h": 86400, "7d": 7 * 86400}
CAP_LEVELS = (1, 2, 5, 10, 20)


def med(v: list[float]) -> Optional[float]:
    return statistics.median(v) if v else None


def entry(pts: list[tuple[float, float]], lat: float, tol: float) -> Optional[tuple[float, float]]:
    if lat == 0:
        return (0.0, 1.0)
    for dt, m in pts:
        if lat <= dt <= lat + tol:
            return dt, m
        if dt > lat + tol:
            break
    return None


def labels(pts: list[tuple[float, float]], fine: bool, lat: float, tol: float) -> dict[str, Any]:
    ent = entry(pts, lat, tol)
    if ent is None:
        return {"entry": None}
    t_e, m_e = ent
    out: dict[str, Any] = {"entry": [t_e, m_e]}
    ok = pde.window(pts, t_e, HORIZON, fine)[1]
    if not ok:
        return out
    ins = [(dt, m / m_e) for dt, m in pts if t_e < dt <= t_e + HORIZON]
    for k in (1.5, 2.0, 3.0):
        out["conf_%g" % k] = int(any(a >= k and b >= k for (_, a), (_, b) in zip(ins, ins[1:])))
        out["single_%g" % k] = int(any(x >= k for _, x in ins))
    first = next((d2 - t_e for (d1, a), (d2, b) in zip(ins, ins[1:]) if a >= 2 and b >= 2), None)
    out["t_2x_s"] = first
    until = [x for dt, x in ins if first is None or dt - t_e <= first]
    out["drawdown"] = (min(until) - 1.0) if until else None
    return out


def buy_events(w: dict[str, Any], recs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One event per (transaction, buyer): SOL the buyer spent, its native balance before and after."""
    out = []
    for r in recs:
        if r.get("err"):
            continue
        spent: dict[str, float] = {}
        if r.get("kind") in ("buy", "create") and r.get("venue") == "curve":
            spent = {o: v for o, v in (r.get("leg_sol") or {}).items() if v > 0}
        elif r.get("kind") == "buy" and r.get("venue") == "pool":
            spent = {o: -v for o, v in (r.get("owner_sol") or {}).items() if v < 0}
        if not spent:
            continue
        t = w["txs"].get(r["sig"])
        keys = [k["pubkey"] for k in t["transaction"]["message"]["accountKeys"]] if t else []
        pre, post = (t["meta"]["preBalances"], t["meta"]["postBalances"]) if t else ([], [])
        for o, s in spent.items():
            i = keys.index(o) if o in keys else None
            out.append({"sig": r["sig"], "slot": r["slot"], "bt": r.get("bt"), "owner": o, "sol": s,
                        "kind": r["kind"], "venue": r["venue"],
                        "pre": pre[i] / 1e9 if i is not None else None,
                        "post": post[i] / 1e9 if i is not None else None})
    return out


def sniper_funding(wal: dict[str, Any], core: list[str], t_create: float, ticket: dict[str, float]
                   ) -> dict[str, Any]:
    """Funding of the snipers before the creation (genesis and the last 5 earlier transactions)."""
    f: dict[str, Any] = {}
    first, funders, hubs = [], [], []
    per_w: dict[str, dict[str, list[float]]] = {k: {"recv": [], "ntx": [], "nf": []} for k in WINDOWS}
    complete = Counter()
    ratio: list[float] = []
    for m in core:
        v = wal["wallets"].get(m) or {}
        g = ((v.get("genesis") or {}).get("funding") or {})
        if g.get("received") is not None and g["received"] > 0:
            first.append(g["received"])
        if g.get("funder"):
            funders.append(g["funder"])
            h = FB._hop(g["funder"], False)
            hubs.append(1.0 if (h or {}).get("hub_before_cursor") else 0.0)
        n = (v.get("prior") or {}).get("n", 0)
        rc = v.get("recent") or []
        oldest = min((x["bt"] for x in rc if x.get("bt")), default=None)
        for lab, h in WINDOWS.items():
            if not (n <= len(rc) or (oldest is not None and oldest < t_create - h)):
                continue
            complete[lab] += 1
            got = [x for x in rc if x.get("bt") and x["bt"] >= t_create - h and (x.get("d") or {}).get(m, 0) > 0]
            senders = {min(x["d"], key=lambda k: x["d"][k]) for x in got if x.get("d")}
            per_w[lab]["recv"].append(sum(x["d"][m] for x in got))
            per_w[lab]["ntx"].append(float(len(got)))
            per_w[lab]["nf"].append(float(len(senders)))
            if lab == "24h" and got and ticket.get(m) and sum(x["d"][m] for x in got) > 0:
                ratio.append(ticket[m] / sum(x["d"][m] for x in got))
    k = len(core)
    f["fu_first_median"] = med(first)
    f["fu_first_max"] = max(first) if first else None
    f["fu_first_min"] = min(first) if first else None
    f["fu_first_sum"] = sum(first) if first else None
    f["fu_share_1sol_about"] = (sum(1 for x in first if 0.9 <= x <= 1.1) / len(first)) if first else None
    f["fu_share_1sol_exact"] = (sum(1 for x in first if 0.99 <= x <= 1.01) / len(first)) if first else None
    f["fu_share_hub"] = (sum(hubs) / len(hubs)) if hubs else None
    c = Counter(funders)
    f["fu_n_funders"] = float(len(c)) if funders else None
    f["fu_top_funder_n"] = float(max(c.values())) if funders else None
    f["fu_funder_hhi"] = (sum((x / len(funders)) ** 2 for x in c.values())) if funders else None
    for lab in WINDOWS:
        d = per_w[lab]
        full = complete[lab] == k and k > 0
        f["fu_recv_%s_sum" % lab] = sum(d["recv"]) if full else None
        f["fu_recv_%s_median" % lab] = med(d["recv"]) if d["recv"] else None
        f["fu_recv_%s_max" % lab] = max(d["recv"]) if d["recv"] else None
        f["fu_ntx_%s_sum" % lab] = sum(d["ntx"]) if full else None
        f["fu_nfunders_%s_max" % lab] = max(d["nf"]) if d["nf"] else None
        f["fu_complete_%s" % lab] = complete[lab] / k if k else None
    f["fu_ticket_over_recv_24h_median"] = med(ratio)
    return f


def trade_features(ev: list[dict[str, Any]], recs: list[dict[str, Any]], core: set[str], creator: Optional[str],
                   t_create: float, cut_bt: Optional[float], slot0: int, mig_bt: Optional[float]) -> dict[str, Any]:
    if cut_bt is None:
        sel = [e for e in ev if e["slot"] == slot0]
        cut_rec = [r for r in recs if r["slot"] == slot0]
    else:
        sel = [e for e in ev if (e["bt"] or 0) <= cut_bt]
        cut_rec = [r for r in recs if (r.get("bt") or 0) <= cut_bt]
    by: dict[str, float] = defaultdict(float)
    first: dict[str, dict[str, Any]] = {}
    for e in sorted(sel, key=lambda x: (x["slot"], x["bt"] or 0)):
        by[e["owner"]] += e["sol"]
        first.setdefault(e["owner"], e)
    dev = sum(e["sol"] for e in sel if e["kind"] == "create")
    snipers = {o for o in by if o in core} | ({creator} if creator and dev >= FB.CORE_MIN_SOL else set())
    bundle = sum(e["sol"] for e in sel if e["slot"] == slot0 and (e["owner"] in core or e["owner"] == creator))
    early = {o for o in by if o not in core and o != creator}
    tk = sorted(by.values(), reverse=True)
    tot = sum(tk)
    f: dict[str, Any] = {
        "sol_total": tot, "sol_bundle": bundle, "sol_outside": tot - bundle, "n_buyers": float(len(by)),
        "n_snipers": float(len(snipers)), "n_early": float(len(early)),
        "sol_mean": tot / len(tk) if tk else None, "sol_median": med(tk), "sol_max": tk[0] if tk else None,
        "sol_top2": sum(tk[:2]) if tk else None, "sol_top3": sum(tk[:3]) if tk else None,
        "top1_share": tk[0] / tot if tot else None, "sol_hhi": sum((x / tot) ** 2 for x in tk) if tot else None,
        "sol_early_total": sum(by[o] for o in early), "sol_early_max": max((by[o] for o in early), default=0.0)}
    out_ev = [e for e in sel if e["slot"] != slot0 and e["owner"] not in core and e["owner"] != creator]
    f["t_since_creation"] = (cut_bt - t_create) if cut_bt is not None else 0.0
    f["buys_5s"] = float(sum(1 for e in out_ev if (e["bt"] or 0) <= t_create + 5))
    f["buys_10s"] = float(sum(1 for e in out_ev if (e["bt"] or 0) <= t_create + 10))
    f["t_first_outside"] = (min(e["bt"] for e in out_ev if e["bt"]) - t_create) if any(e["bt"] for e in out_ev) \
        else None
    cl = [r for r in cut_rec if r.get("curve_lamports") is not None]
    migrated = mig_bt is not None and (cut_bt is None or mig_bt <= cut_bt)
    f["curve_left_sol"] = 0.0 if migrated else (max(0.0, 85.0 - cl[-1]["curve_lamports"]) if cl else None)
    pr = [r for r in cut_rec if r.get("pool_tok")]
    f["pool_sol"] = pr[-1]["pool_sol"] if pr else None
    # capacity: native SOL before each buyer's first buy
    for grp, members in (("all", set(by)), ("snipers", snipers), ("early", early)):
        pre = [first[o]["pre"] for o in members if o in first and first[o]["pre"] is not None]
        ratio = [by[o] / first[o]["pre"] for o in members if o in first and first[o]["pre"]]
        f["cap_%s_sum" % grp] = sum(pre) if pre else None
        f["cap_%s_max" % grp] = max(pre) if pre else None
        f["cap_%s_median" % grp] = med(pre)
        for lv in CAP_LEVELS:
            f["cap_%s_n_ge%d" % (grp, lv)] = float(sum(1 for x in pre if x >= lv)) if pre else None
        spent = sum(by[o] for o in members if o in first and first[o]["pre"])
        f["cap_%s_spent_over_available" % grp] = spent / sum(pre) if pre and sum(pre) > 0 else None
        f["cap_%s_spent_ratio_median" % grp] = med(ratio)
    return f


def price_features(row0: dict[str, Any], pts: list[tuple[float, float]], price_cut: Optional[float]
                   ) -> dict[str, Any]:
    if price_cut is None:
        return {}
    last = 1.0 if price_cut <= 0 else next((m for dt, m in reversed(pts) if dt <= price_cut), None)
    x = row0["fA"]
    lmc, prem = x.get("p_log_mc_usd"), x.get("p_entry_over_operator")
    if last is None:
        return {"mult_since_alert": None, "mc_usd": None, "log_mc_usd": None, "premium": None, "log_price": None}
    return {"mult_since_alert": last, "mc_usd": (10 ** lmc) * last if lmc is not None else None,
            "log_mc_usd": (lmc + math.log10(last)) if lmc is not None else None,
            "premium": prem * last if prem is not None else None,
            "log_price": math.log10(row0["p0"] * last) if row0.get("p0") else None}


def main() -> None:
    if os.path.exists(FREEZE):
        sys.exit("the entry-zone table is frozen (%s); it is not rebuilt" % FREEZE)
    base = {r["mint"]: r for r in ana_lib.load()}
    series = pde.load_series()
    alerts = sorted((a for a in pde.load_journal() if a["genre"] == "alerte_lancement"), key=lambda a: a["t"])
    rows, cover = [], defaultdict(Counter)
    t0 = time.time()
    for a in alerts:
        r0 = base[a["mint"]]
        w = json.load(gzip.open(os.path.join(FB.WIN, a["mint"] + ".json.gz"), "rt"))
        wal = json.load(gzip.open(os.path.join(FB.WAL, a["mint"] + ".json.gz"), "rt"))
        recs, facts = fparse.parse_window(w)
        slot0 = recs[0]["slot"]
        create = next((r for r in recs if r.get("kind") == "create"), None)
        creator = create["signer"] if create else None
        t_create = create["bt"] if create and create.get("bt") else a["t"] - (a.get("age_alerte_s") or 12)
        core = {k for k, v in wal["wallets"].items() if v["role"] == "core"}
        mig = next((r for r in recs if r.get("kind") == "migrate"), None)
        ev = buy_events(w, recs)
        pts = series.get(a["mint"]) or []
        ticket: dict[str, float] = defaultdict(float)
        for e in ev:
            if e["slot"] == slot0 and e["owner"] in core:
                ticket[e["owner"]] += e["sol"]
        fund = sniper_funding(wal, sorted(core), t_create, ticket)
        row = {"mint": a["mint"], "t": a["t"], "utc": a["utc"], "split": r0["split"], "cluster": r0["cluster"],
               "actor": r0["actor_type"], "fine": r0["fine"],
               "ctx": {"premium0": r0["fA"].get("p_entry_over_operator"), "log_mc0": r0["fA"].get("p_log_mc_usd"),
                       "actor_grouped": r0["fA"].get("c_actor_grouped")},
               "f": {}, "y": {}}
        for name, (lat, tcut, pcut, tol) in CUTS.items():
            cut_bt = None if tcut == "slot0" else a["t"] + tcut
            f = trade_features(ev, recs, core, creator, t_create, cut_bt, slot0, mig.get("bt") if mig else None)
            f.update(price_features(r0, pts, pcut))
            f.update(fund)
            row["f"][name] = {k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
                              for k, v in f.items()}
            y = labels(pts, r0["fine"], lat, tol)
            row["y"][name] = y
            cover[name][row["split"] + "_entry"] += y.get("entry") is not None
            cover[name][row["split"] + "_label"] += y.get("conf_2") is not None
        rows.append(row)
    os.makedirs(DERIVED, exist_ok=True)
    with open(TABLE, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
            for r in rows:
                gz.write((json.dumps(r, sort_keys=True) + "\n").encode("utf8"))
    n_split = Counter(r["split"] for r in rows)
    doc = {"frozen_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
           "sha256": hashlib.sha256(open(TABLE, "rb").read()).hexdigest(), "rows": len(rows),
           "rows_by_split": dict(n_split), "coverage_by_cutoff": {k: dict(v) for k, v in cover.items()},
           "cutoffs": {k: {"entry_s": v[0], "trades_until": v[1], "price_until": v[2], "entry_tolerance_s": v[3]}
                       for k, v in CUTS.items()},
           "source_table_sha256": json.load(open(ana_lib.FREEZE))["sha256"],
           "note": "counts only; no rate was computed before this freeze", "build_seconds": round(time.time() - t0)}
    with open(FREEZE, "w", encoding="utf8") as fh:
        json.dump(doc, fh, indent=1)
    os.chmod(TABLE, 0o444)
    os.chmod(FREEZE, 0o444)
    print(json.dumps(doc, indent=1))


if __name__ == "__main__":
    main()
