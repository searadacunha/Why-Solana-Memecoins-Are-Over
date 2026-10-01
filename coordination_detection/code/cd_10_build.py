#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steps 3 to 5 of the protocol: build the coordination table, freeze it, check its integrity.

One row per launch with the raw relations only (no measure, no label): the snipers with their buy
(slot, time, transactions, ticket), genesis funder, last funder before the buy, source and hub
status; the creator with its funders; the early buyers (everyone else buying up to alert + 30 s,
flagged when before alert - 1 s); the snipers' exits up to alert + 30 s. Context from the frozen
table of post_detection_forensics (split, operator cluster, actor, premium, market cap, bundle).
No label of any kind is read. Writes derived/cd_table.jsonl.gz and derived/CD_FREEZE.json, refuses to
run again, then reloads the frozen file and checks it.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
ROOT = os.path.dirname(STUDY)
sys.path.insert(0, os.path.join(ROOT, "sniper_capital", "code"))
import sc_00_coverage as SC  # noqa: E402

FB, fparse, pde = SC.FB, SC.fparse, SC.pde
sys.path.insert(0, os.path.join(ROOT, "post_detection_forensics", "code"))
import ana_lib  # noqa: E402

DERIVED = os.path.join(STUDY, "derived")
TABLE = os.path.join(DERIVED, "cd_table.jsonl.gz")
FREEZE = os.path.join(DERIVED, "CD_FREEZE.json")


def hub_of(addr: Optional[str]) -> Optional[bool]:
    """Hub before its earliest funding in the corpus (genesis_hop cache); None when never measured."""
    if not addr:
        return None
    h = FB._hop(addr, False)
    if not h:
        return None
    return bool(h.get("hub_before_cursor"))


def source_of(addr: Optional[str]) -> Optional[str]:
    if not addr:
        return None
    h = FB._hop(addr, False) or {}
    if h.get("hub_before_cursor"):
        return None
    return (h.get("funding") or {}).get("funder")


def last_funding(entry: dict[str, Any], wallet: str) -> dict[str, Any]:
    fund = [
        x
        for x in entry.get("recent") or []
        if (x.get("d") or {}).get(wallet, 0) > 0 and not x.get("err") and x.get("signer") != wallet and x.get("bt")
    ]
    if not fund:
        return {}
    x = max(fund, key=lambda z: z["bt"])
    sender = min(x["d"], key=lambda k: x["d"][k])
    return {
        "last_funder": sender,
        "last_bt": x["bt"],
        "last_amount": x["d"][wallet],
        "last_sig": x.get("sig"),
        "last_funder_hub": hub_of(sender),
    }


def build_launch(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    w = json.load(gzip.open(os.path.join(FB.WIN, a["mint"] + ".json.gz"), "rt"))
    wal = json.load(gzip.open(os.path.join(FB.WAL, a["mint"] + ".json.gz"), "rt"))
    recs, facts = fparse.parse_window(w)
    slot0 = recs[0]["slot"]
    create = next((r for r in recs if r.get("kind") == "create"), None)
    creator = create["signer"] if create else None
    t_create = create["bt"] if create and create.get("bt") else a["t"] - (a.get("age_alerte_s") or 12)
    core = {k for k, v in wal["wallets"].items() if v["role"] == "core"}
    buys: dict[str, list[dict[str, Any]]] = defaultdict(list)
    early = []
    for r in recs:
        if r.get("err"):
            continue
        spent: dict[str, float] = {}
        if r.get("venue") == "curve" and r.get("kind") in ("buy", "create"):
            spent = {o: v for o, v in (r.get("leg_sol") or {}).items() if v > 0}
        elif r.get("venue") == "pool" and r.get("kind") == "buy":
            spent = {o: -v for o, v in (r.get("owner_sol") or {}).items() if v < 0}
        for o, s in spent.items():
            ev = {"sig": r["sig"], "slot": r["slot"], "bt": r.get("bt"), "sol": s, "venue": r["venue"]}
            if r["slot"] == slot0 and (o in core or o == creator) and r["venue"] == "curve":
                buys[o].append(ev)
            elif o not in core and o != creator and (r.get("bt") or 0) <= a["t"] + 30:
                early.append({"wallet": o, **ev, "pre_alert": (r.get("bt") or 0) <= a["t"] - 1})
    dev = sum(e["sol"] for e in buys.get(creator, [])) if creator else 0.0
    snipers = []
    for m, bl in buys.items():
        if m == creator and dev < FB.CORE_MIN_SOL:
            continue
        v = wal["wallets"].get(m) or {}
        g = (v.get("genesis") or {}).get("funding") or {}
        n = (v.get("prior") or {}).get("n", 0)
        gf = g.get("funder") if n < 1000 else None
        exits = [
            {"slot": r["slot"], "bt": r.get("bt"), "kind": r.get("kind"), "tok": -(r.get("legs") or {})[m]}
            for r in recs
            if (r.get("legs") or {}).get(m, 0) < 0 and (r.get("bt") or 0) <= a["t"] + 30
        ]
        snipers.append(
            {
                "wallet": m,
                "role": "creator" if m == creator else "core",
                "ticket": sum(e["sol"] for e in bl),
                "slot": min(e["slot"] for e in bl),
                "bt": min((e["bt"] for e in bl if e["bt"]), default=None),
                "sigs": sorted({e["sig"] for e in bl}),
                "n_prior": n,
                "gen_funder": gf,
                "gen_received": g.get("received") if gf else None,
                "gen_bt": g.get("bt") if gf else None,
                "gen_funder_hub": hub_of(gf),
                "source": source_of(gf),
                "exits": exits,
                **last_funding(v, m),
            }
        )
    cv = next(((k, v) for k, v in wal["wallets"].items() if v["role"] == "creator"), (creator, {}))
    cg = ((cv[1].get("genesis") or {}).get("funding") or {}) if cv[1] else {}
    cn = (cv[1].get("prior") or {}).get("n", 0) if cv[1] else 0
    creator_rec = {
        "wallet": creator,
        "gen_funder": cg.get("funder") if cn < 1000 else None,
        "gen_funder_hub": hub_of(cg.get("funder") if cn < 1000 else None),
        "source": source_of(cg.get("funder") if cn < 1000 else None),
        **(last_funding(cv[1], cv[0]) if cv[1] else {}),
    }
    x = b["fA"]
    return {
        "mint": a["mint"],
        "t": a["t"],
        "utc": a["utc"],
        "split": b["split"],
        "cluster": b["cluster"],
        "actor": b["actor_type"],
        "slot0": slot0,
        "t_create": t_create,
        "migrated_slot0": facts["migration_slot"] == slot0,
        "ctl": {
            "premium": x.get("p_entry_over_operator"),
            "log_mc": x.get("p_log_mc_usd"),
            "b_core_n": x.get("b_core_n"),
            "sol_bundle": x.get("b_core_sol"),
            "supply": x.get("b_core_supply"),
        },
        "creator": creator_rec,
        "snipers": snipers,
        "early": early,
    }


def main() -> None:
    if os.path.exists(FREEZE):
        sys.exit("the coordination table is frozen (%s); it is not rebuilt" % FREEZE)
    base = {r["mint"]: r for r in ana_lib.load()}
    alerts = sorted((a for a in pde.load_journal() if a["genre"] == "alerte_lancement"), key=lambda a: a["t"])
    rows = [build_launch(a, base[a["mint"]]) for a in alerts]
    os.makedirs(DERIVED, exist_ok=True)
    with open(TABLE, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
            for r in rows:
                gz.write((json.dumps(r, sort_keys=True) + "\n").encode("utf8"))
    sha = hashlib.sha256(open(TABLE, "rb").read()).hexdigest()
    doc = {
        "frozen_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "sha256": sha,
        "rows": len(rows),
        "rows_by_split": dict(Counter(r["split"] for r in rows)),
        "sniper_records": sum(len(r["snipers"]) for r in rows),
        "early_buys": sum(len(r["early"]) for r in rows),
        "source_table_sha256": json.load(open(ana_lib.FREEZE))["sha256"],
        "note": "raw relations only; no coordination measure, label or price outcome computed",
    }
    with open(FREEZE, "w", encoding="utf8") as fh:
        json.dump(doc, fh, indent=1)
    os.chmod(TABLE, 0o444)
    os.chmod(FREEZE, 0o444)
    # step 5: integrity, on the file as frozen
    assert hashlib.sha256(open(TABLE, "rb").read()).hexdigest() == sha
    back = [json.loads(x) for x in gzip.open(TABLE, "rt", encoding="utf8")]
    checks = {
        "rows = alerts of the snapshot": len(back) == len(alerts) == 1657,
        "one row per mint": len({r["mint"] for r in back}) == len(back),
        "every launch has 4 snipers or more": all(len(r["snipers"]) >= 4 for r in back),
        "snipers = the detector's count (b_core_n) on every launch": sum(
            1 for r in back if len(r["snipers"]) == r["ctl"]["b_core_n"]
        )
        == len(back),
        "sniper records as in coverage.md (6,822)": sum(len(r["snipers"]) for r in back) == 6822,
        "every sniper bought in the creation slot": all(s["slot"] == r["slot0"] for r in back for s in r["snipers"]),
        "no early buy after alert + 30 s": all((e["bt"] or 0) <= r["t"] + 30 for r in back for e in r["early"]),
        "no sniper exit after alert + 30 s": all(
            (x["bt"] or 0) <= r["t"] + 30 for r in back for s in r["snipers"] for x in s["exits"]
        ),
        "no last funding at or after the buy": all(
            s.get("last_bt") is None or s["bt"] is None or s["last_bt"] <= s["bt"] for r in back for s in r["snipers"]
        ),
    }
    doc["integrity"] = checks
    print(
        json.dumps({k: doc[k] for k in ("sha256", "rows", "rows_by_split", "sniper_records", "early_buys")}, indent=1)
    )
    for k, v in checks.items():
        print("%-70s %s" % (k, "ok" if v else "FAILED"))
    with open(os.path.join(DERIVED, "CD_INTEGRITY.json"), "w") as fh:
        json.dump(checks, fh, indent=1)


if __name__ == "__main__":
    main()
