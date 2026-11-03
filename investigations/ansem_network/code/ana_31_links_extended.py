"""Second pass of link tests once the Ansem wallet and the deployer are fully read. No network.

Adds the Ansem wallet's exit hops, asks whether any money reaches the other side through a hub, whether the deployer's
family re-entered ANSEM before the airdrop post, and whether the Ansem wallet bought any launch of that family.
Writes evidence/link_tests_extended.json. Addresses named here all come from walked rows.
"""
from __future__ import annotations

import json

import duckdb

from ana_30_links import DEPLOYER_SIDE, GV, SIDE_WALLETS
from lib import DATA, MINT, OUT

A_SET = [GV, "H3t5AYjF4ukuZ1HL2WCQqtSucRWWSZSoaiwYoWeshKPJ", "EvktFyjtaToEGWnKVSJnwJacDvFBddzrxtUmiN795k8D",
         "2YPypQAQkFFtmwNgEcmnyqe2EJTThzoMTeUuMYmYcPiT", "BrV2WXWw5wU9pca4Nu4FJLhLU5cAbrkmLfXQmYm3ZZJG",
         "7oU9nR9VEvFPwvp2PpXo2LQc6A92QRhcUTwhLWT7MsDM"]
AIRDROP_POST = 1782568988  # 2026-06-27 14:03:08 UTC


def main() -> None:
    con = duckdb.connect(config={"memory_limit": "1200MB", "threads": 2})
    src = str(DATA / "rows" / "*.jsonl")
    con.execute(f"""CREATE TABLE r AS SELECT DISTINCT wallet, kind, sig, ts, src, dst, lamports, mint, raw, creator, fee_payer, sol,
                    to_json(mints) AS mints, list_contains(signers, src) AS src_signed
                    FROM read_json('{src}', union_by_name=true, maximum_object_size=8000000, sample_size=20000,
                    columns={{wallet:'VARCHAR', kind:'VARCHAR', sig:'VARCHAR', ts:'BIGINT', src:'VARCHAR', dst:'VARCHAR',
                    lamports:'HUGEINT', mint:'VARCHAR', raw:'HUGEINT', creator:'VARCHAR', fee_payer:'VARCHAR', sol:'HUGEINT',
                    mints:'JSON', signers:'VARCHAR[]'}})""")
    con.execute("CREATE TABLE ds AS SELECT unnest(?::VARCHAR[]) a", [DEPLOYER_SIDE])
    con.execute("CREATE TABLE ag AS SELECT unnest(?::VARCHAR[]) a", [A_SET])
    con.execute("CREATE TABLE sw AS SELECT unnest(?::VARCHAR[]) a", [SIDE_WALLETS])
    con.execute("""CREATE TABLE cp AS SELECT wallet, CASE WHEN src=wallet THEN dst ELSE src END other,
                   CASE WHEN src=wallet THEN 'out' ELSE 'in' END dir, count(*) n, sum(lamports)::DOUBLE/1e9 sol, min(ts) t0, max(ts) t1
                   FROM r WHERE kind='sol' AND lamports>=10000000 GROUP BY 1,2,3""")
    out: dict = {"ansem_side": A_SET}

    def q(sql: str, *p) -> list:
        return con.execute(sql, list(p)).fetchall()

    out["direct_sol_between_sides"] = q("""SELECT wallet,src,dst,count(*),sum(lamports)::DOUBLE/1e9 FROM r WHERE kind='sol'
        AND ((src IN (SELECT a FROM ag) AND dst IN (SELECT a FROM ds)) OR (src IN (SELECT a FROM ds) AND dst IN (SELECT a FROM ag))) GROUP BY 1,2,3""")
    out["hubs_used_by_both_sides"] = q("""SELECT a.other, a.wallet, a.dir, a.n, a.sol, d.wallet, d.dir, d.n, d.sol
        FROM cp a JOIN cp d ON a.other=d.other
        WHERE a.wallet IN (SELECT a FROM ag) AND d.wallet IN (SELECT a FROM ds)
          AND a.other NOT IN (SELECT a FROM ag) AND a.other NOT IN (SELECT a FROM ds)
          AND a.sol>=1 AND d.sol>=1 ORDER BY a.sol+d.sol DESC""")
    out["side_wallets_with_either_side"] = q("""SELECT wallet,src,dst,count(*),sum(lamports)::DOUBLE/1e9,min(ts) FROM r WHERE kind='sol'
        AND ((src IN (SELECT a FROM sw) AND (dst IN (SELECT a FROM ds) OR dst IN (SELECT a FROM ag)))
          OR (dst IN (SELECT a FROM sw) AND (src IN (SELECT a FROM ds) OR src IN (SELECT a FROM ag)))) GROUP BY 1,2,3""")
    out["launches_by_deployer_family"] = q("SELECT creator,count(DISTINCT mint),min(ts),max(ts) FROM r WHERE kind='create' AND creator=wallet AND wallet IN (SELECT a FROM ds) GROUP BY 1 ORDER BY 2 DESC")
    # Buys and sales of the Ansem wallet are in followups.json: a fee-payer filter drops transactions a relayer paid for.
    family = set(DEPLOYER_SIDE)
    reentry = {}
    for name in ("launch_to_takeoff", "pre_takeoff", "takeoff"):
        for line in open(DATA / "mint" / (name + ".jsonl")):
            row = json.loads(line)
            for o, n in row["nets"].items():
                if o in family and row["ts"] > 1781644000:
                    reentry.setdefault(o, []).append((row["ts"], n["tok"], n["sol"], row["sig"]))
    out["deployer_family_in_ANSEM_trades_after_its_exit"] = reentry
    out["signed_ansem_out"] = q("SELECT count(*),sum(raw)::DOUBLE/1e12,count(DISTINCT dst),min(ts),max(ts) FROM r WHERE kind='token_transfer' AND wallet=? AND src=? AND src_signed AND mint=?", GV, GV, MINT)
    (OUT / "link_tests_extended.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    for k, v in out.items():
        if isinstance(v, list):
            print(k, len(v))
            for x in v[:40]:
                print("   ", [y[:12] if isinstance(y, str) else (round(y, 2) if isinstance(y, float) else y) for y in x] if isinstance(x, tuple) else x)
        elif isinstance(v, dict):
            print(k, {a: (b if not isinstance(b, list) else len(b)) for a, b in v.items()})


if __name__ == "__main__":
    main()
