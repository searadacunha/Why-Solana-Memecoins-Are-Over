"""Evidence ledger and timeline. Claims are written here by hand; check_ledger.py re-derives each from raw data.

Signatures are given as prefixes and expanded from walked rows, with exactly one match required, so no signature is ever
typed in full from memory. The raw transaction of every reference is saved to evidence/raw/key_txs.json.gz.
"""
from __future__ import annotations

import csv
import json

import duckdb

from ana_30_links import GV
from lib import CREATOR, DATA, MINT, OUT, client, save_gz, utc

Y = CREATOR
R9 = "9ryBR3SnxgGPhWsKvsfxuNHUCTt6tSpLe8wrKCShXLaq"
T278 = "278DWFskyaXcFy73rgtd4z1ao5PhLCQXKCWvSUqRGmsg"
SP = "FJ2Q9YPYucxPAHnjWzxM6JRJ6qmz5CUsv695dqx5mhhj"
FK = "FkCcgvCoR6p6BRucCnU1t1DXP97Y3rJeMYBiU1o31nuv"
FW = "FWmq7BX3"

# id, claim, rung or kind, on-chain checks, X posts as (id, text that must be in it)
L = [
 ("E01", "Ansem says he linked his X to a pump.fun account and links the wallet GV6UUmNx in his post. Self-claim of the wallet, 2026-06-16 20:59:26 UTC.", "R5 grade for ownership of this wallet only",
  [], [("2066989048497905753", "i just linked my X to a pumpfun account")]),
 ("E02", "The wallet has no transaction before the second of that post. Its first transactions are third parties naming it in their creator-fee settings, and it does not sign them.", "On-chain fact",
  [("evVqcN5GFnkvc4t2Fd", "time", 1781643566), ("evVqcN5GFnkvc4t2Fd", "not_signer", GV)], []),
 ("E03", "In the same thread he denies the wallet AVAZvHLR that Kolscan attributes to him, and says the other wallet is not his.", "His statement, not verifiable on chain",
  [], [("2066926449466966216", "ive asked kolscan to take my X account off"), ("2066991697842655572", "no")]),
 ("E04", "The deployer yHCxHBEa sends 20,000,000 of another token to GV6UUmNx 94 seconds after that post. GV6UUmNx does not sign.", "Direct transfer, one way",
  [("kWZYJ8v2SfEt8Z9W3U", "time", 1781643660), ("kWZYJ8v2SfEt8Z9W3U", "signer", Y), ("kWZYJ8v2SfEt8Z9W3U", "not_signer", GV), ("kWZYJ8v2SfEt8Z9W3U", "owner_token_any", [GV, 20_000_000_000_000])], []),
 ("E05", "A public post by @Donnieonchain says 'sending 60%', 4 min 7 s before the token exists. The largest gift is then 65 %. Who wrote it, and whether it relates to the deployer, is not established.", "Third-party post",
  [], [("2066989612200079857", "sending 60%")]),
 ("E06", "The token's metadata links a rewritten post by the same account, 69 seconds before creation.", "Metadata plus post",
  [], [("2066990360115683402", "not endorsing micro caps")]),
 ("E07", "Creation in one transaction, signed by the deployer and the mint key, slot 426930467: pays 84.740740739 SOL into the curve for 792,454,486.758954 tokens, total out 86.06810776 SOL. No Jito tip in the transaction.", "On-chain fact",
  [("4LteGjWEqA5RZ3EAgQ", "signer", Y), ("4LteGjWEqA5RZ3EAgQ", "signer", MINT), ("4LteGjWEqA5RZ3EAgQ", "slot", 426930467), ("4LteGjWEqA5RZ3EAgQ", "trade_sol", 84740740739), ("4LteGjWEqA5RZ3EAgQ", "owner_sol", [Y, -86068107760]), ("4LteGjWEqA5RZ3EAgQ", "owner_token", [Y, MINT, 792454486758954]), ("4LteGjWEqA5RZ3EAgQ", "no_jito_tip", None)], []),
 ("E08", "The launch tool's fee account receives exactly 0.3 % of an 85.8 SOL input, 0.2574 SOL. The metadata is hosted by the same tool, uxento.io.", "Commercial tool, R2 not met as written",
  [("4LteGjWEqA5RZ3EAgQ", "owner_sol", ["uxtoRPdPjRekYmxs1uUqVRZWh38iqonc9KgPuZXPeSY", 257400000])], []),
 ("E09", "One second after creation the deployer already tries to give 100 % of creator fees to GV6UUmNx. That transaction fails.", "On-chain fact",
  [("3UCYaGue2RyAj3W5", "failed", None), ("3UCYaGue2RyAj3W5", "fee_share", [GV, 10000]), ("3UCYaGue2RyAj3W5", "signer", Y)], []),
 ("E10", "650,000,000 tokens from the deployer to GV6UUmNx, 37 seconds after creation. GV6UUmNx does not sign.", "Direct transfer, one way",
  [("5SGKQKgDfKYRv8Xe", "time", 1781643985), ("5SGKQKgDfKYRv8Xe", "owner_token", [GV, MINT, 650000000000000]), ("5SGKQKgDfKYRv8Xe", "not_signer", GV)], []),
 ("E11", "The deployer sells its remaining 142,454,486.76 tokens in seven transactions over 9 seconds for 159.405670644 SOL. Net on trading: +73.34 SOL.", "On-chain fact",
  [("4WAEncCHFYKWSqjZ", "owner_sol", [Y, 55381300000, "approx"]), ("qZqNofWAHStR5szK", "owner_sol", [Y, 15397000000, "approx"])], []),
 ("E12", "The fee setting succeeds at 21:07:55, with GV6UUmNx at 10,000 basis points. In the same transaction the deployer collects 0.4857 SOL of accrued fees for itself.", "On-chain fact",
  [("4ac9uBpNZZfraa5h", "fee_share", [GV, 10000]), ("4ac9uBpNZZfraa5h", "owner_sol", [Y, 485700000, "approx"])], []),
 ("E13", "The deployer itself signs and pays the transactions that push ANSEM's creator fees to GV6UUmNx: 15.31 SOL at 21:11:00, 165.44 SOL on 22 June, without any signature from GV6UUmNx.", "On-chain fact",
  [("4QpDtDxTgr7vA7Av", "owner_sol", [GV, 15308600000, "approx"]), ("4QpDtDxTgr7vA7Av", "not_signer", GV), ("SYRD8132rLvgbCiX", "owner_sol", [GV, 165444300000, "approx"]), ("SYRD8132rLvgbCiX", "signer", Y)], []),
 ("E14", "9ryBR3Sn is a bot that reacts in the same slot, 1,104 positions later: it buys the last 645,513 tokens, then triggers the migration and buys 30,077,097 tokens on the new pool. Cost 16.09 SOL, including 1.18 SOL of priority fees.", "On-chain fact",
  [("UGfH7ngiC1bq14Lw", "index", 1383), ("UGfH7ngiC1bq14Lw", "owner_sol", [R9, -862313674]), ("Q8uA1zn27PzG7zhe", "index", 1384), ("Q8uA1zn27PzG7zhe", "owner_sol", [R9, -15231725613]), ("Q8uA1zn27PzG7zhe", "owner_token", [R9, MINT, 30077097302155])], []),
 ("E15", "The first transaction GV6UUmNx ever signs is on 23 June, a purchase of another token. It first moves ANSEM on 28 June.", "On-chain fact",
  [("4riXtXs72gSry6", "signer", GV), ("4riXtXs72gSry6", "time", 1782180517), ("5cn8EKLLtE1VZR", "signer", GV), ("5cn8EKLLtE1VZR", "owner_token", [GV, MINT, -10000000000000])], []),
 ("E16", "His post on airdropping the fees directed to his profile, 14:03:08 UTC on 27 June, reposted at 14:06:38. It quotes a suggestion from another account and names no token.", "His post",
  [], [("2070870549492883555", "airdrop portions of the creator fees"), ("2070871430191800832", "airdrop portions of the creator fees"), ("2070607672785744258", "Ansem should launch his own token")]),
 ("E17", "The first buy of 5 SOL or more after that post comes 23 seconds later: 11.0 SOL at 14:03:31.", "On-chain fact",
  [("3Rkq9qDdW98RS1fK", "time", 1782569011)], []),
 ("E18", "He describes it as a community takeover, says not to send coins to his wallet, and reports about $7M airdropped.", "His posts",
  [], [("2075325346547650772", "I CTOd the $ANSEM token"), ("2071204680248545493", "dont send it to my wallet"), ("2071573866875429166", "have airdropped about ~$7M"), ("2072375992555831586", "instead of sending me the supply")]),
 ("E19", "The deployer had launched a first token named The Black Bull, symbol ANSEM, the same day at 15:45:50, 5 h 20 min before. All of it, 400 M tokens, and 100 % of its fees went to a different wallet, Dt4gYgAU.", "On-chain fact",
  [("4VuY1xLQrLH3okjt", "time", 1781624750), ("4VuY1xLQrLH3okjt", "signer", Y)], []),
 ("E20", "Three examples of later launches: about 86 SOL bought and 650 M or more tokens to GV6UUmNx. Counts in evidence/followups.json.", "On-chain fact",
  [("GIFT:dUaSdZm38C", "owner_token_gift", GV), ("GIFT:9j4sMShA1U", "owner_token_gift", GV), ("GIFT:8RF5i3GuHp", "owner_token_gift", GV)], []),
 ("E21", "A token transfer out of GV6UUmNx is not proof that he sent it. This one, to the deployer, is signed by a third wallet that holds a permanent delegate on the mint.", "On-chain fact, trap",
  [("kSURJqBpNNCYUb6r", "signer", SP), ("kSURJqBpNNCYUb6r", "not_signer", GV), ("kSURJqBpNNCYUb6r", "owner_token", [GV, T278, -10000000000000])], []),
 ("E22", "The deployer and FkCcgvCo exchange SOL in both directions from the deployer's first hours.", "R3 same financial network",
  [("3dsLwZLx7qLirU", "owner_sol_gain", Y), ("3XYYUhF2jVQh7C", "owner_sol_gain", FK)], []),
 ("E23", "6,532.87 of the 21,022.09 SOL sent by GV6UUmNx goes through three short-lived wallets into high-volume wallets. None of the three receives from the deployer's side.", "On-chain fact",
  [("4kKiZFGC3wvf", "owner_sol", ["H3t5AYjF4ukuZ1HL2WCQqtSucRWWSZSoaiwYoWeshKPJ", 3000000000000, "approx"]), ("4kKiZFGC3wvf", "signer", GV)], []),
 ("E24", "490 M ANSEM move from GV6UUmNx to a new wallet on 1 August, which a high-volume wallet funded about an hour earlier. Signed by GV6UUmNx.", "On-chain fact",
  [("4mKqcX4taUZs", "signer", GV), ("4mKqcX4taUZs", "owner_token", [GV, MINT, -490000000000000])], []),
 ("E25", "Third parties name the deployer: Lookonchain on the 650 M transfer; others call yHCxHBEa the dev wallet of @Supermanonchain's token. These are claims, not proof.", "Third-party claims",
  [("2DrzWKeXYHwu4qPQ", "signer", Y)], [("2071422705262543187", "yHCxHB"), ("2072432739257549257", "dev wallet"), ("2072603129212711417", "Dev wallet")]),
 ("E26", "An X search for his replies naming the five most cited accounts returns one post, to @Supermanonchain: when you stop vamping good projects. The post it answers cannot be read.", "His post",
  [], [("2077780523175280888", "stop vamping good projects")]),
 ("E27", "Before this launch, another account publicly proposed coining him and sending supply and fees to AVAZvHLR. The idea is public and older than GV6UUmNx.", "Third-party post",
  [], [("2053638871305351384", "send him supply and fees")]),
 ("E28", "Bubblemaps' public count of the airdrop.", "Third-party post",
  [], [("2071608832728686966", "airdropped $6.7M")]),
 ("E29", "In the posts saved here, he first names $ANSEM on 28 June at 12:01:43.", "His post; search limits in evidence/x_searches.md",
  [], [("2071202382239686687", "$ANSEM")]),
 ("E30", "Ten wallets send the deployer 79.23 SOL in one second at 21:01:38, 3 seconds before the '60%' post. Nine are outside the family table, one later gives a large gift to the Ansem wallet. Such bursts are routine for this wallet: 127 seconds in its history have five or more inflows.", "Direct edges, rung not assessed",
  [("2vLBjnKQVDE4EtfGe4AH", "owner_sol_gain", Y), ("2vLBjnKQVDE4EtfGe4AH", "time", 1781643698), ("25A4WR8gjAXTxMYn5Dcd", "owner_sol_gain", Y), ("25A4WR8gjAXTxMYn5Dcd", "time", 1781643698)], []),
 ("E31", "8wvqvPt1 signs a push of 930.135 SOL of fees to GV6UUmNx, without its signature, for a different token called The Black Bull. In a sample of 231 pushes, 200 go to GV6UUmNx and 31 to one other wallet.", "On-chain fact, owner unknown",
  [("66AJCDGDwyJmniaL", "signer", "8wvqvPt1DDdjdghpMpp7ueQFUL5Js5zux4pPeRFXWteB"), ("66AJCDGDwyJmniaL", "not_signer", GV), ("66AJCDGDwyJmniaL", "owner_sol", [GV, 930135000000, "approx"])], []),
 ("E32", "A small wallet receives exactly 1.0 SOL from the deployer on 1 July and 1.0 SOL signed by GV6UUmNx on 2 July.", "On-chain fact, meaning unknown",
  [("2HuRxiKPvVbm", "signer", Y), ("2ZUDY5j8nLqN", "signer", GV), ("2ZUDY5j8nLqN", "owner_sol_gain", "49SecDmFPyFKphUKckC8oWDxKQWp5NN4QD8Wg6CT6Gy3")], []),
 ("E33", "A wallet sells 5.99 M tokens for 15.27 SOL at 13:58:53, one second and three slots before the one-slot group of 15 buyers.", "On-chain fact",
  [("5sXPigJesUYPcEXhcSAUTA", "time", 1782568733), ("5sXPigJesUYPcEXhcSAUTA", "owner_sol", ["8dut5xTs5V7EG9ccek11xDG5eBHkfYc3NdqcxjtWNsbS", 15273505972])], []),
]

# Timeline: UTC time, kind, text, reference. On-chain times are read from raw data by check_ledger.py where a ledger line covers them.
T = [
 ("2026-05-11 00:50:36", "X", "@Bobbythedevorr proposes a coin about Ansem with supply and fees sent to AVAZvHLR", "x:2053638871305351384"),
 ("2026-05-11 00:51:41", "chain", "The deployer launches a token named Ansem, 'The Meme Lord', 9 s after the post it cites", "TOKENS.csv"),
 ("2026-06-16 15:36:21", "X", "Ansem: that's not my wallet lads", "x:2066907740299985396"),
 ("2026-06-16 15:45:50", "chain", "First 'The Black Bull' by the deployer. 400 M tokens and 100 % of fees to Dt4gYgAU", "E19"),
 ("2026-06-16 16:50:41", "X", "Ansem: asked Kolscan to remove his X account from that wallet", "x:2066926449466966216"),
 ("2026-06-16 19:11:33", "X", "@whatadevoor: coins give fees to people who aren't him, confirm or give a newer wallet", "x:2066961899137409484"),
 ("2026-06-16 20:59:26", "X", "Ansem links GV6UUmNx: not endorsing any microcaps, just proving he can connect", "E01"),
 ("2026-06-16 20:59:26", "chain", "First transaction ever citing GV6UUmNx, by a third party setting fee shares", "E02"),
 ("2026-06-16 21:01:00", "chain", "Deployer sends GV6UUmNx 20 M of another token", "E04"),
 ("2026-06-16 21:01:38", "chain", "Ten wallets send the deployer 79.23 SOL in one second", "E30"),
 ("2026-06-16 21:01:41", "X", "@Donnieonchain: not endorsing micro caps, sending 60% so its not a micro cap", "E05"),
 ("2026-06-16 21:02:21", "chain", "Another deployer, 7ZV54Hcw, sends GV6UUmNx 300 M of its own token", "TOKENS_SENT_TO_ANSEM_WALLET.csv"),
 ("2026-06-16 21:04:39", "X", "@Donnieonchain rewrites it. This post is in the token's metadata", "E06"),
 ("2026-06-16 21:05:48", "chain", "ANSEM created. Deployer pays 86.07 SOL, gets 792.45 M tokens. 9ryBR3Sn buys the last tokens and migrates in the same slot", "E07,E14"),
 ("2026-06-16 21:05:49", "chain", "Deployer tries to set 100 % of fees to GV6UUmNx, transaction fails", "E09"),
 ("2026-06-16 21:06:25", "chain", "650 M ANSEM to GV6UUmNx", "E10"),
 ("2026-06-16 21:06:38", "chain", "Deployer has sold the rest: +73.34 SOL net", "E11"),
 ("2026-06-16 21:07:55", "chain", "Fee setting succeeds", "E12"),
 ("2026-06-16 21:09:58", "X", "Asked whether AVAZvHLR is his, Ansem answers no", "x:2066991697842655572"),
 ("2026-06-16 21:11:00", "chain", "Deployer pushes the first 15.31 SOL of fees to GV6UUmNx", "E13"),
 ("2026-06-23 02:08:37", "chain", "GV6UUmNx signs for the first time, buying another token", "E15"),
 ("2026-06-26 20:38:33", "X", "@Clive_99 suggests Ansem launch a token and airdrop the fees", "x:2070607672785744258"),
 ("2026-06-27 13:50:36", "X", "Ansem: hit 1M followers", "x:2070867396605182031"),
 ("2026-06-27 13:53:49", "X", "@_BabyMargiela tags him with $ANSEM in a reply", "x:2070868206441406828"),
 ("2026-06-27 13:57:40", "X", "Ansem replies 'lets ride' to @OnlyLJC ('Delusional bulls always win'). No token named", "x:2070869174889451774"),
 ("2026-06-27 13:58:53", "chain", "A wallet sells 5.99 M tokens for 15.27 SOL", "E33"),
 ("2026-06-27 13:58:54", "chain", "15 wallets buy in one slot, 5.66 SOL. Three slots since 25 June had more buyers", "evidence/numbers.json"),
 ("2026-06-27 14:03:08", "X", "Ansem: will airdrop portions of the creator fees directed to his profile. Names no token", "E16"),
 ("2026-06-27 14:03:31", "chain", "First buy of 5 SOL or more after the post: 11.0 SOL. 432 SOL of buying, by owner, by 14:06:38", "E17"),
 ("2026-06-27 14:09:04", "X", "Ansem: been sent like $200k in a week off the fee sharing", "x:2070872043147374602"),
 ("2026-06-28 02:07:53", "chain", "GV6UUmNx moves ANSEM for the first time: 10 M to 5URyNUmh", "E15"),
 ("2026-06-28 10:53:04", "chain", "Deployer launches 'The Herd', 650 M to GV6UUmNx", "E20"),
 ("2026-06-28 12:01:43", "X", "Ansem names $ANSEM, first time in the posts saved here", "E29"),
 ("2026-06-28 12:10:51", "X", "Ansem: dont send it to my wallet send it to all the $ANSEM holders", "E18"),
 ("2026-06-29 02:37:12", "X", "Lookonchain names yHCxHB as deployer", "E25"),
 ("2026-06-29 12:37:52", "X", "Ansem: have airdropped about ~$7M, goal 1M holders", "E18"),
 ("2026-06-29 14:56:49", "X", "Bubblemaps: $6.7M to 700+ wallets", "E28"),
 ("2026-07-01 17:45:14", "X", "Ansem: airdrop to all holders instead of sending me the supply", "E18"),
 ("2026-07-09 18:11:14", "chain", "Deployer launches another token, 700 M to GV6UUmNx", "E20"),
 ("2026-07-09 21:04:54", "X", "Ansem: I CTOd the $ANSEM token", "E18"),
 ("2026-07-16 15:40:54", "X", "Ansem to @Supermanonchain: when you stop vamping good projects", "E26"),
 ("2026-08-01 00:09:00", "chain", "490 M ANSEM from GV6UUmNx to a new wallet", "E24"),
]


def main() -> None:
    prefixes = {p for _, _, _, checks, _ in L for p, _, _ in checks if not p.startswith("GIFT:")}
    found: dict[str, set[str]] = {p: set() for p in prefixes}
    by12: dict[str, list[str]] = {}
    for p in prefixes:
        by12.setdefault(p[:12], []).append(p)

    def scan(path) -> None:
        with open(path) as f:
            for line in f:  # stream: these files are hundreds of MB together
                i = line.find('"sig": "')
                if i < 0:
                    continue
                sig = line[i + 8:line.index('"', i + 8)]
                for p in by12.get(sig[:12], ()):
                    if sig.startswith(p):
                        found[p].add(sig)

    for path in sorted((DATA / "rows").glob("*.jsonl")) + sorted((DATA / "mint").glob("*.jsonl")):
        scan(path)
    # Transactions that moved nothing for the wallet (a failure, a mention) leave no row: read the walk checkpoints too.
    for path in sorted((DATA / "checkpoints" / "gtfa").glob("*.jsonl")):
        with open(path) as f:
            for line in f:
                for row in json.loads(line)["sigs"]:
                    for p in by12.get(row["signature"][:12], ()):
                        if row["signature"].startswith(p):
                            found[p].add(row["signature"])
    with open(OUT / "creation_slot.json") as f:
        cs = json.load(f)
    for r in cs["rows"]:
        for p in by12.get(r["signature"][:12], ()):
            if r["signature"].startswith(p):
                found[p].add(r["signature"])

    def full(prefix: str) -> str:
        if len(found[prefix]) != 1:
            raise SystemExit("prefix %s matches %d signatures" % (prefix, len(found[prefix])))
        return next(iter(found[prefix]))

    gifts = {}
    for m in ("dUaSdZm38C", "9j4sMShA1U", "8RF5i3GuHp"):
        con = duckdb.connect(config={"memory_limit": "600MB"})
        r = con.execute(f"""SELECT sig, mint, raw FROM read_json('{DATA}/rows/{GV}.jsonl', maximum_object_size=8000000, sample_size=20000,
            columns={{kind:'VARCHAR',sig:'VARCHAR',src:'VARCHAR',dst:'VARCHAR',mint:'VARCHAR',raw:'HUGEINT'}})
            WHERE kind='token_transfer' AND dst='{GV}' AND src='{Y}' AND mint LIKE '{m}%' ORDER BY raw DESC LIMIT 1""").fetchone()
        if not r:
            raise SystemExit("no gift row for " + m)
        gifts[m] = (r[0], r[1], int(r[2]))

    c = client(run_limit=120)
    raw = {}
    ledger = []
    for eid, claim, kind, checks, posts in L:
        out = []
        for pre, what, arg in checks:
            if pre.startswith("GIFT:"):
                sig, mint, amount = gifts[pre[5:]]
                out.append({"sig": sig, "check": "owner_token", "arg": [arg, mint, amount]})
                raw[sig] = c.tx(sig)
                continue
            sig = full(pre)
            raw[sig] = c.tx(sig)
            out.append({"sig": sig, "check": what, "arg": arg})
        ledger.append({"id": eid, "claim": claim, "kind": kind, "checks": out, "posts": [{"id": i, "contains": t} for i, t in posts]})
    save_gz("raw/key_txs.json.gz", raw)
    (OUT / "ledger.json").write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n")
    with open(OUT.parent / "EVIDENCE_LEDGER.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "claim", "kind_or_rung", "signatures", "x_posts"])
        for e in ledger:
            w.writerow([e["id"], e["claim"], e["kind"], " ".join(sorted({x["sig"] for x in e["checks"]})),
                        " ".join("https://x.com/i/status/" + p["id"] for p in e["posts"])])
    with open(OUT.parent / "TIMELINE.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["utc", "kind", "event", "reference"])
        w.writerows(sorted(T))
    lines = ["# Timeline: X and chain together", "", "All times UTC. Times of X posts come from the post ID and agree with the endpoint. `E` references are lines of [EVIDENCE_LEDGER.csv](EVIDENCE_LEDGER.csv). A post is evidence of what the account wrote, not of whether it is true.", "", "| UTC | Source | Event | Reference |", "|---|---|---|---|"]
    for u_, kind, event, ref in sorted(T):
        link = "[post](https://x.com/i/status/%s)" % ref[2:] if ref.startswith("x:") else "`%s`" % ref
        lines.append("| %s | %s | %s | %s |" % (u_, kind, event.replace("|", "/"), link))
    (OUT.parent / "TIMELINE.md").write_text("\n".join(lines) + "\n")
    print("ledger", len(ledger), "txs", len(raw), "timeline", len(T), "credits", c.budget.used(), "last", utc(max(t["blockTime"] for t in raw.values())))
    assert MINT and FW


if __name__ == "__main__":
    main()
