# Provenance of the earlier ANSEM figures

`code/p1_readme_check.py` lists the ANSEM block of the root README as unbacked: "the ANSEM launch has no committed creation-slot measurement". `evidence/creation_slot.json` and `evidence/raw/creation_slot_txs.json.gz` are that measurement. This file compares. **Nothing in the README, the frozen studies or their tables was changed.** Corrections below are proposals for the author.

## Current README, section "Real-World Example"

It presents these as "my original observation, not reproduced by the published artefacts".

| README says | Raw block says | Status |
|---|---|---|
| Created 2026-06-16 21:05:48 UTC, slot 426930467 | Same | Confirmed |
| 85.007 SOL purchased in the creation slot | 85.005359058 SOL into the curve (84.740740739 + 0.264618319). The same wallet then buys more on the pool in the same slot | Off by 0.002 SOL on the curve |
| 84.74 SOL purchased by a single wallet | 84.740740739 SOL | Confirmed |
| Only two buyers | Two wallets gain tokens | Confirmed |
| Sixteen signatures | 18 transactions cite the mint: 5 succeed, 13 fail | 16 not reproduced |
| No bonding-curve supply left for public buyers | The curve is emptied in the slot. The pool opens in the same slot with 176.8 M tokens | Confirmed for the curve |
| Both wallets recur in the catalogue, one a repeat operator, the other shared infrastructure | `docs/out/m4_infra.json` has `yHCxHBEa` on 24 of 282 and `9ryBR3Sn` on 44 of 282. The 24 are launches `yHCxHBEa` created itself. `9ryBR3Sn` reacts in the same slot with its own program | Consistent, and "creator" describes the first one better |
| An alert fired shortly after creation; no log published | Not tested here | Open |

## Older README (`git show c56b45f^:README.md`, lines 131 to 146)

The older text is no longer on the branch. It gave `yHCxHBEa` 84.743 SOL (the curve receives 84.7407, and 86.0681 leaves the wallet with fees and rent) and `9ryBR3Sn` 0.265 SOL (0.2646 for the last curve tokens, then 30.08 M more tokens on the pool, 16.09 SOL in all). It also called this signature "now the norm". This launch is one create-and-buy transaction with no tip, not a multi-wallet bundle.

The footnote URLs on the 7 M$ airdrop agree with his own post saying about $7M (E18). That is his statement, and the on-chain amount in dollars was not measured here. "$6,300" is Lookonchain's figure, in line with 86.07 SOL at the time, not re-derived.

## August notes in `ansem_enquete`

| Note | Now | Why |
|---|---|---|
| `9ryBR3Sn` cost 1.4588 SOL, PnL +34.93 SOL | Cost 16.09 SOL, net +19.94 SOL | The note read native SOL only and missed wrapped SOL |
| `yHCxHBEa` PnL +76.56 SOL, sales 162.63 SOL | +73.34 SOL on trading, sales 159.41 SOL, plus 0.4857 SOL of fees | Native and total sales agree here at 159.405670644 SOL, so wrapped SOL does not explain the gap. Cause not established |
| Start of the run at 14:03:00, "four minutes" after the one-slot group | His post is at 14:03:08, the first buy of 5 SOL or more after it at 14:03:31 | The note worked from a one-minute candle and had not seen the post |
| 8.36 SOL net bought before the run | Pool level, 15 minutes to 14:03:08: 9.16 SOL in from buyers, 16.86 SOL out to sellers | Different windows and method. An owner-level count misses aggregator buys |
| The 15 wallets are clients of one trading platform, on four measures, one being that all pay 0.8583 % to `CQfwrncb67iboVdGB62naWUFUWutuRfizZ3jncGRNTiR` | **That measure is wrong.** It is a token account held by `AdPnUcnMJY4JExDWXb2Zd3QD76VYP1c6KHszwVZqjUfv`, the vault that later pays ANSEM's fees to Ansem's wallet. Every buyer sampled pays it, in the group or not | 13 transactions, 4 in the group and 9 outside, 25 to 27 June: `evidence/small_checks.json` |
| "Same platform" conclusion | Unproven. The other measures stand as written in the note. The one-slot pattern is not rare on this token: nine slots with ten or more buyers since 25 June | `evidence/numbers.json` |
| `GV6UUmNx`: "porteur des 650 M" with no identity given | Ansem's wallet, by his own post | E01 |
| HTX for `BY4StcU9`, and elsewhere "usine à wallets" | Unclassified. The two notes conflict and neither is verified on chain | `evidence/followups.json` |

## Public sources against the chain

The articles were read through a fetch on 2026-11-03 and no copy is kept here, so these two rows cannot be checked offline. Sources: [Bitquery](https://bitquery.io/investigations/ansem-black-bull-370x-investigation), [AMBCrypto](https://ambcrypto.com/ansem-deployer-sends-60-of-supply-to-ansem-who-says-he-has-airdropped-7m-to-holders/).

| Source | Says | Chain says |
|---|---|---|
| Bitquery | Public trading did not open until June 22 | Trading from 16 June: 8,086 transactions changed a token balance that day |
| Lookonchain (also a saved post, E25) | Deployer spent $6.3K, sent 650 M, sold 142.45 M for $11.8K, made $5.5K | Consistent in SOL. It leaves out the other launches |
