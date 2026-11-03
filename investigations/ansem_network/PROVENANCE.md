# Provenance of the earlier ANSEM figures

`code/p1_readme_check.py` lists the ANSEM block of the root README as unbacked: "no committed artefact". `evidence/creation_slot.json` and `evidence/raw/creation_slot_txs.json.gz` are that artefact. This file compares. **Nothing in the README, the frozen studies or their tables was changed.** Corrections below are proposals for the author.

## README, section "Real-World Example"

| README says | Raw block says | Status |
|---|---|---|
| Created 2026-06-16 21:05:48 UTC, slot 426930467 | Same | Confirmed |
| Entire curve bought in the creation slot: 85.007 SOL | 85.005359058 SOL into the curve (84.740740739 + 0.264618319) | Off by 0.002 SOL |
| 84.74 SOL bought by a single wallet | 84.740740739 SOL | Confirmed |
| `yHCxHBEa` at slot 0: 84.743 SOL | 84.7407 into the curve, 86.0681 out of the wallet with fees and rent | 84.743 matches neither |
| `9ryBR3Sn` at slot 0: 0.265 SOL | 0.2646 for the last curve tokens, then 30.08 M more tokens on the pool in the next transaction, 16.09 SOL in all | Incomplete: the larger purchase is missing |
| Only two buyers | Two wallets gain tokens | Confirmed |
| Sixteen signatures | 18 transactions cite the mint: 5 succeed, 13 fail | 16 not reproduced |
| Nothing left for public buyers | The curve is emptied in the slot and the pool opens in the same slot with 176.8 M tokens | Confirmed for the curve |
| `yHCxHBEa`: repeat operator on 24 of 282 tokens, not infrastructure | 24 launches of the corpus are launches it created itself | Confirmed, and better described as the creator |
| `9ryBR3Sn`: shared-infrastructure sniper | Reacts in the same slot, own program, priority fee of 0.59 SOL per transaction; rarity p = 0.999 | Consistent |
| "This signature is now the norm" | Here one wallet buys in the creation transaction with no bundle and no tip | This launch is a single create-and-buy, not a multi-wallet bundle |

The README's 7 M$ airdrop and 1 M holder goal are confirmed by his own post (E18). The "$6,300" is Lookonchain's figure, consistent with 86.07 SOL.

## August notes in `ansem_enquete`

| Note | Now | Why |
|---|---|---|
| `9ryBR3Sn` cost 1.4588 SOL, PnL +34.93 SOL | Cost 16.09 SOL, net +19.94 SOL | The note read native SOL only and missed wrapped SOL |
| `yHCxHBEa` PnL +76.56 SOL | +73.34 SOL on trading, plus 0.4857 SOL of fees | Same |
| Start of the run at 14:03:00, "four minutes" after the group | His post is at 14:03:08, the first buy of 5 SOL or more at 14:03:31 | The note worked from a one-minute candle and had not seen the post |
| The 15 wallets are clients of one trading platform, because all pay 0.8583 % to `CQfwrncb67iboVdGB62naWUFUWutuRfizZ3jncGRNTiR` | **That proof is wrong.** It is a wrapped-SOL token account tied to `AdPnUcnMJY4JExDWXb2Zd3QD76VYP1c6KHszwVZqjUfv`, ANSEM's creator-fee vault. Every buyer on this pool pays it, inside the group or not. `AdPnUcnM` later pays those fees to Ansem's wallet | Checked on 10 transactions in and out of the group, June 25 to 27 |
| "Same platform" conclusion | Unproven. The neutral-day co-firing measure still stands, so the group is related in some way. What binds it is open. The one-slot pattern itself is routine on this token: sixth largest of 2,399 slots | `evidence/numbers.json` |
| `GV6UUmNx`: "porteur des 650 M" with no identity given | Ansem's wallet, by his own post | E01 |
| HTX for `BY4StcU9` | Kept as the author's label, not verified on chain | `etiquettes.json` says so |

## Public sources against the chain

| Source | Says | Chain says |
|---|---|---|
| Bitquery, "ANSEM 370x" | Public trading did not open until June 22 | Trading from 16 June: 7,671 rows with a token change that day alone |
| Bitquery | The creator wallet routed the rest to the pool | Yes, through seven sales for 159.41 SOL, not a neutral routing |
| Lookonchain | Deployer spent $6.3K, sent 650 M, sold 142.45 M for $11.8K, made $5.5K | Consistent in SOL. It leaves out the 50 launches around it |
| Several articles | Holdings of 604 M, 60 % or 65 % | 650 M received, plus 4.28 M; the holding falls with the airdrops. A snapshot question, not a contradiction |
