# Why Solana Memecoins Are Over

Between **October and December 2024**, I withdrew **$237,137.87** trading memecoins on **pump.fun**.

I stopped when the pattern I was exploiting disappeared.

I didn't stop because the market became impossible to understand.

I stopped because the mechanism had changed.

So I did what I had been doing from the beginning: I went back to the chain and looked for what replaced it.

This repository is the result.

It is part trading history, part on-chain investigation, and part attempt to prove myself wrong.

---

## What this repository demonstrates

This is not a tutorial and it is not a collection of screenshots.

It is a reproducible blockchain investigation built from transaction-level data.

The work covers:

* **Blockchain forensics**
* **On-chain transaction tracing**
* **Wallet clustering and relationship analysis**
* **Funding-flow reconstruction**
* **Pattern and anomaly detection**
* **Transaction monitoring**
* **Hypothesis testing and falsification**
* **Manual transaction verification**
* **Python-based data analysis**
* **Reproducible research**
* **On-chain financial-flow reconstruction**

The central question was simple:

> **What changed in the way successful Solana memecoins were accumulated, and could that change be measured directly on-chain?**

---

# Disclosure

The pattern documented below is one I identified and traded myself, lawfully, under my own name.

Starting capital was roughly **$400**; withdrawals over October–December 2024 came to **$237,137.87**, a multiple of roughly **590×**.

The withdrawal figure is reconstructed directly from the blockchain by `code/expl_ledger.py` and reproduces from the committed artefacts.

The starting capital is different: it is a Phase-0 recollection from before the measured window and is explicitly marked as unsourced. The 590× figure is therefore arithmetic based on those two numbers and inherits the same limitation.

I consider that distinction important.

Where this repository can measure something, I measure it.

Where it cannot, I say so.

When the trading stopped, I turned the same methodology against my own claims. `docs/PITFALLS.md` documents fifteen competing explanations that were tested, corrected or retired. Results that could not be regenerated from the published data were deleted rather than kept.

That standard is intentional.

---

# Abstract

In 2024, some of the Solana memecoins that performed strongly followed a surprisingly repeatable accumulation pattern.

Fresh wallets appeared shortly before a token launch.

They were funded through **ChangeNOW**.

They accumulated meaningful portions of supply shortly after launch.

And because the accumulation happened publicly, somebody watching the chain closely could detect it early enough to participate.

I did.

The interesting part came later.

The wallets multiplied.

The funding pattern disappeared.

The public signal became harder to observe.

So I rebuilt the investigation from the blockchain and measured what changed.

The repository contains the data, scripts, validation procedures, competing hypotheses and transaction-level evidence behind that investigation.

---

# Act I — The 2024 Pattern

Before a pump.fun token existed, the wallets participating in it often already did.

Typically, they were:

* created the same day as the token
* funded through ChangeNOW
* holding nothing else
* buying immediately after launch
* accumulating meaningful percentages of supply

The funding trail led back to a single address:

`G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t`

a hot wallet attributed externally to the swap service **ChangeNOW**.[1]

ChangeNOW broke the direct on-chain trail.

The wallets therefore appeared unrelated.

They weren't.

The signal was in the funding behaviour.

Large SOL transfers reached multiple fresh wallets in **identical amounts, down to nine decimal places**.

One example:

* **9 wallets**
* all created that morning
* all funded with exactly **2.976815600 SOL**
* all funded within **343 seconds**
* token launched **7.6 hours later**

The interesting question was no longer:

> "Who is buying this token?"

It was:

> **"Why were these wallets funded in this exact configuration before the token even existed?"**

Once one wallet bought roughly **2% of supply** — around 20 million tokens — the others frequently followed.

That created something unusual in an otherwise chaotic market:

**a measurable, observable accumulation pattern.**

---

# Exploiting the Pattern

Once I understood the pattern, I traded it.

The configuration I looked for was specific:

> A ChangeNOW-funded wallet buying at least **2% of supply** on a fresh pump.fun launch.

When that happened, I bought too — **1% of supply at most**, deliberately small enough not to become part of the signal.

The thesis was simple:

If the first wallet was part of a coordinated accumulation, the remaining wallets should follow.

The chain became the order-flow signal.

I did not need to know who controlled the wallets.

I needed to observe what they repeatedly did.

After every large gain, I moved to a fresh wallet. The objective was to avoid becoming another visible participant in the pattern I was exploiting.

The position was then managed from the operators' own behaviour: accumulation, curve shape, subsequent buying and eventual exhaustion.

The important point for this investigation is not the trading strategy itself.

It is that **the strategy depended on information being publicly observable on-chain.**

And eventually, that information stopped being observable.

---

# Results

The results below are reconstructed from the blockchain.

| Metric                                     |             Result |
| ------------------------------------------ | -----------------: |
| Withdrawn, Oct–Dec 2024                    | **1,190.6957 SOL** |
| USD value at each transfer's own day price |    **$237,137.87** |
| Incoming transfers, Oct–Dec 2024           |            **245** |
| Distinct sending wallets                   |             **74** |
| Example trades in documented sample        |             **19** |
| Full window through 2 Feb 2025             |    **$244,315.58** |

The money rows are the strongest measurements.

Each transfer is valued using the SOL close of its own UTC day rather than a single average price.

The ledger also closes internally:

**1,226.4663 SOL** arrived over the full window against **1,226.4566 SOL** swept out to the exchange.

The transfer and wallet counts are more method-dependent. A transfer represents a successful transaction carrying a positive balance delta, while the sending wallet is attributed using the largest opposing delta in that transaction.

Those definitions are documented rather than hidden.

---

# The evidence is public

The deposit address used for the reconstruction is published:

`6tmiM84AxMzmXzRByq7m1dgNkHtn9wp671e1GMe2ZmWU`

It is my KYC'd exchange deposit address.

Publishing it was deliberate.

It means the central financial result does not depend on trusting a screenshot or trusting me.

Anyone can query the address on-chain and reproduce the ledger.

The reconstruction is:

`code/expl_ledger.py` → `docs/out/expl_ledger.json`

The 74 sending wallets are published as a count rather than as a curated identity list. Where the methodology cannot establish ownership, the repository does not claim ownership.

For example, four of the 74 are resolved by the same methodology as third-party exchange infrastructure and are therefore recorded as `NON_ETABLI` rather than assigned to an individual.

That distinction matters in blockchain investigations:

**transactional relationship is evidence; ownership attribution requires additional evidence.**

---

# Act II — Closing the Leak

That was the trade from my side.

From the operators' side, the model had an obvious weakness:

**it was observable.**

Funding happened hours before launch.

Accumulation happened slowly enough to detect.

The wallets became visible.

And anyone watching the chain could buy alongside them.

As the wallet inventory grew into the thousands, the original funding mechanism became less useful.

The public funding stage disappeared.

The question was no longer:

> "Can I detect the accumulation?"

It became:

> **"Can accumulation still be detected before the public gets there?"**

That is what led to the next investigation.

---

# Act III — What Replaced It

What replaced the previous pattern does not simply shorten the observation window.

**It removes it.**

The new mechanism I identified is what I call the **group snipe**:

instead of accumulating publicly after launch, a group purchases essentially the entire bonding curve in the token's creation slot itself.

The measurement was performed across **42/42 manually verified launches**, with each transaction checked individually.

The observed signature:

* approximately **85 SOL**
* approximately **79% of supply**
* purchased inside the token creation slot
* **zero public bonding-curve purchases beforehand**

I then tested the same signature on a **separate frozen sample** of 70 tokens reaching at least $500k market cap.

**58 of 70 (82.9%)** exhibited the same signature.

This separation between the discovery sample and the frozen sample is deliberate.

It prevents the measurement from simply becoming a collection of examples selected after seeing the result.

---

# Real-World Example

One instance is the launch associated with **ANSEM ("TheBlackBull")**:

Mint:

`9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump`

Created:

**2026-06-16 21:05:48 UTC**

Creation slot:

**426930467**

Using the same measurement scripts:

* **85.007 SOL** purchased in the creation slot
* **84.74 SOL** purchased by a single wallet
* only **two buyers**
* **sixteen signatures**
* no bonding-curve supply left for public buyers

More importantly, both wallets were already present in the repository's historical wallet catalogue before this token existed.

One was a repeat operator observed across multiple tokens.

The other was classified as shared infrastructure.

The alert triggered immediately after creation.

This is the point where the repository moves from historical analysis to something closer to **transaction monitoring**:

a behavioural signature can be defined, measured, and triggered on a new event.

---

# Why Solana Memecoins Are Over

In 2024, outsiders could observe accumulation.

That observation created the opportunity.

By 2026, the same type of activity could happen inside the creation slot itself.

The important change was therefore not simply that memecoins became "harder".

The information advantage changed.

The public went from seeing the accumulation process to seeing the market **after the accumulation had already happened**.

The measured data supports that structural change:

* **42/42** manually verified launches showed the same creation-slot accumulation signature
* **58/70 (82.9%)** showed it in the independent frozen sample
* approximately **79% of supply** was acquired inside the creation slot in the verified launches

The broader market data is consistent with a significant contraction in the memecoin environment, but those macro figures are external measurements rather than outputs of this repository.[3]

The conclusion I can defend from the on-chain evidence is narrower:

> **The observable accumulation pattern that made the 2024 strategy possible was replaced by a much less observable launch-time mechanism.**

The public wasn't simply outcompeted.

**The observable order flow changed.**

---

# What I Tried to Prove Wrong

A blockchain pattern is not interesting because it looks convincing.

It is interesting if it survives attempts to explain it away.

`docs/PITFALLS.md` contains fifteen competing explanations and the tests used against them.

Among the questions I forced the analysis to answer:

* Could exchange infrastructure create the apparent clustering?
* Could batched transactions distort the counts?
* Could unrelated wallets happen to receive identical funding?
* Could bots explain the synchronization?
* Could the observed wallets simply be infrastructure?
* Does temporal proximity actually establish coordination?
* Can wallet activity establish common ownership?
* Can the result be reproduced from frozen data?

Some hypotheses survived partially.

Some were rejected.

Some claims were narrowed.

Some measurements were removed.

That is part of the result.

---

# Methodology

The investigation is built around a simple principle:

> **Every important claim should be traceable to an artefact, a transaction, or an explicitly identified external source.**

The workflow is approximately:

```text
Raw on-chain data
        ↓
Transaction normalization
        ↓
Wallet identification
        ↓
Funding-flow reconstruction
        ↓
Wallet clustering
        ↓
Temporal / behavioural analysis
        ↓
Hypothesis testing
        ↓
Manual verification
        ↓
Reproducible result
```

The repository therefore separates:

**Measured facts**

from

**interpretations**

from

**external claims**

from

**unsourced historical recollections**.

That separation is intentional.

---

# Repository Structure

| Path                   | Description                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------- |
| `docs/PITFALLS.md`     | Fifteen competing explanations, the tests designed to break them, and what survived |
| `docs/METHODOLOGY.md`  | Definitions, populations, validation protocol and declared limitations              |
| `docs/RESULTATS.md`    | Complete 2026 measurements with an English executive summary                        |
| `docs/PATTERN.md`      | Funding distributions token by token with detected bursts                           |
| `docs/EXPLOITATION.md` | Trading methodology, automation, receipts and on-chain totals                       |
| `docs/SPLIT_PHASE1.md` | 2024–2025 split analysis with controls and null models                              |
| `code/`                | One script per measurement                                                          |
| `data/`                | Versioned derived datasets                                                          |
| `figures/`             | Figures regenerated from the analysis scripts                                       |

---

# Author

**Benjamin Da Cunha**

I published this investigation under my real name deliberately.

The commit history is authored under it.

The trading screenshots retain the `teamdacunha` referral handle.

The **$237,137.87** withdrawal figure is reconstructed from my own exchange deposit address.

The chain, the code, the artefacts and the person behind the investigation are therefore connected.

I am not presenting this repository as a generic software-engineering portfolio.

I am presenting it as evidence of a specific capability:

> **I find patterns in blockchain data, build hypotheses around them, try to break those hypotheses, and turn the surviving evidence into a reproducible investigation.**

That is the work I want to keep doing.

---

# Footnotes

1. A 2025 external study on Solana mixers observed funds routed through ChangeNOW arriving at the address used in this investigation. An earlier public attribution also associates the address with the service. The repository measures what leaves the address; it does not independently establish who operates it.

2. External sources document the ANSEM/Black Bull launch. The wallet measurements themselves come from this repository. Where a value is not measured by an artefact in this repository, it is explicitly marked as unsourced.

3. The graduation-rate and Solana-fee figures are network-wide aggregates from an external source. They are included as context, not as measurements produced by this repository.
