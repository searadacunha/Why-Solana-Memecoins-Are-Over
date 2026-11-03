"""Recounts asked by the audit of the conclusions, from walked rows. No network. Writes evidence/followups.json.

Each section answers one correction: which comparison senders are tied to the family, what funded the ANSEM buy,
addresses shared at the plan's dust limit, real buys and sales of the Ansem wallet, gifts by recipient, what the fee pushes paid.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict

import duckdb

from ana_30_links import DEPLOYER_SIDE, GV
from lib import CREATOR, DATA, MINT, OUT, utc

VAULT = "AdPnUcnMJY4JExDWXb2Zd3QD76VYP1c6KHszwVZqjUfv"
A_SET = [GV, "H3t5AYjF4ukuZ1HL2WCQqtSucRWWSZSoaiwYoWeshKPJ", "EvktFyjtaToEGWnKVSJnwJacDvFBddzrxtUmiN795k8D",
         "2YPypQAQkFFtmwNgEcmnyqe2EJTThzoMTeUuMYmYcPiT", "BrV2WXWw5wU9pca4Nu4FJLhLU5cAbrkmLfXQmYm3ZZJG", "7oU9nR9VEvFPwvp2PpXo2LQc6A92QRhcUTwhLWT7MsDM"]
CREATION_TS = 1781643948


def main() -> None:
    con = duckdb.connect(config={"memory_limit": "1200MB", "threads": 2})
    src = str(DATA / "rows" / "*.jsonl")
    con.execute(f"""CREATE TABLE r AS SELECT DISTINCT kind, sig, ts, src, dst, lamports, mint, raw, sol, fee_payer, wallet, to_json(mints) mints, list_contains(signers, src) ss
        FROM read_json('{src}', union_by_name=true, maximum_object_size=8000000, sample_size=20000,
        columns={{wallet:'VARCHAR',kind:'VARCHAR',sig:'VARCHAR',ts:'BIGINT',src:'VARCHAR',dst:'VARCHAR',lamports:'HUGEINT',mint:'VARCHAR',raw:'HUGEINT',sol:'HUGEINT',fee_payer:'VARCHAR',mints:'JSON',signers:'VARCHAR[]'}})
        WHERE kind IN ('sol','token_transfer','trade')""")
    con.execute("CREATE TABLE s AS SELECT DISTINCT sig, src, dst, ts, lamports FROM r WHERE kind='sol'")
    con.execute("CREATE TABLE t AS SELECT DISTINCT sig, src, dst, ts, mint, raw, ss FROM r WHERE kind='token_transfer'")
    con.execute("CREATE TABLE ds AS SELECT unnest(?::VARCHAR[]) a", [DEPLOYER_SIDE])
    con.execute("CREATE TABLE ag AS SELECT unnest(?::VARCHAR[]) a", [A_SET])

    def q(sql, *p):
        return con.execute(sql, list(p)).fetchall()

    out: dict = {}
    # 1. comparison senders with SOL ties to the family
    senders = {r["sender"] for r in csv.DictReader(open(OUT.parent / "TOKENS_SENT_TO_ANSEM_WALLET.csv")) if r["sender"] != CREATOR}
    con.execute("CREATE TABLE sn AS SELECT unnest(?::VARCHAR[]) a", [sorted(senders)])
    tied = q("""SELECT CASE WHEN src IN (SELECT a FROM sn) THEN src ELSE dst END w, count(*), sum(lamports)::DOUBLE/1e9, min(ts), max(ts), min(sig)
        FROM s WHERE lamports>=10000000 AND ((src IN (SELECT a FROM sn) AND dst IN (SELECT a FROM ds)) OR (dst IN (SELECT a FROM sn) AND src IN (SELECT a FROM ds))) GROUP BY 1 ORDER BY 3 DESC""")
    out["comparison_senders"] = len(senders)
    out["comparison_senders_with_direct_sol_tie_to_family"] = [[a, n, round(v, 3), utc(t0), utc(t1), sg] for a, n, v, t0, t1, sg in tied]
    walked = {p.name[:-6].split("_")[0] for p in (DATA / "rows").glob("*.jsonl")}
    out["comparison_senders_walked"] = sorted(senders & walked)
    fw = q("""SELECT src, count(DISTINCT mint), sum(raw)::DOUBLE/1e6 FROM t WHERE dst=? AND ss AND src IN (SELECT a FROM sn)
              AND mint IN (SELECT DISTINCT mint FROM t WHERE src=? AND ss AND dst IN (SELECT a FROM sn)) GROUP BY 1 ORDER BY 2 DESC""", GV, CREATOR)
    out["comparison_senders_forwarding_mints_got_from_deployer"] = [[a, n, round(v)] for a, n, v in fw]
    pre = [r for r in csv.DictReader(open(OUT.parent / "TOKENS_SENT_TO_ANSEM_WALLET.csv")) if r["received_utc"] < "2026-06-27 14:03:08"]
    out["gifts_before_post"] = {"transfers": len(pre), "senders": len({r["sender"] for r in pre}), "not_by_deployer_transfers": sum(r["sender"] != CREATOR for r in pre),
                                "not_by_deployer_senders": len({r["sender"] for r in pre if r["sender"] != CREATOR})}

    tied_set = {x[0] for x in tied} | {x[0] for x in fw}
    out["comparison_senders_tied_to_family_floor"] = sorted(tied_set)
    path = OUT.parent / "TOKENS_SENT_TO_ANSEM_WALLET.csv"
    table = list(csv.DictReader(open(path)))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["received_utc", "sender", "mint", "tokens", "sender_is_deployer", "degree_of_proof"])
        w.writeheader()
        for r in table:
            r["degree_of_proof"] = "Same wallet as ANSEM" if r["sender"] == CREATOR else "Tied to the family by SOL or forwarded mints" if r["sender"] in tied_set else "Gift only: sender mostly unread, independence not tested"
            w.writerow(r)

    # 2. what paid for the ANSEM buy
    b = q("SELECT src, lamports::DOUBLE/1e9, ts, sig FROM s WHERE dst=? AND ts BETWEEN ? AND ? AND lamports>=10000000 ORDER BY ts", CREATOR, CREATION_TS - 900, CREATION_TS)
    out["sol_into_deployer_15_min_before_creation"] = [[a, round(v, 4), utc(t), sg] for a, v, t, sg in b]
    by_sec = Counter()
    for a, v, t, sg in q("SELECT src, lamports::DOUBLE/1e9, ts, sig FROM s WHERE dst=? AND lamports>=100000000", CREATOR):
        by_sec[t] += 1
    out["seconds_with_5_or_more_inflows_to_deployer"] = sum(c >= 5 for c in by_sec.values())
    sweep = q("SELECT src, lamports::DOUBLE/1e9, sig FROM s WHERE dst=? AND ts=1781643698 AND lamports>=10000000", CREATOR)
    out["sweep_21_01_38"] = {"wallets": len(sweep), "sol": round(sum(x[1] for x in sweep), 3), "from": [[a, round(v, 3), sg] for a, v, sg in sweep],
                             "outside_family": sum(a not in DEPLOYER_SIDE for a, _, _ in sweep)}
    fm = [x[0] for x in sweep]
    con.execute("CREATE TABLE sw AS SELECT unnest(?::VARCHAR[]) a", [fm])
    out["sweep_wallets_touching_ansem_side"] = q("SELECT src,dst,count(*),sum(lamports)::DOUBLE/1e9 FROM s WHERE (src IN (SELECT a FROM sw) AND dst IN (SELECT a FROM ag)) OR (dst IN (SELECT a FROM sw) AND src IN (SELECT a FROM ag)) GROUP BY 1,2")
    bb = q("SELECT count(*), sum(lamports)::DOUBLE/1e9 FROM s WHERE dst=? AND src='BbmS8ASj63NpNoZRAmNKdpqDcysbrtMi1TqYUGEAoM6H'", CREATOR)[0]
    out["BbmS8ASj_to_deployer"] = {"tx": bb[0], "sol": round(bb[1], 2)}

    # 3. addresses touching both sides at the plan's dust limit
    con.execute("""CREATE TABLE cp AS SELECT w, other, count(*) n, sum(lamports)::DOUBLE/1e9 v FROM
        (SELECT src w, dst other, lamports, sig FROM s WHERE lamports>=10000000 UNION ALL SELECT dst w, src other, lamports, sig FROM s WHERE lamports>=10000000) GROUP BY 1,2""")
    shared = q("""WITH x AS (SELECT other, sum(v) v, sum(n) n FROM cp WHERE w IN (SELECT a FROM ag) AND other NOT IN (SELECT a FROM ag) AND other NOT IN (SELECT a FROM ds) GROUP BY 1),
                       y AS (SELECT other, sum(v) v FROM cp WHERE w IN (SELECT a FROM ds) AND other NOT IN (SELECT a FROM ag) AND other NOT IN (SELECT a FROM ds) GROUP BY 1)
                  SELECT x.other, x.v, x.n, y.v FROM x JOIN y ON x.other=y.other ORDER BY 2 DESC""")
    out["addresses_shared_at_0_01_SOL"] = [[a, round(v, 3), round(d, 3)] for a, v, _, d in shared]

    # 4. real buys and sales of the Ansem wallet, by its SOL change: a fee payer filter drops transactions a relayer paid for
    buys, sells = [], []
    for sig, sol_, mints, payer in q("SELECT DISTINCT sig, sol, mints, fee_payer FROM r WHERE kind='trade' AND wallet=?", GV):
        for m, dt in json.loads(mints).items():
            if abs(sol_) < 50_000_000 and payer != GV:
                continue
            if dt > 0 and sol_ < 0:
                buys.append((m, -sol_ / 1e9, sig))
            elif dt < 0 and sol_ > 0:
                sells.append((m, sol_ / 1e9, sig))
    family = {x[0] for x in q("SELECT DISTINCT mint FROM read_csv(?, header=true, all_varchar=true)", str(OUT.parent / "TOKENS.csv"))}
    out["ansem_wallet_buys"] = {"n": len(buys), "mints": len({b[0] for b in buys}), "sol": round(sum(b[1] for b in buys), 2), "largest": sorted([[b[0], round(b[1], 2)] for b in buys], key=lambda x: -x[1])[:5],
                                "of_family_launches_over_dust": [[b[0], b[1]] for b in buys if b[0] in family and b[1] > 0.01]}
    out["ansem_wallet_sales"] = {"n": len(sells), "sol": round(sum(s_[1] for s_ in sells), 2), "of_ANSEM": sum(s_[0] == MINT for s_ in sells), "of_family_launches": sum(s_[0] in family for s_ in sells)}
    lp = q("SELECT count(DISTINCT sig), sum(sol)::DOUBLE/1e9 FROM (SELECT DISTINCT sig, sol, mints FROM r WHERE kind='trade' AND wallet='BrV2WXWw5wU9pca4Nu4FJLhLU5cAbrkmLfXQmYm3ZZJG') WHERE mints LIKE ?", f"%{MINT}%")[0]
    out["BrV2WXWw_rows_touching_ANSEM"] = {"tx": lp[0], "net_sol": round(lp[1] or 0, 2), "note": "liquidity provision is not classified, so this is not a sale figure"}
    out["ansem_out_signed_split"] = {"to_7oU9_M": q("SELECT sum(raw)::DOUBLE/1e12 FROM t WHERE src=? AND dst=? AND mint=? AND ss", GV, A_SET[5], MINT)[0][0],
                                     "total_M": q("SELECT sum(raw)::DOUBLE/1e12 FROM t WHERE src=? AND mint=? AND ss", GV, MINT)[0][0]}
    hop = q("SELECT sum(lamports)::DOUBLE/1e9 FROM s WHERE src=? AND dst IN (SELECT a FROM ag)", GV)[0][0]
    out["sol_out_to_ansem_side_hops"] = round(hop, 2)

    # 5. gifts by recipient, over all mints the deployer signed out, sells excluded
    sells_sig = {x[0] for x in q("SELECT DISTINCT sig FROM r WHERE kind='trade' AND wallet=? AND sol>0", CREATOR)}
    per = defaultdict(lambda: defaultdict(int))
    for m, d, a, sg in q("SELECT mint, dst, raw, sig FROM t WHERE src=? AND ss AND dst IS NOT NULL AND dst<>src", CREATOR):
        if sg not in sells_sig:
            per[m][d] += a
    for label, lim in (("650M", 650_000_000 * 10**6), ("100M", 100_000_000 * 10**6)):
        c = Counter(d for m, v in per.items() for d, a in v.items() if a >= lim)
        out["deployer_gifts_at_least_" + label] = {"gifts": sum(c.values()), "recipients": len(c), "top": c.most_common(5), "to_ansem_wallet": c[GV]}
    own = {r["mint"] for r in csv.DictReader(open(OUT.parent / "TOKENS.csv")) if r["creator_wallet"] == CREATOR}
    mints_gv = {m for m, v in per.items() if GV in v}
    out["mints_deployer_sent_to_ansem_wallet"] = {"all": len(mints_gv), "own_launches": len(mints_gv & own), "bought_and_forwarded": len(mints_gv - own),
                                                  "at_650M_after_ansem_own": sum(1 for m in own if per[m].get(GV, 0) >= 650_000_000 * 10**6 and m != MINT),
                                                  "at_650M_not_own": sorted(m for m in mints_gv - own if per[m][GV] >= 650_000_000 * 10**6)}
    rows = {r["mint"]: r for r in csv.DictReader(open(OUT / "deployer_tokens.csv"))}
    t_rows = {r["mint"]: r for r in csv.DictReader(open(OUT.parent / "TOKENS.csv"))}
    recipe = [m for m in own if per[m].get(GV, 0) >= 650_000_000 * 10**6 and m != MINT]
    full = [m for m in recipe if 80 <= float(t_rows[m]["dev_buy_sol"]) <= 95 and rows.get(m, {}).get("fee_shares") == GV + ":10000"]
    next_100 = Counter(o.split(":")[0] for r in rows.values() for o in r["fee_shares"].split(";") if o.endswith(":10000"))
    next_any = Counter(o.split(":")[0] for r in rows.values() for o in r["fee_shares"].split(";") if o)
    out["fee_share_recipients"] = {"at_100_pct_top": next_100.most_common(3), "any_share_top": next_any.most_common(3)}
    out["recipe_check"] = {"launches_at_650M_after_ansem": len(recipe), "with_about_86_sol_and_100pct_fee_share": len(full),
                           "fee_share_unread": sum(1 for m in recipe if m not in rows), "buy_over_95_sol": sum(float(t_rows[m]["dev_buy_sol"]) > 95 for m in recipe),
                           "fee_share_100pct_all_launches": sum(1 for r in rows.values() if r["fee_shares"] == GV + ":10000"), "fee_share_any_all_launches": sum(GV in r["fee_shares"] for r in rows.values())}

    # 6. fee pushes by vault
    cr = list(csv.DictReader(open(OUT / "deployer_cranks.csv")))
    mine = [r for r in cr if r["recipient"] == GV]
    v = defaultdict(lambda: [0, 0.0, ""])
    for r in mine:
        e = v[r["vault"]]
        e[0] += 1
        e[1] += float(r["sol"])
        e[2] = max(e[2], r["ts_utc"])
    out["deployer_pushes_to_ansem_wallet_by_vault"] = {a: [c, round(s_, 2), t_] for a, (c, s_, t_) in v.items()}
    fee = q("SELECT count(*), sum(lamports)::DOUBLE/1e9, min(ts), max(ts) FROM s WHERE src=? AND dst=?", VAULT, GV)[0]
    fee2 = q("SELECT count(*), sum(lamports)::DOUBLE/1e9 FROM s WHERE src=? AND dst=? AND ts<=1782685687", VAULT, GV)[0]
    out["ansem_vault_to_ansem_wallet"] = {"tx_all_time": fee[0], "sol_all_time": round(fee[1], 2), "first": utc(fee[2]), "last": utc(fee[3]), "tx_to_28_june": fee2[0], "sol_to_28_june": round(fee2[1], 2)}
    out["first_citing_wallet_in_deployer_rows"] = q("SELECT count(*) FROM s WHERE (src=? AND dst='F3aJ28RrFA') OR (dst=? AND src='F3aJ28RrFA')", CREATOR, CREATOR)[0][0]
    kinds = {}
    for line in open(OUT / "address_kinds.jsonl"):
        k = json.loads(line)
        kinds[k["address"]] = k
    with open(OUT / "shared_addresses.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["address", "sol_with_ansem_side", "sol_with_family", "owner_program", "balance_sol_when_read", "signatures_read", "seconds_for_last_1000", "class"])
        for a, v, _, d in shared:
            k = kinds.get(a, {})
            owner = k.get("owner")
            speed = k.get("seconds_for_last_1000")
            cls = "closed account" if k and not k.get("exists") else "program-owned" if owner and owner != "11111111111111111111111111111111" else \
                "high-volume wallet" if speed and speed < 86400 else "unclassified" if k else "not read"
            w.writerow([a, round(v, 3), round(d, 3), owner or "", round((k.get("lamports") or 0) / 1e9, 2), k.get("recent_sigs", ""), speed or "", cls])
    prev = json.loads((OUT / "followups.json").read_text()) if (OUT / "followups.json").exists() else {}
    for key in ("unsigned_mints_with_permanent_delegate", "coverage_probes", "8wvqvPt1_sample"):
        if key in prev:
            out[key] = prev[key]
    out["to_7uTT8Xi5"] = round(q("SELECT sum(lamports)::DOUBLE/1e9 FROM s WHERE src=? AND dst='7uTT8Xi5RWXzy7h9XL244GRgEycDYDhLjr3ZyNdXi8pZ'", GV)[0][0], 2)
    out["ansem_out_first_7_wallets_M"] = round(q("SELECT sum(raw)::DOUBLE/1e12 FROM t WHERE src=? AND mint=? AND ss AND ts<=1782613800 AND raw>=1000000000000", GV, MINT)[0][0], 2)
    (OUT / "followups.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("addresses_shared_at_0_01_SOL",)}, indent=0, default=str)[:7000])
    print("shared", len(out["addresses_shared_at_0_01_SOL"]))


if __name__ == "__main__":
    main()
