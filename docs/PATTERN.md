# The funding-dispatch pattern: what is on chain, token by token

**What this chapter answers.** One question, and only that one: **is the funding pattern present on
the tokens where it was said to be present?** This is a presence test on a named list of tokens. It
is not a prevalence estimate, it is not a comparison against other tokens, and it does not attempt
to explain why any token rose. Those are separate questions, answered — and in one case answered
negatively — in [`SPLIT_PHASE1.md`](SPLIT_PHASE1.md).

Everything below regenerates from committed files with `python3 code/a5_author_pattern.py`. No
network, no key.

> Every address, amount and timestamp quoted is a public technical identifier, verifiable on any
> Solana explorer. Nothing here attributes intent, identity or wrongdoing to any person or company.

---

## The pattern, stated precisely

Four properties, required together:

1. **Fresh wallets.** The buying wallet was created shortly before it buys — no prior history.
2. **A common amount.** Several such wallets receive amounts equal to within 0.1 %.
3. **In one burst.** Those payments land close together in time.
4. **Then they buy.** The wallets appear among the first buyers on the token's curve.

Two tiers are reported, because the difference between them is the honest measure of how much the
answer depends on a loose reading:

| tier | rule |
|---|---|
| **broad** | ≥ 2 wallets, within a 6-hour window |
| **clear-cut** | **≥ 3 wallets, within 120 seconds** |

Two wallets receiving a common round amount five hours apart is a coincidence any active week
produces. The same amount reaching three or more fresh wallets inside two minutes is a dispatch.

---

## Result

**The pattern is present on 8 of 15 traded tokens under the broad rule, and on 6 of 15 under the
clear-cut rule.** The reference case is recovered by the detector, which is the positive control:
a detector that cannot find the case it was built from is broken, not informative.

| token | first buyers | genesis reached | fresh wallets | clusters | largest | broad | **clear-cut** |
|---|---:|---:|---:|---:|---:|:-:|:-:|
| `CHOCO` | 40 | 29 | 28 | 3 | **20** | ✅ | **✅** |
| `BLT` | 40 | 26 | 25 | 4 | 5 | ✅ | **✅** |
| `h2w6gm6jz` | 40 | 21 | 20 | 3 | 5 | ✅ | **✅** |
| `ODIN` *(reference case)* | 35 | 12 | 12 | 2 | 4 | ✅ | **✅** |
| `VISUALIZE` | 40 | 19 | 13 | 1 | 3 | ✅ | **✅** |
| `LEXICON` | 40 | 21 | 14 | 2 | 3 | ✅ | **✅** |
| `sumiko` | 40 | 20 | 20 | 2 | 2 | ✅ | – |
| `QAMI` | 40 | 23 | 19 | 1 | 2 | ✅ | – |
| `RAO` | 40 | 29 | 25 | 0 | 0 | – | – |
| `MIKU` | 40 | 24 | 20 | 0 | 0 | – | – |
| `SAFFRON` | 40 | 25 | 18 | 0 | 0 | – | – |
| `OPTIMUS` | 40 | 23 | 16 | 0 | 0 | – | – |
| `ACID` | 40 | 20 | 15 | 0 | 0 | – | – |
| `POLMRKTBOT` | 40 | 21 | 13 | 0 | 0 | – | – |
| `symx` | 40 | 16 | 13 | 0 | 0 | – | – |

### The dispatches themselves

| token | dispatch | span | when (UTC) |
|---|---|---:|---|
| `CHOCO` | **20 wallets × 0.100000000 SOL** | **0 s** | 2024-10-10 10:06:59 |
| `CHOCO` | **20 wallets × 1.050000000 SOL** | **0 s** | 2024-10-10 10:07:26 |
| `CHOCO` | **20 wallets × 0.300000000 SOL** | **0 s** | 2024-10-10 13:31:44 |
| `ODIN` | 4 wallets × 3.000000000 SOL | **0 s** | 2024-11-17 23:55:52 |
| `h2w6gm6jz` | 5 wallets × 2.000000000 SOL | 73 s | 2024-12-13 07:20:16 |
| `BLT` | 5 wallets × 10.000000000 SOL | 49 s | 2024-11-14 13:20:22 |
| `BLT` | 4 wallets × 2.000000000 SOL | 79 s | 2024-11-19 21:31:19 |
| `VISUALIZE` | 3 wallets × 5.000000000 SOL | 42 s | 2024-09-13 18:11:38 |
| `LEXICON` | 3 wallets × 0.350000000 SOL | 29 s | 2024-12-24 05:10:03 |

A **0-second span** means the payments share a single transaction. CHOCO shows three such
fan-outs on one morning, each reaching twenty fresh wallets at an identical amount to nine decimal
places, the first two twenty-seven seconds apart. That is not a coincidence in any tolerable sense
of the word; it is one account paying twenty others in one instruction, three times.

### One correction to the account, from the data

Every cluster found on the buying wallets is a **round** amount — 0.1, 0.3, 1.05, 2, 3, 5, 10 SOL —
not a conversion output like 1.393934883 SOL. The two are one hop apart on the same chain: a
conversion pays a distributor, the distributor pays the wallets in round parts. What is visible at
the buying-wallet layer is therefore the **distributor link**, and the swap output sits one level
upstream. The hub traced in [`SPLIT_PHASE1.md`](SPLIT_PHASE1.md) §2 behaves exactly that way:
it receives an amount and pays the same amount out within the minute, cut into round parts.

This matters for anyone trying to watch for the pattern live: the round amounts are the observable
signal at the wallet layer, and the swap-shaped amount is what identifies the layer above.

### Robustness

The two free parameters are swept rather than chosen. The freshness cut changes nothing at all
between 1 and 30 days; the amount tolerance is what moves the count:

| tolerance | 1e-4 | 1e-3 | 1e-2 | 1e-1 |
|---|---:|---:|---:|---:|
| tokens with the pattern (broad) | 8 | 8 | 12 | 12 |

At 1 % tolerance the count rises to 12, but 1 % is loose enough to merge genuinely different
amounts, so the reported figure is the conservative one. The headline count of 8 holds across the
strict half of the range, and the clear-cut count of 6 rests on same-transaction or sub-two-minute
dispatches that no tolerance choice affects.

---

## What this establishes, and what it does not

**Established.** The dispatch mechanism is real and it is on chain. Fresh wallets funded with
identical amounts in a single burst, then buying early on the curve, is documented on **6 of 15**
traded tokens under the strict rule — including three same-transaction fan-outs of twenty wallets
on one of them. These are observations with transaction-level evidence, and they stand.

**Not established, and not claimed here.**

- **Nothing about why a token rose.** This chapter measures funding structure, not causation.
- **Nothing about prevalence.** The token list was selected on outcome, so it cannot support any
  "X % of launches" statement — see `code/a4_selection_bias.py`.
- **Nothing about exclusivity.** The comparison against graduated tokens that were never traded is
  in [`SPLIT_PHASE1.md`](SPLIT_PHASE1.md) §6, and it does **not** show the mechanism to be
  restricted to this list. Present here, and also present elsewhere: both are true, and the second
  does not erase the first.
- **Nothing about intent.** A wallet paying twenty others in one transaction is a measured fact
  about an instruction on a public ledger.

The seven tokens where the pattern is absent are reported as absent. Six symbols from the same
period could not be resolved to a mint with confidence and are excluded rather than guessed;
resolving them could move the count in either direction.
