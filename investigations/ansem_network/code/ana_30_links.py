"""Link tests between the deployer's side and the wallet Ansem claims, from walked rows only. No network.

A token transfer only counts as sent by a wallet if that wallet signed it: Token-2022 permanent delegates can move
balances without the holder (see the 278DWF mint in REPORT.md). SOL cannot move that way.
Aggregates run in DuckDB under a memory limit. Writes evidence/link_tests.json.
"""
from __future__ import annotations

import json
import sys

import duckdb

from lib import CREATOR, DATA, OUT, utc

GV = "GV6UUmNxz2RpKxmNAPadYKb7uQpszwqQAu3qLJxVdC52"
DEPLOYER_SIDE = [CREATOR, "FkCcgvCoR6p6BRucCnU1t1DXP97Y3rJeMYBiU1o31nuv", "F5XqYtdUWUT7bbuuKEjckDs8Hwk7j7mhdwGe3YKn5Xf7",
                 "AvYukzeAFzFo66i1GJHShcdBbb4jeSkZiEJnNMds54mo", "4qcD8iSFLC5VDZphBtM7pSeevtHtD8Chi7Zmhcm9TvHm",
                 "DxnxpqcUsErqRFRbfVrKr988F9AxayryC5eKWPKgvjmR", "E94dd6pnFhE7LNbC7oSbyWmCCQ9kNoEhSa6cKN6brSAm",
                 "9bxyzm6MFn3TWEedvYuMzSaZkkGWKSyTgWpRXCzMP3dm", "6xMLLrtZAh8ToWjeZ9Nm4RKtEC3uY2Qqscihz4yHp1jK"]
SIDE_WALLETS = ["5URyNUmhcuWdZiiQrtNdFrSbQPfq72UV2gqQasr9c19Y", "6btcCbEdYnCUyuzV3JEMDpw9YbbF1tPFzNSN2Sfwg5eT",
                "DAEdBmTPEKM6xkwfzC3d411QUe6coKpkND6UURa4CvHC", "6F5x9fKqXCfPf8Rufs6ZvLjzPfCicytUgWexzx6LxoDi",
                "5FGoPPj1nL8LCnfVnpTmreqQtqLuMXXAwuS1uahMrp8V", "HDixbrzwwLXczhDBk1JVrurPQsuLE8FUKnW2pucSXN3o",
                "49foKJpRnZUaPKsDgnQhUFRMk7NX4zD5KgtVpxgvctLa", "9nGDHK9mp8JvKiNghu395xr188hXXXNYE4X1GTQjgHTd",
                "3nyg554J8SmDuhr8f6ZAvemWd35ngdzzw4QW678KZTqW"]
EARLY = ["2M2vLX34LXMg24dMEnjWHvRXS1tshpEDRWzmXgV8ENNZ", "8dut5xTs5V7EG9ccek11xDG5eBHkfYc3NdqcxjtWNsbS",
         "H6KiqN3wwirFumem4ZqxbF3hhHNTjpyps3q7TTLX3n33", "AmNDxHzjmkx7FS8sT7QpCYmVt9GTdpAFtmMi33YKgZLZ",
         "CxCTVjvgK3bWcgavMKo8PushR8ycw1atrWiSTruZrdtT", "CeZbzsqje88U7GCCrAiGUr5BrZrBJ3AkQMyG9aggDiqQ",
         "9aP2vSFp2rydWR7C7kVZSQLQa2sT62w23ZHVP8BVSR5T", "CEUA7zVoDRqRYoeHTP58UHU6TR8yvtVbeLrX1dppqoXJ",
         "HTpdiUfKjXxLBUEJ5ZvkaF1ED1qrqF92je39GtUpuKdE", "H87Hk58orfNgTc7st5nxcJmMfLPpLpRHRxK4cnJk8wBY",
         "XXXXXahGswEH6i3Czn19XbGxQrobJoY1TYJegPxp3ex", "PMJA8UQDyWTFw2Smhyp9jGA6aTaP7jKHR7BPudrgyYN",
         "AX78YQBANLBtF2PT5ngHF5oBsH4tiZavCf9QAFaJSdYn", "2c4gLYy6RfY1nNrv1vH7Cnn5AAWVhTezSWTktZbJmtQo"]
DUST = 10_000_000


def main() -> None:
    con = duckdb.connect(config={"memory_limit": "1GB", "threads": 2})
    src = str(DATA / "rows" / "*.jsonl")
    con.execute(f"""CREATE TABLE r AS SELECT DISTINCT wallet, kind, sig, ts, src, dst, lamports, mint, raw, basis,
                    list_contains(signers, src) AS src_signed
                    FROM read_json('{src}', union_by_name=true, maximum_object_size=8000000, sample_size=20000,
                    columns={{wallet:'VARCHAR', kind:'VARCHAR', sig:'VARCHAR', ts:'BIGINT', src:'VARCHAR', dst:'VARCHAR',
                    lamports:'HUGEINT', mint:'VARCHAR', raw:'HUGEINT', basis:'VARCHAR', signers:'VARCHAR[]'}})
                    WHERE kind IN ('sol','token_transfer')""")
    print("rows", con.execute("SELECT count(*) FROM r").fetchone()[0], flush=True)
    con.execute("CREATE TABLE u AS SELECT DISTINCT kind, sig, ts, src, dst, lamports, mint, raw, basis, src_signed FROM r")  # a transfer read from both sides counts once
    con.execute("CREATE TABLE ds AS SELECT unnest(?::VARCHAR[]) a", [DEPLOYER_SIDE])
    out: dict = {"deployer_side": DEPLOYER_SIDE, "ansem_wallet": GV, "dust_lamports": DUST}

    def rows(q: str, *p) -> list:
        return con.execute(q, list(p)).fetchall()

    # 1. Value moved by the Ansem wallet to the deployer's side.
    out["sol_from_ansem_to_deployer_side"] = rows("SELECT src,dst,count(*),sum(lamports)::DOUBLE/1e9 FROM u WHERE kind='sol' AND src=? AND dst IN (SELECT a FROM ds) GROUP BY 1,2", GV)
    out["tokens_signed_by_ansem_to_deployer_side"] = rows("SELECT dst,mint,count(*),sum(raw)::DOUBLE FROM u WHERE kind='token_transfer' AND src=? AND src_signed AND dst IN (SELECT a FROM ds) GROUP BY 1,2", GV)
    out["tokens_not_signed_by_ansem_to_deployer_side"] = rows("SELECT dst,mint,count(*),sum(raw)::DOUBLE FROM u WHERE kind='token_transfer' AND src=? AND NOT src_signed AND dst IN (SELECT a FROM ds) GROUP BY 1,2", GV)

    # 2. Value moved by the deployer's side to the Ansem wallet.
    out["sol_from_deployer_side_to_ansem"] = rows("SELECT src,count(*),sum(lamports)::DOUBLE/1e9,min(ts),max(ts) FROM u WHERE kind='sol' AND dst=? AND src IN (SELECT a FROM ds) GROUP BY 1", GV)
    out["tokens_from_deployer_side_to_ansem"] = rows("SELECT src,count(DISTINCT mint),count(*),sum(raw)::DOUBLE/1e6,min(ts),max(ts) FROM u WHERE kind='token_transfer' AND dst=? AND src_signed AND src IN (SELECT a FROM ds) GROUP BY 1", GV)

    # 3. Counterparties in common over the dust limit, each with how many others use it: a shared service is not a link.
    con.execute("""CREATE TABLE cp AS
        SELECT wallet, CASE WHEN src=wallet THEN dst ELSE src END other, count(*) n, sum(lamports)::DOUBLE/1e9 sol, min(ts) first_ts
        FROM r WHERE kind='sol' AND lamports>=? GROUP BY 1,2""", [DUST])
    out["counterparties_shared_with_deployer_side"] = rows("""
        SELECT g.other, g.n, g.sol, d.wallet, d.n, d.sol,
               (SELECT count(DISTINCT wallet) FROM cp x WHERE x.other=g.other) walked_wallets_using_it
        FROM cp g JOIN cp d ON g.other=d.other
        WHERE g.wallet=? AND d.wallet IN (SELECT a FROM ds) AND g.other<>? AND g.other NOT IN (SELECT a FROM ds)
        ORDER BY g.sol+d.sol DESC LIMIT 60""", GV, GV)

    # 4. The wallets served by the Ansem wallet on 28 June: funders, and any tie to either side.
    con.execute("CREATE TABLE sw AS SELECT unnest(?::VARCHAR[]) a", [SIDE_WALLETS + EARLY])
    out["side_and_early_wallet_links"] = rows("""
        SELECT wallet, CASE WHEN src=wallet THEN 'out' ELSE 'in' END dir, CASE WHEN src=wallet THEN dst ELSE src END other,
               count(*), sum(lamports)::DOUBLE/1e9, min(ts)
        FROM r WHERE kind='sol' AND wallet IN (SELECT a FROM sw)
          AND (src IN (SELECT a FROM ds) OR dst IN (SELECT a FROM ds) OR src=? OR dst=?)
        GROUP BY 1,2,3 ORDER BY 1""", GV, GV)
    out["side_and_early_wallet_first_funder"] = rows("""
        SELECT wallet, arg_min(src, ts), min(ts), arg_min(lamports, ts)::DOUBLE/1e9
        FROM r WHERE kind='sol' AND dst=wallet AND lamports>=? AND wallet IN (SELECT a FROM sw) GROUP BY 1""", DUST)

    # 5. Sellers: did anything from the deployer's side touch ANSEM after it sold out, before the airdrop post?
    mint = "9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump"
    out["ansem_token_moves_on_deployer_side_after_exit"] = rows("""
        SELECT wallet, src, dst, raw::DOUBLE/1e6, ts, sig FROM r
        WHERE kind='token_transfer' AND mint=? AND wallet IN (SELECT a FROM ds) AND ts>1781644000 ORDER BY ts LIMIT 40""", mint)

    # 6. Ties inside the deployer's side, as a positive control: the same query must find these.
    out["positive_control_deployer_side_internal"] = rows("""
        SELECT src,dst,count(*),sum(lamports)::DOUBLE/1e9,min(ts),max(ts) FROM u
        WHERE kind='sol' AND src IN (SELECT a FROM ds) AND dst IN (SELECT a FROM ds) GROUP BY 1,2 ORDER BY 4 DESC""")
    assert out["positive_control_deployer_side_internal"], "the query finds no tie inside the side it should find them in"

    (OUT / "link_tests.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    for k, v in out.items():
        print(k, len(v) if isinstance(v, list) else v)
        if isinstance(v, list):
            for x in v[:25]:
                print("   ", [(utc(y) if isinstance(y, int) and y > 1_700_000_000 else (y[:10] if isinstance(y, str) else round(y, 3) if isinstance(y, float) else y)) for y in x], flush=True)
    return None


if __name__ == "__main__":
    sys.exit(main())
