# The nine wallets of h2w6gm6jz, rebuilt from signatures

Token `FNqJtYs7rsP1H9GXWTtc5VnDoL2GhXEUKhYN46EEpump`. Gateway `G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t`, publicly attributed
to ChangeNOW. Every figure comes from decoded transactions, with none copied from the published dossier, which is only compared with
at the end. Data: [group15_detail.json](group15_detail.json), with the signature of every credit and sweep. Code: `investigations/nine_wallets.py`
and `investigations/posthoc/nine_*.py`.

**The nine credits are real, but the group is fifteen wallets, and this token was not its reason to exist. The fifteen were funded
together, then traded nine tokens as one fleet in four days. They made +49.81 SOL overall, and lost 4.66 SOL on this one.**

## Reconciliation: nine in 343 s against fifteen in 380 s

**The nine are all inside the fifteen. It is one population, partly counted. The published nine, their times and their 343 s are correct as far as they go.**
Data: [reconciliation.json](reconciliation.json), with signatures. Code: `investigations/posthoc/nine_reconcile.py`. Each credit was read twice, from this engine's raw cache and from the
public Solana RPC, with no key: both give the same reading on all 15.

| Wallet | Credit, UTC | Slot | Lamports | First transaction of the wallet | Rank on the curve in the published `e6` | Published? |
|---|---|---:|---:|---|---:|---|
| `Ek9KG4V4` | 07:07:12 | 307170732 | 2,976,815,600 | yes | 139 | not published |
| `Csye9QE8` | 07:07:49 | 307170824 | 2,976,815,600 | yes | 138 | **in the nine** |
| `BmkuX6Da` | 07:08:02 | 307170855 | 2,976,815,600 | yes | 144 | **in the nine** |
| `HMzrigYC` | 07:08:41 | 307170952 | 2,976,815,600 | yes | 135 | not published |
| `AwQqcqdQ` | 07:09:04 | 307171008 | 2,976,815,600 | yes | 141 | **in the nine** |
| `73u1CWYf` | 07:09:28 | 307171065 | 2,976,815,600 | yes | 145 | not published |
| `3bBaA1Mp` | 07:10:12 | 307171171 | 2,976,815,600 | yes | 136 | **in the nine** |
| `CDvfNWia` | 07:10:31 | 307171218 | 2,976,815,600 | yes | 147 | **in the nine** |
| `92w4K8uL` | 07:10:53 | 307171270 | 2,976,815,600 | yes | 133 | **in the nine** |
| `6QMshP9z` | 07:11:20 | 307171335 | 2,976,815,600 | yes | 137 | **in the nine** |
| `BXuznwXT` | 07:11:53 | 307171413 | 2,976,815,600 | yes | 142 | **in the nine** |
| `AMgwVTFS` | 07:12:32 | 307171507 | 2,976,815,600 | yes | 134 | not published |
| `2M3cBCG4` | 07:12:57 | 307171568 | 2,976,815,600 | yes | 140 | not published |
| `JCVPTRSH` | 07:13:05 | 307171584 | 2,976,815,600 | yes | 146 | not published |
| `5ibajLye` | 07:13:32 | 307171650 | 2,976,815,600 | yes | 143 | **in the nine** |

For all 15: the System Transfer is outer instruction 1, its source is the gateway `G2YxRa6w…`, the wallet held 0 lamports before and exactly the credit after, and no other System Transfer is in the transaction.
The fee payer is not the gateway: all 15 are paid by `E9vf42zJ…` and co-signed by `DScDQ1zV…`, the same three signers each time. That is the gateway's own sending setup as far as these 15 show, and it was not measured further.

**Where the 37 extra seconds come from.** One wallet, `Ek9KG4V4`, was credited at 07:07:12, 37 s before the first published credit. The last credit, 07:13:32, is the same in both. The other five added wallets fall inside the published 343 s, so the published span was not wrong about its nine; it missed the group's start.

**Why the two counts differ.** Same chain, different rules:

| | Historical count | Rebuilt count |
|---|---|---|
| Who is looked at | 223 distinct wallets in `all_buyers_g2y.json`. The script that wrote it is not in the repository; the sister script `code/scan_gateway_dispatch.py` counts every fee payer on the curve | 184 wallets with a buy TradeEvent |
| Unreadable wallets | 90 of the 223 left out, with no list of which | None of the 184 |
| How the credit is read | Helius's parsed `nativeTransfers` | The raw transaction: instruction, balances |
| What makes a group | Largest set of exactly equal credits among wallets that could be read | Exactly equal token purchases on the curve, then each wallet's credit and full history |

**Where the six went.** All six are in the published curve-buyer list `e6`, so they were on the scanned curve. None is in the published file's wallets. Each is fresh and credited by the gateway, which that file would have kept had it read them. So they most likely sit among the 90 unreadable wallets (`STRONG_TECHNICAL_INFERENCE`). The file keeps no list of those 90, so this cannot be proved from it.

**What stands and what does not, from the published text.** Stands: exact amount to nine decimals, fresh wallets, common gateway, funding hours before the token, 7.6 hours from the last credit. Incomplete: the count and the span, now 15 and 380 s. Not supported as stated: reading that funding as preparation for this token, for the reasons in the section "What this changes" below.

**Not checked.** Whether any of the 23 other recipients of this amount that day also bought this token with a different size. The group is defined by the purchase, so this does not change the 15; it could only add a looser ring around them.

## What the signatures show

| | Published | Rebuilt |
|---|---|---|
| Wallets credited with exactly 2,976,815,600 lamports | 9 | **15** |
| Time between first and last credit | 343 s | **380 s** (07:07:12 to 07:13:32 UTC, 2024-12-13) |
| Is the credit each wallet's first transaction? | "fresh" | Yes, all 15, history read to its start |
| Hours before the token's creation (14:50:34 UTC) | about 7.6 | 7.62 from the last credit |

The six left out are `Ek9KG4V4`, `HMzrigYC`, `73u1CWYf`, `AMgwVTFS`, `2M3cBCG4`, `JCVPTRSH`. The published scan found 223 buyers and
could not read 90 of them, so nothing in it contradicts this. They were simply not measured.

## The twelve questions

| # | Question | Answer | Level |
|---|---|---|---|
| 1 | Are the nine payments confirmed by their signatures? | Yes, and six more | `ONCHAIN_VERIFIED` |
| 2 | Which instructions? | System Transfer, outer instruction 1, from the gateway | `ONCHAIN_VERIFIED` |
| 3 | Effective beneficiaries? | The wallets themselves: each keeps it, and it is their first transaction | `ONCHAIN_VERIFIED` |
| 4 | Did they buy the token? | All 15, at 14:53:06-07 UTC, about 2.5 minutes after creation | `ONCHAIN_VERIFIED` |
| 5 | In what order? | Consecutive: buyers 134 to 148 of 184 on the curve, in slots 307237978 to 307237981, each in its own transaction, signed by itself | `ONCHAIN_VERIFIED` |
| 6 | For how much SOL? | 0.409 to 0.474 SOL into the curve, rising with each buy; 7.11 SOL all included | `ONCHAIN_VERIFIED` |
| 7 | What share of supply? | **Exactly 2,035,147.973459 tokens each**, 0.2035 %, so 3.05 % together. Not a large share per wallet | `ONCHAIN_VERIFIED` |
| 8 | Did they sell together? | Yes: all 15 at 14:57:40 UTC, slots 307238635-6, their entire position on Raydium, 4 min 34 s later, for 2.45 SOL | `ONCHAIN_VERIFIED` |
| 9 | Who got the proceeds? | They stayed in the wallets and paid for the next token | `ONCHAIN_VERIFIED` |
| 10 | A common treasury? | A common wallet: 30 transfers, 92.12 SOL, from all 15, to `ERGbjcz9fs95YKvM6zXqvEaicK4VPPo2JwNV8beGKZM4`. Treasury or service is not established: the 15 are 3.3 % of what it received | transfers `ONCHAIN_VERIFIED`, role `UNRESOLVED` |
| 11 | Why do the two collections differ? | See below: they measured different things | `ONCHAIN_VERIFIED` |
| 12 | Does the motif return on other tokens? | The same fleet does it again on the same days, table below. Other fleets do it too: [gateway bursts](../gateway_bursts/README.md) | `ONCHAIN_VERIFIED` |

Identical raw amounts from 15 signers in 4 slots, and a sale in the same two slots, are not chance: one tool or one operator ran these
wallets (`STRONG_TECHNICAL_INFERENCE`). Whether that is one owner or a platform's clients is `UNRESOLVED`.

## The fleet, token by token

| First buy (UTC) | Mint | Wallets | Slots between buys | SOL in | SOL out | Result | Same raw amount |
|---|---|---:|---:|---:|---:|---:|---:|
| 12-13 07:51 | `DHq1eHTK…` | 15 | 1,450 | 25.28 | 99.00 | **+73.72** | 15 |
| **12-13 14:53** | **`FNqJtYs7…`** | **15** | **3** | **7.11** | **2.45** | **-4.66** | **15** |
| 12-14 09:59 | `BpXjLp1x…` | 15 | 0 | 19.09 | 21.62 | +2.54 | 15 |
| 12-14 19:34 | `JDjsoEJX…` | 7 | 127,481 | 25.29 | 29.31 | +4.02 | 1 |
| 12-15 11:58 | `FLfwkCVG…` | 8 | 1,426 | 7.23 | 6.79 | -0.44 | 5 |
| 12-15 12:38 | `4Z3SXT4A…` | 12 | 2 | 3.06 | 9.18 | +6.12 | 12 |
| 12-16 10:46 | `9VAUxZwN…` | 15 | 962 | 42.30 | 15.64 | -26.66 | 14 |
| 12-16 11:54 | `HYFwkjJb…` | 13 | 13 | 9.61 | 4.12 | -5.49 | 13 |
| 12-16 14:22 | `DvHm5wvf…` | 14 | 44 | 10.65 | 11.31 | +0.67 | 8 |

Money in the whole fleet: 44.65 SOL credited by the gateway, the only inflow above 0.01 SOL. 92.12 SOL then sent to the common wallet and
5.77 SOL elsewhere. Realised +49.81 SOL. Sweeps at three moments: 12-13 around 08h, 12-13 around 12h, and 12-16 around 14h. All 15 stop on
2024-12-17. This is the same lifecycle the dossier described for six wallets.

## What this changes in the published reading

- **Funding before creation is not preparation for this launch.** Forty minutes after being funded and seven hours before this token existed,
  the fleet was already trading another one, where it made most of its gain. "Funded 7.6 hours before creation" is true and says nothing about
  this token. It was selected because the author had traded it.
- **It is not a large early buyer.** Buyers 134 to 148, 2.5 minutes in, at about 0.2 % each. The deployer bought 4.44 % first.
- **Its behaviour on this token was to lose money.** A fleet with inside knowledge of this launch is not what these trades show.

## Why the two collections differ

- **Collection A**, `data/split/all_buyers_g2y.json`: every buyer of the curve, kept if funded directly by the gateway. 10 wallets: 9 of the 15, plus
  the deployer, funded by the gateway after the token through a relay. Its 90 unreadable buyers hid the other six.
- **Collection B**, `data/trace_h2w6/e1, e2`: the first 40 buyers only, and their funding. The 15 rank 134 to 148, so none could be there.
  Only the deployer `ApBXF9f1…`, rank 1, is in both.

**Verdict: no contradiction.** Same token, different buyers, by construction. The dossier's own ACID lesson about first-40 limits applies here too.
Buyer counts still differ and are not fully reconciled: 184 wallets with a buy TradeEvent here, 183 in `e6`, 223 distinct wallets in A, whose counting
rule was not rebuilt. Ranks inside a slot also differ from `e6`; this report orders by `transactionIndex`, the chain's own order.

## Does the common wallet connect the two collections?

`ERGbjcz9…`, history read to its start: 1,558 transactions, 2024-11-12 to 2025-01-30, 2,825 SOL in from 404 sources, 2,725 SOL out to 230.

- **No direct link.** None of collection B's 40 first buyers, nor the deployer, nor its relay `8RU58K…` ever pays it or receives from it.
- **One indirect link, weak.** `G9X7F4Jz…` funded two of the early fleets of collection B, and it pays `ERGbjcz9…` 1,491.80 SOL in 41 transfers of round
  amounts from 2024-11-20 to 2024-12-16. But it is a very active wallet, about 6,700 transactions a day and 759 destinations in the 10.75 hours measured.
  A shared counterparty of that size is not evidence of a shared owner. (`EXPLORATORY_HYPOTHESIS`)
- **It is a pass-through.** Most of its SOL leaves to `AwzntLka…` (1,576.95 SOL, 72 transfers), and the fleet's last sweep goes straight on to `5x7FPWyC…` (97 SOL
  within hours). It also receives 101.19 SOL directly from the gateway. Those wallets were not read further, so where this capital ends is `UNRESOLVED`.

## Rarity

Same-amount bursts are not rare at this gateway, and neither is linked behaviour: [gateway bursts](../gateway_bursts/README.md), run with a plan
committed first. This case is not an exception to them, and it can't serve as an example of one operator either. The amount 2.9768156 SOL was paid 1,753
times over 49 days in the frozen study's sample, 1 of 9 sampled bursts at this amount showing the same strict signature.

In its own day it stands out. The gateway's whole 2024-12-13 was read for this report ([gateway_day_2024-12-13.json](gateway_day_2024-12-13.json), complete: 7,189
transactions, 1,893 payouts of at least 1 SOL):

- 39 payouts at this exact amount that day, to 38 wallets. The fleet is 15 of them, so the amount alone does not point to the fleet.
- During the fleet's 380 seconds, the gateway made 18 payouts of at least 1 SOL, and **15 of the 18 were these**. Nobody else got this amount in that span.
- Four bursts that day under the rule of the burst test, sizes 25, 17, 15 and 10. This one is not the largest.

So: a real concentration in time, and not a unique event. Coming through the gateway in one burst says nothing on its own about who paid, as a custodial
swap's internal ledger is not on chain.

## Limits

Transfers below 0.01 SOL are not in the tables above. The fleet's other tokens were not traced to their deployers, so who launched them is not
known here. Nothing here identifies a person.
