"""Every number the report states about the launch, the Ansem wallet and the control group. Written to evidence/numbers.json."""
from __future__ import annotations

import csv
import json
import re
import statistics as st
from collections import Counter, defaultdict

import duckdb

from ana_30_links import GV
from lib import CREATOR, DATA, MINT, OUT, SECOND_BUYER, sol, utc

POST_0 = 1782568988  # 14:03:08 UTC, first version of the airdrop post, ID 2070870549492883555
T0 = 1781643566      # 20:59:26 UTC, wallet post, ID 2066989048497905753
POOL = "FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC"


def mint_rows(*names):
    for n in names:
        with open(DATA / "mint" / (n + ".jsonl")) as f:
            yield from map(json.loads, f)


def main() -> None:
    out: dict = {}
    # the two creation-slot wallets on this mint, read over the first days of trading
    led = defaultdict(lambda: {"sol": 0, "tok": 0, "n": 0})
    for r in mint_rows("launch_to_takeoff"):
        for o in (CREATOR, SECOND_BUYER):
            if o in r["nets"]:
                led[o]["sol"] += r["nets"][o]["sol"]
                led[o]["tok"] += r["nets"][o]["tok"]
                led[o]["n"] += 1
    out["creation_wallets_on_ansem"] = {k: {"net_sol": sol(v["sol"]), "tokens_left_raw": v["tok"], "txs": v["n"]} for k, v in led.items()}

    # before and after the first airdrop post
    pre = []
    for r in mint_rows("pre_takeoff"):
        for o, n in r["nets"].items():
            if o != POOL:
                pre.append((r["ts"], o, n["tok"], n["sol"], r["slot"], r["sig"]))
    win = [x for x in pre if POST_0 - 900 <= x[0] <= POST_0]
    buyers = {x[1] for x in win if x[2] > 0}
    out["last_15_min_before_post"] = {"rows": len(win), "buyers": len(buyers), "net_sol_bought": sol(-sum(x[3] for x in win if x[2] > 0 and x[3] < 0)),
                                      "net_sol_received_by_sellers": sol(sum(x[3] for x in win if x[2] < 0 and x[3] > 0))}
    slot = [x for x in win if x[4] == 429250207]
    out["slot_429250207"] = {"rows": len(slot), "wallets": len({x[1] for x in slot}), "sol_in": sol(-sum(x[3] for x in slot if x[3] < 0)), "time": utc(slot[0][0]) if slot else None}
    post = []
    for r in mint_rows("takeoff"):
        for o, n in r["nets"].items():
            if o != POOL:
                post.append((r["ts"], o, n["tok"], n["sol"], r["sig"]))
    big = next(x for x in post if -x[3] >= 5e9 and x[2] > 0)
    out["first_buy_of_5_sol_after_post"] = {"time": utc(big[0]), "seconds_after_post": big[0] - POST_0, "wallet": big[1], "sol": sol(-big[3]), "sig": big[4]}
    b4 = [x for x in pre if x[0] < POST_0 and x[0] >= POST_0 - 3600 and -x[3] >= 5e9 and x[2] > 0]
    out["buys_of_5_sol_in_hour_before_post"] = len(b4)
    out["sol_in_first_218s_after_post"] = sol(-sum(x[3] for x in post if x[3] < 0 and x[2] > 0))

    groups = defaultdict(set)
    gsol = defaultdict(int)
    for r in mint_rows("pre_takeoff"):
        for o, n in r["nets"].items():
            if o != POOL and n["tok"] > 0 and n["sol"] < -1_000_000:
                groups[r["slot"]].add(o)
                gsol[r["slot"]] -= n["sol"]
    rank = sorted(groups, key=lambda s: -len(groups[s]))
    out["one_slot_buyer_groups_25_to_27_june"] = {"slots_with_a_buyer": len(groups), "slots_5_plus": sum(len(v) >= 5 for v in groups.values()), "slots_10_plus": sum(len(v) >= 10 for v in groups.values()),
                                                  "largest": [[s, len(groups[s]), sol(gsol[s])] for s in rank[:6]], "buyers_slot_429250207": len(groups[429250207]), "rank_slot_429250207": rank.index(429250207) + 1}

    con = duckdb.connect(config={"memory_limit": "1200MB", "threads": 2})
    src = str(DATA / "rows" / (GV + ".jsonl"))
    con.execute(f"""CREATE TABLE g AS SELECT DISTINCT kind, sig, ts, src, dst, lamports, mint, raw, list_contains(signers, src) ss FROM read_json('{src}',
        maximum_object_size=8000000, sample_size=20000, columns={{kind:'VARCHAR',sig:'VARCHAR',ts:'BIGINT',src:'VARCHAR',dst:'VARCHAR',lamports:'HUGEINT',mint:'VARCHAR',raw:'HUGEINT',signers:'VARCHAR[]'}}) WHERE kind IN ('sol','token_transfer')""")
    def q(s, *p):
        return con.execute(s, list(p)).fetchall()

    out["ansem_wallet"] = {
        "sol_in": q("SELECT count(*),count(DISTINCT src),sum(lamports)::DOUBLE/1e9 FROM g WHERE kind='sol' AND dst=?", GV)[0],
        "sol_out": q("SELECT count(*),count(DISTINCT dst),sum(lamports)::DOUBLE/1e9 FROM g WHERE kind='sol' AND src=?", GV)[0],
        "ansem_in_tokens": q("SELECT count(*),sum(raw)::DOUBLE/1e12 FROM g WHERE kind='token_transfer' AND dst=? AND mint=?", GV, MINT)[0],
        "ansem_out_signed": q("SELECT count(*),count(DISTINCT dst),sum(raw)::DOUBLE/1e12,min(ts),max(ts) FROM g WHERE kind='token_transfer' AND src=? AND mint=? AND ss", GV, MINT)[0],
        "token_out_not_signed": q("SELECT count(*),count(DISTINCT mint) FROM g WHERE kind='token_transfer' AND src=? AND NOT ss", GV)[0],
        "token_senders": q("SELECT count(DISTINCT src),count(DISTINCT mint),count(*) FROM g WHERE kind='token_transfer' AND dst=? AND src IS NOT NULL", GV)[0],
    }
    gifts = q("SELECT ts,src,mint,raw FROM g WHERE kind='token_transfer' AND dst=? AND ss AND raw>=100000000000000 ORDER BY ts", GV)
    out["control_gifts_100M"] = {"transfers": len(gifts), "senders": len({x[1] for x in gifts}), "mints": len({x[2] for x in gifts}),
                                 "first_24h_senders": len({x[1] for x in gifts if x[0] - T0 <= 86400}),
                                 "before_first_airdrop_post": len([x for x in gifts if x[0] < POST_0]),
                                 "before_post_senders": len({x[1] for x in gifts if x[0] < POST_0}),
                                 "by_deployer": len({x[2] for x in gifts if x[1] == CREATOR})}
    with open(OUT.parent / "TOKENS_SENT_TO_ANSEM_WALLET.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["received_utc", "sender", "mint", "tokens", "sender_is_deployer", "degree_of_proof"])
        for t, s, m, a in gifts:
            w.writerow([utc(t), s, m, a / 1e6, "yes" if s == CREATOR else "no", "same wallet as ANSEM" if s == CREATOR else "R1 same method only"])

    # the deployer
    rows = list(csv.DictReader(open(OUT.parent / "TOKENS.csv")))
    mine = [r for r in rows if r["creator_wallet"] == CREATOR]
    out["deployer"] = {"launches": len(mine), "first": min(r["created_utc"] for r in mine), "last": max(r["created_utc"] for r in mine),
                       "family_launches": len(rows), "sum_dev_buy_sol": round(sum(float(r["dev_buy_sol"]) for r in mine), 2),
                       "sum_net_sol_creator_only": round(sum(float(r["net_sol_creator_only"]) for r in mine), 2),
                       "with_gift_to_ansem": sum(float(r["gift_to_ansem_wallet"]) > 0 for r in mine),
                       "fee_share_to_ansem": sum(r["fee_share_to_ansem_wallet"] == "yes" for r in mine),
                       "fee_shares_read_for": sum(r["fee_shares_read"] == "yes" for r in mine),
                       "same_recipe_650M_plus_after_ansem": sum(float(r["gift_to_ansem_wallet"]) >= 6.5e8 and r["created_utc"] > "2026-06-16 21:06" for r in mine),
                       "in_repo_corpus": sum(r["in_repo_corpus"] == "yes" for r in mine)}
    gifted = sorted((r for r in mine if float(r["gift_to_ansem_wallet"]) > 0), key=lambda r: r["created_utc"])
    out["deployer"]["first_launch_gifted_to_ansem"] = gifted[0]["created_utc"] if gifted else None
    cr = list(csv.DictReader(open(OUT / "deployer_cranks.csv")))
    by = Counter()
    n = Counter()
    for r in cr:
        by[r["recipient"]] += float(r["sol"])
        n[r["recipient"]] += 1
    tot = sum(by.values())
    out["deployer_cranks"] = {"cranks": len(cr), "recipients": len(by), "sol": round(tot, 2), "to_ansem_wallet_sol": round(by[GV], 2), "to_ansem_wallet_cranks": n[GV],
                              "share_of_sol": round(by[GV] / tot, 4), "max_cranks_any_other": max(c for a, c in n.items() if a != GV), "last_to_ansem": max(r["ts_utc"] for r in cr if r["recipient"] == GV)}

    # cited posts
    md = [json.loads(x) for x in open(OUT / "token_metadata.jsonl")]
    created = {r["mint"]: r["created_utc"] for r in mine}
    import calendar, time
    d = []
    acc = Counter()
    for m in md:
        k = re.search(r"(?:x|twitter)\.com/([^/]+)/status/(\d{15,25})", m.get("twitter") or "")
        if k and m["mint"] in created:
            ct = calendar.timegm(time.strptime(created[m["mint"]], "%Y-%m-%d %H:%M:%S"))
            d.append(ct - ((int(k.group(2)) >> 22) + 1288834974657) // 1000)
            acc[k.group(1).lower()] += 1
    d.sort()
    out["cited_posts"] = {"metadata_read": sum(not m.get("error") for m in md), "metadata_failed": sum(bool(m.get("error")) for m in md), "launches_citing_a_post": len(d),
                          "median_delay_s": st.median(d), "p10": d[len(d) // 10], "p90": d[9 * len(d) // 10], "within_10_min": sum(0 <= x <= 600 for x in d), "before_post": sum(x < 0 for x in d),
                          "accounts": len(acc), "top_accounts": acc.most_common(12)}
    # kolscan snapshot
    kol = {e["wallet_address"]: (e.get("name"), e.get("twitter")) for e in json.load(open(DATA / "sources" / "kolscan_snapshot_nirholas_kol-quest.json"))}
    rec = list(csv.DictReader(open(OUT / "deployer_recipients.csv")))
    sub = [r for r in rec if float(r["tokens_gifted"]) >= 1e6 and int(r["n_launches_gifted"]) >= 2]
    feeonly = [r for r in rec if int(r["n_launches_fee_share"]) >= 1]
    traders = set()
    for r in mint_rows("launch_to_takeoff", "pre_takeoff"):
        traders.update(r["nets"])
    out["kol_enrichment_exploratory"] = {"snapshot_wallets": len(kol), "recipients_1M_tokens_2_launches": len(sub), "of_which_on_snapshot": sum(r["recipient"] in kol for r in sub),
                                         "fee_share_recipients": len(feeonly), "fee_share_on_snapshot": sum(r["recipient"] in kol for r in feeonly),
                                         "ansem_traders_before_post": len(traders), "ansem_traders_on_snapshot": len(traders & set(kol)),
                                         "kol_recipients": sorted([(r["recipient"], kol[r["recipient"]][0], int(r["n_launches_gifted"]), int(r["n_launches_fee_share"])) for r in sub + feeonly if r["recipient"] in kol], key=lambda x: -x[2] - x[3])[:30]}
    (OUT / "numbers.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps(out, indent=0, default=str)[:5200])


if __name__ == "__main__":
    main()
