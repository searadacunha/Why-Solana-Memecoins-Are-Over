# ANSEM: who organised what

Investigation of the token `9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump`, written 2026-11-03. Every important claim has a line in [EVIDENCE_LEDGER.csv](EVIDENCE_LEDGER.csv), and `code/check_ledger.py` re-derives the checked ones from the raw transactions and posts saved in `evidence/`.

## The answer

**The hypothesis that Ansem organised this launch, or a network of launches, is not supported by anything on chain or in his public posts. It is not disproved either: chain data cannot see a private message.**

What the data does show:

1. The token was made by a serial launch wallet, `yHCxHBEaJW5tbndqC8JciSThr7U1cqLpdcsvHcx6PRe`. It created 839 tokens from April to November 2026 and belongs to a group of wallets active since January 2025.
2. That wallet gave Ansem's newly published wallet 65 % of the supply and 100 % of the creator fees, starting within minutes of his post. The transfers need no signature from the receiver, and his wallet signs nothing for more than six days.
3. It sent his wallet tokens from 50 of its launches and repeated the full recipe, 650 M tokens or more, on 21 launches after ANSEM, while he asked in public not to be sent coins. 634 other senders also gave his wallet at least 100 M of a token.
4. No SOL and no signed token transfer ever went from his wallet to that group. They share only pools and services.
5. He adopted the token 11 days later, in public, and calls it a community takeover. The price run starts 23 seconds after that post, not before it.

That is the pattern of a deployer using his name and wallet as a launch gimmick, and of him then taking the token up. The one fact that does not fit neatly is in the section "What still looks odd".

## Conclusions by rung

The ladder was fixed in [PLAN.md](PLAN.md) before any new data was read.

| Rung | Conclusion | Basis |
|---|---|---|
| Same technical method | **Yes, and common.** 635 senders gave his wallet at least 100 M of a token. | `TOKENS_SENT_TO_ANSEM_WALLET.csv` |
| Same infrastructure | **Yes for one commercial tool.** The launch pays 0.3 % to `uxtoRPdPjRekYmxs1uUqVRZWh38iqonc9KgPuZXPeSY` and its metadata is on uxento.io. Tools are for sale, so this says nothing about owners. | E08 |
| Same financial network | **Yes for the deployer's family:** nine wallets exchanging thousands of SOL, with signatures, 952 launches. **No link to Ansem's wallet.** | `WALLETS.csv`, `evidence/link_tests_extended.json` |
| Probable same operator | **Certain for the 839 launches of one signing wallet. Not claimed for the rest of the family.** The plan requires a rarity test that rejects chance, and it does not (see below). | `evidence/rarity.json` |
| Personal attribution | **Only this: `GV6UUmNxz2RpKxmNAPadYKb7uQpszwqQAu3qLJxVdC52` is Ansem's wallet, by his own post.** Nothing attributes the launch or the deployer to him. The plan excludes a token received after launch from this rung, and these tokens were received. | E01 |

## What happened

Times are UTC. The full list is in [TIMELINE.md](TIMELINE.md).

**Before.** On 11 May a public post proposes to "dev a coin about him and send him supply and fees", naming the wallet `AVAZvHLR2PcWpDf8BXY4rVxNHYRBytycHkcB5z5QNXYm`, which Kolscan attributes to him. The deployer launches tokens named Ansem that day. In May and June it also sends that wallet tokens from 10 mints, and fee shares on 7 launches.

**16 June.** At 15:36 he writes "that's not my wallet lads". At 15:45:50 the deployer launches a first token called The Black Bull, symbol ANSEM, and gives all 400 M tokens it bought and all its fees to another wallet, `Dt4gYgAUts6puim6yj4m874V5TuGUGFyZVv4RNpFvUkY`. Through the afternoon people press him: coins are sending fees to a wallet that is not his, "confirm or give a newer wallet".

At **20:59:26** he posts: "i just linked my X to a pumpfun account [...] im not endorsing any microcaps, just to prove that i can connect my X to an address on the app", with a link to `GV6UUmNx`. The wallet has no transaction before that second. Its first transactions are third parties adding it to their fee settings.

| Time | Event |
|---|---|
| 21:01:00 | Deployer sends `GV6UUmNx` 20 M of another token, right after serving 17 other wallets the same amount |
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

- Position 279: the deployer, with the mint key. It pays 84.740740739 SOL into the curve, for 792,454,486.76 tokens. With fees, 86.06810776 SOL leave the wallet. The input is exactly 85.8 SOL, and pump.fun takes its 1.25 % from that. No Jito tip in the transaction.
- Position 1383: `9ryBR3SnxgGPhWsKvsfxuNHUCTt6tSpLe8wrKCShXLaq` buys the last 645,513 tokens for 0.2646 SOL.
- Position 1384: the same wallet triggers the migration and buys 30,077,097 tokens on the new pool. Its total cost is 16.09 SOL, of which 1.18 SOL is priority fees. It sells out in seconds, net +19.94 SOL.
- Seven other bot wallets try and fail 13 times.

The deployer's net on the token is +73.34 SOL on trading, plus 0.4857 SOL of fees. It never held the token again.

**The eleven days.** `GV6UUmNx` signs nothing until 23 June, when it buys another token. It never touches ANSEM until 28 June. Meanwhile the deployer keeps pushing ANSEM's fees to it: 144.81 SOL on 19 June, 165.44 SOL on 22 June, 55.05 SOL on 25 June.

**27 June.** In the 15 minutes before his post, 27 wallets buy, 6.38 SOL in all. In the hour before it, one buy reaches 5 SOL.

- 13:50:36: "hit 1M followers".
- 13:57:40: replies "lets ride" to "Delusional bulls always win". No token named.
- 13:58:54: 15 wallets buy in one slot, 5.66 SOL. This looks striking and is not: it is the sixth largest such group among 2,399 slots since 25 June, and the largest had 33 buyers.
- **14:03:08: "sure i will airdrop portions of the creator fees that have been directed to my pump fun profile"**, answering a suggestion from `@Clive_99`. Reposted at 14:06:38.
- **14:03:31: first buy of 5 SOL or more, 11.0 SOL, 23 seconds later.** 432 SOL of buying by 14:06:38.

**After.** On 28 June, "dont send it to my wallet send it to all the $ANSEM holders". He moves ANSEM for the first time at 02:07:53, then airdrops: 567.05 M tokens leave in transactions he signs, to 1,319 wallets, of which 491 M go to a new wallet `7oU9nR9VEvFPwvp2PpXo2LQc6A92QRhcUTwhLWT7MsDM`. On 9 July, "I CTOd the $ANSEM token". On 16 July, to `@Supermanonchain`: "when you stop vamping good projects".

## The tests of H1

For each test, what H1 predicts and what was measured. His wallet is read in full, 122,407 transactions up to 3 November, and so is the deployer, 242,603. So a direct flow between those two cannot be missed.

| Test | If he organised it | Measured |
|---|---|---|
| Money from his wallet to the deployer's family | Some return of value | **0 SOL. 0 token transfers signed by him.** |
| SOL from the family to his wallet, outside the fee mechanism | Some funding | **0** |
| History of his wallet before the launch | Prior contact | **None exists.** First transaction at the second of his post. A signature query before it returns nothing (`evidence/genesis_check.json`) |
| His signature on launch actions | Consent or action | **None** on the transfer, the fee setting or the fee pushes |
| Deployer treats him as a partner | Exclusive or arranged | **No.** 50 launches send him tokens, and it serves many others: 202 fee recipients and 45,103 token recipients in the first 800 pages of its history |
| Deployer stops when he objects | It should | **No.** 21 launches of 650 M tokens or more after 16 June, most after "dont send it to my wallet" |
| Deployer keeps a position, knowing what is coming | It should | **No.** Sold out in 50 seconds, +73.34 SOL. No re-entry in its full history, only dust received. The family's other wallets do not trade ANSEM in the windows read |
| Buying ahead of his post | Accumulation | **No.** 6.38 SOL in 15 minutes |
| His wallet buys the family's other launches | Coordination | **No.** 44 buys over 23 mints, 4,845.79 SOL; none a family launch except three dust receipts of ANSEM. 7 sales, 2,901.30 SOL, none of ANSEM and none of a family launch |
| Common private intermediary | Shared hub | **None found.** 10 addresses touch both sides at 1 SOL or more. Program-owned pools: 5 (GoonFi, BisonFi and Tessera by their program addresses, one more). Hot wallets or services: 2. Closed accounts that behave as fee vaults: 2. One small wallet: `49SecDmFPyFKphUKckC8oWDxKQWp5NN4QD8Wg6CT6Gy3`, see below |
| Exits to the same deposit addresses | Same owner | **None.** His large exits go through one-use wallets into hot wallets, and those one-use wallets receive from him alone |
| The wallet he denies | Would connect him | `AVAZvHLR` has **no flow with `GV6UUmNx`** and none with the family except gifts received, 15 April to 31 July |

The method does find links when they exist. The same queries find 27 SOL relationships inside the deployer's family, up to 19,306 SOL on one pair.

**The natural comparison group.** 1,065 transfers of at least 100 M tokens reached his wallet, from 635 senders across 971 mints. 38 of them, from 23 senders, came before his first adoption post. In the seven minutes after his wallet post, three other senders gave him 300 M, 150 M and 100 M of their tokens before this deployer sent its 650 M. ANSEM is one of many tributes, and the largest of the first day except for one 983 M gift.

## The deployer's family

Rung: same financial network. No statement about who they are.

- `yHCxHBEa` is first funded on 20 April at 13:00:49 by `BY4StcU9Y2BpgH8quZzorg31EGE4L1rjomN8FNsCBEcx` (4.43 SOL, labelled HTX in the author's August notes, not verified), then 96 seconds later by `FkCcgvCoR6p6BRucCnU1t1DXP97Y3rJeMYBiU1o31nuv` (9.13 SOL). Its first launch comes under five minutes after that.
- It sends 19,306 SOL to `FkCcgvCo` and receives 7,791 SOL back. Other main ties: `4qcD8iSFLC5VDZphBtM7pSeevtHtD8Chi7Zmhcm9TvHm`, `E94dd6pnFhE7LNbC7oSbyWmCCQ9kNoEhSa6cKN6brSAm`, `F5XqYtdUWUT7bbuuKEjckDs8Hwk7j7mhdwGe3YKn5Xf7`, `AvYukzeAFzFo66i1GJHShcdBbb4jeSkZiEJnNMds54mo`, `9bxyzm6MFn3TWEedvYuMzSaZkkGWKSyTgWpRXCzMP3dm`, `DxnxpqcUsErqRFRbfVrKr988F9AxayryC5eKWPKgvjmR`, `6xMLLrtZAh8ToWjeZ9Nm4RKtEC3uY2Qqscihz4yHp1jK`.
- The family's earliest traces are January 2025. `F5XqYtdU` is first funded through the ChangeNOW gateway, where tracing ends. `AQd3h5tkbdhTiWv7WmiCbm8uwjYi8vTBbMzEtAGtf1T5`, tied to `F5XqYtdU` by 28,529 SOL out and 14,885 SOL in, held 13,537 SOL when read.
- Launches: `yHCxHBEa` 839, `FkCcgvCo` 74, `F5XqYtdU` 16, `AvYukzeA` 11, `E94dd6pn` 9, three others one each.
- Capital is recycled in the plain sense. One wallet pays 27,227 SOL of dev buys from a pooled balance fed by earlier sales. Sales it signs itself net 18,227 SOL. That figure is low, because tokens moved to side wallets and sold there are not in it, as with $SUPERMAN (1,026 SOL bought, no sale signed by this wallet).

**How it picks launches.** Of 761 launches with readable metadata, 541 link a specific X post. The launch follows that post by a median of 31 seconds, 10th percentile 12 seconds, and never precedes it. 106 accounts are cited, led by `@Supermanonchain` (182), `@NikolaiFrandsen` (135), `@RoaringKittyCat` (21), `@LastManOnchain` (19), `@zitobondoor` (18), `@Donnieonchain` (10) and `@blknoiz06` (9, his own words turned into tokens within seconds).

Exploratory test: of 23 readable posts naming a share ("sending 5%", "sending 60%"), 14 match the largest gift in the launch within 3 points, against 1.09 expected when posts and launches are shuffled (p = 0.0005, 2,000 draws). 434 of 541 cited posts cannot be read through the public endpoint. `@Supermanonchain` shows as suspended on 3 November.

So the deployer executes what these posts announce, within seconds and to the percentage. Either the same people write the posts, or a very fast copier follows them. Two third-party posts call `yHCxHBEa` the dev wallet of `@Supermanonchain`'s token. **That is a lead about the operator, not a finding, and none of it touches Ansem.** An X search for his replies naming the five most cited accounts returns only the hostile one above.

**Rarity test, as fixed in the plan.** 343 launches, 1,856 wallets, 10,000 curveball draws. A planted pair is detected (p = 0.006), shuffled data stays quiet (0 of 40). `yHCxHBEa` p = 0.66, `9ryBR3Sn` p = 0.999, `dshAybqF` p = 0.985: their partners are the bots found everywhere. `LfEcaUf7` is flagged (p = 0.0001), with a redacted wallet that shares 68 of its 91 launches. Six seeds are not in this corpus. This test looks at who buys in the same slot, so it cannot speak to fund flows. It gives no support to a co-sniping group around ANSEM.

**Gift list, exploratory.** 2.8 % of wallets that received at least 1 M tokens in two or more launches, and 5.9 % of fee recipients, are in a public Kolscan snapshot of 472 wallets. Among 28,880 wallets trading ANSEM before his post, 0.09 % are. The snapshot is third-party and undated. Other big recipients are unlabelled, and some are hot wallets. It fits a deployer that targets well-known wallets. It says nothing about whether those people agreed.

## What still looks odd

- **The deployer serves his wallet more than anyone's.** 20 of its 325 fee pushes, 640.16 SOL of 868.96 SOL, go to `GV6UUmNx`, up to 29 June. No other recipient gets more than 2. The simple reason is that fees accrue where trading is, and it stops once others push. Still, it spent effort for 13 days on a token it no longer held, and no chain data says why. It may have been courting attention or chasing the next launch.
- **`8wvqvPt1DDdjdghpMpp7ueQFUL5Js5zux4pPeRFXWteB`** pushes at least 5,131.56 SOL of fees to his wallet from 21:56 on 28 June, the day after he wrote that they need a way to claim in bulk. The count stops at 22:28, where the transaction bodies I kept end, so the real figure may be higher. No flow ties it to his wallet or to the family. I do not know who runs it.
- **`49SecDmF`** gets exactly 1.0 SOL from the deployer on 1 July and 1.0 SOL signed by `GV6UUmNx` on 2 July. It is a small wallet, and nothing else follows. Too thin to mean anything, reported because it is the only ordinary wallet touching both sides.

## A trap for anyone reading this wallet

17,630 token transfers leave `GV6UUmNx` without its signature, across 36 mints. Example: 13 transfers of a token named "TJR WALLET IS: ..." to the deployer, signed by `FJ2Q9YPYucxPAHnjWzxM6JRJ6qmz5CUsv695dqx5mhhj`, which holds a permanent delegate on that mint. Any explorer shows these as sent by him. They are not. A naive reading finds a return flow to the deployer here, and it would be false.

## Limits

- Chain data cannot see a private agreement. That is why the answer is "not supported" and not "disproved".
- Only three wallets are tied to him: one by his own post, and `7oU9nR9V` and `BrV2WXWw5wU9pca4Nu4FJLhLU5cAbrkmLfXQmYm3ZZJG` by flows from it, which is an inference. A wallet of his that is unknown to me would not be tested.
- Family wallets other than the deployer are read in part. `FkCcgvCo` stops at 26 April 2026, and `AvYukzeA` at 21 May, in their own histories. Direct flows with his wallet are still covered from his side. The search for common hubs is not complete.
- Hot wallets are named by behaviour and balance, except where a source is given. A hot wallet says nothing about who deposits.
- ANSEM's trades are read from 16 to 21 June and from 25 June to 14:06:38 on 27 June. The gap of 21 to 25 June is not read, for cost.
- SOL and wrapped SOL are traced. USDC and other assets are not traced as flows. No bridge scan was run.
- Metadata failed for 78 launches. Fee settings are read for 733 of 839 launches.
- Jito bundles were not mapped: the only public source keeps about seven days ([TOOLS_REVIEW.md](TOOLS_REVIEW.md)). The creation transaction carries no tip.
- X search is what X returns to one logged-in account. Deleted posts are missing unless a later post or metadata cites them.
- The exploratory tests were added after seeing data and are labelled as such ([AMENDMENTS.md](AMENDMENTS.md)).

## What would change this conclusion

- Any signed transfer from a wallet he controls to the deployer's family, or the reverse before 16 June.
- An exchange record tying the family's deposits to him.
- A private message, or an admission by the deployer or by the accounts it follows.
- A wallet he demonstrably controls that funded `FkCcgvCo`, `AQd3h5tk` or their sources.

## Files

| File | What |
|---|---|
| [TOKENS.csv](TOKENS.csv) | 952 launches of the family: buy, gifts, fee share, cited post, degree of proof. Token names are on-chain data, some offensive, kept as they are |
| [TOKENS_SENT_TO_ANSEM_WALLET.csv](TOKENS_SENT_TO_ANSEM_WALLET.csv) | The comparison group: every transfer of at least 100 M tokens to his wallet |
| [WALLETS.csv](WALLETS.csv) | Roles, funders, destinations, how much of each history was read |
| [graph.html](graph.html) | Interactive graph, with a date filter and a table |
| [TIMELINE.md](TIMELINE.md) | X and chain together, UTC |
| [EVIDENCE_LEDGER.csv](EVIDENCE_LEDGER.csv) | Claim to signature or post |
| [TOP10.md](TOP10.md) | Findings and open leads, by power to separate the hypotheses |
| [PROVENANCE.md](PROVENANCE.md) | The README's ANSEM figures against the raw block, and corrections to earlier notes |
| [TOOLS_REVIEW.md](TOOLS_REVIEW.md) | Open-source tools reviewed |
| [PLAN.md](PLAN.md), [AMENDMENTS.md](AMENDMENTS.md) | The plan written first, and what changed |
