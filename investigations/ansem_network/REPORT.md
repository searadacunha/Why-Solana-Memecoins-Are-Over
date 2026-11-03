# ANSEM: who organised what

Investigation of the token `9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump`, written 2026-11-03. The main on-chain and X claims have a line in [EVIDENCE_LEDGER.csv](EVIDENCE_LEDGER.csv), and `code/check_ledger.py` re-derives the checked ones from the raw transactions and posts saved in `evidence/`. Counts come from `evidence/numbers.json` and `evidence/followups.json`.

## The answer

**No on-chain or public evidence found here ties Ansem to organising this launch or a network of launches. This does not clear him: chain data cannot see a private agreement or a wallet nobody has tied to him, and some facts stay unexplained.**

What the data shows:

1. The token was made by a serial launch wallet, `yHCxHBEaJW5tbndqC8JciSThr7U1cqLpdcsvHcx6PRe`. It signed 839 launches from April to November 2026 and exchanges SOL with a group of wallets seen since January 2025.
2. That wallet gave the wallet Ansem had just published 65 % of the supply and all the creator fees, starting minutes after his post. These transfers need no signature from the receiver. His wallet signs nothing for more than six days.
3. The deployer went on sending his wallet tokens: 75 mints in all, 50 of them its own launches. 21 of those launches, after ANSEM, gave him 650 M tokens or more, most of them after he wrote "dont send it to my wallet". Other wallets also sent him large amounts, at least 6 of them tied to the deployer and most never read.
4. Across the full history of both wallets, no SOL moves directly between his wallet and the deployer's group, and no token transfer signed by his wallet reaches it.
5. The price run starts 23 seconds after a post of his about airdropping creator fees. That post names no token. He first names $ANSEM in the saved posts the next day, and on 9 July writes "I CTOd the $ANSEM token".

This is consistent with a deployer using his name and his wallet to launch tokens, and with him taking one up later. It is not proof of it. See "What still looks odd" and "Limits".

## Conclusions by rung

The ladder was fixed in [PLAN.md](PLAN.md) before any new data was read.

| Rung | As defined in the plan | Conclusion |
|---|---|---|
| R1 Same technical method | Same mechanics in the creation slot | **Not tested across launches.** The gifts to his wallet happen after launch, and the other senders' creation slots were not read |
| R2 Same infrastructure | A non-service address reused across launches | **Not met as written.** The launch pays 0.3 % to `uxtoRPdPjRekYmxs1uUqVRZWh38iqonc9KgPuZXPeSY` and its metadata is on uxento.io, but that is a commercial tool (E08) |
| R3 Same financial network | Direct non-service transfers between wallets of two launches, with signatures | **Met for the deployer's family:** nine wallets and 952 launches at least. **Not met between that family and the wallets tied to him** |
| R4 Probable same operator | R3, plus recycling in two launches, plus a rarity test rejecting chance | **Not met.** The rarity test does not reject chance for `yHCxHBEa` (p = 0.66). Fact outside the ladder: 839 launches carry one signing key |
| R5 Personal attribution | A wallet he claims, linked on chain to a launch wallet by R3 or better. A token received after launch does not count | **Not met for the launch.** `GV6UUmNxz2RpKxmNAPadYKb7uQpszwqQAu3qLJxVdC52` is his wallet by his own post (E01). The only links to it from the launch wallet are tokens and fees received |

## What happened

Times are UTC. The full list is in [TIMELINE.md](TIMELINE.md).

**Before.** On 11 May a public post proposes to "dev a coin about him and send him supply and fees", naming the wallet `AVAZvHLR2PcWpDf8BXY4rVxNHYRBytycHkcB5z5QNXYm`, which a public Kolscan snapshot attributes to him. The deployer launches tokens named Ansem that day. In May and June it also sends that wallet tokens from 10 mints, and fee shares on 7 launches.

**16 June.** At 15:36 he writes "that's not my wallet lads". At 15:45:50 the deployer launches a first token called The Black Bull, symbol ANSEM, and gives all 400 M tokens it bought and all its fees to another wallet, `Dt4gYgAUts6puim6yj4m874V5TuGUGFyZVv4RNpFvUkY`. Through the afternoon people press him: coins are sending fees to a wallet that is not his, "confirm or give a newer wallet".

At **20:59:26** he posts: "i just linked my X to a pumpfun account [...] im not endorsing any microcaps, just to prove that i can connect my X to an address on the app", with a link to `GV6UUmNx`. The wallet has no transaction before that second. Its first transaction, in that same second, is a third party, `F3aJ28Rr`, adding it to a fee setting. So someone's software could already see the wallet as the post went out. `F3aJ28Rr` has no SOL flow with the family in what was read, and it was not walked itself.

| Time | Event |
|---|---|
| 21:01:00 | Deployer sends `GV6UUmNx` 20 M of another token, right after serving 17 other wallets the same amount |
| 21:01:38 | Ten wallets send the deployer 79.23 SOL in one second. This funds the coming buy. Such bursts are routine for it |
| 21:01:41 | `@Donnieonchain`: "HE SAYS he is not endorsing micro caps sending 60% so its not a micro cap" |
| 21:04:39 | Same account rewrites the post. This version is linked in the token's metadata |
| 21:05:48 | Creation and buy in one transaction, slot 426930467 |
| 21:05:49 | Deployer tries to give 100 % of fees to `GV6UUmNx`. The transaction fails |
| 21:06:25 | 650,000,000 tokens to `GV6UUmNx` |
| 21:06:29 to 21:06:38 | Deployer sells the remaining 142.45 M for 159.41 SOL |
| 21:07:55 | Fee setting succeeds, after the deployer collects 0.4857 SOL for itself |
| 21:09:58 | Asked if `AVAZvHLR` is his, he answers "no" |
| 21:11:00 | Deployer signs and pays the first push of fees to `GV6UUmNx`: 15.31 SOL |

**The creation slot, rebuilt from the raw block** (1,551 transactions, 18 citing the mint, 5 successful, 13 failed; `evidence/creation_slot.json`):

- Position 279: the deployer, with the mint key. It pays 84.740740739 SOL into the curve, for 792,454,486.76 tokens. With fees, 86.06810776 SOL leave the wallet. The curve amount plus pump.fun's 1.25 % comes to 85.8 SOL. No Jito tip in the transaction.
- Position 1383: `9ryBR3SnxgGPhWsKvsfxuNHUCTt6tSpLe8wrKCShXLaq` buys the last 645,513 tokens for 0.2646 SOL.
- Position 1384: the same wallet triggers the migration and buys 30,077,097 tokens on the new pool. Its total cost is 16.09 SOL, of which 1.18 SOL is priority fees. It sells out, net +19.94 SOL.
- Seven other wallets try and fail 13 times.

The deployer's net on the token is +73.34 SOL on trading, plus 0.4857 SOL of fees. Later it receives only dust of this token.

**The eleven days.** `GV6UUmNx` signs nothing until 23 June, when it buys another token, and does not move ANSEM until 28 June. Meanwhile the deployer keeps pushing ANSEM's fees to it: 144.81 SOL on 19 June, 165.44 SOL on 22 June, 55.05 SOL on 25 June.

**27 June.** In the 15 minutes before his post, 27 wallets buy. The pool takes in 9.16 SOL from buyers and pays out 16.86 SOL to sellers. From 25 June up to the post it takes in 1,201.10 SOL and pays out 1,211.67 SOL (21 to 25 June not read). One buy reaches 5 SOL in the last hour.

- 13:50:36: "hit 1M followers".
- 13:57:40: replies "lets ride" to "Delusional bulls always win". No token named.
- 13:58:53: a holder of about 25 M tokens sells for 15.27 SOL.
- 13:58:54: three slots later, 15 wallets buy in one slot, 5.66 SOL. Three slots since 25 June had more buyers, and nine had ten or more. 13 of the 15 sell within 52 seconds after his post, for 8.01 SOL. The timing fits a reaction to that sale. What binds these wallets is open: the August note found they fire together on a neutral day, and that 12 of 15 funding chains end at `BY4StcU9`, the deployer's first funder, which is unclassified (see "Limits"). None has a direct SOL flow with `GV6UUmNx` or with the family wallets read, and one later receives 354 tokens from `GV6UUmNx`. I did not walk these wallets themselves.
- **14:03:08: "sure i will airdrop portions of the creator fees that have been directed to my pump fun profile"**, quoting a suggestion from `@Clive_99`. Names no token. Reposted at 14:06:38.
- **14:03:31: first buy of 5 SOL or more after that post, 11.0 SOL, 23 seconds later.** The pool price is flat until then. 432 SOL of buying, by owner, by 14:06:38.

**After.** `GV6UUmNx` first moves ANSEM on 28 June at 02:07:53, and he first names $ANSEM in the saved posts at 12:01:43. Transactions signed by that wallet move 567.05 M tokens: 491 M to a new wallet `7oU9nR9VEvFPwvp2PpXo2LQc6A92QRhcUTwhLWT7MsDM`, 49.89 M to 7 wallets in 21 minutes, and 26.16 M to 1,311 others. He reports about $7M airdropped on 29 June. On 9 July, "I CTOd the $ANSEM token". On 16 July, to `@Supermanonchain`: "when you stop vamping good projects".

## Tests of H1

**This table was written after seeing data, so it is exploratory.** It is not in the plan. The 15-minute window, the 5 SOL threshold and the 100 M comparison group were also chosen then.

`GV6UUmNx` is read in full, 122,407 transactions up to 3 November. So is the deployer, 242,603. So a direct flow between those two, or between `GV6UUmNx` and any family wallet, cannot be missed. These tests cover direct flows only. H1 also says "indirectly", and that part is limited to the hub test below.

| Test | Measured |
|---|---|
| SOL from the six wallets tied to him to the nine family wallets, or the reverse | **None**, at any size |
| Token transfers signed by `GV6UUmNx` to the family | **None** |
| History of his wallet before the launch | **None.** A signature query before its first transaction returns nothing (`evidence/genesis_check.json`) |
| His wallet's signature on the transfer, the fee setting or the fee pushes | **None** |
| Deployer serves only him | **No.** 176 gifts of 650 M or more went to 111 recipients: 25 to him, the next wallet 7. Fee shares went to 202 wallets. Some recipients are the family's own wallets |
| Deployer stops after he objects | **No.** 20 of the 21 launches come after "dont send it to my wallet" |
| Heavy buying ahead of his post | **Not seen.** Sellers took out more than buyers put in, over the 15 minutes and since 25 June |
| His wallet buys or sells family launches | **No,** beyond dust. 47 buys over 23 mints, 7,795.54 SOL. 9 sales, 3,216.54 SOL, none of ANSEM |
| Addresses used by both sides | **No private hub identified, with gaps.** 29 addresses at the plan's 0.01 SOL limit: 9 program-owned, 12 high-volume, 3 closed, 5 unclassified (`evidence/shared_addresses.csv`). Nearly all the SOL is in one high-volume service and four pools |
| The same exit wallets | **None seen.** Three short-lived wallets take 6,532.87 of his 21,022.09 SOL out, and none receives from the family side. Another 2,180 SOL goes directly to a high-volume wallet |
| The wallet he denies | `AVAZvHLR` has **no flow with `GV6UUmNx`**, and with the family only gifts received, 15 April to 31 July |

Two tests I removed as not separating the hypotheses: that the deployer sold out, and that it never re-entered. Under H1 its stake could be the 650 M sitting in his wallet.

**What the positive control shows.** The same queries find 27 SOL relationships inside the family, up to 19,306 SOL on one pair. That proves the method finds direct flows among wallets I read. It does not show the method would find an indirect path.

**Other senders.** 1,065 transfers of at least 100 M tokens reached his wallet, from 635 senders across 971 mints. 29 of them, from 22 senders other than the deployer, came before his 14:03:08 post. In the seven minutes after his wallet post, three other senders gave him 300 M, 150 M and 100 M of their tokens before this deployer sent its 650 M. **This is not an independent control.** At least 6 of the 634 other senders are tied to the deployer by SOL or by forwarding mints it launched: `23xmd6BXDNVc65ogLAf6j7EAx4R1Je5cEL8ju1dxtvKc`, `2SA6T5FAMdv4MZiE6283n7QkMMaBB3bG7rk2Lhgts1FB`, `7Ua7QXx8QZGUgHyj5xKiUT9ecrmHhoPQxVNXnDPDQexe`, `dropEpU7PJEUA3Mu5fgQchGRAYbb33hJGW3ejT68fuv`, `uGuTB2QsYQbJXSVBYCYmA2GtmjaAcw27q8UvWMdQ3pe`, `5hh7UE6i2BtyCvaMMadS71wFwK88JRmtRTfXkjZ3CHvF`. Only 5 senders were walked, and only in part. So this shows that gifts to his wallet were common. It does not show how many operators sent them.

## The deployer's family

Rung R3. No statement about who they are.

- `yHCxHBEa` is first funded on 20 April at 13:00:49 by `BY4StcU9Y2BpgH8quZzorg31EGE4L1rjomN8FNsCBEcx` (4.43 SOL, unclassified), then 96 seconds later by `FkCcgvCoR6p6BRucCnU1t1DXP97Y3rJeMYBiU1o31nuv` (9.13 SOL). Its first launch comes under five minutes after that.
- It sends 19,306 SOL to `FkCcgvCo` and receives 7,791 SOL back. Other main ties: `4qcD8iSFLC5VDZphBtM7pSeevtHtD8Chi7Zmhcm9TvHm`, `E94dd6pnFhE7LNbC7oSbyWmCCQ9kNoEhSa6cKN6brSAm`, `F5XqYtdUWUT7bbuuKEjckDs8Hwk7j7mhdwGe3YKn5Xf7`, `AvYukzeAFzFo66i1GJHShcdBbb4jeSkZiEJnNMds54mo`, `9bxyzm6MFn3TWEedvYuMzSaZkkGWKSyTgWpRXCzMP3dm`, `DxnxpqcUsErqRFRbfVrKr988F9AxayryC5eKWPKgvjmR`, `6xMLLrtZAh8ToWjeZ9Nm4RKtEC3uY2Qqscihz4yHp1jK`.
- **The nine are a floor.** Ten wallets funded it at 21:01:38, nine of them outside this list, and `23xmd6BX` is one of those nine. They are now closed, and none has a direct flow with his side. `BbmS8ASj63NpNoZRAmNKdpqDcysbrtMi1TqYUGEAoM6H` also sends it 4,991.72 SOL across 1,423 transactions, in the pattern of protocol fees. I did not classify it.
- `F5XqYtdU` is first funded through the ChangeNOW gateway, where tracing ends. `AQd3h5tkbdhTiWv7WmiCbm8uwjYi8vTBbMzEtAGtf1T5`, which receives 28,529 SOL from `F5XqYtdU` and sends it 14,885 SOL, held 13,537 SOL when read.
- Launches found: `yHCxHBEa` 839, `FkCcgvCo` 74, `F5XqYtdU` 16, `AvYukzeA` 11, `E94dd6pn` 9, three others one each. `FkCcgvCo`, `F5XqYtdU`, `AvYukzeA`, `9bxyzm6M` and `4qcD8iSF` are read only in part, so 952 is a floor.
- `yHCxHBEa` paid 27,227 SOL of dev buys and its signed sales net 18,227 SOL. That figure is low, because tokens moved to other wallets and sold there are not in it, as with $SUPERMAN (1,026 SOL bought, no sale signed by this wallet). I measured funding before one launch only, ANSEM, so "recycling" is not established launch by launch.

**The posts.** Of 761 launches with readable metadata, 541 link a specific X post, 508 distinct posts. The launch follows that post by a median of 31 seconds, 10th percentile 12 seconds, and never precedes it. 106 accounts are cited, led by `@Supermanonchain` (182 launches), `@NikolaiFrandsen` (135), `@RoaringKittyCat` (21), `@LastManOnchain` (19), `@zitobondoor` (18), `@Donnieonchain` (10) and `@blknoiz06` (9, with delays of 22 to 116 seconds, turning his own words into tokens).

Exploratory test: of 19 readable posts naming a share ("sending 5%"), forming 23 launch-post pairs from 8 accounts, 14 pairs match the largest gift in the launch within 3 points, against 1.09 expected when shuffled (p ≤ 0.0005, 2,000 draws, pairs treated as independent, which they are not). 9 pairs miss, 7 of them with no gift at all. ANSEM itself is "60 %" against a 65 % gift. None of the 19 posts is his. 414 of the 508 posts cannot be read through the public endpoint, and that includes every post of the three most cited accounts, so 338 launches are untested. `@Supermanonchain` showed as suspended on 3 November (`evidence/x_searches.md`).

So the launches follow these posts closely. That fits a shared operator, a launch tool fed by these accounts, or an independent fast reaction, and this data does not choose between them. Two third-party posts call `yHCxHBEa` the dev wallet of `@Supermanonchain`'s token, unverified. **None of this says who wrote the posts, and none of it touches Ansem.**

**Rarity test, as fixed in the plan, with deviations listed below.** 343 launches, 1,856 wallets, 10,000 curveball draws, Monte Carlo error at most ±0.005. A pair planted in 12 launches is detected (p ≈ 0.006) and shuffled data stays quiet (0 of 40). `yHCxHBEa` p = 0.66, on the 24 of its 839 launches in this corpus. `9ryBR3Sn` p = 0.999, `dshAybqF` p = 0.985: their partners are the bots found everywhere. `LfEcaUf7` is flagged (p ≤ 0.0001), with a redacted wallet that shares 68 of its 91 launches. `GV6UUmNx` and five other seeds are not in this corpus. This test looks at who buys in the same slot and cannot speak to fund flows. 60 wallets were tested, with no correction.

**Gift list, exploratory.** 25 of 888 wallets that received at least 1 M tokens in two or more launches (2.8 %), and 12 of 202 fee recipients (5.9 %), are in a public Kolscan snapshot of 472 wallets. Among 28,880 wallets trading ANSEM before his post, 26 are (0.09 %). The snapshot is third-party and undated. Other big recipients are unlabelled, and some are hot wallets. This fits a deployer that targets well-known wallets. It says nothing about whether those people agreed. The name-to-wallet pairs are not published here, because they are unverified.

## What still looks odd

- **The deployer treats his wallet more than any other, by every count.** 25 gifts of 650 M or more, next wallet 7. 32 launches with a 100 % fee share, next wallet 12. 20 of its 325 fee pushes, 640.16 of 868.96 SOL; no other recipient gets more than 2 pushes. 11 of the 20 come from ANSEM's vault, 513.61 SOL, the last on 27 June at 15:00:39, long after the deployer had sold. Why it did this is not measured.
- **Timing on launch day.** The deployer's funding burst comes 3 seconds before the "sending 60%" post. Bursts are routine for it, and I report this as a fact only.
- **`8wvqvPt1DDdjdghpMpp7ueQFUL5Js5zux4pPeRFXWteB`** pushes at least 5,131.56 SOL of fees to his wallet from 21:56 on 28 June, the day after he wrote that they need a way to claim in bulk. That count stops at 22:28, where the transaction bodies I kept end. In a sample of 231 pushes, 200 go to his wallet between 21:55 and 22:20, and 31 go to one other wallet from 23:40. So it is not exclusive to him, and I do not know who runs it. It has no SOL flow with his wallet. I read it only for 11 hours in April and about 6 hours on 28 and 29 June. Its first funder, also the first funder of `GeBJSHK4WsGrz2HRvTbqvWGx4JRMpHfJG2ikzrYBDuwR`, is a program-owned account holding 10,507 SOL.
- **`49SecDmFPyFKphUKckC8oWDxKQWp5NN4QD8Wg6CT6Gy3`** gets exactly 1.0 SOL from the deployer on 1 July and 1.0 SOL signed by `GV6UUmNx` on 2 July. Read only for April to July 2024 and 25 June to 15 July 2026. Too thin to mean anything, reported because it is the one small wallet with the same amount from both sides.
- **`BrV2WXWw5wU9pca4Nu4FJLhLU5cAbrkmLfXQmYm3ZZJG`**, funded with 5,148 SOL by `GV6UUmNx`, has 280 transactions touching ANSEM, net +1,037.48 SOL. Liquidity provision is not classified, so this is not a sale figure. **"No ANSEM sold" holds for `GV6UUmNx` itself, and nothing more.**

## A trap for anyone reading this wallet

17,630 token transfers leave `GV6UUmNx` without its signature, across 36 mints. All 36 mints have a permanent delegate. Example: 13 transfers of a token named "TJR WALLET IS: ..." to the deployer, signed by `FJ2Q9YPYucxPAHnjWzxM6JRJ6qmz5CUsv695dqx5mhhj`. Explorers show these as sent by him. A naive reading finds a return flow to the deployer here, and it would be false.

## Limits

- Chain data cannot see a private agreement or an arrangement through wallets nobody has tied to him.
- Six wallets are tied to him: one by his own post, five by flows from it, which is an inference. Their ownership is not proved.
- Family histories are partial. `FkCcgvCo`: 9 to 22 January 2025, then 1 March to 26 April 2026. `AvYukzeA`: 24 May to 15 July 2025, then 1 March to 21 May 2026. `F5XqYtdU`: 23 October to 18 November 2025, then 1 March to 8 September 2026. `9bxyzm6M`: January to July 2025, then March to September 2026. `4qcD8iSF` stops on 12 October 2026. Direct flows with `GV6UUmNx` are still covered from its side. The hub test is not complete, and "earliest traces January 2025" comes from those slices.
- `BY4StcU9` is unclassified. The August notes call it HTX and also a wallet factory. It has 248 counterparties in 1,000 transactions on 20 April, under the plan's service test of 500, and moves 10,229 SOL in those five hours. So its shared role in the funding of the deployer and of the 13:58:54 group cannot be dismissed as a service, nor read as a link.
- `2snHHreXbpJ7UwZxPe37gnUNf7Wx7wv6UKDSR2JckKuS` meets the service test only on a sample from November 2024 (537). A sample from the day it paid his wallet 1,922.67 SOL gives 283.
- Hot wallets are named by behaviour and balance. A hot wallet says nothing about who deposits.
- ANSEM's trades are read from 16 to 21 June and from 25 June to 14:06:38 on 27 June.
- SOL and wrapped SOL are traced. USDC and other assets are not traced as flows. No bridge scan was run.
- Metadata failed for 78 launches. Fee settings are read for 733 of 839 launches.
- Jito bundles were not mapped: the only public source keeps about seven days ([TOOLS_REVIEW.md](TOOLS_REVIEW.md)). The creation transaction carries no tip.
- X search is what X returns to one logged-in account (`evidence/x_searches.md`). A post that cannot be read may be deleted, protected or from a suspended account.

## Deviations from the plan

Listed in full, with dates, in [AMENDMENTS.md](AMENDMENTS.md). In short: the population and statistic of the rarity test differ from the plan, the tests of H1 and the other exploratory tests were added after seeing data, no correction for multiple tests was applied, and the hub test first used a 1 SOL cut the plan does not have. The table above uses the plan's 0.01 SOL.

## What would change this conclusion

- Any signed transfer from a wallet he controls to the deployer's family, or the reverse before 16 June.
- An exchange record tying the family's deposits to him.
- A private message, or an admission by the deployer or by the accounts its launches cite.
- A wallet he demonstrably controls that funded `FkCcgvCo`, `AQd3h5tk` or their sources.

## Files

| File | What |
|---|---|
| [TOKENS.csv](TOKENS.csv) | 952 launches of the family: buy, gifts, fee share, cited post, degree of proof. Token names are on-chain data, some offensive, kept as they are |
| [TOKENS_SENT_TO_ANSEM_WALLET.csv](TOKENS_SENT_TO_ANSEM_WALLET.csv) | Every transfer of at least 100 M tokens to his wallet, with what is known of the sender |
| [WALLETS.csv](WALLETS.csv) | Roles, funders, destinations, how much of each history was read |
| [graph.html](graph.html) | Interactive graph, with a date filter and a table |
| [TIMELINE.md](TIMELINE.md) | X and chain together, UTC |
| [EVIDENCE_LEDGER.csv](EVIDENCE_LEDGER.csv) | Claim to signature or post |
| [TOP10.md](TOP10.md) | Findings and open leads, by power to separate the hypotheses |
| [PROVENANCE.md](PROVENANCE.md) | The README's ANSEM figures against the raw block, and corrections to earlier notes |
| [TOOLS_REVIEW.md](TOOLS_REVIEW.md) | Open-source tools reviewed |
| [PLAN.md](PLAN.md), [AMENDMENTS.md](AMENDMENTS.md) | The plan written first, and what changed |
