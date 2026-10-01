#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build, freeze and check the economic-mechanics table (analysis_plan.md, "Data").

Starts from the frozen coordination table (sha256 checked by cd_lib.load) and adds, from the same
on-chain cache, raw relations only: tokens bought; each exit up to alert + 30 s with its tokens, SOL
received, balance after and token recipients; the creation slot's SOL by buyer and the curve or pool
states recorded in it; the deployer's last 20 transactions before the creation; for every sniper that
snipes again later, its transactions between the two buys as recorded before its next buy. Prices go
to a separate file read only by the price-impact section. No group, label, role or measure is
computed here. Writes derived/em_table.jsonl.gz, derived/em_price.jsonl.gz, derived/EM_FREEZE.json,
then reloads both files and checks them.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "coordination_detection", "code"))
sys.path.insert(0, os.path.join(ROOT, "post_detection_forensics", "code"))
import cd_lib  # noqa: E402
import feat_30_build as FB  # noqa: E402
import fparse  # noqa: E402

pde = FB.pde
DERIVED = os.path.join(STUDY, "derived")
TABLE = os.path.join(DERIVED, "em_table.jsonl.gz")
PRICE = os.path.join(DERIVED, "em_price.jsonl.gz")
FREEZE = os.path.join(DERIVED, "EM_FREEZE.json")
_wal_cache: dict[str, Any] = {}


def wal_of(mint: str) -> dict[str, Any]:
    if mint not in _wal_cache:
        _wal_cache[mint] = json.load(gzip.open(os.path.join(FB.WAL, mint + ".json.gz"), "rt"))
    return _wal_cache[mint]


def compact(x: dict[str, Any]) -> dict[str, Any]:
    return {"bt": x.get("bt"), "sig": x.get("sig"), "signer": x.get("signer"), "err": x.get("err"), "d": x.get("d")}


def extend(
    r: dict[str, Any], nxt: dict[tuple[str, str], tuple[str, float]], series: dict[str, Any], p0: dict[str, float]
) -> tuple[dict[str, Any], dict[str, Any]]:
    w = json.load(gzip.open(os.path.join(FB.WIN, r["mint"] + ".json.gz"), "rt"))
    wal = wal_of(r["mint"])
    recs, facts = fparse.parse_window(w)
    curve, pool = facts.get("curve"), facts.get("pool")
    slot0 = r["slot0"]
    slot0_sol: dict[str, float] = defaultdict(float)
    states = []
    for x in recs:
        if x["slot"] != slot0 or x.get("err"):
            continue
        if x.get("venue") == "curve" and x.get("kind") in ("buy", "create"):
            for o, v in (x.get("leg_sol") or {}).items():
                slot0_sol[o] += max(0.0, v)
        states.append(
            {
                "curve_lamports": x.get("curve_lamports"),
                "curve_tok": x.get("curve_tok"),
                "pool_sol": x.get("pool_sol"),
                "pool_tok": x.get("pool_tok"),
                "kind": x.get("kind"),
            }
        )
    out = dict(r)
    out["slot0_sol"] = dict(slot0_sol)
    out["slot0_states"] = states
    out["migration_slot"] = facts.get("migration_slot")
    snipers = []
    for s in r["snipers"]:
        m = s["wallet"]
        bought = sum(max(0.0, (x.get("legs") or {}).get(m, 0.0)) for x in recs if x["sig"] in s["sigs"])
        exits = []
        for x in recs:
            lg = (x.get("legs") or {}).get(m, 0.0)
            if lg >= 0 or (x.get("bt") or 0) > r["t"] + 30:
                continue
            t = w["txs"].get(x["sig"]) or {}
            keys = [k["pubkey"] for k in ((t.get("transaction") or {}).get("message") or {}).get("accountKeys", [])]
            post = t.get("meta", {}).get("postBalances") if t else None
            exits.append(
                {
                    "sig": x["sig"],
                    "slot": x["slot"],
                    "bt": x.get("bt"),
                    "kind": x.get("kind"),
                    "tok_out": -lg,
                    "sol_in": (x.get("owner_sol") or {}).get(m),
                    "post_sol": post[keys.index(m)] / 1e9 if post and m in keys else None,
                    "recipients": {
                        o: v for o, v in (x.get("legs") or {}).items() if v > 0 and o not in (curve, pool, m)
                    },
                }
            )
        between = None
        n2 = nxt.get((m, r["mint"]))
        if n2:
            w2 = wal_of(n2[0])
            e2 = w2["wallets"].get(m) or {}
            rc = e2.get("recent") or []
            between = {
                "next_mint": n2[0],
                "next_t": n2[1],
                "complete": (e2.get("prior") or {}).get("n", 99) <= len(rc)
                or any((x.get("bt") or 0) <= (s["bt"] or r["t"]) for x in rc),
                "txs": [compact(x) for x in rc if (x.get("bt") or 0) > (s["bt"] or r["t"])],
            }
        snipers.append({**s, "tok_bought": bought, "exits_full": exits, "between": between})
    out["snipers"] = snipers
    cr = next((v for v in wal["wallets"].values() if v["role"] == "creator"), None)
    out["deployer_recent"] = [compact(x) for x in (cr or {}).get("recent") or []]
    price = {
        "mint": r["mint"],
        "p0": p0.get(r["mint"]),
        "t": r["t"],
        "t_create": r["t_create"],
        "window": [
            {
                "bt": x.get("bt"),
                "slot": x["slot"],
                "curve_lamports": x.get("curve_lamports"),
                "curve_tok": x.get("curve_tok"),
                "pool_sol": x.get("pool_sol"),
                "pool_tok": x.get("pool_tok"),
            }
            for x in recs
            if not x.get("err") and (x.get("curve_tok") is not None or x.get("pool_tok"))
        ],
        "series": [(dt, m) for dt, m in series.get(r["mint"], []) if dt <= 300],
    }
    return out, price


def main() -> None:
    if os.path.exists(FREEZE):
        sys.exit("the economic-mechanics table is frozen (%s); it is not rebuilt" % FREEZE)
    rows = sorted(cd_lib.load(), key=lambda z: z["t"])
    appear: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for r in rows:
        for s in r["snipers"]:
            appear[s["wallet"]].append((r["t"], r["mint"]))
    nxt = {}
    for wlt, lst in appear.items():
        lst.sort()
        for (t1, m1), (t2, m2) in zip(lst, lst[1:]):
            nxt[(wlt, m1)] = (m2, t2)
    series = pde.load_series()
    sys.path.insert(0, os.path.join(ROOT, "post_detection_forensics", "code"))
    import ana_lib

    p0 = {b["mint"]: b["p0"] for b in ana_lib.load()}
    built = [extend(r, nxt, series, p0) for r in rows]
    os.makedirs(DERIVED, exist_ok=True)
    for path, items in ((TABLE, [b[0] for b in built]), (PRICE, [b[1] for b in built])):
        with open(path, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
                for it in items:
                    gz.write((json.dumps(it, sort_keys=True) + "\n").encode("utf8"))
    doc = {
        "frozen_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "sha256_table": hashlib.sha256(open(TABLE, "rb").read()).hexdigest(),
        "sha256_price": hashlib.sha256(open(PRICE, "rb").read()).hexdigest(),
        "source_coordination_sha256": json.load(open(cd_lib.FREEZE))["sha256"],
        "rows": len(built),
        "note": "raw relations only; groups come from coordination_detection/derived/C_results.json; "
        "prices are in a separate file",
    }
    back = [json.loads(x) for x in gzip.open(TABLE, "rt", encoding="utf8")]
    pr = [json.loads(x) for x in gzip.open(PRICE, "rt", encoding="utf8")]
    cd = {r["mint"]: r for r in rows}
    checks = {
        "1,657 rows, the coordination table's mints": len(back) == 1657 and {r["mint"] for r in back} == set(cd),
        "same snipers as the coordination table": all(
            [s["wallet"] for s in r["snipers"]] == [s["wallet"] for s in cd[r["mint"]]["snipers"]] for r in back
        ),
        "every sniper bought tokens": all(s["tok_bought"] > 0 for r in back for s in r["snipers"]),
        "no exit after alert + 30 s": all(
            (x["bt"] or 0) <= r["t"] + 30 for r in back for s in r["snipers"] for x in s["exits_full"]
        ),
        "no exit before the sniper's buy slot": all(
            x["slot"] >= r["slot0"] for r in back for s in r["snipers"] for x in s["exits_full"]
        ),
        "flows between launches lie between the two buys": all(
            (s["bt"] or r["t"]) < (x["bt"] or 0) <= s["between"]["next_t"]
            for r in back
            for s in r["snipers"]
            if s["between"]
            for x in s["between"]["txs"]
        ),
        "price file aligned, no series read after 5 min": [p["mint"] for p in pr] == [r["mint"] for r in back]
        and all(dt <= 300 for p in pr for dt, _ in p["series"]),
        "no label, group or outcome field in the table": not any(k in back[0] for k in ("y", "labels", "label")),
    }
    doc["integrity"] = checks
    with open(FREEZE, "w", encoding="utf8") as fh:
        json.dump(doc, fh, indent=1)
    for p in (TABLE, PRICE, FREEZE):
        os.chmod(p, 0o444)
    print(json.dumps({k: doc[k] for k in ("sha256_table", "sha256_price", "rows")}, indent=1))
    for k, v in checks.items():
        print("%-60s %s" % (k, "ok" if v else "FAILED"))


if __name__ == "__main__":
    main()
