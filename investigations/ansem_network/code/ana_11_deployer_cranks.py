"""Who receives the creator fees that the deployer itself pushes? Control: is the Ansem wallet treated differently?

Stream over stored bodies. A crank = a transaction signed by the deployer with a DistributeCreatorFees instruction.
Writes evidence/deployer_cranks.csv: one row per crank with the recipient that gains the most SOL.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import zlib
from collections import defaultdict

from lib import CREATOR, DATA, OUT, guard, sol, utc

from forensics_v2 import decode as D


def main() -> None:
    db = sqlite3.connect(DATA / "rpc_raw" / "tx.sqlite")
    ck = DATA / "checkpoints" / "gtfa" / (CREATOR + "_start_end_balanceChanged.jsonl")
    per = defaultdict(lambda: [0, 0, None, None])
    with open(ck) as f, open(OUT / "deployer_cranks.csv", "w", newline="") as o:
        w = csv.writer(o)
        w.writerow(["ts_utc", "signature", "recipient", "sol", "vault"])
        for line in f:
            guard()
            for s in json.loads(line)["sigs"]:
                t = json.loads(zlib.decompress(db.execute("SELECT body FROM tx WHERE sig = ?", (s["signature"],)).fetchone()[0]))
                logs = t["meta"].get("logMessages") or []
                if not any("DistributeCreatorFees" in x for x in logs):
                    continue
                d = D.decode(t)
                if not d.ok or CREATOR not in d.signers:
                    continue
                gains = sorted(((n.sol, a) for a, n in d.owners.items() if n.sol > 0 and a != CREATOR), reverse=True)
                losses = sorted((n.sol, a) for a, n in d.owners.items() if n.sol < 0 and a != CREATOR)
                if not gains:
                    continue
                g, r = gains[0]
                w.writerow([utc(d.block_time), d.signature, r, sol(g), losses[0][1] if losses else ""])
                p = per[r]
                p[0] += 1
                p[1] += g
                p[2] = min(p[2] or d.block_time, d.block_time)
                p[3] = max(p[3] or d.block_time, d.block_time)
    top = sorted(per.items(), key=lambda x: -x[1][1])
    print("cranks", sum(p[0] for _, p in top), "recipients", len(top), "SOL", round(sum(p[1] for _, p in top) / 1e9, 2))
    for r, p in top[:20]:
        print(r, p[0], round(p[1] / 1e9, 2), utc(p[2]), utc(p[3]))


if __name__ == "__main__":
    main()
