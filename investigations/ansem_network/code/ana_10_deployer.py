"""Every launch of the deployer, from the raw transactions already stored: buy, gifts, sales, fee shares, tools.

Stream over the stored bodies, one transaction in memory at a time. Reads no network. Writes
evidence/deployer_tokens.csv and evidence/deployer_recipients.csv. Bodies exist for the first 800 pages of its
history; the later part only has rows, so fee shares after that point are not known and the table says so.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import struct
import zlib
from collections import defaultdict

from lib import CREATOR, DATA, OUT, guard, sol, utc

from forensics_v2 import decode as D

PFEE = "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ"
UXENTO = "uxtoRPdPjRekYmxs1uUqVRZWh38iqonc9KgPuZXPeSY"
DISC = {"bd0d8863bba4ed23", "6ffb31064e4e6a12"}  # the two update-shares layouts seen on the creation of ANSEM


def fee_shares(raw: bytes) -> list[tuple[str, int]]:
    """u32 count, then pubkey + u16 basis points. Raises on a body that does not fit: never a silent empty."""
    n = struct.unpack_from("<I", raw, 8)[0]
    if len(raw) < 12 + n * 34:
        raise ValueError("short fee-share body")
    return [(D.b58encode(raw[12 + i * 34:44 + i * 34]), struct.unpack_from("<H", raw, 44 + i * 34)[0]) for i in range(n)]


def test() -> None:
    body = bytes.fromhex("bd0d8863bba4ed2301000000e611c1799b5538c3bb97c228a465b9ba347131586677e8888312c7697ccdaff51027")
    assert fee_shares(body) == [("GV6UUmNxz2RpKxmNAPadYKb7uQpszwqQAu3qLJxVdC52", 10000)]


def main() -> None:
    test()
    db = sqlite3.connect(DATA / "rpc_raw" / "tx.sqlite")
    ck = DATA / "checkpoints" / "gtfa" / (CREATOR + "_start_end_balanceChanged.jsonl")
    mints: dict[str, dict] = defaultdict(lambda: {"created": None, "sig": None, "buy_sol": 0, "buy_tok": 0, "gifts": [],
                                                  "sold_tok": 0, "sold_sol": 0, "fee_shares": None, "uxento": 0,
                                                  "created_by_deployer": False})
    n = 0
    with open(ck) as f:
        for line in f:
            guard()
            for s in json.loads(line)["sigs"]:
                row = db.execute("SELECT body FROM tx WHERE sig = ?", (s["signature"],)).fetchone()
                if row is None:
                    raise SystemExit("missing body " + s["signature"])
                t = json.loads(zlib.decompress(row[0]))
                d = D.decode(t)
                n += 1
                if not d.ok or CREATOR not in d.signers:
                    continue
                net = d.owners.get(CREATOR)
                created = [x.mint for x in d.transfers if x.kind == "mint" and x.amount == 10**15 and D.PUMP in d.programs]
                for m in created:
                    e = mints[m]
                    e.update(created=d.block_time, sig=d.signature, created_by_deployer=d.fee_payer == CREATOR)
                    e["uxento"] += sum(x.amount for x in d.transfers if x.dst == UXENTO)
                for ix in t["transaction"]["message"]["instructions"]:
                    if d.keys[ix["programIdIndex"]] != PFEE:
                        continue
                    raw = D.b58decode(ix.get("data") or "")
                    if raw[:8].hex() in DISC:
                        target = [a for a in (d.keys[i] for i in ix["accounts"]) if a in mints]
                        for m in target[:1]:
                            mints[m]["fee_shares"] = fee_shares(raw)
                traded = net.tokens if net else {}
                for m, dt in traded.items():
                    if m == D.WSOL:
                        continue
                    e = mints[m]
                    if dt > 0 and net.sol < 0:
                        e["buy_tok"] += dt
                        e["buy_sol"] -= net.sol
                    elif dt < 0 and net.sol > 0:
                        e["sold_tok"] -= dt
                        e["sold_sol"] += net.sol
                for x in d.transfers:
                    if x.kind == "spl" and x.mint not in (None, D.WSOL) and x.src_owner == CREATOR and x.dst_owner \
                            and x.dst_owner != CREATOR and net and net.sol <= 0 and net.tokens.get(x.mint, 0) < 0:
                        mints[x.mint]["gifts"].append((x.dst_owner, x.amount, d.block_time, d.signature))
    created = {m: e for m, e in mints.items() if e["created"]}
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "deployer_tokens.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mint", "created_utc", "create_sig", "dev_buy_sol", "dev_buy_tokens", "gifted_tokens", "n_gift_recipients",
                    "sold_tokens", "sold_sol", "net_sol_trading", "uxento_fee_sol", "fee_shares", "gift_to_GV6UU"])
        for m, e in sorted(created.items(), key=lambda x: x[1]["created"]):
            g = sum(a for _, a, _, _ in e["gifts"])
            gv = sum(a for o, a, _, _ in e["gifts"] if o.startswith("GV6UUmNx"))
            shares = ";".join("%s:%d" % s for s in e["fee_shares"]) if e["fee_shares"] else ""
            w.writerow([m, utc(e["created"]), e["sig"], sol(e["buy_sol"]), e["buy_tok"] / 1e6, g / 1e6, len({o for o, *_ in e["gifts"]}),
                        e["sold_tok"] / 1e6, sol(e["sold_sol"]), sol(e["sold_sol"] - e["buy_sol"]), sol(e["uxento"]), shares, gv / 1e6])
    rec: dict[str, dict] = defaultdict(lambda: {"mints": set(), "tok": 0, "first": None, "last": None})
    fee_rec: dict[str, int] = defaultdict(int)
    for m, e in created.items():
        for o, a, ts, _ in e["gifts"]:
            r = rec[o]
            r["mints"].add(m)
            r["tok"] += a
            r["first"] = min(r["first"] or ts, ts)
            r["last"] = max(r["last"] or ts, ts)
        for o, _ in e["fee_shares"] or []:
            fee_rec[o] += 1
    with open(OUT / "deployer_recipients.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["recipient", "n_launches_gifted", "tokens_gifted", "first_gift_utc", "last_gift_utc", "n_launches_fee_share"])
        for o, r in sorted(rec.items(), key=lambda x: -len(x[1]["mints"])):
            if o not in fee_rec and not (r["tok"] >= 10**12 and len(r["mints"]) >= 2):  # dust sprays stay out of the published table
                continue
            w.writerow([o, len(r["mints"]), r["tok"] / 1e6, utc(r["first"]), utc(r["last"]), fee_rec.get(o, 0)])
        for o, c in fee_rec.items():
            if o not in rec:
                w.writerow([o, 0, 0, "", "", c])
    print("transactions read", n, "launches", len(created), "with fee shares", sum(1 for e in created.values() if e["fee_shares"]),
          "gift recipients", len(rec), "fee-share recipients", len(fee_rec))
    print("top fee-share recipients", sorted(fee_rec.items(), key=lambda x: -x[1])[:15])


if __name__ == "__main__":
    main()
