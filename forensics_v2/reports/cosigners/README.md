# Very active co-signing wallets: one network, or a shared service?

Plan committed before reading: [../../docs/PLAN_cosigners.md](../../docs/PLAN_cosigners.md). Figures:
[results.json](results.json), post hoc in [posthoc.json](posthoc.json). Wallet-level rows stay off the repository. Nothing at or
after 2026-09-22 00:00 UTC was read, and no price or outcome file was opened.

**Not settled. These wallets do not work only for the known operators. But the test written in advance turned out to be a poor
separator, because most of the "other signers" it counted are disposable keys. The label "shared execution service" from that test
should not be quoted without this sentence.**

## Sample

106 co-signers (the count in `funder_network/results.md`, rebuilt from the frozen table), of which 16 reach two operators or more,
against the 25 other very active wallets, which are all the controls there are. Eight windows from 2026-08-21 to 2026-09-21, at
most 100 transactions each: 29,137 transactions, 10,480 credits, read with no failure.

## The pre-registered verdicts

| Group | "Shared execution service" | "Private to the operators" | Not separated | No activity in windows |
|---|---:|---:|---:|---:|
| All co-signers (106) | 69 | 0 | 35 | 2 |
| Reaching 2 operators or more (16) | 10 | 0 | 6 | 0 |
| **Controls (25)** | **16** | 0 | 3 | 6 |

No wallet is private to the operators under the rule. But most controls also get the service label, so the label does not separate
co-signers from very active wallets in general.

Measures against the controls (medians, permutation p, Bonferroni at 0.0056):

| Measure | Co-signers | Controls | p | Passes |
|---|---:|---:|---:|---|
| Share of its transactions it signs | 0.97 | 0.92 | 0.0003 | yes |
| Top 10 share of other signers | 0.32 | 0.19 | 0.0003 | yes |
| Distinct program sets | 7 | 4 | 0.0001 | yes |
| Share of the top program set | 0.55 | 0.76 | 0.0002 | yes |
| Share matching the four-signer sweep | 0.53 | 0.66 | 0.0007 | yes |
| Distinct other signers | 235.5 | 207 | 0.51 | no |
| Known operators among other signers | 1.1 % | 1.0 % | 0.76 | no |
| Distinct destinations | 58 | 45 | 0.14 | no |
| Share of the top destination | 0.19 | 0.28 | 0.044 | no |

## What the plan did not foresee (post hoc, descriptive)

Written after the verdicts and after reading the numbers above.

- **Most other signers are disposable.** Per wallet, a median of 202 signatures come from signers whose balance does not change, over
  198 transactions. So "distinct other signers" mostly counts throwaway keys of the sweep tool, and the threshold of 100 is met for a
  reason that has nothing to do with having many clients.
- **Counting those who actually pay.** Median per co-signer in the windows: 36.5 paying wallets, 2.5 of them known operator wallets.
  Known operators supply a median 20.7 % of the SOL received, against 5.5 % for the controls.
- **Shared counterparties.** 697 of 2,729 payers (26 %) pay two wallets of the set or more, and 861 of 3,998 destinations (22 %) receive
  from two or more. The most shared destination receives from 79 of these wallets. There are 33 direct payments between them.

## Answers to the questions asked

| Question | Answer | Level |
|---|---|---|
| Do they co-sign only for our operators? | No: known operators are a minority of payers | `ONCHAIN_VERIFIED` on the sample, known list only |
| Do they serve many unrelated wallets? | Dozens of payers per wallet in eight days of reading. Unrelated is not shown: an unknown payer may be an unknown wallet of the same operator | `UNRESOLVED` |
| Same technical schemes? | The four-signer sweep is about half their transactions, and more for controls. Not specific to them | `ONCHAIN_VERIFIED` on the sample |
| Do destinations converge? | Partly: one in five destinations is shared, one reaches 79 wallets | `ONCHAIN_VERIFIED` on the sample |
| Is capital separated by operator? | Not tested at that level here | `UNRESOLVED` |
| A common treasury? | Not shown. A destination shared by 79 wallets could be an exchange or a platform; it was not read | `EXPLORATORY_HYPOTHESIS` |
| A shared execution service? | The plan's test leans that way but does not discriminate. One network and a key-holding platform still both fit | `UNRESOLVED` |
| New operators through these wallets? | 2,729 payers seen, most not on the known list. Being a payer does not make one an operator, and none is named here | `EXPLORATORY_HYPOTHESIS` |

A shared signing authority is not evidence of one human owner, and nothing here identifies anyone.

## Next test, to fix in advance

Replace "distinct other signers" by distinct paying wallets, measure persistence over windows, read the most shared destinations, and
classify payers by their own funding. The known list covers only the 24 operators of the study, which limits every share above.
