"""The nine wallets of FNqJtYs7... (h2w6gm6jz), rebuilt from signatures only.

Writes forensics_v2/reports/nine_wallets/evidence.json and prints a summary. No figure is copied from
the published dossier: the dossier's claims are read only to compare against at the end.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .. import decode as D
from ..__main__ import client
from ..trace import history, sol_flows, trips

MINT = "FNqJtYs7rsP1H9GXWTtc5VnDoL2GhXEUKhYN46EEpump"
CURVE = "5TSu3vPcYC1vrxoan9DJK9uQAAHUqmGTMBvnd1iLwzAg"
G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"
AMOUNT = 2_976_815_600
SUPPLY = 10**15
NINE = ("Csye9QE8LomP9RHzQAWLVh8XFdyNXvaopzrAuo3a1PoW BmkuX6DaZUp9UCeR3XqAD6NjSpiFySnBvXyLT9uo7ZEA "
        "AwQqcqdQQ3zydrtWMVF1PPDaWMNK7Lmhm3sUyDNGnSSY 3bBaA1MpQZuQpHjWZBEig12JB1W1TTQikxYPjUgGG3kU "
        "CDvfNWiamAR1B84GUgttvDCGtiQE5dvJ49toF4fzsV5g 92w4K8uLg78KHWHxRovTDksLmou7MekcenY5PntPR34R "
        "6QMshP9zwFXKbpLPh7w8EwadjA6vVasKAC7zu5HfMA22 BXuznwXTXt4QbLtLTkQnKNaXwdJ4PDXHvDcXf9DMogxe "
        "5ibajLyeBmJhDfyZJN9FQsJBi48h8QSYg7eHGGhFjog6").split()
REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "reports" / "nine_wallets"


def curve_order(c: Any) -> dict[str, Any]:
    """Every TradeEvent on the bonding curve, in exact chain order."""
    h = history(c, CURVE, token_accounts="none", max_pages=30)
    order = {}
    for s in reversed(h.walk.signatures):
        order[s["signature"]] = (s["slot"], s.get("transactionIndex", -1))
    events = []
    create = None
    for d in sorted(h.txs, key=lambda x: order.get(x.signature, (x.slot, -1))):
        if not d.ok:
            continue
        for e in d.trade_events:
            if e["mint"] == MINT:
                events.append({**e, "sig": d.signature, "slot": d.slot, "index": order[d.signature][1],
                               "t": d.block_time})
        if create is None and any(t.kind == "mint" and t.mint == MINT for t in d.transfers):
            create = {"signature": d.signature, "slot": d.slot, "t": d.block_time, "fee_payer": d.fee_payer}
    rank: dict[str, int] = {}
    first: dict[str, dict[str, Any]] = {}
    for e in events:
        if e["buy"] and e["user"] not in rank:
            rank[e["user"]] = len(rank) + 1
            first[e["user"]] = e
    return {"complete": h.walk.complete, "stop": h.walk.stop, "n_tx": len(h.txs), "create": create, "events": events,
            "rank": rank, "first": first}


def one_wallet(c: Any, w: str, curve: dict[str, Any]) -> dict[str, Any]:
    h = history(c, w, max_pages=10)
    flows, unresolved = sol_flows(h)
    fund = [f for f in flows if f.dst == w and f.src == G2Y]
    all_in = [f for f in flows if f.dst == w]
    first_tx = h.txs[0] if h.txs else None
    tr = [t for t in trips(h.txs, w) if t.mint == MINT]
    legs = []
    for d in h.txs:
        tok = D.traded_mints(d, w).get(MINT)
        if tok:
            legs.append({"sig": d.signature, "t": d.block_time, "slot": d.slot, "tok": tok,
                         "sol_lamports": d.lamport_delta.get(w, 0), "venues": d.venues,
                         "signers": d.signers, "fee_payer": d.fee_payer,
                         "pct_supply": round(tok * 100 / SUPPLY, 4)})
    last_sell_t = max((x["t"] for x in legs if x["tok"] < 0), default=None)
    out_after = [f for f in flows if f.src == w and last_sell_t is not None and (f.ts or 0) >= last_sell_t]
    dests: dict[str, int] = defaultdict(int)
    for f in out_after:
        dests[f.dst] += f.lamports
    return {
        "wallet": w,
        "coverage": h.coverage(),
        "first_tx_is_g2y_funding": bool(first_tx and fund and fund[0].signature == first_tx.signature),
        "g2y_credits": [{"sig": f.signature, "lamports": f.lamports, "t": f.ts, "slot": f.slot,
                         "instruction": f.path, "evidence": f.evidence} for f in fund],
        "other_inflows_sol": sum(f.lamports for f in all_in if f.src != G2Y) / 1e9,
        "n_other_inflows": sum(1 for f in all_in if f.src != G2Y),
        "curve_rank": curve["rank"].get(w),
        "legs": legs,
        "trips": [{"open": t.t_open, "close": t.t_close, "sol_out": t.sol_out, "sol_in": t.sol_in, "closed": t.closed,
                   "realised_lamports": t.realised, "n_buys": t.n_buys, "n_sells": t.n_sells,
                   "venues": sorted(t.venues)} for t in tr],
        "other_mints_traded": len({t.mint for t in trips(h.txs, w)} - {MINT}),
        "last_activity": h.txs[-1].block_time if h.txs else None,
        "outflows_after_last_sell": sorted(dests.items(), key=lambda x: -x[1])[:12],
        "unresolved_sol_events": len(unresolved),
        "conservation_failures": sum(1 for d in h.txs if not d.conserved),
        "all_out": [{"dst": f.dst, "lamports": f.lamports, "sig": f.signature, "t": f.ts, "evidence": f.evidence}
                    for f in flows if f.src == w],
    }


def main() -> int:
    c = client(int(sys.argv[1]) if len(sys.argv) > 1 else 1500)
    curve = curve_order(c)
    rows = [one_wallet(c, w, curve) for w in NINE]

    a = json.loads((REPO / "data/split/all_buyers_g2y.json").read_text())["h2w6gm6jz"]
    e1 = json.loads((REPO / "data/trace_h2w6/e1_buyers_h2w6gm6jz.json").read_text())
    e2 = json.loads((REPO / "data/trace_h2w6/e2_funding_h2w6gm6jz.json").read_text())
    e6 = json.loads((REPO / "data/trace_h2w6/e6_courbe_acheteurs.json").read_text())
    b_wallets = [x["wallet"] for x in e1["buyers"]]
    a_text = json.dumps(a)
    shared = [w for w in b_wallets if w in a_text]
    create_t = curve["create"]["t"] if curve["create"] else None
    dest_counter: Counter[str] = Counter()
    for r in rows:
        for x in r["all_out"]:
            dest_counter[x["dst"]] += 1
    shared_dests = {k: v for k, v in dest_counter.items() if v >= 2}
    report = {
        "mint": MINT, "curve": CURVE,
        "curve_history": {k: curve[k] for k in ("complete", "stop", "n_tx", "create")},
        "n_curve_events": len(curve["events"]), "n_distinct_curve_buyers": len(curve["rank"]),
        "wallets": rows,
        "reconciliation": {
            "collection_B_e1": {"file": "data/trace_h2w6/e1_buyers_h2w6gm6jz.json", "n": len(b_wallets),
                                "curve_tx_inspected": e1["n_curve_tx_inspected"],
                                "curve_signatures_total": e1["curve_signatures_total"],
                                "ranks_now": sorted(curve["rank"].get(w, -1) for w in b_wallets)},
            "collection_A_keys": sorted(a.keys()),
            "e6_declared_distinct_buyers": e6["n_acheteurs_distincts_courbe"],
            "wallets_shared_B_and_A": shared,
            "nine_ranks_now": {w[:8]: curve["rank"].get(w) for w in NINE},
            "nine_ranks_e6": {w[:8]: e6["rang_par_wallet"].get(w) for w in NINE},
            "e2_n_wallets": e2["n_wallets"],
        },
        "shared_destinations_of_the_nine": shared_dests,
        "seconds_first_to_last_credit": (lambda ts: max(ts) - min(ts))(
            [x["t"] for r in rows for x in r["g2y_credits"] if x["lamports"] == AMOUNT]),
        "hours_last_credit_to_creation": None if not create_t else (create_t - max(
            x["t"] for r in rows for x in r["g2y_credits"] if x["lamports"] == AMOUNT)) / 3600,
        "net_calls": c.net_calls, "cache_hits": c.cache_hits,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "evidence.json").write_text(json.dumps(report, indent=1, default=list))
    print(json.dumps({k: report[k] for k in ("curve_history", "n_curve_events", "n_distinct_curve_buyers",
                                             "seconds_first_to_last_credit", "hours_last_credit_to_creation",
                                             "net_calls", "cache_hits")}, indent=0))
    for r in rows:
        buys = [x for x in r["legs"] if x["tok"] > 0]
        sells = [x for x in r["legs"] if x["tok"] < 0]
        print(r["wallet"][:8], "cred", [x["lamports"] for x in r["g2y_credits"]][:3], "firstIsFund",
              r["first_tx_is_g2y_funding"], "rank", r["curve_rank"], "txs", r["coverage"]["transactions_read"],
              r["coverage"]["walk_stop"], "buys", len(buys), "%.3fSOL" % (sum(-x["sol_lamports"] for x in buys) / 1e9),
              "%.3f%%" % sum(x["pct_supply"] for x in buys), "sells", len(sells),
              "%.3fSOL" % (sum(x["sol_lamports"] for x in sells) / 1e9), "otherMints", r["other_mints_traded"],
              "unres", r["unresolved_sol_events"], "cons", r["conservation_failures"])
    print(json.dumps(report["reconciliation"], indent=0)[:1500])
    print("shared dests", len(shared_dests), sorted(shared_dests.items(), key=lambda x: -x[1])[:8])
    return 0


if __name__ == "__main__":
    sys.exit(main())
