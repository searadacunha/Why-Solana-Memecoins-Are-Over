# Technical Results: Microstructure of Pump.fun Launches

> **Seven-day measurement of pump.fun fast-graduation launches on Solana.**
>
> This document reports three empirical results:
>
> 1. **Launch mechanics:** the bonding curve is acquired inside the token's creation slot, before an external buyer can transact.
> 2. **Operator clusters:** repeated buyer structures exist, but graph connectivity is heavily distorted by shared infrastructure.
> 3. **Buyer economics:** after the initial move, systematic entry and exit policies produce negative results across the tested sample.
>
> The analysis deliberately separates what is **measured** from what is **inferred**, and what is **not established**.

---

## Executive Summary

### 1. Launch mechanics

Across **42 launches reconstructed transaction by transaction**, the bonding curve is bought inside the **creation slot itself**.

* Median capital committed: **85.2 SOL**
* Median supply acquired: **79.0%**
* Curve purchases before the creation slot: **0/42**
* Median transfer of the acquired position: **t+17.5 s**
* Median market cap:

  * Launch: **~$2,158**
  * First point at which an external buyer can transact: **~$53,985**
  * Increase before the market opens: **×25.0**

On a separate frozen sample of **70 tokens that reached ≥$500k ATH**, **58/70 (82.9%)** carry the same creation-slot signature, with a Wilson 95% CI of **72.4–89.9%**.

This does **not** establish that the signature causes tokens to succeed. The ≥$500k population is selected on outcome, and the tokens without the signature actually reached a higher median ATH in that sample.

### 2. Operator clusters

A token–token graph built from shared early buyers initially produces a giant component containing **180/282 tokens (63.8%)**.

That structure is largely explained by a small number of highly reused infrastructure addresses.

Removing nine such addresses reduces the giant component to:

**180 → 57 tokens (63.8% → 20.2%)**

After cleaning, six disjoint clusters remain, covering:

**76/282 tokens = 27.0%**

Their intra-cluster wallet reuse ranges from **0.904 to 1.000**, compared with a base rate of **0.0191**.

However, the graph does **not** provide predictive power over subsequent token performance. Operator identity explains the tested outcome at **p = 1.000**, and the identified clusters perform below the market baseline.

### 3. Cost to a buyer

At first external visibility, the move is already substantially advanced:

* **21.3%** of tokens have already reached their ATH.
* **43.8%** reach ATH within 60 seconds.
* **50.0%** reach ATH within 120 seconds.

Across **15 exit policies** applied to **196 tokens / 20 clusters**:

* **15/15** have negative mean returns.
* **12/15** have negative median returns.
* **0/15** have a cluster-bootstrap 95% CI above zero.
* Mean return across policies: **−11.3%** per round trip.

## At longer horizons, the median multiple falls to **0.20× at +24h**, or **0.03×** when tokens without a tradable candle are counted as zero.

# 0. Corpus and Scope

## 0.1 Capture window

**Window:** 2026-06-27 → 2026-07-04
**Duration:** 7 UTC days
**Scope:** pump.fun launches classified as *fast-grad*, i.e. rapid graduation to the AMM.

All addresses and transaction signatures referenced here are public technical identifiers verifiable on a Solana explorer.

This document makes **no attribution of identity, intent, or person**. It describes observable market microstructure.

## 0.2 Corpus

| Quantity                                          |       Value | Source                                |
| ------------------------------------------------- | ----------: | ------------------------------------- |
| Capture files                                     |         645 | `data/v01_corpus.json`                |
| Captures with swap flow                           |         293 | idem                                  |
| Captures with identified early buyers             |         282 | idem                                  |
| Raw swaps                                         | **511,508** | idem                                  |
| Distinct addresses                                |      91,353 | idem                                  |
| Distinct sniper wallets                           |       1,616 |                                       |
| Sniper-wallet occurrences                         |       2,894 |                                       |
| Launches reconstructed transaction-by-transaction |      **42** | `data/v05`, `v06`, `v07`              |
| Tokens ≥$500k re-audited on-chain                 |      **70** | `data/v09_signature_gros_tokens.json` |

## 0.3 Published-count discrepancy

A separate output, `docs/out/m1_corpus.json`, reports:

* **476,847 swaps**
* **90,979 addresses**

The raw recount used in this document gives:

* **511,508 swaps**
* **91,353 addresses**

The difference is approximately 7%.

`m1` applies an additional filter whose definition is not documented in its header. Both figures remain published rather than silently reconciled.

Importantly, **no result in this document depends on the disputed total**; the count is used only to describe corpus size.

## 0.4 Sensor coverage and selection

The capture system does not observe the complete fast-grad market.

`floor_capture` observes:

**282 / 749 = 37.7%**

of fast-grad tokens in its own window.

Captured tokens are also more likely to be winners:

* ATH ≥$200k among captured tokens: **33.7%**
* ATH ≥$200k among non-captured tokens: **25.5%**

Combined with the cluster-attribution rate of **18.1%**, the effective end-to-end coverage is estimated at:

**6.8%**

The corpus is therefore **not representative of the full flow**. It is biased toward launches that entered the capture pipeline successfully, and all results must be interpreted accordingly.

---

# 1. Reconstructing the Launch Mechanism

## 1.1 The creation-slot event

On the 42 launches reconstructed transaction by transaction, the bonding curve is acquired essentially in full **inside the token's creation slot**, before an external buyer can transact.

### Table A — Creation-block measurements

| Measurement                     |                 Median |        Q1–Q3 |      Min–Max |
| ------------------------------- | ---------------------: | -----------: | -----------: |
| SOL committed in creation block |              **85.21** |  83.12–85.72 |  79.49–87.46 |
| Total supply acquired           |             **78.95%** | 78.31–79.09% | 76.78–79.25% |
| Curve share captured            |                 79.09% |            — | 77.60–79.29% |
| Curve SOL captured              |             **98.72%** |            — |            — |
| Curve purchases before block    |                  **0** |            — |  max = 0 SOL |
| Intra-core time gap             |      **0 s / 0 slots** |            — |        42/42 |
| Ticket CV                       |                 0.0265 |            — |            — |
| Creator dev-buy                 |              0.068 SOL |            — |            — |
| Wallets in creation block       | 4 in 33 cases / 5 in 9 |            — |            — |

Two measurements are particularly important.

### No pre-block purchase

There are **zero curve purchases before the creation block in all 42 launches**.

This means the mechanism is not simply a matter of executing faster than competitors. There is no measurable purchase window between token creation and the observed curve acquisition.

### No intra-block gap

The core purchases occur at:

**0 seconds / 0 slots**

on all 42 launches.

The four or five purchases therefore occupy the same Solana slot. A conventional external observer cannot insert a transaction between those observed purchases merely by reducing monitoring latency.

---

## 1.2 The price staircase

The measured market-cap progression is:

| Stage                             | Median market cap | Relative to launch |
| --------------------------------- | ----------------: | -----------------: |
| Launch                            |        **$2,158** |                 ×1 |
| Creation-block execution          |            $8,321 |               ×3.9 |
| After final creation-block ticket |           $26,093 |              ×12.1 |
| AMM open / first external buyer   |       **$53,985** |          **×25.0** |

The median ratio between AMM-open market cap and creation-block execution is:

**×6.54**

with **40/42 launches at ≥×3**.

An independent measurement on the 293 captures produces a median first externally observable market cap equivalent to:

**×25.2**

relative to the 27.96 SOL launch constant.

The same measurement estimates that **90% of the launch-to-peak log-run has already been consumed at that point**, in median terms. The two measurements differ by only 0.2× despite using separate code paths.

### Interpretation

The observable economic effect is therefore not simply:

> “The actors bought early.”

The stronger measured statement is:

> **The observable external market opens after a substantial portion of the launch repricing has already occurred.**

---

# 1.3 Five End-to-End Verifiable Launches

Five representative launches can be independently verified from their public mint addresses.

| Mint                                           | Cluster | Creation slot | Block wallets |   SOL | Supply acquired | Purchases before |    Block MC → AMM | Transfer |
| ---------------------------------------------- | ------- | ------------: | ------------: | ----: | --------------: | ---------------: | ----------------: | -------: |
| `87QChghgFr2XBNumi2Tg1MJCWHLqoTTT5KThtnDspump` | C1      |   429,307,208 |             4 | 84.94 |          78.05% |            **0** | $8,401 → $122,404 |    23.5s |
| `DuiJLBQbnW7q5DibZNUckqtQbPMpMrXyc81iSNmzpump` | C1      |   429,722,432 |             4 | 85.23 |          79.10% |            **0** |  $8,317 → $60,423 |    14.0s |
| `9hrV5rTGN7s2noUZwo84kpFZKmhsnRuMS6AVMs1upump` | C2      |   429,338,545 |             4 | 82.08 |          77.99% |            **0** |  $8,125 → $52,951 |    16.5s |
| `hCVRw8Qq9e8ZTeGYzWBoY8G5GvhDdkoMDmy4MWypump`  | C3      |   429,414,857 |             4 | 84.81 |          78.84% |            **0** |  $8,304 → $51,938 |    22.0s |
| `ALbvXciC8k4P3G57b4hMRPypvvsc2Rr9K4WucSwLpump` | C4      |   430,477,517 |             4 | 79.49 |          77.45% |            **0** |  $7,923 → $59,736 |    13.0s |

The five tokens have **five distinct creators**.

None of the creators is reused.

This is important because it rules out the simple interpretation that the buyer clusters are the creators of the tokens they purchase.

---

# 1.4 A Repeated Execution Template

During verification, five launches associated with C2 exhibited values identical to the fourth decimal:

* same four ticket sizes
* same token quantity
* same supply share

At first glance, such exact repetition is a plausible data-duplication failure.

The duplication hypothesis was tested.

| Check                                   | Result           | Interpretation                          |
| --------------------------------------- | ---------------- | --------------------------------------- |
| Creators                                | 5 distinct       | Not duplicate records                   |
| Wallet execution order                  | Different on 3/5 | Not duplicate records                   |
| Slots                                   | 5 distinct       | Not duplicate records                   |
| Dev-buy in tokens                       | Identical        | Explains identical starting curve state |
| Distinct `tokens_bloc` values across 42 | 35/42            | Repetition is local                     |

The explanation is a deterministic execution template rather than duplicated data.

The creator dev-buy establishes an identical curve state, after which a fixed ticket ladder expressed in token quantities produces effectively identical SOL costs.

C2's inter-launch coefficient of variation is:

**0.0075**.

---

# 1.5 Position Exit

Across the 42 reconstructed launches:

* **177** creation-block wallets
* **162/177** transfer their acquired position
* **46/177** sell directly
* Median transferred supply: **99.99%**
* Median delay to first transfer: **17.5 seconds**
* Q1–Q3: **13.0–26.2 seconds**
* Range: **0–80 seconds**
* Second-tier collectors: **41**

The dominant pattern is therefore:

**purchase → transfer → secondary liquidation**

rather than:

**purchase → direct sale from the original buyer**

The forensic track measures approximately **119–194 liquidation tranches**, depending on cluster, with individual tranches of approximately 4 SOL spaced around 1.5 seconds apart.

These counts are aggregated per cluster rather than per launch and should therefore be treated as an **order of magnitude**, not as a precise per-launch measurement.

### Wallet age

| Population        |   n | Median age at first snipe |
| ----------------- | --: | ------------------------: |
| Token creator     | 151 |      **0.03 d (~45 min)** |
| Disposable sniper | 267 |                    0.22 d |
| Cluster member    |  58 |                **32.5 d** |

The observed distinction is substantial:

* creator wallets tend to be fresh;
* disposable snipers are also relatively young;
* persistent cluster wallets are generally provisioned well in advance.

One C3 wallet group was created within approximately 50 seconds of one another and was subsequently used **228 days later**.

---

# 1.6 The Signature Among Large Tokens

A separate frozen population of **70 tokens with ATH ≥$500k** was audited independently of the detector.

| Measurement                                 |            Result |
| ------------------------------------------- | ----------------: |
| Median ATH                                  |    **$1,205,423** |
| ≥60 SOL curve buyback inside creation slot  | **58/70 = 82.9%** |
| Wilson 95% CI                               |    **72.4–89.9%** |
| Agreement: ≤30s vs creation-slot definition |         **70/70** |
| Median SOL committed                        |         **85.01** |
| Median buyers in slot                       |                 4 |

The 70/70 agreement is notable:

> Every token whose curve buyback occurs within the tested short window also has that buyback inside the creation slot.

### Three critical limitations

#### 1. The sample is not random

The 70 tokens are the first 70 qualifying tokens in the source file.

The confidence interval quantifies sampling error **within this selected population**. It does not correct for selection bias.

#### 2. The signature does not predict price trajectory

Within these 70 tokens:

* signature present: median ATH **$1.13M**
* signature absent: median ATH **$2.33M**

The tokens without the signature therefore reached a higher median ATH in this selected population.

The signature describes a **launch condition**, not a demonstrated predictor of subsequent performance.

#### 3. This estimates P(signature | large), not P(large | signature)

Because the population was selected on reaching ≥$500k, the measurement cannot answer:

> “What probability does the signature give a token of becoming large?”

It answers the narrower question:

> “Among these already-large tokens, how frequently was the signature observed?”

This distinction is central to avoiding outcome-selection bias.

---

# 1.7 Reconciliation of Two Market-Cap Measurements

Two independent scripts initially produced different AMM-open medians:

* `v05`: **$46,147**
* `v06`: **$53,985**

The discrepancy affected all 42 launches, with individual differences reaching a factor of 100.

The cause was identified:

* `v05` selected the first observed swap;
* some first swaps were dust trades around **0.002 SOL**;
* their implied prices were aberrant;
* `v06` instead takes the median of **PUMP_AMM swaps ≥0.1 SOL during the first 60 seconds**.

`v06` explicitly documents this correction and is therefore the authoritative implementation.

The final document uses the `v06` value of **$53,985**.

This reconciliation illustrates an important principle:

> A reproduced number is not necessarily a validated number. The measurement definition itself must be audited.

---

# 2. Operator Clusters and Graph Analysis

## 2.1 The Infrastructure Trap

A token–token graph was constructed by connecting tokens sharing at least three early buyers.

Before cleaning:

**180 / 282 tokens = 63.8%**

belonged to one giant component.

A naive interpretation would be that a single network spans almost two thirds of the observed market.

That interpretation is incorrect.

A small number of highly reused addresses act as shared infrastructure and bridge otherwise unrelated tokens.

### Infrastructure ubiquity

| Address | Tokens sniped |     Share |
| ------- | ------------: | --------: |
| W1      |           165 | **58.5%** |
| W2      |            99 |     35.1% |
| W3      |            91 |     32.3% |
| W4      |            70 |     24.8% |
| W5      |            44 |     15.6% |

Removing nine infrastructure addresses reduces the giant component:

**180 → 57 tokens**

or:

**63.8% → 20.2%**

The original giant component was therefore substantially a **bridging artefact**.

Two classification errors were also corrected:

* W1 had been classified as a single-mint volume bot, but its last 500 transactions span **45 distinct mints**, with a dominant mint representing only 4.0%.
* `GeBJSHK4…` had been classified as infrastructure even though it is a creator of **51 tokens**, buying its own tokens.

The second error demonstrates the cost of an infrastructure filter that is too broad: it can remove genuine structure along with noise.

---

# 2.2 The Six Surviving Clusters

After cleaning, six disjoint clusters remain.

| Cluster | Core        | Tokens | Wallets / launch | Intra-cluster reuse | Inter-launch CV | Median SOL |
| ------- | ----------- | -----: | ---------------: | ------------------: | --------------: | ---------: |
| C1      | `22vL22Pc…` |     14 |                4 |               0.904 |           0.146 |      84.97 |
| C2      | `339QJtzB…` |     12 |                4 |           **1.000** |      **0.0075** |      80.90 |
| C3      | `2GMhqu3c…` |     10 |                4 |           **1.000** |          0.0118 |      85.10 |
| C4      | `2LLHCtDp…` |      6 |                4 |           **1.000** |          0.0345 |      79.62 |
| C5      | `yHCxHBEa…` |     24 |                1 |           **1.000** |           0.316 |       84.9 |
| C6      | `GeBJSHK4…` |     10 |                1 |           **1.000** |       **0.000** |       84.0 |

Comparison base rate:

**0.0191**

The strongest structural signals are:

* intra-cluster reuse of **0.904–1.000**
* base rate of **0.0191**
* C1 core-pair lift of approximately **×20–×22**
* no shared token between the six clusters
* no shared address between the six clusters
* persistence of the four quad clusters beyond the capture window

The six clusters cover:

**76 / 282 = 27.0%**

of captured tokens.

The remainder is highly fragmented: **1,062/1,183 creators (90%)** launched only one token in the mapped population.

---

# 2.3 What the Clusters Are Not

Across the 42 transaction-level launches:

**42 launches → 42 distinct creators**

The C1–C4 buying clusters have no connection to the wallets creating the tokens they purchase.

This refutes the initial hypothesis that these clusters are simply token creators buying their own launches.

The measured structure is instead consistent with **demand-side actors buying tokens created by others**.

### “Bundle” is not an accurate technical description

The dominant signer represents exactly **1/n** of the observed transactions.

Each wallet signs its own transaction.

There is therefore:

* no duplicated signing;
* no shared fee payer;
* no atomic multi-wallet bundle in the observed structure.

The only atomicity mechanism observed is a single-tip Jito bundle on two clusters.

The historical code terminology retains the word “bundle” for compatibility, but it should not be interpreted as a technical description of the observed transaction structure.

A proposed historical transition from sequential observable purchases to atomic execution is also **not testable** with the available historical depth.

No dating of such an evolution is therefore proposed.

---

# 2.4 Two Software Families, Not Six Proven Operators

Three independent technical dimensions produce the same partition across the four quad clusters:

| Technical axis        | {C1, C3}                   | {C2, C4}             |
| --------------------- | -------------------------- | -------------------- |
| Address Lookup Tables | 100%                       | Partial              |
| Fees / transaction    | 11,500 lamports            | 6,500 lamports       |
| Jito tip              | None                       | Hard-coded recipient |
| Ticket order          | Strictly decreasing, 16/16 | Non-monotonic        |

Two clusters sharing:

* no wallet;
* no token;

nevertheless execute with the same byte-level characteristics.

The evidence therefore supports the existence of a **shared or sold software tool** more directly than it supports an attribution to the same human operator.

---

# 2.5 Three Attacks on the Graph Conclusions

A co-occurrence graph can generate apparently meaningful clusters even from noise.

Three adversarial tests were therefore applied.

## Attack A — Time-aware null model

The initial Chung–Lu degree-preserving null ignored temporal co-presence.

A time-preserving null instead generated:

* **1,502 false-positive pairs / 6,024 = 25%**
* null giant component: **564 wallets**
* observed giant component: 668 wallets

Only the perfect quad structures survived:

* observed: 1
* 30 null replays: **0**

The six clusters reported above are therefore the survivors of the stronger temporal null test.

## Attack B — Operator identity

Operator identity does not explain the tested price outcome.

| Test                                 | Result        |
| ------------------------------------ | ------------- |
| Permutation ANOVA, 4 operators, n=46 | **p = 1.000** |
| Out-of-sample selected tokens        | ×1.162        |
| Out-of-sample discarded tokens       | ×1.167        |
| Relative difference                  | **−0.5%**     |
| Best group                           | UNKNOWN       |
| Core-signature tokens ≥$300k         | 0.130         |
| Base population                      | 0.213         |

The identified clusters' tokens perform below the market baseline.

Their measured economic advantage comes from the **entry → AMM-open repricing gap**, not from demonstrated ability to push the subsequent price higher.

## Attack C — Selecting the “best operator”

A walk-forward rule requiring **k ≥ 8 tokens** initially produced an apparent rate of:

**0.512**

After removing two addresses supplying 55–64% of the selected tokens:

**0.512 → 0.326**

against a base of:

**0.309**

The rule had effectively memorised two addresses out of **822 creators**.

Applied mid-window, the eventual best operator would have ranked only **5th of 22**.

Equal-weighting by creator leaves **6/13 creators with a positive residual** — approximately a coin flip.

### Conclusion

The graph identifies **real, reproducible and persistent structures**.

It does **not** establish predictive power over token price trajectories.

---

# 3. Quantifying the Cost to the Buyer

## 3.1 The Move Precedes External Visibility

The relevant population contains:

**1,243 tokens / 123 clusters / 20 days**

At first external detection:

| Market cap at detection |         n | ATH already passed |  ATH <60s | ATH <120s | Median delay |
| ----------------------- | --------: | -----------------: | --------: | --------: | -----------: |
| $5k–20k                 |        16 |              43.8% |     62.5% |     62.5% |      0.1 min |
| $20k–30k                |       108 |              23.1% |     55.6% |     60.2% |      0.5 min |
| $30k–40k                |       137 |              27.7% |     60.6% |     65.7% |      0.3 min |
| $40k–50k                |       296 |              18.9% |     44.6% |     54.4% |      1.7 min |
| $50k–65k                |       277 |              26.4% |     46.6% |     51.6% |      1.6 min |
| $65k–85k                |       121 |              26.4% |     52.1% |     58.7% |      0.9 min |
| $85k–120k               |       123 |              14.6% |     31.7% |     35.8% |      6.7 min |
| $120k–300k              |       165 |               9.7% |     17.6% |     23.0% |     36.1 min |
| **Whole population**    | **1,243** |          **21.3%** | **43.8%** | **50.0%** |  **2.0 min** |

The central result is therefore:

> **21.3% of tokens have already reached their maximum by the time they become externally visible, and half reach their maximum within 120 seconds.**

This measurement does not require a predictive model. It is fundamentally a **latency measurement**.

An earlier working note reported 67%.

That figure was produced by an improperly restricted population and is discarded.

The published value is:

**21.3%, n=1,243.**

---

# 3.2 Fifteen Exit Policies

The protocol enters systematically at:

**t0 + 120 seconds**

with **no entry filter**.

Population:

**196 exploitable tokens / 20 clusters / 6 days**

The round-trip model deducts:

**5.8241%**

for fees and adverse slippage.

Decisions are live-safe: a signal observed in a 30-second bucket executes on the following bucket rather than at the price that generated the signal.

| Result                              |      Value |
| ----------------------------------- | ---------: |
| Negative mean                       |  **15/15** |
| Negative median                     |  **12/15** |
| Positive both in mean and median    |   **0/15** |
| 95% cluster-bootstrap CI above zero |   **0/15** |
| Mean of means                       | **−11.3%** |

A particularly important distributional effect is visible in `tp30`:

* median: **+22.4%**
* mean: **−16.4%**

The median alone would therefore give the wrong economic impression.

This is a fat-tailed distribution in which frequent small gains coexist with less frequent but substantially larger losses.

---

# 3.3 Post-Snipe Entry Rules

Seven post-buyback entry rules were tested with a common exit at capture end, up to 20 minutes.

| Entry rule       |   n | Median multiple |       95% CI |   >1× | Net mean | Mean without best token |
| ---------------- | --: | --------------: | -----------: | ----: | -------: | ----------------------: |
| Graduation +120s | 196 |        **0.81** | [0.61, 0.93] | 40.3% |   −10.2% |                  −13.8% |
| Retrace −20%     | 181 |            0.70 | [0.56, 0.91] | 38.1% |   −15.6% |                  −19.5% |
| Retrace −30%     | 160 |            0.64 | [0.53, 0.84] | 35.0% |   −14.0% |                  −24.2% |
| Retrace −40%     | 135 |            0.63 | [0.51, 0.84] | 33.3% |   +16.6% |                  −15.2% |
| Retrace −50%     | 118 |            0.67 | [0.46, 0.80] | 28.0% |   +22.3% |                  −14.1% |
| Retrace −60%     |  86 |            0.46 | [0.09, 0.73] | 23.3% |   +23.9% |                  −26.3% |
| Retrace −70%     |  61 |            0.16 | [0.00, 0.51] | 16.4% |   +13.1% |                  −58.0% |

No strategy reaches a median multiple above 1.

The highest median is:

**0.81×**

for graduation +120 seconds.

The apparently positive means of the deeper retracement strategies are not robust:

1. their cluster-bootstrap CIs cross zero;
2. removing the single best token makes every one negative.

The resulting means fall as low as **−58.0%**.

The positive means are therefore driven by a small number of extreme observations rather than a demonstrated positive expectation.

---

# 3.4 Performance Over Longer Horizons

A separate analysis buys at the robust price of the last 120 seconds of the capture and evaluates the hourly candle at different horizons.

Population:

**191 tokens / 27 clusters**

| Horizon | n with candle | No candle | Median multiple |       95% CI | % >1× | Whole population |
| ------- | ------------: | --------: | --------------: | -----------: | ----: | ---------------: |
| +1h     |           189 |         2 |        **0.48** | [0.38, 0.61] | 18.5% |             0.47 |
| +2h     |           185 |         6 |            0.43 | [0.29, 0.54] | 18.4% |             0.41 |
| +4h     |           179 |        12 |            0.38 | [0.26, 0.49] | 15.6% |             0.30 |
| +24h    |           144 |    **47** |        **0.20** | [0.05, 0.29] | 12.5% |         **0.03** |

At +24h:

**25% of tokens have no candle at all.**

These tokens are treated as untradeable in the whole-population calculation.

Consequently:

* median multiple among tokens with a candle: **0.20×**
* whole-population multiple: **0.03×**

---

## Unit validation

A dedicated units control compares:

**external USD price / swap SOL price**

against the contemporaneous SOL/USD conversion.

Median ratio:

**0.850**

on **n=277**.

This provides a direct sanity check on the conversion.

Without the conversion, the resulting multiples would be inflated by approximately **×76**, turning an approximately 78% loss into an apparent ×34 gain.

The earlier working values are therefore discarded.

Published values:

* +1h: **0.48×**
* +24h: **0.20×**
* Whole population at +24h: **0.03×**
* No candle at +24h: **25%**

---

# 3.5 Why ATH Multiples Are a Dangerous Primary Target

A natural metric is:

> **ATH / entry price**

But using that quantity as the primary target can manufacture apparent predictive relationships.

## Denominator artefact

When the target is mechanically defined as ATH divided by entry market cap, variables correlated with entry market cap can appear predictive even if they have no independent predictive effect.

The observed relationship is:

**log₁₀(ATH) ~ log₁₀(MC)**

with:

**b = 0.884**

on **n=1,243**, after demeaning by day.

The adopted correction is to use the **residual of log(ATH) after regression on log(MC)** and prohibit `t_mult*` variables as primary targets.

### Important limitation

The slope below one is a measured relationship, but its economic interpretation is **not established**.

No standard error or confidence interval is reported for b.

Measurement error in entry market cap can itself bias an OLS slope downward, and the band-level results do not provide clean support for a causal interpretation.

The mechanical decomposition remains reproducible:

**slope of the multiple = b − 1**

but the causal statement:

> “Entering at a higher market cap economically causes worse multiples”

is **not established**.

Across observed market-cap bands above $30k, the ×2 rate is relatively flat:

**42–48%**

The two lowest bands are higher, but they also have much higher rates of already having passed ATH.

There is therefore no observed “good entry band” in this dataset.

With no free parameter, the market cap associated with a 90% chance of ×2 is estimated at:

**$24,385**

while median detection market cap is approximately:

**$52k**

The required price level has therefore already been exceeded by the time of typical detection.

Finally:

> **Reaching the ATH is not equivalent to selling at the ATH.**

All ATH-multiple measurements are therefore **upper bounds**, not directly executable returns. The latency analysis in §3.1 is the more economically relevant measure.

---

# 3.6 Outcome Selection: The `buyable` Trap

A previous analysis filtered on a `buyable` field defined as:

> ATH occurs after detection.

That filter changed the observed ×2 rate from:

**38.3% → 63.0%**

or:

**+24.7 percentage points**

The increase is manufactured by the definition itself: the filter selects tokens whose price subsequently rose.

Population:

**1,701 → 1,034**

This is a direct example of outcome-selection bias and is documented in `PITFALLS.md`.

The earlier reported median-ATH gap is also corrected:

* earlier: **310k vs 48k = ×6.4**
* reproduced: **272k vs 62k = ×4.39**

The mechanism survives; the original magnitude does not.

---

# 4. Established Results and Explicitly Refused Claims

## 4.1 Established

The following findings are supported by the measurements documented above.

### 1. Creation-slot acquisition

Across 42 transaction-level reconstructions:

* the bonding curve is bought inside the creation slot;
* there are **0 prior purchases in 42/42**;
* the position is transferred at a median **t+17.5s**.

### 2. Large repricing before external access

Median market cap rises from approximately:

**$2,158 → $53,985**

before an external buyer can transact.

The same phenomenon is independently measured at **×25.2** on 293 captures.

### 3. Signature among large tokens

Among the frozen ≥$500k population:

**58/70 = 82.9%**

carry the creation-slot signature, with Wilson 95% CI:

**72.4–89.9%**

and perfect agreement between the two tested timing definitions.

### 4. Persistent buyer structures

Six disjoint buyer clusters are identified, with:

**0.90–1.00 intra-cluster wallet reuse**

against a:

**0.019 base rate**

and persistence beyond the original capture window.

### 5. Negative buyer economics

For buyers entering after the initial move:

* **15/15** tested exit policies have negative mean returns;
* **0/15** cluster-bootstrap CIs are above zero;
* +24h median multiple is **0.20×**;
* whole-population +24h multiple is **0.03×** when untradeable tokens are counted as zero.

---

# 4.2 Explicitly Not Established

The analysis does **not** establish:

### Historical market evolution

The available historical depth is insufficient to date an evolution from sequential purchases to atomic execution.

### Predictive power of cluster identity

Cluster identity does not predict token trajectory in the tested data:

**p = 1.000**

and the identified clusters perform below baseline.

### A profitable strategy

No trading strategy is proposed.

The principal economic result is negative.

### Identity or intent

No address is attributed to a person, organization, or intent.

The analysis concerns public technical identifiers and observable transaction patterns.

### Generalisation to the entire market

The effective sensor coverage is approximately:

**6.8%**

and the captured population over-represents launches that succeeded.

The findings therefore describe the observed corpus, not the entire pump.fun market.

---

# 5. Reproduction

All figures and tables are designed to regenerate offline from `code/` and `data/`.

```bash
python3 code/f_figures_resultats.py
python3 code/f_signature_gros_tokens.py
python3 code/m4_infra_ubiquity.py
python3 code/t1_base_rate_sorties.py
python3 code/t3_ath_avant_detection.py
python3 code/t4_entree_post_snipe_20min.py
python3 code/t5_horizon_1h_24h.py
```

The scripts above do not make network calls and do not require an API key.

---

# 6. Anonymisation

Infrastructure addresses are represented as `W1`–`W5` in this document and in the figures.

This is a presentation-level redaction rather than a claim that the addresses are private: the underlying identifiers are public and appear elsewhere in the repository.

W1 is specifically redacted because its prefix constitutes a racial slur. Reproducing that identifier would add no analytical value.

W1 remains recoverable through its published metrics:

* 165 tokens
* 58.5% of the corpus

The other infrastructure addresses are anonymised here for presentation consistency but remain available in `docs/out/m4_infra.json`.

---

# 7. Measurement Conventions

The liquidation-tranche counts in §1.5 — approximately **119–194** — are aggregated per cluster rather than per launch.

They should therefore be interpreted as an **order of magnitude**.

All other values in this document are measurements attached to an explicitly declared population size.

---

# 8. Corrected Figures

This document replaces several values from earlier working notes that did not reproduce on the current corpus.

| Measurement                     | Earlier value | Published value |
| ------------------------------- | ------------: | --------------: |
| Selection-bias factor           |          ×6.4 |       **×4.39** |
| ATH already passed at detection |           67% |       **21.3%** |
| +1h multiple                    |         0.35× |       **0.48×** |
| +24h multiple                   |         0.08× |       **0.20×** |
| No-volume share                 |           50% | **25% at +24h** |
| Raw swap count                  |       476,847 |     **511,508** |

A separate reconciliation also corrected the AMM-open market-cap estimate from the earlier `v05` value of **$46,147** to the authoritative `v06` value of **$53,985**.

---

# Final Takeaway

The strongest result in this investigation is not that a particular group “wins” the market.

It is that the **observable launch mechanics are highly structured**, while the **subsequent predictive and trading claims fail under increasingly strict controls**.

The data support three distinct conclusions:

1. **A reproducible creation-slot execution pattern exists.**
2. **Persistent buyer structures exist, but graph connectivity must be aggressively cleaned for shared infrastructure and temporal co-occurrence.**
3. **The observed early-entry advantage does not translate into demonstrated predictive power over subsequent token trajectories or positive post-detection trading returns.**

The analysis therefore treats the forensic signature as a **measured market-microstructure phenomenon**, not as proof of identity, intent, future price direction, or a profitable strategy.

That distinction is deliberate.

The objective is not to make the strongest possible claim.

It is to identify the strongest claim that survives its own attempts at refutation.
