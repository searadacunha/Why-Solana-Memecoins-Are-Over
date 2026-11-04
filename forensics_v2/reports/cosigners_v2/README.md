# Co-signers, second test: those who actually pay

Plan committed before this reading: [../../docs/PLAN_cosigners_v2.md](../../docs/PLAN_cosigners_v2.md). Figures: [results.json](results.json). Code: `investigations/cosigners_v2.py`. Same 131 wallets and eight windows as the first test, no credit spent, no price or outcome file opened. Wallet-level rows stay off the repository.

**Still not settled, and this test does not separate co-signers from controls either: Fisher p = 0.32 on the label it was meant to test, where the plan required under 0.05. What it adds is one measured fact: payers rarely come back. The median co-signer has no paying wallet seen on two of the eight days.**

## Verdicts, by the rule written in advance

| Group | Looks like a service | Looks private to a few parties | Not separated | No payer |
|---|---:|---:|---:|---:|
| Co-signers (106) | 4 | 25 | 75 | 2 |
| Controls (25) | 2 | 8 | 9 | 6 |

By the plan, these labels count only if controls do not get them at the same rate. 3.8 % against 8 %: they do, so the labels mean nothing here. Unlike the first test, which called 69 of 106 a service, this rule calls almost none one.

## Measures

Medians, 10,000 permutations, Bonferroni threshold 0.01.

| Measure | Co-signers | Controls | p | Passes |
|---|---:|---:|---:|---|
| M1 persistent payers | 0 | 1 | 0.0010 | yes |
| M2 share of SOL from persistent payers | 0 % | 5.9 % | 0.0001 | yes |
| M3 share of persistent payers also paying another wallet of the set | 0 % | 0 % | 1.00 | no |
| M4 share of SOL from known operators | 20.7 % | 5.5 % | 0.12 | no |
| M5 share of SOL from its five largest payers | 65.4 % | 59.1 % | 0.20 | no |

## What can be said

- **Co-signers' money comes from wallets that do not return,** even less than for other very active wallets. This fits disposable wallets, whoever runs them. It does not fit a service with regular clients, as far as eight days can show.
- **Known operators weigh more for co-signers,** but not significantly here.
- **A shared service against one network:** still `UNRESOLVED`. A wallet can hold keys for many clients who each pay once, and an operator can use a new wallet every time, and these two look alike in this measure. A payment alone cannot tell them apart.

## Limits

Each window is the first 100 transactions of one day, for eight days over a month, so "does not return" means not seen again in that sample. Very active wallets are the most undersampled.
