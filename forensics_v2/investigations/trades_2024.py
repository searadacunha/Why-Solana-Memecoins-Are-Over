"""Benjamin's own 2024 trades: rebuild every trip with this engine, on the cached raw transactions.

Private by construction: every output goes to forensics_v2/private_trades/, which git ignores. Inputs
are read only from the frozen historical_edge_2024 study, whose ledger gives the wallet perimeter and
whose figures are the thing being checked. A disagreement is reported and never adjusted away.

    python -m forensics_v2.investigations.trades_2024 reconcile
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Optional

from .. import decode as D
from ..trace import Trip, trips

STUDY = Path.home() / "Documents/Crypto/WSMO-historical-edge-2024/historical_edge_2024"
CACHE = STUDY / "data/cache/getTransaction"
PRIVATE = Path(__file__).resolve().parents[1] / "private_trades"
DEPOSIT = "6tmiM84AxMzmXzRByq7m1dgNkHtn9wp671e1GMe2ZmWU"
HOT = "FWznbcNXWQuHTawe9RxvQ2LdCENssh12dsznf4RiouN5"
OCT1, JAN1 = 1727740800, 1735689600  # 2024-10-01, 2025-01-01 UTC
FEB3 = 1738540800                    # 2025-02-03 UTC
SUPPLY_PUMP = 10**15


def ledger() -> dict[str, list[dict[str, Any]]]:
    return json.loads((STUDY / "derived/q1_ledger.json").read_text())["ledger"]


def _decode_wallet(job: tuple[str, list[str]]) -> tuple[str, list[D.Decoded]]:
    w, sigs = job
    out = []
    for s in sigs:
        with open(CACHE / (s + ".json")) as f:
            out.append(D.decode(json.load(f)["result"]))
    return w, out


def load_all() -> dict[str, list[D.Decoded]]:
    jobs = [(w, [r["sig"] for r in rows]) for w, rows in ledger().items()]
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        return dict(ex.map(_decode_wallet, jobs))


def frozen_trips() -> list[dict[str, str]]:
    with open(STUDY / "tables/q1_trips.csv") as f:
        return list(csv.DictReader(f))


def reconcile(all_txs: dict[str, list[D.Decoded]], built: list[Trip]) -> dict[str, Any]:
    """This engine's trips against the frozen study's table, by (wallet, mint, open time)."""
    old = {(r["wallet"], r["mint"], int(r["t_open"])): r for r in frozen_trips()}
    new = {(t.wallet, t.mint, t.t_open): t for t in built}
    in_window = {k: t for k, t in new.items() if OCT1 <= k[2] < JAN1}
    old_window = {k: r for k, r in old.items() if OCT1 <= k[2] < JAN1}
    diffs = []
    for k in set(in_window) & set(old_window):
        t, r = in_window[k], old_window[k]
        d_sol = t.realised - round(float(r["realised_sol"]) * 1e9)
        if abs(d_sol) > 2 or t.closed != (r["closed"] == "True"):
            diffs.append({"key": list(k), "new_lamports": t.realised, "old_sol": r["realised_sol"],
                          "new_closed": t.closed, "old_closed": r["closed"]})
    closed = [t for t in in_window.values() if t.closed]
    return {
        "transactions_decoded": sum(len(v) for v in all_txs.values()),
        "conservation_failures": sum(1 for v in all_txs.values() for d in v if not d.conserved),
        "trips_new_oct_dec": len(in_window), "trips_old_oct_dec": len(old_window),
        "only_new": len(set(in_window) - set(old_window)), "only_old": len(set(old_window) - set(in_window)),
        "closed_new": len(closed), "closed_old": sum(1 for r in old_window.values() if r["closed"] == "True"),
        "realised_lamports_new": sum(t.realised for t in closed),
        "realised_sol_old": sum(float(r["realised_sol"]) for r in old_window.values() if r["closed"] == "True"),
        "rows_differing_over_2_lamports": len(diffs), "diff_sample": diffs[:5],
    }


def fees_of(all_txs: dict[str, list[D.Decoded]], t: Trip) -> int:
    wanted = set(t.sigs)
    return sum(d.fee for d in all_txs[t.wallet] if d.signature in wanted and d.fee_payer == t.wallet)


def write_private(name: str, content: str) -> Path:
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    p = PRIVATE / name
    p.write_text(content)
    os.chmod(p, 0o600)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    all_txs = load_all()
    built = [t for w, v in all_txs.items() for t in trips(v, w)]
    rep = reconcile(all_txs, built)
    print(json.dumps(rep, indent=0))
    if args and args[0] == "reconcile":
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["Counter", "defaultdict"]
