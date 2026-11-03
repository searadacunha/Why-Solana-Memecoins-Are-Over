"""TOKENS.csv: every launch signed by the deployer's family, joined to fee shares, names, cited posts and local corpora.

Rows only, no network, DuckDB under a limit. Degree of proof is decided here by one rule and written per row.
"""
from __future__ import annotations

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

import duckdb

from ana_30_links import DEPLOYER_SIDE, GV
from lib import CREATOR, DATA, OUT, sol, utc

REPO = Path(__file__).resolve().parents[3]


def corpora() -> set[str]:
    s = set()
    with gzip.open(REPO / "data" / "floor_capture_public.jsonl.gz", "rt") as f:
        s |= {json.loads(x)["mint"] for x in f}
    s |= {e["mint"] for e in json.load(open(REPO / "data" / "v05_creation_block.json"))["lancements"]}
    s |= set(json.load(open(Path.home() / "Documents/Crypto/ansem_enquete/data/snipers90.json")))
    return s


def main() -> None:
    con = duckdb.connect(config={"memory_limit": "1200MB", "threads": 2})
    src = str(DATA / "rows" / "*.jsonl")
    con.execute(f"""CREATE TABLE r AS SELECT DISTINCT wallet, kind, sig, ts, src, dst, mint, raw, creator, sol, to_json(mints) mints,
        list_contains(signers, src) ss FROM read_json('{src}', union_by_name=true, maximum_object_size=8000000, sample_size=20000,
        columns={{wallet:'VARCHAR',kind:'VARCHAR',sig:'VARCHAR',ts:'BIGINT',src:'VARCHAR',dst:'VARCHAR',mint:'VARCHAR',raw:'HUGEINT',
        creator:'VARCHAR',sol:'HUGEINT',mints:'JSON',signers:'VARCHAR[]'}}) WHERE kind IN ('create','token_transfer','trade')""")
    con.execute("CREATE TABLE ds AS SELECT unnest(?::VARCHAR[]) a", [DEPLOYER_SIDE])
    launches = con.execute("SELECT mint, min(ts), any_value(sig), any_value(creator) FROM r WHERE kind='create' AND creator=wallet AND wallet IN (SELECT a FROM ds) GROUP BY 1").fetchall()
    per = {m: {"created": t, "sig": s, "creator": c, "buy": 0, "sold": 0, "buy_tok": 0, "sold_tok": 0} for m, t, s, c in launches}
    for wallet, sigv, sol_, mints in con.execute("SELECT wallet, sig, sol, mints FROM r WHERE kind='trade' AND wallet IN (SELECT a FROM ds)").fetchall():
        for m, dt in json.loads(mints).items():
            e = per.get(m)
            if not e or wallet != e["creator"]:
                continue
            if dt > 0 and sol_ < 0:
                e["buy"] -= sol_
                e["buy_tok"] += dt
            elif dt < 0 and sol_ > 0:
                e["sold"] += sol_
                e["sold_tok"] -= dt
    gifts = defaultdict(lambda: defaultdict(int))
    sells = {x[0] for x in con.execute("SELECT DISTINCT sig FROM r WHERE kind='trade' AND sol>0 AND wallet IN (SELECT a FROM ds)").fetchall()}
    for m, s, d, a, sg in con.execute("SELECT DISTINCT mint, src, dst, raw, sig FROM r WHERE kind='token_transfer' AND ss AND src IN (SELECT a FROM ds) AND dst IS NOT NULL AND dst<>src").fetchall():
        if m in per and sg not in sells and s == per[m]["creator"]:
            gifts[m][d] += a
    fee = {r["mint"]: r["fee_shares"] for r in csv.DictReader(open(OUT / "deployer_tokens.csv"))}
    names = {json.loads(x)["mint"]: json.loads(x) for x in open(OUT / "token_names.jsonl")}
    meta = {json.loads(x)["mint"]: json.loads(x) for x in open(OUT / "token_metadata.jsonl")}
    corp = corpora()
    with open(ROOT_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mint", "symbol", "name", "creator_wallet", "created_utc", "create_signature", "dev_buy_sol", "dev_buy_tokens", "sold_sol_by_creator", "net_sol_creator_only",
                    "tokens_gifted", "gift_recipients", "gift_to_ansem_wallet", "fee_share_to_ansem_wallet", "fee_shares_read", "cited_post", "in_repo_corpus", "degree_of_proof"])
        for m, e in sorted(per.items(), key=lambda x: x[1]["created"]):
            g = gifts.get(m, {})
            n, md = names.get(m, {}), meta.get(m, {})
            sh = fee.get(m)
            proof = "R3 same financial network: created by a wallet of the deployer family" if e["creator"] != CREATOR else "Same signing wallet as ANSEM"
            w.writerow([m, n.get("symbol"), n.get("name"), e["creator"], utc(e["created"]), e["sig"], sol(e["buy"]), e["buy_tok"] / 1e6, sol(e["sold"]), sol(e["sold"] - e["buy"]),
                        sum(g.values()) / 1e6, len(g), g.get(GV, 0) / 1e6, "yes" if sh and GV in sh else ("no" if sh is not None else "not read"), "yes" if sh is not None else "no",
                        md.get("twitter") or "", "yes" if m in corp else "no", proof])
    print("launches", len(per), "by creator", {c: sum(1 for e in per.values() if e["creator"] == c) for c in {e["creator"] for e in per.values()}})
    print("in repo corpus", sum(m in corp for m in per), "with names", sum(m in names for m in per), "with gift to Ansem", sum(GV in gifts.get(m, {}) for m in per))


ROOT_OUT = OUT.parent / "TOKENS.csv"
if __name__ == "__main__":
    main()
