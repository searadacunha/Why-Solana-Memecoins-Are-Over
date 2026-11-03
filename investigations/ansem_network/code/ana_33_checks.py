"""Small checks the report leans on: who pays the fee account, the first wallet citing GV6UUmNx, the fee pusher, the one-slot group.

Reads the network for a few transactions. Writes evidence/small_checks.json.
"""
from __future__ import annotations

import json
from collections import Counter

import duckdb

from ana_30_links import DEPLOYER_SIDE, GV
from lib import CREATOR, DATA, MINT, OUT, client, utc

from forensics_v2 import decode as D

CQ = "CQfwrncb67iboVdGB62naWUFUWutuRfizZ3jncGRNTiR"
VAULT = "AdPnUcnMJY4JExDWXb2Zd3QD76VYP1c6KHszwVZqjUfv"
POOL = "FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC"
P8 = "8wvqvPt1DDdjdghpMpp7ueQFUL5Js5zux4pPeRFXWteB"


def main() -> None:
    c = client(run_limit=400)
    out: dict = {}
    rows = [json.loads(x) for x in open(DATA / "mint" / "pre_takeoff.jsonl")]
    group = {o for r in rows if r["slot"] == 429250207 for o, n in r["nets"].items() if o != POOL and n["tok"] > 0 and n["sol"] < -1_000_000}
    out["group"] = sorted(group)

    # 1. every buyer pays the same fee account
    sample = []
    inside = [r for r in rows if r["slot"] == 429250207][:4]
    buys = [r for r in rows if r["slot"] != 429250207 and any(o != POOL and n["tok"] > 0 and n["sol"] < -20_000_000 for o, n in r["nets"].items())]
    for r, tag in [(x, "in group") for x in inside] + [(x, "outside") for x in buys[:3] + buys[len(buys) // 2:len(buys) // 2 + 3] + buys[-3:]]:
        d = D.decode(c.tx(r["sig"]))
        sample.append({"sig": r["sig"], "where": tag, "fee_account_gain": d.lamport_delta.get(CQ, 0), "vault_owner_gain": d.owners[VAULT].sol if VAULT in d.owners else None})
    out["fee_account_sample"] = sample
    assert all(s["fee_account_gain"] > 0 for s in sample)

    # 2. the first wallet citing GV6UUmNx
    first = json.load(open(OUT / "genesis_check.json"))["first_transaction"]
    t = c.tx(first)
    d = D.decode(t)
    out["first_tx"] = {"sig": first, "signers": d.signers, "gv_in_keys": GV in d.keys, "time": utc(d.block_time), "logs": [x.split("Instruction: ")[1] for x in t["meta"]["logMessages"] if "Instruction: " in x][:5]}
    fp = d.fee_payer
    con = duckdb.connect(config={"memory_limit": "1GB", "threads": 2})
    src = str(DATA / "rows" / "*.jsonl")
    con.execute(f"""CREATE TABLE s AS SELECT DISTINCT kind, sig, ts, src, dst, lamports, mint, raw, list_contains(signers, src) ss FROM read_json('{src}', union_by_name=true, maximum_object_size=8000000, sample_size=20000,
        columns={{kind:'VARCHAR',sig:'VARCHAR',ts:'BIGINT',src:'VARCHAR',dst:'VARCHAR',lamports:'HUGEINT',mint:'VARCHAR',raw:'HUGEINT',signers:'VARCHAR[]'}}) WHERE kind IN ('sol','token_transfer')""")
    con.execute("CREATE TABLE ds AS SELECT unnest(?::VARCHAR[]) a", [DEPLOYER_SIDE])
    out["first_tx"]["fee_payer_sol_with_family"] = con.execute("SELECT count(*) FROM s WHERE kind='sol' AND ((src=? AND dst IN (SELECT a FROM ds)) OR (dst=? AND src IN (SELECT a FROM ds)))", [fp, fp]).fetchone()[0]

    # 3. the one-slot group against his wallet and the family
    con.execute("CREATE TABLE g AS SELECT unnest(?::VARCHAR[]) a", [sorted(group)])
    out["group_sol_with_ansem_wallet"] = con.execute("SELECT src,dst,count(*),sum(lamports)::DOUBLE/1e9 FROM s WHERE kind='sol' AND ((src=? AND dst IN (SELECT a FROM g)) OR (dst=? AND src IN (SELECT a FROM g))) GROUP BY 1,2", [GV, GV]).fetchall()
    out["group_ansem_from_ansem_wallet"] = con.execute("SELECT dst,count(*),sum(raw)::DOUBLE/1e6,min(ts) FROM s WHERE kind='token_transfer' AND src=? AND ss AND mint=? AND dst IN (SELECT a FROM g) GROUP BY 1", [GV, MINT]).fetchall()
    out["group_sol_with_family"] = con.execute("SELECT src,dst,count(*),sum(lamports)::DOUBLE/1e9 FROM s WHERE kind='sol' AND ((src IN (SELECT a FROM ds) AND dst IN (SELECT a FROM g)) OR (dst IN (SELECT a FROM ds) AND src IN (SELECT a FROM g))) GROUP BY 1,2", []).fetchall()

    # 4. first funders of the fee pusher and of another sender
    for w in (P8, "GeBJSHK4WsGrz2HRvTbqvWGx4JRMpHfJG2ikzrYBDuwR"):
        out["first_funder_" + w[:8]] = con.execute("SELECT src, lamports::DOUBLE/1e9, ts FROM s WHERE kind='sol' AND dst=? AND lamports>=10000000 ORDER BY ts LIMIT 1", [w]).fetchall()

    # 5. what the fee pusher does, in pages across its 28-29 June window
    who = Counter()
    per_time = []
    n = pushes = 0
    for start in (1782683700, 1782685000, 1782690000, 1782698000):
        r = c.call("getTransactionsForAddress", [P8, {"transactionDetails": "full", "sortOrder": "asc", "limit": 100, "encoding": "json", "maxSupportedTransactionVersion": 1,
                                                      "filters": {"blockTime": {"gte": start, "lte": start + 3600}, "tokenAccounts": "balanceChanged"}}], P8, credits=10)
        here = Counter()
        for t in r["data"]:
            d = D.decode(t)
            n += 1
            if d.fee_payer != P8 or not any("DistributeCreatorFees" in x for x in t["meta"].get("logMessages") or []):
                continue
            pushes += 1
            g = [(x.sol, o) for o, x in d.owners.items() if x.sol > 0 and o != P8]
            if g:
                who[max(g)[1]] += 1
                here[max(g)[1][:8]] += 1
        per_time.append([utc(start), len(r["data"]), here.most_common(3)])
    out["pusher_sample"] = {"transactions": n, "pushes": pushes, "recipients": who.most_common(8), "by_page": per_time}
    (OUT / "small_checks.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print({k: v for k, v in out.items() if k not in ("fee_account_sample", "group")})
    print("fee account paid by all", len(sample), "in group", sum(s["where"] == "in group" for s in sample), "credits", c.budget.used(), CREATOR[:4])


if __name__ == "__main__":
    main()
